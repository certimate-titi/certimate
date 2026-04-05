"""Fix category names to match frontend tabs.

Revision ID: 033
Revises: 032

Merge legacy categories (金融證照, 不動產證照 → 金融) and (iPAS 產業人才鑑定 → IT).
Frontend tabs expect: 金融, IT, 語言, 醫療, 公務員
"""
from alembic import op
import sqlalchemy as sa

revision = "033"
down_revision = "032"
branch_labels = None
depends_on = None

# Target category UUIDs (from migration 021)
TARGET_CATEGORIES = {
    "金融": "a0000001-0000-0000-0000-000000000001",
    "IT": "a0000001-0000-0000-0000-000000000004",
}

# Legacy category names to merge
LEGACY_RENAMES = {
    "金融證照": "金融",
    "不動產證照": "金融",
    "iPAS 產業人才鑑定": "IT",
    "iPAS": "IT",
}


def upgrade():
    conn = op.get_bind()

    for old_name, new_name in LEGACY_RENAMES.items():
        target_id = TARGET_CATEGORIES[new_name]

        # Find legacy category
        legacy = conn.execute(
            sa.text("SELECT id FROM subject_categories WHERE name = :name"),
            {"name": old_name},
        ).fetchone()

        if not legacy:
            continue

        legacy_id = str(legacy[0])

        if legacy_id == target_id:
            # Same row, just rename
            conn.execute(
                sa.text("UPDATE subject_categories SET name = :new_name WHERE id = :id"),
                {"new_name": new_name, "id": legacy_id},
            )
        else:
            # Different row — move subjects to target category, then delete legacy
            # Ensure target category exists
            target_exists = conn.execute(
                sa.text("SELECT id FROM subject_categories WHERE id = :id"),
                {"id": target_id},
            ).fetchone()

            if not target_exists:
                # Create target category
                conn.execute(
                    sa.text("INSERT INTO subject_categories (id, name) VALUES (:id, :name) ON CONFLICT DO NOTHING"),
                    {"id": target_id, "name": new_name},
                )

            # Move subjects from legacy to target
            conn.execute(
                sa.text("UPDATE subjects SET category_id = :target WHERE category_id = :legacy"),
                {"target": target_id, "legacy": legacy_id},
            )

            # Delete legacy category (now empty)
            conn.execute(
                sa.text("DELETE FROM subject_categories WHERE id = :id"),
                {"id": legacy_id},
            )

    # Also rename target categories if they have old names
    conn.execute(
        sa.text("UPDATE subject_categories SET name = '金融' WHERE id = :id AND name != '金融'"),
        {"id": TARGET_CATEGORIES["金融"]},
    )
    conn.execute(
        sa.text("UPDATE subject_categories SET name = 'IT' WHERE id = :id AND name != 'IT'"),
        {"id": TARGET_CATEGORIES["IT"]},
    )


def downgrade():
    conn = op.get_bind()
    # Rename back
    conn.execute(
        sa.text("UPDATE subject_categories SET name = '金融證照' WHERE id = :id"),
        {"id": TARGET_CATEGORIES["金融"]},
    )
    conn.execute(
        sa.text("UPDATE subject_categories SET name = 'iPAS 產業人才鑑定' WHERE id = :id"),
        {"id": TARGET_CATEGORIES["IT"]},
    )
