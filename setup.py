from setuptools import setup, find_packages

setup(
    name="line-ai-assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn>=0.27.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "line-bot-sdk>=3.0.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "pytest>=8.0.0",
        "pytest-cov>=6.0.0",
        "pytest-asyncio>=0.23.0",
    ],
    python_requires=">=3.8",
)