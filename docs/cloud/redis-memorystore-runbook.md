# Redis Memorystore 部署 Runbook（Sprint 8 T67）

> **Sprint 8 T58 已把 plan claim 接好但限流仍走 in-memory，原因：Cloud Run 多實例間計數不共享 → 限流值會被個別實例分攤。本 runbook 為 Memorystore 起服務的步驟（一次性，由 SUPER_ADMIN 執行）。**

## 前置確認

| 項目 | 檢查 |
|------|------|
| Cloud Run service | `certimate-titi`（asia-east1）|
| `app/core/rate_limit.py` | `_RedisTokenBucket` 已實作（Sprint 1 留下）|
| `REDIS_URL` env var | 目前 **未設定** → fallback in-memory |
| 預估月成本 | M1（1 GB / Basic）≈ USD $25/month、M0（256 MB）≈ USD $13/month |

## 實作步驟

### 1. 建立 VPC connector（Cloud Run 連 Memorystore 必要）

```bash
gcloud compute networks vpc-access connectors create certimate-vpc \
  --region=asia-east1 \
  --network=default \
  --range=10.8.0.0/28 \
  --min-instances=2 \
  --max-instances=3
```

預估成本：connector idle ≈ USD $9/month；scale up 時加計流量。

### 2. 建立 Memorystore Redis 實例（M0 起步）

```bash
gcloud redis instances create certimate-rate-limit \
  --size=1 \
  --region=asia-east1 \
  --tier=basic \
  --redis-version=redis_7_0 \
  --network=default
```

> **採用 Basic tier 不啟 HA**：限流是無狀態 / 可降級（in-memory fallback）資料，不需 Standard。
> M0 不存在 — 最小是 size=1（1GB）。如需更省可改 GCP **Memorystore for Redis Cluster** node type C0。

### 3. 取得連線資訊

```bash
gcloud redis instances describe certimate-rate-limit \
  --region=asia-east1 \
  --format='value(host,port)'
```

輸出例：`10.234.0.3 6379`

### 4. 寫入 Secret Manager（避免明文暴露）

```bash
echo "redis://10.234.0.3:6379/0" | gcloud secrets create redis-url \
  --data-file=- --replication-policy=automatic

# 授權 Cloud Run runtime SA 讀取
RUNTIME_SA="certimate-runtime@certimate-titi.iam.gserviceaccount.com"
gcloud secrets add-iam-policy-binding redis-url \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/secretmanager.secretAccessor"
```

### 5. Cloud Run service 加 VPC connector + REDIS_URL

```bash
gcloud run services update certimate-titi \
  --region=asia-east1 \
  --vpc-connector=certimate-vpc \
  --vpc-egress=private-ranges-only \
  --update-secrets=REDIS_URL=redis-url:latest
```

`vpc-egress=private-ranges-only` 確保只有私網流量走 connector，公網仍走原路徑（省成本 + 無 latency 衝擊）。

### 6. 驗證

部署完成後查 startup log：

```bash
gcloud logging read 'resource.type="cloud_run_revision" \
  resource.labels.service_name="certimate-titi" \
  textPayload:"Rate Limit Redis"' --limit=5 --freshness=10m
```

應看到 `✅ Rate Limit Redis 連線成功：redis://10.234.0.3:6379/0`。
若看到 `redis 套件未安裝` 或 `Redis 連線失敗，使用記憶體模式` → 回退步驟 5 再檢查 `REDIS_URL` secret 與 VPC connector。

### 7. 回退（如需）

```bash
gcloud run services update certimate-titi \
  --region=asia-east1 \
  --remove-secrets=REDIS_URL \
  --clear-vpc-connector
gcloud redis instances delete certimate-rate-limit --region=asia-east1
gcloud compute networks vpc-access connectors delete certimate-vpc --region=asia-east1
```

服務自動 fallback in-memory，零停機。

## 成本對照（asia-east1，2026-05 公告價）

| 元件 | 規格 | 月成本估 |
|------|------|---------|
| Memorystore Redis Basic 1 GB | 24/7 | ~ USD $25 |
| VPC Access Connector | 2 idle instances | ~ USD $9 |
| **合計** | | **~ USD $34/month** |

> **觸發條件建議**：MAU ≥ 500 或單日 429 次數 > 1000 時啟動。在那之前 in-memory 已足夠（單實例 + 限流屬「軟性公平 throttle」，不影響業務正確性）。

## 與 T58 plan claim 配合

T58 已讓 JWT 帶 `plan` claim，PRO 60 QPS、ULTRA 200 QPS。但目前 in-memory：

- 單 Cloud Run instance：限流準確
- 多 instance scale up 時：每 instance 各算自己的 bucket（總 QPS 上限 = N × tier_qps）
- Redis 上線後：跨 instance 共享 bucket，總 QPS 嚴格按 tier 限制

對 Free 用戶不公平的情境僅在 cold start 後立即發大量請求觸發；多數場景仍是「軟性 throttle」。

---

**負責角色**：雲端工程師（執行）+ 財務（成本核對）+ SUPER_ADMIN（操作授權）。
**啟動時機**：Sprint 9 起始 / MAU 觸發其一。
