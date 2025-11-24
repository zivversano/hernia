import pandas as pd

# Read the Excel file
df = pd.read_excel('hernia for copilot.xlsx')

print("Data Overview:")
print(df.head())
print(f"\nColumns: {df.columns.tolist()}")
print(f"\nData shape: {df.shape}")

# Identify relevant columns
case_col = None
item_col = None
surgeon_col = None
price_col = None

for col in df.columns:
    col_lower = str(col).lower()
    if 'case' in col_lower and ('number' in col_lower or 'num' in col_lower or 'id' in col_lower):
        case_col = col
    if 'item' in col_lower and 'price' not in col_lower and 'hospital' not in col_lower and 'copy' not in col_lower:
        if item_col is None or len(str(col)) < len(str(item_col)):
            item_col = col
    if 'surgeon' in col_lower or 'doctor' in col_lower or 'physician' in col_lower:
        surgeon_col = col
    if 'effective' in col_lower and 'price' in col_lower:
        price_col = col

print(f"\nIdentified columns:")
print(f"Case: {case_col}")
print(f"Item: {item_col}")
print(f"Surgeon: {surgeon_col}")
print(f"Price: {price_col}")

if case_col and item_col and surgeon_col:
    # Step 1: Build case-level data with combination string
    print(f"\n{'='*80}")
    print("Building Surgery Combinations...")
    print('='*80)
    
    # Group items by case
    case_items = df.groupby(case_col)[item_col].apply(lambda x: ' + '.join(sorted(x))).reset_index()
    case_items.columns = [case_col, 'combination']
    
    # Get surgeon for each case
    case_surgeon = df.groupby(case_col)[surgeon_col].first().reset_index()
    
    # Get total amount per case if price column exists
    if price_col:
        case_total = df.groupby(case_col)[price_col].sum().reset_index()
        case_total.columns = [case_col, 'total_amount']
    else:
        case_total = pd.DataFrame({case_col: case_items[case_col], 'total_amount': 0})
    
    # Merge all case-level info
    case_data = case_items.merge(case_surgeon, on=case_col).merge(case_total, on=case_col)
    
    # Load surgeon group mapping
    group_map = None
    try:
        grp = pd.read_csv('surgeon_cost_analysis.csv')
        surgeon_name_col = None
        for c in grp.columns:
            if 'surgeon' in str(c).lower():
                surgeon_name_col = c
                break
        if surgeon_name_col is None:
            surgeon_name_col = grp.columns[0]
        if 'Group' in grp.columns:
            group_map = dict(zip(grp[surgeon_name_col], grp['Group']))
    except Exception as e:
        print(f"Warning: Could not load surgeon groups ({e})")
    
    # Add surgeon group to case data
    if group_map:
        case_data['surgeon_group'] = case_data[surgeon_col].map(group_map)
    else:
        case_data['surgeon_group'] = 'Unknown'
    
    print(f"\nTotal unique cases: {len(case_data)}")
    print(f"\nSample case-level data (first 5):")
    print(case_data.head().to_string(index=False))
    
    # Step 2: Aggregate by combination
    print(f"\n{'='*80}")
    print("Aggregating by Combination...")
    print('='*80)
    
    combo_agg = case_data.groupby('combination').agg({
        case_col: 'count',
        'total_amount': 'sum',
        surgeon_col: lambda x: ', '.join(sorted(set(x)))
    }).reset_index()
    combo_agg.columns = ['combination', 'frequency', 'total_amount', 'surgeons']
    combo_agg['avg_amount_per_case'] = combo_agg['total_amount'] / combo_agg['frequency']
    combo_agg = combo_agg.sort_values('frequency', ascending=False)
    
    print(f"\nTotal unique combinations: {len(combo_agg)}")
    print(f"\nTop 20 Most Frequent Combinations:")
    print('='*80)
    for idx, row in combo_agg.head(20).iterrows():
        combo_preview = row['combination'][:60] + '...' if len(row['combination']) > 60 else row['combination']
        surgeon_preview = row['surgeons'][:30] + '...' if len(row['surgeons']) > 30 else row['surgeons']
        print(f"\nFrequency: {row['frequency']} | Total Amount: ₪{row['total_amount']:,.2f}")
        print(f"Combination: {combo_preview}")
        print(f"Surgeons: {surgeon_preview}")
    
    # Save detailed case-level data
    case_output = 'surgery_case_combinations.xlsx'
    with pd.ExcelWriter(case_output, engine='openpyxl') as writer:
        case_data.to_excel(writer, index=False, sheet_name='Case Level')
    print(f"\n{'='*80}")
    print(f"Case-level data saved to: {case_output}")
    print(f"Columns: case_number, combination, surgeon, total_amount")
    
    # Save aggregated combination data
    combo_output = 'combination_frequency_summary.xlsx'
    with pd.ExcelWriter(combo_output, engine='openpyxl') as writer:
        combo_agg.to_excel(writer, index=False, sheet_name='Combination Summary')
    print(f"\nAggregated data saved to: {combo_output}")
    print(f"Columns: combination, frequency, total_amount, avg_amount_per_case, surgeons")
    
    # Also save as CSV for easy viewing
    case_data.to_csv('surgery_case_combinations.csv', index=False)
    combo_agg.to_csv('combination_frequency_summary.csv', index=False)
    print(f"\nCSV versions also saved.")
    
    # Step 3: Create frequent combinations by surgeon group
    print(f"\n{'='*80}")
    print("Frequent Combinations by Surgeon Group...")
    print('='*80)
    
    if group_map:
        # Aggregate by combination and surgeon group
        combo_by_group = case_data.groupby(['combination', 'surgeon_group']).agg({
            case_col: 'count',
            'total_amount': 'sum'
        }).reset_index()
        combo_by_group.columns = ['combination', 'surgeon_group', 'frequency', 'total_amount']
        combo_by_group['avg_amount_per_case'] = combo_by_group['total_amount'] / combo_by_group['frequency']
        combo_by_group = combo_by_group.sort_values(['frequency', 'surgeon_group'], ascending=[False, True])
        
        print(f"\nTop 15 combinations by group:")
        print('='*80)
        for group in sorted(combo_by_group['surgeon_group'].unique()):
            group_data = combo_by_group[combo_by_group['surgeon_group'] == group].head(5)
            print(f"\n{group} Group - Top 5:")
            for idx, row in group_data.iterrows():
                combo_preview = row['combination'][:50] + '...' if len(row['combination']) > 50 else row['combination']
                print(f"  Freq: {row['frequency']:3d} | Total: ₪{row['total_amount']:>10,.2f} | Avg/Case: ₪{row['avg_amount_per_case']:>9,.2f} | {combo_preview}")
        
        # Save by-group analysis
        group_output = 'frequent_combinations_by_surgeon_group.xlsx'
        with pd.ExcelWriter(group_output, engine='openpyxl') as writer:
            combo_by_group.to_excel(writer, index=False, sheet_name='By Surgeon Group')
        combo_by_group.to_csv('frequent_combinations_by_surgeon_group.csv', index=False)
        
        print(f"\n{'='*80}")
        print(f"Combinations by surgeon group saved to:")
        print(f"- {group_output}")
        print(f"- frequent_combinations_by_surgeon_group.csv")
    else:
        print("\nSkipping group analysis - surgeon groups not available")
    
else:
    print("\nError: Could not identify required columns")
    print(f"Available columns: {df.columns.tolist()}")
