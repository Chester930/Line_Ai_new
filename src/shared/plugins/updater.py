import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
import tempfile
import shutil
from pathlib import Path
import logging
from .version import PluginVersionManager, PluginVersion
from .manager import PluginManager
from ..config.plugin_config import PluginConfigManager

logger = logging.getLogger(__name__)

class PluginUpdater:
    """插件更新管理器"""
    
    def __init__(
        self,
        plugin_manager: PluginManager,
        version_manager: PluginVersionManager,
        config_manager: PluginConfigManager,
        update_url: str = "https://api.example.com/plugins"
    ):
        self.plugin_manager = plugin_manager
        self.version_manager = version_manager
        self.config_manager = config_manager
        self.update_url = update_url
        self.session = aiohttp.ClientSession()
    
    async def check_updates(self) -> Dict[str, PluginVersion]:
        """檢查更新"""
        available_updates = {}
        
        try:
            async with self.session.get(f"{self.update_url}/versions") as response:
                if response.status == 200:
                    remote_versions = await response.json()
                    
                    for plugin_name, config in self.config_manager.configs.items():
                        current_version = config.version
                        if plugin_name in remote_versions:
                            latest = PluginVersion(**remote_versions[plugin_name])
                            if self._is_newer_version(latest.version, current_version):
                                available_updates[plugin_name] = latest
                                
        except Exception as e:
            logger.error(f"檢查更新失敗: {str(e)}")
        
        return available_updates
    
    async def update_plugin(
        self,
        plugin_name: str,
        target_version: Optional[str] = None
    ) -> bool:
        """更新插件"""
        try:
            # 獲取當前版本
            current_config = self.config_manager.get_plugin_config(plugin_name)
            if not current_config:
                return False
            
            current_version = current_config.version
            
            # 獲取升級路徑
            upgrade_path = self.version_manager.get_upgrade_path(
                plugin_name,
                current_version,
                target_version
            )
            
            if not upgrade_path:
                return False
            
            # 創建臨時目錄
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # 下載並應用每個版本的更新
                for version in upgrade_path:
                    logger.info(f"正在更新 {plugin_name} 到版本 {version.version}")
                    
                    # 下載更新包
                    package_path = await self._download_update(
                        plugin_name,
                        version.version,
                        temp_path
                    )
                    
                    if not package_path:
                        raise Exception("下載更新包失敗")
                    
                    # 安裝依賴
                    await self._install_requirements(version.requirements)
                    
                    # 備份當前版本
                    await self._backup_plugin(plugin_name)
                    
                    try:
                        # 停用插件
                        plugin = self.plugin_manager.get_plugin(plugin_name)
                        if plugin:
                            await plugin.cleanup()
                        
                        # 解壓並安裝更新
                        await self._install_update(package_path, plugin_name)
                        
                        # 更新配置中的版本號
                        current_config.version = version.version
                        self.config_manager.save_configs()
                        
                        # 重新載入插件
                        await self.plugin_manager.reload_plugin(f"plugins/{plugin_name}.py")
                        
                    except Exception as e:
                        # 如果更新失敗，還原備份
                        await self._restore_backup(plugin_name)
                        raise Exception(f"安裝更新失敗: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"更新插件失敗: {str(e)}")
            return False
    
    async def _download_update(
        self,
        plugin_name: str,
        version: str,
        temp_dir: Path
    ) -> Optional[Path]:
        """下載更新包"""
        try:
            url = f"{self.update_url}/download/{plugin_name}/{version}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    package_path = temp_dir / f"{plugin_name}-{version}.zip"
                    with open(package_path, 'wb') as f:
                        f.write(await response.read())
                    return package_path
                return None
        except Exception as e:
            logger.error(f"下載更新包失敗: {str(e)}")
            return None
    
    async def _install_requirements(self, requirements: List[str]):
        """安裝依賴包"""
        if not requirements:
            return
            
        try:
            import pip
            for req in requirements:
                pip.main(['install', req])
        except Exception as e:
            logger.error(f"安裝依賴失敗: {str(e)}")
            raise
    
    async def _backup_plugin(self, plugin_name: str):
        """備份插件"""
        plugin_path = Path(f"plugins/{plugin_name}.py")
        backup_path = Path(f"plugins/backup/{plugin_name}.py.bak")
        
        if plugin_path.exists():
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(plugin_path, backup_path)
    
    async def _restore_backup(self, plugin_name: str):
        """還原備份"""
        backup_path = Path(f"plugins/backup/{plugin_name}.py.bak")
        plugin_path = Path(f"plugins/{plugin_name}.py")
        
        if backup_path.exists():
            shutil.copy2(backup_path, plugin_path)
    
    async def _install_update(self, package_path: Path, plugin_name: str):
        """安裝更新"""
        import zipfile
        
        with zipfile.ZipFile(package_path, 'r') as zip_ref:
            zip_ref.extractall("plugins")
    
    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """檢查版本1是否比版本2新"""
        try:
            v1 = semver.VersionInfo.parse(version1)
            v2 = semver.VersionInfo.parse(version2)
            return v1 > v2
        except ValueError:
            return False
    
    async def close(self):
        """關閉更新管理器"""
        await self.session.close() 