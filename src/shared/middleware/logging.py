import time
from typing import Optional
from fastapi import Request, Response
from .base import BaseMiddleware

class LoggingMiddleware(BaseMiddleware):
    """日誌中間件"""
    
    async def _process_request(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """處理請求"""
        # 記錄請求開始
        start_time = time.time()
        request_id = self._generate_request_id(request)
        
        # 記錄請求信息
        self._log_request(request, request_id)
        
        # 處理請求
        response = await call_next(request)
        
        # 記錄響應信息
        self._log_response(
            request,
            response,
            request_id,
            time.time() - start_time
        )
        
        return response
    
    def _generate_request_id(self, request: Request) -> str:
        """生成請求 ID"""
        return request.headers.get(
            "X-Request-ID",
            f"req_{int(time.time() * 1000)}"
        )
    
    def _log_request(self, request: Request, request_id: str):
        """記錄請求"""
        self.logger.info(
            f"Request {request_id}: "
            f"{request.method} {request.url.path} "
            f"from {self._get_client_ip(request)}"
        )
        
        # 記錄請求頭
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in {"authorization", "cookie"}
        }
        self.logger.debug(f"Request headers: {headers}")
    
    def _log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        duration: float
    ):
        """記錄響應"""
        self.logger.info(
            f"Response {request_id}: "
            f"{response.status_code} "
            f"completed in {duration:.3f}s"
        )
        
        # 記錄響應頭
        self.logger.debug(f"Response headers: {dict(response.headers)}") 