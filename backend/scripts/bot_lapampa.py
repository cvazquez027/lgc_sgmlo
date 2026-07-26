#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 BOLETÍN OFICIAL DE LA PROVINCIA DE LA PAMPA  —  id_jurisdiccion 12
===============================================================================

*** PRIMERA VERSIÓN — construida SIN acceso al PDF real ***
Esta versión se armó analizando 3 boletines de muestra (3735, 3736, 3737)
convertidos a .docx por el usuario y el HTML real de la página de detalle de
uno de ellos. TODO lo que depende de cómo pdfplumber lee el PDF real (ver
sección "QUÉ FALTA VALIDAR" al final) es una hipótesis de trabajo, no un hecho
confirmado. El bot está escrito para que esas partes se puedan corregir sin
tocar el resto (limpieza de encabezado de página, negrita falsa, si los
títulos de rubro son texto real o gráfico).

DESCUBRIMIENTO
--------------
El sitio es un Joomla con una página por año:

    https://boletinoficial.lapampa.gob.ar/anio-2026.html

Adentro hay una grilla (<tbody>, filas <tr class="cat-list-rowN">) con un
<a href="/anio-2026/20890-boletin-oficial-no-3737-24-de-julio-de-2026.html">
que dice "Boletín Oficial Nº 3737 - 24 de julio de 2026". La PRIMERA fila de
la grilla es el ÚLTIMO boletín publicado (orden descendente).

La página de detalle trae, en un único <div class="com-content-article__body">:

    Versión PDF -> /images/Archivos/BoletinOficial/2026/BO3737.pdf
    ANEXOS: enlaces sueltos a PDFs individuales de leyes y algunas
            resoluciones/disposiciones destacadas (Ley_3646.pdf, Res._20_SEM.pdf,
            DI-2026-31-E-GLP-SSMMCM.pdf, ...)
    SUMARIO: un párrafo con <br> que lista, por RUBRO, todos los códigos
             publicados en esa edición:

        Ministerio de Gobierno y Asuntos Municipales: Resolución N° 310 a 315 y 318
        Ministerio de Educación: RESOL-2026-233-E-GLP-ME y RESOL-2026-237-E-GLP-ME

Ese bloque SUMARIO es el ORÁCULO de cobertura (como el calendario de Jujuy o
el sumario de Entre Ríos): da la lista completa y el organismo real de cada
rubro, incluidas listas con rangos ("N a M") y "y" antes del último ítem.

