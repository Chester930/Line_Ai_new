import pytest
from src.shared.config.validator import ConfigValidator, ValidationRule, ValidationError
from src.shared.config.base import BaseConfig, ConfigError
from typing import Optional, List
import json
from pathlib import Path
import logging
import re
from src.shared.config.json_config import JSONConfig

logger = logging.getLogger(__name__)

class SampleConfig:
    """用于测试的配置类"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

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

@pytest.mark.asyncio
async def test_required_field_validation(validator, sample_config):
    """測試必需字段驗證"""
    # 添加必需字段規則
    validator.add_rule(
        ValidationRule("app.name").required()
    )
    validator.add_rule(
        ValidationRule("database.url").required()
    )
    
    # 驗證有效配置
    assert await validator.validate(sample_config) is True
    
    # 刪除必需字段
    invalid_config = sample_config.copy()
    del invalid_config["app"]["name"]
    
    # 驗證無效配置
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_type_validation(validator, sample_config):
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
    assert await validator.validate(sample_config) is True
    
    # 測試無效類型
    invalid_config = sample_config.copy()
    invalid_config["app"]["port"] = "8080"  # 應該是整數
    
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_range_validation(validator, sample_config):
    """測試範圍驗證"""
    validator.add_rule(
        ValidationRule("app.port").min(1024).max(65535)
    )
    validator.add_rule(
        ValidationRule("database.max_connections").min(1).max(100)
    )
    
    # 驗證有效配置
    assert await validator.validate(sample_config) is True
    
    # 測試超出範圍的值
    invalid_config = sample_config.copy()
    invalid_config["app"]["port"] = 80  # 小於最小值
    
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_pattern_validation(validator, sample_config):
    """測試模式驗證"""
    # 添加正則表達式驗證規則
    validator.add_rule(
        ValidationRule("logging.level").pattern(r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    )
    validator.add_rule(
        ValidationRule("logging.file").pattern(r".*\.log$")
    )
    
    # 驗證有效配置
    assert await validator.validate(sample_config) is True
    
    # 測試無效的日誌級別
    invalid_config = sample_config.copy()
    invalid_config["logging"]["level"] = "INVALID"
    
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_custom_validation(validator, sample_config):
    """測試自定義驗證"""
    def validate_database_url(value):
        valid_prefixes = ["sqlite:///", "postgresql://", "mysql://"]
        return any(value.startswith(prefix) for prefix in valid_prefixes)
    
    validator.add_rule(
        ValidationRule("database.url").custom(validate_database_url)
    )
    
    # 驗證有效配置
    assert await validator.validate(sample_config) is True
    
    # 測試無效的數據庫 URL
    invalid_config = sample_config.copy()
    invalid_config["database"]["url"] = "invalid://database"
    
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_nested_validation():
    """測試嵌套驗證規則"""
    address_rule = ValidationRule("zip_code").pattern(r"^\d{5}$")
    user_rule = ValidationRule("address").nested({
        "zip_code": address_rule
    })
    
    validator = ConfigValidator()
    validator.add_rule(user_rule)
    
    # 測試有效地址
    assert await validator.validate({"address": {"zip_code": "12345"}}) is True
    
    # 測試無效郵編
    with pytest.raises(ValidationError) as exc:
        await validator.validate({"address": {"zip_code": "abc"}})
    assert "zip_code 格式不正確" in str(exc.value)

@pytest.mark.asyncio
async def test_conditional_validation(validator, sample_config):
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
    assert await validator.validate(sample_config) is True
    
    # 測試無效的條件配置
    invalid_config = sample_config.copy()
    del invalid_config["app"]["allowed_hosts"]
    
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_multiple_rules():
    """測試多重驗證規則"""
    validator = ConfigValidator()
    
    # 添加多個規則
    validator.add_rule(
        ValidationRule("api_key")
        .required()
        .min_length(32)
        .pattern(r"^[A-Za-z0-9]+$")
    )
    
    validator.add_rule(
        ValidationRule("port")
        .required()
        .type(int)
        .range(1024, 65535)
    )
    
    # 測試多個錯誤
    with pytest.raises(ValidationError) as exc:
        await validator.validate(SampleConfig(
            api_key="short",
            port=80
        ))
    error_msg = str(exc.value)
    assert "api_key: 長度不能小於 32" in error_msg
    assert "port: 不能小於 1024" in error_msg
    
    # 測試全部通過
    config = SampleConfig(
        api_key="a" * 32,
        port=8080
    )
    assert await validator.validate(config) is True

@pytest.mark.asyncio
async def test_error_messages(validator, sample_config):
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
        await validator.validate(invalid_config)
    except ValidationError as e:
        assert "端口必須是整數" in str(e)
    
    # 測試範圍錯誤消息
    invalid_config["app"]["port"] = 80
    
    try:
        await validator.validate(invalid_config)
    except ValidationError as e:
        assert "端口必須大於 1024" in str(e)

@pytest.mark.asyncio
async def test_required_fields():
    """測試必填字段驗證"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("api_key", "API key must not be empty")
        .required()
    )
    
    # 創建一個有效的配置
    config = SampleConfig(api_key="test_key", port=8000)
    assert await validator.validate(config) is True
    
    # 測試缺少必填字段
    with pytest.raises(ValidationError) as exc:
        await validator.validate({"port": 8000})
    assert "API key must not be empty" in str(exc.value)

