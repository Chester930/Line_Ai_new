import streamlit as st
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

class LogViewerUI:
    def __init__(self):
        self.log_dir = Path("logs")
    
    def render(self):
        st.title("系統日誌")
        
        # 選擇日期
        today = datetime.now().date()
        selected_date = st.date_input(
            "選擇日期",
            value=today,
            max_value=today
        )
        
        # 選擇日誌級別
        log_level = st.selectbox(
            "日誌級別",
            ["ALL", "DEBUG", "INFO", "WARNING", "ERROR"]
        )
        
        # 讀取日誌文件
        log_file = self.log_dir / f"cag_{selected_date:%Y%m%d}.log"
        if log_file.exists():
            logs = self._parse_logs(log_file, log_level)
            if logs:
                st.dataframe(pd.DataFrame(logs))
            else:
                st.info("沒有符合條件的日誌")
        else:
            st.warning(f"找不到日期 {selected_date} 的日誌文件")
    
    def _parse_logs(self, log_file: Path, level: str) -> list:
        """解析日誌文件"""
        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    # 解析日誌行
                    parts = line.split(None, 4)
                    if len(parts) >= 5:
                        log_level = parts[1].strip('[]')
                        if level == "ALL" or log_level == level:
                            logs.append({
                                "時間": f"{parts[0]} {parts[1]}",
                                "級別": log_level,
                                "模組": parts[2],
                                "消息": parts[4].strip()
                            })
                except Exception:
                    continue
        return logs

def show():
    ui = LogViewerUI()
    ui.render() 