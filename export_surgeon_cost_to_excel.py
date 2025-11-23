import pandas as pd

src = 'surgeon_cost_analysis.csv'
out = 'surgeon_cost_analysis.xlsx'

# Read CSV (handle potential index column)
df = pd.read_csv(src)

# If the first column looks like an index, try to rename it
if 'Unnamed: 0' in df.columns and 'Surgeon' not in df.columns:
    df = df.rename(columns={'Unnamed: 0': 'Surgeon'})

# Write to Excel
with pd.ExcelWriter(out, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Surgeon Cost Analysis')

print(f"Excel file created: {out}")
print(f"Rows: {len(df)}, Columns: {list(df.columns)}")
