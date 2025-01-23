from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.shared.config.config import config
from src.shared.database.base import db
from src.shared.utils.logger import logger
from src.apps.webhook.routes import router as webhook_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程序生命週期事件處理"""
    # 啟動時執行
    logger.info("應用程序啟動中...")
    try:
        # 初始化數據庫
        db.create_tables()
        logger.info("數據庫表創建成功")
        
        yield  # 應用程序運行
        
    finally:
        # 關閉時執行
        logger.info("應用程序關閉中...")

def create_app() -> FastAPI:
    """創建 FastAPI 應用程序"""
    app = FastAPI(
        title=config.settings.app_name,
        lifespan=lifespan
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 註冊路由
    app.include_router(webhook_router)
    
    return app

# 創建應用程序實例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.settings.app_host,
        port=config.settings.app_port,
        reload=config.settings.debug
    ) 