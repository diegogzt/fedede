"""
Analizador financiero para detección de variaciones significativas.

Este módulo proporciona análisis financiero avanzado:
- Detección de variaciones significativas
- Clasificación por prioridad
- Análisis de tendencias
- Detección de anomalías
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging

from src.processors.models import (
    Account, 
    BalanceSheet, 
    Period, 
    PeriodType,
    Priority,
    QAItem,
    QAReport,
    Status
)
from src.processors.data_normalizer import DataNormalizer
from src.config.settings import get_settings


logger = logging.getLogger(__name__)


class VariationType(Enum):
    """Tipo de variación detectada."""
    SIGNIFICANT_INCREASE = "aumento_significativo"
    SIGNIFICANT_DECREASE = "disminucion_significativa"
    NEW_ITEM = "item_nuevo"
    DISAPPEARED = "item_desaparecido"
    STABLE = "estable"
    MINOR_CHANGE = "cambio_menor"


@dataclass
class VariationResult:
    """Resultado de análisis de variación."""
    account_code: str
    account_description: str
    period_base: str
    period_compare: str
    value_base: Optional[float]
    value_compare: Optional[float]
    absolute_variation: Optional[float]
    percentage_variation: Optional[float]
    variation_type: VariationType
    priority: Priority
    
    # Contexto adicional
    percentage_over_revenue_base: Optional[float] = None
    percentage_over_revenue_compare: Optional[float] = None
    pp_change: Optional[float] = None  # Puntos porcentuales


@dataclass
class AnalysisConfig:
    """Configuración de umbrales para análisis."""
    # Umbral de variación porcentual para considerarse significativa
    significant_variation_threshold: float = 20.0  # 20%
    
    # Umbral de variación absoluta mínima (evitar falsos positivos en montos pequeños)
    min_absolute_variation: float = 1000.0
    
    # Umbral para prioridad alta
    high_priority_variation: float = 50.0  # 50%
    high_priority_absolute: float = 100000.0
    
    # Umbral para prioridad baja
    low_priority_variation: float = 10.0  # 10%
    
    # Cuentas de ingresos (códigos que empiezan con...)
    revenue_account_prefixes: List[str] = field(
        default_factory=lambda: ['70', '71', '72', '73', '74', '75']
    )
    
    # Cuentas de gastos principales
    expense_account_prefixes: List[str] = field(
        default_factory=lambda: ['60', '61', '62', '63', '64', '65', '66', '67', '68', '69']
    )


class FinancialAnalyzer:
    """
    Analizador financiero para detección de variaciones.
    
    Características:
    - Análisis de variaciones entre periodos
    - Clasificación automática por prioridad
    - Detección de anomalías
    - Cálculo de porcentajes sobre ingresos
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Inicializa el analizador.
        
        Args:
            config: Configuración de umbrales (usa defaults si None)
        """
        if config:
            self.config = config
        else:
            # Cargar desde settings globales
            settings = get_settings()
            self.config = AnalysisConfig(
                significant_variation_threshold=settings.report.percentage_threshold,
                high_priority_absolute=settings.report.materiality_threshold
            )
            
        self.normalizer = DataNormalizer()
    
    def analyze_variations(
        self,
        balance: BalanceSheet,
        period_pairs: Optional[List[Tuple[str, str]]] = None
    ) -> List[VariationResult]:
        """
        Analiza variaciones entre periodos.
        
        Args:
            balance: BalanceSheet con datos
            period_pairs: Pares de periodos a comparar (None = auto-detectar)
            
        Returns:
            Lista de resultados de variación
        """
        if period_pairs is None:
            period_pairs = self.normalizer.get_comparison_pairs(balance)
        
        results: List[VariationResult] = []
        
        # Calcular totales agregados
        fiscal_periods = self.normalizer.detect_fiscal_periods(balance)
        target_periods = fiscal_periods['fiscal_years'] + fiscal_periods['ytd_periods']
        aggregated = self.normalizer.aggregate_to_periods(balance, target_periods)
        
        # Obtener cuentas de ingresos para calcular porcentajes
        revenue_accounts = self._get_revenue_accounts(balance)
        
        for account in balance.accounts:
            for base_period, compare_period in period_pairs:
                result = self._analyze_account_variation(
                    account=account,
                    base_period=base_period,
                    compare_period=compare_period,
                    aggregated_values=aggregated,
                    balance=balance,
                    revenue_accounts=revenue_accounts
                )
                
                if result and result.variation_type != VariationType.STABLE:
                    results.append(result)
        
        # Ordenar por prioridad y variación
        results.sort(key=lambda r: (
            0 if r.priority == Priority.ALTA else 1 if r.priority == Priority.MEDIA else 2,
            -(abs(r.percentage_variation or 0))
        ))
        
        logger.info(f"Análisis completado: {len(results)} variaciones detectadas")
        logger.info(f"  - Alta prioridad: {len([r for r in results if r.priority == Priority.ALTA])}")
        logger.info(f"  - Media prioridad: {len([r for r in results if r.priority == Priority.MEDIA])}")
        logger.info(f"  - Baja prioridad: {len([r for r in results if r.priority == Priority.BAJA])}")
        
        return results
    
    def _analyze_account_variation(
        self,
        account: Account,
        base_period: str,
        compare_period: str,
        aggregated_values: Dict[str, Dict[str, float]],
        balance: BalanceSheet,
        revenue_accounts: List[str]
    ) -> Optional[VariationResult]:
        """Analiza la variación de una cuenta específica."""
        
        # Obtener valores (de agregados si están disponibles, sino del account)
        if account.code in aggregated_values:
            value_base = aggregated_values[account.code].get(base_period)
            value_compare = aggregated_values[account.code].get(compare_period)
        else:
            value_base = account.get_value(base_period)
            value_compare = account.get_value(compare_period)
        
        # Calcular variaciones
        abs_var, pct_var = self._calculate_variation(value_base, value_compare)
        
        # Determinar tipo de variación
        var_type = self._classify_variation(value_base, value_compare, pct_var)
        
        # Determinar prioridad
        priority = self._determine_priority(abs_var, pct_var, account)
        
        # Calcular % sobre ingresos
        pct_rev_base = None
        pct_rev_compare = None
        pp_change = None
        
        if revenue_accounts:
            total_rev_base = sum(
                aggregated_values.get(code, {}).get(base_period, 0) 
                for code in revenue_accounts
            )
            total_rev_compare = sum(
                aggregated_values.get(code, {}).get(compare_period, 0) 
                for code in revenue_accounts
            )
            
            if total_rev_base and value_base is not None:
                pct_rev_base = (value_base / abs(total_rev_base)) * 100
            if total_rev_compare and value_compare is not None:
                pct_rev_compare = (value_compare / abs(total_rev_compare)) * 100
            
            if pct_rev_base is not None and pct_rev_compare is not None:
                pp_change = pct_rev_compare - pct_rev_base
        
        return VariationResult(
            account_code=account.code,
            account_description=account.description,
            period_base=base_period,
            period_compare=compare_period,
            value_base=value_base,
            value_compare=value_compare,
            absolute_variation=abs_var,
            percentage_variation=pct_var,
            variation_type=var_type,
            priority=priority,
            percentage_over_revenue_base=pct_rev_base,
            percentage_over_revenue_compare=pct_rev_compare,
            pp_change=pp_change
        )
    
    def _calculate_variation(
        self,
        value_base: Optional[float],
        value_compare: Optional[float]
    ) -> Tuple[Optional[float], Optional[float]]:
        """Calcula variación absoluta y porcentual."""
        if value_base is None and value_compare is None:
            return None, None
        
        if value_base is None:
            return value_compare, None  # Item nuevo
        
        if value_compare is None:
            return -value_base, None  # Item desapareció
        
        abs_var = value_compare - value_base
        
        if value_base == 0:
            pct_var = None if value_compare == 0 else (float('inf') if value_compare > 0 else float('-inf'))
        else:
            pct_var = (abs_var / abs(value_base)) * 100
        
        return abs_var, pct_var
    
    def _classify_variation(
        self,
        value_base: Optional[float],
        value_compare: Optional[float],
        pct_var: Optional[float]
    ) -> VariationType:
        """Clasifica el tipo de variación."""
        if value_base is None and value_compare is not None:
            return VariationType.NEW_ITEM
        
        if value_base is not None and value_compare is None:
            return VariationType.DISAPPEARED
        
        if pct_var is None:
            return VariationType.STABLE
        
        threshold = self.config.significant_variation_threshold
        
        if abs(pct_var) < self.config.low_priority_variation:
            return VariationType.STABLE
        elif abs(pct_var) < threshold:
            return VariationType.MINOR_CHANGE
        elif pct_var > 0:
            return VariationType.SIGNIFICANT_INCREASE
        else:
            return VariationType.SIGNIFICANT_DECREASE
    
    def _determine_priority(
        self,
        abs_var: Optional[float],
        pct_var: Optional[float],
        account: Account
    ) -> Priority:
        """Determina la prioridad basada en la magnitud de variación."""
        if abs_var is None or pct_var is None:
            return Priority.BAJA
        
        abs_abs_var = abs(abs_var)
        abs_pct_var = abs(pct_var)
        
        # Alta prioridad: variación muy significativa
        if abs_pct_var >= self.config.high_priority_variation:
            if abs_abs_var >= self.config.min_absolute_variation:
                return Priority.ALTA
        
        if abs_abs_var >= self.config.high_priority_absolute:
            return Priority.ALTA
        
        # Media prioridad: variación moderada
        if abs_pct_var >= self.config.significant_variation_threshold:
            if abs_abs_var >= self.config.min_absolute_variation:
                return Priority.MEDIA
        
        # Baja prioridad: resto
        return Priority.BAJA
    
    def _get_revenue_accounts(self, balance: BalanceSheet) -> List[str]:
        """Obtiene códigos de cuentas de ingresos."""
        revenue_codes = []
        for account in balance.accounts:
            for prefix in self.config.revenue_account_prefixes:
                if account.code.startswith(prefix):
                    revenue_codes.append(account.code)
                    break
        return revenue_codes
    
    def generate_qa_items(
        self,
        variations: List[VariationResult],
        ilv_mapping: Optional[Dict[str, Dict[str, str]]] = None
    ) -> List[QAItem]:
        """
        Genera items Q&A desde los resultados de variación.
        
        Args:
            variations: Lista de resultados de variación
            ilv_mapping: Mapeo de códigos de cuenta a categorías ILV
            
        Returns:
            Lista de QAItem
        """
        items: List[QAItem] = []
        
        for var in variations:
            # Obtener mapeo ILV si está disponible
            ilv = ilv_mapping.get(var.account_code, {}) if ilv_mapping else {}
            
            # Construir valores por periodo
            values = {}
            if var.value_base is not None:
                values[var.period_base] = var.value_base
            if var.value_compare is not None:
                values[var.period_compare] = var.value_compare
            
            # Construir variaciones
            variations_dict = {}
            if var.absolute_variation is not None:
                key = f"{var.period_base}_vs_{var.period_compare}"
                variations_dict[key] = var.absolute_variation
            
            var_pct_dict = {}
            if var.percentage_variation is not None:
                key = f"{var.period_base}_vs_{var.period_compare}"
                var_pct_dict[key] = var.percentage_variation
            
            # Porcentajes sobre ingresos
            pct_rev = {}
            if var.percentage_over_revenue_base is not None:
                pct_rev[var.period_base] = var.percentage_over_revenue_base
            if var.percentage_over_revenue_compare is not None:
                pct_rev[var.period_compare] = var.percentage_over_revenue_compare
            
            pp_changes = {}
            if var.pp_change is not None:
                pp_changes[f"{var.period_base}_vs_{var.period_compare}"] = var.pp_change
            
            # Generar pregunta automática y razón
            question = self._generate_question(var)
            reason = self._generate_reason(var)
            
            item = QAItem(
                mapping_ilv_1=ilv.get('level1'),
                mapping_ilv_2=ilv.get('level2'),
                mapping_ilv_3=ilv.get('level3'),
                description=var.account_description,
                account_code=var.account_code,
                values=values,
                variations=variations_dict,
                variation_percentages=var_pct_dict,
                percentages_over_revenue=pct_rev,
                percentage_point_changes=pp_changes,
                question=question,
                reason=reason,
                priority=var.priority,
                status=Status.ABIERTO
            )
            
            items.append(item)
        
        return items
    
    def _is_valid_number(self, value) -> bool:
        """Verifica si un valor es un número válido (no None, no NaN, no inf)."""
        import math
        if value is None:
            return False
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return False
        return True
    
    def _generate_reason(self, var: VariationResult) -> str:
        """Genera la razón de la pregunta basada en la variación."""
        pct = var.percentage_variation
        abs_var = var.absolute_variation
        pp = var.pp_change
        
        if var.variation_type == VariationType.NEW_ITEM:
            return "Nuevo concepto detectado"
        
        if var.variation_type == VariationType.DISAPPEARED:
            return "Concepto desaparecido"
            
        if var.variation_type in [VariationType.SIGNIFICANT_INCREASE, VariationType.SIGNIFICANT_DECREASE]:
            reasons = []
            
            # Prioridad a variación en pp si es significativa (> 3 pp)
            if pp is not None and abs(pp) >= 3.0:
                reasons.append(f"Variación > 3 pp")
            
            if pct is not None and abs(pct) >= self.config.significant_variation_threshold:
                reasons.append(f"Variación > {self.config.significant_variation_threshold}%")
            
            if abs_var is not None and abs(abs_var) >= self.config.min_absolute_variation:
                # Solo agregar importe si no hay otras razones más fuertes o si es muy relevante
                if not reasons: 
                    reasons.append(f"Importe > {self.config.min_absolute_variation:,.0f}")
                
            return " y ".join(reasons) if reasons else "Variación significativa"
            
        return "Revisión rutinaria"

    def _generate_question(self, var: VariationResult) -> str:
        """Genera una pregunta automática basada en la variación."""
        desc = var.account_description
        pct = var.percentage_variation
        
        if var.variation_type == VariationType.NEW_ITEM:
            return f"Se observa un nuevo concepto '{desc}' en {var.period_compare}. ¿Cuál es el origen de este item?"
        
        if var.variation_type == VariationType.DISAPPEARED:
            return f"El concepto '{desc}' presente en {var.period_base} no aparece en {var.period_compare}. ¿Cuál es la razón?"
        
        if var.variation_type == VariationType.SIGNIFICANT_INCREASE:
            pct_str = f"{pct:.1f}%" if self._is_valid_number(pct) else "significativo"
            return f"Se observa un incremento de {pct_str} en '{desc}' de {var.period_base} a {var.period_compare}. ¿Cuál es la razón de este aumento?"
        
        if var.variation_type == VariationType.SIGNIFICANT_DECREASE:
            pct_str = f"{abs(pct):.1f}%" if self._is_valid_number(pct) else "significativa"
            return f"Se observa una disminución de {pct_str} en '{desc}' de {var.period_base} a {var.period_compare}. ¿Cuál es la razón de esta reducción?"
        
        return f"Por favor explique las variaciones en '{desc}' entre {var.period_base} y {var.period_compare}."
    
    def create_qa_report(
        self,
        balance: BalanceSheet,
        variations: List[VariationResult],
        ilv_mapping: Optional[Dict[str, Dict[str, str]]] = None
    ) -> QAReport:
        """
        Crea un reporte Q&A completo.
        
        Args:
            balance: BalanceSheet original
            variations: Resultados de variación
            ilv_mapping: Mapeo ILV opcional
            
        Returns:
            QAReport completo
        """
        items = self.generate_qa_items(variations, ilv_mapping)
        
        # Calcular ingresos totales por periodo
        fiscal_periods = self.normalizer.detect_fiscal_periods(balance)
        target_periods = fiscal_periods['fiscal_years'] + fiscal_periods['ytd_periods']
        aggregated = self.normalizer.aggregate_to_periods(balance, target_periods)
        
        revenue_accounts = self._get_revenue_accounts(balance)
        total_revenue = {}
        
        for period in target_periods:
            total = sum(
                aggregated.get(code, {}).get(period, 0) 
                for code in revenue_accounts
            )
            if total != 0:
                total_revenue[period] = total
        
        return QAReport(
            items=items,
            source_file=balance.source_file,
            analysis_periods=target_periods,
            total_revenue=total_revenue
        )
    
    def get_top_variations(
        self,
        variations: List[VariationResult],
        top_n: int = 10,
        by_period: Optional[str] = None
    ) -> List[VariationResult]:
        """
        Obtiene las variaciones más significativas.
        
        Args:
            variations: Lista de variaciones
            top_n: Número de resultados
            by_period: Filtrar por periodo de comparación
            
        Returns:
            Top N variaciones
        """
        filtered = variations
        
        if by_period:
            filtered = [v for v in filtered if v.period_compare == by_period]
        
        # Ordenar por magnitud de variación
        sorted_vars = sorted(
            filtered,
            key=lambda v: abs(v.percentage_variation or 0),
            reverse=True
        )
        
        return sorted_vars[:top_n]
    
    def summarize_by_category(
        self,
        variations: List[VariationResult]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Resume variaciones por categoría de cuenta.
        
        Returns:
            Dict con resumen por categoría
        """
        categories: Dict[str, Dict[str, Any]] = {}
        
        for var in variations:
            # Determinar categoría por primer dígito del código
            category = self._get_category_name(var.account_code)
            
            if category not in categories:
                categories[category] = {
                    'count': 0,
                    'total_absolute_variation': 0.0,
                    'high_priority_count': 0,
                    'items': []
                }
            
            categories[category]['count'] += 1
            if var.absolute_variation:
                categories[category]['total_absolute_variation'] += var.absolute_variation
            if var.priority == Priority.ALTA:
                categories[category]['high_priority_count'] += 1
            categories[category]['items'].append(var)
        
        return categories
    
    def _get_category_name(self, code: str) -> str:
        """Obtiene el nombre de categoría según el código."""
        if not code:
            return 'Otros'
        
        category_names = {
            '1': 'Patrimonio y Pasivo',
            '2': 'Activo No Corriente',
            '3': 'Existencias',
            '4': 'Acreedores y Deudores',
            '5': 'Cuentas Financieras',
            '6': 'Compras y Gastos',
            '7': 'Ventas e Ingresos'
        }
        
        return category_names.get(code[0], 'Otros')