@pytest.mark.asyncio
async def test_value_range():
    """測試數值範圍驗證"""
    validator = ConfigValidator()
    validator.add_rule(ValidationRule("port").type(int).min_value(1024))
    
    # 測試小於最小值
    with pytest.raises(ValidationError) as exc:
        await validator.validate(SampleConfig(api_key="test", port=80))
    assert "port: 不能小於 1024" in str(exc.value)
    
    # 測試有效值
    config = SampleConfig(api_key="test", port=8080)
    assert await validator.validate(config) is True
    
    # 測試最大值
    validator.add_rule(ValidationRule("port").max_value(65535))
    with pytest.raises(ValidationError):
        await validator.validate(SampleConfig(api_key="test", port=70000))
    assert "port: 不能大於 65535" in str(exc.value)
    
    # 測試範圍組合
    validator.add_rule(ValidationRule("age").range(18, 100))
    with pytest.raises(ValidationError):
        await validator.validate(SampleConfig(api_key="test", port=8080, age=15))
    assert "age: 不能小於 18" in str(exc.value)

@pytest.mark.asyncio
async def test_string_pattern():
    """測試字符串模式驗證"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("api_key", "Invalid API key format")
        .pattern(r"^[A-Za-z0-9]{32}$")
    )
    
    # 測試無效格式
    with pytest.raises(ValidationError) as exc:
        await validator.validate(SampleConfig(
            api_key="invalid-key",
            port=8000
        ))
    assert "Invalid API key format" in str(exc.value)

@pytest.mark.asyncio
async def test_list_validation():
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
    assert await validator.validate(config, data) is True
    
    # 測試無效的列表項目
    data = {
        "allowed_hosts": ["localhost", "invalid host!"]
    }
    with pytest.raises(ValidationError):
        await validator.validate(config, data)
    assert "格式不正確" in str(exc.value)
    
    # 測試非列表值
    data = {
        "allowed_hosts": "not a list"
    }
    with pytest.raises(ValidationError):
        await validator.validate(config, data)
    assert "必須是列表類型" in str(exc.value)
    
    # 測試空列表
    data = {
        "allowed_hosts": []
    }
    assert await validator.validate(config, data) is True

@pytest.mark.asyncio
async def test_custom_validation():
    def is_even(value):
        return value % 2 == 0

    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("even_number")
        .custom(is_even, "必須是偶數")
    )

    # 有效測試
    assert await validator.validate({"even_number": 4}) is True
    
    # 無效測試
    with pytest.raises(ValidationError) as exc:
        await validator.validate({"even_number": 3})
    assert "必須是偶數" in str(exc.value)

@pytest.mark.asyncio
async def test_validation_rule_required():
    """測試必填字段驗證"""
    rule = ValidationRule("name").required()
    
    with pytest.raises(ValidationError) as exc_info:
        await rule.validate(None)  # 直接調用驗證方法
    assert "name 不能為空" in str(exc_info.value)

@pytest.mark.asyncio
async def test_validation_rule_min_max_value():
    """測試最小值和最大值驗證"""
    rule = ValidationRule("age").min_value(18).max_value(100)
    
    # 測試有效值
    assert await rule.validate(20) is True
    
    # 測試小於最小值
    assert not await rule.validate(15)
    
    # 測試大於最大值
    assert not await rule.validate(101)

@pytest.mark.asyncio
async def test_validation_rule_min_max_length():
    """測試最小長度和最大長度驗證"""
    rule = ValidationRule("name").min_length(2).max_length(10)
    
    # 測試有效值
    assert await rule.validate("ab") is True
    assert await rule.validate("abcdefghij") is True
    
    # 測試無效值
    with pytest.raises(ValidationError, match="name 長度不能小於 2"):
        await rule.validate("a")
    
    with pytest.raises(ValidationError, match="name 長度不能大於 10"):
        await rule.validate("abcdefghijk")

@pytest.mark.asyncio
async def test_validation_rule_pattern():
    """測試正則表達式驗證"""
    # 測試郵箱格式
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    rule = ValidationRule("email").pattern(email_pattern)
    
    # 測試有效值
    assert await rule.validate("test@example.com") is True
    
    # 測試無效值
    with pytest.raises(ValidationError, match="email 格式不正確"):
        await rule.validate("invalid-email")
    
    # 測試已編譯的正則表達式
    rule = ValidationRule("email").pattern(re.compile(email_pattern))
    assert await rule.validate("test@example.com") is True

@pytest.mark.asyncio
async def test_validation_rule_custom():
    """測試自定義驗證"""
    def is_even(value):
        return isinstance(value, int) and value % 2 == 0
    
    rule = ValidationRule("number").custom(is_even)
    
    # 測試有效值
    assert await rule.validate(2) is True
    assert await rule.validate(4) is True
    
    # 測試無效值
    with pytest.raises(ValidationError, match="number 驗證失敗"):
        await rule.validate(3)
    
    # 測試自定義錯誤消息
    rule = ValidationRule("number").custom(is_even, "數字必須是偶數")
    with pytest.raises(ValidationError, match="數字必須是偶數"):
        await rule.validate(3)

@pytest.mark.asyncio
async def test_config_validator():
    """測試配置驗證器"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("port")
        .required()
        .min_value(1024)
    )
    validator.add_rule(
        ValidationRule("name")
        .required()
        .min_length(3)
    )
    
    config = JSONConfig(data={
        "port": 8080,
        "name": "test_app"
    })
    
    assert await validator.validate(config) is True

