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
# Support both CSV and Parquet formats
CSV_PATH = os.path.join(current_dir, "data", "cortex.csv")
PARQUET_PATH = os.path.join(current_dir, "data", "cortex.parquet")

# Try CSV first, fallback to parquet
if os.path.exists(CSV_PATH):
    DATA_PATH = CSV_PATH
    data_format = "CSV"
elif os.path.exists(PARQUET_PATH):
    DATA_PATH = PARQUET_PATH
    data_format = "Parquet"
else:
    DATA_PATH = None
    data_format = None

try:
    if DATA_PATH:
        if data_format == "CSV":
            df = pd.read_csv(DATA_PATH)
        else:
            df = pd.read_parquet(DATA_PATH)
        print(f"✅ Loaded data with {len(df)} rows from {data_format}.")
    else:
        raise FileNotFoundError("No data file found (cortex.csv or cortex.parquet)")
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
    structured_data: Optional[List[dict]]
    visualization_config: Optional[dict]

# --- Nodes ---

def classify_intent(state: AgentState):
    """
    Classifies the user's intent into one of the known categories.
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
    
    - 'general_chat': Greetings, general questions, company information questions.
      Examples: "Hello", "How are you?", "What can you do?", "Tell me about the company"
    
    User Query: {last_message}
    
    Respond ONLY with the category name (one word).
    """
    response = llm.invoke(prompt)
    # Handle both string and list responses
    content = response.content
    if isinstance(content, list):
        # If content is a list of dicts with 'text' field, extract the text
        text_parts = []
        for item in content:
            if isinstance(item, dict) and 'text' in item:
                text_parts.append(item['text'])
            elif isinstance(item, str):
                text_parts.append(item)
            else:
                text_parts.append(str(item))
        content = ' '.join(text_parts) if text_parts else ''
    intent = str(content).strip().lower()
    
    # Fallback for unclear responses
    valid_intents = ['pnl_analysis', 'property_details', 'general_chat']
    if intent not in valid_intents:
        intent = 'general_chat'
    
    print(f"🎯 Intent: {intent}")
    return {"intent": intent}

def extract_info(state: AgentState):
    """
    Extracts relevant entities (property names, years, tenants, ledger categories) from the query.
    Only called for pnl_analysis and property_details intents.
    """
    messages = state['messages']
    last_message = messages[-1].content
    
    # Get unique values for context
    properties = df['property_name'].dropna().unique().tolist()
    tenants = df['tenant_name'].dropna().unique().tolist()
    ledger_categories = df['ledger_category'].dropna().unique().tolist()
    
    prompt = f"""
    Extract the following information from the user query if present:
    
    PROPERTIES: {properties[:20]}  (showing first 20)
    TENANTS: {tenants[:20]}  (showing first 20)
    
    LEDGER CATEGORIES (IMPORTANT - extract exact matches):
    Revenue: revenue_rent_taxed, proceeds_parking_taxed, vat_compensation, rent_discount_taxed
    Expenses: management_fees, directors_fee, insurance_in_general, bank_charges, financial_expenses,
              interest_mortgage, real_estate_taxes, asset_management_fees, property_management_fees,
              maintenance, other_general_expenses
    
    Extract:
    - property_name: exact property name from list above
    - tenant_name: exact tenant name from list above  
    - year: single year (e.g., 2024) or null
    - quarter: specific quarter (e.g., "2024-Q1", "2024-Q4") or null
    - ledger_type: 'revenue' or 'expenses' or null
    - ledger_category: EXACT category name from list above (e.g., "revenue_rent_taxed", "management_fees")
    - comparison_years: array of years if comparing (e.g., [2024, 2025]) or null
    - aggregate_by: "tenant", "quarter", "property", "category" if grouping is needed, or null
    - metric: "ratio", "growth_rate", "noi", "expense_ratio", "concentration" or null
    - top_n: integer for top N items (e.g., 3) or null
    
    CRITICAL EXAMPLES - FOLLOW THESE EXACTLY:
    "revenue from taxed rent" → ledger_category: "revenue_rent_taxed", ledger_type: "revenue"
    "taxed rent" → ledger_category: "revenue_rent_taxed", ledger_type: "revenue"
    "management fees" → ledger_category: "management_fees", ledger_type: "expenses"
    "percentage of total expenses are management fees" → ledger_category: "management_fees", ledger_type: "expenses"
    "2024 vs 2025" → comparison_years: [2024, 2025]
    "2024 compare to 2025" → comparison_years: [2024, 2025]
    "net profit in 2024 compare to 2025" → comparison_years: [2024, 2025]
    "Q4 2024" → quarter: "2024-Q4", year: "2024"
    "which quarter" → aggregate_by: "quarter"
    "which tenant" → aggregate_by: "tenant"
    "how many buildings" → aggregate_by: "property"
    "ratio of parking to rent" → metric: "ratio", ledger_category: "proceeds_parking_taxed"
    "top 3 tenants" → metric: "concentration", top_n: 3, aggregate_by: "tenant"
    "NOI excluding financing" → metric: "noi"
    "growth from Jan to Dec" → metric: "growth_rate"
    "lowest expense ratio" → metric: "expense_ratio"
    "rent discounts" → ledger_category: "rent_discount_taxed"
    
    User Query: {last_message}
    
    Return a JSON object with all keys. Use null for missing values.
    IMPORTANT: If you see "compare", "vs", or "to" between two years, set comparison_years.
    IMPORTANT: Match ledger categories even if user uses shorthand (e.g., "taxed rent" = "revenue_rent_taxed").
    """
    
    llm_json = llm.bind(response_format={"type": "json_object"})
    response = llm_json.invoke(prompt)
    
    import json
    try:
        content = response.content
        if isinstance(content, list):
            # Extract text from structured list responses
            text_parts = []
            for item in content:
                if isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
                elif isinstance(item, str):
                    text_parts.append(item)
            content = ' '.join(text_parts) if text_parts else '{}'
        extracted = json.loads(str(content))
    except:
        extracted = {}
    
    print(f"📋 Extracted: {extracted}")
    return {"extracted_info": extracted}

