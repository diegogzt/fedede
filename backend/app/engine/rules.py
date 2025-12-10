from typing import Optional, Dict, Any
import re

class RuleEngine:
    """
    Motor de reglas para la generación de preguntas de Due Diligence Financiero.
    Reemplaza el sistema basado en IA por un sistema determinista basado en patrones.
    """

    def __init__(self):
        # Umbrales de variación para disparar preguntas
        self.variation_threshold_percent = 10.0  # 10%
        self.variation_threshold_absolute = 1000.0  # 1000 unidades monetarias

        # Patrones de exclusión (Vehículos específicos, máquinas específicas con bajo impacto)
        self.exclusion_patterns = [
            r"RENTING\s+KIA",
            r"RENTING\s+BMW",
            r"RENTING\s+JAGUAR",
            r"LEASING\s+.*VEHICULO",
            r"LEASING\s+.*COCHE",
            r"MANTENIMIENTO\s+VEHICULO",
            r"SEGURO\s+VEHICULO",
            r"SUMINISTROS\s+OFICINA", # Gasto menor
            r"MATERIAL\s+OFICINA",
        ]

    def should_generate_question(self, variation_percent: float, variation_abs: float, account_name: str) -> bool:
        """Determina si se debe generar una pregunta basada en la magnitud de la variación."""
        
        # Si es una cuenta excluida, no preguntar salvo que la variación sea enorme (ej. > 50k)
        for pattern in self.exclusion_patterns:
            if re.search(pattern, account_name, re.IGNORECASE):
                if abs(variation_abs) > 50000: # Excepción para grandes variaciones en cuentas excluidas
                    return True
                return False

        # Regla general: Variación significativa relativa O absoluta
        if abs(variation_percent) > self.variation_threshold_percent and abs(variation_abs) > self.variation_threshold_absolute:
            return True
        
        # Si la variación absoluta es muy grande, preguntar siempre
        if abs(variation_abs) > 10000:
            return True

        return False

    def generate_question(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Genera una pregunta basada en el contexto de la cuenta y sus variaciones.
        
        Contexto esperado:
        - account_name: str
        - account_code: str
        - level1: str (EBITDA, Balance)
        - level2: str (Revenue, OPEX, etc.)
        - level3: str (Personnel, Supplies, etc.)
        - variation_percent: float (FY vs FY-1)
        - variation_abs: float
        - period_current: str
        - period_previous: str
        """
        
        account_name = context.get("account_name", "")
        level2 = context.get("level2", "")
        level3 = context.get("level3", "")
        var_pct = context.get("variation_percent", 0.0)
        var_abs = context.get("variation_abs", 0.0)
        period_curr = context.get("period_current", "FY Actual")
        period_prev = context.get("period_previous", "FY Anterior")

        if not self.should_generate_question(var_pct, var_abs, account_name):
            return None

        # 1. Reglas de Ingresos (Revenue)
        if level2 == "Revenue":
            if var_pct > 0:
                return f"Comentar de manera general los principales 'drivers' del crecimiento de ingresos entre {period_prev} y {period_curr} ({var_pct:.1f}%)."
            else:
                return f"Explicar las razones de la disminución de ingresos entre {period_prev} y {period_curr} ({var_pct:.1f}%)."

        # 2. Reglas de Aprovisionamientos (Supplies/COGS)
        if level3 == "Purchases" or level3 == "Supplies":
            return 'Ver pestaña "Compras" para detalle de proveedores y evolución.'

        # 3. Reglas de Personal (Personnel costs)
        if level3 == "Personnel costs":
            if var_pct > 0:
                return f"Explicar el incremento del {var_pct:.1f}% en gastos de personal. ¿Se debe a nuevas contrataciones, revisiones salariales o indemnizaciones?"
            else:
                return f"Explicar la reducción en gastos de personal. ¿Ha habido salidas de personal significativas?"

        # 4. Reglas de Mantenimiento (Repairs and maintenance)
        if "MANTENIMIENTO" in account_name.upper() or "REPARACION" in account_name.upper():
            if var_pct > 0:
                return f"Explicar el mayor gasto registrado en {period_curr}. Indicar si es un gasto no recurrente o una reparación mayor."
            
        # 5. Reglas de Alquileres (Leases)
        if "ALQUILER" in account_name.upper() or "RENTING" in account_name.upper() or "LEASING" in account_name.upper():
             if var_pct > 0:
                return f"Explicar el incremento en gastos de arrendamiento. ¿Se han incorporado nuevos activos o renegociado contratos?"

        # 6. Reglas de Servicios Exteriores (External services) - Transporte
        if "TRANSPORTE" in account_name.upper():
             return f"Explicar la variación en costes de transporte en relación con el volumen de ventas."

        # 7. Regla por defecto para variaciones significativas
        if var_pct > 20:
            return f"Explicar la variación significativa ({var_pct:.1f}%) en esta partida."

        return None
