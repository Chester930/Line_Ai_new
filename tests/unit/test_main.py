import pytest
from fastapi.testclient import TestClient
from src.main import create_app
from src.shared.config.manager import config_manager

@pytest.fixture
def client():
    """測試客戶端"""
    app = create_app()
    return TestClient(app)

def test_line_health_check(client):
    """測試 LINE 健康檢查"""
    response = client.get("/line/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_line_webhook_without_signature(client):
    """測試沒有簽名的 webhook"""
    response = client.post("/line/webhook")
    assert response.status_code == 422  # FastAPI 的驗證錯誤

def test_line_webhook_with_invalid_signature(client):
    """測試無效簽名的 webhook"""
    response = client.post(
        "/line/webhook",
        headers={"X-Line-Signature": "invalid"},
        json={"events": []}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "error"}

def test_cors_configuration(client):
    """測試 CORS 配置"""
    response = client.options(
        "/line/health",
        headers={
            "Origin": "http://localhost",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

def test_app_configuration():
    """測試應用配置"""
    app_config = config_manager.get_app_config()
    
    # 驗證必要的配置項
    assert "host" in app_config.to_dict()
    assert "port" in app_config.to_dict()
    assert "debug" in app_config.to_dict()

def test_line_configuration():
    """測試 LINE 配置"""
    line_config = config_manager.get_line_config()
    config_dict = line_config.to_dict()
    
    # 驗證必要的配置項
    assert "handlers" in config_dict
    assert "messages" in config_dict
    assert isinstance(config_dict["handlers"], dict)
    assert isinstance(config_dict["messages"], dict) 