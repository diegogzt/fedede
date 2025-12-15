"""
Sistema de traducciones para reportes bilingües.

Soporta generación de reportes en:
- Español
- Inglés
- Ambos (genera 2 archivos)
"""

from typing import Dict, Literal, Optional
from enum import Enum


class Language(str, Enum):
    """Idiomas soportados."""
    SPANISH = "es"
    ENGLISH = "en"
    BOTH = "both"


# Traducciones de columnas del Excel
COLUMN_NAMES: Dict[str, Dict[str, str]] = {
    # Columnas de identificación
    "mapping_ilv_1": {
        "es": "Mapping ILV 1",
        "en": "Mapping ILV 1"
    },
    "mapping_ilv_2": {
        "es": "Mapping ILV 2",
        "en": "Mapping ILV 2"
    },
    "mapping_ilv_3": {
        "es": "Mapping ILV 3",
        "en": "Mapping ILV 3"
    },
    "description": {
        "es": "Descripción",
        "en": "Description"
    },
    "account": {
        "es": "Cuenta",
        "en": "Account"
    },
    
    # Columnas de valores
    "fy_value": {
        "es": "FY {year}",
        "en": "FY {year}"
    },
    "ytd_value": {
        "es": "YTD {year}",
        "en": "YTD {year}"
    },
    
    # Columnas de variación
    "var_fy_abs": {
        "es": "Var FY {year1}/{year2}",
        "en": "Var FY {year1}/{year2}"
    },
    "var_fy_pct": {
        "es": "Var% FY {year1}/{year2}",
        "en": "Var% FY {year1}/{year2}"
    },
    "var_ytd_abs": {
        "es": "Var YTD {year1}/{year2}",
        "en": "Var YTD {year1}/{year2}"
    },
    "var_ytd_pct": {
        "es": "Var% YTD {year1}/{year2}",
        "en": "Var% YTD {year1}/{year2}"
    },
    
    # Columnas de % sobre revenue
    "pct_rev_fy": {
        "es": "% Rev FY {year}",
        "en": "% Rev FY {year}"
    },
    "pct_rev_ytd": {
        "es": "% Rev YTD {year}",
        "en": "% Rev YTD {year}"
    },
    
    # NUEVA: Variación en puntos porcentuales
    "pp_var_fy": {
        "es": "pp Var FY {year1}/{year2}",
        "en": "pp Var FY {year1}/{year2}"
    },
    "pp_var_ytd": {
        "es": "pp Var YTD {year1}/{year2}",
        "en": "pp Var YTD {year1}/{year2}"
    },
    
    # Columnas de preguntas
    "question": {
        "es": "Pregunta ILV Silver",
        "en": "ILV Silver Question"
    },
    "reason": {
        "es": "Razón de la pregunta",
        "en": "Reason for question"
    },
    "priority": {
        "es": "Prioridad",
        "en": "Priority"
    },
    "status": {
        "es": "Estatus",
        "en": "Status"
    },
    "answer": {
        "es": "Respuesta",
        "en": "Answer"
    },

    # Columnas de respuesta/dirección (export Excel con Q&A)
    "response": {
        "es": "Respuesta Dirección",
        "en": "Management Response"
    },
    "follow_up": {
        "es": "Pregunta de seguimiento ILV",
        "en": "ILV follow-up question"
    },
    
    # Pestaña General
    "number": {
        "es": "#",
        "en": "#"
    },
    "area": {
        "es": "Área",
        "en": "Area"
    },
    "question_request": {
        "es": "Pregunta / Petición",
        "en": "Question / Request"
    },
    "request_date": {
        "es": "Fecha de solicitud",
        "en": "Request date"
    },
    "link": {
        "es": "Link",
        "en": "Link"
    }
}


# Traducciones de nombres de pestañas
SHEET_NAMES: Dict[str, Dict[str, str]] = {
    "general": {
        "es": "Preguntas generales",
        "en": "General"
    },
    "pl": {
        "es": "PT",
        "en": "PL"
    },
    "bs": {
        "es": "BL",
        "en": "BS"
    },
    "purchases": {
        "es": "Compras",
        "en": "Purchases"
    },
    "transport": {
        "es": "Transporte",
        "en": "Transport"
    }
}


