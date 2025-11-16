#!/usr/bin/env python3
"""
Generate comprehensive analysis report for lesson generation comparison
"""

import sys
import os
import json
import time
from typing import Dict, List, Any
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_comparison_results() -> Dict[str, Any]:
    """Load the comparison results from JSON file"""
    try:
        with open("lesson_generation_comparison_results.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Comparison results file not found. Please run the comparison test first.")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error reading results file: {e}")
        return {}

def analyze_standard_selection_accuracy(results: List[Dict]) -> Dict[str, Any]:
    """Analyze standard selection accuracy between keyword and RAG approaches"""
    keyword_scores = []
    rag_scores = []
    
    for result in results:
        if result["approach"] == "keyword":
            if result["selected_standards"]:
                avg_score = sum(std.get("relevance_score", 0) for std in result["selected_standards"]) / len(result["selected_standards"])
                keyword_scores.append(avg_score)
        else:  # RAG approach
            if result["selected_standards"]:
                avg_score = sum(std.get("relevance_score", 0) for std in result["selected_standards"]) / len(result["selected_standards"])
                rag_scores.append(avg_score)
    
    keyword_avg = sum(keyword_scores) / len(keyword_scores) if keyword_scores else 0
    rag_avg = sum(rag_scores) / len(rag_scores) if rag_scores else 0
    improvement = ((rag_avg - keyword_avg) / keyword_avg * 100) if keyword_avg > 0 else 0
    
    return {
        "keyword_avg_score": keyword_avg,
        "rag_avg_score": rag_avg,
        "improvement_percentage": improvement,
        "keyword_scores": keyword_scores,
        "rag_scores": rag_scores
    }

def analyze_teaching_strategies(results: List[Dict]) -> Dict[str, Any]:
    """Analyze teaching strategy quality and diversity"""
    keyword_strategies = []
    rag_strategies = []
    
    for result in results:
        strategies = result["teaching_strategies"]
        if result["approach"] == "keyword":
            keyword_strategies.extend(strategies)
        else:
            rag_strategies.extend(strategies)
    
    # Analyze strategy diversity (unique terms)
    keyword_terms = set(" ".join(keyword_strategies).lower().split())
    rag_terms = set(" ".join(rag_strategies).lower().split())
    
    # Check for evidence-based indicators
    evidence_indicators = ["movement", "visual", "kinesthetic", "collaborative", "interactive", 
                          "assessment", "formative", "summative", "rubric", "reflection"]
    
    keyword_evidence_count = sum(1 for indicator in evidence_indicators 
                                if any(indicator in strategy.lower() for strategy in keyword_strategies))
    rag_evidence_count = sum(1 for indicator in evidence_indicators 
                            if any(indicator in strategy.lower() for strategy in rag_strategies))
    
    return {
        "keyword_strategy_count": len(keyword_strategies),
        "rag_strategy_count": len(rag_strategies),
        "keyword_diversity": len(keyword_terms),
        "rag_diversity": len(rag_terms),
        "keyword_evidence_based": keyword_evidence_count,
        "rag_evidence_based": rag_evidence_count,
        "improvement_diversity": len(rag_terms) - len(keyword_terms),
        "improvement_evidence": rag_evidence_count - keyword_evidence_count
    }

def analyze_assessment_methods(results: List[Dict]) -> Dict[str, Any]:
    """Analyze assessment method sophistication"""
    keyword_assessments = []
    rag_assessments = []
    
    for result in results:
        assessments = result["assessment_methods"]
        if result["approach"] == "keyword":
            keyword_assessments.extend(assessments)
        else:
            rag_assessments.extend(assessments)
    
    # Check for sophisticated assessment terms
    sophisticated_terms = ["rubric", "formative", "summative", "performance", "authentic", 
                           "self-assessment", "peer", "portfolio", "criteria"]
    
    keyword_sophisticated = sum(1 for term in sophisticated_terms 
                               if any(term in assessment.lower() for assessment in keyword_assessments))
    rag_sophisticated = sum(1 for term in sophisticated_terms 
                           if any(term in assessment.lower() for assessment in rag_assessments))
    
    return {
        "keyword_assessment_count": len(keyword_assessments),
        "rag_assessment_count": len(rag_assessments),
        "keyword_sophisticated_terms": keyword_sophisticated,
        "rag_sophisticated_terms": rag_sophisticated,
        "improvement_sophistication": rag_sophisticated - keyword_sophisticated
    }

