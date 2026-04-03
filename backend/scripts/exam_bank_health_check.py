"""
CertiMate 題庫資料品質巡檢腳本

由⭐考題設計人員管理，後端研發人員實作。
定期檢查 DB 中已匯入的考古題品質，產出報告供考題設計人員判讀。

用法:
    cd backend
    python scripts/exam_bank_health_check.py            # 完整巡檢
    python scripts/exam_bank_health_check.py --fix       # 巡檢 + 自動修復可修項目
    python scripts/exam_bank_health_check.py --json      # 輸出 JSON 報告

巡檢項目:
    1. 選項污染（option 文字混入其他題目內容）
    2. 空選項（缺少 A/B/C/D 任一選項）
    3. 答案異常（correct_answer 不是 A/B/C/D）
    4. 內容重複（同一科目下完全相同的題幹）
    5. 來源重複（同 historical_source 出現在多個 exam）
    6. 孤兒題目（exam 已刪但 questions 殘留）
    7. node_id 缺失（已匯入但未對應知識節點）

前置條件:
    - DB 可連線（讀取 .env 中的 DATABASE_URL）
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

# ── 巡檢閾值（⭐考題設計人員可調整）──
OPTION_MAX_LENGTH = 150       # 選項超過此長度視為疑似污染
CONTENT_MIN_LENGTH = 10       # 題幹低於此長度視為異常
DUPLICATE_SIMILARITY = 1.0    # 1.0 = 完全相同才算重複

# ── 污染偵測模式 ──
CONTAMINATION_PATTERNS = [
    r'下列.{0,20}(何者|哪一個|哪些)',
    r'請問.{5,}',
    r'以下.{0,10}(何者|哪一個)',
    r'若.{5,}則',
]
CONTAMINATION_RE = re.compile('|'.join(CONTAMINATION_PATTERNS))


def check_option_contamination(db):
    """檢查 1: 選項污染 — 選項文字異常長或混入其他題目題幹"""
    issues = []

    rows = db.execute(text("""
        SELECT q.id, q.question_number, q.historical_source,
               q.option_a, q.option_b, q.option_c, q.option_d
        FROM questions q
    """)).fetchall()

    for r in rows:
        for label, idx in [('A', 3), ('B', 4), ('C', 5), ('D', 6)]:
            opt = r[idx] or ''
            if len(opt) <= OPTION_MAX_LENGTH:
                continue

            # 長選項不一定是污染，檢查是否含有題目特徵
            if CONTAMINATION_RE.search(opt):
                issues.append({
                    "type": "option_contamination",
                    "severity": "critical",
                    "question_id": str(r[0]),
                    "question_number": r[1],
                    "source": r[2],
                    "field": f"option_{label.lower()}",
                    "length": len(opt),
                    "preview": opt[:100],
                    "fixable": False,
                })

    return issues


def check_empty_options(db):
    """檢查 2: 空選項 — 缺少必要的選項內容"""
    issues = []

    rows = db.execute(text("""
        SELECT q.id, q.question_number, q.historical_source,
               q.option_a, q.option_b, q.option_c, q.option_d
        FROM questions q
    """)).fetchall()

    for r in rows:
        empty_opts = []
        for label, idx in [('A', 3), ('B', 4), ('C', 5), ('D', 6)]:
            if not r[idx] or r[idx].strip() == '':
                empty_opts.append(label)

        if empty_opts:
            issues.append({
                "type": "empty_option",
                "severity": "warning",
                "question_id": str(r[0]),
                "question_number": r[1],
                "source": r[2],
                "missing_options": empty_opts,
            })

    return issues


def check_invalid_answers(db):
    """檢查 3: 答案異常 — correct_answer 不是有效值"""
    issues = []

    rows = db.execute(text("""
        SELECT q.id, q.question_number, q.historical_source, q.correct_answer
        FROM questions q
        WHERE q.correct_answer NOT IN ('A', 'B', 'C', 'D')
    """)).fetchall()

    for r in rows:
        issues.append({
            "type": "invalid_answer",
            "severity": "critical",
            "question_id": str(r[0]),
            "question_number": r[1],
            "source": r[2],
            "actual_answer": r[3],
        })

    return issues


def check_duplicate_content(db):
    """檢查 4: 內容重複 — 同科目下完全相同題幹"""
    issues = []

    rows = db.execute(text("""
        SELECT q.content, COUNT(*) as cnt,
               ARRAY_AGG(q.id::text) as ids,
               ARRAY_AGG(q.historical_source) as sources
        FROM questions q
        GROUP BY q.content
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
        LIMIT 50
    """)).fetchall()

    for r in rows:
        issues.append({
            "type": "duplicate_content",
            "severity": "warning",
            "count": r[1],
            "content_preview": r[0][:80],
            "question_ids": r[2][:5],
            "sources": list(set(r[3]))[:3],
        })

    return issues


def check_source_duplicates(db):
    """檢查 5: 來源重複 — 同 historical_source 出現在多個 exam"""
    issues = []

    rows = db.execute(text("""
        SELECT q.historical_source, COUNT(DISTINCT q.exam_id) as exam_count,
               ARRAY_AGG(DISTINCT q.exam_id::text) as exam_ids
        FROM questions q
        WHERE q.historical_source IS NOT NULL
        GROUP BY q.historical_source
        HAVING COUNT(DISTINCT q.exam_id) > 1
    """)).fetchall()

    for r in rows:
        issues.append({
            "type": "source_duplicate",
            "severity": "warning",
            "source": r[0],
            "exam_count": r[1],
            "exam_ids": r[2],
        })

    return issues


def check_orphan_questions(db):
    """檢查 6: 孤兒題目 — questions 的 exam_id 指向不存在的 exam"""
    issues = []

    rows = db.execute(text("""
        SELECT q.id, q.question_number, q.historical_source, q.exam_id
        FROM questions q
        LEFT JOIN exams e ON e.id = q.exam_id
        WHERE e.id IS NULL
    """)).fetchall()

    for r in rows:
        issues.append({
            "type": "orphan_question",
            "severity": "critical",
            "question_id": str(r[0]),
            "question_number": r[1],
            "source": r[2],
            "missing_exam_id": str(r[3]),
            "fixable": True,
        })

    return issues


def check_missing_node_id(db):
    """檢查 7: node_id 缺失 — 已匯入但未對應到知識節點"""
    issues = []

    rows = db.execute(text("""
        SELECT q.historical_source, COUNT(*) as cnt
        FROM questions q
        WHERE q.node_id IS NULL
          AND q.historical_source IS NOT NULL
        GROUP BY q.historical_source
        ORDER BY COUNT(*) DESC
    """)).fetchall()

    for r in rows:
        issues.append({
            "type": "missing_node_id",
            "severity": "info",
            "source": r[0],
            "count": r[1],
        })

    return issues


def check_short_content(db):
    """檢查 8: 題幹過短 — 可能是解析不完整"""
    issues = []

    rows = db.execute(text("""
        SELECT q.id, q.question_number, q.historical_source, q.content
        FROM questions q
        WHERE LENGTH(q.content) < :min_len
    """), {"min_len": CONTENT_MIN_LENGTH}).fetchall()

    for r in rows:
        issues.append({
            "type": "short_content",
            "severity": "warning",
            "question_id": str(r[0]),
            "question_number": r[1],
            "source": r[2],
            "content": r[3],
        })

    return issues


def auto_fix(db, issues):
    """自動修復可修項目"""
    fixed = 0

    # Fix orphan questions: delete them
    orphans = [i for i in issues if i["type"] == "orphan_question"]
    if orphans:
        orphan_ids = [i["question_id"] for i in orphans]
        for oid in orphan_ids:
            db.execute(text("DELETE FROM questions WHERE id = :id"), {"id": oid})
        db.commit()
        fixed += len(orphans)
        print(f"  修復: 刪除 {len(orphans)} 筆孤兒題目")

    return fixed


def main():
    fix_mode = "--fix" in sys.argv
    json_mode = "--json" in sys.argv

    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    total_questions = db.execute(text("SELECT COUNT(*) FROM questions")).scalar()

    if not json_mode:
        print(f"\n{'='*60}")
        print(f"  CertiMate 題庫資料品質巡檢")
        print(f"  管理者: ⭐考題設計人員")
        print(f"  題庫總數: {total_questions} 題")
        print(f"{'='*60}\n")

    all_issues = []

    checks = [
        ("選項污染", check_option_contamination),
        ("空選項", check_empty_options),
        ("答案異常", check_invalid_answers),
        ("內容重複", check_duplicate_content),
        ("來源重複", check_source_duplicates),
        ("孤兒題目", check_orphan_questions),
        ("node_id 缺失", check_missing_node_id),
        ("題幹過短", check_short_content),
    ]

    for name, check_fn in checks:
        issues = check_fn(db)
        all_issues.extend(issues)

        if not json_mode:
            severity_counts = Counter(i["severity"] for i in issues)
            icon = "✅" if not issues else "⚠️" if not severity_counts.get("critical") else "❌"
            print(f"  {icon} {name}: ", end="")
            if not issues:
                print("通過")
            else:
                parts = []
                if severity_counts.get("critical"):
                    parts.append(f"{severity_counts['critical']} 嚴重")
                if severity_counts.get("warning"):
                    parts.append(f"{severity_counts['warning']} 警告")
                if severity_counts.get("info"):
                    parts.append(f"{severity_counts['info']} 資訊")
                print(" | ".join(parts))

                # Show details for critical issues
                for i in issues:
                    if i["severity"] == "critical":
                        preview = i.get("preview") or i.get("content") or i.get("actual_answer") or ""
                        src = (i.get("source") or "")[:40]
                        print(f"      ❌ Q#{i.get('question_number', '?')} [{src}] {preview[:60]}")

    # Auto-fix if requested
    if fix_mode and not json_mode:
        fixable = [i for i in all_issues if i.get("fixable")]
        if fixable:
            print(f"\n  自動修復 {len(fixable)} 項...")
            auto_fix(db, all_issues)
        else:
            print(f"\n  無可自動修復的項目")

    # Summary
    severity_totals = Counter(i["severity"] for i in all_issues)

    if json_mode:
        report = {
            "total_questions": total_questions,
            "total_issues": len(all_issues),
            "critical": severity_totals.get("critical", 0),
            "warning": severity_totals.get("warning", 0),
            "info": severity_totals.get("info", 0),
            "issues": all_issues,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'='*60}")
        health = "🟢 健康" if severity_totals.get("critical", 0) == 0 else "🔴 需處理"
        print(f"  巡檢結果: {health}")
        print(f"  嚴重: {severity_totals.get('critical', 0)} | "
              f"警告: {severity_totals.get('warning', 0)} | "
              f"資訊: {severity_totals.get('info', 0)}")
        print(f"{'='*60}\n")

    db.close()
    return 1 if severity_totals.get("critical", 0) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