@pytest.mark.asyncio
async def test_validation_error():
    """測試驗證錯誤"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("port")
        .required()
        .min_value(1024)
    )
    
    config = JSONConfig(data={
        "port": 80
    })
    
    with pytest.raises(ValidationError):
        await validator.validate(config)

@pytest.mark.asyncio
async def test_validator_comprehensive():
    """全面測試配置驗證器"""
    # 1. 基本規則
    validator = ConfigValidator()
    
    # 2. 添加類型驗證規則
    validator.add_rule(
        ValidationRule("port")
        .required()
        .type(int)
        .range(1000, 9999)
    )
    
    # 3. 添加字符串驗證規則
    validator.add_rule(
        ValidationRule("app_name")
        .required()
        .type(str)
        .pattern(r"^[a-zA-Z0-9_-]+$")
        .length(min=3, max=50)
    )
    
    # 4. 添加布爾值驗證規則
    validator.add_rule(
        ValidationRule("debug")
        .type(bool)
    )
    
    # 5. 添加嵌套驗證規則
    validator.add_rule(
        ValidationRule("settings.database.host")
        .type(str)
    )
    
    # 6. 添加自定義驗證規則
    def validate_version(value: str) -> bool:
        return bool(re.match(r"^\d+\.\d+\.\d+$", value))
    
    validator.add_rule(
        ValidationRule("version")
        .custom(validate_version, "版本格式必須是 x.y.z")
    )
    
    # 7. 驗證有效配置
    valid_config = {
        "port": 8080,
        "app_name": "test_app",
        "debug": True,
        "settings": {
            "database": {
                "host": "localhost"
            }
        },
        "version": "1.0.0"
    }
    assert await validator.validate(valid_config) is True
    
    # 8. 驗證無效配置
    invalid_configs = [
        ({"port": "invalid"}, "port 必須是整數"),
        ({"app_name": "!invalid!"}, "app_name 格式無效"),
        ({"debug": "not_bool"}, "debug 必須是布爾值"),
        ({"version": "invalid"}, "版本格式必須是 x.y.z"),
        ({}, "port 是必需的")
    ]
    
    for config, error in invalid_configs:
        with pytest.raises(ValidationError, match=error):
            await validator.validate(SampleConfig(**config))

@pytest.mark.asyncio
async def test_edge_cases():
    """測試邊界條件"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("number")
        .type(int)
        .range(0, 100)
    )
    
    # 測試最小值
    assert await validator.validate({"number": 0}) is True
    # 測試最大值
    assert await validator.validate({"number": 100}) is True
    # 測試非整數
    with pytest.raises(ValidationError):
        await validator.validate({"number": 50.5})

