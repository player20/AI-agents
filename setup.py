from setuptools import setup, find_packages

setup(
    name="weaver-pro",
    version="1.0.0",
    description="Weaver Pro - Audit, Optimize, Build platforms",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        # Core CLI dependencies
        "click>=8.0.0",
        "pyyaml>=6.0",
        # HTTP and async
        "aiohttp>=3.8.0",
        "httpx>=0.24.0",
        # Data processing
        "faker>=18.0.0",
    ],
    extras_require={
        # Full audit mode (browser automation)
        "audit": [
            "playwright>=1.40.0",
        ],
        # AI/ML features
        "ai": [
            "anthropic>=0.18.0",
            "crewai>=0.28.0",
            "langgraph>=0.0.20",
        ],
        # Development
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ],
        # All features
        "all": [
            "playwright>=1.40.0",
            "anthropic>=0.18.0",
            "crewai>=0.28.0",
            "langgraph>=0.0.20",
            "dspy-ai>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "weaver=weaver_cli:main",
            "multi-agent=multi_agent_cli:cli",
        ],
    },
    python_requires=">=3.8",
)
