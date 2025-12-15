from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
from pathlib import Path
import logging
from typing import List
from datetime import datetime
import json
import math
from pydantic import BaseModel
from typing import Optional

from app.processors.excel_reader import ExcelReader
from app.processors.qa_generator import QAGenerator
from app.processors.financial_analyzer import AnalysisConfig
from app.processors.models import BalanceSheet, QAReport, QAItem, Priority, Status
from app.config.translations import Language
from app.core.traceability import init_db, log_processing, get_history, delete_document, update_processing

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

# Directorios de trabajo (rutas estables, independen del directorio de ejecución)
BASE_DIR = Path(__file__).resolve().parent  # .../backend
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
REPORT_DIR = DATA_DIR / "reports"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def _report_path(doc_id: int) -> Path:
    return REPORT_DIR / f"report_{doc_id}.json"


def _serialize_report(report):
    def _sanitize(value):
        if isinstance(value, float):
            if not math.isfinite(value):
                return None
            return value
        if isinstance(value, list):
            return [_sanitize(v) for v in value]
        if isinstance(value, dict):
            return {k: _sanitize(v) for k, v in value.items()}
        return value

    payload = {
        "items": [
            {
                "mapping_ilv_1": item.mapping_ilv_1,
                "mapping_ilv_2": item.mapping_ilv_2,
                "mapping_ilv_3": item.mapping_ilv_3,
                "description": item.description,
                "account_code": item.account_code,
                "values": item.values,
                "variations": item.variations,
                "variation_percentages": item.variation_percentages,
                "percentages_over_revenue": item.percentages_over_revenue,
                "percentage_point_changes": item.percentage_point_changes,
                "question": item.question,
                "reason": item.reason,
                "priority": item.priority.value if getattr(item, "priority", None) else None,
                "status": item.status.value if getattr(item, "status", None) else None,
                "response": item.response,
                "follow_up": item.follow_up,
            }
            for item in report.items
        ],
        "company_name": report.company_name,
        "report_date": report.report_date.isoformat() if getattr(report, "report_date", None) else None,
        "source_file": report.source_file,
        "analysis_periods": report.analysis_periods,
        "total_revenue": report.total_revenue,
    }

    return _sanitize(payload)


def _deserialize_report(data: dict) -> QAReport:
    """Reconstruye un QAReport desde el JSON guardado."""
    items = []
    for item_data in data.get("items", []):
        # Mapear priority string a enum
        priority_str = item_data.get("priority")
        if priority_str == "Alta":
            priority = Priority.ALTA
        elif priority_str == "Media":
            priority = Priority.MEDIA
        elif priority_str == "Baja":
            priority = Priority.BAJA
        else:
            priority = Priority.MEDIA

        # Mapear status string a enum
        status_str = item_data.get("status")
        if status_str == "Abierto":
            status = Status.ABIERTO
        elif status_str == "En proceso":
            status = Status.EN_PROCESO
        elif status_str == "Cerrado":
            status = Status.CERRADO
        else:
            status = Status.ABIERTO

        items.append(QAItem(
            mapping_ilv_1=item_data.get("mapping_ilv_1"),
            mapping_ilv_2=item_data.get("mapping_ilv_2"),
            mapping_ilv_3=item_data.get("mapping_ilv_3"),
            description=item_data.get("description", ""),
            account_code=item_data.get("account_code", ""),
            values=item_data.get("values", {}),
            variations=item_data.get("variations", {}),
            variation_percentages=item_data.get("variation_percentages", {}),
            percentages_over_revenue=item_data.get("percentages_over_revenue", {}),
            percentage_point_changes=item_data.get("percentage_point_changes", {}),
            question=item_data.get("question"),
            reason=item_data.get("reason"),
            priority=priority,
            status=status,
            response=item_data.get("response"),
            follow_up=item_data.get("follow_up"),
        ))

    report_date = None
    if data.get("report_date"):
        try:
            report_date = datetime.fromisoformat(data["report_date"])
        except Exception:
            report_date = datetime.now()

    return QAReport(
        items=items,
        company_name=data.get("company_name"),
        report_date=report_date or datetime.now(),
        source_file=data.get("source_file"),
        analysis_periods=data.get("analysis_periods", []),
        total_revenue=data.get("total_revenue", {}),
    )


class UpdateQAItemRequest(BaseModel):
    status: Optional[str] = None
    response: Optional[str] = None
    follow_up: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Finance Due Diligence API is running"}

