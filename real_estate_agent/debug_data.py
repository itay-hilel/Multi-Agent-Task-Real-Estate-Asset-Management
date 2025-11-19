import pandas as pd
import os

# Load data
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to find cortex.csv
root_dir = os.path.dirname(current_dir)
csv_path = os.path.join(root_dir, 'cortex.csv')
df = pd.read_csv(csv_path)

print("DATA INSPECTION")
print("="*50)

# Check Year column type and values
print("\n--- YEAR COLUMN ---")
print(f"Type: {df['year'].dtype}")
print(f"Unique values: {df['year'].unique()}")
print(f"Sample values: {df['year'].head().tolist()}")

# Check Ledger Categories for Management
print("\n--- MANAGEMENT CATEGORIES ---")
mgmt = df[df['ledger_category'].str.contains('management', case=False, na=False)]
print("Unique categories matching 'management':")
print(mgmt['ledger_category'].unique())
print("\nSums by category:")
print(mgmt.groupby('ledger_category')['profit'].sum())

# Check Rent Discounts
print("\n--- RENT DISCOUNTS ---")
discounts = df[df['ledger_category'].str.contains('discount', case=False, na=False)]
print("Unique categories matching 'discount':")
print(discounts['ledger_category'].unique())
print("\nSums by category:")
print(discounts.groupby('ledger_category')['profit'].sum())

# Check Parking
print("\n--- PARKING ---")
parking = df[df['ledger_category'].str.contains('parking', case=False, na=False)]
print("Unique categories matching 'parking':")
print(parking['ledger_category'].unique())
print("\nSums by category:")
print(parking.groupby('ledger_category')['profit'].sum())

# Check Rent Revenue
print("\n--- RENT REVENUE ---")
rent = df[df['ledger_category'] == 'revenue_rent_taxed']
print(f"Sum of revenue_rent_taxed: {rent['profit'].sum()}")

# Check 2024 vs 2025
print("\n--- YEAR COMPARISON ---")
print(f"Sum 2024 (str): {df[df['year'] == '2024']['profit'].sum()}")
print(f"Sum 2024 (int): {df[df['year'] == 2024]['profit'].sum()}")
print(f"Sum 2025 (str): {df[df['year'] == '2025']['profit'].sum()}")
print(f"Sum 2025 (int): {df[df['year'] == 2025]['profit'].sum()}")
