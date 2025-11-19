import pandas as pd

# Load data
df = pd.read_csv('cortex.csv')

print("--- Q8: MANAGEMENT FEES INVESTIGATION ---")
# Filter for potential management fee categories
mgmt_keywords = ['management', 'admin', 'fee', 'director', 'professional', 'legal', 'audit']
mgmt_df = df[df['ledger_category'].str.contains('|'.join(mgmt_keywords), case=False, na=False)]
print(mgmt_df.groupby('ledger_category')['profit'].sum().sort_values())

print("\n--- Q12: RENT REVENUE INVESTIGATION ---")
# Filter for rent revenue
rent_keywords = ['rent', 'revenue', 'lease']
rent_df = df[df['ledger_category'].str.contains('|'.join(rent_keywords), case=False, na=False)]
print(rent_df.groupby('ledger_category')['profit'].sum().sort_values(ascending=False))

print("\n--- Q14: NOI INVESTIGATION ---")
# List all expense categories and their sums to find the ~3.6k difference
exp_df = df[df['ledger_type'] == 'expenses']
print(exp_df.groupby('ledger_category')['profit'].sum().sort_values())
