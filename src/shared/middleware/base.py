from typing import Callable, Dict, Optional
from fastapi import Request, Response
from ..utils.logger import logger, log_execution_time
from ..utils.exceptions import RateLimitError

class BaseMiddleware:
    """基礎中間件"""
    
    def __init__(self):
        self.logger = logger
    
    async def __call__(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """中間件調用"""
        try:
            response = await self._process_request(request, call_next)
            await self._process_response(response)
            return response
        except Exception as e:
            self.logger.error(f"中間件處理錯誤: {str(e)}")
            raise
    
    async def _process_request(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """處理請求"""
        return await call_next(request)
    
    async def _process_response(self, response: Response):
        """處理響應"""
        pass

    def _get_client_ip(self, request: Request) -> str:
        """獲取客戶端 IP"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0]
        return request.client.host if request.client else "unknown"
    
    def _get_request_path(self, request: Request) -> str:
        """獲取請求路徑"""
        return f"{request.method} {request.url.path}" 