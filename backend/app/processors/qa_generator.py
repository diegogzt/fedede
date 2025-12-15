"""
Generador de reportes Q&A para Due Diligence Financiero.

Este módulo genera el archivo de salida Q&A con el formato requerido:
- Mapeo ILV jerárquico
- Valores por periodo fiscal
- Variaciones y porcentajes
- Preguntas automáticas (con IA o basadas en reglas)
- Exportación a CSV/Excel
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime
import logging

from app.processors.models import (
    Account,
    BalanceSheet,
    Period,
    Priority,
    Status,
    QAItem,
    QAReport
)
from app.processors.financial_analyzer import FinancialAnalyzer, VariationResult, AnalysisConfig
from app.processors.data_normalizer import DataNormalizer
from app.core.exceptions import ReportGenerationError
from app.config.translations import TranslationManager, Language
from app.engine.rules import RuleEngine

# Importar ExcelExporter
try:
    from app.processors.excel_exporter import ExcelExporter
    EXCEL_EXPORTER_AVAILABLE = True
except ImportError:
    EXCEL_EXPORTER_AVAILABLE = False
    ExcelExporter = None

logger = logging.getLogger(__name__)


# Mapeo ILV predefinido basado en estructura de cuentas
DEFAULT_ILV_MAPPING = {
    # Ingresos -> EBITDA -> Revenue
    '70': {'level1': 'EBITDA', 'level2': 'Revenue', 'level3': 'Gross revenue'},
    '71': {'level1': 'EBITDA', 'level2': 'Revenue', 'level3': 'Other revenue'},
    '72': {'level1': 'EBITDA', 'level2': 'Revenue', 'level3': 'Other revenue'},
    '73': {'level1': 'EBITDA', 'level2': 'Revenue', 'level3': 'Other revenue'},
    '74': {'level1': 'EBITDA', 'level2': 'Revenue', 'level3': 'Other revenue'},
    '75': {'level1': 'EBITDA', 'level2': 'Revenue', 'level3': 'Other revenue'},
    '76': {'level1': 'EBITDA', 'level2': 'Revenue', 'level3': 'Financial income'},
    '77': {'level1': 'EBITDA', 'level2': 'Revenue', 'level3': 'Extraordinary income'},
    
    # Gastos -> EBITDA -> COGS/OPEX
    '60': {'level1': 'EBITDA', 'level2': 'COGS', 'level3': 'Purchases'},
    '61': {'level1': 'EBITDA', 'level2': 'COGS', 'level3': 'Variation in stock'},
    '62': {'level1': 'EBITDA', 'level2': 'OPEX', 'level3': 'External services'},
    '63': {'level1': 'EBITDA', 'level2': 'OPEX', 'level3': 'Taxes'},
    '64': {'level1': 'EBITDA', 'level2': 'OPEX', 'level3': 'Personnel costs'},
    '65': {'level1': 'EBITDA', 'level2': 'OPEX', 'level3': 'Other operating expenses'},
    '66': {'level1': 'EBITDA', 'level2': 'Financial expenses', 'level3': 'Financial expenses'},
    '67': {'level1': 'EBITDA', 'level2': 'Extraordinary', 'level3': 'Extraordinary expenses'},
    '68': {'level1': 'EBITDA', 'level2': 'D&A', 'level3': 'Depreciation & Amortization'},
    '69': {'level1': 'EBITDA', 'level2': 'Provisions', 'level3': 'Provisions'},
    
    # Activo -> Balance
    '20': {'level1': 'Balance', 'level2': 'Assets', 'level3': 'Intangible assets'},
    '21': {'level1': 'Balance', 'level2': 'Assets', 'level3': 'Tangible assets'},
    '22': {'level1': 'Balance', 'level2': 'Assets', 'level3': 'Real estate investments'},
    '23': {'level1': 'Balance', 'level2': 'Assets', 'level3': 'Fixed assets in progress'},
    '24': {'level1': 'Balance', 'level2': 'Assets', 'level3': 'Financial assets'},
    '25': {'level1': 'Balance', 'level2': 'Assets', 'level3': 'Long-term investments'},
    
    # Existencias
    '30': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Inventory'},
    '31': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Inventory'},
    '32': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Inventory'},
    '33': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Inventory'},
    '34': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Inventory'},
    '35': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Inventory'},
    '36': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Inventory'},
    
    # Deudores/Acreedores
    '40': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Trade payables'},
    '41': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Trade payables'},
    '43': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Trade receivables'},
    '44': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Trade receivables'},
    '46': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Personnel'},
    '47': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Public entities'},
    '48': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Accruals'},
    '49': {'level1': 'Balance', 'level2': 'Working Capital', 'level3': 'Provisions'},
    
    # Cuentas financieras
    '50': {'level1': 'Balance', 'level2': 'Financial Position', 'level3': 'Short-term debt'},
    '51': {'level1': 'Balance', 'level2': 'Financial Position', 'level3': 'Short-term debt'},
    '52': {'level1': 'Balance', 'level2': 'Financial Position', 'level3': 'Short-term investments'},
    '53': {'level1': 'Balance', 'level2': 'Financial Position', 'level3': 'Short-term investments'},
    '54': {'level1': 'Balance', 'level2': 'Financial Position', 'level3': 'Short-term investments'},
    '55': {'level1': 'Balance', 'level2': 'Financial Position', 'level3': 'Intercompany'},
    '56': {'level1': 'Balance', 'level2': 'Financial Position', 'level3': 'Cash pending'},
    '57': {'level1': 'Balance', 'level2': 'Financial Position', 'level3': 'Cash & equivalents'},
    
    # Patrimonio
    '10': {'level1': 'Balance', 'level2': 'Equity', 'level3': 'Share capital'},
    '11': {'level1': 'Balance', 'level2': 'Equity', 'level3': 'Reserves'},
    '12': {'level1': 'Balance', 'level2': 'Equity', 'level3': 'Retained earnings'},
    '13': {'level1': 'Balance', 'level2': 'Equity', 'level3': 'Grants'},
    '14': {'level1': 'Balance', 'level2': 'Liabilities', 'level3': 'Provisions'},
    '15': {'level1': 'Balance', 'level2': 'Liabilities', 'level3': 'Long-term debt'},
    '16': {'level1': 'Balance', 'level2': 'Liabilities', 'level3': 'Long-term debt'},
    '17': {'level1': 'Balance', 'level2': 'Liabilities', 'level3': 'Long-term debt'},
    '18': {'level1': 'Balance', 'level2': 'Liabilities', 'level3': 'Bonds'},
    '19': {'level1': 'Balance', 'level2': 'Liabilities', 'level3': 'Provisions'},
}


class QAGenerator:
    """
    Generador de reportes Q&A para Due Diligence.
    
    Características:
    - Mapeo ILV automático basado en códigos de cuenta
    - Generación de preguntas automáticas (IA o reglas)
    - Múltiples formatos de salida (CSV, Excel)
    - Ordenamiento por prioridad
    - Modo sin IA disponible
    """
    
    def __init__(
        self,
        ilv_mapping: Optional[Dict[str, Dict[str, str]]] = None,
        analysis_config: Optional[AnalysisConfig] = None,
        rule_threshold_percent: Optional[float] = None,
        rule_threshold_absolute: Optional[float] = None,
        # Compat legacy (IA eliminada; se ignoran)
        use_ai: bool = False,
        ai_mode: Optional[str] = None,
    ):
        """
        Inicializa el generador.
        
        Args:
            ilv_mapping: Mapeo de prefijos de cuenta a categorías ILV
        """
        self.ilv_mapping = ilv_mapping or DEFAULT_ILV_MAPPING
        self.normalizer = DataNormalizer()
        self.analyzer = FinancialAnalyzer(config=analysis_config)
        self.rule_engine = RuleEngine()
        if rule_threshold_percent is not None:
            self.rule_engine.variation_threshold_percent = float(rule_threshold_percent)
        if rule_threshold_absolute is not None:
            self.rule_engine.variation_threshold_absolute = float(rule_threshold_absolute)
        
        # Mantener compatibilidad con tests/scripts antiguos
        _ = use_ai
        _ = ai_mode

        # Inicializar servicio de IA si está disponible y habilitado
        self._ai_service: Optional[AIService] = None
        # AI initialization disabled
        self._ai_service = None
    
    def _parse_ai_mode(self, mode_str: Optional[str]):
        """Parsea string de modo a AIMode enum. (Deprecated)"""
        return None
        
    @property
    def ai_enabled(self) -> bool:
        """Verifica si la IA está habilitada y disponible."""
        return self._ai_service is not None and self._ai_service.is_ai_enabled
    
    def get_ai_status(self) -> Dict[str, Any]:
        """Obtiene el estado del servicio de IA."""
        if self._ai_service:
            return self._ai_service.get_status()
        return {
            "mode": "disabled",
            "ai_enabled": False,
            "ollama_available": False,
            "model": None
        }
    
    def get_ilv_for_account(self, account_code: str) -> Dict[str, str]:
        """
        Obtiene el mapeo ILV para un código de cuenta.
        
        Args:
            account_code: Código de cuenta (ej: "70100000")
            
        Returns:
            Dict con level1, level2, level3
        """
        if not account_code:
            return {}

        # Normalizar
        code = str(account_code).strip()
        if not code:
            return {}
        
        # Buscar por prefijos de mayor a menor longitud
        for prefix_len in range(len(code), 1, -1):
            prefix = code[:prefix_len]
            if prefix in self.ilv_mapping:
                return self.ilv_mapping[prefix]

        # Heurística: completar mapeo Balance si no hay prefijo exacto.
        # Evita celdas vacías en Mapping para cuentas BS no cubiertas por DEFAULT_ILV_MAPPING.
        first = code[:1]
        if first in {"1", "2", "3", "4", "5"}:
            if first == "2":
                return {"level1": "Balance", "level2": "Assets", "level3": "Other assets"}
            if first in {"3", "4"}:
                return {"level1": "Balance", "level2": "Working Capital", "level3": "Other working capital"}
            if first == "5":
                return {"level1": "Balance", "level2": "Financial Position", "level3": "Other financial position"}
            # first == "1"
            return {"level1": "Balance", "level2": "Liabilities", "level3": "Other liabilities"}

        return {}

    def _dedupe_drivers_questions(self, items: List[QAItem]) -> None:
        """Elimina la sub-pregunta genérica de "drivers" repetida en cuentas similares.

        Regla: si varias filas comparten el MISMO texto de la línea (i) de drivers
        (y la misma categoría ILV), se mantiene solo en la primera (ya ordenada por prioridad)
        y en el resto se deja únicamente la sub-pregunta (ii), renumerada como (i).
        """
        import re

        # Dedupe por categoría + par de periodos (ignorando el %), para evitar
        # repetir el bloque genérico de drivers en muchas subcuentas.
        seen: set[tuple[str, str, str, str, str]] = set()

        for item in items:
            q = (getattr(item, "question", None) or "").strip()
            if not q:
                continue

            lines = [ln.strip() for ln in q.splitlines() if ln.strip()]
            if len(lines) < 2:
                continue

            first = lines[0]
            if not first.startswith('(i) Comentar de manera general los principales "drivers"'):
                continue

            m = re.search(r"entre\s+(FY\d+|YTD\d+)\s+y\s+(FY\d+|YTD\d+)", first)
            period_base = m.group(1) if m else ""
            period_compare = m.group(2) if m else ""

            key = (
                (item.mapping_ilv_1 or ""),
                (item.mapping_ilv_2 or ""),
                (item.mapping_ilv_3 or ""),
                period_base,
                period_compare,
            )

            if key in seen:
                # Mantener el resto de líneas (normalmente solo la (ii)) y renumerar.
                remainder = "\n".join(lines[1:]).strip()
                remainder = re.sub(r"^\(ii\)\s*", "", remainder, flags=re.IGNORECASE)
                remainder = re.sub(r"^\(i\)\s*", "", remainder, flags=re.IGNORECASE)
                item.question = (f"(i) {remainder}").strip() if remainder else None
            else:
                seen.add(key)
    
    def generate_report(
        self,
        balance: BalanceSheet,
        include_all_accounts: bool = False,
        min_priority: Priority = Priority.BAJA
    ) -> QAReport:
        """
        Genera el reporte Q&A completo - UNA FILA POR CUENTA.
        
        Args:
            balance: BalanceSheet con datos
            include_all_accounts: Si incluir cuentas sin variación significativa
            min_priority: Prioridad mínima a incluir
            
        Returns:
            QAReport con todos los items
        """
        # Detectar periodos fiscales
        fiscal_periods = self.normalizer.detect_fiscal_periods(balance)

        # Plantilla esperada: usar solo 2 FY + 2 YTD más recientes.
        fy_all = list(fiscal_periods.get('fiscal_years', []) or [])
        ytd_all = list(fiscal_periods.get('ytd_periods', []) or [])
        fy_periods = fy_all[-2:] if len(fy_all) >= 2 else fy_all
        ytd_periods = ytd_all[-2:] if len(ytd_all) >= 2 else ytd_all
        target_periods = fy_periods + ytd_periods
        
        # Agregar valores a periodos fiscales
        aggregated = self.normalizer.aggregate_to_periods(balance, target_periods)
        
        # Calcular ingresos totales por periodo para porcentajes
        revenue_totals = self._calculate_revenue_totals(balance, target_periods, aggregated)
        
        # Generar pares de comparación
        # Generar pares de comparación (solo los periodos seleccionados)
        comparison_pairs = []
        if len(fy_periods) >= 2:
            comparison_pairs.append((fy_periods[0], fy_periods[1]))
        if len(ytd_periods) >= 2:
            comparison_pairs.append((ytd_periods[0], ytd_periods[1]))
        if not comparison_pairs:
            comparison_pairs = self.normalizer.get_comparison_pairs(balance)
        
        # Analizar variaciones
        variations = self.analyzer.analyze_variations(balance, comparison_pairs)
        
        # Agrupar variaciones por cuenta
        variations_by_account = {}
        for var in variations:
            if var.account_code not in variations_by_account:
                variations_by_account[var.account_code] = []
            variations_by_account[var.account_code].append(var)
        
        # Determinar prioridad máxima por cuenta
        priority_order = {Priority.ALTA: 0, Priority.MEDIA: 1, Priority.BAJA: 2}
        min_priority_value = priority_order[min_priority]
        
        items: List[QAItem] = []

        # `balance.accounts` puede traer el mismo código varias veces (p.ej. activos
        # distintos compartiendo cuenta). Si iteramos tal cual, se duplican filas y
        # preguntas idénticas. Generamos 1 item por `account_code`.
        descriptions_by_code: Dict[str, List[str]] = {}
        for account in balance.accounts:
            code = (getattr(account, "code", None) or "").strip()
            if not code:
                continue
            desc = (getattr(account, "description", None) or "").strip()
            if code not in descriptions_by_code:
                descriptions_by_code[code] = []
            if desc and desc not in descriptions_by_code[code]:
                descriptions_by_code[code].append(desc)

        unique_account_codes = list(descriptions_by_code.keys())

        for account_code in unique_account_codes:
            descriptions = descriptions_by_code.get(account_code) or []
            # Usar la descripción más específica (más larga) si hay varias.
            description = max(descriptions, key=len) if descriptions else ''

            account_variations = variations_by_account.get(account_code, [])
            
            # Determinar prioridad máxima de las variaciones de esta cuenta
            if account_variations:
                max_priority = min(
                    (priority_order[v.priority] for v in account_variations),
                    default=2
                )
                priority = next(
                    (p for p, val in priority_order.items() if val == max_priority),
                    Priority.BAJA
                )
            else:
                priority = Priority.BAJA
            
            # Filtrar por prioridad mínima
            if priority_order[priority] > min_priority_value:
                if not include_all_accounts:
                    continue
            
            # Obtener valores agregados
            account_values = aggregated.get(account_code, {})
            if not account_values and not include_all_accounts:
                continue
            
            # Obtener mapeo ILV
            ilv = self.get_ilv_for_account(account_code)
            
            # Calcular variaciones consolidadas
            all_variations = {}
            all_var_pcts = {}
            pct_over_revenue = {}
            pp_changes = {}
            
            for var in account_variations:
                key = f"{var.period_base}_vs_{var.period_compare}"
                if var.absolute_variation is not None:
                    all_variations[key] = var.absolute_variation
                if var.percentage_variation is not None:
                    all_var_pcts[key] = var.percentage_variation
                if var.percentage_over_revenue_base is not None:
                    pct_over_revenue[var.period_base] = var.percentage_over_revenue_base
                if var.percentage_over_revenue_compare is not None:
                    pct_over_revenue[var.period_compare] = var.percentage_over_revenue_compare
                if var.pp_change is not None:
                    pp_changes[key] = var.pp_change
            
            # Calcular % sobre ingresos para todos los periodos
            for period in target_periods:
                if period not in pct_over_revenue and period in account_values:
                    if period in revenue_totals and revenue_totals[period] != 0:
                        pct_over_revenue[period] = (account_values[period] / revenue_totals[period]) * 100
            
            # Generar pregunta y razón si hay variación significativa
            question = None
            reason = None

            if account_variations:
                # Estilo “plantilla” para PL (6/7): intenta construir pregunta con FY + YTD si existe.
                if account_code and account_code.startswith(('6', '7')):
                    q, r = self._generate_pl_like_question(account_code, description, account_variations)
                    if (q or '').strip():
                        question, reason = q, r

                # Fallback: elegir la primera variación que realmente dispara una pregunta (umbrales + reglas).
                if not (question or '').strip():
                    _prio = {Priority.ALTA: 0, Priority.MEDIA: 1, Priority.BAJA: 2}
                    for candidate in sorted(
                        account_variations,
                        key=lambda v: (
                            _prio.get(getattr(v, "priority", Priority.BAJA), 2),
                            -(abs(getattr(v, "absolute_variation", 0) or 0)),
                            -(abs(getattr(v, "percentage_variation", 0) or 0)),
                        ),
                    ):
                        q, r = self._generate_question_and_reason_for_variation(candidate)
                        if (q or "").strip():
                            question, reason = q, r
                            break
            
            item = QAItem(
                mapping_ilv_1=ilv.get('level1'),
                mapping_ilv_2=ilv.get('level2'),
                mapping_ilv_3=ilv.get('level3'),
                description=description,
                account_code=account_code,
                values=account_values,
                variations=all_variations,
                variation_percentages=all_var_pcts,
                percentages_over_revenue=pct_over_revenue,
                percentage_point_changes=pp_changes,
                question=question,
                reason=reason,
                priority=priority,
                status=Status.ABIERTO
            )
            
            items.append(item)
        
        # Ordenar items
        items = self._sort_items(items)

        # Evitar repetición de la pregunta genérica de "drivers" en múltiples líneas similares
        self._dedupe_drivers_questions(items)
        
        # Crear reporte
        report = QAReport(
            items=items,
            source_file=balance.source_file,
            analysis_periods=target_periods,
            total_revenue=revenue_totals
        )
        
        logger.info(f"Reporte Q&A generado: {len(items)} items")
        
        return report

    def _normalize_variation_numbers(self, var):
        """Normaliza pct/abs/valores para evitar NaN/Inf y devolver floats consistentes."""
        import math

        pct = getattr(var, "percentage_variation", None)
        abs_val = getattr(var, "absolute_variation", None)
        previous_value = getattr(var, "value_base", None)
        current_value = getattr(var, "value_compare", None)

        def _norm(x, default=0.0):
            if x is None:
                return default
            try:
                x = float(x)
            except Exception:
                return default
            try:
                if math.isnan(x) or math.isinf(x):
                    return default
            except Exception:
                return default
            return x

        pct = _norm(pct, 0.0)
        previous_value = _norm(previous_value, 0.0)
        current_value = _norm(current_value, 0.0)

        if abs_val is None:
            abs_val = current_value - previous_value
        abs_val = _norm(abs_val, current_value - previous_value)

        # Si base=0, el % puede quedar 0; sintetizar para no perder materialidad
        if previous_value == 0.0 and current_value != 0.0 and pct == 0.0:
            pct = 100.0 if abs_val >= 0 else -100.0

        return pct, abs_val, previous_value, current_value

    def _pick_best_variation(self, variations, predicate):
        """Selecciona una variación 'mejor' para preguntar dado un predicado (FY/YTD, etc.)."""
        _prio = {Priority.ALTA: 0, Priority.MEDIA: 1, Priority.BAJA: 2}
        candidates = [v for v in variations if predicate(v)]
        if not candidates:
            return None

        candidates.sort(
            key=lambda v: (
                _prio.get(getattr(v, "priority", Priority.BAJA), 2),
                -(abs(getattr(v, "absolute_variation", 0) or 0)),
                -(abs(getattr(v, "percentage_variation", 0) or 0)),
            )
        )
        return candidates[0]

    def _generate_pl_like_question(self, account_code: str, description: str, variations) -> tuple:
        """Pregunta estilo PL de plantilla: FY + YTD cuando aplique, con detección simple de ralentización."""
        # Elegir mejor FY y mejor YTD (si existen)
        fy_var = self._pick_best_variation(
            variations,
            lambda v: str(getattr(v, "period_base", "")).startswith("FY") and str(getattr(v, "period_compare", "")).startswith("FY"),
        )
        ytd_var = self._pick_best_variation(
            variations,
            lambda v: str(getattr(v, "period_base", "")).startswith("YTD") and str(getattr(v, "period_compare", "")).startswith("YTD"),
        )

        # Si no hay ninguna, no hacer nada
        if not fy_var and not ytd_var:
            return None, None

        # Para decidir si dispara, respetar umbrales del RuleEngine
        def qualifies(v):
            pct, abs_val, _, _ = self._normalize_variation_numbers(v)
            return self.rule_engine.should_generate_question(pct, abs_val, description)

        if fy_var and not qualifies(fy_var):
            fy_var = None
        if ytd_var and not qualifies(ytd_var):
            ytd_var = None

        if not fy_var and not ytd_var:
            return None, None

        group = account_code[:1]
        is_income = group == '7'
        is_expense = group == '6'

        def pct_int(p):
            try:
                return int(round(abs(float(p))))
            except Exception:
                return 0

        parts_raw = []
        reasons = []

        if fy_var:
            fy_pct, fy_abs, _, _ = self._normalize_variation_numbers(fy_var)
            fy_prev = str(getattr(fy_var, 'period_base', 'FY'))
            fy_curr = str(getattr(fy_var, 'period_compare', 'FY'))
            direction = 'crecimiento' if fy_pct > 0 else 'reducción'
            noun = 'ingresos' if is_income else 'gastos' if is_expense else 'saldo'
            parts_raw.append(
                f"Comentar de manera general los principales \"drivers\" del {direction} de {noun} entre {fy_prev} y {fy_curr} ({pct_int(fy_pct)}%)."
            )
            reasons.append(f"FY: {fy_prev}→{fy_curr} pct={fy_pct:+.1f}% abs={fy_abs:+,.0f}")

        if ytd_var:
            ytd_pct, ytd_abs, _, _ = self._normalize_variation_numbers(ytd_var)
            ytd_prev = str(getattr(ytd_var, 'period_base', 'YTD'))
            ytd_curr = str(getattr(ytd_var, 'period_compare', 'YTD'))
            noun = 'ingresos' if is_income else 'gastos' if is_expense else 'saldo'

            # Detectar “ralentización” vs FY si ambos existen y misma dirección
            slowdown = False
            if fy_var:
                fy_pct, _, _, _ = self._normalize_variation_numbers(fy_var)
                if (fy_pct == 0) or (ytd_pct == 0):
                    slowdown = False
                else:
                    same_sign = (fy_pct > 0 and ytd_pct > 0) or (fy_pct < 0 and ytd_pct < 0)
                    slowdown = same_sign and abs(ytd_pct) < abs(fy_pct) * 0.75

            if slowdown:
                fy_pct, _, _, _ = self._normalize_variation_numbers(fy_var)
                fy_prev = str(getattr(fy_var, 'period_base', 'FY'))
                fy_curr = str(getattr(fy_var, 'period_compare', 'FY'))
                parts_raw.append(
                    f"¿Por qué se observa una ralentización en {noun} entre {ytd_prev} y {ytd_curr} ({pct_int(ytd_pct)}%) "
                    f"respecto a la variación observada entre {fy_prev} y {fy_curr} ({pct_int(fy_pct)}%)?"
                )
            else:
                parts_raw.append(
                    f"Explicar la variación registrada en {noun} entre {ytd_prev} y {ytd_curr} ({pct_int(ytd_pct)}%)."
                )
            reasons.append(f"YTD: {ytd_prev}→{ytd_curr} pct={ytd_pct:+.1f}% abs={ytd_abs:+,.0f}")

        # Si solo hubo FY y no YTD, añadir un (ii) genérico para mantener formato
        if fy_var and not ytd_var:
            parts_raw.append("Indicar si el cambio es recurrente o puntual y aportar soporte (desglose, contratos/facturas, conciliaciones).")

        # Numeración consistente (si solo hay 1 parte, será (i))
        parts = [f"({i}) {txt}" for i, txt in zip(["i", "ii", "iii"], parts_raw)]
        question = "\n".join(parts) if parts else None
        reason = " | ".join(reasons) if reasons else None
        return question, reason

    def _generate_question_and_reason_for_variation(self, var):
        """Genera pregunta y razón (regla aplicada) para una variación."""
        import math

        desc = var.account_description
        pct = var.percentage_variation
        abs_val = var.absolute_variation
        period_base = var.period_base
        period_compare = var.period_compare

        previous_value = getattr(var, "value_base", None)
        current_value = getattr(var, "value_compare", None)

        if pct is None:
            pct = 0.0
        else:
            try:
                if math.isnan(pct) or math.isinf(pct):
                    pct = 0.0
            except TypeError:
                # Si no es numérico, dejarlo en 0
                pct = 0.0

        if previous_value is None:
            previous_value = 0.0
        else:
            try:
                if math.isnan(previous_value) or math.isinf(previous_value):
                    previous_value = 0.0
            except TypeError:
                previous_value = 0.0

        if current_value is None:
            current_value = 0.0
        else:
            try:
                if math.isnan(current_value) or math.isinf(current_value):
                    current_value = 0.0
            except TypeError:
                current_value = 0.0

        abs_invalid = False
        if abs_val is None:
            abs_invalid = True
        else:
            try:
                abs_invalid = math.isnan(abs_val) or math.isinf(abs_val)
            except TypeError:
                abs_invalid = True

        if abs_invalid:
            abs_val = current_value - previous_value

        # Normalizar abs_val si sigue inválido tras el fallback
        try:
            if math.isnan(abs_val) or math.isinf(abs_val):
                abs_val = 0.0
        except TypeError:
            abs_val = 0.0

        # Si la base es 0, el % suele venir como NaN/Inf (que arriba normalizamos a 0).
        # Para no perder casos materiales, asignamos un % sintético si hay variación real.
        if previous_value == 0.0 and current_value != 0.0 and pct == 0.0:
            pct = 100.0 if (abs_val or 0) >= 0 else -100.0

        context = {
            "account_name": desc,
            "account_code": var.account_code,
            "level1": "",
            "level2": "",
            "level3": "",
            "variation_percent": pct,
            "variation_absolute": abs_val,
            "current_value": current_value,
            "previous_value": previous_value,
            "period_current": period_compare,
            "period_previous": period_base,
        }

        if var.account_code:
            prefix = var.account_code[:2]
            if prefix in self.ilv_mapping:
                context["level1"] = self.ilv_mapping[prefix].get("level1", "")
                context["level2"] = self.ilv_mapping[prefix].get("level2", "")
                context["level3"] = self.ilv_mapping[prefix].get("level3", "")

        # Si no cumple umbrales, el motor devuelve (None, None) y no generamos pregunta.
        return self.rule_engine.generate_question_with_reason(context)
    
    def _calculate_revenue_totals(
        self,
        balance: BalanceSheet,
        periods: List[str],
        aggregated: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Calcula el total de ingresos por periodo."""
        revenue_totals = {}
        revenue_codes = {
            (getattr(a, "code", "") or "").strip()
            for a in balance.accounts
            if (getattr(a, "code", "") or "").strip().startswith('7')
        }
        for period in periods:
            total = 0.0
            for code in revenue_codes:
                values = aggregated.get(code, {})
                if period in values:
                    total += abs(values[period])
            if total > 0:
                revenue_totals[period] = total
        return revenue_totals
    
    def _generate_question_for_variation(self, var) -> str:
        """Genera una pregunta basada en la variación usando el RuleEngine."""
        import math
        
        desc = var.account_description
        pct = var.percentage_variation
        abs_val = var.absolute_variation
        period_base = var.period_base
        period_compare = var.period_compare

        previous_value = getattr(var, "value_base", None)
        current_value = getattr(var, "value_compare", None)
        
        # Verificar si pct es None o NaN
        if pct is None or (isinstance(pct, float) and math.isnan(pct)):
            pct = 0.0

        # Normalizar variación absoluta
        if abs_val is None or (isinstance(abs_val, float) and math.isnan(abs_val)):
            if previous_value is not None and current_value is not None:
                abs_val = current_value - previous_value
            else:
                abs_val = 0.0

        if previous_value is None or (isinstance(previous_value, float) and math.isnan(previous_value)):
            previous_value = 0.0
        if current_value is None or (isinstance(current_value, float) and math.isnan(current_value)):
            current_value = 0.0

        # Preparar contexto para el RuleEngine
        context = {
            "account_name": desc,
            "account_code": var.account_code,
            "level1": "",  # TODO: Obtener del mapping
            "level2": "",  # TODO: Obtener del mapping
            "level3": "",  # TODO: Obtener del mapping
            "variation_percent": pct,
            "variation_absolute": abs_val,
            "current_value": current_value,
            "previous_value": previous_value,
            "period_current": period_compare,
            "period_previous": period_base,
        }
        
        # Intentar obtener niveles ILV
        if var.account_code:
            prefix = var.account_code[:2]
            if prefix in self.ilv_mapping:
                context["level1"] = self.ilv_mapping[prefix].get("level1", "")
                context["level2"] = self.ilv_mapping[prefix].get("level2", "")
                context["level3"] = self.ilv_mapping[prefix].get("level3", "")

        question = self.rule_engine.generate_question(context)
        
        if question:
            return question
            
        # Fallback simple si el RuleEngine no devuelve nada pero hay variación
        if abs(pct) > 20:
             return f"Se observa una variación significativa de {pct:.1f}% en '{desc}'. ¿Cuál es la razón?"
             
        return f"Comentar variación en '{desc}'."
    
    def generate_report_with_ai(
        self,
        balance: BalanceSheet,
        include_all_accounts: bool = False,
        min_priority: Priority = Priority.BAJA,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> QAReport:
        """
        Genera el reporte Q&A (Método legacy, ahora usa reglas).
        """
        # Simplemente llamar al generador estándar, ya que la IA ha sido eliminada
        return self.generate_report(balance, include_all_accounts, min_priority)
    
    def _generate_ai_question(self, item: QAItem) -> Optional[Any]:
        """Genera una pregunta contextual usando el servicio de IA. (Deprecated)"""
        return None
        context_data = self._prepare_item_context(item)
        
        if not context_data:
            return None
        
        try:
            # Generar la pregunta usando el prompt contextual
            question = self._ai_service.generate_contextual_question(context_data)
            return question
        except Exception as e:
            logger.warning(f"Error generando pregunta contextual para {item.account_code}: {e}")
            return None
    
    def _prepare_item_context(self, item: QAItem) -> Optional[Dict[str, Any]]:
        """Prepara el contexto completo de un item para generar pregunta y razón con IA."""
        if not item.values:
            return None
        
        # Valores por periodo
        period_values_lines = []
        for period in sorted(item.values.keys()):
            val = item.values[period]
            if val is not None:
                period_values_lines.append(f"  {period}: {val:,.0f}")
        
        # Variaciones
        variations_lines = []
        for key, pct in sorted(item.variation_percentages.items()):
            if pct is not None:
                parts = key.split('_vs_')
                if len(parts) == 2:
                    abs_var = item.variations.get(key, 0)
                    direction = "aumento" if pct > 0 else "disminución"
                    variations_lines.append(
                        f"  {parts[0]} vs {parts[1]}: {direction} de {abs(pct):.1f}% ({abs_var:,.0f})"
                    )
        
        # Porcentajes sobre ingresos
        revenue_pct_lines = []
        for period in sorted(item.percentages_over_revenue.keys()):
            pct = item.percentages_over_revenue[period]
            if pct is not None:
                revenue_pct_lines.append(f"  {period}: {pct:.1f}%")
        
        # Puntos porcentuales
        pp_lines = []
        for key, pp in sorted(item.percentage_point_changes.items()):
            if pp is not None and abs(pp) >= 0.5:  # Solo si es significativo
                parts = key.split('_vs_')
                if len(parts) == 2:
                    direction = "incremento" if pp > 0 else "reducción"
                    pp_lines.append(f"  {parts[0]} vs {parts[1]}: {direction} de {abs(pp):.1f} p.p.")
        
        # Detectar tipo de cuenta
        account_type = "General"
        if item.account_code:
            if item.account_code.startswith('7'):
                account_type = "Ingreso"
            elif item.account_code.startswith('6'):
                account_type = "Gasto/Costo"
            elif item.account_code.startswith(('1', '2')):
                account_type = "Activo"
            elif item.account_code.startswith(('4', '5')):
                account_type = "Pasivo/Patrimonio"
        
        # Detectar contexto adicional
        context_lines = []
        
        # Detectar nuevos/desaparecidos
        periods_with_value = [p for p, v in item.values.items() if v is not None and v != 0]
        all_periods = sorted(item.values.keys())
        if periods_with_value and len(periods_with_value) < len(all_periods):
            first_period = min(periods_with_value)
            last_period = max(periods_with_value)
            if first_period != all_periods[0]:
                context_lines.append(f"  - Nuevo concepto desde {first_period}")
            if last_period != all_periods[-1]:
                context_lines.append(f"  - Concepto desaparecido después de {last_period}")
        
        # Detectar inversión de tendencia
        if len(variations_lines) >= 2:
            variations_values = [item.variation_percentages.get(k, 0) for k in sorted(item.variation_percentages.keys())]
            if len(variations_values) >= 2:
                # Comparar signos para detectar inversión
                if (variations_values[0] > 0 and variations_values[-1] < 0) or \
                   (variations_values[0] < 0 and variations_values[-1] > 0):
                    context_lines.append("  - Inversión de tendencia detectada")
                # Detectar aceleración/desaceleración
                elif abs(variations_values[-1]) > abs(variations_values[0]) * 1.5:
                    context_lines.append("  - Aceleración de tendencia")
                elif abs(variations_values[-1]) < abs(variations_values[0]) * 0.5:
                    context_lines.append("  - Desaceleración de tendencia")
        
        return {
            'account_code': item.account_code or '',
            'description': item.description or '',
            'category': item.mapping_ilv_2 or item.mapping_ilv_1 or 'General',
            'account_type': account_type,
            'period_values': "\\n".join(period_values_lines) if period_values_lines else "Sin datos",
            'variations_summary': "\\n".join(variations_lines) if variations_lines else "Sin variaciones significativas",
            'revenue_percentages': "\\n".join(revenue_pct_lines) if revenue_pct_lines else "No aplica",
            'percentage_points': "\\n".join(pp_lines) if pp_lines else "Sin cambios significativos en p.p.",
            'context_info': "\\n".join(context_lines) if context_lines else "Sin contexto adicional"
        }
    
    def generate_executive_summary(self, report: QAReport) -> str:
        """
        Genera un resumen ejecutivo del análisis.
        
        Args:
            report: QAReport generado
            
        Returns:
            Resumen en formato Markdown
        """
        # Contar prioridades
        priority_counts = report.count_by_priority()
        
        # Top variaciones
        top_variations = []
        for item in report.items[:10]:
            if item.variation_percentages:
                var_key = next(iter(item.variation_percentages.keys()))
                var_pct = item.variation_percentages[var_key]
                top_variations.append({
                    'description': item.description,
                    'variation_pct': var_pct or 0,
                    'priority': item.priority.value
                })
        
        # Determinar periodos
        periods = report.analysis_periods
        period_base = periods[0] if periods else "N/A"
        period_compare = periods[-1] if len(periods) > 1 else periods[0] if periods else "N/A"
        
        if self._ai_service:
            # (Eliminado por requerimiento de usuario: No AI)
            pass
        
        # Fallback a resumen basado en reglas
        return self._generate_rule_based_summary(
            period_base, period_compare, len(report.items),
            priority_counts, top_variations
        )
    
    def _generate_rule_based_summary(
        self,
        period_base: str,
        period_compare: str,
        total_items: int,
        priority_counts: Dict[str, int],
        top_variations: List[Dict]
    ) -> str:
        """Genera resumen basado en reglas."""
        lines = [
            "# Resumen Ejecutivo - Due Diligence Financiero",
            "",
            f"**Periodo analizado:** {period_base} a {period_compare}",
            "",
            "## Hallazgos Principales",
            f"- Total de variaciones analizadas: {total_items}",
            f"- Variaciones de alta prioridad: {priority_counts.get('Alta', 0)}",
            f"- Variaciones de media prioridad: {priority_counts.get('Media', 0)}",
            f"- Variaciones de baja prioridad: {priority_counts.get('Baja', 0)}",
            "",
        ]
        
        if top_variations:
            lines.append("## Top Variaciones")
            import math
            for var in top_variations[:5]:
                pct = var.get('variation_pct')
                if pct is None or (isinstance(pct, float) and (math.isnan(pct) or math.isinf(pct))):
                    pct_str = "N/A"
                else:
                    pct_str = f"{pct:.1f}%"
                lines.append(
                    f"- **{var['description']}**: {pct_str} "
                    f"(Prioridad: {var['priority']})"
                )
            lines.append("")
        
        lines.extend([
            "## Recomendaciones",
            "1. Revisar las variaciones de alta prioridad con la dirección",
            "2. Solicitar documentación soporte para cada hallazgo",
            "3. Verificar consistencia de respuestas",
            ""
        ])
        
        return "\n".join(lines)
    
    def _sort_items(self, items: List[QAItem]) -> List[QAItem]:
        """Ordena items por ILV y prioridad."""
        priority_order = {Priority.ALTA: 0, Priority.MEDIA: 1, Priority.BAJA: 2}
        
        return sorted(items, key=lambda x: (
            x.mapping_ilv_1 or 'ZZZ',  # Agrupa por ILV1
            x.mapping_ilv_2 or 'ZZZ',  # Luego por ILV2
            x.mapping_ilv_3 or 'ZZZ',  # Luego por ILV3
            priority_order.get(x.priority, 99),  # Alta prioridad primero
            x.account_code or 'ZZZ'  # Finalmente por código
        ))
    
    def to_dataframe(
        self,
        report: QAReport,
        periods: Optional[List[str]] = None,
        language: Language = Language.SPANISH
    ) -> pd.DataFrame:
        """
        Convierte el reporte a DataFrame.
        
        Args:
            report: QAReport a convertir
            periods: Periodos a incluir (None = todos)
            language: Idioma para las columnas
            
        Returns:
            DataFrame con formato Q&A
        """
        if periods is None:
            periods = report.analysis_periods
        
        tm = TranslationManager(language)
        cols = tm.get_columns()
        
        rows = []
        
        for item in report.items:
            row = {
                cols['mapping_ilv_1']: item.mapping_ilv_1 or '',
                cols['mapping_ilv_2']: item.mapping_ilv_2 or '',
                cols['mapping_ilv_3']: item.mapping_ilv_3 or '',
                cols['description']: item.description,
                cols['account']: item.account_code,
            }
            
            # Agregar valores por periodo
            for period in periods:
                value = item.values.get(period)
                row[period] = value if value is not None else ''
            
            # Agregar variaciones absolutas
            for key, value in item.variations.items():
                parts = key.split('_vs_')
                if len(parts) == 2:
                    col_name = f"{cols['var_abs']} {parts[0]}/{parts[1]}"
                    row[col_name] = value if value is not None else ''
            
            # Agregar variaciones porcentuales
            for key, value in item.variation_percentages.items():
                parts = key.split('_vs_')
                if len(parts) == 2:
                    col_name = f"{cols['var_pct']} {parts[0]}/{parts[1]}"
                    row[col_name] = value if value is not None else ''
            
            # Agregar % sobre ingresos
            for period, value in item.percentages_over_revenue.items():
                col_name = f"{cols['pct_revenue']} {period}"
                row[col_name] = value if value is not None else ''
            
            # Agregar cambio en puntos porcentuales
            for key, value in item.percentage_point_changes.items():
                parts = key.split('_vs_')
                if len(parts) == 2:
                    col_name = f"{cols['var_pp']} {parts[0]}/{parts[1]}"
                    row[col_name] = value if value is not None else ''
            
            # Agregar campos Q&A
            row[cols['question']] = item.question or ''
            row[cols['reason']] = item.reason or ''
            row[cols['priority']] = item.priority.value
            row[cols['status']] = item.status.value
            row[cols['response']] = item.response or ''
            row[cols['follow_up']] = item.follow_up or ''
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def export_to_csv(
        self,
        report: QAReport,
        output_path: Union[str, Path],
        periods: Optional[List[str]] = None,
        encoding: str = 'utf-8-sig'  # utf-8 con BOM para Excel
    ) -> Path:
        """
        Exporta el reporte a CSV.
        
        Args:
            report: QAReport a exportar
            output_path: Ruta de salida
            periods: Periodos a incluir
            encoding: Codificación del archivo
            
        Returns:
            Ruta del archivo creado
        """
        output_path = Path(output_path)
        
        try:
            df = self.to_dataframe(report, periods)
            
            # Crear directorio si no existe
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Exportar
            df.to_csv(output_path, index=False, encoding=encoding)
            
            logger.info(f"Reporte exportado a CSV: {output_path}")
            return output_path
            
        except Exception as e:
            raise ReportGenerationError(
                report_type="CSV",
                message=f"Error al exportar a CSV: {str(e)}"
            )
    
    def export_to_excel(
        self,
        report: QAReport,
        output_path: Union[str, Path],
        periods: Optional[List[str]] = None,
        sheet_name: str = 'Q&A'
    ) -> Path:
        """
        Exporta el reporte a Excel con formato.
        
        Args:
            report: QAReport a exportar
            output_path: Ruta de salida
            periods: Periodos a incluir
            sheet_name: Nombre de la hoja
            
        Returns:
            Ruta del archivo creado
        """
        output_path = Path(output_path)
        
        try:
            df = self.to_dataframe(report, periods)
            
            # Crear directorio si no existe
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Exportar con formato
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Obtener workbook y worksheet
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]
                
                # Formatos
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#4472C4',
                    'font_color': 'white',
                    'border': 1
                })
                
                number_format = workbook.add_format({
                    'num_format': '#,##0.00',
                    'border': 1
                })
                
                percent_format = workbook.add_format({
                    'num_format': '0.00%',
                    'border': 1
                })
                
                priority_alta_format = workbook.add_format({
                    'bg_color': '#FF6B6B',
                    'border': 1
                })
                
                priority_media_format = workbook.add_format({
                    'bg_color': '#FFE66D',
                    'border': 1
                })
                
                # Aplicar formato a encabezados
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Ajustar ancho de columnas
                for i, col in enumerate(df.columns):
                    max_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                    worksheet.set_column(i, i, min(max_len, 50))
                
                # Aplicar formato condicional por prioridad
                priority_col = list(df.columns).index('Prioridad')
                worksheet.conditional_format(
                    1, priority_col, len(df), priority_col,
                    {'type': 'text', 'criteria': 'containing', 
                     'value': 'Alta', 'format': priority_alta_format}
                )
                worksheet.conditional_format(
                    1, priority_col, len(df), priority_col,
                    {'type': 'text', 'criteria': 'containing', 
                     'value': 'Media', 'format': priority_media_format}
                )
                
                # Congelar primera fila
                worksheet.freeze_panes(1, 0)
            
            logger.info(f"Reporte exportado a Excel: {output_path}")
            return output_path
            
        except Exception as e:
            raise ReportGenerationError(
                report_type="Excel",
                message=f"Error al exportar a Excel: {str(e)}"
            )
    
    def export_to_excel_with_tabs(
        self,
        report: QAReport,
        output_path: Union[str, Path],
        project_name: str = "Project",
        include_sheets: Optional[List[str]] = None,
        language: Language = Language.SPANISH,
    ) -> Path:
        """
        Exporta el reporte a Excel con múltiples pestañas y formato profesional.
        
        Genera un archivo Excel con:
        - Pestaña General: Resumen con preguntas por área
        - Pestaña PL: Cuenta de pérdidas y ganancias
        - Pestaña BS: Balance Sheet
        - Pestaña Compras: Detalle de compras
        - Pestaña Transporte: Detalle de transporte
        
        Args:
            report: QAReport a exportar
            output_path: Ruta de salida
            project_name: Nombre del proyecto para el título
            include_sheets: Lista de pestañas a incluir (None = todas)
            
        Returns:
            Ruta del archivo creado
        """
        if not EXCEL_EXPORTER_AVAILABLE:
            raise ImportError(
                "ExcelExporter no disponible. Asegúrate de tener openpyxl instalado."
            )
        
        output_path = Path(output_path)
        
        try:
            exporter = ExcelExporter(project_name=project_name)
            return exporter.export(
                report,
                output_path,
                include_sheets,
                language=language,
                questions_only=True,
            )
            
        except Exception as e:
            raise ReportGenerationError(
                message=f"Error al exportar a Excel con pestañas: {str(e)}",
                details={"report_type": "Excel (multi-tab)"}
            )
    
    def generate_summary(self, report: QAReport) -> Dict[str, Any]:
        """
        Genera un resumen del reporte.
        
        Returns:
            Dict con estadísticas del reporte
        """
        priority_counts = report.count_by_priority()
        
        return {
            'total_items': len(report.items),
            'priority_counts': priority_counts,
            'open_questions': len(report.get_open_items()),
            'analysis_periods': report.analysis_periods,
            'source_file': report.source_file,
            'generated_at': datetime.now().isoformat(),
            'items_with_questions': len([i for i in report.items if i.question])
        }


def process_balance_to_qa(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    output_format: str = 'csv'
) -> Path:
    """
    Función de conveniencia para procesar un archivo de balance a Q&A.
    
    Args:
        input_file: Archivo de balance de entrada
        output_file: Archivo de salida (auto-generado si None)
        output_format: Formato de salida ('csv' o 'excel')
        
    Returns:
        Ruta del archivo generado
    """
    from app.processors.excel_reader import ExcelReader
    
    input_path = Path(input_file)
    
    # Generar nombre de salida si no se proporciona
    if output_file is None:
        suffix = '.xlsx' if output_format == 'excel' else '.csv'
        output_file = input_path.parent / f"{input_path.stem}_QA{suffix}"
    
    output_path = Path(output_file)
    
    # Leer balance
    reader = ExcelReader(input_path)
    reader.read()
    balance = reader.to_balance_sheet()
    
    # Generar Q&A
    generator = QAGenerator()
    report = generator.generate_report(balance)
    
    # Exportar
    if output_format == 'excel':
        return generator.export_to_excel(report, output_path)
    else:
        return generator.export_to_csv(report, output_path)

