# Local LLM Powered Policy Gap Analysis and Improvement Module

## Overview
This tool performs automated gap analysis of organizational cybersecurity policies against the **NIST Cybersecurity Framework** as documented in the CIS MS-ISAC Policy Template Guide (2024). It identifies policy deficiencies, generates revised policy recommendations, and provides a prioritized improvement roadmap.

### Key Features
- ✅ **Fully Offline Operation**: No internet connection required
- ✅ **Local LLM Integration**: Uses Ollama with lightweight models (Llama 3.2 3B)
- ✅ **Zero External APIs**: All processing done locally
- ✅ **NIST CSF Alignment**: Based on official CIS MS-ISAC framework
- ✅ **Comprehensive Analysis**: Covers all 5 NIST functions (Identify, Protect, Detect, Respond, Recover)
- ✅ **Automated Gap Detection**: Identifies missing controls and requirements
- ✅ **Policy Revision**: Generates recommended policy additions
- ✅ **Improvement Roadmap**: Provides phased implementation plan
- ✅ **Multiple Policy Support**: Analyze ISMS, Data Privacy, Patch Management, Risk Management policies

## System Requirements

### Hardware Requirements
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: Minimum 8GB (16GB recommended for LLM features)
- **Storage**: 5GB free space (for LLM model and data)

### Software Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Python**: Version 3.8 or higher
- **Ollama**: Latest version (for LLM features)

## Installation

### Step 1: Install Python Dependencies
The tool has minimal Python dependencies (all in standard library):
```bash
# No additional Python packages required
# The tool uses only standard library modules
```

### Step 2: Install Ollama (Optional but Recommended)
Ollama provides the local LLM capabilities for enhanced policy revision.

#### On Linux:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### On macOS:
```bash
brew install ollama
```

#### On Windows:
Download from https://ollama.ai/download

### Step 3: Pull the LLM Model
```bash
# Start Ollama service
ollama serve

# In another terminal, pull the model
ollama pull llama3.2:3b

# Verify installation
ollama list
```

### Step 4: Verify Installation
```bash
python policy_gap_analyzer.py --help
```

## Usage

### Basic Usage
Analyze a single policy:
```bash
python policy_gap_analyzer.py \
  --policy test_policies/isms_policy.txt \
  --type "ISMS" \
  --output results/
```

### Advanced Usage with LLM
Use local LLM for enhanced policy revision:
```bash
python policy_gap_analyzer.py \
  --policy test_policies/data_privacy_policy.txt \
  --type "Data Privacy" \
  --use-llm \
  --output results/
```

### Batch Analysis
Analyze all policies in a directory:
```bash
python policy_gap_analyzer.py \
  --policy-dir test_policies/ \
  --output results/ \
  --use-llm
```

### Command-Line Options
```
--policy PATH           Path to single policy document (.txt or .md)
--policy-dir PATH       Directory containing multiple policies
--type TEXT             Policy type (ISMS, Data Privacy, Patch Management, Risk Management)
--output PATH           Output directory for results (default: output/)
--use-llm               Enable LLM-powered policy revision (requires Ollama)
--model TEXT            Ollama model to use (default: llama3.2:3b)
```

## Output Files

For each analyzed policy, the tool generates:

### 1. Gap Analysis JSON (`*_gap_analysis.json`)
Structured JSON containing:
- Identified gaps with severity levels
- NIST framework mapping
- Coverage analysis
- Recommendations

Example structure:
```json
{
  "policy_type": "ISMS",
  "analysis_date": "2026-02-07T10:30:00",
  "nist_functions_analyzed": ["IDENTIFY", "PROTECT", "DETECT", "RESPOND", "RECOVER"],
  "identified_gaps": [
    {
      "nist_function": "PROTECT",
      "nist_category": "Data Security (PR.DS)",
      "requirement": "Data-at-rest protected",
      "severity": "critical",
      "current_coverage": "Not addressed",
      "recommendation": "Implement controls and procedures to address: Data-at-rest protected"
    }
  ],
  "severity_summary": {
    "critical": 15,
    "high": 23,
    "medium": 18,
    "low": 10
  }
}
```

