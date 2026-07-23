"""
bot_entrerios.py
===============================================================================
Scraper del Boletín Oficial de la Provincia de Entre Ríos.

Uso normal:
    python bot_entrerios.py 9 "https://www.entrerios.gov.ar/boletin/"

Modos de prueba (no tocan el backend):
    python bot_entrerios.py 9 --dry-run
    python bot_entrerios.py 9 --dry-run --pdf "23-07-26.pdf"
    python bot_entrerios.py 9 --dry-run --fecha 2026-07-23
    python bot_entrerios.py 9 --dry-run --todas        # muestra las individuales
    python bot_entrerios.py 9 --dry-run --volcar       # imprime el sumario y los
                                                       # bloques crudos del cuerpo

Entre Ríos es id_jurisdiccion = 9.

-------------------------------------------------------------------------------
DESCUBRIMIENTO
-------------------------------------------------------------------------------
Igual que Chubut: no hace falta scrapear la grilla del portal
(https://portal.entrerios.gov.ar/gobernacion/imprenta/pf/consulta/7948), porque
el PDF vive en una URL predecible armada con la fecha:

    https://www.entrerios.gov.ar/boletin/calendario/Boletin/2026/Julio/23-07-26.pdf
                                                    ^año  ^mes    ^DD-MM-AA

El mes va en castellano y capitalizado; el archivo es DD-MM-AA (dos dígitos de
año, con ceros adelante). El bot arranca en la fecha pedida (o la de hoy) y
retrocede días hábiles hasta encontrar el boletín más reciente.

Se prueban además algunas variantes defensivas (host `portal.` y mes sin
capitalizar) porque son gratis y evitan que un cambio menor de maqueta rompa
todo el bot.

-------------------------------------------------------------------------------
ESTRUCTURA DEL PDF
-------------------------------------------------------------------------------
Texto nativo, UNA sola columna (a diferencia de Córdoba y Chubut: acá no hay que
detectar el canal entre columnas). El boletín se divide en secciones y cada
página lo declara en su encabezado:

    Paraná, jueves 23 de julio de 2026   BOLETIN OFICIAL / Sección Administrativa   1
    2   BOLETIN OFICIAL / Sección Administrativa   Paraná, jueves 23 de julio de 2026

Sólo interesa la **Sección Administrativa** (decretos, resoluciones). Al llegar
a la primera página de otra sección — normalmente "Sección Comercial", que son
edictos judiciales, sucesorios, remates y asambleas — se corta.

Dentro de la Sección Administrativa hay dos partes:

  1. SUMARIO (primera página de la sección). Es el ORÁCULO del boletín: lista
     rubro (DECRETOS / RESOLUCIONES), organismo emisor, código y título de cada
     norma. De ahí salen el emisor y la síntesis, y contra esa lista se controla
     lo extraído del cuerpo.

         DECRETOS
         GOBERNACION ..................................................... 2
            DTO-2026-1811-E–GER-GOB
                RECHAZO RECURSO INTERPUESTO POR DELELISI, ALICIA DEL C. ... 2

  2. CUERPO. Cada norma abre con su código al principio de renglón, seguido del
     título en mayúsculas, el lugar y la fecha del acto:

         DTO-2026-1811-E–GER-GOB
         RECHAZO RECURSO INTERPUESTO POR DELELISI, ALICIA DEL C.
         PARANÁ, ENTRE RÍOS
         Viernes, 19 de Junio de 2026
         VISTO: ...

     y cierra con la firma y una línea de guiones ("------"). Ojo: ese separador
     NO aparece cuando la norma termina justo al pie de una página, así que el
     corte se hace por el código de la norma siguiente, no por los guiones.

-------------------------------------------------------------------------------
DOS TRAMPAS QUE COSTARON TIEMPO
-------------------------------------------------------------------------------
1. Los títulos están maquetados en "negrita falsa": el mismo texto dibujado dos
   veces con un offset mínimo. pdfplumber devuelve los caracteres duplicados
   ("RREECCHHAAZZOO RREECCUURRSSOO") y ningún patrón matchea. La solución es
   `page.dedupe_chars(tolerance=1)`, que descarta los glifos superpuestos.
   (pdftotext -layout no tiene el problema, pero no queremos depender de
   poppler para un PDF de texto.)

2. El guion del código es un EN DASH: "DTO-2026-1811-E–GER-GOB". Cualquier
   comparación literal tiene que normalizar –/—/‐ a "-" antes.

-------------------------------------------------------------------------------
url_norma
-------------------------------------------------------------------------------
Todas las normas viven en el mismo PDF, así que se usa la URL del boletín más un
fragmento único con el código (`...23-07-26.pdf#DTO-2026-1811`). Sin eso
ingresar_scraping.php deduplica por url_norma exacta y la primera norma
guardada bloquea a todas las demás del boletín.
===============================================================================
"""

import os
import re
import sys
import json
import time
import argparse
import unicodedata
from datetime import date, datetime, timedelta

import requests

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# En Windows la consola usa cp1252 y los print con acentos rompen.
for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8')
    except Exception:
        pass


# ===========================================================================
# CONFIGURACIÓN
# ===========================================================================
def get_env_clean(key, default=None):
    v = os.getenv(key, default)
    if v:
        v = v.strip().strip('"').strip("'")
    return v


API_KEY_BACKEND = get_env_clean('API_KEY_BACKEND', 'Token_Seguro_Scraper_2026_XyZ!')
URL_HISTORIAL = get_env_clean(
    'URL_HISTORIAL', 'http://localhost/lgc_sgmlo/backend/api/boletin/historial_scraping.php')
URL_GUARDAR_NORMAS = get_env_clean(
    'URL_GUARDAR_NORMAS', 'http://localhost/lgc_sgmlo/backend/api/boletin/ingresar_scraping.php')

# Base del calendario de PDFs. El host `www` es el que sirve el archivo; `portal`
# queda como respaldo porque ambos apuntan al mismo sitio.
BASES_PDF = [
    'https://www.entrerios.gov.ar/boletin/calendario/Boletin/',
    'https://portal.entrerios.gov.ar/boletin/calendario/Boletin/',
]

HEADERS_WEB = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'application/pdf,text/html;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
}

DIAS_ATRAS_MAX = 12        # días hábiles a retroceder buscando el último boletín
REINTENTOS = 3
ESPERA_REINTENTO = 3
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

MESES_NUM = {m.lower(): i + 1 for i, m in enumerate(MESES)}
MESES_NUM['setiembre'] = 9