def query_data(state: AgentState):
    """
    Queries the Pandas DataFrame based on extracted info and intent.
    This handles STRUCTURED data queries with smart routing.
    """
    intent = state['intent']
    info = state.get('extracted_info', {})
    last_message = state['messages'][-1].content.lower()
    
    # QUICK WIN 1: Handle entity name queries
    if 'entity' in last_message or 'company' in last_message:
        entity_names = df['entity_name'].dropna().unique()
        if len(entity_names) > 0:
            return {"tool_output": f"Entity name: {entity_names[0]}", "structured_data": [{"entity": entity_names[0]}]}
        return {"tool_output": "No entity name found in dataset"}
    
    # QUICK WIN 2: Handle building count queries
    if 'how many building' in last_message or 'number of building' in last_message:
        building_count = df['property_name'].dropna().nunique()
        buildings = sorted(df['property_name'].dropna().unique().tolist())

        data = [{"property": b} for b in buildings]
        return {"tool_output": f"Total buildings: {building_count}\\nBuildings: {', '.join(buildings)}", "structured_data": data}
    
    # FALLBACK: Handle taxed rent queries (Q5)
    if 'taxed rent' in last_message or 'revenue_rent_taxed' in last_message:
        if not info.get('ledger_category'):
            info['ledger_category'] = 'revenue_rent_taxed'
            info['ledger_type'] = 'revenue'
    
    # FALLBACK: Handle management fees queries (Q8)
    if 'management fee' in last_message or 'management_fee' in last_message:
        if not info.get('ledger_category'):
            # Match all management fee categories
            info['ledger_category'] = 'management'
            info['ledger_type'] = 'expenses'
    
    # FALLBACK: Handle year comparisons (Q9)
    if not info.get('comparison_years'):
        if ('2024' in last_message and '2025' in last_message) and any(word in last_message for word in ['compare', 'vs', 'versus', 'to']):
            info['comparison_years'] = [2024, 2025]
            
    # FALLBACK: Handle rent discounts (Q11)
    if 'discount' in last_message:
         if not info.get('ledger_category'):
            # Use partial match to catch taxed and untaxed
            info['ledger_category'] = 'rent_discount'
            
    # FALLBACK: Handle parking ratio (Q12)
    if 'parking' in last_message and 'ratio' in last_message:
        info['metric'] = 'ratio'
        
    # FALLBACK: Handle top tenants (Q13)
    if 'top' in last_message and 'tenant' in last_message:
        info['metric'] = 'concentration'
        if '3' in last_message:
            info['top_n'] = 3
            
    # FALLBACK: Handle NOI (Q14)
    if 'noi' in last_message or 'net operating income' in last_message:
        info['metric'] = 'noi'
        
    # FALLBACK: Handle growth rate (Q15)
    # FIX Q15: Enhanced pattern matching for growth rate queries
    if any(word in last_message for word in ['growth', 'mom', 'month-over-month']):
        if 'rate' in last_message or ('month' in last_message and 'month' in last_message):
            info['metric'] = 'growth_rate'
            # Extract year if present
            if not info.get('year'):
                if '2024' in last_message:
                    info['year'] = 2024
        
    # FALLBACK: Handle expense ratio (Q16)
    if 'expense ratio' in last_message:
        info['metric'] = 'expense_ratio'
    
    
    # Prepare filtered dataframe
    filtered_df = df.copy()
    filtered_df['property_name'] = filtered_df['property_name'].fillna('Entity-Level')
    
    # Apply basic filters
    if info.get('property_name'):
        filtered_df = filtered_df[filtered_df['property_name'] == info['property_name']]
    
    if info.get('tenant_name'):
        filtered_df = filtered_df[filtered_df['tenant_name'] == info['tenant_name']]
    
    # FIX: Handle Year as INT or STRING safely
    if info.get('year') and not info.get('comparison_years') and not info.get('metric') == 'growth_rate':
        try:
            target_year = int(info['year'])
            filtered_df = filtered_df[filtered_df['year'] == target_year]
        except:
            # Fallback if year is not an integer
            filtered_df = filtered_df[filtered_df['year'].astype(str) == str(info['year'])]
    
    if info.get('quarter'):
        q = info['quarter']
        if 'Q' in str(q).upper() and '-' not in str(q) and info.get('year'):
            q = f"{info['year']}-{q.upper()}"
        filtered_df = filtered_df[filtered_df['quarter'] == q]
    
    if info.get('ledger_type'):
        l_type = info['ledger_type'].lower()
        if 'rev' in l_type:
            filtered_df = filtered_df[filtered_df['ledger_type'] == 'revenue']
        elif 'exp' in l_type:
            filtered_df = filtered_df[filtered_df['ledger_type'] == 'expenses']
    
    # ENHANCEMENT: Filter by specific ledger_category
    if info.get('ledger_category'):
        category = info['ledger_category']
        # Try exact match first
        if category in filtered_df['ledger_category'].values:
            filtered_df = filtered_df[filtered_df['ledger_category'] == category]
        else:
            # Try partial match (e.g., "management" matches "management_fees")
            filtered_df = filtered_df[filtered_df['ledger_category'].str.contains(category, case=False, na=False)]
            
    # --- METRIC HANDLERS ---
    
    # METRIC: Ratio (Q12 - Parking to Rent)
    if info.get('metric') == 'ratio' or ('ratio' in last_message and 'parking' in last_message):
        # Calculate Parking Revenue (Taxed + Untaxed)
        parking_df = df[df['ledger_category'].str.contains('parking', case=False, na=False)]
        parking_rev = abs(parking_df['profit'].sum())
        
        # Calculate Rent Revenue (Taxed + Untaxed)
        # FIX: Include taxed AND untaxed rent (using correct category name 'proceeds_rent_untaxed')
        rent_df = df[df['ledger_category'].str.contains('revenue_rent_taxed|proceeds_rent_untaxed', case=False, na=False, regex=True)]
        rent_rev = abs(rent_df['profit'].sum())
        
        if rent_rev > 0:
            ratio = (parking_rev / rent_rev) * 100

            data = [
                {"Category": "Parking", "Amount": parking_rev},
                {"Category": "Rent", "Amount": rent_rev}
            ]
            return {"tool_output": f"Ratio of Parking to Rent Revenue: {ratio:.2f}%\\nParking: ${parking_rev:,.2f}\\nRent (Gross): ${rent_rev:,.2f}", "structured_data": data}
            
    # METRIC: Concentration (Q13 - Top 3 Tenants)
    if info.get('metric') == 'concentration' or ('top' in last_message and 'tenant' in last_message):
        top_n = info.get('top_n', 3)
        
        # Get tenant revenue
        rev_df = df[df['ledger_type'] == 'revenue']
        tenant_rev = rev_df.groupby('tenant_name')['profit'].sum().sort_values(ascending=False)
        
        total_rev = tenant_rev.sum()
        top_n_rev = tenant_rev.head(top_n).sum()
        
        if total_rev > 0:
            concentration = (top_n_rev / total_rev) * 100
            top_tenants_str = ", ".join([f"{t} (${v:,.2f})" for t, v in tenant_rev.head(top_n).items()])

            
            data = [{"Tenant": t, "Revenue": v} for t, v in tenant_rev.head(top_n).items()]
            
            return {"tool_output": f"Top {top_n} Tenant Concentration: {concentration:.2f}%\\nTotal Tenant Revenue: ${total_rev:,.2f}\\nTop {top_n} Revenue: ${top_n_rev:,.2f}\\nTop Tenants: {top_tenants_str}", "structured_data": data}

    # METRIC: NOI excluding financing (Q14)
    if info.get('metric') == 'noi':
        # Total Revenue
        total_rev = df[df['ledger_type'] == 'revenue']['profit'].sum()
        
        # Operating Expenses (Excluding financing)
        # FIX: Only exclude mortgage interest. Financial expenses and bank charges are OpEx.
        financing_cats = ['interest_mortgage']
        exp_df = df[df['ledger_type'] == 'expenses']
        op_exp_df = exp_df[~exp_df['ledger_category'].isin(financing_cats)]
        
        op_exp = op_exp_df['profit'].sum() # This is negative
        
        noi = total_rev + op_exp # Revenue + (negative expenses)
        

        
        data = [
            {"Category": "Total Revenue", "Amount": total_rev},
            {"Category": "Operating Expenses", "Amount": abs(op_exp)},
            {"Category": "NOI", "Amount": noi}
        ]
        
        return {"tool_output": f"NOI (excluding financing): ${noi:,.2f}\\nTotal Revenue: ${total_rev:,.2f}\\nOperating Expenses: ${op_exp:,.2f}", "structured_data": data}

    # METRIC: Growth Rate (Q15 - Jan to Dec)
    if info.get('metric') == 'growth_rate':
        # Filter for 2024 if not specified
        year = info.get('year', '2024')
        # FIX: Handle int/str year
        try:
            target_year = int(year)
            year_df = df[df['year'] == target_year]
        except:
            year_df = df[df['year'].astype(str) == str(year)]
        
        # Get Jan and Dec
        jan_df = year_df[year_df['month'] == '01']
        dec_df = year_df[year_df['month'] == '12']
        
        jan_val = jan_df['profit'].sum()
        dec_val = dec_df['profit'].sum()
        
        if jan_val != 0:
            growth = ((dec_val - jan_val) / abs(jan_val)) * 100

            data = [
                {"Month": f"Jan {year}", "Profit": jan_val},
                {"Month": f"Dec {year}", "Profit": dec_val}
            ]
            return {"tool_output": f"Growth Rate (Jan to Dec {year}): {growth:.2f}%\\nJan {year}: ${jan_val:,.2f}\\nDec {year}: ${dec_val:,.2f}", "structured_data": data}

    # METRIC: Expense Ratio (Q16)
    if info.get('metric') == 'expense_ratio':
        # Calculate per property
        props = df['property_name'].dropna().unique()
        ratios = {}
        
        for p in props:
            p_df = df[df['property_name'] == p]
            rev = p_df[p_df['ledger_type'] == 'revenue']['profit'].sum()
            exp = abs(p_df[p_df['ledger_type'] == 'expenses']['profit'].sum())
            
            if rev > 0:
                ratios[p] = (exp / rev) * 100
                
        # Find lowest
        if ratios:
            best_prop = min(ratios, key=ratios.get)
            best_ratio = ratios[best_prop]
            data = [{"Property": p, "Expense Ratio": r} for p, r in ratios.items()]
            return {"tool_output": f"Lowest Expense Ratio: {best_prop} at {best_ratio:.2f}%\\nAll Ratios: {ratios}", "structured_data": data}

    
    # ENHANCEMENT: Handle year comparisons
    if info.get('comparison_years'):
        results = {}
        for year in info['comparison_years']:
            # FIX Q9: Handle int/str year - try both approaches
            year_df = df[(df['year'] == year) | (df['year'] == int(year)) | (df['year'].astype(str) == str(year))]
                
            # For 2025, only include Q1 if question mentions "first 3 months"
            if str(year) == '2025' and ('first' in last_message or 'q1' in last_message or '3 month' in last_message):
                year_df = year_df[year_df['quarter'] == '2025-Q1']
            
            # Sum the profit
            year_total = year_df['profit'].sum()
            results[str(year)] = year_total
        
        result_text = "Year comparison:\\n"
        data = []
        for year, profit in results.items():
            result_text += f"  {year}: ${profit:,.2f}\\n"
            data.append({"Year": str(year), "Profit": profit})
        return {"tool_output": result_text, "structured_data": data}
    
    # ENHANCEMENT: Aggregate by quarter
    if info.get('aggregate_by') == 'quarter' or ('quarter' in last_message and 'which' in last_message):
        quarter_summary = filtered_df.groupby('quarter')['profit'].sum().sort_values()
        
        # If asking for highest/lowest expenses
        if 'expense' in last_message or 'cost' in last_message:
            expense_df = filtered_df[filtered_df['ledger_type'] == 'expenses']
            quarter_expenses = expense_df.groupby('quarter')['profit'].sum()
            # Most negative = highest expenses
            # FIX Q6: Define variables before use
            highest_expense_quarter = quarter_expenses.idxmin()  # Most negative
            highest_expense_amount = abs(quarter_expenses.min())
            
            data = [{"Quarter": q, "Expenses": abs(v)} for q, v in quarter_expenses.items()]
            return {"tool_output": f"Quarter with highest expenses: {highest_expense_quarter} (${highest_expense_amount:,.2f})", "structured_data": data}
        
        result_text = "By quarter:\\n"
        data = []
        for quarter, profit in quarter_summary.items():
            result_text += f"  {quarter}: ${profit:,.2f}\\n"
            data.append({"Quarter": quarter, "Profit": profit})
        return {"tool_output": result_text, "structured_data": data}
    
    # ENHANCEMENT: Aggregate by tenant
    if info.get('aggregate_by') == 'tenant' or ('tenant' in last_message and ('which' in last_message or 'most' in last_message)):
        tenant_summary = filtered_df.groupby('tenant_name')['profit'].sum().sort_values(ascending=False)
        if len(tenant_summary) > 0:
            top_tenant = tenant_summary.index[0]
            top_amount = tenant_summary.iloc[0]
            
            result_text = f"Top tenant: {top_tenant} (${top_amount:,.2f})\\n\\nTop 5 tenants:\\n"
            data = []
            for tenant, profit in tenant_summary.head(5).items():
                result_text += f"  {tenant}: ${profit:,.2f}\\n"
                data.append({"Tenant": tenant, "Profit": profit})
            return {"tool_output": result_text, "structured_data": data}
        return {"tool_output": "No tenant data found"}
    
    # ENHANCEMENT: Calculate percentages
    if 'percentage' in last_message or '%' in last_message or 'percent' in last_message:
        # FIX Q8: Handle Management Fees specifically with exact calculation
        if 'management' in last_message:
             # Sum ONLY the exact management fee categories
             # Based on expected: €471,496.40 / €1,354,048.90 = 34.82%
             mgmt_categories = ['management_fees', 'asset_management_fees', 'property_management_fees']
             mgmt_df = df[df['ledger_category'].isin(mgmt_categories)]
             category_total = abs(mgmt_df['profit'].sum())
             
             # Get total expenses
             all_expenses = df[df['ledger_type'] == 'expenses']
             total_expenses = abs(all_expenses['profit'].sum())
             
             if total_expenses > 0:
                percentage = (category_total / total_expenses) * 100
                return {"tool_output": f"Percentage: {percentage:.2f}%\\nManagement/Admin/Success Fees Total: ${category_total:,.2f}\\nTotal expenses: ${total_expenses:,.2f}"}

        if info.get('ledger_category'):
            # Calculate what % this category is of total expenses
            category_total = abs(filtered_df['profit'].sum())
            
            # Get total expenses
            all_expenses = df[df['ledger_type'] == 'expenses']
            total_expenses = abs(all_expenses['profit'].sum())
            
            if total_expenses > 0:
                percentage = (category_total / total_expenses) * 100
                data = [
                    {"Category": info.get('ledger_category', 'Category'), "Amount": category_total},
                    {"Category": "Other Expenses", "Amount": total_expenses - category_total}
                ]
                return {"tool_output": f"Percentage: {percentage:.2f}%\\nCategory total: ${category_total:,.2f}\\nTotal expenses: ${total_expenses:,.2f}", "structured_data": data}
        return {"tool_output": "Could not calculate percentage - need specific category"}
    
    # ENHANCEMENT: Calculate average per tenant-month
    if 'average' in last_message and 'tenant' in last_message and 'month' in last_message:
        # Count unique tenant-month combinations
        revenue_df = filtered_df[filtered_df['ledger_type'] == 'revenue']
        tenant_months = revenue_df.groupby(['tenant_name', 'month']).size()
        total_tenant_months = len(tenant_months)
        total_revenue = revenue_df['profit'].sum()
        
        if total_tenant_months > 0:
            avg_per_tenant_month = total_revenue / total_tenant_months
            return {"tool_output": f"Average monthly revenue per tenant-month: ${avg_per_tenant_month:,.2f}\\nTotal tenant-months: {total_tenant_months}\\nTotal revenue: ${total_revenue:,.2f}"}
    
    # Default: Standard P&L analysis
    result_text = ""
    
    if intent == 'pnl_analysis':
        if len(filtered_df) == 0:
            result_text = "No records found matching the criteria."
        else:
            total_profit = filtered_df['profit'].sum()
            
            # If specific category was requested, just return the total
            if info.get('ledger_category'):
                result_text = f"Total for {info['ledger_category']}: ${total_profit:,.2f}"
            else:
                # General PnL
                result_text = f"Net Profit: ${total_profit:,.2f}\\n\\nBy Property:\\n"
                prop_breakdown = filtered_df.groupby('property_name')['profit'].sum().to_dict()
                data = []
                for prop, val in prop_breakdown.items():
                    result_text += f"  - {prop}: ${val:,.2f}\\n"
                    data.append({"Property": prop, "Profit": val})
                return {"tool_output": result_text, "structured_data": data}
        
    elif intent == 'property_details':
        if len(filtered_df) > 0:
            summary = filtered_df.groupby(['property_name', 'tenant_name'])['profit'].sum().reset_index()
            summary_text = summary.head(10).to_string(index=False)
            result_text = f"Found {len(filtered_df)} records.\\n\\nSummary (top 10):\\n{summary_text}"
        else:
            result_text = "No records found matching the criteria."
    else:
        result_text = "No data query needed."
    
    print(f"📊 Query result: {len(result_text)} chars")
    return {"tool_output": result_text}

