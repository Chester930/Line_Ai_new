from typing import Dict, Any, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from .exceptions import BaseError
from .logger import logger

class ErrorHandler:
    """錯誤處理器"""
    
    @staticmethod
    async def handle_error(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """處理異常"""
        if isinstance(exc, BaseError):
            return await ErrorHandler._handle_known_error(exc)
        else:
            return await ErrorHandler._handle_unknown_error(exc)
    
    @staticmethod
    async def _handle_known_error(error: BaseError) -> JSONResponse:
        """處理已知錯誤"""
        logger.error(f"已知錯誤: {error.code} - {error.message}")
        
        response_data = {
            "success": False,
            "error": {
                "code": error.code,
                "message": error.message
            }
        }
        
        if error.details:
            response_data["error"]["details"] = error.details
            
        return JSONResponse(
            status_code=error.status_code,
            content=response_data
        )
    
    @staticmethod
    async def _handle_unknown_error(error: Exception) -> JSONResponse:
        """處理未知錯誤"""
        logger.error(f"未知錯誤: {str(error)}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "內部服務錯誤"
                }
            }
        )
    
    @staticmethod
    def format_error_response(
        message: str,
        code: str = "UNKNOWN_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """格式化錯誤響應"""
        response = {
            "success": False,
            "error": {
                "code": code,
                "message": message
            }
        }
        
        if details:
            response["error"]["details"] = details
            
        return response 