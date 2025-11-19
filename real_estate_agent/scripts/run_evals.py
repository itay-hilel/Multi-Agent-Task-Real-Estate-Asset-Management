"""
Evaluation Runner for Real Estate Agent
Runs the agent against benchmark questions and collects responses
"""

import os
import json
import time
import pandas as pd
from datetime import datetime
from langchain_core.messages import HumanMessage
from agent import app as agent_app
from dotenv import load_dotenv

load_dotenv()

def load_eval_questions(csv_path='evals.csv'):
    """Load evaluation questions from CSV"""
    df = pd.read_csv(csv_path)
    return df.to_dict('records')

def run_single_eval(question_data):
    """
    Run agent on a single question and capture response + metadata
    
    Returns:
        dict with question, response, metadata
    """
    question = question_data['Question']
    
    print(f"\n{'='*60}")
    print(f"Q{question_data['Question_Number']}: {question}")
    print(f"Difficulty: {question_data['Difficulty']}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run agent
        initial_state = {"messages": [HumanMessage(content=question)]}
        result = agent_app.invoke(initial_state)
        
        # Extract response
        response_msg = result['messages'][-1]
        
        # Handle structured content
        content = response_msg.content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
                elif isinstance(item, str):
                    text_parts.append(item)
            agent_response = '\n'.join(text_parts) if text_parts else str(content)
        else:
            agent_response = str(content)
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Capture metadata
        intent = result.get('intent', 'unknown')
        grounding_sources = result.get('grounding_sources', [])
        
        print(f"\n🤖 Agent Response:")
        print(agent_response[:200] + "..." if len(agent_response) > 200 else agent_response)
        print(f"\n📊 Metadata:")
        print(f"   Intent: {intent}")
        print(f"   Response Time: {response_time_ms}ms")
        if grounding_sources:
            print(f"   Sources: {', '.join(grounding_sources)}")
        
        return {
            'question_number': question_data['Question_Number'],
            'difficulty': question_data['Difficulty'],
            'question': question,
            'expected_answer': question_data['Answer'],
            'expected_details': question_data['Answer_Details'],
            'agent_response': agent_response,
            'intent': intent,
            'grounding_sources': grounding_sources,
            'response_time_ms': response_time_ms,
            'success': True,
            'error': None
        }
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'question_number': question_data['Question_Number'],
            'difficulty': question_data['Difficulty'],
            'question': question,
            'expected_answer': question_data['Answer'],
            'expected_details': question_data['Answer_Details'],
            'agent_response': None,
            'intent': None,
            'grounding_sources': [],
            'response_time_ms': 0,
            'success': False,
            'error': str(e)
        }

def run_all_evals(csv_path='evals.csv', output_path='eval_results.json'):
    """
    Run all evaluation questions and save results
    """
    print("="*60)
    print("  REAL ESTATE AGENT EVALUATION")
    print("="*60)
    
    questions = load_eval_questions(csv_path)
    print(f"\n📋 Loaded {len(questions)} evaluation questions")
    
    results = []
    for q in questions:
        result = run_single_eval(q)
        results.append(result)
        time.sleep(1)  # Brief pause between questions
    
    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'total_questions': len(questions),
        'successful_runs': sum(1 for r in results if r['success']),
        'failed_runs': sum(1 for r in results if not r['success']),
        'results': results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"  EVALUATION COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Results saved to: {output_path}")
    print(f"📊 Summary:")
    print(f"   Total Questions: {len(questions)}")
    print(f"   Successful: {output['successful_runs']}")
    print(f"   Failed: {output['failed_runs']}")
    
    return output

if __name__ == "__main__":
    import sys
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run evaluations
    results = run_all_evals(
        csv_path=os.path.join(current_dir, 'evals.csv'),
        output_path=os.path.join(current_dir, 'eval_results.json')
    )
    
    print(f"\n🎯 Next step: Run grade_evals.py to score the responses")
