# Policy Gap Analyzer (Offline, Local LLM)

A fully **offline-capable policy gap analysis tool** that compares organizational policies against reference frameworks (CIS, MS-ISAC, NIST, etc.) using **local embeddings, semantic similarity, and a local LLM via Ollama**.

> ⚠️ **Note (Update)**  
> The current codebase runs **fully offline after initial setup**, but **FAISS and DOCX support are optional / roadmap features**.  
> Semantic similarity is currently computed directly using `SentenceTransformer + cosine similarity`.  
> FAISS integration can be added without changing the offline guarantees.

This project is designed for **security audits, compliance testing, and LLM evaluation** without relying on cloud APIs.

---

## 🚀 Key Features

- ✅ 100% **offline runtime** (after initial setup)
- ✅ Local **LLM inference via Ollama**
- ✅ **SentenceTransformer embeddings (offline cached)**
- ✅ Optional **FAISS-ready architecture**
- ✅ Supports **TXT / PDF / MD**  
- ⚠️ DOCX listed for compatibility with planned extensions
- ✅ Batch comparison of multiple policies
- ✅ Deterministic, testable gap detection
- ✅ Designed for **Intel CPU (no GPU required)**

---

## 🧠 Architecture Overview

```
Reference Policies ──┐
                     ├─▶ SentenceTransformer
Test Policies ───────┘          │
                                ▼
                      Semantic Similarity
                                │
                                ▼
                       Gap Candidates
                                │
                                ▼
                     Local LLM (Ollama)
                                │
                                ▼
                      Gap Report Files
```

> ℹ️ FAISS can be inserted between embeddings and similarity for large-scale corpora.

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
sudo apt install -y python3 python3-pip python3-venv build-essential poppler-utils git curl
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

### 3️⃣ Download LLM Model (ONE TIME)
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
pip install -r requirements.txt
```

---

## 🗂 Model & Cache Handling (Offline Guarantee)

> ⚠️ Important: **SentenceTransformer models must exist in local cache**  
> The code runs with:
```python
SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", local_files_only=True)
```

Run once with internet:
```bash
python3 - <<'EOF'
from sentence_transformers import SentenceTransformer
SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("Model cached")
EOF
```

After this → **no internet required**.

---

## ▶️ Running the Analyzer

```bash
python3 policy_gap_analyzer.py
```

Input folder:
```
tests/
```

Output folder:
```
reports/
```

---

## 🔐 Offline Guarantee

| Component | Offline |
|---------|---------|
| Python code | ✅ |
| SentenceTransformer | ✅ (cached) |
| Semantic similarity | ✅ |
| Ollama inference | ✅ |
| FAISS (if added) | ✅ |
| Internet APIs | ❌ |

---

## 📜 License
MIT
