"""
Modelos de datos para el sistema FDD.

Define las estructuras de datos para representar:
- Cuentas contables
- Balances
- Periodos financieros
- Estructura Q&A
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import re


class PeriodType(Enum):
    """Tipo de periodo financiero."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    YTD = "ytd"  # Year to Date


class Priority(Enum):
    """Prioridad de las preguntas del Q&A."""
    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"


class Status(Enum):
    """Estado de las preguntas del Q&A."""
    ABIERTO = "Abierto"
    EN_PROCESO = "En proceso"
    CERRADO = "Cerrado"


@dataclass
class Period:
    """
    Representa un periodo financiero.
    
    Attributes:
        name: Nombre del periodo (ej: "Jan-21", "FY23", "YTD24")
        year: Año del periodo
        month: Mes del periodo (1-12, None para periodos anuales)
        period_type: Tipo de periodo
    """
    name: str
    year: int
    month: Optional[int] = None
    period_type: PeriodType = PeriodType.MONTHLY
    
    @classmethod
    def from_string(cls, period_str: str) -> 'Period':
        """
        Crea un Period desde un string.
        
        Soporta formatos:
        - "Jan-21", "Feb-21", etc. (mensual)
        - "FY23", "FY24" (anual)
        - "YTD24", "YTD25" (year to date)
        - "Aug-25" (mensual)
        """
        period_str = period_str.strip()
        
        # Mapeo de meses en inglés
        month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        # Formato FY (Fiscal Year): FY23, FY24
        fy_match = re.match(r'^FY(\d{2})$', period_str, re.IGNORECASE)
        if fy_match:
            year = 2000 + int(fy_match.group(1))
            return cls(
                name=period_str,
                year=year,
                month=None,
                period_type=PeriodType.YEARLY
            )
        
        # Formato YTD: YTD24, YTD25
        ytd_match = re.match(r'^YTD(\d{2})$', period_str, re.IGNORECASE)
        if ytd_match:
            year = 2000 + int(ytd_match.group(1))
            return cls(
                name=period_str,
                year=year,
                month=None,
                period_type=PeriodType.YTD
            )
        
        # Formato mensual: Jan-21, Feb-22, Aug-25
        monthly_match = re.match(r'^([A-Za-z]{3})-(\d{2})$', period_str)
        if monthly_match:
            month_str = monthly_match.group(1).lower()
            year = 2000 + int(monthly_match.group(2))
            month = month_map.get(month_str)
            
            if month:
                return cls(
                    name=period_str,
                    year=year,
                    month=month,
                    period_type=PeriodType.MONTHLY
                )
        
        # Si no coincide con ningún formato, retornar con nombre original
        return cls(name=period_str, year=0, month=None, period_type=PeriodType.MONTHLY)
    
    def __lt__(self, other: 'Period') -> bool:
        """Comparación para ordenar periodos cronológicamente."""
        if self.year != other.year:
            return self.year < other.year
        if self.month is None and other.month is None:
            return False
        if self.month is None:
            return True
        if other.month is None:
            return False
        return self.month < other.month
    
    def to_datetime(self) -> Optional[datetime]:
        """Convierte a datetime si es posible."""
        if self.year and self.month:
            return datetime(self.year, self.month, 1)
        elif self.year:
            return datetime(self.year, 12, 31)
        return None


