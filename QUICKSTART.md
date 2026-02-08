# Quickstart Guide – Policy Gap Analyzer (Offline)

This guide walks you **step by step** from a fresh system to a **fully offline run** of the Policy Gap Analyzer using a **local LLM (Ollama)**.

Follow the steps **in order**.

---

## ✅ What You Will Achieve

- Local installation (no cloud APIs)
- Local LLM via Ollama
- Offline embeddings + FAISS
- Successful policy gap analysis run

---

## 🖥 System Requirements

- Ubuntu 20.04+ or WSL2 (Windows 10/11)
- Python 3.9 – 3.11
- 16 GB RAM recommended
- Internet access **only for initial setup**

---

## 1️⃣ System Preparation

Update system packages:

```bash
sudo apt update && sudo apt upgrade -y
```

Install required system dependencies:

```bash
sudo apt install -y \
  python3 python3-pip python3-venv \
  build-essential \
  poppler-utils \
  git curl
```

Verify Python:

```bash
python3 --version
```

---

## 2️⃣ Clone the Repository

```bash
git clone https://github.com/neonerd-cpu/policy_gap_analyzer.git
cd policy_gap_analyzer
```

---

## 3️⃣ Install Ollama (Local LLM Runtime)

Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify installation:

```bash
ollama --version
```

---

## 4️⃣ Download the LLM Model (ONE TIME)

Download the local model:

```bash
ollama pull llama3.2:3b
```

⚠️ This step **requires internet**, but only once.

---

## 5️⃣ Start Ollama Server

```bash
ollama serve
```

Leave this running in a terminal.

If port is already in use:

```bash
pkill ollama
ollama serve
```

---

## 6️⃣ Python Virtual Environment (Recommended)

Create virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Upgrade pip tools:

```bash
pip install --upgrade pip setuptools wheel
```

---

## 7️⃣ Install Python Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

If NOT using a virtual environment:

```bash
pip install -r requirements.txt --break-system-packages
```

---

## 8️⃣ Download NLTK Data (ONE TIME)

```bash
python3 -c "import nltk; nltk.download('punkt')"
```

After this, NLTK works offline.

---

## 9️⃣ Configure Offline Caching (Recommended)

```bash
mkdir -p cache/{transformers,huggingface,faiss}
```

Export environment variables:

```bash
export TRANSFORMERS_CACHE=$PWD/cache/transformers
export HF_HOME=$PWD/cache/huggingface
export FAISS_CACHE_PATH=$PWD/cache/faiss
export OLLAMA_MODELS=$HOME/.ollama/models
```

(Optional) Persist them:

```bash
echo 'export TRANSFORMERS_CACHE=$PWD/cache/transformers' >> ~/.bashrc
echo 'export HF_HOME=$PWD/cache/huggingface' >> ~/.bashrc
echo 'export FAISS_CACHE_PATH=$PWD/cache/faiss' >> ~/.bashrc
echo 'export OLLAMA_MODELS=$HOME/.ollama/models' >> ~/.bashrc
```

---

## 🔟 Prepare Input Files

Create folders:

```bash
mkdir -p refs tests reports
```

Example files:

```text
refs/
  ├── cis.txt
  ├── nist.docx
  └── ms_isac.pdf

tests/
  └── org_policy.txt
```

---

## 1️⃣1️⃣ Run the Policy Gap Analyzer

Basic run:

```bash
python3 policy_gap_analyzer.py \
  --reference_folder ./refs \
  --test_folder ./tests \
  --output ./reports
```

---

## 1️⃣2️⃣ Verify Output

Expected output files:

```text
reports/
  ├── policy_name/
  │   ├── gap_analysis.txt
  │   └── revised_policy.txt
```

If these exist, the run was successful ✅

---

## ⏱ Expected Runtime (Intel i5, 16GB RAM)

| Stage | Time |
|-----|------|
| Embeddings | 2–4 min |
| FAISS Index | < 30 sec |
| LLM Analysis | 3–8 min |
| Total | 5–12 min |

---

## 🔐 Offline Verification

Disconnect internet and rerun:

```bash
python3 policy_gap_analyzer.py --reference_folder refs --test_folder tests --output outputs
```

If it runs → **Fully offline confirmed** ✅

---

## 🛠 Common Issues

### Ollama port in use
```bash
pkill ollama
ollama serve
```

### NLTK error
```bash
python3 -c "import nltk; nltk.download('punkt')"
```

### Slow performance
- Ensure Ollama is running
- CPU usage near 100% is normal
- First run is always slower (model warm-up)

---

## ✅ You Are Done

Your system is now running a **fully offline, local-LLM-powered policy gap analyzer**.

---

## 📜 License
MIT
