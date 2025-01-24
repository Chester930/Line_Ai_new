from fastapi import APIRouter, Header, Request
from .handler import line_handler
from ..shared.utils.logger import logger

router = APIRouter()

@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(None)
):
    """LINE Webhook 端點"""
    try:
        # 讀取請求內容
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # 處理 webhook 事件
        if await line_handler.handle_request(
            request,
            body_str,
            x_line_signature
        ):
            return {"status": "success"}
        else:
            return {"status": "error"}
            
    except Exception as e:
        logger.error(f"Webhook 處理失敗: {str(e)}")
        return {"status": "error"}

@router.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "ok"} 