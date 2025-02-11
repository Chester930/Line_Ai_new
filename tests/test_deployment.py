import pytest
import os
import docker
import requests
from time import sleep
from unittest.mock import patch
from src.shared.config.base import ConfigManager

class TestDeployment:
    @pytest.fixture
    def setup(self):
        """設置測試環境"""
        config = ConfigManager()
        config.set("DOCKER_IMAGE", "line-ai-bot:test")
        config.set("APP_PORT", "8000")
        return config
        
    def test_docker_build(self, setup):
        """測試 Docker 鏡像構建"""
        client = docker.from_client()
        
        # 構建測試鏡像
        image, logs = client.images.build(
            path=".",
            tag=setup.get("DOCKER_IMAGE"),
            dockerfile="deploy/Dockerfile"
        )
        
        # 驗證鏡像
        assert image.tags[0] == setup.get("DOCKER_IMAGE")
        
        # 檢查必要文件
        container = client.containers.create(image.id)
        assert container.exec_run("test -f /app/main.py").exit_code == 0
        assert container.exec_run("test -f /app/requirements.txt").exit_code == 0
        container.remove()
        
    @pytest.mark.asyncio
    async def test_service_health(self, setup):
        """測試服務健康狀態"""
        client = docker.from_client()
        
        # 啟動服務
        container = client.containers.run(
            setup.get("DOCKER_IMAGE"),
            detach=True,
            ports={f"{setup.get('APP_PORT')}/tcp": setup.get("APP_PORT")},
            environment={
                "GOOGLE_API_KEY": "test_api_key",
                "LINE_CHANNEL_SECRET": "test_secret",
                "LINE_CHANNEL_ACCESS_TOKEN": "test_token"
            }
        )
        
        try:
            # 等待服務啟動
            sleep(5)
            
            # 檢查健康狀態
            response = requests.get(f"http://localhost:{setup.get('APP_PORT')}/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            
            # 檢查服務日誌
            logs = container.logs().decode()
            assert "Application startup complete" in logs
            
        finally:
            container.stop()
            container.remove()
            
    def test_environment_validation(self, setup):
        """測試環境變量驗證"""
        required_vars = [
            "GOOGLE_API_KEY",
            "LINE_CHANNEL_SECRET",
            "LINE_CHANNEL_ACCESS_TOKEN",
            "DATABASE_URL"
        ]
        
        # 清除環境變量
        with patch.dict(os.environ, clear=True):
            # 逐個測試缺失變量
            for var in required_vars:
                env = {v: "test_value" for v in required_vars}
                del env[var]
                
                with patch.dict(os.environ, env, clear=True):
                    with pytest.raises(ValueError) as exc_info:
                        ConfigManager().validate_env()
                    assert var in str(exc_info.value)
                    
    @pytest.mark.asyncio
    async def test_database_migration(self, setup):
        """測試數據庫遷移"""
        from alembic.config import Config
        from alembic import command
        
        # 創建測試數據庫
        test_db_url = "sqlite:///test_migrations.db"
        
        # 運行遷移
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)
        
        try:
            # 執行遷移
            command.upgrade(alembic_cfg, "head")
            
            # 驗證表結構
            from sqlalchemy import create_engine, inspect
            engine = create_engine(test_db_url)
            inspector = inspect(engine)
            
            # 檢查必要的表
            assert "users" in inspector.get_table_names()
            assert "conversations" in inspector.get_table_names()
            assert "error_logs" in inspector.get_table_names()
            
            # 檢查表結構
            user_columns = {col["name"] for col in inspector.get_columns("users")}
            assert "id" in user_columns
            assert "line_id" in user_columns
            assert "created_at" in user_columns
            
        finally:
            # 清理測試數據庫
            if os.path.exists("test_migrations.db"):
                os.remove("test_migrations.db")
                
    def test_static_analysis(self, setup):
        """測試靜態代碼分析"""
        import pylint.lint
        import mypy.api
        
        # 運行 pylint
        pylint_output = pylint.lint.Run(
            ["src/"],
            do_exit=False
        )
        assert pylint_output.linter.stats.global_note >= 8.0  # 確保代碼質量分數
        
        # 運行 mypy
        mypy_result = mypy.api.run(["src/"])
        assert "Success" in mypy_result[0]  # 確保類型檢查通過 