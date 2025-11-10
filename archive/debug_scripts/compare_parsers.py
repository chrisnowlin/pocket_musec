"""
Comprehensive parser comparison script
Compares vision, table-based, and hybrid parsers for accuracy and completeness
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

from backend.ingestion.standards_parser import NCStandardsParser as VisionParser
from backend.ingestion.standards_parser_table import NCStandardsParser as TableParser
from backend.ingestion.standards_parser_hybrid import NCStandardsParser as HybridParser


@dataclass
class ParserResult:
    """Results from a parser run"""
    parser_name: str
    total_standards: int
    total_objectives: int
    avg_objectives_per_standard: float
    parse_time_seconds: float
    grade_distribution: Dict[str, int]
    strand_distribution: Dict[str, int]
    standards: List[Any]  # List of parsed standards
    

@dataclass
class ComparisonMetrics:
    """Metrics comparing parser results"""
    standards_count_diff: Dict[str, int]
    objectives_count_diff: Dict[str, int]
    unique_to_parser: Dict[str, List[str]]  # Standard IDs unique to each parser
    common_standards: List[str]  # Standard IDs found by all parsers
    text_differences: List[Dict[str, Any]]  # Text differences for common standards


def run_parser(parser_class, parser_name: str, pdf_path: str, **kwargs) -> ParserResult:
    """Run a parser and collect results"""
    print(f"\n{'='*80}")
    print(f"Running {parser_name}")
    print(f"{'='*80}")
    
    start_time = time.time()
    parser = parser_class()
    
    # Parse document
    parsed_standards = parser.parse_standards_document(pdf_path, **kwargs)
    
    parse_time = time.time() - start_time
    
    # Calculate statistics
    total_objectives = sum(len(std.objectives) for std in parsed_standards)
    avg_objectives = total_objectives / len(parsed_standards) if parsed_standards else 0
    
    # Distribution by grade
    grade_dist = defaultdict(int)
    for std in parsed_standards:
        grade_dist[std.grade_level] += 1
    
    # Distribution by strand
    strand_dist = defaultdict(int)
    for std in parsed_standards:
        strand_dist[std.strand_code] += 1
    
    result = ParserResult(
        parser_name=parser_name,
        total_standards=len(parsed_standards),
        total_objectives=total_objectives,
        avg_objectives_per_standard=avg_objectives,
        parse_time_seconds=parse_time,
        grade_distribution=dict(grade_dist),
        strand_distribution=dict(strand_dist),
        standards=parsed_standards
    )
    
    # Print summary
    print(f"\n✓ Completed in {parse_time:.2f} seconds")
    print(f"  • Standards: {result.total_standards}")
    print(f"  • Objectives: {result.total_objectives}")
    print(f"  • Avg objectives/standard: {result.avg_objectives_per_standard:.2f}")
    print(f"\n  Grade distribution:")
    for grade in sorted(grade_dist.keys()):
        print(f"    {grade}: {grade_dist[grade]}")
    print(f"\n  Strand distribution:")
    for strand in sorted(strand_dist.keys()):
        print(f"    {strand}: {strand_dist[strand]}")
    
    return result


def compare_results(results: List[ParserResult]) -> ComparisonMetrics:
    """Compare results from multiple parsers"""
    print(f"\n{'='*80}")
    print("COMPARISON ANALYSIS")
    print(f"{'='*80}")
    
    # Create lookup by standard ID for each parser
    parser_standards = {}
    for result in results:
        parser_standards[result.parser_name] = {
            std.standard_id: std for std in result.standards
        }
    
    # Find all unique standard IDs across all parsers
    all_standard_ids = set()
    for standards in parser_standards.values():
        all_standard_ids.update(standards.keys())
    
    # Find common and unique standards
    common_standards = set(all_standard_ids)
    for standards in parser_standards.values():
        common_standards &= set(standards.keys())
    
    unique_to_parser = {}
    for parser_name, standards in parser_standards.items():
        parser_ids = set(standards.keys())
        other_ids = set()
        for other_name, other_standards in parser_standards.items():
            if other_name != parser_name:
                other_ids.update(other_standards.keys())
        unique_to_parser[parser_name] = sorted(list(parser_ids - other_ids))
    
    # Compare standard text for common standards
    text_differences = []
    for std_id in sorted(common_standards):
        texts = {}
        objectives_counts = {}
        
        for parser_name, standards in parser_standards.items():
            if std_id in standards:
                std = standards[std_id]
                texts[parser_name] = std.standard_text
                objectives_counts[parser_name] = len(std.objectives)
        
        # Check if texts differ
        unique_texts = set(texts.values())
        if len(unique_texts) > 1 or len(set(objectives_counts.values())) > 1:
            text_differences.append({
                'standard_id': std_id,
                'texts': texts,
                'objectives_counts': objectives_counts
            })
    
    # Count differences
    standards_count_diff = {
        result.parser_name: result.total_standards 
        for result in results
    }
    
    objectives_count_diff = {
        result.parser_name: result.total_objectives 
        for result in results
    }
    
    metrics = ComparisonMetrics(
        standards_count_diff=standards_count_diff,
        objectives_count_diff=objectives_count_diff,
        unique_to_parser=unique_to_parser,
        common_standards=sorted(list(common_standards)),
        text_differences=text_differences
    )
    
    # Print comparison summary
    print(f"\n📊 Summary:")
    print(f"  • Total unique standard IDs: {len(all_standard_ids)}")
    print(f"  • Common to all parsers: {len(common_standards)}")
    print(f"  • Standards with text differences: {len(text_differences)}")
    
    print(f"\n📈 Standards count by parser:")
    for parser_name, count in standards_count_diff.items():
        print(f"  • {parser_name}: {count}")
    
    print(f"\n📈 Objectives count by parser:")
    for parser_name, count in objectives_count_diff.items():
        print(f"  • {parser_name}: {count}")
    
    print(f"\n🔍 Unique standards per parser:")
    for parser_name, unique_ids in unique_to_parser.items():
        print(f"  • {parser_name}: {len(unique_ids)} unique")
        if unique_ids and len(unique_ids) <= 10:
            print(f"    {', '.join(unique_ids)}")
    
    return metrics


def save_detailed_report(results: List[ParserResult], metrics: ComparisonMetrics, output_file: str):
    """Save detailed comparison report"""
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'parser_results': [
            {
                'parser_name': r.parser_name,
                'total_standards': r.total_standards,
                'total_objectives': r.total_objectives,
                'avg_objectives_per_standard': r.avg_objectives_per_standard,
                'parse_time_seconds': r.parse_time_seconds,
                'grade_distribution': r.grade_distribution,
                'strand_distribution': r.strand_distribution,
            }
            for r in results
        ],
        'comparison_metrics': {
            'standards_count_diff': metrics.standards_count_diff,
            'objectives_count_diff': metrics.objectives_count_diff,
            'total_common_standards': len(metrics.common_standards),
            'unique_standards_per_parser': {
                parser: len(ids) for parser, ids in metrics.unique_to_parser.items()
            },
            'text_differences_count': len(metrics.text_differences)
        },
        'unique_standards': metrics.unique_to_parser,
        'text_differences': metrics.text_differences[:20]  # First 20 for brevity
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {output_file}")


def analyze_text_quality(metrics: ComparisonMetrics, results: List[ParserResult]):
    """Analyze text quality differences"""
    print(f"\n{'='*80}")
    print("TEXT QUALITY ANALYSIS")
    print(f"{'='*80}")
    
    if not metrics.text_differences:
        print("\n✓ All parsers produced identical text for common standards!")
        return
    
    print(f"\n⚠️  Found {len(metrics.text_differences)} standards with differences")
    print(f"\nShowing first 5 differences:\n")
    
    # Create parser lookup
    parser_standards = {}
    for result in results:
        parser_standards[result.parser_name] = {
            std.standard_id: std for std in result.standards
        }
    
    for i, diff in enumerate(metrics.text_differences[:5], 1):
        std_id = diff['standard_id']
        print(f"{i}. {std_id}")
        print(f"   Objectives count: {diff['objectives_counts']}")
        
        for parser_name, text in diff['texts'].items():
            print(f"\n   [{parser_name}]")
            print(f"   {text[:150]}...")
            
            # Show objectives count
            std = parser_standards[parser_name][std_id]
            print(f"   Objectives: {len(std.objectives)}")
            if std.objectives:
                print(f"   First objective: {std.objectives[0][:100]}...")
        
        print()


def main():
    pdf_path = "NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf"
    
    print(f"{'='*80}")
    print("COMPREHENSIVE PARSER COMPARISON")
    print(f"{'='*80}")
    print(f"\nPDF: {pdf_path}")
    print(f"Target: General Music Standards (pages 1-34)")
    print(f"\nParsers to compare:")
    print(f"  1. Vision Parser (Qwen VL - slow but accurate)")
    print(f"  2. Table Parser (fast, structure-aware)")
    print(f"  3. Hybrid Parser (fallback, text-based)")
    
    # Collect results
    results = []
    
    # Run table parser first (fast baseline)
    results.append(run_parser(
        TableParser,
        "Table Parser",
        pdf_path,
        max_page=34
    ))
    
    # Run hybrid parser
    results.append(run_parser(
        HybridParser,
        "Hybrid Parser",
        pdf_path
    ))
    
    # Run vision parser (slow)
    print(f"\n⚠️  Vision parser will take 5-10 minutes...")
    results.append(run_parser(
        VisionParser,
        "Vision Parser",
        pdf_path
    ))
    
    # Compare results
    metrics = compare_results(results)
    
    # Analyze text quality
    analyze_text_quality(metrics, results)
    
    # Save detailed report
    output_file = "parser_comparison_report.json"
    save_detailed_report(results, metrics, output_file)
    
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS")
    print(f"{'='*80}")
    
    # Determine best parser based on metrics
    best_parser = max(results, key=lambda r: r.total_standards)
    print(f"\n🏆 Most complete: {best_parser.parser_name}")
    print(f"   ({best_parser.total_standards} standards, {best_parser.total_objectives} objectives)")
    
    fastest_parser = min(results, key=lambda r: r.parse_time_seconds)
    print(f"\n⚡ Fastest: {fastest_parser.parser_name}")
    print(f"   ({fastest_parser.parse_time_seconds:.2f} seconds)")
    
    if metrics.text_differences:
        print(f"\n⚠️  Text quality issues detected:")
        print(f"   {len(metrics.text_differences)} standards have differing text")
        print(f"   Review detailed report for analysis")
    else:
        print(f"\n✓ Text quality: All parsers agree on common standards")


if __name__ == "__main__":
    main()
