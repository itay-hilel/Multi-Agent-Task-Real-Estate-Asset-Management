import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from langchain_core.messages import HumanMessage, AIMessage
from agent import app as agent_app, DATA_PATH, FILE_URI, api_key
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Real Estate Agent - RAG Enhanced",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Modern UI ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #F4F6F7;
    }
    
    /* Card Styling */
    .metric-card {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        border-left: 5px solid #2E86C1;
    }
    
    /* Chat Styling */
    .stChatMessage {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #2C3E50;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Badges */
    .knowledge-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    .badge-data { background-color: #E3F2FD; color: #1565C0; border: 1px solid #BBDEFB; }
    .badge-doc { background-color: #F3E5F5; color: #6A1B9A; border: 1px solid #E1BEE7; }
    .badge-chat { background-color: #E8F5E9; color: #2E7D32; border: 1px solid #C8E6C9; }
    
    /* Sidebar Tweaks */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
    }
    
    /* Button Styling */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def format_currency(value):
    return f"${value:,.2f}"

# --- Main Layout ---

# Header Section
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.markdown("# 🏢")
with col_title:
    st.title("Real Estate Asset Management")
    st.markdown("**AI-Powered Insights & Document Analysis**")

st.divider()

# --- Initialize session state BEFORE sidebar ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_debug" not in st.session_state:
    st.session_state.show_debug = False

# --- Sidebar: Conversation Management ---
with st.sidebar:
    st.markdown("### 💬 Conversations")
    
    # New Chat Button
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # Company Context Section
    st.markdown("### 🏢 Company Context")
    
    # Get current context
    from company_context_handler import get_company_context, save_company_context, clear_company_context
    current_context = get_company_context()
    
    # Display current context if exists
    if current_context:
        with st.expander("📋 Current Context", expanded=False):
            st.text(current_context)
    
    # Context input
    st.markdown("**Provide information about your company:**")
    context_input = st.text_area(
        "Company context",
        value=current_context if current_context else "",
        height=200,
        help="Describe your company, properties, and any relevant information",
        placeholder="e.g., We are ABC Real Estate, managing 5 commercial properties in downtown...",
        label_visibility="collapsed"
    )
    
    # Buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save Context", use_container_width=True, type="primary"):
            if context_input.strip():
                if save_company_context(context_input):
                    st.success("✅ Context saved!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Failed to save context")
            else:
                st.warning("Please enter some context first")
    
    with col2:
        if current_context and st.button("🗑️ Clear", use_container_width=True):
            if clear_company_context():
                st.success("Context cleared")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Failed to clear context")
    
    st.divider()
    
    # Current Conversation Summary
    if st.session_state.messages:
        st.markdown("#### Current Chat")
        msg_count = len([m for m in st.session_state.messages if isinstance(m, HumanMessage)])
        st.markdown(f"""
        <div style="padding: 0.5rem; background: #f8f9fa; border-radius: 8px;">
            <small style="color: #666;">Messages: {msg_count}</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Quick Stats
    try:
        df = pd.read_parquet(DATA_PATH)
        st.markdown("#### Quick Stats")
        
        total_profit = df['profit'].sum()
        properties = df['property_name'].fillna('Entity-Level').nunique()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Properties", properties, label_visibility="visible")
        with col2:
            st.metric("Net Profit", f"${total_profit/1000:.0f}K", label_visibility="visible")
    except:
        pass

# --- Chat Interface ---

# Chat Container
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user", avatar="👤"):
                st.write(msg.content)
        elif isinstance(msg, AIMessage):
            with st.chat_message("assistant", avatar="🤖"):
                # Extract text from structured content if needed
                content = msg.content
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and 'text' in item:
                            text_parts.append(item['text'])
                        elif isinstance(item, str):
                            text_parts.append(item)
                    content = '\n'.join(text_parts) if text_parts else str(content)
                st.write(content)

# Input Area (Fixed at bottom by Streamlit default)
if prompt := st.chat_input("Ask about properties, financial reports, or documents..."):
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        try:
            initial_state = {"messages": st.session_state.messages}
            result = initial_state.copy()
            
            with st.status("Thinking...", expanded=True) as status:
                import random
                
                # Themed Status Messages
                msgs_intent = [
                    "Reviewing your request...",
                    "Consulting the property manager...",
                    "Analyzing your question...",
                    "Checking property records..."
                ]
                msgs_extract = [
                    "Identifying key property details...",
                    "Looking up tenant records...",
                    "Parsing financial parameters...",
                    "Locating specific assets..."
                ]
                msgs_query = [
                    "Pulling financial reports...",
                    "Accessing the ledger...",
                    "Retrieving lease agreements...",
                    "Querying the database..."
                ]
                msgs_viz = [
                    "Charting performance metrics...",
                    "Visualizing the data...",
                    "Generating market insights...",
                    "Preparing visual reports..."
                ]
                msgs_response = [
                    "Drafting the executive summary...",
                    "Preparing your report...",
                    "Finalizing the analysis...",
                    "Compiling the results..."
                ]

                for output in agent_app.stream(initial_state):
                    for node_name, node_output in output.items():
                        result.update(node_output)
                        
                        if node_name == "classify_intent":
                            intent = node_output.get("intent", "unknown")
                            st.markdown(f"**Intent:** `{intent}`")
                            status.update(label=random.choice(msgs_intent), state="running")
                            
                        elif node_name == "extract_info":
                            st.markdown("Extracted parameters.")
                            status.update(label=random.choice(msgs_extract), state="running")
                            
                        elif node_name == "query_data":
                            st.markdown("Retrieved data.")
                            status.update(label=random.choice(msgs_query), state="running")
                            
                        elif node_name == "generate_visualization":
                            if node_output.get("visualization_config"):
                                st.markdown("Generated visualization.")
                            status.update(label=random.choice(msgs_response), state="running")
                            
                        elif node_name == "generate_response":
                             status.update(label=random.choice(msgs_response), state="running")
                
                status.update(label="Complete", state="complete", expanded=False)

            response_msg = result['messages'][-1]
                
            # Extract text from structured content if needed
            content = response_msg.content
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                    elif isinstance(item, str):
                        text_parts.append(item)
                content = '\n'.join(text_parts) if text_parts else str(content)
            
            st.write(content)
            st.session_state.messages.append(response_msg)
            
            # --- Debug / Metadata Section (Collapsible) ---
            if st.session_state.show_debug:
                with st.expander("🔍 Agent Analysis", expanded=True):
                    intent = result.get('intent', 'unknown')
                    
                    # Intent Badges
                    intent_map = {
                        'pnl_analysis': ('Data Analysis', 'badge-data'),
                        'property_details': ('Property Query', 'badge-data'),
                        'document_search': ('Document Search', 'badge-doc'),
                        'general_chat': ('General Chat', 'badge-chat')
                    }
                    
                    label, badge_class = intent_map.get(intent, (intent, 'badge-data'))
                    st.markdown(f"""
                        <div style="margin-bottom:10px;">
                            <span class="knowledge-badge {badge_class}">{label}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Context
                    if intent == 'document_search' and result.get('grounding_sources'):
                        st.markdown("**📚 Sources:**")
                        for source in result['grounding_sources']:
                            st.caption(f"• {source}")
                    
                    if intent in ['pnl_analysis', 'property_details']:
                        st.json(result.get('extracted_info', {}))
                        
                    # Visualization
                    viz_config = result.get('visualization_config')
                    structured_data = result.get('structured_data')
                    
                    if viz_config and structured_data:
                        st.markdown("### 📊 Visualization")
                        
                        if viz_config['type'] == 'bar':
                            fig = px.bar(
                                structured_data, 
                                x=viz_config['x'], 
                                y=viz_config['y'],
                                color=viz_config['color'],
                                title=viz_config['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                        elif viz_config['type'] == 'line':
                            fig = px.line(
                                structured_data, 
                                x=viz_config['x'], 
                                y=viz_config['y'],
                                title=viz_config['title'],
                                markers=True
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                    if structured_data:
                        with st.expander("📋 Data Table", expanded=False):
                            st.dataframe(structured_data, use_container_width=True)
                        
        except Exception as e:
            st.error(f"Error: {e}")

# --- Footer / Settings ---
with st.sidebar:
    st.divider()
    st.markdown("### ⚙️ Settings")
    st.session_state.show_debug = st.toggle("Debug Mode", value=st.session_state.show_debug)
    
    
    with st.expander("💡 Example Queries"):
        st.markdown("""
        **💰 Financial Analysis**
        - "What was total profit in 2024?"
        - "Show me revenue for Building 180"
        
        **🏢 Property Details**
        - "List all tenants"
        - "What properties do we manage?"
        
        **📚 Documentation**
        - "What does ledger_category mean?"
        - "Explain entity-level expenses"
        """)
