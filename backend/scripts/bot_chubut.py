"""
bot_chubut.py
===============================================================================
Scraper del Boletín Oficial de la Provincia del Chubut.

Uso normal:
    python bot_chubut.py <id_jurisdiccion> "https://boletin.chubut.gov.ar/"

Modos de prueba (no tocan el backend):
    python bot_chubut.py 6 --dry-run
    python bot_chubut.py 6 --dry-run --pdf "Julio 22, 2026.pdf"
    python bot_chubut.py 6 --dry-run --fecha 2026-07-22
    python bot_chubut.py 6 --dry-run --todas

-------------------------------------------------------------------------------
DESCUBRIMIENTO
-------------------------------------------------------------------------------
Chubut no necesita scrapear una grilla: los PDFs viven en una URL predecible
armada con la fecha, p. ej.

    https://boletin.chubut.gov.ar/archivos/boletines/Julio%2022,%202026.pdf

o sea "<Mes> <día>, <año>.pdf" con el mes en castellano y capitalizado. El bot
arranca en la fecha pedida (o la de hoy), y si no encuentra el archivo va
retrocediendo días hábiles hasta dar con el boletín más reciente. Se publica de
lunes a viernes, así que los fines de semana se saltean.

El día va con cero adelante ("Junio 05, 2026.pdf"); igual se prueba la forma
sin cero como respaldo, y "Septiembre"/"Setiembre" por las dudas.

Chubut es id_jurisdiccion = 6.

-------------------------------------------------------------------------------
ESTRUCTURA DEL PDF
-------------------------------------------------------------------------------
Maqueta de diario a DOS COLUMNAS (como Córdoba). El texto es nativo: no hace
falta OCR.

  - Página 1: tapa con autoridades y SUMARIO (índice). Se usa para la fecha, el
    número de edición y, sobre todo, como ORÁCULO: el sumario lista exactamente
    qué normas trae la Sección Oficial, así que el bot compara lo extraído
    contra esa lista y avisa si perdió algo (ver leer_sumario).
  - El cuerpo se divide en dos secciones marcadas con un banner grande (24pt):
    "Sección Oficial" y "Sección General". Sólo interesa la primera; se corta
    al llegar al banner de la segunda.
  - Dentro de la Sección Oficial hay TRES niveles, y no se distinguen por
    tamaño (ver el bloque MAQUETA más abajo):
      * subsección  -> el TIPO ("DECRETOS SINTETIZADOS", "RESOLUCIONES")
      * organismo   -> el EMISOR ("PODER JUDICIAL", "MINISTERIO DE GOBIERNO")
      * encabezado  -> abre la norma ("Dto. N° 1012 16-07-26",
                       "RESOLUCIÓN ADMINISTRATIVA GENERAL N°14061/2026")
    Lo que decide es si la línea en negrita trae "N° <número>". El cuerpo va en
    ~8pt sin negrita y cada publicación cierra con "I: 17-07-26 V: 21-07-26".

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

BASE_PDF = 'https://boletin.chubut.gov.ar/archivos/boletines/'

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
# MAQUETA
# ===========================================================================
# Medido sobre las ediciones 14893, 14894 y 14895 (20, 21 y 22/07/2026):
#
#   24 pt negrita -> banner de sección ("Sección Oficial" / "Sección General")
#   11 pt negrita -> subsección = TIPO ("DECRETOS SINTETIZADOS", "RESOLUCIONES",
#                    "REGISTRO DE PUBLICIDAD OFICIAL"). A veces el ORGANISMO
#                    también sale en 11 pt ("MINISTERIO DE GOBIERNO", ed. 14894).
#    9 pt negrita -> encabezado de decreto ("Dto. N° 1012 16-07-26")
#    8 pt negrita -> encabezado de resolución/registro Y organismo emisor
#                    ("PODER JUDICIAL", "RESOLUCIÓN ADMINISTRATIVA GENERAL
#                    N°14061/2026", "REGISTRO N° 106383")
#    8 pt normal  -> cuerpo
#
# El tamaño NO alcanza para distinguir encabezado de emisor: conviven en 8 pt
# negrita. Lo que decide es si la línea trae "N° <número>".
#
# El umbral anterior (8.5) dejaba afuera TODOS los encabezados de 8 pt, así que
# el bot sólo veía los decretos y perdía en silencio las resoluciones.
TAM_BANNER_SECCION = 14      # "Sección Oficial" va en 24pt; el umbral es holgado
TAM_SUBSECCION_MIN = 10.5    # "DECRETOS SINTETIZADOS" ~11pt
TAM_ENCABEZADO_MIN = 7.5     # encabezados de resolución/registro ~8pt

MARGEN_SUPERIOR = 58         # debajo del encabezado de página
MARGEN_INFERIOR = 30         # arriba del pie

RE_SECCION_OFICIAL = re.compile(r'^secci[óo]n\s+oficial$', re.IGNORECASE)
RE_SECCION_GENERAL = re.compile(r'^secci[óo]n\s+general$', re.IGNORECASE)
RE_PIE_PAGINA = re.compile(
    r'^(P[ÁA]GINA\s+\d+|BOLET[ÍI]N\s+OFICIAL)\b|BOLET[ÍI]N\s+OFICIAL\s+P[ÁA]GINA\s+\d+',
    re.IGNORECASE)

# Encabezado de norma. Un solo patrón para las formas que aparecen realmente:
#   "Dto. N° 1012 16-07-26"                        (decreto)
#   "RESOLUCIÓN ADMINISTRATIVA GENERAL N°14061/2026" (viene partido en 2 líneas)
#   "RESOLUCIÓN N° 84/2026 IGJ"
#   "Resolución II N° 42" / "Res. XXVI N° 09"      (romano = libro del Digesto)
#   "REGISTRO N° 106383"
#   "ACUERDO REGISTRADO BAJO EL N° 186 /26"        (Tribunal de Cuentas)
# El grupo <clase> es no codicioso: prueba primero sin modificadores, así
# "Resolución II N° 42" deja "II" en <rom> y no lo confunde con parte del tipo.
# Los modificadores admiten palabras de dos letras porque el Tribunal de Cuentas
# encabeza con "ACUERDO REGISTRADO BAJO EL N° …": exigiendo tres letras, "EL"
# no entraba y los treinta acuerdos de la ed. 14896 no se reconocían.
RE_NORMA = re.compile(
    r'^(?P<clase>(?:DTOS?|DECRETOS?|LEYE?S?|RES|RESOL|RESOLUCI[OÓ]N(?:ES)?|'
    r'DISP|DISPOSICI[OÓ]N(?:ES)?|ACORDADAS?|ACUERDOS?|REG|REGISTROS?)\.?'
    r'(?:\s+[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ]{1,}\.?){0,3}?)'
    r'\s*(?P<rom>[IVXLC]{1,6})?'
    r'\s*N\s*[°ºo\.]\s*(?P<num>\d{1,7})'
    r'(?:\s*/\s*(?P<anio>\d{2,4}))?'
    r'(?P<resto>.{0,45})$',
    re.IGNORECASE)

# Líneas en negrita que NO son ni tipo ni emisor (fórmulas del cuerpo).
RE_RUIDO = re.compile(
    r'^(VISTO|CONSIDERANDO|RESUELVE|RESUELVO|RESOLVIÓ|POR ELLO|DECRETA|'
    r'ANEXO|ART[IÍ]CULO|ARTICULO|\(Ver)', re.IGNORECASE)

# Pie de cada publicación: "I: 17-07-26 V: 21-07-26" (inicio/vencimiento) o
# "P: 20-07-26" (publicación única). Cierra la norma en curso.
RE_VIGENCIA = re.compile(r'^[IVP]\s*:\s*\d{1,2}-\d{1,2}-\d{2,4}')

# Tipo de norma a partir del encabezado de subsección o del propio encabezado.
# Se conserva el calificativo porque el boletín lo usa para distinguir
# ("Decreto Sintetizado" no es lo mismo que "Decreto"), igual que hace el bot
# de Nación. Todo lo demás de la frase se descarta: "REGISTRO DE PUBLICIDAD
# OFICIAL" -> "REGISTRO".
_NUCLEOS = {'DECRETO', 'LEY', 'RESOLUCION', 'DISPOSICION',
            'REGISTRO', 'ACUERDO', 'ACORDADA'}
_MODIFICADORES = {'SINTETIZADO', 'SINTETIZADA', 'ADMINISTRATIVA', 'GENERAL',
                  'CONJUNTA', 'MINISTERIAL'}
_ABREV = {'DTO': 'DECRETO', 'DTOS': 'DECRETO', 'RES': 'RESOLUCION',
          'RESOL': 'RESOLUCION', 'DISP': 'DISPOSICION', 'REG': 'REGISTRO',
          'ADM': 'ADMINISTRATIVA', 'GRAL': 'GENERAL', 'SINT': 'SINTETIZADO'}
_SINGULAR = {'DECRETOS': 'DECRETO', 'RESOLUCIONES': 'RESOLUCION',
             'LEYES': 'LEY', 'DISPOSICIONES': 'DISPOSICION',
             'REGISTROS': 'REGISTRO', 'ACUERDOS': 'ACUERDO',
             'ACORDADAS': 'ACORDADA', 'SINTETIZADOS': 'SINTETIZADO',
             'SINTETIZADAS': 'SINTETIZADA',
             'ADMINISTRATIVAS': 'ADMINISTRATIVA', 'GENERALES': 'GENERAL'}


def _tipo_desde(texto):
    """'DECRETOS SINTETIZADOS' -> 'DECRETO SINTETIZADO'. None si no reconoce."""
    crudo = _sin_acentos(texto or '').upper()
    palabras = []
    for p in re.split(r'[^A-Z]+', crudo):
        if not p:
            continue
        p = _ABREV.get(p, p)
        p = _SINGULAR.get(p, p)
        palabras.append(p)
    if not palabras or palabras[0] not in _NUCLEOS:
        return None
    tipo = [palabras[0]]
    for p in palabras[1:]:
        if p in _MODIFICADORES:
            tipo.append(p)
        elif p in _NUCLEOS:
            break
    return ' '.join(tipo[:3])


def _compacto(texto):
    """
    Rearma las palabras que el PDF parte por kerning: la edición 14893 trae
    'R EGISTRO N° 106384' en vez de 'REGISTRO N° 106384'. Sólo se usa como
    segundo intento al matchear encabezados, nunca sobre el cuerpo.
    """
    return re.sub(r'\b([A-ZÁÉÍÓÚÑ])\s+(?=[A-ZÁÉÍÓÚÑ]{2,})', r'\1', texto)


# Un encabezado de organismo empieza siempre con una palabra institucional.
# Sin esta lista blanca, cualquier línea en mayúsculas y negrita pasaba por
# emisor: en la ed. 14868 el TÍTULO de la ley ("INSTITUCIONALIZAR, EN EL ÁMBITO
# DE LA…") y la fórmula de sanción ("LA LEGISLATURA… SANCIONA CON FUERZA DE
# LEY") se tomaban por organismos, y como un emisor cierra la norma en curso,
# la ley quedaba con 41 caracteres y se perdía todo el articulado.
# Si aparece un organismo con un encabezamiento no previsto, no se lo reconoce
# y la norma cae en el emisor por defecto: se pierde precisión, no contenido.
_PALABRAS_ORGANISMO = {
    'PODER', 'MINISTERIO', 'SECRETARIA', 'SUBSECRETARIA', 'DIRECCION',
    'INSPECCION', 'INSTITUTO', 'ADMINISTRACION', 'TRIBUNAL', 'SUPERIOR',
    'CONSEJO', 'COMISION', 'AGENCIA', 'ENTE', 'SERVICIO', 'UNIDAD',
    'FISCALIA', 'DEFENSORIA', 'PROCURACION', 'ASESORIA', 'ESCRIBANIA',
    'CONTADURIA', 'TESORERIA', 'POLICIA', 'BANCO', 'HOSPITAL',
    'MUNICIPALIDAD', 'DEPARTAMENTO', 'JEFATURA', 'GERENCIA', 'COORDINACION',
    'HONORABLE', 'LEGISLATURA',
}

# Continuación de un nombre de organismo partido en dos renglones. Se detecta
# de los dos lados porque el corte no siempre cae en una preposición:
#   "ADMINISTRACIÓN PORTUARIA DEL PUERTO" / "DE COMODORO RIVADAVIA"
#   "SECRETARÍA DE INFRAESTRUCTURA,"      / "ENERGÍA Y PLANIFICACIÓN"
# En el segundo caso la pista es la coma colgando al final del primer renglón.
RE_CONTINUA_EMISOR = re.compile(r'^(DE|DEL|Y|E|LA|EL|LOS|LAS)\b', re.IGNORECASE)
RE_EMISOR_COLGADO = re.compile(r'(,|\b(?:DE|DEL|Y|E|LA|EL|LOS|LAS))\s*$', re.IGNORECASE)


def _es_emisor(texto):
    """
    ¿La línea es el nombre de un organismo? Se aplica sólo a líneas en negrita
    que ya se descartaron como tipo y como encabezado de norma.
    """
    t = texto.strip()
    if not (5 <= len(t) <= 90):
        return False
    if t.endswith(':') or re.search(r'\d', t):
        return False
    if RE_RUIDO.match(t):
        return False
    if t != t.upper() or not any(c.isalpha() for c in t):
        return False
    primera = re.split(r'[^A-ZÁÉÍÓÚÑ]+', _sin_acentos(t).upper())
    primera = [p for p in primera if p]
    if not primera:
        return False
    # "LA INSPECCIÓN…" y similares: se saltea el artículo inicial.
    if primera[0] in ('LA', 'EL', 'LOS', 'LAS') and len(primera) > 1:
        primera = primera[1:]
    return primera[0] in _PALABRAS_ORGANISMO


def _sin_acentos(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s or '')
                   if unicodedata.category(c) != 'Mn')


# ===========================================================================
# CLASIFICACIÓN: ACTO GENERAL vs INDIVIDUAL
# ---------------------------------------------------------------------------
# Mismo criterio que Catamarca y Chaco: el boletín mezcla normativa de alcance
# general con actos que afectan a una persona determinada (designaciones, bajas,
# retiros, licencias). Esos no son normativa de interés y arrastran datos
# personales, así que se descartan del envío.
# ===========================================================================
UMBRAL_INDIVIDUAL = 2

PATRONES_INDIVIDUALES = [
    (r'Des[ií]gn[ae]se[\s\S]{0,60}(?:en el cargo|como)', 3, 'designación'),
    # Ojo: la sola MENCIÓN de la palabra no alcanza. En la ed. 14893 aparece en
    # el orden del día de una asamblea ("Designación de dos asociados para
    # firmar el acta") y en la 14894 en una cita reglamentaria ("rechazaren la
    # designación"). Con peso 2 decidía sola y clasificaba mal; ahora suma pero
    # necesita otra señal, igual que el DNI.
    (r'\bDesignaci[óo]n\b',                              1, 'menciona designación'),
    (r'^\s*DESIGNAR\b|ARTICULO\s*\d+°?\.?-?\s*DESIGNAR', 3, 'designación'),
    # Actos de alcance particular vistos en las ediciones 14893/14894: no son
    # normativa general aunque salgan en la Sección Oficial.
    (r'Declarar\s+(?:fracasado|desierto)',               3, 'concurso fracasado/desierto'),
    (r'CONVOCAR a Asamblea',                             2, 'convocatoria a asamblea de una entidad'),
    (r'Dejar sin efecto la Adjudicaci[óo]n',             3, 'baja de adjudicación'),
    (r'D[ée]jase sin efecto[\s\S]{0,60}designaci[óo]n',  3, 'cese de designación'),
    (r'Ac[ée]ptase la renuncia',                         3, 'renuncia'),
    (r'\bRetiro (?:voluntario|obligatorio)\b',           3, 'retiro'),
    (r'Otórg[au]se[\s\S]{0,40}licencia',                 3, 'licencia'),
    (r'\bCesant[íi]a\b',                                 3, 'cesantía'),
    (r'Prom[ué]v[ea]se',                                 2, 'promoción'),
    (r'Recon[óo]zcase[\s\S]{0,40}servicios',             2, 'reconocimiento de servicios'),
    (r'Trasl[áa]d[ae]se',                                2, 'traslado de personal'),
    (r'Ap[lí]iquese[\s\S]{0,40}sanci[óo]n',              3, 'sanción'),
]

PATRONES_GENERALES = [
    (r'Ratif[íi]c(?:ase|anse)',                         -3, 'ratificación'),
    (r'Apru[ée]b(?:ase|anse)',                          -2, 'aprobación'),
    (r'Ex[íi]mase del pago',                            -2, 'exención'),
    (r'Prom[úu]lg(?:ase|uese)',                         -4, 'promulgación de ley'),
    (r'Decl[áa]rase de (?:inter[ée]s|utilidad)',        -3, 'declaración de interés'),
    (r'Adju[dd][íi]c(?:ase|anse)',                      -2, 'adjudicación'),
    (r'Autor[íi]zase[\s\S]{0,40}(?:llamado|licitaci)',  -2, 'licitación'),
    (r'Modif[íi]c(?:ase|anse)[\s\S]{0,40}(?:Decreto|Ley|Resoluci)', -2, 'modificación normativa'),
    (r'\bReglam[ée]ntase\b',                            -3, 'reglamentación'),
]

RE_DOCUMENTO = re.compile(r'\b(?:D\.?N\.?I|CUIL|CUIT|M\.?I\.?)\b', re.IGNORECASE)


# Emisores con regla propia, sin importar el texto. Mismo criterio que se tomó
# en Chaco: TODO lo que dicta el Tribunal de Cuentas son rendiciones de cuentas.
# En Chubut aparecen bajo DOS encabezados distintos, y los dos son lo mismo:
#   "ACUERDO REGISTRADO BAJO EL N° 186 /26"  -> aprueba una rendición
#   "RESOLUCION DEL TRIBUNAL N° 110 /26"     -> emplaza por una rendición
# En la ed. 14896 son 43 de 48 normas. Se pueden volver a incluir con
# --con-tribunal-cuentas, porque es una decisión de criterio y no técnica.
RE_EMISOR_SIEMPRE_INDIVIDUAL = re.compile(r'TRIBUNAL\s+DE\s+CUENTAS', re.IGNORECASE)


def clasificar_norma(texto, emisor=None, regla_emisor=True):
    """Devuelve (es_individual, puntaje, motivos)."""
    puntaje, motivos = 0, []
    if regla_emisor and emisor and RE_EMISOR_SIEMPRE_INDIVIDUAL.search(emisor):
        return True, UMBRAL_INDIVIDUAL, ['emisor Tribunal de Cuentas (rendición de cuentas)']
    for patron, peso, etiqueta in PATRONES_INDIVIDUALES:
        if re.search(patron, texto, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'+{peso} {etiqueta}')
    for patron, peso, etiqueta in PATRONES_GENERALES:
        if re.search(patron, texto, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'{peso} {etiqueta}')
    docs = len(RE_DOCUMENTO.findall(texto))
    if docs:
        puntaje += 1
        motivos.append(f'+1 menciona DNI/CUIL ({docs})')
    return (puntaje >= UMBRAL_INDIVIDUAL), puntaje, motivos


# ===========================================================================
# LECTURA DEL PDF (dos columnas)
# ===========================================================================
def _canal_columnas(pagina):
    """
    Ubica el canal vertical vacío que separa las dos columnas.
    Devuelve la coordenada X del corte, o None si la página es de una sola
    columna (tapa, tablas a ancho completo).
    """
    ancho = int(pagina.width) + 2
    ocupacion = [0] * ancho
    alto = pagina.height
    for w in pagina.extract_words():
        if w['top'] < MARGEN_SUPERIOR or w['top'] > alto - MARGEN_INFERIOR:
            continue
        for x in range(int(w['x0']), min(ancho - 1, int(w['x1']) + 1)):
            ocupacion[x] += 1

    vacios = [x for x in range(60, int(pagina.width) - 50) if ocupacion[x] == 0]
    if not vacios:
        return None
    grupos, actual = [], [vacios[0]]
    for x in vacios[1:]:
        if x == actual[-1] + 1:
            actual.append(x)
        else:
            grupos.append(actual)
            actual = [x]
    grupos.append(actual)

    mayor = max(grupos, key=len)
    centro = (mayor[0] + mayor[-1]) / 2
    # sólo vale si es ancho y cae cerca del medio de la página
    if len(mayor) > 3 and abs(centro - pagina.width / 2) < 60:
        return centro
    return None


def _lineas(palabras):
    """Agrupa palabras en líneas por su coordenada vertical."""
    palabras = sorted(palabras, key=lambda w: (round(w['top'] / 2), w['x0']))
    grupos, actual, top = [], [], None
    for w in palabras:
        t = round(w['top'] / 2) * 2
        if top is None or abs(t - top) <= 2:
            actual.append(w)
            top = t if top is None else top
        else:
            grupos.append(actual)
            actual, top = [w], t
    if actual:
        grupos.append(actual)

    salida = []
    for g in grupos:
        g.sort(key=lambda w: w['x0'])
        salida.append({
            'texto': ' '.join(w['text'] for w in g).strip(),
            'tam': round(max(w['size'] for w in g), 1),
            'bold': any('Bold' in w['fontname'] for w in g),
        })
    return salida


def _lineas_de_pagina(pagina):
    """Líneas en orden de lectura: columna izquierda completa y luego la derecha."""
    alto = pagina.height
    palabras = [w for w in pagina.extract_words(extra_attrs=['fontname', 'size'])
                if MARGEN_SUPERIOR < w['top'] < alto - MARGEN_INFERIOR]
    if not palabras:
        return []
    corte = _canal_columnas(pagina)
    if corte is None:
        return _lineas(palabras)
    izquierda = [w for w in palabras if w['x0'] < corte]
    derecha = [w for w in palabras if w['x0'] >= corte]
    return _lineas(izquierda) + _lineas(derecha)


def leer_seccion_oficial(ruta_pdf, recorte=False):
    """
    Devuelve las líneas (con estilo) que están entre el banner "Sección Oficial"
    y el banner "Sección General". Si no encuentra los banners, devuelve [].

    Con recorte=True arranca a recolectar desde la primera línea: sirve para
    diagnosticar extractos de pocas páginas, que no traen la tapa ni el banner.
    NO usar en producción: sin el banner de cierre entraría toda la Sección
    General (edictos sucesorios, constituciones de sociedades, licitaciones).
    """
    if pdfplumber is None:
        raise RuntimeError("Falta 'pdfplumber' (pip install pdfplumber).")

    recolectando = bool(recorte)
    lineas = []
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            for linea in _lineas_de_pagina(pagina):
                texto = linea['texto'].strip()
                if not texto:
                    continue
                if linea['tam'] >= TAM_BANNER_SECCION:
                    if RE_SECCION_OFICIAL.match(texto):
                        recolectando = True
                        continue
                    if RE_SECCION_GENERAL.match(texto):
                        return lineas          # termina la sección oficial
                if recolectando and not RE_PIE_PAGINA.match(texto):
                    lineas.append(linea)
    return lineas


def metadatos_boletin(ruta_pdf):
    """Número de edición y fecha de portada. Devuelve (numero, fecha_iso)."""
    with pdfplumber.open(ruta_pdf) as pdf:
        texto = pdf.pages[0].extract_text() or ''
    numero = None
    # Anclado al encabezado "AÑO LXIX- N°14895": buscar sólo "N° <dígitos>"
    # tomaba la cuenta del Correo Argentino que figura en la tapa.
    m = re.search(r'A[ÑN]O\s+[IVXLCDM]+\s*-?\s*N[°º]\s*(\d{3,6})', texto, re.IGNORECASE)
    if m:
        numero = m.group(1)
    fecha = None
    m = re.search(r'(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚáéíóúñ]+)\s+de\s+(\d{4})', texto)
    if m:
        mes = MESES_NUM.get(_sin_acentos(m.group(2)).lower())
        if mes:
            fecha = f"{m.group(3)}-{mes:02d}-{int(m.group(1)):02d}"
    return numero, fecha


# ===========================================================================
# EXTRACCIÓN DE NORMAS
# ===========================================================================
def _unir(fragmentos):
    """Une líneas rearmando las palabras cortadas con guion al fin de renglón."""
    salida = ''
    for f in fragmentos:
        s = f.strip()
        if not s:
            continue
        if salida and re.search(r'[A-Za-zÁÉÍÓÚÑáéíóúñ]-$', salida) and re.match(r'^[a-záéíóúñ]', s):
            salida = salida[:-1] + s
        elif salida:
            salida += ' ' + s
        else:
            salida = s
    return re.sub(r'\s+', ' ', salida).strip()


def _fecha_encabezado(txt, anio_boletin=None):
    """'16-07-26' -> '2026-07-16'. Devuelve None si no parsea."""
    if not txt:
        return None
    m = re.match(r'(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})$', txt.strip())
    if not m:
        return None
    d, mes, a = int(m.group(1)), int(m.group(2)), m.group(3)
    a = int(a) + 2000 if len(a) == 2 else int(a)
    if not (1 <= mes <= 12 and 1 <= d <= 31 and 2000 <= a <= 2100):
        return None
    return f"{a:04d}-{mes:02d}-{d:02d}"


def _fusionar_encabezados(lineas):
    """
    Los encabezados de resolución vienen partidos en dos renglones:

        RESOLUCIÓN ADMINISTRATIVA      (negrita 8pt, sin número)
        GENERAL N°14061/2026           (negrita 8pt, con número)

    Se unen sólo cuando la primera línea NO es encabezado por sí sola y la
    unión SÍ lo es. Así no se pegan cosas que no corresponde (por ejemplo
    "SUBSECRETARÍA DE INFORMACIÓN PÚBLICA" + "DIRECCIÓN GENERAL DE PUBLICIDAD",
    que son dos organismos y no una norma).
    """
    salida, i = [], 0
    while i < len(lineas):
        a = lineas[i]
        b = lineas[i + 1] if i + 1 < len(lineas) else None
        if (b and a['bold'] and b['bold'] and abs(a['tam'] - b['tam']) < 0.6
                and not RE_NORMA.match(a['texto'])
                and not re.search(r'\d', a['texto'])):
            unido = f"{a['texto'].strip()} {b['texto'].strip()}"
            if len(unido) <= 70 and RE_NORMA.match(unido):
                salida.append({'texto': unido, 'tam': a['tam'], 'bold': True})
                i += 2
                continue
        salida.append(a)
        i += 1
    return salida


def extraer_normas(lineas, fecha_boletin=None, regla_emisor=True):
    """
    Recorre las líneas de la Sección Oficial y arma las normas.

    Tres cosas que hay que reconocer, y ninguna se distingue sólo por tamaño:
      - subsección  -> fija el TIPO vigente ("RESOLUCIONES")
      - organismo   -> fija el EMISOR vigente ("PODER JUDICIAL")
      - encabezado  -> abre una norma nueva ("RESOLUCIÓN N° 84/2026 IGJ")

    La regla que las separa es simple: si la línea en negrita trae "N° <número>"
    es encabezado; si no, es tipo (si se reconoce) o emisor.
    """
    normas = []
    tipo_actual = None
    emisor_actual = None
    venia_emisor = False
    titulo = []        # título en mayúsculas que precede al encabezado (leyes)
    actual = None      # norma en construcción

    def cerrar():
        if actual and actual['cuerpo']:
            texto = _unir(actual['cuerpo'])
            if texto:
                es_ind, punt, mot = clasificar_norma(texto, actual['emisor'],
                                                    regla_emisor)
                anio = actual['anio'] or (actual['fecha'] or fecha_boletin or '')[:4]
                normas.append({
                    'tipo': actual['tipo'] or 'NORMA',
                    'numero': actual['numero'],
                    # Chubut ordena su Digesto por libros en romanos y los cita
                    # como parte del identificador ("Ley I N° 231", "Resolución
                    # II N° 42"). Se guarda aparte; ver nota en el README.
                    'romano': actual['romano'],
                    'anio': anio or None,
                    # fecha_publicacion = fecha del BOLETÍN, no la de la firma.
                    # El decreto 112 del boletín del 20/07/2026 está firmado el
                    # 06-02-25; si se guardara esa fecha, el historial de
                    # scraping quedaría con la fecha equivocada.
                    'fecha_publicacion': fecha_boletin or actual['fecha'],
                    'fecha_norma': actual['fecha'],
                    'emisor': actual['emisor'],
                    'encabezado': actual['encabezado'],
                    'titulo': actual['titulo'],
                    'texto_completo': texto,
                    'es_individual': es_ind, 'puntaje': punt, 'motivos': mot,
                })

    def abrir(m, encabezado):
        anio = m.group('anio')
        if anio:
            anio = str(int(anio) + 2000) if len(anio) == 2 else anio
        fecha = _fecha_encabezado((m.group('resto') or '').strip())
        # El encabezado abrevia ("Dto. N° 112") y la subsección califica
        # ("DECRETOS SINTETIZADOS"); al revés pasa con las resoluciones
        # ("RESOLUCIÓN ADMINISTRATIVA GENERAL" bajo "RESOLUCIONES"). Cuando los
        # dos hablan del mismo núcleo, gana el más específico.
        tipo_cab = _tipo_desde(m.group('clase'))
        tipo = tipo_cab or tipo_actual
        if tipo_cab and tipo_actual and \
                tipo_cab.split(' ')[0] == tipo_actual.split(' ')[0]:
            tipo = max((tipo_cab, tipo_actual), key=lambda t: len(t.split(' ')))
        return {
            'tipo': tipo,
            'numero': m.group('num'),
            'romano': (m.group('rom') or '').upper() or None,
            'anio': anio or (fecha or '')[:4] or None,
            'fecha': fecha,
            'emisor': emisor_actual,
            'encabezado': encabezado,
            'titulo': _unir(titulo) or None,
            'cuerpo': [],
        }

    for linea in _fusionar_encabezados(lineas):
        texto = linea['texto'].strip()
        if not texto:
            continue

        # Pie de publicación ("I: 17-07-26 V: 21-07-26"): cierra la norma.
        if RE_VIGENCIA.match(texto):
            cerrar()
            actual = None
            venia_emisor = False
            continue

        if linea['bold'] and linea['tam'] >= TAM_ENCABEZADO_MIN and len(texto) <= 70:
            m = RE_NORMA.match(texto) or RE_NORMA.match(_compacto(texto))
            if m:
                cerrar()
                actual = abrir(m, texto)
                titulo, venia_emisor = [], False
                continue

            # Subsección: fija el tipo y reinicia el emisor (cada bloque trae
            # el suyo; si no lo trae, el emisor es el Poder Ejecutivo).
            if linea['tam'] >= TAM_SUBSECCION_MIN and texto == texto.upper():
                tipo = _tipo_desde(texto)
                if tipo:
                    cerrar()
                    actual, tipo_actual = None, tipo
                    emisor_actual, venia_emisor, titulo = None, False, []
                    continue

            # Organismo emisor. Dos casos distintos cuando vienen dos líneas
            # seguidas: si la segunda arranca con preposición es el mismo
            # nombre partido en dos renglones ("ADMINISTRACIÓN PORTUARIA DEL
            # PUERTO" / "DE COMODORO RIVADAVIA") y se une; si arranca con otra
            # palabra institucional es una dependencia interna ("SUBSECRETARÍA…"
            # / "DIRECCIÓN GENERAL…") y se conserva el organismo de arriba.
            continuacion = (venia_emisor and emisor_actual
                            and texto == texto.upper()
                            and not re.search(r'\d', texto)
                            and not RE_RUIDO.match(texto)
                            and (RE_CONTINUA_EMISOR.match(texto)
                                 or RE_EMISOR_COLGADO.search(emisor_actual)))
            if _es_emisor(texto) or continuacion:
                cerrar()
                actual = None
                limpio = re.sub(r'\s+', ' ', texto)
                if not venia_emisor:
                    emisor_actual = limpio
                elif continuacion:
                    emisor_actual = f"{emisor_actual} {limpio}"
                venia_emisor = True
                titulo = []
                continue

            # Título de la norma: las leyes publican su objeto en mayúsculas y
            # negrita ANTES del encabezado ("INSTITUCIONALIZAR… LA SEÑAL
            # INTERNACIONAL DE AUXILIO…"). Es la mejor síntesis posible, así que
            # se guarda para la norma que abra a continuación.
            if actual is None and texto == texto.upper() and len(titulo) < 8:
                titulo.append(texto)
                venia_emisor = False
                continue

        venia_emisor = False

        # Respaldo: encabezado al que el PDF le comió la negrita. Pasó con
        # "REGISTRO N° 106447" en la edición 14894. Se acepta sólo si la línea
        # es exactamente un encabezado del tipo que está corriendo, para no
        # abrir normas con cualquier "N° x" del cuerpo.
        if tipo_actual:
            m = RE_NORMA.match(_compacto(texto))
            if (m and not (m.group('resto') or '').strip()
                    and (_tipo_desde(m.group('clase')) or '').split(' ')[0]
                    == tipo_actual.split(' ')[0]):
                cerrar()
                actual = abrir(m, texto)
                titulo = []
                continue

        if actual is not None:
            actual['cuerpo'].append(texto)

    cerrar()
    return normas


# ===========================================================================
# SUMARIO (oráculo de control)
# ---------------------------------------------------------------------------
# La página 1 lista exactamente qué normas trae la Sección Oficial:
#
#     DECRETOS SINTETIZADOS
#     Año 2025 - Dto. N° 112.......................................... 2
#     Año 2026 - Dto. N° 867, 946 y 947............................... 2
#     RESOLUCIONES
#     Poder Judicial
#     Año 2026 - Res. Adm. Gral. N° 14061 y 14064..................... 2-4
#
# Es el único control objetivo que tiene el bot: si extrajo menos normas de las
# que anuncia el sumario, algo se perdió y hay que avisar en vez de reportar
# éxito. La tapa no tiene el canal vacío entre columnas (la recuadra un marco),
# así que el detector genérico no sirve: se recorta por posición.
# ===========================================================================
RE_SUMARIO_ANIO = re.compile(r'A[ñn]o\s+(?P<anio>\d{4})\s*-\s*(?P<resto>.+)$',
                             re.IGNORECASE)

# Dentro de una entrada puede haber más de una norma. La ed. 14868 anuncia
# "Año 2026 - Ley XV N° 45 Dto. N° 708 «Institucionalizar…»": son la ley y el
# decreto que la promulga, y el boletín publica las dos.
RE_SUMARIO_ITEM = re.compile(
    r'(?P<clase>[A-Za-zÁÉÍÓÚÑáéíóúñ][A-Za-zÁÉÍÓÚÑáéíóúñ\.]*'
    r'(?:\s+[A-Za-zÁÉÍÓÚÑáéíóúñ\.]{1,12}){0,3}?)'
    r'\s*N[°º]\s*(?P<lista>\d+(?:\s*(?:,|\s+y\s+|\s+a\s+)\s*\d+)*)',
    re.IGNORECASE)


def _expandir_numeros(lista):
    """'106383 a 106398, 106420 y 106423' -> [106383, ..., 106398, 106420, 106423]"""
    lista = re.sub(r'\.{2,}.*$', '', lista)          # puntos de relleno y página
    lista = re.sub(r'\s+y\s+', ',', lista, flags=re.IGNORECASE)
    numeros = []
    for parte in lista.split(','):
        rango = re.match(r'^\s*(\d+)\s+a\s+(\d+)\s*$', parte, re.IGNORECASE)
        if rango:
            ini, fin = int(rango.group(1)), int(rango.group(2))
            if 0 <= fin - ini <= 500:
                numeros.extend(str(n) for n in range(ini, fin + 1))
            continue
        suelto = re.search(r'\d+', parte)
        if suelto:
            # literal, sin int(): la ed. 14865 numera "Res. N° 0196"
            numeros.append(suelto.group(0))
    return numeros


def leer_sumario(ruta_pdf):
    """Devuelve la lista de (tipo, anio, numero) que anuncia la tapa."""
    with pdfplumber.open(ruta_pdf) as pdf:
        pagina = pdf.pages[0]
        palabras = [w for w in pagina.extract_words(extra_attrs=['fontname', 'size'])
                    if w['x0'] > pagina.width * 0.38]
        lineas = _lineas(palabras)

    esperadas, tipo_actual, dentro = [], None, False
    pendiente = None
    for linea in lineas:
        texto = linea['texto'].strip()
        if RE_SECCION_OFICIAL.match(texto):
            dentro = True
            continue
        if RE_SECCION_GENERAL.match(texto):
            break
        if not dentro:
            continue

        # Una entrada puede seguir en el renglón siguiente cuando la lista de
        # números no entra ("… 106425 a" / "106428……… 5-11").
        if pendiente is not None:
            texto = pendiente + ' ' + texto
            pendiente = None

        m = RE_SUMARIO_ANIO.search(texto)
        if m:
            # La entrada sigue en el renglón siguiente mientras no aparezcan los
            # puntos de relleno que la cierran contra el número de página.
            if '...' not in texto and '…' not in texto:
                pendiente = texto
                continue
            resto = re.sub(r'\.{3,}.*$', '', m.group('resto').split('«')[0])
            for item in RE_SUMARIO_ITEM.finditer(resto):
                tipo = _tipo_desde(item.group('clase')) or tipo_actual or 'NORMA'
                for numero in _expandir_numeros(item.group('lista')):
                    esperadas.append((tipo, m.group('anio'), numero))
            continue

        tipo = _tipo_desde(texto)
        if tipo:
            tipo_actual = tipo
    return esperadas


def comparar_con_sumario(esperadas, normas):
    """Devuelve (faltantes, sobrantes) comparando por (tipo, año, número)."""
    def clave(t, a, n):
        # "0196" y "196" son la misma norma: el cuerpo la numera con cero
        # adelante y el sumario no siempre lo respeta.
        return (str(t or '').split(' ')[0], str(a or ''),
                str(n or '').lstrip('0') or '0')

    obtenidas = {clave(n['tipo'], n['anio'], n['numero']) for n in normas}
    faltantes = [e for e in esperadas if clave(*e) not in obtenidas]
    esperadas_set = {clave(*e) for e in esperadas}
    sobrantes = [n for n in normas
                 if clave(n['tipo'], n['anio'], n['numero']) not in esperadas_set]
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
    Variantes de URL para una fecha. Los nombres reales de los archivos
    descargados del sitio ("Junio 05, 2026.pdf", "Julio 20, 2026.pdf")
    confirman que el día va con cero adelante, así que esa forma se prueba
    primero; la otra queda como respaldo por si no son consistentes.

    Antes las variantes salían de un set, cuyo orden de iteración cambia entre
    corridas: para los días de un dígito el bot pedía las dos URLs en orden
    impredecible y gastaba un 404 evitable la mitad de las veces.
    """
    mes = MESES[dia.month - 1]
    nombres = [mes]
    if mes == 'Septiembre':
        nombres.append('Setiembre')
    variantes = []
    for nombre in nombres:
        for dd in dict.fromkeys([f'{dia.day:02d}', str(dia.day)]):
            variantes.append(f'{nombre} {dd}, {dia.year}.pdf')
    # Sólo hay que codificar los espacios: la coma va literal, tal como la
    # sirve el sitio (".../Julio%2022,%202026.pdf").
    return [BASE_PDF + requests.utils.quote(v, safe=',') for v in variantes]


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
        if dia.weekday() < 5:          # sólo días hábiles: publica lunes a viernes
            for url in urls_candidatas(dia):
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