@dataclass
class Account:
    """
    Representa una cuenta contable.
    
    Attributes:
        code: Código de la cuenta (ej: "10000000", "70000000")
        description: Descripción de la cuenta
        values: Diccionario de valores por periodo {period_name: value}
        parent_code: Código de la cuenta padre (para jerarquía)
        level: Nivel en la jerarquía de cuentas
    """
    code: str
    description: str
    values: Dict[str, float] = field(default_factory=dict)
    parent_code: Optional[str] = None
    level: int = 0
    
    # Mapeo ILV (para Q&A)
    mapping_ilv_1: Optional[str] = None
    mapping_ilv_2: Optional[str] = None
    mapping_ilv_3: Optional[str] = None
    
    def get_value(self, period: Union[str, Period]) -> Optional[float]:
        """Obtiene el valor para un periodo específico."""
        period_name = period if isinstance(period, str) else period.name
        return self.values.get(period_name)
    
    def get_values_range(self, start_period: str, end_period: str) -> Dict[str, float]:
        """Obtiene valores para un rango de periodos."""
        # Esto requeriría ordenar los periodos, implementación simplificada
        return {k: v for k, v in self.values.items() 
                if k >= start_period and k <= end_period}
    
    def calculate_variation(
        self, 
        period1: str, 
        period2: str, 
        as_percentage: bool = True
    ) -> Optional[float]:
        """
        Calcula la variación entre dos periodos.
        
        Args:
            period1: Periodo base
            period2: Periodo de comparación
            as_percentage: Si retornar como porcentaje
            
        Returns:
            Variación absoluta o porcentual
        """
        val1 = self.values.get(period1)
        val2 = self.values.get(period2)
        
        if val1 is None or val2 is None:
            return None
        
        if as_percentage:
            if val1 == 0:
                return None if val2 == 0 else float('inf') if val2 > 0 else float('-inf')
            return ((val2 - val1) / abs(val1)) * 100
        
        return val2 - val1
    
    def get_account_type(self) -> str:
        """
        Determina el tipo de cuenta basado en el código.
        
        Returns:
            Tipo de cuenta: 'patrimonio', 'activo', 'pasivo', 'ingreso', 'gasto'
        """
        if not self.code:
            return 'desconocido'
        
        first_digit = self.code[0] if self.code else ''
        
        account_types = {
            '1': 'patrimonio',      # Fondos propios, Pasivo no corriente
            '2': 'activo',          # Activo no corriente
            '3': 'existencias',     # Existencias
            '4': 'terceros',        # Acreedores/Deudores
            '5': 'financiero',      # Cuentas financieras
            '6': 'gasto',           # Compras y gastos
            '7': 'ingreso',         # Ventas e ingresos
        }
        
        return account_types.get(first_digit, 'otro')
    
    def is_balance_account(self) -> bool:
        """Determina si es cuenta de balance."""
        return self.code[0] in ['1', '2', '3', '4', '5'] if self.code else False
    
    def is_income_statement_account(self) -> bool:
        """Determina si es cuenta de PyG."""
        return self.code[0] in ['6', '7'] if self.code else False
    
    def __hash__(self):
        return hash((self.code, self.description))


@dataclass
class BalanceSheet:
    """
    Representa un balance completo con todas las cuentas.
    
    Attributes:
        accounts: Lista de cuentas
        periods: Lista de periodos disponibles
        source_file: Archivo de origen
        metadata: Metadatos adicionales
    """
    accounts: List[Account] = field(default_factory=list)
    periods: List[Period] = field(default_factory=list)
    source_file: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_account_by_code(self, code: str) -> Optional[Account]:
        """Busca una cuenta por su código."""
        for account in self.accounts:
            if account.code == code:
                return account
        return None
    
    def get_accounts_by_type(self, account_type: str) -> List[Account]:
        """Obtiene todas las cuentas de un tipo específico."""
        return [acc for acc in self.accounts if acc.get_account_type() == account_type]
    
    def get_income_accounts(self) -> List[Account]:
        """Obtiene cuentas de ingresos (grupo 7)."""
        return [acc for acc in self.accounts if acc.code and acc.code.startswith('7')]
    
    def get_expense_accounts(self) -> List[Account]:
        """Obtiene cuentas de gastos (grupo 6)."""
        return [acc for acc in self.accounts if acc.code and acc.code.startswith('6')]
    
    def get_period_names(self) -> List[str]:
        """Obtiene los nombres de todos los periodos ordenados."""
        sorted_periods = sorted(self.periods)
        return [p.name for p in sorted_periods]
    
    def calculate_total(self, period: str, account_codes: List[str]) -> float:
        """Calcula el total para un conjunto de cuentas en un periodo."""
        total = 0.0
        for code in account_codes:
            account = self.get_account_by_code(code)
            if account:
                value = account.get_value(period)
                if value is not None:
                    total += value
        return total
    
    def get_fiscal_years(self) -> List[int]:
        """Obtiene los años fiscales únicos."""
        years = set()
        for period in self.periods:
            if period.year:
                years.add(period.year)
        return sorted(years)
    
    def filter_by_year(self, year: int) -> 'BalanceSheet':
        """Crea un nuevo BalanceSheet filtrado por año."""
        filtered_periods = [p for p in self.periods if p.year == year]
        period_names = {p.name for p in filtered_periods}
        
        filtered_accounts = []
        for account in self.accounts:
            filtered_values = {k: v for k, v in account.values.items() if k in period_names}
            if filtered_values:
                new_account = Account(
                    code=account.code,
                    description=account.description,
                    values=filtered_values,
                    parent_code=account.parent_code,
                    level=account.level
                )
                filtered_accounts.append(new_account)
        
        return BalanceSheet(
            accounts=filtered_accounts,
            periods=filtered_periods,
            source_file=self.source_file,
            metadata={**self.metadata, 'filtered_year': year}
        )


