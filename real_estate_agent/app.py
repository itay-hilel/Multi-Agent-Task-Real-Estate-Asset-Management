import streamlit as st
import pandas as pd
from langchain_core.messages import HumanMessage, AIMessage
from agent import app as agent_app, DATA_PATH
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Real Estate Agent", layout="wide")

st.title("🏢 Real Estate Asset Management Agent")

# --- Sidebar: Data Preview ---
st.sidebar.header("Data Preview")
try:
    # Load data again for preview (or import from agent if shared)
    df = pd.read_parquet(DATA_PATH)
    # Fill missing property names
    df['property_name'] = df['property_name'].fillna('General/Corporate')
    st.sidebar.write(f"Total Rows: {len(df)}")
    st.sidebar.dataframe(df.head(100))
    
    # Charts
    if 'profit' in df.columns and 'ledger_type' in df.columns:
        st.sidebar.subheader("Financial Overview")
        
        # Revenue vs Expenses
        rev_exp = df.groupby('ledger_type')['profit'].sum().abs()
        st.sidebar.bar_chart(rev_exp)
        
        st.sidebar.subheader("Profit by Property")
        profit_by_prop = df.groupby('property_name')['profit'].sum().sort_values()
        st.sidebar.bar_chart(profit_by_prop)
        
except Exception as e:
    st.sidebar.error(f"Could not load data: {e}")

# --- Chat Interface ---

if "messages" not in st.session_state:
    st.session_state.messages = []

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
        with st.spinner("Thinking..."):
            try:
                # Prepare state with full history
                initial_state = {"messages": st.session_state.messages}
                result = agent_app.invoke(initial_state)
                
                response_msg = result['messages'][-1]
                st.write(response_msg.content)
                
                # Add assistant message to history
                st.session_state.messages.append(response_msg)
                
                # Optional: Show thought process (debug)
                with st.expander("Agent Thoughts"):
                    st.write(f"Intent: {result.get('intent')}")
                    st.write(f"Extracted Info: {result.get('extracted_info')}")
                    st.write(f"Tool Output: {result.get('tool_output')}")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")
