import os
import sys
import glob
import json
import requests
from datetime import datetime
from docx import Document
import pdfplumber
import nltk
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer, util
import numpy as np

# ================= NLTK Setup ==================
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK punkt tokenizer (first run only)...")
    nltk.download('punkt', quiet=True)

# ================= FILE EXTRACTION ==================

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return '\n'.join([p.text for p in doc.paragraphs])
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
            print(f"Error reading {file_path}: {e}")
            return ""
    elif ext == 'pdf':
        try:
            with pdfplumber.open(file_path) as pdf:
                return '\n'.join([p.extract_text() or "" for p in pdf.pages])
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""
    else:
        print(f"Unsupported file type: {file_path}")
        return ""

def get_docx_files(folder_path):
    if not os.path.exists(folder_path):
        raise ValueError(f"{folder_path} does not exist")
    files = glob.glob(os.path.join(folder_path, "*.docx"))
    if not files:
        print(f"Warning: No .docx files found in {folder_path}")
    return files

def get_test_files(folder_path):
    if not os.path.exists(folder_path):
        raise ValueError(f"{folder_path} does not exist")
    patterns = [os.path.join(folder_path, ext) for ext in ["*.docx","*.txt","*.pdf"]]
    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    if not files:
        print(f"Warning: No test files found in {folder_path}")
    return files

def combine_references(reference_files):
    combined = ""
    for file in reference_files:
        combined += extract_text_from_docx(file) + "\n\n"
    return combined.strip()

# ================= TEXT CHUNKING ==================

def chunk_text(text, chunk_size=500, overlap=100):
    sentences = nltk.sent_tokenize(text)
    text_joined = ' '.join(sentences)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n","\n",". "," ",""]
    )
    return splitter.split_text(text_joined)

# ================= POLICY TYPE DETECTION ==================

def detect_policy_type(filename, text):
    filename_lower = filename.lower()
    text_lower = text.lower()
    indicators = {
        'ISMS': ['isms','information_security','infosec','security_management'],
        'Data Privacy': ['privacy','data_privacy','gdpr','pii'],
        'Patch Management': ['patch','update','vulnerability'],
        'Risk Management': ['risk','risk_assessment'],
        'Incident Response': ['incident','ir','incident_response'],
        'Access Control': ['access','iam','identity'],
        'Backup Recovery': ['backup','recovery','disaster']
    }
    scores = {}
    for policy, keywords in indicators.items():
        score = sum(3 if kw in filename_lower else 0 for kw in keywords)
        score += sum(1 for kw in keywords if kw in text_lower[:2000])
        scores[policy] = score
    best = max(scores, key=scores.get)
    return best if scores[best]>=2 else 'General'

def filter_relevant_references(chunks, policy_type):
    domain_keywords = {
        'ISMS': ['security','isms','iso 27001','asset','governance'],
        'Data Privacy': ['privacy','personal data','gdpr','pii','consent'],
        'Patch Management': ['patch','vulnerability','update','deployment'],
        'Risk Management': ['risk','threat','vulnerability','assessment'],
        'Incident Response': ['incident','breach','forensics','response'],
        'Access Control': ['access','authentication','authorization','identity'],
        'Backup Recovery': ['backup','recovery','continuity','restoration'],
        'General': []
    }
    if policy_type=='General': return chunks
    keywords = domain_keywords.get(policy_type, [])
    filtered = []
    for c in chunks:
        c_lower = c.lower()
        if any(kw in c_lower for kw in keywords) or any(k in c_lower for k in ['must','shall','required','policy','procedure','process']):
            filtered.append(c)
    return filtered

# ================= NIST REQUIREMENTS ==================

def extract_nist_requirements(chunks):
    nist = {'IDENTIFY':[],'PROTECT':[],'DETECT':[],'RESPOND':[],'RECOVER':[]}
    nist_keywords = {
        'IDENTIFY':['asset','governance','risk assessment'],
        'PROTECT':['access','training','encryption','baseline'],
        'DETECT':['anomaly','monitoring','alerts','event'],
        'RESPOND':['response','containment','forensics','communication'],
        'RECOVER':['recovery','continuity','restoration','backup']
    }
    for chunk in chunks:
        scores = {f: sum(1 for k in kws if k in chunk.lower()) for f,kws in nist_keywords.items()}
        if max(scores.values())>0:
            nist[max(scores,key=scores.get)].append(chunk)
    return nist

# ================= LLM INTERFACE ==================

def check_ollama():
    try:
        r = requests.get('http://localhost:11434/api/tags', timeout=5)
        return r.status_code==200
    except:
        return False

def query_llm(prompt, model="llama3.2:3b", timeout=180):
    try:
        r = requests.post(
            'http://localhost:11434/api/generate',
            json={'model':model,'prompt':prompt,'stream':False},
            timeout=timeout
        )
        if r.status_code==200:
            return r.json()['response']
        else:
            print(f"LLM failed: {r.status_code}")
            return None
    except Exception as e:
        print(f"LLM error: {e}")
        return None

# ================= GAP ANALYSIS ==================

