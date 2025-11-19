"""
Script to visualize the LangGraph flow
"""
import sys
import os

# Suppress LLM initialization warnings
os.environ.setdefault('GOOGLE_API_KEY', 'dummy-key-for-visualization')

# Import after setting env
from typing import TypedDict, List, Union, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

# Define state (copy from agent.py to avoid full import)
class AgentState(TypedDict):
    messages: List[Union[SystemMessage, HumanMessage, AIMessage]]
    intent: str
    extracted_info: dict
    tool_output: str
    grounding_sources: Optional[List[str]]
    structured_data: Optional[List[dict]]
    visualization_config: Optional[dict]

# Rebuild graph structure for visualization
workflow = StateGraph(AgentState)

# Add all nodes
workflow.add_node("classify_intent", lambda x: x)
workflow.add_node("extract_info", lambda x: x)
workflow.add_node("query_data", lambda x: x)
workflow.add_node("generate_visualization", lambda x: x)
workflow.add_node("generate_response", lambda x: x)

workflow.set_entry_point("classify_intent")

# Add edges
workflow.add_conditional_edges(
    "classify_intent",
    lambda x: "generate_response",
    {
        "generate_response": "generate_response",
        "extract_info": "extract_info"
    }
)

workflow.add_edge("extract_info", "query_data")
workflow.add_edge("query_data", "generate_visualization")
workflow.add_edge("generate_visualization", "generate_response")
workflow.add_edge("generate_response", END)

app = workflow.compile()

# Generate Mermaid diagram
print("=== Mermaid Diagram ===")
mermaid_code = app.get_graph().draw_mermaid()
print(mermaid_code)
print("\n")

# Save it to a file
with open("graph_diagram.mmd", "w") as f:
    f.write(mermaid_code)
print("✅ Saved Mermaid diagram to graph_diagram.mmd")
print("   → You can view this at: https://mermaid.live/")

# Try to generate PNG  
try:
    png_data = app.get_graph().draw_mermaid_png()
    with open("graph_diagram.png", "wb") as f:
        f.write(png_data)
    print("✅ Saved PNG diagram to graph_diagram.png")
except Exception as e:
    print(f"⚠️  Could not generate PNG: {e}")
    print("   → Install with: pip install pygraphviz (requires graphviz system library)")
