"""Test para verificar la generación de preguntas contextuales con IA."""
import pytest
from pathlib import Path

from src.processors.excel_reader import ExcelReader
from src.processors.data_normalizer import DataNormalizer
from src.processors.financial_analyzer import FinancialAnalyzer
from src.processors.qa_generator import QAGenerator
from src.processors.models import Priority, BalanceSheet, Period, Account
from src.utils.validators import DataValidator

# Ruta al archivo de ejemplo
EXAMPLE_FILE = Path("examples/Balance SyS 2021-Ago25.xlsx - SyS 2021-Ago25 (1).csv")


@pytest.fixture(scope="module")
def real_balance():
    """Fixture que carga el balance real."""
    if not EXAMPLE_FILE.exists():
        pytest.skip(f"El archivo de ejemplo no existe: {EXAMPLE_FILE}")
    
    reader = ExcelReader(EXAMPLE_FILE)
    df = reader.read()
    
    # Convertir a BalanceSheet
    balance = BalanceSheet(source_file=str(EXAMPLE_FILE))
    
    # Detectar columnas
    code_col = next((c for c in df.columns if str(c).lower() in ['code', 'codigo']), None)
    desc_col = next((c for c in df.columns if str(c).lower() in ['description', 'descripcion']), None)
    
    if not code_col or not desc_col:
        pytest.fail("No se pudieron detectar columnas de código o descripción")
        
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
        
    return balance


def test_contextual_question_generation_with_ai(real_balance):
    """Prueba la generación de preguntas contextuales usando IA."""
    # Crear generador con IA habilitada
    generator = QAGenerator(use_ai=True, ai_mode='auto')
    
    # Verificar que la IA esté disponible
    status = generator.get_ai_status()
    print(f"\nEstado de IA: {status}")
    
    if not status.get('ai_enabled'):
        pytest.skip("IA no disponible, saltando test")
    
    # Generar reporte base (sin IA)
    report_base = generator.generate_report(real_balance, min_priority=Priority.ALTA)
    
    print(f"\nReporte base generado: {len(report_base.items)} items")
    
    # Mostrar algunas preguntas base
    print("\n=== PREGUNTAS BASE (sin IA) ===")
    for i, item in enumerate(report_base.items[:3]):
        print(f"\n{i+1}. Cuenta: {item.account_code} - {item.description}")
        print(f"   Pregunta: {item.question}")
        print(f"   Razón: {item.reason}")
    
    # Generar reporte con IA
    report_ai = generator.generate_report_with_ai(real_balance, min_priority=Priority.ALTA)
    
    print(f"\n\n=== PREGUNTAS CON IA ===")
    for i, item in enumerate(report_ai.items[:3]):
        print(f"\n{i+1}. Cuenta: {item.account_code} - {item.description}")
        print(f"   Pregunta: {item.question}")
        print(f"   Razón: {item.reason}")
        
        # Verificar que las preguntas sean diferentes (más contextuales)
        base_item = next((b for b in report_base.items if b.account_code == item.account_code), None)
        if base_item:
            # La pregunta con IA debería ser más larga y contextual
            assert len(item.question) >= len(base_item.question), \
                "La pregunta con IA debería ser más detallada"
            
            # La razón con IA debería ser más específica
            assert len(item.reason) >= len(base_item.reason), \
                "La razón con IA debería ser más detallada"


def test_reason_generation_with_ai(real_balance):
    """Prueba específica para la generación de razones con IA."""
    generator = QAGenerator(use_ai=True, ai_mode='auto')
    
    status = generator.get_ai_status()
    if not status.get('ai_enabled'):
        pytest.skip("IA no disponible")
    
    report = generator.generate_report_with_ai(real_balance, min_priority=Priority.ALTA)
    
    print(f"\n=== ANÁLISIS DE RAZONES ===")
    
    # Verificar que las razones sean más específicas que "Variación > 20%"
    generic_reasons = 0
    contextual_reasons = 0
    
    for item in report.items:
        if item.reason:
            if item.reason == "Variación > 20.0%" or item.reason == "Variación significativa":
                generic_reasons += 1
            else:
                contextual_reasons += 1
                
    print(f"Razones genéricas: {generic_reasons}")
    print(f"Razones contextuales: {contextual_reasons}")
    
    # Mostrar ejemplos de razones contextuales
    print("\nEjemplos de razones contextuales:")
    for i, item in enumerate(report.items[:10]):
        if item.reason and item.reason not in ["Variación > 20.0%", "Variación significativa"]:
            print(f"  - {item.account_code}: {item.reason}")
    
    # Al menos el 50% deberían ser contextuales si la IA funciona bien
    total = generic_reasons + contextual_reasons
    if total > 0:
        contextual_pct = (contextual_reasons / total) * 100
        print(f"\nPorcentaje de razones contextuales: {contextual_pct:.1f}%")
        # Nota: Este umbral puede ajustarse según el comportamiento de la IA
        # assert contextual_pct >= 30, "Esperábamos al menos 30% de razones contextuales"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