@pytest.mark.asyncio
async def test_null_values():
    """測試空值處理"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("optional_field")
        .type(str)
        .optional()
    )
    
    # 測試允許空值
    assert await validator.validate({"optional_field": None}) is True
    # 測試無效類型
    with pytest.raises(ValidationError):
        await validator.validate({"optional_field": 123})

@pytest.mark.asyncio
async def test_optional_fields():
    """測試可選字段驗證"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("optional_field")
        .type(str)
        .optional()
    )
    
    # 測試字段不存在
    assert await validator.validate({}) is True
    # 測試空值
    assert await validator.validate({"optional_field": None}) is True
    # 測試有效值
    assert await validator.validate({"optional_field": "valid"}) is True
    # 測試無效類型
    with pytest.raises(ValidationError):
        await validator.validate({"optional_field": 123})

@pytest.mark.asyncio
async def test_optional_validation():
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("nickname")
        .optional()
        .min_length(3)
    )

    # 有效測試
    assert await validator.validate({"nickname": None}) is True
    assert await validator.validate({"nickname": "alice"}) is True
    
    # 無效測試（當有值時驗證）
    with pytest.raises(ValidationError) as exc:
        await validator.validate({"nickname": "a"})
    assert "長度不能小於 3" in str(exc.value)

@pytest.mark.asyncio
async def test_complex_type_validation():
    """測試複雜類型驗證"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("metadata")
        .type(dict)
        .nested({
            "tags": ValidationRule().type(list),
            "created_at": ValidationRule().type(str)
        })
    )
    
    valid_config = {
        "metadata": {
            "tags": ["test", "config"],
            "created_at": "2024-01-01"
        }
    }
    assert await validator.validate(valid_config) is True

@pytest.mark.asyncio
async def test_validator_exception_handling():
    """測試驗證器異常處理"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("test_field")
        .custom(lambda x: 1/0, "測試錯誤處理")
    )

    with pytest.raises(ValidationError) as exc:
        await validator.validate({"test_field": 0})
    assert "驗證過程發生意外錯誤" in str(exc.value)

@pytest.mark.asyncio
async def test_list_validation():
    """測試列表驗證"""
    # 測試無效列表項目
    invalid_config = SampleConfig(
        api_key="test",
        port=8000,
        allowed_hosts=["invalid_host!", "127.0.0.1"]
    )
    
    with pytest.raises(ValidationError) as exc:
        await validator.validate(invalid_config)
    assert "主機列表無效" in str(exc.value)

