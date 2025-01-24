import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .line.router import router as line_router
from .shared.config.manager import config_manager
from .shared.utils.logger import logger

def create_app() -> FastAPI:
    """創建 FastAPI 應用"""
    # 載入配置
    app_config = config_manager.get_app_config()
    
    # 創建應用
    app = FastAPI(
        title="AI Chat Bot",
        description="LINE AI 聊天機器人",
        version="1.0.0"
    )
    
    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_config.get("cors.origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 註冊路由
    app.include_router(
        line_router,
        prefix="/line",
        tags=["line"]
    )
    
    # 啟動事件
    @app.on_event("startup")
    async def startup():
        logger.info("應用程式啟動")
    
    # 關閉事件
    @app.on_event("shutdown")
    async def shutdown():
        logger.info("應用程式關閉")
    
    return app

app = create_app()

if __name__ == "__main__":
    # 載入配置
    app_config = config_manager.get_app_config()
    
    # 啟動服務器
    uvicorn.run(
        "main:app",
        host=app_config.get("host", "0.0.0.0"),
        port=app_config.get("port", 8000),
        reload=app_config.get("debug", False)
    ) 