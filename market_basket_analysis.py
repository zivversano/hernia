import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

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

for col in df.columns:
    col_lower = str(col).lower()
    if 'case' in col_lower and ('number' in col_lower or 'num' in col_lower or 'id' in col_lower):
        case_col = col
    if 'item' in col_lower and 'price' not in col_lower and 'hospital' not in col_lower:
        # Use the most descriptive item column
        if item_col is None or len(str(col)) < len(str(item_col)):
            item_col = col
    if 'surgeon' in col_lower or 'doctor' in col_lower or 'physician' in col_lower:
        surgeon_col = col

print(f"\nIdentified columns:")
print(f"Case: {case_col}")
print(f"Item: {item_col}")
print(f"Surgeon: {surgeon_col}")

if case_col and item_col:
    # Create transaction list - each transaction is a list of items used in one surgery
    grouped_items = df.groupby(case_col)[item_col].apply(list)
    transactions = grouped_items.tolist()
    # Map case -> surgeon (assuming one surgeon per case)
    case_to_surgeon = df.groupby(case_col)[surgeon_col].first() if surgeon_col else None
    
    print(f"\n{'='*80}")
    print(f"Market Basket Analysis - Surgical Items")
    print('='*80)
    print(f"Total number of transactions (unique cases): {len(transactions)}")
    print(f"Total number of items across all transactions: {len(df)}")
    
    # Show sample transactions
    print(f"\nSample transactions (first 3 cases):")
    for i, trans in enumerate(transactions[:3], 1):
        print(f"\nCase {i}: {len(trans)} items")
        for item in trans[:5]:  # Show first 5 items
            print(f"  - {item}")
        if len(trans) > 5:
            print(f"  ... and {len(trans) - 5} more items")
    
    # Transform transactions into one-hot encoded format
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_encoded = pd.DataFrame(te_ary, columns=te.columns_)
    
    print(f"\n{'='*80}")
    print("One-Hot Encoded Data Shape:")
    print('='*80)
    print(f"Rows (transactions): {df_encoded.shape[0]}")
    print(f"Columns (unique items): {df_encoded.shape[1]}")
    
    # Apply Apriori algorithm with different support thresholds
    min_support = 0.05  # Item must appear in at least 5% of transactions
    
    print(f"\n{'='*80}")
    print(f"Running Apriori Algorithm (min_support={min_support})")
    print('='*80)
    
    frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)
    
    if len(frequent_itemsets) > 0:
        frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))
        frequent_itemsets = frequent_itemsets.sort_values('support', ascending=False)
        
        print(f"\nFound {len(frequent_itemsets)} frequent itemsets")
        
        # Show most frequent single items
        single_items = frequent_itemsets[frequent_itemsets['length'] == 1].head(20)
        print(f"\n{'='*80}")
        print("Top 20 Most Frequent Single Items:")
        print('='*80)
        for idx, row in single_items.iterrows():
            item = list(row['itemsets'])[0]
            support_pct = row['support'] * 100
            print(f"{item:60s} - {support_pct:6.2f}% of surgeries")
        
        # Show frequent itemsets of size 2
        itemsets_2 = frequent_itemsets[frequent_itemsets['length'] == 2].head(15)
        if len(itemsets_2) > 0:
            print(f"\n{'='*80}")
            print("Top 15 Frequent Item Pairs:")
            print('='*80)
            for idx, row in itemsets_2.iterrows():
                items = list(row['itemsets'])
                support_pct = row['support'] * 100
                print(f"{support_pct:6.2f}% - {items[0]} + {items[1]}")
        
        # Show frequent itemsets of size 3
        itemsets_3 = frequent_itemsets[frequent_itemsets['length'] == 3].head(10)
        if len(itemsets_3) > 0:
            print(f"\n{'='*80}")
            print("Top 10 Frequent Item Triplets:")
            print('='*80)
            for idx, row in itemsets_3.iterrows():
                items = list(row['itemsets'])
                support_pct = row['support'] * 100
                print(f"{support_pct:6.2f}% - {' + '.join(items)}")
        
        # Generate association rules
        print(f"\n{'='*80}")
        print("Generating Association Rules")
        print('='*80)
        
        if len(frequent_itemsets[frequent_itemsets['length'] >= 2]) > 0:
            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)
            
            if len(rules) > 0:
                # Sort by lift (strength of association)
                rules = rules.sort_values('lift', ascending=False)
                
                print(f"\nFound {len(rules)} association rules")
                
                # Show top rules by lift
                print(f"\n{'='*80}")
                print("Top 15 Association Rules (sorted by lift):")
                print('='*80)
                print(f"{'Antecedent':40s} => {'Consequent':40s} | Conf%  | Lift")
                print('-'*80)
                
                for idx, row in rules.head(15).iterrows():
                    antecedent = ', '.join(list(row['antecedents']))
                    consequent = ', '.join(list(row['consequents']))
                    confidence = row['confidence'] * 100
                    lift = row['lift']
                    
                    # Truncate long names
                    if len(antecedent) > 38:
                        antecedent = antecedent[:35] + '...'
                    if len(consequent) > 38:
                        consequent = consequent[:35] + '...'
                    
                    print(f"{antecedent:40s} => {consequent:40s} | {confidence:5.1f}% | {lift:5.2f}")
                
                # Save results to CSV files
                frequent_itemsets.to_csv('frequent_itemsets.csv', index=False)
                rules.to_csv('association_rules.csv', index=False)
                
                print(f"\n{'='*80}")
                print("Results saved to:")
                print('='*80)
                print("- frequent_itemsets.csv")
                print("- association_rules.csv")
                
                # Interpretation guide
                print(f"\n{'='*80}")
                print("Interpretation Guide:")
                print('='*80)
                print("Support:    % of surgeries that contain the itemset")
                print("Confidence: If antecedent is used, probability consequent is also used")
                print("Lift > 1:   Items appear together more often than expected by chance")
                print("Lift = 1:   Items are independent")
                print("Lift < 1:   Items appear together less often than expected")
            else:
                print("\nNo association rules found with confidence >= 50%")
                print("Try lowering the confidence threshold or minimum support")
        else:
            print("\nNot enough frequent itemsets of size >= 2 to generate rules")
            print("Try lowering the minimum support threshold")

        # ------------------------------------------------------------------
        # Per-surgeon-group frequency table for frequent itemsets
        # ------------------------------------------------------------------
        print(f"\n{'='*80}")
        print("Per-Group Frequency of Frequent Itemsets")
        print('='*80)

        # Load surgeon group labels from previous analysis if available
        group_map = None
        try:
            grp = pd.read_csv('surgeon_cost_analysis.csv')
            # Find surgeon name column
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
            print(f"Warning: Could not load surgeon_cost_analysis.csv ({e})")

        # Build case-level dataframe
        case_df = pd.DataFrame({
            'case': grouped_items.index,
            'items_set': [set(x) for x in grouped_items.values]
        })
        if case_to_surgeon is not None:
            case_df['surgeon'] = case_df['case'].map(case_to_surgeon)
            case_df['group'] = case_df['surgeon'].map(group_map) if group_map is not None else None
        else:
            case_df['surgeon'] = None
            case_df['group'] = None

        rows = []
        # Determine groups present
        groups_present = sorted([g for g in case_df['group'].dropna().unique()]) if 'group' in case_df.columns else []

        for _, r in frequent_itemsets.iterrows():
            itemset = r['itemsets']
            itemset_str = ' + '.join(sorted(list(itemset)))
            if groups_present:
                for g in groups_present:
                    subset = case_df[case_df['group'] == g]
                    freq = int(sum(itemset.issubset(s) for s in subset['items_set']))
                    rows.append({'itemset': itemset_str, 'frequency': freq, 'surgeon_group': g})
            else:
                freq = int(sum(itemset.issubset(s) for s in case_df['items_set']))
                rows.append({'itemset': itemset_str, 'frequency': freq, 'surgeon_group': 'All'})

        freq_by_group_df = pd.DataFrame(rows)
        out_path = 'frequent_itemsets_by_group.csv'
        freq_by_group_df.to_csv(out_path, index=False)
        print(f"Saved per-group frequencies to: {out_path}")
        print("Sample:")
        print(freq_by_group_df.head(12).to_string(index=False))

        # ------------------------------------------------------------------
        # Per-surgeon-group frequency for rule combinations (antecedent+consequent)
        # Each row shows the full combination in one cell, the count, and the group
        # ------------------------------------------------------------------
        try:
            if 'rules' in locals() and len(rules) > 0:
                combo_rows = []
                # Determine groups present (reuse computed groups if available)
                groups_present = sorted([g for g in case_df['group'].dropna().unique()]) if 'group' in case_df.columns else []

                # Find effective price column
                price_col = None
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'effective' in col_lower and 'price' in col_lower:
                        price_col = col
                        break

                for _, rr in rules.iterrows():
                    combo_set = set(rr['antecedents']).union(set(rr['consequents']))
                    combo_str = ' + '.join(sorted(list(combo_set)))
                    if groups_present:
                        for g in groups_present:
                            subset = case_df[case_df['group'] == g]
                            # Find cases that contain the entire combination
                            matching_cases = [c for c, s in zip(subset['case'], subset['items_set']) if combo_set.issubset(s)]
                            freq = len(matching_cases)
                            
                            # Calculate average effective price for the combination items in matching cases
                            avg_price = 0.0
                            if price_col and freq > 0:
                                # For each matching case, sum the effective prices of items in the combination
                                case_prices = []
                                for case_id in matching_cases:
                                    case_data = df[(df[case_col] == case_id) & (df[item_col].isin(combo_set))]
                                    if len(case_data) > 0:
                                        case_total = case_data[price_col].sum()
                                        case_prices.append(case_total)
                                if case_prices:
                                    avg_price = sum(case_prices) / len(case_prices)
                            
                            combo_rows.append({
                                'combination': combo_str,
                                'frequency': freq,
                                'average_price': round(avg_price, 2),
                                'surgeon_group': g
                            })
                    else:
                        matching_cases = [c for c, s in zip(case_df['case'], case_df['items_set']) if combo_set.issubset(s)]
                        freq = len(matching_cases)
                        
                        avg_price = 0.0
                        if price_col and freq > 0:
                            case_prices = []
                            for case_id in matching_cases:
                                case_data = df[(df[case_col] == case_id) & (df[item_col].isin(combo_set))]
                                if len(case_data) > 0:
                                    case_total = case_data[price_col].sum()
                                    case_prices.append(case_total)
                            if case_prices:
                                avg_price = sum(case_prices) / len(case_prices)
                        
                        combo_rows.append({
                            'combination': combo_str,
                            'frequency': freq,
                            'average_price': round(avg_price, 2),
                            'surgeon_group': 'All'
                        })

                combo_df = pd.DataFrame(combo_rows)
                combo_df = combo_df.sort_values(['combination', 'surgeon_group']).reset_index(drop=True)
                combo_out = 'rule_combinations_by_group.csv'
                combo_df.to_csv(combo_out, index=False)
                print(f"Saved rule combinations per-group to: {combo_out}")
                print("Sample:")
                print(combo_df.head(12).to_string(index=False))
            else:
                print("No association rules available to compute combination frequencies.")
        except Exception as e:
            print(f"Warning while building rule combination table: {e}")
    else:
        print(f"\nNo frequent itemsets found with min_support={min_support}")
        print("Try lowering the minimum support threshold")
        print(f"For example, try min_support=0.01 (1% of transactions)")
        
else:
    print("\nError: Could not identify required columns")
    print(f"Available columns: {df.columns.tolist()}")
