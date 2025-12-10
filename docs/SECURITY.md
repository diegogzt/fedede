# Guía de Seguridad - FDD

## Configuración Segura del Sistema

### 1. Variables de Entorno

#### Crear archivo `.env`

```env
# .env (en la raíz del proyecto)
# ¡NUNCA COMMITEAR ESTE ARCHIVO!

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-tu-clave-aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.7

# Ollama Configuration (alternativa local)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2

# Application Settings
LOG_LEVEL=INFO
STRICT_ANONYMIZATION=true
```

#### Verificar `.gitignore`

```gitignore
# Secrets
.env
.env.local
.env.*.local
*.pem
*.key

# Datos sensibles
data/input/*.xlsx
data/input/*.csv
data/output/*.xlsx

# Logs con información sensible
logs/*.log
```

### 2. Rotación de Claves API

Si una clave API ha sido expuesta (en código, logs, o repositorio):

1. **Revocar inmediatamente** en el dashboard del proveedor
2. **Generar nueva clave**
3. **Actualizar archivo `.env`**
4. **Buscar en historial de git** posibles exposiciones anteriores

```powershell
# Buscar claves expuestas en historial
git log -p --all -S 'sk-proj' -- .
git log -p --all -S 'api_key' -- .
```

### 3. Permisos de Archivos

```powershell
# En Windows, limitar acceso al archivo .env
icacls .env /inheritance:r /grant:r "%USERNAME%:F"
```

---

## Configuración de Modos de IA

### Modo OpenAI (con anonimización)

```python
# src/config/settings.py
AI_CONFIG = {
    'provider': 'openai',
    'model': 'gpt-4o-mini',
    'anonymize': True,           # SIEMPRE True para OpenAI
    'strict_mode': True,         # Máxima anonimización
}
```

### Modo Ollama (local)

```python
# src/config/settings.py
AI_CONFIG = {
    'provider': 'ollama',
    'model': 'llama2',           # o 'mistral', 'codellama', etc.
    'host': 'http://localhost:11434',
    'anonymize': False,          # Opcional para local
}
```

### Modo Rule-Based (sin IA)

```python
# src/config/settings.py
AI_CONFIG = {
    'provider': 'rule_based',
    'anonymize': False,          # No aplica
}
```

---

## Auditoría de Seguridad

### Logs de Acceso a IA

El sistema registra todas las llamadas a servicios de IA:

```python
# Ubicación: logs/ai_calls.log
# Formato:
# [timestamp] [provider] [anonymized: true/false] [tokens_used]
```

### Verificar qué se envía

```python
# Script de diagnóstico
from src.ai.data_anonymizer import DataAnonymizer

# Habilitar logging detallado
import logging
logging.getLogger('src.ai').setLevel(logging.DEBUG)

# Ver exactamente qué se enviaría
anonymizer = DataAnonymizer(strict_mode=True)
result = anonymizer.anonymize(
    description="Tu descripción de prueba",
    account_code="7000001",
    value_base=1000000,
    value_compare=500000,
    variation_pct=-50.0,
    period_base="FY23",
    period_compare="FY24"
)

print("=== DATOS QUE SE ENVIARÍAN A OPENAI ===")
print(f"Categoría: {result.category_generic}")
print(f"Tipo: {result.account_type}")
print(f"Variación: {result.variation_direction} {result.variation_magnitude}")
print(f"Porcentaje: {result.variation_percentage}%")
print(f"Rango: {result.value_range}")
print(f"Prioridad: {result.priority_suggested}")
print()
print("=== DATOS QUE NO SE ENVÍAN (quedan locales) ===")
print(f"Descripción original: {result._original_description}")
print(f"Valor base: {result._original_value_base}")
print(f"Valor compare: {result._original_value_compare}")
print(f"Código cuenta: {result._account_code}")
```

---

## Checklist Pre-Despliegue

### Obligatorio

- [ ] API key en variable de entorno (no en código)
- [ ] `.env` añadido a `.gitignore`
- [ ] Clave anterior rotada si fue expuesta
- [ ] `strict_mode=True` en DataAnonymizer
- [ ] Logs no contienen datos sensibles

### Recomendado

- [ ] Usar Ollama para datos muy sensibles
- [ ] Revisar prompts.py por posibles fugas
- [ ] Configurar retención de logs
- [ ] Documentar política de uso de IA

### Para Producción

- [ ] Usar Azure Key Vault o similar para secrets
- [ ] Configurar alertas de uso anómalo de API
- [ ] Implementar rate limiting
- [ ] Backup de configuración encriptado

---

## Respuesta a Incidentes

### Si se detecta fuga de API key

1. **INMEDIATO:** Revocar la clave en el dashboard del proveedor
2. Generar nueva clave
3. Actualizar todos los sistemas que la usen
4. Revisar logs de uso para detectar abuso
5. Documentar el incidente

### Si se detecta envío de datos sensibles

1. Revisar logs de llamadas a IA
2. Identificar qué datos se enviaron
3. Contactar al proveedor si es necesario
4. Corregir la configuración de anonimización
5. Evaluar impacto y notificar según políticas

---

## Contacto

Para reportar vulnerabilidades de seguridad:

- Contactar directamente al equipo de desarrollo
- NO usar issues públicos de GitHub
- Incluir pasos para reproducir y evidencia
