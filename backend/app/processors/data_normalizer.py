"""
Normalizador de datos financieros.

Este módulo proporciona funcionalidad para normalizar y transformar
datos financieros, incluyendo:
- Conversión de formatos numéricos
- Agregación por periodos fiscales
- Cálculo de totales YTD
"""

from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
from collections import defaultdict
import logging

from app.processors.models import (
    Account, BalanceSheet, Period, PeriodType
)


logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Normalizador de datos financieros.
    
    Proporciona funcionalidades para:
    - Agregar valores mensuales a fiscales (FY)
    - Calcular Year-to-Date (YTD)
    - Normalizar estructuras de cuentas
    """
    
    # Meses por trimestre (Q1 = Ene-Mar, etc.)
    QUARTERS = {
        1: [1, 2, 3],    # Q1
        2: [4, 5, 6],    # Q2
        3: [7, 8, 9],    # Q3
        4: [10, 11, 12]  # Q4
    }
    
    def __init__(self, fiscal_year_start_month: int = 1):
        """
        Inicializa el normalizador.
        
        Args:
            fiscal_year_start_month: Mes de inicio del año fiscal (1 = enero)
        """
        self.fiscal_year_start_month = fiscal_year_start_month
    
    def calculate_fiscal_year_totals(
        self, 
        balance: BalanceSheet,
        years: Optional[List[int]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcula totales por año fiscal para cada cuenta.
        
        Args:
            balance: BalanceSheet con datos mensuales
            years: Lista de años a calcular (None = todos)
            
        Returns:
            Dict[account_code, Dict[fiscal_year, total]]
        """
        if years is None:
            years = balance.get_fiscal_years()
        
        result: Dict[str, Dict[str, float]] = {}
        
        for account in balance.accounts:
            account_totals: Dict[str, float] = {}
            
            for year in years:
                fy_name = f"FY{str(year)[2:]}"  # FY23, FY24
                
                # Sumar todos los meses del año
                total = 0.0
                months_found = 0
                
                for period in balance.periods:
                    if period.year == year and period.period_type == PeriodType.MONTHLY:
                        value = account.get_value(period.name)
                        if value is not None:
                            total += value
                            months_found += 1
                
                if months_found > 0:
                    account_totals[fy_name] = total
            
            if account_totals:
                result[account.code] = account_totals
        
        logger.info(f"Calculados totales fiscales para {len(result)} cuentas")
        return result
    
    def calculate_ytd(
        self,
        balance: BalanceSheet,
        reference_date: Optional[datetime] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcula valores Year-to-Date para cada cuenta.
        
        Args:
            balance: BalanceSheet con datos mensuales
            reference_date: Fecha de referencia (None = usar último periodo)
            
        Returns:
            Dict[account_code, Dict[ytd_name, total]]
        """
        # Determinar mes de referencia
        if reference_date is None:
            # Usar el último periodo disponible
            monthly_periods = [p for p in balance.periods if p.period_type == PeriodType.MONTHLY]
            if not monthly_periods:
                return {}
            monthly_periods.sort()
            last_period = monthly_periods[-1]
            ref_month = last_period.month
            ref_year = last_period.year
        else:
            ref_month = reference_date.month
            ref_year = reference_date.year
        
        result: Dict[str, Dict[str, float]] = {}
        years = balance.get_fiscal_years()
        
        for account in balance.accounts:
            account_ytd: Dict[str, float] = {}
            
            for year in years:
                # Para años anteriores al último, calcular YTD hasta el mismo mes
                # Para el año actual, calcular YTD hasta el mes actual
                end_month = ref_month if year == ref_year else ref_month
                
                ytd_name = f"YTD{str(year)[2:]}"
                total = 0.0
                months_found = 0
                
                for period in balance.periods:
                    if (period.year == year and 
                        period.period_type == PeriodType.MONTHLY and
                        period.month and period.month <= end_month):
                        
                        value = account.get_value(period.name)
                        if value is not None:
                            total += value
                            months_found += 1
                
                if months_found > 0:
                    account_ytd[ytd_name] = total
            
            if account_ytd:
                result[account.code] = account_ytd
        
        logger.info(f"Calculados YTD para {len(result)} cuentas (hasta mes {ref_month})")
        return result
    
    def calculate_variations(
        self,
        balance: BalanceSheet,
        period_pairs: List[Tuple[str, str]]
    ) -> Dict[str, Dict[str, Dict[str, Optional[float]]]]:
        """
        Calcula variaciones entre pares de periodos.
        
        Args:
            balance: BalanceSheet con datos
            period_pairs: Lista de tuplas (periodo_base, periodo_comparacion)
            
        Returns:
            Dict[account_code, Dict[pair_name, Dict['absolute'|'percentage', value]]]
        """
        result: Dict[str, Dict[str, Dict[str, Optional[float]]]] = {}
        
        for account in balance.accounts:
            account_variations: Dict[str, Dict[str, Optional[float]]] = {}
            
            for base_period, compare_period in period_pairs:
                pair_name = f"{base_period}_vs_{compare_period}"
                
                variation = account.calculate_variation(
                    base_period, compare_period, as_percentage=False
                )
                variation_pct = account.calculate_variation(
                    base_period, compare_period, as_percentage=True
                )
                
                account_variations[pair_name] = {
                    'absolute': variation,
                    'percentage': variation_pct
                }
            
            if account_variations:
                result[account.code] = account_variations
        
        return result
    
    def calculate_percentage_over_revenue(
        self,
        balance: BalanceSheet,
        revenue_account_codes: List[str],
        periods: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Calcula porcentaje de cada cuenta sobre ingresos totales.
        
        Args:
            balance: BalanceSheet con datos
            revenue_account_codes: Códigos de cuentas de ingresos
            periods: Periodos a calcular (None = todos)
            
        Returns:
            Dict[account_code, Dict[period, percentage]]
        """
        if periods is None:
            periods = balance.get_period_names()
        
        # Calcular ingresos totales por periodo
        revenue_by_period: Dict[str, float] = {}
        for period in periods:
            total_revenue = balance.calculate_total(period, revenue_account_codes)
            if total_revenue != 0:
                revenue_by_period[period] = total_revenue
        
        # Calcular porcentajes para cada cuenta
        result: Dict[str, Dict[str, Optional[float]]] = {}
        
        for account in balance.accounts:
            percentages: Dict[str, Optional[float]] = {}
            
            for period in periods:
                value = account.get_value(period)
                revenue = revenue_by_period.get(period)
                
                if value is not None and revenue and revenue != 0:
                    percentages[period] = (value / abs(revenue)) * 100
                else:
                    percentages[period] = None
            
            result[account.code] = percentages
        
        return result
    
    def calculate_percentage_points_variation(
        self,
        balance: BalanceSheet,
        revenue_account_codes: List[str],
        period_pairs: List[Tuple[str, str]]
    ) -> Dict[str, Dict[str, Optional[float]]]:
        """
        Calcula variación en puntos porcentuales del % sobre revenue.
        
        Args:
            balance: BalanceSheet con datos
            revenue_account_codes: Códigos de cuentas de ingresos
            period_pairs: Lista de tuplas (periodo_base, periodo_comparacion)
            
        Returns:
            Dict[account_code, Dict[pair_name, pp_variation]]
        """
        # Primero calcular % sobre revenue para todos los periodos involucrados
        all_periods = set()
        for p1, p2 in period_pairs:
            all_periods.add(p1)
            all_periods.add(p2)
            
        pct_revenue = self.calculate_percentage_over_revenue(
            balance, revenue_account_codes, list(all_periods)
        )
        
        result: Dict[str, Dict[str, Optional[float]]] = {}
        
        for account in balance.accounts:
            account_pp_vars: Dict[str, Optional[float]] = {}
            
            if account.code in pct_revenue:
                account_pcts = pct_revenue[account.code]
                
                for base_period, compare_period in period_pairs:
                    pair_name = f"{base_period}_vs_{compare_period}"
                    
                    pct_base = account_pcts.get(base_period)
                    pct_compare = account_pcts.get(compare_period)
                    
                    if pct_base is not None and pct_compare is not None:
                        # Variación en puntos porcentuales es una resta simple
                        # Ejemplo: 15% - 10% = +5 pp
                        pp_var = pct_compare - pct_base
                        account_pp_vars[pair_name] = pp_var
                    else:
                        account_pp_vars[pair_name] = None
            
            if account_pp_vars:
                result[account.code] = account_pp_vars
                
        return result
    
    def normalize_account_hierarchy(
        self,
        balance: BalanceSheet
    ) -> BalanceSheet:
        """
        Normaliza la jerarquía de cuentas detectando relaciones padre-hijo.
        
        Args:
            balance: BalanceSheet a normalizar
            
        Returns:
            BalanceSheet con jerarquía normalizada
        """
        # Ordenar cuentas por código
        sorted_accounts = sorted(balance.accounts, key=lambda a: a.code)
        
        for i, account in enumerate(sorted_accounts):
            # Buscar cuenta padre
            code = account.code
            
            # Intentar encontrar padre quitando dígitos significativos
            for j in range(len(code) - 1, 0, -1):
                potential_parent_code = code[:j] + '0' * (len(code) - j)
                
                # Buscar si existe esta cuenta padre
                parent = balance.get_account_by_code(potential_parent_code)
                if parent and parent.code != account.code:
                    account.parent_code = parent.code
                    break
        
        return balance
    
    def aggregate_to_periods(
        self,
        balance: BalanceSheet,
        target_periods: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Agrega valores mensuales a los periodos objetivo.
        
        Args:
            balance: BalanceSheet con datos
            target_periods: Lista de periodos objetivo (FY23, YTD24, etc.)
            
        Returns:
            Dict[account_code, Dict[period, aggregated_value]]
        """
        fy_totals = self.calculate_fiscal_year_totals(balance)
        ytd_totals = self.calculate_ytd(balance)
        
        result: Dict[str, Dict[str, float]] = {}
        
        for account in balance.accounts:
            account_values: Dict[str, float] = {}
            
            for period in target_periods:
                if period.startswith('FY'):
                    # Buscar en totales fiscales
                    if account.code in fy_totals:
                        value = fy_totals[account.code].get(period)
                        if value is not None:
                            account_values[period] = value
                
                elif period.startswith('YTD'):
                    # Buscar en YTD
                    if account.code in ytd_totals:
                        value = ytd_totals[account.code].get(period)
                        if value is not None:
                            account_values[period] = value
                
                else:
                    # Periodo mensual regular
                    value = account.get_value(period)
                    if value is not None:
                        account_values[period] = value
            
            if account_values:
                result[account.code] = account_values
        
        return result
    
    def detect_fiscal_periods(
        self,
        balance: BalanceSheet
    ) -> Dict[str, List[str]]:
        """
        Detecta los periodos fiscales disponibles.
        
        Identifica años fiscales completos (12 meses) vs incompletos.
        Solo incluye años completos en 'fiscal_years', los incompletos
        solo estarán disponibles vía YTD.
        
        Returns:
            Dict con:
            - 'fiscal_years': Años fiscales con 12 meses completos
            - 'fiscal_years_all': Todos los años fiscales (incluidos incompletos)
            - 'ytd_periods': Periodos YTD
            - 'monthly_periods': Periodos mensuales
            - 'incomplete_years': Años con menos de 12 meses
        """
        years = balance.get_fiscal_years()
        
        monthly_periods = [
            p.name for p in balance.periods 
            if p.period_type == PeriodType.MONTHLY
        ]
        
        # Contar meses por año para detectar años incompletos
        months_per_year = {}
        for period in balance.periods:
            if period.period_type == PeriodType.MONTHLY:
                year = period.year
                if year not in months_per_year:
                    months_per_year[year] = 0
                months_per_year[year] += 1
        
        # Separar años completos e incompletos
        complete_years = []
        incomplete_years = []
        
        for year in years:
            month_count = months_per_year.get(year, 0)
            if month_count >= 12:
                complete_years.append(year)
            else:
                incomplete_years.append(year)
        
        # Generar nombres de periodos
        all_fiscal_years = [f"FY{str(y)[2:]}" for y in years]
        complete_fiscal_years = [f"FY{str(y)[2:]}" for y in complete_years]
        incomplete_fy = [f"FY{str(y)[2:]}" for y in incomplete_years]
        ytd_periods = [f"YTD{str(y)[2:]}" for y in years]
        
        # Log para debugging
        if incomplete_years:
            logger.info(f"Años fiscales incompletos detectados: {incomplete_fy}")
            for year in incomplete_years:
                logger.info(f"  {year}: {months_per_year.get(year, 0)} meses")
        
        return {
            'fiscal_years': complete_fiscal_years,  # Solo años completos
            'fiscal_years_all': all_fiscal_years,    # Todos los años
            'ytd_periods': ytd_periods,
            'monthly_periods': monthly_periods,
            'years': [str(y) for y in years],
            'incomplete_years': incomplete_fy
        }
    
    def get_comparison_pairs(
        self,
        balance: BalanceSheet
    ) -> List[Tuple[str, str]]:
        """
        Genera pares de periodos para comparación.
        
        Returns:
            Lista de tuplas (periodo_anterior, periodo_actual)
        """
        years = balance.get_fiscal_years()
        pairs: List[Tuple[str, str]] = []
        
        # Comparar años fiscales consecutivos
        for i in range(len(years) - 1):
            fy_prev = f"FY{str(years[i])[2:]}"
            fy_curr = f"FY{str(years[i + 1])[2:]}"
            pairs.append((fy_prev, fy_curr))
        
        # Comparar YTD de años consecutivos
        for i in range(len(years) - 1):
            ytd_prev = f"YTD{str(years[i])[2:]}"
            ytd_curr = f"YTD{str(years[i + 1])[2:]}"
            pairs.append((ytd_prev, ytd_curr))
        
        return pairs

