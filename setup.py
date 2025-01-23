from setuptools import setup, find_packages

setup(
    name="line_ai_new",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyYAML==6.0.1",
        "python-dotenv==1.0.0",
        "loguru==0.7.2",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="LINE AI New Project",
    python_requires=">=3.8",
)