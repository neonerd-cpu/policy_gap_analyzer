#!/usr/bin/env python3
"""
Setup script for Policy Gap Analyzer
Run this once with internet connection to download required models and data
"""

import os
import sys
import subprocess

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def check_python_version():
    """Ensure Python 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def install_requirements():
    """Install Python dependencies"""
    print_header("Installing Python Dependencies")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", 
    "--break-system-packages"
        ])
        print("\n✅ Python dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        sys.exit(1)

def download_nltk_data():
    """Download required NLTK data"""
    print_header("Downloading NLTK Data")
    
    try:
        import nltk
        nltk.download('punkt', quiet=False)
        print("✅ NLTK data downloaded successfully")
    except Exception as e:
        print(f"❌ Error downloading NLTK data: {e}")
        sys.exit(1)

def download_sentence_transformer():
    """Download and cache sentence transformer model"""
    print_header("Downloading Sentence Transformer Model")
    
    print("This will download ~100MB of model files...")
    print("Model: all-MiniLM-L6-v2 (lightweight, optimized for semantic similarity)\n")
    
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("\n✅ Sentence transformer model downloaded and cached")
        print(f"   Cache location: {model._model_card_vars['model_name']}")
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        sys.exit(1)

def setup_ollama():
    """Check and setup Ollama"""
    print_header("Ollama LLM Setup (Optional)")
    
    print("Ollama provides local LLM capabilities for enhanced policy revision.")
    print("This is OPTIONAL - the tool works without it using template-based generation.\n")
    
    # Check if ollama is installed
    try:
        result = subprocess.run(
            ['ollama', '--version'], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ Ollama is installed: {result.stdout.strip()}")
            
            # Offer to pull the model
            response = input("\nWould you like to download the llama3.2:3b model (~2GB)? [y/N]: ")
            if response.lower() in ['y', 'yes']:
                print("\nDownloading llama3.2:3b model (this may take several minutes)...")
                try:
                    subprocess.check_call(['ollama', 'pull', 'llama3.2:3b'])
                    print("✅ Ollama model downloaded successfully")
                except subprocess.CalledProcessError:
                    print("⚠️  Model download failed. You can try manually: ollama pull llama3.2:3b")
            else:
                print("⏭️  Skipped model download. You can download later: ollama pull llama3.2:3b")
        else:
            raise FileNotFoundError
    
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("ℹ️  Ollama not found or not running")
        print("\nTo install Ollama (optional for LLM features):")
        print("  Linux:   curl -fsSL https://ollama.ai/install.sh | sh")
        print("  macOS:   brew install ollama")
        print("  Windows: Download from https://ollama.ai/download")
        print("\nAfter installation, run: ollama pull llama3.2:3b")
        print("\nThe tool will work without Ollama using template-based generation.")

def verify_setup():
    """Verify all components are working"""
    print_header("Verifying Installation")
    
    try:
        # Test imports
        import docx
        import pdfplumber
        import langchain_text_splitters
        from sentence_transformers import SentenceTransformer
        import numpy
        import nltk
        import requests
        from tqdm import tqdm
        
        print("✅ All Python packages imported successfully")
        
        # Test sentence transformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        test_embedding = model.encode("test")
        print("✅ Sentence transformer model working")
        
        # Test NLTK
        nltk.data.find('tokenizers/punkt')
        print("✅ NLTK data available")
        
        print("\n🎉 Setup complete! You can now run the analyzer offline.")
        
    except Exception as e:
        print(f"⚠️  Verification failed: {e}")
        print("Some features may not work correctly.")

def main():
    """Main setup workflow"""
    print_header("Policy Gap Analyzer - First-Time Setup")
    
    print("This script will:")
    print("  1. Check Python version")
    print("  2. Install Python dependencies")
    print("  3. Download NLTK data (~3MB)")
    print("  4. Download sentence transformer model (~100MB)")
    print("  5. Optionally setup Ollama LLM (~2GB)")
    print("\nTotal download size: ~100MB (or ~2.1GB with Ollama)")
    print("After this setup, the tool will work completely offline.\n")
    
    response = input("Continue with setup? [Y/n]: ")
    if response.lower() in ['n', 'no']:
        print("Setup cancelled.")
        sys.exit(0)
    
    # Run setup steps
    check_python_version()
    install_requirements()
    download_nltk_data()
    download_sentence_transformer()
    setup_ollama()
    verify_setup()
    
    print_header("Next Steps")
    print("1. Prepare your reference documents (NIST framework .docx files)")
    print("2. Prepare test policies (.txt, .docx, or .pdf)")
    print("3. Run the analyzer:")
    print("\n   python policy_gap_analyzer_enhanced.py \\")
    print("     --reference_folder reference/ \\")
    print("     --test_folder test_policies/ \\")
    print("     --use-llm  # Optional, requires Ollama")
    print("\nFor help: python policy_gap_analyzer_enhanced.py --help")
    print()

if __name__ == "__main__":
    main()