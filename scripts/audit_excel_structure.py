import openpyxl
import json

wb = openpyxl.load_workbook('assets/templates/arang-simulator-master.xlsx', data_only=True)

def analyze_sheet_sections(sheet_name):
    ws = wb[sheet_name]
    print(f"==================================================")
    print(f"SHEET: {sheet_name} | Max Row: {ws.max_row}, Max Col: {ws.max_column}")
    print(f"==================================================")
    
    # Scan row 1 to 5 to find section titles
    sections = []
    for c in range(1, min(ws.max_column + 1, 60)):
        col_headers = [str(ws.cell(r, c).value or '').strip() for r in range(1, 10)]
        non_empty = [h for h in col_headers if h]
        if non_empty:
            sections.append((c, non_empty[0], non_empty[:3]))
    
    # Print distinct sections
    for col_idx, top_h, sample in sections:
        if any(keyword in top_h.lower() for keyword in ['stat', 'slot', 'weapon', 'buff', 'achievement', 'card', 'pet', 'shadow', 'input', 'title', 'guild', 'output', 'dps', 'damage', 'skill', 'debuff', 'set']):
            print(f"  Col {col_idx}: {top_h} -> {sample}")

print("ANALYZING INPUT1, INPUT2, INPUT3, OUTPUT, DEBUFF...")
for s in ['Input1', 'Input2', 'Input3', 'Output', 'Debuff of MVPMINI', 'InputTally']:
    if s in wb.sheetnames:
        analyze_sheet_sections(s)
