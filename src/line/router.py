from fastapi import APIRouter, Header, Request
from .handler import line_handler
from ..shared.utils.logger import logger

router = APIRouter()

@router.post("/webhook")
async def webhook(request: Request):
    """處理 LINE webhook 請求"""
    body = await request.body()
    signature = request.headers.get("X-Line-Signature")
    return await line_handler.handle_request(request, body, signature)

@router.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "ok"} 