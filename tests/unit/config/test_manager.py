import pytest
from pathlib import Path
import tempfile
import json
from typing import Dict, Optional, Any
from src.shared.config.manager import ConfigManager
from src.shared.config.json_config import JSONConfig
from src.shared.config.validator import ConfigValidator, ValidationRule
from src.shared.config.base import BaseConfig, ConfigError
from pydantic import Field, ConfigDict
import os
from unittest.mock import Mock, patch
import aiofiles
import logging
import asyncio

logger = logging.getLogger(__name__)

class TestConfig(BaseConfig):
    """測試用配置類"""
    api_key: Optional[str] = Field(default=None)
    port: int = Field(default=8000)
    debug: bool = False
    _config_path: Optional[str] = None  # 添加配置路徑字段
    _loaded: bool = False
    _data: Dict[str, Any] = {}
    
    # 确保包含必要属性
    config_file_path: Optional[Path] = Field(default=None, exclude=True)
    config_data: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    is_loaded: bool = Field(default=False, exclude=True)
    env_prefix: Optional[str] = Field(default=None, exclude=True)
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra='allow',
        arbitrary_types_allowed=True
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_file_path = Path(kwargs.get('path')) if kwargs.get('path') else None
        self.is_loaded = False
        self.config_data = kwargs.get('data', {}) or {}
        # 從 data 初始化屬性
        for key, value in self.config_data.items():
            if key in self.model_fields:
                setattr(self, key, value)
        # 如果傳入 data 則標記為已加載
        if kwargs.get('data'):
            self.is_loaded = True

    async def save(self) -> bool:
        """保存配置"""
        try:
            if not self.config_file_path:
                return False
            
            # 确保目标目录存在
            self.config_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 获取当前配置数据并处理 Path 对象
            data = self.model_dump(exclude={'config_file_path'}, mode='json')
            async with aiofiles.open(self.config_file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            
            self.is_loaded = True
            return True
        except Exception as e:
            logger.error(f"保存配置失敗: {str(e)}")
            return False

    async def load(self) -> bool:
        """載入配置"""
        try:
            if not self.config_file_path:
                return False
            
            path = Path(self.config_file_path)
            if not path.exists():
                return True
            
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            if not content:
                return True
            
            data = json.loads(content)
            self.config_data.update(data)
            # 更新实例属性
            for key, value in data.items():
                if key in self.model_fields:
                    setattr(self, key, value)
            self.is_loaded = True
            return True
        except Exception as e:
            logger.error(f"載入配置失敗: {str(e)}")
            return False

@pytest.fixture
def temp_config_dir(tmp_path):
    """創建臨時配置目錄"""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

@pytest.fixture
async def config_manager(temp_config_dir):
    """創建配置管理器實例"""
    manager = ConfigManager(temp_config_dir)
    # 設置測試環境
    await manager.set_environment("test")
    return manager

@pytest.fixture
def validator():
    """創建配置驗證器"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("port")
        .required()
        .min_value(1024)
        .max_value(65535)
    )
    return validator

def test_init_config_manager(temp_config_dir):
    """測試配置管理器初始化"""
    manager = ConfigManager(temp_config_dir)
    assert manager.base_path == temp_config_dir
    assert isinstance(manager.configs, dict)
    assert isinstance(manager.validators, dict)
    assert temp_config_dir.exists()

@pytest.mark.asyncio
async def test_register_config(config_manager):
    """測試註冊配置"""
    config = await config_manager.register_config(
        "app",
        TestConfig,
        filename="app.json",
        data={"api_key": "test_key"}
    )
    assert config.is_loaded
    assert await config.save()

@pytest.mark.asyncio
async def test_register_config_with_validator(config_manager):
    """測試使用驗證器註冊配置"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("api_key")
        .required()
        .custom("API金鑰不能為空", lambda x: bool(x))
    )
    
    config = await config_manager.register_config(
        name="test",
        config_class=TestConfig,
        filename="test.json",
        validator=validator
    )
    
    assert isinstance(config, TestConfig)
    assert "test" in config_manager.configs
    assert "test" in config_manager.validators
    assert config_manager.validators["test"] == validator

@pytest.mark.asyncio
async def test_get_config(config_manager):
    """測試獲取配置"""
    config = await config_manager.register_config(
        "test",
        TestConfig,
        data={"api_key": "test_key"}
    )
    assert await config.save()
    await config.load()  # 重新加載確保數據同步
    loaded = await config_manager.get_config("test")
    assert loaded.api_key == "test_key"

