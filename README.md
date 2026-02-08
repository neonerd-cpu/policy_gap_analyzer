# Policy Gap Analyzer (Offline, Local LLM)

A fully **offline-capable policy gap analysis tool** that compares organizational policies against reference frameworks (CIS, MS-ISAC, NIST, etc.) using **local embeddings, FAISS similarity search, and a local LLM via Ollama**.

This project is designed for **security audits, compliance testing, and LLM evaluation** without relying on cloud APIs.

---

## 🚀 Key Features

- ✅ 100% **offline runtime** (after initial setup)
- ✅ Local **LLM inference via Ollama**
- ✅ **SentenceTransformer embeddings**
- ✅ **FAISS** for fast semantic similarity search
- ✅ Supports **TXT / DOCX / PDF**
- ✅ Batch comparison of multiple policies
- ✅ Deterministic, testable gap detection
- ✅ Designed for **Intel CPU (no GPU required)**

---

## 🧠 Architecture Overview

```
Reference Policies ──┐
                     ├─▶ SentenceTransformer ─▶ FAISS Index
Test Policies ───────┘                               │
                                                     ▼
                                           Gap Candidates
                                                     │
                                                     ▼
                                           Local LLM (Ollama)
                                                     │
                                                     ▼
                                            Gap Report Files
```

---

## 📦 Requirements

### System
- Ubuntu 20.04+ / WSL2
- Python **3.9 – 3.12**
- 16 GB RAM recommended
- Intel CPU supported (no CUDA needed)

---

## 🔧 One-Time Online Setup (Required)

### 1️⃣ System packages
```bash
sudo apt update
sudo apt install -y   python3 python3-pip python3-venv   build-essential   poppler-utils   git curl
```

---

### 2️⃣ Install Ollama (Local LLM Runtime)
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify:
```bash
ollama --version
```

---

### 3️⃣ Download LLM Model (DO THIS ONCE)
```bash
ollama pull llama3.2:3b
```

---

### 4️⃣ Start Ollama Server
```bash
ollama serve
```

---

## 🐍 Python Environment Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --break-system-packages
```

---

## 🗂 Data & Model Caching

```bash
export TRANSFORMERS_CACHE=$PWD/cache/transformers
export HF_HOME=$PWD/cache/huggingface
export FAISS_CACHE_PATH=$PWD/cache/faiss
export OLLAMA_MODELS=$HOME/.ollama/models
```

---

## ▶️ Running the Analyzer

```bash
python3 policy_gap_analyzer.py   --reference_folder ./refs   --test_folder ./tests   --output ./reports
```

---

## ⏱ Performance (Intel i5, 16GB RAM)

- Embeddings: 2–4 minutes
- FAISS indexing: < 30 seconds
- LLM analysis: 3–8 minutes

---

## 🔐 Offline Guarantee

| Component | Offline |
|---------|---------|
| Python code | ✅ |
| FAISS | ✅ |
| SentenceTransformer | ✅ |
| Ollama inference | ✅ |
| Internet APIs | ❌ |

---

