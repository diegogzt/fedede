"""Script para verificar que no hay 'nan' en las preguntas generadas."""
from src.processors.excel_reader import ExcelReader
from src.processors.qa_generator import QAGenerator
from src.processors.models import Priority
from pathlib import Path
import traceback

# Leer archivo
file_path = Path('examples/Balance SyS 2021-Ago25.xlsx - SyS 2021-Ago25 (1).csv')
reader = ExcelReader(file_path)
reader.read()
balance = reader.to_balance_sheet()

# Generar Q&A SIN IA para probar reglas
generator = QAGenerator(use_ai=False)
report = generator.generate_report(balance, include_all_accounts=True, min_priority=Priority.BAJA)

# Buscar preguntas con nan (el valor especial, no subcadenas)
nan_questions = []
for item in report.items:
    if item.question:
        # Buscar "nan" como palabra completa o como valor (e.g., "nan%", " nan ", "nan,")
        import re
        # Patrón: nan que no sea parte de otra palabra (como "financiero", "ganancia")
        if re.search(r'\bnan\b|nan%|nan\s|nan$', item.question.lower()):
            nan_questions.append((item.account_code, item.question[:100]))

print(f'Total items: {len(report.items)}')
print(f'Preguntas con nan: {len(nan_questions)}')

if nan_questions:
    print('\nEjemplos de preguntas con nan:')
    for acc, q in nan_questions[:10]:
        print(f'  {acc}: {q}...')
else:
    print('\n✅ ÉXITO: Ninguna pregunta contiene "nan"')

# Exportar a Excel para verificar
output_path = Path('data/output/test_output.xlsx')
try:
    generator.export_to_excel_with_tabs(report, output_path, project_name="Test Project")
    print(f'\nExcel exportado a: {output_path}')
except Exception as e:
    print(f'\nError al exportar: {e}')
    traceback.print_exc()
