import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

# 設置測試環境變數
os.environ['ENV'] = 'test'
os.environ['APP_NAME'] = 'LINE AI Assistant Test'
os.environ['DEBUG'] = 'true'
os.environ['LINE_CHANNEL_SECRET'] = 'test_secret'
os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'test_token'
os.environ['DATABASE_URL'] = 'sqlite:///test.db'
os.environ['GOOGLE_API_KEY'] = 'test_key'

# 加載測試環境變量
load_dotenv(".env.test")

# 導入需要的模組
from src.shared.database.base import Base, Database
from src.shared.config import Settings
from src.main import create_app
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.shared.database.models.user import User
from src.shared.database.models.conversation import Conversation
from typing import Generator
from fastapi.testclient import TestClient

# 添加專案根目錄到 Python 路徑
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

@pytest.fixture
def mock_gemini_model():
    """Mock Gemini 模型"""
    mock = Mock()
    mock.generate_response.return_value = "這是一個測試回應"
    return mock

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
def test_app():
    """創建測試用的 FastAPI 應用程式"""
    return create_app()

@pytest.fixture(scope="session")
def db_engine():
    # Use SQLite for testing
    engine = create_engine("sqlite:///test.db")
    Base.metadata.create_all(bind=engine)
    yield engine
    os.remove("./test.db")

@pytest.fixture(scope="session")
def test_db():
    """提供測試數據庫實例"""
    from src.shared.database.base import init_db
    db = init_db()
    return db

@pytest.fixture
def db_session(test_db):
    """提供測試數據庫會話"""
    session = next(test_db.get_session())
    try:
        yield session
    finally:
        session.rollback()
        session.close()

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
    config = Config()
    config.reload()  # 確保使用測試環境變量
    return config

@pytest.fixture(scope="session")
def test_line_client(test_config):
    """提供測試 LINE 客戶端"""
    from src.shared.line_sdk.client import LineClient
    return LineClient()

@pytest.fixture
def test_client(test_app):
    """創建測試用的 HTTP 客戶端"""
    return TestClient(test_app) 