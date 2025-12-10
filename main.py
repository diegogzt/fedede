#!/usr/bin/env python3
"""
Punto de entrada principal para la aplicación FDD GUI.

Uso:
    python main.py          # Inicia la interfaz gráfica
    python main.py --help   # Muestra ayuda
    python main.py --cli    # Modo línea de comandos (futuro)
"""

import sys
import argparse
import logging
from pathlib import Path

# Asegurar que el directorio src está en el path
ROOT_DIR = Path(__file__).parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR.parent))


def setup_logging(verbose: bool = False) -> None:
    """
    Configura el sistema de logging.
    
    Args:
        verbose: Si activar modo verbose
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(ROOT_DIR / 'logs' / 'fdd_app.log', mode='a', encoding='utf-8')
        ]
    )
    
    # Crear directorio de logs si no existe
    (ROOT_DIR / 'logs').mkdir(exist_ok=True)


def check_dependencies() -> bool:
    """
    Verifica que las dependencias necesarias estén instaladas.
    
    Returns:
        True si todas las dependencias están disponibles
    """
    missing = []
    
    try:
        import tkinter
    except ImportError:
        missing.append("tkinter")
    
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    
    try:
        import openpyxl
    except ImportError:
        missing.append("openpyxl")
    
    if missing:
        print(f"❌ Faltan dependencias: {', '.join(missing)}")
        print("Instale con: pip install -r requirements.txt")
        return False
    
    return True


def run_gui() -> None:
    """Inicia la aplicación en modo GUI."""
    from src.gui import MainWindow
    
    app = MainWindow()
    app.run()


def run_cli(args: argparse.Namespace) -> None:
    """
    Ejecuta en modo línea de comandos.
    
    Args:
        args: Argumentos parseados
    """
    print("📊 FDD - Due Diligence Financiero Automatizado")
    print("=" * 50)
    
    if not args.input:
        print("❌ Error: Debe especificar archivos de entrada con --input")
        sys.exit(1)
    
    from src.processors.excel_reader import ExcelReader
    from src.processors.qa_generator import QAGenerator
    from src.processors.models import Priority
    
    all_results = []
    
    for input_file in args.input:
        print(f"\n📂 Procesando: {input_file}")
        
        try:
            # Leer
            print("  ├─ Leyendo archivo...")
            reader = ExcelReader(input_file)
            reader.read()
            balance = reader.to_balance_sheet()
            print(f"  │   Cuentas: {len(balance.accounts)}, Periodos: {len(balance.periods)}")
            
            # Generar Q&A (QAGenerator hace análisis internamente)
            print("  ├─ Analizando y generando Q&A...")
            
            use_ai = args.ai_mode != "rule_based"
            generator = QAGenerator(use_ai=use_ai, ai_mode=args.ai_mode)
            
            if use_ai and generator.ai_enabled:
                print("  │   Usando IA para generar preguntas...")
                report = generator.generate_report_with_ai(balance, min_priority=Priority.BAJA)
            else:
                print("  │   Usando reglas para generar preguntas...")
                report = generator.generate_report(balance, min_priority=Priority.BAJA)
            
            all_results.extend(report.items)
            
            print(f"  └─ ✅ {len(report.items)} items Q&A generados")
            
        except Exception as e:
            print(f"  └─ ❌ Error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
    
    # Exportar resultados
    if all_results and args.output:
        print(f"\n📤 Exportando resultados a: {args.output}")
        
        import pandas as pd
        
        data = []
        for item in all_results:
            data.append({
                "Cuenta": item.account_code or "-",
                "ILV1": item.mapping_ilv_1 or "-",
                "ILV2": item.mapping_ilv_2 or "-",
                "ILV3": item.mapping_ilv_3 or "-",
                "Pregunta": item.question or "Sin pregunta",
                "Prioridad": item.priority.value if hasattr(item.priority, 'value') else str(item.priority)
            })
        
        df = pd.DataFrame(data)
        
        output_path = Path(args.output)
        if output_path.suffix == '.xlsx':
            df.to_excel(output_path, index=False)
        else:
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"✅ Exportado exitosamente")
    
    print(f"\n📊 Resumen: {len(all_results)} items Q&A generados en total")


def main() -> None:
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="FDD - Due Diligence Financiero Automatizado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py                              # Iniciar GUI
  python main.py --cli -i balance.xlsx        # Modo CLI
  python main.py --cli -i *.xlsx -o qa.xlsx   # Procesar múltiples archivos
        """
    )
    
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Ejecutar en modo línea de comandos'
    )
    
    parser.add_argument(
        '-i', '--input',
        nargs='+',
        help='Archivos de entrada (Excel/CSV)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Archivo de salida (Excel/CSV)'
    )
    
    parser.add_argument(
        '--ai-mode',
        choices=['auto', 'full_ai', 'hybrid', 'rule_based'],
        default='auto',
        help='Modo de IA (default: auto)'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=10.0,
        help='Umbral de variación significativa en %% (default: 10)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Modo verbose con más información'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='FDD 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.verbose)
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Ejecutar según modo
    if args.cli:
        run_cli(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()