@pytest.mark.asyncio
async def test_validate_config(config_manager):
    """測試配置驗證"""
    config = config_manager.register_config(
        "test",
        TestConfig
    )
    with pytest.raises(ConfigError):
        await config_manager.validate_config("test")

@pytest.mark.asyncio
async def test_reload_config(config_manager):
    """測試重新加載配置"""
    # 初始化配置
    test_data = {
        "name": "test_app",
        "app_name": "test_app",
        "data_path": "config/data",  # 测试路径序列化
        "version": "1.0.0"
    }
    
    config = await config_manager.register_config(
        "app",
        JSONConfig,
        filename="app.json",
        data=test_data
    )
    
    # 验证初始值
    assert config.name == "test_app"
    assert config.data_path == Path("config/data")
    
    # 修改并保存配置
    config.version = "2.0.0"
    await config.save()
    
    # 重新加载验证
    assert await config_manager.reload_config("app")
    reloaded = await config_manager.get_config("app")
    
    # 新增详细断言
    assert reloaded.version == "2.0.0", "版本号未更新"
    assert reloaded.name == "test_app", "应用名称未保持"
    assert isinstance(reloaded.data_path, Path), "路径类型错误"
    assert reloaded.data_path == Path("config/data"), "路径值不一致"

@pytest.mark.asyncio
async def test_update_config(config_manager):
    """測試更新配置"""
    await config_manager.register_config(
        "app",
        JSONConfig,
        filename="app.json"
    )
    assert await config_manager.update_config("app", {"version": "1.0.0"})
    config = await config_manager.get_config("app")
    assert config.version == "1.0.0"

@pytest.mark.asyncio
async def test_save_and_reload(config_manager):
    """測試保存和重新加載配置"""
    config = await config_manager.register_config(
        "test",
        TestConfig,
        filename="test_config.json"
    )
    await config_manager.update_config("test", {
        "api_key": "saved_key",
        "port": 9000
    })
    assert await config_manager.save_all()

@pytest.mark.asyncio
async def test_multiple_configs(config_manager):
    """測試多個配置"""
    # 註冊多個配置
    config1 = await config_manager.register_config(
        name="app1",
        config_class=TestConfig,
        filename="app1.json"
    )
    config2 = await config_manager.register_config(
        name="app2",
        config_class=TestConfig,
        filename="app2.json"
    )

    # 更新不同配置
    await config_manager.update_config("app1", {"api_key": "key1"})
    await config_manager.update_config("app2", {"api_key": "key2"})

    # 驗證各自的更新
    config1 = await config_manager.get_config("app1")
    config2 = await config_manager.get_config("app2")
    assert config1.api_key == "key1"
    assert config2.api_key == "key2"

def teardown_module(module):
    """清理測試文件"""
    # 清理可能存在的測試文件
    temp_dir = Path(tempfile.gettempdir())
    for pattern in ['*.json']:
        for file in temp_dir.glob(pattern):
            try:
                file.unlink()
            except OSError:
                pass

