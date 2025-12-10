# ⚠️ Privacidad de Datos y Protección de Información Sensible

## RESUMEN EJECUTIVO

Este documento describe cómo el sistema FDD maneja datos financieros sensibles cuando utiliza servicios de IA para generar preguntas de due diligence.

### Estado Actual

| Aspecto           | Estado        | Acción                      |
| ----------------- | ------------- | --------------------------- |
| API Key en código | ⚠️ CRÍTICO    | Mover a variable de entorno |
| Datos a OpenAI    | 🛡️ MITIGADO   | Usar `DataAnonymizer`       |
| Alternativa local | ✅ DISPONIBLE | Usar Ollama                 |
| Modo sin IA       | ✅ DISPONIBLE | Usar `rule_based`           |

---

## 1. ¿QUÉ DATOS MANEJA EL SISTEMA?

### Datos de Entrada (Sensibles)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATOS SENSIBLES DE ENTRADA                   │
├─────────────────────────────────────────────────────────────────┤
│ • Nombres de cuentas contables (ej: "Ventas a Iberdrola S.A.") │
│ • Códigos de cuenta (ej: "7000001234")                          │
│ • Montos exactos (ej: "5,247,892.45 €")                         │
│ • Nombres de clientes/proveedores                               │
│ • Variaciones absolutas (revelan tamaño del negocio)            │
│ • Periodos temporales (pueden identificar la empresa)           │
└─────────────────────────────────────────────────────────────────┘
```

### Datos Generados (Menos Sensibles)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATOS GENERADOS                              │
├─────────────────────────────────────────────────────────────────┤
│ • Preguntas de due diligence (genéricas)                        │
│ • Clasificación ILV (Ingresos/Logística/Ventas)                 │
│ • Prioridades (alta/media/baja)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. MODOS DE OPERACIÓN Y PRIVACIDAD

### Modo 1: OpenAI (Cloud) - ⚠️ REQUIERE ANONIMIZACIÓN

```
┌──────────┐     Internet      ┌──────────────┐
│  Tu PC   │ ──────────────►   │  OpenAI API  │
│          │   datos ───────►  │  (EE.UU.)    │
│          │   ◄──── respuesta │              │
└──────────┘                   └──────────────┘

Riesgos:
• Datos viajan por internet
• OpenAI almacena datos (política de retención)
• Posible uso para entrenar modelos (ver políticas)
• Regulaciones GDPR pueden aplicar
```

**Mitigación implementada: `DataAnonymizer`**

### Modo 2: Ollama (Local) - ✅ SEGURO

```
┌──────────────────────────────────┐
│            Tu PC                 │
│  ┌─────────┐     ┌─────────────┐│
│  │   FDD   │────►│   Ollama    ││
│  │   App   │◄────│   (local)   ││
│  └─────────┘     └─────────────┘│
│                                  │
│  ✅ Datos NUNCA salen del PC    │
└──────────────────────────────────┘
```

### Modo 3: Rule-Based - ✅ MÁS SEGURO

```
┌─────────────────────────────────────┐
│            Tu PC                    │
│  ┌─────────┐     ┌───────────────┐ │
│  │   FDD   │────►│  Templates    │ │
│  │   App   │◄────│  Predefinidos │ │
│  └─────────┘     └───────────────┘ │
│                                     │
│  ✅ Sin IA, sin envío de datos     │
└─────────────────────────────────────┘
```

---

## 3. SISTEMA DE ANONIMIZACIÓN

### Ubicación: `src/ai/data_anonymizer.py`

### Principio de Funcionamiento

```
ANTES de anonimizar (SENSIBLE - NO ENVIAR):
┌─────────────────────────────────────────────────────────────────┐
│ Descripción: "Ventas a Iberdrola Generación S.A.U."            │
│ Código:      "7000012345"                                       │
│ Valor Base:  5,247,892.45 €                                     │
│ Valor Comp:  3,148,735.67 €                                     │
│ Variación:   -2,099,156.78 € (-40%)                            │
└─────────────────────────────────────────────────────────────────┘

DESPUÉS de anonimizar (SEGURO - SE PUEDE ENVIAR):
┌─────────────────────────────────────────────────────────────────┐
│ Categoría:   "Cuenta de ingresos"                               │
│ Tipo:        "income_revenue"                                   │
│ Dirección:   "decremento"                                       │
│ Magnitud:    "significativa"                                    │
│ Porcentaje:  -40%                                               │
│ Rango Valor: "grande"                                           │
│ Prioridad:   "alta"                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Lo que OpenAI VE vs NO VE

| Dato               | ¿Lo ve OpenAI? | Ejemplo que ve       |
| ------------------ | -------------- | -------------------- |
| Nombre de cuenta   | ❌ NO          | "Cuenta de ingresos" |
| Código de cuenta   | ❌ NO          | (nada)               |
| Monto exacto       | ❌ NO          | (nada)               |
| Variación absoluta | ❌ NO          | (nada)               |
| Variación %        | ✅ Sí          | "-40%"               |
| Magnitud           | ✅ Sí          | "significativa"      |
| Rango de valor     | ✅ Sí          | "grande"             |
| Periodo            | ✅ Sí          | "FY23 vs FY24"       |

