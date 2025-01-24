import pytest
from fastapi import Request
from src.shared.utils.exceptions import (
    ValidationError,
    AIModelError,
    SessionError,
    RateLimitError
)
from src.shared.utils.error_handler import ErrorHandler

@pytest.fixture
def mock_request():
    """模擬請求"""
    return Request({"type": "http", "method": "GET", "path": "/"})

@pytest.mark.asyncio
async def test_validation_error_handling(mock_request):
    """測試驗證錯誤處理"""
    error = ValidationError("無效的輸入", {"field": "username"})
    response = await ErrorHandler.handle_error(mock_request, error)
    
    assert response.status_code == 400
    assert "validation_error" in response.body.decode().lower()
    
@pytest.mark.asyncio
async def test_model_error_handling(mock_request):
    """測試模型錯誤處理"""
    error = AIModelError("模型調用失敗", {"model": "gemini"})
    response = await ErrorHandler.handle_error(mock_request, error)
    
    assert response.status_code == 500
    assert "model_error" in response.body.decode().lower()

@pytest.mark.asyncio
async def test_session_error_handling(mock_request):
    """測試會話錯誤處理"""
    error = SessionError("會話已過期")
    response = await ErrorHandler.handle_error(mock_request, error)
    
    assert response.status_code == 400
    assert "session_error" in response.body.decode().lower()

@pytest.mark.asyncio
async def test_rate_limit_error_handling(mock_request):
    """測試頻率限制錯誤處理"""
    error = RateLimitError("請求過於頻繁")
    response = await ErrorHandler.handle_error(mock_request, error)
    
    assert response.status_code == 429
    assert "rate_limited" in response.body.decode().lower()

@pytest.mark.asyncio
async def test_unknown_error_handling(mock_request):
    """測試未知錯誤處理"""
    error = Exception("未知錯誤")
    response = await ErrorHandler.handle_error(mock_request, error)
    
    assert response.status_code == 500
    assert "internal_error" in response.body.decode().lower()

def test_error_response_formatting():
    """測試錯誤響應格式化"""
    response = ErrorHandler.format_error_response(
        message="測試錯誤",
        code="TEST_ERROR",
        status_code=400,
        details={"test": "detail"}
    )
    
    assert response["success"] is False
    assert response["error"]["code"] == "TEST_ERROR"
    assert response["error"]["message"] == "測試錯誤"
    assert response["error"]["details"]["test"] == "detail" 