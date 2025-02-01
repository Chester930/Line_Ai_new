import pytest
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
import pandas as pd
from src.admin.pages.logs import LogViewerUI

class TestLogViewerUI:
    @pytest.fixture
    def logs_ui(self):
        return LogViewerUI()
    
    @pytest.fixture
    def mock_streamlit(self):
        with patch('streamlit.title') as mock_title, \
             patch('streamlit.date_input') as mock_date, \
             patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.dataframe') as mock_df, \
             patch('streamlit.info') as mock_info, \
             patch('streamlit.warning') as mock_warning:
            yield {
                'title': mock_title,
                'date': mock_date,
                'selectbox': mock_selectbox,
                'dataframe': mock_df,
                'info': mock_info,
                'warning': mock_warning
            }
    
    @pytest.fixture
    def sample_logs(self):
        return """
2024-02-20 10:00:00 [INFO] cag.core: System started
2024-02-20 10:01:00 [DEBUG] cag.models: Loading model configuration
2024-02-20 10:02:00 [WARNING] cag.plugins: Plugin 'test' not found
2024-02-20 10:03:00 [ERROR] cag.database: Connection failed
2024-02-20 10:04:00 [INFO] cag.session: New session created
"""
    
    def test_initialize(self, logs_ui):
        """測試初始化"""
        assert logs_ui.log_dir == Path("logs")
    
    def test_render_controls(self, logs_ui, mock_streamlit):
        """測試渲染控制項"""
        today = datetime.now().date()
        mock_streamlit['date'].return_value = today
        mock_streamlit['selectbox'].return_value = "ALL"
        
        logs_ui.render()
        
        # 驗證標題
        mock_streamlit['title'].assert_called_once_with("系統日誌")
        
        # 驗證日期選擇器
        mock_streamlit['date'].assert_called_once_with(
            "選擇日期",
            value=today,
            max_value=today
        )
        
        # 驗證日誌級別選擇器
        mock_streamlit['selectbox'].assert_called_once_with(
            "日誌級別",
            ["ALL", "DEBUG", "INFO", "WARNING", "ERROR"]
        )
    
    def test_parse_logs_all_levels(self, logs_ui, sample_logs):
        """測試解析所有級別的日誌"""
        with patch("builtins.open", mock_open(read_data=sample_logs)):
            logs = logs_ui._parse_logs(Path("test.log"), "ALL")
            
            assert len(logs) == 5
            assert logs[0]["級別"] == "INFO"
            assert logs[1]["級別"] == "DEBUG"
            assert logs[2]["級別"] == "WARNING"
            assert logs[3]["級別"] == "ERROR"
            assert logs[4]["級別"] == "INFO"
    
    def test_parse_logs_filtered(self, logs_ui, sample_logs):
        """測試按級別過濾日誌"""
        with patch("builtins.open", mock_open(read_data=sample_logs)):
            # 測試 INFO 級別
            info_logs = logs_ui._parse_logs(Path("test.log"), "INFO")
            assert len(info_logs) == 2
            assert all(log["級別"] == "INFO" for log in info_logs)
            
            # 測試 ERROR 級別
            error_logs = logs_ui._parse_logs(Path("test.log"), "ERROR")
            assert len(error_logs) == 1
            assert error_logs[0]["級別"] == "ERROR"
    
    def test_render_logs_exists(self, logs_ui, mock_streamlit, sample_logs):
        """測試渲染存在的日誌"""
        # 模擬日誌文件存在
        with patch('pathlib.Path.exists', return_value=True), \
             patch("builtins.open", mock_open(read_data=sample_logs)):
            logs_ui.render()
            
            # 驗證數據框顯示
            mock_streamlit['dataframe'].assert_called_once()
            df_arg = mock_streamlit['dataframe'].call_args[0][0]
            assert isinstance(df_arg, pd.DataFrame)
            assert len(df_arg) == 5
    
    def test_render_logs_not_exists(self, logs_ui, mock_streamlit):
        """測試渲染不存在的日誌"""
        # 模擬日誌文件不存在
        with patch('pathlib.Path.exists', return_value=False):
            logs_ui.render()
            
            # 驗證警告提示
            mock_streamlit['warning'].assert_called_once()
            assert "找不到日期" in mock_streamlit['warning'].call_args[0][0]
    
    def test_render_empty_logs(self, logs_ui, mock_streamlit):
        """測試渲染空日誌"""
        # 模擬空日誌文件
        with patch('pathlib.Path.exists', return_value=True), \
             patch("builtins.open", mock_open(read_data="")):
            logs_ui.render()
            
            # 驗證信息提示
            mock_streamlit['info'].assert_called_once_with("沒有符合條件的日誌")
    
    def test_parse_invalid_log_line(self, logs_ui):
        """測試解析無效的日誌行"""
        invalid_log = "Invalid log line format"
        with patch("builtins.open", mock_open(read_data=invalid_log)):
            logs = logs_ui._parse_logs(Path("test.log"), "ALL")
            assert len(logs) == 0
    
    def test_log_date_format(self, logs_ui, mock_streamlit):
        """測試日誌日期格式"""
        today = datetime.now().date()
        mock_streamlit['date'].return_value = today
        
        logs_ui.render()
        
        # 驗證日誌文件名格式
        expected_filename = f"cag_{today:%Y%m%d}.log"
        assert expected_filename in str(logs_ui.log_dir / expected_filename)
    
    def test_module_filtering(self, logs_ui, sample_logs):
        """測試模組過濾"""
        with patch("builtins.open", mock_open(read_data=sample_logs)):
            logs = logs_ui._parse_logs(Path("test.log"), "ALL")
            
            # 驗證模組名稱
            modules = {log["模組"] for log in logs}
            assert modules == {"cag.core", "cag.models", "cag.plugins", "cag.database", "cag.session"} 