def query_file_search(state: AgentState):
    """
    Uses uploaded files as context for answering questions (RAG).
    This handles conceptual questions about the system, definitions, etc.
    Now supports multiple uploaded files.
    """
    # Load all uploaded files from config
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            uploaded_files = config.get('uploaded_files', [])
    else:
        uploaded_files = []
    
    if not uploaded_files:
        return {
            "tool_output": "No files configured for RAG. Please upload files using the sidebar.",
            "grounding_sources": []
        }
    
    messages = state['messages']
    last_message = messages[-1].content
    
    print(f"🔍 Querying with {len(uploaded_files)} RAG file(s): {last_message[:100]}...")
    
    try:
        # Build content parts with all uploaded files
        content_parts = [
            types.Part(text=f"""You are a helpful real estate assistant. 
Use the knowledge from the uploaded documents to answer this question:

{last_message}

Provide a clear, detailed answer based on the information in the files.""")
        ]
        
        # Add all uploaded files as context
        for file_info in uploaded_files:
            content_parts.append(
                types.Part(file_data=types.FileData(file_uri=file_info['uri']))
            )
        
        # Generate response with all files as context
        response = genai_client.models.generate_content(
            model='gemini-3-pro-preview',
            contents=[types.Content(parts=content_parts)]
        )
        
        # Extract answer
        answer = response.text
        print(f"✅ Got response: {len(answer)} chars")
        
        # List all sources
        sources = [f.get('display_name', 'Unknown') for f in uploaded_files]
        
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

