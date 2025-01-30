# AI 聊天機器人

基於 LINE Messaging API 的智能對話系統。

## 當前功能

### 已實現
- AI 模型整合
  - Gemini 模型支持
  - 模型工廠模式
  - 統一的錯誤處理
- 提示詞系統
  - 模板化管理
  - 多角色支持（助手、專家）
  - 動態提示詞生成
- 對話管理
  - 會話狀態追踪
  - 上下文維護
  - 記憶管理
- 消息處理
  - 文本消息支持
  - 圖片分析能力
  - 格式驗證

### 開發中
- 多模型支持
  - GPT 模型整合
  - Claude 模型整合
- 增強的對話能力
  - 情感分析
  - 意圖識別
  - 多輪對話優化
- 知識庫整合
  - 外部知識導入
  - 動態學習能力

### 規劃中
- 進階功能
  - 多語言支持
  - 語音識別
  - 自定義角色
  - 群組對話支持
- 系統優化
  - 分布式部署
  - 性能監控
  - 數據分析

## 快速開始

1. 環境準備

```bash
# 複製環境變量模板
cp .env.example .env

# 編輯環境變量
vim .env

# 安裝依賴
pip install -r requirements.txt
```

2. 啟動服務

```bash
# 開發環境
uvicorn src.main:app --reload

# 生產環境
docker-compose -f deploy/docker-compose.yml up -d
```

## 項目結構

```
src/
├── shared/          # 共享模組
│   ├── ai/          # AI 模型相關
│   │   ├── base.py          # 模型基礎類
│   │   ├── factory.py       # 模型工廠
│   │   ├── models/          # 具體模型實現
│   │   └── prompts/         # 提示詞系統
│   ├── chat/        # 對話管理
│   │   ├── session.py       # 會話管理
│   │   ├── context.py       # 上下文管理
│   │   ├── memory.py        # 記憶系統
│   │   └── handlers/        # 消息處理器
│   └── utils/       # 工具函數
│       ├── logger.py        # 日誌工具
│       └── config.py        # 配置管理
├── line/            # LINE Bot 相關
└── main.py          # 主程序

tests/               # 測試文件
├── unit/           # 單元測試
└── integration/    # 集成測試

deploy/              # 部署配置
docs/                # 文檔
```

## 開發指南

### 添加新模型
1. 在 `src/shared/ai/models/` 創建新模型類
2. 實現 `BaseAIModel` 接口
3. 在 `ModelType` 中添加新類型
4. 使用 `@AIModelFactory.register` 註冊

### 添加新角色
1. 在 `src/shared/ai/prompts/roles/` 創建新角色類
2. 繼承 `BasePrompt`
3. 實現 `build` 方法
4. 定義角色特定的提示詞模板

### 添加新處理器
1. 在 `src/shared/chat/handlers/` 創建新處理器
2. 繼承 `BaseMessageHandler`
3. 實現必要的方法
4. 在 `MessageHandlerManager` 中註冊

## 測試

```bash
# 運行所有測試
pytest

# 運行特定測試
pytest tests/unit/ai/
pytest tests/unit/chat/
```

## 文檔

- [API 文檔](docs/api.md)
- [部署指南](docs/deployment.md)
- [開發指南](docs/development.md)

## 授權協議

MIT License

## 虛擬環境設置

本專案使用 Python 虛擬環境來管理依賴，請按照以下步驟設置：

### Windows 環境：
```bash
# 建立虛擬環境
python -m venv venv


# 啟動虛擬環境
venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 安裝開發依賴（可選）
pip install pytest pytest-cov
```

### Linux/Mac 環境：
```bash
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 安裝開發依賴（可選）
pip install pytest pytest-cov
```

### 退出虛擬環境
```bash
deactivate
```

注意：
- 所有的開發和測試都應在虛擬環境中進行
- 每次開啟新的終端機都需要重新啟動虛擬環境
- 安裝新的依賴後，請更新 requirements.txt：
  ```bash
  pip freeze > requirements.txt
  ```

## API 密鑰需求

本系統支援多個 AI 模型，需要以下 API 密鑰：

1. Google Gemini API
   - 獲取地址：https://makersuite.google.com/app/apikey
   - 環境變量：GOOGLE_API_KEY

2. OpenAI API（待實現）
   - 獲取地址：https://platform.openai.com/api-keys
   - 環境變量：OPENAI_API_KEY
   - 所需權限：GPT-4 訪問權限

3. Anthropic Claude API（待實現）
   - 獲取地址：https://console.anthropic.com/
   - 環境變量：ANTHROPIC_API_KEY
   - 所需模型：Claude 3

注意：目前系統已完成 Gemini 模型整合，OpenAI 和 Claude 模型將在取得 API 密鑰後進行測試和調整。


