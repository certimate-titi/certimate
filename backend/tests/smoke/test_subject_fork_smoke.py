"""Smoke test — PRD-034 SubjectForkService end-to-end.

執行：
    cd backend
    .venv/bin/python -m pytest tests/smoke/test_subject_fork_smoke.py -v -s
"""

from __future__ import annotations

import os
import tempfile
import uuid

import pytest
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def db_engine():
    with PostgresContainer("pgvector/pgvector:pg15") as pg:
        url = pg.get_connection_url().replace("postgresql+psycopg2", "postgresql+psycopg")
        os.environ["DATABASE_URL"] = url

        from alembic import command
        from alembic.config import Config
        from sqlalchemy import create_engine

        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(cfg, "head")

        engine = create_engine(url)
        # Work around pre-existing mismatch: model says JSON, migration 002 created text[]
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE resources ALTER COLUMN tags DROP DEFAULT"))
            conn.execute(
                text("ALTER TABLE resources ALTER COLUMN tags TYPE jsonb USING to_jsonb(tags)")
            )
            conn.execute(text("ALTER TABLE resources ALTER COLUMN tags SET DEFAULT '[]'::jsonb"))
        yield engine


@pytest.fixture
def db(db_engine):
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    # Clean slate for test isolation
    session.execute(
        __import__("sqlalchemy").text(
            "TRUNCATE subjects, resources, knowledge_nodes, "
            "subject_default_resources, users, subject_categories CASCADE"
        )
    )
    session.commit()
    yield session
    session.close()


@pytest.fixture
def tmp_storage(monkeypatch):
    """Use LocalStorageService with tmpdir to avoid GCS."""
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    with tempfile.TemporaryDirectory() as tmp:
        from app.services import storage_service as ss

        orig = ss.LocalStorageService.__init__

        def patched(self, base_dir=None):
            orig(self, base_dir=tmp)

        monkeypatch.setattr(ss.LocalStorageService, "__init__", patched)
        yield tmp


def _seed_platform_subject(db) -> tuple[uuid.UUID, uuid.UUID, list[uuid.UUID]]:
    """建立 platform subject + category + admin user + 2 份 PDF resources + 3 個 nodes。"""
    from app.models.knowledge_node import KnowledgeNode
    from app.models.resource import Resource, ResourceScope, ResourceStatus, ResourceType
    from app.models.subject import Subject, SubjectCategory
    from app.models.subject_default_resource import SubjectDefaultResource
    from app.models.user import User

    cat = SubjectCategory(id=uuid.uuid4(), name="iPAS", sort_order=1)
    db.add(cat)
    admin = User(
        id=uuid.uuid4(),
        email="admin@test.com",
        password_hash="x",
        display_name="admin",
    )
    db.add(admin)
    db.flush()

    platform = Subject(
        id=uuid.uuid4(),
        category_id=cat.id,
        name="iPAS AI 應用規劃師（初級）",
        scope="platform",
        version=1,
    )
    db.add(platform)
    db.flush()

    # 建立 2 份 platform resources + 實體檔案
    from app.services.storage_service import get_storage_service

    storage = get_storage_service()
    platform_rids = []
    for i in range(2):
        rid = uuid.uuid4()
        gcs_path = storage.save_file(
            user_id=str(admin.id),
            resource_id=str(rid),
            filename=f"ch{i+1}.pdf",
            data=f"fake pdf content {i+1}".encode(),
        )
        res = Resource(
            id=rid,
            user_id=admin.id,
            subject_id=platform.id,
            name=f"ch{i+1}.pdf",
            type=ResourceType.PDF.value,
            scope=ResourceScope.PLATFORM.value,
            status=ResourceStatus.COMPLETED.value,
            gcs_path=gcs_path,
            file_size_bytes=100,
            tags=None,
        )
        db.add(res)
        db.flush()
        db.add(SubjectDefaultResource(subject_id=platform.id, resource_id=rid))
        platform_rids.append(rid)
    db.flush()

    # 建立 3 個 knowledge_nodes（1 root, 2 children）
    root = KnowledgeNode(
        id=uuid.uuid4(),
        subject_id=platform.id,
        resource_id=platform_rids[0],
        name="AI 概論",
        depth=0,
        sort_order=0,
    )
    db.add(root)
    db.flush()
    for i in range(2):
        db.add(
            KnowledgeNode(
                id=uuid.uuid4(),
                subject_id=platform.id,
                resource_id=platform_rids[i],
                parent_id=root.id,
                name=f"子節點 {i+1}",
                depth=1,
                sort_order=i,
            )
        )
    db.commit()
    return admin.id, platform.id, platform_rids


