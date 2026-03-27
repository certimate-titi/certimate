"""綠界金流串接 Service。"""

import hashlib
import time
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.user import User, SubscriptionPlan
from app.models.audit_log import AdminAuditLog
from app.models.user_usage import UserUsage


# 可覆寫的時間函數，測試時可替換
_now_func = None


def set_now_func(func):
    """設定自訂的時間函數（用於測試注入固定時間）。"""
    global _now_func
    _now_func = func


def _get_now():
    if _now_func is not None:
        return _now_func()
    return datetime.now(timezone.utc)


# 方案價格對照表
PLAN_PRICES = {
    "PRO_199": 199,
    "PRO_PLUS_399": 399,
    "ULTRA_1599": 1599,
}

# 方案名稱 → SubscriptionPlan enum 映射
PLAN_ENUM_MAP = {
    "PRO_199": SubscriptionPlan.PRO,
    "PRO_PLUS_399": SubscriptionPlan.PRO_PLUS,
    "ULTRA_1599": SubscriptionPlan.ULTRA,
}

# 預設綠界設定（測試環境）
ECPAY_CONFIG = {
    "MerchantID": "3002607",
    "HashKey": "pwFHCqoQZGmho4w6",
    "HashIV": "EkRm7iFT261dpevs",
    "ReturnURL": "https://api.certimate.tw/api/v1/ecpay/callback",
    "OrderResultURL": "https://certimate.tw/payment/result",
}


class ECPayService:
    def __init__(self, db: Session):
        self.db = db

    def create_order(self, user_id: str, target_plan: str) -> dict:
        """建立付款訂單並回傳綠界表單參數。"""
        user_uuid = uuid.UUID(user_id)

        # 驗證方案
        if target_plan not in PLAN_PRICES:
            return {"error": True, "status_code": 400, "message": "無效的訂閱方案"}

        # 檢查使用者
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        # 檢查是否已訂閱相同方案
        current_plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        target_enum = PLAN_ENUM_MAP.get(target_plan)
        if target_enum and current_plan == target_enum.value:
            return {"error": True, "status_code": 400, "message": "您已訂閱此方案，無須重複付款"}

        # 產生交易編號
        now = _get_now()
        trade_no = f"CRT{now.strftime('%Y%m%d%H%M%S')}{int(time.time() * 1000) % 10000:04d}"
        if len(trade_no) > 20:
            trade_no = trade_no[:20]

        amount = PLAN_PRICES[target_plan]
        trade_date = now.strftime("%Y/%m/%d %H:%M:%S")

        # 建立 pending 交易紀錄
        txn = Transaction(
            user_id=user_uuid,
            merchant_trade_no=trade_no,
            target_plan=target_plan,
            amount=Decimal(amount),
            status="pending",
            payment_provider="ecpay",
        )
        self.db.add(txn)
        self.db.commit()

        # 組裝綠界表單參數
        params = {
            "MerchantID": ECPAY_CONFIG["MerchantID"],
            "MerchantTradeNo": trade_no,
            "MerchantTradeDate": trade_date,
            "TotalAmount": str(amount),
            "TradeDesc": f"CertiMate {target_plan} 訂閱",
            "ItemName": f"CertiMate {target_plan} 月訂閱方案",
            "PaymentType": "aio",
            "ChoosePayment": "ALL",
            "EncryptType": "1",
            "ReturnURL": ECPAY_CONFIG["ReturnURL"],
            "OrderResultURL": ECPAY_CONFIG["OrderResultURL"],
        }

        # 計算 CheckMacValue
        params["CheckMacValue"] = self._calculate_mac(params)

        return params

    def handle_callback(self, form_data: dict) -> dict:
        """處理綠界回呼。"""
        trade_no = form_data.get("MerchantTradeNo", "")
        check_mac = form_data.get("CheckMacValue", "")

        # 驗證 CheckMacValue
        verify_params = {k: v for k, v in form_data.items() if k != "CheckMacValue"}
        expected_mac = self._calculate_mac(verify_params)
        if check_mac != expected_mac:
            return {"error": True, "status_code": 400, "body": "0|CheckMacValue verification failed"}

        # 查找交易紀錄
        txn = self.db.query(Transaction).filter_by(merchant_trade_no=trade_no).first()
        if not txn:
            return {"error": True, "body": "0|Transaction not found"}

        # 冪等：已處理的交易不再重複處理
        if txn.status in ("success", "failed"):
            return {"error": False, "body": "1|OK"}

        rtn_code = form_data.get("RtnCode", "")

        if str(rtn_code) == "1":
            # 付款成功
            txn.status = "success"
            txn.trade_no = form_data.get("TradeNo", "")
            txn.payment_type = form_data.get("PaymentType", "")
            txn.rtn_code = str(rtn_code)
            self.db.commit()

            # 更新使用者訂閱
            user = self.db.query(User).filter_by(id=txn.user_id).first()
            if user:
                previous_plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
                plan_enum = PLAN_ENUM_MAP.get(txn.target_plan)
                if plan_enum:
                    user.subscription_plan = plan_enum
                from app.models.user import SubscriptionStatus
                user.subscription_status = SubscriptionStatus.ACTIVE
                user.next_billing_date = _get_now() + timedelta(days=31)

                # 重置用量額度
                now = _get_now()
                period = now.strftime("%Y-%m")
                usage = self.db.query(UserUsage).filter_by(
                    user_id=txn.user_id, period=period
                ).first()
                if usage:
                    usage.daily_ai_chats_used = 0
                    usage.monthly_uploads_used = 0
                    usage.monthly_exams_used = 0
                    usage.monthly_vision_pages_used = 0
                    usage.last_reset_at = now

                # 記錄審計日誌
                audit = AdminAuditLog(
                    admin_id=txn.user_id,
                    action="subscription_upgrade",
                    target_type="user",
                    target_id=txn.user_id,
                    details={
                        "user_id": str(txn.user_id),
                        "previous_plan": previous_plan,
                        "new_plan": txn.target_plan,
                        "trigger": "ecpay_callback",
                        "transaction_id": txn.merchant_trade_no,
                    },
                )
                self.db.add(audit)
                self.db.commit()
        else:
            # 付款失敗
            txn.status = "failed"
            txn.rtn_code = str(rtn_code)
            self.db.commit()

        return {"error": False, "body": "1|OK"}

    def _calculate_mac(self, params: dict) -> str:
        """計算綠界 CheckMacValue（SHA256）。"""
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        raw = (
            f"HashKey={ECPAY_CONFIG['HashKey']}&"
            + "&".join(f"{k}={v}" for k, v in sorted_params)
            + f"&HashIV={ECPAY_CONFIG['HashIV']}"
        )
        encoded = urllib.parse.quote_plus(raw).lower()
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest().upper()
