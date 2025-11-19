"""
Model-Based Grader for Agent Evaluations
Uses LLM to grade agent responses against expected answers
"""

import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM for grading
api_key = os.getenv("GOOGLE_API_KEY")
grader_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=api_key
)

def grade_single_response(question, expected_answer, expected_details, agent_response):
    """
    Use LLM to grade a single agent response
    
    Returns:
        dict with grade, score, explanation
    """
    
    if not agent_response:
        return {
            'grade': 'INCORRECT',
            'score': 0.0,
            'explanation': 'Agent failed to produce a response'
        }
    
    grading_prompt = f"""You are an expert evaluator for a Real Estate AI Agent.

**Question:** {question}

**Expected Answer:** {expected_answer}

**Expected Details:** {expected_details}

**Agent's Response:** {agent_response}

---

Grade the agent's response using these criteria:

1. **CORRECT** (Score: 1.0)
   - Answer is accurate and matches expected answer
   - All key information is present
   - Minor formatting differences are acceptable

2. **PARTIAL** (Score: 0.5)
   - Answer is partially correct
   - Missing some details but core answer is right
   - OR answer is in the right direction but not precise enough

3. **INCORRECT** (Score: 0.0)
   - Answer is wrong
   - Completely misses the question
   - Provides irrelevant information

**IMPORTANT:** Be lenient with formatting. If the agent says "PropCo" or "The entity is PropCo", both should be CORRECT.
For numerical answers, accept reasonable variations (e.g., "€1,533,331.87" vs "€1533331.87" vs "approximately €1.5M").

Respond in JSON format:
{{
  "grade": "CORRECT" | "PARTIAL" | "INCORRECT",
  "score": 1.0 | 0.5 | 0.0,
  "explanation": "Brief explanation of why this grade was given"
}}
"""
    
    try:
        llm_json = grader_llm.bind(response_format={"type": "json_object"})
        response = llm_json.invoke(grading_prompt)
        
        # Handle structured content
        content = response.content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
                elif isinstance(item, str):
                    text_parts.append(item)
            content = ' '.join(text_parts) if text_parts else '{}'
        
        # Clean up content - sometimes has markdown code blocks
        content_str = str(content).strip()
        if content_str.startswith('```json'):
            content_str = content_str[7:]
        if content_str.startswith('```'):
            content_str = content_str[3:]
        if content_str.endswith('```'):
            content_str = content_str[:-3]
        content_str = content_str.strip()
        
        result = json.loads(content_str)
        return result
        
    except Exception as e:
        print(f"❌ Grading error: {e}")
        print(f"   Content was: {str(content)[:200]}")
        return {
            'grade': 'ERROR',
            'score': 0.0,
            'explanation': f'Grading failed: {str(e)}'
        }

def grade_all_evals(results_path='eval_results.json', output_path='eval_grades.json'):
    """
    Grade all evaluation results
    """
    print("="*60)
    print("  GRADING AGENT RESPONSES")
    print("="*60)
    
    # Load results
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    results = data['results']
    print(f"\n📋 Grading {len(results)} responses...")
    
    graded_results = []
    total_score = 0.0
    
    for i, result in enumerate(results, 1):
        print(f"\n[{i}/{len(results)}] Q{result['question_number']}: {result['difficulty']}")
        
        if not result['success']:
            grade_info = {
                'grade': 'FAILED',
                'score': 0.0,
                'explanation': f"Agent error: {result['error']}"
            }
        else:
            grade_info = grade_single_response(
                question=result['question'],
                expected_answer=result['expected_answer'],
                expected_details=result['expected_details'],
                agent_response=result['agent_response']
            )
        
        # Combine result with grade
        graded_result = {**result, **grade_info}
        graded_results.append(graded_result)
        total_score += grade_info['score']
        
        print(f"   Grade: {grade_info['grade']} ({grade_info['score']})")
        print(f"   Reason: {grade_info['explanation']}")
    
    # Calculate statistics
    accuracy = (total_score / len(results)) * 100 if results else 0
    
    # By difficulty
    difficulty_stats = {}
    for difficulty in ['Easy', 'Medium', 'Hard', 'Very Hard']:
        diff_results = [r for r in graded_results if r['difficulty'] == difficulty]
        if diff_results:
            diff_score = sum(r['score'] for r in diff_results)
            diff_total = len(diff_results)
            difficulty_stats[difficulty] = {
                'total': diff_total,
                'score': diff_score,
                'accuracy': (diff_score / diff_total) * 100
            }
    
    # Save graded results
    output = {
        'timestamp': data['timestamp'],
        'total_questions': len(results),
        'total_score': total_score,
        'max_score': len(results),
        'accuracy_percent': accuracy,
        'difficulty_breakdown': difficulty_stats,
        'graded_results': graded_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"  GRADING COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Grades saved to: {output_path}")
    print(f"\n📊 Overall Results:")
    print(f"   Score: {total_score:.1f}/{len(results)}")
    print(f"   Accuracy: {accuracy:.1f}%")
    print(f"\n📈 By Difficulty:")
    for difficulty, stats in difficulty_stats.items():
        print(f"   {difficulty}: {stats['score']:.1f}/{stats['total']} ({stats['accuracy']:.0f}%)")
    
    return output

if __name__ == "__main__":
    import sys
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Grade evaluations
    grades = grade_all_evals(
        results_path=os.path.join(current_dir, 'eval_results.json'),
        output_path=os.path.join(current_dir, 'eval_grades.json')
    )
    
    print(f"\n🎯 Next step: Run generate_eval_report.py to create detailed report")
