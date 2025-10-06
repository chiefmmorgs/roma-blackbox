"""Setup script for roma-blackbox package"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="roma-blackbox",
    version="0.3.2",
    author="Your Name",
    author_email="your.email@example.com",
    description="Privacy-first monitoring wrapper for ROMA agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/roma-blackbox",
    packages=find_packages(exclude=["tests", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=["pydantic>=2.0.0"],
    extras_require={
        "postgresql": ["asyncpg>=0.29.0"],
        "prometheus": ["prometheus-client>=0.19.0"],
        "all": ["asyncpg>=0.29.0", "prometheus-client>=0.19.0", "cryptography>=41.0.0"],
        "dev": ["pytest>=7.4.0", "pytest-asyncio>=0.21.0", "black>=23.0.0", "ruff>=0.1.0"],
    },
)
