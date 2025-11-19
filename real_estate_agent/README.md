# Real Estate Agent with Google File Search RAG - Setup Guide

## Overview

This enhanced agent combines **two knowledge sources**:
1. **Structured Data** (cortex.parquet) → For numerical queries, aggregations, financial analysis
2. **Unstructured Documents** (File Search RAG) → For conceptual questions, definitions, system understanding

---

## Architecture Explained

### Why This Hybrid Approach?

**Problem:** Traditional agents either query databases OR search documents, not both effectively.

**Solution:** Route queries to the appropriate knowledge source:

```
User: "What was total profit in 2024?"
  → Intent: pnl_analysis
  → Source: Pandas query on parquet
  → Fast, accurate numerical result

User: "What does 'ledger_category' mean?"
  → Intent: document_search  
  → Source: Google File Search RAG
  → Conceptual explanation with citations
```

### How File Search RAG Works

**File Search** is Google's managed RAG solution:
- **Automatic chunking** of uploaded documents
- **Semantic search** across document chunks
- **Grounding citations** showing which document sections were used
- **No vector DB setup** needed - Google manages everything

**Traditional RAG** requires:
1. Manually chunk documents
2. Generate embeddings
3. Store in vector DB (Pinecone, Weaviate)
4. Query vector DB
5. Inject chunks into LLM context

**File Search** simplifies this to:
1. Upload documents
2. Query with natural language
3. Get answers with citations

---

## Step-by-Step Setup

### 1. Install Dependencies

```bash
cd real_estate_agent
pip install -r requirements.txt
```

**New dependencies added:**
- `google-genai` - Google's unified SDK for File Search
- `reportlab` - For generating PDF data dictionaries (optional)

### 2. Set Environment Variables

Create/update `.env` in the project root:

```bash
GOOGLE_API_KEY=your_google_api_key_here
```

**Getting an API Key:**
- Visit: https://aistudio.google.com/app/apikey
- Click "Create API Key"
- Copy and paste into `.env`

### 3. Generate Data Dictionary

This converts your parquet data into a searchable document:

```bash
python3 real_estate_agent/scripts/generate_data_dictionary.py
```

**What this does:**
- Analyzes `cortex.parquet`
- Creates `data_dictionary.md` with:
  - Property listings
  - Tenant information
  - Ledger category explanations
  - Financial summaries
  - Example queries
  - Data schema documentation

**Output:**
```
✅ Data dictionary generated: real_estate_agent/docs/data_dictionary.md
   Total size: ~15,000 characters
```

### 4. Setup File Search Store

This is a **one-time operation** that creates the RAG knowledge base:

```bash
python3 real_estate_agent/scripts/setup_rag.py
```

**What this does:**
1. Creates a Google File Search store (cloud-based)
2. Uploads documents:
   - `AI Developer Agent Real Estate Task.pdf` (task specification)
   - `data_dictionary.md` (generated data documentation)
3. Saves store configuration to `file_search_config.json`

**Output:**
```
📦 Creating File Search store...
✅ Store created: file_search_stores/abc123...

📤 Uploading: AI Developer Agent Real Estate Task.pdf
   ✅ Upload complete

📤 Uploading: data_dictionary.md
   ✅ Upload complete

✅ Configuration saved to: file_search_config.json
```

**Important:** The store name is saved in `file_search_config.json` - don't delete this file!

### 5. Test the Enhanced Agent

#### Command Line Interface:

```bash
python3 real_estate_agent/agent.py
```

**Try these queries:**

```
User: What does ledger_category mean?
🎯 Intent: document_search
🔍 Querying File Search...
📚 Grounding sources: data_dictionary.md

User: What was total profit in 2024?
🎯 Intent: pnl_analysis
📋 Extracted: {'year': '2024'}
📊 Query result: ...
```

#### Streamlit Web Interface:

```bash
streamlit run real_estate_agent/app.py
```

---

## Understanding the Components

### File Structure

```
real_estate_agent/
├── agent.py                     # Main agent with File Search RAG
├── app.py                       # Streamlit UI
├── requirements.txt             # Dependencies
├── data/                        # Data files
│   ├── cortex.parquet           # Financial data
│   └── evals.csv                # Evaluation dataset
├── docs/                        # Documentation
│   ├── data_dictionary.md       # Auto-generated RAG doc
│   └── eval_report.md           # Performance report
└── scripts/                     # Helper scripts
    ├── setup_rag.py             # One-time RAG setup
    ├── generate_data_dictionary.py
    ├── run_evals.py
    └── ...
```

