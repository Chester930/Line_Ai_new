import pytest
import jwt
import hashlib
from unittest.mock import patch
from src.shared.config.base import ConfigManager
from src.shared.line_sdk.client import LineClient
from src.shared.utils.security import SecurityUtils

class TestSecurity:
    @pytest.fixture
    def setup(self):
        config = ConfigManager()
        config.set("LINE_CHANNEL_SECRET", "test_secret")
        config.set("JWT_SECRET", "test_jwt_secret")
        return config
        
    def test_webhook_signature_validation(self, setup):
        """測試 Webhook 簽名驗證"""
        client = LineClient(
            channel_secret=setup.get("LINE_CHANNEL_SECRET"),
            channel_access_token="test_token"
        )
        
        # 生成測試數據
        body = b'{"events":[{"type":"message"}]}'
        signature = hashlib.sha256(
            (setup.get("LINE_CHANNEL_SECRET") + body.decode()).encode()
        ).hexdigest()
        
        # 驗證簽名
        assert client.verify_signature(signature, body)
        assert not client.verify_signature("invalid_signature", body)
        
    def test_jwt_token_security(self, setup):
        """測試 JWT 令牌安全性"""
        # 生成令牌
        payload = {"user_id": "test_user", "role": "user"}
        token = jwt.encode(
            payload,
            setup.get("JWT_SECRET"),
            algorithm="HS256"
        )
        
        # 驗證令牌
        decoded = jwt.decode(
            token,
            setup.get("JWT_SECRET"),
            algorithms=["HS256"]
        )
        assert decoded["user_id"] == "test_user"
        
        # 測試令牌篡改
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(
                token + "tampered",
                setup.get("JWT_SECRET"),
                algorithms=["HS256"]
            )
            
    def test_input_sanitization(self, setup):
        """測試輸入數據清理"""
        utils = SecurityUtils()
        
        # 測試 XSS 防護
        malicious_input = "<script>alert('xss')</script>"
        sanitized = utils.sanitize_input(malicious_input)
        assert "<script>" not in sanitized
        
        # 測試 SQL 注入防護
        sql_injection = "'; DROP TABLE users; --"
        sanitized = utils.sanitize_input(sql_injection)
        assert "DROP TABLE" not in sanitized
        
    def test_rate_limiting(self, setup):
        """測試速率限制"""
        utils = SecurityUtils()
        
        # 模擬請求
        user_id = "test_user"
        
        # 正常請求
        for _ in range(5):
            assert utils.check_rate_limit(user_id)
            
        # 超出限制
        assert not utils.check_rate_limit(user_id) 