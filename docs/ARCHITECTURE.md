# Arquitectura del Sistema

## Visión General

El sistema Finance Due Diligence (Fedede) es una aplicación web diseñada para automatizar el análisis de documentos financieros. Utiliza una arquitectura cliente-servidor desacoplada.

## Diagrama de Componentes

```mermaid
graph TD
    Client[Frontend (Next.js)] <--> API[Backend API (FastAPI)]
    API --> Engine[Rule Engine]
    API --> DB[(SQLite Traceability DB)]
    Engine --> Excel[Excel Processor]
    Excel --> Files[File System]
```

## Componentes

### 1. Frontend (Next.js)

- **Tecnología**: Next.js 14 (App Router), React, TypeScript.
- **UI**: Tailwind CSS, Shadcn UI, Lucide React.
- **Responsabilidad**:
  - Interfaz de usuario para carga de archivos.
  - Visualización de estado de procesamiento.
  - Dashboard de historial de documentos (Traceability).
  - Comunicación con el Backend vía REST.

### 2. Backend (FastAPI)

- **Tecnología**: Python 3.12, FastAPI, Uvicorn.
- **Responsabilidad**:
  - Exposición de endpoints REST (`/process-document`, `/history`).
  - Gestión de carga y descarga de archivos.
  - Orquestación del procesamiento.
  - Registro de auditoría en base de datos.

### 3. Motor de Reglas (Rule Engine)

- **Ubicación**: `backend/app/engine/rules.py`
- **Responsabilidad**:
  - Reemplaza la lógica de IA anterior.
  - Aplica reglas deterministas basadas en patrones (Regex) y umbrales.
  - Filtra transacciones irrelevantes (ej. "RENTING KIA").
  - Genera preguntas de auditoría basadas en anomalías detectadas.

### 4. Procesamiento de Datos

- **Ubicación**: `backend/app/processors/`
- **Responsabilidad**:
  - `excel_reader.py`: Lectura y normalización de archivos Excel.
  - `qa_generator.py`: Generación de reportes de preguntas y respuestas.
  - `data_normalizer.py`: Limpieza y estandarización de datos financieros.

### 5. Trazabilidad (Traceability)

- **Ubicación**: `backend/app/core/traceability.py`
- **Tecnología**: SQLite.
- **Responsabilidad**:
  - Almacena un registro de cada archivo procesado.
  - Guarda metadatos: nombre de archivo, fecha, estado, ruta de salida.
  - Permite auditoría del uso del sistema.

## Flujo de Datos

1. **Carga**: El usuario sube un archivo Excel desde el Frontend.
2. **Recepción**: FastAPI recibe el archivo y lo guarda temporalmente en `data/input`.
3. **Procesamiento**:
   - Se lee el Excel.
   - Se normalizan los datos.
   - El `RuleEngine` analiza cada fila.
   - Se genera un reporte CSV/Excel con los hallazgos.
4. **Persistencia**: Se registra el evento en la base de datos SQLite.
5. **Respuesta**: El Backend devuelve la URL de descarga y el estado.
6. **Visualización**: El Frontend muestra el éxito y actualiza la tabla de historial.
