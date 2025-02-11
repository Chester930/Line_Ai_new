import os
import pytest
from pathlib import Path
from src.shared.config.manager import ConfigManager
from src.shared.config.validator import ConfigValidator, ValidationRule
from src.shared.config.json_config import JSONConfig
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)

class TestConfig(JSONConfig):
    """測試配置類"""
    app_name: str = "test_app"
    debug: bool = False
    port: int = 8000
    database_url: Optional[str] = None
    api_keys: Dict[str, str] = {}
    allowed_users: List[str] = []
    env: str = "test"
    
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
def config_manager(tmp_path):
    """配置管理器"""
    return ConfigManager(tmp_path)

@pytest.fixture
def json_config(tmp_path):
    """JSON 配置"""
    config_path = tmp_path / "test_config.json"
    return TestConfig(config_path=config_path)

def test_config_creation():
    """測試配置創建"""
    config = TestConfig()
    assert config.app_name == "test_app"
    assert config.debug is False
    assert config.port == 8000
    assert config.database_url is None
    assert config.api_keys == {}

def test_config_from_dict():
    """測試從字典創建配置"""
    config_data = {
        "app_name": "my_app",
        "debug": True,
        "port": 9000,
        "database_url": "sqlite:///test.db",
        "api_keys": {"service1": "key1"}
    }
    config = TestConfig.model_validate(config_data)
    
    assert config.app_name == "my_app"
    assert config.debug is True
    assert config.port == 9000
    assert config.database_url == "sqlite:///test.db"
    assert config.api_keys == {"service1": "key1"}

def test_config_validation():
    """測試配置驗證"""
    with pytest.raises(ValueError):
        TestConfig.model_validate({
            "port": "invalid_port"  # 應該是整數
        })

def test_config_update(json_config):
    """測試配置更新"""
    # 更新配置
    update_data = {
        "app_name": "Updated App",
        "port": 9000
    }
    assert json_config.update(update_data)
    
    # 驗證更新
    assert json_config.app_name == "Updated App"
    assert json_config.port == 9000
    
    # 保存並重新加載
    assert json_config.save()
    json_config._load_config()
    
    # 驗證持久化
    assert json_config.app_name == "Updated App"
    assert json_config.port == 9000

def test_config_file_operations(tmp_path):
    """測試配置文件操作"""
    config_path = tmp_path / "test_config.json"
    config = TestConfig(config_path=config_path)
    
    # 測試保存
    assert config.save()
    assert config_path.exists()
    
    # 測試加載
    data = json.loads(config_path.read_text())
    assert data["app_name"] == "test_app"
    assert data["port"] == 8000
    
    # 測試更新
    config.app_name = "Modified App"
    assert config.save()
    
    # 驗證更新後的文件
    data = json.loads(config_path.read_text())
    assert data["app_name"] == "Modified App"

def test_config_manager_operations(config_manager):
    """測試配置管理器操作"""
    # 註冊配置
    config = config_manager.register_config(
        "test",
        TestConfig,
        "test_config.json"
    )
    
    # 驗證註冊
    assert config.app_name == "test_app"
    assert config.port == 8000
    
    # 更新配置
    assert config_manager.update_config("test", {
        "app_name": "Manager Updated",
        "port": 9000
    })
    
    # 獲取並驗證更新
    updated = config_manager.get_config("test")
    assert updated.app_name == "Manager Updated"
    assert updated.port == 9000
    
    # 保存所有配置
    assert config_manager.save_all()
    
    # 重新加載
    config_manager.reload_all()
    reloaded = config_manager.get_config("test")
    assert reloaded.app_name == "Manager Updated"
    assert reloaded.port == 9000 