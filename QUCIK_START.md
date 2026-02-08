# Quick Start Guide - Policy Gap Analyzer (Fixed Version)

## 🚀 5-Minute Setup

### Step 1: Install Ollama and Pull Model (One Time)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended model (3.8 GB download)
ollama pull llama3.2:3b

# Verify installation
ollama list
```

### Step 2: Install Python Dependencies

```bash
# Clone or download the fixed version
cd policy_gap_analyzer_fixed

# Install requirements
pip install -r requirements.txt
```

### Step 3: Prepare Your Policy

Place your policy PDF in a test directory:
```bash
mkdir test_policies
# Copy your policy.pdf to test_policies/
```

### Step 4: Run Analysis

```bash
# Edit policy_gap_analyzer.py line 321 to point to your policy
# Change: policy_path = "test_policies/your_policy.pdf"

# Run the analysis
python policy_gap_analyzer.py
```

### Step 5: Review Results

Check the generated files:
- `gap_analysis_report.txt` - Detailed gap report
- `revised_policy.txt` - Policy with suggested additions

---

## 📊 Expected Results

For a typical 10-page policy, you should see:

```
✅ ANALYSIS COMPLETE
================================================================================
📊 Total Gaps: 30-40 (NOT 200+!)
🔴 Critical: 6-8
🟠 High: 10-12
🟡 Medium: 8-10
🟢 Low: 6-10
```

**Processing Time**: 4-6 minutes on average hardware

---

## ⚙️ Tuning the Gap Count

### If You're Getting Too Many Gaps (50+)

**Option 1: Edit code directly**
```python
# In policy_gap_analyzer.py, line 42
analyzer = PolicyGapAnalyzer(
    similarity_threshold=0.60  # Lower = fewer gaps (was 0.65)
)
```

**Option 2: Use config file**
```bash
# Edit config.ini
similarity_threshold = 0.60

# Run with config
python run_with_config.py test_policies/your_policy.pdf
```

**Option 3: Test different thresholds**
```bash
# This will show you gap counts at different thresholds
python test_thresholds.py test_policies/your_policy.pdf

# Output:
# Threshold 0.55 → 22 gaps
# Threshold 0.60 → 28 gaps
# Threshold 0.65 → 35 gaps ← Recommended
# Threshold 0.70 → 48 gaps
```

### If You're Getting Too Few Gaps (<15)

```python
# Increase threshold for stricter analysis
analyzer = PolicyGapAnalyzer(
    similarity_threshold=0.70  # Higher = more gaps
)
```

---

## 🎯 Threshold Guide

| Threshold | Gap Count | Best For |
|-----------|-----------|----------|
| 0.55-0.60 | 15-25 | Initial assessment, not ready for compliance |
| 0.65 | 25-40 | **Most use cases** (recommended) |
| 0.70-0.75 | 40-60 | Comprehensive audit, certification prep |

---

## 📝 Common Use Cases

### Use Case 1: Quick Assessment
```bash
# Fast check with lenient threshold
python test_thresholds.py your_policy.pdf 0.60
```

### Use Case 2: Compliance Audit
```bash
# Comprehensive check with strict threshold  
python test_thresholds.py your_policy.pdf 0.70
```

### Use Case 3: Compare Multiple Policies
```python
# Edit policy_gap_analyzer.py main() function
policies = [
    "test_policies/isms_policy.pdf",
    "test_policies/data_privacy_policy.pdf",
    "test_policies/risk_management_policy.pdf"
]

for policy in policies:
    print(f"\n=== Analyzing {policy} ===")
    gaps = analyzer.identify_gaps(policy)
    print(f"Gaps found: {len(gaps)}")
```

### Use Case 4: Focus on Critical Gaps Only
```python
# After running analysis
critical_gaps = [g for g in gaps if g.severity == "Critical"]
print(f"Critical gaps: {len(critical_gaps)}")

for gap in critical_gaps:
    print(f"- {gap.category}: {gap.gap_description}")
```

---

## 🔧 Troubleshooting

### Problem: "ConnectionError: Ollama not running"
```bash
# Start Ollama service
ollama serve

# In another terminal, run your analysis
python policy_gap_analyzer.py
```

### Problem: "Model not found"
```bash
# List available models
ollama list

# Pull missing model
ollama pull llama3.2:3b
```

### Problem: Out of memory
```bash
# Use smaller model
ollama pull phi3:mini

# Update config.ini or code
model_name = phi3:mini
```

### Problem: Very slow processing
```python
# In config.ini or code, reduce max topics
max_topics = 10  # Instead of 15

# Or use faster model
model_name = phi3:mini
```

---

## 📦 File Structure

After setup, you should have:

```
policy_gap_analyzer_fixed/
│
├── policy_gap_analyzer.py      # Main analyzer
├── run_with_config.py          # Run with config file
├── test_thresholds.py          # Test different thresholds
├── config.ini                  # Configuration file
├── requirements.txt            # Python dependencies
│
├── test_policies/              # Your policies
│   └── your_policy.pdf
│
└── outputs/                    # Generated reports
    ├── gap_analysis_report.txt
    ├── revised_policy.txt
    └── improvement_roadmap.json
```

---

## 🎓 Next Steps

1. **Run your first analysis** with default settings
2. **Review the gap report** to understand what's detected
3. **Adjust the threshold** if needed based on results
4. **Generate revised policy** with suggested additions
5. **Create improvement roadmap** for your team

---

## 💡 Pro Tips

### Tip 1: Batch Processing
```python
# Process multiple policies at once
import glob

for policy_path in glob.glob("test_policies/*.pdf"):
    print(f"Analyzing {policy_path}...")
    gaps = analyzer.identify_gaps(policy_path)
    print(f"  → {len(gaps)} gaps found\n")
```

### Tip 2: Export to CSV
```python
import csv

# After running analysis
with open('gaps.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Category', 'Severity', 'Description', 'Recommendation'])
    
    for gap in gaps:
        writer.writerow([
            gap.category,
            gap.severity,
            gap.gap_description,
            gap.recommendation
        ])
```

### Tip 3: Filter by Function
```python
# Only analyze specific NIST functions
# Edit config.ini
analyze_identify = true
analyze_protect = true
analyze_detect = false    # Skip this
analyze_respond = false   # Skip this
analyze_recover = false   # Skip this
```

### Tip 4: Custom Categories
```python
# Add your own framework categories
# In policy_gap_analyzer.py __init__
self.nist_framework["CUSTOM"] = [
    "Your Custom Category 1",
    "Your Custom Category 2"
]
```

---

## 📞 Support

If you encounter issues:

1. Check this guide first
2. Review TECHNICAL_DOCS.md for detailed explanations
3. Try different thresholds using test_thresholds.py
4. Ensure Ollama is running and model is downloaded

---

## ✅ Success Checklist

- [ ] Ollama installed and running
- [ ] Model downloaded (llama3.2:3b or similar)
- [ ] Python dependencies installed
- [ ] Policy PDF available
- [ ] Analysis completed successfully
- [ ] Gap count is reasonable (20-50 for typical policy)
- [ ] Report generated and reviewed
- [ ] Threshold adjusted if needed

---

**You're all set! Start analyzing your policies and improving your cybersecurity posture! 🎉**
