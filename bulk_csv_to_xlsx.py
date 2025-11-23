import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

csv_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith('.csv')]
if not csv_files:
    print('No CSV files found.')
    raise SystemExit(0)

print('Found CSV files:')
for f in csv_files:
    print('-', f)

created = []
failed = []
for csv_name in csv_files:
    src_path = os.path.join(BASE_DIR, csv_name)
    xlsx_name = os.path.splitext(csv_name)[0] + '.xlsx'
    out_path = os.path.join(BASE_DIR, xlsx_name)

    # Try multiple encodings for safety
    df = None
    for enc in (None, 'utf-8', 'utf-8-sig', 'latin1'):
        try:
            if enc is None:
                df = pd.read_csv(src_path)
            else:
                df = pd.read_csv(src_path, encoding=enc)
            break
        except Exception as e:
            last_err = e
            df = None
    if df is None:
        failed.append((csv_name, str(last_err)))
        continue

    # Sheet name max 31 chars
    sheet_name = os.path.splitext(csv_name)[0][:31]

    try:
        with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        created.append(out_path)
    except Exception as e:
        failed.append((csv_name, str(e)))

print('\nCreated Excel files:')
for p in created:
    print('-', os.path.basename(p))

if failed:
    print('\nFailures:')
    for name, err in failed:
        print(f'- {name}: {err}')
