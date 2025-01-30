import pytest
from src.shared.config.validator import ConfigValidator, ValidationRule, ValidationError
from src.shared.config.base import BaseConfig, ConfigError
from typing import Optional, List
import json
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)

class SampleConfig(BaseConfig):  # 改名以避免被視為測試類
    """測試配置類"""
    api_key: str
    port: int
    debug: bool = False
    allowed_hosts: List[str] = ["localhost"]
    max_connections: Optional[int] = None
    config_path: Optional[Path] = None
    name: str = ""
    age: int = 0
    email: str = ""
    score: float = 0.0
    settings: dict = {}
    
    def _load_config(self) -> None:
        """載入配置"""
        try:
            if not self.config_path:
                self._config = self.model_dump(exclude={'config_path'})
                return
            
            if not self.config_path.exists():
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                self.config_path.write_text("{}")
            
            self._config = json.loads(self.config_path.read_text())
            logger.info(f"已載入配置: {self.config_path}")
            
            # 更新實例屬性
            for key, value in self._config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
        except Exception as e:
            logger.error(f"載入配置失敗: {str(e)}")
            self._config = {}
    
    def save(self) -> bool:
        """保存配置"""
        try:
            if not self.config_path:
                return False
            
            # 合併實例屬性和配置字典
            data = self.model_dump(exclude={'config_path'})
            data.update(self._config)
            
            # 將 Path 對象轉換為字符串
            def convert_path(obj):
                if isinstance(obj, Path):
                    return str(obj)
                elif isinstance(obj, dict):
                    return {k: convert_path(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_path(x) for x in obj]
                return obj
            
            data = convert_path(data)
            
            # 確保目標目錄存在
            if self.config_path:
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.config_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False)
            )
            logger.info(f"已保存配置: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失敗: {str(e)}")
            return False

@pytest.fixture
def validator():
    """提供配置驗證器實例"""
    return ConfigValidator()

@pytest.fixture
def sample_config():
    """提供測試配置數據"""
    return {
        "app": {
            "name": "test_app",
            "port": 8080,
            "debug": True,
            "allowed_hosts": ["localhost", "127.0.0.1"]
        },
        "database": {
            "url": "sqlite:///test.db",
            "max_connections": 5,
            "timeout": 30
        },
        "logging": {
            "level": "INFO",
            "file": "app.log"
        }
    }

def test_required_field_validation(validator, sample_config):
    """測試必需字段驗證"""
    # 添加必需字段規則
    validator.add_rule(
        ValidationRule("app.name").required()
    )
    validator.add_rule(
        ValidationRule("database.url").required()
    )
    
    # 驗證有效配置
    assert validator.validate(sample_config) is True
    
    # 刪除必需字段
    invalid_config = sample_config.copy()
    del invalid_config["app"]["name"]
    
    # 驗證無效配置
    with pytest.raises(ValidationError):
        validator.validate(invalid_config)

def test_type_validation(validator, sample_config):
    """測試類型驗證"""
    validator.add_rule(
        ValidationRule("app.port").type(int)
    )
    validator.add_rule(
        ValidationRule("app.debug").type(bool)
    )
    validator.add_rule(
        ValidationRule("app.allowed_hosts").type(list)
    )
    
    # 驗證有效配置
    assert validator.validate(sample_config) is True
    
    # 測試無效類型
    invalid_config = sample_config.copy()
    invalid_config["app"]["port"] = "8080"  # 應該是整數
    
    with pytest.raises(ValidationError):
        validator.validate(invalid_config)

def test_range_validation(validator, sample_config):
    """測試範圍驗證"""
    validator.add_rule(
        ValidationRule("app.port").min(1024).max(65535)
    )
    validator.add_rule(
        ValidationRule("database.max_connections").min(1).max(100)
    )
    
    # 驗證有效配置
    assert validator.validate(sample_config) is True
    
    # 測試超出範圍的值
    invalid_config = sample_config.copy()
    invalid_config["app"]["port"] = 80  # 小於最小值
    
    with pytest.raises(ValidationError):
        validator.validate(invalid_config)

