from typing import Dict, Type, Optional, List, Set
from .base import BasePlugin, PluginConfig, PluginError
import logging
import importlib
import pkgutil
from pathlib import Path
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys

logger = logging.getLogger(__name__)

class PluginWatcher(FileSystemEventHandler):
    """插件文件監視器"""
    def __init__(self, manager: 'PluginManager'):
        self.manager = manager
        self.processing = False
    
    async def on_modified(self, event):
        if event.is_directory or self.processing:
            return
            
        if event.src_path.endswith('.py'):
            self.processing = True
            try:
                await self.manager.reload_plugin(event.src_path)
            finally:
                self.processing = False

class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_classes: Dict[str, Type[BasePlugin]] = {}
        self._observer: Optional[Observer] = None
        self._watched_paths: Set[str] = set()
    
    async def start_watching(self, plugins_dir: str) -> None:
        """開始監視插件目錄"""
        if self._observer is None:
            self._observer = Observer()
            event_handler = PluginWatcher(self)
            self._observer.schedule(event_handler, plugins_dir, recursive=False)
            self._observer.start()
            logger.info(f"Started watching plugin directory: {plugins_dir}")
    
    async def stop_watching(self) -> None:
        """停止監視"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Stopped watching plugin directory")
    
    async def reload_plugin(self, plugin_path: str) -> None:
        """重新載入插件"""
        try:
            # 獲取插件名稱
            plugin_name = Path(plugin_path).stem
            
            # 如果插件正在運行，先清理
            if plugin_name in self._plugins:
                await self._plugins[plugin_name].cleanup()
                del self._plugins[plugin_name]
            
            # 重新載入模組
            if plugin_name in sys.modules:
                del sys.modules[plugin_name]
            
            # 動態導入插件模組
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找插件類
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BasePlugin) and 
                    attr != BasePlugin):
                    self._plugin_classes[plugin_name] = attr
                    logger.info(f"Reloaded plugin: {plugin_name}")
                    
                    # 如果有配置，重新初始化插件
                    config = self._get_plugin_config(plugin_name)
                    if config:
                        await self.initialize_plugin(plugin_name, config)
                    break
            
        except Exception as e:
            logger.error(f"Failed to reload plugin {plugin_path}: {str(e)}")
            raise PluginError(f"Failed to reload plugin: {str(e)}")
    
    async def _get_plugin_config(self, plugin_name: str) -> Optional[PluginConfig]:
        """從配置管理器獲取插件配置"""
        try:
            from ..config.plugin_config import plugin_config_manager
            return plugin_config_manager.get_plugin_config(plugin_name)
        except Exception:
            return None
    
    async def load_plugins(self, plugins_dir: str = "plugins") -> None:
        """載入所有插件"""
        try:
            plugins_path = Path(plugins_dir)
            if not plugins_path.exists():
                logger.warning(f"插件目錄不存在: {plugins_dir}")
                return
            
            # 遍歷插件目錄
            for finder, name, _ in pkgutil.iter_modules([str(plugins_path)]):
                try:
                    # 動態導入插件模組
                    spec = finder.find_spec(name)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 查找插件類
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BasePlugin) and 
                            attr != BasePlugin):
                            self._plugin_classes[name] = attr
                            logger.info(f"已載入插件類: {name}")
                            
                except Exception as e:
                    logger.error(f"載入插件 {name} 失敗: {str(e)}")
                    
        except Exception as e:
            logger.error(f"載入插件失敗: {str(e)}")
            raise PluginError(f"Failed to load plugins: {str(e)}")
    
    async def initialize_plugin(
        self,
        name: str,
        config: PluginConfig
    ) -> BasePlugin:
        """初始化插件"""
        try:
            if name not in self._plugin_classes:
                raise PluginError(f"插件未找到: {name}")
                
            plugin_class = self._plugin_classes[name]
            plugin = plugin_class(config)
            
            # 初始化插件
            if await plugin.initialize():
                self._plugins[name] = plugin
                logger.info(f"已初始化插件: {name}")
                return plugin
            else:
                raise PluginError(f"插件初始化失敗: {name}")
                
        except Exception as e:
            logger.error(f"初始化插件 {name} 失敗: {str(e)}")
            raise PluginError(f"Failed to initialize plugin {name}: {str(e)}")
    
    async def execute_plugin(
        self,
        name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """執行插件"""
        try:
            if name not in self._plugins:
                raise PluginError(f"插件未初始化: {name}")
                
            plugin = self._plugins[name]
            if not plugin.is_enabled():
                raise PluginError(f"插件未啟用: {name}")
                
            return await plugin.execute(context)
            
        except Exception as e:
            logger.error(f"執行插件 {name} 失敗: {str(e)}")
            raise PluginError(f"Failed to execute plugin {name}: {str(e)}")
    
    async def cleanup_plugins(self) -> None:
        """清理所有插件"""
        for name, plugin in self._plugins.items():
            try:
                await plugin.cleanup()
                logger.info(f"已清理插件: {name}")
            except Exception as e:
                logger.error(f"清理插件 {name} 失敗: {str(e)}")
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """獲取插件實例"""
        return self._plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """列出所有已載入的插件"""
        return list(self._plugins.keys()) 