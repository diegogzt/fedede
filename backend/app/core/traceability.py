import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

DB_PATH = Path("data/traceability.db")

def init_db():
    """Inicializa la base de datos de trazabilidad."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            output_path TEXT,
            user_id TEXT DEFAULT 'anonymous'
        )
    ''')
    
    conn.commit()
    conn.close()

def log_processing(filename: str, status: str, output_path: str = None, user_id: str = 'anonymous'):
    """Registra un evento de procesamiento."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO processed_documents (filename, status, output_path, user_id)
        VALUES (?, ?, ?, ?)
    ''', (filename, status, output_path, user_id))
    
    conn.commit()
    conn.close()

def get_history() -> List[Dict[str, Any]]:
    """Obtiene el historial de documentos procesados."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM processed_documents ORDER BY processed_at DESC LIMIT 50')
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
