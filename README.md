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

## 測試策略

### 測試計劃

### 測試覆蓋率目標
- 當前: 42% ✅
- 第一階段: 50% ⏳ 
- 第二階段: 70% 🔜
- 第三階段: 80%+ 🔜

### 已完成測試
1. 核心功能測試
   - 配置系統 ✅
   - 事件系統 ✅
   - 數據庫操作 ✅
   - LINE SDK 整合 ✅
   - AI 模型 ✅

2. 性能測試
   - 響應時間 ✅
   - 並發處理 ✅
   - 記憶體使用 ✅
   - 數據庫性能 ✅

3. 穩定性測試
   - 長時間運行 ✅
   - 錯誤恢復 ✅
   - 連接穩定性 ✅
   - 資源釋放 ✅

4. 邊界情況測試
   - 空輸入處理 ✅
   - 大量輸入 ✅
   - 特殊字符 ✅
   - Unicode 支持 ✅
   - 速率限制 ✅

### 待完成測試
1. 整合測試
   - [ ] 完整對話流程
   - [ ] 多用戶並發
   - [ ] 系統恢復流程
   - [ ] 數據一致性

2. 負載測試
   - [ ] 高並發處理
   - [ ] 資源限制
   - [ ] 數據庫壓力
   - [ ] 網絡延遲

3. 自動化測試
   - [ ] CI/CD 整合
   - [ ] 測試報告生成
   - [ ] 性能指標監控
   - [ ] 錯誤追踪

### 執行指南
```bash
# 安裝依賴
pip install -r requirements.txt

# 運行所有測試
pytest tests/ -v

# 運行特定測試
pytest tests/test_events.py -v
pytest tests/test_database.py -v
pytest tests/test_line_sdk.py -v

# 生成覆蓋率報告
pytest --cov=src tests/
```

### 測試報告
- 測試總數: 45
- 通過率: 100%
- 覆蓋率: 42%
- 平均響應時間: < 500ms
- 錯誤率: < 1%

### 下一步計劃
1. 提高測試覆蓋率
   - 補充缺失的單元測試
   - 添加更多整合測試
   - 實現端到端測試

2. 性能優化
   - 優化數據庫查詢
   - 改進並發處理
   - 減少資源使用

3. 監控改進
   - 添加性能指標
   - 完善錯誤日誌
   - 實現自動報警

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

# LINE AI Assistant

一個基於 LINE Messaging API 的 AI 助手，具有數據庫整合功能。

## 開發環境設置

1. 安裝依賴：
```bash
pip install -r requirements.txt
```

2. 設置環境變數：
```bash
# .env
DATABASE_URL=sqlite+aiosqlite:///:memory:  # 開發環境使用
LINE_CHANNEL_SECRET=your_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_access_token
```

## 測試

### 運行測試
```bash
# 運行所有測試
pytest

# 運行特定測試文件
pytest tests/test_database.py

# 查看測試覆蓋率報告
pytest --cov=src tests/
```

### 測試覆蓋率目標

目前項目的測試覆蓋率目標：

- 整體覆蓋率：50%
- 核心模組覆蓋率：
  - database: 80%
  - line_sdk: 70%
  - events: 70%
  - config: 60%

### 提高測試覆蓋率的策略

1. 優先測試核心功能：
   - 數據庫操作
   - LINE 消息處理
   - 事件系統
   - 配置管理

2. 下一步計劃：
   - 添加 LINE SDK 的單元測試
   - 完善配置系統的測試
   - 添加事件系統的整合測試
   - 實現 utils 模組的測試

3. 測試類型：
   - 單元測試：測試獨立組件
   - 整合測試：測試組件間的交互
   - 功能測試：測試完整功能流程

## 項目結構

```
src/
├── line/           # LINE 相關功能
├── shared/         # 共享組件
│   ├── database/   # 數據庫模組
│   ├── events/     # 事件系統
│   ├── config/     # 配置管理
│   └── utils/      # 工具函數
└── main.py         # 主程序入口

tests/              # 測試目錄
├── test_database.py
├── test_line.py
└── test_events.py
```

## 貢獻指南

1. Fork 本項目
2. 創建功能分支
3. 提交更改
4. 創建 Pull Request

## 許可證

MIT License


