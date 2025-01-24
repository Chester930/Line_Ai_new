# 開發指南

## 開發環境設置

1. 克隆項目
```bash
git clone <repository_url>
cd <project_directory>
```

2. 創建虛擬環境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安裝開發依賴
```bash
pip install -r requirements-dev.txt
```

## 代碼規範

### Python 風格指南
- 遵循 PEP 8
- 使用 4 空格縮進
- 最大行長度 88 字符
- 使用類型註解

### 文檔規範
- 所有公共方法必須有文檔字符串
- 使用 Google 風格的文檔格式
- 包含參數說明和返回值說明

### 測試規範
- 單元測試覆蓋率 > 80%
- 使用 pytest 框架
- 測試文件命名：`test_*.py`

## 開發流程

### 1. 添加新功能

#### 添加新的 AI 模型
1. 在 `src/shared/ai/models/` 創建新文件
```python
from ..base import BaseAIModel, ModelType, AIResponse

@AIModelFactory.register(ModelType.NEW_MODEL)
class NewModel(BaseAIModel):
    async def generate(self, prompt: str, **kwargs) -> AIResponse:
        # 實現生成方法
        pass
```

2. 更新模型類型
```python
class ModelType(str, Enum):
    NEW_MODEL = "new_model"
```

#### 添加新的消息處理器
1. 在 `src/shared/chat/handlers/` 創建新文件
```python
from .base import BaseMessageHandler

class NewHandler(BaseMessageHandler):
    async def handle(self, message: Message) -> Dict:
        # 實現處理邏輯
        pass
```

2. 註冊處理器
```python
handler_manager.register_handler("new_type", NewHandler())
```

### 2. 測試

#### 編寫測試
```python
import pytest

def test_new_feature():
    # 準備測試數據
    # 執行測試
    # 驗證結果
```

#### 運行測試
```bash
# 運行所有測試
pytest

# 運行特定測試
pytest tests/unit/path/to/test.py

# 生成覆蓋率報告
pytest --cov=src tests/
```

### 3. 提交代碼

```bash
# 檢查代碼格式
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# 提交更改
git add .
git commit -m "feat: add new feature"
git push
```

## 調試技巧

### 日誌調試
```python
from src.shared.utils.logger import logger

logger.debug("調試信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("錯誤信息")
```

### 使用 debugger
```python
import pdb; pdb.set_trace()
# 或使用 Python 3.7+ 的 breakpoint()
breakpoint()
```

## 性能優化

### 代碼優化
- 使用異步操作處理 I/O
- 實現緩存機制
- 優化數據結構

### 記憶體優化
- 及時清理不需要的對象
- 使用生成器處理大數據
- 控制並發數量

## 錯誤處理

### 異常處理範例
```python
try:
    await self.process_message(message)
except ValidationError as e:
    logger.warning(f"驗證錯誤: {e}")
    return {"error": str(e)}
except Exception as e:
    logger.error(f"處理錯誤: {e}")
    return {"error": "內部錯誤"}
```

## 版本發布

### 版本號規範
- 主版本號：不兼容的 API 修改
- 次版本號：向下兼容的功能性新增
- 修訂號：向下兼容的問題修正

### 發布檢查清單
- 所有測試通過
- 文檔更新
- CHANGELOG 更新
- 版本號更新 