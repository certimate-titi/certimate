"""EncouragementService — 根據觸發情境生成鼓勵語句（F-01 接線）。"""

import json
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_FALLBACK_SYSTEM = """你是 TiTi 學習教練 Certi。根據以下觸發情境與學習狀態，生成一段溫暖的鼓勵訊息。

語調規則：
- 絕不使用「不及格」「失敗」「退步」「差」等負面詞彙
- 可使用表情符號增添溫度
- 每次回覆應有變化，避免重複相同句型

情境語調指南：
- pre_exam_cheer：自信、輕鬆
- post_exam_celebrate：興奮、驕傲、具體指出進步
- post_exam_comfort：同理、溫暖
- inactivity_care：溫柔邀請
- streak_break：「休息也是學習的一部分」
- achievement_unlock：慶祝
- milestone_reached：恭喜

長度：最多 100 字。"""


class EncouragementService:
    """Encouragement Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db
        self._llm = None
        self._prompt_svc = None

    def _get_llm(self):
        """取得 llm。"""
        if self._llm is None:
            from app.core.config import get_settings
            settings = get_settings()
            if settings.GEMINI_API_KEY or settings.ANTHROPIC_API_KEY or settings.OPENAI_API_KEY:
                from app.services.llm_service import LLMService
                self._llm = LLMService(db=self.db)
        return self._llm

    def _load_prompt(self, name: str, variables: dict | None = None) -> dict | None:
        """載入 prompt。"""
        if not self._prompt_svc:
            try:
                from app.services.prompt_template_service import PromptTemplateService
                self._prompt_svc = PromptTemplateService(self.db)
            except Exception:
                return None
        try:
            result = self._prompt_svc.get_prompt_for_ai(name)
            if result.get("error"):
                return None
            if variables:
                render = self._prompt_svc.render_prompt
                result["system_prompt"] = render(result["system_prompt"], variables)
                result["user_prompt"] = render(result["user_prompt"], variables)
            return result
        except Exception:
            return None

    def generate(self, trigger_type: str, learning_state: dict) -> str:
        """生成鼓勵語句。

        Args:
            trigger_type: 觸發類型 (pre_exam_cheer, post_exam_celebrate,
                         post_exam_comfort, inactivity_care, streak_break,
                         achievement_unlock, milestone_reached)
            learning_state: 學習狀態 dict (streak_days, last_score, trend, etc.)

        Returns:
            鼓勵語句字串，LLM 失敗時回傳預設語句
        """
        llm = self._get_llm()
        if not llm:
            return self._get_fallback_message(trigger_type)

        state_json = json.dumps(learning_state, ensure_ascii=False)

        db_prompt = self._load_prompt("encouragement", {
            "trigger_type": trigger_type,
            "learning_state": state_json,
        })

        if db_prompt:
            system_prompt = db_prompt["system_prompt"]
            user_prompt = db_prompt["user_prompt"]
        else:
            system_prompt = _FALLBACK_SYSTEM
            user_prompt = f"觸發類型：{trigger_type}\n學習狀態：\n{state_json}"

        try:
            result = llm.generate(
                system_prompt, user_prompt,
                model="gemini-flash", max_tokens=256,
            )
            if result and len(result.strip()) > 5:
                return result.strip()
        except Exception as e:
            logger.warning("F-01 encouragement generation failed: %s", e)

        return self._get_fallback_message(trigger_type)

    @staticmethod
    def _get_fallback_message(trigger_type: str) -> str:
        """LLM 不可用時的預設訊息。"""
        messages = {
            "pre_exam_cheer": "你準備好了！放輕鬆，相信自己的實力 💪",
            "post_exam_celebrate": "太棒了！你的努力有了回報 🎉",
            "post_exam_comfort": "別灰心，每一次練習都讓你更接近目標 🌟",
            "inactivity_care": "好久不見！隨時歡迎回來繼續學習 📚",
            "streak_break": "休息也是學習的一部分，歡迎回來 ☀️",
            "achievement_unlock": "恭喜你解鎖新成就！繼續加油 🏆",
            "milestone_reached": "又完成一個里程碑！你真的很棒 ⭐",
        }
        return messages.get(trigger_type, "繼續加油，你做得很好！💪")