### Uso del Anonimizador

```python
from src.ai.data_anonymizer import DataAnonymizer, anonymize_for_ai

# Opción 1: Uso completo
anonymizer = DataAnonymizer(strict_mode=True)
anon_data = anonymizer.anonymize(
    description="Ventas a Iberdrola",
    account_code="7000012345",
    value_base=5_247_892.45,
    value_compare=3_148_735.67,
    variation_pct=-40.0,
    period_base="FY23",
    period_compare="FY24"
)

# El prompt seguro
safe_prompt = create_safe_prompt(anon_data)

# Opción 2: Función de conveniencia
anon_data, safe_prompt = anonymize_for_ai(
    description="Ventas a Iberdrola",
    account_code="7000012345",
    value_base=5_247_892.45,
    value_compare=3_148_735.67,
    variation_pct=-40.0,
    period_base="FY23",
    period_compare="FY24"
)
```

### Niveles de Anonimización

| Nivel    | strict_mode | Descripción               |
| -------- | ----------- | ------------------------- |
| Estricto | `True`      | Solo categorías genéricas |
| Moderado | `False`     | Incluye categoría ILV     |

---

## 4. CONFIGURACIÓN SEGURA DE API KEYS

### ❌ INCORRECTO (Actual)

```python
# src/ai/ai_service.py - LÍNEA 24
OPENAI_API_KEY = "sk-proj-FsUoxAgU4VPKWP5bK7pD..."  # ¡EXPUESTA!
```

### ✅ CORRECTO (Recomendado)

**Paso 1: Crear archivo `.env`**

```env
# .env (en la raíz del proyecto)
OPENAI_API_KEY=sk-proj-tu-clave-aquí
OLLAMA_HOST=http://localhost:11434
```

**Paso 2: Añadir `.env` a `.gitignore`**

```gitignore
# .gitignore
.env
.env.local
.env.*.local
```

**Paso 3: Modificar código**

```python
# src/ai/ai_service.py
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY no configurada. "
        "Crea un archivo .env con OPENAI_API_KEY=tu-clave"
    )
```

**Paso 4: Rotar la clave expuesta**

```
1. Ir a: https://platform.openai.com/api-keys
2. Eliminar la clave expuesta
3. Crear una nueva clave
4. Guardarla en .env
```

---

## 5. COMPARATIVA DE OPCIONES

### Tabla de Decisión

| Criterio          | OpenAI + Anon. | Ollama Local   | Rule-Based   |
| ----------------- | -------------- | -------------- | ------------ |
| Calidad preguntas | ⭐⭐⭐⭐⭐     | ⭐⭐⭐         | ⭐⭐         |
| Privacidad        | ⭐⭐⭐⭐       | ⭐⭐⭐⭐⭐     | ⭐⭐⭐⭐⭐   |
| Costo             | 💰💰           | 💰 (hardware)  | 💰 (ninguno) |
| Velocidad         | ⭐⭐⭐         | ⭐⭐           | ⭐⭐⭐⭐⭐   |
| Requiere internet | ✅ Sí          | ❌ No          | ❌ No        |
| Requiere GPU      | ❌ No          | ✅ Recomendado | ❌ No        |

### Recomendaciones por Caso de Uso

| Escenario                            | Recomendación               |
| ------------------------------------ | --------------------------- |
| Datos muy sensibles (fusiones, OPAs) | **Ollama** o **Rule-Based** |
| Uso interno normal                   | **OpenAI + Anonimización**  |
| Sin presupuesto IA                   | **Rule-Based**              |
| Máxima calidad preguntas             | **OpenAI + Anonimización**  |
| Empresa con políticas estrictas GDPR | **Ollama**                  |

---

## 6. CUMPLIMIENTO NORMATIVO

### GDPR (UE)

| Requisito GDPR          | Estado                         |
| ----------------------- | ------------------------------ |
| Minimización de datos   | ✅ Con anonimización           |
| Derecho al olvido       | ⚠️ Depende de OpenAI           |
| Transferencias fuera UE | ⚠️ OpenAI está en EE.UU.       |
| Consentimiento          | ❓ Responsabilidad del usuario |

**Recomendación para GDPR estricto:** Usar Ollama local.

### SOX / Auditoría Financiera

- Los datos anonimizados NO revelan información que afecte a la auditoría
- El sistema mantiene trazabilidad local completa
- Los reportes generados NO contienen indicios del proveedor de IA

---

## 7. CHECKLIST DE SEGURIDAD

### Antes de Producción

- [ ] Mover API key a variable de entorno
- [ ] Crear archivo `.env` local
- [ ] Añadir `.env` a `.gitignore`
- [ ] Rotar la clave expuesta en GitHub
- [ ] Configurar `DataAnonymizer` con `strict_mode=True`
- [ ] Verificar que prompts no incluyen datos sensibles
- [ ] Documentar política de uso de IA

