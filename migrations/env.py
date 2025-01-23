import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from pathlib import Path

from src.shared.database import Base
from src.shared.config.config import config as app_config

# 獲取 alembic.ini 的配置
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    """獲取數據庫 URL"""
    url = app_config.get('database.url', 'sqlite:///data/app.db')
    
    # 確保 SQLite 數據庫目錄存在
    if url.startswith('sqlite:///'):
        db_path = Path(url.replace('sqlite:///', ''))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    return url

def run_migrations_offline():
    """離線運行遷移"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """在線運行遷移"""
    # 配置數據庫連接
    configuration = {
        'sqlalchemy.url': get_url()
    }
    
    # 如果是 SQLite，添加特殊配置
    if configuration['sqlalchemy.url'].startswith('sqlite'):
        configuration['sqlalchemy.connect_args'] = {'check_same_thread': False}
    
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 