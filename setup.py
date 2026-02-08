from setuptools import setup, find_packages

setup(
    name="policy-gap-analyzer",
    version="1.0.0",
    description="Offline LLM-powered policy gap analysis using NIST CSF and Ollama",
    author="neonerd-cpu",
    packages=find_packages(exclude=["tests", "reports"]),
    install_requires=[
        "numpy",
        "scikit-learn",
        "sentence-transformers",
        "torch",
        "transformers",
        "PyPDF2",
        "ollama",
        "faiss-cpu",
        "nltk"
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "policy-gap-analyzer=policy_gap_analyzer:main"
        ]
    },
)
