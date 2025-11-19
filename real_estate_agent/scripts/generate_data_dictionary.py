"""
Generate a comprehensive data dictionary from cortex.parquet
This document will be uploaded to Google File Search for RAG queries
"""

import pandas as pd
import os
from datetime import datetime

def generate_data_dictionary():
    """
    Creates a markdown document describing the real estate data structure.
    This enables the LLM to answer questions about data structure, categories, etc.
    """
    
    # Load data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, "..", "data", "cortex.parquet")
    df = pd.read_parquet(data_path)
    
    # Fill missing property names for analysis
    df_filled = df.copy()
    df_filled['property_name'] = df_filled['property_name'].fillna('Entity-Level')
    df_filled['tenant_name'] = df_filled['tenant_name'].fillna('N/A')
    
    # Generate comprehensive documentation
    content = f"""# Real Estate Asset Management System - Data Dictionary

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Total Records:** {len(df):,}

---

## 1. Dataset Overview

This dataset contains financial records (profit/loss statements) for a real estate portfolio managed by **{df['entity_name'].iloc[0]}**.

### Key Metrics:
- **Properties Managed:** {df['property_name'].nunique() - 1} (excluding entity-level)
- **Unique Tenants:** {df['tenant_name'].nunique() - 1}
- **Time Period:** {df['year'].min()} to {df['year'].max()}
- **Total Net Profit/Loss:** ${df['profit'].sum():,.2f}

---

## 2. Data Schema

### Column Descriptions:

| Column | Type | Description | Example Values |
|--------|------|-------------|----------------|
| `entity_name` | Text | Name of the managing entity | {df['entity_name'].iloc[0]} |
| `property_name` | Text | Property identifier (NULL = entity-level) | {', '.join(df['property_name'].dropna().unique()[:3].tolist())} |
| `tenant_name` | Text | Tenant name (NULL if not tenant-specific) | {', '.join(df['tenant_name'].dropna().unique()[:3].tolist())} |
| `ledger_type` | Text | Revenue or Expenses | {', '.join(df['ledger_type'].unique().tolist())} |
| `ledger_group` | Text | High-level category grouping | {', '.join(df['ledger_group'].unique()[:5].tolist())} |
| `ledger_category` | Text | Specific expense/revenue category | {', '.join(df['ledger_category'].unique()[:5].tolist())} |
| `ledger_code` | Integer | Internal accounting code | {df['ledger_code'].min()} - {df['ledger_code'].max()} |
| `ledger_description` | Text | Detailed description | Various |
| `month` | Text | Month in YYYY-MM format | {df['month'].iloc[0]} |
| `quarter` | Text | Quarter in YYYY-QX format | {df['quarter'].iloc[0]} |
| `year` | Text | Year | {df['year'].iloc[0]} |
| `profit` | Float | Amount (positive = revenue, negative = expense) | -$500 to $50,000 |

---

## 3. Properties in Portfolio

### Property List:
{df_filled.groupby('property_name')['profit'].agg(['sum', 'count']).to_string()}

**Note:** "Entity-Level" represents corporate expenses not attributable to a specific property (e.g., corporate taxes, insurance, management fees).

---

## 4. Tenant Information

### Active Tenants:
{df_filled[df_filled['tenant_name'] != 'N/A'].groupby('tenant_name')['profit'].agg(['sum', 'count']).head(20).to_string()}

---

## 5. Ledger Categories Explained

### Revenue Categories:
{df[df['ledger_type'] == 'revenue']['ledger_category'].value_counts().to_string()}

**Common Revenue Sources:**
- **Rental Income:** Monthly rent payments from tenants
- **Parking Fees:** Additional charges for parking spaces
- **Late Fees:** Penalties for late rent payments
- **Other Income:** Miscellaneous revenue streams

### Expense Categories:
{df[df['ledger_type'] == 'expenses']['ledger_category'].value_counts().head(15).to_string()}

**Common Expense Types:**
- **Property Tax:** Annual property taxes
- **Insurance:** Property and liability insurance
- **Maintenance:** Repairs, cleaning, upkeep
- **Utilities:** Water, electricity, gas (if paid by landlord)
- **Management Fees:** Property management company fees
- **Legal & Professional:** Attorney fees, accounting
- **Marketing:** Advertising for tenant acquisition

---

## 6. Financial Performance Summary

### Overall Performance:
- **Total Revenue:** ${df[df['ledger_type'] == 'revenue']['profit'].sum():,.2f}
- **Total Expenses:** ${abs(df[df['ledger_type'] == 'expenses']['profit'].sum()):,.2f}
- **Net Operating Income:** ${df['profit'].sum():,.2f}

### By Year:
{df_filled.groupby('year')['profit'].sum().to_string()}

### By Quarter:
{df_filled.groupby('quarter')['profit'].sum().sort_index().to_string()}

### Top 10 Profitable Properties:
{df_filled.groupby('property_name')['profit'].sum().sort_values(ascending=False).head(10).to_string()}

### Top 10 Loss-Making Properties:
{df_filled.groupby('property_name')['profit'].sum().sort_values(ascending=True).head(10).to_string()}

---

## 7. Data Quality Notes

### Missing Data:
- **Property Name:** {df['property_name'].isna().sum()} records ({df['property_name'].isna().sum() / len(df) * 100:.1f}%)
  - These are entity-level expenses (corporate overhead, taxes, etc.)
- **Tenant Name:** {df['tenant_name'].isna().sum()} records ({df['tenant_name'].isna().sum() / len(df) * 100:.1f}%)
  - Common for shared expenses or vacant units

---

## 8. Example Queries

### Financial Analysis:
- "What was the total profit in 2024?"
- "Show me revenue for Building 180"
- "What were the maintenance expenses for Q1 2025?"
- "Which property is most profitable?"

### Property Details:
- "List all tenants in Building 180"
- "What are the entity-level expenses?"
- "Show me all expenses for TechCorp tenant"

### Category Explanations:
- "What does 'ledger_category' mean?"
- "Explain the difference between entity-level and property-level expenses"
- "What types of revenue do we track?"

---

## 9. Important Concepts

### Entity-Level vs Property-Level:
- **Property-Level:** Expenses/revenue directly attributable to a specific building (e.g., rent from Building 180)
- **Entity-Level:** Corporate overhead shared across all properties (e.g., corporate insurance, entity taxes)

### Profit Field Convention:
- **Positive values:** Revenue (money coming in)
- **Negative values:** Expenses (money going out)
- **Sum of all profit values:** Net Operating Income

### Time Periods:
- Data is organized by **month**, **quarter**, and **year**
- Use these fields to filter historical data
- Quarter format: YYYY-QX (e.g., 2024-Q1)

---

## 10. Technical Notes

### Data Source:
- File: `cortex.parquet`
- Format: Apache Parquet (columnar storage)
- Rows: {len(df):,}
- Columns: {len(df.columns)}

### Access Methods:
- **Direct Pandas Query:** For numerical calculations, aggregations, filtering
- **File Search RAG:** For conceptual questions, definitions, system understanding

---

**End of Data Dictionary**
"""
    
    # Save as markdown
    output_path = os.path.join(current_dir, "..", "docs", "data_dictionary.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Data dictionary generated: {output_path}")
    print(f"   Total size: {len(content)} characters")
    
    return output_path

if __name__ == "__main__":
    generate_data_dictionary()

