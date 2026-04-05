#!/usr/bin/env python3
"""CertiMate 本地開發伺服器啟動腳本。

同時啟動 PostgreSQL (Docker) + FastAPI (uvicorn --reload) + Next.js (npm run dev)。
若偵測到前次仍在執行，會先關閉再重啟。

用法:
    python dev.py              # 啟動 DB + API + Frontend
    python dev.py --stop       # 停止所有服務
    python dev.py --no-frontend  # 只啟動後端
"""

import os
import sys
import signal
import subprocess
import time
import argparse
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.resolve()
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
PID_FILE = BACKEND_DIR / ".dev-server.pid"
FRONTEND_PID_FILE = BACKEND_DIR / ".frontend-server.pid"
DOCKER_COMPOSE = BACKEND_DIR / "docker-compose.yml"
VENV_PYTHON = BACKEND_DIR / ".venv" / "bin" / "python"
API_PORT = 8000
FRONTEND_PORT = 3000

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
    """關閉前次啟動的 uvicorn 與 frontend 進程。"""
    kill_pid_file(PID_FILE, "uvicorn")
    kill_pid_file(FRONTEND_PID_FILE, "Next.js")


def kill_pid_file(pid_file: Path, label: str):
    """關閉指定 PID 檔案記錄的進程。"""
    if not pid_file.exists():
        return

    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, FileNotFoundError):
        pid_file.unlink(missing_ok=True)
        return

    if is_process_alive(pid):
        print(f"🔄 關閉前次 {label} 進程 (PID {pid})...")
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(50):
                if not is_process_alive(pid):
                    break
                time.sleep(0.1)
            else:
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
            print(f"   ✅ 已關閉 PID {pid}")
        except ProcessLookupError:
            pass

    pid_file.unlink(missing_ok=True)


def kill_port_occupant(port: int):
    """如果 port 被佔用，找到並關閉佔用進程。"""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True,
        )
        pids = result.stdout.strip().split("\n")
        for pid_str in pids:
            if pid_str.strip():
                pid = int(pid_str.strip())
                print(f"🔄 Port {port} 被 PID {pid} 佔用，正在關閉...")
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


def start_frontend():
    """啟動 Next.js 開發伺服器（背景執行）。"""
    if not FRONTEND_DIR.exists():
        print(f"⚠️  找不到前端目錄: {FRONTEND_DIR}")
        return None

    print(f"⚡ 啟動 Next.js 前端 (port {FRONTEND_PORT})...")
    print(f"   URL: http://localhost:{FRONTEND_PORT}")

    proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(FRONTEND_PORT)],
        cwd=str(FRONTEND_DIR),
    )

    FRONTEND_PID_FILE.write_text(str(proc.pid))
    return proc


def start_server(with_frontend=True):
    """啟動 uvicorn 開發伺服器（+可選 Next.js 前端）。"""
    python = find_python()

    # 啟動前端（背景）
    frontend_proc = None
    if with_frontend:
        frontend_proc = start_frontend()
        print()

    print(f"🚀 啟動 API 伺服器 (port {API_PORT})...")
    print(f"   Python: {python}")
    print(f"   URL: http://localhost:{API_PORT}")
    print(f"   Docs: http://localhost:{API_PORT}/api/v1/docs")
    print("   按 Ctrl+C 停止\n")

    # 啟動 uvicorn（前台執行，支持 --reload）
    backend_proc = subprocess.Popen(
        [python, "-m", "uvicorn", "app.main:app",
         "--reload", "--host", "0.0.0.0", "--port", str(API_PORT)],
        cwd=str(BACKEND_DIR),
    )

    # 寫入 PID
    PID_FILE.write_text(str(backend_proc.pid))

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n\n⏹️  收到 Ctrl+C，正在停止...")
        backend_proc.terminate()
        backend_proc.wait(timeout=5)
        if frontend_proc and frontend_proc.poll() is None:
            print("   停止 Next.js...")
            frontend_proc.terminate()
            frontend_proc.wait(timeout=5)
    finally:
        PID_FILE.unlink(missing_ok=True)
        FRONTEND_PID_FILE.unlink(missing_ok=True)


def stop_all():
    """停止所有服務。"""
    kill_previous()
    kill_port_occupant(API_PORT)
    kill_port_occupant(FRONTEND_PORT)
    stop_db()
    print("\n✅ 所有服務已停止")


def main():
    global API_PORT

    parser = argparse.ArgumentParser(description="CertiMate 本地開發伺服器")
    parser.add_argument("--stop", action="store_true", help="停止所有服務")
    parser.add_argument("--no-db", action="store_true", help="不啟動 DB（使用已有的）")
    parser.add_argument("--no-frontend", action="store_true", help="不啟動前端")
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
    kill_port_occupant(API_PORT)
    if not args.no_frontend:
        kill_port_occupant(FRONTEND_PORT)

    # 2. 啟動 DB
    if not args.no_db:
        start_db()

    # 3. 啟動 API server + Frontend
    start_server(with_frontend=not args.no_frontend)


if __name__ == "__main__":
    main()
