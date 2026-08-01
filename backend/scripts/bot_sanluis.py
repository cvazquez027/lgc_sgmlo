#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
 BOLETÍN OFICIAL Y JUDICIAL DE LA PROVINCIA DE SAN LUIS  —  id_jurisdiccion 20
===============================================================================

SITIO Y RECONOCIMIENTO
-------------------------------------------------------------------------------
El usuario pasó dos HTML reales: el "Ctrl+U" de la home
(https://boletinoficial.sanluis.gov.ar/) y el HTML completo de una edición
puntual (https://boletinoficial.sanluis.gov.ar/Boletins/VerBoletin/16126,
edición 16.126 del 31/07/2026). Con eso alcanzó para reconocer TODO el sitio
sin necesitar más pedidos — es HTML servido ya renderizado (sin JavaScript
de por medio para el contenido en sí), confirmado también con
mcp__workspace__web_fetch contra el sitio real.

BUENA NOTICIA GRANDE respecto a San Juan: el texto es REAL de punta a punta.
El HTML de cada edición es la exportación "para web" de InDesign (se nota en
los ids `_idContainerNNN` y las clases de párrafo `_idGenObject...`) — no hay
ninguna imagen escaneada ni falta OCR. Esto simplifica mucho el bot: no hace
falta pypdfium2/pytesseract, ni lidiar con ruido de reconocimiento óptico.
Lo que sí hay es la messiness normal de un documento armado a mano en
InDesign edición tras edición: acentos inconsistentes ("RESOLUCION" vs
"RESOLUCIÓN"), un espacio de más entre "N" y "º" en algunos títulos, un
encabezado partido en dos párrafos consecutivos en vez de uno solo, etc. —
real pero mucho más manejable que ruido de Tesseract.

ESTRUCTURA DEL HTML DE UNA EDICIÓN (confirmado real, 16.126, 3.2 MB,
19.495 elementos h1/h2/h3/p dentro de <div id="boletin-wrapper">)
-------------------------------------------------------------------------------
Es una secuencia PLANA de párrafos con estilos (no hay <section> anidada):

  <h1 class="SECCIONES-CELESTE">ADMINISTRATIVAS</h1>          <- sección
  <h2 class="MINISTERIO-AZUL">MINISTERIO DE HACIENDA...</h2>  <- emisor
  <h3 class="DECRETO-N">DECRETO Nº 7258-MHIP-2026.-</h3>      <- encabezado de norma
  <p class="Normal">San Luis, 27 de Junio de 2026</p>         <- fecha
  <p class="BICENTENARIO-SARMIENTO">"2026 - AÑO DE LA...</p>  <- eslogan, ruido
  <p class="Normal">VISTO: ...</p>
  <p class="Normal">CONSIDERANDO: ...</p>
  <p class="BOLD-CENTRADO">EL GOBERNADOR DE LA PROVINCIA</p>  <- emisor (cuando no hay h2)
  <p class="BOLD-CENTRADO">DECRETA:</p>                       <- marca resolutiva
  <p class="Normal">Art. 1º.- ...</p>                         <- articulado real
  ...
  <p class="FIRMAS">CLAUDIO JAVIER POGGI</p>                  <- firma, fin del cuerpo normativo
  (puede seguir un ANEXO con texto adicional del mismo trámite)
  <h3 class="DECRETO-N">DECRETO Nº 7259-MHIP-2026.-</h3>      <- arranca la siguiente

Todos los encabezados de norma (Decretos, Resoluciones, Acuerdos, e incluso
Licitaciones y Ordenanzas municipales) comparten la MISMA clase de párrafo
"DECRETO-N" — no hay una clase por tipo. El tipo real está en el TEXTO del
h3, no en su clase, así que _RE_TIPO_NORMA lo lee de ahí (ver más abajo).

SECCIONES (h1) confirmadas reales en la edición 16.126:
  ADMINISTRATIVAS  -> 133 DECRETO (normativa provincial real, el grueso)
  RESOLUCIONES     -> RESOLUCION/RESOLUCIÓN (normativa; SIN h2, el emisor
                       sale del propio cuerpo — ver más abajo)
  ACUERDOS         -> ACUERDO (normativa; son Acuerdos del Superior Tribunal
                       de Justicia de San Luis — STJSL en la sigla del
                       número —, equivalente a lo que otras provincias
                       llaman "Acordada"; se normaliza el tipo a ACORDADA)
  MUNICIPALIDADES  -> ORDENANZA + DECRETO (municipal — MISMO patrón real que
                       San Juan: el Boletín provincial publica, como
                       servicio, las Ordenanzas de los municipios junto con
                       el Decreto del Intendente que las promulga. Se
                       excluye del envío por el mismo motivo que en San
                       Juan — ver RUBROS_MUNICIPALES abajo, aplicado acá
                       DESDE EL PRIMER DÍA en vez de como fix posterior)
  LICITACIONES, ASAMBLEAS, COMERCIALES, JUDICIALES -> no-normativa
                       confirmada real (avisos de terceros, no actos del
                       Estado; LICITACIONES además tiene ejemplos reales de
                       encabezado partido en 2 párrafos, ver más abajo).
  LEYES no apareció en la única edición real inspeccionada — se la incluye
  igual en SECCIONES_NORMATIVA por las dudas (mismo criterio que San Juan
  con sus rubros no confirmados).

EMISOR: se arma DE FORMA MUCHO MÁS CONFIABLE que en San Juan, en dos capas:
  1) h2 (MINISTERIO-AZUL) es el nombre COMPLETO del ministerio/secretaría,
     no una sigla a decodificar. Ojo: puede haber DOS h2 consecutivos antes
     de un lote de Decretos (co-firma de dos Secretarías, confirmado real:
     "SECRETARÍA GENERAL DE LA GOBERNACIÓN" + "SECRETARÍA DE TRANSPORTE"
     antes de 4 Decretos con sigla compuesta "SGG-ST" en el número) — se
     acumulan los h2 consecutivos y se juntan con " / ".
  2) Cuando no hay h2 desde el último h1 (RESOLUCIONES y ACUERDOS no traen
     h2 nunca, confirmado real), se usa el párrafo BOLD-CENTRADO
     INMEDIATAMENTE anterior a la marca resolutiva, si no es él mismo otra
     marca — es la línea de autoidentificación del organismo ("EL SEÑOR
     DIRECTOR DE INFRAESTRUCTURA HIDRICA Y ENERGETICA", visto real antes de
     una Resolución). Para ACUERDOS del STJSL esa línea NO existe (el
     cuerpo arranca directo con la fecha en palabras, sin
     autoidentificación en BOLD-CENTRADO) — para ese caso puntual se cae a
     un diccionario SIGLAS_EMISOR chico (mismo mecanismo que San Juan) con
     la única sigla vista real: STJSL.

