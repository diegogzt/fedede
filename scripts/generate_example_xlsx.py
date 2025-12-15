from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Al ejecutar `python scripts/...`, sys.path[0] apunta a `scripts/`.
# Insertamos el root del repo para poder importar `src.*`.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src._backend_imports import ensure_backend_on_path

ensure_backend_on_path()

from app.config.settings import get_settings  # noqa: E402
from app.config.translations import Language  # noqa: E402
from app.processors.excel_reader import read_balance_file  # noqa: E402
from app.processors.excel_exporter import ExcelExporter  # noqa: E402
from app.processors.qa_generator import QAGenerator  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera XLSX (multi-tab) desde el ejemplo")
    parser.add_argument(
        "--input",
        default="examples/Q&A_Metals_Financiero.xlsx - PL.csv",
        help="Ruta al archivo de entrada (CSV/XLSX)",
    )
    parser.add_argument(
        "--output",
        default="output/example_report.xlsx",
        help="Ruta de salida del XLSX",
    )
    parser.add_argument(
        "--variation-threshold",
        type=float,
        default=0.10,
        help="Umbral de variación porcentual (ej. 0.10 = 10%)",
    )
    parser.add_argument(
        "--materiality-threshold",
        type=float,
        default=100000.0,
        help="Umbral de materialidad absoluta",
    )
    parser.add_argument(
        "--project-name",
        default="Example",
        help="Nombre del proyecto (título en el Excel)",
    )
    parser.add_argument(
        "--include-all-accounts",
        action="store_true",
        help="Incluye todas las cuentas aunque no haya variación significativa",
    )
    parser.add_argument(
        "--questions-only",
        action="store_true",
        help="Exporta solo filas con pregunta (modo compacto)",
    )
    args = parser.parse_args()

    input_path = (REPO_ROOT / args.input).resolve() if not Path(args.input).is_absolute() else Path(args.input)
    output_path = (REPO_ROOT / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    settings = get_settings()
    settings.report.percentage_threshold = float(args.variation_threshold)
    settings.report.materiality_threshold = float(args.materiality_threshold)

    balance = read_balance_file(str(input_path))

    generator = QAGenerator(use_ai=False)
    report = generator.generate_report(balance, include_all_accounts=bool(args.include_all_accounts))

    exporter = ExcelExporter(project_name=args.project_name)
    exporter.export(
        report,
        output_path,
        include_sheets=None,
        language=Language.SPANISH,
        questions_only=bool(args.questions_only),
    )

    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
