#!/usr/bin/env python3
"""Seed B2B 教育平台 demo 資料.

建立一個示範機構 + 老師帳號 + 學生群組 + 學生帳號，供 /edu-console 頁面開發使用。

使用方式：
    .venv/bin/python -m app.scripts.seed_edu_demo
"""

import hashlib
import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings, PUBLIC_B2C_TENANT_ID
from app.models.user import User, UserStatus, UserRole, SubscriptionPlan
from app.models.institution import Institution
from app.models.student_group import StudentGroup, StudentGroupMember
from app.models.exam import Exam, ExamStatus
from app.models.question import Question
from app.models.answer import Answer
from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource, ResourceStatus

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

TEACHER_EMAIL = "teacher@edu-demo.com"
INSTITUTION_NAME = "TiTi 示範補習班"
STUDENT_EMAILS = [
    "student01@edu-demo.com",
    "student02@edu-demo.com",
    "student03@edu-demo.com",
    "student04@edu-demo.com",
    "student05@edu-demo.com",
]
STUDENT_NAMES = ["王小明", "李美玲", "張大偉", "陳雅婷", "林志豪"]


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def main():
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Skip if already seeded
        existing = db.query(User).filter(User.email == TEACHER_EMAIL).first()
        if existing:
            log.info(f"已存在 {TEACHER_EMAIL}，跳過 seed")
            return

        # 1. 建立老師帳號（先建帳號再建機構，因為 institution 需要 admin_user_id）
        teacher_id = uuid.uuid4()
        teacher = User(
            id=teacher_id,
            email=TEACHER_EMAIL,
            password_hash=_hash("teacher123"),
            display_name="Demo 老師",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            subscription_plan=SubscriptionPlan.PRO,
        )
        db.add(teacher)
        db.flush()
        log.info(f"✓ 老師: {TEACHER_EMAIL} / teacher123")

        # 2. 建立機構
        inst_id = uuid.uuid4()
        institution = Institution(
            id=inst_id,
            name=INSTITUTION_NAME,
            admin_user_id=teacher_id,
        )
        db.add(institution)
        db.flush()
        log.info(f"✓ 機構: {INSTITUTION_NAME}")

        # institution_id 不在 User model 上（透過 student_group 關聯）
        db.add(teacher)
        log.info(f"✓ 老師: {TEACHER_EMAIL} / teacher123")

        # 3. 建立學生群組
        group_id = uuid.uuid4()
        group = StudentGroup(
            id=group_id,
            name="114 年金融證照班",
            institution_id=inst_id,
        )
        db.add(group)
        log.info(f"✓ 群組: 114 年金融證照班")

        # 4. 建立學生帳號
        student_ids = []
        for i, (email, name) in enumerate(zip(STUDENT_EMAILS, STUDENT_NAMES)):
            sid = uuid.uuid4()
            student = User(
                id=sid,
                email=email,
                password_hash=_hash("student123"),
                display_name=name,
                role=UserRole.STUDENT,
                status=UserStatus.ACTIVE,
                subscription_plan=SubscriptionPlan.FREE,
            )
            db.add(student)
            student_ids.append(sid)
            log.info(f"  ✓ 學生: {name} ({email})")

        # Flush students first (FK dependency)
        db.flush()

        # 4b. 加入群組
        for sid in student_ids:
            member = StudentGroupMember(
                id=uuid.uuid4(),
                group_id=group_id,
                user_id=sid,
            )
            db.add(member)
        db.flush()

        # 5. 建立示範資源 + 知識節點
        resource_id = uuid.uuid4()
        # Need a subject for the resource
        from app.models.subject import Subject, SubjectCategory
        cat = db.query(SubjectCategory).first()
        if not cat:
            cat = SubjectCategory(id=uuid.uuid4(), name="金融證照")
            db.add(cat)
            db.flush()
        subj = db.query(Subject).first()
        if not subj:
            subj = Subject(id=uuid.uuid4(), category_id=cat.id, name="金融市場常識", code="FIN_MARKET")
            db.add(subj)
            db.flush()

        resource = Resource(
            id=resource_id,
            user_id=teacher_id,
            subject_id=subj.id,
            name="金融市場常識講義.pdf",
            type="pdf",
            status=ResourceStatus.COMPLETED,
            tenant_id=PUBLIC_B2C_TENANT_ID,
        )
        db.add(resource)
        db.flush()

        node_names = ["金融市場概論", "股票市場", "債券市場", "衍生性商品", "風險管理"]
        node_ids = []
        for j, node_name in enumerate(node_names):
            nid = uuid.uuid4()
            node = KnowledgeNode(
                id=nid,
                resource_id=resource_id,
                name=node_name,
                depth=1,
                sort_order=j,
                source_text=f"{node_name}的相關知識內容...",
                tenant_id=PUBLIC_B2C_TENANT_ID,
            )
            db.add(node)
            node_ids.append(nid)
        db.flush()

        # 6. 為每位學生建立示範考試 + 作答（分層 flush 避免 FK 衝突）
        import random

        # 6a. 先建立所有考試
        exam_ids = {}
        for sid, name in zip(student_ids, STUDENT_NAMES):
            eid = uuid.uuid4()
            exam = Exam(
                id=eid,
                user_id=sid,
                subject_id=subj.id,
                status=ExamStatus.SUBMITTED,
                total_questions=10,
                duration_minutes=30,
                score=random.randint(50, 95),
                correct_count=random.randint(5, 9),
                tenant_id=PUBLIC_B2C_TENANT_ID,
            )
            db.add(exam)
            exam_ids[sid] = eid
        db.flush()

        # 6b. 建立題目
        question_map = {}  # (exam_id, q_num) -> (q_id, correct_answer)
        for sid in student_ids:
            eid = exam_ids[sid]
            for q_num in range(1, 11):
                q_id = uuid.uuid4()
                correct_ans = random.choice(["A", "B", "C", "D"])
                q = Question(
                    id=q_id,
                    exam_id=eid,
                    question_number=q_num,
                    content=f"示範題目 {q_num}：關於{random.choice(node_names)}的問題",
                    option_a="選項 A", option_b="選項 B",
                    option_c="選項 C", option_d="選項 D",
                    correct_answer=correct_ans,
                    source_type="ai_generated",
                    tenant_id=PUBLIC_B2C_TENANT_ID,
                )
                db.add(q)
                question_map[(eid, q_num)] = (q_id, correct_ans)
        db.flush()

        # 6c. 建立作答
        for sid in student_ids:
            eid = exam_ids[sid]
            for q_num in range(1, 11):
                q_id, correct_ans = question_map[(eid, q_num)]
                selected = random.choice(["A", "B", "C", "D"])
                answer = Answer(
                    id=uuid.uuid4(),
                    exam_id=eid,
                    question_id=q_id,
                    user_id=sid,
                    selected_answer=selected,
                    is_correct=(selected == correct_ans),
                    confidence=random.choice(["confident", "somewhat", "guessing"]),
                    tenant_id=PUBLIC_B2C_TENANT_ID,
                )
                db.add(answer)

        db.commit()
        log.info(f"\n✅ B2B Demo 資料建立完成！")
        log.info(f"  老師登入: {TEACHER_EMAIL} / teacher123")
        log.info(f"  學生登入: student01@edu-demo.com / student123")
        log.info(f"  機構: {INSTITUTION_NAME}")
        log.info(f"  群組: 114 年金融證照班 ({len(STUDENT_NAMES)} 名學生)")

    except Exception as e:
        db.rollback()
        log.error(f"Seed 失敗: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
