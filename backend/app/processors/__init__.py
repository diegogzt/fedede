"""
Módulo de Procesamiento de Datos.

Contiene las clases y funciones para:
- Lectura de archivos Excel/CSV
- Normalización de datos financieros
- Modelos de datos contables
- Análisis financiero
- Generación de Q&A
"""

from .excel_reader import ExcelReader, read_balance_file
from .data_normalizer import DataNormalizer
from .models import (
    Account, 
    BalanceSheet, 
    Period,
    PeriodType,
    Priority,
    Status,
    QAItem,
    QAReport,
)
from .financial_analyzer import (
    FinancialAnalyzer,
    AnalysisConfig,
    VariationResult,
    VariationType,
)
from .qa_generator import (
    QAGenerator,
    process_balance_to_qa,
    DEFAULT_ILV_MAPPING,
)

__all__ = [
    # Modelos
    'Account',
    'BalanceSheet',
    'Period',
    'PeriodType',
    'Priority',
    'Status',
    'QAItem',
    'QAReport',
    # Lectores
    'ExcelReader',
    'read_balance_file',
    # Normalizador
    'DataNormalizer',
    # Analizador
    'FinancialAnalyzer',
    'AnalysisConfig',
    'VariationResult',
    'VariationType',
    # Generador Q&A
    'QAGenerator',
    'process_balance_to_qa',
    'DEFAULT_ILV_MAPPING',
]
