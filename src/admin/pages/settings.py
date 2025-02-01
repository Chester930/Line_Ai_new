import streamlit as st
import json
from pathlib import Path
from src.shared.config.cag_config import ConfigManager
from src.shared.config.plugin_config import PluginConfigManager
from src.shared.utils.logger import logger

class SystemSettingsUI:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.plugin_config_manager = PluginConfigManager()
    
    def render(self):
        st.title("系統配置")
        
        # 載入配置
        system_config = self.config_manager.load_config()
        
        # 系統基礎配置
        st.header("基礎配置")
        with st.form("basic_settings"):
            # 上下文配置
            st.subheader("上下文配置")
            max_context = st.number_input(
                "最大上下文長度",
                value=system_config.max_context_length,
                min_value=100,
                max_value=10000
            )
            max_history = st.number_input(
                "最大歷史消息數",
                value=system_config.max_history_messages,
                min_value=5,
                max_value=100
            )
            
            # 記憶配置
            st.subheader("記憶配置")
            memory_ttl = st.number_input(
                "記憶存活時間(秒)",
                value=system_config.memory_ttl,
                min_value=60,
                max_value=86400
            )
            max_memory = st.number_input(
                "最大記憶項數",
                value=system_config.max_memory_items,
                min_value=100,
                max_value=10000
            )
            
            # 日誌配置
            st.subheader("日誌配置")
            log_level = st.selectbox(
                "日誌級別",
                ["DEBUG", "INFO", "WARNING", "ERROR"],
                index=["DEBUG", "INFO", "WARNING", "ERROR"].index(
                    system_config.log_level
                )
            )
            
            if st.form_submit_button("保存基礎配置"):
                try:
                    # 更新配置
                    system_config.max_context_length = max_context
                    system_config.max_history_messages = max_history
                    system_config.memory_ttl = memory_ttl
                    system_config.max_memory_items = max_memory
                    system_config.log_level = log_level
                    
                    # 保存配置
                    self.config_manager.save_config()
                    st.success("配置已更新")
                    
                except Exception as e:
                    st.error(f"保存配置失敗: {str(e)}")
        
        # AI 模型配置
        st.header("AI 模型配置")
        
        # 選擇默認模型
        default_model = st.selectbox(
            "默認模型",
            list(system_config.models.keys()),
            index=list(system_config.models.keys()).index(
                system_config.default_model
            )
        )
        
        if default_model != system_config.default_model:
            system_config.default_model = default_model
            self.config_manager.save_config()
            st.success("默認模型已更新")
        
        # 模型配置
        for model_name, model_config in system_config.models.items():
            with st.expander(f"{model_name} 配置"):
                with st.form(f"model_{model_name}"):
                    # API 密鑰
                    api_key = st.text_input(
                        "API 密鑰",
                        value=model_config.api_key,
                        type="password"
                    )
                    
                    # 模型參數
                    max_tokens = st.number_input(
                        "最大 Token 數",
                        value=model_config.max_tokens,
                        min_value=100,
                        max_value=10000
                    )
                    
                    temperature = st.slider(
                        "溫度",
                        value=model_config.temperature,
                        min_value=0.0,
                        max_value=1.0,
                        step=0.1
                    )
                    
                    if st.form_submit_button("保存模型配置"):
                        try:
                            # 更新配置
                            model_config.api_key = api_key
                            model_config.max_tokens = max_tokens
                            model_config.temperature = temperature
                            
                            # 保存配置
                            self.config_manager.save_config()
                            st.success("模型配置已更新")
                            
                        except Exception as e:
                            st.error(f"保存配置失敗: {str(e)}")
        
        # 系統狀態
        st.header("系統狀態")
        if st.button("重新載入配置"):
            try:
                self.config_manager.load_config()
                self.plugin_config_manager.load_configs()
                st.success("配置已重新載入")
            except Exception as e:
                st.error(f"重新載入配置失敗: {str(e)}")

def show():
    ui = SystemSettingsUI()
    ui.render() 