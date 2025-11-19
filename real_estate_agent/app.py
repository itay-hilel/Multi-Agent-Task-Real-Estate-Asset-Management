"""
Enhanced Streamlit App with File Search RAG Integration
Shows grounding sources and knowledge source used for each query
"""

import streamlit as st
import pandas as pd
from langchain_core.messages import HumanMessage, AIMessage
from agent import app as agent_app, DATA_PATH, FILE_URI
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Real Estate Agent - RAG Enhanced", 
    layout="wide",
    page_icon="🏢"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .knowledge-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        margin: 4px;
    }
    .badge-data { background-color: #e3f2fd; color: #1565c0; }
    .badge-doc { background-color: #f3e5f5; color: #6a1b9a; }
    .badge-chat { background-color: #e8f5e9; color: #2e7d32; }
</style>
""", unsafe_allow_html=True)

st.title("🏢 Real Estate Asset Management Agent")
st.caption("Enhanced with Google File Search RAG")

# --- Sidebar: System Info & Data Preview ---
with st.sidebar:
    st.header("📊 System Information")
    
    # Show File Search status
    if FILE_URI:
        st.success("✅ RAG Active")
        with st.expander("🔍 RAG Configuration"):
            st.code(FILE_URI, language=None)
    else:
        st.warning("⚠️ RAG not configured")
        st.caption("Run setup_rag.py")
    
    st.divider()
    
    # Knowledge Sources
    st.subheader("🧠 Knowledge Sources")
    st.markdown("""
    <div>
        <span class="knowledge-badge badge-data">📊 Structured Data</span>
        <span class="knowledge-badge badge-doc">📚 Documents (RAG)</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("The agent automatically chooses the best source for your query")
    
    st.divider()
    
    # Data Preview
    st.header("📈 Data Preview")
    try:
        df = pd.read_parquet(DATA_PATH)
        df['property_name'] = df['property_name'].fillna('Entity-Level')
        
        st.metric("Total Records", f"{len(df):,}")
        st.metric("Properties", df['property_name'].nunique())
        st.metric("Net Profit", f"${df['profit'].sum():,.2f}")
        
        # Quick stats
        with st.expander("View Sample Data"):
            st.dataframe(df.head(50), use_container_width=True)
        
        # Financial charts
        with st.expander("📊 Financial Charts"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.caption("Revenue vs Expenses")
                rev_exp = df.groupby('ledger_type')['profit'].sum().abs()
                st.bar_chart(rev_exp)
            
            with col2:
                st.caption("Profit by Property (Top 10)")
                profit_by_prop = df.groupby('property_name')['profit'].sum().sort_values(ascending=False).head(10)
                st.bar_chart(profit_by_prop)
        
    except Exception as e:
        st.error(f"Could not load data: {e}")

# --- Main Chat Interface ---

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_debug" not in st.session_state:
    st.session_state.show_debug = False

# Debug toggle
st.session_state.show_debug = st.checkbox("🔧 Show debug info", value=st.session_state.show_debug)

# Example queries
with st.expander("💡 Example Queries"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Data Queries:**")
        st.code("What was total profit in 2024?")
        st.code("Show me revenue for Building 180")
        st.code("List all tenants")
        st.code("What were maintenance expenses in Q1 2025?")
    
    with col2:
        st.markdown("**📚 Documentation Queries:**")
        st.code("What does ledger_category mean?")
        st.code("Explain entity-level expenses")
        st.code("What properties do we manage?")
        st.code("What revenue types exist?")

st.divider()

# Display chat history
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.write(msg.content)

# User Input
if prompt := st.chat_input("Ask about your properties..."):
    # Add user message to history
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.write(prompt)

    # Run Agent
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                # Prepare state with full history
                initial_state = {"messages": st.session_state.messages}
                result = agent_app.invoke(initial_state)
                
                response_msg = result['messages'][-1]
                st.write(response_msg.content)
                
                # Add assistant message to history
                st.session_state.messages.append(response_msg)
                
                # Show debug information if enabled
                if st.session_state.show_debug:
                    with st.expander("🔍 Agent Reasoning Process", expanded=False):
                        intent = result.get('intent', 'unknown')
                        
                        # Show intent with badge
                        intent_badges = {
                            'pnl_analysis': '<span class="knowledge-badge badge-data">📊 Structured Data Query</span>',
                            'property_details': '<span class="knowledge-badge badge-data">📊 Structured Data Query</span>',
                            'document_search': '<span class="knowledge-badge badge-doc">📚 File Search RAG</span>',
                            'general_chat': '<span class="knowledge-badge badge-chat">💬 General Chat</span>'
                        }
                        
                        st.markdown(f"**Intent:** {intent_badges.get(intent, intent)}", unsafe_allow_html=True)
                        
                        # Show extracted info for data queries
                        if intent in ['pnl_analysis', 'property_details']:
                            st.write("**Extracted Information:**")
                            st.json(result.get('extracted_info', {}))
                        
                        # Show grounding sources for document queries
                        if intent == 'document_search' and result.get('grounding_sources'):
                            st.write("**📚 Grounding Sources:**")
                            for source in result['grounding_sources']:
                                st.write(f"- {source}")
                        
                        # Show raw tool output
                        with st.expander("Raw Tool Output"):
                            st.text(result.get('tool_output', 'N/A')[:500])
                    
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
                
                # Show helpful error messages
                if "File Search" in str(e):
                    st.info("💡 Tip: Make sure you've run `python3 real_estate_agent/setup_rag.py`")
                elif "API key" in str(e):
                    st.info("💡 Tip: Check your .env file has GOOGLE_API_KEY set")

# Footer
st.divider()
st.caption("💡 Tip: Toggle 'Show debug info' to see how the agent makes decisions")

