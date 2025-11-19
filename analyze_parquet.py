import pandas as pd

try:
    df = pd.read_parquet('cortex.parquet')
    print(f"Shape: {df.shape}")
    print("\nColumns:")
    print(df.columns.tolist())
    print("\nTypes:")
    print(df.dtypes)
    print("\nHead:")
    print(df.head())
    print("\nMissing Values:")
    print(df.isnull().sum())
except Exception as e:
    print(f"Error reading parquet file: {e}")