@pytest.mark.asyncio
async def test_number_type_conversion():
    """測試數值類型轉換驗證"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("number")
        .min_value(0)
        .max_value(100)
    )

    # 測試邊界值
    assert await validator.validate({"number": 0}) is True
    assert await validator.validate({"number": 100}) is True
    assert await validator.validate({"number": 50.5}) is True
    assert await validator.validate({"number": "100"}) is True  # 字符串數值
    assert await validator.validate({"number": "50.5"}) is True
    
    # 測試無效情況
    assert await validator.validate({"number": -1}) is False
    assert await validator.validate({"number": 101}) is False
    assert await validator.validate({"number": "invalid"}) is False

@pytest.mark.asyncio
async def test_number_boundary_validation():
    """測試數值邊界驗證"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("number")
        .type(int)
        .min_value(0)
        .max_value(100)
    )

    # 有效測試
    assert await validator.validate({"number": 0}) is True
    assert await validator.validate({"number": 100}) is True
    assert await validator.validate({"number": "50"}) is True  # 整數字符串
    
    # 無效測試
    assert await validator.validate({"number": -1}) is False
    assert await validator.validate({"number": 101}) is False
    assert await validator.validate({"number": 50.5}) is False  # 浮點數
    assert await validator.validate({"number": "50.5"}) is False  # 浮點數字串

@pytest.mark.asyncio
async def test_integer_string_validation():
    """測試整數字符串驗證"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("port")
        .type(int)
        .min_value(1024)
        .max_value(65535)
    )

    # 有效測試
    assert await validator.validate({"port": "8080"}) is True
    assert await validator.validate({"port": 65535}) is True
    
    # 無效測試
    assert await validator.validate({"port": "80.5"}) is False  # 浮點數字串
    assert await validator.validate({"port": "invalid"}) is False

@pytest.mark.asyncio
async def test_edge_case_validation():
    """測試邊界條件驗證"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("percentage")
        .type(float)
        .min_value(0.0)
        .max_value(1.0)
    )
    
    # 測試邊界值
    assert await validator.validate({"percentage": 0.0}) is True
    assert await validator.validate({"percentage": 1.0}) is True
    assert await validator.validate({"percentage": "0.5"}) is True
    
    # 測試超出範圍
    assert await validator.validate({"percentage": -0.1}) is False
    assert await validator.validate({"percentage": 1.1}) is False

@pytest.mark.asyncio
async def test_required_validation():
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("username")
        .required()
        .type(str)
    )

    # 有效測試
    assert await validator.validate({"username": "john_doe"}) is True
    
    # 無效測試
    with pytest.raises(ValidationError) as exc:
        await validator.validate({"username": None})
    assert "username 不能為空" in str(exc.value)

@pytest.mark.asyncio
async def test_type_conversion_validation():
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("port")
        .type(int)
        .min_value(1024)
        .max_value(65535)
    )

    # 有效字符串轉換
    assert await validator.validate({"port": "8080"}) is True
    assert await validator.validate({"port": 65535}) is True
    
    # 無效類型轉換
    with pytest.raises(ValidationError) as exc:
        await validator.validate({"port": "80.5"})
    assert "必須是整數" in str(exc.value)

@pytest.mark.asyncio
async def test_boundary_validation():
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("temperature")
        .type(float)
        .min_value(-20.0)
        .max_value(60.0)
    )

    # 邊界測試
    assert await validator.validate({"temperature": -20.0}) is True
    assert await validator.validate({"temperature": 60.0}) is True
    
    # 超出範圍測試
    with pytest.raises(ValidationError) as exc:
        await validator.validate({"temperature": -20.1})
    assert "不能小於 -20.0" in str(exc.value)

@pytest.mark.asyncio
async def test_type_conversion_edge_cases():
    """測試類型轉換邊界條件"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("number")
        .type(float)
        .min_value(0.1)
        .max_value(0.9)
    )
    
    # 測試字符串轉浮點數
    assert await validator.validate({"number": "0.5"}) is True
    
    # 測試無效轉換
    with pytest.raises(ValidationError) as exc:
        await validator.validate({"number": "invalid"})
    assert "必須是數值類型" in str(exc.value)