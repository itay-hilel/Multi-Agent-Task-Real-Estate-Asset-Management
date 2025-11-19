import pandas as pd

try:
    df = pd.read_parquet('cortex.parquet')
    print(f"Unique Property Names: {df['property_name'].nunique()}")
    print(f"Unique Tenant Names: {df['tenant_name'].nunique()}")
    
    print("\nSample of rows with missing property_name:")
    print(df[df['property_name'].isnull()].head())
except Exception as e:
    print(f"Error: {e}")
