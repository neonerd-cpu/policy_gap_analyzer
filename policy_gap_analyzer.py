import os
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import subprocess
import textwrap

# ---------------- CONFIG ----------------

REFERENCE_FILE = Path("reference/isms_policy.txt")
TEST_POLICY_FILE = Path("test_policies/test_policy.txt")
OUTPUT_DIR = Path("outputs")

LLM_MODEL = "llama3"   # change if needed
TOP_K = 5

# ----------------------------------------


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text, chunk_size=600, overlap=100):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap

    return chunks


def build_faiss_index(chunks, embedder):
    embeddings = embedder.encode(chunks)
    embeddings = np.array(embeddings).astype("float32")

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    return index, embeddings


def retrieve_reference_chunks(policy_chunk, embedder, index, ref_chunks):
    q_emb = embedder.encode([policy_chunk]).astype("float32")
    _, indices = index.search(q_emb, TOP_K)
    return [ref_chunks[i] for i in indices[0]]


def call_llm(prompt):
    process = subprocess.run(
        ["ollama", "run", LLM_MODEL],
        input=prompt,
        text=True,
        capture_output=True
    )
    return process.stdout.strip()


# ---------------- MAIN PIPELINE ----------------

def analyze_policy():
    OUTPUT_DIR.mkdir(exist_ok=True)

    reference_text = read_text(REFERENCE_FILE)
    test_policy_text = read_text(TEST_POLICY_FILE)

    ref_chunks = chunk_text(reference_text)
    policy_chunks = chunk_text(test_policy_text)

    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    index, _ = build_faiss_index(ref_chunks, embedder)

    all_gaps = []

    for chunk in policy_chunks:
        retrieved_refs = retrieve_reference_chunks(
            chunk, embedder, index, ref_chunks
        )

        prompt = f"""
You are a cybersecurity policy analyst.

REFERENCE POLICY (official standards):
{chr(10).join(retrieved_refs)}

ORGANIZATION POLICY:
{chunk}

TASK:
1. Identify missing, weak, or incomplete policy controls.
2. Compare BOTH:
   - the reference policy text
   - your internal cybersecurity standards knowledge
3. Merge similar findings.
4. Assign severity: Critical / High / Medium / Low.

OUTPUT FORMAT (plain text only):
- Gap description
- Severity
"""

        response = call_llm(prompt)
        all_gaps.append(response)

    # ---------------- CONSOLIDATION ----------------

    consolidation_prompt = f"""
You are consolidating policy gaps.

RAW GAPS:
{chr(10).join(all_gaps)}

TASK:
- Merge duplicates and low-level overlaps
- Reduce excessive LOW gaps
- Produce a clean final list

OUTPUT:
Plain text list of final gaps with severity.
"""

    consolidated_gaps = call_llm(consolidation_prompt)

    # ---------------- REVISED POLICY ----------------

    revision_prompt = f"""
Using the FINAL GAPS below, generate revised policy text
that formally addresses each gap.

FINAL GAPS:
{consolidated_gaps}

OUTPUT:
Audit-ready policy language.
"""

    revised_policy = call_llm(revision_prompt)

    # ---------------- ROADMAP ----------------

    roadmap_prompt = f"""
Based on the FINAL GAPS below, create an improvement roadmap.

FINAL GAPS:
{consolidated_gaps}

FORMAT:
Short-term (0–3 months)
Medium-term (3–9 months)
Long-term (9–18 months)
"""

    roadmap = call_llm(roadmap_prompt)

    # ---------------- WRITE OUTPUTS ----------------

    (OUTPUT_DIR / "gap_analysis.txt").write_text(consolidated_gaps, encoding="utf-8")
    (OUTPUT_DIR / "revised_policy.txt").write_text(revised_policy, encoding="utf-8")
    (OUTPUT_DIR / "improvement_roadmap.txt").write_text(roadmap, encoding="utf-8")

    print("✔ Analysis complete. TXT outputs generated.")


if __name__ == "__main__":
    analyze_policy()

