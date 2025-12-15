import re

import pytest

from backend.app.processors.excel_reader import read_balance_file
from backend.app.processors.qa_generator import QAGenerator
from backend.app.config.settings import get_settings


EXAMPLE_FILE = "examples/Q&A_Metals_Financiero.xlsx - PL.csv"


def _extract_period_pair_from_drivers_line(text: str) -> str | None:
    """Extrae el par de periodos del lead-in (i) de drivers."""
    if not text:
        return None
    m = re.search(r"vs\s+(FY\d{2}|YTD\d{2})\s+vs\s+(FY\d{2}|YTD\d{2})", text)
    if not m:
        return None
    return f"{m.group(1)}->{m.group(2)}"


@pytest.mark.integration
class TestExampleRegressions:
    def test_example_period_window_is_last_2_fy_and_2_ytd(self):
        balance = read_balance_file(EXAMPLE_FILE)

        settings = get_settings()
        settings.report.percentage_threshold = 0.10
        settings.report.materiality_threshold = 100000

        generator = QAGenerator(use_ai=False)
        report = generator.generate_report(balance)

        assert report.analysis_periods, "analysis_periods vacío"

        fiscal_periods = generator.normalizer.detect_fiscal_periods(balance)
        fy_all = list(fiscal_periods.get("fiscal_years", []) or [])
        ytd_all = list(fiscal_periods.get("ytd_periods", []) or [])
        expected = (fy_all[-2:] if len(fy_all) >= 2 else fy_all) + (ytd_all[-2:] if len(ytd_all) >= 2 else ytd_all)
        assert report.analysis_periods == expected, f"analysis_periods inesperado: {report.analysis_periods} vs {expected}"

    def test_example_no_old_periods_in_questions(self):
        balance = read_balance_file(EXAMPLE_FILE)

        settings = get_settings()
        settings.report.percentage_threshold = 0.10
        settings.report.materiality_threshold = 100000

        generator = QAGenerator(use_ai=False)
        report = generator.generate_report(balance)

        question_text = "\n".join([i.question or "" for i in report.items])
        # Con la ventana 2 FY + 2 YTD, no deberían aparecer periodos muy antiguos.
        assert "FY21" not in question_text
        assert "YTD21" not in question_text

    def test_example_drivers_lead_in_not_repeated_by_category_and_pair(self):
        balance = read_balance_file(EXAMPLE_FILE)

        settings = get_settings()
        settings.report.percentage_threshold = 0.10
        settings.report.materiality_threshold = 100000

        generator = QAGenerator(use_ai=False)
        report = generator.generate_report(balance)

        # Contabiliza el lead-in (i) por categoría ILV y par de periodos.
        seen: dict[tuple[str, str], int] = {}
        for item in report.items:
            q = item.question or ""
            if "(i)" not in q:
                continue
            # Usamos la primera línea, que es donde vive el lead-in de drivers.
            first_line = q.splitlines()[0].strip()
            if "drivers" not in first_line.lower():
                continue

            pair = _extract_period_pair_from_drivers_line(first_line)
            if not pair:
                continue

            key = (getattr(item, "ilv_category", "") or "", pair)
            seen[key] = seen.get(key, 0) + 1

        repeats = {k: v for k, v in seen.items() if v > 1}
        assert not repeats, f"Drivers lead-in repetido: {repeats}"
