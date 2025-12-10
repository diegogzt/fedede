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
from app.processors.financial_analyzer import FinancialAnalyzer, VariationResult
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
    ):
        """
        Inicializa el generador.
        
        Args:
            ilv_mapping: Mapeo de prefijos de cuenta a categorías ILV
        """
        self.ilv_mapping = ilv_mapping or DEFAULT_ILV_MAPPING
        self.normalizer = DataNormalizer()
        self.analyzer = FinancialAnalyzer()
        self.rule_engine = RuleEngine()
        
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
        
        # Buscar por prefijos de mayor a menor longitud
        for prefix_len in range(len(account_code), 1, -1):
            prefix = account_code[:prefix_len]
            if prefix in self.ilv_mapping:
                return self.ilv_mapping[prefix]
        
        return {}
    
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
        target_periods = fiscal_periods['fiscal_years'] + fiscal_periods['ytd_periods']
        
        # Agregar valores a periodos fiscales
        aggregated = self.normalizer.aggregate_to_periods(balance, target_periods)
        
        # Calcular ingresos totales por periodo para porcentajes
        revenue_totals = self._calculate_revenue_totals(balance, target_periods, aggregated)
        
        # Generar pares de comparación
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
        
        for account in balance.accounts:
            account_code = account.code
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
                # Usar la variación más significativa
                significant_var = max(
                    account_variations,
                    key=lambda v: abs(v.percentage_variation or 0)
                )
                question = self._generate_question_for_variation(significant_var)
                # Usar el analizador para generar la razón
                reason = self.analyzer._generate_reason(significant_var)
            
            item = QAItem(
                mapping_ilv_1=ilv.get('level1'),
                mapping_ilv_2=ilv.get('level2'),
                mapping_ilv_3=ilv.get('level3'),
                description=account.description,
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
        
        # Crear reporte
        report = QAReport(
            items=items,
            source_file=balance.source_file,
            analysis_periods=target_periods,
            total_revenue=revenue_totals
        )
        
        logger.info(f"Reporte Q&A generado: {len(items)} items")
        
        return report
    
    def _calculate_revenue_totals(
        self,
        balance: BalanceSheet,
        periods: List[str],
        aggregated: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Calcula el total de ingresos por periodo."""
        revenue_totals = {}
        for period in periods:
            total = 0.0
            for account in balance.accounts:
                if account.code.startswith('7'):  # Ingresos
                    values = aggregated.get(account.code, {})
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
        
        # Verificar si pct es None o NaN
        if pct is None or (isinstance(pct, float) and math.isnan(pct)):
            pct = 0.0

        # Preparar contexto para el RuleEngine
        context = {
            "account_name": desc,
            "account_code": var.account_code,
            "level1": "", # TODO: Obtener del mapping
            "level2": "", # TODO: Obtener del mapping
            "level3": "", # TODO: Obtener del mapping
            "variation_percent": pct,
            "variation_abs": abs_val,
            "period_current": period_compare,
            "period_previous": period_base
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
        include_sheets: Optional[List[str]] = None
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
            return exporter.export(report, output_path, include_sheets)
            
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

