"""
Test script for the enhanced agent with File Search RAG
Tests all four intent types with example queries
"""

from langchain_core.messages import HumanMessage
from agent import app
import json

# Test queries for each intent type
TEST_QUERIES = {
    'pnl_analysis': [
        "What was the total profit in 2024?",
        "Show me revenue for Building 180",
        "What were maintenance expenses in Q1 2025?",
    ],
    'property_details': [
        "List all properties we manage",
        "Who are the tenants in Building 180?",
        "Show me all tenant information",
    ],
    'document_search': [
        "What does ledger_category mean?",
        "Explain the difference between entity-level and property-level expenses",
        "What revenue types do we track?",
        "How is the data structured?",
    ],
    'general_chat': [
        "Hello! What can you help me with?",
        "What are your capabilities?",
    ]
}

def test_query(query: str, expected_intent: str = None):
    """Test a single query and show results"""
    print(f"\n{'='*70}")
    print(f"❓ Query: {query}")
    print('='*70)
    
    try:
        initial_state = {"messages": [HumanMessage(content=query)]}
        result = app.invoke(initial_state)
        
        intent = result.get('intent', 'unknown')
        response = result['messages'][-1].content
        
        # Check intent matches expected
        intent_match = "✅" if intent == expected_intent else "⚠️"
        print(f"\n{intent_match} Intent: {intent} (expected: {expected_intent})")
        
        # Show extracted info for data queries
        if intent in ['pnl_analysis', 'property_details']:
            extracted = result.get('extracted_info', {})
            print(f"📋 Extracted: {json.dumps(extracted, indent=2)}")
        
        # Show grounding sources for doc queries
        if intent == 'document_search':
            sources = result.get('grounding_sources', [])
            if sources:
                print(f"📚 Sources: {', '.join(sources)}")
        
        # Show response
        print(f"\n🤖 Response:")
        print("-" * 70)
        print(response[:500])  # First 500 chars
        if len(response) > 500:
            print(f"... (truncated, {len(response)} total chars)")
        print("-" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def run_all_tests():
    """Run all test queries"""
    print("\n" + "="*70)
    print("  TESTING ENHANCED AGENT WITH FILE SEARCH RAG")
    print("="*70)
    
    total_tests = sum(len(queries) for queries in TEST_QUERIES.values())
    passed_tests = 0
    
    for intent, queries in TEST_QUERIES.items():
        print(f"\n\n{'#'*70}")
        print(f"# Testing Intent: {intent.upper()}")
        print(f"{'#'*70}")
        
        for query in queries:
            success = test_query(query, expected_intent=intent)
            if success:
                passed_tests += 1
    
    # Summary
    print("\n\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    print(f"\n✅ Passed: {passed_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed - check output above")

def quick_test():
    """Run a quick test with one query of each type"""
    print("\n" + "="*70)
    print("  QUICK TEST - One Query Per Intent")
    print("="*70)
    
    quick_queries = [
        ("What was total profit in 2024?", 'pnl_analysis'),
        ("List all properties", 'property_details'),
        ("What does ledger_category mean?", 'document_search'),
        ("Hello", 'general_chat'),
    ]
    
    for query, expected_intent in quick_queries:
        test_query(query, expected_intent)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_test()
    else:
        print("\nRunning full test suite...")
        print("(Use --quick flag for faster testing)\n")
        run_all_tests()