# ===========================================================================
# NORMALIZACIÓN Y PATRONES
# ===========================================================================
# El PDF mezcla guion común, en dash y em dash dentro del mismo código.
GUIONES = {ord('–'): '-', ord('—'): '-', ord('‐'): '-', ord('‑'): '-', ord('−'): '-'}


def _guiones(texto):
    return (texto or '').translate(GUIONES)


def _sin_acentos(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s or '')
                   if unicodedata.category(c) != 'Mn')


def _compacto(texto):
    return re.sub(r'\s+', ' ', (texto or '')).strip()


# Encabezado de página: sirve para (a) tirarlo a la basura y (b) saber en qué
# sección estamos. Las páginas pares lo escriben al revés que las impares, y en
# la Sección Comercial a veces sale "BOLETIN OFICIAL" pelado, sin sección.
RE_ENCABEZADO = re.compile(
    r'BOLET[IÍ]N\s+OFICIAL(?:\s*/\s*Secci[óo]n\s+(?P<seccion>[A-Za-zÁÉÍÓÚáéíóúÑñ]+))?',
    re.IGNORECASE)

RE_PIE = re.compile(r'^(?:Powered by TCPDF|\d+\s*/\s*\d+)\s*$', re.IGNORECASE)

# Línea del sumario con línea de puntos y número de página al final.
RE_PUNTEADO = re.compile(r'^(?P<texto>.*?)\s*\.{3,}\s*(?P<pagina>\d{1,4})\s*$')

# Separador entre normas en el cuerpo.
RE_SEPARADOR = re.compile(r'^-{3,}$')

# Metadatos de la tapa.
RE_NRO_BOLETIN = re.compile(r'Nro\.?\s*([\d\.]+)\s*-\s*([\d/]+)', re.IGNORECASE)
RE_FECHA_LARGA = re.compile(
    r'(?:\w+,\s*)?(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+de\s+(\d{4})', re.IGNORECASE)

# --- Códigos de norma -------------------------------------------------------
# Formato GDE (el habitual desde 2019): PREFIJO-AAAA-NNNN-E–GER-ORGANISMO
#     DTO-2026-1811-E–GER-GOB
#     RESOL-2026-399-E–GER-SAMB#MDE
RE_COD_GDE = re.compile(
    r'^(?P<pref>[A-ZÁÉÍÓÚÑ]{2,12})-(?P<anio>(?:19|20)\d{2})-(?P<num>\d{1,6})(?P<resto>\b.*)$')

# Formato clásico, todavía usado por organismos que no están en GDE:
#     RESOLUCIÓN N° 352 PCMER
#     LEY N° 11.227
#     DECRETO Nº 2968 MGJ
RE_COD_CLASICO = re.compile(
    r'^(?P<tipo>LEY|DECRETO\s+SINTETIZADO|DECRETO|RESOLUCI[ÓO]N\s+GENERAL|'
    r'RESOLUCI[ÓO]N\s+CONJUNTA|RESOLUCI[ÓO]N|DISPOSICI[ÓO]N|ACUERDO|ACORDADA|'
    r'CIRCULAR|COMUNICACI[ÓO]N|CONVENIO|ACTA)\s*'
    r'(?:N[°ºro]*\.?\s*)?(?P<num>\d{1,6}(?:\.\d{3})*)'
    r'(?:\s*/\s*(?P<anio>\d{2,4}))?(?P<resto>.*)$', re.IGNORECASE)

# Prefijos GDE conocidos -> tipo de norma que espera el backend.
PREFIJOS_TIPO = {
    'DTO': 'DECRETO', 'DECTO': 'DECRETO', 'DECRE': 'DECRETO', 'DEC': 'DECRETO',
    'DECSI': 'DECRETO SINTETIZADO',
    'RESOL': 'RESOLUCION', 'RES': 'RESOLUCION', 'RSL': 'RESOLUCION',
    'RESGE': 'RESOLUCION GENERAL', 'RESFC': 'RESOLUCION CONJUNTA',
    'DISPO': 'DISPOSICION', 'DISP': 'DISPOSICION',
    'LEY': 'LEY', 'ACUER': 'ACUERDO', 'ACORD': 'ACORDADA', 'ACTA': 'ACTA',
    'CIRC': 'CIRCULAR', 'CONVE': 'CONVENIO', 'CONV': 'CONVENIO',
    'DECAD': 'DECISION ADMINISTRATIVA', 'INSTR': 'INSTRUCCION',
}

# Rubros del sumario ("DECRETOS", "RESOLUCIONES"): son el respaldo del tipo
# cuando el prefijo del código no está en la tabla de arriba.
RUBRO_TIPO = {
    'DECRETOS': 'DECRETO', 'DECRETOS SINTETIZADOS': 'DECRETO SINTETIZADO',
    'RESOLUCIONES': 'RESOLUCION', 'RESOLUCIONES GENERALES': 'RESOLUCION GENERAL',
    'DISPOSICIONES': 'DISPOSICION', 'LEYES': 'LEY', 'ACUERDOS': 'ACUERDO',
    'ACORDADAS': 'ACORDADA', 'CIRCULARES': 'CIRCULAR', 'CONVENIOS': 'CONVENIO',
    'ACTAS': 'ACTA', 'RESOLUCIONES CONJUNTAS': 'RESOLUCION CONJUNTA',
    'DECISIONES ADMINISTRATIVAS': 'DECISION ADMINISTRATIVA',
}

# Fin del sumario administrativo: lo que sigue ya es el índice de otra sección.
RE_OTRA_SECCION = re.compile(
    r'^\s*SECCI[ÓO]N\s+(COMERCIAL|JUDICIAL|GENERAL|LEGISLATIVA)\s*$', re.IGNORECASE)

# Encabezado de organismo en el CUERPO. Va suelto entre dos normas, así que sin
# esto queda pegado al final de la norma anterior ("...Rosa Mirta Hojman CONSEJO
# DE LA MAGISTRATURA DE ENTRE RIOS"). Se recorta sólo si tiene forma de
# organismo: un all-caps a secas no alcanza, porque las firmas también lo son
# ("ROGELIO FRIGERIO") y no hay que borrarlas del texto.
RE_ORGANISMO = re.compile(
    r'^(?:MINISTERIO|SECRETAR[ÍI]A|SECRETARIA|CONSEJO|DIRECCI[ÓO]N|INSTITUTO|TRIBUNAL|'
    r'FISCAL[ÍI]A|CAJA|PODER|GOBERNACI[ÓO]N|GOBERNACION|SUPERIOR|CONTADUR[ÍI]A|'
    r'POLIC[ÍI]A|COMISI[ÓO]N|COORDINACI[ÓO]N|UNIDAD|AGENCIA|ADMINISTRADORA|ENTE|'
    r'BANCO|HOSPITAL|JUNTA|VIALIDAD|DEFENSOR)\b[A-ZÁÉÍÓÚÑ0-9 .,ºª()#/&-]*$')


