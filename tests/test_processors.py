"""
Tests para el módulo de procesamiento de datos.

Incluye tests para:
- ExcelReader
- DataNormalizer
- Modelos de datos
- FinancialAnalyzer
- QAGenerator
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import os

# Importar módulos a testear
from src.processors.models import (
    Account,
    BalanceSheet,
    Period,
    PeriodType,
    Priority,
    Status,
    QAItem,
    QAReport,
)
from src.processors.data_normalizer import DataNormalizer
from src.processors.financial_analyzer import (
    FinancialAnalyzer,
    AnalysisConfig,
    VariationType,
)
from src.processors.qa_generator import QAGenerator, DEFAULT_ILV_MAPPING


class TestPeriod:
    """Tests para la clase Period."""
    
    def test_from_string_monthly(self):
        """Test parsing de periodo mensual."""
        period = Period.from_string("Jan-21")
        assert period.name == "Jan-21"
        assert period.year == 2021
        assert period.month == 1
        assert period.period_type == PeriodType.MONTHLY
    
    def test_from_string_fiscal_year(self):
        """Test parsing de año fiscal."""
        period = Period.from_string("FY23")
        assert period.name == "FY23"
        assert period.year == 2023
        assert period.month is None
        assert period.period_type == PeriodType.YEARLY
    
    def test_from_string_ytd(self):
        """Test parsing de YTD."""
        period = Period.from_string("YTD24")
        assert period.name == "YTD24"
        assert period.year == 2024
        assert period.month is None
        assert period.period_type == PeriodType.YTD
    
    def test_period_comparison(self):
        """Test comparación de periodos."""
        p1 = Period.from_string("Jan-21")
        p2 = Period.from_string("Feb-21")
        p3 = Period.from_string("Jan-22")
        
        assert p1 < p2
        assert p2 < p3
        assert p1 < p3
    
    def test_to_datetime(self):
        """Test conversión a datetime."""
        period = Period.from_string("Mar-22")
        dt = period.to_datetime()
        
        assert dt is not None
        assert dt.year == 2022
        assert dt.month == 3


class TestAccount:
    """Tests para la clase Account."""
    
    def test_create_account(self):
        """Test creación de cuenta."""
        account = Account(
            code="70100000",
            description="Ventas nacionales",
            values={"Jan-21": 1000, "Feb-21": 1200}
        )
        
        assert account.code == "70100000"
        assert account.description == "Ventas nacionales"
        assert len(account.values) == 2
    
    def test_get_value(self):
        """Test obtención de valor."""
        account = Account(
            code="70100000",
            description="Ventas",
            values={"Jan-21": 1000, "Feb-21": 1200}
        )
        
        assert account.get_value("Jan-21") == 1000
        assert account.get_value("Mar-21") is None
    
    def test_calculate_variation_absolute(self):
        """Test cálculo de variación absoluta."""
        account = Account(
            code="70100000",
            description="Ventas",
            values={"FY23": 1000, "FY24": 1500}
        )
        
        var = account.calculate_variation("FY23", "FY24", as_percentage=False)
        assert var == 500
    
    def test_calculate_variation_percentage(self):
        """Test cálculo de variación porcentual."""
        account = Account(
            code="70100000",
            description="Ventas",
            values={"FY23": 1000, "FY24": 1500}
        )
        
        var = account.calculate_variation("FY23", "FY24", as_percentage=True)
        assert var == 50.0  # 50% de incremento
    
    def test_get_account_type(self):
        """Test detección de tipo de cuenta."""
        income = Account(code="70100000", description="Ventas")
        expense = Account(code="62000000", description="Servicios")
        asset = Account(code="21000000", description="Inmovilizado")
        
        assert income.get_account_type() == "ingreso"
        assert expense.get_account_type() == "gasto"
        assert asset.get_account_type() == "activo"
    
    def test_is_balance_account(self):
        """Test identificación de cuenta de balance."""
        balance_acc = Account(code="21000000", description="Inmovilizado")
        income_acc = Account(code="70100000", description="Ventas")
        
        assert balance_acc.is_balance_account() is True
        assert income_acc.is_balance_account() is False
    
    def test_is_income_statement_account(self):
        """Test identificación de cuenta de PyG."""
        balance_acc = Account(code="21000000", description="Inmovilizado")
        income_acc = Account(code="70100000", description="Ventas")
        expense_acc = Account(code="62000000", description="Servicios")
        
        assert balance_acc.is_income_statement_account() is False
        assert income_acc.is_income_statement_account() is True
        assert expense_acc.is_income_statement_account() is True


class TestBalanceSheet:
    """Tests para la clase BalanceSheet."""
    
    @pytest.fixture
    def sample_balance(self):
        """Fixture con balance de ejemplo."""
        accounts = [
            Account(
                code="70100000",
                description="Ventas nacionales",
                values={"Jan-21": 1000, "Feb-21": 1200, "Mar-21": 1100}
            ),
            Account(
                code="70200000",
                description="Ventas exportación",
                values={"Jan-21": 500, "Feb-21": 600, "Mar-21": 550}
            ),
            Account(
                code="62000000",
                description="Servicios externos",
                values={"Jan-21": -200, "Feb-21": -250, "Mar-21": -220}
            ),
        ]
        
        periods = [
            Period.from_string("Jan-21"),
            Period.from_string("Feb-21"),
            Period.from_string("Mar-21"),
        ]
        
        return BalanceSheet(accounts=accounts, periods=periods)
    
    def test_get_account_by_code(self, sample_balance):
        """Test búsqueda de cuenta por código."""
        account = sample_balance.get_account_by_code("70100000")
        assert account is not None
        assert account.description == "Ventas nacionales"
    
    def test_get_income_accounts(self, sample_balance):
        """Test obtención de cuentas de ingresos."""
        income_accounts = sample_balance.get_income_accounts()
        assert len(income_accounts) == 2
    
    def test_get_expense_accounts(self, sample_balance):
        """Test obtención de cuentas de gastos."""
        expense_accounts = sample_balance.get_expense_accounts()
        assert len(expense_accounts) == 1
    
    def test_calculate_total(self, sample_balance):
        """Test cálculo de totales."""
        total = sample_balance.calculate_total(
            "Jan-21", 
            ["70100000", "70200000"]
        )
        assert total == 1500


class TestDataNormalizer:
    """Tests para el normalizador de datos."""
    
    @pytest.fixture
    def sample_balance(self):
        """Fixture con balance de ejemplo."""
        accounts = [
            Account(
                code="70100000",
                description="Ventas",
                values={
                    "Jan-21": 1000, "Feb-21": 1200, "Mar-21": 1100,
                    "Apr-21": 1300, "May-21": 1400, "Jun-21": 1500,
                    "Jul-21": 1600, "Aug-21": 1700, "Sep-21": 1800,
                    "Oct-21": 1900, "Nov-21": 2000, "Dec-21": 2100
                }
            ),
        ]
        
        periods = [
            Period.from_string(f"{month}-21") 
            for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        ]
        
        return BalanceSheet(accounts=accounts, periods=periods)
    
    def test_calculate_fiscal_year_totals(self, sample_balance):
        """Test cálculo de totales anuales."""
        normalizer = DataNormalizer()
        totals = normalizer.calculate_fiscal_year_totals(sample_balance)
        
        assert "70100000" in totals
        assert "FY21" in totals["70100000"]
        # Suma de todos los meses
        expected = sum(range(1000, 2200, 100))  # 1000 + 1100 + ... + 2100
        assert totals["70100000"]["FY21"] == expected
    
    def test_detect_fiscal_periods(self, sample_balance):
        """Test detección de periodos fiscales."""
        normalizer = DataNormalizer()
        periods = normalizer.detect_fiscal_periods(sample_balance)
        
        assert "FY21" in periods['fiscal_years']
        assert "YTD21" in periods['ytd_periods']
        assert len(periods['monthly_periods']) == 12


class TestFinancialAnalyzer:
    """Tests para el analizador financiero."""
    
    @pytest.fixture
    def sample_balance(self):
        """Fixture con balance para análisis."""
        accounts = [
            Account(
                code="70100000",
                description="Ventas",
                values={"FY23": 1000000, "FY24": 1500000}  # +50%
            ),
            Account(
                code="62000000",
                description="Servicios externos",
                values={"FY23": -100000, "FY24": -80000}  # -20%
            ),
            Account(
                code="64000000",
                description="Gastos de personal",
                values={"FY23": -300000, "FY24": -310000}  # +3.3%
            ),
        ]
        
        periods = [
            Period.from_string("FY23"),
            Period.from_string("FY24"),
        ]
        
        return BalanceSheet(accounts=accounts, periods=periods)
    
    def test_analyze_variations(self, sample_balance):
        """Test análisis de variaciones."""
        analyzer = FinancialAnalyzer()
        variations = analyzer.analyze_variations(
            sample_balance,
            period_pairs=[("FY23", "FY24")]
        )
        
        # Debe detectar variaciones significativas
        assert len(variations) > 0
        
        # La variación del 50% en ventas debe ser de alta prioridad
        ventas_var = next(
            (v for v in variations if v.account_code == "70100000"), 
            None
        )
        assert ventas_var is not None
        assert ventas_var.percentage_variation == 50.0
    
    def test_variation_type_classification(self, sample_balance):
        """Test clasificación de tipos de variación."""
        analyzer = FinancialAnalyzer()
        variations = analyzer.analyze_variations(
            sample_balance,
            period_pairs=[("FY23", "FY24")]
        )
        
        ventas_var = next(
            (v for v in variations if v.account_code == "70100000"), 
            None
        )
        
        if ventas_var:
            assert ventas_var.variation_type == VariationType.SIGNIFICANT_INCREASE
    
    def test_generate_qa_items(self, sample_balance):
        """Test generación de items Q&A."""
        analyzer = FinancialAnalyzer()
        variations = analyzer.analyze_variations(
            sample_balance,
            period_pairs=[("FY23", "FY24")]
        )
        
        items = analyzer.generate_qa_items(variations)
        
        # Debe haber items generados
        assert len(items) > 0
        
        # Los items deben tener preguntas
        assert any(item.question is not None for item in items)


class TestQAGenerator:
    """Tests para el generador de Q&A."""
    
    def test_get_ilv_for_account(self):
        """Test mapeo ILV."""
        generator = QAGenerator()
        
        # Cuenta de ingresos
        ilv = generator.get_ilv_for_account("70100000")
        assert ilv.get('level1') == 'EBITDA'
        assert ilv.get('level2') == 'Revenue'
        
        # Cuenta de gastos
        ilv = generator.get_ilv_for_account("62000000")
        assert ilv.get('level1') == 'EBITDA'
        assert ilv.get('level2') == 'OPEX'
    
    def test_default_ilv_mapping_coverage(self):
        """Test que el mapeo ILV cubre las principales cuentas."""
        # Verificar que hay mapeo para grupos principales
        for prefix in ['10', '20', '30', '40', '50', '60', '70']:
            assert prefix in DEFAULT_ILV_MAPPING


class TestQAItem:
    """Tests para QAItem."""
    
    def test_create_qa_item(self):
        """Test creación de item Q&A."""
        item = QAItem(
            mapping_ilv_1="EBITDA",
            mapping_ilv_2="Revenue",
            mapping_ilv_3="Gross revenue",
            description="Ventas nacionales",
            account_code="70100000",
            values={"FY23": 1000000, "FY24": 1200000},
            priority=Priority.ALTA,
            status=Status.ABIERTO
        )
        
        assert item.priority == Priority.ALTA
        assert item.status == Status.ABIERTO
    
    def test_has_significant_variation(self):
        """Test detección de variación significativa."""
        item = QAItem(
            description="Test",
            account_code="70100000",
            variation_percentages={"FY23_vs_FY24": 25.0}
        )
        
        assert item.has_significant_variation(threshold=20.0) is True
        assert item.has_significant_variation(threshold=30.0) is False
    
    def test_to_dict(self):
        """Test conversión a diccionario."""
        item = QAItem(
            mapping_ilv_1="EBITDA",
            description="Ventas",
            account_code="70100000",
            priority=Priority.ALTA
        )
        
        d = item.to_dict()
        
        assert d['Mapping ILV 1'] == 'EBITDA'
        assert d['Prioridad'] == 'Alta'


class TestQAReport:
    """Tests para QAReport."""
    
    def test_count_by_priority(self):
        """Test conteo por prioridad."""
        items = [
            QAItem(description="A", account_code="1", priority=Priority.ALTA),
            QAItem(description="B", account_code="2", priority=Priority.ALTA),
            QAItem(description="C", account_code="3", priority=Priority.MEDIA),
            QAItem(description="D", account_code="4", priority=Priority.BAJA),
        ]
        
        report = QAReport(items=items)
        counts = report.count_by_priority()
        
        assert counts['Alta'] == 2
        assert counts['Media'] == 1
        assert counts['Baja'] == 1
    
    def test_get_open_items(self):
        """Test obtención de items abiertos."""
        items = [
            QAItem(description="A", account_code="1", status=Status.ABIERTO),
            QAItem(description="B", account_code="2", status=Status.CERRADO),
            QAItem(description="C", account_code="3", status=Status.ABIERTO),
        ]
        
        report = QAReport(items=items)
        open_items = report.get_open_items()
        
        assert len(open_items) == 2
