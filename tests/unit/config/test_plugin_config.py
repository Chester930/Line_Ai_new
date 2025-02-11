import pytest
from pathlib import Path
import json
from src.shared.config.plugin_config import PluginConfigManager, PluginSettings, PluginConfig
from src.shared.exceptions import ValidationError

class TestPluginConfigManager:
    def setup_method(self):
        self.test_config_path = "tests/data/test_plugins_config.json"
        self.config_manager = PluginConfigManager(self.test_config_path)
    
    def teardown_method(self):
        config_file = Path(self.test_config_path)
        if config_file.exists():
            config_file.unlink()
    
    def test_load_configs(self):
        # 創建測試配置文件
        config_data = {
            "plugins": {
                "test_plugin": {
                    "enabled": True,
                    "version": "1.0",
                    "settings": {
                        "api_key": "test_key"
                    }
                }
            }
        }
        
        config_file = Path(self.test_config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # 載入配置
        self.config_manager.load_configs()
        
        # 驗證配置
        assert "test_plugin" in self.config_manager.configs
        plugin_config = self.config_manager.configs["test_plugin"]
        assert plugin_config.enabled
        assert plugin_config.version == "1.0"
        assert plugin_config.settings["api_key"] == "test_key"
    
    def test_save_configs(self):
        # 設置測試配置
        self.config_manager.configs["test_plugin"] = PluginSettings(
            enabled=True,
            version="1.0",
            settings={"api_key": "test_key"}
        )
        
        # 保存配置
        self.config_manager.save_configs()
        
        # 驗證保存的文件
        config_file = Path(self.test_config_path)
        assert config_file.exists()
        
        with open(config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert "test_plugin" in saved_data["plugins"]
        plugin_data = saved_data["plugins"]["test_plugin"]
        assert plugin_data["enabled"]
        assert plugin_data["version"] == "1.0"
        assert plugin_data["settings"]["api_key"] == "test_key"

@pytest.mark.asyncio
async def test_plugin_config():
    """測試插件配置"""
    config = PluginConfig(
        name="test_plugin",
        enabled=True,
        settings={"key": "value"}
    )
    
    # 測試基本屬性
    assert config.name == "test_plugin"
    assert config.enabled
    assert config.settings["key"] == "value"
    
    # 測試啟用/禁用
    config.disable()
    assert not config.enabled
    config.enable()
    assert config.enabled

@pytest.mark.asyncio
async def test_plugin_config_validation():
    """測試插件配置驗證"""
    # 測試有效配置
    valid_config = PluginConfig(
        name="test_plugin",
        enabled=True,
        settings={
            "api_key": "test_key",
            "max_retries": 3
        }
    )
    assert valid_config.validate()
    
    # 測試無效配置
    invalid_config = PluginConfig(
        name="",  # 空名稱
        enabled=True,
        settings={}
    )
    with pytest.raises(ValidationError):
        invalid_config.validate()

@pytest.mark.asyncio
async def test_plugin_config_update():
    """測試插件配置更新"""
    config = PluginConfig(
        name="test_plugin",
        enabled=True,
        settings={"key": "old_value"}
    )
    
    # 測試更新設置
    new_settings = {"key": "new_value", "new_key": "value"}
    await config.update_settings(new_settings)
    assert config.settings["key"] == "new_value"
    assert config.settings["new_key"] == "value"
    
    # 測試部分更新
    await config.update_settings({"key": "updated"})
    assert config.settings["key"] == "updated"
    assert config.settings["new_key"] == "value"  # 保持不變

@pytest.mark.asyncio
async def test_plugin_config_serialization():
    """測試插件配置序列化"""
    config = PluginConfig(
        name="test_plugin",
        enabled=True,
        settings={"key": "value"}
    )
    
    # 測試序列化
    data = config.to_dict()
    assert data["name"] == "test_plugin"
    assert data["enabled"]
    assert data["settings"]["key"] == "value"
    
    # 測試反序列化
    new_config = PluginConfig.from_dict(data)
    assert new_config.name == config.name
    assert new_config.enabled == config.enabled
    assert new_config.settings == config.settings

@pytest.mark.asyncio
async def test_plugin_config_manager_operations():
    """測試插件配置管理器操作"""
    manager = PluginConfigManager()
    
    # 測試添加配置
    config = PluginConfig(
        name="test_plugin",
        enabled=True,
        settings={"key": "value"}
    )
    await manager.add_config(config)
    assert "test_plugin" in manager.configs
    
    # 測試獲取配置
    loaded = await manager.get_config("test_plugin")
    assert loaded.name == config.name
    assert loaded.settings == config.settings
    
    # 測試更新配置
    new_settings = {"key": "new_value"}
    await manager.update_config("test_plugin", new_settings)
    updated = await manager.get_config("test_plugin")
    assert updated.settings["key"] == "new_value"
    
    # 測試刪除配置
    await manager.remove_config("test_plugin")
    with pytest.raises(KeyError):
        await manager.get_config("test_plugin")

@pytest.mark.asyncio
async def test_plugin_config_version_management():
    """測試插件配置版本管理"""
    config = PluginConfig(
        name="test_plugin",
        enabled=True,
        version="1.0.0",
        settings={"key": "value"}
    )
    
    # 測試版本比較
    assert config.check_version("1.0.0")  # 精確匹配
    assert config.check_version(">= 0.9.0")  # 大於等於
    assert config.check_version("> 0.9.0")  # 大於
    assert config.check_version("<= 1.1.0")  # 小於等於
    assert config.check_version("< 1.1.0")  # 小於
    assert not config.check_version("> 1.0.0")  # 不大於
    
    # 測試版本更新
    await config.update_version("1.1.0")
    assert config.version == "1.1.0"
    
    # 測試無效版本
    with pytest.raises(ValidationError):
        await config.update_version("invalid")

@pytest.mark.asyncio
async def test_plugin_config_migration():
    """測試插件配置遷移"""
    manager = PluginConfigManager()
    
    # 定義遷移函數
    async def migrate_v1_to_v2(config_data):
        config_data["version"] = "2.0.0"
        config_data["settings"]["new_key"] = config_data["settings"].pop("old_key")
        return config_data
    
    # 註冊遷移規則
    manager.register_migration("1.0.0", "2.0.0", migrate_v1_to_v2)
    
    # 創建舊版本配置
    old_config = {
        "name": "test_plugin",
        "enabled": True,
        "version": "1.0.0",
        "settings": {
            "old_key": "old_value"
        }
    }
    
    # 執行遷移
    migrated = await manager.load_and_migrate(old_config)
    assert migrated.version == "2.0.0"
    assert "new_key" in migrated.settings
    assert migrated.settings["new_key"] == "old_value"
    assert "old_key" not in migrated.settings

@pytest.mark.asyncio
async def test_plugin_config_validation_rules():
    """測試插件配置驗證規則"""
    # 定義驗證規則
    validation_rules = {
        "api_key": {
            "type": str,
            "required": True,
            "min_length": 10
        },
        "max_retries": {
            "type": int,
            "min": 1,
            "max": 5
        }
    }
    
    # 測試有效配置
    valid_config = PluginConfig(
        name="test_plugin",
        enabled=True,
        settings={
            "api_key": "1234567890",
            "max_retries": 3
        },
        validation_rules=validation_rules
    )
    assert valid_config.validate()
    
    # 測試無效配置
    invalid_configs = [
        # API key 太短
        {
            "api_key": "123",
            "max_retries": 3
        },
        # max_retries 超出範圍
        {
            "api_key": "1234567890",
            "max_retries": 6
        },
        # 缺少必要字段
        {
            "max_retries": 3
        }
    ]
    
    for invalid_config_data in invalid_configs:
        config = PluginConfig(
            name="test_plugin",
            enabled=True,
            settings=invalid_config_data,
            validation_rules=validation_rules
        )
        with pytest.raises(ValidationError):
            config.validate()

@pytest.mark.asyncio
async def test_plugin_config_dependencies():
    """測試插件配置依賴關係"""
    manager = PluginConfigManager()
    
    # 創建相互依賴的配置
    plugin_a = PluginConfig(
        name="plugin_a",
        enabled=True,
        settings={},
        dependencies=["plugin_b"]
    )
    
    plugin_b = PluginConfig(
        name="plugin_b",
        enabled=True,
        settings={},
        dependencies=["plugin_c"]
    )
    
    plugin_c = PluginConfig(
        name="plugin_c",
        enabled=True,
        settings={}
    )
    
    # 測試依賴檢查
    await manager.add_config(plugin_c)
    await manager.add_config(plugin_b)
    await manager.add_config(plugin_a)
    
    # 驗證依賴順序
    load_order = await manager.get_load_order()
    assert load_order == ["plugin_c", "plugin_b", "plugin_a"]
    
    # 測試循環依賴檢測
    plugin_c.dependencies = ["plugin_a"]  # 創建循環依賴
    with pytest.raises(ValidationError, match="循環依賴"):
        await manager.validate_dependencies()

@pytest.mark.asyncio
async def test_plugin_config_conflicts():
    """測試插件配置衝突檢測"""
    manager = PluginConfigManager()

    # 創建可能衝突的配置
    plugin_1 = PluginConfig(
        name="plugin_1",
        enabled=True,
        settings={"port": 8080},
        conflicts=["plugin_2"]
    )

    plugin_2 = PluginConfig(
        name="plugin_2",
        enabled=True,
        settings={"port": 8080}
    )

    # 添加第一個插件
    await manager.add_config(plugin_1)

    # 測試衝突檢測 - 嘗試添加衝突的插件
    with pytest.raises(ValidationError) as exc_info:
        await manager.add_config(plugin_2)
    assert "衝突" in str(exc_info.value)

    # 測試端口衝突
    plugin_3 = PluginConfig(
        name="plugin_3",
        enabled=True,
        settings={"port": 8080}
    )
    with pytest.raises(ValidationError) as exc_info:
        await manager.add_config(plugin_3)
    assert "端口" in str(exc_info.value)

@pytest.mark.asyncio
async def test_plugin_config_backup_restore():
    """測試插件配置備份和恢復"""
    manager = PluginConfigManager()
    
    # 創建測試配置
    config = PluginConfig(
        name="test_plugin",
        enabled=True,
        version="1.0.0",
        settings={"key": "value"}
    )
    await manager.add_config(config)
    
    # 創建備份
    backup_path = await manager.create_backup()
    assert backup_path.exists()
    
    # 修改配置
    await manager.update_config("test_plugin", {"key": "modified"})
    modified = await manager.get_config("test_plugin")
    assert modified.settings["key"] == "modified"
    
    # 從備份恢復
    await manager.restore_from_backup(backup_path)
    restored = await manager.get_config("test_plugin")
    assert restored.settings["key"] == "value"
    
    # 清理備份文件
    backup_path.unlink()

@pytest.mark.asyncio
async def test_plugin_config_error_handling():
    """測試插件配置錯誤處理"""
    manager = PluginConfigManager()
    
    # 測試無效的配置路徑
    manager.config_path = Path("non_existent/config.json")
    manager.load_configs()  # 不應該拋出異常
    
    # 測試無效的備份路徑
    with pytest.raises(FileNotFoundError):
        await manager.restore_from_backup(Path("non_existent.bak"))
    
    # 測試無效的遷移
    invalid_config = {
        "name": "test",
        "version": "1.0.0",  # 有效的版本號
        "settings": {}
    }
    manager.register_migration("2.0.0", "3.0.0", None)  # 註冊一個不相關的遷移
    config = await manager.load_and_migrate(invalid_config)  # 應該返回原始配置
    assert config.version == "1.0.0"

@pytest.mark.asyncio
async def test_plugin_config_edge_cases():
    """測試插件配置邊界條件"""
    # 測試空配置
    config = PluginConfig(name="test")
    assert config.settings == {}
    assert config.dependencies == []
    assert config.conflicts == []
    
    # 測試重複添加配置
    manager = PluginConfigManager()
    await manager.add_config(config)
    
    # 修改配置並再次添加
    config.settings["new_key"] = "new_value"
    await manager.add_config(config)
    
    # 驗證配置已更新
    loaded = await manager.get_config("test")
    assert loaded.settings["new_key"] == "new_value"
    
    # 測試刪除不存在的配置
    await manager.remove_config("non_existent")  # 不應該拋出異常 

@pytest.mark.asyncio
async def test_plugin_config_validation_and_dependencies():
    """測試插件配置驗證和依賴關係"""
    manager = PluginConfigManager()
    
    # 創建一系列相互依賴的插件
    plugin_a = PluginConfig(
        name="plugin_a",
        enabled=True,
        version="1.0.0",
        settings={"port": 8080},
        dependencies=["plugin_b"],
        validation_rules={
            "port": {
                "type": int,
                "min": 1024,
                "max": 65535
            }
        }
    )
    
    plugin_b = PluginConfig(
        name="plugin_b",
        enabled=True,
        version="1.0.0",
        settings={"port": 8081},
        dependencies=["plugin_c"]
    )
    
    plugin_c = PluginConfig(
        name="plugin_c",
        enabled=True,
        version="1.0.0",
        settings={"port": 8082}
    )
    
    # 測試依賴順序
    await manager.add_config(plugin_c)
    await manager.add_config(plugin_b)
    await manager.add_config(plugin_a)
    
    load_order = await manager.get_load_order()
    assert load_order == ["plugin_c", "plugin_b", "plugin_a"]
    
    # 測試循環依賴檢測
    plugin_c.dependencies = ["plugin_a"]
    with pytest.raises(ValidationError, match="循環依賴"):
        await manager.validate_dependencies()
    
    # 測試端口衝突
    plugin_d = PluginConfig(
        name="plugin_d",
        enabled=True,
        settings={"port": 8080}  # 與 plugin_a 使用相同端口
    )
    
    with pytest.raises(ValidationError, match="端口.*衝突"):
        await manager.add_config(plugin_d)
    
    # 測試版本管理
    assert plugin_a.check_version(">= 1.0.0")
    assert not plugin_a.check_version("> 1.0.0")
    
    await plugin_a.update_version("1.1.0")
    assert plugin_a.version == "1.1.0"
    
    with pytest.raises(ValidationError):
        await plugin_a.update_version("invalid") 