def test_pattern_validation(validator, sample_config):
    """測試模式驗證"""
    # 添加正則表達式驗證規則
    validator.add_rule(
        ValidationRule("logging.level").pattern(r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    )
    validator.add_rule(
        ValidationRule("logging.file").pattern(r".*\.log$")
    )
    
    # 驗證有效配置
    assert validator.validate(sample_config) is True
    
    # 測試無效的日誌級別
    invalid_config = sample_config.copy()
    invalid_config["logging"]["level"] = "INVALID"
    
    with pytest.raises(ValidationError):
        validator.validate(invalid_config)

def test_custom_validation(validator, sample_config):
    """測試自定義驗證"""
    def validate_database_url(value):
        valid_prefixes = ["sqlite:///", "postgresql://", "mysql://"]
        return any(value.startswith(prefix) for prefix in valid_prefixes)
    
    validator.add_rule(
        ValidationRule("database.url").custom(validate_database_url)
    )
    
    # 驗證有效配置
    assert validator.validate(sample_config) is True
    
    # 測試無效的數據庫 URL
    invalid_config = sample_config.copy()
    invalid_config["database"]["url"] = "invalid://database"
    
    with pytest.raises(ValidationError):
        validator.validate(invalid_config)

def test_nested_validation(validator, sample_config):
    """測試嵌套配置驗證"""
    # 驗證整個 app 部分
    validator.add_rule(
        ValidationRule("app").nested({
            "name": ValidationRule().required().type(str),
            "port": ValidationRule().required().type(int).min(1024),
            "debug": ValidationRule().type(bool),
            "allowed_hosts": ValidationRule().type(list)
        })
    )
    
    # 驗證有效配置
    assert validator.validate(sample_config) is True
    
    # 測試無效的嵌套配置
    invalid_config = sample_config.copy()
    invalid_config["app"] = {
        "name": 123,  # 應該是字符串
        "port": 8080,
        "debug": True
    }
    
    with pytest.raises(ValidationError):
        validator.validate(invalid_config)

def test_conditional_validation(validator, sample_config):
    """測試條件驗證"""
    # 如果 debug 為 True，則必須提供 allowed_hosts
    def validate_debug_config(config):
        if config.get("app", {}).get("debug", False):
            return "allowed_hosts" in config["app"]
        return True
    
    validator.add_rule(
        ValidationRule("app").custom(validate_debug_config)
    )
    
    # 驗證有效配置
    assert validator.validate(sample_config) is True
    
    # 測試無效的條件配置
    invalid_config = sample_config.copy()
    del invalid_config["app"]["allowed_hosts"]
    
    with pytest.raises(ValidationError):
        validator.validate(invalid_config)

def test_multiple_rules(validator, sample_config):
    """測試多個規則組合"""
    validator.add_rule(
        ValidationRule("database.timeout")
        .required()
        .type(int)
        .min(0)
        .max(3600)
    )
    
    # 驗證有效配置
    assert validator.validate(sample_config) is True
    
    # 測試違反多個規則
    invalid_config = sample_config.copy()
    invalid_config["database"]["timeout"] = -1  # 違反最小值規則
    
    with pytest.raises(ValidationError):
        validator.validate(invalid_config)
    
    invalid_config["database"]["timeout"] = "30"  # 違反類型規則
    
    with pytest.raises(ValidationError):
        validator.validate(invalid_config)

def test_error_messages(validator, sample_config):
    """測試錯誤消息"""
    validator.add_rule(
        ValidationRule("app.port")
        .type(int, message="端口必須是整數")
        .min(1024, message="端口必須大於 1024")
        .max(65535, message="端口必須小於 65535")
    )
    
    # 測試類型錯誤消息
    invalid_config = sample_config.copy()
    invalid_config["app"]["port"] = "8080"
    
    try:
        validator.validate(invalid_config)
    except ValidationError as e:
        assert "端口必須是整數" in str(e)
    
    # 測試範圍錯誤消息
    invalid_config["app"]["port"] = 80
    
    try:
        validator.validate(invalid_config)
    except ValidationError as e:
        assert "端口必須大於 1024" in str(e)

def test_required_fields():
    """測試必填字段驗證"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("api_key", "API key must not be empty")
        .required()
    )
    
    # 創建一個有效的配置
    config = SampleConfig(api_key="test_key", port=8000)
    assert validator.validate(config) is True
    
    # 測試缺少必填字段
    data = {"port": 8000}
    with pytest.raises(ValueError) as exc:
        validator.validate(config, data)
    assert "API key must not be empty" in str(exc.value)

def test_value_range():
    """測試數值範圍驗證"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("port", "Port must be between 1024 and 65535")
        .min_value(1024)
        .max_value(65535)
    )
    
    # 測試範圍外的值
    with pytest.raises(ValueError):
        validator.validate(SampleConfig(api_key="test", port=80))
    
    with pytest.raises(ValueError):
        validator.validate(SampleConfig(api_key="test", port=70000))
    
    # 測試有效範圍
    config = SampleConfig(api_key="test", port=8000)
    assert validator.validate(config) is True

