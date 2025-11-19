# Real Estate Agent - AI-Powered Property Data Analysis

An intelligent agent that answers complex questions about real estate portfolios using Google's GenAI and RAG (Retrieval Augmented Generation).

## 🎯 North Star Metric: **90% Accuracy** 
With more time and real user question understanding, we would get to 99% accuracy

This project follows an **eval-first development approach**:
1. ✅ **Evals First** - Started with comprehensive test cases (16 questions across 4 difficulty levels)
2. ✅ **Incremental Development** - Built features iteratively to improve accuracy
3. ✅ **Current Status** - **90% accuracy** on evaluation suite (14.5/16 questions correct)

This methodology ensures quality and prevents regressions as the system evolves.

---

## 🚀 Quick Start

### Installation

1. **Clone and navigate to the project**
```bash
cd real_estate_agent
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

5. **Initialize RAG system**
```bash
python scripts/setup_rag.py
```

6. **Run the application**
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 📊 Changing the Data

### Option 1: Replace Dataset
Replace the files in the `data/` directory:
- `data/cortex.csv` - Main dataset (CSV format)
- `data/cortex.parquet` - Main dataset (Parquet format, more efficient)

After changing data, re-run:
```bash
python scripts/setup_rag.py
```

### Option 2: Direct Text Input
Paste content directly in the UI text area for quick analysis.

---

## 🧪 Evaluation System

### Pre-built Eval Suite
The project includes **16 ready-to-use evaluation questions** in `data/evals.csv`:
- **Easy** (3 questions) - Basic data retrieval
- **Medium** (3 questions) - Aggregations and filtering
- **Hard** (5 questions) - Complex calculations
- **Very Hard** (5 questions) - Multi-step analytical reasoning

### Run Evaluations

**Full eval pipeline:**
```bash
# 1. Run evals (generates answers)
python scripts/run_evals.py

# 2. Grade the results
python scripts/grade_evals.py

# 3. Generate detailed report
python scripts/generate_eval_report.py
```

Results are saved in `scripts/`:
- `eval_results.json` - Agent responses
- `eval_grades.json` - Grading details
- Grading report displayed in terminal

### Add Your Own Evals

Edit `data/evals.csv` and add rows with:
- `Question_Number` - Unique identifier
- `Difficulty` - Easy, Medium, Hard, Very Hard
- `Question` - The question to ask
- `Answer` - Expected answer
- `Answer_Details` - Additional context for grading

**Example:**
```csv
17,Medium,What is the average rent per unit?,€2500,"Based on 100 units across all properties"
```

Then re-run the eval pipeline to test your new questions.

---