@app.get("/history")
async def history():
    # Consolidar duplicados históricos (started/processing/success) quedándonos con el más reciente por filename
    rows = get_history()
    consolidated = []
    seen = set()
    for row in rows:
        key = row.get("filename")
        if not key:
            consolidated.append(row)
            continue
        if key in seen:
            continue
        seen.add(key)
        consolidated.append(row)

    # Backfill de métricas si la DB no las tiene pero existe el reporte JSON
    for row in consolidated:
        if (row.get("status") or "").lower() != "success":
            continue
        if row.get("questions_generated") is not None:
            continue

        report_path = row.get("report_path")
        path = Path(report_path) if report_path else _report_path(int(row["id"]))
        if not path.exists():
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                report_json = json.load(f)
            items = report_json.get("items") or []
            question_items = [it for it in items if (it.get("question") or "").strip()]

            def _bucket(priority_value: str) -> str:
                p = (priority_value or "").strip().upper()
                if "ALTA" in p or p == "HIGH":
                    return "high"
                if "MEDIA" in p or p == "MEDIUM":
                    return "medium"
                if "BAJA" in p or p == "LOW":
                    return "low"
                return ""

            high_priority = sum(1 for it in question_items if _bucket(str(it.get("priority") or "")) == "high")
            medium_priority = sum(1 for it in question_items if _bucket(str(it.get("priority") or "")) == "medium")
            low_priority = sum(1 for it in question_items if _bucket(str(it.get("priority") or "")) == "low")

            row["questions_generated"] = len(question_items)
            row["high_priority_count"] = high_priority
            row["medium_priority_count"] = medium_priority
            row["low_priority_count"] = low_priority
        except Exception:
            continue
    return consolidated

