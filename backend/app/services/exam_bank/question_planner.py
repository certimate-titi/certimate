"""
TiTi 出題規劃器 — 四層 Pipeline 核心模組

依據 exam-generation-spec.md v2.0 設計：
  Layer -1: 模式判定（衝刺/標準/精熟）
  Layer  0: 弱點 + 記憶 + 信心度 綜合分析
  Layer  1: 配比計算（模式 × 弱點 × 難度 × Bloom）
  Layer  2: 混合出題計畫 + 交錯排列

純邏輯模組 — 不含 DB 查詢，所有資料由呼叫方注入。
"""

from __future__ import annotations

import random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


# ── 資料結構 ──────────────────────────────────────────────

@dataclass
class NodeProfile:
    """每個知識節點的完整 profile（由呼叫方從 DB 查詢後注入）"""
    node_id: str
    name: str
    # 掌握度（from node_mastery）
    mastery_rate: Optional[float] = None   # 0-100, None=未測
    mastery_color: str = "gray"            # green/orange/red/gray
    # SM-2（from question_stats）
    ease_factor: float = 2.5
    next_review_date: Optional[date] = None
    success_count: int = 0
    fail_count: int = 0
    # 信心度（from answers 統計）
    dangerous_blindspot_count: int = 0     # confident + wrong 次數
    lucky_guess_count: int = 0             # guessing + correct 次數
    # 考古題
    historical_count: int = 0              # 該節點可用考古題數
    # 配額（由 Planner 計算填入）
    weight: float = 0.0
    quota: int = 0
    difficulty_dist: dict = field(default_factory=dict)
    bloom_target: dict = field(default_factory=dict)


@dataclass
class PlanResult:
    """QuestionPlanner 的輸出"""
    mode: str                              # sprint / standard / mastery
    mode_reason: str
    total_questions: int
    # 每節點的出題計畫
    node_plans: list[NodePlan] = field(default_factory=list)
    # 錯題穿插（衝刺模式）
    wrong_review_count: int = 0
    # 全局 Bloom 統計
    bloom_summary: dict = field(default_factory=dict)


@dataclass
class NodePlan:
    """單一節點的出題計畫"""
    node_id: str
    name: str
    mastery_color: str
    quota: int                             # 該節點應出幾題
    historical_count: int                  # 其中考古題幾題
    ai_count: int                          # 其中 AI 生成幾題
    difficulty_dist: dict                  # {easy: N, medium: N, hard: N}
    bloom_target: dict                     # {remember: N, understand: N, ...}


# ── 常數 ──────────────────────────────────────────────

MODE_CONFIG = {
    "sprint": {
        "label": "🔥 衝刺模式",
        "wrong_ratio": 0.50,               # 50% 錯題
        "weakness_influence": 0.8,
        "bloom_bias": {
            "remember": 30, "understand": 15, "apply": 30,
            "analyze": 15, "evaluate": 5, "create": 5,
        },
    },
    "standard": {
        "label": "📚 標準模式",
        "wrong_ratio": 0.10,               # 10% 錯題穿插
        "weakness_influence": 0.6,
        "bloom_bias": {
            "remember": 20, "understand": 20, "apply": 25,
            "analyze": 20, "evaluate": 10, "create": 5,
        },
    },
    "mastery": {
        "label": "🧠 精熟模式",
        "wrong_ratio": 0.0,                # 不抽錯題，改抽 SM-2 到期
        "review_ratio": 0.70,              # 70% 遺忘邊緣
        "weakness_influence": 0.4,
        "bloom_bias": {
            "remember": 5, "understand": 10, "apply": 20,
            "analyze": 25, "evaluate": 25, "create": 15,
        },
    },
}

DIFFICULTY_PRESETS = {
    1: {"easy": 60, "medium": 30, "hard": 10},
    2: {"easy": 30, "medium": 50, "hard": 20},
    3: {"easy": 10, "medium": 30, "hard": 60},
}

WEAKNESS_DIFFICULTY = {
    "red":    {"easy": 50, "medium": 40, "hard": 10},
    "orange": {"easy": 20, "medium": 50, "hard": 30},
    "green":  {"easy": 10, "medium": 30, "hard": 60},
}

WEAKNESS_BLOOM = {
    "red":    {"remember": 40, "understand": 30, "apply": 20, "analyze": 10, "evaluate": 0, "create": 0},
    "orange": {"remember": 20, "understand": 20, "apply": 25, "analyze": 20, "evaluate": 10, "create": 5},
    "green":  {"remember": 0, "understand": 10, "apply": 20, "analyze": 25, "evaluate": 25, "create": 20},
}

HISTORICAL_RATIO = 0.20  # 20% 考古題（標準）
ULTRA_HISTORICAL_RATIO = 0.60  # 60% 考古題（ULTRA 優先召回）


