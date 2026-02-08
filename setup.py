
---

# ⚙️ `setup.py`

```python
from setuptools import setup, find_packages

setup(
    name="policy-gap-analyzer",
    version="1.0.0",
    description="Offline Policy Gap Analyzer using FAISS, SentenceTransformers, and local LLM via Ollama",
    author="neonerd-cpu",
    license="MIT",
    python_requires=">=3.9",
    packages=find_packages(exclude=("tests",)),
    install_requires=[
        "sentence-transformers>=2.2.2",
        "faiss-cpu>=1.7.4",
        "numpy>=1.23",
        "scikit-learn>=1.2",
        "tqdm>=4.65",
        "nltk>=3.8",
        "requests>=2.31",
        "pdfplumber>=0.10",
        "python-docx>=1.1.0",
        "torch>=2.0.0",
        "transformers>=4.36.0",
    ],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "policy-gap-analyzer=policy_gap_analyzer:main"
        ]
    },
)
