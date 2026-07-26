#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 BOLETÍN OFICIAL DE LA PROVINCIA DE JUJUY  —  id_jurisdiccion 11
===============================================================================

Un solo archivo, SIN OCR: el PDF tiene capa de texto nativa y una sola columna.

DESCUBRIMIENTO
--------------
La home de boletines es un calendario de WordPress:

    https://boletinoficial.jujuy.gob.ar/?page_id=2017
    https://boletinoficial.jujuy.gob.ar/?page_id=2017&month=jun&yr=2026   (mes anterior)

El mes va en inglés abreviado (jan…dec), no en castellano.

Cada día publicado tiene DOS enlaces al mismo PDF: uno con el texto corto
("Boletín Oficial Nº 78") y otro cuyo texto es EL SUMARIO COMPLETO del boletín,
con las secciones y el código de cada norma. Ese segundo enlace es oro: es el
oráculo de cobertura y evita tener que adivinar dónde corta cada sección dentro
del PDF. Se identifica quedándose, entre los enlaces que apuntan a la misma URL,
con el de texto más largo.

Las rutas son correlativas y predecibles:

    .../wp-content/uploads/2016/Boletines/2026/84-2026.pdf
                                  ^fijo   ^año   ^nº de boletín (sube de a uno)

El "2016" es parte fija de la ruta de WordPress, NO el año. Publica lunes,
miércoles y viernes. El calendario a veces se actualiza más tarde que el
archivo, así que después de leer el calendario se tantea el correlativo
siguiente (N+1, N+2, N+3) por si el PDF ya está subido y la celda todavía no.

ESTRUCTURA DEL PDF
------------------
Página 1 = tapa ("B.O. Nº 84" + "San Salvador de Jujuy, 20 de julio de 2026-").
De ahí en más, cada página repite un encabezado de tres líneas
("Julio, 20 de 2026.-" / "Boletín Oficial Nº 84" / nº de página) que hay que
limpiar o se cuela en el medio de las normas.

El boletín se divide en secciones con banners:

    LEYES - DECRETOS - RESOLUCIONES      <- lo único que interesa
    MUNICIPIOS - COMISIONES MUNICIPALES  <- opcional (--municipios)
    LICITACIONES - CONCURSO DE PRECIOS   <- opcional (--licitaciones)
    CONTRATOS - CONVOCATORIAS - ACTAS    } ruido: actas societarias, remates,
    REMATES / CONCURSOS Y QUIEBRAS       } sucesorios, usucapión, notificaciones.
    EDICTOS DE MINAS / USUCAPION / …     } Equivale a la Sección Comercial de ER.

LAS CUATRO TRAMPAS DE JUJUY
---------------------------
1. EL BANNER DE SECCIÓN NO ESTÁ DONDE SE VE. En el orden de lectura del PDF,
   "LEYES - DECRETOS - RESOLUCIONES" sale AL FINAL del texto de la página, no
   arriba (es un cuadro dibujado aparte, al final del content stream). Cortar
   secciones buscando el banner deja media sección afuera. Por eso el corte se
   hace por los CÓDIGOS que anuncia el sumario del calendario, y el banner se
   usa sólo como red de contención.

2. LA SECCIÓN COMERCIAL ESTÁ LLENA DE "RESOLUCION Nº …". Cada acta societaria
   viene acompañada de una "RESOLUCION Nº 500-DPSC-2026" de la Dirección
   Provincial de Sociedades Comerciales. Un regex global sobre el PDF entero
   mete decenas de resoluciones que no son normativa. Sin el corte de sección
   (punto 1) el boletín entra podrido.

3. EL AÑO DEL CÓDIGO NO ES EL AÑO DEL BOLETÍN. El B.O. 76 del 01/07/2026
   publica "DECRETO Nº 4589-ISPTyV/2025". El año sale SIEMPRE del código.

4. LOS NÚMEROS DE RESOLUCIÓN SE REPITEN ENTRE ORGANISMOS. Conviven
   "RESOLUCION Nº 240-SOTyH/2026" y "RESOLUCION Nº 1269-E/2026": el número solo
   no identifica nada. Como el backend deduplica por tipo|numero|anio|emisor,
   las resoluciones DEBEN ir con el organismo real como emisor (no un genérico),
   o dos resoluciones distintas del mismo número se pisan entre sí. La sigla del
   código (-E-, -HF-, -ISPTyV-) es la que manda; ver SIGLAS.

Variantes de escritura ya contempladas (todas vistas en boletines reales):
    DECRETO Nº 5522-HF/2026.-            RESOLUCION Nº 710-ISPTyV/2026.-
    RESOLUCIÓN Nª 95- SMeH/2026.-        (Nª y espacio después del guion)
    Resolución General Nº 1762-DPR/2026  (minúsculas y sin ".-" final)
    RESOLUCION GENERAL Nº 1761-DPR2026.- (sin la barra del año)
    RESOLUCION Nº 101-E-JUJ-MPEM/2026.-  (sigla compuesta, formato GDE)
    DECRETO Nº 12-E-JUJ-GOB/2026.-       LEY Nº 6511.-  (sin sigla ni año)

