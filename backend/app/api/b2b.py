"""B2B API — 機構管理後台。"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user_id
from app.services.b2b_service import B2BService

router = APIRouter(prefix="/b2b")


def _handle_result(result: dict):
    if result.get("error"):
        status_code = result.get("status_code", 400)
        raise HTTPException(status_code=status_code, detail={"message": result["message"]})
    return result


@router.get("/dashboard")
def get_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = B2BService(db)
    result = service.get_dashboard(user_id=user_id)
    return _handle_result(result)


@router.post("/import-students")
async def import_students(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail={"message": "請上傳 .csv 格式的檔案"})

    content = await file.read()
    try:
        csv_text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail={"message": "檔案編碼錯誤，請使用 UTF-8 編碼"})

    service = B2BService(db)
    result = service.import_students(user_id=user_id, csv_content=csv_text)
    return _handle_result(result)