El PDF (BO3737.pdf) trae el texto completo de cada norma, agrupado bajo un
título de rubro que es LITERALMENTE el mismo texto que la etiqueta del
SUMARIO ("MINISTERIO DE GOBIERNO Y ASUNTOS MUNICIPALES", "DECRETOS
SINTETIZADOS", "DESIGNACIONES", ...). Eso da el organismo/emisor GRATIS,
sin tener que adivinarlo del cuerpo (a diferencia de Jujuy). *Esto asume que
esos títulos de rubro son texto real extraíble por pdfplumber y no un
gráfico — ver "QUÉ FALTA VALIDAR".*

DOS FORMATOS DE CÓDIGO CONVIVEN
--------------------------------
La Pampa está en transición del sistema clásico al GDE (Gestión Documental
Electrónica), y AMBOS aparecen en la misma edición:

    Decreto N° 1042                    (clásico: sin año en el código; el año
                                         sale de la fecha impresa debajo del
                                         encabezado, no del boletín)
    DECRE-2026-1153-E-GLP-GPLP          (GDE: año y sigla ya vienen en el código)
    Resolución N° 310                   RESOL-2026-233-E-GLP-ME
    Disposición N° 66                   DI-2026-31-E-GLP-SSM#MCM   (sigla con "#")
    Ley N° 3646                         (no se vio Ley en formato GDE)
    Sentencia Nº1637                    (Tribunal de Cuentas; excluida por defecto)

TRAMPA — LOS NÚMEROS CLÁSICOS Y GDE **NO** SON LA MISMA SERIE.
En el sumario de un mismo boletín aparecen intercalados sin orden numérico:
"Decreto N° 1042, 1088, 1150, 1159, DECRE-2026-1153-E-GLP-GPLP,
DECRE-2026-1166-..." — el 1153 GDE sale DESPUÉS del 1159 clásico. Son dos
numeradores paralelos (la Provincia migró de uno a otro). Por eso el número
GDE se guarda con su sigla pegada en el campo `numero` que se manda al backend
("1153-E-GLP-GPLP"), no como "1153" pelado: si se guardara pelado, un futuro
"Decreto Nº 1153" clásico (de otra fecha, incluso otro año) chocaría contra
él en la deduplicación tipo|numero|anio|emisor del backend, porque ambos son
"DECRETO" + "PODER EJECUTIVO". Esto es una decisión de diseño discutible —
si el equipo de backend prefiere separarlo en su propio campo, avisar.

RANGOS Y LISTAS EN EL SUMARIO
------------------------------
El sumario escribe listas mixtas, con rangos ("a") y el conector "y" antes del
último ítem, y mezcla los dos formatos en la misma lista:

    "Decreto N° 1177, 1184, 1201, 1202, 1217, DECRE-2026-1193-E-GLP-GPLP,
     DECRE-2026-1196-E-GLP-GPLP, DECRE-2026-1200-E-GLP-GPLP a
     DECRE-2026-1203-E-GLP-GPLP, ... y Decreto N° 1222"
    "Ley N° 3646 a 3649 y 3651"
    "Disposición N° 66 a 68"

`expandir_rubro()` tokeniza la lista y expande los rangos (mismo prefijo/sigla
en ambos extremos para GDE; mismo tipo para los clásicos). Un número "pelado"
(sin palabra clave) hereda el tipo del último código explícito visto ANTES de
él en la misma lista.

SECCIONES Y CORTE
------------------
Orden fijo observado en las 3 muestras: primero (si hay) LEYES PROVINCIALES,
después DECRETOS SINTETIZADOS y a veces DESIGNACIONES (subconjunto de
decretos de personal que el propio boletín separa aparte — no reemplaza el
clasificador individual/general, pero es una señal fuerte), después un
rubro por cada organismo que publicó ese día (Ministerios, Secretarías,
Subsecretarías, Direcciones, Institutos...), y por último, opcionalmente,
TRIBUNAL DE CUENTAS ("Sentencia") y TRIBUNAL ELECTORAL (resoluciones con
formato judicial "AUTOS Y VISTOS.../RESUELVE: Primero:...").

Después de eso arranca SIEMPRE ruido (equivalente a la Sección Comercial de
otras provincias): LICITACIONES, EDICTOS, AVISOS JUDICIALES, SECCIÓN
COMERCIO INDUSTRIA Y ENTIDADES CIVILES, CONCURSOS. El corte es el primero de
estos rubros que aparezca — nunca hay nada de interés después.

TRIBUNAL DE CUENTAS / TRIBUNAL ELECTORAL — excluidos por defecto
------------------------------------------------------------------
El Tribunal de Cuentas publica decenas de "Sentencia" por edición (una por
expediente de rendición de cuentas de una escuela, comisión de fomento, etc.):
son fallos sobre un caso puntual, no normativa general, y su volumen es
altísimo (en el B.O. 3737 hay más de 40). El Tribunal Electoral resuelve
sobre partidos políticos puntuales. Ambos quedan afuera salvo `--tribunales`.

CONCURSOS — dos resoluciones "se escapan" del rubro de su organismo
----------------------------------------------------------------------
El sumario agrupa aparte, bajo "Concursos", dos llamados que en realidad son
resoluciones de un organismo real ("Concursos: Llamados - Ministerio de la
Producción: Resolución N° 240 - Cámara de Diputados ...: Resolución N° 260").
Ese rubro tiene un formato interno distinto (organismo y código en la misma
línea, separados por otro rubro) y cae dentro del corte de ruido: por ahora
se pierden esas 1-2 resoluciones por edición. Si el cliente las quiere, hay
que escribir un parser aparte para esa línea específica.

SÍNTESIS
--------
- LEYES: el propio PDF ya trae, en la sección LEYES PROVINCIALES, una síntesis
  de una oración por ley ("Ley N° 3646: Declara a la localidad de Macachín
  como Capital Provincial del Rally..."). Se usa tal cual: no hace falta
  buscar el Artículo 1º.
- El resto (Decretos, Resoluciones, Disposiciones): se arma del Artículo 1º,
  igual que Jujuy — la mayoría se publican sintetizados (sin VISTO/CONSIDERANDO)
  así que el articulado es casi todo el texto.
- Tribunal Electoral (si se incluye con --tribunales): no tiene "Artículo 1º"
  sino "Primero:" — hay un fallback para ese formato.

FECHA Y AÑO DE CADA NORMA
--------------------------
A diferencia de Jujuy (donde el año sale del código), acá cada norma trae su
propia fecha impresa en el renglón siguiente al código ("29 de junio de
2026", a veces con día de la semana adelante: "Martes 14 de julio de 2026").
El año de esa fecha es el que se manda, no el año del boletín — un boletín de
julio puede publicar un decreto firmado en mayo. Para los códigos GDE el año
ya viene en el propio código y ambas fuentes deberían coincidir; si no
coinciden se loguea un aviso pero se prioriza el de la fecha impresa.

Se vieron un par de fechas sin día ("- de julio de 2026", Resoluciones 315 y
318 del Ministerio de Gobierno en el B.O. 3737) en el .docx de muestra. Puede
ser un problema real del PDF o un artefacto de la conversión a Word — falta
confirmarlo contra el PDF real. El fallback es usar la fecha del boletín y
avisar por stderr.

CONTRATO CON EL BACKEND (igual que el resto de los bots)
--------------------------------------------------------
- El JSON de salida va a stdout; todo lo demás a stderr.
- Todas las normas viven en un único PDF compilado (salvo las que tienen PDF
  propio listado en ANEXOS, que se usa cuando está disponible): url_norma
  lleva un fragmento único (#TIPO-NUMERO-ANIO) porque ingresar_scraping.php
  deduplica por url_norma EXACTA.

FLAGS
-----
    --dry-run           no envía nada
    --pdf ARCHIVO        usa un PDF local
    --texto ARCHIVO      usa un .txt ya extraído del PDF (pruebas del parser)
    --sumario ARCHIVO    usa un HTML de detalle guardado en un archivo (para
                         probar sin pegarle al sitio)
    --boletin N          número de boletín a procesar
    --anio AAAA          año del boletín (default: el actual)
    --todas              muestra también las individuales, con puntaje y motivos
    --sin-filtro         envía todo, sin filtrar actos individuales
    --tribunales         suma TRIBUNAL DE CUENTAS y TRIBUNAL ELECTORAL
    --emisor-refrenda    para Decretos/Designaciones, intenta usar el
                         Ministerio que refrenda en vez de "PODER EJECUTIVO"
    --volcar             imprime sumario y bloques y sale

===============================================================================
QUÉ FALTA VALIDAR CONTRA EL PDF REAL (no se pudo correr pdfplumber: el sandbox
no tiene salida de red hacia lapampa.gob.ar y el sitio bloquea robots)
===============================================================================
1. ¿Los títulos de rubro ("DECRETOS SINTETIZADOS", "MINISTERIO DE...") son
   texto real que pdfplumber extrae, o están dibujados/en un cuadro gráfico
   (como los banners de Jujuy, que pdfplumber NO ve)? Todo el corte por
   organismo depende de que sean texto real. Si no lo son, hay que caer a
   cortar sólo por los códigos del sumario, sin nombre de rubro (como hace
   el fallback de Jujuy), y el emisor de Resoluciones/Disposiciones quedaría
   sin resolver.
2. Encabezado/pie de página real por página: en el .docx de muestra aparece
   "BOLETÍN OFICIAL Nº 3737 / Santa Rosa, 24 de julio de 2026 / Pág. Nº 100"
   pero sólo 1-2 veces en todo el documento, no una vez por página — es
   casi seguro un artefacto de la conversión a Word (que no preserva
   paginación), no el comportamiento real del PDF. RE_ENCABEZADO_PAG de
   este archivo es una hipótesis basada en Jujuy/Entre Ríos; hay que
   confirmarla con `pdfplumber` página por página.
3. Negrita falsa (texto duplicado tipo "RREECCHHAAZZOO"): no se detectó en
   los .docx, pero el docx no necesariamente viene de pdfplumber crudo. Se
   dejó el mismo mecanismo defensivo de Jujuy/Entre Ríos (dedupe_chars) por
   las dudas; si no hace falta, no rompe nada (sólo se aplica si detecta el
   patrón).
4. Si un código GDE largo se corta entre dos líneas por ancho de página
   (no se vio ningún caso en las muestras, pero son códigos largos:
   "DECRE-2026-1186-E-GLP-GPLP").
5. Confirmar con una edición SIN decretos GDE (más vieja) y una con muchas
   leyes, para no sobreajustar a estas 3 ediciones de julio 2026.
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

SITIO = 'https://boletinoficial.lapampa.gob.ar'

HEADERS_WEB = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/pdf;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
}

REINTENTOS = 3
ESPERA_REINTENTO = 3
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700

MESES_NUM = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'setiembre': 9, 'octubre': 10,
    'noviembre': 11, 'diciembre': 12,
}


# ===========================================================================
# NORMALIZACIÓN
# ===========================================================================
GUIONES = {ord('–'): '-', ord('—'): '-', ord('‐'): '-', ord('‑'): '-', ord('−'): '-'}


def _guiones(texto):
    return (texto or '').translate(GUIONES)


def _sin_acentos(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def _compacto(texto):
    return re.sub(r'\s+', ' ', _guiones(texto or '')).strip()


def _clave_rubro(texto):
    """Clave normalizada (sin acentos, sin mayúsculas/minúsculas) para comparar
    el nombre de un rubro sin depender de tildes."""
    return re.sub(r'\s+', ' ', _sin_acentos(texto or '').upper()).strip(' :')


# ===========================================================================
# RUBROS
# ===========================================================================
RUBRO_LEYES = 'LEYES PROVINCIALES'
RUBRO_DECRETOS = 'DECRETOS SINTETIZADOS'
RUBRO_DESIGNACIONES = 'DESIGNACIONES'
RUBRO_TRIBUNAL_CUENTAS = 'TRIBUNAL DE CUENTAS'
RUBRO_TRIBUNAL_ELECTORAL = 'TRIBUNAL ELECTORAL'

# Rubros que, apenas aparecen, marcan el fin de la parte normativa del
# boletín. Nunca hay nada de interés después de esto (equivalente a la
# Sección Comercial de otras provincias).
RUBROS_CIERRE = [
    'LICITACIONES', 'EDICTOS', 'AVISOS JUDICIALES',
    'SECCION COMERCIO, INDUSTRIA Y ENTIDADES CIVILES', 'CONCURSOS',
]

# Emisor fijo para los rubros que no son "un organismo publicando lo suyo".
EMISOR_FIJO = {
    _clave_rubro(RUBRO_LEYES): 'PODER LEGISLATIVO',
    _clave_rubro(RUBRO_DECRETOS): 'PODER EJECUTIVO',
    _clave_rubro(RUBRO_DESIGNACIONES): 'PODER EJECUTIVO',
    _clave_rubro(RUBRO_TRIBUNAL_CUENTAS): 'TRIBUNAL DE CUENTAS',
    _clave_rubro(RUBRO_TRIBUNAL_ELECTORAL): 'TRIBUNAL ELECTORAL',
}

RUBROS_TRIBUNALES_CLAVE = {_clave_rubro(RUBRO_TRIBUNAL_CUENTAS),
                           _clave_rubro(RUBRO_TRIBUNAL_ELECTORAL)}
RUBROS_CIERRE_CLAVE = {_clave_rubro(r) for r in RUBROS_CIERRE}


# ===========================================================================
# CÓDIGOS: clásico ("Decreto N° 1042") y GDE ("DECRE-2026-1153-E-GLP-GPLP")
# ===========================================================================
TIPOS_CLASICOS = ['Ley', 'Decreto', 'Resoluci[oó]n', 'Disposici[oó]n',
                  'Sentencia', 'Ordenanza']
_ALT_CLASICO = '|'.join(TIPOS_CLASICOS)

# Prefijo GDE -> tipo normalizado. RESFC se vio una sola vez citado dentro de
# un considerando del Tribunal de Cuentas (RESFC-2026-122-E-TRICUELP-TDEC);
# se lo mapea a RESOLUCION por las dudas, pero no hay muestra de que sea un
# encabezado real.
PREFIJOS_GDE = {
    'DECRE': 'DECRETO', 'RESOL': 'RESOLUCION', 'DI': 'DISPOSICION',
    'DISPO': 'DISPOSICION', 'RESFC': 'RESOLUCION',
}
_ALT_GDE = '|'.join(sorted(PREFIJOS_GDE, key=len, reverse=True))

RE_NUMERAL = r'N[º°ª]?\.?'

# Código GDE en cualquier posición (para tokenizar listas del sumario).
RE_GDE = re.compile(
    r'(?P<prefijo>' + _ALT_GDE + r')-(?P<anio>\d{4})-(?P<numero>\d+)'
    r'-(?P<sigla>[A-Z0-9#]+(?:-[A-Z0-9#]+)*)')

# Código clásico "Tipo N° numero" en cualquier posición.
RE_CLASICO = re.compile(
    r'(?P<tipo>' + _ALT_CLASICO + r')\s*' + RE_NUMERAL + r'\s*(?P<numero>\d+)',
    re.IGNORECASE)

# Número pelado (hereda el tipo del código explícito anterior en la lista).
RE_BARE = re.compile(r'\d+')

# Un token del sumario: GDE, clásico o número pelado (en ese orden). No se
# pueden reusar los grupos 'numero'/'anio'/'sigla'/'tipo' de RE_GDE/RE_CLASICO
# dentro de esta alternancia combinada (Python no permite el mismo nombre de
# grupo dos veces), así que se renombran con sufijo para cada alternativa.
RE_TOKEN_SUMARIO = re.compile(
    r'(?P<gde>(?P<prefijo_g>' + _ALT_GDE + r')-(?P<anio_g>\d{4})-(?P<numero_g>\d+)'
    r'-(?P<sigla_g>[A-Z0-9#]+(?:-[A-Z0-9#]+)*))|'
    r'(?P<clasico>(?P<tipo_c>' + _ALT_CLASICO + r')\s*' + RE_NUMERAL +
    r'\s*(?P<numero_c>\d+))|'
    r'(?P<bare>' + RE_BARE.pattern + r')')

# Encabezado clásico SOLO en su renglón (nada más que eso, quizás un punto).
RE_CABECERA_CLASICA = re.compile(
    r'^[ \t]*(?P<tipo>' + _ALT_CLASICO + r')\s*' + RE_NUMERAL +
    r'\s*(?P<numero>\d+)\s*\.?\s*$', re.IGNORECASE | re.MULTILINE)

# Encabezado GDE solo en su renglón.
RE_CABECERA_GDE = re.compile(
    r'^[ \t]*' + RE_GDE.pattern + r'\s*$', re.MULTILINE)

# Ley: "Ley N° 3646: Declara..." — la síntesis puede ocupar más de un
# renglón en el PDF real (se vio cortada a mitad de oración cuando el regex
# anterior anclaba al fin de línea), así que se toma todo hasta la próxima
# "Ley N°" o el final del bloque.
RE_LEY_INLINE = re.compile(
    r'^[ \t]*Ley\s*' + RE_NUMERAL + r'\s*(?P<numero>\d+)\s*:\s*'
    r'(?P<sintesis>[\s\S]+?)(?=^[ \t]*Ley\s*' + RE_NUMERAL + r'\s*\d+\s*:|\Z)',
    re.IGNORECASE | re.MULTILINE)

# Fecha impresa debajo del encabezado: día de semana opcional + DD de MES de AAAA.
RE_FECHA_NORMA = re.compile(
    r'^\s*(?:(?:Lunes|Martes|Mi[ée]rcoles|Jueves|Viernes|S[áa]bado|Domingo)\s+)?'
    r'(?P<dia>\d{1,2})\s+de\s+(?P<mes>[A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+de\s+(?P<anio>\d{4})',
    re.IGNORECASE | re.MULTILINE)


def _tipo_normalizado(crudo):
    t = _sin_acentos((crudo or '').upper())
    t = re.sub(r'\s+', ' ', t).strip()
    if t.startswith('RESOLUCI'):
        return 'RESOLUCION'
    if t.startswith('DISPOSICI'):
        return 'DISPOSICION'
    return t


def _fecha_iso(dia, mes_nombre, anio):
    mes = MESES_NUM.get(_sin_acentos((mes_nombre or '').lower()))
    if not mes:
        return None
    try:
        return date(int(anio), mes, int(dia)).isoformat()
    except ValueError:
        return None


# ===========================================================================
# SUMARIO: parsear "Label: contenido" y expandir rangos/listas
# ===========================================================================
def partir_sumario_en_rubros(texto_sumario):
    """
    El bloque SUMARIO de la página de detalle es un párrafo con un rubro por
    renglón ("Label: contenido"), separados por <br> (ya convertidos a '\n'
    antes de llegar acá). Devuelve {nombre_rubro: contenido}, en orden.
    """
    rubros = {}
    orden = []
    for linea in (texto_sumario or '').splitlines():
        linea = linea.strip()
        if not linea or ':' not in linea:
            continue
        etiqueta, contenido = linea.split(':', 1)
        etiqueta = _compacto(etiqueta)
        contenido = _compacto(contenido)
        if not etiqueta or len(etiqueta) > 90:
            continue
        rubros[etiqueta] = contenido
        orden.append(etiqueta)
    return rubros, orden


def expandir_rubro(contenido):
    """
    Tokeniza la lista de un rubro ("Decreto N° 1042, 1088, ..., 1186 a 1191,
    ..., DECRE-2026-1193-E-GLP-GPLP") y devuelve la lista de items
    {'tipo','numero','anio','sigla','formato'} con los rangos expandidos.

    - Un número pelado hereda el tipo del último código explícito visto.
    - "X a Y" expande el rango (mismo prefijo/sigla en GDE; mismo tipo en
      clásico). "y" es sólo el conector antes del último ítem: no dispara
      expansión.
    """
    texto = _compacto(contenido)
    tokens = list(RE_TOKEN_SUMARIO.finditer(texto))
    items = []
    tipo_actual = None

    def _item_desde_match(m):
        if m.group('gde'):
            return {
                'tipo': PREFIJOS_GDE.get(m.group('prefijo_g'), m.group('prefijo_g')),
                'numero': m.group('numero_g'),
                'anio': m.group('anio_g'),
                'sigla': m.group('sigla_g'),
                'formato': 'gde',
            }
        if m.group('clasico'):
            return {
                'tipo': _tipo_normalizado(m.group('tipo_c')),
                'numero': m.group('numero_c'),
                'anio': None,
                'sigla': None,
                'formato': 'clasico',
            }
        return None  # bare: se resuelve afuera, necesita tipo_actual

    i = 0
    while i < len(tokens):
        m = tokens[i]
        if m.group('bare'):
            if tipo_actual is None:
                i += 1
                continue  # número suelto sin contexto: no se puede resolver
            it = {'tipo': tipo_actual, 'numero': m.group('bare'),
                  'anio': None, 'sigla': None, 'formato': 'clasico'}
        else:
            it = _item_desde_match(m)
            tipo_actual = it['tipo']

        rango_consumido = False
        if i + 1 < len(tokens):
            entre = texto[m.end():tokens[i + 1].start()]
            if re.fullmatch(r'\s*a\s*', entre, re.IGNORECASE):
                nxt = tokens[i + 1]
                if nxt.group('bare'):
                    it2 = {'tipo': tipo_actual, 'numero': nxt.group('bare'),
                           'anio': None, 'sigla': None, 'formato': 'clasico'}
                else:
                    it2 = _item_desde_match(nxt)
                    tipo_actual = it2['tipo']
                ini, fin = int(it['numero']), int(it2['numero'])
                if 0 <= fin - ini <= 200:  # cota defensiva contra un "a" mal leído
                    plantilla = it2 if it2['formato'] == 'gde' else it
                    for n in range(ini, fin + 1):
                        nuevo = dict(plantilla)
                        nuevo['numero'] = str(n)
                        items.append(nuevo)
                    rango_consumido = True

        if not rango_consumido:
            items.append(it)
        i += 2 if rango_consumido else 1

    return items


def clave_norma(tipo, numero, anio, sigla=None):
    base_numero = str(numero)
    if sigla:
        base_numero = f"{numero}-{sigla}"
    return (tipo, base_numero, str(anio or ''))


# ===========================================================================
# LECTURA DEL PDF
# ===========================================================================
RE_NEGRITA_FALSA = re.compile(r'\b([A-ZÁÉÍÓÚÑ])\1([A-ZÁÉÍÓÚÑ])\2([A-ZÁÉÍÓÚÑ])\3')

# HIPÓTESIS sin confirmar contra el PDF real (ver "QUÉ FALTA VALIDAR" arriba).
RE_ENCABEZADO_PAG = re.compile(
    r'^\s*(?:'
    r'BOLET[ÍI]N\s+OFICIAL\s+N[º°]?\s*\d+'
    r'|Santa\s+Rosa,\s*\d{1,2}\s+de\s+[A-Za-zÁÉÍÓÚáéíóúñÑ]+\s+de\s+\d{4}'
    r'|P[áa]g\.?\s*N[º°]?\s*\d+'
    r'|Propiedad\s+Intelectual\s+N[º°]?\s*\d+'
    r')\s*$', re.IGNORECASE | re.MULTILINE)


def leer_paginas(ruta_pdf):
    if pdfplumber is None:
        raise RuntimeError("Falta pdfplumber: pip install pdfplumber")
    paginas = []
    avisado = False
    with pdfplumber.open(ruta_pdf) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ''
            if RE_NEGRITA_FALSA.search(txt):
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


def limpiar_cuerpo(paginas):
    limpias = []
    for txt in paginas:
        txt = _guiones(txt or '')
        txt = RE_ENCABEZADO_PAG.sub('', txt)
        limpias.append(txt)
    return '\n'.join(limpias)


def metadatos_boletin(paginas):
    """(numero, fecha ISO) leídos de la tapa/primera página."""
    cabeza = '\n'.join(paginas[:2])
    numero = None
    m = re.search(r'BOLET[ÍI]N\s+OFICIAL\s+N[º°]?\s*(\d+)', cabeza, re.IGNORECASE)
    if m:
        numero = m.group(1)
    fecha = None
    m = re.search(r'Santa\s+Rosa,\s*(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+de\s+(\d{4})',
                  cabeza, re.IGNORECASE)
    if m:
        fecha = _fecha_iso(m.group(1), m.group(2), m.group(3))
    return numero, fecha


# ===========================================================================
# CORTE POR RUBRO EN EL CUERPO
# ===========================================================================
# Fallback cuando no hay SUMARIO disponible (--pdf/--texto solos, sin
# --sumario, o el sitio no respondió): detecta títulos de rubro directamente
# en el cuerpo por su forma típica, en vez de por la lista exacta que
# debería traer el sumario. Sin esto el bot queda ciego a las secciones y no
# extrae nada. No da control de cobertura (no hay oráculo con el que
# comparar), pero al menos corta por organismo y clasifica cada norma.
RE_RUBRO_GENERICO = re.compile(
    r'^[ \t]*((?:MINISTERIO|SECRETAR[IÍ]A|SUBSECRETAR[IÍ]A|DIRECCI[OÓ]N(?:\s+GENERAL)?|'
    r'INSTITUTO|TRIBUNAL|LEYES\s+PROVINCIALES|DECRETOS\s+SINTETIZADOS|'
    r'DESIGNACIONES)\b[^\n]{0,80}?)\s*$', re.IGNORECASE | re.MULTILINE)


def detectar_rubros_desde_cuerpo(cuerpo_plano):
    """Lista de nombres de rubro, en el orden en que aparecen sus títulos en
    el cuerpo, deducida sin el sumario. Usada sólo como fallback."""
    orden = []
    for m in RE_RUBRO_GENERICO.finditer(cuerpo_plano):
        nombre = _compacto(m.group(1)).title()
        if nombre not in orden:
            orden.append(nombre)
    return orden


def _regex_titulo_rubro(nombre):
    """Regex tolerante a mayúsculas/acentos para un título de rubro solo en
    su renglón (posiblemente con espacios extra, como los introduce a veces
    la maquetación: 'Ministerio de Educación' con doble espacio)."""
    plano = _sin_acentos(nombre).upper()
    partes = [re.escape(p) for p in plano.split(' ')]
    patron = r'\s+'.join(partes)
    return re.compile(r'^[ \t]*' + patron + r'\s*$', re.IGNORECASE | re.MULTILINE)


def cortar_por_rubros(cuerpo_plano, rubros_orden, incluir_tribunales):
    """
    Devuelve [(nombre_rubro, ini, fin)] con los OFFSETS del contenido de cada
    rubro (después de su título y hasta el título del rubro siguiente),
    buscando los títulos en `cuerpo_plano` (texto sin acentos y en
    mayúsculas, para no depender de tildes). `rubros_orden` viene del sumario
    tal cual está escrito ahí.

    `_sin_acentos(...).upper()` no cambia la cantidad de caracteres respecto
    del texto original (cada acentuada se reemplaza por su base, 1 a 1), así
    que estos offsets valen igual sobre el texto legible original — no hace
    falta volver a buscar el texto.

    Si un rubro del sumario no se encuentra como título en el cuerpo, se
    omite (se avisa en el llamador vía control de cobertura general).
    """
    # OJO: acá se ubican TODOS los títulos (incluidos Tribunal de Cuentas /
    # Tribunal Electoral) aunque no se vayan a devolver, porque un título
    # saltado deja de actuar como límite y el rubro anterior se traga todo
    # el contenido siguiente (se probó contra la muestra: sin este cuidado,
    # "Instituto de Seguridad Social" se comía las ~40 Sentencias del
    # Tribunal de Cuentas). El filtro de --tribunales se aplica DESPUÉS.
    posiciones = []
    for nombre in rubros_orden:
        rx = _regex_titulo_rubro(nombre)
        m = rx.search(cuerpo_plano)
        if m:
            posiciones.append((m.start(), m.end(), nombre))

    # Techo: el primer rubro de cierre que aparezca en el cuerpo (aparezca o
    # no en el sumario — a veces el sumario no lista "Concursos" si viene
    # vacío, pero el título igual puede estar impreso).
    techo = len(cuerpo_plano)
    for nombre_cierre in RUBROS_CIERRE:
        rx = _regex_titulo_rubro(nombre_cierre)
        m = rx.search(cuerpo_plano)
        if m and m.start() < techo:
            techo = m.start()

    posiciones.sort()
    bloques = []
    for i, (ini, fin, nombre) in enumerate(posiciones):
        fin_bloque = posiciones[i + 1][0] if i + 1 < len(posiciones) else techo
        if fin_bloque <= fin:
            continue
        clave = _clave_rubro(nombre)
        if clave in RUBROS_TRIBUNALES_CLAVE and not incluir_tribunales:
            continue  # límite ya usado arriba; ahora sí se descarta el contenido
        bloques.append((nombre, fin, fin_bloque))
    return bloques


# ===========================================================================
# EXTRACCIÓN DE NORMAS DENTRO DE UN BLOQUE DE RUBRO
# ===========================================================================
_ART1 = (r'ART[ÍI]?CULO\s*(?:N[º°]\s*)?1(?!\d)\s*[º°]?\s*[.:,;-]+\s*'
         r'(?P<texto>[\s\S]{0,1200}?)(?=ART[ÍI]?CULO\s*(?:N[º°]\s*)?2(?!\d)|\Z)')
RE_ARTICULO1 = re.compile(_ART1, re.IGNORECASE)
# Fallback para el formato judicial del Tribunal Electoral/Tribunal de
# Cuentas cuando resuelve con "Primero:" en vez de "Artículo 1º".
RE_PRIMERO = re.compile(
    r'\bPrimero\s*[:.]\s*(?P<texto>[\s\S]{0,1200}?)(?=\bSegundo\s*[:.]|\Z)',
    re.IGNORECASE)


def _sintesis_de_bloque(tipo, bloque):
    m = RE_ARTICULO1.search(bloque)
    if m:
        return _compacto(m.group('texto'))
    m = RE_PRIMERO.search(bloque)
    if m:
        return _compacto(m.group('texto'))
    return _compacto(bloque[:400])


def extraer_normas_de_rubro(nombre_rubro, bloque, fecha_boletin, anio_boletin):
    """Devuelve la lista de normas encontradas dentro del texto de UN rubro."""
    normas = []
    clave = _clave_rubro(nombre_rubro)

    if clave == _clave_rubro(RUBRO_LEYES):
        for m in RE_LEY_INLINE.finditer(bloque):
            numero = m.group('numero')
            sintesis = _compacto(m.group('sintesis')).rstrip('.')
            normas.append({
                'tipo': 'LEY', 'numero': numero, 'anio': str(anio_boletin),
                'sigla': None, 'formato': 'clasico',
                'sintesis': sintesis, 'texto_completo': sintesis,
                'rubro': nombre_rubro, 'fecha_publicacion': fecha_boletin,
            })
        return normas

    # Posiciones de todos los encabezados (clásico + GDE) dentro del bloque.
    marcas = []
    for m in RE_CABECERA_CLASICA.finditer(bloque):
        marcas.append((m.start(), m.end(), _tipo_normalizado(m.group('tipo')),
                       m.group('numero'), None, None, 'clasico'))
    for m in RE_CABECERA_GDE.finditer(bloque):
        marcas.append((m.start(), m.end(),
                       PREFIJOS_GDE.get(m.group('prefijo'), m.group('prefijo')),
                       m.group('numero'), m.group('anio'), m.group('sigla'), 'gde'))
    marcas.sort()

    for i, (ini, fin_cab, tipo, numero, anio_codigo, sigla, formato) in enumerate(marcas):
        fin_bloque = marcas[i + 1][0] if i + 1 < len(marcas) else len(bloque)
        cuerpo_norma = bloque[fin_cab:fin_bloque]

        anio = anio_codigo
        fecha_norma = fecha_boletin
        m_fecha = RE_FECHA_NORMA.search(cuerpo_norma[:200])
        if m_fecha:
            iso = _fecha_iso(m_fecha.group('dia'), m_fecha.group('mes'), m_fecha.group('anio'))
            if iso:
                fecha_norma = iso
                anio = m_fecha.group('anio')
        if not anio:
            anio = str(anio_boletin)

        sintesis = _sintesis_de_bloque(tipo, cuerpo_norma)
        normas.append({
            'tipo': tipo, 'numero': numero, 'anio': anio, 'sigla': sigla,
            'formato': formato, 'sintesis': sintesis,
            'texto_completo': cuerpo_norma, 'rubro': nombre_rubro,
            'fecha_publicacion': fecha_norma,
        })
    return normas


# ===========================================================================
# CLASIFICACIÓN INDIVIDUAL / GENERAL
# ===========================================================================
# Patrones adaptados de Jujuy/Entre Ríos/Chubut/Catamarca (mismo idioma y
# dominio administrativo). Se agregan un par de patrones propios de La Pampa
# (aportes a municipios uno por uno vs. tabla de muchos municipios).
UMBRAL_INDIVIDUAL = 3

PATRONES_INDIVIDUAL = [
    (r'\bDes[íi]gn[ae]se\b',                                        4, 'designación'),
    (r'\bAc[ée]pt[ae]se\b[\s\S]{0,80}\brenuncia\b',                 4, 'renuncia'),
    (r'\brenuncia\s+presentada\s+por\b',                            4, 'renuncia'),
    (r'\bPromu[ée]v[ae]se\b',                                       4, 'promoción de un agente'),
    (r'\bContrato\s+de\s+Locaci[óo]n\s+de\s+Servicios\b',           3, 'contrato de personal'),
    (r'\bReca[íi]?tegor[íi]?[ae]?se\b',                             2, 'recategorización'),
    (r'\bexoneraci[óo]n\b|\bcesant[íi]a\b',                         4, 'sanción expulsiva'),
    (r'\bRecurso\s+(?:Jer[áa]rquico|de\s+Revocatoria)\s+interpuesto\b', 3, 'recurso de un particular'),
    (r'\bOt[óo]rg[au]ese\b[\s\S]{0,60}\bLicencia\b',                3, 'licencia'),
    (r'\ba\s+(?:favor\s+de\s+)?la\s+Municipalidad\s+de\s+[A-ZÁÉÍÓÚ]', 2, 'aporte a un solo municipio'),
    (r'\bBaja\s+definitiva\b|\bJubilaci[óo]n\b',                    3, 'baja / jubilación'),
    (r'\bDNI\b|\bD\.N\.I\b',                                        1, 'menciona DNI de una persona'),
]

PATRONES_GENERAL = [
    (r'\bMunicipalidades\s+y\s+Comisiones\s+de\s+Fomento\s+que\s+se\s+detallan\b', -4,
     'aporte distribuido a varios municipios'),
    (r'\bApru[ée]b[ae](?:nse)?\b[\s\S]{0,60}(?:Reglamento|Manual|Anexo|Cuadro\s+Tarifario)', -3, 'aprobación normativa'),
    (r'\bPrecios\s+de\s+Venta\s+M[áa]ximos\b|\bCuadro\s+Tarifario\b',            -4, 'tarifas'),
    (r'\bDeclara(?:se)?\b[\s\S]{0,60}\bCapital\s+Provincial\b',                  -4, 'declaración de interés provincial'),
    (r'\bInstituye\b[\s\S]{0,60}\bD[íi]a\b',                                    -4, 'instituye un día conmemorativo'),
    (r'\bDeclara\s+Municipalidad\b',                                            -4, 'creación de municipalidad'),
    (r'\bCrea\s+el\b',                                                         -3, 'creación normativa'),
    (r'\breconocimiento\s+definitivo\s+como\s+partido\s+pol[íi]tico\b',          -3, 'reconocimiento de partido político'),
]


def clasificar_norma(tipo, sintesis, texto_completo, rubro=None):
    if tipo == 'LEY':
        return False, -99, ['ley: siempre general']
    if rubro and _clave_rubro(rubro) == _clave_rubro(RUBRO_DESIGNACIONES):
        # El propio boletín ya separó estos decretos como actos de personal
        # (designación, prórroga, renuncia, jubilación...): no hace falta
        # adivinar por palabras clave, el rubro editorial ya lo dice.
        return True, 99, ['rubro Designaciones: siempre individual']

    puntaje, motivos = 0, []
    art = sintesis or ''
    cuerpo = texto_completo or ''

    for patron, peso, etiqueta in PATRONES_INDIVIDUAL:
        if re.search(patron, art, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'+{peso} síntesis: {etiqueta}')
        elif re.search(patron, cuerpo, re.IGNORECASE):
            medio = max(1, peso // 2)
            puntaje += medio
            motivos.append(f'+{medio} cuerpo: {etiqueta}')

    for patron, peso, etiqueta in PATRONES_GENERAL:
        if re.search(patron, art, re.IGNORECASE) or re.search(patron, cuerpo, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'{peso}: {etiqueta}')

    return (puntaje >= UMBRAL_INDIVIDUAL), puntaje, motivos


# ===========================================================================
# EMISOR
# ===========================================================================
RE_REFRENDA = re.compile(
    r'refrendad[oa]\s+por\s+(?:(?:el|la|los|las)\s+)?señor(?:es)?a?s?\s+'
    r'(?P<cargo>Ministro|Ministra|Ministros|Ministras)\s+de\s+(?P<area>[^.,\n]{3,80})',
    re.IGNORECASE)


def emisor_de_norma(norma, usar_refrenda=False):
    clave = _clave_rubro(norma.get('rubro') or '')
    fijo = EMISOR_FIJO.get(clave)
    if fijo in ('PODER EJECUTIVO',) and usar_refrenda:
        m = RE_REFRENDA.search(norma.get('texto_completo') or '')
        if m:
            area = _compacto(m.group('area')).rstrip('.')
            return f"MINISTERIO DE {area}".upper()
    if fijo:
        return fijo
    # Cualquier otro rubro es, literalmente, el nombre del organismo.
    return _compacto(norma.get('rubro') or '').upper() or 'PODER EJECUTIVO'


# ===========================================================================
# DESCUBRIMIENTO (sitio en vivo)
# ===========================================================================
_SESION = None


def sesion():
    global _SESION
    if _SESION is None:
        _SESION = requests.Session()
        _SESION.headers.update(HEADERS_WEB)
    return _SESION


def descargar(url, timeout=45, esperar_pdf=False):
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


RE_FILA_GRILLA = re.compile(
    r'Bolet[íi]n\s+Oficial\s+N[º°o]\s*(?P<numero>\d+)\s*-\s*'
    r'(?P<dia>\d{1,2})\s+de\s+(?P<mes>[A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+de\s+(?P<anio>\d{4})',
    re.IGNORECASE)


def buscar_fila_boletin(anio, numero=None):
    """
    Recorre la grilla de /anio-{anio}.html y devuelve
    (numero, fecha_iso, url_detalle) de la primera fila (= último boletín) o,
    si se pidió `numero`, de la fila que matchea ese número.
    """
    if BeautifulSoup is None:
        raise RuntimeError("Falta beautifulsoup4: pip install beautifulsoup4")
    html = descargar(f'{SITIO}/anio-{anio}.html')
    if not html:
        return None, None, None
    soup = BeautifulSoup(html, 'html.parser')
    for tr in soup.find_all('tr'):
        a = tr.find('a', href=True)
        if not a:
            continue
        m = RE_FILA_GRILLA.search(_compacto(a.get_text(' ')))
        if not m:
            continue
        num = m.group('numero')
        if numero and str(numero) != num:
            continue
        fecha_iso = _fecha_iso(m.group('dia'), m.group('mes'), m.group('anio'))
        href = a['href']
        url_detalle = href if href.startswith('http') else f"{SITIO}{href}"
        return num, fecha_iso, url_detalle
    return None, None, None


def leer_detalle(url_detalle):
    """
    De la página de detalle de un boletín, devuelve:
    (url_pdf, texto_sumario, anexos_map)

    `texto_sumario` es el texto plano posterior al marcador "SUMARIO" (con los
    <br> ya convertidos a '\n'). `anexos_map` mapea texto de enlace normalizado
    -> URL del PDF individual (leyes, y algunas resoluciones/disposiciones
    destacadas), para usar como url_norma cuando esté disponible.
    """
    if BeautifulSoup is None:
        raise RuntimeError("Falta beautifulsoup4: pip install beautifulsoup4")
    html = descargar(url_detalle)
    if not html:
        return None, '', {}
    soup = BeautifulSoup(html, 'html.parser')
    cuerpo = soup.find('div', class_='com-content-article__body') or soup

    anexos_map = {}
    url_pdf = None
    for a in cuerpo.find_all('a', href=True):
        href = a['href']
        if not href.lower().endswith('.pdf'):
            continue
        href_abs = href if href.startswith('http') else f"{SITIO}{href}"
        texto = _compacto(a.get_text(' '))
        if texto.lower().startswith('versión pdf') or texto.lower().startswith('version pdf'):
            url_pdf = href_abs
            continue
        if texto:
            anexos_map[_clave_rubro(texto)] = href_abs

    for br in cuerpo.find_all('br'):
        br.replace_with('\n')
    texto_completo = cuerpo.get_text()
    idx = texto_completo.upper().find('SUMARIO')
    texto_sumario = texto_completo[idx + len('SUMARIO'):] if idx != -1 else ''

    return url_pdf, texto_sumario, anexos_map


def construir_url_pdf(numero, anio):
    """Fallback si la página de detalle no trajo el link directo."""
    return f"{SITIO}/images/Archivos/BoletinOficial/{anio}/BO{numero}.pdf"


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


def construir_sintesis(norma):
    cuerpo = _compacto(norma.get('sintesis') or '').strip(' .-:')
    if len(cuerpo) > MAX_SINTESIS:
        cuerpo = cuerpo[:MAX_SINTESIS].rsplit(' ', 1)[0] + '…'
    return cuerpo or f"{norma.get('tipo')} {norma.get('numero')}"


def recortar_texto(texto, tope=MAX_TEXTO_COMPLETO):
    texto = texto or ''
    if len(texto) <= tope:
        return texto
    marca = ' […] '
    cabeza = int((tope - len(marca)) * 0.55)
    cola = tope - len(marca) - cabeza
    return texto[:cabeza] + marca + texto[-cola:]


def url_norma(url_pdf, norma, anexos_map):
    numero_legible = norma.get('numero')
    if norma.get('sigla'):
        numero_legible = f"{numero_legible}-{norma['sigla']}"
    etiqueta_anexo = _clave_rubro(f"{norma.get('tipo')} N {numero_legible}")
    # Búsqueda tolerante en el mapa de anexos: por número solo (evita fallar
    # si la etiqueta del anexo no repite el tipo exacto, p.ej. "DI-2026-31-...").
    for clave_anexo, href in anexos_map.items():
        if str(norma.get('numero')) in clave_anexo or (
                norma.get('sigla') and norma['sigla'].upper() in clave_anexo):
            return href
    base = f"{norma.get('tipo')}-{numero_legible}-{norma.get('anio')}"
    slug = re.sub(r'[^A-Za-z0-9]+', '-', _sin_acentos(base)).strip('-')
    return f"{url_pdf}#{slug}"


def emisor_final(norma, usar_refrenda=False):
    return emisor_de_norma(norma, usar_refrenda)


# ===========================================================================
# EJECUCIÓN
# ===========================================================================
def _main():
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de La Pampa.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se descubre por la grilla del año')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--pdf', metavar='ARCHIVO', help='usar un PDF local (pruebas)')
    ap.add_argument('--texto', metavar='ARCHIVO',
                    help='usar un .txt ya extraído del PDF (pruebas del parser)')
    ap.add_argument('--sumario', metavar='ARCHIVO',
                    help='HTML de la página de detalle guardado en un archivo')
    ap.add_argument('--boletin', type=int, help='número de boletín a procesar')
    ap.add_argument('--anio', type=int, help='año del boletín (default: el actual)')
    ap.add_argument('--todas', action='store_true',
                    help='muestra también las individuales, con puntaje y motivos')
    ap.add_argument('--sin-filtro', action='store_true', help='envía todo sin filtrar')
    ap.add_argument('--tribunales', action='store_true',
                    help='suma TRIBUNAL DE CUENTAS y TRIBUNAL ELECTORAL')
    ap.add_argument('--emisor-refrenda', action='store_true',
                    help='para Decretos/Designaciones, usa el Ministerio que '
                         'refrenda en vez de PODER EJECUTIVO')
    ap.add_argument('--volcar', action='store_true', help='imprime sumario y bloques y sale')
    args = ap.parse_args()

    anio_boletin = args.anio or date.today().year
    numero_boletin = args.boletin
    fecha_boletin = None
    url_pdf = ''
    anexos_map = {}
    texto_sumario_html = ''
    ruta_temporal = None
    paginas = None

    # ---- 1. Conseguir el boletín -------------------------------------------
    if args.texto:
        with open(args.texto, encoding='utf-8') as f:
            crudo = f.read()
        paginas = [crudo]
        print(f"Usando texto local: {args.texto}", file=sys.stderr)
    elif args.pdf:
        ruta_pdf = args.pdf
        print(f"Usando PDF local: {args.pdf}", file=sys.stderr)
    else:
        try:
            num, fecha_iso, url_detalle = buscar_fila_boletin(anio_boletin, numero_boletin)
        except RuntimeError as e:
            salida("error", str(e))
        if not num:
            salida("warning", f"No se encontró el boletín en la grilla de {anio_boletin}.")
        numero_boletin, fecha_boletin = num, fecha_iso
        print(f"Boletín Nº {numero_boletin} ({fecha_boletin}): {url_detalle}", file=sys.stderr)

        try:
            url_pdf_detectada, texto_sumario_html, anexos_map = leer_detalle(url_detalle)
        except RuntimeError as e:
            salida("error", str(e))
        url_pdf = url_pdf_detectada or construir_url_pdf(numero_boletin, anio_boletin)

        contenido = descargar(url_pdf, timeout=90, esperar_pdf=True)
        if not contenido:
            salida("warning", f"No se pudo descargar el PDF del Boletín Nº {numero_boletin}.")
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.write(contenido)
        tmp.close()
        ruta_pdf = ruta_temporal = tmp.name

    if args.sumario:
        with open(args.sumario, encoding='utf-8') as f:
            crudo_sumario = f.read()
        if '<' in crudo_sumario and BeautifulSoup is not None:
            soup = BeautifulSoup(crudo_sumario, 'html.parser')
            cuerpo = soup.find('div', class_='com-content-article__body') or soup
            for a in cuerpo.find_all('a', href=True):
                href = a['href']
                if not href.lower().endswith('.pdf'):
                    continue
                href_abs = href if href.startswith('http') else f"{SITIO}{href}"
                texto = _compacto(a.get_text(' '))
                if texto and not texto.lower().startswith(('versión pdf', 'version pdf')):
                    anexos_map[_clave_rubro(texto)] = href_abs
            for br in cuerpo.find_all('br'):
                br.replace_with('\n')
            texto_completo = cuerpo.get_text()
            idx = texto_completo.upper().find('SUMARIO')
            texto_sumario_html = texto_completo[idx + len('SUMARIO'):] if idx != -1 else texto_completo
        else:
            texto_sumario_html = crudo_sumario

    # ---- 2. Parsear ---------------------------------------------------------
    try:
        if paginas is None:
            paginas = leer_paginas(ruta_pdf)
        num_tapa, fecha_tapa = metadatos_boletin(paginas)
        numero_boletin = numero_boletin or num_tapa
        fecha_boletin = fecha_boletin or fecha_tapa
        anio_boletin = int((fecha_boletin or '')[:4] or anio_boletin)
        cuerpo_limpio = limpiar_cuerpo(paginas)
        cuerpo_plano = _sin_acentos(cuerpo_limpio).upper()

        rubros_sumario, orden_sumario = partir_sumario_en_rubros(texto_sumario_html)
        if not rubros_sumario:
            orden_sumario = detectar_rubros_desde_cuerpo(cuerpo_plano)
            print(f"Aviso: no se pudo leer el SUMARIO (¿--pdf sin --sumario, o "
                  f"el sitio no devolvió el bloque esperado?). Se detectaron "
                  f"{len(orden_sumario)} rubros directamente en el cuerpo, SIN "
                  f"control de cobertura contra un oráculo.", file=sys.stderr)

        bloques_offsets = cortar_por_rubros(cuerpo_plano, orden_sumario, args.tribunales)
        # Los offsets se calcularon sobre el texto en mayúsculas/sin acentos,
        # pero _sin_acentos(...).upper() preserva la cantidad de caracteres,
        # así que valen igual sobre `cuerpo_limpio` (el texto legible).
        bloques_legibles = [(nombre, cuerpo_limpio[ini:fin])
                           for nombre, ini, fin in bloques_offsets]

        normas = []
        for nombre_rubro, bloque in bloques_legibles:
            normas.extend(extraer_normas_de_rubro(nombre_rubro, bloque, fecha_boletin, anio_boletin))

    except Exception as e:
        salida("error", f"No se pudo parsear el boletín: {e}")
    finally:
        if ruta_temporal:
            try:
                os.unlink(ruta_temporal)
            except Exception:
                pass

    # ---- 3. Control de cobertura contra el sumario -------------------------
    esperadas = []
    for etiqueta, contenido in rubros_sumario.items():
        clave = _clave_rubro(etiqueta)
        if clave in RUBROS_TRIBUNALES_CLAVE and not args.tribunales:
            continue
        if clave in RUBROS_CIERRE_CLAVE:
            continue
        for it in expandir_rubro(contenido):
            it['rubro'] = etiqueta
            esperadas.append(it)

    extraidas_clave = {clave_norma(n['tipo'], n['numero'], n['anio'], n.get('sigla'))
                       for n in normas}
    faltantes = [e for e in esperadas
                 if clave_norma(e['tipo'], e['numero'], e.get('anio') or anio_boletin,
                                e.get('sigla')) not in extraidas_clave]

    print(f"Sumario: anuncia {len(esperadas)} normas (rubros: {len(rubros_sumario)}), "
          f"se extrajeron {len(normas)} ({len(faltantes)} faltantes)", file=sys.stderr)
    for f in faltantes[:15]:
        print(f"  FALTA  [{f['rubro']}] {f['tipo']} {f['numero']}"
              f"{'-' + f['sigla'] if f.get('sigla') else ''}", file=sys.stderr)

    if args.volcar:
        print(f"--- PDF: {len(paginas)} páginas ---", file=sys.stderr)
        print(f"--- RUBROS detectados en el cuerpo: {len(bloques_legibles)} ---", file=sys.stderr)
        for nombre, bloque in bloques_legibles:
            print(f"  {nombre:45s} {len(bloque):7d} car.", file=sys.stderr)
        print(f"--- SUMARIO: {len(esperadas)} normas anunciadas ---", file=sys.stderr)
        for e in esperadas:
            print(f"  [{e['rubro']}] {e['tipo']:12s} {e['numero']:>8s}"
                  f"{'-' + e['sigla'] if e.get('sigla') else '':15s}", file=sys.stderr)
        print(f"--- CUERPO: {len(normas)} normas extraídas ---", file=sys.stderr)
        for n in normas:
            print(f"  [{n['rubro']}] {n['tipo']:12s} {str(n['numero']):>8s} "
                  f"{len(n['texto_completo']):6d} car. | {n['sintesis'][:60]}", file=sys.stderr)
        salida("success", f"volcado: {len(esperadas)} en el sumario, {len(normas)} en el cuerpo.")

    for n in normas:
        n['es_individual'], n['puntaje'], n['motivos'] = clasificar_norma(
            n['tipo'], n['sintesis'], n['texto_completo'], n.get('rubro'))

    generales = [n for n in normas if not n['es_individual']]
    individuales = [n for n in normas if n['es_individual']]
    a_enviar = normas if args.sin_filtro else generales

    guardar_debug(json.dumps(normas, ensure_ascii=False, indent=2, default=str), 'debug_lapampa.json')
    print(f"Boletín {numero_boletin or '?'} del {fecha_boletin} | normas: {len(normas)} "
          f"(generales {len(generales)} / individuales {len(individuales)})", file=sys.stderr)

    if args.dry_run:
        for n in (normas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            numero_legible = n['numero'] + (f"-{n['sigla']}" if n.get('sigla') else '')
            print(f"[{marca}] {n['tipo']:12s} N° {numero_legible:>18s}/{n['anio']} "
                  f"{emisor_final(n, args.emisor_refrenda)[:35]:35s} "
                  f"{n['sintesis'][:50]}", file=sys.stderr)
            if args.todas and n.get('motivos'):
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    if not normas:
        salida("warning", "No se reconoció ninguna norma en los rubros procesados.")
    if not a_enviar:
        salida("warning", f"Las {len(individuales)} normas del boletín son actos "
                          f"individuales; no se envió ninguna.")

    if fecha_boletin and verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

    # ---- 4. Envío -----------------------------------------------------------
    payload = [{
        "id_jurisdiccion": args.id_jurisdiccion,
        "nombre_emisor": emisor_final(n, args.emisor_refrenda),
        "tipo_norma_desc": n["tipo"],
        "numero": n["numero"] + (f"-{n['sigla']}" if n.get('sigla') else ''),
        "anio": n["anio"],
        "fecha_publicacion": n.get("fecha_publicacion", fecha_boletin),
        "sintesis": construir_sintesis(n),
        "texto_completo": recortar_texto(n["texto_completo"]),
        "url_norma": url_norma(url_pdf, n, anexos_map),
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

    mensaje = respuesta.get('mensaje', 'OK') or 'OK'
    extra = None
    if faltantes:
        detalle = ', '.join(f"{f['tipo']} {f['numero']}" for f in faltantes[:10])
        if len(faltantes) > 10:
            detalle += f" y {len(faltantes) - 10} más"
        extra = {
            "advertencia": f"El sumario anuncia {len(faltantes)} normas que no se extrajeron: {detalle}",
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