"""Given 步驟 — K-RE-01 章節級讀前定錨 BDD setup."""

import uuid

from behave import given

from app.models.historical_exam import HistoricalExam
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType
from app.models.scaffold_node_link import ScaffoldNodeLink
from app.models.subject import Subject, SubjectCategory
from app.models.user import SubscriptionPlan, User, UserRole, UserStatus


# ── 用戶建立 helpers ──────────────────────────────────────────────────────────

def _ensure_user(db, email: str, role=UserRole.USER, plan=SubscriptionPlan.PRO) -> str:
    """建立或取得用戶，回傳 user_id 字串。"""
    user = db.query(User).filter_by(email=email).first()
    if user is None:
        user = User(
            email=email,
            password_hash="test-hash",
            subscription_plan=plan,
            role=role,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
    return str(user.id)


@given('已存在 SUPER_ADMIN 用戶 "{email}"')
def step_super_admin_exists(context, email):
    """建立或確保 SUPER_ADMIN 用戶存在。"""
    db = context.db_session
    user_id = _ensure_user(db, email, role=UserRole.SUPER_ADMIN, plan=SubscriptionPlan.PRO)
    db.commit()
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids[email] = user_id


# ── 科目 + 知識樹 + 考古題 setup ─────────────────────────────────────────────

def _ensure_category(db) -> uuid.UUID:
    cat = db.query(SubjectCategory).filter_by(name="Chapter-Anchor-Test").first()
    if cat is None:
        cat = SubjectCategory(name="Chapter-Anchor-Test")
        db.add(cat)
        db.flush()
    return cat.id


def _create_subject_with_nodes_and_questions(db, subject_name: str) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    """建立科目 + depth=1 章節 + depth=2 節點 + 歷史考古題。

    Returns:
        (subject_id, chapter_node_id, leaf_node_id)
    """
    cat_id = _ensure_category(db)

    # 科目
    subj = db.query(Subject).filter_by(name=subject_name).first()
    if subj is None:
        subj = Subject(
            name=subject_name,
            category_id=cat_id,
            exam_subject_codes=[f"TEST:test_{subject_name.replace(' ', '_').lower()}"],
        )
        db.add(subj)
        db.flush()
    sid = subj.id

    # depth=1 章節
    chapter = db.query(KnowledgeNode).filter_by(
        subject_id=sid, depth=1, name="機器學習核心技術"
    ).first()
    if chapter is None:
        chapter = KnowledgeNode(
            subject_id=sid,
            name="機器學習核心技術",
            depth=1,
            sort_order=1,
        )
        db.add(chapter)
        db.flush()

    # depth=2 子節點
    leaf = db.query(KnowledgeNode).filter_by(
        subject_id=sid, parent_id=chapter.id, name="監督式學習"
    ).first()
    if leaf is None:
        leaf = KnowledgeNode(
            subject_id=sid,
            parent_id=chapter.id,
            name="監督式學習",
            depth=2,
            sort_order=1,
        )
        db.add(leaf)
        db.flush()

    # 歷史考試 + 題目
    he = db.query(HistoricalExam).filter_by(
        exam_code="TEST",
        subject_code=f"test_{subject_name.replace(' ', '_').lower()}",
    ).first()
    if he is None:
        he = HistoricalExam(
            exam_name=f"{subject_name}測試考古題",
            exam_code="TEST",
            subject_code=f"test_{subject_name.replace(' ', '_').lower()}",
            subject_name=subject_name,
            year=2024,
        )
        db.add(he)
        db.flush()

    # 至少 1 題含節點名稱的考古題
    q = db.query(Question).filter_by(historical_exam_id=he.id).first()
    if q is None:
        q = Question(
            content="下列關於監督式學習的敘述，何者正確？",
            historical_exam_id=he.id,
            question_number=1,
            correct_answer="A",
        )
        db.add(q)
        db.flush()

    db.commit()
    return sid, chapter.id, leaf.id


@given('已存在逆向工程科目 "AI規劃師" 含 depth=1 章節與 depth=2 節點及考古題')
def step_re_subject_with_tree_and_questions(context):
    """建立 AI規劃師 科目含完整知識樹 + 考古題。"""
    db = context.db_session
    if not hasattr(context, "ids"):
        context.ids = {}
    if not hasattr(context, "memo"):
        context.memo = {}

    sid, chapter_id, leaf_id = _create_subject_with_nodes_and_questions(db, "AI規劃師")
    context.memo["subject_id"] = str(sid)
    context.memo["chapter_id"] = str(chapter_id)
    context.memo["leaf_node_id"] = str(leaf_id)


@given('另存在逆向工程科目 "B科目" 含章節與考古題')
def step_re_subject_b(context):
    """建立科目 B。"""
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}
    sid, chapter_id, leaf_id = _create_subject_with_nodes_and_questions(db, "B科目")
    context.memo["subject_b_id"] = str(sid)


