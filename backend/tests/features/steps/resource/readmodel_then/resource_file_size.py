from behave import then


@then('資源檔案大小應為 {size:d}MB')
def step_impl(context, size):
    response = context.last_response
    data = response.json()
    file_size_bytes = data.get("file_size_bytes") or data.get("resource", {}).get("file_size_bytes")
    assert file_size_bytes is not None, \
        f"回應中找不到 file_size_bytes 欄位: {data}"
    expected_bytes = size * 1024 * 1024
    assert int(file_size_bytes) == expected_bytes, \
        f"檔案大小應為 {expected_bytes} bytes ({size}MB)，實際為 {file_size_bytes}"
