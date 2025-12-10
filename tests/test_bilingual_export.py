import pytest
import pandas as pd
from pathlib import Path
from src.processors.models import QAItem, QAReport, Priority, Status
from src.processors.qa_generator import QAGenerator
from src.config.translations import Language, TranslationManager
from src.config.settings import get_settings

@pytest.fixture
def sample_report():
    items = [
        QAItem(
            mapping_ilv_1="EBITDA",
            mapping_ilv_2="Revenue",
            mapping_ilv_3="Gross revenue",
            description="Ventas Nacionales",
            account_code="700000",
            values={"FY23": 100000.0, "FY24": 120000.0},
            variations={"FY23_vs_FY24": 20000.0},
            variation_percentages={"FY23_vs_FY24": 20.0},
            percentages_over_revenue={"FY23": 100.0, "FY24": 100.0},
            percentage_point_changes={"FY23_vs_FY24": 0.0},
            question="¿Por qué aumentaron las ventas?",
            reason="Variación > 20%",
            priority=Priority.ALTA,
            status=Status.ABIERTO
        )
    ]
    return QAReport(
        items=items,
        analysis_periods=["FY23", "FY24"],
        total_revenue={"FY23": 100000.0, "FY24": 120000.0}
    )

def test_translation_manager():
    tm_es = TranslationManager(Language.SPANISH)
    assert tm_es.get_sheet_names()['general'] == "General"
    
    tm_en = TranslationManager(Language.ENGLISH)
    assert tm_en.get_sheet_names()['general'] == "General" # Es igual en ambos por ahora, pero verificamos acceso
    assert tm_en.get_columns()['description'] == "Description"

def test_dataframe_generation_spanish(sample_report):
    generator = QAGenerator(use_ai=False)
    df = generator.to_dataframe(sample_report, language=Language.SPANISH)
    
    assert "Descripción" in df.columns
    assert "Razón de la pregunta" in df.columns
    assert df.iloc[0]["Razón de la pregunta"] == "Variación > 20%"

def test_dataframe_generation_english(sample_report):
    generator = QAGenerator(use_ai=False)
    df = generator.to_dataframe(sample_report, language=Language.ENGLISH)
    
    assert "Description" in df.columns
    assert "Reason for question" in df.columns
    assert df.iloc[0]["Reason for question"] == "Variación > 20%" # El contenido sigue en español porque viene del objeto, pero la columna cambia

def test_settings_update():
    settings = get_settings()
    settings.report.language = Language.ENGLISH
    settings.report.materiality_threshold = 50000.0
    
    assert settings.report.language == Language.ENGLISH
    assert settings.report.materiality_threshold == 50000.0
