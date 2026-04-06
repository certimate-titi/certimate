"""When 系統執行知識樹合併對齊 / 語意比對 / 合併 — Command"""

from behave import when


@when('系統執行知識樹合併對齊')
def step_trigger_merge(context):
    subject_id = context.memo.get("merge_subject_id")
    assert subject_id, "找不到 merge_subject_id，請先設定考科"

    admin_email = None
    for key in context.ids:
        if "@" in key:
            admin_email = key
            break
    assert admin_email, "找不到管理員帳號"

    user_id = context.ids[admin_email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        f"/api/v1/knowledge-merge/subjects/{subject_id}/merge",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "incoming_nodes": context.memo.get("incoming_nodes", []),
        },
    )
    context.last_response = response


@when('系統執行語意比對')
def step_semantic_compare(context):
    subject_id = context.memo.get("merge_subject_id")
    assert subject_id, "找不到 merge_subject_id"

    admin_email = None
    for key in context.ids:
        if "@" in key:
            admin_email = key
            break

    user_id = context.ids[admin_email]
    token = context.jwt_helper.generate_token(user_id)

    # First, do a compare to get similarity score
    existing_names = context.memo.get("existing_node_names", [])
    incoming_nodes = context.memo.get("incoming_nodes", [])

    existing_name = existing_names[0] if existing_names else ""
    incoming_name = incoming_nodes[0]["name"] if incoming_nodes else ""

    compare_resp = context.api_client.post(
        f"/api/v1/knowledge-merge/subjects/{subject_id}/compare",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "existing_name": existing_name,
            "incoming_name": incoming_name,
        },
    )

    # Then, trigger the merge to create actual conflicts/merges
    merge_resp = context.api_client.post(
        f"/api/v1/knowledge-merge/subjects/{subject_id}/merge",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "incoming_nodes": incoming_nodes,
        },
    )

    # Combine results: use compare similarity but also include merge results
    compare_data = compare_resp.json() if compare_resp.status_code == 200 else {}
    merge_data = merge_resp.json() if merge_resp.status_code == 200 else {}

    # Store both for Then steps to use
    context.memo["compare_result"] = compare_data
    context.memo["merge_result"] = merge_data

    # last_response uses compare for similarity checks, merge for conflict checks
    # Use compare as primary response (has similarity field)
    context.last_response = compare_resp
    context.memo["merge_response"] = merge_resp


@when('系統執行合併')
def step_execute_merge(context):
    subject_id = context.memo.get("merge_subject_id")
    assert subject_id, "找不到 merge_subject_id"

    admin_email = None
    for key in context.ids:
        if "@" in key:
            admin_email = key
            break

    user_id = context.ids[admin_email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        f"/api/v1/knowledge-merge/subjects/{subject_id}/merge",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "incoming_nodes": context.memo.get("incoming_nodes", []),
        },
    )
    context.last_response = response


@when('兩者被判定為語意匹配')
def step_semantic_match(context):
    subject_id = context.memo.get("merge_subject_id")
    assert subject_id, "找不到 merge_subject_id"

    admin_email = None
    for key in context.ids:
        if "@" in key:
            admin_email = key
            break

    user_id = context.ids[admin_email]
    token = context.jwt_helper.generate_token(user_id)

    # Trigger merge which will internally do semantic matching
    response = context.api_client.post(
        f"/api/v1/knowledge-merge/subjects/{subject_id}/merge",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "incoming_nodes": context.memo.get("incoming_nodes", []),
        },
    )
    context.last_response = response
    context.memo["semantic_match"] = True


@when('合併完成')
def step_merge_complete(context):
    # If merge was already triggered, verify. Otherwise trigger now.
    if context.last_response is None:
        subject_id = context.memo.get("merge_subject_id")
        if subject_id:
            admin_email = None
            for key in context.ids:
                if "@" in key:
                    admin_email = key
                    break

            user_id = context.ids[admin_email]
            token = context.jwt_helper.generate_token(user_id)

            response = context.api_client.post(
                f"/api/v1/knowledge-merge/subjects/{subject_id}/merge",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "incoming_nodes": context.memo.get("incoming_nodes", []),
                },
            )
            context.last_response = response