def emisor_por_defecto(tipo):
    """
    Las leyes las sanciona la Legislatura; los decretos y todo lo demás sin
    encabezado de organismo son del Poder Ejecutivo.
    """
    return 'PODER LEGISLATIVO' if str(tipo).startswith('LEY') else 'PODER EJECUTIVO'


def construir_sintesis(texto, tipo, numero):
    cuerpo = (texto or '').strip(' .-:')
    if len(cuerpo) > MAX_SINTESIS:
        cuerpo = cuerpo[:MAX_SINTESIS].rsplit(' ', 1)[0] + '…'
    return cuerpo or f"{tipo} {numero}"


def url_norma(url_pdf, tipo, numero):
    """
    Chubut no tiene URL por norma (todas viven en el mismo PDF), así que se usa
    la URL del PDF más un fragmento único. Es necesario porque
    ingresar_scraping.php deduplica por url_norma exacta: sin el fragmento, la
    primera norma guardada bloquearía a todas las demás del boletín.
    """
    slug = re.sub(r'[^A-Za-z0-9]+', '-', f"{tipo}-{numero}").strip('-')
    return f"{url_pdf}#{slug}"


# ===========================================================================
# EJECUCIÓN
# ===========================================================================
def _main():
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Chubut.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', default='https://boletin.chubut.gov.ar/')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--pdf', metavar='ARCHIVO', help='usar un PDF local (pruebas)')
    ap.add_argument('--fecha', metavar='AAAA-MM-DD', help='buscar el boletín de esta fecha')
    ap.add_argument('--todas', action='store_true', help='mostrar también las individuales')
    ap.add_argument('--con-registros', action='store_true',
                    help='incluir el Registro de Publicidad Oficial (excluido por defecto)')
    ap.add_argument('--con-tribunal-cuentas', action='store_true',
                    help='cargar también las normas del Tribunal de Cuentas '
                         '(rendiciones de cuentas; excluidas por defecto)')
    ap.add_argument('--recorte', action='store_true',
                    help='el PDF es un extracto sin tapa ni banner de sección: '
                         'parsear desde el principio (sólo para diagnóstico)')
    ap.add_argument('--volcar', action='store_true',
                    help='imprimir las líneas de la Sección Oficial con tamaño y '
                         'negrita, y salir (para diagnosticar normas que no se extraen)')
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
        numero_edicion, fecha_portada = metadatos_boletin(ruta_pdf)
        fecha_boletin = fecha_boletin or fecha_portada
        lineas = leer_seccion_oficial(ruta_pdf, recorte=args.recorte)
        normas = extraer_normas(lineas, fecha_boletin,
                                regla_emisor=not args.con_tribunal_cuentas)
        try:
            esperadas = leer_sumario(ruta_pdf)
        except Exception as e:
            esperadas = []
            print(f"No se pudo leer el sumario: {e}", file=sys.stderr)
    except Exception as e:
        salida("error", f"No se pudo parsear el PDF: {e}")
    finally:
        if ruta_temporal:
            try:
                os.unlink(ruta_temporal)
            except Exception:
                pass

    if not lineas:
        salida("warning", "No se encontró la Sección Oficial en el PDF "
                          "(¿cambió la maqueta del boletín?).")

    # Volcado de diagnóstico. Cuando el sumario anuncia normas que no se
    # extrajeron, esto muestra exactamente qué ve el parser: sin el tamaño y la
    # negrita de cada línea no hay forma de saber por qué un encabezado no se
    # reconoció (así se encontró que las resoluciones van en 8 pt y no en 9).
    if args.volcar:
        for i, linea in enumerate(lineas):
            print(f"{i:5d} {'B' if linea['bold'] else ' '} {linea['tam']:5.1f}  "
                  f"{linea['texto'][:110]}", file=sys.stderr)
        print(f"--- {len(lineas)} líneas en la Sección Oficial ---", file=sys.stderr)
        for t, a, n in esperadas:
            print(f"SUMARIO  {t} {n}/{a}", file=sys.stderr)
        salida("success", f"volcado: {len(lineas)} líneas, "
                          f"{len(esperadas)} normas en el sumario.")

    # Control contra el sumario ANTES de filtrar nada: el sumario los lista todos.
    faltantes, sobrantes = comparar_con_sumario(esperadas, normas)
    if esperadas:
        print(f"Sumario: anuncia {len(esperadas)} normas, se extrajeron {len(normas)} "
              f"({len(faltantes)} faltantes, {len(sobrantes)} no anunciadas)", file=sys.stderr)
        for t, a, n in faltantes[:15]:
            print(f"  FALTA   {t} {n}/{a}", file=sys.stderr)
        for n in sobrantes[:15]:
            print(f"  DE MÁS  {n['tipo']} {n['numero']}/{n['anio']} "
                  f"<- {n['encabezado'][:50]}", file=sys.stderr)

    # El Registro de Publicidad Oficial son contratos de pauta publicitaria
    # (30 a 40 por boletín), no normativa. Se excluyen salvo pedido expreso.
    registros = [n for n in normas if str(n['tipo']).startswith('REGISTRO')]
    if not args.con_registros:
        normas = [n for n in normas if not str(n['tipo']).startswith('REGISTRO')]

    generales = [n for n in normas if not n['es_individual']]
    individuales = [n for n in normas if n['es_individual']]

    guardar_debug(json.dumps(normas, ensure_ascii=False, indent=2, default=str),
                  'debug_chubut.json')
    print(f"Edición {numero_edicion or '?'} | normas: {len(normas)} "
          f"(generales {len(generales)} / individuales {len(individuales)}"
          f"{'' if args.con_registros else f' / registros omitidos {len(registros)}'})",
          file=sys.stderr)

    # 3. Prueba
    if args.dry_run:
        for n in (normas if args.todas else generales):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {str(n['tipo']):33s} N° {str(n['numero']):8s} "
                  f"{str(n['anio'] or '-'):5s} {str(n['emisor'] or emisor_por_defecto(n['tipo']))[:38]:38s} "
                  f"{len(n['texto_completo']):5d} car.  {n['encabezado'][:38]}",
                  file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(generales))

    if not normas:
        salida("warning", "La Sección Oficial no contenía normas reconocibles.")
    if not generales:
        salida("warning", f"Las {len(individuales)} normas del boletín son actos "
                          f"individuales; no se envió ninguna.")

    # 4. Envío
    payload = [{
        "id_jurisdiccion": args.id_jurisdiccion,
        # El emisor sale del encabezado del bloque ("PODER JUDICIAL",
        # "INSPECCIÓN GENERAL DE JUSTICIA", "MINISTERIO DE GOBIERNO"). Los
        # decretos no traen encabezado de organismo: son del Poder Ejecutivo.
        "nombre_emisor": n["emisor"] or emisor_por_defecto(n["tipo"]),
        "tipo_norma_desc": n["tipo"],
        "numero": n["numero"],
        "anio": n["anio"],
        "fecha_publicacion": n["fecha_publicacion"],
        # Las leyes publican su objeto como título; es mejor síntesis que el
        # arranque del articulado.
        "sintesis": construir_sintesis(n["titulo"] or n["texto_completo"],
                                       n["tipo"], n["numero"]),
        "texto_completo": n["texto_completo"][:MAX_TEXTO_COMPLETO],
        "url_norma": url_norma(url_pdf, n["tipo"], n["numero"]),
    } for n in generales]

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

    # El aviso del sumario va en un campo aparte, NO en el status.
    #
    # Antes esto devolvía status='warning' y el frontend, que sólo refresca la
    # grilla cuando recibe 'success', dejaba de recargar: las normas entraban
    # bien pero había que apretar F5 para verlas. El insert salió bien, así que
    # el status tiene que decir 'success'; que falten normas del sumario es una
    # advertencia sobre la COBERTURA, no una falla de la corrida.
    perdidas = [f for f in faltantes
                if args.con_registros or not str(f[0]).startswith('REGISTRO')]
    mensaje = respuesta.get('mensaje', 'OK') or 'OK'
    extra = None
    if perdidas:
        detalle = ', '.join(f"{t} {n}/{a}" for t, a, n in perdidas[:10])
        if len(perdidas) > 10:
            detalle += f" y {len(perdidas) - 10} más"
        extra = {
            "advertencia": (f"El sumario anuncia {len(perdidas)} normas que no se "
                            f"extrajeron: {detalle}"),
            "faltantes_sumario": len(perdidas),
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