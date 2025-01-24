# 部署指南

## 環境要求

- Python 3.11+
- Docker & Docker Compose (可選)
- Redis (用於會話管理)
- 足夠的硬碟空間 (建議 10GB+)

## 部署方式

### 1. 直接部署

1. 準備環境
```bash
# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安裝依賴
pip install -r requirements.txt
```

2. 配置環境變量
```bash
cp .env.example .env
# 編輯 .env 文件，填入必要的配置
```

3. 啟動服務
```bash
# 開發環境
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 生產環境
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Docker 部署

1. 構建鏡像
```bash
docker-compose -f deploy/docker-compose.yml build
```

2. 啟動服務
```bash
docker-compose -f deploy/docker-compose.yml up -d
```

3. 查看日誌
```bash
docker-compose -f deploy/docker-compose.yml logs -f
```

## 配置說明

### 必要配置
- `LINE_CHANNEL_SECRET`: LINE Channel 密鑰
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Channel 訪問令牌
- `GOOGLE_API_KEY`: Google API 密鑰

### 可選配置
- `MODEL_TIMEOUT`: 模型調用超時時間（秒）
- `MAX_RETRIES`: 重試次數
- `LOG_LEVEL`: 日誌級別
- `CONTEXT_LIMIT`: 上下文限制（字符數）

## 監控與維護

### 健康檢查
```bash
curl http://localhost:8000/health
```

### 日誌查看
```bash
# 直接部署
tail -f logs/app.log

# Docker 部署
docker-compose -f deploy/docker-compose.yml logs -f app
```

### 備份
建議定期備份以下內容：
- 環境配置文件
- 日誌文件
- Redis 數據（如果使用）

## 故障排除

### 常見問題

1. 服務無法啟動
- 檢查環境變量配置
- 檢查端口佔用
- 檢查日誌輸出

2. AI 模型調用失敗
- 驗證 API 密鑰
- 檢查網絡連接
- 查看錯誤日誌

3. 記憶體使用過高
- 調整 `CONTEXT_LIMIT`
- 減少並發數
- 增加系統資源

## 安全建議

1. 環境配置
- 使用環境變量而非硬編碼
- 定期更換密鑰
- 限制訪問權限

2. 網絡安全
- 啟用 HTTPS
- 配置防火牆
- 限制 IP 訪問

3. 數據安全
- 定期備份
- 加密敏感數據
- 日誌脫敏 