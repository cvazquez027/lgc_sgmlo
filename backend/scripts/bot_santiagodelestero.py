#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
 BOLETÍN OFICIAL DE LA PROVINCIA DE SANTIAGO DEL ESTERO  —  id_jurisdiccion 23
===============================================================================

SITIO Y ACCESO — HTTP PURO, SIN NÚMERO DE EDICIÓN NAVEGABLE, SIN ARCHIVO
-------------------------------------------------------------------------------
Sitio: http://www.boletinsde.gov.ar/  — confirmado por el usuario que NO
acepta https (probado real: tanto la portada como el PDF devuelven 403 a
través del proxy de mi sandbox por allowlist, y por separado mi propia
herramienta de fetch reescribe silenciosamente a https sin avisar, lo que
en un sitio que de verdad no tiene TLS produce una conexión fallida
silenciosa). NINGUNO de los dos síntomas es informativo sobre si el sitio
funciona por http puro para un cliente normal (requests, sin proxy, sin
reescritura de esquema) — no pude confirmarlo en vivo yo mismo (ver "QUÉ NO
SE PUDO VALIDAR EN VIVO" más abajo). SITIO/URL_PDF están escritos
literalmente con 'http://' a propósito; no cambiar a https.

La portada normal del sitio (http://www.boletinsde.gov.ar/) pide datos
personales para "descargar" el Boletín — el bot NUNCA toca ese formulario
(no se completan ni envían datos personales). El usuario identificó que el
PDF del día es accesible directo, sin ese formulario, en:

    http://www.boletinsde.gov.ar/boletin/boletindeldia.pdf

Ese PDF es SIEMPRE "el más reciente disponible", no necesariamente el de
hoy: confirmado por el usuario en vivo (pedido un domingo 2/8/2026, el PDF
mostraba la edición del viernes 31/7 — no se publica en fin de semana, el
sitio simplemente sigue sirviendo la última real). El usuario tampoco
encontró forma de navegar a ediciones anteriores desde el sitio — a
diferencia de TODA la familia anterior (Salta/San Juan/San Luis/Santa
Cruz/Santa Fe), acá no existe ni un número de edición para saltar
(--bo N) ni una fecha para pedir (--fecha YYYY-MM-DD): este bot SIEMPRE
procesa lo que esté publicado en boletindeldia.pdf en el momento de
ejecutarlo. La identidad de la edición (para verificar_boletin_procesado /
registrar_boletin_procesado) se toma de la fecha real impresa en la tapa
del PDF (ver _fecha_edicion_portada), exactamente el mismo criterio
"por fecha, no por número" que ya usa bot_santafe.py.

DESCARGA EN PRODUCCIÓN — CONFIRMADA REAL
-------------------------------------------------------------------------------
Mi propio sandbox de desarrollo no pudo alcanzar boletinsde.gov.ar (proxy
saliente propio que lo bloquea por allowlist, 403 "blocked-by-allowlist",
sin relación con el sitio en sí). Pero el usuario corrió el bot en su
servidor real (VPS/XAMPP) con `descargar_bytes(URL_PDF)` sin ningún ajuste
de User-Agent adicional, y bajó y procesó el PDF correctamente en el
primer intento — confirma que el sitio SÍ es alcanzable libremente por
http puro desde un cliente normal, sin necesidad de headers especiales.
Sigue sin confirmarse si el nombre de archivo "boletindeldia.pdf" es
siempre fijo entre ediciones (no hay forma de comprobarlo sin esperar a
ver una edición distinta).

TODO el resto de este módulo (estructura del PDF, columnas, secciones,
campos de cada Decreto, limpieza de texto) SÍ está confirmado contra el PDF
real que el usuario subió (boletindeldia.pdf, edición del 31/07/2026, 16
páginas, Boletín N° 23.139) — bajado y procesado en un sandbox que sí tuvo
acceso normal a la red en un momento posterior de esta misma sesión (ver
detalle técnico en cada función).

ESTRUCTURA DEL PDF — CONFIRMADA REAL (16 páginas, edición 31/07/2026)
-------------------------------------------------------------------------------
Página 1: tapa/portada (masthead, sin normativa) — de acá se lee la fecha
real de la edición (_fecha_edicion_portada): "...Viernes 31 de Julio de
2026..." aparece dos veces (masthead superior + bloque de datos de tapa).

A partir de página 2: el documento está dividido en SECCIONES con un
título centrado de ancho de página, en una tipografía con tracking muy
ancho — tan ancho que pdfplumber (con el x_tolerance por defecto de
extract_words) separa cada letra como una "palabra" de 1 carácter (ver
_titulos_seccion). Confirmado real en esta edición, en este orden:

    Pág.  2, primera línea de cuerpo: SECCION ADMINISTRATIVA
              (subtítulo de rubro, mismo estilo): DECRETOS
    Pág.  6, línea 41: SECCIÓN AVISOS VARIOS
    Pág. 12, línea 13: SECCIÓN AVISOS DE HOY

Sólo "SECCION ADMINISTRATIVA" importa (instrucción explícita del usuario:
"nos interesa la sección administrativa nomás"). En esta edición, dentro
de esa sección hay UN solo rubro con estructura de norma individual:
DECRETOS (10 decretos reales, DECRETO-2026-1272 a 1281). No hay ejemplos
reales de LEYES ni RESOLUCIONES publicadas como acto independiente dentro
de esta sección en la muestra disponible — sí aparecen RESOLUCIONES
mencionadas, pero siempre como el objeto que un Decreto homologa/ratifica,
nunca publicadas por sí solas. RE_HEADER_NORMA igual reconoce LEY/
RESOLUCION/DISPOSICION con el mismo patrón de encabezado que DECRETO (ver
más abajo) por si alguna aparece publicada directamente en una edición
futura — sin garantía de que el formato coincida exactamente, al no haber
podido verlo real.

Las otras 2 secciones (AVISOS VARIOS, AVISOS DE HOY — edictos, cédulas,
notificaciones catastrales, avisos de particulares/organismos, y al menos
una Resolución de personal con Anexo de altas/bajas) quedan explícitamente
fuera de alcance por instrucción del usuario, y además no tienen estructura
de "una norma por ítem" sino que son avisos sueltos — igual que las
secciones de Avisos/Licitaciones que se excluyeron en Santa Fe.

DISEÑO DE 3 COLUMNAS — CONFIRMADO REAL, RESUELTO CON pdfplumber
-------------------------------------------------------------------------------
Cada página de la Sección Administrativa está maquetada en 3 columnas
verticales fijas (A4, 596x842pt). Confirmado real midiendo la ocupación
horizontal de palabras (histograma de x0..x1) en 5 páginas distintas: hay
"calles" vacías (gutters) siempre en los mismos rangos:

    columna 0: x < 213          (gutter 202-225 entre col.0 y col.1)
    columna 1: 213 <= x < 385   (gutter 374-397 entre col.1 y col.2)
    columna 2: x >= 385

COL_LIMITE_1 / COL_LIMITE_2 son estos 2 cortes. Es una maqueta fija
(mismo generador día a día — "Corel PDF Engine" / "Print Server 120" según
los metadatos del PDF), así que se usan como constantes en vez de
recalcularlas por página; si una edición futura cambiara el ancho de
columnas esto se rompería visiblemente (columnas mezcladas) y se vería en
--volcar.

Se probaron 2 caminos de extracción de texto y se descartó el primero:

  1. `pdftotext -layout` (poppler): reconstruye las 3 columnas sorprendente-
     mente bien via heurística de espacios en blanco, PERO reintroduce
     espacios falsos DENTRO de palabras normales en partes del cuerpo
     ("R e f e r e n c ia :", "EX -2 0 25 -0 4 3 8 6 2 7 6") de forma
     inconsistente entre líneas — probablemente por kerning/posicionamiento
     de glyphs particular de este generador de PDF. Encontrado real,
     descartado.

  2. `pdfplumber.Page.extract_words()` + clustering manual por columna:
     agrupa palabras completas correctamente en el 99% de los casos (nada
     de espacios falsos en "Referencia:", "VISTO:", números de expediente,
     etc. — ver _extraer_texto_columnas), Y da control total sobre el
     límite de fin de sección (a diferencia de -layout, que mezclaría
     texto de la sección siguiente sin un punto de corte explícito).
     ELEGIDO.

Dentro de cada página, cada columna se arma ordenando sus palabras por
(top redondeado, x0) y uniéndolas con espacio; las 3 columnas se concatenan
en orden (columna 0, luego 1, luego 2) antes de pasar a la página
siguiente. Confirmado real que un Decreto puede empezar en la columna 2 de
una página y seguir en la columna 0 de la página siguiente sin ningún
marcador especial (DECRETO-2026-1279, fin de pág. 5 -> inicio pág. 6) — la
concatenación por página, en orden de columna, alcanza para que quede en
el orden de lectura correcto sin tratamiento especial.

FUENTE DE TÍTULOS DE SECCIÓN / CÓMO SE DETECTA EL LÍMITE
-------------------------------------------------------------------------------
En vez de buscar el texto literal "SECCION ADMINISTRATIVA" (frágil: ese
texto NUNCA aparece como una sola palabra en el flujo de extract_words(),
por el tracking ancho ya descripto), _titulos_seccion barre TODAS las
páginas buscando corridas de 3+ "palabras" de 1 sola letra mayúscula
consecutivas (mismo top, tolerancia 3pt) y las concatena sin espacios. Se
queda sólo con las corridas de 7+ letras cuyo resultado empieza con
"SECCION"/"SECCIÓN" (sin acentos) — esto también detecta "DECRETA:" (7
letras) pero como no empieza con "SECCION" no genera falso positivo.
_rango_seccion_administrativa toma el primer título que CONTENGA
"ADMINISTRATIVA" como inicio, y el siguiente título SECCION (cualquiera)
como fin — así, si algún día la Sección Administrativa no fuera la primera
del documento, o si el número de decretos cambia el largo de la sección
(más o menos páginas), el corte se sigue encontrando solo. Si no se
encuentra ningún título "...ADMINISTRATIVA..." en absoluto (estructura del
PDF cambió de forma más profunda), procesar_pdf devuelve normas=None y el
bot corta con status "warning" sin enviar nada — se prefiere no mandar
nada a mandar algo mal recortado.

CAMPOS DE CADA DECRETO — CONFIRMADO REAL (10/10 decretos de la muestra)
-------------------------------------------------------------------------------
Cada norma dentro de la sección tiene este patrón, confirmado real en los
10 decretos de la edición 31/07/2026 (1272 a 1281, todos firmados el mismo
día real "MARTES 23 DE JUNIO DE 2026" pese a publicarse 5 semanas después
— igual de desfasado que Santa Fe entre fecha de sanción y de edición):

    DECRETO-2026-1272-E-GDESDE- GSDE
    SANTIAGO DEL ESTERO, MARTES 23 DE JUNIO DE 2026
    Referencia: EX-2025-04386276-GDESDE-DEPSE#MOP - CONT DIR 37/2025 -
    LINEAS ELECTRICAS S.A. MT HOSP SUMAMPA.
    VISTO: ... CONSIDERANDO: ... EL SEÑOR GOBERNADOR DE LA PROVINCIA
    DECRETA: ARTICULO 1º.- ... ARTÍCULO 2º.- ...
    Sr. Elías Miguel Suárez
    Dr. Víctor Rodolfo Araujo

RE_HEADER_NORMA reconoce el encabezado "TIPO-AAAA-NNNN-E-GDESDE-SIGLA"
(sólo DECRETO confirmado real; LEY/RESOLUCION/DISPOSICION incluidos por
si acaso, sin confirmar — ver arriba). RE_FECHA_SANCION lee la fecha de
firma de la línea "SANTIAGO DEL ESTERO, {día} {fecha}" (siempre esa
ciudad, es la sede del Poder Ejecutivo — se usa como ancla fija del
patrón). RE_REFERENCIA lee la línea "Referencia:" hasta "VISTO:".

El bloque de firma NO trae el cargo de cada firmante (a diferencia de
Santa Cruz/San Luis, donde había que separar "titular" de "dependencia"):
acá son solo nombres propios ("Sr. Elías Miguel Suárez", "Dr. Víctor
Rodolfo Araujo") sin cargo impreso. Los 10 decretos de la muestra usan
siempre la fórmula "EL SEÑOR GOBERNADOR DE LA PROVINCIA ... DECRETA" en el
cuerpo, así que el emisor de un DECRETO se fija directo en "PODER EJECUTIVO
DE LA PROVINCIA DE SANTIAGO DEL ESTERO" sin necesidad de mapear nombre ->
cargo (mucho más simple que San Luis/Santa Cruz).

LIMPIEZA DE TEXTO DEL PDF — 3 ARTEFACTOS REALES, VER _limpiar_texto_pdf
-------------------------------------------------------------------------------
1. "(cid:47)": el glyph usado para el signo "°" (grado, como en "N° 23.139"
   o "ARTICULO 1°") no tiene mapeo Unicode en la fuente en ALGUNAS
   instancias (inconsistente incluso dentro del mismo documento: a veces
   "1º.-" sale perfecto, a veces "1(cid:47):" sale roto) — se reemplaza
   literal por "°".

2. Palabras en negrita/énfasis con tracking ancho (mismo fenómeno que los
   títulos de sección, pero aplicado a palabras sueltas dentro del cuerpo):
   confirmado real en "D E C R E T A:" (la palabra operativa de cada
   decreto, siempre en negrita) y, de forma más irregular, en algunos
   nombres propios en negrita dentro de "Referencia:" (real: "N UE V O
   D E S A R R O L L O" en vez de "NUEVO DESARROLLO", con mezcla de
   fragmentos de 1 y 2 caracteres). _limpiar_texto_pdf sólo resuelve el
   caso seguro y consistente (corridas de 4+ "palabras" de 1 sola letra
   mayúscula consecutiva, como en "D E C R E T A:") uniéndolas sin
   espacio — cubre el 100% de las 10 apariciones de "DECRETA:" en la
   muestra. El caso mezclado (1 y 2 caracteres, como en "NUEVO
   DESARROLLO") NO se intenta arreglar: no hay forma confiable de saber
   dónde estaba el espacio real de palabra vs. el espacio de tracking sólo
   mirando el ancho del hueco a nivel de "palabras" ya agrupadas por
   pdfplumber — habría que bajar a nivel de carácter con un umbral
   adaptativo, que no se justificó para lo que es, en la práctica, un
   defecto cosmético dentro de nombres propios de terceros en la línea
   "Referencia:" (queda igual de identificable el resto del texto). Mismo
   criterio de "no perseguir cada artefacto tipográfico" que ya se aplicó
   con los PDF de Ley en Santa Fe.

3. Números de expediente partidos en dos líneas por el salto de columna,
   que al unirse con espacio quedan con un guión sobrante ("EX-2025-
   04386276 -GDESDE-DEPSE#MOP" o "EX-2026-00565461- -GDESDE-CG#MS" en vez
   de "...04386276-GDESDE-..."): normalizado con una regex dirigida sólo a
   esa forma puntual (dígito + espacio/guión sueltos + "GDESDE"), no un
   reemplazo genérico de "espacio-guión" (eso sí rompería texto real, como
   "archívese. -" al final de un artículo, o un guión usado como raya en
   prosa corrida).

ALCANCE Y CLASIFICACIÓN
-------------------------------------------------------------------------------
Se reusa tal cual PATRONES_INDIVIDUAL / PATRONES_GENERAL / clasificar_norma
del resto de la familia (mismo idioma administrativo argentino), incluida
la restricción de Promuévese/Promuévanse ya corregida en bot_santafe.py
(no se vio ningún caso de "promover" genérico en la muestra de Santiago
del Estero, pero se parte ya con el patrón corregido en vez del original
más laxo). Se sumaron 2 patrones GENERAL propios de este boletín
("Homologar/Homologase/Homologuese" y "Adjudicar/Adjudicase", -2 cada uno)
porque son el verbo operativo de 9 de los 10 decretos reales de la muestra
y sin ellos esos decretos quedaban en 0 (ni individual ni con motivo
general claro) — no cambia si se envían (igual daban "general" por
default al no alcanzar UMBRAL_INDIVIDUAL), pero deja motivos más
explicables en --todas/debug. Ninguno de los 10 decretos de la muestra
dispara clasificación individual (son todos de tipo contractual/
administrativo: adjudicaciones de obra pública, homologación de
resoluciones de Jefatura de Gabinete) — no hay en la muestra ningún caso
real de designación/renuncia/sumario para confirmar que los patrones de
PATRONES_INDIVIDUAL efectivamente enganchan con la fraseología local;
queda pendiente de validar contra un Decreto de personal real.

CLAVE DE verificar_boletin_procesado / registrar_boletin_procesado
-------------------------------------------------------------------------------
Por fecha de EDICIÓN (la de la tapa, ej. "2026-07-31"), igual que Santa Fe
— NO por fecha de sanción del decreto (esa puede ser semanas anterior, ver
arriba) y no por número de edición (no hay uno navegable). Como el link
fijo siempre muestra "lo último publicado" sin forma de pedir una fecha
puntual, no tiene sentido un flag --fecha/--bo acá: el bot simplemente
procesa lo que haya HOY en boletindeldia.pdf. Si ya se procesó esa fecha
(edición repetida porque no hubo Boletín nuevo, ej. fin de semana), el
mismo mecanismo estándar de verificar_boletin_procesado lo detecta y no
reenvía nada.

QUÉ FALTA VALIDAR
-------------------------------------------------------------------------------
- Formato real de un encabezado LEY-/RESOLUCION-/DISPOSICION- publicado
  directo en la Sección Administrativa (sin ejemplos en la muestra).
- Fraseología real de un Decreto de personal (designación/renuncia/sumario)
  contra PATRONES_INDIVIDUAL.
- Estabilidad de COL_LIMITE_1/COL_LIMITE_2 en ediciones con más o menos
  columnas de texto por página (debería ser estable, es maqueta fija, pero
  sólo se vio 1 edición real).
- Qué pasa si algún día SECCION ADMINISTRATIVA no es la primera sección del
  documento (el código ya lo tolera — ver _rango_seccion_administrativa —
  pero no hay ejemplo real que lo ejercite).
===============================================================================
"""

import io
import os
import re
import sys
import json
import time
import argparse
import unicodedata

import requests

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


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

# HTTP puro a propósito -- el sitio no acepta https (ver docstring).
SITIO = 'http://www.boletinsde.gov.ar'
URL_PDF = f'{SITIO}/boletin/boletindeldia.pdf'

HEADERS_WEB = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'application/pdf,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
}

REINTENTOS = 3
ESPERA_REINTENTO = 3
MAX_PAGINAS_DOC = 60        # salvaguarda: tope de páginas a barrer buscando títulos
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700

# Límites de columna (x, en puntos) confirmados reales -- ver docstring
# "DISEÑO DE 3 COLUMNAS". Página A4 = 596pt de ancho.
COL_LIMITE_1 = 213
COL_LIMITE_2 = 385
# Pie de página: cada página lleva su propio número centrado en la columna
# 1 (x0=296.6, ¡adentro del rango de columna de texto!) entre top 777 y
# 786 según la página (A4 = 842pt de alto) -- confirmado real en las 5
# páginas 2 a 6. Sin este corte, ese número se cuela como una palabra
# suelta en medio del texto de la columna (visto real: "...AL HOSPITAL 2
# ZONAL SUMAMPA..." con el "2" de pie de página de la página 2 intercalado
# en pleno Artículo 1º). El máximo top real de contenido de cuerpo visto
# en la muestra es 767.8 -- 775 deja margen sin arriesgar cortar cuerpo.
TOPE_PIE_PAGINA = 775


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


MESES = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SETIEMBRE': 9, 'SEPTIEMBRE': 9, 'OCTUBRE': 10,
    'NOVIEMBRE': 11, 'DICIEMBRE': 12,
}


# ===========================================================================
# DESCARGA
# ===========================================================================
_SESION = None


def sesion():
    global _SESION
    if _SESION is None:
        _SESION = requests.Session()
        _SESION.headers.update(HEADERS_WEB)
    return _SESION


def descargar_bytes(url, timeout=60):
    """GET binario (PDF). None si 404/4xx o si fallan todos los reintentos."""
    for intento in range(1, REINTENTOS + 1):
        try:
            r = sesion().get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            if r.status_code == 200:
                return r.content
            if r.status_code < 500:
                return None
        except requests.RequestException as e:
            if intento == REINTENTOS:
                print(f"Aviso: error de red pidiendo {url}: {e}", file=sys.stderr)
                return None
        time.sleep(ESPERA_REINTENTO * intento)
    return None


# ===========================================================================
# TAPA: FECHA DE LA EDICIÓN
# ===========================================================================
RE_FECHA_PORTADA = re.compile(
    r'\b[A-ZÁÉÍÓÚÑa-záéíóúñ]+\s+(\d{1,2})\s+de\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+)\s+de\s+(\d{4})\b')


def _fecha_edicion_portada(pdf):
    """Fecha ISO leída de la tapa (página 1, aparece 2 veces en el masthead
    y en el bloque de datos -- ver docstring): '...Viernes 31 de Julio de
    2026...' -> '2026-07-31'. None si no matchea (tapa con formato
    inesperado)."""
    if not pdf.pages:
        return None
    texto = pdf.pages[0].extract_text() or ''
    for m in RE_FECHA_PORTADA.finditer(texto):
        dia, mes_txt, anio = m.group(1), m.group(2), m.group(3)
        mes = MESES.get(_sin_acentos(mes_txt).upper())
        if mes:
            return f'{anio}-{mes:02d}-{int(dia):02d}'
    return None


# ===========================================================================
# TÍTULOS DE SECCIÓN Y RANGO DE LA SECCIÓN ADMINISTRATIVA
# ===========================================================================
def _es_letra_mayus_suelta(w):
    t = w['text']
    return len(t) == 1 and t.isalpha() and t.isupper()


def _titulos_seccion(pdf, tope_paginas=MAX_PAGINAS_DOC):
    """[(pageidx, top, titulo), ...] de cada corrida de 7+ "palabras" de 1
    letra mayúscula consecutiva (mismo top, tolerancia 3pt) cuyo texto
    (concatenado sin espacios) empiece con SECCION/SECCIÓN -- ver docstring
    "FUENTE DE TÍTULOS DE SECCIÓN"."""
    marcadores = []
    for pageidx, page in enumerate(pdf.pages[:tope_paginas]):
        palabras = page.extract_words()
        i, n = 0, len(palabras)
        while i < n:
            if _es_letra_mayus_suelta(palabras[i]):
                top0 = palabras[i]['top']
                letras = []
                j = i
                while j < n and _es_letra_mayus_suelta(palabras[j]) \
                        and abs(palabras[j]['top'] - top0) < 3:
                    letras.append(palabras[j]['text'])
                    j += 1
                titulo = ''.join(letras)
                if len(titulo) >= 7 and _sin_acentos(titulo).upper().startswith('SECCION'):
                    marcadores.append((pageidx, top0, titulo))
                i = j
            else:
                i += 1
    return marcadores


def _rango_seccion_administrativa(titulos):
    """(pageidx_ini, top_ini, pageidx_fin, top_fin) desde el primer título
    que contenga ADMINISTRATIVA hasta el próximo título SECCION (el que
    sea). pageidx_fin/top_fin quedan en None si es la última sección del
    documento (llega hasta el final del PDF). None si no se encontró
    ningún título ADMINISTRATIVA."""
    idx_inicio = None
    for i, (_, __, titulo) in enumerate(titulos):
        if 'ADMINISTRATIVA' in _sin_acentos(titulo).upper():
            idx_inicio = i
            break
    if idx_inicio is None:
        return None
    pageidx_ini, top_ini, _ = titulos[idx_inicio]
    if idx_inicio + 1 < len(titulos):
        pageidx_fin, top_fin, _ = titulos[idx_inicio + 1]
    else:
        pageidx_fin, top_fin = None, None
    return (pageidx_ini, top_ini, pageidx_fin, top_fin)


# ===========================================================================
# EXTRACCIÓN DE TEXTO POR COLUMNAS
# ===========================================================================
def _columna_de(x0):
    if x0 < COL_LIMITE_1:
        return 0
    if x0 < COL_LIMITE_2:
        return 1
    return 2


def _extraer_texto_columnas(pdf, pageidx_ini, top_ini, pageidx_fin, top_fin):
    """Texto de [pageidx_ini/top_ini, pageidx_fin/top_fin) respetando las 3
    columnas -- ver docstring "DISEÑO DE 3 COLUMNAS". pageidx_fin=None
    significa "hasta el final del PDF"."""
    fin_absoluto = (pageidx_fin + 1) if pageidx_fin is not None else len(pdf.pages)
    partes = []
    for pageidx in range(pageidx_ini, fin_absoluto):
        page = pdf.pages[pageidx]
        palabras = page.extract_words()
        # En la 1ra página saltar el propio título de sección + subtítulo de
        # rubro (margen de 30pt, ver docstring); en las siguientes, sólo el
        # encabezado corrido "Boletin Oficial N°... " de cada página (visto
        # real entre top 31.7 y 40.9 según la página).
        top_desde = (top_ini + 30) if pageidx == pageidx_ini else 45
        top_hasta_pagina = top_fin - 1 if (pageidx == pageidx_fin and top_fin is not None) \
            else TOPE_PIE_PAGINA
        cuerpo = [w for w in palabras if top_desde < w['top'] < top_hasta_pagina]
        cols = [[], [], []]
        for w in cuerpo:
            cols[_columna_de(w['x0'])].append(w)
        for c in cols:
            c.sort(key=lambda w: (round(w['top']), w['x0']))
            if c:
                partes.append(' '.join(w['text'] for w in c))
    return '\n'.join(partes)


# ===========================================================================
# LIMPIEZA DEL TEXTO EXTRAÍDO -- ver docstring "LIMPIEZA DE TEXTO DEL PDF"
# ===========================================================================
RE_CID47 = re.compile(r'\(cid:47\)')
# Guión doble PEGADO (sin espacio de por medio), confirmado real en
# producción (corrida real del usuario, no vista en la muestra propia):
# "...en el expediente EX-2026-01084183--GDESDE-ME..." -- distinto del
# caso "- -" con espacio (ver RE_GUION_DOBLE, más abajo, que sigue
# haciendo falta para ESE otro caso). Un "--" pegado no tiene uso
# legítimo en prosa española, así que se colapsa sin condición.
RE_GUION_PEGADO = re.compile(r'--+')
# Corridas de 1 sola "palabra"-letra consecutiva (mismo top, ver
# _titulos_seccion) por tracking ancho de la fuente en negrita/énfasis --
# confirmado real tanto en MAYÚSCULAS puras ("D E C R E T A:") como en
# palabras con mayúscula inicial y resto minúscula ("R e f e r e n c i a :",
# la propia etiqueta "Referencia:" en algunos decretos) -- ver docstring
# "LIMPIEZA DE TEXTO DEL PDF", punto 2.
RE_LETRAS_SUELTAS = re.compile(
    r'\b(?:[A-Za-zÁÉÍÓÚÑáéíóúñ]\s){3,}[A-Za-zÁÉÍÓÚÑáéíóúñ]:?\b')
# 3 formas reales del mismo artefacto de salto de columna/línea en medio de
# un código alfanumérico (expediente/resolución) -- ver docstring punto 3:
#   "- -"        (guión-espacio-guión sobrante, p.ej. "00565461- -GDESDE")
#   "\d + -LETRA" (falta el guión pegado al número, p.ej. "2726 -E-GDESDE")
#   "-LETRA/\d + espacio + \d" (guión pegado, número separado, p.ej.
#                                "RESOL- 2026-2794")
RE_GUION_DOBLE = re.compile(r'-\s+-')
# Espacio sobrante SÓLO DE UN LADO del guión (nunca de los 2): confirmado
# real en 3 formas -- "04386276 -GDESDE" (espacio antes, pegado después),
# "01864982- GDESDE" (pegado antes, espacio después), "RESOL- 2026"
# (ídem, pegado antes / espacio después). El ancla en [0-9A-Z] (nunca
# minúscula) por los DOS lados -- incluido el lado que debe quedar
# "pegado" -- es lo que evita enganchar un guión de prosa real como
# "Adjudicación - Insumos" (ahí hay espacio A LOS DOS LADOS del guión, así
# que el lado que estas regex exigen pegado nunca lo está, y no matchean;
# probado real, ver debug de esta sesión).
RE_ESPACIO_ANTES_GUION = re.compile(r'(?<=[0-9A-Z])\s+-(?=[0-9A-Z])')
RE_ESPACIO_TRAS_GUION = re.compile(r'(?<=[0-9A-Z])-\s+(?=[0-9A-Z])')


def _limpiar_texto_pdf(texto):
    if not texto:
        return ''
    texto = _guiones(texto)  # normaliza – — ‐ ‑ − -> '-' antes de las regex de abajo
    texto = RE_CID47.sub('°', texto)
    texto = RE_GUION_PEGADO.sub('-', texto)
    texto = RE_LETRAS_SUELTAS.sub(lambda m: m.group(0).replace(' ', ''), texto)
    texto = RE_GUION_DOBLE.sub('-', texto)
    texto = RE_ESPACIO_ANTES_GUION.sub('-', texto)
    texto = RE_ESPACIO_TRAS_GUION.sub('-', texto)
    lineas = [_compacto(l) for l in texto.split('\n')]
    return '\n'.join(l for l in lineas if l)


# ===========================================================================
# DIVISIÓN EN NORMAS Y EXTRACCIÓN DE CAMPOS
# ===========================================================================
# Sólo DECRETO confirmado real -- LEY/RESOLUCION/DISPOSICION incluidos por
# si acaso, mismo patrón de encabezado GDE, sin confirmar (ver docstring).
RE_HEADER_NORMA = re.compile(
    r'\b(DECRETO|LEY|RESOLUCION|RESOLUCIÓN|DISPOSICION|DISPOSICIÓN)-(\d{4})-(\d+)-E-GDESDE-\s*([A-Z]+)',
    re.IGNORECASE)

RE_FECHA_SANCION = re.compile(
    r'SANTIAGO DEL ESTERO,\s*[A-ZÁÉÍÓÚÑa-záéíóúñ]+\s+(\d{1,2})\s+DE\s+'
    r'([A-ZÁÉÍÓÚÑa-záéíóúñ]+)\s+DE\s+(\d{4})', re.IGNORECASE)

RE_REFERENCIA = re.compile(r'Referencia\s*:\s*(.+?)\s*VISTO\s*:', re.IGNORECASE | re.DOTALL)

RE_EXPEDIENTE = re.compile(r'EX-\d{4}-\d+-GDESDE-[\w#]+', re.IGNORECASE)


def _dividir_normas(texto):
    """Bloques de texto, uno por norma, separados en el encabezado
    "TIPO-AAAA-NNNN-E-GDESDE-". Descarta cualquier fragmento inicial que no
    empiece con un encabezado reconocido (p.ej. el subtítulo de rubro
    "DECRETOS" que quedó pegado antes del primer Decreto real)."""
    partes = re.split(
        r'(?=\b(?:DECRETO|LEY|RESOLUCION|RESOLUCIÓN|DISPOSICION|DISPOSICIÓN)-\d{4}-\d+-E-GDESDE-)',
        texto, flags=re.IGNORECASE)
    return [p for p in partes if RE_HEADER_NORMA.match(p.strip())]


def _sintesis_desde_referencia(referencia):
    sin_expediente = RE_EXPEDIENTE.sub('', referencia or '')
    return _compacto(sin_expediente).strip(' -.')


def _campos_norma(bloque):
    """Campos parseados (sin efectos de red) de UN bloque de norma ya
    dividido por _dividir_normas."""
    m_header = RE_HEADER_NORMA.match(bloque.strip())
    tipo = _sin_acentos(m_header.group(1)).upper() if m_header else 'DECRETO'
    anio_gde = m_header.group(2) if m_header else ''
    numero = m_header.group(3) if m_header else ''

    m_fecha = RE_FECHA_SANCION.search(bloque)
    fecha_sancion = None
    if m_fecha:
        dia, mes_txt, anio = m_fecha.groups()
        mes = MESES.get(_sin_acentos(mes_txt).upper())
        if mes:
            fecha_sancion = f'{anio}-{mes:02d}-{int(dia):02d}'

    m_ref = RE_REFERENCIA.search(bloque)
    referencia = _compacto(m_ref.group(1)) if m_ref else ''

    return {
        'tipo': tipo,
        'numero': numero,
        'anio': anio_gde,
        'fecha_sancion': fecha_sancion,
        'referencia': referencia,
        'cuerpo': _compacto(bloque),
    }


def _armar_norma(campos, fecha_edicion, url_pdf):
    """Armado PURO (sin red) de una norma a partir de los campos ya
    parseados por _campos_norma. Separado a propósito para poder probarlo
    contra campos conocidos (fixtures reales) sin depender del PDF."""
    tipo = campos['tipo']
    numero = campos['numero'] or '?'
    anio = campos['anio'] or (campos['fecha_sancion'] or fecha_edicion or '')[:4] or '????'
    fecha = campos['fecha_sancion'] or fecha_edicion

    if tipo == 'DECRETO':
        emisor = 'PODER EJECUTIVO DE LA PROVINCIA DE SANTIAGO DEL ESTERO'
    elif tipo == 'LEY':
        emisor = 'PODER LEGISLATIVO DE LA PROVINCIA DE SANTIAGO DEL ESTERO'
    else:
        # RESOLUCION/DISPOSICION publicadas directo: sin ejemplos reales
        # todavía para saber a qué organismo atribuirlas -- ver docstring.
        emisor = 'GOBIERNO DE LA PROVINCIA DE SANTIAGO DEL ESTERO'

    sintesis = _sintesis_desde_referencia(campos['referencia']) or f'{tipo} {numero}/{anio}'

    return {
        'id': f'{tipo}-{numero}-{anio}-{fecha_edicion}',
        'seccion': 'ADMINISTRATIVA',
        'tipo': tipo,
        'numero': numero,
        'anio': anio,
        'fecha': fecha,
        'emisor': emisor,
        'sintesis': sintesis,
        'texto_completo': campos['cuerpo'],
        'url_norma': url_pdf,
    }


def procesar_pdf(pdf_bytes):
    """(fecha_edicion, normas) del PDF completo. normas=None si no se
    encontró la Sección Administrativa (distinto de [] = se encontró pero
    sin normas reconocibles adentro)."""
    if pdfplumber is None:
        raise RuntimeError('falta pdfplumber (pip install pdfplumber)')
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        fecha_edicion = _fecha_edicion_portada(pdf)
        titulos = _titulos_seccion(pdf)
        rango = _rango_seccion_administrativa(titulos)
        if rango is None:
            return fecha_edicion, None
        texto = _extraer_texto_columnas(pdf, *rango)

    texto = _limpiar_texto_pdf(texto)
    bloques = _dividir_normas(texto)
    normas = [_armar_norma(_campos_norma(b), fecha_edicion, URL_PDF) for b in bloques]
    return fecha_edicion, normas


# ===========================================================================
# CLASIFICACIÓN INDIVIDUAL / GENERAL -- heredado del resto de la familia,
# ya con el ajuste de Promuévese/Promuévanse de bot_santafe.py (ver
# docstring "ALCANCE Y CLASIFICACIÓN")
# ===========================================================================
UMBRAL_INDIVIDUAL = 3

PATRONES_INDIVIDUAL = [
    (r'\bDes[íi]gn(?:[ae]se|a|ar)\b', 4, 'designación'),
    (r'\bAc[ée]pt(?:[ae]se|a|ar)\b[\s\S]{0,80}\brenuncia\b', 4, 'renuncia'),
    (r'\brenuncia\s+presentada\s+por\b', 4, 'renuncia'),
    (r'\bPromu[ée]v(?:ese|anse)\b', 4, 'promoción de un agente (reflexivo: Promuévese/Promuévanse)'),
    (r'\bContrato\s+de\s+(?:Locaci[óo]n|Prestaci[óo]n)\s+de\s+Servicios?\b', 3, 'contrato de personal'),
    (r'\bInstr[úu]yase\s+Sumario\s+Administrativo\b', 4, 'sumario administrativo'),
    (r'\bexoneraci[óo]n\b|\bcesant[íi]a\b', 4, 'sanción expulsiva'),
    (r'\bsumario\s+administrativo\b', 2, 'sumario administrativo (mención)'),
    (r'\bRecurso\s+Jer[áa]rquico\s+interpuesto\b', 3, 'recurso de un particular'),
    (r'\bOt[oó]rg(?:[ae]se|a|ar)\b[\s\S]{0,60}\b[Bb]eneficio\b', 3, 'beneficio a una persona'),
    (r'\bAcu[eé]rd(?:ase|anse|a|an|o)\b[\s\S]{0,60}\b[Bb]eneficio\b', 3, 'beneficio a una persona (acuérdase)'),
    (r'\bretiro\s+voluntario\b|\bpase\s+a\s+situaci[óo]n\s+de\s+retiro\b', 3, 'retiro/pase a retiro'),
    (r'\bBaja\s+definitiva\b|\bJubilaci[óo]n\b', 3, 'baja / jubilación'),
    (r'\bOt[óo]rg(?:[ae]se|a|ar)\b[\s\S]{0,60}\bLicencia\b', 3, 'licencia'),
    (r'\bSANCIONAR\b[\s\S]{0,60}\bmulta\b', 3, 'sanción de multa a una persona'),
    (r'\bD\.?N\.?I\.?\s*N?\s*[º°]?\s*[\d.]{6,}', 1, 'menciona DNI de una persona'),
]

PATRONES_GENERAL = [
    (r'\bPromu[úu]lg', -5, 'promulgación de ley'),
    (r'\bCr[ée]a(?:se)?\s+el\b|\bCr[ée]ase\b', -3, 'creación normativa'),
    (r'\bDeclara(?:se)?\b[\s\S]{0,60}\bInter[ée]s\s+Provincial\b', -4, 'declaración de interés provincial'),
    (r'\bApru[ée]b[ae](?:nse)?\b[\s\S]{0,60}(?:Reglamento|Manual|Anexo|Convenio)\b', -3, 'aprobación normativa/convenio'),
    (r'\bactualizaci[óo]n\s+tarifaria\b|\bcuadro\s+tarifario\b', -3, 'actualización tarifaria general'),
    (r'\bDer[óo]ganse\b|\bDer[óo]gase\b', -3, 'derogación'),
    (r'\bHomolog(?:ase|uese|a|ar)\b', -2, 'homologación de resolución'),
    (r'\bAdjud[íi]c(?:ase|a|ar)\b', -2, 'adjudicación de contratación/obra'),
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
# BACKEND (mismo contrato que el resto de la familia de bots)
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


# ===========================================================================
# EJECUCIÓN
# ===========================================================================
def _main():
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Santiago del Estero.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se usa siempre boletindeldia.pdf')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--todas', action='store_true',
                    help='muestra también las individuales, con puntaje y motivos')
    ap.add_argument('--sin-filtro', action='store_true',
                    help='envía también las individuales')
    ap.add_argument('--volcar', action='store_true', help='imprime lo reconocido y sale')
    args = ap.parse_args()

    # ---- 1. Bajar el PDF (siempre el mismo link; no hay ediciones puntuales) ----
    print(f"PDF: {URL_PDF}", file=sys.stderr)
    pdf_bytes = descargar_bytes(URL_PDF)
    if not pdf_bytes:
        salida("warning", f"No se pudo descargar {URL_PDF} (ver stderr).")

    try:
        fecha_boletin, normas_todas = procesar_pdf(pdf_bytes)
    except RuntimeError as e:
        salida("error", str(e))

    if not fecha_boletin:
        salida("warning", "No se pudo determinar la fecha de la edición leída de la tapa "
                          "del PDF (ver stderr).")
    print(f"Edición: {fecha_boletin}", file=sys.stderr)

    if normas_todas is None:
        salida("warning", f"No se encontró la Sección Administrativa en la edición del "
                          f"{fecha_boletin} (estructura del PDF inesperada; no se envió nada).")

    print(f"Normas encontradas en Sección Administrativa del {fecha_boletin}: "
          f"{len(normas_todas)}", file=sys.stderr)

    for n in normas_todas:
        n['es_individual'], n['puntaje'], n['motivos'] = clasificar_norma(
            n['tipo'], n['sintesis'], n['texto_completo'])

    if args.volcar:
        for n in normas_todas:
            print(f"  [{n['seccion']}] {n['tipo']:10s} N° {n['numero']:>10s}/{n['anio']} "
                  f"fecha={n['fecha'] or '?':10s} emisor={n['emisor'][:50]}", file=sys.stderr)
        salida("success", f"volcado: {len(normas_todas)} normas reconocidas.")

    guardar_debug(json.dumps(normas_todas, ensure_ascii=False, indent=2, default=str),
                  'debug_santiagodelestero.json')

    if not normas_todas:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Sin novedades: el boletín del {fecha_boletin} no publicó "
                          f"normativa reconocible en la Sección Administrativa.", total=0)

    generales = [n for n in normas_todas if not n['es_individual']]
    individuales = [n for n in normas_todas if n['es_individual']]
    a_enviar = normas_todas if args.sin_filtro else generales

    print(f"Boletín {fecha_boletin} | normas: {len(normas_todas)} "
          f"(generales {len(generales)} / individuales {len(individuales)})", file=sys.stderr)

    if args.dry_run:
        for n in (normas_todas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {n['tipo']:10s} N° {n['numero']:>10s}/{n['anio']} "
                  f"{n['emisor'][:40]:40s} {n['sintesis'][:50]}", file=sys.stderr)
            if args.todas and n.get('motivos'):
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    if verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

    if not a_enviar:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Se procesó el {fecha_boletin}, pero las {len(individuales)} "
                          f"normas encontradas son actos individuales; no se envió "
                          f"ninguna.", total=0)

    # ---- Envío -----------------------------------------------------------
    payload = [{
        "id_jurisdiccion": args.id_jurisdiccion,
        "nombre_emisor": n['emisor'],
        "tipo_norma_desc": n['tipo'],
        "numero": n['numero'],
        "anio": n['anio'],
        "fecha_publicacion": n['fecha'] or fecha_boletin,
        "sintesis": construir_sintesis(n),
        "texto_completo": recortar_texto(n['texto_completo']),
        "url_norma": n['url_norma'],
    } for n in a_enviar]

    try:
        r = requests.post(URL_GUARDAR_NORMAS, json={"normas": payload},
                          headers={"Authorization": f"Bearer {API_KEY_BACKEND}",
                                   "Content-Type": "application/json"}, timeout=120)
        r.raise_for_status()
        respuesta = r.json()
    except Exception as e:
        salida("error", f"Error enviando al backend: {e}")

    registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, len(payload))
    salida("success", respuesta.get('mensaje', 'OK') or 'OK', total=len(payload))


if __name__ == '__main__':
    try:
        _main()
    except SystemExit:
        raise
    except Exception as e:
        salida("error", f"Error inesperado: {e}")