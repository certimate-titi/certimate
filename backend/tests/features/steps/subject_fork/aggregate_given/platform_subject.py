"""Given — PRD-034 Fork 相關前置資料。"""

from __future__ import annotations

import os
import tempfile
import uuid

from behave import given


def _ensure_storage_tmpdir(context) -> str:
    """建立臨時 LocalStorage 目錄並 monkey-patch BaseService。"""
    if context.memo.get("_fork_tmpdir"):
        return context.memo["_fork_tmpdir"]
    tmp = tempfile.mkdtemp(prefix="fork_bdd_")
    context.memo["_fork_tmpdir"] = tmp
    os.environ["STORAGE_BACKEND"] = "local"
    # Patch LocalStorageService.__init__ 使其使用臨時目錄
    from app.services import storage_service as ss

    orig = ss.LocalStorageService.__init__

    def _patched(self, base_dir=None):
        orig(self, base_dir=tmp)

    context.memo["_orig_local_init"] = orig
    ss.LocalStorageService.__init__ = _patched
    return tmp


def _alter_tags_column(db):
    """pre-existing model/DB mismatch 工作繞：tags text[] → jsonb。一次性操作。"""
    from sqlalchemy import text

    db.execute(
        text(
            "DO $$ BEGIN "
            "  IF (SELECT data_type FROM information_schema.columns "
            "      WHERE table_name='resources' AND column_name='tags') = 'ARRAY' THEN "
            "    ALTER TABLE resources ALTER COLUMN tags DROP DEFAULT; "
            "    ALTER TABLE resources ALTER COLUMN tags TYPE jsonb USING to_jsonb(tags); "
            "    ALTER TABLE resources ALTER COLUMN tags SET DEFAULT '[]'::jsonb; "
            "  END IF; "
            "END $$;"
        )
    )
    db.commit()


@given("資料庫已套用 migration 065")
def step_migration(context):
    # Testcontainers + alembic upgrade head 已在 before_all 執行
    _alter_tags_column(context.db_session)


@given('存在平台管理員帳號 "{email}"')
def step_admin(context, email):
    from app.models.user import User

    uid = uuid.uuid4()
    user = User(
        id=uid,
        email=email,
        password_hash="x",
        display_name="admin",
        role="admin",
    )
    context.db_session.add(user)
    context.db_session.commit()
    context.ids[email] = str(uid)


@given('存在考生帳號 "{email}"')
def step_user(context, email):
    from app.models.user import User

    uid = uuid.uuid4()
    user = User(id=uid, email=email, password_hash="x", display_name=email)
    context.db_session.add(user)
    context.db_session.commit()
    context.ids[email] = str(uid)


@given('存在 scope=platform 的科目 "{name}" 綁定 {n:d} 份預載 PDF 資源')
def step_platform_subject(context, name, n):
    _ensure_storage_tmpdir(context)
    from app.models.knowledge_node import KnowledgeNode
    from app.models.resource import Resource, ResourceScope, ResourceStatus, ResourceType
    from app.models.subject import Subject, SubjectCategory
    from app.models.subject_default_resource import SubjectDefaultResource
    from app.models.user import User
    from app.services.storage_service import get_storage_service

    db = context.db_session

    # 確保 admin user 存在
    admin = db.query(User).filter(User.role == "admin").first()
    if not admin:
        admin = User(
            id=uuid.uuid4(),
            email="_fork_seed_admin@test.com",
            password_hash="x",
            display_name="seed",
            role="admin",
        )
        db.add(admin)
        db.flush()

    cat = SubjectCategory(id=uuid.uuid4(), name="iPAS", sort_order=1)
    db.add(cat)
    db.flush()

    platform = Subject(
        id=uuid.uuid4(),
        category_id=cat.id,
        name=name,
        scope="platform",
        version=1,
    )
    db.add(platform)
    db.flush()

    storage = get_storage_service()
    platform_rids = []
    for i in range(n):
        rid = uuid.uuid4()
        gcs_path = storage.save_file(
            user_id=str(admin.id),
            resource_id=str(rid),
            filename=f"ch{i+1}.pdf",
            data=f"fake pdf {i+1}".encode(),
        )
        db.add(
            Resource(
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
        )
        db.flush()
        db.add(SubjectDefaultResource(subject_id=platform.id, resource_id=rid))
        platform_rids.append(rid)
    db.flush()

    # 3 個知識節點
    root = KnowledgeNode(
        id=uuid.uuid4(),
        subject_id=platform.id,
        resource_id=platform_rids[0],
        name=f"{name} 概論",
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
                resource_id=platform_rids[min(i, n - 1)],
                parent_id=root.id,
                name=f"子節點 {i+1}",
                depth=1,
                sort_order=i,
            )
        )
    db.commit()

    context.memo["platform_subject_id"] = str(platform.id)
    context.memo["platform_subject_name"] = name
    context.memo["platform_resource_ids"] = [str(r) for r in platform_rids]