def analyze_gaps(reference_chunks, test_chunks, nist_reqs, threshold=0.7, model_name='all-MiniLM-L6-v2'):
    print("Loading embedding model...")
    model = SentenceTransformer(model_name)
    test_emb = model.encode(test_chunks, convert_to_tensor=True, show_progress_bar=True)
    gaps = {'IDENTIFY':[],'PROTECT':[],'DETECT':[],'RESPOND':[],'RECOVER':[]}
    for func, req_chunks in nist_reqs.items():
        if not req_chunks: continue
        req_emb = model.encode(req_chunks, convert_to_tensor=True, show_progress_bar=False)
        sims = util.cos_sim(test_emb, req_emb)
        for i, req in enumerate(req_chunks):
            max_sim = float(np.max(sims[:,i].cpu().numpy()))
            if max_sim < threshold:
                if max_sim<0.4: severity='Critical'; coverage='Not addressed'
                elif max_sim<0.55: severity='High'; coverage='Minimally addressed'
                else: severity='Medium'; coverage='Partially addressed'
                gaps[func].append({
                    'nist_function': func,
                    'requirement': req[:500],
                    'max_similarity': max_sim,
                    'severity': severity,
                    'current_coverage': coverage,
                    'recommendation': f"Implement controls to address: {req[:200]}..."
                })
    return gaps

# ================= POLICY REVISION WITH LLM ==================

def generate_revised_policy_llm(test_text, gaps, ref_text, model="llama3.2:3b"):
    all_gaps = sum([g for g in gaps.values()], [])
    all_gaps.sort(key=lambda x: {'Critical':0,'High':1,'Medium':2,'Low':3}[x['severity']])
    top_gaps = all_gaps[:15]
    gap_summary = "\n".join([f"{i+1}. [{g['severity']}] {g['nist_function']}: {g['requirement'][:150]}..." for i,g in enumerate(top_gaps)])
    prompt = f"""You are a cybersecurity policy expert.

ORIGINAL POLICY:
{test_text[:3000]}

IDENTIFIED GAPS:
{gap_summary}

NIST FRAMEWORK EXCERPT:
{ref_text[:2500]}

Provide revised policy sections addressing these gaps. Format as policy text."""
    resp = query_llm(prompt, model=model)
    return resp or generate_revised_policy_template(test_text, all_gaps)

def generate_revised_policy_template(test_text, gaps):
    revised = "# Policy Revisions\n\n## Original Policy\n\n" + test_text + "\n\n---\n\n## Recommended Additions\n\n"
    grouped = {}
    for gap in gaps:
        grouped.setdefault(gap['nist_function'], []).append(gap)
    for func, fgaps in grouped.items():
        revised += f"### {func}\n\n"
        for g in fgaps[:5]:
            revised += f"**Severity {g['severity']}**: {g['recommendation']}\n\n"
    return revised

# ================= OUTPUT FUNCTIONS ==================

def save_json(data, filename, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path,'w',encoding='utf-8') as f: json.dump(data,f,indent=2)
    print(f"Saved: {path}")
    return path

def save_markdown(text, filename, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path,'w',encoding='utf-8') as f: f.write(text)
    print(f"Saved: {path}")
    return path

# ================= MAIN FUNCTION ==================

def main(reference_folder, test_folder, output_dir='reports', chunk_size=500, overlap=100, use_llm=True, model="llama3.2:3b", threshold=0.7):
    print("="*50,"\n🔐 POLICY GAP ANALYSIS WITH LLM\n","="*50)
    
    if use_llm and not check_ollama():
        print("⚠️ Ollama not running, disabling LLM")
        use_llm=False
    
    reference_files = get_docx_files(reference_folder)
    if not reference_files: return
    ref_text = combine_references(reference_files)
    ref_chunks = chunk_text(ref_text, chunk_size, overlap)
    nist_reqs = extract_nist_requirements(ref_chunks)
    
    test_files = get_test_files(test_folder)
    if not test_files: return
    
    for idx, test_file in enumerate(test_files,1):
        print(f"\n📄 Processing {test_file} ({idx}/{len(test_files)})")
        test_text = extract_text_from_file(test_file)
        if not test_text: continue
        
        policy_type = detect_policy_type(os.path.basename(test_file), test_text)
        filtered_chunks = filter_relevant_references(ref_chunks, policy_type)
        domain_nist = extract_nist_requirements(filtered_chunks)
        test_chunks = chunk_text(test_text, chunk_size, overlap)
        
        gaps = analyze_gaps(filtered_chunks, test_chunks, domain_nist, threshold)
        save_json(gaps, os.path.basename(test_file).rsplit('.',1)[0]+"_gap_analysis.json", output_dir)
        
        print("\n📝 Generating revised policy...")
        revised = generate_revised_policy_llm(test_text, gaps, "\n\n".join(filtered_chunks[:50]), model) if use_llm else generate_revised_policy_template(test_text, sum([g for g in gaps.values()],[]))
        save_markdown(revised, os.path.basename(test_file).rsplit('.',1)[0]+"_revised_policy.md", output_dir)
    
    print("\n✅ ALL DONE. Reports in:", os.path.abspath(output_dir))

# ================= ENTRY POINT ==================

if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference_folder', required=True)
    parser.add_argument('--test_folder', required=True)
    parser.add_argument('--output', default='reports')
    parser.add_argument('--chunk_size', type=int, default=500)
    parser.add_argument('--overlap', type=int, default=100)
    parser.add_argument('--use_llm', action='store_true')
    parser.add_argument('--model', default='llama3.2:3b')
    parser.add_argument('--threshold', type=float, default=0.7)
    args = parser.parse_args()
    main(args.reference_folder, args.test_folder, args.output, args.chunk_size, args.overlap, args.use_llm, args.model, args.threshold)
