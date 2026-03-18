# 會員中心與訂閱管理 (Account & Billing)

## 📌 頁面定位與目標

提供使用者管理個人資料、設定偏好以及 **升級/查閱訂閱狀態** 的整合入口。設計應保持簡單明瞭，減少退訂時的摩擦力，提升信任感。

## 🧩 核心分頁設計 (Tabs)

### 1. 個人資料 (Profile Settings)

- **大頭貼與基本資訊**：姓名、顯示名稱、Email 的修改。
- **密碼管理**：變更密碼功能。
- **危險區域 (Danger Zone)**：包含「匯出我的所有資料」與「刪除帳號」的按鈕，需有再三確認的彈窗 (Confirmation Modal)。

### 2. 訂閱與帳單 (Subscription & Billing)

- **目前方案卡片 (Current Plan)**：
  - 清楚標示使用者當前的方案 (Free / Pro / Ultra)。
  - 若為付費版本，顯示下一次扣款日期與金額。
- **升級/變更方案區**：
  - 若為 Free 用戶：顯示升級 Pro 或 Ultra 的行動呼籲與功能比較表。
  - 若為付費戶：提供「取消訂閱 (Cancel Subscription)」的無痛連結（避免隱匿取消路徑造成客訴）。
- **帳單歷史紀錄 (Billing History)**：
  - 條列過去每月的扣款紀錄，並提供發票 / 收據 PDF 下載按鈕。

### 3. 系統偏好設定 (Preferences)

- **介面設定**：淺色 / 深色模式 (Light / Dark Theme) 切換。
- **通知設定**：是否接收「每日複習提醒信」、「考前一週衝刺信」等 Email。

## 💻 技術面/實作建議

- **Stripe / 第三方金流整合 (Customer Portal)**：
  - 強烈建議不要自己寫信用卡表單與歷史帳單 UI。
  - 當使用者點擊「管理訂閱」時，直接 Redirect (導航) 至 **Stripe Customer Portal**。在該 Portal 內，使用者可以安全地更換信用卡、下載收據或取消訂閱。
  - 處理 Webhooks 接收金流平台的訂閱狀態更新 (如 `subscription.updated` 或 `invoice.payment_succeeded`)，同步回 CertiMate 的資料庫。