# ── QuestionPlanner ──────────────────────────────────────

class QuestionPlanner:
    """四層出題規劃器"""

    def plan(
        self,
        nodes: list[NodeProfile],
        total_q: int,
        user_difficulty: int = 2,          # 1/2/3
        exam_date: Optional[date] = None,
        wrong_answer_count: int = 0,       # 使用者累計錯題數
        custom_bloom_ratio: Optional[dict] = None,  # ULTRA: 自訂 Bloom 比例 {remember:20, ...}
        historical_priority: bool = False,  # ULTRA: 考古題優先召回
    ) -> PlanResult:
        """執行完整四層 Pipeline，回傳出題計畫"""

        # Layer -1: 模式判定
        mode, mode_reason = self._determine_mode(exam_date)
        mode_cfg = MODE_CONFIG[mode]

        # Layer 0: 弱點 + 記憶 + 信心度 綜合分析
        self._analyze_weakness(nodes)

        # 計算錯題穿插數量
        wrong_count = 0
        if mode == "sprint":
            wrong_count = min(
                round(total_q * mode_cfg["wrong_ratio"]),
                wrong_answer_count,
            )
        elif mode == "standard":
            wrong_count = min(
                round(total_q * mode_cfg["wrong_ratio"]),
                wrong_answer_count,
            )

        new_count = total_q - wrong_count

        # Layer 1: 配比計算
        self._allocate_quota(nodes, new_count, user_difficulty, mode_cfg, custom_bloom_ratio)

        # Layer 2: 混合出題計畫 + Bloom 分配
        node_plans = []
        bloom_totals = defaultdict(int)

        hist_ratio = ULTRA_HISTORICAL_RATIO if historical_priority else HISTORICAL_RATIO

        for node in nodes:
            if node.quota <= 0:
                continue

            hist_target = max(1, round(node.quota * hist_ratio))
            hist_actual = min(hist_target, node.historical_count)
            ai_count = node.quota - hist_actual

            # 難度分配（實際題數）
            diff_counts = self._distribute_counts(node.quota, node.difficulty_dist)

            # Bloom 分配（實際題數）
            bloom_counts = self._distribute_counts(node.quota, node.bloom_target)
            for bk, bv in bloom_counts.items():
                bloom_totals[bk] += bv

            node_plans.append(NodePlan(
                node_id=node.node_id,
                name=node.name,
                mastery_color=node.mastery_color,
                quota=node.quota,
                historical_count=hist_actual,
                ai_count=ai_count,
                difficulty_dist=diff_counts,
                bloom_target=bloom_counts,
            ))

        return PlanResult(
            mode=mode,
            mode_reason=mode_reason,
            total_questions=total_q,
            node_plans=node_plans,
            wrong_review_count=wrong_count,
            bloom_summary=dict(bloom_totals),
        )

    # ── Layer -1: 模式判定 ──

    def _determine_mode(self, exam_date: Optional[date]) -> tuple[str, str]:
        if exam_date is None:
            return "mastery", "無考試日期，使用廣讀模式"
        days_left = (exam_date - date.today()).days
        if days_left <= 7:
            return "final", f"距考 {days_left} 天（≤ 7 天），自動使用最後衝刺模式"
        if days_left <= 30:
            return "sprint", f"距考 {days_left} 天（8-30 天），自動使用衝刺模式"
        if days_left <= 180:
            return "standard", f"距考 {days_left} 天（31-180 天），自動使用標準模式"
        return "mastery", f"距考 {days_left} 天（> 6 月），使用廣讀模式"

    # ── Layer 0: 弱點 + 記憶 + 信心度 ──

    def _analyze_weakness(self, nodes: list[NodeProfile]):
        for node in nodes:
            # 維度 1: 掌握度
            if node.mastery_rate is None or node.mastery_color == "gray":
                weakness = 0.5
            elif node.mastery_rate < 60:
                weakness = 0.8
            elif node.mastery_rate < 80:
                weakness = 0.5
            else:
                weakness = 0.2

            # 維度 2: SM-2 記憶緊迫度
            memory_urgency = 0.0
            if node.ease_factor < 2.0:
                memory_urgency = 0.3
            elif node.next_review_date and node.next_review_date <= date.today():
                memory_urgency = 0.2

            # 維度 3: 信心度危險盲點
            confidence_weight = min(0.3, node.dangerous_blindspot_count * 0.1)

            node.weight = weakness + memory_urgency + confidence_weight

    # ── Layer 1: 配比計算 ──

    def _allocate_quota(
        self,
        nodes: list[NodeProfile],
        new_count: int,
        user_difficulty: int,
        mode_cfg: dict,
        custom_bloom_ratio: Optional[dict] = None,
    ):
        base_diff = DIFFICULTY_PRESETS.get(user_difficulty, DIFFICULTY_PRESETS[2])
        wi = mode_cfg["weakness_influence"]
        # ULTRA 自訂 Bloom 比例：若提供則覆蓋 mode_bloom
        mode_bloom = custom_bloom_ratio if custom_bloom_ratio else mode_cfg["bloom_bias"]

        total_weight = sum(n.weight for n in nodes) or 1.0

        # 分配 quota
        assigned = 0
        for i, node in enumerate(nodes):
            if i == len(nodes) - 1:
                node.quota = new_count - assigned  # 最後一個吃剩餘
            else:
                node.quota = max(1, round(new_count * node.weight / total_weight))
            assigned += node.quota

        # 每節點的難度和 Bloom
        for node in nodes:
            # 難度：base × (1-wi) + weakness_adjusted × wi
            wa_diff = WEAKNESS_DIFFICULTY.get(node.mastery_color, base_diff)
            node.difficulty_dist = {
                k: round(base_diff[k] * (1 - wi) + wa_diff[k] * wi)
                for k in ["easy", "medium", "hard"]
            }

            # Bloom：custom_bloom_ratio 直接使用；否則混合弱點 + mode
            if custom_bloom_ratio:
                node.bloom_target = {
                    k: custom_bloom_ratio.get(k, 0)
                    for k in ["remember", "understand", "apply", "analyze", "evaluate", "create"]
                }
            else:
                wa_bloom = WEAKNESS_BLOOM.get(node.mastery_color, mode_bloom)
                node.bloom_target = {
                    k: round(mode_bloom.get(k, 0) * 0.4 + wa_bloom.get(k, 0) * 0.6)
                    for k in ["remember", "understand", "apply", "analyze", "evaluate", "create"]
                }

    # ── Layer 2 輔助：百分比 → 實際題數 ──

    @staticmethod
    def _distribute_counts(total: int, pct_dist: dict) -> dict:
        """將百分比分佈轉為實際題數，確保總和 = total"""
        raw = {k: total * v / 100 for k, v in pct_dist.items()}
        floored = {k: int(v) for k, v in raw.items()}
        remainder = total - sum(floored.values())

        # 將剩餘分配給小數最大的
        fracs = sorted(
            ((k, raw[k] - floored[k]) for k in raw),
            key=lambda x: -x[1],
        )
        for i in range(remainder):
            floored[fracs[i][0]] += 1

        return floored


