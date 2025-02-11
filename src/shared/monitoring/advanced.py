class PerformanceProfiler:
    def __init__(self):
        self.metrics = defaultdict(list)
        self.alert_rules = {
            'high_latency': {'threshold': 500, 'window': '5m'},
            'error_rate': {'threshold': 0.05, 'window': '1h'}
        }
        
    async def track_metric(self, name: str, value: float):
        """即時效能指標追蹤"""
        self.metrics[name].append({
            'timestamp': datetime.now(),
            'value': value
        })
        await self._check_alerts(name)
        
    async def _check_alerts(self, metric_name: str):
        """實作滑動窗口警報"""
        window = self.alert_rules[metric_name]['window']
        threshold = self.alert_rules[metric_name]['threshold']
        
        # 計算最近時間窗口內的平均值
        now = datetime.now()
        window_start = now - timedelta(minutes=int(window[:-1]))
        
        window_data = [
            m['value'] for m in self.metrics[metric_name]
            if m['timestamp'] > window_start
        ]
        
        if window_data:
            avg_value = sum(window_data) / len(window_data)
            if avg_value > threshold:
                await self._trigger_alert(metric_name, avg_value)
        
    async def _trigger_alert(self, metric_name: str, value: float):
        """實作異常警報觸發"""
        # 實作警報觸發邏輯
        # ... 