from behave import then


@then('使用者可從第 {next_chunk:d} 片繼續上傳')
def step_impl(context, next_chunk):
    response = context.last_response
    data = response.json()
    next_chunk_index = data.get("next_chunk_index") or data.get("next_chunk")
    assert next_chunk_index is not None, \
        f"回應中找不到 next_chunk_index 欄位: {data}"
    assert int(next_chunk_index) == next_chunk, \
        f"下一片應從第 {next_chunk} 片開始，實際為 {next_chunk_index}"
