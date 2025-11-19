import pandas as pd

try:
    df = pd.read_parquet('cortex.parquet')
    print(f"Unique Entity Names: {df['entity_name'].unique()}")
    print(df['entity_name'].value_counts())
except Exception as e:
    print(f"Error: {e}")
