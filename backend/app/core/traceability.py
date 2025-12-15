import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parents[2]  # .../backend
DB_PATH = BASE_DIR / "data" / "traceability.db"

def init_db():
    """Inicializa la base de datos de trazabilidad."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            output_path TEXT,
            report_path TEXT,
            error_message TEXT,
            rows_processed INTEGER,
            questions_generated INTEGER,
            high_priority_count INTEGER,
            medium_priority_count INTEGER,
            low_priority_count INTEGER,
            user_id TEXT DEFAULT 'anonymous'
        )
    ''')

    # Migración suave para bases existentes
    def _try_add_column(sql: str):
        try:
            cursor.execute(sql)
        except sqlite3.OperationalError:
            pass

    _try_add_column("ALTER TABLE processed_documents ADD COLUMN original_filename TEXT")
    _try_add_column("ALTER TABLE processed_documents ADD COLUMN report_path TEXT")
    _try_add_column("ALTER TABLE processed_documents ADD COLUMN error_message TEXT")
    _try_add_column("ALTER TABLE processed_documents ADD COLUMN rows_processed INTEGER")
    _try_add_column("ALTER TABLE processed_documents ADD COLUMN questions_generated INTEGER")
    _try_add_column("ALTER TABLE processed_documents ADD COLUMN high_priority_count INTEGER")
    _try_add_column("ALTER TABLE processed_documents ADD COLUMN medium_priority_count INTEGER")
    _try_add_column("ALTER TABLE processed_documents ADD COLUMN low_priority_count INTEGER")
    
    conn.commit()
    conn.close()

def log_processing(
    filename: str,
    status: str,
    output_path: str = None,
    user_id: str = 'anonymous',
    original_filename: str = None,
) -> int:
    """Inserta un registro de procesamiento y devuelve el ID insertado."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO processed_documents (
            filename, original_filename, status, output_path, user_id
        )
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, original_filename, status, output_path, user_id))

    inserted_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return inserted_id


def update_processing(
    doc_id: int,
    status: str,
    output_path: str = None,
    report_path: str = None,
    error_message: str = None,
    rows_processed: int = None,
    questions_generated: int = None,
    high_priority_count: int = None,
    medium_priority_count: int = None,
    low_priority_count: int = None,
) -> bool:
    """Actualiza un registro existente de procesamiento."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        '''
        UPDATE processed_documents
        SET status = ?,
            output_path = COALESCE(?, output_path),
            report_path = COALESCE(?, report_path),
            error_message = COALESCE(?, error_message),
            rows_processed = COALESCE(?, rows_processed),
            questions_generated = COALESCE(?, questions_generated),
            high_priority_count = COALESCE(?, high_priority_count),
            medium_priority_count = COALESCE(?, medium_priority_count),
            low_priority_count = COALESCE(?, low_priority_count),
            processed_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''',
        (
            status,
            output_path,
            report_path,
            error_message,
            rows_processed,
            questions_generated,
            high_priority_count,
            medium_priority_count,
            low_priority_count,
            doc_id,
        ),
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def get_history() -> List[Dict[str, Any]]:
    """Obtiene el historial de documentos procesados."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM processed_documents ORDER BY processed_at DESC, id DESC LIMIT 50')
    rows = cursor.fetchall()
    
    history = [dict(row) for row in rows]
    conn.close()
    return history

def delete_document(doc_id: int) -> bool:
    """Elimina un documento del historial por su ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM processed_documents WHERE id = ?', (doc_id,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    return deleted
