import pytest
from src.processors.data_normalizer import DataNormalizer
from src.processors.financial_analyzer import FinancialAnalyzer, VariationType, VariationResult
from src.processors.models import BalanceSheet, Account, Period, PeriodType, Priority
from src.config.settings import get_settings

@pytest.fixture
def sample_balance_sheet():
    bs = BalanceSheet()
    
    # Crear periodos
    p1 = Period(name="FY23", year=2023, period_type=PeriodType.YEARLY)
    p2 = Period(name="FY24", year=2024, period_type=PeriodType.YEARLY)
    bs.periods = [p1, p2]
    
    # Crear cuentas
    # Revenue: 1000 -> 1200
    rev = Account(code="70001", description="Revenue")
    rev.values["FY23"] = 1000.0
    rev.values["FY24"] = 1200.0
    bs.accounts.append(rev)
    
    # Cost: 500 (50%) -> 720 (60%)
    # Variación pp: 60% - 50% = 10 pp
    cost = Account(code="60001", description="Cost")
    cost.values["FY23"] = 500.0
    cost.values["FY24"] = 720.0
    bs.accounts.append(cost)
    
    return bs

def test_calculate_percentage_points_variation(sample_balance_sheet):
    normalizer = DataNormalizer()
    revenue_codes = ["70001"]
    pairs = [("FY23", "FY24")]
    
    pp_vars = normalizer.calculate_percentage_points_variation(
        sample_balance_sheet, revenue_codes, pairs
    )
    
    # Verificar Costo
    # FY23: 500/1000 = 50%
    # FY24: 720/1200 = 60%
    # Var: 10 pp
    cost_pp = pp_vars["60001"]["FY23_vs_FY24"]
    assert cost_pp == pytest.approx(10.0)
    
    # Verificar Revenue (debería ser 0 pp, 100% -> 100%)
    rev_pp = pp_vars["70001"]["FY23_vs_FY24"]
    assert rev_pp == pytest.approx(0.0)

def test_reason_generation():
    analyzer = FinancialAnalyzer()
    
    # Caso 1: Variación > 20%
    res1 = VariationResult(
        account_code="1", account_description="Test",
        period_base="FY23", period_compare="FY24",
        value_base=100, value_compare=150, # +50%
        absolute_variation=50, percentage_variation=50.0,
        variation_type=VariationType.SIGNIFICANT_INCREASE,
        priority=Priority.ALTA
    )
    reason1 = analyzer._generate_reason(res1)
    assert "Variación > 20.0%" in reason1
    
    # Caso 2: Nuevo item
    res2 = VariationResult(
        account_code="2", account_description="New",
        period_base="FY23", period_compare="FY24",
        value_base=0, value_compare=100,
        absolute_variation=100, percentage_variation=None,
        variation_type=VariationType.NEW_ITEM,
        priority=Priority.ALTA
    )
    reason2 = analyzer._generate_reason(res2)
    assert "Nuevo concepto detectado" in reason2
    
    # Caso 3: Item desaparecido
    res3 = VariationResult(
        account_code="3", account_description="Gone",
        period_base="FY23", period_compare="FY24",
        value_base=100, value_compare=0,
        absolute_variation=-100, percentage_variation=None,
        variation_type=VariationType.DISAPPEARED,
        priority=Priority.ALTA
    )
    reason3 = analyzer._generate_reason(res3)
    assert "Concepto desaparecido" in reason3

def test_reason_generation_with_pp():
    analyzer = FinancialAnalyzer()
    
    # Caso 4: Variación pp significativa (> 3 pp)
    res4 = VariationResult(
        account_code="4", account_description="PP Change",
        period_base="FY23", period_compare="FY24",
        value_base=100, value_compare=120,
        absolute_variation=20, percentage_variation=20.0,
        variation_type=VariationType.SIGNIFICANT_INCREASE,
        priority=Priority.ALTA,
        pp_change=5.0 # 5 pp change
    )
    reason4 = analyzer._generate_reason(res4)
    assert "Variación > 3 pp" in reason4
