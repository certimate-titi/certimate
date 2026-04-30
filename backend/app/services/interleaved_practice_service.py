"""交錯練習排列服務 — F19 交錯練習演算法。

支援三種排列模式：
- interleaved：交錯排列，避免同節點題目連續（預設，多節點時自動選擇）
- sequential：依難度由易到難排列（單節點時自動選擇）
- grouped：按知識節點分組排列

交錯演算法使用 Round-Robin 策略（Heap-based interleaving），
確保同一節點的題目均勻分散，同時考慮難度分散原則。
"""

from __future__ import annotations

import heapq
from typing import Any

DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}
ORDER_INTERLEAVED = "interleaved"
ORDER_SEQUENTIAL = "sequential"
ORDER_GROUPED = "grouped"

DISPLAY_LABELS = {
    ORDER_INTERLEAVED: "交錯練習",
    ORDER_SEQUENTIAL: "循序漸進",
    ORDER_GROUPED: "集中練習",
}

INTERLEAVED_HINT = "交錯練習有助於長期記憶，持續使用效果更佳"


def determine_order_mode(
    node_ids: list[str],
    explicit_mode: str | None = None,
) -> str:
    """決定排列模式。

    Args:
        node_ids: 選擇的知識節點 ID 清單。
        explicit_mode: 使用者明確指定的模式（"interleaved"/"sequential"/"grouped"/"集中練習"/"交錯練習"）。

    Returns:
        排列模式字串（interleaved / sequential / grouped）。
    """
    if explicit_mode:
        mode_map = {
            "interleaved": ORDER_INTERLEAVED,
            "交錯練習": ORDER_INTERLEAVED,
            "sequential": ORDER_SEQUENTIAL,
            "循序漸進": ORDER_SEQUENTIAL,
            "grouped": ORDER_GROUPED,
            "集中練習": ORDER_GROUPED,
        }
        mapped = mode_map.get(explicit_mode)
        if mapped:
            return mapped

    # 自動判斷：單節點 → sequential，多節點 → interleaved
    if len(node_ids) <= 1:
        return ORDER_SEQUENTIAL
    return ORDER_INTERLEAVED


def interleave_questions(questions: list[dict]) -> list[dict]:
    """交錯排列題目：使用 Round-Robin（heap-based）演算法。

    演算法：
    1. 依 node_id 將題目分群（各群內依難度升冪）
    2. 使用 min-heap，每次從題目最多的群取一題
    3. 確保同節點題目最多連續 2 題

    Args:
        questions: 題目清單，每個元素須含 "node_id" 和 "difficulty" 欄位。

    Returns:
        交錯排列後的題目清單。
    """
    if not questions:
        return []

    # 1. 按 node_id 分群，各群內依難度排序
    groups: dict[str, list[dict]] = {}
    for q in questions:
        nid = str(q.get("node_id", ""))
        groups.setdefault(nid, []).append(q)

    for nid in groups:
        groups[nid].sort(key=lambda q: DIFFICULTY_ORDER.get(
            str(q.get("difficulty", "")).lower(), 1
        ))

    # 2. heap：(-剩餘數量, node_id, deque)
    heap: list[tuple[int, str, list[dict]]] = []
    for nid, qs in groups.items():
        heapq.heappush(heap, (-len(qs), nid, list(qs)))

    result: list[dict] = []
    last_node: str | None = None

    while heap:
        neg_count, nid, qs = heapq.heappop(heap)

        # 避免連續同節點（如果還有其他節點可用）
        if nid == last_node and len(heap) > 0:
            # 暫存，取下一個
            heapq.heappush(heap, (neg_count, nid, qs))
            neg_count2, nid2, qs2 = heapq.heappop(heap)
            result.append(qs2.pop(0))
            last_node = nid2
            if qs2:
                heapq.heappush(heap, (-len(qs2), nid2, qs2))
        else:
            result.append(qs.pop(0))
            last_node = nid
            if qs:
                heapq.heappush(heap, (-len(qs), nid, qs))

    return result


