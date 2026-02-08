import os
import sys
import argparse
import glob
import json
import requests
from datetime import datetime
from docx import Document  # For reading .docx files
import pdfplumber  # For reading .pdf files
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer, util
import numpy as np
import nltk
from tqdm import tqdm

# Download NLTK data if not present (run once with internet)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK punkt tokenizer (first run only)...")
    nltk.download('punkt', quiet=True)

# ============================================================================

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        full_text = [para.text for para in doc.paragraphs]
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def extract_text_from_file(file_path):
    ext = file_path.lower().split('.')[-1]
    if ext == 'docx':
        return extract_text_from_docx(file_path)
    elif ext == 'txt':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading .txt file {file_path}: {e}")
            return ""
    elif ext == 'pdf':
        try:
            with pdfplumber.open(file_path) as pdf:
                return '\n'.join([page.extract_text() for page in pdf.pages if page.extract_text()])
        except Exception as e:
            print(f"Error reading .pdf file {file_path}: {e}")
            return ""
    else:
        print(f"Unsupported file format: {file_path}")
        return ""

def get_docx_files(folder_path):
    if not os.path.exists(folder_path):
        raise ValueError(f"Folder {folder_path} does not exist.")
    files = glob.glob(os.path.join(folder_path, "*.docx"))
    if not files:
        print(f"Warning: No .docx files found in {folder_path}.")
    return files

def get_test_files(folder_path):
    if not os.path.exists(folder_path):
        raise ValueError(f"Folder {folder_path} does not exist.")
    patterns = [
        os.path.join(folder_path, "*.docx"),
        os.path.join(folder_path, "*.txt"),
        os.path.join(folder_path, "*.pdf")
    ]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    if not files:
        print(f"Warning: No .docx, .txt, or .pdf files found in {folder_path}.")
    return files

def combine_references(reference_files):
    combined_text = ""
    for ref_file in reference_files:
        combined_text += extract_text_from_docx(ref_file) + "\n\n"
    return combined_text.strip()

# ============================================================================

def chunk_text(text, chunk_size=1200, overlap=200):
    sentences = nltk.sent_tokenize(text)
    sentence_text = ' '.join(sentences)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return text_splitter.split_text(sentence_text)

# ============================================================================

def detect_policy_type(filename, policy_text):
    filename_lower = filename.lower()
    text_lower = policy_text.lower()
    policy_indicators = {
        'ISMS': {'filename_keywords': ['isms','information_security','infosec','security_management'],
                 'content_keywords': ['information security management','isms','security policy','information assets','security controls','iso 27001']},
        'Data Privacy': {'filename_keywords':['privacy','data_privacy','data_protection','gdpr','pii'],
                 'content_keywords':['personal data','privacy','data subject','consent','data protection','gdpr','personally identifiable']},
        'Patch Management': {'filename_keywords':['patch','patching','update','vulnerability'],
                 'content_keywords':['patch management','software update','vulnerability remediation','patch deployment','security patch','patch cycle']},
        'Risk Management': {'filename_keywords':['risk','risk_management','risk_assessment'],
                 'content_keywords':['risk management','risk assessment','risk analysis','risk mitigation','threat assessment','risk register']},
        'Incident Response': {'filename_keywords':['incident','ir','incident_response'],
                 'content_keywords':['incident response','security incident','incident handling','breach response','incident management']},
        'Access Control': {'filename_keywords':['access','access_control','iam','identity'],
                 'content_keywords':['access control','authentication','authorization','identity management','privileged access']},
        'Backup Recovery': {'filename_keywords':['backup','recovery','bcdr','disaster'],
                 'content_keywords':['backup','disaster recovery','business continuity','data recovery','restoration']}
    }
    scores = {}
    for policy_type, indicators in policy_indicators.items():
        score = 0
        for keyword in indicators['filename_keywords']:
            if keyword in filename_lower:
                score += 3
        text_sample = text_lower[:2000]
        for keyword in indicators['content_keywords']:
            if keyword in text_sample:
                score += 1
        scores[policy_type] = score
    if max(scores.values()) >= 2:
        return max(scores, key=scores.get)
    else:
        return 'General'

