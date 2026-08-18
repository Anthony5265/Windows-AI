#!/usr/bin/env python3
"""Packaging configuration for Windows-AI."""

from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent


def read_requirements(filename: str) -> list[str]:
    """Read install requirements while ignoring comments and include directives."""
    path = ROOT / filename
    if not path.exists():
        return []

    requirements: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(("-r ", "--")):
            continue
        requirements.append(line)
    return requirements


setup(
    name="windows-ai",
    version="2.0.0a1",
    description="Windows-first AI platform for models, agents, tools, automation, and Windows integration",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/Anthony5265/Windows-AI",
    project_urls={
        "Bug Tracker": "https://github.com/Anthony5265/Windows-AI/issues",
        "Documentation": "https://github.com/Anthony5265/Windows-AI/tree/main/docs",
        "Source Code": "https://github.com/Anthony5265/Windows-AI",
    },
    packages=find_packages(include=["windows_ai", "windows_ai.*"]),
    include_package_data=True,
    package_data={
        "windows_ai": [
            "plugins/**/*.py",
            "config/**/*.yaml",
            "config/**/*.json",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements("requirements.txt"),
    extras_require={"dev": read_requirements("requirements-dev.txt")},
    entry_points={"console_scripts": ["windows-ai=windows_ai.__main__:main"]},
    keywords=["ai", "windows", "agents", "automation", "plugins", "mcp"],
    zip_safe=False,
)