### Verificación de Anonimización

```python
# Script de verificación
from src.ai.data_anonymizer import DataAnonymizer

anonymizer = DataAnonymizer(strict_mode=True)
result = anonymizer.anonymize(
    description="NOMBRE_SENSIBLE_EMPRESA",
    account_code="7000012345",
    value_base=5_000_000,
    value_compare=3_000_000,
    variation_pct=-40.0,
    period_base="FY23",
    period_compare="FY24"
)

# Verificar que no aparece el nombre sensible
prompt = create_safe_prompt(result)
assert "NOMBRE_SENSIBLE_EMPRESA" not in prompt
assert "5000000" not in prompt
assert "3000000" not in prompt
print("✅ Anonimización verificada")
```

---

## 8. ARQUITECTURA DE PRIVACIDAD

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FLUJO DE DATOS                              │
└─────────────────────────────────────────────────────────────────────┘

     ZONA SEGURA (Tu PC)                    ZONA EXTERNA (Internet)
┌────────────────────────────┐        ┌──────────────────────────────┐
│                            │        │                              │
│  ┌──────────────────────┐  │        │                              │
│  │     Excel Input      │  │        │                              │
│  │   (datos sensibles)  │  │        │                              │
│  └──────────┬───────────┘  │        │                              │
│             │              │        │                              │
│             ▼              │        │                              │
│  ┌──────────────────────┐  │        │                              │
│  │   DataNormalizer     │  │        │                              │
│  │   (procesa datos)    │  │        │                              │
│  └──────────┬───────────┘  │        │                              │
│             │              │        │                              │
│             ▼              │        │                              │
│  ┌──────────────────────┐  │        │                              │
│  │  🛡️ DataAnonymizer   │  │        │                              │
│  │  (protege datos)     │──────────────┐                           │
│  └──────────┬───────────┘  │        │  │                           │
│             │              │        │  │  Solo datos anónimos      │
│             │              │        │  ▼                           │
│  ┌──────────┴───────────┐  │        │  ┌─────────────────────────┐│
│  │   Datos Originales   │  │        │  │       OpenAI API        ││
│  │   (quedan locales)   │  │        │  │                         ││
│  └──────────────────────┘  │        │  │  Ve: "Cuenta ingresos"  ││
│                            │        │  │  Ve: "-40%"             ││
│                            │        │  │  Ve: "magnitud grande"  ││
│                            │        │  │                         ││
│                            │        │  │  NO ve: montos          ││
│                            │        │  │  NO ve: nombres         ││
│                            │        │  │  NO ve: códigos         ││
│                            │        │  └────────────┬────────────┘│
│                            │        │               │              │
│  ┌──────────────────────┐  │        │               │              │
│  │   Pregunta Generada  │◄─────────────────────────┘              │
│  │   (texto genérico)   │  │        │                              │
│  └──────────┬───────────┘  │        │                              │
│             │              │        │                              │
│             ▼              │        │                              │
│  ┌──────────────────────┐  │        │                              │
│  │    Excel Output      │  │        │                              │
│  │  (pregunta + datos   │  │        │                              │
│  │   originales)        │  │        │                              │
│  └──────────────────────┘  │        │                              │
│                            │        │                              │
└────────────────────────────┘        └──────────────────────────────┘
```

---

## 9. FAQ

### ¿OpenAI puede ver los montos de mi empresa?

**Con anonimización:** NO. Solo ve "cuenta grande" o "cuenta pequeña".

**Sin anonimización:** SÍ. Los montos exactos irían en el prompt.

### ¿OpenAI guarda los datos?

Según la política de OpenAI (2024):

- API calls NO se usan para entrenar modelos por defecto
- Datos se retienen 30 días para monitoreo de abuso
- Se puede optar out de retención contactando a OpenAI

**Recomendación:** Incluso así, usar anonimización.

### ¿Puedo usar esto para due diligence de fusiones confidenciales?

**Recomendación:** Usar **Ollama** (local) para operaciones altamente sensibles.

### ¿El modo rule_based genera buenas preguntas?

Las preguntas son más genéricas pero funcionales. Ejemplo:

- **OpenAI:** "Explique los factores que han contribuido a la reducción del 40% en ingresos operativos, detallando si corresponde a pérdida de clientes o cambios en precios."
- **Rule-based:** "Explique la reducción del 40% en esta cuenta de ingresos."

---

## 10. CONTACTO Y SOPORTE

Para reportar vulnerabilidades de seguridad o problemas de privacidad:

1. NO abrir un issue público en GitHub
2. Contactar directamente al equipo de desarrollo
3. Incluir descripción detallada del problema

---

## Ver También

- [ALGORITHM.md](ALGORITHM.md) - Detalles del anonimizador
- [SECURITY.md](SECURITY.md) - Configuración segura
- `src/ai/data_anonymizer.py` - Código fuente del anonimizador
