#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 BOLETÍN OFICIAL DE LA PROVINCIA DE LA RIOJA  —  id_jurisdiccion 13
===============================================================================

A diferencia de La Pampa, ESTA VERSIÓN SÍ SE PROBÓ CONTRA LOS PDFs REALES
(con pdfplumber, no una aproximación en .docx): los 3 boletines que mandó el
usuario (2026-05-29, 2026-07-17, 2026-07-24) se corrieron completos. La trampa
grande de esta provincia (columnas) se descubrió y resolvió así, corriendo
contra el PDF real — no es una hipótesis pendiente de confirmar.

DESCUBRIMIENTO
--------------
Un solo HTML (`boletin.html`) muestra siempre el último boletín publicado:

    https://www.boletinoflarioja.com.ar/boletin.html
    <a href="boletin/2026-07-24.pdf">-2026-07-24</a>

y la ruta del PDF es predecible por FECHA (no por número correlativo, y sin
tantear nada): `https://www.boletinoflarioja.com.ar/boletin/AAAA-MM-DD.pdf`.
Para pedir una fecha vieja alcanza con armar la URL directamente, sin pasar
por `boletin.html`.

LA TRAMPA GRANDE: EL PDF ESTÁ EN DOS COLUMNAS
------------------------------------------------
Cada página del cuerpo (de la 2 en adelante) tiene dos columnas de texto.
`pdfplumber.page.extract_text()`, sin ayuda, NO respeta el orden de lectura:
mezcla renglones de la columna izquierda y la derecha según su altura en la
página, así que el texto sale intercalado y roto a la mitad de cada oración.
Comprobado contra el PDF real: el Artículo 4º de la Ley 10.877 se corta a la
mitad y sigue con el final del Artículo 9º de OTRA norma.

La solución (`texto_de_pagina()`) NO usa `extract_text()` directo. Por cada
página:
  1. Recorta la banda del encabezado (los primeros ~45pt), que es una sola
     línea que cruza las dos columnas y se rompería mal si se la deja adentro
     del recorte por columna.
  2. Busca el "gutter" (el corredor vertical vacío entre columnas) mirando el
     hueco más grande entre las posiciones X de las palabras, en la franja
     central de la página (30%-70% del ancho). En los 3 PDFs de muestra el
     gutter cae justo en el medio (~297pt de 595pt), pero se lo recalcula por
     página en vez de asumir el punto medio fijo, por si alguna página usa
     otra maqueta (una tabla ancha, por ejemplo).
  3. Extrae el texto de la mitad izquierda y de la mitad derecha por
     separado (cada uno ya en su propio orden de lectura correcto) y los
     concatena: primero toda la columna izquierda, después toda la derecha.
  4. Si no se encuentra un hueco real (>=8pt) en esa franja central, se
     asume que la página no está en columnas y se usa el recorte completo
     sin dividir (fallback defensivo).

La página 1 (tapa, con el cuadro RESUMEN) y la última página (contratapa con
la nómina de funcionarios y las tarifas) NO pasan por `texto_de_pagina()`:
la tapa se lee con `extract_text()` plano porque ahí sólo importa el cuadro
RESUMEN, y la contratapa se descarta entera (ver más abajo).

EL ORÁCULO VIVE EN LA TAPA DEL PROPIO PDF (no hace falta scrapear nada aparte)
--------------------------------------------------------------------------------
La página 1 trae un cuadro fijo:

    RESUMEN
    LEYES
    N°s. 10.877 – 10.880 – 10.881
    DECRETOS
    Año 2026
    N°s. 1.088 – 1.089 – 1.090
    RESOLUCIONES
    LICITACIONES

Los cuatro rubros (LEYES, DECRETOS, RESOLUCIONES, LICITACIONES) SIEMPRE
aparecen en ese orden, aunque estén vacíos (edición sin novedades — pasó en
2 de las 3 muestras). Es el control de cobertura, análogo al sumario de
Entre Ríos o al calendario de Jujuy, sólo que acá no requiere una segunda
petición HTTP: ya viene en el propio PDF.

DOS TRAMPAS CHICAS DEL CUADRO RESUMEN
---------------------------------------
1. La lista de números va separada por GUION MEDIO (–, no "-" guion corto):
   "10.877 – 10.880 – 10.881". No se vio ningún rango ("X a Y") en las 3
   muestras — a diferencia de La Pampa, acá parece ser siempre lista plana.
   El separador `y` se vio sólo en LICITACIONES ("33 y 34/2026"), que de
   todos modos se ignora (ver "LICITACIONES" abajo).
2. El año sólo aparece pegado al rubro DECRETOS ("Año 2026") en la muestra
   donde hubo decretos — no se sabe si LEYES/RESOLUCIONES también lo llevan
   cuando tienen contenido (no hubo ninguna muestra con Leyes/Resoluciones Y
   año explícito a la vez). El código lo busca en cualquiera de los tres
   rubros, por las dudas.

CADA NORMA, EN EL CUERPO
--------------------------
El encabezado va SOLO en su renglón ("LEY N° 10.877" o "DECRETO Nº 1.088"),
y entre una norma y la siguiente hay un separador "* * *" (tres asteriscos)
— confirmado contra el PDF real, aunque el separador también se usa más
adelante entre avisos de VARIOS/REMATES/EDICTOS, así que no alcanza solo:
el corte de cada bloque toma el mínimo entre (a) el próximo encabezado
esperado, (b) el próximo "* * *" y (c) el próximo título de sección ruidosa
(ver abajo) — lo que aparezca primero.

