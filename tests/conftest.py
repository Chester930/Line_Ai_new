import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv
from unittest.mock import Mock, AsyncMock, patch

# 設置測試環境變數
os.environ['ENV'] = 'test'
os.environ['APP_NAME'] = 'LINE AI Assistant Test'
os.environ['DEBUG'] = 'true'
os.environ['LINE_CHANNEL_SECRET'] = 'test_secret'
os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'test_token'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['GOOGLE_API_KEY'] = 'test_key'

# 加載測試環境變量
load_dotenv(".env.test")

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 導入需要的模組
from src.shared.database.base import Database, Base
from src.main import create_app
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.shared.database.models.user import User
from src.shared.database.models.conversation import Conversation
from typing import Generator
from fastapi.testclient import TestClient
from src.shared.ai.models.gemini import GeminiModel
from src.shared.ai.base import ModelResponse

@pytest.fixture
async def mock_gemini_model():
    """Mock Gemini 模型"""
    with patch('google.generativeai.GenerativeModel') as mock_genai:
        model = GeminiModel(api_key="test_key")
        
        # Mock 基本方法
        model.generate = AsyncMock()
        model.generate_stream = AsyncMock()
        model.analyze_image = AsyncMock()
        model.count_tokens = AsyncMock()
        
        # Mock 響應
        mock_response = ModelResponse(
            text="Test response",
            usage={"total_tokens": 10},
            model_info={"model": "test"},
            raw_response={}
        )
        model.generate.return_value = mock_response
        model.chat_with_context = AsyncMock(return_value=mock_response)
        
        # Mock 流式生成
        async def mock_stream():
            yield mock_response
        model.generate_stream.return_value = mock_stream()
        
        # Mock 圖片分析
        model.analyze_image.return_value = mock_response
        
        # Mock token 計算
        model.count_tokens.return_value = 10
        
        yield model

@pytest.fixture
def mock_session():
    """Mock 聊天會話"""
    mock = Mock()
    mock.send_message.return_value = "測試回應"
    return mock 

def pytest_configure(config):
    """
    在測試開始前加載環境變數
    """
    load_dotenv()

@pytest.fixture(scope="session")
def test_env():
    """
    提供測試環境配置
    """
    return {
        "LINE_CHANNEL_SECRET": os.getenv("LINE_CHANNEL_SECRET"),
        "LINE_CHANNEL_ACCESS_TOKEN": os.getenv("LINE_CHANNEL_ACCESS_TOKEN"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY")
    }

@pytest.fixture(scope="session")
async def test_app():
    """創建測試用的 FastAPI 應用程式"""
    app = await create_app()
    return app

@pytest.fixture(scope="session")
async def test_db():
    """提供測試數據庫"""
    db = Database()
    await db.initialize()
    yield db
    await db.close()

@pytest.fixture
async def test_session(test_db):
    """提供測試會話"""
    async with test_db.async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """設置測試環境"""
    # 加載測試環境變數
    load_dotenv(".env.test")
    
    # 設置必要的測試環境變數
    os.environ.update({
        'LINE_CHANNEL_SECRET': 'test_secret',
        'LINE_CHANNEL_ACCESS_TOKEN': 'test_token',
        'GOOGLE_API_KEY': 'test_key',
        'ENV': 'test',
        'DEBUG': 'false'
    })
    
    yield
    
    # 測試結束後清理環境變數
    for key in ['LINE_CHANNEL_SECRET', 'LINE_CHANNEL_ACCESS_TOKEN', 
               'GOOGLE_API_KEY', 'ENV', 'DEBUG']:
        os.environ.pop(key, None)

@pytest.fixture
def test_config():
    """配置測試夾具"""
    return {
        "models": {
            "gemini": {
                "api_key": "test_key",
                "name": "gemini",
                "model_name": "gemini-pro",
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40
            }
        },
        "max_context_length": 2000,
        "memory_ttl": 3600,
        "enable_state_tracking": True,
        "plugins": {
            "web_search": {
                "enabled": True,
                "version": "1.0",
                "settings": {}
            },
            "image_analyzer": {
                "enabled": True,
                "version": "1.0",
                "settings": {}
            }
        }
    }

@pytest.fixture(scope="session")
def test_line_client():
    """提供測試 LINE 客戶端"""
    from src.shared.line_sdk.client import LineClient
    return LineClient()

@pytest.fixture
def test_client(test_app):
    """Provide test client"""
    # TODO: Setup test client
    yield client
    # TODO: Cleanup test client

@pytest.fixture
def test_client():
    """Provide test client"""
    # TODO: Setup test client
    yield client
    # TODO: Cleanup test client 