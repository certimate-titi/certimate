#!/usr/bin/env python3
"""
雲端部署後煙霧測試腳本。

Usage:
    python3 scripts/cloud_smoke_test.py [BASE_URL]

Default BASE_URL: https://certimate-titi-63018063271.asia-east1.run.app/api/v1
"""

import sys
import json
import urllib.request
import urllib.error
import jwt
import datetime

# --- Config ---
DEFAULT_BASE = "https://certimate-titi-63018063271.asia-east1.run.app/api/v1"
JWT_SECRET = "certimate-production-jwt-secret-2026"
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TENANT_ID = "00000000-0000-0000-0000-000000b2cb2c"


def make_token() -> str:
    payload = {
        "sub": TEST_USER_ID,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
        "tenant_id": TENANT_ID,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def api_get(base: str, path: str, token: str) -> tuple:
    """GET request, returns (status_code, response_dict)."""
    url = f"{base}{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        return resp.status, data
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
        except Exception:
            data = {"raw": body[:500]}
        return e.code, data


def api_post(base: str, path: str, token: str, body: dict) -> tuple:
    """POST request, returns (status_code, response_dict)."""
    url = f"{base}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            result = json.loads(body)
        except Exception:
            result = {"raw": body[:500]}
        return e.code, result


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE
    token = make_token()
    results = []

    def check(name: str, passed: bool, detail: str = ""):
        status = "✅" if passed else "❌"
        results.append((name, passed, detail))
        print(f"  {status} {name}" + (f" — {detail}" if detail else ""))

    print(f"\n{'='*60}")
    print(f"CertiMate 雲端煙霧測試")
    print(f"Base URL: {base}")
    print(f"{'='*60}\n")

    # --- Test 0: Health check ---
    print("[0] 健康檢查")
    code, data = api_get(base, "/admin/version", token)
    check("API 回應", code == 200, f"status={code}")
    if code == 200:
        check("版本資訊", "backend_version" in data, f"v={data.get('backend_version')}")
        check("環境", data.get("environment") == "production", f"env={data.get('environment')}")

    # --- Test 1: 考科設定 ---
    print("\n[1] 考科設定")
    code, data = api_get(base, "/subjects/available", token)
    check("考科列表 API", code == 200, f"status={code}")
    subjects = []
    if code == 200:
        subjects = data.get("subjects", [])
        check("有考科資料", len(subjects) > 0, f"count={len(subjects)}")
        # Find AI初級
        ai_basic = next((s for s in subjects if "初級" in s.get("name", "") and "AI" in s.get("name", "")), None)
        if ai_basic:
            check("AI初級 available_questions > 0",
                  (ai_basic.get("available_questions", 0) or 0) > 0,
                  f"available={ai_basic.get('available_questions')}")

    # --- Test 1b: Debug subject (exam_subject_codes) ---
    if subjects:
        ai_basic = next((s for s in subjects if "初級" in s.get("name", "") and "AI" in s.get("name", "")), subjects[0])
        sid = ai_basic.get("id")
        print(f"\n[1b] Debug Subject: {ai_basic.get('name')}")
        code, data = api_get(base, f"/admin/debug-subject/{sid}", token)
        check("Debug endpoint", code == 200, f"status={code}")
        if code == 200:
            codes = data.get("exam_subject_codes", [])
            check("exam_subject_codes 已設定", len(codes) > 0, f"codes={codes}")
            code_results = data.get("code_results", [])
            total_q = sum(cr.get("questions", 0) for cr in code_results)
            check("考古題數量 > 0", total_q > 0, f"total={total_q}")
            nodes = data.get("knowledge_nodes", [])
            check("知識節點存在", len(nodes) > 0, f"nodes={len(nodes)}")
            nodes_with_q = [n for n in nodes if (n.get("available_questions", 0) or 0) > 0]
            check("節點有 available_questions", len(nodes_with_q) > 0,
                  f"with_questions={len(nodes_with_q)}/{len(nodes)}")
            mapped = data.get("mapped_historical_questions", 0)
            check("已映射考古題數", mapped > 0, f"mapped={mapped}")

    # --- Test 2: 知識心智圖 ---
    if subjects:
        ai_basic = next((s for s in subjects if "初級" in s.get("name", "") and "AI" in s.get("name", "")), subjects[0])
        sid = ai_basic.get("id")
        print(f"\n[2] 知識心智圖: {ai_basic.get('name')}")
        code, data = api_get(base, f"/knowledge-map/subjects/{sid}/nodes", token)
        check("知識節點 API", code == 200, f"status={code}")
        if code == 200:
            nodes = data.get("nodes", [])
            check("有知識節點", len(nodes) > 0, f"count={len(nodes)}")
            # Check tree structure
            if nodes:
                has_children = any(len(n.get("children", [])) > 0 for n in nodes)
                check("樹狀結構正確", has_children, "有子節點")
                # Check available_questions
                def count_nodes_with_q(node_list):
                    count = 0
                    for n in node_list:
                        if (n.get("available_questions", 0) or 0) > 0:
                            count += 1
                        count += count_nodes_with_q(n.get("children", []))
                    return count
                with_q = count_nodes_with_q(nodes)
                check("節點有考題數量", with_q > 0, f"with_questions={with_q}")

    # --- Test 3: 考古題生成測試 ---
    if subjects:
        ai_basic = next((s for s in subjects if "初級" in s.get("name", "") and "AI" in s.get("name", "")), subjects[0])
        sid = ai_basic.get("id")
        print(f"\n[3] 考古題生成測試")
        # First get node_ids
        code, data = api_get(base, f"/knowledge-map/subjects/{sid}/nodes", token)
        node_ids = []
        if code == 200:
            def collect_ids(node_list):
                ids = []
                for n in node_list:
                    if (n.get("available_questions", 0) or 0) > 0:
                        ids.append(n["id"])
                    ids.extend(collect_ids(n.get("children", [])))
                return ids
            node_ids = collect_ids(data.get("nodes", []))

        if node_ids:
            check("有可用節點", True, f"node_ids={len(node_ids)}")
            # Create exam
            body = {
                "node_ids": node_ids[:5],
                "question_count": 5,
                "exam_mode": "historical_only",
            }
            code, data = api_post(base, "/exams/config", token, body)
            check("建立考試", code == 200, f"status={code}, data={json.dumps(data, ensure_ascii=False)[:200]}")
            if code == 200:
                exam_id = data.get("exam_id")
                total_q = data.get("total_questions", 0)
                check("考試狀態 READY", data.get("status") == "READY", f"status={data.get('status')}")
                check("有考題", total_q > 0, f"total={total_q}")

                # --- Test 3b: Resume exam ---
                if exam_id:
                    code, data = api_get(base, f"/exams/{exam_id}/resume", token)
                    check("Resume 考試", code == 200, f"status={code}")
                    if code == 200:
                        questions = data.get("questions", [])
                        check("載入考題", len(questions) > 0, f"questions={len(questions)}")
                        if questions:
                            q = questions[0]
                            check("考題有選項", len(q.get("options", [])) >= 2,
                                  f"options={len(q.get('options', []))}")

                        # --- Test 4: 考試結果 (submit) ---
                        print(f"\n[4] 考試結果")
                        answers = [{"questionId": q["id"], "userChoice": "A"} for q in questions]
                        submit_body = {
                            "examId": exam_id,
                            "answers": answers,
                            "timeSpentSeconds": 60,
                        }
                        code, data = api_post(base, "/exams/submit", token, submit_body)
                        check("提交考試", code == 200, f"status={code}")
                        if code == 200:
                            check("有考試結果", "score" in data or "result" in data or "exam_id" in data,
                                  f"keys={list(data.keys())[:5]}")
        else:
            check("有可用節點", False, "node_ids 為空 — 知識節點沒有 available_questions")

    # --- Test 5: 儀表板 + 雷達圖 ---
    print(f"\n[5] 儀表板與雷達圖")
    code, data = api_get(base, "/dashboard", token)
    check("儀表板 API", code == 200, f"status={code}")
    if code == 200:
        check("有科目資料", len(data.get("subjects", [])) > 0,
              f"subjects={len(data.get('subjects', []))}")
        check("有統計資料", "stats" in data, f"keys={list(data.keys())[:8]}")
        domain = data.get("domainStrengths", [])
        check("有領域強度資料", isinstance(domain, list), f"domains={len(domain)}")
        radar = data.get("radar_chart")
        check("雷達圖資料", radar is not None, f"radar={'有' if radar else '無'}")

    # --- Summary ---
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    print(f"\n{'='*60}")
    print(f"測試結果：✅ {passed} 通過 / ❌ {failed} 失敗")
    print(f"{'='*60}\n")

    if failed > 0:
        print("失敗項目：")
        for name, p, detail in results:
            if not p:
                print(f"  ❌ {name} — {detail}")
        sys.exit(1)


if __name__ == "__main__":
    main()