NÚMERO Y SIGLA: el número trae la sigla del emisor INCRUSTADA, separada por
guiones o a veces por un simple espacio (confirmado real: "7258-MHIP-2026",
pero también "65 MVC-2026.-" con espacio en vez de guion antes de la sigla).
_partir_numero_crudo separa el primer token (número puro), el último token
de 4 dígitos (año), y lo que quede en el medio (sigla, puede ser compuesta:
"SGG-ST") tokenizando por cualquier corrida de guion/espacio — no hace falta
adivinar la sigla por separado como en San Juan, así que no hay
SIGLAS_EMISOR grande acá; sólo un diccionario mínimo para los casos SIN h2
(ver arriba).

ENCABEZADO PARTIDO EN DOS PÁRRAFOS: visto real en LICITACIONES (sección
no-normativa, así que no afecta el resultado, pero el mecanismo de
detección tiene que tolerarlo igual por si pasa alguna vez en una sección
normativa): "LICITACIÓN PÚBLICA" en un <h3> y "Nº 06-S.L.A.-2026 – DEC
8276/26" en el <h3> SIGUIENTE, ambos DECRETO-N. _candidata_de_norma junta
hasta 3 <h3> DECRETO-N consecutivos hasta lograr un match de tipo+número
válido, no asume que siempre es uno solo.

SÍNTESIS: la marca resolutiva NO es siempre la misma palabra — confirmado
real: "DECRETA:" (Decretos), "RESUELVE:" (Resoluciones), "ACORDARON:"
(Acuerdos del STJSL) — las tres SIEMPRE en su propio párrafo BOLD-CENTRADO,
lo cual es mucho más confiable que buscarlas por regex en texto corrido
(como hace bot_sanjuan.py, que no tiene el lujo de una clase CSS para
esto). El articulado en sí también varía: Decretos y Resoluciones usan
"Art. 1º.-"/"Art. 2°.-" (no "ARTÍCULO" completo); los Acuerdos del STJSL NO
usan artículos sino numeración romana con paréntesis ("I) ABROGAR...",
"II) FIJAR..."). _sintesis_de_texto intenta Art./ARTÍCULO primero y el
numeral romano después, con el mismo fallback final de San Juan (texto
después de la marca) si ninguno matchea.

