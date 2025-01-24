import time
from typing import Dict, Tuple
from fastapi import Request, Response
from .base import BaseMiddleware
from ..utils.exceptions import RateLimitError

class RateLimitMiddleware(BaseMiddleware):
    """請求限制中間件"""
    
    def __init__(
        self,
        rate_limit: int = 60,  # 每分鐘請求數
        window_size: int = 60   # 時間窗口（秒）
    ):
        super().__init__()
        self.rate_limit = rate_limit
        self.window_size = window_size
        self._requests: Dict[str, list] = {}  # {ip: [timestamp, ...]}
    
    async def _process_request(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """處理請求"""
        client_ip = self._get_client_ip(request)
        
        # 檢查並更新請求記錄
        self._update_request_records(client_ip)
        
        # 檢查是否超過限制
        if self._is_rate_limited(client_ip):
            raise RateLimitError(
                message="請求過於頻繁，請稍後再試",
                details={
                    "limit": self.rate_limit,
                    "window_size": self.window_size,
                    "remaining_time": self._get_reset_time(client_ip)
                }
            )
        
        # 添加新請求記錄
        self._add_request_record(client_ip)
        
        return await call_next(request)
    
    def _update_request_records(self, client_ip: str):
        """更新請求記錄"""
        if client_ip not in self._requests:
            self._requests[client_ip] = []
        
        # 清理過期記錄
        current_time = time.time()
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip]
            if current_time - ts < self.window_size
        ]
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """檢查是否超過限制"""
        return len(self._requests.get(client_ip, [])) >= self.rate_limit
    
    def _add_request_record(self, client_ip: str):
        """添加請求記錄"""
        self._requests[client_ip].append(time.time())
    
    def _get_reset_time(self, client_ip: str) -> int:
        """獲取重置時間（秒）"""
        if not self._requests.get(client_ip):
            return 0
        
        oldest_request = min(self._requests[client_ip])
        return int(self.window_size - (time.time() - oldest_request)) 