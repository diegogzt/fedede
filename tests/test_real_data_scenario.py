import pytest
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

from src.processors.excel_reader import ExcelReader
from src.processors.data_normalizer import DataNormalizer
from src.processors.financial_analyzer import FinancialAnalyzer
from src.processors.qa_generator import QAGenerator
from src.processors.excel_exporter import ExcelExporter
from src.processors.models import BalanceSheet, PeriodType, Priority
from src.config.translations import Language

# Ruta al archivo de ejemplo
EXAMPLE_FILE = Path("examples/Balance SyS 2021-Ago25.xlsx - SyS 2021-Ago25 (1).csv")
OUTPUT_DIR = Path("data/output")

@pytest.fixture(scope="module")
def real_data_balance():
    """Fixture que carga el balance real una sola vez para todos los tests."""
    if not EXAMPLE_FILE.exists():
        pytest.skip(f"El archivo de ejemplo no existe: {EXAMPLE_FILE}")
    
    reader = ExcelReader(EXAMPLE_FILE)
    df = reader.read()
    
    # Convertir a BalanceSheet
    # Nota: ExcelReader devuelve un DataFrame, necesitamos convertirlo a BalanceSheet
    # Esto normalmente lo hace el Orchestrator o se hace manualmente mapeando columnas
    
    # Simulamos lo que haría el Orchestrator o un método de conversión
    balance = BalanceSheet(source_file=str(EXAMPLE_FILE))
    
    # Detectar columnas
    code_col = next((c for c in df.columns if str(c).lower() in ['code', 'codigo']), None)
    desc_col = next((c for c in df.columns if str(c).lower() in ['description', 'descripcion']), None)
    
    if not code_col or not desc_col:
        pytest.fail("No se pudieron detectar columnas de código o descripción")
        
    # Detectar periodos (columnas que parecen fechas)
    period_cols = [c for c in df.columns if c not in [code_col, desc_col] and not str(c).startswith('Unnamed')]
    
    # Crear periodos en el balance
    from src.processors.models import Period
    for p_name in period_cols:
        # Intentar parsear fecha
        period = Period.from_string(str(p_name))
        if period:
            balance.periods.append(period)
            
    # Crear cuentas
    from src.processors.models import Account
    from src.utils.validators import DataValidator
    
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

def test_file_loading(real_data_balance):
    """Prueba que el archivo se carga correctamente y tiene datos."""
    assert len(real_data_balance.accounts) > 0
    assert len(real_data_balance.periods) > 0
    print(f"\nCuentas cargadas: {len(real_data_balance.accounts)}")
    print(f"Periodos detectados: {len(real_data_balance.periods)}")

def test_fiscal_year_calculation(real_data_balance):
    """Prueba el cálculo de años fiscales."""
    normalizer = DataNormalizer()
    
    # Calcular totales fiscales
    fy_totals = normalizer.calculate_fiscal_year_totals(real_data_balance)
    
    assert len(fy_totals) > 0
    
    # Verificar que tenemos FY21, FY22, etc.
    first_account = next(iter(fy_totals.values()))
    print(f"\nPeriodos fiscales calculados: {list(first_account.keys())}")
    
    assert any(k.startswith("FY") for k in first_account.keys())

def test_variation_analysis(real_data_balance):
    """Prueba el análisis de variaciones."""
    normalizer = DataNormalizer()
    analyzer = FinancialAnalyzer()
    
    # Preparar datos
    fiscal_periods = normalizer.detect_fiscal_periods(real_data_balance)
    target_periods = fiscal_periods['fiscal_years'] + fiscal_periods['ytd_periods']
    
    # Agregar a periodos
    aggregated = normalizer.aggregate_to_periods(real_data_balance, target_periods)
    
    # Actualizar balance con valores agregados (simulado)
    for account in real_data_balance.accounts:
        if account.code in aggregated:
            account.values.update(aggregated[account.code])
            
    # Pares de comparación
    pairs = normalizer.get_comparison_pairs(real_data_balance)
    print(f"\nPares de comparación: {pairs}")
    
    # Analizar
    variations = analyzer.analyze_variations(real_data_balance, pairs)
    
    assert len(variations) > 0
    print(f"Variaciones detectadas: {len(variations)}")
    
    # Verificar tipos de variación
    types = {}
    for v in variations:
        t = v.variation_type.value
        types[t] = types.get(t, 0) + 1
    
    print(f"Tipos de variación: {types}")

def test_report_generation_and_reason_field(real_data_balance):
    """Prueba la generación del reporte y verifica el campo 'Reason'."""
    normalizer = DataNormalizer()
    analyzer = FinancialAnalyzer()
    generator = QAGenerator(use_ai=False) # Sin IA para ser determinista
    
    # Inyectar dependencias
    generator.normalizer = normalizer
    generator.analyzer = analyzer
    
    # Generar reporte
    report = generator.generate_report(real_data_balance, min_priority=Priority.MEDIA)
    
    assert len(report.items) > 0
    print(f"\nItems en el reporte: {len(report.items)}")
    
    # Verificar campo Reason
    items_with_reason = [i for i in report.items if i.reason]
    print(f"Items con razón: {len(items_with_reason)}")
    
    assert len(items_with_reason) > 0
    
    # Verificar contenido de algunas razones
    for item in items_with_reason[:5]:
        print(f"  - {item.account_code}: {item.reason}")
        assert isinstance(item.reason, str)
        assert len(item.reason) > 0

def test_excel_export_bilingual(real_data_balance):
    """Prueba la exportación a Excel en ambos idiomas."""
    normalizer = DataNormalizer()
    analyzer = FinancialAnalyzer()
    generator = QAGenerator(use_ai=False)
    generator.normalizer = normalizer
    generator.analyzer = analyzer
    
    report = generator.generate_report(real_data_balance, min_priority=Priority.MEDIA)
    exporter = ExcelExporter()
    
    # Asegurar directorio de salida
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Exportar Español
    es_path = OUTPUT_DIR / f"QA_Report_ES_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    exporter.export(report, str(es_path), language=Language.SPANISH)
    assert es_path.exists()
    print(f"\nReporte Español generado: {es_path}")
    
    # Exportar Inglés
    en_path = OUTPUT_DIR / f"QA_Report_EN_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    exporter.export(report, str(en_path), language=Language.ENGLISH)
    assert en_path.exists()
    print(f"Reporte Inglés generado: {en_path}")

if __name__ == "__main__":
    # Permitir ejecutar directamente
    pytest.main([__file__, "-v", "-s"])
