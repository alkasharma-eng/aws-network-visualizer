"""
AWS Network Visualizer - Setup configuration.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="aws-network-visualizer",
    version="1.0.0",
    description="Production-grade AWS network topology discovery and analysis platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Organization",
    author_email="your-email@example.com",
    url="https://github.com/your-org/aws-network-visualizer",
    packages=find_packages(include=["src", "src.*"]),
    python_requires=">=3.10",
    install_requires=[
        "boto3>=1.34.0,<2.0.0",
        "botocore>=1.34.0,<2.0.0",
        "pydantic>=2.5.0,<3.0.0",
        "pydantic-settings>=2.1.0,<3.0.0",
        "python-dotenv>=1.0.0,<2.0.0",
        "python-json-logger>=2.0.7,<3.0.0",
        "watchtower>=3.0.1,<4.0.0",
        "aws-xray-sdk>=2.12.0,<3.0.0",
        "tenacity>=8.2.3,<9.0.0",
        "networkx>=3.2.1,<4.0.0",
        "matplotlib>=3.8.2,<4.0.0",
        "plotly>=5.18.0,<6.0.0",
        "pillow>=10.1.0,<11.0.0",
        "aioboto3>=12.3.0,<13.0.0",
        "aiohttp>=3.9.1,<4.0.0",
        "fastapi>=0.109.0,<1.0.0",
        "mangum>=0.17.0,<1.0.0",
        "redis>=5.0.1,<6.0.0",
        "orjson>=3.9.10,<4.0.0",
        "click>=8.1.7,<9.0.0",
        "rich>=13.7.0,<14.0.0",
        "tqdm>=4.66.1,<5.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3,<8.0.0",
            "pytest-asyncio>=0.23.2,<1.0.0",
            "pytest-cov>=4.1.0,<5.0.0",
            "pytest-mock>=3.12.0,<4.0.0",
            "moto>=4.2.11,<5.0.0",
            "black>=23.12.1,<24.0.0",
            "flake8>=7.0.0,<8.0.0",
            "mypy>=1.8.0,<2.0.0",
            "pylint>=3.0.3,<4.0.0",
            "isort>=5.13.2,<6.0.0",
            "boto3-stubs[essential]>=1.34.0,<2.0.0",
            "types-requests>=2.31.0,<3.0.0",
            "ipython>=8.19.0,<9.0.0",
            "ipdb>=0.13.13,<1.0.0",
        ],
        "docs": [
            "mkdocs>=1.5.3,<2.0.0",
            "mkdocs-material>=9.5.3,<10.0.0",
            "mkdocstrings[python]>=0.24.0,<1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aws-network-visualizer=src.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="aws network vpc topology visualization security analysis bedrock",
    project_urls={
        "Bug Reports": "https://github.com/your-org/aws-network-visualizer/issues",
        "Documentation": "https://github.com/your-org/aws-network-visualizer/docs",
        "Source": "https://github.com/your-org/aws-network-visualizer",
    },
)