def sort_sequential(questions: list[dict]) -> list[dict]:
    """依難度由易到難排列（sequential 模式）。

    Args:
        questions: 題目清單。

    Returns:
        依難度升冪排列的題目清單。
    """
    return sorted(
        questions,
        key=lambda q: DIFFICULTY_ORDER.get(
            str(q.get("difficulty", "")).lower(), 1
        ),
    )


def sort_grouped(questions: list[dict]) -> list[dict]:
    """按知識節點分組排列（grouped 模式）。

    同節點題目集中，組內依難度升冪，各組依原始節點 ID 順序排列。

    Args:
        questions: 題目清單。

    Returns:
        分組排列後的題目清單。
    """
    if not questions:
        return []

    # 保持 node_id 出現順序
    seen: list[str] = []
    groups: dict[str, list[dict]] = {}
    for q in questions:
        nid = str(q.get("node_id", ""))
        if nid not in groups:
            seen.append(nid)
            groups[nid] = []
        groups[nid].append(q)

    result: list[dict] = []
    for nid in seen:
        sorted_group = sorted(
            groups[nid],
            key=lambda q: DIFFICULTY_ORDER.get(
                str(q.get("difficulty", "")).lower(), 1
            ),
        )
        result.extend(sorted_group)
    return result


def apply_order_mode(
    questions: list[dict],
    mode: str,
) -> list[dict]:
    """依模式排列題目並重設 question_number。

    Args:
        questions: 題目清單（含 node_id, difficulty 欄位）。
        mode: 排列模式（interleaved / sequential / grouped）。

    Returns:
        排列後並重設 question_number 的題目清單。
    """
    if mode == ORDER_SEQUENTIAL:
        ordered = sort_sequential(questions)
    elif mode == ORDER_GROUPED:
        ordered = sort_grouped(questions)
    else:
        # 預設 interleaved
        ordered = interleave_questions(questions)

    for i, q in enumerate(ordered, start=1):
        q["question_number"] = i

    return ordered


def sprint_weighted_interleave(
    questions: list[dict],
    high_error_node_ids: list[str],
) -> list[dict]:
    """Sprint 模式：錯題相關節點的題目優先均勻穿插。

    將錯題節點的題目與其餘題目交錯，使錯題節點的題目均勻散布，
    不集中在考卷前段或後段。

    Args:
        questions: 題目清單（含 node_id 欄位）。
        high_error_node_ids: 高錯誤率節點 ID 清單（priority 節點）。

    Returns:
        Sprint 模式排列後的題目清單。
    """
    if not questions or not high_error_node_ids:
        return interleave_questions(questions)

    priority_set = set(str(nid) for nid in high_error_node_ids)
    priority_qs = [q for q in questions if str(q.get("node_id", "")) in priority_set]
    other_qs = [q for q in questions if str(q.get("node_id", "")) not in priority_set]

    if not priority_qs:
        return interleave_questions(questions)
    if not other_qs:
        return interleave_questions(questions)

    # 計算插入間隔：使 priority 題目均勻散布
    total = len(questions)
    p_count = len(priority_qs)
    interval = max(1, total // (p_count + 1))

    # 先做基礎交錯
    other_interleaved = interleave_questions(other_qs)
    result: list[dict] = []
    priority_iter = iter(priority_qs)
    inserted = 0
    pos = 0

    for i, q in enumerate(other_interleaved):
        # 每隔 interval 插入一個 priority 題目
        if inserted < p_count and (i + inserted) % interval == interval - 1:
            try:
                result.append(next(priority_iter))
                inserted += 1
            except StopIteration:
                pass
        result.append(q)
        pos += 1

    # 剩餘 priority 題目補到尾端（均勻穿插）
    for q in priority_iter:
        result.append(q)

    for i, q in enumerate(result, start=1):
        q["question_number"] = i

    return result


def build_result_summary(mode: str) -> dict[str, Any]:
    """建立測驗結果頁的排列模式摘要資訊。

    Args:
        mode: 排列模式（interleaved / sequential / grouped）。

    Returns:
        含 label 和 hint 的摘要字典。
    """
    summary: dict[str, Any] = {
        "question_order_mode": mode,
        "question_order_label": DISPLAY_LABELS.get(mode, mode),
    }
    if mode == ORDER_INTERLEAVED:
        summary["question_order_hint"] = INTERLEAVED_HINT
    return summary
