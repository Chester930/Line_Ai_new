import pytest
from fastapi import FastAPI, Request, Response
from src.shared.middleware.rate_limit import RateLimitMiddleware
from src.shared.middleware.logging import LoggingMiddleware
from src.shared.utils.exceptions import RateLimitError

@pytest.fixture
def app():
    """測試應用"""
    app = FastAPI()
    return app

@pytest.fixture
def rate_limit_middleware():
    """速率限制中間件"""
    return RateLimitMiddleware(rate_limit=2, window_size=5)

@pytest.fixture
def logging_middleware():
    """日誌中間件"""
    return LoggingMiddleware()

@pytest.mark.asyncio
async def test_rate_limit(rate_limit_middleware):
    """測試請求限制"""
    request = Request(scope={
        "type": "http",
        "method": "GET",
        "path": "/test",
        "client": ("127.0.0.1", 8000)
    })
    
    # 第一個請求應該成功
    async def call_next(request):
        return Response()
    
    response = await rate_limit_middleware._process_request(request, call_next)
    assert isinstance(response, Response)
    
    # 第二個請求應該成功
    response = await rate_limit_middleware._process_request(request, call_next)
    assert isinstance(response, Response)
    
    # 第三個請求應該被限制
    with pytest.raises(RateLimitError):
        await rate_limit_middleware._process_request(request, call_next)

@pytest.mark.asyncio
async def test_logging(logging_middleware):
    """測試日誌記錄"""
    request = Request(scope={
        "type": "http",
        "method": "GET",
        "path": "/test",
        "client": ("127.0.0.1", 8000),
        "headers": []
    })
    
    async def call_next(request):
        return Response(status_code=200)
    
    response = await logging_middleware._process_request(request, call_next)
    assert isinstance(response, Response)
    assert response.status_code == 200

def test_client_ip_detection(rate_limit_middleware):
    """測試客戶端 IP 檢測"""
    request = Request(scope={
        "type": "http",
        "method": "GET",
        "path": "/test",
        "client": ("127.0.0.1", 8000),
        "headers": [(b"x-forwarded-for", b"1.2.3.4")]
    })
    
    ip = rate_limit_middleware._get_client_ip(request)
    assert ip == "1.2.3.4" 