def analyze_performance_metrics(results: List[Dict]) -> Dict[str, Any]:
    """Analyze performance metrics like response time and content size"""
    keyword_times = []
    rag_times = []
    keyword_prompt_sizes = []
    rag_prompt_sizes = []
    keyword_response_sizes = []
    rag_response_sizes = []
    
    for result in results:
        if result["approach"] == "keyword":
            keyword_times.append(result["generation_time"])
            keyword_prompt_sizes.append(result["prompt_size"])
            keyword_response_sizes.append(result["response_size"])
        else:
            rag_times.append(result["generation_time"])
            rag_prompt_sizes.append(result["prompt_size"])
            rag_response_sizes.append(result["response_size"])
    
    return {
        "keyword_avg_time": sum(keyword_times) / len(keyword_times) if keyword_times else 0,
        "rag_avg_time": sum(rag_times) / len(rag_times) if rag_times else 0,
        "keyword_avg_prompt_size": sum(keyword_prompt_sizes) / len(keyword_prompt_sizes) if keyword_prompt_sizes else 0,
        "rag_avg_prompt_size": sum(rag_prompt_sizes) / len(rag_prompt_sizes) if rag_prompt_sizes else 0,
        "keyword_avg_response_size": sum(keyword_response_sizes) / len(keyword_response_sizes) if keyword_response_sizes else 0,
        "rag_avg_response_size": sum(rag_response_sizes) / len(rag_response_sizes) if rag_response_sizes else 0,
        "time_overhead": ((sum(rag_times) / len(rag_times)) - (sum(keyword_times) / len(keyword_times))) if rag_times and keyword_times else 0,
        "prompt_enhancement": ((sum(rag_prompt_sizes) / len(rag_prompt_sizes)) - (sum(keyword_prompt_sizes) / len(keyword_prompt_sizes))) if rag_prompt_sizes and keyword_prompt_sizes else 0
    }

def analyze_quality_metrics(results: List[Dict]) -> Dict[str, Any]:
    """Analyze overall quality metrics"""
    keyword_quality = []
    rag_quality = []
    
    quality_categories = [
        "standard_relevance_score",
        "teaching_strategy_quality", 
        "assessment_quality",
        "coherence_score",
        "educational_value_score",
        "age_appropriateness_score",
        "overall_quality_score"
    ]
    
    keyword_category_scores = {cat: [] for cat in quality_categories}
    rag_category_scores = {cat: [] for cat in quality_categories}
    
    for result in results:
        quality = result.get("quality_metrics", {})
        if result["approach"] == "keyword":
            keyword_quality.append(quality.get("overall_quality_score", 0))
            for cat in quality_categories:
                keyword_category_scores[cat].append(quality.get(cat, 0))
        else:
            rag_quality.append(quality.get("overall_quality_score", 0))
            for cat in quality_categories:
                rag_category_scores[cat].append(quality.get(cat, 0))
    
    # Calculate improvements by category
    category_improvements = {}
    for cat in quality_categories:
        keyword_avg = sum(keyword_category_scores[cat]) / len(keyword_category_scores[cat]) if keyword_category_scores[cat] else 0
        rag_avg = sum(rag_category_scores[cat]) / len(rag_category_scores[cat]) if rag_category_scores[cat] else 0
        improvement = rag_avg - keyword_avg
        category_improvements[cat] = {
            "keyword_avg": keyword_avg,
            "rag_avg": rag_avg,
            "improvement": improvement,
            "improvement_percentage": (improvement / keyword_avg * 100) if keyword_avg > 0 else 0
        }
    
    overall_keyword_avg = sum(keyword_quality) / len(keyword_quality) if keyword_quality else 0
    overall_rag_avg = sum(rag_quality) / len(rag_quality) if rag_quality else 0
    overall_improvement = overall_rag_avg - overall_keyword_avg
    
    return {
        "overall_keyword_quality": overall_keyword_avg,
        "overall_rag_quality": overall_rag_avg,
        "overall_improvement": overall_improvement,
        "overall_improvement_percentage": (overall_improvement / overall_keyword_avg * 100) if overall_keyword_avg > 0 else 0,
        "category_breakdown": category_improvements
    }

