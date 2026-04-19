# Super Admin 權限設計與稽核規範

**文件編號**: SEC-cost-monitor-permissions
**產出角色**: 安全工程師（CTO 技術線）
**產出日期**: 2026-04-14
**狀態**: Draft v1（待 CTO Review）
**對應 Feature**: 33 — 成本監控中心
**對應程式碼**: `backend/app/core/permissions.py`

---

## 1. 現況盤點

### 1.1 已存在的權限資產
| 項目 | 位置 | 狀態 |
|------|------|------|
| `UserRole.SUPER_ADMIN` enum | `backend/app/models/user.py:50` | ✅ 已存在 |
| JWT payload `role` claim | `backend/app/core/deps.py:104` | ✅ 已存在 |
| `admin_audit_logs` 表 | `backend/app/models/audit_log.py` | ✅ 已存在 |
| `require_admin` dependency | 無（既有 admin router 未統一） | ⚠️ 分散實作 |

### 1.2 gap 分析
- **無統一的 `require_super_admin` dependency** — 本次新增
- **既有 admin router 各自實作權限檢查** — 本次不改動，只為成本監控提供新 dependency

## 2. 設計決策

### 2.1 以 DB 為真實來源，JWT role 僅作快取
```python
payload = _decode_jwt_payload(credentials)   # 讀 JWT
user = db.query(User).filter(User.id == user_id).first()  # 再查 DB
if user.role != UserRole.SUPER_ADMIN:
    raise 403
```

**理由**：
- JWT 是 stateless，使用者角色被降級時 JWT 仍有效 → 有安全風險
- 成本監控是高敏感操作，多一次 DB 查詢的開銷可接受
- DB 查詢 User by id 本來就會走 primary key 索引，成本可忽略

### 2.2 錯誤代碼統一
固定使用 `FORBIDDEN_SUPER_ADMIN_ONLY`，與 Feature File 33 的 Scenario 一致。

### 2.3 稽核 action 常數化
新增 `AuditAction` class 集中管理所有 Feature 33 的 action 字串，避免：
- 字串拼寫錯誤（例如 `BUDGET_UPDATE` vs `BUDGET_UPDATED`）
- 未來修改時散落各處漏改

## 3. 稽核日誌整合規範

### 3.1 所有 Super Admin 操作必寫稽核

| 操作 | action 常數 | details 最小欄位 |
|------|------------|-----------------|
| 查看成本監控頁面 | `COST_MONITOR_VIEWED` | `{"endpoint": "/cost/summary"}` |
| 修改單一 scope 預算 | `BUDGET_UPDATED` | `{"scope": "AI_ANTHROPIC", "before": 700, "after": 800, "reason": "..."}` |
| 整體 %調整 | `BUDGET_GLOBAL_SCALED` | `{"scale_factor": 1.2, "before": {...}, "after": {...}, "reason": "..."}` |
| 整體設固定金額 | `BUDGET_GLOBAL_SET` | `{"target_total_usd": 1500, "before": {...}, "after": {...}, "reason": "..."}` |
| 手動解除停用 | `BUDGET_OVERRIDE` | `{"scope": "AI_VOYAGE", "overridden_until": "...", "reason": "..."}` |
| 擴充預算觸發佇列恢復 | `BUDGET_RECOVERY_TRIGGERED` | `{"scope": "AI_VOYAGE", "recovered_count": 3}` |

### 3.2 寫入範例

```python
from app.core.permissions import AuditAction
from app.models.audit_log import AdminAuditLog

def update_budget_with_audit(
    db: Session, super_admin: User, scope: str, new_limit: Decimal, reason: str
):
    old_config = db.query(BudgetConfig).filter_by(scope=scope).first()
    before_value = float(old_config.monthly_limit_usd)

    old_config.monthly_limit_usd = new_limit
    old_config.updated_by = super_admin.id

    audit = AdminAuditLog(
        admin_id=super_admin.id,
        action=AuditAction.BUDGET_UPDATED,
        target_type="budget_config",
        target_id=old_config.id,
        details={
            "scope": scope,
            "before": before_value,
            "after": float(new_limit),
            "reason": reason,
        },
    )
    db.add(audit)
    db.commit()
```

### 3.3 稽核記錄不可刪除
- `admin_audit_logs` 表沒有 `delete` endpoint
- 若未來需要資料保留期限管理，應另建歸檔表而非刪除

## 4. 多層權限防護

```
第一層：前端 UI
  └── useCurrentUser().role !== 'super_admin' → 不渲染選單項

第二層：FastAPI Router
  └── @router.get(..., dependencies=[Depends(require_super_admin)])
        └── 401 若 JWT 無效
        └── 403 若 DB 中 role != super_admin

第三層：Service 層
  └── 不信任 Router 的檢查，關鍵操作再次檢查 current_user.role

第四層：DB 約束
  └── budget_config.updated_by FK → users.id
        若未來加 CHECK 確認 updated_by 的 role（本次不做）
```

**原則**：前端隱藏 ≠ 安全，必須後端 API 層也擋。兩層都要做。

## 5. 安全測試計畫（供測試工程師參考）

### 5.1 必測 Scenario（已在 Feature File 33 涵蓋）
- [x] `super_admin 成功取得當月成本總覽`
- [x] `一般 admin 存取被拒絕` → 驗證 403 + `FORBIDDEN_SUPER_ADMIN_ONLY`
- [x] `一般 user 存取被拒絕`
- [x] `一般 admin 修改預算被拒絕`
- [x] `一般 admin 執行整體調整被拒絕`

### 5.2 額外建議測試（補充，可選）
- [ ] JWT 過期 → 401
- [ ] JWT 角色為 super_admin 但 DB 中已降級 → 403（驗證 DB 為真實來源）
- [ ] 無 `Authorization` header → 401
- [ ] 直接打 API 不經前端 → 仍擋（驗證後端獨立防護）

## 6. 憑證管理

### 6.1 Super Admin 帳號設定
- 首個 Super Admin 必須**手動在 DB 設定**（不可透過註冊或升級流程）：
```sql
UPDATE users SET role = 'super_admin' WHERE email = 'super@certimate.com';
```
- 本專案 Seed 腳本建議新增 Super Admin seed（供開發環境）

### 6.2 GCP 服務帳號憑證（雲端工程師交付）
- **禁止 commit**：`*.json` 服務帳號金鑰必須進 `.gitignore`
- **存放位置**：Cloud Run 部署環境使用 **GCP Secret Manager**，本地開發使用環境變數
- **最小權限原則**：服務帳號僅需 `BigQuery Data Viewer` + `BigQuery Job User` 兩個角色，**不得**給 `Owner` 或 `Editor`

## 7. 給 CTO 的三句話

1. 新增 `require_super_admin()` dependency **以 DB 為真實來源**，JWT role 僅作快取，避免降級後舊 Token 繼續生效
2. 所有 Super Admin 操作透過 `AuditAction` 常數集中管理，稽核欄位必填 `before/after/reason`
3. 前端隱藏 ≠ 安全，**後端 API 必須獨立擋**，測試工程師需補「直接打 API」的案例
