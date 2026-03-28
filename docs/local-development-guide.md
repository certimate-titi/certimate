# CertiMate 本地開發環境指南

## 前置需求

| 工具 | 最低版本 | 用途 |
|------|---------|------|
| Docker Desktop | 28+ | PostgreSQL 容器、Testcontainers |
| Node.js | 24+ | 前端 Next.js |
| Python | 3.11+ | 後端 FastAPI |
| pip | 25+ | Python 套件管理 |

> Docker Desktop 必須在運行中，後端資料庫與 BDD 測試皆依賴 Docker daemon。

---

## 一、後端啟動

### 1.1 啟動 PostgreSQL

```bash
cd project/backend
docker compose up -d
```

確認容器狀態為 healthy：

```bash
docker compose ps
```

預期輸出：`certimate-api-postgres` 狀態為 `running (healthy)`。

資料庫預設連線資訊：

| 項目 | 值 |
|------|---|
| Host | localhost |
| Port | 5432 |
| User | postgres |
| Password | postgres |
| Database | certimate-api_dev |

### 1.2 安裝 Python 依賴（首次）

```bash
pip install -r requirements.txt
```

### 1.3 執行資料庫 Migration

```bash
python -m alembic upgrade head
```

此指令會套用 `alembic/versions/` 下的 16 個 migration，建立 42 張資料表。

驗證：

```bash
docker exec certimate-api-postgres psql -U postgres -d certimate-api_dev -c "\dt" | head -20
```

### 1.4 啟動 FastAPI 開發伺服器

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

驗證端點：

| URL | 說明 |
|-----|------|
| http://localhost:8000/health | 健康檢查 |
| http://localhost:8000/api/v1/docs | Swagger API 文件 |
| http://localhost:8000/api/v1/redoc | ReDoc API 文件 |

---

## 二、前端啟動

### 2.1 安裝 Node.js 依賴（首次）

```bash
cd project/frontend
npm install
```

### 2.2 設定環境變數

```bash
cp .env.example .env.local
```

編輯 `.env.local`：

```env
GEMINI_API_KEY="你的 Google Gemini API Key"
APP_URL="http://localhost:3000"
NEXT_PUBLIC_FIREBASE_API_KEY="你的 Firebase API Key"
```

| 變數 | 必要性 | 說明 |
|------|--------|------|
| `GEMINI_API_KEY` | 選用 | 缺少時 AI 功能（知識心智圖、AI 考題生成）不可用，其他頁面正常 |
| `APP_URL` | 必要 | 設為 `http://localhost:3000` |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | 必要 | Firebase Auth 登入需要；缺少時可使用 localStorage demo 模式 |

### 2.3 啟動 Next.js 開發伺服器

```bash
npm run dev
```

瀏覽器開啟 http://localhost:3000

---

## 三、執行 BDD E2E 測試

BDD 測試使用 Testcontainers，會**自動啟動獨立的 PostgreSQL 容器**，不需要手動啟動 `docker compose`。

```bash
cd project/backend
```

### 執行全部已完成的測試

```bash
python -m behave tests/features/ --tags=~@ignore
```

### 執行特定 Feature

```bash
python -m behave tests/features/01-身分驗證.feature
```

### 執行特定 Scenario（依標籤）

```bash
python -m behave tests/features/ --tags=@auth
```

### 測試輸出格式

預設使用 `pretty` 格式（彩色輸出）。設定位於 `behave.ini`。

---

## 四、常用指令速查

### 後端

```bash
# 啟動 / 停止 PostgreSQL
docker compose up -d
docker compose down

# 資料庫 migration
python -m alembic upgrade head          # 套用全部 migration
python -m alembic downgrade -1          # 回滾一步
python -m alembic current               # 查看目前版本

# 啟動 API 伺服器
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 程式碼品質
black .                                 # 格式化
isort .                                 # import 排序
mypy app/                               # 型別檢查
```

### 前端

```bash
# 開發伺服器
npm run dev

# 正式建置（靜態匯出）
npm run build

# ESLint 檢查
npm run lint

# 清除 Next.js 快取
npm run clean
```

---

## 五、常見問題

### Q: `docker compose up` 時 port 5432 已被佔用

```bash
# 找出佔用 port 的程序
lsof -i :5432
# 或修改 docker-compose.yml 將 port 改為其他（如 5433:5432）
# 同時更新 alembic.ini 與 config.py 的連線字串
```

### Q: Alembic migration 失敗

```bash
# 確認 PostgreSQL 容器已 healthy
docker compose ps
# 確認連線字串正確
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

### Q: Testcontainers 無法啟動

確認 Docker Desktop 正在運行：

```bash
docker info > /dev/null 2>&1 && echo "Docker OK" || echo "Docker not running"
```

### Q: 前端 API 呼叫返回錯誤

目前前端 `lib/api/services.ts` 回傳 mock 資料，尚未連接後端 API。若要測試前後端整合，需修改 `lib/api/client.ts` 將 base URL 指向 `http://localhost:8000`。
