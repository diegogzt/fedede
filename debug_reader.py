"""
Script para depurar la lectura de archivos Excel.
"""
import sys
from pathlib import Path

# Añadir backend al path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.processors.excel_reader import ExcelReader
import logging

logging.basicConfig(level=logging.INFO)

def debug_file(file_path: str):
    """Depura la lectura de un archivo."""
    print(f"\n{'='*80}")
    print(f"Depurando: {file_path}")
    print(f"{'='*80}\n")
    
    reader = ExcelReader(file_path)
    df = reader.read()
    
    print(f"\n📊 DataFrame Shape: {df.shape}")
    print(f"\n📝 Columnas detectadas ({len(df.columns)}):")
    for i, col in enumerate(df.columns):
        print(f"  {i}: '{col}'")
    
    print(f"\n🔍 Primeras 3 filas:")
    print(df.head(3))
    
    print(f"\n📊 Valores de la primera cuenta (si hay datos):")
    if len(df) > 0:
        first_row = df.iloc[0]
        print(f"  Código: {first_row.get('Cuenta', 'N/A')}")
        print(f"  Descripción: {first_row.get('Description', 'N/A')}")
        print(f"  FY23 (col 5): {first_row.iloc[5] if len(first_row) > 5 else 'N/A'}")
        print(f"  FY24 (col 6): {first_row.iloc[6] if len(first_row) > 6 else 'N/A'}")
        print(f"  YTD24 (col 7): {first_row.iloc[7] if len(first_row) > 7 else 'N/A'}")
        print(f"  YTD25 (col 8): {first_row.iloc[8] if len(first_row) > 8 else 'N/A'}")
    
    print(f"\n🎯 Columnas identificadas:")
    print(f"  - Código: {reader._code_column}")
    print(f"  - Descripción: {reader._description_column}")
    
    print(f"\n📅 Periodos detectados ({len(reader._periods)}):")
    for i, p in enumerate(reader._periods):
        print(f"  {i}: '{p.name}' ({p.period_type.value})")
    
    print(f"\n🔍 Verificando coincidencia de nombres:")
    period_names = [p.name for p in reader._periods]
    for period_name in period_names[:5]:  # Solo primeros 5
        if period_name in df.columns:
            print(f"  ✅ '{period_name}' encontrado en columnas")
        else:
            print(f"  ❌ '{period_name}' NO encontrado en columnas")
            # Buscar similares
            similar = [c for c in df.columns if period_name.strip().lower() in str(c).strip().lower()]
            if similar:
                print(f"     Similares: {similar}")
    
    print(f"\n🏦 Creando BalanceSheet...")
    try:
        # Añadir debug al proceso
        print(f"\n🔬 Debug de extracción de valores:")
        first_row = df.iloc[0]
        period_names = [p.name for p in reader._periods]
        print(f"  Periodo names: {period_names[:5]}")
        print(f"  First row keys: {list(first_row.keys())[:10]}")
        print(f"  Buscando períodos en la primera fila:")
        for pname in period_names[:5]:
            if pname in first_row:
                print(f"    '{pname}': {first_row[pname]}")
            else:
                print(f"    '{pname}': NO ENCONTRADO")
        
        balance = reader.to_balance_sheet()
        print(f"✅ BalanceSheet creado: {len(balance.accounts)} cuentas")
        
        # Mostrar algunas cuentas de ejemplo
        print(f"\n📋 Primeras 5 cuentas:")
        for i, account in enumerate(balance.accounts[:5]):
            print(f"\n  Cuenta {i+1}:")
            print(f"    Código: {account.code}")
            print(f"    Descripción: {account.description}")
            print(f"    Valores: {account.values}")
            
    except Exception as e:
        print(f"❌ Error al crear BalanceSheet: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Si se pasa un archivo como argumento, usarlo
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Usar un archivo de ejemplo
        examples_dir = Path(__file__).parent / "examples"
        files = list(examples_dir.glob("*.xlsx")) + list(examples_dir.glob("*.csv"))
        if files:
            file_path = str(files[0])
        else:
            print("❌ No hay archivos de ejemplo disponibles")
            print("Uso: python debug_reader.py <ruta_archivo>")
            sys.exit(1)
    
    debug_file(file_path)
