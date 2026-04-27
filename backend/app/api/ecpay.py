"""ECPay API — 綠界金流串接。"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user_id
from app.services.ecpay_service import ECPayService

router = APIRouter(prefix="/ecpay")


class CreateOrderRequest(BaseModel):
    target_plan: str


@router.post("/create-order")
def create_order(
    body: CreateOrderRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """create order。

    此 endpoint 對應 `create_order` 操作。

    Args:
        body: 參數。

    Returns:
        回應內容（依 response_model 定義）。
    """
    service = ECPayService(db)
    result = service.create_order(user_id=user_id, target_plan=body.target_plan)
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail={"message": result["message"]},
        )
    return result


@router.post("/callback")
async def ecpay_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """ecpay callback。

    此 endpoint 對應 `ecpay_callback` 操作。

    Returns:
        回應內容（依 response_model 定義）。
    """
    form_data = await request.form()
    form_dict = dict(form_data)

    service = ECPayService(db)
    result = service.handle_callback(form_dict)

    status_code = result.get("status_code", 200)
    return PlainTextResponse(content=result["body"], status_code=status_code)
