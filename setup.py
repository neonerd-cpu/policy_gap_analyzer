"""
Setup configuration for Policy Gap Analyzer
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="policy-gap-analyzer",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Local LLM-powered policy gap analysis tool with NIST CSF framework support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/neonerd-cpu/policy_gap_analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "policy-gap-analyzer=policy_gap_analyzer:main",
        ],
    },
    include_package_data=True,
    keywords="policy analysis cybersecurity nist framework gap-analysis llm ollama",
    project_urls={
        "Bug Reports": "https://github.com/neonerd-cpu/policy_gap_analyzer/issues",
        "Source": "https://github.com/neonerd-cpu/policy_gap_analyzer",
    },
)
