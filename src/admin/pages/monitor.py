import streamlit as st
import psutil
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from src.shared.utils.logger import logger

class SystemMonitorUI:
    def __init__(self):
        self.history_length = 60  # 保存60個數據點
        self.cpu_history = []
        self.memory_history = []
        self.timestamps = []
    
    def render(self):
        st.title("系統監控")
        
        # 更新系統指標
        self._update_metrics()
        
        # 顯示即時指標
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "CPU 使用率",
                f"{psutil.cpu_percent()}%"
            )
        
        with col2:
            memory = psutil.virtual_memory()
            st.metric(
                "記憶體使用率",
                f"{memory.percent}%"
            )
        
        with col3:
            disk = psutil.disk_usage('/')
            st.metric(
                "磁碟使用率",
                f"{disk.percent}%"
            )
        
        # 顯示歷史圖表
        st.subheader("系統資源使用趨勢")
        
        # CPU 使用率圖表
        fig_cpu = go.Figure()
        fig_cpu.add_trace(go.Scatter(
            x=self.timestamps,
            y=self.cpu_history,
            name="CPU"
        ))
        fig_cpu.update_layout(
            title="CPU 使用率歷史",
            xaxis_title="時間",
            yaxis_title="使用率 (%)"
        )
        st.plotly_chart(fig_cpu)
        
        # 記憶體使用率圖表
        fig_mem = go.Figure()
        fig_mem.add_trace(go.Scatter(
            x=self.timestamps,
            y=self.memory_history,
            name="Memory"
        ))
        fig_mem.update_layout(
            title="記憶體使用率歷史",
            xaxis_title="時間",
            yaxis_title="使用率 (%)"
        )
        st.plotly_chart(fig_mem)
        
        # 顯示進程列表
        st.subheader("進程列表")
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        df = pd.DataFrame(processes)
        df = df.sort_values('cpu_percent', ascending=False).head(10)
        st.dataframe(df)
        
        # 添加網絡統計
        self._show_network_stats()
        
        # 添加磁盤統計
        self._show_disk_stats()
    
    def _update_metrics(self):
        """更新系統指標歷史數據"""
        now = datetime.now()
        
        # 添加新數據
        self.cpu_history.append(psutil.cpu_percent())
        self.memory_history.append(psutil.virtual_memory().percent)
        self.timestamps.append(now)
        
        # 保持固定長度
        if len(self.cpu_history) > self.history_length:
            self.cpu_history.pop(0)
            self.memory_history.pop(0)
            self.timestamps.pop(0)

    def _show_network_stats(self):
        """顯示網絡統計"""
        st.subheader("網絡統計")
        
        # 獲取網絡統計
        net_io = psutil.net_io_counters()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "發送數據",
                f"{net_io.bytes_sent / 1024 / 1024:.2f} MB"
            )
        
        with col2:
            st.metric(
                "接收數據",
                f"{net_io.bytes_recv / 1024 / 1024:.2f} MB"
            )
        
        # 顯示網絡連接
        st.subheader("網絡連接")
        connections = []
        for conn in psutil.net_connections():
            try:
                connections.append({
                    "類型": conn.type,
                    "本地地址": f"{conn.laddr.ip}:{conn.laddr.port}",
                    "遠程地址": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-",
                    "狀態": conn.status
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if connections:
            st.dataframe(pd.DataFrame(connections))

    def _show_disk_stats(self):
        """顯示磁盤統計"""
        st.subheader("磁盤統計")
        
        # 獲取所有磁盤分區
        partitions = psutil.disk_partitions()
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                st.metric(
                    f"分區 {partition.mountpoint}",
                    f"已用: {usage.used / 1024 / 1024 / 1024:.2f} GB / "
                    f"總計: {usage.total / 1024 / 1024 / 1024:.2f} GB"
                )
            except Exception:
                pass

def show():
    ui = SystemMonitorUI()
    ui.render() 