### Intent Classification

The agent now recognizes **4 intent types**:

1. **`pnl_analysis`** → Pandas query for financial calculations
   - "What was profit in Q1?"
   - "Show me revenue for Building 180"

2. **`property_details`** → Pandas query for property/tenant info
   - "List all tenants"
   - "What properties do we manage?"

3. **`document_search`** → File Search RAG for conceptual questions
   - "What does 'entity-level' mean?"
   - "Explain the data structure"
   - "What ledger categories exist?"

4. **`general_chat`** → Simple conversational responses
   - "Hello"
   - "What can you do?"

### Data Flow Examples

**Example 1: Numerical Query**
```
User: "What was total profit in 2024?"
  ↓
classify_intent → "pnl_analysis"
  ↓
extract_info → {year: "2024"}
  ↓
query_data → Pandas: df[df['year']=='2024']['profit'].sum()
  ↓
generate_response → "Total profit in 2024 was $X,XXX"
```

**Example 2: Conceptual Query**
```
User: "What does ledger_category mean?"
  ↓
classify_intent → "document_search"
  ↓
query_file_search → Google File Search RAG
  ↓
  - Searches data_dictionary.md
  - Finds relevant section
  - Returns explanation with citations
  ↓
generate_response → Answer + grounding sources
```

---

## Advantages of This Approach

### 1. **Precision for Structured Data**
- Direct Pandas queries are faster and more accurate for numbers
- No risk of LLM hallucinating financial figures
- Can perform complex aggregations and filtering

### 2. **Flexibility for Concepts**
- File Search handles "why" and "what is" questions
- Can explain business logic and data structure
- Provides citations for transparency

### 3. **Scalability**
- Easy to add more documents:
  - Lease agreements
  - Property reports
  - Maintenance logs
  - Tenant contracts
- All become queryable without code changes

### 4. **Grounding & Trust**
- File Search provides source citations
- Users can verify answers
- Transparent about information sources

---

## Troubleshooting

### "File Search store not configured"
**Solution:** Run `python3 real_estate_agent/scripts/setup_rag.py`

### "data_dictionary.md not found"
**Solution:** Run `python3 real_estate_agent/scripts/generate_data_dictionary.py` first

### "GOOGLE_API_KEY not found"
**Solution:** Add API key to `.env` file in project root

### Import errors
**Solution:** Ensure all dependencies installed: `pip install -r requirements.txt`

### File Search returns unexpected results
**Solution:** 
1. Check which documents are in the store
2. Regenerate data dictionary with more detail
3. Add more example queries to documentation

---

## Next Steps

### Enhance Data Dictionary
Add more detailed explanations:
```python
# In generate_data_dictionary.py
content += """
## Business Logic

### Entity-Level Expenses Explained:
Entity-level expenses are corporate costs that benefit the entire
portfolio but aren't directly tied to a single property. Examples:
- Corporate insurance covering all properties
- Entity-level taxes (not property taxes)
- Management company fees
- Legal fees for corporate matters
"""
```

### Add More Documents
```python
# Upload property reports, lease agreements, etc.
upload_op = client.file_search_stores.upload_to_file_search_store(
    file_search_store_name=store.name,
    file='property_reports/building_180_report.pdf'
)
```

### Update Streamlit UI
- Show grounding sources
- Add toggle for "Show sources"
- Display which knowledge source was used

---

## Cost Considerations

**Google File Search Pricing:**
- Storage: ~$0.30 per GB/month
- Queries: Included in Gemini API pricing
- Small docs (< 100MB): Negligible cost

**Comparison to Vector DB:**
- No separate vector DB subscription needed
- No embedding generation costs
- Simpler infrastructure

---

## Summary

You've now built a **hybrid AI agent** that:
✅ Answers numerical questions with precision (Pandas)
✅ Explains concepts with context (File Search RAG)
✅ Provides source citations for transparency
✅ Handles multiple query types intelligently

This is production-ready for a real estate asset management system!

