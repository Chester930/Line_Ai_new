# LINE AI Assistant (New Version)

基於 LINE Messaging API 的新一代 AI 助手系統，整合多個 AI 模型，提供智能對話與多媒體處理功能。

## 功能特點

- 多模型 AI 對話系統
  - OpenAI GPT
  - Google Gemini
  - Anthropic Claude
- 進階對話管理
  - 角色系統
  - 上下文管理
  - 多輪對話
- 多媒體處理
  - 圖片識別與生成
  - 文件處理
  - 語音轉文字
- 管理後台
  - 使用者管理
  - 對話記錄
  - 系統監控
- 開發工具
  - Studio 測試環境
  - 性能分析
  - 日誌追蹤

## 系統要求

- Python 3.8+
- PostgreSQL 13+
- Redis (選用，用於快取)

## 快速開始

1. 克隆專案
```bash
git clone https://github.com/your-username/LINE_AI_New.git
cd LINE_AI_New
```

2. 設置虛擬環境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. 安裝依賴
```bash
pip install -r requirements.txt
```

4. 環境設定
```bash
cp .env.example .env
# 編輯 .env 文件，填入必要的設定
```

5. 初始化數據庫
```bash
alembic upgrade head
```

6. 啟動服務
```bash
# 開發模式
uvicorn src.main:app --reload --port 8000

# 生產模式
uvicorn src.main:app --workers 4 --port 8000
```

## 專案結構

```
LINE_AI_New/
├── src/                # 源代碼
│   ├── apps/          # 應用程序
│   ├── core/          # 核心功能
│   ├── shared/        # 共享模組
│   │   ├── config/    # 配置管理
│   │   └── utils/     # 工具函數
│   └── interfaces/    # 介面定義
├── tests/             # 測試文件
├── docs/              # 文檔
└── config/            # 配置文件
```

## 開發指南

- 遵循 PEP 8 編碼規範
- 使用 Black 進行代碼格式化
- 撰寫單元測試
- 提交前運行測試套件

## 測試

運行測試：
```bash
pytest
```

檢查覆蓋率：
```bash
pytest --cov=src
```

## 文檔

詳細文檔請參考 `docs/` 目錄：
- [API 文檔](docs/api/README.md)
- [開發指南](docs/development/README.md)
- [部署指南](docs/deployment/README.md)

## 貢獻指南

1. Fork 專案
2. 創建特性分支
3. 提交變更
4. 發起 Pull Request

## 授權

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


