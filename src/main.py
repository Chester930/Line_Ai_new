import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .line.router import router as line_router
from .shared.config import settings
from .shared.utils.logger import logger
from .shared.database.base import Database
from contextlib import asynccontextmanager

# 全局應用實例
_app = None
_db = None

async def get_application():
    """獲取應用實例"""
    global _app
    if _app is None:
        _app = await create_app()
    return _app

async def create_app():
    """創建應用實例"""
    app = FastAPI(title="LINE AI Assistant")
    
    # 初始化數據庫
    global _db
    _db = Database()
    await _db.initialize()
    app.db = _db
    
    # 添加 CORS 中間件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 註冊路由
    app.include_router(line_router, prefix="/line", tags=["LINE"])
    
    return app

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時執行
    logger.info("應用程序啟動中...")
    yield
    # 關閉時執行
    logger.info("應用程序關閉中...")
    if _db is not None:
        await _db.close()

# 創建應用實例
app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":
    # 載入配置
    app_config = settings.get_app_config()
    
    # 啟動服務器
    uvicorn.run(
        "main:app",
        host=app_config.get("host", "0.0.0.0"),
        port=app_config.get("port", 8000),
        reload=app_config.get("debug", False)
    ) 