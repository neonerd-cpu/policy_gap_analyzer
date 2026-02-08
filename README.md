# Local LLM Powered Policy Gap Analysis and Improvement Module

## Overview

This tool performs automated gap analysis of organizational cybersecurity policies against the **NIST Cybersecurity Framework** using semantic similarity analysis and optional local LLM enhancement. It identifies policy deficiencies, generates revised policy recommendations, and provides a prioritized improvement roadmap.

### Key Features

✅ **Fully Offline Operation** - Works completely offline after initial setup  
✅ **Semantic Gap Analysis** - Uses sentence transformers for intelligent similarity detection  
✅ **Optional LLM Enhancement** - Integrates Ollama for advanced policy revision  
✅ **NIST Framework Aligned** - Maps gaps to NIST CSF functions and categories  
✅ **Multiple File Formats** - Supports .txt, .docx, and .pdf policy documents  
✅ **Structured Outputs** - JSON gap analysis, Markdown revised policies, roadmaps  
✅ **Batch Processing** - Analyze multiple policies in one run  
✅ **Zero External APIs** - All processing done locally  

## Solution Architecture

```
┌─────────────────────┐
│ Reference Documents │ (.docx NIST framework)
│ (NIST CSF Guide)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Extract & Chunk     │
│ Framework Data      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Categorize by       │
│ NIST Function       │
│ (ID/PR/DE/RS/RC)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│ Test Policy         │────▶│ Extract & Chunk     │
│ Documents           │     │ Policy Text         │
│ (.txt/.docx/.pdf)   │     └──────────┬──────────┘
└─────────────────────┘                │
                                       ▼
                            ┌─────────────────────┐
                            │ Semantic Similarity │
                            │ Analysis            │
                            │ (SentenceTransformer)│
                            └──────────┬──────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │ Identify Gaps       │
                            │ + Severity Rating   │
                            │ + NIST Mapping      │
                            └──────────┬──────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
         ┌─────────────────────┐              ┌─────────────────────┐
         │ LLM-Enhanced        │              │ Template-Based      │
         │ Policy Revision     │              │ Revision (Fallback) │
         │ (Ollama)            │              └──────────┬──────────┘
         └──────────┬──────────┘                         │
                    │                                     │
                    └──────────────────┬──────────────────┘
                                       ▼
                            ┌─────────────────────┐
                            │ Generate Outputs:   │
                            │ • Gap Analysis JSON │
                            │ • Revised Policy MD │
                            │ • Roadmap JSON      │
                            │ • Summary Report MD │
                            └─────────────────────┘
```

## Requirements

### Hardware
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: 8GB minimum, 16GB recommended (for LLM features)
- **Storage**: 5GB free space

### Software
- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Ollama**: Latest version (optional, for LLM features)

## Installation

### Quick Start

```bash
# 1. Clone or download the repository
cd policy_gap_analyzer

# 2. Run the setup script (requires internet for first-time setup)
python setup.py

# 3. Verify installation
python policy_gap_analyzer_enhanced.py --help
```

### Manual Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt')"

# Download sentence transformer model (downloads on first use)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Optional: Install Ollama for LLM features
# Linux:
curl -fsSL https://ollama.ai/install.sh | sh

# macOS:
brew install ollama

# Windows: Download from https://ollama.ai/download

# Pull the LLM model
ollama pull llama3.2:3b
```

## Usage

### Basic Analysis (Without LLM)

```bash
python policy_gap_analyzer_enhanced.py \
  --reference_folder reference/ \
  --test_folder test_policies/ \
  --output results/
```

### Enhanced Analysis (With LLM)

```bash
# Start Ollama (in separate terminal)
ollama serve

# Run analysis with LLM
python policy_gap_analyzer_enhanced.py \
  --reference_folder reference/ \
  --test_folder test_policies/ \
  --output results/ \
  --use-llm
```

### Advanced Options

```bash
python policy_gap_analyzer_enhanced.py \
  --reference_folder reference/ \
  --test_folder test_policies/ \
  --output results/ \
  --use-llm \
  --model llama3.2:3b \
  --threshold 0.65 \
  --chunk_size 600 \
  --overlap 150