@given('章節 "機器學習核心技術" 已有 template_code=\'K-RE-01\' 的 advance_organizer')
def step_chapter_already_has_k_re_01(context):
    """預先建立 K-RE-01 advance_organizer scaffold 供冪等測試。"""
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    chapter_id = context.memo.get("chapter_id")
    if not chapter_id:
        return

    chapter = db.query(KnowledgeNode).filter_by(id=uuid.UUID(chapter_id)).first()
    if not chapter:
        return

    # 先確認是否已存在
    existing = (
        db.query(ResourceScaffold)
        .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
        .filter(
            ScaffoldNodeLink.node_id == chapter.id,
            ResourceScaffold.type == ResourceScaffoldType.ADVANCE_ORGANIZER.value,
            ResourceScaffold.template_code == "K-RE-01",
        )
        .first()
    )
    if existing:
        context.memo["pre_existing_scaffold_id"] = str(existing.id)
        return

    scaffold = ResourceScaffold(
        resource_id=None,
        type=ResourceScaffoldType.ADVANCE_ORGANIZER.value,
        content="💡 想想：這是預先存在的定錨。這章學：機器學習三大範式。",
        chapter_heading="機器學習核心技術",
        template_code="K-RE-01",
        tenant_id=chapter.tenant_id,
        trust_level="SYSTEM_GENERATED",
        is_orphan_fill=False,
    )
    db.add(scaffold)
    db.flush()

    link = ScaffoldNodeLink(
        scaffold_id=scaffold.id,
        node_id=chapter.id,
        similarity=1.0,
        link_method="chapter_anchor",
    )
    db.add(link)
    db.commit()
    context.memo["pre_existing_scaffold_id"] = str(scaffold.id)


@given('逆向工程科目含章節 "無題目章節" 無對應考古題')
def step_chapter_with_no_questions(context):
    """建立一個無對應考古題的章節。"""
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    sid_str = context.memo.get("subject_id")
    if not sid_str:
        return

    sid = uuid.UUID(sid_str)
    existing = db.query(KnowledgeNode).filter_by(
        subject_id=sid, depth=1, name="無題目章節"
    ).first()
    if existing is None:
        node = KnowledgeNode(
            subject_id=sid,
            name="無題目章節",
            depth=1,
            sort_order=99,
        )
        db.add(node)
        db.commit()


@given('章節 "機器學習核心技術" 有子節點 "監督式學習"')
def step_chapter_has_child_node(context):
    """確認子節點存在（已由 Background 建立，此為語意確認）。"""
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}
    chapter_id = context.memo.get("chapter_id")
    if chapter_id:
        leaf = db.query(KnowledgeNode).filter_by(
            parent_id=uuid.UUID(chapter_id), name="監督式學習"
        ).first()
        if leaf:
            context.memo["leaf_node_id"] = str(leaf.id)


@given('科目 "AI規劃師" 已生成 advance_organizer scaffold')
def step_subject_a_has_anchor(context):
    """記錄 AI規劃師 當前 advance_organizer scaffold 數量，供後續比較。"""
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}
    sid_str = context.memo.get("subject_id")
    if not sid_str:
        context.memo["subject_a_scaffold_count_before"] = 0
        return
    sid = uuid.UUID(sid_str)
    # 計算已存在的 advance_organizer 數
    count = (
        db.query(ResourceScaffold)
        .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
        .join(KnowledgeNode, KnowledgeNode.id == ScaffoldNodeLink.node_id)
        .filter(
            KnowledgeNode.subject_id == sid,
            ResourceScaffold.type == ResourceScaffoldType.ADVANCE_ORGANIZER.value,
            ResourceScaffold.template_code == "K-RE-01",
        )
        .count()
    )
    context.memo["subject_a_scaffold_count_before"] = count


@given('已對該科目成功觸發 K-RE-01 生成')
def step_trigger_k_re_01_via_service(context):
    """直接呼叫 service 生成（繞過 LLM，注入 mock content）。"""
    from unittest.mock import patch
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    sid_str = context.memo.get("subject_id")
    if not sid_str:
        return

    chapter_id = context.memo.get("chapter_id")
    if not chapter_id:
        return

    chapter = db.query(KnowledgeNode).filter_by(id=uuid.UUID(chapter_id)).first()
    if not chapter:
        return

    # 確認是否已有 K-RE-01 scaffold
    existing = (
        db.query(ResourceScaffold)
        .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
        .filter(
            ScaffoldNodeLink.node_id == chapter.id,
            ResourceScaffold.type == ResourceScaffoldType.ADVANCE_ORGANIZER.value,
            ResourceScaffold.template_code == "K-RE-01",
        )
        .first()
    )
    if existing:
        return  # 已存在，跳過

    # 直接寫入（不打 LLM）
    scaffold = ResourceScaffold(
        resource_id=None,
        type=ResourceScaffoldType.ADVANCE_ORGANIZER.value,
        content="💡 想想：不同老師教法不同，AI 學習也是。這章學：監督/非監督/強化三大範式。",
        chapter_heading=chapter.name,
        template_code="K-RE-01",
        tenant_id=chapter.tenant_id,
        trust_level="SYSTEM_GENERATED",
        is_orphan_fill=False,
    )
    db.add(scaffold)
    db.flush()

    # 掛到 chapter + leaf
    for nid_str in [chapter_id, context.memo.get("leaf_node_id", "")]:
        if not nid_str:
            continue
        try:
            nid = uuid.UUID(nid_str)
        except ValueError:
            continue
        link = ScaffoldNodeLink(
            scaffold_id=scaffold.id,
            node_id=nid,
            similarity=1.0,
            link_method="chapter_anchor",
        )
        db.add(link)

    db.commit()
    context.memo["generated_scaffold_id"] = str(scaffold.id)