@given('我以 "{email}" 身份登入')
def step_login(context, email):
    user_id = context.ids[email]
    context.memo["current_user_id"] = user_id
    context.memo["current_user_email"] = email
    context.memo["current_token"] = context.jwt_helper.generate_token(user_id)


@given('我已 fork 過 "{name}"')
@given('我已 fork "{name}"')
def step_already_forked(context, name):
    from app.services.subject_fork_service import SubjectForkService

    uid = context.memo["current_user_id"]
    platform_id = context.memo["platform_subject_id"]
    result = SubjectForkService(context.db_session).fork_platform_subject(
        user_id=uid, platform_subject_id=platform_id
    )
    assert "user_subject_id" in result, result
    context.memo["user_subject_id"] = result["user_subject_id"]


@given('我已 fork "{name}" 並刪除全部 {n:d} 份資源')
def step_fork_then_delete_all(context, name, n):
    from app.models.knowledge_node import KnowledgeNode
    from app.models.resource import Resource
    from app.models.learning_journey import LearningJourney
    from app.services.subject_fork_service import SubjectForkService

    uid = context.memo["current_user_id"]
    platform_id = context.memo["platform_subject_id"]
    result = SubjectForkService(context.db_session).fork_platform_subject(
        user_id=uid, platform_subject_id=platform_id
    )
    user_sid = uuid.UUID(result["user_subject_id"])
    context.memo["user_subject_id"] = str(user_sid)

    db = context.db_session
    # 建立 LearningJourney（nav service 需要）
    db.add(LearningJourney(id=uuid.uuid4(), user_id=uuid.UUID(uid), subject_id=user_sid))

    rids = [
        r.id for r in db.query(Resource).filter(Resource.subject_id == user_sid).all()
    ]
    db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == user_sid).delete(
        synchronize_session=False
    )
    db.query(Resource).filter(Resource.subject_id == user_sid).delete(
        synchronize_session=False
    )
    db.commit()
    assert len(rids) == n, f"expected {n} resources, got {len(rids)}"


@given("我的科目中有資源 {res:w} 對應 {n:d} 個專屬節點（source_resource_count = 1）")
def step_fork_r1_exclusive_nodes(context, res, n):
    from app.models.knowledge_node import KnowledgeNode
    from app.models.resource import Resource

    db = context.db_session
    user_sid = uuid.UUID(context.memo["user_subject_id"])
    # 抓第一份 resource 當作 R1
    r1 = db.query(Resource).filter(Resource.subject_id == user_sid).first()
    context.memo[f"{res}_id"] = str(r1.id)

    # 刪掉既有該 resource 的節點，新增 n 個單引用節點
    # 先找出要刪除的節點 id，再把所有指向它們的 parent_id 設為 NULL（避免自參考 FK 違規）
    to_delete_ids = [
        n.id for n in db.query(KnowledgeNode).filter(KnowledgeNode.resource_id == r1.id).all()
    ]
    if to_delete_ids:
        db.query(KnowledgeNode).filter(KnowledgeNode.parent_id.in_(to_delete_ids)).update(
            {KnowledgeNode.parent_id: None}, synchronize_session=False
        )
        db.flush()
    db.query(KnowledgeNode).filter(KnowledgeNode.resource_id == r1.id).delete(
        synchronize_session=False
    )
    node_ids = []
    for i in range(n):
        nid = uuid.uuid4()
        db.add(
            KnowledgeNode(
                id=nid,
                subject_id=user_sid,
                resource_id=r1.id,
                name=f"{res}專屬節點 {i+1}",
                depth=1,
                sort_order=i,
                source_resource_count=1,
            )
        )
        node_ids.append(str(nid))
    db.commit()
    context.memo[f"{res}_exclusive_node_ids"] = node_ids


