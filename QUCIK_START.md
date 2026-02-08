# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies (First Time Only)

```bash
# Run the automated setup
python setup.py
```

**What this does:**
- Installs Python packages
- Downloads NLTK data (~3MB)
- Downloads SentenceTransformer model (~100MB)
- Optionally sets up Ollama LLM (~2GB)

**After this, everything runs offline!**

---

### Step 2: Prepare Your Files

#### Reference Documents (NIST Framework)
Place NIST framework .docx files in `reference/` folder:

```bash
reference/
├── nist_identify.docx
├── nist_protect.docx
├── nist_detect.docx
├── nist_respond.docx
└── nist_recover.docx
```

#### Test Policies
Place your organizational policies in `test_policies/` folder:

```bash
test_policies/
├── isms_policy.txt
├── data_privacy_policy.docx
├── patch_management.pdf
└── risk_management.txt
```

**Supported formats:** .txt, .docx, .pdf

---

### Step 3: Run Analysis

#### Option A: Basic Analysis (No LLM)
```bash
python policy_gap_analyzer.py \
  --reference_folder refs/ \
  --test_folder tests/
```

**Run time:** 5-10 seconds per policy  
**Output:** Template-based recommendations

#### Option B: Enhanced Analysis (With LLM)
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Run analysis
python policy_gap_analyzer.py \
  --reference_folder refs/ \
  --test_folder tests/ \
  --use-llm
```

**Run time:** 30-90 seconds per policy  
**Output:** Intelligent LLM-generated recommendations

---

### Step 4: Review Results

Results are saved in `reports/` folder:

```bash
reports/
├── isms_gap_analysis.json          # Detailed gap data
├── isms_revised_policy.md          # Policy recommendations
├── isms_improvement_roadmap.json   # Implementation plan
└── isms_summary_report.md          # Executive summary
```

**Start with:** `*_summary_report.md` for an overview

---

## Common Use Cases

### Single Policy Analysis
```bash
python policy_gap_analyzer.py \
  --reference_folder refs/ \
  --test_folder tests/ \
  --use-llm
```

### Batch Analysis (Multiple Policies)
```bash
# The tool automatically processes all files in test_folder
python policy_gap_analyzer.py \
  --reference_folder refs/ \
  --test_folder tests/ \
  --use-llm
```

### Strict Gap Detection
```bash
# Lower threshold = more gaps detected
python policy_gap_analyzer.py \
  --reference_folder refs/ \
  --test_folder tests/ \
  --threshold 0.6
```

### Lenient Gap Detection
```bash
# Higher threshold = fewer gaps (only obvious missing items)
python policy_gap_analyzer.py \
  --reference_folder refs/ \
  --test_folder tests/ \
  --threshold 0.8
```

---

## Understanding Outputs

### 1. Gap Analysis JSON
**File:** `*_gap_analysis.json`

**What it contains:**
- All identified gaps
- NIST function mapping (IDENTIFY, PROTECT, etc.)
- Severity ratings (Critical, High, Medium, Low)
- Similarity scores

**Use for:** Detailed technical analysis, programmatic processing

### 2. Revised Policy (Markdown)
**File:** `*_revised_policy.md`

**What it contains:**
- Recommended policy additions
- NIST-aligned language
- Justifications for changes

**Use for:** Policy writing, stakeholder review

### 3. Improvement Roadmap (JSON)
**File:** `*_improvement_roadmap.json`

**What it contains:**
- Phased implementation plan
- Timeline (0-3, 3-6, 6-12, 12+ months)
- Actions prioritized by severity

**Use for:** Project planning, resource allocation

### 4. Summary Report (Markdown)
**File:** `*_summary_report.md`

**What it contains:**
- Executive summary
- Gap statistics
- Top gaps by NIST function

**Use for:** Management briefings, quick overview

---

## Troubleshooting

### Issue: "No reference files found"
**Solution:**
```bash
# Make sure reference folder exists and contains .docx files
ls reference/
# Should show: *.docx files
```

### Issue: "Ollama not available"
**Solution:**
```bash
# Start Ollama in a separate terminal
ollama serve

# Or run without LLM
python policy_gap_analyzer.py \
  --reference_folder refs/ \
  --test_folder tests/
  # (no --use-llm flag)
```

### Issue: "Model not found"
**Solution:**
```bash
# Download the model manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Issue: Analysis is slow
**Solution:**
```bash
# Remove --use-llm for faster (but less intelligent) analysis
# OR
# Use smaller chunks
python policy_gap_analyzer.py \
  --reference_folder refs/ \
  --test_folder tests/ \
  --chunk_size 300
```

---

## Getting Help

```bash
# See all available options
python policy_gap_analyzer.py --help

# Test with example
python policy_gap_analyzer.py \
  --reference_folder refs/ \
  --test_folder tests/ \
  --output test_run/
```

---

## Next Steps

1. ✅ Run setup.py (one time)
2. ✅ Prepare reference documents
3. ✅ Prepare test policies
4. ✅ Run basic analysis
5. ✅ Review outputs
6. 🔄 Refine threshold if needed
7. 🎯 Implement recommendations

---

**Need More Details?** See README.md for comprehensive documentation.