def _limpiar_numero(num):
    """
    '11.227' -> '11227', '01' -> '1'. El backend guarda numero como texto y
    deduplica por tipo|numero|anio|emisor, así que 'RESOLUCION Nº 01/26' y
    'RESOLUCION N° 1/26' tienen que dar la misma clave.
    """
    limpio = re.sub(r'\.', '', (num or '').strip())
    limpio = limpio.lstrip('0') or ('0' if limpio else '')
    return limpio or 'S/N'


def _normalizar_tipo(texto):
    t = _sin_acentos(_compacto(texto)).upper()
    t = t.replace('RESOLUCION GRAL', 'RESOLUCION GENERAL')
    return t


def parsear_codigo(linea, anio_boletin=None, rubro=None):
    """
    Reconoce el código que abre una norma.

    Devuelve dict(codigo, tipo, numero, anio, organismo_codigo) o None.
    `organismo_codigo` es la cola del código GDE ("GER-GOB", "GER-SAMB#MDE"):
    no se usa como emisor (para eso está el sumario) pero sirve para depurar.
    """
    texto = _compacto(_guiones(linea))
    if not texto or len(texto) > 90:
        return None

    m = RE_COD_GDE.match(texto)
    if m:
        pref = m.group('pref').upper()
        resto = m.group('resto').strip()
        # La cola tiene que ser corta y sin prosa: si el "código" viene seguido
        # de una oración es una cita dentro del cuerpo, no el arranque de una
        # norma ("...conforme DTO-2026-1811 de fecha...").
        if not re.fullmatch(r'[-A-Z0-9#/.º°\s]{0,45}', resto, re.IGNORECASE):
            return None
        tipo = PREFIJOS_TIPO.get(pref) or RUBRO_TIPO.get((rubro or '').upper())
        if not tipo:
            # Prefijo desconocido: mejor un tipo razonable que crear basura en
            # la tabla tipo_norma.
            tipo = ('RESOLUCION' if pref.startswith('RES')
                    else 'DECRETO' if pref.startswith('DE')
                    else 'DISPOSICION' if pref.startswith('DIS')
                    else pref)
        return {
            'codigo': texto,
            'tipo': _normalizar_tipo(tipo),
            'numero': m.group('num').lstrip('0') or '0',
            'anio': m.group('anio'),
            'organismo_codigo': resto.lstrip('-').strip(),
        }

    m = RE_COD_CLASICO.match(texto)
    if m:
        resto = m.group('resto').strip()
        if not re.fullmatch(r'[-A-Z0-9#/.º°\s]{0,45}', resto, re.IGNORECASE):
            return None
        anio = m.group('anio')
        if anio and len(anio) == 2:
            anio = ('20' if int(anio) < 70 else '19') + anio
        return {
            'codigo': texto,
            'tipo': _normalizar_tipo(m.group('tipo')),
            'numero': _limpiar_numero(m.group('num')),
            'anio': anio or (str(anio_boletin) if anio_boletin else None),
            'organismo_codigo': resto,
        }
    return None


def clave_norma(n):
    """Clave para cruzar sumario y cuerpo."""
    return (_normalizar_tipo(n.get('tipo')), str(n.get('numero')), str(n.get('anio')))


# ===========================================================================
# CLASIFICACIÓN: ACTO GENERAL vs INDIVIDUAL
# ---------------------------------------------------------------------------
# Mismo criterio que Catamarca, Chaco y Chubut: el boletín mezcla normativa de
# alcance general con actos que afectan a una persona determinada. Esos no son
# normativa de interés y además arrastran datos personales (DNI, domicilio,
# correo), así que se descartan del envío.
#
# En Entre Ríos hay una ventaja: el TÍTULO del sumario es texto limpio, corto y
# describe el acto ("RECHAZO RECURSO INTERPUESTO POR DELELISI, ALICIA DEL C.",
# "TRANSFERENCIA DE BIENES A COMUNA ARROYO CORRALITO"). Es el equivalente al
# campo `Referencia:` de los decretos de Chaco, que resultó ser la mejor señal.
# Por eso el título puntúa aparte y con más peso que el cuerpo.
#
# OJO: en la edición del 23/07/2026 diez de las doce normas son recursos de
# apelación jerárquica de jubilados, o sea actos individuales. Es una edición
# atípicamente pobre; conviene revisar el criterio con dos o tres boletines más
# antes de darlo por bueno (ver --todas).
# ===========================================================================
UMBRAL_INDIVIDUAL = 3