EMISOR
------
Se lee del propio cuerpo, de la línea que precede a DECRETA:/RESUELVE:
("EL GOBERNADOR DE LA PROVINCIA", "LA MINISTRA DE EDUCACIÓN", "EL DIRECTORIO
DE LA SUSEPU"). Si no aparece, se cae a la tabla de SIGLAS. Los decretos van
como PODER EJECUTIVO y las leyes como PODER LEGISLATIVO (los firma el
Gobernador / la Legislatura); las resoluciones van SIEMPRE por organismo por lo
explicado en la trampa 4.

SÍNTESIS
--------
A diferencia de Entre Ríos, el sumario de Jujuy NO trae título descriptivo: sólo
el código. La síntesis se arma del cuerpo: el título entre comillas en las leyes
("HORA SILENCIOSA") y el ARTÍCULO 1º recortado en todo lo demás.

FLAGS
-----
    --dry-run           no envía nada
    --pdf ARCHIVO       usa un PDF local
    --texto ARCHIVO     usa un .txt ya extraído (para probar el parser sin PDF)
    --boletin N         fuerza el número de boletín
    --anio AAAA         año del boletín (default: el actual)
    --todas             muestra también las individuales, con puntaje y motivos
    --sin-filtro        envía todo, sin filtrar actos individuales
    --municipios        suma la sección MUNICIPIOS - COMISIONES MUNICIPALES
    --licitaciones      suma la sección LICITACIONES - CONCURSO DE PRECIOS
    --emisor-organismo  manda también decretos y leyes por organismo
    --volcar            imprime sumario y bloques y sale

CONTRATO CON EL BACKEND (igual que el resto de los bots)
--------------------------------------------------------
- El JSON de salida va a stdout; TODO lo demás a stderr.
- url_norma lleva un fragmento único (#TIPO-NUMERO-SIGLA-ANIO) porque
  ingresar_scraping.php deduplica por url_norma EXACTA: sin el fragmento, la
  primera norma guardada bloquea a todas las demás del mismo boletín.
===============================================================================
"""

import os
import re
import sys
import json
import time
import argparse
import unicodedata
from datetime import date, datetime

import requests

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

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

SITIO = 'https://boletinoficial.jujuy.gob.ar'
URL_CALENDARIO = f'{SITIO}/?page_id=2017'
# El "2016" es parte fija de la ruta de WordPress, no el año del boletín.
BASE_PDF = f'{SITIO}/wp-content/uploads/2016/Boletines'

HEADERS_WEB = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'application/pdf,text/html;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
}

REINTENTOS = 3
ESPERA_REINTENTO = 3
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700
TANTEO_CORRELATIVO = 3      # cuántos números probar más allá del calendario

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
MESES_NUM = {m.lower(): i + 1 for i, m in enumerate(MESES)}
MESES_NUM['setiembre'] = 9
# El calendario de WordPress usa el mes en inglés abreviado.
MESES_EN = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
            'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


# ===========================================================================
# NORMALIZACIÓN
# ===========================================================================
# El PDF mezcla guion común, en dash y em dash dentro del mismo código.
GUIONES = {ord('–'): '-', ord('—'): '-', ord('‐'): '-', ord('‑'): '-', ord('−'): '-'}


def _guiones(texto):
    return (texto or '').translate(GUIONES)


def _sin_acentos(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def _compacto(texto):
    return re.sub(r'\s+', ' ', _guiones(texto or '')).strip()


def _limpiar_numero(num):
    """
    '0249' -> '249'; '1.762' -> '1762'. Sin esto la misma norma entra dos veces,
    una como 0249 y otra como 249.

    Excepción: los decretos municipales usan un código compuesto de tres grupos
    ('DECRETO Nº 1609.26.040'). Ahí los puntos son parte del número y sacarlos
    lo convierte en otra cosa.
    """
    if num is None:
        return ''
    n = str(num).strip(' .')
    if n.count('.') >= 2:                       # 1609.26.040 -> se conserva
        return n
    m = re.fullmatch(r'(\d{1,3})\.(\d{3})', n)  # 1.762 -> separador de miles
    if m:
        n = m.group(1) + m.group(2)
    n = re.sub(r'[.\s]', '', n)
    return n.lstrip('0') or '0'


# ===========================================================================
# SECCIONES DEL BOLETÍN
# ===========================================================================
SECCION_NORMATIVA = 'LEYES - DECRETOS - RESOLUCIONES'
SECCION_MUNICIPIOS = 'MUNICIPIOS - COMISIONES MUNICIPALES'
SECCION_LICITACIONES = 'LICITACIONES - CONCURSO DE PRECIOS'

# En el orden en que aparecen en el boletín. Sirven para partir el sumario del
# calendario y como red de contención dentro del PDF.
SECCIONES = [
    SECCION_NORMATIVA,
    SECCION_MUNICIPIOS,
    SECCION_LICITACIONES,
    'CONTRATOS - CONVOCATORIAS - ACTAS',
    'REMATES',
    'CONCURSOS Y QUIEBRAS',
    'EDICTOS DE MINAS',
    'EDICTOS DE USUCAPION',
    'EDICTOS DE NOTIFICACION',
    'EDICTOS DE CITACION',
    'EDICTOS SUCESORIOS',
    # 'FE DE ERRATAS' NO va acá: no es un banner de sección sino un ítem que
    # aparece dentro de la sección normativa. Si se lo trata como sección,
    # corta el sumario ahí y se pierde todo lo que venga después.
]


def _re_seccion(nombre):
    """Regex tolerante para un banner: acentos, espacios y guiones flexibles."""
    partes = [re.escape(p) for p in _sin_acentos(nombre).split(' - ')]
    return re.compile(r'\s*[-–—]?\s*'.join(partes).replace(r'\ ', r'\s+'), re.IGNORECASE)


RE_SECCIONES = [(n, _re_seccion(n)) for n in SECCIONES]


# ===========================================================================
# CÓDIGOS DE NORMA
# ===========================================================================
# El orden importa: "RESOLUCION GENERAL" antes que "RESOLUCION", "DECRETO
# ACUERDO" antes que "DECRETO", o el patrón corto se come al largo.
TIPOS = [
    ('RESOLUCION GENERAL', r'RESOLUCI[OÓ]N\s+GENERAL'),
    ('DECRETO ACUERDO',    r'DECRETO\s+ACUERDO'),
    ('DECRETO',            r'DECRETO'),
    ('RESOLUCION',         r'RESOLUCI[OÓ]N'),
    ('DISPOSICION',        r'DISPOSICI[OÓ]N'),
    ('ACORDADA',           r'ACORDADA'),
    ('ORDENANZA',          r'ORDENANZA'),
    ('LEY',                r'LEY'),
]

_ALT_TIPOS = '|'.join(p for _, p in TIPOS)

# N° / Nº / Nª / N. / No — el OCR-limpio de Jujuy usa las cuatro primeras.
_NUMERAL = r'(?:N\s*[º°ª\.o]?)?'
# Sigla del organismo: E, HF, ISPTyV, MAyCC, SMeH, E-JUJ-MPEM, DPR…
_SIGLA = r'[A-Za-zÁÉÍÓÚÑáéíóúñ][A-Za-z0-9ÁÉÍÓÚÑáéíóúñ.]*(?:\s*-\s*[A-Za-z][A-Za-z0-9.]*)*'

RE_CODIGO = re.compile(
    r'(?P<tipo>' + _ALT_TIPOS + r')'
    r'\s*' + _NUMERAL + r'\s*'
    r'(?P<numero>\d{1,6}(?:\.\d{1,3}){0,3})'
    r'(?:\s*-\s*(?P<sigla>' + _SIGLA + r'))?'
    r'(?:\s*[-/]?\s*(?P<anio>(?:19|20)\d{2}))?',
    re.IGNORECASE)

# Para abrir una norma dentro del CUERPO se exige principio de línea. Sin esto,
# cada "conforme el Decreto Nº 5193-HF/2026" citado en un considerando abriría
# una norma nueva.
RE_CODIGO_LINEA = re.compile(r'^[ \t]*' + RE_CODIGO.pattern, re.IGNORECASE | re.MULTILINE)

# Las leyes no se anuncian con "LEY Nº" a secas en el cuerpo: vienen precedidas
# por la fórmula de sanción. Se usa como ancla adicional.
RE_SANCION_LEY = re.compile(
    r'LA\s+LEGISLATURA\s+DE\s+JUJUY\s+SANCIONA\s+CON\s+FUERZA\s+DE\s*\n?\s*'
    r'LEY\s*' + _NUMERAL + r'\s*(?P<numero>\d+)', re.IGNORECASE)


def parsear_codigo(texto, anio_boletin=None):
    """Devuelve dict(tipo, numero, sigla, anio, codigo) o None."""
    m = RE_CODIGO.search(_guiones(texto or ''))
    if not m:
        return None
    return _desde_match(m, anio_boletin)


def _desde_match(m, anio_boletin=None):
    crudo = m.group('tipo').upper()
    crudo = _sin_acentos(crudo)
    crudo = re.sub(r'\s+', ' ', crudo)
    tipo = 'RESOLUCION'
    for nombre, patron in TIPOS:
        if re.fullmatch(_sin_acentos(patron).replace('[OO]', 'O'), crudo, re.IGNORECASE) \
                or crudo == nombre:
            tipo = nombre
            break
    else:
        # fallback: primera palabra
        tipo = crudo.split(' ')[0]
        if tipo.startswith('RESOLUCION') and 'GENERAL' in crudo:
            tipo = 'RESOLUCION GENERAL'

    numero = _limpiar_numero(m.group('numero'))
    sigla = (m.group('sigla') or '').strip(' .-')
    sigla = re.sub(r'\s*-\s*', '-', sigla).upper()
    # El sumario municipal escribe "DECRETO Nº 1609.26.040 - MUNICIPAL DE SAN
    # SALVADOR…": lo que sigue al guion es el organismo, no una sigla. Las siglas
    # reales son cortas (E, HF, ISPTyV, SUSEPU) o compuestas con guiones
    # (E-JUJ-MPEM).
    if len(sigla) > 7 and '-' not in sigla and \
            re.sub(r'[^A-Z0-9]', '', _sin_acentos(sigla)) not in SIGLAS:
        sigla = ''
    # El año del código manda sobre el del boletín (ver trampa 3).
    anio = m.group('anio') or (str(anio_boletin) if anio_boletin else '')
    return {
        'tipo': tipo,
        'numero': numero,
        'sigla': sigla,
        'anio': str(anio),
        'codigo': _compacto(m.group(0)),
    }


def clave_norma(n):
    """Identidad de una norma para comparar sumario contra cuerpo."""
    return (n.get('tipo', ''), _limpiar_numero(n.get('numero')),
            (n.get('sigla') or '').upper(), str(n.get('anio', '')))


# ===========================================================================
# ORGANISMOS
# ===========================================================================
# La sigla del código es lo más confiable que hay: viaja pegada al número y no
# depende de que el cuerpo tenga bien escrita la línea del cargo.
SIGLAS = {
    'E': 'MINISTERIO DE EDUCACIÓN',
    'S': 'MINISTERIO DE SALUD',
    'MS': 'MINISTERIO DE SALUD',
    'HF': 'MINISTERIO DE HACIENDA Y FINANZAS',
    'G': 'MINISTERIO DE GOBIERNO, JUSTICIA, DERECHOS HUMANOS Y TRABAJO',
    'JG': 'JEFATURA DE GABINETE DE MINISTROS',
    'ISPTYV': 'MINISTERIO DE INFRAESTRUCTURA, SERVICIOS PÚBLICOS, TIERRA Y VIVIENDA',
    'DEYP': 'MINISTERIO DE DESARROLLO ECONÓMICO Y PRODUCCIÓN',
    'MAYCC': 'MINISTERIO DE AMBIENTE Y CAMBIO CLIMÁTICO',
    'DH': 'MINISTERIO DE DESARROLLO HUMANO',
    'CYT': 'MINISTERIO DE CULTURA Y TURISMO',
    'SG': 'MINISTERIO DE SEGURIDAD',
    'PEYM': 'MINISTERIO DE PLANIFICACIÓN ESTRATÉGICA Y MODERNIZACIÓN',
    'MPEM': 'MINISTERIO DE PLANIFICACIÓN ESTRATÉGICA Y MODERNIZACIÓN',
    'SOTYH': 'SECRETARÍA DE ORDENAMIENTO TERRITORIAL Y HÁBITAT',
    'SMEH': 'SECRETARÍA DE MINERÍA E HIDROCARBUROS',
    'DPR': 'DIRECCIÓN PROVINCIAL DE RENTAS',
    'SUSEPU': 'SUPERINTENDENCIA DE SERVICIOS PÚBLICOS Y OTRAS CONCESIONES',
    'OA': 'OFICINA ANTICORRUPCIÓN',
    'DPAJ': 'DIRECCIÓN PROVINCIAL DE ASUNTOS JURÍDICOS',
    'CAJ': 'COLEGIO DE ABOGADOS Y PROCURADORES DE JUJUY',
    'EAZF': 'ENTE DE ADMINISTRACIÓN DE ZONAS FRANCAS',
    'DPSC': 'DIRECCIÓN PROVINCIAL DE SOCIEDADES COMERCIALES',
    'GOB': 'PODER EJECUTIVO',
}

# Línea del cargo que precede a DECRETA:/RESUELVE:. Es la señal más precisa
# cuando existe, porque la escribe el propio organismo.
RE_CARGO = re.compile(
    r'^[ \t]*(?P<cargo>(?:EL|LA)\s+[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9.,;()\'"\s/e-]{5,120}?)'
    r'\s*(?:\n\s*)?(?:DECRETA|RESUELVE|DISPONE|ACUERDA)\s*:',
    re.MULTILINE)


def detectar_organismo(texto, sigla=''):
    m = RE_CARGO.search(texto or '')
    if m:
        cargo = _compacto(m.group('cargo'))
        cargo = re.sub(r'^(EL|LA)\s+', '', cargo, flags=re.IGNORECASE).strip(' .,-')
        if cargo and len(cargo) > 4:
            return cargo.upper()
    clave = re.sub(r'[^A-Z0-9]', '', _sin_acentos(sigla or '').upper())
    # Siglas compuestas tipo E-JUJ-MPEM: vale la última parte significativa.
    if clave in SIGLAS:
        return SIGLAS[clave]
    for parte in reversed(re.split(r'[-]', _sin_acentos(sigla or '').upper())):
        parte = re.sub(r'[^A-Z0-9]', '', parte)
        if parte in SIGLAS:
            return SIGLAS[parte]
    return ''


# ===========================================================================
# FILTRO DE ACTOS INDIVIDUALES
# ===========================================================================
# Mismo criterio que Catamarca, Chaco, Chubut y Entre Ríos: el boletín mezcla
# normativa de alcance general con actos sobre una persona determinada, que no
# son normativa de interés y además arrastran datos personales.
#
# Diferencia con Entre Ríos: acá NO hay título de sumario. La mejor señal es el
# ARTÍCULO 1º, que en Jujuy es tajante ("Desígnese…", "Acéptese la renuncia…",
# "Promuévase…"). Casi todos los decretos se publican SINTETIZADOS, sin VISTO ni
# CONSIDERANDO, así que el articulado es prácticamente todo el texto.
#
# Los pesos se calibraron contra las normas reales de los B.O. 77, 78 y 84 de
# julio de 2026. Ver la sección VALIDACIÓN del traspaso.
UMBRAL_INDIVIDUAL = 3

PATRONES_INDIVIDUAL = [
    (r'\bDes[íi]gn[ae]se\b|\bDesignase\b|\bDesignese\b',           4, 'designación'),
    (r'\bAc[ée]pt[ae]se\b[\s\S]{0,80}\brenuncia\b',                4, 'renuncia'),
    (r'\brenuncia\s+presentada\s+por\b',                           4, 'renuncia'),
    (r'\bPromu[ée]v[ae]se\b',                                      4, 'promoción de un agente'),
    (r'\bAdec[úu]?ase\b[\s\S]{0,80}\bcategor[íi]a\b',              3, 'recategorización'),
    (r'\bT[ée]n(?:er|gase)\s+por\s+aprobad[oa]s?\s+y\s+cumplid',   4, 'contrato de locación de servicios'),
    (r'\bContrato\s+de\s+Locaci[óo]n\s+de\s+Servicios\b',          3, 'contrato de personal'),
    (r'\bsanci[óo]n\s+expulsiva\b|\bexoneraci[óo]n\b|\bcesant[íi]a\b', 4, 'sanción expulsiva'),
    (r'\bRecurso\s+Jer[áa]rquico\s+interpuesto\b',                 3, 'recurso de un particular'),
    (r'\breclamo\s+administrativo\s+previo\s+interpuesto\s+por\b', 3, 'reclamo de un particular'),
    (r'\bRechazar\b[\s\S]{0,60}\binterpuest[oa]\s+por\s+(?:el|la)\s+Sr', 3, 'rechazo a un particular'),
    (r'\bOt[óo]rg[au]ese\b[\s\S]{0,60}\bLicencia\b|\bConc[ée]dese\s+Licencia\b', 3, 'licencia'),
    (r'\bLicencia\s+Sin\s+Goce\s+de\s+Haberes\b',                  3, 'licencia sin goce de haberes'),
    (r'\bEnc[áa]rguese\s+la\s+cartera\b',                          3, 'interinato de cartera'),
    (r'\bSOLICITUD\s+DE\s+PAGO\b',                                 3, 'pago a una persona'),
    (r'\bimputar\s+la\s+erogaci[óo]n\b',                           2, 'imputación de un pago puntual'),
    (r'\ba\s+favor\s+d(?:el|e\s+la)\s+Sr',                         3, 'beneficiario individual'),
    (r'\bCancelaci[óo]n\s+de\s+Hipoteca\b',                        2, 'cancelación de hipoteca'),
    (r'\bAdjudic[au]?ese\b[\s\S]{0,60}\b(?:al|a\s+la)\s+Sr',       3, 'adjudicación individual'),
    (r'\bTraslad[au]?ese\b|\bPermuta\b|\bAdscripci[óo]n\b',        3, 'traslado / adscripción'),
    (r'\bSubrogancia\b|\bSuplencia\b',                             4, 'subrogancia'),
    (r'\bjubilaci[óo]n\b|\bhaber\s+jubilatorio\b|\bbaja\s+por\s+jubilaci', 3, 'previsional'),
    (r'\bsumario\s+administrativo\b',                              4, 'sumario administrativo'),
    (r'\bal?\s+(?:Sr\.|Sra\.|Srta\.|agente|Lic\.|Dr\.|Dra\.|C\.?P\.?|Prof)\b', 2, 'nombra a una persona'),
]

PATRONES_GENERAL = [
    (r'\bAprub[ée]|\bAprub[ée]nse|\bApru[ée]b[ae](?:nse)?\b[\s\S]{0,60}'
     r'(?:Reglamento|Pliego|Convenio|Estructura|Misiones|Cuadro\s+Tarifario|Resoluciones)',
     -4, 'aprobación normativa'),
    (r'\bMisiones\s+y\s+Funciones\b|\bEstructura\s+Org[áa]nica\b',  -4, 'estructura orgánica'),
    (r'\bCr[ée]ase\b|\bCr[ée]anse\b|\bIncorp[óo]rase\b',            -3, 'creación normativa'),
    (r'\bDer[óo]gase\b|\bModif[íi]c[ae]se\s+(?:el|la|los)\b',       -3, 'modificación normativa'),
    (r'\bProm[úu]lg',                                              -4, 'promulgación'),
    (r'\bPr[óo]rrog|\bProrr[óo]gu|\bDif[íi][ée]rase\b',            -3, 'prórroga'),
    (r'\bExti[ée]ndase\s+(?:hasta|el\s+plazo)\b',                  -3, 'extensión de plazo'),
    (r'\bR[ée]gimen\b[\s\S]{0,40}\b(?:previsto|establecid|transitorio)\b', -3, 'régimen general'),
    (r'\bLicitaci[óo]n\s+P[úu]blica\b|\bConcurso\s+de\s+Precios\b', -4, 'licitación'),
    (r'\bDecl[áa]rase\s+de\s+inter[ée]s\b|\bInter[ée]s\s+Provincial\b', -3, 'declaración de interés'),
    (r'\bEmergencia\b',                                            -3, 'emergencia'),
    (r'\bAd(?:hesi[óo]n|hi[ée]rase)\b',                            -3, 'adhesión'),
    (r'\bTarifa\s+Social\b|\bCuadro\s+Tarifario\b|\bAlic[úu]ota',   -3, 'tarifas'),
    (r'\bvencimientos?\s+de\s+(?:las\s+)?obligaciones\s+tributarias\b', -3, 'calendario fiscal'),
    (r'\bImpacto\s+Ambiental\b',                                   -3, 'evaluación ambiental'),
    (r'\bimplementaci[óo]n\s+de\s+la\s+carrera\b|\bDise[ñn]o\s+Curricular\b', -3, 'oferta educativa'),
    (r'\bInv[íi]tase\s+a\s+los\s+Municipios\b',                    -3, 'invitación a municipios'),
    (r'\bAsueto\b|\bFeriado\b|\bCalendario\s+Escolar\b',           -3, 'asueto / calendario'),
]

RE_DOCUMENTO = re.compile(r'\b(?:D\.?N\.?I|C\.?U\.?I\.?[LT]|L\.?[CE]\.?|M\.?I\.?)\b[\s.:Nnºo°-]*\d',
                          re.IGNORECASE)


def clasificar_norma(tipo, articulo1, texto):
    """Devuelve (es_individual, puntaje, motivos)."""
    # Las leyes son siempre de alcance general: la Legislatura no dicta actos
    # de administración de personal.
    if str(tipo).startswith('LEY'):
        return False, -99, ['ley: siempre general']
    # Las "resoluciones generales" lo dicen en el nombre.
    if str(tipo).startswith('RESOLUCION GENERAL'):
        return False, -99, ['resolución general: siempre general']

    puntaje, motivos = 0, []
    art = articulo1 or ''
    cuerpo = texto or ''

    # El artículo 1º pesa completo; el resto del cuerpo, la mitad (el articulado
    # de cierre repite fórmulas administrativas iguales en todas las normas).
    for patron, peso, etiqueta in PATRONES_INDIVIDUAL:
        if re.search(patron, art, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'+{peso} art.1: {etiqueta}')
        elif re.search(patron, cuerpo, re.IGNORECASE):
            medio = max(1, peso // 2)
            puntaje += medio
            motivos.append(f'+{medio} cuerpo: {etiqueta}')

    for patron, peso, etiqueta in PATRONES_GENERAL:
        if re.search(patron, art, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'{peso} art.1: {etiqueta}')
        elif re.search(patron, cuerpo, re.IGNORECASE):
            medio = min(-1, peso // 2)
            puntaje += medio
            motivos.append(f'{medio} cuerpo: {etiqueta}')

    # Mencionar un documento suma, pero no decide solo: los decretos generales
    # también citan el DNI del funcionario que firma.
    docs = len(RE_DOCUMENTO.findall(cuerpo))
    if docs:
        puntaje += 1
        motivos.append(f'+1 menciona DNI/CUIL/CUIT ({docs})')

    return (puntaje >= UMBRAL_INDIVIDUAL), puntaje, motivos


# ===========================================================================
# LECTURA DEL PDF
# ===========================================================================
RE_ENCABEZADO_PAG = re.compile(
    r'^\s*(?:'
    r'[A-Za-zÁÉÍÓÚáéíóúñÑ]+,\s*\d{1,2}\s+de\s+\d{4}\.?-?'      # "Julio, 20 de 2026.-"
    r'|Bolet[ií]n\s+Oficial\s+N[º°]?\s*\d+'                     # "Boletín Oficial Nº 84"
    r'|\d{1,4}'                                                 # número de página suelto
    r')\s*$',
    re.IGNORECASE | re.MULTILINE)

RE_TAPA_NUMERO = re.compile(r'B\.?\s*O\.?\s*N[º°]?\s*(\d{1,4})', re.IGNORECASE)
RE_TAPA_FECHA = re.compile(
    r'San\s+Salvador\s+de\s+Jujuy,\s*(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+de\s+(\d{4})',
    re.IGNORECASE)
# Duplicación de caracteres por negrita falsa (el caso de Entre Ríos). Acá no se
# vio, pero detectarlo es barato y evita perder un boletín entero en silencio.
RE_NEGRITA_FALSA = re.compile(r'\b([A-ZÁÉÍÓÚÑ])\1([A-ZÁÉÍÓÚÑ])\2([A-ZÁÉÍÓÚÑ])\3')


def leer_paginas(ruta_pdf):
    """Devuelve la lista de textos de página del PDF."""
    if pdfplumber is None:
        raise RuntimeError("Falta pdfplumber: pip install pdfplumber")
    paginas = []
    avisado = False
    with pdfplumber.open(ruta_pdf) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ''
            if RE_NEGRITA_FALSA.search(txt):
                # Los títulos vienen dibujados dos veces con un offset mínimo y
                # pdfplumber devuelve los caracteres duplicados
                # ("RREECCHHAAZZOO"). Se acepta el dedupe sólo si de verdad
                # acortó el texto: si no, el patrón fue un falso positivo y
                # quedarse con el original es más seguro.
                try:
                    limpio = page.dedupe_chars(tolerance=1).extract_text() or ''
                    if limpio and len(limpio) < len(txt) * 0.95:
                        txt = limpio
                        if not avisado:
                            print("Aviso: negrita falsa detectada, se aplicó "
                                  "dedupe_chars", file=sys.stderr)
                            avisado = True
                except Exception:
                    pass
            paginas.append(txt)
    return paginas


def metadatos_boletin(paginas):
    """(numero_boletin, fecha ISO) leídos de la tapa."""
    cabeza = '\n'.join(paginas[:2])
    numero = None
    m = RE_TAPA_NUMERO.search(cabeza)
    if m:
        numero = m.group(1)
    fecha = None
    m = RE_TAPA_FECHA.search(cabeza)
    if m:
        dia, mes, anio = m.group(1), m.group(2).lower(), m.group(3)
        mes_num = MESES_NUM.get(_sin_acentos(mes))
        if mes_num:
            try:
                fecha = date(int(anio), mes_num, int(dia)).isoformat()
            except ValueError:
                fecha = None
    return numero, fecha


def limpiar_cuerpo(paginas):
    """Une las páginas sacando los encabezados repetidos de cada una."""
    limpias = []
    for txt in paginas:
        txt = _guiones(txt or '')
        txt = RE_ENCABEZADO_PAG.sub('', txt)
        limpias.append(txt)
    return '\n'.join(limpias)


# ===========================================================================
# SUMARIO (viene del CALENDARIO, no del PDF)
# ===========================================================================
def partir_sumario(texto_sumario):
    """
    Parte el texto del tooltip del calendario en secciones.
    Devuelve {nombre_seccion: texto}.
    """
    texto = _compacto(texto_sumario or '')
    plano = _sin_acentos(texto).upper()
    cortes = []
    for nombre, rx in RE_SECCIONES:
        for m in rx.finditer(plano):
            cortes.append((m.start(), m.end(), nombre))
    cortes.sort()
    # Se descartan solapamientos (p. ej. "REMATES" dentro de otra cadena).
    limpios = []
    for ini, fin, nombre in cortes:
        if limpios and ini < limpios[-1][1]:
            continue
        limpios.append((ini, fin, nombre))

    secciones = {}
    for i, (ini, fin, nombre) in enumerate(limpios):
        hasta = limpios[i + 1][0] if i + 1 < len(limpios) else len(texto)
        secciones.setdefault(nombre, '')
        secciones[nombre] += ' ' + texto[fin:hasta]
    return secciones


def leer_sumario(texto_sumario, secciones_deseadas, anio_boletin=None):
    """
    Lista de normas anunciadas por el calendario para las secciones pedidas.
    El sumario es el oráculo de cobertura: si el cuerpo no trae algo que el
    sumario anuncia, hay que mirarlo.
    """
    secciones = partir_sumario(texto_sumario)
    esperadas, sin_parsear = [], []
    for nombre in secciones_deseadas:
        bloque = secciones.get(nombre, '')
        if not bloque:
            continue
        # Los ítems del sumario terminan en ".-"
        for item in re.split(r'\.-|\.–', bloque):
            item = _compacto(item)
            if len(item) < 5:
                continue
            datos = parsear_codigo(item, anio_boletin)
            if datos:
                datos['seccion'] = nombre
                datos['titulo_sumario'] = item
                if not any(clave_norma(d) == clave_norma(datos) for d in esperadas):
                    esperadas.append(datos)
            else:
                sin_parsear.append(item)
    return esperadas, sin_parsear


# --- Fallback: sumario deducido del propio PDF -----------------------------
# El camino bueno es el sumario del calendario. Pero con --pdf local, o si el
# sitio no responde, hay que poder trabajar igual. Acá se usan los banners de
# sección, con la salvedad conocida: pdfplumber los devuelve AL FINAL del texto
# de su página, no en el lugar visual. Por eso se razona por PÁGINA y no por
# posición: la sección normativa va desde la página cuyo texto contiene el
# banner "LEYES - DECRETOS - RESOLUCIONES" hasta la página que trae el banner
# de la sección siguiente, inclusive (esa página tiene el final de una y el
# comienzo de la otra).
RE_ORGANO_MUNICIPAL = re.compile(
    r'^\s*(?:CONCEJO\s+DELIBERANTE|MUNICIPALIDAD\s+DE|MUNICIPAL\s+DE\s+SAN|'
    r'COMISI[ÓO]N\s+MUNICIPAL|COMUNA\s+MUNICIPAL)', re.IGNORECASE | re.MULTILINE)


def banners_por_pagina(paginas):
    """{indice_de_pagina: [secciones cuyo banner aparece en esa página]}."""
    mapa = {}
    for i, txt in enumerate(paginas):
        plano = _sin_acentos(txt or '').upper()
        presentes = [n for n, rx in RE_SECCIONES if rx.search(plano)]
        if presentes:
            mapa[i] = presentes
    return mapa


def sumario_desde_pdf(paginas, secciones_deseadas, anio_boletin=None):
    """Lista de normas deducida del PDF, sin calendario. Devuelve (normas, aviso)."""
    mapa = banners_por_pagina(paginas)
    pagina_inicio = None
    for i in sorted(mapa):
        if SECCION_NORMATIVA in mapa[i]:
            pagina_inicio = i
            break
    if pagina_inicio is None:
        # Sin banner: se asume que la sección normativa arranca después de la
        # tapa, que es lo que hace el boletín cuando no hay nada más.
        pagina_inicio = 1 if len(paginas) > 1 else 0

    pagina_fin = len(paginas) - 1
    for i in sorted(mapa):
        if i < pagina_inicio:
            continue
        otras = [s for s in mapa[i] if s != SECCION_NORMATIVA
                 and s not in secciones_deseadas]
        if otras:
            pagina_fin = i
            break

    esperadas = []
    for i in range(pagina_inicio, pagina_fin + 1):
        texto = _guiones(paginas[i] or '')
        # En la página de transición se descarta lo que venga después del primer
        # encabezado de un órgano municipal: de ahí en adelante ya es otra
        # sección.
        if i == pagina_fin:
            corte = RE_ORGANO_MUNICIPAL.search(texto)
            if corte and SECCION_MUNICIPIOS not in secciones_deseadas:
                texto = texto[:corte.start()]
        for m in RE_CODIGO_LINEA.finditer(texto):
            if not _es_encabezado(texto, m):
                continue          # código citado dentro de un artículo
            datos = _desde_match(m, anio_boletin)
            if not datos:
                continue
            # La Dirección Provincial de Sociedades Comerciales sólo firma
            # edictos societarios: nunca es normativa de interés.
            if 'DPSC' in (datos.get('sigla') or ''):
                continue
            if datos['tipo'] == 'ORDENANZA' and SECCION_MUNICIPIOS not in secciones_deseadas:
                continue
            datos['seccion'] = SECCION_NORMATIVA
            datos['titulo_sumario'] = datos['codigo']
            if not any(clave_norma(d) == clave_norma(datos) for d in esperadas):
                esperadas.append(datos)

    aviso = (f"sumario deducido del PDF (páginas {pagina_inicio + 1} a "
             f"{pagina_fin + 1}), sin control de cobertura contra el calendario")
    return esperadas, aviso


# ===========================================================================
# EXTRACCIÓN DE NORMAS DEL CUERPO
# ===========================================================================
# El "1" tiene que ir seguido del ordinal o del punto, nunca de otro dígito: sin
# el (?!\d) la frase "en uso de las facultades del artículo 10° del Código
# Fiscal", que aparece en el considerando, se lleva puesto el artículo 1º real y
# la síntesis sale con el texto equivocado.
_ART1 = (r'ART[ÍI]?CULO\s*(?:N[º°]\s*)?1(?!\d)\s*[º°]?\s*[.:,;-]+\s*'
         r'(?P<texto>[\s\S]{0,1200}?)(?=ART[ÍI]?CULO\s*(?:N[º°]\s*)?2(?!\d)|\Z)')
RE_ARTICULO1_LINEA = re.compile(r'^[ \t]*' + _ART1, re.IGNORECASE | re.MULTILINE)
RE_ARTICULO1 = re.compile(_ART1, re.IGNORECASE)
RE_TITULO_LEY = re.compile(r'LEY\s*N?[º°]?\s*\d+\s*[.\-]*\s*\n\s*["“\'](?P<titulo>[^"”\']{5,300})',
                           re.IGNORECASE)


def _es_encabezado(texto, m):
    """
    ¿El código abre de verdad una norma, o está citado dentro de un artículo?

    En Jujuy el encabezado va SOLO en su renglón ("DECRETO Nº 5522-HF/2026.-"),
    mientras que las citas viajan dentro de una oración ("...en contra de la
    Resolución N° 027-S.O.TyH de fecha 23 de enero de 2026, y..."). Cuando el
    salto de línea deja la cita al principio de un renglón, el ancla de línea no
    alcanza: hay que mirar cuánto sobra en la línea DESPUÉS del código.
    """
    ini = texto.rfind('\n', 0, m.start()) + 1
    fin = texto.find('\n', m.end())
    if fin == -1:
        fin = len(texto)
    antes = texto[ini:m.start()].strip()
    resto = texto[m.end():fin].strip(' .:-–—')
    return not antes and len(resto) <= 3


def _posiciones_codigos(cuerpo):
    """Todos los códigos que abren línea en el cuerpo, con su offset."""
    encontrados = []
    for m in RE_CODIGO_LINEA.finditer(cuerpo):
        if _es_encabezado(cuerpo, m):
            encontrados.append((m.start(), m))
    for m in RE_SANCION_LEY.finditer(cuerpo):
        encontrados.append((m.start(), m))
    encontrados.sort(key=lambda x: x[0])
    return encontrados


def extraer_normas(cuerpo, esperadas, fecha_boletin=None, anio_boletin=None):
    """
    Recorta el cuerpo en normas usando los códigos del sumario como guía.

    Se va en orden: cada norma se busca a partir del final de la anterior, y
    termina donde arranca la siguiente que aparece en el sumario. Es el mismo
    criterio de Entre Ríos (cortar por el código de la norma siguiente, nunca
    por separadores gráficos), reforzado acá porque la lista de códigos ya la
    dio el calendario.
    """
    normas = []
    if not cuerpo:
        return normas

    cuerpo_plano = _sin_acentos(cuerpo).upper()
    posicion = 0
    marcas = []          # (offset_inicio, esperada)

    for esp in esperadas:
        rx = _regex_encabezado(esp)
        m = rx.search(cuerpo_plano, posicion)
        if not m:
            # Segunda pasada sin restricción de posición: a veces el boletín
            # publica fuera del orden del sumario.
            m = rx.search(cuerpo_plano)
        if not m:
            continue
        marcas.append((m.start(), esp))
        posicion = m.end()

    marcas.sort(key=lambda x: x[0])

    # El final de cada norma es el inicio de la siguiente marca; para la última,
    # el primer encabezado de línea que YA NO pertenece al sumario pedido (o el
    # fin del texto). Eso evita arrastrar la sección comercial entera.
    todos = _posiciones_codigos(cuerpo)
    inicios_marca = {ini for ini, _ in marcas}

    for i, (ini, esp) in enumerate(marcas):
        if i + 1 < len(marcas):
            fin = marcas[i + 1][0]
        else:
            # La última norma termina en el primer encabezado que NO pertenece
            # al sumario pedido. Hay que ignorar las repeticiones del propio
            # código dentro del bloque: "EL CONCEJO ... SANCIONA LA SIGUIENTE /
            # ORDENANZA N° 8271/2026" y "CORRESP. A LEY Nº 6511.-" repiten el
            # encabezado y cortarían la norma a los pocos renglones.
            fin = len(cuerpo)
            propio = (esp['tipo'], _limpiar_numero(esp['numero']))
            for off, m in todos:
                if off <= ini or off in inicios_marca:
                    continue
                otro = _desde_match(m, anio_boletin) if m.groupdict().get('tipo') else None
                if otro and (otro['tipo'], otro['numero']) == propio:
                    continue
                fin = off
                break
        bloque = cuerpo[ini:fin].strip()
        normas.append(_armar_norma(esp, bloque, fecha_boletin, anio_boletin))

    return normas


def _regex_encabezado(esp):
    """Regex del encabezado de una norma esperada, sobre texto sin acentos."""
    tipo = _sin_acentos(esp['tipo']).replace(' ', r'\s+')
    # El número puede venir con ceros a la izquierda, con puntos de miles o con
    # el formato compuesto de los decretos municipales: se compara dígito a
    # dígito admitiendo un punto entre medio.
    digitos = re.sub(r'\D', '', str(esp['numero']))
    num_rx = r'0*' + r'\.?'.join(digitos)
    if esp['tipo'] == 'LEY':
        return re.compile(r'(?:SANCIONA\s+CON\s+FUERZA\s+DE\s*)?\n?\s*'
                          r'LEY\s*N?[º°ª.]?\s*' + num_rx + r'\b', re.IGNORECASE)
    return re.compile(r'^[ \t]*' + tipo + r'\s*N?[º°ª.]?\s*' + num_rx + r'\b',
                      re.IGNORECASE | re.MULTILINE)


def _armar_norma(esp, bloque, fecha_boletin, anio_boletin):
    art1 = ''
    m = RE_ARTICULO1_LINEA.search(bloque) or RE_ARTICULO1.search(bloque)
    if m:
        art1 = _compacto(m.group('texto'))

    titulo = ''
    if esp['tipo'] == 'LEY':
        mt = RE_TITULO_LEY.search(bloque)
        if mt:
            titulo = _compacto(mt.group('titulo'))
    if not titulo:
        titulo = art1 or _compacto(bloque[:400])

    organismo = detectar_organismo(bloque, esp.get('sigla', ''))
    # En la sección de municipios el cuerpo dice "EL INTENDENTE MUNICIPAL DE X",
    # pero el sumario trae el organismo completo después del guion
    # ("ORDENANZA Nº 8271/2026 - CONCEJO DELIBERANTE DE SAN SALVADOR DE JUJUY"),
    # que es más preciso y además distingue un municipio de otro.
    if esp.get('seccion') == SECCION_MUNICIPIOS:
        resto = re.split(r'\s+-\s+', esp.get('titulo_sumario', ''), maxsplit=1)
        if len(resto) == 2 and len(resto[1]) > 5:
            organismo = _compacto(resto[1]).upper().strip(' .-')
    es_ind, puntaje, motivos = clasificar_norma(esp['tipo'], art1, bloque)

    norma = dict(esp)
    norma.update({
        'titulo': titulo,
        'articulo1': art1,
        'emisor': organismo,
        'texto_completo': bloque,
        'fecha_publicacion': fecha_boletin,
        'es_individual': es_ind,
        'puntaje': puntaje,
        'motivos': motivos,
        'anunciada': True,
    })
    if not norma.get('anio'):
        norma['anio'] = str(anio_boletin or date.today().year)
    return norma


def comparar_con_sumario(esperadas, normas):
    extraidas = {clave_norma(n) for n in normas}
    faltantes = [e for e in esperadas if clave_norma(e) not in extraidas]
    return faltantes


# ===========================================================================
# DESCUBRIMIENTO
# ===========================================================================
_SESION = None


def sesion():
    global _SESION
    if _SESION is None:
        _SESION = requests.Session()
        _SESION.headers.update(HEADERS_WEB)
    return _SESION


def url_boletin(numero, anio):
    return f'{BASE_PDF}/{anio}/{numero}-{anio}.pdf'


def descargar(url, timeout=90, esperar_pdf=True):
    for intento in range(1, REINTENTOS + 1):
        try:
            r = sesion().get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            if r.status_code == 200:
                if not esperar_pdf:
                    return r.text
                return r.content if r.content[:5] == b'%PDF-' else None
            if r.status_code < 500:
                return None
        except requests.RequestException as e:
            if intento == REINTENTOS:
                raise RuntimeError(f"Error de red pidiendo {url}: {e}")
        time.sleep(ESPERA_REINTENTO * intento)
    return None


RE_HREF_PDF = re.compile(
    r'/wp-content/uploads/\d{4}/Boletines/(?P<anio>\d{4})/(?P<numero>\d{1,4})-(?P=anio)\.pdf',
    re.IGNORECASE)


def leer_calendario(anio=None, mes=None):
    """
    Devuelve la lista [(numero, anio, url, sumario)] que publica el calendario,
    ordenada por número de boletín.

    El sumario sale del enlace cuyo texto es más largo entre los que apuntan al
    mismo PDF: WordPress repite el enlace, uno con el título corto y otro con el
    índice completo del boletín.
    """
    url = URL_CALENDARIO
    if anio and mes:
        url += f'&month={MESES_EN[mes - 1]}&yr={anio}'
    html = descargar(url, timeout=45, esperar_pdf=False)
    if not html:
        return []

    sumarios = {}
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a', href=True):
            m = RE_HREF_PDF.search(a['href'])
            if not m:
                continue
            texto = _compacto(a.get_text(' '))
            clave = (m.group('numero'), m.group('anio'))
            if len(texto) > len(sumarios.get(clave, '')):
                sumarios[clave] = texto
    else:
        print("Aviso: falta beautifulsoup4; el sumario del calendario no se puede leer",
              file=sys.stderr)

    encontrados = {}
    for m in RE_HREF_PDF.finditer(html):
        clave = (m.group('numero'), m.group('anio'))
        encontrados[clave] = sumarios.get(clave, '')

    salida_ = [(int(n), int(a), url_boletin(int(n), int(a)), s)
               for (n, a), s in encontrados.items()]
    salida_.sort()
    return salida_


def buscar_boletin(numero=None, anio=None):
    """
    (contenido, url, numero, sumario) del boletín más nuevo disponible.

    1. Lee el calendario del mes en curso (y el anterior si estamos en los
       primeros días del mes y todavía no hay nada publicado).
    2. Tantea los correlativos siguientes: el PDF suele subirse antes de que la
       celda del calendario aparezca.
    """
    hoy = date.today()
    anio = anio or hoy.year

    if numero:
        contenido = descargar(url_boletin(numero, anio))
        return contenido, url_boletin(numero, anio), numero, ''

    entradas = leer_calendario()
    if not entradas:
        mes_ant = hoy.month - 1 or 12
        anio_ant = anio if hoy.month > 1 else anio - 1
        entradas = leer_calendario(anio_ant, mes_ant)
    if not entradas:
        return None, None, None, ''

    entradas = [e for e in entradas if e[1] == anio] or entradas
    ultimo_num, ultimo_anio, ultima_url, ultimo_sumario = entradas[-1]

    # Tanteo del correlativo: puede haber PDF sin celda todavía.
    mejor = (None, None, None, '')
    for salto in range(TANTEO_CORRELATIVO, 0, -1):
        cand = ultimo_num + salto
        contenido = descargar(url_boletin(cand, ultimo_anio))
        if contenido:
            print(f"Boletín Nº {cand} encontrado por correlativo "
                  f"(el calendario sólo llegaba al {ultimo_num})", file=sys.stderr)
            return contenido, url_boletin(cand, ultimo_anio), cand, ''
    del mejor

    contenido = descargar(ultima_url)
    return contenido, ultima_url, ultimo_num, ultimo_sumario


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

    Decretos y leyes van por poder: los firma el Gobernador o la Legislatura, y
    su numeración es única en la provincia, así que mandarlos por organismo sólo
    lograría que el mismo decreto entre dos veces con emisores distintos.

    Las resoluciones van SIEMPRE por organismo, y esto no es opcional: los
    números se repiten entre organismos ("RESOLUCION Nº 240-SOTyH" y
    "RESOLUCION Nº 240-E" son normas distintas) y el backend deduplica por
    tipo|numero|anio|emisor. Con un emisor genérico, la segunda se pierde.
    """
    tipo = str(norma.get('tipo') or '')
    organismo = _compacto(norma.get('emisor') or '')
    if usar_organismo and organismo:
        return organismo
    # Un "DECRETO Nº 1609.26.040" de la sección municipios lo firma un
    # intendente, no el Gobernador: nunca puede salir como PODER EJECUTIVO.
    if norma.get('seccion') == SECCION_MUNICIPIOS:
        return organismo or 'MUNICIPIO'
    if tipo.startswith('LEY'):
        return 'PODER LEGISLATIVO'
    if tipo.startswith('DECRETO'):
        return 'PODER EJECUTIVO'
    if tipo.startswith('ORDENANZA'):
        return organismo or 'CONCEJO DELIBERANTE'
    return organismo or 'PODER EJECUTIVO'


def construir_sintesis(norma):
    cuerpo = _compacto(norma.get('titulo') or norma.get('articulo1') or '')
    cuerpo = cuerpo.strip(' .-:')
    if len(cuerpo) > MAX_SINTESIS:
        cuerpo = cuerpo[:MAX_SINTESIS].rsplit(' ', 1)[0] + '…'
    return cuerpo or f"{norma.get('tipo')} {norma.get('numero')}"


def recortar_texto(texto, tope=MAX_TEXTO_COMPLETO):
    """
    Recorta conservando el principio Y EL FINAL.

    En los decretos largos (los que sí traen VISTO y CONSIDERANDO) el exordio se
    lleva casi todo y el articulado, que es lo que dice qué resuelve la norma, va
    al final. Truncar desde el principio le manda al backend justo la parte que
    no sirve para categorizar.
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
    Jujuy no publica una URL por norma (todas viven en el mismo PDF), así que se
    usa la URL del boletín más un fragmento único. Es obligatorio: el backend
    deduplica por url_norma EXACTA y sin el fragmento la primera norma guardada
    bloquea a todas las demás del boletín. La sigla entra en el fragmento porque
    el número solo no distingue una resolución de otra.
    """
    base = f"{norma.get('tipo')}-{norma.get('numero')}-{norma.get('sigla') or 'SN'}-{norma.get('anio')}"
    slug = re.sub(r'[^A-Za-z0-9]+', '-', _sin_acentos(base)).strip('-')
    return f"{url_pdf}#{slug}"


# ===========================================================================
# EJECUCIÓN
# ===========================================================================
def _main():
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Jujuy.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se usa el calendario oficial')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--pdf', metavar='ARCHIVO', help='usar un PDF local (pruebas)')
    ap.add_argument('--texto', metavar='ARCHIVO',
                    help='usar un .txt ya extraído del PDF (pruebas del parser)')
    ap.add_argument('--sumario', metavar='ARCHIVO',
                    help='sumario del calendario en un .txt (para usar junto con --pdf)')
    ap.add_argument('--boletin', type=int, help='número de boletín a procesar')
    ap.add_argument('--anio', type=int, help='año del boletín (default: el actual)')
    ap.add_argument('--todas', action='store_true',
                    help='muestra también las individuales, con puntaje y motivos')
    ap.add_argument('--sin-filtro', action='store_true', help='envía todo sin filtrar')
    ap.add_argument('--municipios', action='store_true',
                    help='suma la sección MUNICIPIOS - COMISIONES MUNICIPALES')
    ap.add_argument('--licitaciones', action='store_true',
                    help='suma la sección LICITACIONES - CONCURSO DE PRECIOS')
    ap.add_argument('--emisor-organismo', action='store_true',
                    help='manda también decretos y leyes por organismo')
    ap.add_argument('--fuente-sumario', choices=['auto', 'calendario', 'pdf'],
                    default='auto',
                    help='de dónde sacar la lista de normas (default: auto, '
                         'intenta el calendario y cae al PDF)')
    ap.add_argument('--volcar', action='store_true', help='imprime sumario y bloques y sale')
    args = ap.parse_args()

    secciones = [SECCION_NORMATIVA]
    if args.municipios:
        secciones.append(SECCION_MUNICIPIOS)
    if args.licitaciones:
        secciones.append(SECCION_LICITACIONES)

    ruta_temporal = None
    url_pdf = ''
    texto_sumario = ''
    numero_boletin = args.boletin

    # ---- 1. Conseguir el boletín -----------------------------------------
    paginas = None
    if args.texto:
        with open(args.texto, encoding='utf-8') as f:
            crudo = f.read()
        # Se reconstruyen las páginas cortando ANTES de cada encabezado
        # repetido ("Julio, 06 de 2026.-"). Queda el banner de sección al final
        # de su página, que es justo donde lo pone pdfplumber.
        partes = re.split(r'\f|(?=^[ \t]*[A-Za-zÁÉÍÓÚáéíóúñÑ]+,\s*\d{1,2}\s+de\s+\d{4}\s*\.?-)',
                          crudo, flags=re.MULTILINE)
        paginas = [p for p in partes if p.strip()] or [crudo]
        print(f"Usando texto local: {args.texto} ({len(paginas)} páginas)", file=sys.stderr)
    elif args.pdf:
        ruta_pdf = args.pdf
        print(f"Usando PDF local: {args.pdf}", file=sys.stderr)
    else:
        try:
            contenido, url_pdf, numero_boletin, texto_sumario = buscar_boletin(
                args.boletin, args.anio)
        except RuntimeError as e:
            salida("error", str(e))
        if not contenido:
            salida("warning", "No se encontró ningún boletín publicado en el calendario.")
        print(f"Boletín Nº {numero_boletin}: {url_pdf}", file=sys.stderr)
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.write(contenido)
        tmp.close()
        ruta_pdf = ruta_temporal = tmp.name

    if args.sumario:
        with open(args.sumario, encoding='utf-8') as f:
            texto_sumario = f.read()

    # ---- 2. Parsear -------------------------------------------------------
    try:
        if paginas is None:
            paginas = leer_paginas(ruta_pdf)
        num_tapa, fecha_boletin = metadatos_boletin(paginas)
        numero_boletin = numero_boletin or num_tapa
        anio_boletin = (fecha_boletin or '')[:4] or str(args.anio or date.today().year)
        cuerpo = limpiar_cuerpo(paginas)

        # El sumario del calendario es el camino bueno: es el único control de
        # cobertura que existe. Si no está (PDF local, sitio caído, falta bs4),
        # se deduce del propio PDF y se avisa, pero no se aborta.
        origen_sumario = 'calendario'
        if not texto_sumario and numero_boletin and args.fuente_sumario != 'pdf':
            try:
                entradas = leer_calendario()
                if not entradas:
                    print("Aviso: el calendario no devolvió boletines "
                          "(¿sin red, o falta beautifulsoup4?)", file=sys.stderr)
                for entrada in entradas:
                    if str(entrada[0]) == str(numero_boletin):
                        texto_sumario = entrada[3]
                        break
                if entradas and not texto_sumario:
                    print(f"Aviso: el calendario no tiene el boletín Nº "
                          f"{numero_boletin} en el mes en curso", file=sys.stderr)
            except Exception as e:
                print(f"Aviso: no se pudo leer el calendario: {e}", file=sys.stderr)

        esperadas, sin_parsear = [], []
        if texto_sumario and args.fuente_sumario != 'pdf':
            esperadas, sin_parsear = leer_sumario(texto_sumario, secciones, anio_boletin)
        if not esperadas and args.fuente_sumario != 'calendario':
            esperadas, aviso = sumario_desde_pdf(paginas, secciones, anio_boletin)
            origen_sumario = 'pdf'
            print(f"Aviso: {aviso}", file=sys.stderr)

        normas = extraer_normas(cuerpo, esperadas, fecha_boletin, anio_boletin)
    except Exception as e:
        salida("error", f"No se pudo parsear el boletín: {e}")
    finally:
        if ruta_temporal:
            try:
                os.unlink(ruta_temporal)
            except Exception:
                pass

    if not esperadas:
        print("--- BANNERS DE SECCIÓN DETECTADOS POR PÁGINA ---", file=sys.stderr)
        for i, nombres in sorted(banners_por_pagina(paginas).items()):
            print(f"  pág {i + 1}: {', '.join(nombres)}", file=sys.stderr)
        salida("warning",
               f"No se reconoció ninguna norma en la sección '{SECCION_NORMATIVA}' "
               f"(origen del sumario: {origen_sumario}). Ver el detalle de banners "
               f"por página en la salida de error.")

    if args.volcar:
        print(f"--- PDF: {len(paginas)} páginas | sumario: {origen_sumario} ---",
              file=sys.stderr)
        for i, nombres in sorted(banners_por_pagina(paginas).items()):
            print(f"  banner pág {i + 1}: {', '.join(nombres)}", file=sys.stderr)
        print(f"--- SUMARIO: {len(esperadas)} normas anunciadas ---", file=sys.stderr)
        for e in esperadas:
            print(f"  {e['codigo']:38s} {e['tipo']:18s} {e['numero']:>6s}"
                  f"-{e.get('sigla', ''):10s}/{e['anio']}", file=sys.stderr)
        for s in sin_parsear:
            print(f"  (sin código) {s[:80]}", file=sys.stderr)
        print(f"--- CUERPO: {len(normas)} bloques ---", file=sys.stderr)
        for n in normas:
            print(f"  {n['codigo']:38s} {len(n['texto_completo']):6d} car. "
                  f"| {str(n['emisor'])[:30]:30s} | {n['titulo'][:50]}", file=sys.stderr)
        salida("success", f"volcado: {len(esperadas)} en el sumario, "
                          f"{len(normas)} bloques en el cuerpo.")

    # Control de cobertura ANTES de filtrar nada.
    faltantes = comparar_con_sumario(esperadas, normas)
    print(f"Sumario: anuncia {len(esperadas)} normas, se extrajeron {len(normas)} "
          f"({len(faltantes)} faltantes)", file=sys.stderr)
    for f in faltantes[:15]:
        print(f"  FALTA   {f['tipo']} {f['numero']}-{f.get('sigla', '')}/{f['anio']}",
              file=sys.stderr)
    for s in sin_parsear[:10]:
        print(f"  SIN CÓDIGO EN EL SUMARIO: {s[:70]}", file=sys.stderr)

    generales = [n for n in normas if not n['es_individual']]
    individuales = [n for n in normas if n['es_individual']]
    a_enviar = normas if args.sin_filtro else generales

    guardar_debug(json.dumps(normas, ensure_ascii=False, indent=2, default=str),
                  'debug_jujuy.json')
    print(f"Boletín {numero_boletin or '?'} del {fecha_boletin} | páginas: {len(paginas)} "
          f"| normas: {len(normas)} (generales {len(generales)} / "
          f"individuales {len(individuales)})", file=sys.stderr)

    # ---- 3. Prueba --------------------------------------------------------
    if args.dry_run:
        for n in (normas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {str(n['tipo']):18s} N° {str(n['numero']):>6s}"
                  f"-{str(n.get('sigla') or ''):10s}/{n['anio']} "
                  f"{emisor_final(n, args.emisor_organismo)[:34]:34s} "
                  f"{len(n['texto_completo']):6d} car.  {n['titulo'][:46]}", file=sys.stderr)
            if args.todas and n['motivos']:
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    if not normas:
        salida("warning", "No se reconoció ninguna norma en la sección normativa.")
    if not a_enviar:
        salida("warning", f"Las {len(individuales)} normas del boletín son actos "
                          f"individuales; no se envió ninguna.")

    if fecha_boletin and verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

    # ---- 4. Envío ---------------------------------------------------------
    payload = [{
        "id_jurisdiccion": args.id_jurisdiccion,
        "nombre_emisor": emisor_final(n, args.emisor_organismo),
        "tipo_norma_desc": n["tipo"],
        "numero": n["numero"],
        "anio": n["anio"],
        "fecha_publicacion": n["fecha_publicacion"],
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

    # El aviso de cobertura va en un campo aparte, NO en el status: el frontend
    # sólo refresca la grilla cuando recibe 'success'.
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