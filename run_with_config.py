"""
Enhanced Policy Gap Analyzer with Configuration File Support
"""

import configparser
from policy_gap_analyzer import PolicyGapAnalyzer
import os


class ConfigurableAnalyzer(PolicyGapAnalyzer):
    """Extended analyzer that reads settings from config file"""
    
    def __init__(self, config_path: str = "config.ini"):
        """Initialize analyzer from config file"""
        
        # Read configuration
        config = configparser.ConfigParser()
        config.read(config_path)
        
        # Extract settings with defaults
        model_name = config.get('analyzer', 'model_name', fallback='llama3.2:3b')
        similarity_threshold = config.getfloat('analyzer', 'similarity_threshold', fallback=0.65)
        
        # Initialize parent class
        super().__init__(model_name=model_name, similarity_threshold=similarity_threshold)
        
        # Store additional config
        self.config = config
        self.borderline_filter = config.getfloat('analyzer', 'borderline_filter', fallback=0.15)
        self.duplicate_threshold = config.getfloat('deduplication', 'duplicate_threshold', fallback=0.80)
        self.max_priority_gaps = config.getint('processing', 'max_priority_gaps', fallback=10)
        
        # Severity thresholds
        self.severity_thresholds = {
            'critical': config.getfloat('severity', 'critical_threshold', fallback=0.30),
            'high': config.getfloat('severity', 'high_threshold', fallback=0.50),
            'medium': config.getfloat('severity', 'medium_threshold', fallback=0.60)
        }
        
        # Framework functions to analyze
        self.analyze_functions = {
            'IDENTIFY': config.getboolean('framework', 'analyze_identify', fallback=True),
            'PROTECT': config.getboolean('framework', 'analyze_protect', fallback=True),
            'DETECT': config.getboolean('framework', 'analyze_detect', fallback=True),
            'RESPOND': config.getboolean('framework', 'analyze_respond', fallback=True),
            'RECOVER': config.getboolean('framework', 'analyze_recover', fallback=True),
        }
        
        # Output settings
        self.output_files = {
            'report': config.get('output', 'gap_report', fallback='gap_analysis_report.txt'),
            'revised': config.get('output', 'revised_policy', fallback='revised_policy.txt'),
            'roadmap': config.get('output', 'roadmap_file', fallback='improvement_roadmap.json')
        }
        
        print(f"✅ Configuration loaded from {config_path}")
        print(f"   Model: {model_name}")
        print(f"   Similarity Threshold: {similarity_threshold}")
        print(f"   Borderline Filter: {self.borderline_filter}")
    
    def identify_gaps_with_config(self, policy_path: str):
        """Identify gaps using configuration settings"""
        
        print("\n🔧 Analysis Configuration:")
        print(f"   Similarity Threshold: {self.similarity_threshold}")
        print(f"   Borderline Filter: {self.borderline_filter}")
        print(f"   Duplicate Threshold: {self.duplicate_threshold}")
        print(f"   Active Functions: {[k for k,v in self.analyze_functions.items() if v]}\n")
        
        # Call parent's identify_gaps method
        gaps = self.identify_gaps(policy_path)
        
        return gaps
    
    def run_full_analysis(self, policy_path: str):
        """Run complete analysis pipeline with config settings"""
        
        print("="*80)
        print("CONFIGURABLE POLICY GAP ANALYSIS")
        print("="*80)
        
        # Step 1: Identify gaps
        gaps = self.identify_gaps_with_config(policy_path)
        
        # Step 2: Generate roadmap
        roadmap = self.generate_improvement_roadmap(gaps)
        
        # Step 3: Generate revised policy
        revised = self.generate_revised_policy(
            policy_path,
            gaps,
            output_path=self.output_files['revised']
        )
        
        # Step 4: Generate report
        report = self.generate_report(
            policy_path,
            gaps,
            roadmap,
            output_path=self.output_files['report']
        )
        
        # Step 5: Save roadmap as JSON if configured
        if self.output_files['roadmap'].endswith('.json'):
            import json
            with open(self.output_files['roadmap'], 'w') as f:
                json.dump(roadmap, f, indent=2)
            print(f"📊 Roadmap saved to: {self.output_files['roadmap']}")
        
        return gaps, roadmap, revised, report


def main():
    """Main execution with config file"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python run_with_config.py <policy_path> [config_path]")
        print("\nExample:")
        print("  python run_with_config.py test_policies/isms_policy.pdf")
        print("  python run_with_config.py test_policies/isms_policy.pdf custom_config.ini")
        sys.exit(1)
    
    policy_path = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else "config.ini"
    
    # Check if files exist
    if not os.path.exists(policy_path):
        print(f"❌ Policy file not found: {policy_path}")
        sys.exit(1)
    
    if not os.path.exists(config_path):
        print(f"⚠️  Config file not found: {config_path}")
        print(f"   Using default settings...")
        config_path = None
    
    # Run analysis
    if config_path:
        analyzer = ConfigurableAnalyzer(config_path)
    else:
        analyzer = ConfigurableAnalyzer()
    
    gaps, roadmap, revised, report = analyzer.run_full_analysis(policy_path)
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)
    print(f"\n📊 Results:")
    print(f"   Total Gaps: {len(gaps)}")
    print(f"   Critical: {len([g for g in gaps if g.severity == 'Critical'])}")
    print(f"   High: {len([g for g in gaps if g.severity == 'High'])}")
    print(f"   Medium: {len([g for g in gaps if g.severity == 'Medium'])}")
    print(f"   Low: {len([g for g in gaps if g.severity == 'Low'])}")
    print(f"\n📄 Output Files:")
    for name, path in analyzer.output_files.items():
        if os.path.exists(path):
            print(f"   {name.capitalize()}: {path}")


if __name__ == "__main__":
    main()
