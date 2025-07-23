#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="edgecommit",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer[all]>=0.9.0",
        "openai>=1.12.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "rich>=13.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "ruff>=0.2.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "edgecommit=cli:app",
        ],
    },
    python_requires=">=3.11",
)