# Patrones sobre el TÍTULO del sumario (peso completo).
PATRONES_TITULO_INDIVIDUAL = [
    (r'RECURSO\s+INTERPUESTO\s+POR',            4, 'recurso de un particular'),
    (r'\bRECHAZO\s+RECURSO\b',                  3, 'rechazo de recurso'),
    (r'DEJA\s+SIN\s+EFECTO\s+FUNCIONES',        4, 'cese de funciones'),
    (r'\bDESIGNACI[ÓO]N\b|\bDESIGNA\b',         4, 'designación'),
    (r'\bASIGNACI[ÓO]N\s+DE\s+FUNCIONES\b',     4, 'asignación de funciones'),
    (r'\bRENUNCIA\b',                           4, 'renuncia'),
    (r'\bJUBILACI[ÓO]N\b|\bRETIRO\b',           4, 'jubilación / retiro'),
    (r'\bCESANT[ÍI]A\b|\bEXONERACI[ÓO]N\b',     4, 'cesantía / exoneración'),
    (r'\bLICENCIA\b',                           3, 'licencia'),
    (r'\bTRASLADO\b|\bPERMUTA\b',               3, 'traslado / permuta'),
    (r'\bSUBROGANCIA\b|\bSUPLENCIA\b',          4, 'subrogancia'),
    # Sumario administrativo: el título puede abrirlo ("INICIO SUMARIO A X") o
    # cerrarlo ("FINALIZA SUMARIO DE X"), y en ambos casos es un procedimiento
    # disciplinario contra un agente con nombre y apellido.
    (r'\bSUMARIO\b',                            4, 'sumario administrativo'),
    # "TRANSFERENCIA DE MILANO, SONIA V." es un pase de agente; "TRANSFERENCIA
    # DE BIENES A COMUNA ARROYO CORRALITO" es patrimonial. Lo que las separa es
    # la coma del "APELLIDO, Nombre" pegada al sustantivo transferido.
    (r'\bTRANSFERENCIA\s+DE\s+[A-ZÁÉÍÓÚÑ]{3,}\s*,', 4, 'transferencia de un agente'),
    # Excepciones a la Ley 7413 (incompatibilidad de cargos): siempre a nombre
    # de un agente puntual.
    (r'\bEXCEPCI[ÓO]N\b',                       3, 'excepción a título personal'),
    # "RECONOCIMIENTO DE PAGO" no nombra a nadie en el título, pero en el cuerpo
    # siempre hay un beneficiario único con DNI.
    (r'\bRECONOCIMIENTO\s+DE\s+(?:PAGO|SERVICIOS|HABERES)\b', 3, 'reconocimiento de pago'),
    (r'\bSUSPENSI[ÓO]N\b.*\bA\b\s+[A-ZÁÉÍÓÚÑ]', 3, 'suspensión a una persona'),
    (r'\bAPERCIBIMIENTO\b|\bSANCI[ÓO]N\s+A\b',  3, 'sanción'),
    (r'\bASCENSO\b|\bPROMOCI[ÓO]N\s+DE\b',      3, 'ascenso'),
    (r'\bADSCRIPCI[ÓO]N\b|\bCOMISI[ÓO]N\s+DE\s+SERVICIO', 3, 'adscripción'),
    (r'\bRECONOCIMIENTO\s+DE\s+SERVICIOS\b',    3, 'reconocimiento de servicios'),
    # "APELLIDO, NOMBRE" en el título: casi siempre es un acto sobre esa
    # persona. Suma pero no alcanza sola, igual que el DNI.
    (r'\b[A-ZÁÉÍÓÚÑ]{4,},\s*[A-ZÁÉÍÓÚÑ]',       2, 'nombra a una persona'),
]

PATRONES_TITULO_GENERAL = [
    (r'\bLICITACI[ÓO]N\b|\bCONCURSO\s+DE\s+PRECIOS\b', -4, 'licitación'),
    (r'\bCONCURSOS?\s+P[ÚU]BLICOS?\b',                 -4, 'concurso público'),
    (r'\bREGLAMENT|\bESTRUCTURA\s+ORG[ÁA]NICA\b',      -4, 'reglamento / estructura'),
    (r'\bPRESUPUESTO\b|\bPARTIDA\b',                   -3, 'presupuesto'),
    (r'\bEMERGENCIA\b|\bPR[ÓO]RROGA\s+DE\s+(?:LA\s+)?EMERGENCIA', -4, 'emergencia'),
    (r'\bCONVENIO\b|\bADDENDA\b|\bACTA\s+ACUERDO\b',   -3, 'convenio'),
    (r'\bTRANSFERENCIA\s+DE\s+BIENES\b',               -3, 'transferencia patrimonial'),
    (r'\bDECLARA\s+DE\s+INTER[ÉE]S\b|\bINTER[ÉE]S\s+PROVINCIAL\b', -3, 'declaración de interés'),
    (r'\bCREA(?:CI[ÓO]N)?\b|\bMODIFICA\b|\bDEROGA\b',  -3, 'crea / modifica normativa'),
    (r'\bPROMULGA\b|\bVETO\b',                         -4, 'promulgación'),
    (r'\bADHESI[ÓO]N\b|\bADHIERE\b',                   -3, 'adhesión'),
    (r'\bESCALA\s+SALARIAL\b|\bAUMENTO\b|\bRECOMPOSICI[ÓO]N\b', -3, 'salarial general'),
    (r'\bCALENDARIO\b|\bASUETO\b|\bFERIADO\b',         -3, 'calendario / asueto'),
    (r'\bTARIFA|\bCANON\b|\bARANCEL',                  -3, 'tarifas'),
]

# Patrones sobre el CUERPO (media ponderación: el articulado repite fórmulas).
PATRONES_CUERPO_INDIVIDUAL = [
    (r'D[ée]j[ae]se\s+sin\s+efecto[\s\S]{0,80}(?:designaci|funciones)', 2, 'cese de designación'),
    (r'Des[ií]gn[ae]se[\s\S]{0,80}(?:en el cargo|como|para)',           2, 'designación'),
    (r'Ac[ée]pt[ae]se\s+la\s+renuncia',                                 2, 'renuncia'),
    (r'Otórg[au]se[\s\S]{0,60}licencia',                                2, 'licencia'),
    (r'\bRech[áa]zase\s+el\s+Recurso\b',                                2, 'rechazo de recurso'),
    (r'\bRecurso\s+de\s+Apelaci[óo]n\s+Jer[áa]rquica\b',                2, 'apelación jerárquica'),
    (r'\bhaber\s+jubilatorio\b|\breajuste\s+de\s+su\s+haber\b',         2, 'reclamo previsional'),
    (r'\bCesant[íi]a\b|\bExoneraci[óo]n\b',                             2, 'cesantía'),
]

PATRONES_CUERPO_GENERAL = [
    (r'Apru[ée]b[ae]se\s+(?:el\s+)?(?:Reglamento|Pliego|Convenio|Estructura)', -3, 'aprobación normativa'),
    (r'Prom[úu]lg', -3, 'promulgación'),
    (r'Decl[áa]rase\s+de\s+(?:inter[ée]s|utilidad)', -3, 'declaración de interés'),
    (r'Autor[íi]z[ae]se[\s\S]{0,60}(?:llamado|licitaci)', -3, 'licitación'),
    (r'Modif[íi]c[ae]se[\s\S]{0,60}(?:Decreto|Ley|Resoluci)', -2, 'modificación normativa'),
]

RE_DOCUMENTO = re.compile(r'\b(?:D\.?N\.?I|CUIL|CUIT|L\.?[CE]\.?|M\.?I\.?)\b[\s.:Nnºo°]*\d',
                          re.IGNORECASE)


