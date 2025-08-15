#!/usr/bin/env python3
"""
AI Code Reviewer Package Setup
Distribueerbaar package voor de AI Code Review methodiek
"""

from setuptools import setup, find_packages
import os

# Read version from __init__.py
def read_version():
    with open(os.path.join("ai_code_reviewer", "__init__.py"), "r") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split('"')[1]
    return "0.1.0"

# Read long description from README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "AI Code Reviewer - Automated code review with AI integration"

setup(
    name="ai-code-reviewer",
    version=read_version(),
    author="Chris Lehnen",
    author_email="chris@example.com",
    description="Automated code review system with AI integration, BMAD Method support and universal post-edit hooks (v2.0.0)",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ChrisLehnen/ai-code-reviewer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "ruff>=0.1.5",
        "black>=23.1.0",
        "mypy>=1.0.0",
        "bandit[toml]>=1.7.5",
        "pytest>=7.4.0",
        "pre-commit>=3.5.0",
        "pyyaml>=6.0",
        "requests>=2.28.0",
        "click>=8.0.0",
    ],
    extras_require={
        "streamlit": ["streamlit>=1.28.0", "pandas>=2.0.0"],
        "dev": ["pytest>=7.4.0", "pytest-cov>=4.0.0", "flake8>=6.0.0"],
        "bmad": ["bmad-method>=1.0.0"],  # Als BMAD een package wordt
    },
    entry_points={
        "console_scripts": [
            "ai-code-review=ai_code_reviewer.cli:main",
            "ai-review=ai_code_reviewer.cli:main",
            "setup-ai-review=ai_code_reviewer.setup:setup_project",
        ],
    },
    include_package_data=True,
    package_data={
        "ai_code_reviewer": [
            "templates/*.yaml",
            "templates/*.md",
            "templates/.pre-commit-config.yaml",
            "bmad_integration/*",
            "configs/*.yaml",
        ],
    },
    zip_safe=False,
)