import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from langchain_core.messages import HumanMessage, AIMessage
from agent import app as agent_app, DATA_PATH, FILE_URI
import os
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

# --- Sidebar: System Info & Analytics ---
with st.sidebar:
    st.markdown("### 📊 Dashboard")
    
    # RAG Status Card
    rag_status_color = "#4CAF50" if FILE_URI else "#FF5252"
    rag_status_text = "Active" if FILE_URI else "Inactive"
    rag_icon = "✅" if FILE_URI else "⚠️"
    
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: {rag_status_color};">
        <h4 style="margin:0; color: #555;">RAG System</h4>
        <h3 style="margin:0; color: {rag_status_color};">{rag_icon} {rag_status_text}</h3>
        <small style="color: #888;">{FILE_URI if FILE_URI else "Setup Required"}</small>
    </div>
    """, unsafe_allow_html=True)

    # Data Analytics Section
    try:
        df = pd.read_parquet(DATA_PATH)
        df['property_name'] = df['property_name'].fillna('Entity-Level')
        
        # Key Metrics Grid
        st.markdown("#### Key Performance Indicators")
        
        total_profit = df['profit'].sum()
        total_revenue = df[df['profit'] > 0]['profit'].sum() # Simplified proxy if not explicit
        
        # Custom HTML Metrics for better control
        st.markdown(f"""
        <div class="metric-card">
            <div style="display:flex; justify-content:space-between;">
                <div>
                    <small>Net Profit</small>
                    <h3 style="margin:0;">{format_currency(total_profit)}</h3>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Properties", df['property_name'].nunique())
        with col_b:
            st.metric("Records", f"{len(df):,}")
            
        st.divider()
        
        # Charts
        st.markdown("#### Financial Overview")
        
        # 1. Profit by Property (Bar Chart)
        profit_by_prop = df.groupby('property_name')['profit'].sum().sort_values(ascending=True).tail(10)
        fig_prop = px.bar(
            profit_by_prop, 
            orientation='h',
            title="Top Performing Properties",
            labels={'value': 'Profit ($)', 'property_name': 'Property'},
            color_discrete_sequence=['#2E86C1'],
            template="plotly_white"
        )
        fig_prop.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=300)
        st.plotly_chart(fig_prop, use_container_width=True)
        
        # 2. Revenue vs Expenses (Donut or Bar)
        # Assuming positive profit is revenue proxy and negative is expense for this viz
        rev = df[df['profit'] > 0]['profit'].sum()
        exp = df[df['profit'] < 0]['profit'].sum()
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Revenue', 'Expenses'], 
            values=[rev, abs(exp)], 
            hole=.6,
            marker_colors=['#4CAF50', '#FF5252']
        )])
        fig_pie.update_layout(title="Revenue vs Expenses", margin=dict(l=0, r=0, t=30, b=0), height=250)
        st.plotly_chart(fig_pie, use_container_width=True)

    except Exception as e:
        st.error(f"Could not load analytics: {e}")

# --- Chat Interface ---

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_debug" not in st.session_state:
    st.session_state.show_debug = False

# Chat Container
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user", avatar="👤"):
                st.write(msg.content)
        elif isinstance(msg, AIMessage):
            with st.chat_message("assistant", avatar="🤖"):
                st.write(msg.content)

# Input Area (Fixed at bottom by Streamlit default)
if prompt := st.chat_input("Ask about properties, financial reports, or documents..."):
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                initial_state = {"messages": st.session_state.messages}
                result = agent_app.invoke(initial_state)
                response_msg = result['messages'][-1]
                
                st.write(response_msg.content)
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
                            
            except Exception as e:
                st.error(f"Error: {e}")

# --- Footer / Settings ---
with st.sidebar:
    st.divider()
    st.markdown("### ⚙️ Settings")
    st.session_state.show_debug = st.toggle("Debug Mode", value=st.session_state.show_debug)
    
    with st.expander("💡 Query Examples"):
        st.markdown("""
        **💰 Financials**
        - "Total profit for Building 180?"
        - "Show me top 5 expenses."
        
        **📄 Documents**
        - "What is the lease policy?"
        - "Explain CAM charges."
        """)
