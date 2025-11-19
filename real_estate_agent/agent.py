"""
Enhanced Real Estate Agent with Google File Search RAG Integration

This agent combines:
1. Structured data queries (Pandas on cortex.parquet)
2. Unstructured knowledge retrieval (Google File Search RAG)
"""

import os
import json
import pandas as pd
from typing import TypedDict, Annotated, List, Union, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# --- Configuration ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("WARNING: GOOGLE_API_KEY not found in environment variables.")

# LangChain LLM for intent classification and response generation
llm = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", temperature=0, google_api_key=api_key)

# Google GenAI client for File Search
genai_client = genai.Client(api_key=api_key)

# --- Load File for RAG Configuration ---
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'file_search_config.json')

FILE_URI = None
FILE_NAME = None
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
        FILE_URI = config.get('file_uri')
        FILE_NAME = config.get('file_name')
        print(f"✅ RAG file loaded: {FILE_NAME}")
else:
    print("⚠️  RAG file not configured. Run setup_rag.py first.")

# --- Data Loading ---
DATA_PATH = os.path.join(current_dir, "..", "cortex.parquet")
try:
    df = pd.read_parquet(DATA_PATH)
    print(f"✅ Loaded data with {len(df)} rows.")
except Exception as e:
    print(f"❌ Error loading data: {e}")
    df = pd.DataFrame()

# --- State Definition ---
class AgentState(TypedDict):
    messages: List[Union[SystemMessage, HumanMessage, AIMessage]]
    intent: str
    extracted_info: dict
    tool_output: str
    grounding_sources: Optional[List[str]]

# --- Nodes ---

def classify_intent(state: AgentState):
    """
    Classifies the user's intent into one of the known categories.
    
    NEW: Added 'document_search' intent for conceptual questions
    """
    messages = state['messages']
    last_message = messages[-1].content
    
    prompt = f"""
    You are a helpful assistant for a real estate asset management system.
    Classify the user's intent into one of the following categories:
    
    - 'pnl_analysis': Questions about profit, loss, revenue, expenses, financial performance, net income.
      Examples: "What was total profit?", "Show me revenue for Building 180", "Q1 expenses?"
    
    - 'property_details': Questions about specific property details, tenants, lease terms, property information.
      Examples: "List tenants in Building 180", "What properties do we manage?", "Who rents from us?"
    
    - 'document_search': Questions about system structure, data definitions, how things work, explanations of concepts.
      Examples: "What does ledger_category mean?", "Explain entity-level expenses", "What columns are in the data?",
               "How is the P&L structured?", "What revenue types do we track?"
    
    - 'general_chat': Greetings, general questions not related to specific data or documentation.
      Examples: "Hello", "How are you?", "What can you do?"
    
    User Query: {last_message}
    
    Respond ONLY with the category name (one word).
    """
    response = llm.invoke(prompt)
    # Handle both string and list responses
    content = response.content
    if isinstance(content, list):
        # If content is a list, join it or take the first element
        content = ' '.join(str(item) for item in content) if content else ''
    intent = str(content).strip().lower()
    
    # Fallback for unclear responses
    valid_intents = ['pnl_analysis', 'property_details', 'document_search', 'general_chat']
    if intent not in valid_intents:
        intent = 'general_chat'
    
    print(f"🎯 Intent: {intent}")
    return {"intent": intent}

def extract_info(state: AgentState):
    """
    Extracts relevant entities (property names, years, tenants) from the query.
    Only called for pnl_analysis and property_details intents.
    """
    messages = state['messages']
    last_message = messages[-1].content
    
    # Get unique values for context
    properties = df['property_name'].dropna().unique().tolist()
    tenants = df['tenant_name'].dropna().unique().tolist()
    
    prompt = f"""
    Extract the following information from the user query if present:
    - property_name: Look for these known properties: {properties[:20]}  (showing first 20)
    - tenant_name: Look for these known tenants: {tenants[:20]}  (showing first 20)
    - year: e.g., 2023, 2024
    - quarter: e.g., Q1, Q2, 2024-Q1
    - ledger_type: 'revenue' or 'expenses' (or null if asking for net profit/both)
    - category: Any specific expense/revenue category mentioned (e.g., 'tax', 'maintenance', 'rent')
    
    User Query: {last_message}
    
    Return a JSON object with keys 'property_name', 'tenant_name', 'year', 'quarter', 'ledger_type', 'category'. 
    Values should be null if not found.
    """
    
    llm_json = llm.bind(response_format={"type": "json_object"})
    response = llm_json.invoke(prompt)
    
    import json
    try:
        content = response.content
        if isinstance(content, list):
            content = ' '.join(str(item) for item in content) if content else '{}'
        extracted = json.loads(str(content))
    except:
        extracted = {}
    
    print(f"📋 Extracted: {extracted}")
    return {"extracted_info": extracted}

