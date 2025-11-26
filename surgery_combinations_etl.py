import pandas as pd
import re

def extract_data():
    df = pd.read_excel('hernia for copilot.xlsx')
    return df

def identify_columns(df):
    case_col = item_col = surgeon_col = price_col = None
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
    return case_col, item_col, surgeon_col, price_col

def extract_surgeon_groups():
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
            return dict(zip(grp[surgeon_name_col], grp['Group']))
    except Exception as e:
        print(f"Warning: Could not load surgeon groups ({e})")
    return None

def transform_case_level(df, case_col, item_col, surgeon_col, price_col, group_map):
    def combo_with_quantity(subdf):
        counts = subdf[item_col].value_counts()
        return ' + '.join([f"{item} ({counts[item]})" for item in sorted(counts.index)])
    case_items = df.groupby(case_col).apply(combo_with_quantity).reset_index()
    case_items.columns = [case_col, 'combination']
    case_surgeon = df.groupby(case_col)[surgeon_col].first().reset_index()
    if price_col:
        case_total = df.groupby(case_col)[price_col].sum().reset_index()
        case_total.columns = [case_col, 'total_amount']
    else:
        case_total = pd.DataFrame({case_col: case_items[case_col], 'total_amount': 0})
    case_data = case_items.merge(case_surgeon, on=case_col).merge(case_total, on=case_col)
    if group_map:
        case_data['surgeon_group'] = case_data[surgeon_col].map(group_map)
    else:
        case_data['surgeon_group'] = 'Unknown'
    # Add all surgeons for each combination
    combo_to_surgeons = case_data.groupby('combination')[surgeon_col].apply(lambda x: ', '.join(sorted(set(x)))).to_dict()
    case_data['all_surgeons_for_combination'] = case_data['combination'].map(combo_to_surgeons)
    return case_data

def transform_combination_summary(case_data, case_col, surgeon_col):
    def total_item_quantity(combination_str):
        return sum([int(q) for q in re.findall(r'\((\d+)\)', combination_str)])
    combo_agg = case_data.groupby('combination').agg({
        case_col: 'count',
        'total_amount': 'sum',
        surgeon_col: lambda x: ', '.join(sorted(set(x)))
    }).reset_index()
    combo_agg.columns = ['combination', 'frequency', 'total_amount', 'surgeons']
    combo_agg['avg_amount_per_case'] = combo_agg['total_amount'] / combo_agg['frequency']
    combo_agg['total_item_quantity'] = combo_agg['combination'].apply(total_item_quantity)
    combo_agg = combo_agg.sort_values('frequency', ascending=False)
    return combo_agg

def transform_group_summary(case_data, case_col):
    combo_by_group = case_data.groupby(['combination', 'surgeon_group']).agg({
        case_col: 'count',
        'total_amount': 'sum'
    }).reset_index()
    combo_by_group.columns = ['combination', 'surgeon_group', 'frequency', 'total_amount']
    combo_by_group['avg_amount_per_case'] = combo_by_group['total_amount'] / combo_by_group['frequency']
    combo_by_group = combo_by_group.sort_values(['frequency', 'surgeon_group'], ascending=[False, True])
    return combo_by_group

def load_outputs(case_data, combo_agg, combo_by_group):
    case_data.to_csv('surgery_case_combinations.csv', index=False)
    combo_agg.to_csv('combination_frequency_summary.csv', index=False)
    combo_by_group.to_csv('frequent_combinations_by_surgeon_group.csv', index=False)
    with pd.ExcelWriter('surgery_case_combinations.xlsx', engine='openpyxl') as writer:
        case_data.to_excel(writer, index=False, sheet_name='Case Level')
    with pd.ExcelWriter('combination_frequency_summary.xlsx', engine='openpyxl') as writer:
        combo_agg.to_excel(writer, index=False, sheet_name='Combination Summary')
    with pd.ExcelWriter('frequent_combinations_by_surgeon_group.xlsx', engine='openpyxl') as writer:
        combo_by_group.to_excel(writer, index=False, sheet_name='By Surgeon Group')
    print("ETL process complete. Files saved:")
    print("- surgery_case_combinations.xlsx/csv")
    print("- combination_frequency_summary.xlsx/csv")
    print("- frequent_combinations_by_surgeon_group.xlsx/csv")

def main():
    print("Starting ETL process...")
    df = extract_data()
    case_col, item_col, surgeon_col, price_col = identify_columns(df)
    group_map = extract_surgeon_groups()
    case_data = transform_case_level(df, case_col, item_col, surgeon_col, price_col, group_map)
    combo_agg = transform_combination_summary(case_data, case_col, surgeon_col)
    combo_by_group = transform_group_summary(case_data, case_col)
    load_outputs(case_data, combo_agg, combo_by_group)

if __name__ == "__main__":
    main()
