#!/usr/bin/env python3
"""擴充 B2B 教育平台豐富 mock 資料.

在 seed_edu_demo 基礎上增加：
- 多個學生群組（不同科目）
- 每位學生多場考試（有進步趨勢）
- 學習歷程 + 知識節點掌握度
- 錯題記錄 + 信心度
- 週報資料

使用方式：
    .venv/bin/python -m app.scripts.seed_edu_rich
"""

import hashlib
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings, PUBLIC_B2C_TENANT_ID
from app.models.user import User, UserStatus, UserRole, SubscriptionPlan
from app.models.institution import Institution
from app.models.student_group import StudentGroup, StudentGroupMember
from app.models.exam import Exam, ExamStatus
from app.models.question import Question
from app.models.answer import Answer
from app.models.subject import Subject, SubjectCategory
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.resource import Resource, ResourceStatus

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

TEACHER_EMAIL = "teacher@edu-demo.com"


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def main():
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        teacher = db.query(User).filter(User.email == TEACHER_EMAIL).first()
        if not teacher:
            log.error("請先執行 seed_edu_demo: .venv/bin/python -m app.scripts.seed_edu_demo")
            return

        inst = db.query(Institution).filter(Institution.admin_user_id == teacher.id).first()
        if not inst:
            log.error("找不到機構")
            return

        log.info(f"機構: {inst.name} (老師: {teacher.email})")

        # 取得 subject
        subj = db.query(Subject).first()
        if not subj:
            cat = SubjectCategory(id=uuid.uuid4(), name="金融證照")
            db.add(cat)
            db.flush()
            subj = Subject(id=uuid.uuid4(), category_id=cat.id, name="金融市場常識", code="FIN_MARKET")
            db.add(subj)
            db.flush()

        # ── 新增第二個群組 ──────────────────────────────────────
        existing_groups = db.query(StudentGroup).filter(StudentGroup.institution_id == inst.id).count()
        if existing_groups < 2:
            group2_id = uuid.uuid4()
            group2 = StudentGroup(id=group2_id, name="113 年不動產經紀人班", institution_id=inst.id)
            db.add(group2)
            db.flush()

            # 新增 3 位學生到第二組
            new_students = [
                ("student06@edu-demo.com", "黃建宏"),
                ("student07@edu-demo.com", "吳佳穎"),
                ("student08@edu-demo.com", "鄭心怡"),
            ]
            for email, name in new_students:
                if db.query(User).filter(User.email == email).first():
                    continue
                sid = uuid.uuid4()
                s = User(id=sid, email=email, password_hash=_hash("student123"),
                         display_name=name, role=UserRole.STUDENT,
                         status=UserStatus.ACTIVE, subscription_plan=SubscriptionPlan.FREE)
                db.add(s)
                db.flush()
                db.add(StudentGroupMember(id=uuid.uuid4(), group_id=group2_id, user_id=sid))
            db.flush()
            log.info("✓ 新增群組: 113 年不動產經紀人班 (3 名學生)")

        # ── 為所有學生建立多場考試（模擬進步趨勢）──────────────
        students = db.query(User).filter(User.role == UserRole.STUDENT, User.email.like("%edu-demo.com")).all()
        log.info(f"找到 {len(students)} 名學生")

        node_names = ["金融市場概論", "股票市場", "債券市場", "衍生性商品", "風險管理",
                      "投資組合", "財務報表分析", "經濟學基礎"]

        # 確保知識節點存在
        resource = db.query(Resource).filter(Resource.user_id == teacher.id).first()
        if not resource:
            resource = Resource(id=uuid.uuid4(), user_id=teacher.id, subject_id=subj.id,
                                name="金融市場常識講義.pdf", type="pdf",
                                status=ResourceStatus.COMPLETED, tenant_id=PUBLIC_B2C_TENANT_ID)
            db.add(resource)
            db.flush()

        existing_nodes = db.query(KnowledgeNode).filter(KnowledgeNode.resource_id == resource.id).all()
        node_map = {n.name: n for n in existing_nodes}

        for i, name in enumerate(node_names):
            if name not in node_map:
                nid = uuid.uuid4()
                node = KnowledgeNode(id=nid, resource_id=resource.id, name=name,
                                     depth=1, sort_order=i,
                                     source_text=f"{name}的相關知識內容...",
                                     available_questions=random.randint(10, 30),
                                     tenant_id=PUBLIC_B2C_TENANT_ID)
                db.add(node)
                node_map[name] = node
        db.flush()

        now = datetime.now(timezone.utc)

        for student in students:
            # 檢查此學生是否已有多場考試
            exam_count = db.query(Exam).filter(Exam.user_id == student.id).count()
            if exam_count >= 4:
                continue

            # 建立 4 場考試（4 週，分數遞增模擬進步）
            base_score = random.randint(40, 55)
            for week in range(4):
                exam_date = now - timedelta(weeks=3 - week)
                score = min(95, base_score + week * random.randint(5, 12))
                correct = int(score / 10)

                eid = uuid.uuid4()
                exam = Exam(
                    id=eid, user_id=student.id, subject_id=subj.id,
                    status=ExamStatus.SUBMITTED, total_questions=10,
                    duration_minutes=30, score=score, correct_count=correct,
                    submitted_at=exam_date, tenant_id=PUBLIC_B2C_TENANT_ID,
                )
                db.add(exam)
                db.flush()

                # 建立題目
                q_data = []
                for q_num in range(1, 11):
                    q_id = uuid.uuid4()
                    node_name = random.choice(node_names)
                    correct_ans = random.choice(["A", "B", "C", "D"])
                    q = Question(
                        id=q_id, exam_id=eid, question_number=q_num,
                        content=f"第{week+1}週模擬考 Q{q_num}：關於{node_name}的問題",
                        option_a="選項 A", option_b="選項 B",
                        option_c="選項 C", option_d="選項 D",
                        correct_answer=correct_ans, source_type="ai_generated",
                        tenant_id=PUBLIC_B2C_TENANT_ID,
                    )
                    db.add(q)
                    q_data.append((q_id, correct_ans))

                db.flush()  # Questions must exist before answers

                # 建立答案
                for q_id, correct_ans in q_data:
                    if random.random() < (0.4 + week * 0.15):
                        selected = correct_ans
                    else:
                        selected = random.choice([x for x in ["A", "B", "C", "D"] if x != correct_ans])

                    confidence = random.choices(
                        ["confident", "somewhat", "guessing"],
                        weights=[0.3 + week * 0.1, 0.4, 0.3 - week * 0.1]
                    )[0]

                    answer = Answer(
                        id=uuid.uuid4(), exam_id=eid, question_id=q_id,
                        user_id=student.id, selected_answer=selected,
                        is_correct=(selected == correct_ans),
                        confidence=confidence, tenant_id=PUBLIC_B2C_TENANT_ID,
                    )
                    db.add(answer)

            # ── 建立知識掌握度 ──────────────────────────────────
            for name, node in node_map.items():
                existing = db.query(NodeMastery).filter(
                    NodeMastery.user_id == student.id, NodeMastery.node_id == node.id
                ).first()
                if not existing:
                    total = random.randint(5, 30)
                    correct = min(total, random.randint(3, 25))
                    rate = round(correct / total, 2)
                    color = "green" if rate >= 0.7 else "yellow" if rate >= 0.4 else "red"
                    mastery = NodeMastery(
                        id=uuid.uuid4(), user_id=student.id, node_id=node.id,
                        mastery_rate=rate, total_count=total,
                        correct_count=correct, color=color,
                    )
                    db.add(mastery)

            log.info(f"  ✓ {student.display_name}: 4 場考試 + {len(node_map)} 個知識掌握度")

        db.commit()
        log.info(f"\n✅ 教育平台豐富資料建立完成！")
        log.info(f"  群組數: {db.query(StudentGroup).filter(StudentGroup.institution_id == inst.id).count()}")
        log.info(f"  學生數: {len(students)}")
        log.info(f"  考試總數: {db.query(Exam).filter(Exam.user_id.in_([s.id for s in students])).count()}")

    except Exception as e:
        db.rollback()
        log.error(f"失敗: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
