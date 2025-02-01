import streamlit as st
import asyncio
from typing import Dict, Any, List
from src.shared.config.plugin_config import plugin_config_manager
from src.shared.plugins.manager import PluginManager
from src.shared.plugins.version import PluginVersionManager, PluginVersion
from src.shared.plugins.updater import PluginUpdater

class PluginManagementUI:
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.config_manager = plugin_config_manager
        self.version_manager = PluginVersionManager()
        self.updater = PluginUpdater(
            self.plugin_manager,
            self.version_manager,
            self.config_manager
        )
    
    def render(self):
        st.title("插件管理")
        
        # 載入插件配置
        self.config_manager.load_configs()
        
        # 顯示插件列表
        st.header("已安裝的插件")
        
        for name, config in self.config_manager.configs.items():
            with st.expander(f"插件: {name} (v{config.version})"):
                # 啟用/禁用開關
                enabled = st.toggle(
                    "啟用",
                    value=config.enabled,
                    key=f"toggle_{name}"
                )
                
                if enabled != config.enabled:
                    config.enabled = enabled
                    self.config_manager.save_configs()
                    if enabled:
                        asyncio.run(self._enable_plugin(name))
                    else:
                        asyncio.run(self._disable_plugin(name))
                
                # 顯示設置
                if config.settings:
                    st.subheader("設置")
                    new_settings = {}
                    for key, value in config.settings.items():
                        if isinstance(value, bool):
                            new_settings[key] = st.checkbox(
                                key,
                                value=value,
                                key=f"setting_{name}_{key}"
                            )
                        elif isinstance(value, (int, float)):
                            new_settings[key] = st.number_input(
                                key,
                                value=value,
                                key=f"setting_{name}_{key}"
                            )
                        else:
                            new_settings[key] = st.text_input(
                                key,
                                value=str(value),
                                key=f"setting_{name}_{key}"
                            )
                    
                    # 如果設置有變更
                    if new_settings != config.settings:
                        config.settings = new_settings
                        self.config_manager.save_configs()
                        st.success("設置已更新")
                
                # 顯示操作按鈕
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("重新載入", key=f"reload_{name}"):
                        asyncio.run(self._reload_plugin(name))
                        st.success("插件已重新載入")
                
                with col2:
                    if st.button("清理", key=f"cleanup_{name}"):
                        asyncio.run(self._cleanup_plugin(name))
                        st.success("插件已清理")
        
        # 添加版本管理部分
        st.header("版本管理")
        
        for name, config in self.config_manager.configs.items():
            with st.expander(f"{name} 版本信息"):
                # 顯示當前版本
                current_version = config.version
                st.text(f"當前版本: {current_version}")
                
                # 獲取最新版本
                latest = self.version_manager.get_latest_version(name)
                if latest and latest.version != current_version:
                    st.warning(f"有新版本可用: {latest.version}")
                    st.text(f"更新說明: {latest.changes}")
                    
                    # 顯示升級路徑
                    upgrade_path = self.version_manager.get_upgrade_path(
                        name, current_version
                    )
                    if upgrade_path:
                        st.subheader("升級路徑")
                        for version in upgrade_path:
                            st.text(
                                f"版本 {version.version}: {version.changes}"
                            )
                        
                        if st.button(f"升級到 {latest.version}", key=f"upgrade_{name}"):
                            self._upgrade_plugin(name, upgrade_path)
                
                # 檢查兼容性
                issues = self.version_manager.check_compatibility(
                    name, current_version
                )
                if issues:
                    st.error("兼容性問題:")
                    for issue in issues:
                        st.text(f"- {issue}")
        
        # 添加自動更新部分
        st.header("自動更新")
        
        if st.button("檢查更新"):
            with st.spinner("正在檢查更新..."):
                updates = asyncio.run(self.updater.check_updates())
                
                if updates:
                    st.success(f"發現 {len(updates)} 個可用更新")
                    for name, version in updates.items():
                        with st.expander(f"{name} v{version.version}"):
                            st.text(f"更新說明: {version.changes}")
                            st.text(f"作者: {version.author}")
                            
                            if version.requirements:
                                st.text("需要安裝以下依賴:")
                                for req in version.requirements:
                                    st.text(f"- {req}")
                            
                            if st.button("更新", key=f"update_{name}"):
                                with st.spinner("正在更新..."):
                                    success = asyncio.run(
                                        self.updater.update_plugin(name)
                                    )
                                    if success:
                                        st.success("更新成功")
                                    else:
                                        st.error("更新失敗")
                else:
                    st.info("所有插件都是最新版本")
    
    async def _enable_plugin(self, name: str):
        """啟用插件"""
        config = self.config_manager.get_plugin_config(name)
        if config:
            await self.plugin_manager.initialize_plugin(name, config)
    
    async def _disable_plugin(self, name: str):
        """禁用插件"""
        plugin = self.plugin_manager.get_plugin(name)
        if plugin:
            await plugin.cleanup()
    
    async def _reload_plugin(self, name: str):
        """重新載入插件"""
        plugin_path = f"plugins/{name}.py"
        await self.plugin_manager.reload_plugin(plugin_path)
    
    async def _cleanup_plugin(self, name: str):
        """清理插件"""
        plugin = self.plugin_manager.get_plugin(name)
        if plugin:
            await plugin.cleanup()
    
    async def _upgrade_plugin(
        self,
        plugin_name: str,
        upgrade_path: List[PluginVersion]
    ):
        """升級插件"""
        try:
            # 禁用插件
            await self._disable_plugin(plugin_name)
            
            # 執行升級
            for version in upgrade_path:
                st.text(f"正在升級到 {version.version}...")
                # TODO: 實現實際的升級邏輯
                
            # 更新配置中的版本號
            config = self.config_manager.get_plugin_config(plugin_name)
            if config:
                config.version = upgrade_path[-1].version
                self.config_manager.save_configs()
            
            # 重新載入插件
            await self._reload_plugin(plugin_name)
            
            st.success("升級完成")
            
        except Exception as e:
            st.error(f"升級失敗: {str(e)}")

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.updater.close()

def show():
    ui = PluginManagementUI()
    ui.render()

if __name__ == "__main__":
    show() 