```

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--reference_folder` | Path to NIST framework .docx files (required) | - |
| `--test_folder` | Path to test policy files (required) | - |
| `--output` | Output directory for results | `reports/` |
| `--use-llm` | Enable LLM-powered revision | `False` |
| `--model` | Ollama model to use | `llama3.2:3b` |
| `--threshold` | Similarity threshold for gaps (0-1) | `0.7` |
| `--chunk_size` | Text chunk size in characters | `500` |
| `--overlap` | Overlap between chunks | `100` |

### Threshold Guide

- **0.8-1.0**: Very strict (fewer gaps, only obvious missing items)
- **0.7**: Balanced (recommended default)
- **0.6**: More sensitive (catches more potential gaps)
- **<0.6**: Very sensitive (may flag minor wording differences)

## Outputs

For each analyzed policy, the tool generates 4 files:

### 1. Gap Analysis JSON (`*_gap_analysis.json`)

Structured JSON containing all identified gaps with NIST mapping and severity ratings.

```json
{
  "policy_type": "ISMS",
  "analysis_date": "2026-02-08T10:30:00",
  "total_gaps": 66,
  "severity_summary": {
    "critical": 15,
    "high": 23,
    "medium": 18,
    "low": 10
  },
  "identified_gaps": [
    {
      "nist_function": "PROTECT",
      "nist_category": "Data Security",
      "requirement": "Data-at-rest must be encrypted...",
      "severity": "critical",
      "current_coverage": "Not addressed",
      "max_similarity": 0.35,
      "recommendation": "Implement controls for..."
    }
  ]
}
```

### 2. Revised Policy Markdown (`*_revised_policy.md`)

Policy revision recommendations in Markdown format:
- LLM-generated intelligent revisions (if --use-llm enabled)
- Template-based recommendations (fallback mode)

### 3. Improvement Roadmap JSON (`*_improvement_roadmap.json`)

Phased implementation plan with timelines:

```json
{
  "overview": {
    "total_gaps": 66,
    "critical": 15,
    "high": 23,
    "medium": 18,
    "low": 10
  },
  "phases": [
    {
      "phase": 1,
      "timeline": "0-3 months",
      "priority": "Critical",
      "gap_count": 15,
      "actions": [...]
    }
  ]
}
```

### 4. Summary Report Markdown (`*_summary_report.md`)

Human-readable executive summary with:
- Gap statistics
- Top gaps by NIST function
- Recommended next steps

## Technical Implementation

### Gap Detection Algorithm

The tool uses a **semantic similarity approach** that is superior to simple keyword matching:

1. **Text Chunking**: Splits documents into semantic chunks with overlap
2. **Embedding Generation**: Converts chunks to vector embeddings using SentenceTransformer
3. **Similarity Computation**: Calculates cosine similarity between policy and framework chunks
4. **Gap Identification**: Flags requirements with similarity < threshold as gaps
5. **Severity Classification**: Assigns severity based on similarity score and NIST category

### Severity Classification

| Similarity Score | Severity | Interpretation |
|------------------|----------|----------------|
| < 0.4 | Critical | Requirement not addressed at all |
| 0.4 - 0.55 | High | Minimally addressed |
| 0.55 - 0.7 | Medium | Partially addressed |
| 0.7 - 1.0 | Low/No Gap | Adequately addressed |

### NIST Framework Mapping

The tool automatically categorizes requirements into NIST CSF functions:

- **IDENTIFY** (ID): Asset Management, Governance, Risk Assessment, etc.
- **PROTECT** (PR): Access Control, Data Security, Training, etc.
- **DETECT** (DE): Monitoring, Detection Processes, Anomalies, etc.
- **RESPOND** (RS): Response Planning, Analysis, Mitigation, etc.
- **RECOVER** (RC): Recovery Planning, Improvements, Communications, etc.

### LLM Integration

When `--use-llm` is enabled:

