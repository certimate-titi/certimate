"""共用 helper：從 User 物件產生個人化背景提示字串，供 prompt 模板使用。

設計原則：
- 直接陳述事實（年齡 / 學歷 / 職業），由 LLM 自行調整深度與用詞
- 缺欄位自動省略，不強加假設
- 全部缺值回空字串（避免「使用者背景：未提供」這種雜訊）
"""

from app.models.user import User


def build_user_profile_hint(user: User | None) -> str:
    """產生模板用的「使用者背景」提示字串。

    回傳範例：
        "使用者背景：35 歲、碩士學歷、軟體工程師。請依此調整講解深度與用詞。"
        "使用者背景：22 歲。請依此調整講解深度與用詞。"
        ""（全部缺值）
    """
    if not user:
        return ""

    parts: list[str] = []
    if getattr(user, "age", None):
        parts.append(f"{user.age} 歲")
    if getattr(user, "education", None):
        parts.append(f"{user.education}學歷")
    if getattr(user, "career", None):
        parts.append(f"{user.career}")

    if not parts:
        return ""

    return f"使用者背景：{'、'.join(parts)}。請依此調整講解深度與用詞。"


def build_profile_vars(user: User | None) -> dict[str, str]:
    """產生個別欄位變數（給模板顯式使用）。

    回傳 dict 含三個 key：age / education / career（缺值為空字串）
    + user_background_instruction（合成版，向後相容）
    """
    return {
        "age": str(user.age) if user and getattr(user, "age", None) else "",
        "education": (user.education or "") if user else "",
        "career": (user.career or "") if user else "",
        "user_background_instruction": build_user_profile_hint(user),
    }
