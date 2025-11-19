import os
import pandas as pd
from typing import TypedDict, Annotated, List, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
# Ensure you have GOOGLE_API_KEY in your .env file
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("WARNING: GOOGLE_API_KEY not found in environment variables.")

llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0, google_api_key=api_key)

# --- Data Loading ---
# Calculate absolute path to cortex.parquet (one level up from this script)
current_dir = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(current_dir, "..", "cortex.parquet")
try:
    df = pd.read_parquet(DATA_PATH)
    print(f"Loaded data with {len(df)} rows.")
except Exception as e:
    print(f"Error loading data: {e}")
    df = pd.DataFrame() # Empty fallback

# --- State Definition ---
class AgentState(TypedDict):
    messages: List[Union[SystemMessage, HumanMessage, AIMessage]]
    intent: str
    extracted_info: dict
    tool_output: str

# --- Nodes ---

def classify_intent(state: AgentState):
    """Classifies the user's intent into one of the known categories."""
    messages = state['messages']
    last_message = messages[-1].content
    
    prompt = f"""
    You are a helpful assistant for a real estate asset management system.
    Classify the user's intent into one of the following categories:
    - 'pnl_analysis': Questions about profit, loss, revenue, expenses, financial performance, net income.
    - 'property_details': Questions about specific property details, tenants, lease terms.
    - 'general_chat': Greetings, general questions not related to specific data.
    
    User Query: {last_message}
    
    Respond ONLY with the category name.
    """
    response = llm.invoke(prompt)
    intent = response.content.strip().lower()
    
    # Fallback for unclear responses
    valid_intents = ['pnl_analysis', 'property_details', 'general_chat']
    if intent not in valid_intents:
        intent = 'general_chat'
        
    return {"intent": intent}

def extract_info(state: AgentState):
    """Extracts relevant entities (property names, years, tenants) from the query."""
    messages = state['messages']
    last_message = messages[-1].content
    
    # Get unique values for context
    properties = df['property_name'].dropna().unique().tolist()
    tenants = df['tenant_name'].dropna().unique().tolist()
    
    prompt = f"""
    Extract the following information from the user query if present:
    - property_name: Look for these known properties: {properties}
    - tenant_name: Look for these known tenants: {tenants}
    - year: e.g., 2023, 2024
    - quarter: e.g., Q1, Q2
    - ledger_type: 'revenue' or 'expenses' (or null if asking for net profit/both)
    - category: Any specific expense/revenue category mentioned (e.g., 'tax', 'maintenance', 'rent')
    
    User Query: {last_message}
    
    Return a JSON object with keys 'property_name', 'tenant_name', 'year', 'quarter', 'ledger_type', 'category'. 
    Values should be null if not found.
    """
    # structured output would be better, but using json mode for simplicity with gemini flash
    llm_json = llm.bind(response_format={"type": "json_object"})
    response = llm_json.invoke(prompt)
    import json
    try:
        extracted = json.loads(response.content)
    except:
        extracted = {}
        
    return {"extracted_info": extracted}