@given('節點 {node:w} 被資源 {r1:w} 與 {r2:w} 共同引用（source_resource_count = {cnt:d}）')
def step_merged_node(context, node, r1, r2, cnt):
    from app.models.knowledge_node import KnowledgeNode
    from app.models.resource import Resource, ResourceScope, ResourceStatus, ResourceType
    from app.models.subject import Subject, SubjectCategory
    from app.models.user import User
    from app.services.storage_service import get_storage_service

    _ensure_storage_tmpdir(context)
    db = context.db_session
    uid = uuid.UUID(context.memo["current_user_id"])

    cat = db.query(SubjectCategory).first()
    if not cat:
        cat = SubjectCategory(id=uuid.uuid4(), name="iPAS", sort_order=1)
        db.add(cat)
        db.flush()

    user_sid = context.memo.get("user_subject_id")
    if user_sid:
        user_sid = uuid.UUID(user_sid)
    else:
        subj = Subject(
            id=uuid.uuid4(),
            category_id=cat.id,
            name="用戶科目",
            scope="personal",
            owner_user_id=uid,
            version=1,
        )
        db.add(subj)
        db.flush()
        user_sid = subj.id
        context.memo["user_subject_id"] = str(user_sid)

    storage = get_storage_service()
    r_ids = {}
    for label in (r1, r2):
        rid = uuid.uuid4()
        gcs = storage.save_file(str(uid), str(rid), f"{label}.pdf", b"x")
        db.add(
            Resource(
                id=rid,
                user_id=uid,
                subject_id=user_sid,
                name=f"{label}.pdf",
                type=ResourceType.PDF.value,
                scope=ResourceScope.PERSONAL.value,
                status=ResourceStatus.COMPLETED.value,
                gcs_path=gcs,
                file_size_bytes=100,
                tags=None,
            )
        )
        db.flush()
        r_ids[label] = rid
        context.memo[f"{label}_id"] = str(rid)

    nid = uuid.uuid4()
    # merged 節點歸屬 R1（主要引用），但 count=cnt 代表被多份資源引用
    db.add(
        KnowledgeNode(
            id=nid,
            subject_id=user_sid,
            resource_id=r_ids[r1],
            name=f"merged 節點 {node}",
            depth=1,
            sort_order=0,
            source_resource_count=cnt,
        )
    )
    db.commit()
    context.memo[f"{node}_id"] = str(nid)


@given('"{email}" 已 fork "{name}"（版本 v{ver:d}）')
def step_other_user_forked(context, email, name, ver):
    from app.models.user import User
    from app.services.subject_fork_service import SubjectForkService

    db = context.db_session
    if email not in context.ids:
        uid = uuid.uuid4()
        db.add(User(id=uid, email=email, password_hash="x", display_name=email))
        db.commit()
        context.ids[email] = str(uid)

    platform_id = context.memo["platform_subject_id"]
    result = SubjectForkService(db).fork_platform_subject(
        user_id=context.ids[email], platform_subject_id=platform_id
    )
    assert "user_subject_id" in result
    context.memo[f"{email}_subject_id"] = result["user_subject_id"]


@given('platform subject 版本為 v{ver:d}，已有草稿修改')
def step_platform_v1_with_draft(context, ver):
    # 已由 step_platform_subject 建立 v1；無需額外動作（draft = 修改 default_resources，此處略）
    assert context.memo.get("platform_subject_id")


@given('platform subject 已發布 v{src:d} → v{dst:d}')
def step_platform_published(context, src, dst):
    from app.services.platform_subject_admin_service import PlatformSubjectAdminService

    pid = context.memo["platform_subject_id"]
    svc = PlatformSubjectAdminService(context.db_session)
    for _ in range(dst - src):
        r = svc.publish(pid)
        assert r.get("error") is not True, r


@given('GCS copy_blob 在第 {n:d} 份檔案模擬失敗')
def step_inject_gcs_failure(context, n):
    """Monkey-patch LocalStorageService.copy_file 在第 n 次呼叫時 raise。"""
    from app.services import storage_service as ss

    call_count = {"n": 0}

    orig_copy = ss.LocalStorageService.copy_file

    def _failing_copy(self, src_path, dst_user_id, dst_resource_id, dst_filename):
        call_count["n"] += 1
        if call_count["n"] == n:
            raise RuntimeError(f"模擬第 {n} 份複製失敗")
        return orig_copy(self, src_path, dst_user_id, dst_resource_id, dst_filename)

    context.memo["_orig_copy_file"] = orig_copy
    ss.LocalStorageService.copy_file = _failing_copy
