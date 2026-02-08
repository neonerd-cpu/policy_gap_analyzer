"""
Local LLM-Powered Policy Gap Analysis Module
Fixed version with intelligent gap detection to avoid over-reporting
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass
import PyPDF2
import ollama
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class PolicyGap:
    """Represents a gap in the policy"""
    category: str
    gap_description: str
    severity: str  # Critical, High, Medium, Low
    recommendation: str
    framework_reference: str


class PolicyGapAnalyzer:
    """Analyzes policy documents for gaps against NIST CSF framework"""
    
    def __init__(self, model_name: str = "llama3.2:3b", similarity_threshold: float = 0.65):
        """
        Initialize the analyzer
        
        Args:
            model_name: Local Ollama model to use
            similarity_threshold: Minimum similarity score (0-1) to consider content as covered
                                Higher = stricter (more gaps), Lower = lenient (fewer gaps)
                                Default 0.65 is balanced
        """
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        try:
            self.embedding_model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2",
                local_files_only=True
            )
        except Exception as e:
            raise RuntimeError(
                "SentenceTransformer model not found in local cache.\n"
                "Run once with internet:\n"
                "  python3 -c \"from sentence_transformers import SentenceTransformer; "
                "SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')\""
            ) from e

        
        # NIST CSF Core Functions and Categories (high-level framework)
        self.nist_framework = {
            "IDENTIFY": [
                "Asset Management",
                "Business Environment",
                "Governance",
                "Risk Assessment",
                "Risk Management Strategy"
            ],
            "PROTECT": [
                "Identity Management and Access Control",
                "Awareness and Training",
                "Data Security",
                "Information Protection Processes and Procedures",
                "Maintenance",
                "Protective Technology"
            ],
            "DETECT": [
                "Anomalies and Events",
                "Security Continuous Monitoring",
                "Detection Processes"
            ],
            "RESPOND": [
                "Response Planning",
                "Communications",
                "Analysis",
                "Mitigation",
                "Improvements"
            ],
            "RECOVER": [
                "Recovery Planning",
                "Improvements",
                "Communications"
            ]
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF or TXT file"""
        if pdf_path.endswith('.txt'):
            # Handle plain text files
            with open(pdf_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Handle PDF files
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            return text
    
    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into manageable chunks for processing"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks
    
    def extract_policy_topics(self, policy_text: str) -> List[str]:
        """Extract key topics and sections from the policy using LLM"""
        prompt = f"""Analyze this policy document and extract the main topics and areas it covers.
List only the specific cybersecurity topics/areas mentioned (e.g., "Access Control", "Incident Response", "Data Classification").
Return ONLY a comma-separated list of topics, nothing else.

Policy text:
{policy_text[:3000]}

Topics:"""
        
        response = ollama.generate(model=self.model_name, prompt=prompt)
        topics = [topic.strip() for topic in response['response'].split(',')]
        return topics[:15]  # Limit to top 15 topics
    
    def check_framework_coverage(self, policy_text: str, framework_requirements: List[str]) -> Dict:
        """
        Check which framework requirements are covered using semantic similarity
        
        Returns:
            Dict with 'covered' and 'missing' requirements
        """
        # Create embeddings
        policy_embedding = self.embedding_model.encode([policy_text])[0]
        requirement_embeddings = self.embedding_model.encode(framework_requirements)
        
        # Calculate similarities
        similarities = cosine_similarity(
            [policy_embedding], 
            requirement_embeddings
        )[0]
        
        covered = []
        missing = []
        
        for req, sim in zip(framework_requirements, similarities):
            if sim >= self.similarity_threshold:
                covered.append(req)
            else:
                missing.append((req, sim))
        
        return {
            'covered': covered,
            'missing': missing
        }
    
    def identify_gaps(self, policy_path: str, framework_path: str = None) -> List[PolicyGap]:
        """
        Identify gaps in policy compared to NIST CSF framework
        
        Args:
            policy_path: Path to policy PDF
            framework_path: Path to framework PDF (optional, uses built-in NIST categories)
        
        Returns:
            List of PolicyGap objects
        """
        print("📄 Extracting policy text...")
        policy_text = self.extract_text_from_pdf(policy_path)
        
        print("🔍 Analyzing policy coverage...")
        policy_topics = self.extract_policy_topics(policy_text)
        
        print(f"📊 Found {len(policy_topics)} main topics in policy")
        print(f"Topics: {', '.join(policy_topics[:5])}...")
        
        gaps = []
        
        # Check coverage for each NIST function
        for function, categories in self.nist_framework.items():
            print(f"\n🔎 Analyzing {function} function...")
            
            coverage = self.check_framework_coverage(policy_text, categories)
            
            # Only report significant gaps
            for missing_category, similarity_score in coverage['missing']:
                # Skip if similarity is close to threshold (borderline cases)
                if similarity_score > self.similarity_threshold - 0.15:
                    continue
                
                # Determine severity based on how far below threshold
                if similarity_score < 0.3:
                    severity = "Critical"
                elif similarity_score < 0.5:
                    severity = "High"
                elif similarity_score < 0.6:
                    severity = "Medium"
                else:
                    severity = "Low"
                
                # Generate detailed gap analysis using LLM
                gap_analysis = self._analyze_specific_gap(
                    policy_text, 
                    function, 
                    missing_category,
                    severity
                )
                
                if gap_analysis:
                    gaps.append(gap_analysis)
        
        # Deduplicate similar gaps
        gaps = self._deduplicate_gaps(gaps)
        
        print(f"\n✅ Analysis complete: Found {len(gaps)} significant gaps")
        return gaps
    
    def _analyze_specific_gap(
        self, 
        policy_text: str, 
        function: str, 
        category: str,
        severity: str
    ) -> PolicyGap:
        """Use LLM to analyze a specific gap in detail"""
        
        # Create focused prompt
        prompt = f"""You are analyzing a cybersecurity policy for gaps against NIST Cybersecurity Framework.

NIST CSF Function: {function}
Category: {category}
Severity: {severity}

Policy excerpt (first 2000 chars):
{policy_text[:2000]}

Task: Determine if this policy adequately addresses "{category}" under the {function} function.

Respond in this exact JSON format:
{{
    "gap_exists": true/false,
    "gap_description": "Brief description of what's missing (if gap exists)",
    "recommendation": "Specific actionable recommendation to address gap",
    "framework_reference": "Specific NIST CSF reference"
}}

Be strict: Only report as a gap if there is NO meaningful coverage of this topic in the policy.
JSON response:"""
        
        try:
            response = ollama.generate(model=self.model_name, prompt=prompt)
            result = self._extract_json(response['response'])
            
            if result and result.get('gap_exists', False):
                return PolicyGap(
                    category=category,
                    gap_description=result.get('gap_description', f"Missing {category} controls"),
                    severity=severity,
                    recommendation=result.get('recommendation', f"Implement {category} controls"),
                    framework_reference=result.get('framework_reference', f"NIST CSF - {function}")
                )
        except Exception as e:
            print(f"⚠️  Error analyzing {category}: {str(e)}")
        
        return None
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response"""
        try:
            # Try to find JSON in the response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass
        return None
    
    def _deduplicate_gaps(self, gaps: List[PolicyGap]) -> List[PolicyGap]:
        """Remove duplicate or very similar gaps"""
        if not gaps:
            return gaps
        
        # Create embeddings for gap descriptions
        descriptions = [gap.gap_description for gap in gaps]
        embeddings = self.embedding_model.encode(descriptions)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(embeddings)
        
        # Keep only unique gaps (similarity < 0.8 with all previous gaps)
        unique_gaps = []
        for i, gap in enumerate(gaps):
            is_unique = True
            for j in range(i):
                if similarity_matrix[i][j] > 0.8:
                    is_unique = False
                    break
            if is_unique:
                unique_gaps.append(gap)
        
        return unique_gaps
    
    def save_gaps_as_json(
        self,
        policy_path: str,
        gaps: List[PolicyGap],
        output_path: str
    ) -> None:
        """
        Save identified gaps in structured JSON format
        """
        json_data = {
            "policy_name": os.path.basename(policy_path),
            "analysis_date": __import__('datetime').datetime.now().isoformat(),
            "framework": "NIST Cybersecurity Framework",
            "total_gaps": len(gaps),
            "severity_breakdown": {
                "Critical": len([g for g in gaps if g.severity == "Critical"]),
                "High": len([g for g in gaps if g.severity == "High"]),
                "Medium": len([g for g in gaps if g.severity == "Medium"]),
                "Low": len([g for g in gaps if g.severity == "Low"]),
            },
            "gaps": [
                {
                    "category": g.category,
                    "severity": g.severity,
                    "gap_description": g.gap_description,
                    "recommendation": g.recommendation,
                    "framework_reference": g.framework_reference
                }
                for g in gaps
            ]
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        print(f"🧾 JSON gap output saved to: {output_path}")

    def generate_revised_policy(
        self, 
        policy_path: str, 
        gaps: List[PolicyGap],
        output_path: str = None
    ) -> str:
        """
        Generate a revised policy that addresses identified gaps
        
        Args:
            policy_path: Original policy path
            gaps: List of identified gaps
            output_path: Where to save revised policy (optional)
        
        Returns:
            Revised policy text
        """
        print("\n📝 Generating revised policy...")
        
        original_policy = self.extract_text_from_pdf(policy_path)
        
        # Group gaps by severity
        critical_gaps = [g for g in gaps if g.severity == "Critical"]
        high_gaps = [g for g in gaps if g.severity == "High"]
        
        # Focus on critical and high severity gaps
        priority_gaps = critical_gaps + high_gaps
        
        if not priority_gaps:
            print("✅ No critical or high priority gaps to address")
            return original_policy
        
        # Generate additions for each gap
        additions = []
        for gap in priority_gaps[:10]:  # Limit to top 10 priority gaps
            prompt = f"""Based on this gap in a cybersecurity policy, write a concise policy section to address it.

Gap Category: {gap.category}
Gap Description: {gap.gap_description}
Recommendation: {gap.recommendation}

Write a brief policy section (2-4 sentences) that addresses this gap.
Use formal policy language. Start with a section header.

Policy section:"""
            
            response = ollama.generate(model=self.model_name, prompt=prompt)
            additions.append(f"\n\n### {gap.category}\n{response['response'].strip()}")
        
        # Combine original policy with additions
        revised_policy = original_policy + "\n\n" + "="*50
        revised_policy += "\n## ADDITIONS TO ADDRESS IDENTIFIED GAPS\n"
        revised_policy += "="*50
        revised_policy += "".join(additions)
        
        # Save if output path provided
        if output_path:
            # Ensure parent directory exists
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(revised_policy)
            print(f"💾 Revised policy saved to: {output_path}")
        
        return revised_policy
    
    def generate_improvement_roadmap(self, gaps: List[PolicyGap]) -> Dict:
        """
        Generate a prioritized roadmap for addressing gaps
        
        Returns:
            Dictionary with phased improvement plan
        """
        # Group by severity
        severity_order = ["Critical", "High", "Medium", "Low"]
        roadmap = {
            "Phase 1 (0-3 months) - Critical": [],
            "Phase 2 (3-6 months) - High Priority": [],
            "Phase 3 (6-12 months) - Medium Priority": [],
            "Phase 4 (12+ months) - Low Priority": []
        }
        
        for gap in gaps:
            if gap.severity == "Critical":
                roadmap["Phase 1 (0-3 months) - Critical"].append({
                    "category": gap.category,
                    "action": gap.recommendation,
                    "framework_ref": gap.framework_reference
                })
            elif gap.severity == "High":
                roadmap["Phase 2 (3-6 months) - High Priority"].append({
                    "category": gap.category,
                    "action": gap.recommendation,
                    "framework_ref": gap.framework_reference
                })
            elif gap.severity == "Medium":
                roadmap["Phase 3 (6-12 months) - Medium Priority"].append({
                    "category": gap.category,
                    "action": gap.recommendation,
                    "framework_ref": gap.framework_reference
                })
            else:
                roadmap["Phase 4 (12+ months) - Low Priority"].append({
                    "category": gap.category,
                    "action": gap.recommendation,
                    "framework_ref": gap.framework_reference
                })
        
        return roadmap
    
    def generate_report(
        self, 
        policy_path: str,
        gaps: List[PolicyGap],
        roadmap: Dict,
        output_path: str = "reports/gap_analysis_report.txt"
    ) -> str:
        """Generate a comprehensive gap analysis report"""
        
        report = f"""
{'='*80}
POLICY GAP ANALYSIS REPORT
{'='*80}

Policy Analyzed: {os.path.basename(policy_path)}
Analysis Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Framework: NIST Cybersecurity Framework
Total Gaps Identified: {len(gaps)}

{'='*80}
EXECUTIVE SUMMARY
{'='*80}

Gap Severity Breakdown:
- Critical: {len([g for g in gaps if g.severity == 'Critical'])}
- High:     {len([g for g in gaps if g.severity == 'High'])}
- Medium:   {len([g for g in gaps if g.severity == 'Medium'])}
- Low:      {len([g for g in gaps if g.severity == 'Low'])}

{'='*80}
DETAILED GAP ANALYSIS
{'='*80}
"""
        
        # Group gaps by severity
        for severity in ["Critical", "High", "Medium", "Low"]:
            severity_gaps = [g for g in gaps if g.severity == severity]
            if severity_gaps:
                report += f"\n{severity.upper()} SEVERITY GAPS ({len(severity_gaps)})\n"
                report += "-" * 80 + "\n"
                
                for i, gap in enumerate(severity_gaps, 1):
                    report += f"\n{i}. {gap.category}\n"
                    report += f"   Gap: {gap.gap_description}\n"
                    report += f"   Recommendation: {gap.recommendation}\n"
                    report += f"   Framework Reference: {gap.framework_reference}\n"
        
        # Add roadmap
        report += f"\n\n{'='*80}\n"
        report += "IMPROVEMENT ROADMAP\n"
        report += f"{'='*80}\n"
        
        for phase, items in roadmap.items():
            if items:
                report += f"\n{phase}\n"
                report += "-" * 80 + "\n"
                for item in items:
                    report += f"• {item['category']}: {item['action']}\n"
        
        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📊 Report saved to: {output_path}")
        return report


def main():
    """Main execution function - processes all policies in tests/ folder"""
    import os
    import glob
    
    # Initialize analyzer with balanced threshold
    # Increase threshold (e.g., 0.70) for fewer gaps
    # Decrease threshold (e.g., 0.60) for more gaps
    analyzer = PolicyGapAnalyzer(
        model_name="llama3.2:3b",  # Change to your preferred local model
        similarity_threshold=0.65   # Balanced threshold
    )
    
    # Find all policy files in tests/ folder
    policy_files = []
    for ext in ['*.txt', '*.pdf', '*.md']:
        policy_files.extend(glob.glob(os.path.join("tests", ext)))
    
    if not policy_files:
        print("❌ No policy files found in tests/ folder")
        print("   Looking for: .txt, .pdf, .md files")
        return
    
    print("="*80)
    print("🚀 BATCH POLICY GAP ANALYSIS")
    print("="*80)
    print(f"📌 Similarity Threshold: {analyzer.similarity_threshold}")
    print(f"📌 Higher threshold = stricter = more gaps")
    print(f"📌 Lower threshold = lenient = fewer gaps")
    print(f"📄 Policies Found: {len(policy_files)}\n")
    
    # Process each policy
    for i, policy_path in enumerate(policy_files, 1):
        # Extract policy name (without extension)
        policy_name = os.path.splitext(os.path.basename(policy_path))[0]
        
        # Create output folder for this policy
        output_folder = os.path.join("reports", policy_name)
        os.makedirs(output_folder, exist_ok=True)
        
        print("\n" + "="*80)
        print(f"📄 [{i}/{len(policy_files)}] Analyzing: {os.path.basename(policy_path)}")
        print(f"📁 Output Folder: {output_folder}")
        print("="*80)
        
        try:
            # Step 1: Identify gaps
            print("🔍 Identifying gaps...")
            gaps = analyzer.identify_gaps(policy_path)
            
            # Step 2: Generate improvement roadmap
            print("🗺️  Generating roadmap...")
            roadmap = analyzer.generate_improvement_roadmap(gaps)
            
            # Step 3: Generate revised policy
            print("📝 Generating revised policy...")
            revised_policy = analyzer.generate_revised_policy(
                policy_path,
                gaps,
                output_path=os.path.join(output_folder, "revised_policy.txt")
            )
            
            # Step 4: Generate comprehensive report
            print("📊 Generating analysis report...")
            report = analyzer.generate_report(
                policy_path,
                gaps,
                roadmap,
                output_path=os.path.join(output_folder, "gap_analysis.txt")
            )
            # Step 5: Save gaps as JSON
            analyzer.save_gaps_as_json(
            policy_path,
            gaps,
            output_path=os.path.join(output_folder, "gaps.json")
            )

            
            print("\n" + "-"*80)
            print(f"✅ ANALYSIS COMPLETE FOR: {policy_name}")
            print("-"*80)
            print(f"📊 Total Gaps: {len(gaps)}")
            print(f"🔴 Critical: {len([g for g in gaps if g.severity == 'Critical'])}")
            print(f"🟠 High: {len([g for g in gaps if g.severity == 'High'])}")
            print(f"🟡 Medium: {len([g for g in gaps if g.severity == 'Medium'])}")
            print(f"🟢 Low: {len([g for g in gaps if g.severity == 'Low'])}")
            print(f"\n📁 Output folder: {output_folder}/")
            print(f"   - gap_analysis.txt")
            print(f"   - revised_policy.txt")
            
        except Exception as e:
            print(f"\n❌ Error analyzing {policy_name}: {str(e)}")
            continue
    
    print("\n\n" + "="*80)
    print("✅ ALL POLICIES ANALYZED")
    print("="*80)
    print(f"📁 Results saved in reports/ folder")
    print(f"   Each policy has its own subfolder with 3 output files")
    print("="*80)
    

if __name__ == "__main__":
    main()
