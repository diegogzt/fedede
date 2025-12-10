from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
from pathlib import Path
import logging
from typing import List

from app.processors.excel_reader import ExcelReader
from app.processors.qa_generator import QAGenerator
from app.processors.models import BalanceSheet
from app.core.traceability import init_db, log_processing, get_history

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar DB
init_db()

app = FastAPI(title="Finance Due Diligence API")

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorios de trabajo
UPLOAD_DIR = Path("data/input")
OUTPUT_DIR = Path("data/output")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Finance Due Diligence API is running"}

@app.get("/history")
async def history():
    return get_history()

@app.post("/process-document")
async def process_document(file: UploadFile = File(...)):
    try:
        # 1. Guardar archivo subido
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Archivo recibido: {file.filename}")
        log_processing(file.filename, "started")

        # 2. Procesar Excel
        reader = ExcelReader()
        df = reader.read_excel(str(file_path))
        
        # 3. Generar Balance Sheet (Simplificado para demo)
        # Nota: Aquí deberíamos usar la lógica completa de DataNormalizer
        # Para este MVP, asumimos que ExcelReader devuelve un DataFrame procesable
        
        # TODO: Integrar DataNormalizer correctamente
        # Por ahora, instanciamos QAGenerator que internamente usa DataNormalizer
        
        generator = QAGenerator()
        
        # Simulación de carga de datos al modelo BalanceSheet
        # En una implementación real, DataNormalizer haría esto
        balance = BalanceSheet() 
        # ... lógica de mapeo DF -> BalanceSheet ...
        
        # 4. Generar Reporte Q&A
        # Como el mapeo DF -> BalanceSheet es complejo, por ahora usaremos
        # el flujo existente si es posible, o adaptaremos el ExcelReader
        
        # ALERTA: El código original de ExcelReader devolvía un DataFrame.
        # Necesitamos convertir ese DataFrame a la estructura BalanceSheet
        # que espera QAGenerator.
        
        # Solución temporal: Usar el DataNormalizer para procesar el archivo
        # Asumiendo que DataNormalizer tiene un método `process_file` o similar
        # Si no, tendremos que invocarlo manualmente.
        
        normalized_data = generator.normalizer.normalize_data(df)
        balance = generator.analyzer.create_balance_sheet(normalized_data)
        
        report = generator.generate_report(balance)
        
        # 5. Exportar a Excel
        output_filename = f"QA_{file.filename}"
        output_path = OUTPUT_DIR / output_filename
        
        # Usar ExcelExporter si está disponible, sino CSV
        if generator.export_to_excel(report, str(output_path)):
             log_processing(file.filename, "success", str(output_path))
             return {"status": "success", "download_url": f"/download/{output_filename}"}
        else:
             # Fallback CSV
             output_csv = output_path.with_suffix('.csv')
             generator.export_to_csv(report, str(output_csv))
             log_processing(file.filename, "success", str(output_csv))
             return {"status": "success", "download_url": f"/download/{output_csv.name}"}

    except Exception as e:
        logger.error(f"Error procesando documento: {str(e)}")
        log_processing(file.filename, "error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = OUTPUT_DIR / filename
    if file_path.exists():
        return FileResponse(path=file_path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