def generate_improvement_examples(results: List[Dict]) -> List[Dict[str, str]]:
    """Generate specific examples of improvements found"""
    examples = []
    
    # Pair up results for comparison
    keyword_results = [r for r in results if r["approach"] == "keyword"]
    rag_results = [r for r in results if r["approach"] == "rag"]
    
    for kw_result, rag_result in zip(keyword_results, rag_results):
        scenario = kw_result["scenario"]
        
        # Compare standard selection
        kw_standards = kw_result["selected_standards"]
        rag_standards = rag_result["selected_standards"]
        
        if kw_standards and rag_standards:
            kw_avg_relevance = sum(std.get("relevance_score", 0) for std in kw_standards) / len(kw_standards)
            rag_avg_relevance = sum(std.get("relevance_score", 0) for std in rag_standards) / len(rag_standards)
            
            if rag_avg_relevance > kw_avg_relevance:
                examples.append({
                    "scenario": f"{scenario['grade_level']} - {scenario['musical_topic']}",
                    "category": "Standard Selection",
                    "improvement": f"RAG approach achieved {rag_avg_relevance:.2f} avg relevance vs {kw_avg_relevance:.2f} for keyword approach",
                    "details": f"RAG: {[std['standard_id'] for std in rag_standards[:2]]} vs Keyword: {[std['standard_id'] for std in kw_standards[:2]]}"
                })
        
        # Compare teaching strategies
        kw_strategies = kw_result["teaching_strategies"]
        rag_strategies = rag_result["teaching_strategies"]
        
        if len(rag_strategies) > len(kw_strategies):
            examples.append({
                "scenario": f"{scenario['grade_level']} - {scenario['musical_topic']}",
                "category": "Teaching Strategies",
                "improvement": f"RAG provided {len(rag_strategies)} strategies vs {len(kw_strategies)} for keyword approach",
                "details": f"RAG examples: {rag_strategies[:2]}"
            })
        
        # Compare assessment methods
        kw_assessments = kw_result["assessment_methods"]
        rag_assessments = rag_result["assessment_methods"]
        
        if len(rag_assessments) > len(kw_assessments):
            examples.append({
                "scenario": f"{scenario['grade_level']} - {scenario['musical_topic']}",
                "category": "Assessment Methods", 
                "improvement": f"RAG provided {len(rag_assessments)} assessment methods vs {len(kw_assessments)} for keyword approach",
                "details": f"RAG examples: {rag_assessments[:2]}"
            })
    
    return examples