@dataclass
class QAItem:
    """
    Representa un item del Q&A generado.
    
    Attributes:
        mapping_ilv_1: Primer nivel de mapeo (ej: "EBITDA")
        mapping_ilv_2: Segundo nivel de mapeo (ej: "Revenue")
        mapping_ilv_3: Tercer nivel de mapeo (ej: "Gross revenue")
        description: Descripción de la cuenta
        account_code: Código de la cuenta
        values: Valores por periodo (FY23, FY24, YTD24, YTD25, etc.)
        variations: Variaciones calculadas
        percentages: Porcentajes sobre ingresos
        question: Pregunta ILV generada
        priority: Prioridad de la pregunta
        status: Estado de la pregunta
        response: Respuesta de la dirección
        follow_up: Pregunta de seguimiento
    """
    mapping_ilv_1: Optional[str] = None
    mapping_ilv_2: Optional[str] = None
    mapping_ilv_3: Optional[str] = None
    description: str = ""
    account_code: str = ""
    
    # Valores por periodo
    values: Dict[str, float] = field(default_factory=dict)
    
    # Variaciones (abs y %)
    variations: Dict[str, float] = field(default_factory=dict)
    variation_percentages: Dict[str, float] = field(default_factory=dict)
    
    # Porcentajes sobre ingresos
    percentages_over_revenue: Dict[str, float] = field(default_factory=dict)
    percentage_point_changes: Dict[str, float] = field(default_factory=dict)
    
    # Q&A
    question: Optional[str] = None
    reason: Optional[str] = None  # Razón de la pregunta
    priority: Priority = Priority.MEDIA
    status: Status = Status.ABIERTO
    response: Optional[str] = None
    follow_up: Optional[str] = None
    
    def has_significant_variation(self, threshold: float = 20.0) -> bool:
        """Determina si hay variaciones significativas."""
        for var in self.variation_percentages.values():
            if var is not None and abs(var) >= threshold:
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para exportación."""
        return {
            'Mapping ILV 1': self.mapping_ilv_1 or '',
            'Mapping ILV 2': self.mapping_ilv_2 or '',
            'Mapping ILV 3': self.mapping_ilv_3 or '',
            'Description': self.description,
            'Cuenta': self.account_code,
            **{f'{k}': v for k, v in self.values.items()},
            **{f'Var {k}': v for k, v in self.variations.items()},
            **{f'Var% {k}': v for k, v in self.variation_percentages.items()},
            **{f'% Rev {k}': v for k, v in self.percentages_over_revenue.items()},
            **{f'p.p. {k}': v for k, v in self.percentage_point_changes.items()},
            'Pregunta ILV': self.question or '',
            'Razón de la pregunta': self.reason or '',
            'Prioridad': self.priority.value,
            'Estatus': self.status.value,
            'Respuesta': self.response or '',
            'Seguimiento': self.follow_up or ''
        }


@dataclass
class QAReport:
    """
    Representa el reporte Q&A completo.
    """
    items: List[QAItem] = field(default_factory=list)
    company_name: Optional[str] = None
    report_date: datetime = field(default_factory=datetime.now)
    source_file: Optional[str] = None
    analysis_periods: List[str] = field(default_factory=list)
    
    # Totales y resúmenes
    total_revenue: Dict[str, float] = field(default_factory=dict)
    
    # Preguntas personalizadas o generales
    custom_questions: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_items_by_priority(self, priority: Priority) -> List[QAItem]:
        """Obtiene items por prioridad."""
        return [item for item in self.items if item.priority == priority]
    
    def get_open_items(self) -> List[QAItem]:
        """Obtiene items con preguntas abiertas."""
        return [item for item in self.items if item.status == Status.ABIERTO]
    
    def count_by_priority(self) -> Dict[str, int]:
        """Cuenta items por prioridad."""
        return {
            'Alta': len(self.get_items_by_priority(Priority.ALTA)),
            'Media': len(self.get_items_by_priority(Priority.MEDIA)),
            'Baja': len(self.get_items_by_priority(Priority.BAJA))
        }
