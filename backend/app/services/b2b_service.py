"""B2B 機構管理 Service。"""

import csv
import hashlib
import io
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User, UserRole, SubscriptionPlan, UserStatus
from app.models.institution import Institution
from app.models.student_group import StudentGroup, StudentGroupMember

REQUIRED_CSV_COLUMNS = {"姓名", "電子郵件", "群組"}


class B2BService:
    def __init__(self, db: Session):
        self.db = db

    def _validate_org_admin(self, user_id: str) -> dict[str, Any] | tuple[Any, Institution]:
        """共用的權限驗證，回傳 error dict 或 (user, institution) tuple。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        is_admin = role in ("admin", "super_admin", "ADMIN", "SUPER_ADMIN")

        if plan != "ULTRA" and not is_admin:
            return {"error": True, "status_code": 403, "message": "此功能僅限 ULTRA 方案用戶使用"}

        if role != "org_admin" and not is_admin:
            return {"error": True, "status_code": 403, "message": "您沒有機構管理員權限"}

        institution = self.db.query(Institution).filter_by(admin_user_id=user_uuid).first()
        if not institution:
            return {"error": True, "status_code": 404, "message": "找不到您管理的機構"}

        return (user, institution)

    def get_dashboard(self, user_id: str):
        """取得機構管理後台資訊，包含學員列表。"""
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        # 取得機構下所有群組成員
        members = (
            self.db.query(StudentGroupMember, User, StudentGroup)
            .join(User, StudentGroupMember.user_id == User.id)
            .join(StudentGroup, StudentGroupMember.group_id == StudentGroup.id)
            .filter(StudentGroup.institution_id == institution.id)
            .all()
        )

        students = []
        for member, user, group in members:
            students.append({
                "id": str(user.id),
                "name": user.display_name or user.email.split("@")[0],
                "email": user.email,
                "progress": 0,
                "averageScore": None,
                "trend": "flat",
                "status": "inactive",
                "competencies": [],
                "lastActiveAt": user.last_login_at.isoformat() if user.last_login_at else None,
                "lastActiveLabel": "尚未登入",
                "enrolledSubjectIds": [],
                "group": group.name,
            })

        return {
            "institution_name": institution.name,
            "institution_id": str(institution.id),
            "students": students,
            "total": len(students),
            "classStats": {
                "averageScore": 0,
                "scoreChange": 0,
                "topWeaknesses": [],
            },
        }

    def import_students(self, user_id: str, csv_content: str) -> dict:
        """從 CSV 匯入學員名單。

        CSV 格式：姓名,電子郵件,群組
        - 自動建立不存在的群組
        - 自動建立不存在的使用者帳號（FREE 方案、user 角色）
        - 將使用者加入對應群組
        """
        result = self._validate_org_admin(user_id)
        if isinstance(result, dict):
            return result
        _, institution = result

        # 解析 CSV
        try:
            reader = csv.DictReader(io.StringIO(csv_content))
            if not reader.fieldnames:
                return {"error": True, "status_code": 400, "message": "CSV 檔案為空或格式錯誤"}

            headers = {h.strip() for h in reader.fieldnames}
            missing = REQUIRED_CSV_COLUMNS - headers
            if missing:
                return {
                    "error": True,
                    "status_code": 400,
                    "message": f"CSV 缺少必要欄位：{', '.join(missing)}。必要欄位：姓名、電子郵件、群組",
                }

            rows = []
            for i, row in enumerate(reader, start=2):
                name = row.get("姓名", "").strip()
                email = row.get("電子郵件", "").strip().lower()
                group_name = row.get("群組", "").strip()
                if not name or not email or not group_name:
                    return {
                        "error": True,
                        "status_code": 400,
                        "message": f"第 {i} 行資料不完整：姓名、電子郵件、群組皆為必填",
                    }
                rows.append({"name": name, "email": email, "group": group_name})
        except csv.Error:
            return {"error": True, "status_code": 400, "message": "CSV 格式解析失敗"}

        if not rows:
            return {"error": True, "status_code": 400, "message": "CSV 不包含任何資料列"}

        # 建立/取得群組（按機構）
        group_cache: dict[str, StudentGroup] = {}
        existing_groups = self.db.query(StudentGroup).filter_by(institution_id=institution.id).all()
        for g in existing_groups:
            group_cache[g.name] = g

        created_users = 0
        added_members = 0
        skipped = 0

        for row in rows:
            # 確保群組存在
            if row["group"] not in group_cache:
                new_group = StudentGroup(
                    institution_id=institution.id,
                    name=row["group"],
                )
                self.db.add(new_group)
                self.db.flush()
                group_cache[row["group"]] = new_group

            group = group_cache[row["group"]]

            # 確保使用者帳號存在
            user = self.db.query(User).filter_by(email=row["email"]).first()
            if not user:
                default_password = hashlib.sha256(
                    f"{row['email']}:certimate2026".encode()
                ).hexdigest()
                user = User(
                    email=row["email"],
                    display_name=row["name"],
                    password_hash=default_password,
                    subscription_plan=SubscriptionPlan.FREE,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                )
                self.db.add(user)
                self.db.flush()
                created_users += 1

            # 確保不重複加入群組
            existing_member = (
                self.db.query(StudentGroupMember)
                .filter_by(group_id=group.id, user_id=user.id)
                .first()
            )
            if existing_member:
                skipped += 1
                continue

            member = StudentGroupMember(group_id=group.id, user_id=user.id)
            self.db.add(member)
            added_members += 1

        self.db.commit()

        return {
            "total_rows": len(rows),
            "created_users": created_users,
            "added_members": added_members,
            "skipped_duplicates": skipped,
            "groups": list(group_cache.keys()),
        }
