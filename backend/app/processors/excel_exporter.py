"""
Exportador de reportes Q&A a Excel con formato y múltiples pestañas.

Este módulo genera archivos Excel (.xlsx) con el formato requerido:
- Múltiples pestañas (General, PL, BS, Compras, Transporte, etc.)
- Formato visual profesional con colores y estilos
- Agrupación jerárquica de cuentas
- Encabezados y títulos personalizados
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

try:
    from openpyxl import Workbook
    from openpyxl.styles import (
        Font, Fill, PatternFill, Border, Side, Alignment,
        NamedStyle, Color
    )
    from openpyxl.utils import get_column_letter
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.worksheet.worksheet import Worksheet
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

from app.processors.models import QAReport, QAItem, Priority, Status
from app.config.translations import TranslationManager, Language

logger = logging.getLogger(__name__)


# Colores para el formato
COLORS = {
    'header_bg': 'B8CCE4',      # Azul claro para encabezados
    'header_bg_alt': 'FDE9D9',  # Naranja claro alternativo
    'header_bg_yellow': 'FFFF00',  # Amarillo para columnas importantes
    'total_row_bg': '92D050',   # Verde para filas de totales
    'group_row_bg': 'DCE6F1',   # Azul muy claro para grupos
    'high_priority': 'FF6B6B', # Rojo para alta prioridad
    'medium_priority': 'FFE066', # Amarillo para media prioridad
    'low_priority': '51CF66',   # Verde para baja prioridad
    'status_open': 'FF9999',    # Rosa para estado abierto
    'revenue_row': '4BACC6',    # Azul teal para ingresos
    'white': 'FFFFFF',
}


class ExcelExporter:
    """
    Exportador de reportes Q&A a formato Excel con múltiples pestañas.
    
    Características:
    - Pestaña General con resumen de áreas
    - Pestañas por tipo (PL, BS, Compras, etc.)
    - Formato visual profesional
    - Agrupación jerárquica
    - Totales y subtotales
    """
    
    def __init__(self, project_name: str = "Project"):
        """
        Inicializa el exportador.
        
        Args:
            project_name: Nombre del proyecto para el título
        """
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl es necesario. Instalar con: pip install openpyxl")
        
        self.project_name = project_name
        self._setup_styles()
    
    def _setup_styles(self):
        """Configura los estilos de formato."""
        # Bordes
        self.thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Fuentes
        self.title_font = Font(name='Calibri', size=24, bold=True, color='1F4E79')
        self.subtitle_font = Font(name='Calibri', size=14, bold=True)
        self.header_font = Font(name='Calibri', size=10, bold=True, color='000000')
        self.normal_font = Font(name='Calibri', size=10)
        self.bold_font = Font(name='Calibri', size=10, bold=True)
        
        # Alineación
        self.center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
        self.left_align = Alignment(horizontal='left', vertical='center', wrap_text=True)
        self.right_align = Alignment(horizontal='right', vertical='center')
        
        # Fills
        self.header_fill = PatternFill(start_color=COLORS['header_bg'], 
                                        end_color=COLORS['header_bg'], 
                                        fill_type='solid')
        self.header_fill_alt = PatternFill(start_color=COLORS['header_bg_alt'],
                                            end_color=COLORS['header_bg_alt'],
                                            fill_type='solid')
        self.total_fill = PatternFill(start_color=COLORS['total_row_bg'],
                                       end_color=COLORS['total_row_bg'],
                                       fill_type='solid')
        self.revenue_fill = PatternFill(start_color=COLORS['revenue_row'],
                                         end_color=COLORS['revenue_row'],
                                         fill_type='solid')
    
    def export(
        self,
        report: QAReport,
        output_path: Path,
        include_sheets: Optional[List[str]] = None,
        language: Language = Language.SPANISH
    ) -> Path:
        """
        Exporta el reporte a Excel con múltiples pestañas.
        
        Args:
            report: QAReport a exportar
            output_path: Ruta del archivo de salida
            include_sheets: Lista de pestañas a incluir (None = todas)
            language: Idioma para las columnas y pestañas
            
        Returns:
            Ruta del archivo creado
        """
        output_path = Path(output_path)
        if not output_path.suffix == '.xlsx':
            output_path = output_path.with_suffix('.xlsx')
        
        # Crear directorio si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Crear workbook
        wb = Workbook()
        
        # Inicializar traducciones
        tm = TranslationManager(language)
        sheet_names = tm.get_sheet_names()
        
        # Separar items por tipo/pestaña
        sheets_data = self._categorize_items(report)
        
        # Crear pestaña General
        self._create_general_sheet(wb, report, sheets_data, language)
        
        # Mapeo de nombres internos a nombres traducidos
        internal_to_translated = {
            'PL': sheet_names['pl'],
            'BS': sheet_names['bs'],
            'Compras': 'Compras',
            'Transporte': 'Transporte'
        }
        
        # Crear pestañas por categoría
        default_sheets = ['PL', 'BS']
        sheets_to_create = include_sheets or default_sheets
        
        for internal_name in sheets_to_create:
            if internal_name in sheets_data and sheets_data[internal_name]:
                translated_name = internal_to_translated.get(internal_name, internal_name)
                self._create_detail_sheet(wb, translated_name, sheets_data[internal_name], report, language)
        
        # Guardar archivo
        wb.save(output_path)
        logger.info(f"Excel exportado: {output_path}")
        
        return output_path
    
    def _categorize_items(self, report: QAReport) -> Dict[str, List[QAItem]]:
        """
        Categoriza items por tipo de pestaña.
        
        Returns:
            Dict con listas de items por categoría
        """
        categories = {
            'General': [],  # Resumen de áreas
            'PL': [],       # P&L - Profit and Loss
            'BS': [],       # Balance Sheet
            'Compras': [],  # Detalle de compras (códigos 60)
            'Transporte': [],  # Detalle de transporte
        }
        
        for item in report.items:
            ilv1 = item.mapping_ilv_1 or ''
            ilv2 = item.mapping_ilv_2 or ''
            ilv3 = item.mapping_ilv_3 or ''
            code = item.account_code or ''
            desc = (item.description or '').upper()
            
            # Detectar si es cuenta de Transporte
            is_transport = (
                'TRANSPORTE' in desc or 
                code.startswith('6012') or 
                code.startswith('624') or
                code.startswith('6241') or
                code.startswith('6242')
            )
            
            # Detectar si es cuenta de Compras
            is_purchase = (
                code.startswith('60') or 
                ilv2 == 'COGS' or
                ilv3 == 'Purchases' or
                'COMPRA' in desc or
                'CRIBA' in desc
            )
            
            # Clasificar por tipo
            if ilv1 == 'EBITDA' or code.startswith('6') or code.startswith('7'):
                categories['PL'].append(item)
                
                if is_purchase:
                    categories['Compras'].append(item)
                    
                if is_transport:
                    categories['Transporte'].append(item)
                        
            elif ilv1 == 'Balance' or code.startswith(('1', '2', '3', '4', '5')):
                categories['BS'].append(item)
                
                # También verificar transporte en proveedores (40, 41)
                if is_transport and (code.startswith('40') or code.startswith('41')):
                    categories['Transporte'].append(item)
            else:
                # Clasificar por código
                if code.startswith('6') or code.startswith('7'):
                    categories['PL'].append(item)
                    if is_purchase:
                        categories['Compras'].append(item)
                    if is_transport:
                        categories['Transporte'].append(item)
                elif code.startswith(('1', '2', '3', '4', '5')):
                    categories['BS'].append(item)
        
        return categories
    
    def _create_general_sheet(
        self,
        wb: Workbook,
        report: QAReport,
        sheets_data: Dict[str, List[QAItem]],
        language: Language = Language.SPANISH
    ):
        """Crea la pestaña General con resumen."""
        tm = TranslationManager(language)
        sheet_names = tm.get_sheet_names()
        
        # Usar la primera hoja (default)
        ws = wb.active
        ws.title = sheet_names['general']
        
        current_row = 1
        
        # Título
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=8)
        title_cell = ws.cell(row=1, column=1, value="ilv silver")
        title_cell.font = self.title_font
        current_row += 2
        
        # Nombre del proyecto
        ws.cell(row=current_row, column=1, value=self.project_name)
        ws.cell(row=current_row, column=1).font = self.subtitle_font
        current_row += 2
        
        # Subtítulo
        subtitle = "Listado de preguntas y respuestas (Q&A)" if language == Language.SPANISH else "Questions & Answers List (Q&A)"
        ws.cell(row=current_row, column=1, value=subtitle)
        ws.cell(row=current_row, column=1).font = self.subtitle_font
        current_row += 2
        
        # Encabezados de tabla resumen
        if language == Language.SPANISH:
            headers = ['#', 'Área', 'Pregunta / Petición', 'Prioridad', 
                       'Fecha de solicitud', 'Link', 'Estatus']
        else:
            headers = ['#', 'Area', 'Question / Request', 'Priority', 
                       'Request Date', 'Link', 'Status']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.thin_border
            cell.alignment = self.center_align
        
        current_row += 1
        
        # Datos del resumen por área
        summary_items = self._generate_summary_items(report, sheets_data, language)
        
        for idx, item in enumerate(summary_items, 1):
            ws.cell(row=current_row, column=1, value=idx).border = self.thin_border
            ws.cell(row=current_row, column=2, value=item['area']).border = self.thin_border
            
            question_cell = ws.cell(row=current_row, column=3, value=item['question'])
            question_cell.border = self.thin_border
            question_cell.alignment = self.left_align
            
            priority_cell = ws.cell(row=current_row, column=4, value=item['priority'])
            priority_cell.border = self.thin_border
            priority_cell.alignment = self.center_align
            self._apply_priority_color(priority_cell, item['priority'])
            
            ws.cell(row=current_row, column=5, value=item['date']).border = self.thin_border
            
            link_cell = ws.cell(row=current_row, column=6, value=item['link'])
            link_cell.border = self.thin_border
            if item['link'] and item['link'] != 'n.a.':
                link_cell.font = Font(color='0000FF', underline='single')
            
            status_cell = ws.cell(row=current_row, column=7, value=item['status'])
            status_cell.border = self.thin_border
            status_cell.alignment = self.center_align
            if item['status'] in ['Abierto', 'Open']:
                status_cell.fill = PatternFill(start_color=COLORS['status_open'],
                                               end_color=COLORS['status_open'],
                                               fill_type='solid')
            
            current_row += 1
        
        # Ajustar anchos de columna
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 80
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 10
        ws.column_dimensions['G'].width = 12
    
    def _generate_summary_items(
        self,
        report: QAReport,
        sheets_data: Dict[str, List[QAItem]],
        language: Language = Language.SPANISH
    ) -> List[Dict[str, Any]]:
        """Genera los items de resumen para la pestaña General."""
        today = datetime.now().strftime("%d/%m/%Y")
        tm = TranslationManager(language)
        sheet_names = tm.get_sheet_names()
        
        summary_items = []
        
        if language == Language.SPANISH:
            pl_text = 'Hemos realizado una serie de preguntas relacionadas principalmente con variaciones y naturaleza de cuentas registradas en el SyS para la cuenta de perdidas y ganancias ({count} items). Por favor referirse a la pestaña "{sheet}" para ver y responder estas preguntas.'
            bs_text = 'Hemos realizado una serie de preguntas relacionadas principalmente con variaciones y naturaleza de cuentas registradas en el SyS para el balance ({count} items). Por favor referirse a la pestaña "{sheet}" para ver y responder estas preguntas.'
            fin_dept_text = '(i) Por favor comentar de manera general la estructura financiera y contable actual de la Compañía - cómo se compone el área, cuántas personas forman el equipo, qué posición tienen, etc. (incluyendo empleados internos y externos).\n(ii) Describir los sistemas contables y operativos (ERP) que usa la Compañía para el análisis de la información y para los diferentes módulos contables como existencias, clientes, proveedores, etc.'
            prod_text = '(i) Comentar de manera general respecto a la capacidad de producción utilizada (en %) de la planta de reciclaje.\n(ii) La Dirección considera que es necesario incrementar la capacidad de producción para cumplir con las ventas esperadas a futuro?\n(iii) Hay planes de crecimiento vigentes para aumentar la capacidad de producción?'
            status_open = 'Abierto'
            priority_high = 'Alta'
            priority_medium = 'Media'
        else:
            pl_text = 'We have raised a series of questions mainly related to variations and nature of accounts recorded in the Trial Balance for the Profit & Loss account ({count} items). Please refer to the "{sheet}" tab to view and answer these questions.'
            bs_text = 'We have raised a series of questions mainly related to variations and nature of accounts recorded in the Trial Balance for the Balance Sheet ({count} items). Please refer to the "{sheet}" tab to view and answer these questions.'
            fin_dept_text = '(i) Please comment generally on the current financial and accounting structure of the Company - how the area is composed, how many people make up the team, what position they hold, etc. (including internal and external employees).\n(ii) Describe the accounting and operating systems (ERP) used by the Company for information analysis and for different accounting modules such as inventory, customers, suppliers, etc.'
            prod_text = '(i) Comment generally regarding the used production capacity (in %) of the recycling plant.\n(ii) Does Management consider it necessary to increase production capacity to meet expected future sales?\n(iii) Are there current growth plans to increase production capacity?'
            status_open = 'Open'
            priority_high = 'High'
            priority_medium = 'Medium'
        
        # Item 2: P&L
        pl_count = len(sheets_data.get('PL', []))
        summary_items.append({
            'area': 'P&L',
            'question': pl_text.format(count=pl_count, sheet=sheet_names['pl']),
            'priority': priority_high,
            'date': today,
            'link': sheet_names['pl'],
            'status': status_open
        })
        
        # Item 3: BS
        bs_count = len(sheets_data.get('BS', []))
        summary_items.append({
            'area': 'BS',
            'question': bs_text.format(count=bs_count, sheet=sheet_names['bs']),
            'priority': priority_high,
            'date': today,
            'link': sheet_names['bs'],
            'status': status_open
        })
        
        # Item 4: Departamento financiero
        summary_items.append({
            'area': 'Financial Dept' if language == Language.ENGLISH else 'Departamento financiero',
            'question': fin_dept_text,
            'priority': priority_medium,
            'date': today,
            'link': 'n.a.',
            'status': status_open
        })
        
        # Item 5: Producción
        summary_items.append({
            'area': 'Production' if language == Language.ENGLISH else 'Producción',
            'question': prod_text,
            'priority': priority_medium,
            'date': today,
            'link': 'n.a.',
            'status': status_open
        })
        
        # Item 6: FX
        summary_items.append({
            'area': 'FX',
            'question': '(i) La Compañía exporta/importa materiales a algún cliente o de algún proveedor? '
                        'es todo mercado local?\n'
                        '(ii) Comentar de manera general las operaciones en moneda extranjera que '
                        'realiza la Compañía (si aplica)\n'
                        '(iii) Comentar respecto al tratamiento contable y registro de las operaciones '
                        'con moneda extranjera (si aplica)',
            'priority': priority_medium,
            'date': today,
            'link': 'n.a.',
            'status': status_open
        })
        
        # Item 7: Derivados
        summary_items.append({
            'area': 'Derivados', # TODO: Traducir
            'question': 'La Compañía tiene alguna cobertura o hace uso de algún derivado contra '
                        'variación de energía, moneda y/o precios de los metales (materia prima)?',
            'priority': priority_medium,
            'date': today,
            'link': 'n.a.',
            'status': status_open
        })
        
        # Item 8: Precios y tarifas
        summary_items.append({
            'area': 'Precios y tarifas', # TODO: Traducir
            'question': '(i) Comentar de manera general cómo es el proceso de actualización de '
                        'tarifas y cada cuánto se actualizan.',
            'priority': priority_medium,
            'date': today,
            'link': 'n.a.',
            'status': status_open
        })
        
        return summary_items
    
    def _create_detail_sheet(
        self,
        wb: Workbook,
        sheet_name: str,
        items: List[QAItem],
        report: QAReport,
        language: Language = Language.SPANISH
    ):
        """Crea una pestaña de detalle (PL, BS, etc.)."""
        ws = wb.create_sheet(title=sheet_name)
        tm = TranslationManager(language)
        cols = tm.get_columns()
        
        # Definir columnas
        # Encabezados fijos
        headers = [
            cols['mapping_ilv_1'], cols['mapping_ilv_2'], cols['mapping_ilv_3'],
            cols['description'], cols['account']
        ]
        
        # Periodos
        periods = report.analysis_periods
        headers.extend(periods)
        
        # Variaciones absolutas
        var_keys = []
        if items:
            var_keys = list(items[0].variations.keys())
            for key in var_keys:
                parts = key.split('_vs_')
                if len(parts) == 2:
                    headers.append(f"{cols['var_abs']} {parts[0]}/{parts[1]}")
        
        # Variaciones porcentuales
        var_pct_keys = []
        if items:
            var_pct_keys = list(items[0].variation_percentages.keys())
            for key in var_pct_keys:
                parts = key.split('_vs_')
                if len(parts) == 2:
                    headers.append(f"{cols['var_pct']} {parts[0]}/{parts[1]}")
        
        # % sobre ingresos
        pct_rev_keys = []
        if items:
            pct_rev_keys = list(items[0].percentages_over_revenue.keys())
            for key in pct_rev_keys:
                headers.append(f"{cols['pct_revenue']} {key}")
        
        # Puntos porcentuales
        pp_keys = []
        if items:
            pp_keys = list(items[0].percentage_point_changes.keys())
            for key in pp_keys:
                parts = key.split('_vs_')
                if len(parts) == 2:
                    headers.append(f"{cols['var_pp']} {parts[0]}/{parts[1]}")
        
        # Columnas Q&A
        qa_headers = [
            cols['question'], cols['reason'], cols['priority'], 
            cols['status'], cols['response'], cols['follow_up']
        ]
        headers.extend(qa_headers)
        
        # Escribir encabezados
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.border = self.thin_border
            cell.alignment = self.center_align
            
            # Color especial para columnas de Q&A
            if header in qa_headers:
                cell.fill = self.header_fill_alt
        
        # Escribir datos
        current_row = 2
        
        for item in items:
            col_idx = 1
            
            # Mapeo ILV y cuenta
            ws.cell(row=current_row, column=col_idx, value=item.mapping_ilv_1).border = self.thin_border; col_idx += 1
            ws.cell(row=current_row, column=col_idx, value=item.mapping_ilv_2).border = self.thin_border; col_idx += 1
            ws.cell(row=current_row, column=col_idx, value=item.mapping_ilv_3).border = self.thin_border; col_idx += 1
            ws.cell(row=current_row, column=col_idx, value=item.description).border = self.thin_border; col_idx += 1
            ws.cell(row=current_row, column=col_idx, value=item.account_code).border = self.thin_border; col_idx += 1
            
            # Periodos
            for period in periods:
                val = item.values.get(period)
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                cell.border = self.thin_border
                cell.number_format = '#,##0.00'
                col_idx += 1
            
            # Variaciones
            for key in var_keys:
                val = item.variations.get(key)
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                cell.border = self.thin_border
                cell.number_format = '#,##0.00'
                col_idx += 1
                
            # Variaciones %
            for key in var_pct_keys:
                val = item.variation_percentages.get(key)
                cell = ws.cell(row=current_row, column=col_idx, value=val/100 if val is not None else None)
                cell.border = self.thin_border
                cell.number_format = '0.0%'
                col_idx += 1
            
            # % Revenue
            for key in pct_rev_keys:
                val = item.percentages_over_revenue.get(key)
                cell = ws.cell(row=current_row, column=col_idx, value=val/100 if val is not None else None)
                cell.border = self.thin_border
                cell.number_format = '0.0%'
                col_idx += 1
                
            # Puntos porcentuales
            for key in pp_keys:
                val = item.percentage_point_changes.get(key)
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                cell.border = self.thin_border
                cell.number_format = '0.00'
                col_idx += 1
            
            # Q&A
            # Pregunta
            cell = ws.cell(row=current_row, column=col_idx, value=item.question)
            cell.border = self.thin_border
            cell.alignment = self.left_align
            col_idx += 1
            
            # Razón
            cell = ws.cell(row=current_row, column=col_idx, value=item.reason)
            cell.border = self.thin_border
            cell.alignment = self.left_align
            col_idx += 1
            
            # Prioridad
            cell = ws.cell(row=current_row, column=col_idx, value=item.priority.value)
            cell.border = self.thin_border
            cell.alignment = self.center_align
            self._apply_priority_color(cell, item.priority.value)
            col_idx += 1
            
            # Status
            cell = ws.cell(row=current_row, column=col_idx, value=item.status.value)
            cell.border = self.thin_border
            cell.alignment = self.center_align
            col_idx += 1
            
            # Respuesta
            cell = ws.cell(row=current_row, column=col_idx, value=item.response)
            cell.border = self.thin_border
            cell.alignment = self.left_align
            col_idx += 1
            
            # Follow up
            cell = ws.cell(row=current_row, column=col_idx, value=item.follow_up)
            cell.border = self.thin_border
            cell.alignment = self.left_align
            col_idx += 1
            
            current_row += 1
            
        # Ajustar anchos
        for i, col in enumerate(headers):
            ws.column_dimensions[get_column_letter(i+1)].width = 15
        
        # Anchos específicos
        ws.column_dimensions['D'].width = 40 # Description
        # Calcular índices de columnas Q&A
        qa_start_idx = len(headers) - 6
        ws.column_dimensions[get_column_letter(qa_start_idx + 1)].width = 50 # Question
        ws.column_dimensions[get_column_letter(qa_start_idx + 2)].width = 30 # Reason
        ws.column_dimensions[get_column_letter(qa_start_idx + 5)].width = 40 # Response
        
        # Freeze panes
        ws.freeze_panes = 'E2'
    

    
    def _group_items_by_category(
        self,
        items: List[QAItem]
    ) -> Dict[str, List[QAItem]]:
        """Agrupa items por categoría (ILV3)."""
        groups = {}
        
        for item in items:
            category = item.mapping_ilv_3 or item.mapping_ilv_2 or 'Otros'
            
            if category not in groups:
                groups[category] = []
            groups[category].append(item)
        
        return groups
    
    def _item_to_row(
        self,
        item: QAItem,
        fy_periods: List[str],
        ytd_periods: List[str]
    ) -> List[Any]:
        """Convierte un QAItem a una fila de datos."""
        import math
        
        def is_valid_number(val):
            """Verifica si un valor es un número válido (no None, no NaN)."""
            if val is None:
                return False
            if isinstance(val, float) and math.isnan(val):
                return False
            return True
        
        row = [
            '',  # ILV3 (ya está en el grupo)
            item.description,
            item.account_code,
        ]
        
        # Valores por periodo
        for period in fy_periods[-2:] + ytd_periods[-2:]:
            value = item.values.get(period)
            row.append(self._format_number(value) if is_valid_number(value) else '-')
        
        # Variaciones absolutas y porcentuales
        if len(fy_periods) >= 2:
            key = f"{fy_periods[-2]}_vs_{fy_periods[-1]}"
            var_abs = item.variations.get(key)
            var_pct = item.variation_percentages.get(key)
            row.append(self._format_number(var_abs) if is_valid_number(var_abs) else '-')
            row.append(self._format_percent(var_pct) if is_valid_number(var_pct) else '-')
        
        if len(ytd_periods) >= 2:
            key = f"{ytd_periods[-2]}_vs_{ytd_periods[-1]}"
            var_abs = item.variations.get(key)
            var_pct = item.variation_percentages.get(key)
            row.append(self._format_number(var_abs) if is_valid_number(var_abs) else '-')
            row.append(self._format_percent(var_pct) if is_valid_number(var_pct) else '-')
        
        # % sobre ingresos
        for period in fy_periods[-2:] + ytd_periods[-2:]:
            pct = item.percentages_over_revenue.get(period)
            row.append(self._format_percent(pct) if is_valid_number(pct) else '-')
        
        # Q&A (solo en algunas filas, no repetir)
        row.extend(['', '', '', ''])  # Pregunta, Prioridad, Estatus, Respuesta
        
        return row
    
    def _calculate_category_total(
        self,
        items: List[QAItem],
        fy_periods: List[str],
        ytd_periods: List[str]
    ) -> List[Any]:
        """Calcula el total de una categoría."""
        import math
        
        row = ['', '', '']  # ILV columns vacías
        
        # Suma por periodo (ignorando NaN)
        for period in fy_periods[-2:] + ytd_periods[-2:]:
            total = 0.0
            for item in items:
                val = item.values.get(period, 0)
                if val is not None and not (isinstance(val, float) and math.isnan(val)):
                    total += val
            row.append(self._format_number(total) if total != 0 else '-')
        
        # Variaciones y % (simplificado - podría calcular de nuevo)
        row.extend(['-', '-'])  # FY variation
        row.extend(['-', '-'])  # YTD variation
        
        # % sobre ingresos
        for _ in range(len(fy_periods[-2:]) + len(ytd_periods[-2:])):
            row.append('-')
        
        return row
    
    def _format_number(self, value: Optional[float]) -> str:
        """Formatea un número para visualización."""
        import math
        
        if value is None:
            return '-'
        
        # Manejar NaN
        if isinstance(value, float) and math.isnan(value):
            return '-'
        
        # Formato según magnitud
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        elif abs(value) >= 1_000:
            return f"{value / 1_000:.0f}K" if abs(value) >= 10_000 else f"{value / 1_000:.1f}K"
        else:
            return f"{value:.0f}"
    
    def _format_percent(self, value: Optional[float]) -> str:
        """Formatea un porcentaje para visualización."""
        import math
        
        if value is None:
            return '-'
        
        # Manejar NaN
        if isinstance(value, float) and math.isnan(value):
            return '-'
        
        if value < 0:
            return f"({abs(value):.1f}%)"
        else:
            return f"{value:.1f}%"
    
    def _apply_priority_color(self, cell, priority: str):
        """Aplica color según prioridad."""
        colors = {
            'Alta': COLORS['high_priority'],
            'Media': COLORS['medium_priority'],
            'Baja': COLORS['low_priority'],
        }
        color = colors.get(priority)
        if color:
            cell.fill = PatternFill(start_color=color, end_color=color, fill_type='solid')
    
    def _adjust_column_widths(self, ws: Worksheet, headers: List[str]):
        """Ajusta los anchos de columna automáticamente."""
        widths = {
            'Mapping ILV 3': 15,
            'Description': 35,
            'Cuenta': 12,
            'Pregunta ILV Silver': 50,
            'Prioridad': 10,
            'Estatus': 10,
            'Respuesta': 40,
        }
        
        for col, header in enumerate(headers, 1):
            letter = get_column_letter(col)
            
            if header in widths:
                ws.column_dimensions[letter].width = widths[header]
            elif header.startswith('FY') or header.startswith('YTD'):
                ws.column_dimensions[letter].width = 10
            elif header.startswith('Var'):
                ws.column_dimensions[letter].width = 12
            elif header.startswith('%'):
                ws.column_dimensions[letter].width = 10
            else:
                ws.column_dimensions[letter].width = 12

