import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from src.admin.pages.plugins import PluginManagementUI
from src.shared.plugins.version import PluginVersion

class TestPluginManagementUI:
    @pytest.fixture
    def plugins_ui(self):
        with patch('src.shared.plugins.manager.PluginManager') as mock_manager, \
             patch('src.shared.plugins.version.PluginVersionManager') as mock_version_manager, \
             patch('src.shared.config.plugin_config.plugin_config_manager') as mock_config_manager:
            ui = PluginManagementUI()
            yield ui
            # 清理資源
            asyncio.run(ui.updater.close())
    
    @pytest.fixture
    def mock_streamlit(self):
        with patch('streamlit.title') as mock_title, \
             patch('streamlit.header') as mock_header, \
             patch('streamlit.expander') as mock_expander, \
             patch('streamlit.toggle') as mock_toggle, \
             patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.number_input') as mock_number_input, \
             patch('streamlit.checkbox') as mock_checkbox, \
             patch('streamlit.button') as mock_button, \
             patch('streamlit.success') as mock_success, \
             patch('streamlit.error') as mock_error, \
             patch('streamlit.warning') as mock_warning, \
             patch('streamlit.info') as mock_info, \
             patch('streamlit.spinner') as mock_spinner:
            yield {
                'title': mock_title,
                'header': mock_header,
                'expander': mock_expander,
                'toggle': mock_toggle,
                'text_input': mock_text_input,
                'number_input': mock_number_input,
                'checkbox': mock_checkbox,
                'button': mock_button,
                'success': mock_success,
                'error': mock_error,
                'warning': mock_warning,
                'info': mock_info,
                'spinner': mock_spinner
            }
    
    @pytest.fixture
    def sample_plugins(self):
        return {
            "test_plugin": Mock(
                name="test_plugin",
                version="1.0.0",
                enabled=True,
                settings={
                    "api_key": "test_key",
                    "max_retries": 3
                }
            )
        }
    
    def test_initialize(self, plugins_ui):
        """測試初始化"""
        assert plugins_ui.plugin_manager is not None
        assert plugins_ui.config_manager is not None
        assert plugins_ui.version_manager is not None
        assert plugins_ui.updater is not None
    
    def test_render_plugin_list(self, plugins_ui, mock_streamlit, sample_plugins):
        """測試渲染插件列表"""
        # 模擬配置
        plugins_ui.config_manager.configs = sample_plugins
        
        plugins_ui.render()
        
        # 驗證標題和頭部
        mock_streamlit['title'].assert_called_once_with("插件管理")
        mock_streamlit['header'].assert_any_call("已安裝的插件")
    
    def test_plugin_toggle(self, plugins_ui, mock_streamlit, sample_plugins):
        """測試插件啟用/禁用開關"""
        # 模擬配置
        plugins_ui.config_manager.configs = sample_plugins
        
        # 模擬開關切換
        mock_streamlit['toggle'].return_value = False
        
        with patch.object(plugins_ui, '_disable_plugin') as mock_disable:
            plugins_ui.render()
            mock_disable.assert_called_once_with("test_plugin")
    
    def test_plugin_settings(self, plugins_ui, mock_streamlit, sample_plugins):
        """測試插件設置"""
        # 模擬配置
        plugins_ui.config_manager.configs = sample_plugins
        
        # 模擬設置更新
        mock_streamlit['text_input'].return_value = "new_key"
        mock_streamlit['number_input'].return_value = 5
        
        plugins_ui.render()
        
        # 驗證配置保存
        plugins_ui.config_manager.save_configs.assert_called()
    
    @pytest.mark.asyncio
    async def test_plugin_reload(self, plugins_ui, mock_streamlit, sample_plugins):
        """測試插件重新載入"""
        # 模擬配置
        plugins_ui.config_manager.configs = sample_plugins
        
        # 模擬重載按鈕點擊
        mock_streamlit['button'].side_effect = [True, False]  # 重載按鈕點擊，清理按鈕不點擊
        
        with patch.object(plugins_ui, '_reload_plugin') as mock_reload:
            plugins_ui.render()
            mock_reload.assert_called_once_with("test_plugin")
    
    @pytest.mark.asyncio
    async def test_plugin_cleanup(self, plugins_ui, mock_streamlit, sample_plugins):
        """測試插件清理"""
        # 模擬配置
        plugins_ui.config_manager.configs = sample_plugins
        
        # 模擬清理按鈕點擊
        mock_streamlit['button'].side_effect = [False, True]  # 重載按鈕不點擊，清理按鈕點擊
        
        with patch.object(plugins_ui, '_cleanup_plugin') as mock_cleanup:
            plugins_ui.render()
            mock_cleanup.assert_called_once_with("test_plugin")
    
    def test_version_check(self, plugins_ui, mock_streamlit, sample_plugins):
        """測試版本檢查"""
        # 模擬配置
        plugins_ui.config_manager.configs = sample_plugins
        
        # 模擬最新版本
        latest_version = PluginVersion(
            version="1.1.0",
            description="Test Plugin",
            author="Test Author",
            dependencies={},
            requirements=[],
            changes="Test changes"
        )
        plugins_ui.version_manager.get_latest_version.return_value = latest_version
        
        plugins_ui.render()
        
        # 驗證版本提示
        mock_streamlit['warning'].assert_called_with("有新版本可用: 1.1.0")
    
    @pytest.mark.asyncio
    async def test_plugin_update(self, plugins_ui, mock_streamlit, sample_plugins):
        """測試插件更新"""
        # 模擬配置
        plugins_ui.config_manager.configs = sample_plugins
        
        # 模擬更新按鈕點擊
        mock_streamlit['button'].return_value = True
        
        # 模擬更新過程
        with patch.object(plugins_ui.updater, 'update_plugin') as mock_update:
            mock_update.return_value = True
            
            plugins_ui.render()
            
            # 驗證更新成功提示
            mock_streamlit['success'].assert_called_with("更新成功")
    
    def test_compatibility_check(self, plugins_ui, mock_streamlit, sample_plugins):
        """測試兼容性檢查"""
        # 模擬配置
        plugins_ui.config_manager.configs = sample_plugins
        
        # 模擬兼容性問題
        plugins_ui.version_manager.check_compatibility.return_value = [
            "缺少依賴插件: test_dep"
        ]
        
        plugins_ui.render()
        
        # 驗證兼容性警告
        mock_streamlit['error'].assert_called()
        assert "兼容性問題" in mock_streamlit['error'].call_args[0][0]
    
    def test_error_handling(self, plugins_ui, mock_streamlit):
        """測試錯誤處理"""
        # 模擬配置載入錯誤
        plugins_ui.config_manager.load_configs.side_effect = Exception("Config error")
        
        plugins_ui.render()
        
        # 驗證錯誤提示
        mock_streamlit['error'].assert_called() 