# Quickstart Guide – Policy Gap Analyzer (Offline)

This guide walks you **step by step** from a fresh system to a **fully offline run** of the Policy Gap Analyzer using a **local LLM (Ollama)**.

---

## ✅ What You Will Achieve

- Local installation (no cloud APIs)
- Local LLM via Ollama
- Offline embeddings (SentenceTransformer)
- Fully offline policy gap analysis

---

## 🖥 System Requirements

- Ubuntu 20.04+ or WSL2
- Python 3.9 – 3.12
- 16 GB RAM recommended
- Internet access **only for initial setup**

---

## 1️⃣ System Preparation

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv build-essential poppler-utils git curl
```

---

## 2️⃣ Clone Repository

```bash
git clone https://github.com/neonerd-cpu/policy_gap_analyzer.git
cd policy_gap_analyzer
```

---

## 3️⃣ Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama --version
```

---

## 4️⃣ Download LLM Model (ONE TIME)

```bash
ollama pull llama3.2:3b
```

---

## 5️⃣ Start Ollama Server

```bash
ollama serve
```

---

## 6️⃣ Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## 7️⃣ Cache Embedding Model (CRITICAL)

```bash
python3 - <<'EOF'
from sentence_transformers import SentenceTransformer
SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("Embedding model cached")
EOF
```

After this step, **internet is no longer required**.

---

## 8️⃣ Prepare Input Files

```bash
mkdir -p tests reports
```

Example:
```
tests/
  └── org_policy.txt
```

---

## 9️⃣ Run Analyzer

```bash
python3 policy_gap_analyzer.py
```

---

## 🔐 Offline Verification

Disconnect internet and re-run:
```bash
python3 policy_gap_analyzer.py
```

If it runs → **Offline confirmed** ✅

---

## 🛠 Notes

- FAISS is **optional** and can be added for large reference sets
- DOCX support can be enabled with `python-docx`
- CPU usage near 100% is normal

---

## ✅ Done

You are now running a **fully offline, local LLM-powered policy gap analyzer**.