# ── 交錯排列 + 開局保護（Layer 2 後處理）──────────────

def interleave_questions(questions: list[dict]) -> list[dict]:
    """
    將題目按 node_id 交錯排列（A→B→C→A→B→C）。
    學術依據：Rohrer & Taylor (2007) 交錯練習。
    """
    by_node = defaultdict(deque)
    for q in questions:
        by_node[q.get("node_id", "unknown")].append(q)

    result = []
    node_order = list(by_node.keys())
    while any(by_node.values()):
        for nid in node_order:
            if by_node[nid]:
                result.append(by_node[nid].popleft())
    return result


def difficulty_smooth(questions: list[dict]) -> list[dict]:
    """避免連續 3 題以上相同難度"""
    result = list(questions)
    for i in range(2, len(result)):
        if (result[i].get("difficulty") == result[i-1].get("difficulty") ==
                result[i-2].get("difficulty")):
            # 找後面第一個不同難度的題目交換
            for j in range(i + 1, len(result)):
                if result[j].get("difficulty") != result[i].get("difficulty"):
                    result[i], result[j] = result[j], result[i]
                    break
    return result


def ensure_easy_opening(questions: list[dict], min_easy: int = 1, first_n: int = 3) -> list[dict]:
    """前 N 題保證至少 min_easy 題 easy，建立正向開局"""
    result = list(questions)
    easy_in_first = sum(1 for q in result[:first_n] if q.get("difficulty") == "easy")

    if easy_in_first < min_easy:
        # 從後面找 easy 題換到前面
        for i in range(first_n, len(result)):
            if result[i].get("difficulty") == "easy":
                # 換到 first_n 內的第一個非 easy 位置
                for j in range(first_n):
                    if result[j].get("difficulty") != "easy":
                        result[i], result[j] = result[j], result[i]
                        easy_in_first += 1
                        break
            if easy_in_first >= min_easy:
                break
    return result


def renumber_questions(questions: list[dict]) -> list[dict]:
    """重新編號 question_number = 1..N"""
    for i, q in enumerate(questions):
        q["question_number"] = i + 1
    return questions


def post_process_questions(questions: list[dict]) -> list[dict]:
    """完整的 Layer 2 後處理 Pipeline"""
    result = interleave_questions(questions)
    result = difficulty_smooth(result)
    result = ensure_easy_opening(result)
    result = renumber_questions(result)
    return result
