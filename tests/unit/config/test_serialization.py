import pytest
from pathlib import Path
from src.shared.config.json_config import JSONConfig, EnhancedPathEncoder, Settings
import json
import re

class TestSerialization:
    @pytest.mark.asyncio
    async def test_path_serialization(self, tmp_path):
        """测试路径序列化"""
        config = JSONConfig(
            data_path=tmp_path / "data",
            config_file_path=tmp_path / "config.json"
        )
        
        # 手动触发配置同步
        config._sync_config()
        
        # 验证序列化
        serialized = json.dumps(config.config_data, cls=EnhancedPathEncoder)
        assert "data_path" in serialized
        assert re.search(r'["\']data_path["\']\s*:\s*["\'].*data["\']', serialized)
        
        # 验证反序列化
        loaded_data = json.loads(serialized)
        loaded_config = JSONConfig(**loaded_data)
        assert isinstance(loaded_config.data_path, Path)
        assert loaded_config.data_path.as_posix() == config.data_path.as_posix()

    @pytest.mark.asyncio
    async def test_complex_serialization(self, tmp_path):
        """测试复杂对象序列化"""
        complex_config = JSONConfig(
            data_path=tmp_path / "data",
            config_file_path=tmp_path / "config.json",
            settings=Settings(database={"host": "localhost"})
        )
        complex_config._sync_config()
        
        # 序列化包含嵌套结构
        serialized = json.dumps(complex_config.config_data, cls=EnhancedPathEncoder)
        assert "database" in serialized
        
        # 反序列化验证
        loaded = json.loads(serialized)
        assert loaded["settings"]["database"]["host"] == "localhost"

    @pytest.mark.asyncio
    async def test_empty_config_serialization(self):
        """测试空配置序列化"""
        config = JSONConfig.model_construct(
            app_name=None,
            settings=None,
            debug=None,
            port=None,
            data_path=None,
            version=None,
            api_key=None,
            config_file_path=None,
            config_data={},
            is_loaded=False,
            env_prefix=None
        )
        config._sync_config()
        
        serialized = json.dumps(config.config_data, cls=EnhancedPathEncoder)
        expected_fields = ['app_name', 'settings', 'debug', 'port', 'data_path', 'version', 'api_key']
        for field in expected_fields:
            assert f'"{field}": null' in serialized
        
        # 反序列化验证
        loaded = json.loads(serialized)
        assert loaded == {}

    @pytest.mark.asyncio
    async def test_partial_config_serialization(self):
        """测试部分字段序列化"""
        config = JSONConfig.model_construct(
            app_name="partial_app",
            data_path=Path("/partial/path")
        )
        config._sync_config()
        
        serialized = json.dumps(config.config_data, cls=EnhancedPathEncoder)
        assert "partial_app" in serialized
        assert re.search(r'["\']data_path["\']\s*:\s*["\'][\\\\/]partial[\\\\/]path["\']', serialized)
        assert "debug" not in serialized 