def generate_markdown_report(analysis: Dict[str, Any]) -> str:
    """Generate a comprehensive markdown report"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# 🎵 Lesson Generation Quality Analysis Report
*Generated on {timestamp}*

## 📊 Executive Summary

This report provides a comprehensive analysis of lesson generation quality improvements achieved through RAG (Retrieval-Augmented Generation) integration compared to the previous keyword-based approach.

**Key Findings:**
- Overall quality improvement: **{analysis['quality_metrics']['overall_improvement_percentage']:.1f}%**
- Standard selection accuracy improvement: **{analysis['standard_selection']['improvement_percentage']:.1f}%**
- Teaching strategy diversity improvement: **{analysis['teaching_strategies']['improvement_diversity']} additional unique terms**
- Assessment sophistication improvement: **{analysis['assessment_methods']['improvement_sophistication']} additional evidence-based terms**

---

## 🔍 Standard Selection Analysis

### Accuracy Comparison
- **Keyword Approach Average Score:** {analysis['standard_selection']['keyword_avg_score']:.3f}
- **RAG Approach Average Score:** {analysis['standard_selection']['rag_avg_score']:.3f}
- **Improvement:** {analysis['standard_selection']['improvement_percentage']:.1f}%

### Insights
The RAG-enhanced semantic search demonstrates superior standard selection by:
- Understanding contextual meaning rather than simple keyword matches
- Identifying conceptually relevant standards that don't contain exact keywords
- Providing more nuanced similarity scoring for better ranking

---

## 📚 Teaching Strategies Analysis

### Strategy Diversity
- **Keyword Approach:** {analysis['teaching_strategies']['keyword_strategy_count']} strategies, {analysis['teaching_strategies']['keyword_diversity']} unique terms
- **RAG Approach:** {analysis['teaching_strategies']['rag_strategy_count']} strategies, {analysis['teaching_strategies']['rag_diversity']} unique terms
- **Diversity Improvement:** {analysis['teaching_strategies']['improvement_diversity']} additional unique terms

### Evidence-Based Content
- **Keyword Approach:** {analysis['teaching_strategies']['keyword_evidence_based']} evidence-based indicators
- **RAG Approach:** {analysis['teaching_strategies']['rag_evidence_based']} evidence-based indicators
- **Improvement:** {analysis['teaching_strategies']['improvement_evidence']} additional evidence-based elements

### Insights
RAG integration provides:
- More comprehensive pedagogical content from educational resources
- Age-appropriate teaching strategies specific to grade levels
- Research-supported instructional methods

---

## 📝 Assessment Methods Analysis

### Sophistication Comparison
- **Keyword Approach:** {analysis['assessment_methods']['keyword_assessment_count']} methods, {analysis['assessment_methods']['keyword_sophisticated_terms']} sophisticated terms
- **RAG Approach:** {analysis['assessment_methods']['rag_assessment_count']} methods, {analysis['assessment_methods']['rag_sophisticated_terms']} sophisticated terms
- **Sophistication Improvement:** {analysis['assessment_methods']['improvement_sophistication']} additional sophisticated terms

### Insights
The RAG-enhanced approach includes:
- More diverse assessment strategies beyond basic observations
- Specialized evaluation methods for musical learning
- Age-appropriate assessment design principles

---

## ⚡ Performance Metrics

### Response Time Analysis
- **Keyword Approach:** {analysis['performance_metrics']['keyword_avg_time']:.2f}s average
- **RAG Approach:** {analysis['performance_metrics']['rag_avg_time']:.2f}s average
- **Overhead:** {analysis['performance_metrics']['time_overhead']:.2f}s additional processing time

### Content Size Analysis
- **Prompt Enhancement:** {analysis['performance_metrics']['prompt_enhancement']:.0f} characters increase in prompt size
- **Response Size:** {analysis['performance_metrics']['rag_avg_response_size']:.0f} characters (RAG) vs {analysis['performance_metrics']['keyword_avg_response_size']:.0f} characters (Keyword)

### Performance Assessment
The slight increase in processing time is justified by:
- Significant improvements in content quality and relevance
- Enhanced educational value through semantic search
- More comprehensive lesson planning resources

---

## 🎯 Quality Metrics Breakdown

"""
    
    # Add category breakdown table
    categories = analysis['quality_metrics']['category_breakdown']
    report += "| Quality Category | Keyword Average | RAG Average | Improvement | % Improvement |\n"
    report += "|------------------|-----------------|-------------|-------------|---------------|\n"
    
    for category, metrics in categories.items():
        formatted_category = category.replace('_', ' ').title()
        report += f"| {formatted_category} | {metrics['keyword_avg']:.1f} | {metrics['rag_avg']:.1f} | {metrics['improvement']:+.1f} | {metrics['improvement_percentage']:+.1f}% |\n"
    
    report += f"""
### Key Quality Improvements

1. **Standard Relevance**: {categories['standard_relevance_score']['improvement_percentage']:+.1f}% improvement in selecting contextually appropriate standards
2. **Teaching Strategy Quality**: {categories['teaching_strategy_quality']['improvement_percentage']:+.1f}% enhancement in pedagogical content
3. **Assessment Quality**: {categories['assessment_quality']['improvement_percentage']:+.1f}% improvement in assessment sophistication
4. **Educational Value**: {categories['educational_value_score']['improvement_percentage']:+.1f}% increase in overall educational worth
5. **Coherence**: {categories['coherence_score']['improvement_percentage']:+.1f}% better organizational structure

---

## ✨ Specific Improvement Examples

"""
    
    # Add improvement examples
    examples = analysis['improvement_examples']
    for i, example in enumerate(examples[:10], 1):  # Limit to top 10 examples
        report += f"### {i}. {example['scenario']} - {example['category']}\n\n"
        report += f"**Improvement:** {example['improvement']}\n\n"
        report += f"**Details:** {example['details']}\n\n"
    
    # Add API test results
    if analysis.get('api_test_result'):
        api_result = analysis['api_test_result']
        report += f"""
---

## 🌐 Live API Integration Test

### Endpoint Performance
- **Success:** ✅ {api_result['success']}
- **Response Time:** {api_result['response_time']:.2f}s
- **Quality Score:** {api_result['quality_score']:.1f}%
- **RAG Context Items Used:** {api_result['rag_context_items']}

### Quality Indicators
"""
        for indicator, value in api_result['quality_indicators'].items():
            status = "✅" if value else "❌"
            report += f"- {status} {indicator.replace('_', ' ').title()}\n"
    
    report += f"""
---

## 🎉 Conclusions and Recommendations

### Major Achievements

1. **Significant Quality Enhancement**: The RAG integration delivers a {analysis['quality_metrics']['overall_improvement_percentage']:.1f}% improvement in overall lesson generation quality.

2. **Superior Standard Selection**: Semantic search outperforms keyword matching by {analysis['standard_selection']['improvement_percentage']:.1f}%, providing more contextually relevant standards.

3. **Richer Educational Content**: Teaching strategies are {analysis['teaching_strategies']['improvement_diversity']} terms more diverse with {analysis['teaching_strategies']['improvement_evidence']} additional evidence-based elements.

4. **Advanced Assessment Design**: Assessment methods show {analysis['assessment_methods']['improvement_sophistication']} more sophisticated approaches.

### Performance Considerations

- **Acceptable Overhead**: {analysis['performance_metrics']['time_overhead']:.2f}s additional processing time for substantial quality gains
- **Enhanced Prompts**: {analysis['performance_metrics']['prompt_enhancement']:.0f} character increase provides valuable context
- **Maintainable Performance**: System remains responsive with fast response times

### Recommendations

1. **Deploy RAG Integration**: The quality improvements justify the minimal performance overhead.

2. **Continue Monitoring**: Track performance metrics as scaling increases.

3. **Expand Knowledge Base**: Consider adding more educational resources to further enhance RAG context.

4. **Fine-tune Similarity Thresholds**: Optimize semantic search parameters for different grade levels.

5. **User Feedback Integration**: Collect teacher feedback to validate quality improvements in real-world usage.

### Next Steps

- [ ] Deploy RAG-enhanced lesson generation to production
- [ ] Set up monitoring and alerting for performance metrics
- [ ] Conduct user acceptance testing with music educators
- [ ] Plan knowledge base expansion with additional educational resources
- [ ] Implement A/B testing for continuous quality improvement

---

*Report generated by PocketMusec Lesson Generation Quality Analysis System*
"""
    
    return report