def query_data(state: AgentState):
    """
    Queries the Pandas DataFrame based on extracted info and intent.
    This handles STRUCTURED data queries.
    """
    intent = state['intent']
    info = state.get('extracted_info', {})
    
    filtered_df = df.copy()
    
    # Fill missing property names with 'General/Corporate' for better handling
    filtered_df['property_name'] = filtered_df['property_name'].fillna('Entity-Level')
    
    # Apply filters
    if info.get('property_name'):
        filtered_df = filtered_df[filtered_df['property_name'] == info['property_name']]
    if info.get('tenant_name'):
        filtered_df = filtered_df[filtered_df['tenant_name'] == info['tenant_name']]
    if info.get('year'):
        # Handle both string and int
        year_str = str(info['year'])
        filtered_df = filtered_df[filtered_df['year'] == year_str]
    if info.get('quarter'):
        q = info['quarter']
        # Handle Q1, Q2 format or 2024-Q1 format
        if 'Q' in str(q).upper() and '-' not in str(q):
            # User said "Q1" - need to add year if we have it
            if info.get('year'):
                q = f"{info['year']}-{q.upper()}"
        filtered_df = filtered_df[filtered_df['quarter'] == q]
    if info.get('ledger_type'):
        l_type = info['ledger_type'].lower()
        if 'rev' in l_type:
            filtered_df = filtered_df[filtered_df['ledger_type'] == 'revenue']
        elif 'exp' in l_type:
            filtered_df = filtered_df[filtered_df['ledger_type'] == 'expenses']
            
    if info.get('category'):
        cat = info['category'].lower()
        filtered_df = filtered_df[filtered_df['ledger_category'].str.contains(cat, case=False, na=False)]
    
    result_text = ""
    
    if intent == 'pnl_analysis':
        if len(filtered_df) == 0:
            result_text = "No records found matching the criteria."
        else:
            total_profit = filtered_df['profit'].sum()
            
            # Create a breakdown
            if info.get('ledger_type') or info.get('category'):
                breakdown = filtered_df.groupby('ledger_category')['profit'].sum().sort_values().to_dict()
                result_text = f"Total: ${total_profit:,.2f}\nBreakdown by Category:\n"
                for cat, val in breakdown.items():
                    result_text += f"  - {cat}: ${val:,.2f}\n"
            else:
                # General PnL, show breakdown by Property and Ledger Type
                prop_breakdown = filtered_df.groupby('property_name')['profit'].sum().to_dict()
                type_breakdown = filtered_df.groupby('ledger_type')['profit'].sum().to_dict()
                result_text = f"Net Profit: ${total_profit:,.2f}\n\nBy Property:\n"
                for prop, val in prop_breakdown.items():
                    result_text += f"  - {prop}: ${val:,.2f}\n"
                result_text += f"\nBy Type:\n"
                for typ, val in type_breakdown.items():
                    result_text += f"  - {typ}: ${val:,.2f}\n"
        
    elif intent == 'property_details':
        if len(filtered_df) > 0:
            # Show more details including category and description
            cols = ['property_name', 'tenant_name', 'ledger_type', 'ledger_category', 'profit']
            cols = [c for c in cols if c in filtered_df.columns]
            
            # Group by property and tenant for cleaner output
            summary = filtered_df.groupby(['property_name', 'tenant_name'])['profit'].sum().reset_index()
            summary_text = summary.head(10).to_string(index=False)
            
            result_text = f"Found {len(filtered_df)} records.\n\nSummary (top 10):\n{summary_text}"
        else:
            result_text = "No records found matching the criteria."
    else:
        result_text = "No data query needed."
    
    print(f"📊 Query result: {len(result_text)} chars")
    return {"tool_output": result_text}

def query_file_search(state: AgentState):
    """
    Uses uploaded file as context for answering questions (RAG).
    This handles conceptual questions about the system, definitions, etc.
    """
    if not FILE_URI:
        return {
            "tool_output": "RAG file not configured. Please run setup_rag.py first.",
            "grounding_sources": []
        }
    
    messages = state['messages']
    last_message = messages[-1].content
    
    print(f"🔍 Querying with RAG file: {last_message[:100]}...")
    
    try:
        # Use the uploaded file as context
        response = genai_client.models.generate_content(
            model='gemini-3-pro-preview',
            contents=[
                types.Content(
                    parts=[types.Part(text=f"""You are a helpful real estate assistant. 
Use the knowledge from the uploaded data dictionary file to answer this question:

{last_message}

Provide a clear, detailed answer based on the information in the file.""")]
                ),
                types.Content(
                    parts=[types.Part(file_data=types.FileData(file_uri=FILE_URI))]
                )
            ]
        )
        
        # Extract answer
        answer = response.text
        print(f"✅ Got response: {len(answer)} chars")
        
        # For now, note that we used the data dictionary
        sources = [FILE_NAME or "data_dictionary.md"]
        
        return {
            "tool_output": answer,
            "grounding_sources": sources
        }
        
    except Exception as e:
        print(f"❌ RAG query error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "tool_output": f"RAG query encountered an error: {str(e)}",
            "grounding_sources": []
        }

