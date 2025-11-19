"""
Report Generator for Agent Evaluations
Creates human-readable markdown report from graded evaluations
"""

import os
import json
from datetime import datetime

def generate_report(grades_path='eval_grades.json', output_path='eval_report.md'):
    """
    Generate detailed markdown report from graded evaluations
    """
    print("="*60)
    print("  GENERATING EVALUATION REPORT")
    print("="*60)
    
    # Load graded results
    with open(grades_path, 'r') as f:
        data = json.load(f)
    
    results = data['graded_results']
    
    # Start building report
    report = []
    report.append("# Real Estate Agent - Evaluation Report\n")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"**Evaluation Run:** {data['timestamp']}\n")
    report.append("\n---\n")
    
    # Overall Summary
    report.append("## 📊 Overall Summary\n")
    report.append(f"- **Total Questions:** {data['total_questions']}")
    report.append(f"- **Total Score:** {data['total_score']:.1f}/{data['max_score']}")
    report.append(f"- **Accuracy:** {data['accuracy_percent']:.1f}%\n")
    
    # Calculate average response time
    successful_results = [r for r in results if r['success']]
    if successful_results:
        avg_time = sum(r['response_time_ms'] for r in successful_results) / len(successful_results)
        report.append(f"- **Average Response Time:** {avg_time:.0f}ms\n")
    
    report.append("\n---\n")
    
    # By Difficulty
    report.append("## 📈 Performance by Difficulty\n")
    for difficulty, stats in data['difficulty_breakdown'].items():
        emoji = {
            'Easy': '🟢',
            'Medium': '🟡',
            'Hard': '🟠',
            'Very Hard': '🔴'
        }.get(difficulty, '⚪')
        
        report.append(f"### {emoji} {difficulty}\n")
        report.append(f"- Score: {stats['score']:.1f}/{stats['total']}")
        report.append(f"- Accuracy: {stats['accuracy']:.0f}%\n")
    
    report.append("\n---\n")
    
    # Detailed Results
    report.append("## 📝 Detailed Results\n")
    
    for result in results:
        grade_emoji = {
            'CORRECT': '✅',
            'PARTIAL': '⚠️',
            'INCORRECT': '❌',
            'FAILED': '💥',
            'ERROR': '🔥'
        }.get(result['grade'], '❓')
        
        report.append(f"### Question {result['question_number']}: {grade_emoji} {result['grade']} ({result['score']})\n")
        report.append(f"**Difficulty:** {result['difficulty']}\n")
        report.append(f"**Question:** {result['question']}\n")
        report.append(f"**Expected Answer:** {result['expected_answer']}\n")
        
        if result['success']:
            report.append(f"**Agent Response:**\n```\n{result['agent_response']}\n```\n")
            report.append(f"**Grader Explanation:** {result['explanation']}\n")
            report.append(f"**Metadata:**\n")
            report.append(f"- Intent: `{result['intent']}`")
            report.append(f"- Response Time: {result['response_time_ms']}ms")
            if result['grounding_sources']:
                report.append(f"- Sources: {', '.join(result['grounding_sources'])}")
        else:
            report.append(f"**Error:** {result['error']}\n")
        
        report.append("\n---\n")
    
    # Failed Questions Summary
    failed = [r for r in results if r['score'] < 1.0]
    if failed:
        report.append("## ❌ Failed/Partial Questions Summary\n")
        for result in failed:
            report.append(f"- **Q{result['question_number']}** ({result['difficulty']}): {result['grade']}")
            report.append(f"  - {result['explanation']}\n")
    
    # Performance Insights
    report.append("\n---\n")
    report.append("## 💡 Performance Insights\n")
    
    # Intent classification breakdown
    intent_counts = {}
    for r in successful_results:
        intent = r['intent']
        if intent not in intent_counts:
            intent_counts[intent] = {'total': 0, 'correct': 0}
        intent_counts[intent]['total'] += 1
        if r['score'] == 1.0:
            intent_counts[intent]['correct'] += 1
    
    report.append("### Intent Classification Usage\n")
    for intent, counts in intent_counts.items():
        accuracy = (counts['correct'] / counts['total'] * 100) if counts['total'] > 0 else 0
        report.append(f"- `{intent}`: {counts['total']} questions ({accuracy:.0f}% correct)\n")
    
    # Recommendations
    report.append("\n### 🎯 Recommendations\n")
    
    easy_failed = [r for r in results if r['difficulty'] == 'Easy' and r['score'] < 1.0]
    if easy_failed:
        report.append("- ⚠️ **Critical:** Failed easy questions. Review basic data queries.\n")
    
    if data['accuracy_percent'] < 70:
        report.append("- 📚 Improve data dictionary with more examples\n")
        report.append("- 🔍 Review intent classification accuracy\n")
    
    hard_success = [r for r in results if r['difficulty'] in ['Hard', 'Very Hard'] and r['score'] == 1.0]
    if hard_success:
        report.append(f"- ✨ Strong performance on {len(hard_success)} hard questions!\n")
    
    # Write report
    report_text = '\n'.join(report)
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    print(f"\n✅ Report generated: {output_path}")
    print(f"📄 Report length: {len(report_text)} characters")
    
    return report_text

if __name__ == "__main__":
    import sys
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Generate report
    report = generate_report(
        grades_path=os.path.join(current_dir, 'eval_grades.json'),
        output_path=os.path.join(current_dir, 'eval_report.md')
    )
    
    print(f"\n✅ Evaluation complete! Review the report at:")
    print(f"   {os.path.join(current_dir, 'eval_report.md')}")