### 2. Revised Policy (`*_revised_policy.md`)
Original policy with recommended additions to address gaps

### 3. Improvement Roadmap (`*_improvement_roadmap.json`)
Phased implementation plan:
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
      "focus": "Address critical security gaps",
      "actions": [...]
    }
  ]
}
```

### 4. Summary Report (`*_summary_report.md`)
Human-readable markdown report with:
- Executive summary
- Top gaps identified
- Recommended actions
- Implementation timeline

## Workflow

```
┌─────────────────────┐
│ Input Policy        │
│ Document            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Extract Policy      │
│ Content             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ NIST Framework      │
│ Comparison          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Gap Identification  │
│ (Keyword Analysis)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Severity            │
│ Assessment          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Policy Revision     │
│ (LLM or Template)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Roadmap Generation  │
│ (Phased Plan)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Output Files        │
│ Generation          │
└─────────────────────┘
```

## Implementation Logic

### 1. Policy Content Extraction
- Reads .txt or .md policy files
- Normalizes text for analysis
- Preserves document structure

### 2. NIST Framework Mapping
The tool contains embedded NIST CSF structure covering:
- **IDENTIFY**: Asset Management, Governance, Risk Assessment, Risk Management Strategy, Supply Chain
- **PROTECT**: Access Control, Training, Data Security, Information Protection, Maintenance, Protective Technology
- **DETECT**: Anomalies & Events, Continuous Monitoring, Detection Processes
- **RESPOND**: Response Planning, Communications, Analysis, Mitigation, Improvements
- **RECOVER**: Recovery Planning, Improvements, Communications

### 3. Gap Detection Algorithm
```python
for each NIST requirement:
    1. Extract keywords from requirement
    2. Search policy text for keywords
    3. Calculate coverage ratio
    4. If coverage < 60%:
       - Flag as gap
       - Assess severity
       - Generate recommendation
```

### 4. Severity Assessment
Gaps are classified based on keyword analysis:
- **Critical**: Governance, access control, data protection, encryption, authentication
- **High**: Risk management, incident response, vulnerability management, monitoring
- **Medium**: Training, awareness, documentation, testing
- **Low**: Other operational controls

### 5. Policy Revision
Two modes available:

#### A. LLM-Enhanced Mode (Requires Ollama)
- Sends gaps to local LLM
- Generates contextual policy additions
- Maintains policy writing style
- Provides specific, actionable content

#### B. Template-Based Mode (Fallback)
- Groups gaps by NIST function
- Generates structured recommendations
- Creates boilerplate policy sections
- Always available (no LLM required)

### 6. Roadmap Generation
Organizes gaps into 4 phases:
- **Phase 1 (0-3 months)**: Critical gaps requiring immediate action
- **Phase 2 (3-6 months)**: High-priority security enhancements
- **Phase 3 (6-12 months)**: Medium-priority maturity improvements
- **Phase 4 (12+ months)**: Low-priority comprehensive coverage

## Example Analysis Run

```bash
$ python policy_gap_analyzer.py --policy test_policies/isms_policy.txt --type ISMS --use-llm

======================================================================
🔐 LOCAL LLM POWERED POLICY GAP ANALYSIS TOOL
======================================================================
Framework: NIST Cybersecurity Framework (CIS MS-ISAC 2024)
Model: llama3.2:3b
LLM-Enhanced Revision: Enabled
======================================================================

======================================================================
📄 Analyzing: isms_policy.txt
📋 Type: ISMS
======================================================================

🔍 Analyzing ISMS policy for gaps...
  → Analyzing IDENTIFY function...
  → Analyzing PROTECT function...
  → Analyzing DETECT function...
  → Analyzing RESPOND function...
  → Analyzing RECOVER function...

📝 Generating revised policy...
  → Using local LLM for policy revision...

🗺️  Generating improvement roadmap...

✅ Gap analysis saved: output/isms_gap_analysis.json
✅ Revised policy saved: output/isms_revised_policy.md
✅ Improvement roadmap saved: output/isms_improvement_roadmap.json
✅ Summary report saved: output/isms_summary_report.md

