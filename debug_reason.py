from src.processors.financial_analyzer import FinancialAnalyzer, VariationResult, VariationType
from src.processors.models import QAItem, Priority, Status, BalanceSheet, Account, Period, PeriodType

def test_reason_population():
    analyzer = FinancialAnalyzer()
    
    # Create a dummy variation
    var = VariationResult(
        account_code="123",
        account_description="Test Account",
        period_base="FY23",
        period_compare="FY24",
        value_base=100,
        value_compare=150,
        absolute_variation=50,
        percentage_variation=50.0,
        variation_type=VariationType.SIGNIFICANT_INCREASE,
        priority=Priority.ALTA
    )
    
    # Generate reason directly
    reason = analyzer._generate_reason(var)
    print(f"Generated reason: '{reason}'")
    
    # Simulate analyze_variations flow (mocking parts of it)
    # We can't easily mock the whole analyze_variations without a full BalanceSheet setup
    # But we can check _generate_qa_items which is what creates the QAItem
    
    items = analyzer._generate_qa_items([var], {}, 0)
    if items:
        print(f"QAItem reason: '{items[0].reason}'")
    else:
        print("No items generated")

if __name__ == "__main__":
    test_reason_population()