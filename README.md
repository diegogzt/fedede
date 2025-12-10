# Finance Due Diligence (Fedede)

Sistema automatizado para Due Diligence Financiero (FDD) basado en reglas de negocio y trazabilidad.

## Descripción

Este proyecto es una aplicación web moderna diseñada para procesar archivos financieros (Excel), aplicar reglas de negocio predefinidas para detectar anomalías o generar preguntas de auditoría, y mantener una trazabilidad completa de los documentos procesados.

El sistema ha evolucionado de una aplicación de escritorio con IA a una arquitectura web robusta y determinista.

## Arquitectura

El proyecto está dividido en dos componentes principales:

- **Backend**: API REST construida con FastAPI (Python). Maneja la lógica de negocio, el procesamiento de archivos Excel y la base de datos de trazabilidad.
- **Frontend**: Interfaz de usuario moderna construida con Next.js (React), Tailwind CSS y Shadcn UI. Permite la carga de archivos y visualización de resultados.

Para más detalles técnicos, consulta [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Estructura del Proyecto

```
FinanceDueDilligenceV1/
├── backend/                 # Servidor Python (FastAPI)
│   ├── app/
│   │   ├── core/            # Configuración, logs, trazabilidad (SQLite)
│   │   ├── engine/          # Motor de reglas de negocio
│   │   ├── processors/      # Procesamiento de Excel y generación de reportes
│   │   └── utils/           # Utilidades generales
│   ├── main.py              # Punto de entrada de la API
│   └── requirements.txt     # Dependencias de Python
├── frontend/                # Cliente Web (Next.js)
│   ├── app/                 # Páginas y componentes
│   ├── components/          # Componentes UI reutilizables
│   └── package.json         # Dependencias de Node.js
├── data/                    # Almacenamiento temporal de archivos
├── docs/                    # Documentación
└── logs/                    # Archivos de log del sistema
```

## Requisitos Previos

- Python 3.10+
- Node.js 18+
- Git

## Instalación y Ejecución

### 1. Backend (Python)

```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt

# Ejecutar servidor de desarrollo
uvicorn main:app --reload
```

El backend estará disponible en `http://localhost:8000`.

### 2. Frontend (Next.js)

```bash
cd frontend
npm install

# Ejecutar servidor de desarrollo
npm run dev
```

El frontend estará disponible en `http://localhost:3000`.

## Uso

1. Abre el navegador en `http://localhost:3000`.
2. Sube un archivo Excel financiero (formato soportado).
3. El sistema procesará el archivo aplicando las reglas de negocio.
4. Descarga el reporte generado con las preguntas de auditoría.
5. Consulta el historial de documentos procesados en el dashboard.

## Licencia

Propiedad privada.
