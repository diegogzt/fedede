"""
Motor de reglas para generación automática de preguntas de auditoría financiera.
Basado en el Plan General Contable (PGC) español.

Este módulo contiene un diccionario completo de preguntas contextuales que se
generan automáticamente según:
- El código de cuenta (prefijo PGC)
- La dirección de la variación (aumento/disminución)
- La magnitud de la variación (porcentaje y valor absoluto)
- Patrones en la descripción de la cuenta
"""

from typing import Dict, Any, Optional, List, Tuple
import re
from dataclasses import dataclass

from app.config.settings import get_settings


@dataclass
class QuestionRule:
    """Regla para generación de preguntas."""
    patterns: List[str]  # Patrones de texto a buscar en descripción
    code_prefixes: List[str]  # Prefijos de código de cuenta
    question_increase: str  # Pregunta para aumentos
    question_decrease: str  # Pregunta para disminuciones
    priority: int = 1  # Prioridad de la regla (mayor = más específica)
    min_variation_percent: float = 10.0  # Variación mínima para generar pregunta
    min_variation_absolute: float = 1000.0  # Variación absoluta mínima


class RuleEngine:
    """
    Motor de reglas para generación de preguntas de auditoría.
    
    Categoriza las cuentas según el Plan General Contable:
    - Grupo 1 (10-19): Financiación básica
    - Grupo 2 (20-29): Activo no corriente (inmovilizado)
    - Grupo 3 (30-39): Existencias
    - Grupo 4 (40-49): Acreedores y deudores
    - Grupo 5 (50-57): Cuentas financieras
    - Grupo 6 (60-69): Compras y gastos
    - Grupo 7 (70-79): Ventas e ingresos
    """
    
    def __init__(self):
        settings = get_settings()
        self.variation_threshold_percent = float(settings.report.percentage_threshold)
        self.variation_threshold_absolute = float(settings.report.materiality_threshold)
        
        # Patrones de exclusión (no generar preguntas)
        self.exclusion_patterns = [
            r"alquiler.*veh[ií]culo",
            r"renting.*coche",
            r"material.*oficina",
            r"papeler[ií]a",
        ]
        
        # Diccionario completo de reglas por categoría
        self.rules = self._build_rules_dictionary()
        
    def _build_rules_dictionary(self) -> List[QuestionRule]:
        """Construye el diccionario completo de reglas de preguntas."""
        rules = []
        
        # ═══════════════════════════════════════════════════════════════════
        # GRUPO 1: FINANCIACIÓN BÁSICA (10-19)
        # ═══════════════════════════════════════════════════════════════════
        
        # Capital social (100-109)
        rules.append(QuestionRule(
            patterns=["capital", "capital social", "acciones"],
            code_prefixes=["100", "101", "102", "103", "104", "105", "106", "107", "108", "109"],
            question_increase="¿Se ha realizado alguna ampliación de capital durante el período? ¿Cuáles fueron los términos y condiciones?",
            question_decrease="¿Ha habido alguna reducción de capital? ¿Cuál fue el motivo (pérdidas, devolución a accionistas)?",
            priority=3
        ))
        
        # Reservas (110-119)
        rules.append(QuestionRule(
            patterns=["reserva", "reservas", "beneficios retenidos"],
            code_prefixes=["110", "111", "112", "113", "114", "115", "116", "117", "118", "119"],
            question_increase="¿Se ha dotado reservas con cargo a resultados? ¿Cuál es el origen del incremento?",
            question_decrease="¿Se han utilizado reservas para compensar pérdidas o para otros fines? Por favor detalle.",
            priority=2
        ))
        
        # Resultados de ejercicios anteriores (120-129)
        rules.append(QuestionRule(
            patterns=["resultado", "ejercicios anteriores", "pérdidas acumuladas", "remanente"],
            code_prefixes=["120", "121", "122", "129"],
            question_increase="¿Corresponde a beneficios no distribuidos de ejercicios anteriores? ¿Hay plan de distribución?",
            question_decrease="¿Las pérdidas acumuladas provienen de ejercicios específicos? ¿Existe plan de saneamiento?",
            priority=2
        ))
        
        # Subvenciones (130-139)
        rules.append(QuestionRule(
            patterns=["subvenci", "donacion", "ayuda", "subvención"],
            code_prefixes=["130", "131", "132", "133", "134", "135", "136", "137"],
            question_increase="¿Se han recibido nuevas subvenciones? ¿De qué organismo y para qué finalidad?",
            question_decrease="¿Se ha imputado subvención a resultados? ¿Cumple con los requisitos de la concesión?",
            priority=2
        ))
        
        # Provisiones largo plazo (140-149)
        rules.append(QuestionRule(
            patterns=["provisión", "provision", "obligacion", "contingencia"],
            code_prefixes=["140", "141", "142", "143", "145", "146", "147"],
            question_increase="¿Se han dotado nuevas provisiones a largo plazo? ¿Cuál es el riesgo u obligación subyacente?",
            question_decrease="¿Se ha revertido o aplicado la provisión? ¿Cuál fue el desenlace del riesgo provisionado?",
            priority=2
        ))
        
        # Deudas largo plazo (170-179)
        rules.append(QuestionRule(
            patterns=["deuda", "préstamo", "prestamo", "obligacion", "financiaci"],
            code_prefixes=["170", "171", "172", "173", "174", "175", "176", "177", "178", "179"],
            question_increase="¿Se ha obtenido nueva financiación a largo plazo? ¿Cuáles son las condiciones (tipo, plazo, garantías)?",
            question_decrease="¿Se han amortizado deudas a largo plazo? ¿Con qué fondos se ha realizado el pago?",
            priority=2
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # GRUPO 2: ACTIVO NO CORRIENTE - INMOVILIZADO (20-29)
        # ═══════════════════════════════════════════════════════════════════
        
        # Inmovilizado intangible (200-209)
        rules.append(QuestionRule(
            patterns=["intangible", "patente", "marca", "software", "licencia", "fondo comercio", "I+D"],
            code_prefixes=["200", "201", "202", "203", "204", "205", "206", "207", "208", "209"],
            question_increase="¿Se han adquirido nuevos activos intangibles? ¿Cuál es la naturaleza y vida útil estimada?",
            question_decrease="¿Se ha dado de baja o deteriorado algún intangible? ¿Cuál fue el motivo?",
            priority=2
        ))
        
        # Terrenos y bienes naturales (210)
        rules.append(QuestionRule(
            patterns=["terreno", "finca", "solar", "parcela"],
            code_prefixes=["210"],
            question_increase="¿Se han adquirido nuevos terrenos? ¿Cuál es su ubicación y finalidad?",
            question_decrease="¿Se han vendido terrenos? ¿Cuál fue el precio de venta y el resultado de la operación?",
            priority=3
        ))
        
        # Construcciones (211)
        rules.append(QuestionRule(
            patterns=["construccion", "edificio", "nave", "local", "inmueble"],
            code_prefixes=["211"],
            question_increase="¿Se han adquirido o construido nuevos inmuebles? ¿Para qué uso?",
            question_decrease="¿Se han vendido inmuebles o se ha registrado deterioro? Por favor detalle.",
            priority=3
        ))
        
        # Instalaciones técnicas (212)
        rules.append(QuestionRule(
            patterns=["instalaci", "técnica", "maquinaria"],
            code_prefixes=["212"],
            question_increase="¿Se han realizado inversiones en instalaciones técnicas? ¿Mejoran la capacidad productiva?",
            question_decrease="¿Se han dado de baja instalaciones? ¿Por obsolescencia o renovación?",
            priority=2
        ))
        
        # Maquinaria (213)
        rules.append(QuestionRule(
            patterns=["maquinaria", "máquina", "equipo industrial"],
            code_prefixes=["213"],
            question_increase="¿Se ha adquirido nueva maquinaria? ¿Para qué proceso productivo?",
            question_decrease="¿Se ha dado de baja maquinaria? ¿Por venta, obsolescencia o siniestro?",
            priority=2
        ))
        
        # Utillaje (214)
        rules.append(QuestionRule(
            patterns=["utillaje", "herramienta", "útil"],
            code_prefixes=["214"],
            question_increase="¿Se ha adquirido nuevo utillaje? ¿Para qué actividad?",
            question_decrease="¿Se ha dado de baja utillaje por desgaste o sustitución?",
            priority=1
        ))
        
        # Mobiliario (216)
        rules.append(QuestionRule(
            patterns=["mobiliario", "mueble", "enseres"],
            code_prefixes=["216"],
            question_increase="¿Se ha adquirido nuevo mobiliario? ¿Para nuevas instalaciones o renovación?",
            question_decrease="¿Se ha dado de baja mobiliario? ¿Por deterioro o traslado?",
            priority=1
        ))
        
        # Equipos informáticos (217)
        rules.append(QuestionRule(
            patterns=["equipo", "informátic", "ordenador", "servidor", "hardware", "IT"],
            code_prefixes=["217"],
            question_increase="¿Se han adquirido nuevos equipos informáticos? ¿Forman parte de un proyecto de modernización?",
            question_decrease="¿Se han dado de baja equipos informáticos? ¿Por obsolescencia tecnológica?",
            priority=2
        ))
        
        # Elementos de transporte (218)
        rules.append(QuestionRule(
            patterns=["transporte", "vehículo", "vehiculo", "coche", "furgoneta", "camión", "flota"],
            code_prefixes=["218"],
            question_increase="¿Se han adquirido nuevos vehículos? ¿Para qué uso (comercial, logística)?",
            question_decrease="¿Se han vendido vehículos? ¿Cuál fue el resultado de la venta?",
            priority=2
        ))
        
        # Otro inmovilizado material (219)
        rules.append(QuestionRule(
            patterns=["otro inmovilizado", "diversos"],
            code_prefixes=["219"],
            question_increase="¿Se han adquirido otros elementos de inmovilizado? Por favor especifique la naturaleza.",
            question_decrease="¿Se han dado de baja otros elementos de inmovilizado? ¿Cuál fue el motivo?",
            priority=1
        ))
        
        # Inversiones inmobiliarias (220-229)
        rules.append(QuestionRule(
            patterns=["inversión inmobiliaria", "inmueble inversión", "alquiler inmueble"],
            code_prefixes=["220", "221", "222", "223"],
            question_increase="¿Se han adquirido inmuebles para inversión? ¿Cuál es la rentabilidad esperada?",
            question_decrease="¿Se han vendido inversiones inmobiliarias? ¿Cuál fue el resultado?",
            priority=2
        ))
        
        # Inmovilizado en curso (230-239)
        rules.append(QuestionRule(
            patterns=["en curso", "construcción", "montaje", "proyecto"],
            code_prefixes=["230", "231", "232", "233", "237", "239"],
            question_increase="¿Hay nuevos proyectos de inversión en curso? ¿Cuál es el plazo estimado de finalización?",
            question_decrease="¿Se ha activado algún proyecto finalizado? ¿O se ha cancelado algún proyecto?",
            priority=2
        ))
        
        # Inversiones financieras LP en empresas grupo (240-249)
        rules.append(QuestionRule(
            patterns=["participación", "grupo", "asociada", "vinculada", "inversión financiera"],
            code_prefixes=["240", "241", "242", "243", "244", "245", "246", "247", "248", "249"],
            question_increase="¿Se han realizado inversiones en empresas del grupo? ¿Ampliación de participación o nueva adquisición?",
            question_decrease="¿Se han vendido participaciones o deteriorado inversiones en empresas del grupo?",
            priority=3
        ))
        
        # Inversiones financieras LP (250-259)
        rules.append(QuestionRule(
            patterns=["inversión", "valores", "acción", "bono", "renta fija", "renta variable"],
            code_prefixes=["250", "251", "252", "253", "254", "255", "256", "257", "258", "259"],
            question_increase="¿Se han realizado nuevas inversiones financieras? ¿Cuál es la estrategia de inversión?",
            question_decrease="¿Se han liquidado inversiones? ¿Cuál fue el resultado obtenido?",
            priority=2
        ))
        
        # Fianzas y depósitos LP (260-269)
        rules.append(QuestionRule(
            patterns=["fianza", "depósito", "garantía"],
            code_prefixes=["260", "261", "265", "266", "269"],
            question_increase="¿Se han constituido nuevas fianzas o depósitos? ¿Por qué concepto?",
            question_decrease="¿Se han recuperado fianzas o depósitos? ¿Ha finalizado la obligación garantizada?",
            priority=1
        ))
        
        # Amortización acumulada (280-289)
        rules.append(QuestionRule(
            patterns=["amortizaci", "depreciación"],
            code_prefixes=["280", "281", "282", "283", "284"],
            question_increase="¿El incremento de amortización corresponde a la dotación anual normal? ¿Se han revisado vidas útiles?",
            question_decrease="¿Se ha reducido la amortización por bajas de activos? Por favor confirme las bajas realizadas.",
            priority=2
        ))
        
        # Deterioro de valor (290-299)
        rules.append(QuestionRule(
            patterns=["deterioro", "provisión por depreciación"],
            code_prefixes=["290", "291", "292", "293", "294", "295", "296", "297", "298", "299"],
            question_increase="¿Se ha registrado deterioro de valor? ¿Qué activos han sido afectados y por qué motivo?",
            question_decrease="¿Se ha revertido deterioro de valor? ¿Ha mejorado el valor recuperable del activo?",
            priority=3
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # GRUPO 3: EXISTENCIAS (30-39)
        # ═══════════════════════════════════════════════════════════════════
        
        # Mercaderías (300-309)
        rules.append(QuestionRule(
            patterns=["mercader", "mercancía", "producto terminado", "stock"],
            code_prefixes=["300", "301", "302", "303", "304", "305", "306", "307", "308", "309"],
            question_increase="¿Ha aumentado el inventario de mercaderías? ¿Se debe a mayor actividad o acumulación de stock?",
            question_decrease="¿Ha disminuido el inventario? ¿Por ventas, mermas o deterioro?",
            priority=2
        ))
        
        # Materias primas (310-319)
        rules.append(QuestionRule(
            patterns=["materia prima", "materiales", "aprovisionamiento"],
            code_prefixes=["310", "311", "312", "313", "314", "315", "316", "317", "318", "319"],
            question_increase="¿Se ha incrementado el stock de materias primas? ¿Por anticipación de producción o precios?",
            question_decrease="¿Ha disminuido el inventario de materias primas? ¿Por consumo productivo o deterioro?",
            priority=2
        ))
        
        # Otros aprovisionamientos (320-329)
        rules.append(QuestionRule(
            patterns=["combustible", "repuesto", "embalaje", "envase", "material diverso"],
            code_prefixes=["320", "321", "322", "323", "324", "325", "326", "327", "328", "329"],
            question_increase="¿Se ha incrementado el stock de otros aprovisionamientos? ¿Por qué concepto?",
            question_decrease="¿Ha disminuido el inventario de aprovisionamientos? ¿Por consumo o deterioro?",
            priority=1
        ))
        
        # Productos en curso (330-339)
        rules.append(QuestionRule(
            patterns=["producto en curso", "fabricación", "semiterminado", "WIP"],
            code_prefixes=["330", "331", "332", "333", "334", "335", "336"],
            question_increase="¿Ha aumentado el producto en curso? ¿Hay retrasos en la producción?",
            question_decrease="¿Ha disminuido el producto en curso? ¿Se ha completado la producción?",
            priority=2
        ))
        
        # Productos terminados (350-359)
        rules.append(QuestionRule(
            patterns=["producto terminado", "acabado", "almacén producto"],
            code_prefixes=["350", "351", "352", "353", "354", "355", "356"],
            question_increase="¿Ha aumentado el stock de productos terminados? ¿Hay problemas de ventas o es por estacionalidad?",
            question_decrease="¿Ha disminuido el inventario? ¿Las ventas han sido mayores a la producción?",
            priority=2
        ))
        
        # Subproductos y residuos (360-369)
        rules.append(QuestionRule(
            patterns=["subproducto", "residuo", "recuperación", "material recuperado"],
            code_prefixes=["360", "361", "362", "363", "364", "365", "366", "367", "368", "369"],
            question_increase="¿Se han generado más subproductos? ¿Existe mercado para su venta?",
            question_decrease="¿Se han vendido subproductos o eliminado residuos?",
            priority=1
        ))
        
        # Deterioro de existencias (390-399)
        rules.append(QuestionRule(
            patterns=["deterioro existencia", "obsolescencia", "depreciación stock"],
            code_prefixes=["390", "391", "392", "393", "394", "395", "396"],
            question_increase="¿Se ha dotado provisión por deterioro de existencias? ¿Qué productos están afectados?",
            question_decrease="¿Se ha revertido o aplicado provisión de existencias? ¿Se han vendido o dado de baja?",
            priority=3
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # GRUPO 4: ACREEDORES Y DEUDORES (40-49)
        # ═══════════════════════════════════════════════════════════════════
        
        # Proveedores (400-409)
        rules.append(QuestionRule(
            patterns=["proveedor", "acreedor comercial", "cuenta por pagar"],
            code_prefixes=["400", "401", "402", "403", "404", "405", "406", "407"],
            question_increase="¿Ha aumentado el saldo con proveedores? ¿Se han extendido los plazos de pago o hay más compras?",
            question_decrease="¿Se han pagado proveedores? ¿Se han obtenido descuentos por pronto pago?",
            priority=2
        ))
        
        # Efectos comerciales a pagar (401)
        rules.append(QuestionRule(
            patterns=["efecto", "pagaré", "letra"],
            code_prefixes=["401"],
            question_increase="¿Se han aceptado nuevos efectos comerciales? ¿Cuáles son los vencimientos?",
            question_decrease="¿Se han pagado efectos comerciales a su vencimiento?",
            priority=2
        ))
        
        # Acreedores varios (410-419)
        rules.append(QuestionRule(
            patterns=["acreedor", "cuenta por pagar", "terceros"],
            code_prefixes=["410", "411", "412", "419"],
            question_increase="¿Han aumentado las cuentas por pagar a acreedores? ¿Por qué concepto?",
            question_decrease="¿Se han liquidado deudas con acreedores? Por favor especifique.",
            priority=1
        ))
        
        # Clientes (430-439)
        rules.append(QuestionRule(
            patterns=["cliente", "cuenta por cobrar", "deudor comercial"],
            code_prefixes=["430", "431", "432", "433", "434", "435", "436", "437"],
            question_increase="¿Ha aumentado el saldo de clientes? ¿Por mayores ventas o retrasos en cobro?",
            question_decrease="¿Se han cobrado clientes? ¿Se han dado de baja créditos incobrables?",
            priority=2
        ))
        
        # Efectos comerciales a cobrar (431)
        rules.append(QuestionRule(
            patterns=["efecto a cobrar", "letra a cobrar", "pagaré recibido"],
            code_prefixes=["431"],
            question_increase="¿Se han recibido nuevos efectos de clientes? ¿Cuáles son los vencimientos?",
            question_decrease="¿Se han cobrado efectos comerciales? ¿Hubo algún impagado?",
            priority=2
        ))
        
        # Deudores varios (440-449)
        rules.append(QuestionRule(
            patterns=["deudor", "anticipos", "cuenta por cobrar"],
            code_prefixes=["440", "441", "449"],
            question_increase="¿Han aumentado los deudores varios? ¿Por qué concepto?",
            question_decrease="¿Se han cobrado deudores? Por favor especifique la naturaleza.",
            priority=1
        ))
        
        # Personal (460-469)
        rules.append(QuestionRule(
            patterns=["personal", "empleado", "anticipo personal", "remuneración pendiente"],
            code_prefixes=["460", "465", "466"],
            question_increase="¿Han aumentado los saldos con personal? ¿Por anticipos o remuneraciones pendientes?",
            question_decrease="¿Se han liquidado cuentas con personal? Por favor detalle.",
            priority=1
        ))
        
        # Hacienda Pública - Administraciones (470-479)
        rules.append(QuestionRule(
            patterns=["hacienda", "administración pública", "IVA", "impuesto", "IRPF", "seguridad social"],
            code_prefixes=["470", "471", "472", "473", "474", "475", "476", "477", "479"],
            question_increase="¿Han aumentado los saldos con Hacienda? ¿Por qué impuesto o concepto?",
            question_decrease="¿Se han pagado o compensado saldos con administraciones públicas?",
            priority=2
        ))
        
        # Deterioro de créditos comerciales (490-499)
        rules.append(QuestionRule(
            patterns=["deterioro crédito", "insolvencia", "moroso", "incobrable"],
            code_prefixes=["490", "493", "494", "495", "496", "499"],
            question_increase="¿Se ha dotado provisión por insolvencia? ¿Qué clientes están en situación de riesgo?",
            question_decrease="¿Se ha revertido o aplicado provisión por insolvencia? ¿Se han recuperado o dado de baja créditos?",
            priority=3
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # GRUPO 5: CUENTAS FINANCIERAS (50-57)
        # ═══════════════════════════════════════════════════════════════════
        
        # Deudas corto plazo empresas grupo (500-509)
        rules.append(QuestionRule(
            patterns=["préstamo grupo", "deuda grupo", "obligación grupo"],
            code_prefixes=["500", "501", "502", "503", "504", "505", "506", "507", "508", "509"],
            question_increase="¿Se ha obtenido financiación del grupo a corto plazo? ¿Cuáles son las condiciones?",
            question_decrease="¿Se han amortizado deudas con empresas del grupo?",
            priority=2
        ))
        
        # Deudas corto plazo (520-529)
        rules.append(QuestionRule(
            patterns=["préstamo corto", "póliza crédito", "crédito bancario", "línea crédito"],
            code_prefixes=["520", "521", "522", "523", "524", "525", "526", "527", "528", "529"],
            question_increase="¿Se ha dispuesto de financiación bancaria a corto plazo? ¿Para qué necesidad?",
            question_decrease="¿Se ha amortizado deuda bancaria a corto plazo? ¿Con qué fondos?",
            priority=2
        ))
        
        # Inversiones financieras CP empresas grupo (530-539)
        rules.append(QuestionRule(
            patterns=["inversión grupo CP", "préstamo a grupo", "crédito grupo"],
            code_prefixes=["530", "531", "532", "533", "534", "535", "536", "537", "538", "539"],
            question_increase="¿Se han realizado inversiones en empresas del grupo a corto plazo?",
            question_decrease="¿Se han recuperado préstamos a empresas del grupo?",
            priority=2
        ))
        
        # Inversiones financieras CP (540-549)
        rules.append(QuestionRule(
            patterns=["inversión temporal", "depósito plazo", "valores CP"],
            code_prefixes=["540", "541", "542", "543", "544", "545", "546", "547", "548", "549"],
            question_increase="¿Se han realizado inversiones financieras temporales? ¿Cuál es el objetivo?",
            question_decrease="¿Se han liquidado inversiones temporales? ¿Cuál fue el rendimiento obtenido?",
            priority=2
        ))
        
        # Otras cuentas no bancarias (550-559)
        rules.append(QuestionRule(
            patterns=["cuenta corriente socio", "dividendo", "cuenta partícipe"],
            code_prefixes=["550", "551", "552", "553", "554", "555", "556", "557", "558", "559"],
            question_increase="¿Han aumentado los saldos con socios o partícipes? ¿Por qué concepto?",
            question_decrease="¿Se han liquidado cuentas con socios? ¿Se han pagado dividendos?",
            priority=2
        ))
        
        # Fianzas y depósitos recibidos/constituidos CP (560-569)
        rules.append(QuestionRule(
            patterns=["fianza CP", "depósito CP", "garantía corto"],
            code_prefixes=["560", "561", "565", "566", "569"],
            question_increase="¿Se han constituido o recibido nuevas fianzas a corto plazo? ¿Por qué concepto?",
            question_decrease="¿Se han devuelto o recuperado fianzas? ¿Ha finalizado la obligación?",
            priority=1
        ))
        
        # Tesorería (570-579)
        rules.append(QuestionRule(
            patterns=["caja", "banco", "tesorería", "efectivo", "cuenta corriente"],
            code_prefixes=["570", "571", "572", "573", "574", "575", "576"],
            question_increase="¿Ha aumentado la tesorería? ¿Por cobros, financiación o desinversiones?",
            question_decrease="¿Ha disminuido la tesorería? ¿Por pagos operativos, inversiones o financiación?",
            priority=2
        ))
        
        # Deterioro inversiones financieras CP (590-599)
        rules.append(QuestionRule(
            patterns=["deterioro inversión CP", "provisión valores"],
            code_prefixes=["590", "591", "592", "593", "594", "595", "596", "597", "598", "599"],
            question_increase="¿Se ha dotado deterioro de inversiones financieras? ¿Qué valores están afectados?",
            question_decrease="¿Se ha revertido deterioro de inversiones? ¿Ha mejorado el valor de mercado?",
            priority=3
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # GRUPO 6: COMPRAS Y GASTOS (60-69)
        # ═══════════════════════════════════════════════════════════════════
        
        # Compras de mercaderías (600)
        rules.append(QuestionRule(
            patterns=["compra mercader", "aprovisionamiento", "coste mercancía"],
            code_prefixes=["600"],
            question_increase="¿Han aumentado las compras de mercaderías? ¿Por mayor volumen de ventas o incremento de precios?",
            question_decrease="¿Han disminuido las compras? ¿Por menor actividad o cambio de proveedores?",
            priority=3
        ))
        
        # Compras de materias primas (601)
        rules.append(QuestionRule(
            patterns=["compra materia prima", "coste material", "aprovision"],
            code_prefixes=["601"],
            question_increase="¿Han aumentado las compras de materias primas? ¿Por mayor producción o subida de precios?",
            question_decrease="¿Han disminuido las compras de materias primas? ¿Por menor producción o eficiencias?",
            priority=3
        ))
        
        # Otros aprovisionamientos (602)
        rules.append(QuestionRule(
            patterns=["otro aprovision", "consumible", "material auxiliar"],
            code_prefixes=["602"],
            question_increase="¿Han aumentado otros aprovisionamientos? ¿Por qué concepto?",
            question_decrease="¿Han disminuido otros aprovisionamientos? ¿Se han conseguido eficiencias?",
            priority=2
        ))
        
        # Descuentos sobre compras (606-608)
        rules.append(QuestionRule(
            patterns=["descuento compra", "rappel", "bonificación proveedor"],
            code_prefixes=["606", "607", "608", "609"],
            question_increase="¿Se han obtenido más descuentos de proveedores? ¿Por qué concepto?",
            question_decrease="¿Han disminuido los descuentos? ¿Se han renegociado condiciones con proveedores?",
            priority=2
        ))
        
        # Variación de existencias (610-612)
        rules.append(QuestionRule(
            patterns=["variación existencia", "variación stock", "diferencia inventario"],
            code_prefixes=["610", "611", "612"],
            question_increase="¿La variación de existencias refleja una disminución de stock? ¿Por consumo o mermas?",
            question_decrease="¿La variación negativa indica aumento de stock? ¿Por acumulación de inventario?",
            priority=2
        ))
        
        # Servicios exteriores - Arrendamientos (621)
        rules.append(QuestionRule(
            patterns=["alquiler", "arrendamiento", "renting", "leasing operativo"],
            code_prefixes=["621"],
            question_increase="¿Han aumentado los gastos de alquiler? ¿Por nuevos contratos o subidas de renta?",
            question_decrease="¿Han disminuido los alquileres? ¿Se han rescindido contratos o renegociado rentas?",
            priority=2
        ))
        
        # Reparaciones y conservación (622)
        rules.append(QuestionRule(
            patterns=["reparación", "mantenimiento", "conservación"],
            code_prefixes=["622"],
            question_increase="¿Han aumentado los gastos de mantenimiento? ¿Por reparaciones extraordinarias o contratos nuevos?",
            question_decrease="¿Han disminuido los gastos de mantenimiento? ¿Se han renegociado contratos o menos averías?",
            priority=2
        ))
        
        # Servicios profesionales independientes (623)
        rules.append(QuestionRule(
            patterns=["profesional", "consultor", "asesor", "abogado", "auditor", "honorario"],
            code_prefixes=["623"],
            question_increase="¿Han aumentado los servicios profesionales? ¿Por qué tipo de asesoramiento?",
            question_decrease="¿Han disminuido los servicios externos? ¿Se han internalizado funciones?",
            priority=2
        ))
        
        # Transportes (624)
        rules.append(QuestionRule(
            patterns=["transporte", "porte", "flete", "logística", "envío"],
            code_prefixes=["624"],
            question_increase="¿Han aumentado los gastos de transporte? ¿Por mayor volumen o subida de tarifas?",
            question_decrease="¿Han disminuido los transportes? ¿Por eficiencias logísticas o menor actividad?",
            priority=2
        ))
        
        # Primas de seguros (625)
        rules.append(QuestionRule(
            patterns=["seguro", "prima", "póliza seguro"],
            code_prefixes=["625"],
            question_increase="¿Han aumentado las primas de seguros? ¿Por nuevas coberturas o subida de tarifas?",
            question_decrease="¿Han disminuido los seguros? ¿Se han eliminado coberturas o renegociado primas?",
            priority=1
        ))
        
        # Servicios bancarios (626)
        rules.append(QuestionRule(
            patterns=["comisión banco", "servicio bancario", "gastos financieros menores"],
            code_prefixes=["626"],
            question_increase="¿Han aumentado los gastos bancarios? ¿Por qué servicios o comisiones?",
            question_decrease="¿Han disminuido los gastos bancarios? ¿Se han renegociado comisiones?",
            priority=1
        ))
        
        # Publicidad y propaganda (627)
        rules.append(QuestionRule(
            patterns=["publicidad", "marketing", "promoción", "campaña", "patrocinio"],
            code_prefixes=["627"],
            question_increase="¿Ha aumentado la inversión en publicidad? ¿Para qué campañas o productos?",
            question_decrease="¿Ha disminuido el gasto en marketing? ¿Se ha reducido la inversión comercial?",
            priority=2
        ))
        
        # Suministros (628)
        rules.append(QuestionRule(
            patterns=["suministro", "electricidad", "agua", "gas", "teléfono", "internet"],
            code_prefixes=["628"],
            question_increase="¿Han aumentado los suministros? ¿Por subida de tarifas o mayor consumo?",
            question_decrease="¿Han disminuido los suministros? ¿Por ahorro energético o cambio de proveedor?",
            priority=1
        ))
        
        # Otros servicios (629)
        rules.append(QuestionRule(
            patterns=["otro servicio", "viaje", "dieta", "formación", "suscripción"],
            code_prefixes=["629"],
            question_increase="¿Han aumentado otros servicios? ¿Por qué concepto específico?",
            question_decrease="¿Han disminuido otros servicios? ¿Se han eliminado gastos no esenciales?",
            priority=1
        ))
        
        # Tributos (631)
        rules.append(QuestionRule(
            patterns=["tributo", "impuesto local", "IBI", "IAE", "tasa"],
            code_prefixes=["630", "631", "634", "636", "639"],
            question_increase="¿Han aumentado los tributos? ¿Por nuevas obligaciones o subida de tipos?",
            question_decrease="¿Han disminuido los tributos? ¿Por bonificaciones o reducción de base?",
            priority=1
        ))
        
        # Gastos de personal - Sueldos y salarios (640)
        rules.append(QuestionRule(
            patterns=["sueldo", "salario", "nómina", "retribución"],
            code_prefixes=["640"],
            question_increase="¿Han aumentado los sueldos? ¿Por nuevas contrataciones, subidas salariales o bonus?",
            question_decrease="¿Han disminuido los sueldos? ¿Por despidos, jubilaciones o reducción de plantilla?",
            priority=3
        ))
        
        # Indemnizaciones (641)
        rules.append(QuestionRule(
            patterns=["indemnización", "despido", "finiquito", "prejubilación"],
            code_prefixes=["641"],
            question_increase="¿Se han pagado indemnizaciones? ¿Por despidos, ERE o prejubilaciones?",
            question_decrease="¿Han disminuido las indemnizaciones respecto al periodo anterior?",
            priority=3
        ))
        
        # Seguridad Social a cargo de la empresa (642)
        rules.append(QuestionRule(
            patterns=["seguridad social", "cotización social", "cuota patronal"],
            code_prefixes=["642"],
            question_increase="¿Ha aumentado la Seguridad Social? ¿Por más plantilla o subida de bases?",
            question_decrease="¿Ha disminuido la Seguridad Social? ¿Por reducciones de plantilla o bonificaciones?",
            priority=2
        ))
        
        # Retribuciones a largo plazo (643)
        rules.append(QuestionRule(
            patterns=["retribución LP", "plan pensiones", "compromiso personal"],
            code_prefixes=["643"],
            question_increase="¿Se han incrementado compromisos de retribución a largo plazo? ¿Planes de pensiones?",
            question_decrease="¿Han disminuido los compromisos a largo plazo? ¿Por qué concepto?",
            priority=2
        ))
        
        # Retribuciones mediante instrumentos de patrimonio (644)
        rules.append(QuestionRule(
            patterns=["stock option", "retribución acciones", "phantom shares"],
            code_prefixes=["644"],
            question_increase="¿Se han concedido planes de retribución en acciones? ¿A qué colectivo?",
            question_decrease="¿Han vencido o cancelado planes de retribución en acciones?",
            priority=2
        ))
        
        # Otros gastos sociales (649)
        rules.append(QuestionRule(
            patterns=["gasto social", "formación", "comedor", "beneficio social"],
            code_prefixes=["649"],
            question_increase="¿Han aumentado los gastos sociales? ¿Por qué conceptos (formación, beneficios)?",
            question_decrease="¿Han disminuido los gastos sociales? ¿Se han reducido beneficios al personal?",
            priority=1
        ))
        
        # Pérdidas de créditos (650)
        rules.append(QuestionRule(
            patterns=["pérdida crédito", "crédito incobrable", "insolvencia"],
            code_prefixes=["650"],
            question_increase="¿Se han registrado pérdidas por créditos incobrables? ¿Qué clientes están afectados?",
            question_decrease="¿Han disminuido las pérdidas por créditos? ¿Se ha mejorado la gestión de cobro?",
            priority=3
        ))
        
        # Otros gastos de gestión (651-659)
        rules.append(QuestionRule(
            patterns=["otro gasto gestión", "resultado enajenación", "gasto excepcional"],
            code_prefixes=["651", "659"],
            question_increase="¿Han aumentado otros gastos de gestión? ¿Por qué concepto específico?",
            question_decrease="¿Han disminuido otros gastos de gestión?",
            priority=1
        ))
        
        # Gastos financieros (661-669)
        rules.append(QuestionRule(
            patterns=["interés", "gasto financiero", "comisión financiera", "diferencia cambio negativa"],
            code_prefixes=["661", "662", "663", "664", "665", "666", "667", "668", "669"],
            question_increase="¿Han aumentado los gastos financieros? ¿Por más deuda, subida de tipos o diferencias de cambio?",
            question_decrease="¿Han disminuido los gastos financieros? ¿Por amortización de deuda o bajada de tipos?",
            priority=2
        ))
        
        # Pérdidas de instrumentos financieros (670-679)
        rules.append(QuestionRule(
            patterns=["pérdida financiera", "deterioro participación", "pérdida inversión"],
            code_prefixes=["670", "671", "672", "673", "675", "676", "677", "678", "679"],
            question_increase="¿Se han registrado pérdidas en instrumentos financieros? ¿Por qué inversiones?",
            question_decrease="¿Han disminuido las pérdidas financieras respecto al periodo anterior?",
            priority=3
        ))
        
        # Amortizaciones (680-689)
        rules.append(QuestionRule(
            patterns=["amortización", "depreciación anual"],
            code_prefixes=["680", "681", "682"],
            question_increase="¿Ha aumentado la amortización? ¿Por nuevas inversiones o revisión de vidas útiles?",
            question_decrease="¿Ha disminuido la amortización? ¿Por activos totalmente amortizados o bajas?",
            priority=2
        ))
        
        # Pérdidas por deterioro (690-699)
        rules.append(QuestionRule(
            patterns=["pérdida deterioro", "provisión deterioro", "corrección valorativa"],
            code_prefixes=["690", "691", "692", "693", "694", "695", "696", "697", "698", "699"],
            question_increase="¿Se ha dotado deterioro de activos? ¿Qué elementos están afectados?",
            question_decrease="¿Se ha revertido deterioro? ¿Ha mejorado el valor recuperable?",
            priority=3
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # GRUPO 7: VENTAS E INGRESOS (70-79)
        # ═══════════════════════════════════════════════════════════════════
        
        # Ventas de mercaderías (700)
        rules.append(QuestionRule(
            patterns=["venta mercader", "ingreso comercial", "facturación producto"],
            code_prefixes=["700"],
            question_increase="¿Han aumentado las ventas de mercaderías? ¿Por volumen, precio o nuevos clientes?",
            question_decrease="¿Han disminuido las ventas? ¿Por pérdida de clientes, competencia o estacionalidad?",
            priority=3
        ))
        
        # Ventas de productos terminados (701)
        rules.append(QuestionRule(
            patterns=["venta producto", "facturación producción"],
            code_prefixes=["701"],
            question_increase="¿Han aumentado las ventas de productos? ¿Por mayor producción o nuevos productos?",
            question_decrease="¿Han disminuido las ventas de productos? ¿Por menor demanda o discontinuación?",
            priority=3
        ))
        
        # Ventas de productos semiterminados/residuos (702-703)
        rules.append(QuestionRule(
            patterns=["venta semiterminado", "venta residuo", "venta subproducto"],
            code_prefixes=["702", "703"],
            question_increase="¿Han aumentado las ventas de semiterminados o residuos? ¿Hay nuevos canales?",
            question_decrease="¿Han disminuido estas ventas? ¿Se han eliminado canales de comercialización?",
            priority=2
        ))
        
        # Prestación de servicios (705)
        rules.append(QuestionRule(
            patterns=["servicio", "prestación", "consultoría", "asesoramiento", "trabajo realizado"],
            code_prefixes=["705"],
            question_increase="¿Han aumentado los ingresos por servicios? ¿Por nuevos contratos o subida de tarifas?",
            question_decrease="¿Han disminuido los servicios? ¿Por finalización de contratos o pérdida de clientes?",
            priority=3
        ))
        
        # Descuentos sobre ventas (706-709)
        rules.append(QuestionRule(
            patterns=["descuento venta", "rappel cliente", "bonificación", "devolución"],
            code_prefixes=["706", "707", "708", "709"],
            question_increase="¿Han aumentado los descuentos a clientes? ¿Por campañas promocionales o devoluciones?",
            question_decrease="¿Han disminuido los descuentos? ¿Se han reducido las promociones?",
            priority=2
        ))
        
        # Variación de existencias de productos (710-712)
        rules.append(QuestionRule(
            patterns=["variación existencia producto", "variación fabricación"],
            code_prefixes=["710", "711", "712", "713"],
            question_increase="¿La variación positiva indica aumento de inventario de productos?",
            question_decrease="¿La variación negativa indica reducción de inventario de productos?",
            priority=2
        ))
        
        # Trabajos realizados para el inmovilizado (730-739)
        rules.append(QuestionRule(
            patterns=["trabajo propio", "activación gasto", "inmovilizado fabricación propia"],
            code_prefixes=["730", "731", "732", "733"],
            question_increase="¿Se han activado trabajos realizados para el inmovilizado propio? ¿Qué proyectos?",
            question_decrease="¿Han disminuido los trabajos para inmovilizado propio? ¿Se han finalizado proyectos?",
            priority=2
        ))
        
        # Subvenciones, donaciones y legados (740-749)
        rules.append(QuestionRule(
            patterns=["subvención", "donación", "legado", "ayuda pública"],
            code_prefixes=["740", "746", "747"],
            question_increase="¿Se han recibido subvenciones o donaciones? ¿De qué organismo y para qué fin?",
            question_decrease="¿Han disminuido las subvenciones? ¿Se han devuelto o no renovado ayudas?",
            priority=2
        ))
        
        # Otros ingresos de gestión (751-759)
        rules.append(QuestionRule(
            patterns=["ingreso accesorio", "comisión", "royalty", "propiedad industrial"],
            code_prefixes=["751", "752", "753", "754", "755", "759"],
            question_increase="¿Han aumentado otros ingresos de gestión? ¿Por qué concepto?",
            question_decrease="¿Han disminuido otros ingresos de gestión? ¿Se han perdido fuentes de ingreso?",
            priority=1
        ))
        
        # Ingresos financieros (760-769)
        rules.append(QuestionRule(
            patterns=["ingreso financiero", "interés cobrado", "dividendo", "diferencia cambio positiva"],
            code_prefixes=["760", "761", "762", "763", "764", "765", "766", "767", "768", "769"],
            question_increase="¿Han aumentado los ingresos financieros? ¿Por mayores inversiones, tipos o dividendos?",
            question_decrease="¿Han disminuido los ingresos financieros? ¿Por desinversiones o bajada de tipos?",
            priority=2
        ))
        
        # Beneficios de instrumentos financieros (770-779)
        rules.append(QuestionRule(
            patterns=["beneficio financiero", "plusvalía", "ganancia inversión"],
            code_prefixes=["770", "771", "772", "773", "774", "775", "776", "777", "778", "779"],
            question_increase="¿Se han registrado beneficios por inversiones? ¿Qué instrumentos se han vendido?",
            question_decrease="¿Han disminuido los beneficios financieros respecto al periodo anterior?",
            priority=2
        ))
        
        # Reversión de deterioros (790-799)
        rules.append(QuestionRule(
            patterns=["reversión", "recuperación deterioro"],
            code_prefixes=["790", "791", "792", "793", "794", "795", "796", "797", "798", "799"],
            question_increase="¿Se ha revertido deterioro de activos? ¿Qué elementos han recuperado valor?",
            question_decrease="¿Ha disminuido la reversión de deterioros?",
            priority=2
        ))
        
        # ═══════════════════════════════════════════════════════════════════
        # REGLAS GENÉRICAS POR PREFIJO DE CUENTA
        # ═══════════════════════════════════════════════════════════════════
        
        # Regla genérica para grupo 1 (Financiación)
        rules.append(QuestionRule(
            patterns=[],
            code_prefixes=["1"],
            question_increase="¿Cuál es el origen del incremento en esta partida de financiación?",
            question_decrease="¿Por qué ha disminuido esta partida de financiación?",
            priority=0
        ))
        
        # Regla genérica para grupo 2 (Inmovilizado)
        rules.append(QuestionRule(
            patterns=[],
            code_prefixes=["2"],
            question_increase="¿Se han realizado inversiones en esta partida de inmovilizado? Por favor detalle.",
            question_decrease="¿Ha habido bajas o deterioro en esta partida de inmovilizado? Por favor detalle.",
            priority=0
        ))
        
        # Regla genérica para grupo 3 (Existencias)
        rules.append(QuestionRule(
            patterns=[],
            code_prefixes=["3"],
            question_increase="¿Ha aumentado el nivel de inventario? ¿Por qué razón?",
            question_decrease="¿Ha disminuido el inventario? ¿Por ventas, consumo o deterioro?",
            priority=0
        ))
        
        # Regla genérica para grupo 4 (Acreedores/Deudores)
        rules.append(QuestionRule(
            patterns=[],
            code_prefixes=["4"],
            question_increase="¿Cuál es el origen del incremento en esta cuenta? Por favor detalle.",
            question_decrease="¿Por qué ha disminuido el saldo de esta cuenta?",
            priority=0
        ))
        
        # Regla genérica para grupo 5 (Cuentas financieras)
        rules.append(QuestionRule(
            patterns=[],
            code_prefixes=["5"],
            question_increase="¿Cuál es el origen del incremento en esta partida financiera?",
            question_decrease="¿Por qué ha disminuido esta partida financiera?",
            priority=0
        ))
        
        # Regla genérica para grupo 6 (Gastos)
        rules.append(QuestionRule(
            patterns=[],
            code_prefixes=["6"],
            question_increase="¿Por qué han aumentado estos gastos? Por favor justifique el incremento.",
            question_decrease="¿A qué se debe la reducción de estos gastos?",
            priority=0
        ))
        
        # Regla genérica para grupo 7 (Ingresos)
        rules.append(QuestionRule(
            patterns=[],
            code_prefixes=["7"],
            question_increase="¿Cuál es el origen del incremento en estos ingresos?",
            question_decrease="¿Por qué han disminuido estos ingresos? Por favor explique.",
            priority=0
        ))
        
        return rules
    
    def should_generate_question(
        self, 
        variation_percent: float, 
        variation_absolute: float,
        account_name: str
    ) -> bool:
        """
        Determina si se debe generar pregunta basándose en umbrales y exclusiones.
        """
        # Verificar exclusiones
        for pattern in self.exclusion_patterns:
            if re.search(pattern, account_name.lower()):
                return False
        
        # Verificar umbrales
        if abs(variation_percent) < self.variation_threshold_percent:
            return False
        if abs(variation_absolute) < self.variation_threshold_absolute:
            return False
            
        return True
    
    def _match_rule(
        self, 
        account_code: str, 
        account_name: str
    ) -> Optional[QuestionRule]:
        """
        Encuentra la regla más específica que coincide con la cuenta.
        """
        matching_rules = []
        
        for rule in self.rules:
            code_match = False
            pattern_match = False
            
            # Verificar prefijo de código
            for prefix in rule.code_prefixes:
                if account_code.startswith(prefix):
                    code_match = True
                    break
            
            if not code_match:
                continue
            
            # Verificar patrones en descripción
            if not rule.patterns:
                # Regla genérica sin patrones
                pattern_match = True
            else:
                for pattern in rule.patterns:
                    if re.search(pattern, account_name.lower()):
                        pattern_match = True
                        break
            
            if pattern_match:
                matching_rules.append(rule)
        
        if not matching_rules:
            return None
        
        # Ordenar por prioridad (mayor primero) y devolver la más específica
        matching_rules.sort(key=lambda r: r.priority, reverse=True)
        return matching_rules[0]

    def _match_rule_with_details(
        self,
        account_code: str,
        account_name: str,
    ) -> Optional[Tuple[QuestionRule, Optional[str], Optional[str]]]:
        """Devuelve la regla y detalles de match (prefijo y patrón)."""
        matching: List[Tuple[QuestionRule, Optional[str], Optional[str]]] = []

        for rule in self.rules:
            matched_prefix: Optional[str] = None
            matched_pattern: Optional[str] = None

            for prefix in rule.code_prefixes:
                if account_code.startswith(prefix):
                    matched_prefix = prefix
                    break

            if not matched_prefix:
                continue

            if not rule.patterns:
                matching.append((rule, matched_prefix, None))
                continue

            for pattern in rule.patterns:
                if re.search(pattern, account_name.lower()):
                    matched_pattern = pattern
                    break

            if matched_pattern:
                matching.append((rule, matched_prefix, matched_pattern))

        if not matching:
            return None

        matching.sort(key=lambda t: t[0].priority, reverse=True)
        return matching[0]

    def generate_question_with_reason(self, context: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Genera pregunta y razón (regla aplicada) basada en el contexto."""
        account_code = str(context.get("account_code", ""))
        account_name = context.get("account_name", "")
        variation_percent = context.get("variation_percent", 0)
        variation_absolute = context.get("variation_absolute", 0)
        current_value = context.get("current_value", 0)
        previous_value = context.get("previous_value", 0)
        period_current = context.get("period_current", "actual")
        period_previous = context.get("period_previous", "anterior")

        if not self.should_generate_question(variation_percent, variation_absolute, account_name):
            return None, None

        match = self._match_rule_with_details(account_code, account_name)
        rule: Optional[QuestionRule] = match[0] if match else None
        matched_prefix: Optional[str] = match[1] if match else None
        matched_pattern: Optional[str] = match[2] if match else None

        if not rule:
            if abs(variation_percent) > 20:
                direction = "incrementado" if variation_percent > 0 else "disminuido"
                question = (
                    f"La cuenta ha {direction} un {abs(variation_percent):.1f}% "
                    f"(de {previous_value:,.2f} a {current_value:,.2f}). "
                    f"Por favor, explique el motivo de esta variación significativa."
                )
                reason = (
                    f"Regla aplicada: fallback (sin match). "
                    f"Umbrales: |%|>20 (fallback). "
                    f"Variación: {variation_percent:+.1f}% | abs: {variation_absolute:+,.2f} | "
                    f"{period_previous}: {previous_value:,.2f} → {period_current}: {current_value:,.2f}"
                )
                return question, reason
            return None, None

        if variation_percent == 0 and isinstance(variation_absolute, (int, float)):
            direction_increase = variation_absolute > 0
        else:
            direction_increase = variation_percent > 0

        base_question = rule.question_increase if direction_increase else rule.question_decrease

        # Formato estilo plantilla: 2 sub-preguntas con periodos y % (sin bloque extra de valores)
        try:
            pct_int = int(round(abs(float(variation_percent))))
        except Exception:
            pct_int = 0

        group = account_code[:1] if account_code else ""
        if group == "7":
            drivers_topic = "del crecimiento de ingresos" if direction_increase else "de la disminución de ingresos"
        elif group == "6":
            drivers_topic = "del incremento de gastos" if direction_increase else "de la reducción de gastos"
        else:
            drivers_topic = "de la variación del saldo"

        drivers = (
            f"(i) Comentar de manera general los principales \"drivers\" {drivers_topic} "
            f"entre {period_previous} y {period_current} ({pct_int}%)."
        )
        follow = f"(ii) {base_question}"

        reason = (
            f"Regla aplicada: prefijo='{matched_prefix}'"
            + (f", patrón='{matched_pattern}'" if matched_pattern else ", patrón=genérica")
            + f", prioridad={rule.priority}. "
            f"Umbrales: |%|>={self.variation_threshold_percent:.1f} y |abs|>={self.variation_threshold_absolute:,.0f}. "
            f"Variación: {variation_percent:+.1f}% | abs: {variation_absolute:+,.2f} | "
            f"{period_previous}: {previous_value:,.2f} → {period_current}: {current_value:,.2f}"
        )

        return f"{drivers}\n{follow}", reason
    
    def generate_question(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Genera una pregunta de auditoría basada en el contexto de la cuenta.
        
        Args:
            context: Diccionario con:
                - account_code: Código de cuenta PGC
                - account_name: Nombre/descripción de la cuenta
                - variation_percent: Porcentaje de variación
                - variation_absolute: Variación en valor absoluto
                - current_value: Valor actual
                - previous_value: Valor del periodo anterior
                - period_current: Periodo actual
                - period_previous: Periodo anterior
        
        Returns:
            Pregunta contextualizada o None si no aplica
        """
        account_code = str(context.get("account_code", ""))
        account_name = context.get("account_name", "")
        variation_percent = context.get("variation_percent", 0)
        variation_absolute = context.get("variation_absolute", 0)
        current_value = context.get("current_value", 0)
        previous_value = context.get("previous_value", 0)
        period_current = context.get("period_current", "actual")
        period_previous = context.get("period_previous", "anterior")
        
        # Verificar si debemos generar pregunta
        if not self.should_generate_question(variation_percent, variation_absolute, account_name):
            return None
        
        # Buscar regla aplicable
        rule = self._match_rule(account_code, account_name)
        
        if not rule:
            # Regla por defecto para variaciones muy significativas
            if abs(variation_percent) > 20:
                direction = "incrementado" if variation_percent > 0 else "disminuido"
                return (
                    f"La cuenta ha {direction} un {abs(variation_percent):.1f}% "
                    f"(de {previous_value:,.2f} a {current_value:,.2f}). "
                    f"Por favor, explique el motivo de esta variación significativa."
                )
            return None
        
        # Seleccionar pregunta según dirección de variación
        if variation_percent > 0:
            base_question = rule.question_increase
        else:
            base_question = rule.question_decrease
        
        # Enriquecer la pregunta con datos contextuales
        variation_info = (
            f"[Variación: {variation_percent:+.1f}% | "
            f"Valor anterior ({period_previous}): {previous_value:,.2f} | "
            f"Valor actual ({period_current}): {current_value:,.2f}]"
        )
        
        return f"{base_question}\n{variation_info}"
    
    def get_all_rules_summary(self) -> Dict[str, int]:
        """Devuelve un resumen del número de reglas por grupo."""
        summary = {}
        for rule in self.rules:
            for prefix in rule.code_prefixes:
                group = prefix[0] if len(prefix) > 0 else "?"
                group_name = {
                    "1": "Financiación básica",
                    "2": "Inmovilizado",
                    "3": "Existencias", 
                    "4": "Acreedores/Deudores",
                    "5": "Cuentas financieras",
                    "6": "Gastos",
                    "7": "Ingresos"
                }.get(group, "Otros")
                
                if group_name not in summary:
                    summary[group_name] = 0
                summary[group_name] += 1
                break
        
        return summary