def clasificar_norma(titulo, texto):
    """Devuelve (es_individual, puntaje, motivos)."""
    puntaje, motivos = 0, []
    tit = _compacto(titulo or '')
    cuerpo = texto or ''

    for patron, peso, etiqueta in PATRONES_TITULO_INDIVIDUAL:
        if re.search(patron, tit, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'+{peso} título: {etiqueta}')
    for patron, peso, etiqueta in PATRONES_TITULO_GENERAL:
        if re.search(patron, tit, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'{peso} título: {etiqueta}')
    for patron, peso, etiqueta in PATRONES_CUERPO_INDIVIDUAL:
        if re.search(patron, cuerpo, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'+{peso} cuerpo: {etiqueta}')
    for patron, peso, etiqueta in PATRONES_CUERPO_GENERAL:
        if re.search(patron, cuerpo, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'{peso} cuerpo: {etiqueta}')

    # Mencionar un documento suma, pero no decide solo: los decretos generales
    # también citan el DNI del funcionario que firma un convenio.
    docs = len(RE_DOCUMENTO.findall(cuerpo))
    if docs:
        puntaje += 1
        motivos.append(f'+1 menciona DNI/CUIL/CUIT ({docs})')

    return (puntaje >= UMBRAL_INDIVIDUAL), puntaje, motivos


# ===========================================================================
# LECTURA DEL PDF
# ===========================================================================
def leer_paginas(ruta_pdf):
    """
    Devuelve (paginas, tapa) donde `paginas` es la lista de páginas de la
    Sección Administrativa ya sin encabezados ni pies, cada una como lista de
    líneas, y `tapa` es el texto de la portada (para los metadatos).

    Se corta en la primera página que declare otra sección. Cuando el
    encabezado no nombra ninguna (pasa en la Sección Comercial) se hereda la
    anterior, así que el corte no se pierde por una página mal maquetada.
    """
    if pdfplumber is None:
        raise RuntimeError("Falta pdfplumber: pip install pdfplumber")

    paginas, tapa = [], ''
    seccion = None

    with pdfplumber.open(ruta_pdf) as pdf:
        for i, pagina in enumerate(pdf.pages):
            # dedupe_chars deshace la "negrita falsa" de los títulos, que si no
            # salen con todos los caracteres duplicados.
            try:
                plano = pagina.dedupe_chars(tolerance=1)
            except Exception:
                plano = pagina
            texto = plano.extract_text() or ''
            lineas = [l.rstrip() for l in texto.split('\n')]
            lineas = [l for l in lineas if not RE_PIE.match(l.strip())]
            if not lineas:
                continue

            m = RE_ENCABEZADO.search(lineas[0])
            if m:
                nombre = m.group('seccion')
                if nombre:
                    seccion = _sin_acentos(nombre).lower()
                lineas = lineas[1:]          # el encabezado no es contenido
            elif seccion is None:
                # Todavía no empezó ninguna sección: es la tapa.
                tapa = texto
                continue

            if seccion and seccion != 'administrativa':
                break                        # arrancó la Comercial: se termina

            paginas.append(lineas)

    return paginas, tapa


def metadatos_boletin(tapa, paginas):
    """(numero_boletin, fecha_iso) leídos de la tapa; si falla, del encabezado."""
    numero, fecha = None, None
    fuentes = [tapa] + ['\n'.join(p[:3]) for p in paginas[:2]]

    for fuente in fuentes:
        if not fuente:
            continue
        if not numero:
            m = RE_NRO_BOLETIN.search(fuente)
            if m:
                numero = f"{m.group(1)} - {m.group(2)}"
        if not fecha:
            m = RE_FECHA_LARGA.search(fuente)
            if m:
                mes = MESES_NUM.get(_sin_acentos(m.group(2)).lower())
                if mes:
                    fecha = f"{int(m.group(3)):04d}-{mes:02d}-{int(m.group(1)):02d}"
        if numero and fecha:
            break
    return numero, fecha


def separar_sumario(paginas):
    """
    Parte las páginas administrativas en (páginas de sumario, páginas de cuerpo).

    Una página es del sumario si tiene varias líneas con puntos suspensivos y
    número de página al final. Se clasifica por contenido y no por posición para
    aguantar sumarios de más de una página (los boletines grandes los tienen).
    """
    sumario, cuerpo, en_sumario = [], [], True
    for pagina in paginas:
        punteadas = sum(1 for l in pagina if RE_PUNTEADO.match(l.strip()))
        if en_sumario and punteadas >= 3:
            sumario.append(pagina)
        else:
            en_sumario = False
            cuerpo.append(pagina)
    return sumario, cuerpo


def leer_sumario(paginas_sumario, anio_boletin=None):
    """
    Convierte el sumario en la lista de normas anunciadas.

    Estructura (tres niveles, se distinguen por la forma de la línea):
        DECRETOS                            -> rubro    (sin puntos, sin página)
        GOBERNACION ................... 2   -> emisor   (con puntos)
        DTO-2026-1811-E–GER-GOB             -> código
            RECHAZO RECURSO ......... 2     -> título   (con puntos)
    """
    normas = []
    rubro, emisor = None, None
    pendiente, titulo_parcial = None, []

    for pagina in paginas_sumario:
        for cruda in pagina:
            linea = _compacto(cruda)
            if not linea or linea.upper() == 'SUMARIO':
                continue
            if RE_OTRA_SECCION.match(linea):
                pendiente = None
                return normas            # el índice administrativo terminó

            cod = parsear_codigo(linea, anio_boletin, rubro)
            if cod:
                pendiente, titulo_parcial = cod, []
                continue

            m = RE_PUNTEADO.match(linea)
            if m:
                texto = _compacto(m.group('texto'))
                if pendiente:
                    titulo = _compacto(' '.join(titulo_parcial + [texto]))
                    pendiente.update({
                        'titulo': titulo.rstrip('. '),
                        'pagina': int(m.group('pagina')),
                        'emisor': emisor,
                        'rubro': rubro,
                    })
                    normas.append(pendiente)
                    pendiente, titulo_parcial = None, []
                else:
                    # Línea con puntos sin código pendiente = organismo emisor.
                    emisor = texto.rstrip('. ')
                continue

            # Línea suelta: o es un rubro, o es la primera mitad de un título
            # largo que sigue en el renglón siguiente.
            if pendiente:
                titulo_parcial.append(linea)
            elif linea.upper() in RUBRO_TIPO or (linea.isupper() and len(linea) <= 45):
                rubro = linea.upper()

    return normas


def _limpiar_lineas_cuerpo(paginas_cuerpo):
    """Aplana las páginas del cuerpo en una sola lista de líneas."""
    lineas = []
    for pagina in paginas_cuerpo:
        for l in pagina:
            lineas.append(l)
    return lineas


