# API 文檔

## 外部 API

### LINE Webhook
```http
POST /webhook/line
Content-Type: application/json
X-Line-Signature: {signature}
```

處理來自 LINE 平台的事件。

#### 請求格式
```json
{
  "destination": "xxxxxxxxxx",
  "events": [
    {
      "type": "message",
      "message": {
        "type": "text",
        "id": "14353798921116",
        "text": "Hello"
      },
      "timestamp": 1625665242211,
      "source": {
        "type": "user",
        "userId": "U80696558e1aa831..."
      },
      "replyToken": "757913772c4646b784d4b7ce46d12671",
      "mode": "active"
    }
  ]
}
```

#### 響應格式
```json
{
  "success": true,
  "message": "OK"
}
```

### 健康檢查
```http
GET /health
```

檢查服務運行狀態。

#### 響應格式
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "ai_model": "ok",
    "database": "ok",
    "memory": "ok"
  }
}
```

## 內部 API

### 對話管理

#### 創建會話
```http
POST /api/v1/sessions
Content-Type: application/json
```

請求體：
```json
{
  "user_id": "U80696558e1aa831...",
  "metadata": {
    "platform": "line",
    "language": "zh-TW"
  }
}
```

響應：
```json
{
  "session_id": "sess_123456789",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-01T01:00:00Z"
}
```

#### 發送消息
```http
POST /api/v1/sessions/{session_id}/messages
Content-Type: application/json
```

請求體：
```json
{
  "type": "text",
  "content": "你好",
  "metadata": {
    "importance": 0.8
  }
}
```

響應：
```json
{
  "success": true,
  "response": {
    "type": "text",
    "content": "你好！有什麼我可以幫你的嗎？",
    "model": "gemini",
    "tokens": 15
  }
}
```

### 系統管理

#### 獲取系統狀態
```http
GET /api/v1/system/status
```

響應：
```json
{
  "active_sessions": 10,
  "memory_usage": {
    "total": "1024MB",
    "used": "512MB"
  },
  "model_stats": {
    "total_requests": 1000,
    "success_rate": 0.98,
    "average_latency": 200
  }
}
```

## 錯誤處理

### 錯誤響應格式
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "錯誤描述",
    "details": {}
  }
}
```

### 常見錯誤碼
- `INVALID_REQUEST`: 請求格式錯誤
- `AUTH_FAILED`: 認證失敗
- `SESSION_EXPIRED`: 會話過期
- `MODEL_ERROR`: AI 模型錯誤
- `RATE_LIMITED`: 請求頻率超限
- `INTERNAL_ERROR`: 內部服務錯誤

## 安全性

- 所有 API 調用需要通過 HTTPS
- 外部 API 需要驗證簽名
- 內部 API 需要 API Key 認證
- 請求頻率限制：每分鐘 60 次

需補齊以下核心 API 才能進行 UI 開發：

```plaintext
用戶管理：
├── GET    /users          # 用戶列表 (需增加分頁)
├── PATCH  /users/{id}     # 用戶資料修改
└── POST   /users/{id}/role # 角色分配

知識庫：
├── POST   /knowledge/import    # 批量導入
├── DELETE /knowledge/batch     # 批量刪除
└── GET    /knowledge/versions  # 版本歷史

對話系統：
├── GET    /conversations/search # 對話搜索
└── DELETE /conversations/batch  # 批量刪除

系統管理：
├── GET    /system/analytics # 使用統計
└── GET    /system/health    # 健康檢查
``` 