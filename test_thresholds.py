"""
Test script to compare different similarity thresholds
This helps you find the optimal threshold for your use case
"""

from policy_gap_analyzer import PolicyGapAnalyzer
import sys


def test_different_thresholds(policy_path: str):
    """
    Test the same policy with different thresholds to find optimal setting
    """
    
    thresholds = [0.55, 0.60, 0.65, 0.70, 0.75]
    
    print("="*80)
    print("THRESHOLD COMPARISON TEST")
    print("="*80)
    print(f"Policy: {policy_path}\n")
    
    results = []
    
    for threshold in thresholds:
        print(f"\n{'='*80}")
        print(f"Testing with threshold: {threshold}")
        print(f"{'='*80}\n")
        
        analyzer = PolicyGapAnalyzer(
            model_name="llama3.2:3b",
            similarity_threshold=threshold
        )
        
        try:
            gaps = analyzer.identify_gaps(policy_path)
            
            gap_counts = {
                'total': len(gaps),
                'critical': len([g for g in gaps if g.severity == 'Critical']),
                'high': len([g for g in gaps if g.severity == 'High']),
                'medium': len([g for g in gaps if g.severity == 'Medium']),
                'low': len([g for g in gaps if g.severity == 'Low'])
            }
            
            results.append({
                'threshold': threshold,
                'counts': gap_counts
            })
            
            print(f"\n📊 Results for threshold {threshold}:")
            print(f"   Total Gaps: {gap_counts['total']}")
            print(f"   Critical: {gap_counts['critical']}")
            print(f"   High: {gap_counts['high']}")
            print(f"   Medium: {gap_counts['medium']}")
            print(f"   Low: {gap_counts['low']}")
            
        except Exception as e:
            print(f"❌ Error with threshold {threshold}: {str(e)}")
    
    # Print summary
    print("\n\n" + "="*80)
    print("SUMMARY - THRESHOLD COMPARISON")
    print("="*80)
    print(f"\n{'Threshold':<12} {'Total':<8} {'Critical':<10} {'High':<8} {'Medium':<8} {'Low':<8}")
    print("-"*80)
    
    for result in results:
        t = result['threshold']
        c = result['counts']
        print(f"{t:<12.2f} {c['total']:<8} {c['critical']:<10} {c['high']:<8} {c['medium']:<8} {c['low']:<8}")
    
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    # Find optimal threshold (aiming for 20-50 total gaps)
    optimal = None
    for result in results:
        total = result['counts']['total']
        if 20 <= total <= 50:
            optimal = result['threshold']
            break
    
    if optimal:
        print(f"\n✅ Recommended threshold: {optimal}")
        print(f"   This gives a balanced {[r['counts']['total'] for r in results if r['threshold']==optimal][0]} gaps")
    else:
        # Find closest to 35 (midpoint of 20-50)
        closest = min(results, key=lambda x: abs(x['counts']['total'] - 35))
        print(f"\n💡 Suggested threshold: {closest['threshold']}")
        print(f"   Closest to optimal range with {closest['counts']['total']} gaps")
    
    print("\n📌 Interpretation:")
    print("   • 0.55-0.60: Lenient (good for initial assessment)")
    print("   • 0.65-0.70: Balanced (recommended for most use cases)")
    print("   • 0.70-0.75: Strict (comprehensive compliance audit)")
    print()


def quick_test(policy_path: str, threshold: float = 0.65):
    """
    Quick single test with specified threshold
    """
    print("="*80)
    print(f"QUICK TEST - Threshold: {threshold}")
    print("="*80)
    
    analyzer = PolicyGapAnalyzer(
        model_name="llama3.2:3b",
        similarity_threshold=threshold
    )
    
    gaps = analyzer.identify_gaps(policy_path)
    roadmap = analyzer.generate_improvement_roadmap(gaps)
    
    analyzer.generate_report(
        policy_path,
        gaps,
        roadmap,
        output_path=f"quick_test_report_t{threshold}.txt"
    )
    
    print(f"\n✅ Test complete!")
    print(f"   Total gaps: {len(gaps)}")
    print(f"   Report saved to: quick_test_report_t{threshold}.txt")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_thresholds.py <policy_path>                    # Compare all thresholds")
        print("  python test_thresholds.py <policy_path> <threshold>        # Quick test with specific threshold")
        print("\nExample:")
        print("  python test_thresholds.py test_policies/isms_policy.pdf")
        print("  python test_thresholds.py test_policies/isms_policy.pdf 0.65")
        sys.exit(1)
    
    policy_path = sys.argv[1]
    
    if len(sys.argv) == 3:
        # Quick test with specified threshold
        threshold = float(sys.argv[2])
        quick_test(policy_path, threshold)
    else:
        # Compare multiple thresholds
        test_different_thresholds(policy_path)
