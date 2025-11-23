import pandas as pd
import numpy as np

# Read the Excel file
df = pd.read_excel('hernia for copilot.xlsx')

# Display the first few rows to understand the data structure
print("Data Overview:")
print(df.head())
print(f"\nColumns: {df.columns.tolist()}")
print(f"\nData shape: {df.shape}")

# Try to identify surgeon, cost, and case number columns
surgeon_col = None
cost_col = None
case_col = None

for col in df.columns:
    col_lower = str(col).lower()
    if 'surgeon' in col_lower or 'doctor' in col_lower or 'physician' in col_lower:
        surgeon_col = col
    if 'cost' in col_lower or 'price' in col_lower or 'charge' in col_lower or 'amount' in col_lower:
        cost_col = col
    if 'case' in col_lower and ('number' in col_lower or 'num' in col_lower or 'id' in col_lower):
        case_col = col

print(f"\nIdentified columns:")
print(f"Surgeon: {surgeon_col}")
print(f"Cost: {cost_col}")
print(f"Case: {case_col}")

if surgeon_col and cost_col and case_col:
    # Calculate total cost per unique case number
    case_costs = df.groupby(case_col)[cost_col].sum().reset_index()
    case_costs.columns = [case_col, 'total_cost']
    
    # Get surgeon for each case (assuming one surgeon per case)
    case_surgeon = df.groupby(case_col)[surgeon_col].first().reset_index()
    
    # Merge to get surgeon and total cost per case
    case_data = case_surgeon.merge(case_costs, on=case_col)
    
    # Calculate average surgery cost per surgeon
    surgeon_stats = case_data.groupby(surgeon_col).agg({
        'total_cost': ['mean', 'count', 'std', 'min', 'max']
    }).round(2)
    
    surgeon_stats.columns = ['Average Cost', 'Number of Cases', 'Std Dev', 'Min Cost', 'Max Cost']
    surgeon_stats = surgeon_stats.sort_values('Average Cost', ascending=False)
    
    print(f"\n{'='*100}")
    print("SURGERY COST ANALYSIS BY SURGEON (Based on Unique Case Numbers)")
    print('='*100)
    print(surgeon_stats.to_string())
    
    # Calculate median to split into two groups
    median_cost = surgeon_stats['Average Cost'].median()
    
    # Categorize surgeons into expensive and cheap groups
    expensive_surgeons = surgeon_stats[surgeon_stats['Average Cost'] >= median_cost]
    cheap_surgeons = surgeon_stats[surgeon_stats['Average Cost'] < median_cost]
    
    print(f"\n{'='*100}")
    print(f"EXPENSIVE SURGEONS (Above or At Median: ${median_cost:,.2f})")
    print('='*100)
    print(expensive_surgeons.to_string())
    
    print(f"\n{'='*100}")
    print(f"CHEAPER SURGEONS (Below Median: ${median_cost:,.2f})")
    print('='*100)
    print(cheap_surgeons.to_string())
    
    print(f"\n{'='*100}")
    print("SUMMARY STATISTICS")
    print('='*100)
    print(f"Total unique cases: {len(case_data)}")
    print(f"Total surgeons: {len(surgeon_stats)}")
    print(f"Median surgery cost: ${median_cost:,.2f}")
    print(f"Number of expensive surgeons: {len(expensive_surgeons)}")
    print(f"Number of cheaper surgeons: {len(cheap_surgeons)}")
    print(f"Average cost (expensive group): ${expensive_surgeons['Average Cost'].mean():,.2f}")
    print(f"Average cost (cheaper group): ${cheap_surgeons['Average Cost'].mean():,.2f}")
    
    # Save results to CSV
    output_file = 'surgeon_cost_analysis.csv'
    surgeon_stats_export = surgeon_stats.copy()
    surgeon_stats_export['Group'] = surgeon_stats_export['Average Cost'].apply(
        lambda x: 'Expensive' if x >= median_cost else 'Cheap'
    )
    surgeon_stats_export.to_csv(output_file)
    print(f"\nResults saved to: {output_file}")
    
else:
    print("\nError: Could not automatically identify required columns.")
    print("Please check the column names in your data.")
    print(f"Available columns: {df.columns.tolist()}")
    print("\nLooking for columns containing:")
    print("- Surgeon/Doctor/Physician")
    print("- Cost/Price/Charge/Amount")
    print("- Case Number/Case ID")
