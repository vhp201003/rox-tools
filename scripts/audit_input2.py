import openpyxl

wb = openpyxl.load_workbook('assets/templates/arang-simulator-master.xlsx', data_only=True)

def inspect_input2():
    ws = wb['Input2']
    print("=== DETAILED INPUT2 COLUMNS (Row 1-5) ===")
    current_slot = None
    for c in range(1, ws.max_column + 1):
        r1 = ws.cell(1, c).value
        r2 = ws.cell(2, c).value
        r3 = ws.cell(3, c).value
        r4 = ws.cell(4, c).value
        print(f"Col {c} ({openpyxl.utils.get_column_letter(c)}): R1='{r1}', R2='{r2}', R3='{r3}', R4='{r4}'")

inspect_input2()
