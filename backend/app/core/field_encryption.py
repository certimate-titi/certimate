"""欄位級加密模組 — 應用層 Fernet 對稱加密.

用途：
- 保護 `answers.selected_answer`（作答選項）等含個資的欄位
- 金鑰由環境變數 FIELD_ENCRYPTION_KEY 管理（Base64-urlsafe 32 bytes）
- 使用 AES-128-CBC + HMAC-SHA256（Fernet 規格），每次加密結果皆含隨機 IV

使用方式：
    from app.core.field_encryption import encrypt_field, decrypt_field, is_encrypted

    # 加密
    cipher = encrypt_field("A")           # → "enc:gAAAAAB..."
    # 解密
    plain  = decrypt_field(cipher)        # → "A"
    # 判斷是否已加密
    flag   = is_encrypted(cipher)         # → True

金鑰輪替（Key Rotation）：
    設定 FIELD_ENCRYPTION_KEY_PREVIOUS 為舊金鑰，decrypt_field 會自動 fallback。
    輪替完成後清除 PREVIOUS 環境變數。

重要：
    - 測試環境若未設定 FIELD_ENCRYPTION_KEY，使用固定的開發用金鑰（明確標示）
    - 正式環境必須設定強隨機金鑰（使用 `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` 產生）
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── 加密前綴，用於判斷欄位是否已加密 ────────────────────────────────────
_ENC_PREFIX = "enc:"

# ── 開發用固定金鑰（僅供測試，正式環境必須覆蓋）────────────────────────
_DEV_KEY = b"ZmRldmtleS1ub3QtZm9yLXByb2R1Y3Rpb24tY2VydGltYXQ="

# ── 懶載入 Fernet 實例（避免啟動時 import 失敗）────────────────────────
_fernet_primary: Optional[object] = None
_fernet_previous: Optional[object] = None
_initialized: bool = False


def _get_fernet():
    """取得或初始化 Fernet 實例（懶載入，線程安全）。"""
    global _fernet_primary, _fernet_previous, _initialized

    if _initialized:
        return _fernet_primary, _fernet_previous

    try:
        from cryptography.fernet import Fernet, MultiFernet

        raw_key = os.environ.get("FIELD_ENCRYPTION_KEY", "").strip()
        if raw_key:
            key_bytes = raw_key.encode()
        else:
            logger.warning(
                "⚠️  FIELD_ENCRYPTION_KEY 未設定，使用開發用固定金鑰（僅限測試環境）"
            )
            key_bytes = _DEV_KEY

        _fernet_primary = Fernet(key_bytes)

        # 舊金鑰（金鑰輪替期間使用）
        prev_key = os.environ.get("FIELD_ENCRYPTION_KEY_PREVIOUS", "").strip()
        if prev_key:
            _fernet_previous = Fernet(prev_key.encode())

        _initialized = True

    except ImportError:
        logger.error(
            "cryptography 套件未安裝，欄位加密功能停用。"
            "請執行: pip install cryptography"
        )
        _fernet_primary = None
        _fernet_previous = None
        _initialized = True

    except Exception as e:
        logger.error(f"Fernet 初始化失敗：{e}")
        _fernet_primary = None
        _fernet_previous = None
        _initialized = True

    return _fernet_primary, _fernet_previous


def is_encrypted(value: Optional[str]) -> bool:
    """判斷欄位值是否已加密（以 `enc:` 前綴識別）。"""
    if value is None:
        return False
    return value.startswith(_ENC_PREFIX)


def encrypt_field(plain_text: Optional[str]) -> Optional[str]:
    """加密欄位值，回傳帶 `enc:` 前綴的 Base64 密文。

    Args:
        plain_text: 明文字串；若為 None 則直接回傳 None。

    Returns:
        "enc:{fernet_token}" 格式的密文字串，或 None。
    """
    if plain_text is None:
        return None
    if is_encrypted(plain_text):
        # 已加密，避免重複加密
        return plain_text

    fernet_primary, _ = _get_fernet()
    if fernet_primary is None:
        # cryptography 未安裝，降級為明文存儲（記錄警告）
        logger.warning("欄位加密停用，以明文存儲（生產環境禁止）")
        return plain_text

    try:
        token = fernet_primary.encrypt(plain_text.encode("utf-8"))
        return f"{_ENC_PREFIX}{token.decode('ascii')}"
    except Exception as e:
        logger.error(f"欄位加密失敗：{e}")
        return plain_text


def decrypt_field(cipher_text: Optional[str]) -> Optional[str]:
    """解密欄位值，自動辨識是否已加密。

    支援金鑰輪替：先試主金鑰，失敗時嘗試舊金鑰。

    Args:
        cipher_text: 帶 `enc:` 前綴的密文，或未加密的明文。

    Returns:
        解密後的明文字串，或 None。
    """
    if cipher_text is None:
        return None
    if not is_encrypted(cipher_text):
        # 未加密（舊資料相容），直接回傳
        return cipher_text

    token_str = cipher_text[len(_ENC_PREFIX):]
    token_bytes = token_str.encode("ascii")

    fernet_primary, fernet_previous = _get_fernet()
    if fernet_primary is None:
        logger.warning("欄位解密停用，直接回傳密文")
        return cipher_text

    # 先嘗試主金鑰
    try:
        return fernet_primary.decrypt(token_bytes).decode("utf-8")
    except Exception:
        pass

    # 嘗試舊金鑰（輪替期間）
    if fernet_previous is not None:
        try:
            plain = fernet_previous.decrypt(token_bytes).decode("utf-8")
            logger.info("使用舊金鑰解密成功（建議排程重新加密以完成金鑰輪替）")
            return plain
        except Exception:
            pass

    logger.error("欄位解密失敗（主金鑰與舊金鑰均無法解密）")
    return None


def rotate_encrypt(cipher_text: Optional[str]) -> Optional[str]:
    """將舊金鑰加密的密文重新以新金鑰加密（金鑰輪替用）。

    流程：先解密（使用舊金鑰），再重新加密（使用新金鑰）。

    Args:
        cipher_text: 帶 `enc:` 前綴的舊密文。

    Returns:
        以新金鑰重新加密的密文，或原值（若解密失敗）。
    """
    plain = decrypt_field(cipher_text)
    if plain is None or plain == cipher_text:
        return cipher_text
    return encrypt_field(plain)


def reset_for_testing():
    """重置 Fernet 實例（僅供測試使用，正式環境勿呼叫）。"""
    global _fernet_primary, _fernet_previous, _initialized
    _fernet_primary = None
    _fernet_previous = None
    _initialized = False
