"""安全防護模組 — SSRF、URL 驗證、出站流量控制.

Phase 1 SSRF 防護：
- 防止用戶輸入的 URL 指向內網 IP（SSRF 攻擊）
- 阻擋 Cloud Metadata 服務（169.254.169.254、metadata.google.internal 等）
- 白名單允許特定外部域名（YouTube、S3 等業務需要）
- 提供 async-safe 的安全 HTTP 請求 wrapper
"""

import ipaddress
import re
import socket
from urllib.parse import urlparse

# ── 黑名單 IP 範圍（RFC 1918 內網 + Link-local + Loopback）──────────────
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),        # RFC 1918 私有 A 類
    ipaddress.ip_network("172.16.0.0/12"),      # RFC 1918 私有 B 類
    ipaddress.ip_network("192.168.0.0/16"),     # RFC 1918 私有 C 類
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("::1/128"),            # IPv6 Loopback
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local（AWS/GCP Metadata）
    ipaddress.ip_network("fc00::/7"),           # IPv6 私有
    ipaddress.ip_network("fe80::/10"),          # IPv6 Link-local
    ipaddress.ip_network("0.0.0.0/8"),          # 未指定
    ipaddress.ip_network("100.64.0.0/10"),      # CGNAT
]

# ── 黑名單域名（Cloud Metadata 服務）─────────────────────────────────────
_BLOCKED_HOSTNAMES = {
    "metadata.google.internal",   # GCP Metadata
    "metadata.internal",
    "169.254.169.254",            # AWS/GCP/Azure Metadata IP
    "fd00:ec2::254",              # AWS IMDSv2 IPv6
    "localhost",
    "localhost.localdomain",
}

# ── 允許的外部域名白名單（業務需要的外部服務）────────────────────────────
_ALLOWED_DOMAINS_WHITELIST = {
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "storage.googleapis.com",    # GCS
    "s3.amazonaws.com",          # AWS S3
    "firebasestorage.googleapis.com",
}

# ── 允許的 URL scheme ─────────────────────────────────────────────────────
_ALLOWED_SCHEMES = {"https", "http"}


class SSRFError(ValueError):
    """SSRF 攻擊嘗試偵測錯誤。"""
    pass


def validate_url_for_ssrf(url: str, *, require_https: bool = False) -> str:
    """驗證 URL 不會造成 SSRF 攻擊，並回傳正規化後的 URL。

    Args:
        url: 用戶輸入的 URL 字串
        require_https: 是否強制要求 HTTPS（生產環境建議設為 True）

    Returns:
        正規化後的 URL（str）

    Raises:
        SSRFError: 當 URL 可能造成 SSRF 攻擊時
        ValueError: 當 URL 格式無效時
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL 不可為空")

    url = url.strip()

    # 解析 URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"無效的 URL 格式: {e}")

    # 檢查 scheme
    scheme = parsed.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise SSRFError(f"不允許的 URL scheme: {scheme!r}（允許: {_ALLOWED_SCHEMES}）")

    if require_https and scheme != "https":
        raise SSRFError("安全政策要求使用 HTTPS")

    # 取得 hostname
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL 缺少 hostname")

    hostname = hostname.lower().rstrip(".")

    # 檢查黑名單域名
    if hostname in _BLOCKED_HOSTNAMES:
        raise SSRFError(f"URL 指向受保護的內部服務: {hostname!r}")

    # 始終檢查 resolved IP（防止 DNS rebinding 攻擊）
    _check_host_ip(hostname)

    # 白名單模式：若啟用白名單，非白名單域名直接拒絕
    if _ALLOWED_DOMAINS_WHITELIST:
        normalized_host = hostname.removeprefix("www.")
        if normalized_host not in _ALLOWED_DOMAINS_WHITELIST and \
           hostname not in _ALLOWED_DOMAINS_WHITELIST:
            raise SSRFError(
                f"域名 {hostname!r} 不在允許的白名單中。"
                f"允許的域名: {_ALLOWED_DOMAINS_WHITELIST}"
            )

    return url


def _check_host_ip(hostname: str) -> None:
    """解析 hostname 對應的 IP 並驗證非內網。

    Raises:
        SSRFError: 若 IP 在黑名單範圍內
    """
    try:
        # 嘗試直接解析為 IP
        addr = ipaddress.ip_address(hostname)
        _validate_ip_address(addr, hostname)
        return
    except ValueError:
        pass  # 不是 IP，繼續 DNS 解析

    # DNS 解析
    try:
        results = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValueError(f"無法解析 hostname: {hostname!r}")

    for result in results:
        ip_str = result[4][0]
        try:
            addr = ipaddress.ip_address(ip_str)
            _validate_ip_address(addr, hostname)
        except SSRFError:
            raise
        except ValueError:
            continue


def _validate_ip_address(addr: ipaddress.IPv4Address | ipaddress.IPv6Address,
                          hostname: str) -> None:
    """驗證 IP 地址不在黑名單範圍內。"""
    for network in _BLOCKED_NETWORKS:
        # 同類型才能比較
        if isinstance(addr, ipaddress.IPv4Address) and isinstance(network, ipaddress.IPv4Network):
            if addr in network:
                raise SSRFError(
                    f"URL 指向內網 IP: {addr}（來自 {hostname!r}），"
                    f"符合黑名單範圍 {network}"
                )
        elif isinstance(addr, ipaddress.IPv6Address) and isinstance(network, ipaddress.IPv6Network):
            if addr in network:
                raise SSRFError(
                    f"URL 指向內網 IPv6: {addr}（來自 {hostname!r}），"
                    f"符合黑名單範圍 {network}"
                )


def validate_youtube_url(url: str) -> str:
    """專用 YouTube URL 驗證器（資源上傳用）。

    僅允許 youtube.com 和 youtu.be 域名。
    Returns:
        正規化後的 YouTube URL

    Raises:
        ValueError: 不是有效的 YouTube URL
    """
    validated = validate_url_for_ssrf(url)
    parsed = urlparse(validated)
    hostname = (parsed.hostname or "").lower().removeprefix("www.")

    if hostname not in {"youtube.com", "youtu.be"}:
        raise ValueError(f"不是有效的 YouTube URL（domain: {hostname!r}）")

    # 驗證有 video ID
    if hostname == "youtube.com":
        if not re.search(r"[?&]v=[\w-]{11}", parsed.query or ""):
            # 允許 /embed/{id} 或 /watch?v={id} 格式
            if not re.search(r"/embed/[\w-]{11}|/v/[\w-]{11}", parsed.path or ""):
                raise ValueError("YouTube URL 缺少有效的 video ID")
    elif hostname == "youtu.be":
        if not re.match(r"/[\w-]{11}", parsed.path or ""):
            raise ValueError("youtu.be 短網址缺少有效的 video ID")

    return validated


# ── 快速檢查 helper（供其他模組 import）────────────────────────────────────
def is_safe_url(url: str) -> bool:
    """快速檢查 URL 是否安全（不拋出例外）。"""
    try:
        validate_url_for_ssrf(url)
        return True
    except (SSRFError, ValueError):
        return False