@app.post("/process-document")
async def process_document(
    file: UploadFile = File(...),
    variation_threshold: float = Form(...),
    materiality_threshold: float = Form(...),
    thresholds_confirmed: bool = Form(...),
    language: Optional[str] = Form(None),
):
    try:
        if not thresholds_confirmed:
            raise HTTPException(
                status_code=400,
                detail="Debes confirmar los umbrales antes de procesar el documento",
            )
        # 1. Guardar archivo subido
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Archivo recibido: {file.filename}")
        started_id = log_processing(filename=file.filename, status="processing", original_filename=file.filename)

        # 2. Leer Excel y convertir a BalanceSheet
        reader = ExcelReader(str(file_path))
        balance = reader.to_balance_sheet()
        
        logger.info(f"Balance cargado: {len(balance.accounts)} cuentas")

        # 3. Generar Reporte Q&A
        analysis_config = AnalysisConfig(
            significant_variation_threshold=float(variation_threshold),
            high_priority_absolute=float(materiality_threshold),
        )

        generator = QAGenerator(
            analysis_config=analysis_config,
            rule_threshold_percent=float(variation_threshold),
            rule_threshold_absolute=float(materiality_threshold),
        )
        report = generator.generate_report(balance)
        
        logger.info(f"Reporte generado: {len(report.items)} items")

        question_items = [i for i in report.items if (getattr(i, "question", None) or "").strip()]
        high_priority = sum(1 for i in question_items if getattr(i, "priority", None) and i.priority.name == 'ALTA')
        medium_priority = sum(1 for i in question_items if getattr(i, "priority", None) and i.priority.name == 'MEDIA')
        low_priority = sum(1 for i in question_items if getattr(i, "priority", None) and i.priority.name == 'BAJA')

        # 4. Exportar a Excel
        output_filename = f"QA_{Path(file.filename).stem}.xlsx"
        output_path = OUTPUT_DIR / output_filename

        export_language = Language.ENGLISH if (language or "").lower().startswith("en") else Language.SPANISH
        
        # Export multi-tab (3 pestañas): Preguntas generales + PT + BL
        if generator.export_to_excel_with_tabs(
            report,
            str(output_path),
            project_name=Path(file.filename).stem,
            include_sheets=["PL", "BS"],
            language=export_language,
        ):
            report_path = _report_path(started_id)
            # Persistir el reporte como JSON (para UI de auditoría)
            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(_serialize_report(report), f, ensure_ascii=False, allow_nan=False)
            except Exception as e:
                logger.warning(f"No se pudo persistir el reporte JSON: {e}")

            update_processing(
                doc_id=started_id,
                status="success",
                output_path=str(output_path),
                report_path=str(report_path),
                rows_processed=len(balance.accounts),
                questions_generated=len(question_items),
                high_priority_count=high_priority,
                medium_priority_count=medium_priority,
                low_priority_count=low_priority,
            )

            return {
                "success": True,
                "message": f"Procesado exitosamente: {len(report.items)} items generados",
                "download_url": f"/download/{output_filename}",
                "report_url": f"/report/{started_id}",
                "document": {
                    "id": started_id,
                    "filename": file.filename,
                    "original_filename": file.filename,
                    "processed_at": datetime.now().isoformat(),
                    "status": "success",
                    "output_path": str(output_path),
                    "report_path": str(report_path),
                    "file_size": file_path.stat().st_size if file_path.exists() else None,
                    "rows_processed": len(balance.accounts),
                    "questions_generated": len(question_items),
                    "high_priority_count": high_priority,
                    "medium_priority_count": medium_priority,
                    "low_priority_count": low_priority,
                }
            }
        else:
            # Fallback CSV
            output_csv = output_path.with_suffix('.csv')
            generator.export_to_csv(report, str(output_csv))
            report_path = _report_path(started_id)

            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(_serialize_report(report), f, ensure_ascii=False, allow_nan=False)
            except Exception as e:
                logger.warning(f"No se pudo persistir el reporte JSON: {e}")

            update_processing(
                doc_id=started_id,
                status="success",
                output_path=str(output_csv),
                report_path=str(report_path),
                rows_processed=len(balance.accounts),
                questions_generated=len(question_items),
                high_priority_count=high_priority,
                medium_priority_count=medium_priority,
                low_priority_count=low_priority,
            )

            return {
                "success": True,
                "message": f"Procesado exitosamente (CSV): {len(report.items)} items",
                "download_url": f"/download/{output_csv.name}",
                "report_url": f"/report/{started_id}",
                "document": {
                    "id": started_id,
                    "filename": file.filename,
                    "original_filename": file.filename,
                    "processed_at": datetime.now().isoformat(),
                    "status": "success",
                    "output_path": str(output_csv),
                    "report_path": str(report_path),
                    "file_size": file_path.stat().st_size if file_path.exists() else None,
                    "rows_processed": len(balance.accounts),
                    "questions_generated": len(question_items),
                    "high_priority_count": high_priority,
                    "medium_priority_count": medium_priority,
                    "low_priority_count": low_priority,
                },
            }

    except Exception as e:
        logger.error(f"Error procesando documento: {str(e)}")
        try:
            if "started_id" in locals():
                update_processing(doc_id=started_id, status="error", error_message=str(e))
            else:
                log_processing(file.filename, "error")
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/report/{doc_id}")
async def get_report(doc_id: int):
    path = _report_path(doc_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        def _sanitize(value):
            if isinstance(value, float):
                if not math.isfinite(value):
                    return None
                return value
            if isinstance(value, list):
                return [_sanitize(v) for v in value]
            if isinstance(value, dict):
                return {k: _sanitize(v) for k, v in value.items()}
            return value

        return _sanitize(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read report: {e}")


@app.patch("/report/{doc_id}/item/{account_code}")
async def update_report_item(doc_id: int, account_code: str, payload: UpdateQAItemRequest):
    path = _report_path(doc_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    with open(path, "r", encoding="utf-8") as f:
        report = json.load(f)

    items = report.get("items") or []
    target = None
    for item in items:
        if str(item.get("account_code")) == str(account_code):
            target = item
            break

    if target is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if payload.status is not None:
        if payload.status not in {"Abierto", "En proceso", "Cerrado"}:
            raise HTTPException(status_code=400, detail="Invalid status")
        target["status"] = payload.status
    if payload.response is not None:
        target["response"] = payload.response
    if payload.follow_up is not None:
        target["follow_up"] = payload.follow_up

    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False)

    return {"success": True, "item": target}

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = OUTPUT_DIR / filename
    if file_path.exists():
        return FileResponse(path=file_path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/report/{doc_id}/export")
async def export_report_with_changes(doc_id: int, language: Optional[str] = "es"):
    """
    Exporta el reporte a Excel incluyendo los cambios de auditoría.
    
    El Excel original se genera al procesar el documento, pero los cambios
    de auditoría (status, response, follow_up) se guardan solo en JSON.
    Este endpoint regenera el Excel con los datos actualizados.
    """
    report_path = _report_path(doc_id)
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Reconstruir el QAReport desde JSON
        report = _deserialize_report(data)

        # Generar nombre de archivo
        source_name = Path(data.get("source_file", "Report")).stem if data.get("source_file") else f"Report_{doc_id}"
        output_filename = f"QA_{source_name}_updated.xlsx"
        output_path = OUTPUT_DIR / output_filename

        # Exportar usando QAGenerator
        export_language = Language.ENGLISH if (language or "").lower().startswith("en") else Language.SPANISH
        generator = QAGenerator()
        result = generator.export_to_excel_with_tabs(
            report,
            str(output_path),
            project_name=source_name,
            include_sheets=["PL", "BS"],
            language=export_language,
        )

        if result and output_path.exists():
            return FileResponse(
                path=str(output_path),
                filename=output_filename,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate Excel file")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


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
