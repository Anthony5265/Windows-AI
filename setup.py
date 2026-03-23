#!/usr/bin/env python3
"""
Setup configuration for Windows AI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements from file, filtering out comment lines and -r include lines
def read_requirements(filename):
    """Read requirements from file"""
    req_path = this_directory / filename
    if req_path.exists():
        with open(req_path) as f:
            return [
                line.strip() for line in f
                if line.strip()
                and not line.startswith('#')
                and not line.startswith('-r ')
                and not line.startswith('--')
            ]
    return []

# Core requirements
install_requires = read_requirements('requirements.txt')

setup(
    name="windows-ai",
    version="2.0.0a1",
    author="Windows AI Team",
    author_email="windows-ai@example.com",
    description="AI Integration Platform for Windows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Anthony5265/Windows-AI",
    project_urls={
        "Bug Tracker": "https://github.com/Anthony5265/Windows-AI/issues",
        "Documentation": "https://github.com/Anthony5265/Windows-AI/tree/main/docs",
        "Source Code": "https://github.com/Anthony5265/Windows-AI",
    },
    packages=find_packages(include=['windows_ai', 'windows_ai.*']),
    include_package_data=True,
    package_data={
        'windows_ai': [
            'plugins/**/*.py',
            'config/**/*.yaml',
            'config/**/*.json',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.10",
    install_requires=install_requires,
    extras_require={
        'dev': read_requirements('requirements-dev.txt'),
    },
    entry_points={
        'console_scripts': [
            'windows-ai=windows_ai.__main__:main',
        ],
    },
    keywords='ai windows automation plugins integration',
    zip_safe=False,
)