def test_string_pattern():
    """測試字符串模式驗證"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("api_key", "Invalid API key format")
        .pattern(r"^[A-Za-z0-9]{32}$")
    )
    
    # 測試無效格式
    with pytest.raises(ValueError):
        validator.validate(SampleConfig(
            api_key="invalid-key",
            port=8000
        ))
    
    # 測試有效格式
    config = SampleConfig(
        api_key="a" * 32,
        port=8000
    )
    assert validator.validate(config) is True

def test_list_validation():
    """測試列表驗證"""
    validator = ConfigValidator()
    
    # 創建列表項目的驗證規則
    item_rule = ValidationRule("host").pattern(r"^[\w\.-]+$")
    
    # 創建列表的驗證規則
    validator.add_rule(
        ValidationRule("allowed_hosts", "主機列表無效")
        .required()
        .list_items(item_rule)
    )
    
    # 創建基本配置
    config = SampleConfig(api_key="test", port=8000)
    
    # 測試有效列表
    data = {
        "allowed_hosts": ["localhost", "example.com"]
    }
    assert validator.validate(config, data) is True
    
    # 測試無效的列表項目
    data = {
        "allowed_hosts": ["localhost", "invalid host!"]
    }
    with pytest.raises(ValueError) as exc:
        validator.validate(config, data)
    assert "格式不正確" in str(exc.value)
    
    # 測試非列表值
    data = {
        "allowed_hosts": "not a list"
    }
    with pytest.raises(ValueError) as exc:
        validator.validate(config, data)
    assert "必須是列表類型" in str(exc.value)
    
    # 測試空列表
    data = {
        "allowed_hosts": []
    }
    assert validator.validate(config, data) is True

def test_custom_validation():
    """測試自定義驗證"""
    def validate_connections(value):
        if value is not None and value < 1:
            raise ValueError("Connections must be positive")
        return True
    
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("max_connections", "Invalid connections value")
        .custom(validate_connections)
    )
    
    # 測試無效值
    with pytest.raises(ValueError):
        validator.validate(SampleConfig(
            api_key="test",
            port=8000,
            max_connections=0
        ))
    
    # 測試有效值
    config = SampleConfig(
        api_key="test",
        port=8000,
        max_connections=100
    )
    assert validator.validate(config) is True
    
    # 測試 None 值
    config = SampleConfig(
        api_key="test",
        port=8000,
        max_connections=None
    )
    assert validator.validate(config) is True

def test_multiple_rules():
    """測試多重驗證規則"""
    validator = ConfigValidator()
    
    # 添加多個規則
    validator.add_rule(
        ValidationRule("api_key", "API key validation failed")
        .required()
        .min_length(32)
        .max_length(32)
    )
    
    validator.add_rule(
        ValidationRule("port", "Port validation failed")
        .required()
        .min_value(1024)
        .max_value(65535)
    )
    
    # 測試多重驗證失敗
    with pytest.raises(ValueError) as exc:
        validator.validate(SampleConfig(
            api_key="short",
            port=80
        ))
    
    error_msg = str(exc.value)
    assert "API key validation failed" in error_msg
    assert "Port validation failed" in error_msg
    
    # 測試全部通過
    config = SampleConfig(
        api_key="a" * 32,
        port=8000
    )
    assert validator.validate(config) is True

def test_conditional_validation():
    """測試條件驗證"""
    validator = ConfigValidator()
    
    # 當 debug 為 True 時，port 必須大於 8000
    def debug_port_rule(value, config=None):
        if not config or not config.debug:
            return True
        return value > 8000
    
    validator.add_rule(
        ValidationRule("port", "Debug mode requires port > 8000")
        .custom(lambda x: debug_port_rule(x, config))
    )
    
    # 創建配置
    config = SampleConfig(api_key="test", port=8000)
    
    # 測試 debug=False 時的情況
    config.debug = False
    assert validator.validate(config) is True
    
    # 測試 debug=True 時的情況
    config.debug = True
    with pytest.raises(ValueError) as exc:
        validator.validate(config)
    assert "Debug mode requires port > 8000" in str(exc.value)
    
    # 測試有效值
    config.port = 8001
    assert validator.validate(config) is True

def test_validation_rule_required():
    """測試必填驗證"""
    rule = ValidationRule("name").required()
    
    # 測試空值
    with pytest.raises(ValueError, match="name 不能為空"):
        rule.validate(None)
    
    # 測試非空值
    assert rule.validate("test") is True
    
    # 測試自定義錯誤消息
    rule = ValidationRule("name").required("名稱是必填的")
    with pytest.raises(ValueError, match="名稱是必填的"):
        rule.validate(None)

def test_validation_rule_min_max_value():
    """測試最小值和最大值驗證"""
    rule = ValidationRule("age").min_value(18).max_value(100)
    
    # 測試有效值
    assert rule.validate(20) is True
    assert rule.validate(18) is True
    assert rule.validate(100) is True
    
    # 測試無效值
    with pytest.raises(ValueError, match="age 不能小於 18"):
        rule.validate(17)
    
    with pytest.raises(ValueError, match="age 不能大於 100"):
        rule.validate(101)
    
    # 測試非數字值
    with pytest.raises(ValueError, match="age 必須是數字"):
        rule.validate("not a number")

def test_validation_rule_min_max_length():
    """測試最小長度和最大長度驗證"""
    rule = ValidationRule("name").min_length(2).max_length(10)
    
    # 測試有效值
    assert rule.validate("ab") is True
    assert rule.validate("abcdefghij") is True
    
    # 測試無效值
    with pytest.raises(ValueError, match="name 長度不能小於 2"):
        rule.validate("a")
    
    with pytest.raises(ValueError, match="name 長度不能大於 10"):
        rule.validate("abcdefghijk")

def test_validation_rule_pattern():
    """測試正則表達式驗證"""
    # 測試郵箱格式
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    rule = ValidationRule("email").pattern(email_pattern)
    
    # 測試有效值
    assert rule.validate("test@example.com") is True
    
    # 測試無效值
    with pytest.raises(ValueError, match="email 格式不正確"):
        rule.validate("invalid-email")
    
    # 測試已編譯的正則表達式
    rule = ValidationRule("email").pattern(re.compile(email_pattern))
    assert rule.validate("test@example.com") is True

def test_validation_rule_custom():
    """測試自定義驗證"""
    def is_even(value):
        return isinstance(value, int) and value % 2 == 0
    
    rule = ValidationRule("number").custom(is_even)
    
    # 測試有效值
    assert rule.validate(2) is True
    assert rule.validate(4) is True
    
    # 測試無效值
    with pytest.raises(ValueError, match="number 驗證失敗"):
        rule.validate(3)
    
    # 測試自定義錯誤消息
    rule = ValidationRule("number").custom(is_even, "數字必須是偶數")
    with pytest.raises(ValueError, match="數字必須是偶數"):
        rule.validate(3)

def test_config_validator():
    """測試配置驗證器"""
    validator = ConfigValidator()
    
    # 添加多個驗證規則
    validator.add_rule(
        ValidationRule("name")
        .required()
        .min_length(2)
        .max_length(10)
    )
    validator.add_rule(
        ValidationRule("age")
        .required()
        .min_value(18)
        .max_value(100)
    )
    validator.add_rule(
        ValidationRule("email")
        .required()
        .pattern(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    )
    
    # 創建配置對象
    config = SampleConfig(api_key="test_key", port=8000)
    config.name = "test"
    config.age = 20
    config.email = "test@example.com"
    
    # 測試有效配置
    assert validator.validate(config) is True
    
    # 測試無效配置
    data = {
        "name": "test",
        "age": 15,
        "email": "test@example.com"
    }
    with pytest.raises(ValueError) as exc_info:
        validator.validate(config, data)
    assert "age 不能小於 18" in str(exc_info.value)
    
    # 測試無效郵箱格式
    data["age"] = 20
    data["email"] = "invalid-email"
    with pytest.raises(ValueError) as exc_info:
        validator.validate(config, data)
    assert "email 格式不正確" in str(exc_info.value)

def test_validator_error_collection():
    """測試錯誤收集"""
    validator = ConfigValidator()
    
    # 添加多個驗證規則
    validator.add_rule(ValidationRule("name").required())
    validator.add_rule(ValidationRule("age").min_value(18))
    
    # 創建配置對象
    config = SampleConfig(api_key="test_key", port=8000)
    
    # 測試多個錯誤
    data = {
        "age": 15
    }
    
    # 驗證並檢查錯誤
    with pytest.raises(ValueError) as exc_info:
        validator.validate(config, data)
    
    error_message = str(exc_info.value)
    assert "name 不能為空" in error_message
    assert "age 不能小於 18" in error_message 