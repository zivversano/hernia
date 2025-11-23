import pandas as pd

# Read the CSV file
df = pd.read_csv('rule_combinations_by_group.csv')

# Save as Excel file
output_file = 'rule_combinations_by_group.xlsx'
df.to_excel(output_file, index=False, sheet_name='Rule Combinations')

print(f"Excel file created: {output_file}")
print(f"Total rows: {len(df)}")
print(f"\nFirst few rows:")
print(df.head())