@pytest.fixture
def config_dir(tmp_path):
    """創建測試配置目錄"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def config_files(config_dir):
    """創建測試配置文件"""
    # 創建基礎配置
    base_config = {
        "app": {
            "name": "test_app",
            "version": "1.0.0"
        },
        "database": {
            "url": "sqlite:///test.db"
        }
    }
    
    # 創建開發環境配置
    dev_config = {
        "app": {
            "debug": True
        },
        "database": {
            "echo": True
        }
    }
    
    # 創建生產環境配置
    prod_config = {
        "app": {
            "debug": False
        },
        "database": {
            "url": "postgresql://user:pass@localhost/prod"
        }
    }
    
    # 寫入配置文件
    with open(config_dir / "base.json", "w") as f:
        json.dump(base_config, f)
    
    with open(config_dir / "development.json", "w") as f:
        json.dump(dev_config, f)
    
    with open(config_dir / "production.json", "w") as f:
        json.dump(prod_config, f)
    
    return {
        "base": base_config,
        "development": dev_config,
        "production": prod_config
    }

@pytest.mark.asyncio
async def test_load_config_files(config_dir, config_files):
    """測試加載配置文件"""
    manager = ConfigManager(config_dir=str(config_dir))
    
    # 寫入配置文件
    with open(config_dir / "development" / "app.json", "w") as f:
        json.dump({"name": "test_app"}, f)
    
    # 加載開發環境配置
    await manager.load_config("development")
    config = await manager.get_config("app")
    assert config.name == "test_app"

@pytest.mark.asyncio
async def test_environment_override(config_dir):
    """測試環境變量覆蓋配置"""
    manager = ConfigManager(config_dir=str(config_dir))
    
    # 創建配置文件路徑
    config_path = config_dir / "app.json"
    
    # 註冊配置時明確傳遞環境前綴
    config = await manager.register_config(
        "app",
        JSONConfig,
        filename=str(config_path),
        env_prefix="TEST_",
        data={"name": "test_app"}
    )
    config.config_path = config_path
    
    # 設置環境變量並重新載入
    os.environ["TEST_NAME"] = "env_app"
    await config.reload()
    
    assert config.name == "env_app"

@pytest.mark.asyncio
async def test_invalid_environment(config_dir):
    """測試無效的環境名稱"""
    manager = ConfigManager(config_dir=str(config_dir))
    
    with pytest.raises(ConfigError):
        await manager.load_config("invalid_env")

@pytest.mark.asyncio
async def test_missing_base_config(tmp_path):
    """測試缺少基礎配置文件"""
    config_dir = tmp_path / "empty_config"
    config_dir.mkdir()
    
    manager = ConfigManager(config_dir=str(config_dir))
    
    # 嘗試加載不存在的配置
    with pytest.raises(ConfigError):
        await manager.load_config("non_existent")

@pytest.mark.asyncio
async def test_get_environment(config_dir, config_files):
    """測試獲取當前環境"""
    manager = ConfigManager(config_dir=str(config_dir))
    
    # 加載開發環境配置
    await manager.load_config("development")
    assert manager.get_environment() == "development"
    
    # 切換到生產環境
    await manager.set_environment("production")
    assert manager.get_environment() == "production"

@pytest.mark.asyncio
async def test_validate_config_schema(config_dir):
    """測試配置模式驗證"""
    from pydantic import BaseModel
    
    class AppConfig(BaseModel):
        name: str
        debug: bool = False
    
    class Config(BaseModel):
        app: AppConfig
    
    manager = ConfigManager(config_dir=str(config_dir))
    
    # 創建有效的配置
    valid_config = {
        "name": "test_app",
        "debug": True
    }
    
    # 加載並驗證配置
    await manager.load_config("development", schema=Config, data=valid_config)
    config = await manager.get_config("app")
    assert config.name == "test_app"
    assert config.debug is True

@pytest.mark.asyncio
async def test_config_manager_environment(tmp_path):
    """測試配置管理器環境處理"""
    config_dir = tmp_path / "config"
    manager = ConfigManager(config_dir=config_dir)
    
    # 測試默認環境
    assert manager.get_environment() == "development"
    
    # 測試切換環境
    await manager.set_environment("production")
    assert manager.get_environment() == "production"
    
    # 測試無效環境
    with pytest.raises(ConfigError):
        await manager.set_environment("invalid")

@pytest.mark.asyncio
async def test_config_load_error(config_manager, tmp_path):
    """測試配置加載錯誤"""
    # 創建無效的配置文件
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{invalid json")
    
    # 註冊配置並嘗試加載
    with pytest.raises(ConfigError):
        await config_manager.register_config(
            "invalid",
            JSONConfig,
            filename=str(invalid_file)
        )
        await config_manager.get_config("invalid")

@pytest.mark.asyncio
async def test_config_validation_error(config_manager):
    """測試配置驗證錯誤"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("api_key")
        .required()
        .custom("API金鑰不能為空", lambda x: bool(x))
    )

    config = config_manager.register_config(
        "test",
        TestConfig,
        validator=validator
    )
    
    # 驗證應該失敗
    with pytest.raises(ConfigError):
        await config_manager.validate_config("test")

@pytest.mark.asyncio
async def test_immediate_save(config_manager):
    """測試立即保存功能"""
    config = await config_manager.register_config("test_save", JSONConfig)
    config.name = "test_save"
    assert await config.save()

@pytest.mark.asyncio
async def test_config_manager_save_load(config_manager):
    """测试配置管理器保存加载流程"""
    # 注册配置
    config = await config_manager.register_config(
        "test_save",
        JSONConfig,
        filename="test_save.json",
        data={"app_name": "save_test"}
    )
    
    # 修改并保存
    config.port = 9000
    await config.save()
    
    # 重新加载验证
    await config_manager.reload_config("test_save")
    reloaded = await config_manager.get_config("test_save")
    assert reloaded.port == 9000
    assert reloaded.app_name == "save_test" 