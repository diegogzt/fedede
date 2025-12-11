from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
from pathlib import Path
import logging
from typing import List
from datetime import datetime

from app.processors.excel_reader import ExcelReader
from app.processors.qa_generator import QAGenerator
from app.processors.models import BalanceSheet
from app.core.traceability import init_db, log_processing, get_history, delete_document

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

        # 2. Leer Excel y convertir a BalanceSheet
        reader = ExcelReader(str(file_path))
        balance = reader.to_balance_sheet()
        
        logger.info(f"Balance cargado: {len(balance.accounts)} cuentas")

        # 3. Generar Reporte Q&A
        generator = QAGenerator()
        report = generator.generate_report(balance)
        
        logger.info(f"Reporte generado: {len(report.items)} items")

        # 4. Exportar a Excel
        output_filename = f"QA_{Path(file.filename).stem}.xlsx"
        output_path = OUTPUT_DIR / output_filename
        
        if generator.export_to_excel(report, str(output_path)):
            log_processing(file.filename, "success", str(output_path))
            return {
                "success": True,
                "message": f"Procesado exitosamente: {len(report.items)} items generados",
                "download_url": f"/download/{output_filename}",
                "document": {
                    "id": str(hash(file.filename)),
                    "filename": file.filename,
                    "processed_at": datetime.now().isoformat(),
                    "status": "success",
                    "output_file": output_filename,
                    "stats": {
                        "total_accounts": len(balance.accounts),
                        "total_items": len(report.items),
                        "high_priority": sum(1 for i in report.items if i.priority.name == 'ALTA'),
                        "medium_priority": sum(1 for i in report.items if i.priority.name == 'MEDIA'),
                        "low_priority": sum(1 for i in report.items if i.priority.name == 'BAJA'),
                    }
                }
            }
        else:
            # Fallback CSV
            output_csv = output_path.with_suffix('.csv')
            generator.export_to_csv(report, str(output_csv))
            log_processing(file.filename, "success", str(output_csv))
            return {
                "success": True,
                "message": f"Procesado exitosamente (CSV): {len(report.items)} items",
                "download_url": f"/download/{output_csv.name}"
            }

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

@app.delete("/history/{doc_id}")
async def delete_history_item(doc_id: int):
    """Elimina un documento del historial."""
    success = delete_document(doc_id)
    if success:
        return {"success": True, "message": "Documento eliminado"}
    raise HTTPException(status_code=404, detail="Documento no encontrado")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