- LEY: no trae fecha propia pegada al encabezado (a diferencia del decreto).
  Cierra con una fórmula fija ("Dada en la Sala de Sesiones de la
  Legislatura de la Provincia, en La Rioja, 141º Período Legislativo, a
  dieciocho días del mes de junio del año dos mil veintiséis...") con el
  día y el año escritos EN PALABRAS. Parsear eso es releventamente más
  trabajo para un dato que no cambia el resultado: se usa la fecha del
  propio boletín como fecha_publicacion y, para el año, el "Año AAAA" del
  cuadro RESUMEN si estaba, si no el año del boletín. Puede haber algún caso
  raro (una ley de fin de año que sale publicada al año siguiente) que esto
  no cubra bien — no se vio en las 3 muestras.
- DECRETO: sí trae fecha propia ("La Rioja, 08 de julio de 2026") pegada al
  encabezado. Se usa esa fecha (y su año) cuando está.
- Las 6 normas de las 3 muestras (3 leyes + 3 decretos, todos del B.O.
  12.370) fueron promulgaciones de ley encadenadas: cada Ley va seguida
  inmediatamente de SU PROPIO Decreto de promulgación, no agrupadas por tipo
  como sugeriría el cuadro RESUMEN. El corte por código (no por título de
  sección) es justamente lo que hace que este orden intercalado no importe.
- RESOLUCIONES: ⚠️ NINGUNA de las 3 muestras tenía resoluciones (el cuadro
  RESUMEN las mostró vacías las 3 veces). El código las trata igual que
  Decretos/Leyes (mismo regex de encabezado, mismo corte por "* * *"), pero
  el formato real —¿trae fecha pegada como el Decreto?, ¿quién firma?— es
  una hipótesis sin confirmar. Ver "QUÉ FALTA VALIDAR".

SÍNTESIS Y EMISOR
------------------
- Síntesis: se arma del Artículo 1º, igual que Jujuy — no hay síntesis
  corta en ningún otro lado (a diferencia de la Ley de La Pampa, acá no
  viene resumida en una oración en ningún lado).
- Emisor: LEY → PODER LEGISLATIVO. DECRETO → PODER EJECUTIVO (todas las
  muestras las firma "EL GOBERNADOR DE LA PROVINCIA"). RESOLUCIÓN /
  DISPOSICIÓN → se intenta leer el cargo que antecede a RESUELVE:/DISPONE:
  (mismo mecanismo que Jujuy) y State convertirlo a nombre de organismo; si
  no se encuentra, cae a PODER EJECUTIVO. Sin muestras reales de
  Resolución, esto está sin confirmar.

LICITACIONES / VARIOS / REMATES / EDICTOS — quedan afuera
-------------------------------------------------------------
El cuadro RESUMEN trata a LICITACIONES como una categoría de primer nivel,
al mismo nivel que Leyes/Decretos/Resoluciones. Son llamados a licitación
pública (compras, obra pública), no normativa con Artículo 1º/2º — se
excluyen del envío, igual que en el resto de las provincias. Sirven sólo
como límite: el primer título de "LICITACIONES" (o "VARIOS", "REMATES
JUDICIALES", "EDICTOS JUDICIALES", "EDICTOS DE MINAS") que aparece en el
cuerpo marca el techo de la zona normativa — de ahí en más no hay nada de
interés (edictos judiciales, remates, mensuras mineras, convocatorias de
asambleas de sociedades anónimas: el equivalente a la Sección Comercial de
otras provincias).

Dato curioso: "VARIOS" mezcla avisos privados (asambleas de S.A.) con al
menos un edicto oficial real (Secretaría de Tierras, Resolución de
Expropiación Nº 421) — pero ese acto se menciona DENTRO del edicto, no se
publica su texto completo con Artículo 1º/2º, así que no hay nada que
extraer ahí aunque se quisiera.

LA CONTRATAPA (nómina de funcionarios + tarifas) — se descarta entera
-------------------------------------------------------------------------
La última página de las 3 muestras es idéntica letra por letra (mismos
funcionarios, mismo texto legal, misma tabla de tarifas) pese a ser de
fechas distintas: es una contratapa fija del diseño, no contenido del día.
Se la identifica buscando "FUNCION EJECUTIVA" o "LEYES NUMEROS 226" (la cita
a la ley fundacional del Boletín, texto fijo) y se corta el cuerpo ahí, lo
que primero aparezca.

FECHA Y AÑO DEL BOLETÍN
-------------------------
La tapa también trae, después del cuadro con la dirección postal:
"LA RIOJA Viernes 29 de Mayo de 2026 Edición de páginas 16 - Nº 12.357" —
de ahí sale el número de edición y sirve de respaldo si se corre con --pdf
sin saber la fecha por el nombre del archivo.

FLAGS
-----
    --dry-run        no envía nada
    --pdf ARCHIVO     usa un PDF local (pruebas)
    --texto ARCHIVO   usa un .txt ya extraído (sin separación de columnas:
                      pensado para pegar el cuerpo ya reconstruido, no el
                      PDF crudo)
    --fecha AAAA-MM-DD   fuerza la fecha del boletín a pedir
    --todas          muestra también las individuales, con puntaje y motivos
    --sin-filtro     envía todo sin filtrar
    --volcar         imprime el resumen y los bloques del cuerpo y sale

===============================================================================
QUÉ FALTA VALIDAR
===============================================================================
1. RESOLUCIONES: ninguna de las 3 muestras tenía. Falta una edición con
   resoluciones para confirmar formato de encabezado, si trae fecha propia
   pegada, y quién firma (para el emisor).
2. Rangos en el cuadro RESUMEN ("N° X a Y"): no se vio ninguno en las 3
   muestras (todas listas planas separadas por "–"). Si La Rioja alguna vez
   publica un rango así, hoy no se expande — se perdería del control de
   cobertura (saldría "sin parsear" y quedaría afuera).
3. Actos individuales (designaciones, renuncias, etc.): ninguna de las 6
   normas de muestra es de alcance individual — son 3 leyes de interés
   general y 3 decretos de promulgación. El clasificador reutiliza los
   mismos patrones que Jujuy/La Pampa (mismo idioma administrativo), pero
   no se pudo calibrar con un caso real de La Rioja.
4. Páginas sin dos columnas (una tabla ancha, por ejemplo) podrían confundir
   la detección de gutter. No se vio ningún caso en las páginas con normas
   de las 3 muestras (sólo en páginas de edictos de minas, que ya quedan
   fuera del corte de todos modos).
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

SITIO = 'https://www.boletinoflarioja.com.ar'
URL_BOLETIN_DIA = f'{SITIO}/boletin.html'

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
ALTO_ENCABEZADO_PT = 45   # banda superior de cada página con "Pág. N BOLETIN OFICIAL ..."

MESES_NUM = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'setiembre': 9, 'octubre': 10,
    'noviembre': 11, 'diciembre': 12,
}

# Rubros fijos del cuadro RESUMEN de tapa, en el orden en que siempre aparecen.
RUBROS_RESUMEN = ['LEYES', 'DECRETOS', 'RESOLUCIONES', 'LICITACIONES']
TIPO_DE_RUBRO = {'LEYES': 'LEY', 'DECRETOS': 'DECRETO', 'RESOLUCIONES': 'RESOLUCION'}

# Títulos que marcan el fin de la zona normativa (nada de interés después).
# Los primeros tres son títulos de sección fijos; "Convocatoria" y "Poder
# Judicial de la Nación" se agregaron después de probar contra el PDF real:
# a veces el último decreto de la edición no lleva "* * *" antes del primer
# aviso de VARIOS, así que sin esta ancla el bloque se comía la convocatoria
# siguiente entera.
RUBROS_CIERRE = ['LICITACIONES', 'VARIOS', 'REMATES JUDICIALES',
                 'EDICTOS JUDICIALES', 'EDICTOS DE MINAS']
RE_RUIDO_EXTRA = [
    re.compile(r'^[ \t]*Convocatoria\b.*$', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^[ \t]*Poder\s+Judicial\s+de\s+la\s+Naci[óo]n\s*$', re.MULTILINE | re.IGNORECASE),
]

# Ancla de la contratapa fija (nómina de funcionarios + tarifas), idéntica en
# todas las ediciones. Cualquiera de las dos frases sirve; se usa la que
# aparezca primero.
ANCLAS_CONTRATAPA = ['FUNCION EJECUTIVA', 'LEYES NUMEROS 226']


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
    return re.sub(r'\s+', ' ', (texto or '')).strip()


def _limpiar_numero(num):
    """'10.877' -> '10877'; '421' -> '421'. El punto es separador de miles."""
    if num is None:
        return ''
    n = str(num).strip(' .')
    m = re.fullmatch(r'(\d{1,3})\.(\d{3})', n)
    if m:
        n = m.group(1) + m.group(2)
    n = re.sub(r'[.\s]', '', n)
    return n.lstrip('0') or '0'


def _fecha_iso(dia, mes_nombre, anio):
    mes = MESES_NUM.get(_sin_acentos((mes_nombre or '').lower()))
    if not mes:
        return None
    try:
        return date(int(anio), mes, int(dia)).isoformat()
    except ValueError:
        return None


# ===========================================================================
# LECTURA DEL PDF — LA TRAMPA DE LAS DOS COLUMNAS
# ===========================================================================
RE_NEGRITA_FALSA = re.compile(r'\b([A-ZÁÉÍÓÚÑ])\1([A-ZÁÉÍÓÚÑ])\2([A-ZÁÉÍÓÚÑ])\3')


def texto_de_pagina(page, alto_header=ALTO_ENCABEZADO_PT):
    """
    Texto de una página del CUERPO (no tapa ni contratapa) en el orden de
    lectura correcto. Ver la trampa de las columnas al principio del archivo.
    """
    w, h = page.width, page.height
    banda = page.crop((0, alto_header, w, h))
    words = banda.extract_words()
    if not words:
        return banda.extract_text() or ''

    if RE_NEGRITA_FALSA.search(banda.extract_text() or ''):
        try:
            banda = banda.dedupe_chars(tolerance=1)
            words = banda.extract_words()
        except Exception:
            pass

    xs = sorted(set(round(wd['x0'], 1) for wd in words))
    franja_central = [x for x in xs if w * 0.3 <= x <= w * 0.7]
    gutter = None
    if len(franja_central) >= 2:
        huecos = [(franja_central[i + 1] - franja_central[i],
                  (franja_central[i] + franja_central[i + 1]) / 2)
                 for i in range(len(franja_central) - 1)]
        mejor = max(huecos, key=lambda hu: hu[0])
        if mejor[0] >= 8:   # hueco real; si no, se asume una sola columna
            gutter = mejor[1]

    if gutter is None:
        return banda.extract_text() or ''

    izq = page.crop((0, alto_header, gutter, h)).extract_text() or ''
    der = page.crop((gutter, alto_header, w, h)).extract_text() or ''
    return izq + '\n' + der


def leer_paginas(ruta_pdf):
    """[texto_tapa, texto_pag2, texto_pag3, ..., texto_ultima] — la tapa (índice
    0) se lee sin separar columnas (sólo importa el cuadro RESUMEN); el resto,
    con `texto_de_pagina`."""
    if pdfplumber is None:
        raise RuntimeError("Falta pdfplumber: pip install pdfplumber")
    paginas = []
    with pdfplumber.open(ruta_pdf) as pdf:
        for i, page in enumerate(pdf.pages):
            if i == 0:
                paginas.append(page.extract_text() or '')
            else:
                paginas.append(texto_de_pagina(page))
    return paginas


def cortar_contratapa(paginas_cuerpo):
    """Corta la contratapa fija (nómina de funcionarios + tarifas) si aparece
    entre las páginas del cuerpo. Devuelve la lista de páginas ya recortada."""
    for i, txt in enumerate(paginas_cuerpo):
        pos = None
        for ancla in ANCLAS_CONTRATAPA:
            m = re.search(re.escape(ancla), txt, re.IGNORECASE)
            if m and (pos is None or m.start() < pos):
                pos = m.start()
        if pos is not None:
            return paginas_cuerpo[:i] + [txt[:pos]]
    return paginas_cuerpo


# ===========================================================================
# RESUMEN DE TAPA (el oráculo)
# ===========================================================================
def parsear_resumen(texto_tapa):
    """{'LEYES': contenido, 'DECRETOS': contenido, ...} tal como aparecen en
    el cuadro de tapa. Contenido vacío ('') si el rubro no tuvo novedades."""
    idx1 = texto_tapa.find('RESUMEN')
    idx2 = texto_tapa.find('Nuestra')
    if idx1 == -1:
        return {}
    bloque = texto_tapa[idx1 + len('RESUMEN'):idx2 if idx2 != -1 else len(texto_tapa)]

    posiciones = []
    for etiqueta in RUBROS_RESUMEN:
        m = re.search(r'^[ \t]*' + etiqueta + r'\s*$', bloque, re.MULTILINE | re.IGNORECASE)
        if m:
            posiciones.append((m.start(), m.end(), etiqueta))
    posiciones.sort()

    resumen = {}
    for i, (ini, fin, etiqueta) in enumerate(posiciones):
        fin_bloque = posiciones[i + 1][0] if i + 1 < len(posiciones) else len(bloque)
        resumen[etiqueta] = _compacto(bloque[fin:fin_bloque])
    return resumen


def parsear_lista_resumen(contenido):
    """
    'N°s. 10.877 – 10.880 – 10.881' -> [('10877', None), ('10880', None), ('10881', None)]
    'Año 2026\\nN°s. 1.088 – 1.089' -> [('1088', '2026'), ('1089', '2026')]

    No se vieron rangos ("X a Y") en las 3 muestras — a diferencia de La
    Pampa, sólo listas planas. Si aparece un rango en el futuro, hoy no se
    expande (queda "sin parsear").
    """
    if not contenido:
        return []
    anio = None
    m = re.search(r'A[ñn]o\s*(\d{4})', contenido, re.IGNORECASE)
    if m:
        anio = m.group(1)
        contenido = contenido[:m.start()] + contenido[m.end():]

    m2 = re.search(r'N[º°]s?\.?\s*(.+)', contenido, re.DOTALL)
    if not m2:
        return []
    # Separadores vistos entre números: "–" (guion medio), "-" (guion simple,
    # menos frecuente) e incluso "." con espacios alrededor — a diferencia
    # del punto de miles ("10.862", pegado), el de separación siempre tiene
    # espacio de los dos lados ("10.862 . 10.863"), así que no se confunden.
    partes = re.split(r'\s+[.\-–—]\s+|\s*,\s*|\s+y\s+', m2.group(1))
    numeros = []
    for p in partes:
        p = re.sub(r'[^\d.]', '', p or '')
        if p:
            numeros.append((_limpiar_numero(p), anio))
    return numeros


# ===========================================================================
# ENCABEZADOS Y BLOQUES DEL CUERPO
# ===========================================================================
RE_CABECERA = re.compile(
    r'^[ \t]*(?P<tipo>LEY|DECRETO|RESOLUCI[ÓO]N|DISPOSICI[ÓO]N)\s*'
    r'(?:[A-ZÁÉÍÓÚÑ.]{2,15}\s+)?(?:N[º°]\.?)?\s*'
    r'(?P<numero>\d[\d.]*)\s*$', re.IGNORECASE | re.MULTILINE)

RE_SEPARADOR = re.compile(r'\*\s*\*\s*\*')

RE_FECHA_NORMA = re.compile(
    r'La\s+Rioja,\s*(?P<dia>\d{1,2})\s+de\s+(?P<mes>[A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+de\s+(?P<anio>\d{4})',
    re.IGNORECASE)


def _tipo_normalizado(crudo):
    t = _sin_acentos((crudo or '').upper())
    if t.startswith('RESOLUCI'):
        return 'RESOLUCION'
    if t.startswith('DISPOSICI'):
        return 'DISPOSICION'
    return t


def _regex_titulo(nombre):
    partes = [re.escape(p) for p in nombre.split(' ')]
    return re.compile(r'^[ \t]*' + r'\s+'.join(partes) + r'\s*$', re.IGNORECASE | re.MULTILINE)


def encontrar_marcas(cuerpo):
    """[(inicio, fin_cabecera, tipo, numero)] de todos los encabezados del cuerpo."""
    marcas = []
    for m in RE_CABECERA.finditer(cuerpo):
        marcas.append((m.start(), m.end(), _tipo_normalizado(m.group('tipo')),
                       _limpiar_numero(m.group('numero'))))
    marcas.sort()
    return marcas


def techo_ruido(cuerpo):
    """Offset del primer título de sección ruidosa (LICITACIONES, VARIOS, ...)."""
    techo = len(cuerpo)
    for nombre in RUBROS_CIERRE:
        m = _regex_titulo(nombre).search(cuerpo)
        if m and m.start() < techo:
            techo = m.start()
    for rx in RE_RUIDO_EXTRA:
        m = rx.search(cuerpo)
        if m and m.start() < techo:
            techo = m.start()
    return techo


# ===========================================================================
# SÍNTESIS
# ===========================================================================
_ART1 = (r'ART[ÍI]?CULO\s*(?:N[º°]\s*)?1(?!\d)\s*[º°]?\s*[.:,;-]+\s*'
         r'(?P<texto>[\s\S]{0,1200}?)(?=ART[ÍI]?CULO\s*(?:N[º°]\s*)?2(?!\d)|\Z)')
RE_ARTICULO1 = re.compile(_ART1, re.IGNORECASE)


def _sintesis_de_bloque(bloque):
    m = RE_ARTICULO1.search(bloque)
    if m:
        return _compacto(m.group('texto'))
    return _compacto(bloque[:400])


# ===========================================================================
# EMISOR
# ===========================================================================
RE_CARGO = re.compile(
    r'^[ \t]*(?P<cargo>(?:EL|LA)\s+[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9.,;()\'"\s/e-]{5,120}?)'
    r':?\s*(?:\n\s*)?(?:DECRETA|RESUELVE|DISPONE)\s*:', re.MULTILINE)

_MAPA_CARGO_ORGANISMO = {
    'MINISTRO': 'MINISTERIO', 'MINISTRA': 'MINISTERIO',
    'SECRETARIO': 'SECRETARÍA', 'SECRETARIA': 'SECRETARÍA',
    'DIRECTOR': 'DIRECCIÓN', 'DIRECTORA': 'DIRECCIÓN',
    'SUBSECRETARIO': 'SUBSECRETARÍA', 'SUBSECRETARIA': 'SUBSECRETARÍA',
}


def _cargo_a_organismo(cargo):
    texto = cargo.upper().strip()
    for palabra, base in _MAPA_CARGO_ORGANISMO.items():
        if texto.startswith(palabra + ' ') or texto == palabra:
            return (base + ' ' + texto[len(palabra):].lstrip()).strip()
    return None


def emisor_de_norma(tipo, bloque):
    if tipo == 'LEY':
        return 'PODER LEGISLATIVO'
    if tipo == 'DECRETO':
        return 'PODER EJECUTIVO'
    # RESOLUCION / DISPOSICION: sin muestra real (ver docstring). Se intenta
    # leer el cargo que antecede a RESUELVE:/DISPONE:, con PODER EJECUTIVO
    # como último recurso.
    m = RE_CARGO.search(bloque or '')
    if m:
        cargo = _compacto(m.group('cargo'))
        cargo = re.sub(r'^(EL|LA)\s+', '', cargo, flags=re.IGNORECASE).strip(' .,-')
        org = _cargo_a_organismo(cargo)
        if org:
            return org
        if cargo:
            return cargo.upper()
    return 'PODER EJECUTIVO'


# ===========================================================================
# CLASIFICACIÓN INDIVIDUAL / GENERAL
# ===========================================================================
# Mismos patrones que Jujuy/La Pampa (mismo idioma administrativo). Sin
# muestra real de acto individual en La Rioja — ver "QUÉ FALTA VALIDAR".
UMBRAL_INDIVIDUAL = 3

PATRONES_INDIVIDUAL = [
    (r'\bDes[íi]gn[ae]se\b',                                  4, 'designación'),
    (r'\bAc[ée]pt[ae]se\b[\s\S]{0,80}\brenuncia\b',           4, 'renuncia'),
    (r'\brenuncia\s+presentada\s+por\b',                      4, 'renuncia'),
    (r'\bPromu[ée]v[ae]se\b',                                 4, 'promoción de un agente'),
    (r'\bContrato\s+de\s+Locaci[óo]n\s+de\s+Servicios\b',     3, 'contrato de personal'),
    (r'\bexoneraci[óo]n\b|\bcesant[íi]a\b',                   4, 'sanción expulsiva'),
    (r'\bRecurso\s+Jer[áa]rquico\s+interpuesto\b',            3, 'recurso de un particular'),
    (r'\bOt[óo]rg[au]ese\b[\s\S]{0,60}\bLicencia\b',          3, 'licencia'),
    (r'\bBaja\s+definitiva\b|\bJubilaci[óo]n\b',              3, 'baja / jubilación'),
    (r'\bDNI\b|\bD\.N\.I\b',                                  1, 'menciona DNI de una persona'),
]

PATRONES_GENERAL = [
    (r'\bPromu[úu]lg', -5, 'promulgación de ley'),
    (r'\bCr[ée]a(?:se)?\s+el\b|\bCr[ée]ase\b',                -3, 'creación normativa'),
    (r'\bDeclara(?:se)?\b[\s\S]{0,60}\bCapital\s+Provincial\b', -4, 'declaración de interés provincial'),
    (r'\bInstituye\b[\s\S]{0,60}\bD[íi]a\b',                  -4, 'instituye un día conmemorativo'),
    (r'\bAutor[íi]zase\s+a\s+la\s+Funci[óo]n\s+Ejecutiva\s+a\s+transferir\b', -3, 'donación/transferencia de bien público'),
    (r'\bDer[óo]ganse\b|\bDer[óo]gase\b',                     -3, 'derogación'),
]


def clasificar_norma(tipo, sintesis, texto_completo):
    if tipo == 'LEY':
        return False, -99, ['ley: siempre general']

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
# ARMADO DE NORMAS
# ===========================================================================
def extraer_normas(cuerpo, esperadas, fecha_boletin, anio_boletin):
    marcas = encontrar_marcas(cuerpo)
    separadores = [m.start() for m in RE_SEPARADOR.finditer(cuerpo)]
    techo = techo_ruido(cuerpo)

    normas = []
    for i, (ini, fin_cab, tipo, numero) in enumerate(marcas):
        limite_siguiente = marcas[i + 1][0] if i + 1 < len(marcas) else techo
        limite_estrella = next((s for s in separadores if s > fin_cab), len(cuerpo))
        fin_bloque = min(limite_siguiente, limite_estrella, techo)
        if fin_bloque <= fin_cab:
            continue
        bloque = cuerpo[fin_cab:fin_bloque]

        anio = None
        fecha_norma = fecha_boletin
        m_fecha = RE_FECHA_NORMA.search(bloque[:200])
        if m_fecha:
            iso = _fecha_iso(m_fecha.group('dia'), m_fecha.group('mes'), m_fecha.group('anio'))
            if iso:
                fecha_norma = iso
                anio = m_fecha.group('anio')
        if not anio:
            # ¿el sumario de tapa traía año explícito para este código?
            for e in esperadas:
                if e['tipo'] == tipo and e['numero'] == numero and e.get('anio'):
                    anio = e['anio']
                    break
        if not anio:
            anio = str(anio_boletin)

        sintesis = _sintesis_de_bloque(bloque)
        normas.append({
            'tipo': tipo, 'numero': numero, 'anio': anio,
            'sintesis': sintesis, 'texto_completo': bloque,
            'fecha_publicacion': fecha_norma,
            'emisor': emisor_de_norma(tipo, bloque),
        })
    return normas


def clave_norma(numero):
    return numero


def comparar_con_sumario(esperadas, normas):
    """
    Compara sólo por número, no por tipo: el rubro "RESOLUCIONES" del
    cuadro de tapa es una etiqueta paraguas que en el cuerpo puede
    corresponder a una "DISPOSICIÓN" (se vio con una Disposición D.G.M. de
    la Dirección Gral. de Minería, listada como "RESOLUCIONES" en el
    resumen) — exigir coincidencia exacta de tipo generaba falsos
    "faltantes" para normas que sí se habían extraído bien, sólo que con el
    tipo real que trae el propio encabezado en el cuerpo.
    """
    extraidas = {clave_norma(n['numero']) for n in normas}
    return [e for e in esperadas if clave_norma(e['numero']) not in extraidas]


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


def construir_url_pdf_archivo(fecha_iso):
    """Patrón de las ediciones YA archivadas (todas menos la del día, según
    confirmó el usuario). Nótese la doble barra "AAAA//AAAA-MM-DD.pdf": así
    la arma el propio sitio, se reproduce tal cual."""
    anio = fecha_iso[:4]
    return f'{SITIO}/pdf/{anio}//{fecha_iso}.pdf'


def construir_url_pdf_del_dia(fecha_iso):
    """Patrón de la edición del día, mientras es la última publicada en
    boletin.html. Una vez que deja de ser la última, pasa a vivir sólo en
    `construir_url_pdf_archivo`."""
    return f'{SITIO}/boletin/{fecha_iso}.pdf'


def descargar_pdf_boletin(fecha_iso, url_directa=None):
    """
    Prueba, en orden: la URL descubierta directamente en boletin.html (si
    se tiene), después el patrón de archivo (`/pdf/AAAA//...`, el de la
    inmensa mayoría de las ediciones) y por último el patrón del día
    (`/boletin/...`, por si `--fecha` apunta a la edición de hoy y todavía
    no se archivó). Devuelve (contenido_bytes, url_que_funcionó) o
    (None, None) si ninguna sirvió.
    """
    candidatos = []
    if url_directa:
        candidatos.append(url_directa)
    for u in (construir_url_pdf_archivo(fecha_iso), construir_url_pdf_del_dia(fecha_iso)):
        if u not in candidatos:
            candidatos.append(u)
    for url in candidatos:
        contenido = descargar(url, timeout=90, esperar_pdf=True)
        if contenido:
            return contenido, url
        print(f"Aviso: no se pudo bajar {url}, probando el siguiente patrón de URL...",
              file=sys.stderr)
    return None, None


RE_HREF_BOLETIN = re.compile(r'href="(?:\./)?(boletin/(\d{4}-\d{2}-\d{2})\.pdf)"', re.IGNORECASE)


def buscar_ultimo_boletin():
    """(fecha_iso, url_pdf) del boletín más nuevo listado en boletin.html."""
    html = descargar(URL_BOLETIN_DIA)
    if not html:
        return None, None
    m = RE_HREF_BOLETIN.search(html)
    if not m:
        return None, None
    return m.group(2), f'{SITIO}/{m.group(1)}'


RE_TAPA_METADATOS = re.compile(
    r'LA\s+RIOJA\s+\w+\s+(?P<dia>\d{1,2})\s+de\s+(?P<mes>[A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+de\s+'
    r'(?P<anio>\d{4})\s+Edici[óo]n\s+de\s+p[áa]ginas\s+(?P<paginas>\d+)\s*-\s*'
    r'N[º°]\s*(?P<numero>[\d.]+)', re.IGNORECASE)


def metadatos_tapa(texto_tapa):
    m = RE_TAPA_METADATOS.search(texto_tapa or '')
    if not m:
        return None, None
    fecha = _fecha_iso(m.group('dia'), m.group('mes'), m.group('anio'))
    return fecha, _limpiar_numero(m.group('numero'))


# ===========================================================================
# BACKEND (mismo contrato que el resto de los bots)
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


def url_norma(url_pdf, norma):
    base = f"{norma.get('tipo')}-{norma.get('numero')}-{norma.get('anio')}"
    slug = re.sub(r'[^A-Za-z0-9]+', '-', _sin_acentos(base)).strip('-')
    return f"{url_pdf}#{slug}"


# ===========================================================================
# EJECUCIÓN
# ===========================================================================
def _main():
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de La Rioja.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se descubre por boletin.html')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--pdf', metavar='ARCHIVO', help='usar un PDF local (pruebas)')
    ap.add_argument('--texto', metavar='ARCHIVO',
                    help='usar un cuerpo ya extraído en .txt (pruebas del parser)')
    ap.add_argument('--fecha', metavar='AAAA-MM-DD', help='fuerza la fecha del boletín a pedir')
    ap.add_argument('--todas', action='store_true',
                    help='muestra también las individuales, con puntaje y motivos')
    ap.add_argument('--sin-filtro', action='store_true', help='envía todo sin filtrar')
    ap.add_argument('--volcar', action='store_true', help='imprime resumen y bloques y sale')
    args = ap.parse_args()

    anio_boletin = date.today().year
    fecha_boletin = args.fecha
    numero_edicion = None
    url_pdf = ''
    texto_tapa = ''
    ruta_temporal = None
    paginas = None

    # ---- 1. Conseguir el boletín -------------------------------------------
    if args.texto:
        with open(args.texto, encoding='utf-8') as f:
            cuerpo_directo = f.read()
        paginas = ['', cuerpo_directo]   # tapa vacía: sin oráculo, sólo prueba del parser
        print(f"Usando cuerpo local: {args.texto} (sin cuadro RESUMEN)", file=sys.stderr)
    elif args.pdf:
        ruta_pdf = args.pdf
        print(f"Usando PDF local: {args.pdf}", file=sys.stderr)
    else:
        if not fecha_boletin:
            fecha_boletin, url_directa = buscar_ultimo_boletin()
            if not fecha_boletin:
                salida("warning", "No se encontró el boletín en boletin.html.")
        else:
            url_directa = None
        print(f"Boletín del {fecha_boletin}" +
              (f": {url_directa}" if url_directa else " (buscando URL...)"), file=sys.stderr)

        contenido, url_pdf = descargar_pdf_boletin(fecha_boletin, url_directa)
        if not contenido:
            salida("warning", f"No se pudo descargar el PDF del {fecha_boletin} "
                              f"(probé el patrón de archivo y el del día).")
        print(f"PDF descargado de: {url_pdf}", file=sys.stderr)
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.write(contenido)
        tmp.close()
        ruta_pdf = ruta_temporal = tmp.name

    # ---- 2. Parsear ---------------------------------------------------------
    try:
        if paginas is None:
            paginas = leer_paginas(ruta_pdf)
        texto_tapa = paginas[0]
        fecha_tapa, num_tapa = metadatos_tapa(texto_tapa)
        fecha_boletin = fecha_boletin or fecha_tapa
        numero_edicion = num_tapa
        anio_boletin = int((fecha_boletin or '')[:4] or anio_boletin)

        cuerpo_paginas = cortar_contratapa(paginas[1:])
        cuerpo = '\n'.join(cuerpo_paginas)

        resumen = parsear_resumen(texto_tapa)
        esperadas = []
        for rubro, tipo in TIPO_DE_RUBRO.items():
            for numero, anio in parsear_lista_resumen(resumen.get(rubro, '')):
                esperadas.append({'tipo': tipo, 'numero': numero, 'anio': anio})

        normas = extraer_normas(cuerpo, esperadas, fecha_boletin, anio_boletin)
    except Exception as e:
        salida("error", f"No se pudo parsear el boletín: {e}")
    finally:
        if ruta_temporal:
            try:
                os.unlink(ruta_temporal)
            except Exception:
                pass

    faltantes = comparar_con_sumario(esperadas, normas)
    print(f"Resumen de tapa: anuncia {len(esperadas)} normas "
          f"(Leyes/Decretos/Resoluciones), se extrajeron {len(normas)} "
          f"({len(faltantes)} faltantes)", file=sys.stderr)
    for f in faltantes[:15]:
        print(f"  FALTA  {f['tipo']} {f['numero']}", file=sys.stderr)

    if args.volcar:
        print(f"--- PDF: {len(paginas)} páginas | edición Nº {numero_edicion} ---", file=sys.stderr)
        print(f"--- RESUMEN de tapa: {resumen} ---", file=sys.stderr)
        print(f"--- {len(esperadas)} normas anunciadas ---", file=sys.stderr)
        for e in esperadas:
            print(f"  {e['tipo']:12s} {e['numero']:>8s}  año={e.get('anio')}", file=sys.stderr)
        print(f"--- {len(normas)} normas extraídas ---", file=sys.stderr)
        for n in normas:
            print(f"  {n['tipo']:12s} {n['numero']:>8s}/{n['anio']} "
                  f"{len(n['texto_completo']):6d} car. | {n['emisor']:20s} | {n['sintesis'][:50]}",
                  file=sys.stderr)
        salida("success", f"volcado: {len(esperadas)} anunciadas, {len(normas)} extraídas.")

    for n in normas:
        n['es_individual'], n['puntaje'], n['motivos'] = clasificar_norma(
            n['tipo'], n['sintesis'], n['texto_completo'])

    generales = [n for n in normas if not n['es_individual']]
    individuales = [n for n in normas if n['es_individual']]
    a_enviar = normas if args.sin_filtro else generales

    guardar_debug(json.dumps(normas, ensure_ascii=False, indent=2, default=str), 'debug_larioja.json')
    print(f"Boletín del {fecha_boletin} (Nº {numero_edicion}) | normas: {len(normas)} "
          f"(generales {len(generales)} / individuales {len(individuales)})", file=sys.stderr)

    if args.dry_run:
        for n in (normas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {n['tipo']:12s} N° {n['numero']:>8s}/{n['anio']} "
                  f"{n['emisor'][:30]:30s} {n['sintesis'][:55]}", file=sys.stderr)
            if args.todas and n.get('motivos'):
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    if fecha_boletin and verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

    if not normas:
        if esperadas:
            # El resumen de tapa anunciaba algo y no se extrajo nada: esto sí
            # es un problema real de parseo (no una edición sin novedades).
            # No se registra el historial para poder reintentar/investigar.
            salida("warning", f"El resumen de tapa anuncia {len(esperadas)} normas "
                              f"pero no se reconoció ninguna en el cuerpo del boletín "
                              f"({fecha_boletin}). Revisar el parser.")
        # Edición sin Leyes/Decretos/Resoluciones: no es un error, pasa
        # seguido (sólo trajo Licitaciones, o nada). Se registra en el
        # historial para no reprocesarla, y se informa "success" con 0
        # normas — un "warning" sin este mismo contrato rompía el frontend.
        if fecha_boletin:
            registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Sin novedades: el boletín del {fecha_boletin} no publicó "
                          f"Leyes, Decretos ni Resoluciones.", total=0)

    if not a_enviar:
        # Había normas, pero todas resultaron actos individuales (se filtran
        # del feed general). El boletín SÍ se procesó bien, sólo que no
        # había nada para mandar — se registra el historial igual.
        if fecha_boletin:
            registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Se procesó el boletín del {fecha_boletin}, pero las "
                          f"{len(individuales)} normas encontradas son actos "
                          f"individuales; no se envió ninguna.", total=0)

    # ---- 3. Envío -----------------------------------------------------------
    payload = [{
        "id_jurisdiccion": args.id_jurisdiccion,
        "nombre_emisor": n['emisor'],
        "tipo_norma_desc": n["tipo"],
        "numero": n["numero"],
        "anio": n["anio"],
        "fecha_publicacion": n.get("fecha_publicacion", fecha_boletin),
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

    mensaje = respuesta.get('mensaje', 'OK') or 'OK'
    extra = None
    if faltantes:
        detalle = ', '.join(f"{f['tipo']} {f['numero']}" for f in faltantes[:10])
        extra = {
            "advertencia": f"El resumen de tapa anuncia {len(faltantes)} normas que no se extrajeron: {detalle}",
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