import pytest
from unittest.mock import Mock, patch
from src.shared.version.controller import VersionController
from src.shared.version.models import Version, VersionInfo
from src.shared.exceptions import VersionError

class TestVersionControl:
    @pytest.fixture
    def version_controller(self):
        return VersionController()
    
    def test_version_parsing(self, version_controller):
        """測試版本號解析"""
        version = version_controller.parse_version("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
    
    def test_version_comparison(self, version_controller):
        """測試版本比較"""
        v1 = version_controller.parse_version("1.0.0")
        v2 = version_controller.parse_version("1.1.0")
        v3 = version_controller.parse_version("2.0.0")
        
        assert v1 < v2 < v3
        assert v3 > v2 > v1
        assert v1 != v2
    
    @pytest.mark.asyncio
    async def test_version_check(self, version_controller):
        """測試版本檢查"""
        with patch.object(version_controller, 'fetch_latest_version') as mock_fetch:
            mock_fetch.return_value = "1.1.0"
            
            result = await version_controller.check_version("1.0.0")
            assert result.has_update
            assert result.latest_version == "1.1.0"
    
    @pytest.mark.asyncio
    async def test_compatibility_check(self, version_controller):
        """測試兼容性檢查"""
        version_info = VersionInfo(
            version="1.1.0",
            min_supported="1.0.0",
            dependencies={
                "python": ">=3.8.0",
                "database": ">=1.0.0"
            }
        )
        
        result = await version_controller.check_compatibility(version_info)
        assert result.is_compatible
        assert len(result.issues) == 0
    
    @pytest.mark.asyncio
    async def test_update_process(self, version_controller):
        """測試更新流程"""
        with patch.object(version_controller, 'backup_current_version') as mock_backup, \
             patch.object(version_controller, 'apply_update') as mock_apply, \
             patch.object(version_controller, 'verify_update') as mock_verify:
            
            await version_controller.perform_update("1.1.0")
            
            mock_backup.assert_called_once()
            mock_apply.assert_called_once_with("1.1.0")
            mock_verify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rollback(self, version_controller):
        """測試回滾機制"""
        with patch.object(version_controller, 'apply_update', side_effect=Exception("Update failed")):
            with pytest.raises(VersionError):
                await version_controller.perform_update("1.1.0")
            
            # 驗證回滾
            assert version_controller.get_current_version() == "1.0.0"
    
    def test_invalid_version(self, version_controller):
        """測試無效版本號"""
        with pytest.raises(ValueError):
            version_controller.parse_version("invalid")
    
    @pytest.mark.asyncio
    async def test_dependency_check(self, version_controller):
        """測試依賴檢查"""
        dependencies = {
            "python": ">=3.8.0",
            "database": ">=1.0.0"
        }
        
        result = await version_controller.check_dependencies(dependencies)
        assert result.is_satisfied
        assert len(result.missing) == 0
    
    @pytest.mark.asyncio
    async def test_migration(self, version_controller):
        """測試數據遷移"""
        with patch.object(version_controller, 'run_migrations') as mock_migrate:
            await version_controller.perform_update("1.1.0", migrate=True)
            mock_migrate.assert_called_once() 