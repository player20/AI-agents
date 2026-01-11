from setuptools import setup, find_packages

setup(
    name="multi-agent-cli",
    version="1.0.0",
    description="CLI for Multi-Agent Team Platform",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "multi-agent=multi_agent_cli:cli",
        ],
    },
    python_requires=">=3.8",
)