def _create_user(db, email: str) -> uuid.UUID:
    from app.models.user import User

    user = User(id=uuid.uuid4(), email=email, password_hash="x", display_name=email)
    db.add(user)
    db.commit()
    return user.id


def test_fork_success(db, tmp_storage):
    from app.models.knowledge_node import KnowledgeNode
    from app.models.resource import Resource
    from app.models.subject import Subject
    from app.services.subject_fork_service import SubjectForkService

    _, platform_id, _ = _seed_platform_subject(db)
    alice = _create_user(db, "alice@test.com")

    result = SubjectForkService(db).fork_platform_subject(
        user_id=str(alice), platform_subject_id=str(platform_id)
    )

    assert "user_subject_id" in result, result
    assert result["resources_copied"] == 2
    assert result["nodes_copied"] == 3

    user_sid = uuid.UUID(result["user_subject_id"])
    user_subj = db.query(Subject).filter(Subject.id == user_sid).first()
    assert user_subj.scope == "personal"
    assert user_subj.owner_user_id == alice
    assert user_subj.source_platform_subject_id == platform_id

    user_resources = db.query(Resource).filter(Resource.subject_id == user_sid).all()
    assert len(user_resources) == 2
    for r in user_resources:
        assert r.user_id == alice
        assert r.scope == "personal"
        assert r.gcs_path and str(alice) in r.gcs_path

    user_nodes = db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == user_sid).all()
    assert len(user_nodes) == 3
    root_count = sum(1 for n in user_nodes if n.parent_id is None)
    assert root_count == 1
    for n in user_nodes:
        assert n.source_resource_count == 1


def test_fork_idempotent_409(db, tmp_storage):
    from app.services.subject_fork_service import SubjectForkService

    _, platform_id, _ = _seed_platform_subject(db)
    alice = _create_user(db, "alice@test.com")

    svc = SubjectForkService(db)
    svc.fork_platform_subject(
        user_id=str(alice), platform_subject_id=str(platform_id)
    )
    result2 = svc.fork_platform_subject(
        user_id=str(alice), platform_subject_id=str(platform_id)
    )
    assert result2.get("error") is True
    assert result2["status_code"] == 409
    assert "您已擁有此科目" in result2["message"]


def test_empty_reason_no_resources(db, tmp_storage):
    """PRD-034 US-02: fork 後刪光所有資源，心智圖應回 empty_reason=no_resources。"""
    from app.models.learning_journey import LearningJourney
    from app.models.resource import Resource
    from app.services.knowledge_nav_service import KnowledgeNavService
    from app.services.subject_fork_service import SubjectForkService

    _, platform_id, _ = _seed_platform_subject(db)
    alice = _create_user(db, "alice@test.com")

    fork_result = SubjectForkService(db).fork_platform_subject(
        user_id=str(alice), platform_subject_id=str(platform_id)
    )
    user_sid = uuid.UUID(fork_result["user_subject_id"])

    # 建立 LearningJourney（nav service 檢查用）
    db.add(LearningJourney(id=uuid.uuid4(), user_id=alice, subject_id=user_sid))
    db.commit()

    # 刪光 resources + 對應 knowledge_nodes
    from app.models.knowledge_node import KnowledgeNode

    rids = [r.id for r in db.query(Resource).filter(Resource.subject_id == user_sid).all()]
    db.query(KnowledgeNode).filter(KnowledgeNode.resource_id.in_(rids)).delete(
        synchronize_session=False
    )
    db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == user_sid).delete(
        synchronize_session=False
    )
    db.query(Resource).filter(Resource.subject_id == user_sid).delete(
        synchronize_session=False
    )
    db.commit()

    result = KnowledgeNavService(db).get_nodes_by_subject(str(user_sid), str(alice))
    assert result.get("error") is False
    assert result["nodes"] == []
    assert result["empty_reason"] == "no_resources"


def test_admin_publish_rollback(db, tmp_storage):
    from app.models.subject import Subject
    from app.services.platform_subject_admin_service import PlatformSubjectAdminService

    _, platform_id, _ = _seed_platform_subject(db)
    svc = PlatformSubjectAdminService(db)

    r1 = svc.publish(str(platform_id))
    assert r1["version"] == 2
    assert r1["published_at"] is not None

    r2 = svc.rollback(str(platform_id))
    assert r2["version"] == 1
    assert r2["published_at"] is None

    r3 = svc.rollback(str(platform_id))
    assert r3.get("error") is True
    assert r3["status_code"] == 400

    platform = db.query(Subject).filter(Subject.id == platform_id).first()
    assert platform.version == 1
