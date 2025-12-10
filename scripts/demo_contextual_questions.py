"""Script para ver ejemplos de preguntas contextuales generadas."""
from pathlib import Path
from src.processors.excel_reader import ExcelReader
from src.processors.qa_generator import QAGenerator
from src.processors.models import Priority, BalanceSheet, Period, Account
from src.utils.validators import DataValidator

EXAMPLE_FILE = Path("examples/Balance SyS 2021-Ago25.xlsx - SyS 2021-Ago25 (1).csv")

# Cargar balance
reader = ExcelReader(EXAMPLE_FILE)
df = reader.read()

balance = BalanceSheet(source_file=str(EXAMPLE_FILE))

# Detectar columnas
code_col = next((c for c in df.columns if str(c).lower() in ['code', 'codigo']), None)
desc_col = next((c for c in df.columns if str(c).lower() in ['description', 'descripcion']), None)

# Detectar periodos
period_cols = [c for c in df.columns if c not in [code_col, desc_col] and not str(c).startswith('Unnamed')]

# Crear periodos en el balance
for p_name in period_cols:
    period = Period.from_string(str(p_name))
    if period:
        balance.periods.append(period)
        
# Crear cuentas
for _, row in df.iterrows():
    code = str(row[code_col]).strip()
    desc = str(row[desc_col]).strip()
    
    if not code or code.lower() == 'nan':
        continue
        
    account = Account(code=code, description=desc)
    
    for p_name in period_cols:
        val_str = str(row[p_name])
        val = DataValidator.parse_number(val_str)
        if val is not None:
            account.values[p_name] = val
            
    balance.accounts.append(account)

print(f"Balance cargado: {len(balance.accounts)} cuentas, {len(balance.periods)} periodos")

# Generar reporte base (sin IA)
print("\n" + "="*80)
print("GENERANDO REPORTE BASE (sin IA)...")
print("="*80)
generator_base = QAGenerator(use_ai=False)
report_base = generator_base.generate_report(balance, min_priority=Priority.ALTA)

print(f"\nReporte base: {len(report_base.items)} items")
print("\n--- EJEMPLOS DE PREGUNTAS BASE (SIN IA) ---")
for i, item in enumerate(report_base.items[:5]):
    print(f"\n{i+1}. Cuenta: {item.account_code}")
    print(f"   Descripción: {item.description}")
    print(f"   Pregunta: {item.question}")
    print(f"   Razón: {item.reason}")

# Generar reporte con IA
print("\n\n" + "="*80)
print("GENERANDO REPORTE CON IA...")
print("="*80)
generator_ai = QAGenerator(use_ai=True, ai_mode='auto')
status = generator_ai.get_ai_status()
print(f"\nEstado de IA: {status}")

if status.get('ai_enabled'):
    report_ai = generator_ai.generate_report_with_ai(balance, min_priority=Priority.ALTA)
    
    print(f"\nReporte con IA: {len(report_ai.items)} items")
    print("\n--- EJEMPLOS DE PREGUNTAS CON IA ---")
    for i, item in enumerate(report_ai.items[:5]):
        print(f"\n{i+1}. Cuenta: {item.account_code}")
        print(f"   Descripción: {item.description}")
        print(f"   Pregunta: {item.question}")
        print(f"   Razón: {item.reason}")
        print(f"   Prioridad: {item.priority.value}")
else:
    print("\nIA no disponible!")
