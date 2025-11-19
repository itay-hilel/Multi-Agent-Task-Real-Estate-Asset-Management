import pandas as pd

try:
    df = pd.read_parquet('cortex.parquet')
    print("Ledger Types:")
    print(df['ledger_type'].value_counts())
    print("\nLedger Groups (Top 10):")
    print(df['ledger_group'].value_counts().head(10))
    print("\nLedger Categories (Top 10):")
    print(df['ledger_category'].value_counts().head(10))
except Exception as e:
    print(f"Error: {e}")