def filter_relevant_references(reference_chunks, policy_type):
    domain_keywords = {
        'ISMS': ['information security','isms','security management','iso 27001','security controls','information assets','security governance','security policy','security framework','asset management','governance','risk assessment','access control','data security'],
        'Data Privacy': ['privacy','personal data','data protection','gdpr','pii','personally identifiable','data subject','consent','data breach','privacy rights','data minimization','retention','data security','confidentiality','encryption'],
        'Patch Management': ['patch','vulnerability','update','software update','patch management','vulnerability management','remediation','patch deployment','patch testing','maintenance','configuration management','baseline configuration','system hardening'],
        'Risk Management': ['risk','threat','vulnerability','risk assessment','risk management','risk analysis','risk mitigation','risk treatment','likelihood','impact','risk register','threat assessment','control effectiveness','risk appetite','risk tolerance'],
        'Incident Response': ['incident','incident response','security incident','breach','incident handling','containment','forensics','investigation','incident management','response procedures','escalation','anomalies','detection','monitoring','alerts'],
        'Access Control': ['access control','authentication','authorization','identity','access management','privileged access','least privilege','credential','multi-factor','password','user access','role-based access','access review'],
        'Backup Recovery': ['backup','recovery','business continuity','disaster recovery','restoration','resilience','backup procedures','recovery planning','continuity planning','recovery time','recovery point','data backup','system recovery'],
        'General': []
    }
    if policy_type == 'General':
        return reference_chunks
    relevant_keywords = domain_keywords.get(policy_type, [])
    filtered_chunks = []
    for chunk in reference_chunks:
        chunk_lower = chunk.lower()
        relevance_score = sum(1 for kw in relevant_keywords if kw in chunk_lower)
        is_core_requirement = any(kw in chunk_lower for kw in ['must','shall','required','policy','procedure','process','management','organization','documentation'])
        # Strict filtering: require 2 keyword matches OR core + 1 keyword
        if relevance_score >= 2 or (is_core_requirement and relevance_score >= 1):
            filtered_chunks.append(chunk)
    print(f"  Policy type: {policy_type}")
    print(f"  Filtered references: {len(filtered_chunks)}/{len(reference_chunks)} chunks relevant")
    return filtered_chunks

# ============================================================================

def extract_nist_requirements(reference_chunks):
    nist_requirements = {'IDENTIFY': [],'PROTECT': [],'DETECT': [],'RESPOND': [],'RECOVER': []}
    nist_keywords = {
        'IDENTIFY':['asset management','business environment','governance','risk assessment','risk management strategy','supply chain','inventory','criticality','organizational understanding','priorities','objectives','stakeholder'],
        'PROTECT':['access control','awareness','training','data security','information protection','maintenance','protective technology','authentication','authorization','encryption','least privilege','security awareness','baseline configuration','integrity checking'],
        'DETECT':['anomalies','events','continuous monitoring','detection processes','security monitoring','event detection','alerts','logging','baseline deviation','malicious code','unauthorized access'],
        'RESPOND':['response planning','communications','analysis','mitigation','improvements','incident response','containment','forensics','incident handling','response procedures','stakeholder notification'],
        'RECOVER':['recovery planning','improvements','communications','restoration','business continuity','disaster recovery','resilience','lessons learned','recovery procedures','recovery time objective','backup restoration']
    }
    for chunk in reference_chunks:
        chunk_lower = chunk.lower()
        scores = {f: sum(1 for kw in kws if kw in chunk_lower) for f,kws in nist_keywords.items()}
        if max(scores.values()) > 0:
            best_function = max(scores, key=scores.get)
            nist_requirements[best_function].append(chunk)
    return nist_requirements

# ============================================================================

def check_ollama_available():
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        return response.status_code == 200
    except:
        return False

