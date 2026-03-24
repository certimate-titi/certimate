# behave 在載入 step 模組時，globals 可能缺少 __name__，導致相對匯入失敗
if "__name__" not in globals():
    __name__ = "{{PY_TEST_MODULE}}.steps"
if "__package__" not in globals():
    __package__ = "{{PY_TEST_MODULE}}.steps"

# Common Then
from .common_then import success
from .common_then import failure
from .common_then import failure_with_reason
from .common_then import error_message