def extraer_normas(paginas_cuerpo, esperadas, fecha_boletin=None, anio_boletin=None):
    """
    Corta el cuerpo en bloques, uno por norma.

    El corte se hace por el código que abre cada norma, NO por la línea de
    guiones: ese separador falta cuando la norma termina justo al pie de una
    página (pasa con el DTO-2026-1816 en la edición 133/26).

    Los códigos anunciados en el sumario se aceptan siempre; los que no están
    anunciados se aceptan igual si tienen forma de código válido (para no
    perder una norma en silencio si el sumario viene incompleto), pero quedan
    marcados como `anunciada=False`.
    """
    lineas = _limpiar_lineas_cuerpo(paginas_cuerpo)
    codigos_sumario = {_compacto(_guiones(n['codigo'])).upper() for n in esperadas}
    emisores_sumario = {_sin_acentos(_compacto(n.get('emisor') or '')).upper()
                        for n in esperadas if n.get('emisor')}
    por_clave = {clave_norma(n): n for n in esperadas}

    def _recortar_organismo(bloque):
        """
        Saca del final del bloque anterior las líneas de encabezado de organismo
        que en realidad pertenecen a la norma que empieza. Devuelve el texto del
        encabezado, que sirve de emisor de respaldo si el sumario no trae esa
        norma.
        """
        recortadas = []
        while bloque and bloque['lineas'] and len(recortadas) < 3:
            ultima = _compacto(bloque['lineas'][-1])
            if not ultima:
                bloque['lineas'].pop()
                continue
            plana = _sin_acentos(ultima).upper()
            if plana in emisores_sumario or (len(ultima) <= 70 and ultima.isupper()
                                             and RE_ORGANISMO.match(plana)):
                recortadas.insert(0, bloque['lineas'].pop())
            else:
                break
        return _compacto(' '.join(recortadas))

    bloques, actual, rubro = [], None, None
    for cruda in lineas:
        linea = _compacto(cruda)
        if not linea:
            if actual:
                actual['lineas'].append('')
            continue

        if RE_SEPARADOR.match(linea):
            continue

        cod = parsear_codigo(linea, anio_boletin, rubro)
        if cod:
            anunciada = _compacto(_guiones(cod['codigo'])).upper() in codigos_sumario
            if anunciada or not actual or len(actual['lineas']) > 3:
                cod.update({'anunciada': anunciada, 'rubro': rubro, 'lineas': [],
                            'emisor_cuerpo': _recortar_organismo(actual)})
                bloques.append(cod)
                actual = cod
                continue

        # Banner de rubro entre grupos de normas ("DECRETOS", "RESOLUCIONES").
        if linea.upper() in RUBRO_TIPO and (actual is None or len(actual['lineas']) > 3):
            rubro = linea.upper()
            continue

        if actual:
            actual['lineas'].append(linea)

    normas = []
    for b in bloques:
        cuerpo = _compacto(' '.join(b['lineas']))
        # La primera línea del bloque es el título en mayúsculas; el sumario da
        # la versión limpia, así que sólo se usa como respaldo.
        titulo_cuerpo = _compacto(b['lineas'][0]) if b['lineas'] else ''
        anunciada = por_clave.get(clave_norma(b))
        titulo = (anunciada or {}).get('titulo') or titulo_cuerpo
        emisor = (anunciada or {}).get('emisor') or b.get('emisor_cuerpo') or None

        individual, puntaje, motivos = clasificar_norma(titulo, cuerpo)
        normas.append({
            'codigo': b['codigo'],
            'tipo': b['tipo'],
            'numero': b['numero'],
            'anio': b['anio'] or anio_boletin,
            'emisor': emisor,
            'organismo_codigo': b.get('organismo_codigo'),
            'rubro': b.get('rubro'),
            'titulo': titulo,
            'texto_completo': cuerpo,
            'fecha_publicacion': fecha_boletin,
            'anunciada': b['anunciada'],
            'es_individual': individual,
            'puntaje': puntaje,
            'motivos': motivos,
        })
    return normas


def comparar_con_sumario(esperadas, normas):
    """(faltantes, sobrantes) para el control de cobertura."""
    extraidas = {clave_norma(n) for n in normas}
    faltantes = [e for e in esperadas if clave_norma(e) not in extraidas]
    anunciadas = {clave_norma(e) for e in esperadas}
    sobrantes = [n for n in normas if clave_norma(n) not in anunciadas]
    return faltantes, sobrantes


# ===========================================================================
# DESCUBRIMIENTO DEL BOLETÍN
# ===========================================================================
_SESION = None


def sesion():
    global _SESION
    if _SESION is None:
        _SESION = requests.Session()
        _SESION.headers.update(HEADERS_WEB)
    return _SESION


def urls_candidatas(dia):
    """
    Variantes de URL para una fecha. La forma confirmada es
        .../Boletin/2026/Julio/23-07-26.pdf
    o sea año completo / mes capitalizado en castellano / DD-MM-AA con ceros.
    El resto son respaldos baratos por si cambia un detalle de la maqueta.
    """
    mes = MESES[dia.month - 1]
    nombres = [mes]
    if mes == 'Septiembre':
        nombres.append('Setiembre')
    nombres.append(mes.lower())

    archivos = [f'{dia.day:02d}-{dia.month:02d}-{dia:%y}.pdf',
                f'{dia.day:02d}-{dia.month:02d}-{dia.year}.pdf']

    urls = []
    for base in BASES_PDF:
        for nombre in dict.fromkeys(nombres):
            for archivo in dict.fromkeys(archivos):
                urls.append(f'{base}{dia.year}/{nombre}/{archivo}')
    return urls


def descargar_pdf(url, timeout=90):
    """Descarga si existe y es un PDF. Devuelve bytes o None."""
    for intento in range(1, REINTENTOS + 1):
        try:
            r = sesion().get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            if r.status_code == 200 and r.content[:5] == b'%PDF-':
                return r.content
            if r.status_code == 200:
                return None          # respondió algo que no es PDF (404 disfrazado)
            if r.status_code < 500:
                return None
        except requests.RequestException as e:
            if intento == REINTENTOS:
                raise RuntimeError(f"Error de red pidiendo {url}: {e}")
        time.sleep(ESPERA_REINTENTO * intento)
    return None