def query_local_llm(prompt, model="llama3.2:3b", timeout=180):
    try:
        response = requests.post('http://localhost:11434/api/generate', json={'model':model,'prompt':prompt,'stream':False}, timeout=timeout)
        if response.status_code == 200:
            return response.json()['response']
        else:
            print(f"LLM query failed with status {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print(f"LLM query timed out after {timeout} seconds")
        return None
    except requests.exceptions.ConnectionError:
        print("Cannot connect to Ollama. Make sure it's running (ollama serve)")
        return None
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return None

# ============================================================================

def analyze_gaps_nist_aligned(reference_chunks, test_chunks, nist_requirements, model_name='all-MiniLM-L6-v2', threshold=0.7):
    print("Loading sentence transformer model...")
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        print(f"Error loading model {model_name}: {e}")
        sys.exit(1)
    
    print("Encoding test policy chunks...")
    test_embeddings = model.encode(test_chunks, convert_to_tensor=True, show_progress_bar=True)
    
    gaps = {'IDENTIFY': [],'PROTECT': [],'DETECT': [],'RESPOND': [],'RECOVER': []}
    
    for function, req_chunks in nist_requirements.items():
        if not req_chunks:
            continue
        # Limit number of chunks per function
        req_chunks = req_chunks[:50]
        print(f"Analyzing {function} function ({len(req_chunks)} requirements)...")
        req_embeddings = model.encode(req_chunks, convert_to_tensor=True, show_progress_bar=False)
        similarities = util.cos_sim(test_embeddings, req_embeddings)
        for i, req_chunk in enumerate(req_chunks):
            max_sim = float(np.max(similarities[:, i].cpu().numpy()))
            if max_sim < threshold:
                if max_sim < 0.5:
                    severity = "Critical"
                    coverage = "Not addressed"
                elif max_sim < 0.65:
                    severity = "High"
                    coverage = "Minimally addressed"
                elif max_sim < threshold:
                    severity = "Medium"
                    coverage = "Partially addressed"
                else:
                    severity = "Low"
                    coverage = "Mostly addressed"
                category = extract_nist_category(req_chunk, function)
                gaps[function].append({
                    'nist_function': function,
                    'nist_category': category,
                    'requirement': req_chunk[:500],
                    'max_similarity': max_sim,
                    'severity': severity,
                    'current_coverage': coverage,
                    'recommendation': f"Implement controls and procedures to address: {req_chunk[:200]}..."
                })
    return gaps

def extract_nist_category(requirement_text, function):
    categories = {
        'IDENTIFY': {'Asset Management':['asset','inventory','hardware','software','data flow'],
                     'Business Environment':['business','mission','stakeholder','priority'],
                     'Governance':['governance','policy','legal','regulatory','privacy'],
                     'Risk Assessment':['risk','threat','vulnerability','likelihood','impact'],
                     'Risk Management Strategy':['risk strategy','risk tolerance','risk appetite'],
                     'Supply Chain':['supply chain','supplier','vendor','third-party']},
        'PROTECT': {'Access Control':['access','authentication','authorization','credential'],
                    'Awareness and Training':['awareness','training','education'],
                    'Data Security':['data security','encryption','data protection','confidentiality'],
                    'Information Protection':['information protection','baseline','configuration'],
                    'Maintenance':['maintenance','logging','audit'],
                    'Protective Technology':['protective technology','technical security','firewall']},
        'DETECT': {'Anomalies and Events':['anomaly','anomalies','event','baseline'],
                   'Security Continuous Monitoring':['monitoring','continuous','real-time'],
                   'Detection Processes':['detection','alerts','threshold','indicator']},
        'RESPOND': {'Response Planning':['response plan','incident response','procedures'],
                    'Communications':['communication','notification','reporting'],
                    'Analysis':['analysis','investigate','forensic','root cause'],
                    'Mitigation':['mitigation','contain','isolate','remediate'],
                    'Improvements':['lessons learned','improvement','update']},
        'RECOVER': {'Recovery Planning':['recovery plan','business continuity','disaster recovery'],
                    'Improvements':['recovery improvement','recovery update'],
                    'Communications':['recovery communication','stakeholder notification']}
    }
    req_lower = requirement_text.lower()
    if function in categories:
        for category, keywords in categories[function].items():
            if any(keyword in req_lower for keyword in keywords):
                return category
    return "General"

# ============================================================================
# POLICY REVISION GENERATION
# ============================================================================

def generate_revised_policy_with_llm(test_text, gaps, reference_text, model="llama3.2:3b"):
    """Generate revised policy using local LLM"""
    
    # Flatten and prioritize gaps
    all_gaps = []
    for function, function_gaps in gaps.items():
        all_gaps.extend(function_gaps)
    
    # Sort by severity
    severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
    all_gaps.sort(key=lambda x: severity_order.get(x['severity'], 4))
    
    # Select top gaps (limit for context window)
    top_gaps = all_gaps[:15]
    
    # Prepare gap summary
    gap_summary = "\n".join([
        f"{i+1}. [{g['severity']}] {g['nist_function']} - {g['nist_category']}: {g['requirement'][:150]}..."
        for i, g in enumerate(top_gaps)
    ])
    
    # Prepare prompt
    prompt = f"""You are a cybersecurity policy expert specializing in the NIST Cybersecurity Framework. 

Your task is to revise an organizational policy to address identified gaps based on NIST CSF requirements.

ORIGINAL POLICY (excerpt):
{test_text[:3000]}

IDENTIFIED GAPS (Top Priority):
{gap_summary}

NIST FRAMEWORK GUIDANCE (excerpt):
{reference_text[:2500]}

Please provide specific policy additions and modifications to address the identified gaps. For each gap, provide:
1. The policy section to add or modify
2. Precise policy language aligned with NIST CSF
3. Brief justification

Format your response as clear policy text that can be directly incorporated into the document.

REVISED POLICY SECTIONS:"""
    
    print("Querying LLM for policy revision (this may take 30-60 seconds)...")
    llm_response = query_local_llm(prompt, model=model)
    
    if llm_response:
        return llm_response
    else:
        # Fallback to template-based revision
        print("LLM unavailable. Using template-based revision.")
        return generate_revised_policy_template(test_text, all_gaps)

def generate_revised_policy_template(test_text, gaps):
    """Fallback template-based policy revision"""
    revised = "# Policy Revisions Based on Gap Analysis\n\n"
    revised += "## Original Policy\n\n"
    revised += test_text + "\n\n"
    revised += "---\n\n"
    revised += "## Recommended Additions to Address Identified Gaps\n\n"
    
    # Group by NIST function
    grouped = {}
    for gap in gaps:
        func = gap['nist_function']
        if func not in grouped:
            grouped[func] = []
        grouped[func].append(gap)
    
    for function, function_gaps in grouped.items():
        revised += f"### {function} Function\n\n"
        for gap in function_gaps[:5]:  # Limit to top 5 per function
            revised += f"**{gap['nist_category']}** (Severity: {gap['severity']})\n\n"
            revised += f"{gap['recommendation']}\n\n"
    
    return revised

# ============================================================================
# ROADMAP GENERATION
# ============================================================================

def generate_roadmap_with_llm(gaps, test_file_name, model="llama3.2:3b"):
    """Generate implementation roadmap using local LLM"""
    
    # Flatten gaps
    all_gaps = []
    for function, function_gaps in gaps.items():
        all_gaps.extend(function_gaps)
    
    # Count by severity
    severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
    for gap in all_gaps:
        severity_counts[gap['severity']] += 1
    
    # Prepare gap details (limit for context)
    gap_details = "\n".join([
        f"- [{g['severity']}] {g['nist_function']}: {g['requirement'][:120]}..."
        for g in all_gaps[:20]
    ])
    
    prompt = f"""You are a cybersecurity implementation consultant. Create a phased implementation roadmap to address policy gaps.

POLICY: {test_file_name}

GAP SUMMARY:
- Critical gaps: {severity_counts['Critical']}
- High priority gaps: {severity_counts['High']}
- Medium priority gaps: {severity_counts['Medium']}
- Low priority gaps: {severity_counts['Low']}

SAMPLE GAPS:
{gap_details}

Create a 4-phase roadmap:

PHASE 1 (0-3 months): Address Critical gaps
PHASE 2 (3-6 months): Address High priority gaps  
PHASE 3 (6-12 months): Address Medium priority gaps
PHASE 4 (12+ months): Address Low priority gaps and continuous improvement

For each phase, provide:
- Key objectives
- Specific actions (3-5 actions)
- Resource requirements
- Success metrics
- Dependencies

Format as a clear, actionable roadmap.

IMPLEMENTATION ROADMAP:"""
    
    print("Querying LLM for roadmap generation (this may take 30-60 seconds)...")
    llm_response = query_local_llm(prompt, model=model)
    
    if llm_response:
        return create_roadmap_json(llm_response, severity_counts, all_gaps)
    else:
        print("LLM unavailable. Using template-based roadmap.")
        return generate_roadmap_template(all_gaps, severity_counts)

def create_roadmap_json(llm_text, severity_counts, all_gaps):
    """Convert LLM roadmap text to structured JSON"""
    
    roadmap = {
        'overview': {
            'total_gaps': len(all_gaps),
            'critical': severity_counts['Critical'],
            'high': severity_counts['High'],
            'medium': severity_counts['Medium'],
            'low': severity_counts['Low']
        },
        'llm_generated_roadmap': llm_text,
        'phases': generate_phase_structure(all_gaps)
    }
    
    return roadmap

def generate_roadmap_template(gaps, severity_counts):
    """Generate template-based roadmap structure"""
    
    phases = generate_phase_structure(gaps)
    
    roadmap = {
        'overview': {
            'total_gaps': len(gaps),
            'critical': severity_counts['Critical'],
            'high': severity_counts['High'],
            'medium': severity_counts['Medium'],
            'low': severity_counts['Low']
        },
        'phases': phases
    }
    
    return roadmap

def generate_phase_structure(gaps):
    """Generate structured phase breakdown"""
    
    # Group gaps by severity
    critical = [g for g in gaps if g['severity'] == 'Critical']
    high = [g for g in gaps if g['severity'] == 'High']
    medium = [g for g in gaps if g['severity'] == 'Medium']
    low = [g for g in gaps if g['severity'] == 'Low']
    
    phases = []
    
    # Phase 1: Critical
    if critical:
        phases.append({
            'phase': 1,
            'timeline': '0-3 months',
            'priority': 'Critical',
            'focus': 'Address critical security gaps',
            'gap_count': len(critical),
            'actions': [
                f"{g['nist_function']}: {g['recommendation'][:150]}..."
                for g in critical[:5]
            ]
        })
    
    # Phase 2: High
    if high:
        phases.append({
            'phase': 2,
            'timeline': '3-6 months',
            'priority': 'High',
            'focus': 'Enhance security controls and processes',
            'gap_count': len(high),
            'actions': [
                f"{g['nist_function']}: {g['recommendation'][:150]}..."
                for g in high[:5]
            ]
        })
    
    # Phase 3: Medium
    if medium:
        phases.append({
            'phase': 3,
            'timeline': '6-12 months',
            'priority': 'Medium',
            'focus': 'Improve security maturity',
            'gap_count': len(medium),
            'actions': [
                f"{g['nist_function']}: {g['recommendation'][:150]}..."
                for g in medium[:5]
            ]
        })
    
    # Phase 4: Low
    if low:
        phases.append({
            'phase': 4,
            'timeline': '12+ months',
            'priority': 'Low',
            'focus': 'Comprehensive coverage and optimization',
            'gap_count': len(low),
            'actions': [
                f"{g['nist_function']}: {g['recommendation'][:150]}..."
                for g in low[:5]
            ]
        })
    
    return phases

# ============================================================================
# OUTPUT GENERATION
# ============================================================================

def save_gap_analysis_json(gaps, test_file, output_dir, policy_type='General'):
    """Save structured JSON gap analysis"""
    
    base_name = os.path.basename(test_file).rsplit('.', 1)[0]
    
    # Flatten gaps for JSON
    identified_gaps = []
    severity_summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    
    for function, function_gaps in gaps.items():
        for gap in function_gaps:
            identified_gaps.append({
                'nist_function': gap['nist_function'],
                'nist_category': gap['nist_category'],
                'requirement': gap['requirement'],
                'severity': gap['severity'].lower(),
                'current_coverage': gap['current_coverage'],
                'max_similarity': round(gap['max_similarity'], 3),
                'recommendation': gap['recommendation']
            })
            severity_summary[gap['severity'].lower()] += 1
    
    gap_data = {
        'policy_type': policy_type,
        'policy_file': os.path.basename(test_file),
        'analysis_date': datetime.now().isoformat(),
        'nist_functions_analyzed': list(gaps.keys()),
        'total_gaps': len(identified_gaps),
        'severity_summary': severity_summary,
        'identified_gaps': identified_gaps
    }
    
    output_path = os.path.join(output_dir, f"{base_name}_gap_analysis.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(gap_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Gap analysis saved: {output_path}")
    return output_path

def save_revised_policy_markdown(revised_text, test_file, output_dir, policy_type='General'):
    """Save revised policy as Markdown"""
    
    base_name = os.path.basename(test_file).rsplit('.', 1)[0]
    output_path = os.path.join(output_dir, f"{base_name}_revised_policy.md")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Revised Policy: {base_name.replace('_', ' ').title()}\n\n")
        f.write(f"**Policy Type**: {policy_type}\n\n")
        f.write(f"**Original File**: {os.path.basename(test_file)}\n\n")
        f.write(f"**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Framework**: NIST Cybersecurity Framework (CIS MS-ISAC 2024)\n\n")
        f.write("---\n\n")
        f.write(revised_text)
    
    print(f"✅ Revised policy saved: {output_path}")
    return output_path

def save_roadmap_json(roadmap_data, test_file, output_dir, policy_type='General'):
    """Save roadmap as structured JSON"""
    
    base_name = os.path.basename(test_file).rsplit('.', 1)[0]
    output_path = os.path.join(output_dir, f"{base_name}_improvement_roadmap.json")
    
    # Add policy type to roadmap metadata
    if isinstance(roadmap_data, dict):
        roadmap_data['policy_type'] = policy_type
        roadmap_data['policy_file'] = os.path.basename(test_file)
        roadmap_data['generated_date'] = datetime.now().isoformat()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(roadmap_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Improvement roadmap saved: {output_path}")
    return output_path

def save_summary_report(gaps, test_file, output_dir, policy_type='General'):
    """Generate human-readable summary report"""
    
    base_name = os.path.basename(test_file).rsplit('.', 1)[0]
    output_path = os.path.join(output_dir, f"{base_name}_summary_report.md")
    
    # Count gaps
    total_gaps = sum(len(function_gaps) for function_gaps in gaps.values())
    severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
    
    for function_gaps in gaps.values():
        for gap in function_gaps:
            severity_counts[gap['severity']] += 1
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Policy Gap Analysis Summary Report\n\n")
        f.write(f"**Policy**: {base_name.replace('_', ' ').title()}\n\n")
        f.write(f"**Policy Type**: {policy_type}\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write(f"**Framework**: NIST Cybersecurity Framework (CIS MS-ISAC 2024)\n\n")
        f.write("---\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"This {policy_type} policy was analyzed against domain-relevant NIST CSF requirements.\n\n")
        f.write(f"Total gaps identified: **{total_gaps}**\n\n")
        f.write("### Severity Breakdown\n\n")
        f.write(f"- 🔴 Critical: {severity_counts['Critical']}\n")
        f.write(f"- 🟠 High: {severity_counts['High']}\n")
        f.write(f"- 🟡 Medium: {severity_counts['Medium']}\n")
        f.write(f"- 🟢 Low: {severity_counts['Low']}\n\n")
        
        f.write("---\n\n")
        f.write("## Gap Analysis by NIST Function\n\n")
        
        for function, function_gaps in gaps.items():
            if function_gaps:
                f.write(f"### {function} ({len(function_gaps)} gaps)\n\n")
                
                # Show top 5 gaps
                for gap in function_gaps[:5]:
                    f.write(f"**{gap['nist_category']}** - Severity: {gap['severity']}\n\n")
                    f.write(f"- Requirement: {gap['requirement'][:200]}...\n")
                    f.write(f"- Current Coverage: {gap['current_coverage']}\n")
                    f.write(f"- Recommendation: {gap['recommendation'][:200]}...\n\n")
                
                if len(function_gaps) > 5:
                    f.write(f"*...and {len(function_gaps) - 5} more gaps*\n\n")
        
        f.write("---\n\n")
        f.write("## Recommended Next Steps\n\n")
        f.write("1. Review the detailed gap analysis JSON file\n")
        f.write("2. Examine the revised policy recommendations\n")
        f.write("3. Follow the phased improvement roadmap\n")
        f.write("4. Prioritize addressing Critical and High severity gaps within 3-6 months\n")
    
    print(f"✅ Summary report saved: {output_path}")
    return output_path

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main(reference_folder, test_folder, output_dir='reports', chunk_size=500, 
         overlap=100, use_llm=False, model='llama3.2:3b', threshold=0.7):
    
    print("="*70)
    print("🔐 LOCAL LLM POWERED POLICY GAP ANALYSIS TOOL")
    print("="*70)
    print(f"Framework: NIST Cybersecurity Framework (CIS MS-ISAC 2024)")
    print(f"Model: {model if use_llm else 'Semantic similarity only'}")
    print(f"LLM-Enhanced Revision: {'Enabled' if use_llm else 'Disabled (template-based)'}")
    print("="*70)
    print()
    
    # Check Ollama availability if LLM requested
    if use_llm:
        if not check_ollama_available():
            print("⚠️  Warning: Ollama is not running or not accessible.")
            print("   LLM features will be disabled. Using template-based generation.")
            print("   To enable LLM: Run 'ollama serve' in another terminal")
            print()
            use_llm = False
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}\n")
    
    # Get reference files
    print("Loading reference framework documents...")
    reference_files = get_docx_files(reference_folder)
    if not reference_files:
        print("❌ No reference files found. Exiting.")
        return
    print(f"Found {len(reference_files)} reference document(s)\n")
    
    # Combine and chunk references
    print("Processing reference documents...")
    reference_text = combine_references(reference_files)
    if not reference_text:
        print("❌ No valid reference text found. Exiting.")
        return
    
    ref_chunks = chunk_text(reference_text, chunk_size, overlap)
    print(f"Reference combined into {len(ref_chunks)} chunks\n")
    
    # Extract NIST requirements structure
    print("Extracting NIST framework structure...")
    nist_requirements = extract_nist_requirements(ref_chunks)
    for function, reqs in nist_requirements.items():
        print(f"  {function}: {len(reqs)} requirements")
    print()
    
    # Get test files
    print("Scanning for test policy files...")
    test_files = get_test_files(test_folder)
    if not test_files:
        print("❌ No test files found. Exiting.")
        return
    print(f"Found {len(test_files)} test policy file(s)\n")
    
    # Process each test file
    for idx, test_file in enumerate(test_files, 1):
        print("="*70)
        print(f"📄 Analyzing: {os.path.basename(test_file)} ({idx}/{len(test_files)})")
        print("="*70)
        
        # Extract test policy text
        test_text = extract_text_from_file(test_file)
        if not test_text:
            print(f"❌ No text extracted from {test_file}. Skipping.\n")
            continue
        
        print(f"Policy text extracted: {len(test_text)} characters")
        
        # Detect policy type
        print("\n🔍 Detecting policy type...")
        policy_type = detect_policy_type(os.path.basename(test_file), test_text)
        
        # Filter reference chunks to relevant domain
        print(f"\n📋 Filtering NIST requirements for {policy_type} domain...")
        filtered_ref_chunks = filter_relevant_references(ref_chunks, policy_type)
        
        # Extract NIST requirements from filtered chunks
        print("\n🔧 Extracting NIST framework structure from relevant requirements...")
        domain_nist_requirements = extract_nist_requirements(filtered_ref_chunks)
        for function, reqs in domain_nist_requirements.items():
            if reqs:
                print(f"  {function}: {len(reqs)} requirements")
        
        # Chunk test policy
        test_chunks = chunk_text(test_text, chunk_size, overlap)
        print(f"\nPolicy chunked into {len(test_chunks)} chunks\n")
        
        # Analyze gaps with domain-specific requirements
        print("🔍 Analyzing gaps against domain-relevant NIST requirements...")
        gaps = analyze_gaps_nist_aligned(
            filtered_ref_chunks, 
            test_chunks, 
            domain_nist_requirements,
            threshold=threshold
        )
        
        total_gaps = sum(len(fg) for fg in gaps.values())
        print(f"\n✅ Analysis complete: {total_gaps} total gaps identified\n")
        
        # Generate outputs
        base_name = os.path.basename(test_file).rsplit('.', 1)[0]
        
        # 1. Gap Analysis JSON
        try:
            save_gap_analysis_json(gaps, test_file, output_dir, policy_type)
        except Exception as e:
            print(f"❌ Error saving gap analysis: {e}")
        
        # 2. Revised Policy
        try:
            print("\n📝 Generating revised policy...")
            if use_llm:
                # Use filtered reference text for LLM context
                filtered_ref_text = '\n\n'.join(filtered_ref_chunks[:50])  # Limit for context window
                revised_policy = generate_revised_policy_with_llm(
                    test_text, gaps, filtered_ref_text, model
                )
            else:
                all_gaps = []
                for function_gaps in gaps.values():
                    all_gaps.extend(function_gaps)
                revised_policy = generate_revised_policy_template(test_text, all_gaps)
            
            save_revised_policy_markdown(revised_policy, test_file, output_dir, policy_type)
        except Exception as e:
            print(f"❌ Error saving revised policy: {e}")
        
        # 3. Improvement Roadmap
        try:
            print("\n🗺️  Generating improvement roadmap...")
            if use_llm:
                roadmap = generate_roadmap_with_llm(gaps, base_name, model)
            else:
                severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
                all_gaps = []
                for function_gaps in gaps.values():
                    all_gaps.extend(function_gaps)
                    for gap in function_gaps:
                        severity_counts[gap['severity']] += 1
                roadmap = generate_roadmap_template(all_gaps, severity_counts)
            
            save_roadmap_json(roadmap, test_file, output_dir, policy_type)
        except Exception as e:
            print(f"❌ Error saving roadmap: {e}")
        
        # 4. Summary Report
        try:
            save_summary_report(gaps, test_file, output_dir, policy_type)
        except Exception as e:
            print(f"❌ Error saving summary report: {e}")
        
        print(f"\n✅ Analysis complete for {base_name}\n")
    
    print("="*70)
    print("✅ ALL ANALYSES COMPLETE")
    print(f"📁 Results saved to: {os.path.abspath(output_dir)}")
    print("="*70)

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze policy gaps using NIST Cybersecurity Framework with local LLM support (offline after first run).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis without LLM
  python policy_gap_analyzer_enhanced.py --reference_folder reference/ --test_folder test_policies/
  
  # With LLM-enhanced revision
  python policy_gap_analyzer_enhanced.py --reference_folder reference/ --test_folder test_policies/ --use-llm
  
  # Custom similarity threshold
  python policy_gap_analyzer_enhanced.py --reference_folder reference/ --test_folder test_policies/ --threshold 0.65
        """
    )
    
    parser.add_argument(
        '--reference_folder', 
        required=True, 
        help="Path to folder containing reference .docx files (NIST framework)"
    )
    parser.add_argument(
        '--test_folder', 
        required=True, 
        help="Path to folder containing test .docx/.txt/.pdf policy files"
    )
    parser.add_argument(
        '--output', 
        default='reports', 
        help="Output directory for reports (default: reports/)"
    )
    parser.add_argument(
        '--chunk_size', 
        type=int, 
        default=500, 
        help="Chunk size in characters (default: 500)"
    )
    parser.add_argument(
        '--overlap', 
        type=int, 
        default=100, 
        help="Overlap between chunks in characters (default: 100)"
    )
    parser.add_argument(
        '--use-llm', 
        action='store_true', 
        help="Enable LLM-powered policy revision using Ollama (requires Ollama running)"
    )
    parser.add_argument(
        '--model', 
        default='llama3.2:3b', 
        help="Ollama model to use (default: llama3.2:3b)"
    )
    parser.add_argument(
        '--threshold', 
        type=float, 
        default=0.7, 
        help="Similarity threshold for gap detection (default: 0.7, lower = more gaps)"
    )
    
    args = parser.parse_args()
    
    main(
        reference_folder=args.reference_folder,
        test_folder=args.test_folder,
        output_dir=args.output,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        use_llm=args.use_llm,
        model=args.model,
        threshold=args.threshold
    )