# Traducciones de categorías ILV
ILV_CATEGORIES: Dict[str, Dict[str, str]] = {
    # ILV 1
    "balance": {
        "es": "Balance",
        "en": "Balance"
    },
    "pl": {
        "es": "P&L",
        "en": "P&L"
    },
    
    # ILV 2 - Balance
    "assets": {
        "es": "Activos",
        "en": "Assets"
    },
    "liabilities": {
        "es": "Pasivos",
        "en": "Liabilities"
    },
    "equity": {
        "es": "Patrimonio",
        "en": "Equity"
    },
    
    # ILV 2 - P&L
    "revenue": {
        "es": "Ingresos",
        "en": "Revenue"
    },
    "cost_of_sales": {
        "es": "Coste de ventas",
        "en": "Cost of sales"
    },
    "operating_expenses": {
        "es": "Gastos operativos",
        "en": "Operating expenses"
    },
    "financial": {
        "es": "Financiero",
        "en": "Financial"
    },
    
    # ILV 3 - Assets
    "fixed_assets": {
        "es": "Activo fijo",
        "en": "Fixed assets"
    },
    "intangible_assets": {
        "es": "Activos intangibles",
        "en": "Intangible assets"
    },
    "current_assets": {
        "es": "Activo corriente",
        "en": "Current assets"
    },
    "trade_receivables": {
        "es": "Clientes",
        "en": "Trade receivables"
    },
    "inventory": {
        "es": "Inventario",
        "en": "Inventory"
    },
    
    # ILV 3 - Liabilities
    "trade_payables": {
        "es": "Proveedores",
        "en": "Trade payables"
    },
    "financial_debt": {
        "es": "Deuda financiera",
        "en": "Financial debt"
    },
    "other_liabilities": {
        "es": "Otros pasivos",
        "en": "Other liabilities"
    },
    
    # ILV 3 - Revenue
    "product_sales": {
        "es": "Venta de productos",
        "en": "Product sales"
    },
    "service_revenue": {
        "es": "Ingresos por servicios",
        "en": "Service revenue"
    },
    "other_income": {
        "es": "Otros ingresos",
        "en": "Other income"
    },
    
    # ILV 3 - Expenses
    "personnel": {
        "es": "Personal",
        "en": "Personnel"
    },
    "transport": {
        "es": "Transporte",
        "en": "Transport"
    },
    "purchases": {
        "es": "Compras",
        "en": "Purchases"
    },
    "supplies": {
        "es": "Suministros",
        "en": "Supplies"
    },
    "depreciation": {
        "es": "Amortización",
        "en": "Depreciation"
    }
}


# Traducciones de prioridades
PRIORITIES: Dict[str, Dict[str, str]] = {
    "high": {
        "es": "Alta",
        "en": "High"
    },
    "medium": {
        "es": "Media",
        "en": "Medium"
    },
    "low": {
        "es": "Baja",
        "en": "Low"
    }
}


# Traducciones de estados
STATUSES: Dict[str, Dict[str, str]] = {
    "open": {
        "es": "Abierto",
        "en": "Open"
    },
    "closed": {
        "es": "Cerrado",
        "en": "Closed"
    },
    "pending": {
        "es": "Pendiente",
        "en": "Pending"
    }
}


# Traducciones de áreas (para pestaña General)
AREAS: Dict[str, Dict[str, str]] = {
    "pl": {
        "es": "P&L",
        "en": "P&L"
    },
    "bs": {
        "es": "BS",
        "en": "BS"
    },
    "financial_department": {
        "es": "Departamento financiero",
        "en": "Financial department"
    },
    "production": {
        "es": "Producción",
        "en": "Production"
    },
    "fx": {
        "es": "FX",
        "en": "FX"
    },
    "derivatives": {
        "es": "Derivados",
        "en": "Derivatives"
    },
    "pricing": {
        "es": "Precios y tarifas",
        "en": "Pricing and tariffs"
    }
}


# Traducciones de razones (para columna "Razón")
REASONS: Dict[str, Dict[str, str]] = {
    "high_variation": {
        "es": "Variación > {threshold}%",
        "en": "Variation > {threshold}%"
    },
    "material_amount": {
        "es": "Importe material > {amount:,.0f}€",
        "en": "Material amount > €{amount:,.0f}"
    },
    "high_variation_and_amount": {
        "es": "Variación del {var_pct:.1f}% ({var_abs:,.0f}€) supera umbrales (>{threshold_pct}%, >{threshold_amt:,.0f}€)",
        "en": "Variation of {var_pct:.1f}% (€{var_abs:,.0f}) exceeds thresholds (>{threshold_pct}%, >€{threshold_amt:,.0f})"
    },
    "new_account": {
        "es": "Nueva cuenta detectada",
        "en": "New account detected"
    },
    "account_disappeared": {
        "es": "Cuenta desaparecida",
        "en": "Account disappeared"
    },
    "negative_to_positive": {
        "es": "Cambio de signo: negativo a positivo",
        "en": "Sign change: negative to positive"
    },
    "positive_to_negative": {
        "es": "Cambio de signo: positivo a negativo",
        "en": "Sign change: positive to negative"
    },
    "high_percentage_revenue": {
        "es": "Representa {pct:.1f}% de los ingresos",
        "en": "Represents {pct:.1f}% of revenue"
    },
    "revenue_percentage_change": {
        "es": "Cambio de {pct_before:.1f}% a {pct_after:.1f}% sobre ingresos ({pp_change:+.1f} pp)",
        "en": "Change from {pct_before:.1f}% to {pct_after:.1f}% of revenue ({pp_change:+.1f} pp)"
    }
}