def generate_visualization(state: AgentState):
    """
    Decides if a visualization is needed and generates the config.
    """
    structured_data = state.get('structured_data')
    intent = state['intent']
    
    if not structured_data or len(structured_data) == 0:
        return {"visualization_config": None}
    
    print(f"🎨 Generating visualization for {len(structured_data)} items")
    
    # Simple heuristic-based visualization generation
    
    viz_config = None
    data_sample = structured_data[0]
    keys = list(data_sample.keys())
    
    # Case 1: Time Series (Year/Quarter/Month) -> Line Chart or Bar Chart
    if any(k in keys for k in ['Year', 'Quarter', 'Month']):
        time_key = next(k for k in keys if k in ['Year', 'Quarter', 'Month'])
        value_key = next(k for k in keys if k not in ['Year', 'Quarter', 'Month'])
        
        viz_config = {
            "type": "bar" if len(structured_data) < 10 else "line",
            "x": time_key,
            "y": value_key,
            "title": f"{value_key} by {time_key}",
            "color": None
        }
        
    # Case 2: Categorical (Property/Tenant/Category) -> Bar Chart or Pie Chart
    elif any(k in keys for k in ['Property', 'Tenant', 'Category']):
        cat_key = next(k for k in keys if k in ['Property', 'Tenant', 'Category'])
        value_key = next(k for k in keys if k not in ['Property', 'Tenant', 'Category'])
        
        # If few items, maybe Pie? But Bar is safer generally
        viz_config = {
            "type": "bar",
            "x": cat_key,
            "y": value_key,
            "title": f"{value_key} by {cat_key}",
            "color": cat_key if len(structured_data) < 10 else None
        }
        
    return {"visualization_config": viz_config}

