# Financial Due Diligence (FDD) - Documentación

Esta carpeta contiene la documentación técnica completa del sistema FDD.

## Índice de Documentos

| Documento                          | Descripción                                             |
| ---------------------------------- | ------------------------------------------------------- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitectura del sistema y componentes                  |
| [LIBRARIES.md](LIBRARIES.md)       | Librerías utilizadas y justificación                    |
| [ALGORITHM.md](ALGORITHM.md)       | Algoritmos de detección de periodos y generación de Q&A |
| [DATA_PRIVACY.md](DATA_PRIVACY.md) | **⚠️ CRÍTICO:** Manejo de datos sensibles y privacidad  |
| [SECURITY.md](SECURITY.md)         | Configuración segura y mejores prácticas                |
| [USER_GUIDE.md](USER_GUIDE.md)     | Guía de usuario para la aplicación                      |

## Documento Más Importante

**📛 [DATA_PRIVACY.md](DATA_PRIVACY.md)** - Lee este documento primero si vas a trabajar con servicios de IA externos (OpenAI). Explica:

- Qué datos se envían a la IA
- Cómo proteger información sensible
- Sistema de anonimización implementado
- Comparación OpenAI vs Ollama (local)

## Inicio Rápido

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python main.py
```

## Estructura del Proyecto

```
FDD/
├── src/
│   ├── ai/              # Servicios de IA (OpenAI, Ollama)
│   │   ├── ai_service.py      # Servicio unificado
│   │   ├── data_anonymizer.py # 🛡️ Anonimización de datos
│   │   └── prompts.py         # Templates de prompts
│   ├── config/          # Configuración
│   ├── core/            # Logging, excepciones
│   ├── gui/             # Interfaz gráfica Tkinter
│   ├── processors/      # Procesamiento de datos
│   └── utils/           # Utilidades
├── tests/               # Tests unitarios
├── docs/                # Esta documentación
└── data/                # Datos de entrada/salida
```
