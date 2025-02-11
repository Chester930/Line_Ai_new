from prometheus_client import Counter, Histogram
import time
from contextlib import contextmanager

class MetricsCollector:
    """指標收集器"""
    def __init__(self):
        self.response_time = Histogram(
            'response_time_seconds',
            'Response time in seconds'
        )
        self.request_count = Counter(
            'request_total',
            'Total requests'
        )
        
    def track_request(self):
        """追蹤請求"""
        self.request_count.inc()
        
    @contextmanager
    def track_time(self):
        """追蹤響應時間"""
        start = time.time()
        yield
        self.response_time.observe(time.time() - start) 