def buscar_boletin(desde=None, dias=DIAS_ATRAS_MAX):
    """
    Busca el boletín más reciente retrocediendo desde `desde` (o hoy).
    Devuelve (contenido_pdf, url, fecha) o (None, None, None).
    """
    dia = desde or date.today()
    revisados = 0
    while revisados < dias:
        if dia.weekday() < 5:          # publica de lunes a viernes
            # Las variantes de nombre se prueban completas sólo en los dos
            # primeros días hábiles: alcanza para detectar un cambio de maqueta
            # sin disparar 12 pedidos por cada día que se retrocede (retroceder
            # es lo normal después de un feriado, no una anomalía).
            urls = urls_candidatas(dia)
            if revisados >= 2:
                urls = urls[:1]
            for url in urls:
                contenido = descargar_pdf(url)
                if contenido:
                    return contenido, url, dia
            revisados += 1
        dia -= timedelta(days=1)
    return None, None, None


# ===========================================================================
# BACKEND
# ===========================================================================
def salida(status, message, total=None, extra=None):
    out = {"status": status, "message": message}
    if total is not None:
        out["total_enviadas"] = total
    if extra:
        out.update(extra)
    print(json.dumps(out))
    sys.exit(0)


def verificar_boletin_procesado(id_jurisdiccion, fecha_boletin):
    try:
        r = requests.post(URL_HISTORIAL,
                          json={"id_jurisdiccion": id_jurisdiccion,
                                "fecha_boletin": fecha_boletin, "accion": "verificar"},
                          headers={"Authorization": f"Bearer {API_KEY_BACKEND}"}, timeout=10)
        return r.json().get('procesado', False)
    except Exception:
        return False


def registrar_boletin_procesado(id_jurisdiccion, fecha_boletin, cantidad):
    try:
        requests.post(URL_HISTORIAL,
                      json={"id_jurisdiccion": id_jurisdiccion, "fecha_boletin": fecha_boletin,
                            "accion": "registrar", "cantidad_normas": cantidad},
                      headers={"Authorization": f"Bearer {API_KEY_BACKEND}"}, timeout=10)
    except Exception:
        pass


def guardar_debug(contenido, nombre):
    try:
        with open(nombre, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"Guardado {nombre} para depuración", file=sys.stderr)
    except Exception as e:
        print(f"No se pudo guardar {nombre}: {e}", file=sys.stderr)


def emisor_final(norma, usar_organismo=False):
    """
    Emisor que se manda al backend.

    Los decretos los firma el Gobernador: el organismo que figura en el sumario
    ("GOBERNACION", "SALUD") es el área que instruyó el trámite, no quien dicta.
    Como el backend deduplica por tipo|numero|anio|emisor y los decretos llevan
    numeración provincial única, mandarlos todos como PODER EJECUTIVO evita que
    el mismo decreto entre dos veces con emisores distintos.

    Con --emisor-organismo se usa el encabezado del sumario tal cual, por si
    después se prefiere ese criterio.
    """
    tipo = str(norma.get('tipo') or '')
    organismo = _compacto(norma.get('emisor') or '')
    if usar_organismo and organismo:
        return organismo
    if tipo.startswith('LEY'):
        return 'PODER LEGISLATIVO'
    if tipo.startswith('DECRETO'):
        return 'PODER EJECUTIVO'
    return organismo or 'PODER EJECUTIVO'


def construir_sintesis(norma):
    cuerpo = _compacto(norma.get('titulo') or norma.get('texto_completo') or '')
    cuerpo = cuerpo.strip(' .-:')
    if len(cuerpo) > MAX_SINTESIS:
        cuerpo = cuerpo[:MAX_SINTESIS].rsplit(' ', 1)[0] + '…'
    return cuerpo or f"{norma.get('tipo')} {norma.get('numero')}"


def recortar_texto(texto, tope=MAX_TEXTO_COMPLETO):
    """
    Recorta conservando el principio Y EL FINAL.

    Los decretos de Entre Ríos son largos (siete de los doce de la edición
    133/26 miden más de 20.000 caracteres) y el VISTO + CONSIDERANDO se lleva
    casi todo: el articulado, que es lo que dice qué resuelve la norma, va al
    final. Truncar desde el principio le manda al backend justo la parte que no
    sirve para categorizar, así que se guarda la cabecera (título, visto,
    arranque de los considerandos) y la cola (los ARTÍCULOS y la firma).
    """
    texto = texto or ''
    if len(texto) <= tope:
        return texto
    marca = ' […] '
    cabeza = int((tope - len(marca)) * 0.55)
    cola = tope - len(marca) - cabeza
    return texto[:cabeza] + marca + texto[-cola:]


def url_norma(url_pdf, norma):
    """
    Entre Ríos no publica una URL por norma (todas viven en el mismo PDF), así
    que se usa la URL del boletín más un fragmento único con el código. Es
    necesario porque ingresar_scraping.php deduplica por url_norma EXACTA: sin
    el fragmento, la primera norma guardada bloquearía a todas las demás.
    """
    base = f"{norma.get('tipo')}-{norma.get('numero')}-{norma.get('anio')}"
    slug = re.sub(r'[^A-Za-z0-9]+', '-', _guiones(base)).strip('-')
    return f"{url_pdf}#{slug}"


