#!/usr/bin/env python3
"""CertiMate 本地開發伺服器啟動腳本。

啟動 PostgreSQL (Docker) + FastAPI (uvicorn --reload)。
若偵測到前次仍在執行，會先關閉再重啟。

用法:
    python dev.py          # 啟動 DB + API server
    python dev.py --stop   # 停止所有服務
"""

import os
import sys
import signal
import subprocess
import time
import argparse
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.resolve()
PID_FILE = BACKEND_DIR / ".dev-server.pid"
DOCKER_COMPOSE = BACKEND_DIR / "docker-compose.yml"
VENV_PYTHON = BACKEND_DIR / ".venv" / "bin" / "python"
API_PORT = 8000

# 確保 PATH 包含常見工具路徑
_EXTRA_PATHS = "/usr/local/bin:/opt/homebrew/bin"
if _EXTRA_PATHS not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _EXTRA_PATHS + ":" + os.environ.get("PATH", "")


def find_python():
    """找到可用的 Python 執行檔。"""
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    # fallback
    for cmd in ["python3", "python"]:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            return cmd
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    print("❌ 找不到 Python，請確認已安裝")
    sys.exit(1)


def is_process_alive(pid: int) -> bool:
    """檢查 PID 是否仍在執行。"""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def kill_previous():
    """關閉前次啟動的 uvicorn 進程。"""
    if not PID_FILE.exists():
        return

    try:
        pid = int(PID_FILE.read_text().strip())
    except (ValueError, FileNotFoundError):
        PID_FILE.unlink(missing_ok=True)
        return

    if is_process_alive(pid):
        print(f"🔄 關閉前次 uvicorn 進程 (PID {pid})...")
        try:
            os.kill(pid, signal.SIGTERM)
            # 等待進程結束（最多 5 秒）
            for _ in range(50):
                if not is_process_alive(pid):
                    break
                time.sleep(0.1)
            else:
                # 強制殺掉
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
            print(f"   ✅ 已關閉 PID {pid}")
        except ProcessLookupError:
            pass

    PID_FILE.unlink(missing_ok=True)


def kill_port_occupant():
    """如果 port 被佔用，找到並關閉佔用進程。"""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{API_PORT}"],
            capture_output=True, text=True,
        )
        pids = result.stdout.strip().split("\n")
        for pid_str in pids:
            if pid_str.strip():
                pid = int(pid_str.strip())
                print(f"🔄 Port {API_PORT} 被 PID {pid} 佔用，正在關閉...")
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
    except (FileNotFoundError, ValueError, ProcessLookupError):
        pass


def start_db():
    """啟動 PostgreSQL Docker 容器。"""
    print("🐘 啟動 PostgreSQL...")

    # 檢查 Docker 是否可用
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ Docker 未啟動或未安裝，請先啟動 Docker Desktop")
        sys.exit(1)

    # docker compose up -d
    result = subprocess.run(
        ["docker", "compose", "-f", str(DOCKER_COMPOSE), "up", "-d"],
        cwd=str(BACKEND_DIR),
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        # fallback to docker-compose (v1)
        result = subprocess.run(
            ["docker-compose", "-f", str(DOCKER_COMPOSE), "up", "-d"],
            cwd=str(BACKEND_DIR),
            capture_output=True, text=True,
        )

    if result.returncode != 0:
        # 如果是 port already allocated，表示 DB 已在運行
        if "port is already allocated" in result.stderr or "is already in use" in result.stderr:
            print("   ℹ️  PostgreSQL 已在運行中，跳過啟動")
            return
        print(f"❌ 啟動 PostgreSQL 失敗:\n{result.stderr}")
        sys.exit(1)

    # 等待 DB 就緒
    print("   等待 PostgreSQL 就緒...", end="", flush=True)
    for i in range(30):
        check = subprocess.run(
            ["docker", "exec", "certimate-api-postgres",
             "pg_isready", "-U", "postgres"],
            capture_output=True,
        )
        if check.returncode == 0:
            print(" ✅")
            return
        print(".", end="", flush=True)
        time.sleep(1)

    print("\n❌ PostgreSQL 啟動逾時")
    sys.exit(1)


def stop_db():
    """停止 PostgreSQL Docker 容器。"""
    print("🐘 停止 PostgreSQL...")
    try:
        subprocess.run(
            ["docker", "compose", "-f", str(DOCKER_COMPOSE), "down"],
            cwd=str(BACKEND_DIR),
            capture_output=True,
        )
        print("   ✅ PostgreSQL 已停止")
    except FileNotFoundError:
        print("   ⚠️  Docker 未安裝，跳過")


def start_server():
    """啟動 uvicorn 開發伺服器。"""
    python = find_python()

    print(f"🚀 啟動 API 伺服器 (port {API_PORT})...")
    print(f"   Python: {python}")
    print(f"   URL: http://localhost:{API_PORT}")
    print(f"   Docs: http://localhost:{API_PORT}/api/v1/docs")
    print("   按 Ctrl+C 停止\n")

    # 啟動 uvicorn（前台執行，支持 --reload）
    proc = subprocess.Popen(
        [python, "-m", "uvicorn", "app.main:app",
         "--reload", "--host", "0.0.0.0", "--port", str(API_PORT)],
        cwd=str(BACKEND_DIR),
    )

    # 寫入 PID
    PID_FILE.write_text(str(proc.pid))

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n\n⏹️  收到 Ctrl+C，正在停止...")
        proc.terminate()
        proc.wait(timeout=5)
    finally:
        PID_FILE.unlink(missing_ok=True)


def stop_all():
    """停止所有服務。"""
    kill_previous()
    kill_port_occupant()
    stop_db()
    print("\n✅ 所有服務已停止")


def main():
    global API_PORT

    parser = argparse.ArgumentParser(description="CertiMate 本地開發伺服器")
    parser.add_argument("--stop", action="store_true", help="停止所有服務")
    parser.add_argument("--no-db", action="store_true", help="不啟動 DB（使用已有的）")
    parser.add_argument("--port", type=int, default=API_PORT, help=f"API 埠號 (預設 {API_PORT})")
    args = parser.parse_args()

    API_PORT = args.port

    if args.stop:
        stop_all()
        return

    print("=" * 50)
    print("  CertiMate 本地開發環境")
    print("=" * 50)
    print()

    # 1. 關閉前次
    kill_previous()
    kill_port_occupant()

    # 2. 啟動 DB
    if not args.no_db:
        start_db()

    # 3. 啟動 API server
    start_server()


if __name__ == "__main__":
    main()
