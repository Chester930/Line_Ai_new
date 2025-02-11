import pytest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime
import psutil
from src.admin.pages.monitor import SystemMonitorUI

class TestSystemMonitorUI:
    @pytest.fixture
    def monitor_ui(self):
        return SystemMonitorUI()
    
    @pytest.fixture
    def mock_streamlit(self):
        with patch('streamlit.title') as mock_title, \
             patch('streamlit.metric') as mock_metric, \
             patch('streamlit.subheader') as mock_subheader, \
             patch('streamlit.plotly_chart') as mock_chart, \
             patch('streamlit.dataframe') as mock_df:
            yield {
                'title': mock_title,
                'metric': mock_metric,
                'subheader': mock_subheader,
                'chart': mock_chart,
                'dataframe': mock_df
            }
    
    @pytest.fixture
    def mock_psutil(self):
        with patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.net_io_counters') as mock_net, \
             patch('psutil.process_iter') as mock_process:
            # 設置 CPU 使用率
            mock_cpu.return_value = 50.0
            
            # 設置記憶體使用率
            mock_memory.return_value = Mock(
                percent=60.0,
                total=16000000000,  # 16GB
                used=9600000000     # 9.6GB
            )
            
            # 設置磁碟使用率
            mock_disk.return_value = Mock(
                percent=70.0,
                total=500000000000,  # 500GB
                used=350000000000    # 350GB
            )
            
            # 設置網絡統計
            mock_net.return_value = Mock(
                bytes_sent=1000000,  # 1MB
                bytes_recv=2000000   # 2MB
            )
            
            # 設置進程列表
            mock_process.return_value = [
                Mock(info={
                    'pid': 1,
                    'name': 'test_process',
                    'cpu_percent': 5.0,
                    'memory_percent': 2.0
                })
            ]
            
            yield {
                'cpu': mock_cpu,
                'memory': mock_memory,
                'disk': mock_disk,
                'net': mock_net,
                'process': mock_process
            }
    
    def test_initialize(self, monitor_ui):
        """測試初始化"""
        assert monitor_ui.history_length == 60
        assert len(monitor_ui.cpu_history) == 0
        assert len(monitor_ui.memory_history) == 0
        assert len(monitor_ui.timestamps) == 0
    
    def test_update_metrics(self, monitor_ui, mock_psutil):
        """測試更新指標"""
        monitor_ui._update_metrics()
        
        assert len(monitor_ui.cpu_history) == 1
        assert len(monitor_ui.memory_history) == 1
        assert len(monitor_ui.timestamps) == 1
        
        assert monitor_ui.cpu_history[0] == 50.0
        assert monitor_ui.memory_history[0] == 60.0
    
    def test_render_metrics(self, monitor_ui, mock_streamlit, mock_psutil):
        """測試渲染指標"""
        monitor_ui.render()
        
        # 驗證標題
        mock_streamlit['title'].assert_called_once_with("系統監控")
        
        # 驗證指標顯示
        mock_streamlit['metric'].assert_any_call(
            "CPU 使用率",
            "50.0%"
        )
        mock_streamlit['metric'].assert_any_call(
            "記憶體使用率",
            "60.0%"
        )
        mock_streamlit['metric'].assert_any_call(
            "磁碟使用率",
            "70.0%"
        )
    
    def test_render_charts(self, monitor_ui, mock_streamlit, mock_psutil):
        """測試渲染圖表"""
        # 先更新一些數據點
        for _ in range(3):
            monitor_ui._update_metrics()
        
        monitor_ui.render()
        
        # 驗證圖表渲染
        assert mock_streamlit['chart'].call_count == 2  # CPU 和記憶體圖表
    
    def test_render_process_list(self, monitor_ui, mock_streamlit, mock_psutil):
        """測試渲染進程列表"""
        monitor_ui.render()
        
        # 驗證進程列表顯示
        mock_streamlit['dataframe'].assert_called_once()
        df_arg = mock_streamlit['dataframe'].call_args[0][0]
        assert isinstance(df_arg, pd.DataFrame)
        assert len(df_arg) == 1
        assert df_arg.iloc[0]['name'] == 'test_process'
    
    def test_history_length_limit(self, monitor_ui, mock_psutil):
        """測試歷史數據長度限制"""
        # 新增超過限制的數據點
        for _ in range(monitor_ui.history_length + 10):
            monitor_ui._update_metrics()
        
        assert len(monitor_ui.cpu_history) == monitor_ui.history_length
        assert len(monitor_ui.memory_history) == monitor_ui.history_length
        assert len(monitor_ui.timestamps) == monitor_ui.history_length
    
    def test_network_stats(self, monitor_ui, mock_streamlit, mock_psutil):
        """測試網絡統計顯示"""
        monitor_ui._show_network_stats()
        
        # 驗證網絡統計顯示
        mock_streamlit['metric'].assert_any_call(
            "發送數據",
            "0.95 MB"
        )
        mock_streamlit['metric'].assert_any_call(
            "接收數據",
            "1.91 MB"
        )
    
    def test_disk_stats(self, monitor_ui, mock_streamlit, mock_psutil):
        """測試磁碟統計顯示"""
        monitor_ui._show_disk_stats()
        
        # 驗證磁碟統計顯示
        mock_streamlit['metric'].assert_called_with(
            "分區 /",
            "已用: 325.99 GB / 總計: 465.66 GB"
        ) 