1. Connects to local Ollama instance (http://localhost:11434)
2. Sends policy context + gap summary to LLM
3. Receives intelligent, context-aware policy recommendations
4. Falls back to template-based generation if LLM unavailable

## Example Workflow

```bash
# 1. Prepare reference documents
mkdir reference/
# Add NIST framework .docx files extracted from PDF

# 2. Prepare test policies
mkdir test_policies/
# Add organizational policies (.txt, .docx, or .pdf)

# 3. Start Ollama (optional, for LLM features)
ollama serve &

# 4. Run analysis
python policy_gap_analyzer_enhanced.py \
  --reference_folder reference/ \
  --test_folder test_policies/ \
  --output results/ \
  --use-llm

# 5. Review outputs
ls results/
# isms_gap_analysis.json
# isms_revised_policy.md
# isms_improvement_roadmap.json
# isms_summary_report.md
```

## Comparison: Original vs Enhanced Version

| Feature | Original Version | Enhanced Version |
|---------|------------------|------------------|
| Gap Detection | Keyword matching | Semantic similarity (embeddings) |
| NIST Alignment | Manual categorization | Automatic function mapping |
| LLM Integration | ❌ Not present | ✅ Full Ollama integration |
| Output Format | .txt files | JSON + Markdown (structured) |
| File Support | .txt only | .txt, .docx, .pdf |
| Severity Rating | Basic | Advanced (4 levels with scores) |
| Documentation | Basic README | Comprehensive docs |
| Progress Indicators | ❌ None | ✅ tqdm progress bars |
| Batch Processing | ✅ Yes | ✅ Yes (improved) |
| Error Handling | Basic | Comprehensive try-catch blocks |

## Limitations

### Current Limitations

1. **Semantic Understanding**: While better than keywords, embedding similarity can:
   - Miss nuanced policy language differences
   - Require manual validation of results
   - Be sensitive to threshold tuning

2. **LLM Context Window**: Very long policies (>5000 words) may be truncated when sent to LLM

3. **NIST Categorization**: Automatic categorization uses heuristics and may occasionally misclassify requirements

4. **Language Support**: Optimized for English-language policies only

5. **Framework Updates**: NIST framework is embedded from reference documents, not auto-updated

### Performance Considerations

- **Without LLM**: 5-10 seconds per policy (instant for small policies)
- **With LLM**: 30-90 seconds per policy (depends on model size and gap count)

## Troubleshooting

### "Model not found" Error

```bash
# Download the sentence transformer model manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### "Ollama not available" Warning

```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve

# Pull the model if needed
ollama pull llama3.2:3b
```

### "No reference files found"

Ensure your reference folder contains .docx files extracted from the NIST PDF:

```bash
ls reference/
# Should show: framework_identify.docx, framework_protect.docx, etc.
```

### Out of Memory Errors

```bash
# Reduce chunk size to decrease memory usage
python policy_gap_analyzer_enhanced.py \
  --reference_folder reference/ \
  --test_folder test_policies/ \
  --chunk_size 300 \
  --overlap 50
```

## Future Enhancements

### Planned Features

1. **Fine-tuned Models**: Custom SentenceTransformer fine-tuned on policy documents
2. **Multi-framework Support**: ISO 27001, SOC 2, GDPR mapping
3. **Version Comparison**: Track policy improvements over time
4. **Web Interface**: Browser-based GUI for non-technical users
5. **Export Options**: Word/PDF export for revised policies
6. **Compliance Dashboard**: Visual analytics and trend analysis

### Contribution Ideas

- Additional framework templates
- Improved NIST categorization algorithm
- Multi-language support
- Integration with GRC platforms
- Automated testing suite

## Technical Dependencies

### Python Packages

- `python-docx`: Reading .docx files
- `pdfplumber`: Extracting text from PDFs
- `langchain-text-splitters`: Semantic text chunking
- `sentence-transformers`: Embedding generation and similarity
- `numpy`: Numerical operations
- `nltk`: Natural language tokenization
- `requests`: Ollama API communication
- `tqdm`: Progress bars

### Models

- **SentenceTransformer**: `all-MiniLM-L6-v2` (384-dimensional embeddings, ~80MB)
- **Ollama LLM** (optional): `llama3.2:3b` (~2GB)

## License

This tool is provided for educational and organizational use.

## References

- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS MS-ISAC NIST CSF Policy Template Guide 2024](https://www.cisecurity.org/-/media/project/cisecurity/cisecurity/data/media/files/uploads/2024/08/cisms-isac-nist-cybersecurity-framework-policy-template-guide-2024.pdf)
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Ollama Documentation](https://ollama.ai/docs)
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)

## Support

For issues or questions:
1. Check this documentation
2. Review the troubleshooting section
3. Examine source code comments
4. Test with the provided example policies

---

**Version**: 2.0 (Enhanced)  
**Last Updated**: February 2026  
**Compliance**: Meets all NIST CSF Policy Gap Analysis requirements