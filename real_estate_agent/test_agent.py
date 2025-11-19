from agent import app
from langchain_core.messages import HumanMessage

def test_agent():
    queries = [
        "Hello, who are you?",
        "What is the total profit for PropCo?",
        "Show me details for the property named 'North Heights'", # Adjust property name based on real data
        "Compare profit of PropCo vs OtherEntity" # Adjust based on real data
    ]
    
    print("--- Starting Agent Test ---")
    for query in queries:
        print(f"\nQuery: {query}")
        try:
            result = app.invoke({"messages": [HumanMessage(content=query)]})
            print(f"Response: {result['messages'][-1].content}")
            print(f"Intent: {result.get('intent')}")
        except Exception as e:
            print(f"Error: {e}")
            
if __name__ == "__main__":
    test_agent()
