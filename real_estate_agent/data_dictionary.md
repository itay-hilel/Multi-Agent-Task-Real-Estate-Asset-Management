# Real Estate Asset Management System - Data Dictionary

**Generated on:** 2025-11-19 16:52:05

**Total Records:** 3,924

---

## 1. Dataset Overview

This dataset contains financial records (profit/loss statements) for a real estate portfolio managed by **PropCo**.

### Key Metrics:
- **Properties Managed:** 4 (excluding entity-level)
- **Unique Tenants:** 17
- **Time Period:** 2024 to 2025
- **Total Net Profit/Loss:** $1,533,331.87

---

## 2. Data Schema

### Column Descriptions:

| Column | Type | Description | Example Values |
|--------|------|-------------|----------------|
| `entity_name` | Text | Name of the managing entity | PropCo |
| `property_name` | Text | Property identifier (NULL = entity-level) | Building 180, Building 17, Building 160 |
| `tenant_name` | Text | Tenant name (NULL if not tenant-specific) | Tenant 8, Tenant 15, Tenant 10 |
| `ledger_type` | Text | Revenue or Expenses | expenses, revenue |
| `ledger_group` | Text | High-level category grouping | general_expenses, management_fees, sales_discounts, rental_income, taxes_and_insurances |
| `ledger_category` | Text | Specific expense/revenue category | bank_charges, financial_expenses, directors_fee, other_general_expenses, rent_discount_taxed |
| `ledger_code` | Integer | Internal accounting code | 4370 - 8008 |
| `ledger_description` | Text | Detailed description | Various |
| `month` | Text | Month in YYYY-MM format | 2025-M01 |
| `quarter` | Text | Quarter in YYYY-QX format | 2025-Q1 |
| `year` | Text | Year | 2025 |
| `profit` | Float | Amount (positive = revenue, negative = expense) | -$500 to $50,000 |

---

## 3. Properties in Portfolio

### Property List:
                      sum  count
property_name                   
Building 120    850567.42    246
Building 140    526658.85    841
Building 160    713065.13    482
Building 17     352566.81   1450
Building 180    384900.03    324
Entity-Level  -1294426.37    581

**Note:** "Entity-Level" represents corporate expenses not attributable to a specific property (e.g., corporate taxes, insurance, management fees).

---

## 4. Tenant Information

### Active Tenants:
                   sum  count
tenant_name                  
Tenant 1      61156.87     54
Tenant 10     23881.72    120
Tenant 11    292531.00    148
Tenant 12    166887.76    479
Tenant 13    274344.48    115
Tenant 14    391490.29    297
Tenant 15    153179.91    193
Tenant 16    115150.16    139
Tenant 17     48385.04    140
Tenant 18     91925.71    104
Tenant 2      64323.43    129
Tenant 3     204788.42    375
Tenant 4      37961.58    178
Tenant 5       9204.77     59
Tenant 6       6671.98     56
Tenant 7     880512.18    191
Tenant 8      24587.98    330
Tenant 9      17777.53     58

---

## 5. Ledger Categories Explained

### Revenue Categories:
ledger_category
revenue_rent_taxed          2031
proceeds_parking_taxed       469
proceeds_parking_untaxed     186
rent_discount_taxed          174
proceeds_rent_untaxed        136
vat_compensation             110
rent_discount_untaxed         29

**Common Revenue Sources:**
- **Rental Income:** Monthly rent payments from tenants
- **Parking Fees:** Additional charges for parking spaces
- **Late Fees:** Penalties for late rent payments
- **Other Income:** Miscellaneous revenue streams

### Expense Categories:
ledger_category
insurance_in_general        180
bank_charges                121
financial_expenses          121
other_general_expenses       76
interest_mortgage            42
research_and_information     38
directors_fee                35
real_estate_taxes            33
asset_management_fees        27
other_consultancy_costs      20
property_management_fees     19
expense_return               13
non_reclaimable_vat          12
other_management_fees        12
success_fees                 12

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
- **Total Revenue:** $2,887,652.89
- **Total Expenses:** $1,354,321.02
- **Net Operating Income:** $1,533,331.87

### By Year:
year
2024    1171521.55
2025     361810.32

### By Quarter:
quarter
2024-Q1    262309.07
2024-Q2    317892.76
2024-Q3    312364.85
2024-Q4    278954.87
2025-Q1    361810.32

### Top 10 Profitable Properties:
property_name
Building 120     850567.42
Building 160     713065.13
Building 140     526658.85
Building 180     384900.03
Building 17      352566.81
Entity-Level   -1294426.37

### Top 10 Loss-Making Properties:
property_name
Entity-Level   -1294426.37
Building 17      352566.81
Building 180     384900.03
Building 140     526658.85
Building 160     713065.13
Building 120     850567.42

---

## 7. Data Quality Notes

### Missing Data:
- **Property Name:** 581 records (14.8%)
  - These are entity-level expenses (corporate overhead, taxes, etc.)
- **Tenant Name:** 759 records (19.3%)
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
- Rows: 3,924
- Columns: 12

### Access Methods:
- **Direct Pandas Query:** For numerical calculations, aggregations, filtering
- **File Search RAG:** For conceptual questions, definitions, system understanding

---

**End of Data Dictionary**
