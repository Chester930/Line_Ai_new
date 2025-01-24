from typing import Optional, Dict, Any

class BaseError(Exception):
    """基礎錯誤類"""
    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ConfigError(BaseError):
    """配置錯誤"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="CONFIG_ERROR",
            status_code=500,
            details=details
        )

class ValidationError(BaseError):
    """驗證錯誤"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class AIModelError(BaseError):
    """AI 模型錯誤"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="MODEL_ERROR",
            status_code=500,
            details=details
        )

class SessionError(BaseError):
    """會話錯誤"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="SESSION_ERROR",
            status_code=400,
            details=details
        )

class RateLimitError(BaseError):
    """頻率限制錯誤"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="RATE_LIMITED",
            status_code=429,
            details=details
        )

class LineAPIError(BaseError):
    """LINE API 錯誤"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="LINE_API_ERROR",
            status_code=500,
            details=details
        ) 