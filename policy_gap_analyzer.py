import os
import sys
import argparse
import glob
from docx import Document  # For reading .docx files
import pdfplumber  # For reading .pdf files
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer, util
import numpy as np
import nltk

# Download NLTK data if not present (run once with internet)
nltk.download('punkt')

# Function to extract text from a .docx file
def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

# Function to extract text from any supported file (.docx, .txt, .pdf)
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
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
                return text
        except Exception as e:
            print(f"Error reading .pdf file {file_path}: {e}")
            return ""
    else:
        print(f"Unsupported file format for {file_path}. Supported: .docx, .txt, .pdf")
        return ""

# Function to get all .docx files from a folder (for references)
def get_docx_files(folder_path):
    if not os.path.exists(folder_path):
        raise ValueError(f"Folder {folder_path} does not exist.")
    pattern = os.path.join(folder_path, "*.docx")
    files = glob.glob(pattern)
    if not files:
        print(f"Warning: No .docx files found in {folder_path}.")
    return files

# Function to get all supported test files (.docx, .txt, .pdf) from a folder
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

# Function to combine multiple reference files into one text
def combine_references(reference_files):
    combined_text = ""
    for ref_file in reference_files:
        text = extract_text_from_docx(ref_file)
        combined_text += text + "\n\n"  # Add separators
    return combined_text.strip()

# Improved chunking function
def chunk_text(text, chunk_size=500, overlap=100):
    # First, split into sentences for better semantic boundaries
    sentences = nltk.sent_tokenize(text)
    sentence_text = ' '.join(sentences)
    
    # Use LangChain's RecursiveCharacterTextSplitter for overlapping chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", ""]  # Prioritize paragraphs, then sentences
    )
    chunks = text_splitter.split_text(sentence_text)
    return chunks

# Function to compute similarities and find gaps
def analyze_gaps(reference_chunks, test_chunks, model_name='all-MiniLM-L6-v2'):
    # Load model: Downloads on first run (requires internet), then uses cache offline
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        print(f"Error loading model {model_name}. For first run, ensure internet to download: {e}")
        sys.exit(1)
    
    # Encode chunks
    ref_embeddings = model.encode(reference_chunks, convert_to_tensor=True)
    test_embeddings = model.encode(test_chunks, convert_to_tensor=True)
    
    # Compute cosine similarities
    similarities = util.cos_sim(test_embeddings, ref_embeddings)
    
    gaps = []
    for i, test_chunk in enumerate(test_chunks):
        max_sim = np.max(similarities[i].cpu().numpy())
        if max_sim < 0.7:  # Threshold for "gap" (adjust as needed)
            gaps.append({
                'test_chunk': test_chunk,
                'max_similarity': max_sim,
                'reason': 'Low similarity to any reference chunk'
            })
    
    return gaps

# Main function
def main(reference_folder, test_folder, output_dir='reports', chunk_size=500, overlap=100):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Get reference files (.docx only)
    reference_files = get_docx_files(reference_folder)
    if not reference_files:
        print("No reference files found. Exiting.")
        return
    
    # Combine references
    reference_text = combine_references(reference_files)
    if not reference_text:
        print("No valid reference text found. Exiting.")
        return
    
    # Chunk the combined reference
    ref_chunks = chunk_text(reference_text, chunk_size, overlap)
    print(f"Reference combined into {len(ref_chunks)} chunks.")
    
    # Get test files (.docx, .txt, .pdf)
    test_files = get_test_files(test_folder)
    if not test_files:
        print("No test files found. Exiting.")
        return
    
    # Process each test file
    for test_file in test_files:
        test_text = extract_text_from_file(test_file)
        if not test_text:
            print(f"No text extracted from {test_file}. Skipping.")
            continue
        
        test_chunks = chunk_text(test_text, chunk_size, overlap)
        print(f"Test file {test_file} chunked into {len(test_chunks)} chunks.")
        
        # Analyze gaps
        gaps = analyze_gaps(ref_chunks, test_chunks)
        
        # Generate report (strip extension from filename)
        base_name = os.path.basename(test_file).rsplit('.', 1)[0]
        report_path = os.path.join(output_dir, f"gap_report_{base_name}.txt")
        with open(report_path, 'w') as f:
            f.write(f"Gap Analysis Report for {test_file}\n")
            f.write(f"Reference folder: {reference_folder} ({len(reference_files)} files)\n\n")
            if gaps:
                f.write("Identified Gaps:\n")
                for gap in gaps:
                    f.write(f"- Chunk: {gap['test_chunk'][:200]}...\n")
                    f.write(f"  Max Similarity: {gap['max_similarity']:.2f}\n")
                    f.write(f"  Reason: {gap['reason']}\n\n")
            else:
                f.write("No significant gaps found.\n")
        
        print(f"Report saved to {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze policy gaps with reference (.docx) and test (.docx/.txt/.pdf) folders (offline after first run).")
    parser.add_argument('--reference_folder', required=True, help="Path to folder containing reference .docx files")
    parser.add_argument('--test_folder', required=True, help="Path to folder containing test .docx/.txt/.pdf files")
    parser.add_argument('--output', default='reports', help="Output directory for reports")
    parser.add_argument('--chunk_size', type=int, default=500, help="Chunk size in characters")
    parser.add_argument('--overlap', type=int, default=100, help="Overlap between chunks")
    
    args = parser.parse_args()
    main(args.reference_folder, args.test_folder, args.output, args.chunk_size, args.overlap)