# ===========================================================================
# EJECUCIÓN
# ===========================================================================
def _main():
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Entre Ríos.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?',
                    default='https://portal.entrerios.gov.ar/gobernacion/imprenta/')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--pdf', metavar='ARCHIVO', help='usar un PDF local (pruebas)')
    ap.add_argument('--fecha', metavar='AAAA-MM-DD', help='buscar el boletín de esta fecha')
    ap.add_argument('--todas', action='store_true',
                    help='mostrar también las normas clasificadas como individuales')
    ap.add_argument('--sin-filtro', action='store_true',
                    help='enviar TODAS las normas, sin descartar los actos individuales')
    ap.add_argument('--emisor-organismo', action='store_true',
                    help='usar el organismo del sumario como emisor también en los '
                         'decretos (por defecto van como PODER EJECUTIVO)')
    ap.add_argument('--volcar', action='store_true',
                    help='imprimir el sumario y los bloques detectados, y salir')
    args = ap.parse_args()

    ruta_temporal = None
    url_pdf = args.pdf or ''
    fecha_boletin = None

    # 1. Conseguir el PDF
    if args.pdf:
        ruta_pdf = args.pdf
        print(f"Usando PDF local: {args.pdf}", file=sys.stderr)
    else:
        desde = None
        if args.fecha:
            try:
                desde = datetime.strptime(args.fecha, '%Y-%m-%d').date()
            except ValueError:
                salida("error", "El parámetro --fecha debe tener formato AAAA-MM-DD.")
        try:
            contenido, url_pdf, dia = buscar_boletin(desde)
        except RuntimeError as e:
            salida("error", str(e))
        if not contenido:
            salida("warning",
                   f"No se encontró ningún boletín en los últimos {DIAS_ATRAS_MAX} días hábiles.")
        fecha_boletin = dia.isoformat()
        print(f"Boletín del {fecha_boletin}: {url_pdf}", file=sys.stderr)

        if not args.dry_run and verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
            salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.write(contenido)
        tmp.close()
        ruta_pdf = ruta_temporal = tmp.name

    # 2. Parsear
    try:
        paginas, tapa = leer_paginas(ruta_pdf)
        numero_boletin, fecha_portada = metadatos_boletin(tapa, paginas)
        fecha_boletin = fecha_boletin or fecha_portada
        anio_boletin = (fecha_boletin or '')[:4] or str(date.today().year)

        sumario_pag, cuerpo_pag = separar_sumario(paginas)
        esperadas = leer_sumario(sumario_pag, anio_boletin)
        normas = extraer_normas(cuerpo_pag, esperadas, fecha_boletin, anio_boletin)
    except Exception as e:
        salida("error", f"No se pudo parsear el PDF: {e}")
    finally:
        if ruta_temporal:
            try:
                os.unlink(ruta_temporal)
            except Exception:
                pass

    if not paginas:
        salida("warning", "No se encontró la Sección Administrativa en el PDF "
                          "(¿cambió la maqueta del boletín?).")

    if args.volcar:
        print(f"--- SUMARIO: {len(esperadas)} normas anunciadas ---", file=sys.stderr)
        for e in esperadas:
            print(f"  {e['codigo']:32s} {e['tipo']:12s} {e['numero']:>7s}/{e['anio']} "
                  f"| {str(e.get('emisor'))[:28]:28s} | pág {e.get('pagina')} "
                  f"| {e.get('titulo', '')[:60]}", file=sys.stderr)
        print(f"--- CUERPO: {len(normas)} bloques ---", file=sys.stderr)
        for n in normas:
            print(f"  {n['codigo']:32s} {len(n['texto_completo']):6d} car. "
                  f"{'anunciada' if n['anunciada'] else 'NO ANUNCIADA'} "
                  f"| {n['titulo'][:60]}", file=sys.stderr)
        salida("success", f"volcado: {len(esperadas)} en el sumario, "
                          f"{len(normas)} bloques en el cuerpo.")

    # Control de cobertura contra el sumario ANTES de filtrar nada.
    faltantes, sobrantes = comparar_con_sumario(esperadas, normas)
    if esperadas:
        print(f"Sumario: anuncia {len(esperadas)} normas, se extrajeron {len(normas)} "
              f"({len(faltantes)} faltantes, {len(sobrantes)} no anunciadas)", file=sys.stderr)
        for f in faltantes[:15]:
            print(f"  FALTA   {f['tipo']} {f['numero']}/{f['anio']} - "
                  f"{f.get('titulo', '')[:60]}", file=sys.stderr)
        for s in sobrantes[:15]:
            print(f"  DE MÁS  {s['tipo']} {s['numero']}/{s['anio']} - "
                  f"{s['titulo'][:60]}", file=sys.stderr)

    generales = [n for n in normas if not n['es_individual']]
    individuales = [n for n in normas if n['es_individual']]
    a_enviar = normas if args.sin_filtro else generales

    guardar_debug(json.dumps(normas, ensure_ascii=False, indent=2, default=str),
                  'debug_entrerios.json')
    print(f"Boletín {numero_boletin or '?'} del {fecha_boletin} | "
          f"páginas administrativas: {len(paginas)} | normas: {len(normas)} "
          f"(generales {len(generales)} / individuales {len(individuales)})",
          file=sys.stderr)

    # 3. Prueba
    if args.dry_run:
        for n in (normas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {str(n['tipo']):22s} N° {str(n['numero']):>7s}/{n['anio']} "
                  f"{emisor_final(n, args.emisor_organismo)[:32]:32s} "
                  f"{len(n['texto_completo']):6d} car.  {n['titulo'][:52]}",
                  file=sys.stderr)
            if args.todas and n['motivos']:
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    if not normas:
        salida("warning", "La Sección Administrativa no contenía normas reconocibles.")
    if not a_enviar:
        salida("warning", f"Las {len(individuales)} normas del boletín son actos "
                          f"individuales; no se envió ninguna.")

    # 4. Envío
    payload = [{
        "id_jurisdiccion": args.id_jurisdiccion,
        "nombre_emisor": emisor_final(n, args.emisor_organismo),
        "tipo_norma_desc": n["tipo"],
        "numero": n["numero"],
        "anio": n["anio"],
        "fecha_publicacion": n["fecha_publicacion"],
        # El título del sumario es una síntesis mucho mejor que el arranque del
        # articulado, que siempre empieza con "VISTO: Las presentes actuaciones".
        "sintesis": construir_sintesis(n),
        "texto_completo": recortar_texto(n["texto_completo"]),
        "url_norma": url_norma(url_pdf, n),
    } for n in a_enviar]

    try:
        r = requests.post(URL_GUARDAR_NORMAS, json={"normas": payload},
                          headers={"Authorization": f"Bearer {API_KEY_BACKEND}",
                                   "Content-Type": "application/json"}, timeout=120)
        r.raise_for_status()
        respuesta = r.json()
    except Exception as e:
        salida("error", f"Error enviando al backend: {e}")

    if fecha_boletin:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, len(payload))

    # El aviso del sumario va en un campo aparte, NO en el status: el frontend
    # sólo refresca la grilla cuando recibe 'success', y que falten normas del
    # sumario es una advertencia sobre la COBERTURA, no una falla del insert.
    mensaje = respuesta.get('mensaje', 'OK') or 'OK'
    extra = None
    if faltantes:
        detalle = ', '.join(f"{f['tipo']} {f['numero']}/{f['anio']}" for f in faltantes[:10])
        if len(faltantes) > 10:
            detalle += f" y {len(faltantes) - 10} más"
        extra = {
            "advertencia": (f"El sumario anuncia {len(faltantes)} normas que no se "
                            f"extrajeron: {detalle}"),
            "faltantes_sumario": len(faltantes),
        }
        print("ADVERTENCIA: " + extra["advertencia"], file=sys.stderr)

    salida("success", mensaje, total=len(payload), extra=extra)


if __name__ == '__main__':
    try:
        _main()
    except SystemExit:
        raise
    except Exception as e:
        salida("error", str(e))