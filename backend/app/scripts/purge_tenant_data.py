"""租戶資料抹除腳本 — Phase 4 退場機制.

用途：當企業租戶解約時，物理性刪除該 tenant_id 關聯的所有資料。

⚠️  警告：此操作不可逆，請務必在執行前進行完整備份。

使用方式：
    # 模擬執行（顯示將被刪除的資料量，不實際刪除）
    python -m app.scripts.purge_tenant_data --tenant-id <uuid> --dry-run

    # 正式執行（需要 --confirm 標誌）
    python -m app.scripts.purge_tenant_data --tenant-id <uuid> --confirm

    # 含 GCS 檔案清理（需要設定 GOOGLE_APPLICATION_CREDENTIALS）
    python -m app.scripts.purge_tenant_data --tenant-id <uuid> --confirm --purge-files

環境變數：
    DATABASE_URL — PostgreSQL 連線字串
    GCS_BUCKET   — Google Cloud Storage bucket 名稱（若 --purge-files）
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# 依刪除順序排列的業務資料表（依賴關係：子表在前，父表在後）
# 每個項目：(table_name, tenant_id_column, join_condition_if_needed)
PURGE_PLAN = [
    # 直接含 tenant_id 的表
    ("resource_chunks",      "tenant_id",  None),
    ("answers",              "tenant_id",  None),
    ("questions",            "tenant_id",  None),
    ("exams",                "tenant_id",  None),
    ("knowledge_nodes",      "tenant_id",  None),
    ("ai_chat_sessions",     "tenant_id",  None),
    ("resources",            "tenant_id",  None),
    # 間接關聯（透過 user_id 或 resource_id 關聯到租戶，謹慎處理）
    # 注意：ai_chat_messages 透過 session_id 關聯，需子查詢
]

# 間接關聯表（需要 JOIN 查詢）
INDIRECT_PURGE_PLAN = [
    {
        "table": "ai_chat_messages",
        "via": "ai_chat_sessions",
        "join": "ai_chat_messages.session_id = ai_chat_sessions.id",
        "filter": "ai_chat_sessions.tenant_id = :tenant_id",
    },
]


def count_tenant_data(db: Session, tenant_id: str) -> dict[str, int]:
    """計算各表中屬於該租戶的資料筆數。"""
    counts = {}
    for table, col, _ in PURGE_PLAN:
        result = db.execute(
            text(f"SELECT COUNT(*) FROM {table} WHERE {col} = :tid"),
            {"tid": tenant_id},
        ).scalar()
        counts[table] = result or 0

    for spec in INDIRECT_PURGE_PLAN:
        result = db.execute(
            text(
                f"SELECT COUNT(*) FROM {spec['table']} "
                f"JOIN {spec['via']} ON {spec['join']} "
                f"WHERE {spec['filter']}"
            ),
            {"tenant_id": tenant_id},
        ).scalar()
        counts[spec["table"]] = result or 0

    return counts


def get_gcs_paths_for_tenant(db: Session, tenant_id: str) -> list[str]:
    """取得屬於該租戶的所有 GCS 檔案路徑。"""
    rows = db.execute(
        text(
            "SELECT gcs_path FROM resources "
            "WHERE tenant_id = :tid AND gcs_path IS NOT NULL"
        ),
        {"tid": tenant_id},
    ).fetchall()
    return [row[0] for row in rows if row[0]]


def purge_gcs_files(gcs_paths: list[str], bucket_name: str, dry_run: bool) -> int:
    """刪除 GCS 中的檔案（需要 google-cloud-storage 套件）。"""
    try:
        from google.cloud import storage  # type: ignore
    except ImportError:
        logger.warning("⚠️  google-cloud-storage 未安裝，跳過 GCS 清理")
        return 0

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    deleted = 0

    for path in gcs_paths:
        blob_name = path.removeprefix(f"gs://{bucket_name}/").removeprefix("/")
        if dry_run:
            logger.info(f"  [DRY-RUN] 將刪除 GCS: gs://{bucket_name}/{blob_name}")
        else:
            try:
                bucket.blob(blob_name).delete()
                logger.info(f"  ✓ 刪除 GCS: gs://{bucket_name}/{blob_name}")
                deleted += 1
            except Exception as e:
                logger.error(f"  ✗ 刪除失敗 {blob_name}: {e}")

    return deleted


def purge_tenant(
    tenant_id: str,
    dry_run: bool = True,
    purge_files: bool = False,
    gcs_bucket: Optional[str] = None,
) -> dict:
    """執行租戶資料抹除。

    Returns:
        {
            "tenant_id": str,
            "dry_run": bool,
            "counts_before": dict,
            "rows_deleted": int,
            "files_deleted": int,
            "tenant_deactivated": bool,
            "timestamp": str,
        }
    """
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    SessionFactory = sessionmaker(bind=engine)

    result = {
        "tenant_id": tenant_id,
        "dry_run": dry_run,
        "counts_before": {},
        "rows_deleted": 0,
        "files_deleted": 0,
        "tenant_deactivated": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with SessionFactory() as db:
        # 1. 驗證租戶存在
        tenant = db.execute(
            text("SELECT id, slug, name, is_active FROM tenants WHERE id = :tid"),
            {"tid": tenant_id},
        ).fetchone()

        if not tenant:
            raise ValueError(f"找不到 tenant_id: {tenant_id}")

        logger.info(f"🏢 租戶資訊: slug={tenant[1]!r}, name={tenant[2]!r}, is_active={tenant[3]}")

        if tenant[1] == "public_b2c":
            raise ValueError("❌ 禁止刪除 public_b2c 預設租戶")

        # 2. 統計資料量
        counts = count_tenant_data(db, tenant_id)
        result["counts_before"] = counts
        total_rows = sum(counts.values())

        logger.info(f"\n📊 待清理資料統計（tenant_id: {tenant_id}）：")
        for table, count in counts.items():
            if count > 0:
                logger.info(f"  {table}: {count:,} 筆")
        logger.info(f"  合計: {total_rows:,} 筆")

        # 3. 取得 GCS 路徑（在刪除前取得）
        gcs_paths = []
        if purge_files:
            gcs_paths = get_gcs_paths_for_tenant(db, tenant_id)
            logger.info(f"\n📁 待清理 GCS 檔案: {len(gcs_paths):,} 個")

        if dry_run:
            logger.info("\n🔍 DRY-RUN 模式：以上資料將被刪除，但尚未執行")
            return result

        # 4. 正式刪除（依順序）
        logger.info("\n🗑️  開始刪除資料...")

        # 間接關聯表先刪
        for spec in INDIRECT_PURGE_PLAN:
            r = db.execute(
                text(
                    f"DELETE FROM {spec['table']} "
                    f"WHERE {spec['table'].split('_')[0]}_id IN ("
                    f"  SELECT id FROM {spec['via']} WHERE {spec['filter']}"
                    f")"
                ),
                {"tenant_id": tenant_id},
            )
            deleted = r.rowcount
            result["rows_deleted"] += deleted
            logger.info(f"  ✓ {spec['table']}: 刪除 {deleted:,} 筆")

        # 直接含 tenant_id 的表
        for table, col, _ in PURGE_PLAN:
            r = db.execute(
                text(f"DELETE FROM {table} WHERE {col} = :tid"),
                {"tid": tenant_id},
            )
            deleted = r.rowcount
            result["rows_deleted"] += deleted
            logger.info(f"  ✓ {table}: 刪除 {deleted:,} 筆")

        # 5. 停用租戶（不刪除租戶記錄本身，保留稽核軌跡）
        db.execute(
            text(
                "UPDATE tenants SET is_active = false, "
                "updated_at = now() WHERE id = :tid"
            ),
            {"tid": tenant_id},
        )
        result["tenant_deactivated"] = True
        logger.info(f"  ✓ 租戶已停用（保留記錄供稽核）")

        db.commit()
        logger.info(f"\n✅ 資料庫清理完成，共刪除 {result['rows_deleted']:,} 筆")

    # 6. 清理 GCS 檔案（在 DB commit 後）
    if purge_files and gcs_paths and gcs_bucket:
        logger.info(f"\n🗑️  清理 GCS 檔案（bucket: {gcs_bucket}）...")
        result["files_deleted"] = purge_gcs_files(gcs_paths, gcs_bucket, dry_run=False)
        logger.info(f"  ✓ GCS 清理完成，刪除 {result['files_deleted']:,} 個檔案")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="CertiMate 租戶資料抹除工具（Phase 4 退場機制）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  # 模擬執行
  python -m app.scripts.purge_tenant_data --tenant-id <uuid> --dry-run

  # 正式執行（不可逆！）
  python -m app.scripts.purge_tenant_data --tenant-id <uuid> --confirm

  # 含 GCS 清理
  python -m app.scripts.purge_tenant_data --tenant-id <uuid> --confirm --purge-files --gcs-bucket my-bucket
        """,
    )
    parser.add_argument("--tenant-id", required=True, help="要刪除的租戶 UUID")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="模擬執行（預設）")
    parser.add_argument("--confirm", action="store_true",
                        help="確認正式刪除（覆蓋 --dry-run）")
    parser.add_argument("--purge-files", action="store_true",
                        help="同時清理 GCS 儲存檔案")
    parser.add_argument("--gcs-bucket", help="GCS bucket 名稱（--purge-files 時必填）")

    args = parser.parse_args()

    dry_run = not args.confirm

    if not dry_run:
        logger.warning("⚠️  正式刪除模式！此操作不可逆。")
        confirm = input(f"請輸入租戶 ID 確認（{args.tenant_id}）: ").strip()
        if confirm != args.tenant_id:
            logger.error("租戶 ID 不符，操作取消")
            sys.exit(1)

    try:
        result = purge_tenant(
            tenant_id=args.tenant_id,
            dry_run=dry_run,
            purge_files=args.purge_files,
            gcs_bucket=args.gcs_bucket,
        )
        logger.info(f"\n📋 執行摘要: {result}")
    except ValueError as e:
        logger.error(f"❌ 錯誤: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ 未預期錯誤: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
