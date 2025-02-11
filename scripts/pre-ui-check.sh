#!/bin/bash

# API 端點驗證
curl -sSf http://localhost:8000/health > /dev/null || exit 1

# 測試覆蓋率檢查
coverage=$(pytest --cov=src --cov-report=term | grep TOTAL | awk '{print $4}')
if (( $(echo "$coverage < 70" | bc -l) )); then
    echo "測試覆蓋率不足: $coverage%"
    exit 2
fi

# 效能基準測試
locust -f tests/performance/basic.py --headless -u 100 -r 10 --run-time 1m || exit 3 