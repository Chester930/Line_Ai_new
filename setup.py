from setuptools import setup, find_packages

setup(
    name="line_ai_new",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyYAML==6.0.1",
        "python-dotenv==1.0.0",
        "loguru==0.7.2",
        "fastapi>=0.109.0",  # 用於 Web API
        "uvicorn>=0.27.0",   # ASGI 服務器
        "sqlalchemy>=2.0.0",  # 數據庫 ORM
        "alembic>=1.13.0",   # 數據庫遷移
        "psycopg2-binary>=2.9.9",  # PostgreSQL 驅動
        "pydantic>=2.6.0",   # 數據驗證
    ],
    author="LINE AI Team",
    author_email="your.email@example.com",
    description="Next Generation LINE AI Assistant System",
    long_description=open("README.md", encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)