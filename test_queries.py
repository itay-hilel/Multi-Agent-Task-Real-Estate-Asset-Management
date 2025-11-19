import os
import sys
from langchain_core.messages import HumanMessage

# Add real_estate_agent to path
sys.path.append(os.path.join(os.getcwd(), 'real_estate_agent'))

try:
    from real_estate_agent.agent import app
    print("Agent loaded successfully.")
except Exception as e:
    print(f"Failed to load agent: {e}")
    sys.exit(1)

def run_test(query):
    print(f"\n--- Testing Query: '{query}' ---")
    try:
        initial_state = {"messages": [HumanMessage(content=query)]}
        result = app.invoke(initial_state)
        
        print(f"Intent: {result.get('intent')}")
        print(f"Extracted Info: {result.get('extracted_info')}")
        print(f"Tool Output: {result.get('tool_output')}")
        print(f"Final Response: {result['messages'][-1].content}")
        return result
    except Exception as e:
        print(f"Error running test: {e}")
        return None

# Test Cases
run_test("What is my total profit?")
run_test("Show me a breakdown of my expenses.")
run_test("What are the revenues for PropCo?")
run_test("How much did I spend on taxes?")