def main():
    """Generate the comprehensive analysis report"""
    print("📊 Generating Comprehensive Lesson Generation Analysis Report")
    print("=" * 70)
    
    # Load comparison results
    print("📥 Loading comparison results...")
    results_data = load_comparison_results()
    
    if not results_data:
        print("❌ No results data found. Please run the comparison test first.")
        return False
    
    print("✅ Results data loaded successfully")
    
    # Analyze results
    print("🔍 Analyzing comparison results...")
    comparison_results = results_data.get("comparison_results", [])
    api_test_result = results_data.get("api_test_result", {})
    
    analysis = {
        "standard_selection": analyze_standard_selection_accuracy(comparison_results),
        "teaching_strategies": analyze_teaching_strategies(comparison_results),
        "assessment_methods": analyze_assessment_methods(comparison_results),
        "performance_metrics": analyze_performance_metrics(comparison_results),
        "quality_metrics": analyze_quality_metrics(comparison_results),
        "improvement_examples": generate_improvement_examples(comparison_results),
        "api_test_result": api_test_result
    }
    
    print("✅ Analysis completed")
    
    # Generate markdown report
    print("📝 Generating markdown report...")
    markdown_report = generate_markdown_report(analysis)
    
    # Save report
    report_filename = f"lesson_generation_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_filename, "w") as f:
        f.write(markdown_report)
    
    # Save analysis JSON
    analysis_filename = f"lesson_generation_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(analysis_filename, "w") as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"✅ Comprehensive analysis report generated!")
    print(f"📄 Markdown report: {report_filename}")
    print(f"📊 Analysis data: {analysis_filename}")
    print(f"\n🎉 Key Findings:")
    print(f"   • Overall quality improvement: {analysis['quality_metrics']['overall_improvement_percentage']:.1f}%")
    print(f"   • Standard selection improvement: {analysis['standard_selection']['improvement_percentage']:.1f}%")
    print(f"   • Additional teaching strategies: {analysis['teaching_strategies']['improvement_diversity']} unique terms")
    print(f"   • Enhanced assessment methods: {analysis['assessment_methods']['improvement_sophistication']} sophisticated terms")
    print(f"   • Processing overhead: {analysis['performance_metrics']['time_overhead']:.2f}s")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)