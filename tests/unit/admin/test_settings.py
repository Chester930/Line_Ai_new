import pytest
from unittest.mock import Mock, patch
from src.admin.pages.settings import SystemSettingsUI
from src.shared.config.cag_config import CAGSystemConfig

class TestSystemSettingsUI:
    @pytest.fixture
    def settings_ui(self):
        with patch('src.shared.config.cag_config.ConfigManager') as mock_config_manager, \
             patch('src.shared.config.plugin_config.PluginConfigManager') as mock_plugin_config:
            ui = SystemSettingsUI()
            yield ui
    
    @pytest.fixture
    def mock_streamlit(self):
        with patch('streamlit.title') as mock_title, \
             patch('streamlit.header') as mock_header, \
             patch('streamlit.subheader') as mock_subheader, \
             patch('streamlit.form') as mock_form, \
             patch('streamlit.number_input') as mock_number_input, \
             patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.slider') as mock_slider, \
             patch('streamlit.form_submit_button') as mock_submit, \
             patch('streamlit.success') as mock_success, \
             patch('streamlit.error') as mock_error, \
             patch('streamlit.expander') as mock_expander, \
             patch('streamlit.button') as mock_button:
            yield {
                'title': mock_title,
                'header': mock_header,
                'subheader': mock_subheader,
                'form': mock_form,
                'number_input': mock_number_input,
                'selectbox': mock_selectbox,
                'text_input': mock_text_input,
                'slider': mock_slider,
                'submit': mock_submit,
                'success': mock_success,
                'error': mock_error,
                'expander': mock_expander,
                'button': mock_button
            }
    
    @pytest.fixture
    def sample_config(self):
        return CAGSystemConfig(
            max_context_length=2000,
            max_history_messages=10,
            memory_ttl=3600,
            max_memory_items=1000,
            enable_state_tracking=True,
            max_state_history=100,
            default_model="gemini",
            log_level="INFO",
            enable_debug=False,
            models={
                "gemini": Mock(
                    api_key="test_key",
                    max_tokens=1000,
                    temperature=0.7
                )
            }
        )
    
    def test_initialize(self, settings_ui):
        """測試初始化"""
        assert settings_ui.config_manager is not None
        assert settings_ui.plugin_config_manager is not None
    
    def test_render_basic_settings(self, settings_ui, mock_streamlit, sample_config):
        """測試渲染基礎配置"""
        # 模擬配置載入
        settings_ui.config_manager.load_config.return_value = sample_config
        
        settings_ui.render()
        
        # 驗證標題和表單
        mock_streamlit['title'].assert_called_once_with("系統配置")
        mock_streamlit['header'].assert_any_call("基礎配置")
        mock_streamlit['form'].assert_any_call("basic_settings")
    
    def test_update_basic_settings(self, settings_ui, mock_streamlit, sample_config):
        """測試更新基礎配置"""
        # 模擬配置載入
        settings_ui.config_manager.load_config.return_value = sample_config
        
        # 模擬表單輸入
        mock_streamlit['number_input'].side_effect = [3000, 20, 7200, 2000]
        mock_streamlit['selectbox'].return_value = "DEBUG"
        mock_streamlit['submit'].return_value = True
        
        settings_ui.render()
        
        # 驗證配置更新
        assert sample_config.max_context_length == 3000
        assert sample_config.max_history_messages == 20
        assert sample_config.memory_ttl == 7200
        assert sample_config.max_memory_items == 2000
        assert sample_config.log_level == "DEBUG"
        
        # 驗證配置保存
        settings_ui.config_manager.save_config.assert_called_once()
    
    def test_render_model_settings(self, settings_ui, mock_streamlit, sample_config):
        """測試渲染模型配置"""
        # 模擬配置載入
        settings_ui.config_manager.load_config.return_value = sample_config
        
        settings_ui.render()
        
        # 驗證模型配置部分
        mock_streamlit['header'].assert_any_call("AI 模型配置")
        mock_streamlit['selectbox'].assert_any_call(
            "默認模型",
            ["gemini"]
        )
    
    def test_update_model_settings(self, settings_ui, mock_streamlit, sample_config):
        """測試更新模型配置"""
        # 模擬配置載入
        settings_ui.config_manager.load_config.return_value = sample_config
        
        # 模擬模型設置輸入
        mock_streamlit['text_input'].return_value = "new_key"
        mock_streamlit['number_input'].return_value = 2000
        mock_streamlit['slider'].return_value = 0.8
        mock_streamlit['submit'].return_value = True
        
        settings_ui.render()
        
        # 驗證模型配置更新
        model_config = sample_config.models["gemini"]
        assert model_config.api_key == "new_key"
        assert model_config.max_tokens == 2000
        assert model_config.temperature == 0.8
        
        # 驗證配置保存
        settings_ui.config_manager.save_config.assert_called()
    
    def test_change_default_model(self, settings_ui, mock_streamlit, sample_config):
        """測試更改默認模型"""
        # 模擬配置載入
        settings_ui.config_manager.load_config.return_value = sample_config
        
        # 模擬選擇新的默認模型
        mock_streamlit['selectbox'].return_value = "gpt"
        
        settings_ui.render()
        
        # 驗證默認模型更新
        assert sample_config.default_model == "gpt"
        settings_ui.config_manager.save_config.assert_called()
    
    def test_reload_config(self, settings_ui, mock_streamlit):
        """測試重新載入配置"""
        # 模擬重載按鈕點擊
        mock_streamlit['button'].return_value = True
        
        settings_ui.render()
        
        # 驗證配置重載
        settings_ui.config_manager.load_config.assert_called()
        settings_ui.plugin_config_manager.load_configs.assert_called()
        mock_streamlit['success'].assert_called_with("配置已重新載入")
    
    def test_error_handling(self, settings_ui, mock_streamlit):
        """測試錯誤處理"""
        # 模擬配置保存錯誤
        settings_ui.config_manager.save_config.side_effect = Exception("Save error")
        
        # 模擬表單提交
        mock_streamlit['submit'].return_value = True
        
        settings_ui.render()
        
        # 驗證錯誤提示
        mock_streamlit['error'].assert_called()
        assert "保存配置失敗" in mock_streamlit['error'].call_args[0][0]
    
    def test_validation(self, settings_ui, mock_streamlit, sample_config):
        """測試配置驗證"""
        # 模擬配置載入
        settings_ui.config_manager.load_config.return_value = sample_config
        
        # 模擬無效輸入
        mock_streamlit['number_input'].return_value = -1
        mock_streamlit['submit'].return_value = True
        
        settings_ui.render()
        
        # 驗證錯誤提示
        mock_streamlit['error'].assert_called() 