def get_translation(
    key: str,
    lang: Literal["es", "en"],
    category: str = "COLUMN_NAMES",
    **kwargs
) -> str:
    """
    Obtiene la traducción de una clave.
    
    Args:
        key: Clave a traducir
        lang: Idioma ("es" o "en")
        category: Categoría del diccionario (COLUMN_NAMES, SHEET_NAMES, etc.)
        **kwargs: Parámetros para formatear la cadena
        
    Returns:
        Cadena traducida y formateada
    """
    # Seleccionar diccionario según categoría
    translations = {
        "COLUMN_NAMES": COLUMN_NAMES,
        "SHEET_NAMES": SHEET_NAMES,
        "ILV_CATEGORIES": ILV_CATEGORIES,
        "PRIORITIES": PRIORITIES,
        "STATUSES": STATUSES,
        "AREAS": AREAS,
        "REASONS": REASONS
    }
    
    translation_dict = translations.get(category, COLUMN_NAMES)
    
    # Buscar traducción
    if key in translation_dict:
        text = translation_dict[key].get(lang, key)
        
        # Formatear si hay kwargs
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                return text
        return text
    
    # Si no existe traducción, retornar la clave
    return key


def get_column_name(key: str, lang: Literal["es", "en"], **kwargs) -> str:
    """Obtiene el nombre de una columna traducido."""
    return get_translation(key, lang, "COLUMN_NAMES", **kwargs)


def get_sheet_name(key: str, lang: Literal["es", "en"]) -> str:
    """Obtiene el nombre de una pestaña traducido."""
    return get_translation(key, lang, "SHEET_NAMES")


def get_priority(priority: str, lang: Literal["es", "en"]) -> str:
    """Obtiene la prioridad traducida."""
    return get_translation(priority.lower(), lang, "PRIORITIES")


def get_status(status: str, lang: Literal["es", "en"]) -> str:
    """Obtiene el estado traducido."""
    return get_translation(status.lower(), lang, "STATUSES")


def get_area(area: str, lang: Literal["es", "en"]) -> str:
    """Obtiene el área traducida."""
    return get_translation(area.lower(), lang, "AREAS")


def get_reason(reason_key: str, lang: Literal["es", "en"], **kwargs) -> str:
    """Obtiene la razón traducida y formateada."""
    return get_translation(reason_key, lang, "REASONS", **kwargs)


def get_output_filename(base_name: str, lang: Language) -> str:
    """
    Genera el nombre del archivo de salida según el idioma.
    
    Args:
        base_name: Nombre base del archivo (sin extensión)
        lang: Idioma
        
    Returns:
        Nombre del archivo con sufijo de idioma
    """
    if lang == Language.SPANISH:
        return f"{base_name}_ES.xlsx"
    elif lang == Language.ENGLISH:
        return f"{base_name}_EN.xlsx"
    else:
        # Para Language.BOTH, retornar lista
        return f"{base_name}_{{lang}}.xlsx"


class TranslationManager:
    """Gestor de traducciones."""
    
    def __init__(self, language: Language = Language.SPANISH):
        self.language = language
        self.lang_code = "en" if language == Language.ENGLISH else "es"
    
    def get_columns(self) -> Dict[str, str]:
        """Obtiene diccionario de columnas traducidas."""
        # Mapeo manual para simplificar el uso en el código
        # Nota: Para las columnas con variables ({year}), devolvemos el prefijo
        # Esto asume que el código que lo usa concatenará el resto
        
        cols = {
            'mapping_ilv_1': get_column_name('mapping_ilv_1', self.lang_code),
            'mapping_ilv_2': get_column_name('mapping_ilv_2', self.lang_code),
            'mapping_ilv_3': get_column_name('mapping_ilv_3', self.lang_code),
            'description': get_column_name('description', self.lang_code),
            'account': get_column_name('account', self.lang_code),
            
            # Para estas, devolvemos el texto base sin los placeholders
            # Ejemplo: "Var FY {year1}/{year2}" -> "Var FY"
            # Esto requiere que el código cliente construya el string correctamente
            'var_abs': "Var" if self.lang_code == "es" else "Var", # Simplificado
            'var_pct': "Var%" if self.lang_code == "es" else "Var%",
            'pct_revenue': "% Rev" if self.lang_code == "es" else "% Rev",
            'var_pp': "p.p." if self.lang_code == "es" else "p.p.",
            
            'question': get_column_name('question', self.lang_code),
            'reason': get_column_name('reason', self.lang_code),
            'priority': get_column_name('priority', self.lang_code),
            'status': get_column_name('status', self.lang_code),
            'response': get_column_name('response', self.lang_code),
            'follow_up': get_column_name('follow_up', self.lang_code)
        }
        return cols
    
    def get_sheet_names(self) -> Dict[str, str]:
        """Obtiene diccionario de nombres de pestañas."""
        return {
            'general': get_sheet_name('general', self.lang_code),
            'pl': get_sheet_name('pl', self.lang_code),
            'bs': get_sheet_name('bs', self.lang_code)
        }