def generate_response(state: AgentState):
    """
    Generates the final natural language response.
    
    ENHANCED: Now includes grounding sources if available
    """
    messages = state['messages']
    intent = state['intent']
    tool_output = state.get('tool_output', "")
    extracted = state.get('extracted_info', {})
    grounding_sources = state.get('grounding_sources', [])
    
    # For document_search, the tool_output already contains the answer
    if intent == 'document_search':
        response_text = tool_output
        
        # Add sources if available
        if grounding_sources:
            response_text += "\n\n📚 **Sources:**\n"
            for source in grounding_sources:
                response_text += f"- {source}\n"
        
        return {"messages": [AIMessage(content=response_text)]}
    
    # For general chat
    if intent == 'general_chat':
        prompt = f"""
        You are a helpful Real Estate Asset Manager Assistant.
        User Query: {messages[-1].content}
        
        Provide a friendly response. Mention that you can help with:
        - Financial analysis (P&L, revenue, expenses)
        - Property details (tenants, properties)
        - System explanations (data structure, definitions)
        """
        response = llm.invoke(prompt)
        return {"messages": [response]}
    
    # For data queries (pnl_analysis, property_details)
    prompt = f"""
    You are a Real Estate Asset Manager Assistant.
    User Query: {messages[-1].content}
    Intent: {intent}
    Extracted Info: {extracted}
    Data Analysis Result: {tool_output}
    
    Provide a clear, concise, and professional answer to the user.
    - Present breakdowns clearly with bullet points
    - Numbers are already formatted as currency
    - If 'Entity-Level' appears, explain these are corporate expenses not tied to a specific property
    - Be conversational but professional
    """
    response = llm.invoke(prompt)
    return {"messages": [response]}

# --- Graph Construction ---
workflow = StateGraph(AgentState)

workflow.add_node("classify_intent", classify_intent)
workflow.add_node("extract_info", extract_info)
workflow.add_node("query_data", query_data)
workflow.add_node("query_file_search", query_file_search)
workflow.add_node("generate_response", generate_response)

workflow.set_entry_point("classify_intent")

def route_intent(state: AgentState):
    """
    Routes to appropriate node based on intent.
    
    NEW: Added routing for document_search
    """
    intent = state['intent']
    
    if intent == 'general_chat':
        return "generate_response"
    elif intent == 'document_search':
        return "query_file_search"
    else:
        # pnl_analysis or property_details
        return "extract_info"

workflow.add_conditional_edges(
    "classify_intent",
    route_intent,
    {
        "generate_response": "generate_response",
        "query_file_search": "query_file_search",
        "extract_info": "extract_info"
    }
)

workflow.add_edge("extract_info", "query_data")
workflow.add_edge("query_data", "generate_response")
workflow.add_edge("query_file_search", "generate_response")
workflow.add_edge("generate_response", END)

app = workflow.compile()

if __name__ == "__main__":
    """
    Simple CLI test interface
    """
    print("=" * 60)
    print("  REAL ESTATE AGENT - Enhanced with File Search RAG")
    print("=" * 60)
    print("\nCapabilities:")
    print("  1. 📊 Financial Analysis (from parquet data)")
    print("  2. 🏢 Property Details (from parquet data)")
    print("  3. 📚 System Documentation (from File Search RAG)")
    print("  4. 💬 General Chat")
    print("\nType 'quit' to exit.\n")
    
    # Show example queries
    print("📝 Example Queries:")
    print("  Financial: 'What was total profit in 2024?'")
    print("  Property:  'Show me tenants in Building 180'")
    print("  Document:  'What does ledger_category mean?'")
    print("  Document:  'Explain entity-level expenses'")
    print("\n" + "=" * 60 + "\n")
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        initial_state = {"messages": [HumanMessage(content=user_input)]}
        
        try:
            result = app.invoke(initial_state)
            response = result['messages'][-1].content
            
            print(f"\n🤖 Agent: {response}\n")
            
            # Show debug info
            if result.get('intent'):
                print(f"   [Intent: {result['intent']}]")
            
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

