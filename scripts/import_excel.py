from openpyxl import load_workbook

workbook = load_workbook("data/knowledge.xlsx")

print("Sheets found:")

for sheet in workbook.sheetnames:
    print("-", sheet)