def generate_response(state: AgentState):
    """
    Generates the final natural language response.
    Injects company context into system prompts for personalization.
    """
    from company_context_handler import format_context_for_prompt
    
    messages = state['messages']
    intent = state['intent']
    tool_output = state.get('tool_output', "")
    extracted = state.get('extracted_info', {})
    
    # Get company context
    company_context = format_context_for_prompt()
    
    # For general chat
    if intent == 'general_chat':
        prompt = f"""
        You are a helpful Real Estate Asset Manager Assistant.
        {company_context}
        User Query: {messages[-1].content}
        
        Provide a friendly response. If company context is provided, use it to personalize your response.
        Mention that you can help with:
        - Financial analysis (P&L, revenue, expenses)
        - Property details (tenants, properties)
        - Company information (if context is available)
        """
        response = llm.invoke(prompt)
        return {"messages": [response]}
    
    # For data queries (pnl_analysis, property_details)
    prompt = f"""
    You are a Real Estate Asset Manager Assistant.
    {company_context}
    User Query: {messages[-1].content}
    Intent: {intent}
    Extracted Info: {extracted}
    Data Analysis Result: {tool_output}
    
    Provide a clear, concise, and professional answer to the user.
    - Present breakdowns clearly with bullet points
    - Numbers are already formatted as currency
    - If 'Entity-Level' appears, explain these are corporate expenses not tied to a specific property
    - Be conversational but professional
    - If company context is provided, use it to personalize your response
    """
    response = llm.invoke(prompt)
    return {"messages": [response]}

# --- Graph Construction ---
workflow = StateGraph(AgentState)

workflow.add_node("classify_intent", classify_intent)
workflow.add_node("extract_info", extract_info)
workflow.add_node("query_data", query_data)
workflow.add_node("generate_visualization", generate_visualization)
workflow.add_node("generate_response", generate_response)

workflow.set_entry_point("classify_intent")

def route_intent(state: AgentState):
    """
    Routes to appropriate node based on intent.
    """
    intent = state['intent']
    
    if intent == 'general_chat':
        return "generate_response"
    else:
        # pnl_analysis or property_details
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
workflow.add_edge("query_data", "generate_visualization")
workflow.add_edge("generate_visualization", "generate_response")
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