def query_data(state: AgentState):
    """Queries the Pandas DataFrame based on extracted info and intent."""
    intent = state['intent']
    info = state.get('extracted_info', {})
    
    filtered_df = df.copy()
    
    # Fill missing property names with 'General/Corporate' for better handling
    filtered_df['property_name'] = filtered_df['property_name'].fillna('General/Corporate')
    
    # Apply filters
    if info.get('property_name'):
        filtered_df = filtered_df[filtered_df['property_name'] == info['property_name']]
    if info.get('tenant_name'):
        filtered_df = filtered_df[filtered_df['tenant_name'] == info['tenant_name']]
    if info.get('year'):
        filtered_df = filtered_df[filtered_df['year'] == str(info['year'])]
    if info.get('quarter'):
        filtered_df = filtered_df[filtered_df['quarter'] == info['quarter']]
    if info.get('ledger_type'):
        # Map common terms if needed, but assuming LLM extracts 'revenue' or 'expenses' matches data or close enough
        l_type = info['ledger_type'].lower()
        if 'rev' in l_type:
            filtered_df = filtered_df[filtered_df['ledger_type'] == 'revenue']
        elif 'exp' in l_type:
            filtered_df = filtered_df[filtered_df['ledger_type'] == 'expenses']
            
    if info.get('category'):
        # Fuzzy match or partial match for category
        cat = info['category'].lower()
        filtered_df = filtered_df[filtered_df['ledger_category'].str.contains(cat, case=False, na=False)]
        
    result_text = ""
    
    if intent == 'pnl_analysis':
        total_profit = filtered_df['profit'].sum()
        
        # Create a breakdown
        # If specific ledger type requested, show breakdown by category
        if info.get('ledger_type') or info.get('category'):
            breakdown = filtered_df.groupby('ledger_category')['profit'].sum().sort_values().to_dict()
            result_text = f"Total: {total_profit}\nBreakdown by Category: {breakdown}"
        else:
            # General PnL, show breakdown by Property and Ledger Type
            prop_breakdown = filtered_df.groupby('property_name')['profit'].sum().to_dict()
            type_breakdown = filtered_df.groupby('ledger_type')['profit'].sum().to_dict()
            result_text = f"Net Profit: {total_profit}\nBy Property: {prop_breakdown}\nBy Type: {type_breakdown}"
        
    elif intent == 'property_details':
        if len(filtered_df) > 0:
            # Show more details including category and description
            cols = ['property_name', 'ledger_type', 'ledger_category', 'ledger_description', 'profit']
            # Filter cols that exist
            cols = [c for c in cols if c in filtered_df.columns]
            summary = filtered_df[cols].head(5).to_string()
            result_text = f"Found {len(filtered_df)} records. Here are the top 5:\n{summary}"
        else:
            result_text = "No records found matching the criteria."
            
    else:
        result_text = "No data query needed."
        
    return {"tool_output": result_text}

def generate_response(state: AgentState):
    """Generates the final natural language response."""
    messages = state['messages']
    intent = state['intent']
    tool_output = state.get('tool_output', "")
    extracted = state.get('extracted_info', {})
    
    prompt = f"""
    You are a Real Estate Asset Manager Assistant.
    User Query: {messages[-1].content}
    Intent: {intent}
    Extracted Info: {extracted}
    Data Analysis Result: {tool_output}
    
    Provide a clear, concise, and professional answer to the user.
    - If the result is a breakdown, present it clearly (e.g., bullet points).
    - Format numbers as currency (USD).
    - If 'General/Corporate' appears in property lists, explain these are entity-level expenses not tied to a specific property.
    """
    response = llm.invoke(prompt)
    return {"messages": [response]}

# --- Graph Construction ---
workflow = StateGraph(AgentState)

workflow.add_node("classify_intent", classify_intent)
workflow.add_node("extract_info", extract_info)
workflow.add_node("query_data", query_data)
workflow.add_node("generate_response", generate_response)

workflow.set_entry_point("classify_intent")

def route_intent(state: AgentState):
    intent = state['intent']
    if intent == 'general_chat':
        return "generate_response"
    else:
        return "extract_info"

workflow.add_conditional_edges(
    "classify_intent",
    route_intent,
    {
        "generate_response": "generate_response",
        "extract_info": "extract_info"
    }
)

workflow.add_edge("extract_info", "query_data")
workflow.add_edge("query_data", "generate_response")
workflow.add_edge("generate_response", END)

app = workflow.compile()

if __name__ == "__main__":
    # Simple CLI test
    print("Agent loaded. Type 'quit' to exit.")
    while True:
        user_input = input("User: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        initial_state = {"messages": [HumanMessage(content=user_input)]}
        result = app.invoke(initial_state)
        print(f"Agent: {result['messages'][-1].content}")
