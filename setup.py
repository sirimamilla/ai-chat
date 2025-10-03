"""Setup configuration for AI Chat."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-chat",
    version="0.1.0",
    author="AI Chat Team",
    description="Agentic AI chat with Vertex AI, PostgreSQL RAG, and MCP integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sirimamilla/ai-chat",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ai-chat=ai_chat.cli:cli",
        ],
    },
)
