import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .line.router import router as line_router
from .shared.config import settings
from .shared.utils.logger import logger
from .shared.database.base import init_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時執行
    logger.info("應用程序啟動中...")
    # 在這裡添加其他啟動時需要的初始化代碼
    init_db()
    yield
    # 關閉時執行
    logger.info("應用程序關閉中...")
    # 在這裡添加清理代碼

def create_app() -> FastAPI:
    """創建 FastAPI 應用程式"""
    app_config = settings.get_app_config()
    
    app = FastAPI(
        title="LINE AI Assistant",
        description="智能對話系統 API",
        version="1.0.1",
        lifespan=lifespan
    )
    
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

# 創建應用程式實例
app = create_app()

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