FECHA: dos formatos reales.
  - Normal (Decretos/Resoluciones): "San Luis, 27 de Junio de 2026",
    "San Luis, 22 de Julio del 2026.-" (con "del"), "San Luis, 24 julio
    2026." (sin "de" antes del mes) — RE_DATELINE tolera las tres.
  - Acuerdos del STJSL: fecha en PALABRAS ("a VEINTINUEVE días del mes de
    JULIO de DOS MIL VEINTISEIS") — no hay un sólo dígito. Se armó un
    diccionario chico NUMERO_PALABRA (1 a 31) reutilizado tanto para el día
    como para la unidad del año ("DOS MIL" + NUMERO_PALABRA), ver
    _fecha_desde_palabras. Si no matchea (algún giro no previsto), cae a la
    fecha de la propia edición del Boletín, igual que el resto de la
    familia de bots.

DESCUBRIMIENTO DE LA EDICIÓN — MÁS SIMPLE QUE SAN JUAN, PERO CON UNA TRAMPA
-------------------------------------------------------------------------------
La home real tiene una tarjeta "📘 Última edición" (clase `bg-gradient-
edicion`, distinta de `bg-gradient-edicionNO` para las demás) con el link
directo a /Boletins/VerBoletin/<numero>. PERO la home en sí redirige a
/Boletin/Periodo/<AAAA-M> del mes CALENDARIO ACTUAL, y confirmado real
CONTRA EL SITIO EN VIVO (01/08/2026): si todavía no se publicó ninguna
edición ese mes (t=01/08, mismo día que arranca agosto), esa página viene
VACÍA — nada de "Última edición", nada de nada. /Boletin/Periodo/2026-7
(el mes anterior) sí trae la 16.126 como última. obtener_ultima_edicion
prueba el mes actual y, si no encuentra ninguna tarjeta con link "VER",
retrocede mes a mes (hasta MAX_MESES_ATRAS) hasta encontrar una.

Números de edición: correlativos simples (16126, 16125, 16124...), NO hace
falta ancla+caminata como San Juan — el número de la home ya es la fuente
de verdad. Cada edición puede traer además un "-ANEXO" (mismo número,
sufijo, sólo descargable en PDF, sin versión "VER" en HTML) — ESTE BOT NO
LO PROCESA (queda fuera de alcance por ahora, ver "QUÉ FALTA VALIDAR");
puede haber normativa real ahí adentro que este bot no ve.

Cadencia observada real (14 ediciones, 01/07 a 31/07/2026): lunes, miércoles
y viernes — nunca fin de semana. No confirmado como regla dura.

LO QUE NO TIENE ESTE BOT (a propósito, simplifica mucho vs. San Juan):
  - Sin pypdfium2/pytesseract/pdfplumber — no hace falta, no hay PDF ni OCR.
  - Sin ancla+caminata — el número de edición sale directo de la home/mes.
  - url_norma NO es un deep-link a la norma puntual: todos los ids de
    contenedor dentro del HTML de una edición son EL MISMO
    ("_idContainer218" para las 155 normas de la 16.126 — es un único
    "cuadro de texto" de InDesign con todo el contenido fluyendo adentro),
    así que no hay ancla usable por norma. url_norma es la URL completa de
    VerBoletin — el usuario tiene que buscar la norma dentro de esa página
    (larga, pero es HTML real, Ctrl+F encuentra cualquier número al toque).

QUÉ SE VALIDÓ EN SANDBOX CONTRA DATOS REALES (esta ronda, antes de entregar)
-------------------------------------------------------------------------------
A diferencia de la primera entrega de bot_sanjuan.py (que se probó recién en
la corrida real del usuario), acá hubo tiempo de hacer una pasada de
verificación propia contra los dos HTML reales antes de entregar:
  - _procesar_boletin_html contra bocompleto_sanluis.html completo: 145/145
    encabezados <h3 class="DECRETO-N"> de las secciones normativa+municipal
    se interpretaron sin un sólo aviso de "no interpretable" (los otros 10
    h3 del documento son de LICITACIONES, no-normativa, correctamente
    ignorados antes de intentar interpretarlos).
  - Acumulación de h2 consecutivos (co-firma): confirmado real con Decreto
    6534 (sigla SGG-ST -> emisor_h2 "SECRETARÍA GENERAL DE LA GOBERNACIÓN /
    SECRETARÍA DE TRANSPORTE") y Decreto 6345 (sigla SGG-SD -> "...
    GOBERNACIÓN / SECRETARÍA DE DEPORTE"), con reseteo correcto entre
    bloques (Decreto 6539 inmediatamente después, sigla SGG sola, sin
    arrastrar el h2 del bloque anterior).
  - Emisor sin h2 (RESOLUCIONES): confirmado real, sale de la
    autoidentificación en BOLD-CENTRADO ("EL SEÑOR DIRECTOR DE
    INFRAESTRUCTURA HIDRICA Y ENERGETICA", "LA DIRECTORA DE PERSONAS
    JURÍDICAS").
  - Emisor de ACUERDOS del STJSL (sin h2 NI autoidentificación en el
    cuerpo): confirmado real, cae correctamente al diccionario
    SIGLAS_EMISOR partiendo la sigla compuesta (STJSL-SC / STJSL-SA ->
    "SUPERIOR TRIBUNAL DE JUSTICIA DE SAN LUIS").
  - Síntesis vía numeral romano I) en ACUERDOS: confirmado real (Acuerdo
    147, sin ningún "Art." en el cuerpo).
  - Fecha en palabras de ACUERDOS: confirmado real, "a VEINTINUEVE días del
    mes de JULIO de DOS MIL VEINTISEIS" -> 2026-07-29 correctamente en los
    2 Acuerdos de la edición.
  - Descubrimiento: _ediciones_de_periodo contra el HTML real de la home
    (bot_sanluis.html) reprodujo exactamente las 14 ediciones con "VER" que
    trae el período 2026-7 (mismos números, mismas fechas, mismo orden) al
    comparar contra una consulta en vivo al sitio real. Y el fallback de
    mes se confirmó en vivo: /Boletin/Periodo/2026-8 (mes actual, 01/08)
    viene vacío, /Boletin/Periodo/2026-7 no.
  - Envío al backend: se simuló _main() completo con requests.post
    interceptado — 83 normas generales, contrato de payload correcto (9
    claves esperadas, sin campos vacíos, texto_completo recortado a
    ≤20.000, síntesis a ≤700, año siempre 4 dígitos), contrato stdout/stderr
    respetado (stdout: 1 sola línea JSON válida; el resto a stderr).
  - Revisando a mano una muestra de clasificación IND/GEN se encontraron y
    corrigieron 3 huecos reales de PATRONES_INDIVIDUAL (heredados de
    bot_sanjuan.py sin adaptar a San Luis): el regex de DNI no toleraba
    "N º" con espacio (sólo "N°" pegado) y no disparaba en Decreto 7450;
    faltaba un patrón para adjudicación de vivienda a beneficiarios
    nombrados (Decretos 7449/7450, "Adjudicar UNA (01) unidad
    habitacional..."); y el patrón de contrato de personal sólo reconocía
    "Locación de Servicios" y no "Prestación de Servicio" (Decreto 7469,
    un caso grande: renovación de contrato de decenas de agentes en un
    Anexo-tabla de 13.196 párrafos). Los tres ya están en el código.

QUÉ FALTA VALIDAR TODAVÍA
-------------------------------------------------------------------------------
1. Nunca se corrió el flujo real contra el sitio en vivo (descubrimiento +
   descarga + parseo + envío encadenados con la CLI real, sin --html) — el
   descubrimiento y el parseo se validaron por separado (ver arriba), pero
   no en una única corrida real de punta a punta. Falta la primera corrida
   real del usuario, como con Salta y San Juan.
2. LEYES / DECRETO-LEY / DISPOSICIONES / DECISIONES ADMINISTRATIVAS: ningún
   ejemplo real (la única edición inspeccionada no tuvo ninguna). Mapeados
   "por las dudas" igual que en San Juan.
3. PATRONES_INDIVIDUAL/PATRONES_GENERAL: la pasada de esta ronda revisó una
   muestra (no la totalidad de las 137 normas provinciales) y corrigió 3
   huecos reales encontrados así (ver arriba) — es razonable esperar que
   aparezcan más giros propios de San Luis con el uso real, igual que pasó
   varias rondas seguidas con San Juan.
4. El Anexo de cada edición (PDF aparte, "-ANEXO") no se procesa — puede
   haber normativa real ahí que este bot no ve. No implementado.
5. Encabezado partido en más de 2 párrafos <h3> consecutivos: el máximo que
   se tolera es 3; no se vio ningún caso real de 3, sólo de 2 (y ese único
   caso real fue en una sección no-normativa, LICITACIONES).
6. Emisor de ACUERDOS del STJSL: sólo 2 siglas confirmadas (STJSL-SC,
   STJSL-SA, ambas resueltas vía el primer segmento "STJSL"). Si el
   Superior Tribunal firma alguna vez sin el prefijo STJSL, cae a
   sigla.upper() tal cual (igual que San Juan con emisores desconocidos).
===============================================================================
"""

import os
import re
import sys
import json
import time
import argparse
import unicodedata
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

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

SITIO = 'https://boletinoficial.sanluis.gov.ar'

HEADERS_WEB = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
}

REINTENTOS = 3
ESPERA_REINTENTO = 3
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700
MAX_MESES_ATRAS = 3  # cuántos meses retrocede obtener_ultima_edicion si el actual viene vacío

# Sección (h1) -> tipo_norma_desc por defecto que se manda al backend (el
# tipo REAL de cada norma sale de su propio encabezado h3, esto es el
# fallback si por algún motivo no se pudo derivar de ahí). Confirmados
# reales en la 16.126: ADMINISTRATIVAS, RESOLUCIONES, ACUERDOS,
# MUNICIPALIDADES. LEYES/DISPOSICIONES/DECISIONES ADMINISTRATIVAS no
# aparecieron — mapeadas por las dudas, igual que San Juan.
SECCIONES_NORMATIVA = {
    'ADMINISTRATIVAS': 'DECRETO',
    'RESOLUCIONES': 'RESOLUCION',
    'ACUERDOS': 'ACORDADA',
    'LEYES': 'LEY',
    'DISPOSICIONES': 'DISPOSICION',
    'DECISIONES ADMINISTRATIVAS': 'DECISION ADMINISTRATIVA',
}

# No-normativa confirmada real (avisos de terceros, no actos del Estado).
SECCIONES_NO_NORMATIVA = {'LICITACIONES', 'ASAMBLEAS', 'COMERCIALES', 'JUDICIALES'}

# Municipal — mismo motivo y mismo mecanismo que RUBROS_MUNICIPALES en
# bot_sanjuan.py (ver docstring, sección EMISOR/SECCIONES): el Boletín
# provincial publica Ordenanzas municipales y sus Decretos promulgatorios
# como servicio, pero no son normativa de la Provincia. Acá se excluye
# desde el arranque (en San Juan fue un fix posterior, pedido por el
# usuario, sobre datos reales ya en producción).
SECCIONES_MUNICIPALES = {'MUNICIPALIDADES'}

_TIPO_CRUDO_A_TIPO = {
    'LEY': 'LEY',
    'DECRETO': 'DECRETO',
    'RESOLUCION': 'RESOLUCION',
    'RESOLUCIÓN': 'RESOLUCION',
    'ACUERDO': 'ACORDADA',  # ver docstring: "Acuerdo" del STJSL == "Acordada" en el vocabulario compartido
    'ORDENANZA': 'ORDENANZA',
    'ORDENANZA MUNICIPAL': 'ORDENANZA',
    'DISPOSICION': 'DISPOSICION',
    'DISPOSICIÓN': 'DISPOSICION',
}


# ===========================================================================
# NORMALIZACIÓN (mismas utilidades que el resto de la familia de bots)
# ===========================================================================
GUIONES = {ord('–'): '-', ord('—'): '-', ord('‐'): '-', ord('‑'): '-', ord('−'): '-'}


def _guiones(texto):
    return (texto or '').translate(GUIONES)


def _sin_acentos(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def _compacto(texto):
    return re.sub(r'\s+', ' ', (texto or '')).strip()


def _texto_elemento(el):
    return _compacto(_guiones(el.get_text(' ', strip=True)))


def _clase(el):
    c = el.get('class') or ['']
    return c[0]


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


def descargar(url, timeout=45):
    """GET de texto/HTML, con reintentos. None si 404 o error definitivo."""
    for intento in range(1, REINTENTOS + 1):
        try:
            r = sesion().get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            if r.status_code == 200:
                return r.text
            if r.status_code < 500:
                return None
        except requests.RequestException as e:
            if intento == REINTENTOS:
                raise RuntimeError(f"Error de red pidiendo {url}: {e}")
        time.sleep(ESPERA_REINTENTO * intento)
    return None


# ===========================================================================
# DESCUBRIMIENTO DE LA EDICIÓN
# ===========================================================================
MESES_ABREV = {
    'ENE': 1, 'FEB': 2, 'MAR': 3, 'ABR': 4, 'MAY': 5, 'JUN': 6,
    'JUL': 7, 'AGO': 8, 'SEP': 9, 'SET': 9, 'OCT': 10, 'NOV': 11, 'DIC': 12,
}


def _mes_atras(anio, mes, cantidad):
    total = (anio * 12 + (mes - 1)) - cantidad
    return total // 12, total % 12 + 1


def _pagina_periodo(anio, mes):
    url = f'{SITIO}/Boletin/Periodo/{anio}-{mes}'
    try:
        return descargar(url)
    except RuntimeError as e:
        print(f"Aviso: falló pedido a {url}: {e}", file=sys.stderr)
        return None


def _ediciones_de_periodo(html_periodo):
    """[(numero_str, fecha_iso, url_verboletin), ...] en el mismo orden del
    HTML (confirmado real: descendente, la más nueva primero). Sólo
    ediciones con versión HTML ("VER" -> /Boletins/VerBoletin/N); los
    Anexo (sólo "Descargar", sin VER) quedan afuera a propósito."""
    if not html_periodo:
        return []
    soup = BeautifulSoup(html_periodo, 'html.parser')
    salida_lista = []
    for item in soup.select('.list-group-item'):
        a_ver = item.find('a', href=re.compile(r'/Boletins/VerBoletin/\d+'))
        if not a_ver:
            continue
        m_num = re.search(r'/Boletins/VerBoletin/(\d+)', a_ver['href'])
        numero = m_num.group(1)
        texto_fecha = _texto_elemento(item)
        m_fecha = re.search(
            r'(\d{1,2})\s+([A-Za-zñ]{3})\.?\s+(\d{4})', texto_fecha, re.IGNORECASE)
        fecha_iso = None
        if m_fecha:
            mes_num = MESES_ABREV.get(_sin_acentos(m_fecha.group(2)).upper()[:3])
            if mes_num:
                try:
                    fecha_iso = date(int(m_fecha.group(3)), mes_num,
                                      int(m_fecha.group(1))).isoformat()
                except ValueError:
                    fecha_iso = None
        url_verboletin = f"{SITIO}/Boletins/VerBoletin/{numero}"
        salida_lista.append((numero, fecha_iso, url_verboletin))
    return salida_lista


def obtener_ultima_edicion():
    """(numero, fecha_iso, url_verboletin) de la última edición, probando
    el mes calendario actual y retrocediendo mes a mes si viene vacío
    (confirmado real: el 01/08/2026 el mes actual —agosto— no tenía ni una
    edición todavía, hubo que caer a julio). None,None,None si no se
    encuentra en MAX_MESES_ATRAS intentos."""
    hoy = date.today()
    anio_pedido, mes_pedido = hoy.year, hoy.month
    anio, mes = anio_pedido, mes_pedido
    for intento in range(MAX_MESES_ATRAS + 1):
        html_periodo = _pagina_periodo(anio, mes)
        ediciones = _ediciones_de_periodo(html_periodo)
        if ediciones:
            if intento > 0:
                # ojo: anio/mes ya apuntan al mes que SÍ tuvo resultado (el
                # de esta misma iteración) -- anio_pedido/mes_pedido es el
                # mes original vacío que disparó la búsqueda hacia atrás.
                print(f"Aviso: el mes {anio_pedido}-{mes_pedido:02d} no tenía ediciones; "
                      f"se usó {anio}-{mes:02d} ({intento} mes(es) atrás).", file=sys.stderr)
            return ediciones[0]
        anio, mes = _mes_atras(anio, mes, 1)
    return None, None, None


def obtener_edicion_por_numero(numero):
    """(fecha_iso, url_verboletin) para un número de edición puntual,
    buscándolo en su propio mes de publicación — hace falta saber/adivinar
    el mes porque /Boletins/VerBoletin/<numero> no trae la fecha en la URL.
    Prueba el mes actual y los MAX_MESES_ATRAS anteriores."""
    hoy = date.today()
    anio, mes = hoy.year, hoy.month
    for _ in range(MAX_MESES_ATRAS + 1):
        html_periodo = _pagina_periodo(anio, mes)
        for num, fecha_iso, url in _ediciones_de_periodo(html_periodo):
            if num == str(numero):
                return fecha_iso, url
        anio, mes = _mes_atras(anio, mes, 1)
    # no se encontró en el listado por período -- igual se puede intentar
    # pedir la página directo, por si el listado está incompleto
    url_directo = f"{SITIO}/Boletins/VerBoletin/{numero}"
    return None, url_directo


def obtener_edicion_por_fecha(fecha_objetivo_iso):
    """(numero, fecha_iso, url_verboletin) de la edición publicada en una
    fecha puntual, buscando en el Período de ese mes. None,None,None si no
    se encuentra ninguna edición justo en esa fecha."""
    objetivo = date.fromisoformat(fecha_objetivo_iso)
    html_periodo = _pagina_periodo(objetivo.year, objetivo.month)
    for numero, fecha_iso, url in _ediciones_de_periodo(html_periodo):
        if fecha_iso == fecha_objetivo_iso:
            return numero, fecha_iso, url
    return None, None, None


# ===========================================================================
# PARSEO DEL HTML DE UNA EDICIÓN
# ===========================================================================
RE_TIPO_NORMA = re.compile(
    r'^(?P<tipo_crudo>LEY|DECRETO|RESOLUCI[OÓ]N|ACUERDO|DISPOSICI[OÓ]N|'
    r'ORDENANZA(?:\s+MUNICIPAL)?)\b', re.IGNORECASE)
RE_NUMERO_TRAS_TIPO = re.compile(r'N\s*[ºo°]\s*(?P<resto>.+)$', re.IGNORECASE | re.DOTALL)
MAX_H3_A_JUNTAR = 3


def _partir_numero_crudo(numero_crudo):
    """"7258-MHIP-2026.-" -> ('7258', 'MHIP', '2026'); "65 MVC-2026.-" ->
    ('65', 'MVC', '2026'); "6534-SGG-ST-2026.-" -> ('6534', 'SGG-ST',
    '2026'). Tokeniza por cualquier corrida de guion/espacio (el separador
    varía real entre guion y espacio) y asume: primer token = número,
    último token de 4 dígitos = año, lo del medio = sigla (puede ser
    compuesta)."""
    limpio = numero_crudo.strip(' .-–')
    tokens = [t for t in re.split(r'[\s\-–]+', limpio) if t]
    if not tokens:
        return '', '', ''
    numero = tokens[0]
    anio = ''
    resto = tokens[1:]
    if resto and re.match(r'^(19|20)\d{2}$', resto[-1]):
        anio = resto[-1]
        resto = resto[:-1]
    sigla = '-'.join(resto)
    return numero, sigla, anio


def _candidata_de_norma(elems, i):
    """Intenta armar un encabezado válido juntando desde elems[i] hasta 3
    <h3 class=DECRETO-N> consecutivos (ver docstring: encabezados partidos
    en 2 párrafos, visto real en Licitaciones). Devuelve
    (indice_ultimo_h3_consumido, tipo_crudo, numero_crudo) o (None, None,
    None) si no se pudo interpretar."""
    texto = ''
    j = i
    n = len(elems)
    for _paso in range(MAX_H3_A_JUNTAR):
        if j >= n or elems[j].name != 'h3' or _clase(elems[j]) != 'DECRETO-N':
            break
        texto = _compacto(f'{texto} {_texto_elemento(elems[j])}')
        m_tipo = RE_TIPO_NORMA.match(texto)
        if m_tipo:
            m_num = RE_NUMERO_TRAS_TIPO.search(texto[m_tipo.end():])
            if m_num:
                return j, m_tipo.group('tipo_crudo'), m_num.group('resto')
        j += 1
    return None, None, None


def _normalizar_tipo_crudo(tipo_crudo):
    t = _compacto(_sin_acentos(tipo_crudo or '')).upper()
    t_original = _compacto(tipo_crudo or '').upper()
    return _TIPO_CRUDO_A_TIPO.get(t_original) or _TIPO_CRUDO_A_TIPO.get(t, t)


RE_MARCA_RESOLUTIVA_PALABRA = re.compile(
    r'^(DECRETA|RESUELVEN?|DISPONEN?|ACORD(?:ARON|[OÓ])|SANCIONAN?)\s*:?\s*$')


def _idx_marca_resolutiva(elems_cuerpo):
    """Índice (en elems_cuerpo) del ÚLTIMO párrafo BOLD-CENTRADO que sea
    una marca resolutiva reconocida, o None. Como el cuerpo de cada norma
    ya viene cortado por <h3> reales (no por regex sobre texto corrido),
    tomar la última no arrastra el riesgo de mezclar con OTRA norma que sí
    existía en San Juan (bot_sanjuan.py) — acá los límites son exactos."""
    idx = None
    for i, el in enumerate(elems_cuerpo):
        if el.name == 'p' and _clase(el) == 'BOLD-CENTRADO':
            if RE_MARCA_RESOLUTIVA_PALABRA.match(_texto_elemento(el).upper()):
                idx = i
    return idx


def _emisor_desde_cuerpo(elems_cuerpo, idx_marca):
    """El párrafo BOLD-CENTRADO INMEDIATAMENTE antes de la marca resolutiva
    suele ser la autoidentificación del organismo ("EL GOBERNADOR DE LA
    PROVINCIA", "EL SEÑOR DIRECTOR DE..."), confirmado real en Decretos y
    Resoluciones. Los Acuerdos del STJSL no tienen esta línea (arrancan
    directo con la fecha en palabras) — devuelve '' en ese caso, y
    _resolver_emisor cae al diccionario SIGLAS_EMISOR por la sigla."""
    if not idx_marca:
        return ''
    el = elems_cuerpo[idx_marca - 1]
    if el.name == 'p' and _clase(el) == 'BOLD-CENTRADO':
        t = _texto_elemento(el)
        if t and not RE_MARCA_RESOLUTIVA_PALABRA.match(t.upper()):
            return t
    return ''


RE_DATELINE = re.compile(
    r'San\s+Luis,?\s*(?P<dia>\d{1,2})\s*(?:de\s+)?(?P<mes>[A-Za-zÁÉÍÓÚñáéíóú]{3,12})'
    r'\s*(?:de|del)?\s*(?P<anio>(?:19|20)\d{2})', re.IGNORECASE)
MESES_COMPLETOS = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SETIEMBRE': 9, 'SEPTIEMBRE': 9, 'OCTUBRE': 10,
    'NOVIEMBRE': 11, 'DICIEMBRE': 12,
}

# Sólo para Acuerdos del STJSL: fecha en palabras ("a VEINTINUEVE días del
# mes de JULIO de DOS MIL VEINTISEIS"). 1-31, reutilizado también para la
# unidad del año ("DOS MIL" + NUMERO_PALABRA -> 2000+n).
NUMERO_PALABRA = {
    'UNO': 1, 'DOS': 2, 'TRES': 3, 'CUATRO': 4, 'CINCO': 5, 'SEIS': 6,
    'SIETE': 7, 'OCHO': 8, 'NUEVE': 9, 'DIEZ': 10, 'ONCE': 11, 'DOCE': 12,
    'TRECE': 13, 'CATORCE': 14, 'QUINCE': 15, 'DIECISEIS': 16,
    'DIECISIETE': 17, 'DIECIOCHO': 18, 'DIECINUEVE': 19, 'VEINTE': 20,
    'VEINTIUNO': 21, 'VEINTIUN': 21, 'VEINTIDOS': 22, 'VEINTITRES': 23,
    'VEINTICUATRO': 24, 'VEINTICINCO': 25, 'VEINTISEIS': 26,
    'VEINTISIETE': 27, 'VEINTIOCHO': 28, 'VEINTINUEVE': 29, 'TREINTA': 30,
}
RE_FECHA_PALABRAS = re.compile(
    r'\bA\s+(?P<dia>[A-Z]+(?:\s+Y\s+[A-Z]+)?)\s+D[IÍ]AS\s+DEL\s+MES\s+DE\s+'
    r'(?P<mes>[A-Z]+)\s+DE\s+(?P<anio>DOS\s+MIL(?:\s+[A-Z]+(?:\s+Y\s+[A-Z]+)?)?)\b')


def _numero_desde_palabras(texto_palabras):
    t = _sin_acentos(texto_palabras.strip()).upper()
    if t == 'TREINTA Y UNO':
        return 31
    return NUMERO_PALABRA.get(t.replace(' ', ''))


def _fecha_desde_palabras(texto):
    m = RE_FECHA_PALABRAS.search(_sin_acentos(texto).upper())
    if not m:
        return None
    dia = _numero_desde_palabras(m.group('dia'))
    mes = MESES_COMPLETOS.get(m.group('mes'))
    anio_txt = m.group('anio').replace('DOS MIL', '').strip()
    anio = 2000 + (_numero_desde_palabras(anio_txt) if anio_txt else 0)
    if not (dia and mes):
        return None
    try:
        return date(anio, mes, dia).isoformat()
    except ValueError:
        return None


def _fecha_desde_dateline(texto):
    m = RE_DATELINE.search(texto)
    if not m:
        return None
    mes_num = MESES_COMPLETOS.get(_sin_acentos(m.group('mes')).upper())
    if not mes_num:
        return None
    try:
        return date(int(m.group('anio')), mes_num, int(m.group('dia'))).isoformat()
    except ValueError:
        return None


def _procesar_boletin_html(html_boletin):
    """[{tipo, seccion, numero, sigla, anio, fecha, emisor, texto_completo}, ...]
    Recorre <div id="boletin-wrapper"> en orden de documento; h1 marca
    sección, h2 acumula emisor (junta consecutivos), h3.DECRETO-N es
    candidata de norma (ver _candidata_de_norma)."""
    soup = BeautifulSoup(html_boletin, 'html.parser')
    wrapper = soup.find(id='boletin-wrapper')
    if wrapper is None:
        raise RuntimeError(
            "No se encontró <div id=\"boletin-wrapper\"> en la página — "
            "¿cambió la plantilla del sitio?")
    elems = wrapper.find_all(['h1', 'h2', 'h3', 'p'], recursive=True)

    normas = []
    secciones_desconocidas = {}
    sin_formato_por_seccion = {}
    seccion = None
    emisor_h2 = []
    viene_de_h2 = False

    i, n = 0, len(elems)
    while i < n:
        el = elems[i]
        if el.name == 'h1':
            seccion = _texto_elemento(el).upper()
            if (seccion not in SECCIONES_NORMATIVA and seccion not in SECCIONES_MUNICIPALES
                    and seccion not in SECCIONES_NO_NORMATIVA):
                secciones_desconocidas[seccion] = secciones_desconocidas.get(seccion, 0) + 1
            emisor_h2 = []
            viene_de_h2 = False
            i += 1
            continue
        if el.name == 'h2':
            texto_h2 = _texto_elemento(el)
            if viene_de_h2:
                emisor_h2.append(texto_h2)
            else:
                emisor_h2 = [texto_h2]
            viene_de_h2 = True
            i += 1
            continue
        if el.name == 'h3' and _clase(el) == 'DECRETO-N':
            viene_de_h2 = False
            if seccion not in SECCIONES_NORMATIVA and seccion not in SECCIONES_MUNICIPALES:
                i += 1
                continue
            j, tipo_crudo, numero_crudo = _candidata_de_norma(elems, i)
            if j is None:
                clave = seccion or '(sin sección)'
                sin_formato_por_seccion[clave] = sin_formato_por_seccion.get(clave, 0) + 1
                print(f"Aviso: encabezado no interpretable en sección {seccion}: "
                      f"{_texto_elemento(el)[:80]!r}", file=sys.stderr)
                i += 1
                continue
            # cuerpo: desde el elemento siguiente al último <h3> del
            # encabezado hasta el próximo h1/h2/h3.DECRETO-N
            k = j + 1
            cuerpo = []
            while k < n:
                ek = elems[k]
                if ek.name in ('h1', 'h2'):
                    break
                if ek.name == 'h3' and _clase(ek) == 'DECRETO-N':
                    break
                cuerpo.append(ek)
                k += 1

            numero, sigla, anio_numero = _partir_numero_crudo(numero_crudo)
            idx_marca = _idx_marca_resolutiva(cuerpo)
            emisor_cuerpo = _emisor_desde_cuerpo(cuerpo, idx_marca)
            texto_cuerpo_plano = '\n'.join(_texto_elemento(e) for e in cuerpo)

            fecha_iso = (_fecha_desde_dateline(texto_cuerpo_plano)
                         or _fecha_desde_palabras(texto_cuerpo_plano))

            normas.append({
                'tipo': _normalizar_tipo_crudo(tipo_crudo),
                'seccion': seccion,
                'numero': numero,
                'sigla': sigla.upper(),
                'anio': (fecha_iso or '')[:4] or anio_numero or '????',
                'fecha': fecha_iso,
                'emisor_h2': ' / '.join(emisor_h2),
                'emisor_cuerpo': emisor_cuerpo,
                'texto_completo': texto_cuerpo_plano,
                'idx_marca': idx_marca,
                'cuerpo_tras_marca': ('\n'.join(_texto_elemento(e) for e in cuerpo[idx_marca + 1:])
                                      if idx_marca is not None else ''),
            })
            i = k
            continue
        i += 1

    return normas, sin_formato_por_seccion, secciones_desconocidas


# ===========================================================================
# SÍNTESIS
# ===========================================================================
# "Art. 1º.-"/"Art. 2°.-" (Decretos/Resoluciones) — NO "ARTÍCULO" completo,
# a diferencia de San Juan; se tolera igual por si alguna sección lo usa
# entero. El numeral romano "I)"/"II)" es el formato real de los Acuerdos
# del STJSL (no tienen "Art."), se intenta como segunda opción.
RE_ARTICULO1 = re.compile(
    r'(?:ART[ÍI]?CULO|Art)\.?\s*(?:N[º°]\s*)?1(?!\d)\s*[ºo°]{0,2}\s*[.\-:)]+\s*'
    r'(?P<texto>[\s\S]{0,1200}?)'
    r'(?=(?:ART[ÍI]?CULO|Art)\.?\s*(?:N[º°]\s*)?2(?!\d)|\Z)', re.IGNORECASE)
RE_ROMANO_I = re.compile(
    r'^\s*I\)\s*(?P<texto>[\s\S]{0,1200}?)(?=^\s*II\)|\Z)', re.IGNORECASE | re.MULTILINE)


def _sintesis_de_texto(norma):
    resto = norma.get('cuerpo_tras_marca') or ''
    if not resto:
        return _compacto(norma.get('texto_completo') or '')[:400]
    m = RE_ARTICULO1.search(resto)
    if m:
        return _compacto(m.group('texto'))
    m = RE_ROMANO_I.search(resto)
    if m:
        return _compacto(m.group('texto'))
    return _compacto(resto[:500])


# ===========================================================================
# EMISOR
# ===========================================================================
# Best-effort, chico a propósito: la mayoría de los emisores salen directo
# del h2 (nombre completo, sin adivinar) o de la autoidentificación en el
# cuerpo (ver _emisor_desde_cuerpo). Sólo hace falta este diccionario para
# el único caso real sin ninguna de las dos cosas: los Acuerdos del STJSL.
SIGLAS_EMISOR = {
    'STJSL': 'SUPERIOR TRIBUNAL DE JUSTICIA DE SAN LUIS',
}
_SIGLAS_EMISOR_UPPER = {k.upper(): v for k, v in SIGLAS_EMISOR.items()}

# La línea de autoidentificación que arma _emisor_desde_cuerpo nombra a
# veces al FUNCIONARIO a cargo ("El señor Director de X", "La Directora de
# Y") en vez de a la DEPENDENCIA — confirmado real en las 2 Resoluciones de
# la 16.126 (Nº 28: "EL SEÑOR DIRECTOR DE INFRAESTRUCTURA HIDRICA Y
# ENERGETICA"; Nº 418: "LA DIRECTORA DE PERSONAS JURÍDICAS"). Como nombre
# de emisor es más prolijo y consistente con los que vienen del h2 (nombres
# de dependencia, sin artículo ni honorífico) usar "Dirección de X". Sólo
# se tocan roles de nivel sub-ministerial con un equivalente de oficina
# obvio; "Gobernador"/"Ministro" quedan igual porque esa SÍ es la forma
# habitual de identificar al emisor de un Decreto/Ministerio en los
# boletines argentinos (y a los Decretos ni les llega esta función, porque
# siempre traen h2).
ROL_CUERPO_A_OFICINA = {
    'DIRECTOR': 'DIRECCIÓN', 'DIRECTORA': 'DIRECCIÓN',
    'SUBDIRECTOR': 'SUBDIRECCIÓN', 'SUBDIRECTORA': 'SUBDIRECCIÓN',
    'SECRETARIO': 'SECRETARÍA', 'SECRETARIA': 'SECRETARÍA',
    'SUBSECRETARIO': 'SUBSECRETARÍA', 'SUBSECRETARIA': 'SUBSECRETARÍA',
    'COORDINADOR': 'COORDINACIÓN', 'COORDINADORA': 'COORDINACIÓN',
    'ADMINISTRADOR': 'ADMINISTRACIÓN', 'ADMINISTRADORA': 'ADMINISTRACIÓN',
    'JEFE': 'JEFATURA', 'JEFA': 'JEFATURA',
    'INTERVENTOR': 'INTERVENCIÓN', 'INTERVENTORA': 'INTERVENCIÓN',
    'PRESIDENTE': 'PRESIDENCIA', 'PRESIDENTA': 'PRESIDENCIA',
}
RE_EMISOR_CUERPO_ROL = re.compile(
    r'^(?:EL|LA)\s+(?:(?:SE[ÑN]ORA?|SRA?\.)\s+)?'
    r'(?P<rol>' + '|'.join(ROL_CUERPO_A_OFICINA) + r')\s+(?P<resto>DE\b.*)$',
    re.IGNORECASE)


def _limpiar_titular_emisor(texto):
    t = _compacto(texto or '')
    m = RE_EMISOR_CUERPO_ROL.match(t)
    if not m:
        return t
    oficina = ROL_CUERPO_A_OFICINA[m.group('rol').upper()]
    return _compacto(f"{oficina} {m.group('resto')}")


def _resolver_emisor(norma):
    if norma.get('emisor_h2'):
        return norma['emisor_h2']
    if norma.get('emisor_cuerpo'):
        return _limpiar_titular_emisor(norma['emisor_cuerpo'])
    sigla = (norma.get('sigla') or '').upper()
    if sigla:
        # sigla compuesta ("STJSL-SC") -- probar la sigla entera y, si no
        # está, el primer segmento (STJSL) antes del primer guion
        if sigla in _SIGLAS_EMISOR_UPPER:
            return _SIGLAS_EMISOR_UPPER[sigla]
        primer_segmento = sigla.split('-')[0]
        if primer_segmento in _SIGLAS_EMISOR_UPPER:
            return _SIGLAS_EMISOR_UPPER[primer_segmento]
        return sigla
    return 'PODER EJECUTIVO'


# ===========================================================================
# CLASIFICACIÓN INDIVIDUAL / GENERAL
# ===========================================================================
# Mismo set base que el resto de la familia (San Juan/Salta) — mismo idioma
# administrativo argentino. Revisado a mano contra una muestra de la
# edición real 16.126 (ver "QUÉ SE VALIDÓ..." en el docstring principal);
# de ahí salieron 3 ajustes (DNI con espacio antes de °, adjudicación de
# vivienda, contrato de "prestación" además de "locación" de servicios).
# No se revisó la totalidad de las 137 normas provinciales de esa edición,
# así que es esperable que aparezcan más giros con el uso real.
UMBRAL_INDIVIDUAL = 3

PATRONES_INDIVIDUAL = [
    (r'\bDes[íi]gn(?:[ae]se|a|ar)\b', 4, 'designación'),
    (r'\bAc[ée]pt(?:[ae]se|a|ar)\b[\s\S]{0,80}\brenuncia\b', 4, 'renuncia'),
    (r'\brenuncia\s+presentada\s+por\b', 4, 'renuncia'),
    (r'\b(?:Promu[ée]v[ae](?:se)?|Promover)\b', 4, 'promoción de un agente'),
    (r'\bContrato\s+de\s+(?:Locaci[óo]n|Prestaci[óo]n)\s+de\s+Servicios?\b', 3, 'contrato de personal'),
    (r'\bInstr[úu]yase\s+Sumario\s+Administrativo\b', 4, 'sumario administrativo'),
    (r'\bexoneraci[óo]n\b|\bcesant[íi]a\b', 4, 'sanción expulsiva'),
    (r'\bRecurso\s+Jer[áa]rquico\s+interpuesto\b', 3, 'recurso de un particular'),
    (r'\bOt[oó]rg(?:[ae]se|a|ar)\b[\s\S]{0,60}\b[Bb]eneficio\b', 3, 'beneficio a una persona'),
    (r'\bAcu[eé]rd(?:ase|anse|a|an|o)\b[\s\S]{0,60}\b[Bb]eneficio\b', 3, 'beneficio a una persona (acuérdase)'),
    (r'\bretiro\s+voluntario\b|\bpase\s+a\s+situaci[óo]n\s+de\s+retiro\b', 3, 'retiro/pase a retiro'),
    (r'\bBaja\s+definitiva\b|\bJubilaci[óo]n\b', 3, 'baja / jubilación'),
    (r'\bOt[óo]rg(?:[ae]se|a|ar)\b[\s\S]{0,60}\bLicencia\b', 3, 'licencia'),
    (r'\bD\.?N\.?I\.?\s*N?\s*[º°]?\s*[\d.]{6,}', 1, 'menciona DNI de una persona'),
    (r'\bAdjudic(?:a|ar|ase)\b[\s\S]{0,100}\b(?:unidad(?:es)?\s+habitacional(?:es)?|vivienda)\b',
     3, 'adjudicación de vivienda a beneficiario(s)'),
]

PATRONES_GENERAL = [
    (r'\bPromu[úu]lg', -5, 'promulgación de ley/ordenanza'),
    (r'\bCr[ée]a(?:se)?\s+el\b|\bCr[ée]ase\b', -3, 'creación normativa'),
    (r'\bDeclara(?:se)?\b[\s\S]{0,60}\bInter[ée]s\s+Provincial\b', -4, 'declaración de interés provincial'),
    (r'\bApru[ée]b[ae](?:nse)?\b[\s\S]{0,60}(?:Reglamento|Manual|Anexo|Convenio)\b', -3, 'aprobación normativa/convenio'),
    (r'\bactualizaci[óo]n\s+tarifaria\b|\bcuadro\s+tarifario\b', -3, 'actualización tarifaria general'),
    (r'\bDer[óo]ganse\b|\bDer[óo]gase\b', -3, 'derogación'),
]


def clasificar_norma(tipo, sintesis, texto_completo):
    if tipo in ('LEY', 'DECRETO LEY'):
        return False, -99, ['ley/decreto-ley: siempre general']

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
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de San Luis.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se descubre solo')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--fecha', metavar='AAAA-MM-DD',
                    help='edición publicada en esa fecha exacta (busca en el Período de ese mes)')
    ap.add_argument('--numero', type=int, metavar='N',
                    help='edición puntual por número, salta el descubrimiento')
    ap.add_argument('--html', metavar='ARCHIVO',
                    help='usa un HTML de VerBoletin ya guardado (pruebas offline)')
    ap.add_argument('--todas', action='store_true',
                    help='muestra también las individuales, con puntaje y motivos')
    ap.add_argument('--sin-filtro', action='store_true',
                    help='envía también las individuales (no afecta el filtro de '
                         'municipales, que siempre se excluyen)')
    ap.add_argument('--volcar', action='store_true', help='imprime lo reconocido y sale')
    args = ap.parse_args()

    fecha_boletin = None
    url_boletin = None

    # ---- 1. Ubicar la edición y bajar el HTML --------------------------------
    if args.html:
        with open(args.html, encoding='utf-8') as f:
            html_boletin = f.read()
        fecha_boletin = args.fecha or 'desconocida'
        print(f"Usando HTML local: {args.html}", file=sys.stderr)
    else:
        if args.numero:
            fecha_boletin, url_boletin = obtener_edicion_por_numero(args.numero)
            numero = args.numero
        elif args.fecha:
            numero, fecha_boletin, url_boletin = obtener_edicion_por_fecha(args.fecha)
        else:
            numero, fecha_boletin, url_boletin = obtener_ultima_edicion()

        if not url_boletin:
            salida("warning", "No se pudo ubicar la edición a procesar en "
                              "boletinoficial.sanluis.gov.ar (ver stderr para el detalle).")

        print(f"Boletín Oficial - {numero} ({fecha_boletin or 'fecha desconocida'}): "
              f"{url_boletin}", file=sys.stderr)
        try:
            html_boletin = descargar(url_boletin, timeout=90)
        except RuntimeError as e:
            salida("error", str(e))
        if not html_boletin:
            salida("error", f"No se pudo descargar la edición: {url_boletin}")

    # ---- 2. Parsear el HTML: normas crudas por sección -----------------------
    try:
        normas_crudas, sin_formato_por_seccion, secciones_desconocidas = _procesar_boletin_html(
            html_boletin)
    except Exception as e:
        salida("error", f"Error procesando el HTML del boletín: {e}")

    print(f"Normas reconocidas (todas las secciones): {len(normas_crudas)}", file=sys.stderr)
    if sin_formato_por_seccion:
        for seccion, cant in sin_formato_por_seccion.items():
            print(f"Aviso: {cant} encabezado(s) en la sección {seccion} no se pudieron "
                  f"interpretar como TIPO+N°+número — revisar con --volcar.", file=sys.stderr)
    if secciones_desconocidas:
        for seccion, cant in secciones_desconocidas.items():
            print(f"Aviso: sección no reconocida {seccion!r} ({cant} encabezado(s) dentro) "
                  f"— si es normativa, agregarla a SECCIONES_NORMATIVA.", file=sys.stderr)

    if args.volcar:
        for nrm in normas_crudas:
            print(f"  [{nrm['seccion']}] {nrm['tipo']:14s} N° {nrm['numero']:>10s} "
                  f"sigla={nrm['sigla']:10s} fecha={nrm['fecha'] or '?':10s} "
                  f"{nrm['texto_completo'][:70]!r}", file=sys.stderr)
        salida("success", f"volcado: {len(normas_crudas)} normas reconocidas.")

    # ---- 3. Síntesis, emisor, clasificación, filtro de jurisdicción ---------
    normas_todas = []
    for nrm in normas_crudas:
        nrm['sintesis'] = _sintesis_de_texto(nrm)
        nrm['emisor'] = _resolver_emisor(nrm)
        nrm['url_norma'] = url_boletin or (args.html or '')
        nrm['es_individual'], nrm['puntaje'], nrm['motivos'] = clasificar_norma(
            nrm['tipo'], nrm['sintesis'], nrm['texto_completo'])
        nrm['es_provincial'] = nrm['seccion'] not in SECCIONES_MUNICIPALES
        normas_todas.append(nrm)

    normas = [n for n in normas_todas if n['es_provincial']]
    normas_municipales = [n for n in normas_todas if not n['es_provincial']]
    if normas_municipales:
        detalle = '; '.join(f"{n['tipo']} N° {n['numero']} ({n['emisor']})"
                             for n in normas_municipales)
        print(f"Aviso: se excluyeron {len(normas_municipales)} norma(s) de nivel MUNICIPAL "
              f"(sección {'/'.join(sorted(SECCIONES_MUNICIPALES))}) — San Luis publica "
              f"ordenanzas municipales y sus decretos promulgatorios en el mismo Boletín, "
              f"pero id_jurisdiccion={args.id_jurisdiccion} es sólo la Provincia: {detalle}. "
              f"No se envían (quedan en debug_sanluis.json con es_provincial=false).",
              file=sys.stderr)

    generales = [n for n in normas if not n['es_individual']]
    individuales = [n for n in normas if n['es_individual']]
    a_enviar = normas if args.sin_filtro else generales

    for n in normas_todas:
        n.pop('idx_marca', None)
        n.pop('cuerpo_tras_marca', None)
    guardar_debug(json.dumps(normas_todas, ensure_ascii=False, indent=2, default=str),
                  'debug_sanluis.json')
    print(f"Boletín {fecha_boletin} | normas provinciales: {len(normas)} (generales "
          f"{len(generales)} / individuales {len(individuales)})"
          + (f" | municipales excluidas: {len(normas_municipales)}" if normas_municipales else ''),
          file=sys.stderr)

    if args.dry_run:
        for n in (normas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {n['tipo']:14s} N° {n['numero']:>10s} {n['emisor'][:40]:40s} "
                  f"{n['sintesis'][:50]}", file=sys.stderr)
            if args.todas and n.get('motivos'):
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    fecha_valida = fecha_boletin and fecha_boletin != 'desconocida'

    if fecha_valida and verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

    if not normas:
        if fecha_valida:
            registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Sin novedades: el boletín del {fecha_boletin} no publicó "
                          f"normativa provincial reconocible.", total=0)

    if not a_enviar:
        if fecha_valida:
            registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Se procesó el boletín del {fecha_boletin}, pero las "
                          f"{len(individuales)} normas encontradas son actos individuales; "
                          f"no se envió ninguna.", total=0)

    # ---- 4. Envío -------------------------------------------------------------
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

    if fecha_valida:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, len(payload))

    salida("success", respuesta.get('mensaje', 'OK') or 'OK', total=len(payload))


if __name__ == '__main__':
    try:
        _main()
    except SystemExit:
        raise
    except Exception as e:
        salida("error", f"Error inesperado: {e}")