✅ Analysis complete for ISMS

======================================================================
✅ ALL ANALYSES COMPLETE
📁 Results saved to: /path/to/output
======================================================================
```

## Testing

### Test Data
The `test_policies/` directory contains 4 dummy policies:
1. **ISMS Policy** - General information security management
2. **Data Privacy Policy** - Data protection and privacy controls
3. **Patch Management Policy** - Software update procedures
4. **Risk Management Policy** - Risk identification and treatment

### Running Tests
```bash
# Analyze all test policies
python policy_gap_analyzer.py \
  --policy-dir test_policies/ \
  --output test_results/ \
  --use-llm

# Verify outputs were generated
ls -la test_results/
```

## Limitations

### Current Limitations
1. **Keyword-Based Detection**: Gap detection relies on keyword matching, which may:
   - Miss gaps phrased differently
   - Generate false positives for generic terms
   - Require manual validation of results

2. **LLM Context Window**: Very long policies (>2000 words) are truncated when sent to LLM

3. **No PDF Support**: Currently supports only .txt and .md files
   - Use `pdftotext` to convert PDFs: `pdftotext policy.pdf policy.txt`

4. **English Only**: Framework and analysis optimized for English-language policies

5. **Static Framework**: NIST framework embedded in code (not dynamically loaded)

### Performance Considerations
- **Without LLM**: Near-instantaneous analysis
- **With LLM**: 30-60 seconds per policy depending on:
  - Number of gaps identified
  - LLM model size
  - System specifications

## Future Improvements

### Planned Enhancements
1. **Enhanced Gap Detection**:
   - Semantic similarity analysis using embeddings
   - Multi-lingual support
   - Custom framework upload capability

2. **Advanced Policy Generation**:
   - Multi-turn LLM conversations for refinement
   - Policy comparison across versions
   - Compliance mapping (GDPR, ISO 27001, SOC 2)

3. **Integration Features**:
   - PDF document support
   - DOCX import/export
   - Web interface for non-technical users
   - API for integration with GRC platforms

4. **Analytics & Reporting**:
   - Trend analysis across multiple policy versions
   - Benchmark against industry standards
   - Compliance dashboard
   - Export to PowerPoint presentations

5. **Model Options**:
   - Support for alternative local LLMs (GPT4All, LM Studio)
   - Fine-tuned models for policy analysis
   - Ensemble approach using multiple models

## Troubleshooting

### Issue: "Ollama not found"
**Solution**: Ensure Ollama is installed and in system PATH
```bash
which ollama  # Should return path to ollama binary
```

### Issue: "Model not available"
**Solution**: Pull the model explicitly
```bash
ollama pull llama3.2:3b
ollama list  # Verify model is downloaded
```

### Issue: "LLM query timed out"
**Solution**: This indicates the LLM is taking too long (>180 seconds)
- Check system resources (CPU, RAM usage)
- Try smaller model: `--model llama3.2:1b`
- Disable LLM mode: remove `--use-llm` flag

### Issue: "Policy file not found"
**Solution**: Check file path and format
```bash
ls -la test_policies/  # Verify files exist
file test_policies/isms_policy.txt  # Should show: ASCII text
```

### Issue: "No gaps identified" (unexpected)
**Solution**: This can happen if policy is very comprehensive or keyword matching fails
- Review the policy content
- Check if policy uses different terminology
- Examine the gap_analysis.json to see what was checked

## Support & Contact

For issues, questions, or contributions:
- Review this documentation
- Check the `documentation/` directory for additional guides
- Examine the source code comments for implementation details

## License
This tool is provided for educational and organizational use. 

## References
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS MS-ISAC NIST CSF Policy Template Guide 2024](https://www.cisecurity.org/-/media/project/cisecurity/cisecurity/data/media/files/uploads/2024/08/cisms-isac-nist-cybersecurity-framework-policy-template-guide-2024.pdf)
- [Ollama Documentation](https://ollama.ai/docs)
- [Llama 3.2 Model Details](https://ollama.ai/library/llama3.2)
