import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.shared.database.base import Base, Database
from src.main import create_app
from src.shared.config.config import Config
from src.shared.database.models.user import User
from src.shared.database.models.conversation import Conversation
from typing import Generator
from fastapi.testclient import TestClient

# 添加專案根目錄到 Python 路徑
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# 設置測試環境變數
os.environ['ENV'] = 'test'
os.environ['APP_NAME'] = 'LINE AI Assistant Test'
os.environ['DEBUG'] = 'true'
os.environ['LINE_CHANNEL_SECRET'] = 'test_secret'
os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'test_token'
os.environ['DATABASE_URL'] = 'sqlite:///test.db'
os.environ['GOOGLE_API_KEY'] = 'test_key'

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
    """配置測試環境"""
    os.environ['ENV'] = 'test'
    os.environ['APP_NAME'] = 'LINE AI Assistant Test'
    os.environ['DEBUG'] = 'true'
    os.environ['LINE_CHANNEL_SECRET'] = 'test_secret'
    os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'test_token'

@pytest.fixture(scope="session")
def test_app():
    """創建測試用的 FastAPI 應用程序"""
    return create_app()

@pytest.fixture(scope="session")
def db_engine():
    # Use SQLite for testing
    engine = create_engine("sqlite:///test.db")
    Base.metadata.create_all(bind=engine)
    yield engine
    os.remove("./test.db")

@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """設置測試環境"""
    # 保存原始環境變量
    original_env = {
        'LINE_CHANNEL_SECRET': os.getenv('LINE_CHANNEL_SECRET'),
        'LINE_CHANNEL_ACCESS_TOKEN': os.getenv('LINE_CHANNEL_ACCESS_TOKEN'),
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY')
    }
    
    # 設置測試環境變量
    os.environ['LINE_CHANNEL_SECRET'] = 'test_secret'
    os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'test_token'
    os.environ['DATABASE_URL'] = 'sqlite:///test.db'
    os.environ['GOOGLE_API_KEY'] = 'test_key'
    
    # 重新加載配置
    config = Config()
    config.reload()
    
    yield
    
    # 恢復原始環境變量
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    
    # 重新加載配置
    config.reload()

@pytest.fixture
def test_config():
    """配置測試夾具"""
    config = Config()
    config.reload()  # 確保使用測試環境變量
    return config

@pytest.fixture(scope="session")
def test_db(test_config):
    """提供測試數據庫實例"""
    database = Database(test_config.settings)
    database.init_db()
    return database

@pytest.fixture(scope="session")
def test_line_client(test_config):
    """提供測試 LINE 客戶端"""
    from src.shared.line_sdk.client import LineClient
    return LineClient()

@pytest.fixture
def test_client(test_app):
    """創建測試用的 HTTP 客戶端"""
    return TestClient(test_app) 