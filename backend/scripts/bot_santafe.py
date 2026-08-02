#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
 BOLETÍN OFICIAL DE LA PROVINCIA DE SANTA FE  —  id_jurisdiccion 22
===============================================================================

SITIO Y ARQUITECTURA — SIN "NÚMERO DE EDICIÓN", TODO POR FECHA
-------------------------------------------------------------------------------
Confirmado real (HTML crudo subido por el usuario — santafe.html, portada del
31/07/2026 — y santafe_otrodia.html, resumendia.php del 27/07/2026 — más 6
ediciones adicionales leídas en vivo vía mcp__workspace__web_fetch: 22, 28,
29, 30 jul y 1 ago 2026): no existe un "número de Boletín" como en Santa Cruz
(BO NNNN). Cada edición se identifica únicamente por FECHA:

  https://www.santafe.gov.ar/boletinoficial/                         -> ÚLTIMA edición
  https://www.santafe.gov.ar/boletinoficial/resumendia.php?dia=YYYY-MM-DD -> edición puntual

La portada NO es "la de hoy" literalmente — es la ÚLTIMA publicada. Confirmado
real: pedida un domingo 2/8, devolvió la edición del viernes 31/7 (no hay
Boletín los fines de semana; el sitio simplemente sigue mostrando la última
real, con fecha propia en el <h1>). Por eso el bot SIEMPRE lee la fecha real
de la edición desde el <h1> ("Boletín Oficial del {día} {N} de {mes} de
{año}") en vez de asumir que la última edición es "hoy".

Confirmado real también el aviso de día sin edición (probado en vivo con
2026-08-01, sábado): la misma página, pero con la tabla de secciones vacía y
una fila "Este Boletín no fue publicado o no tiene publicaciones." —
_no_publicado() lo detecta por ese texto, sin necesidad de calendario de
feriados.

Como el resto de la familia de bots ya usa FECHA (no un número de edición)
como clave de verificar_boletin_procesado/registrar_boletin_procesado, la
ausencia de número de edición acá no es un problema: la fecha ISO de la
edición ES directamente el identificador que el backend espera.

ALCANCE — CONFIRMADO REAL CONTRA 8 EDICIONES DISTINTAS
-------------------------------------------------------------------------------
La página de cada edición trae, siempre, las 18 secciones (I a XVIII) aunque
estén vacías ese día. De las 18, sólo 4 traen normativa oficial con
estructura de "un ítem por norma" (encabezado propio + texto + link a su
propia ficha):

  II-  LEYES PROVINCIALES        (confirmado real: Ley 14465, ed. 27/07)
  III- DECRETOS PROVINCIALES     (confirmado real: Decretos 1501 y 1530 el
                                   27/07; 1552 y 1553 el 30/07; 1476 el 22/07)
  IV-  DECRETOS SINTETIZADOS     (**sin ejemplo real** — vacía en las 8
                                   ediciones vistas. Se incluye por analogía
                                   estructural directa con III, a pedido
                                   explícito del usuario. Si el formato real
                                   difiere, hay que ajustarlo cuando aparezca
                                   el primer caso real.)
  V-   RESOLUCIONES PROVINCIALES (**sin ejemplo real**, mismo caso que IV)

El resto (Licitaciones, Avisos Oficiales, Convocatorias, Contratos/Estatutos/
Balances/Etc, las 6 secciones de Sección Judicial, Ley 11867, Instituto
Municipal de Previsión Social de Rosario, Avisos) sí tuvieron contenido real
en varias de las 8 ediciones vistas, pero CONFIRMADO REAL que no tienen
estructura de "un ítem por norma": es un único bloque de texto por sección
que concatena avisos de decenas de organismos/particulares sin relación entre
sí, con un solo link a una página de sección completa (no por ítem). Ejemplo
real puntual: VI- LICITACIONES del 27/07/2026 traía 13 licitaciones de 13
organismos distintos (2 Ministerios, 1 Hospital, 1 Caja de Jubilaciones, 6
Municipios/Comunas, 1 Unidad de Gestión, 1 Dirección Provincial de Vialidad)
pegadas una tras otra en un solo ver.php, sin ningún encabezado ni link
individual por licitación — no hay forma confiable de separarlas en normas
individuales desde el listado. Esto confirma la sospecha del propio usuario
("Licitaciones... lo dudo", "Avisos Oficiales... lo dudo también"): se
descartan por completo, junto con el resto de las secciones no-normativas
(que el usuario no llegó a mencionar pero comparten el mismo problema
estructural).

ESTRUCTURA DE UN ÍTEM DE LEY/DECRETO EN EL LISTADO — CONFIRMADA REAL
-------------------------------------------------------------------------------
HTML real (santafe_otrodia.html, sin modificar):

  <hr size="1" width="75%" align="left" noshade><span>III.1) Decreto 1501</span><br>
  DECRETO N°1501      Ref.: Implementa la Plataforma Única de Rendición
  de Cuentas...      Link de Acceso: https://www.santafe.gob.ar/normativa/
  item.php?id=354425&cod=bb48954aa53644c5e1e2f2167199eb1b         49542...<br>
  <a href='ver.php?seccion=2026/2026-07-27decreto1501.html' class='blue-text
  text-darken-3'>Ver texto completo</a><br>

Cada norma es un <span>{ROMANO}.{N}) {Tipo} {Número}</span> seguido de texto
plano SIN etiqueta (no <p>, no <div>) que siempre trae, en este orden: tipo+
número repetidos, "Ref.:" + síntesis, "Link de Acceso"/"Link de acceso" (con
o sin ":", confirmado real ambas formas) + URL a la ficha normativa, un
número de trámite suelto, y "..." de corte. Termina con un <a href='ver.php?
seccion=...'>Ver texto completo</a> que NO trae más información que la
síntesis ya vista (confirmado real: se pidió esa página con
mcp__workspace__web_fetch y devuelve exactamente el mismo texto truncado) —
por eso este bot no la usa como fuente, sólo la guarda como url_norma de
respaldo si la ficha normativa (mejor fuente, ver abajo) no está disponible.
items_de_edicion() parte el HTML del <td> de contenido con regex sobre los
propios <span> (_dividir_por_marcadores), primero por sección (Nº- TÍTULO),
después por ítem (Nº.N) Tipo Número) dentro de cada sección en alcance — no
hace falta un parser de árbol estricto porque el HTML es plano (sin anidar
un <div> por norma) y ya viene así en las 2 páginas reales vistas.

FICHA NORMATIVA (normativa/item.php) — LA FUENTE BUENA, CONFIRMADA REAL
-------------------------------------------------------------------------------
El link "Link de Acceso" de cada ítem apunta al Sistema de Información de
Normativa (SIN) de la Provincia — confirmado real pidiendo 2 fichas reales
completas (Ley 14465 y Decreto 1501/2026) vía mcp__workspace__web_fetch. Es
MUCHO mejor fuente que el listado del Boletín: trae campos ya etiquetados y
limpios, sin necesidad de ninguna heurística de emisor:

  Ley:     Número / Fecha / Firmantes / Temas / Descripción / Jurisdicción
  Decreto: Número / Fecha / Gestión / Firmantes / Iniciador / Expediente /
           Temas / Descripción / Jurisdicción / "Publicado en el Boletín
           Oficial de la Provincia" (Boletín oficial: NNNNN / Fecha del
           boletín: DD-MM-AAAA)

Diferencias reales confirmadas entre los dos tipos: "Número" de Ley es sólo
el número ("14465", sin año); "Número" de Decreto SÍ trae año ("1501/2026").
"Fecha" es la fecha de sanción/firma (Ley: 02-07-2026; Decreto: 24-07-2026),
DISTINTA de la fecha de publicación en el Boletín (Ley: 27-07-2026 según la
edición; Decreto: "Fecha del boletín: 27-07-2026" explícito en su propia
ficha). Este bot guarda como `fecha` la de sanción/firma cuando está (mismo
criterio que bot_santacruz.py, que también prefiere la fecha propia de la
norma sobre la de la edición), con la fecha de la edición como respaldo.
_campos_normativa() extrae estos campos por etiqueta de texto (no por
selector CSS — la página se leyó vía web_fetch, que ya convierte a texto/
markdown, así que no hay certeza de la clase/tag exacta de cada etiqueta;
el escaneo por texto es indiferente a eso, mismo criterio defensivo que
_texto_antes_de en bot_santacruz.py) buscando la posición de cada etiqueta
conocida y tomando como valor el texto hasta la SIGUIENTE etiqueta conocida
— incluida "Publicado en el Boletín Oficial de la Provincia", que no tiene
valor propio pero hay que reconocerla igual para que no quede pegada al
final de "Jurisdicción".

PDF DEL TEXTO ÍNTEGRO — CONFIRMADO REAL, CALIDAD DISPAREJA ENTRE LEY Y DECRETO
-------------------------------------------------------------------------------
Ni el listado del Boletín ni la ficha normativa traen el articulado completo
en HTML — sólo la "Descripción" (resumen de 1-3 oraciones) y un link a un PDF
oficial. El usuario pidió explícitamente descargar y extraer ese PDF (no sólo
quedarse con la Descripción). Se probaron los 2 PDF reales de los ejemplos de
arriba vía mcp__workspace__web_fetch:

  - Decreto 1501/2026: texto LIMPIO, capa de texto digital real, sin errores
    — el Decreto se tramitó 100% digital (el propio texto lo dice: sistema
    "TIMBÓ", firma electrónica). VISTO/CONSIDERANDO/POR ELLO/"EL GOBERNADOR
    DE LA PROVINCIA"/"D E C R E T A :" (marca resolutiva espaciada en
    letras, igual que Santa Cruz)/ARTÍCULO 1° a 6°, siempre con esa misma
    forma "ARTÍCULO N°:" (más consistente que Santa Cruz, que tenía 3
    convenciones de numeración distintas).
  - Ley 14465: texto con partes GARBLED (dígitos separados por espacios
    "1 4 4 6 5", "Sefior" en vez de "Señor", tramos ilegibles en la sección
    del Acta Acuerdo interprovincial) — el trámite legislativo de esta Ley
    en particular parece incluir un documento escaneado/fotografiado, no
    texto digital nativo como el Decreto.
  Con sólo 1 ejemplo real de cada tipo no se puede afirmar que TODAS las
  Leyes salgan garbled y TODOS los Decretos salgan limpios — pero alcanza
  para saber que NO se puede asumir calidad uniforme, y que hace falta un
  mecanismo de degradación segura, no sólo "confiar en el PDF".

Diseño elegido (_extraer_texto_pdf + _limpiar_texto_pdf): pdfplumber por
página, con el mismo umbral de longitud que bot_sanjuan.py (UMBRAL_TEXTO_
REAL_PDF) para descartar páginas casi vacías (probable escaneo sin capa de
texto en absoluto) — pero OJO, esto NO detecta el caso real visto en la Ley
14465 (texto garbled pero NO corto/vacío: pdfplumber igual devuelve bastante
texto, sólo que con errores). Por eso este bot NO intenta un OCR de respaldo
todavía (el usuario mismo anticipó "probablemente no hace falta OCR, sólo
extracción de texto", y agregar pypdfium2+pytesseract sin un disparador
confiable para saber CUÁNDO usarlo sería sumar complejidad sin certeza de que
ayude) — en cambio, texto_completo se arma SIEMPRE con la Descripción oficial
limpia primero, más los metadatos limpios (Firmantes/Jurisdicción/Expediente/
Temas), y el texto del PDF se agrega DESPUÉS, aparte, como "mejor esfuerzo".
Así, aunque el tramo de PDF salga con errores en algunas Leyes, el resto del
registro (síntesis, emisor, metadatos) queda intacto y confiable. Conviene
que el usuario revise a ojo unas cuantas Leyes reales una vez el bot corra de
verdad, para decidir si hace falta sumar OCR más adelante.
_limpiar_texto_pdf() saca líneas de membrete reconocidas en los 2 PDF reales
vistos (el slogan anual "{AÑO} - Año del ... Aniversario...", "Provincia de
Santa Fe - Poder Ejecutivo/Legislativo", "Hoja Adicional de Firmas", "Anexo",
"Número:"/"Referencia:" sueltos, el bloque de firma digital "Firmado
Digitalmente por...", "Razón: Gestion de tramites - Timbó") — el patrón del
slogan anual usa el año como variable (\d{4}), no "2026" literal, para no
romper el año que viene.

EMISOR — SALE DIRECTO DE "JURISDICCIÓN:", SIN HEURÍSTICA DE TEXTO
-------------------------------------------------------------------------------
A diferencia de TODA la familia anterior (Salta/San Juan/San Luis/Santa Cruz,
que arman el emisor buscando la línea antes de la marca resolutiva o
expandiendo siglas a mano), acá la ficha normativa ya trae "Jurisdicción:"
como campo limpio y ya redactado por la Provincia — confirmado real:
"Poder Legislativo de la Provincia de Santa Fe" (Ley 14465), "Poder Ejecutivo
de la Provincia de Santa Fe" (Decreto 1501/2026). Se aplica sólo .upper()
para ser consistente con la convención MAYÚSCULA del resto del sistema (los
otros bots normalizan a mayúsculas después de resolver el emisor) — no hace
falta ningún diccionario de siglas ni limpieza de "El/La {cargo} de" como en
San Luis/Santa Cruz, porque acá el campo nunca nombra al titular, nombra
directamente la institución. Si la ficha normativa no se pudo descargar (o
no trajo "Jurisdicción:"), se cae a un valor fijo por tipo ("PODER
LEGISLATIVO DE LA PROVINCIA DE SANTA FE" para LEY, "PODER EJECUTIVO DE LA
PROVINCIA DE SANTA FE" para cualquier otro tipo) — mismo criterio
constitucional que usa bot_santacruz.py para Decretos sin emisor detectado.
Sin confirmar real todavía: qué trae "Jurisdicción:" en una Resolución (¿el
Ministerio/Secretaría puntual, o "Poder Ejecutivo" genérico?) — no hay
ejemplo real disponible (ver ALCANCE arriba).

NÚMERO, AÑO Y TIPO
-------------------------------------------------------------------------------
tipo sale de la primera palabra del propio <span> del ítem ("Decreto 1501" ->
DECRETO, vía _sin_acentos+upper, igual convención que el resto de la
familia) — NO de a qué sección perteneció, así que "Decretos Sintetizados"
también saldría tipo=DECRETO si su formato real resulta ser igual al de
Decretos Provinciales (mismo criterio que bot_santacruz.py, que unifica
"Completos"/"Sintetizados" bajo el mismo tipo_norma_desc). numero/anio
priorizan el campo "Número:" de la ficha normativa (más confiable: ahí el
Decreto SÍ trae el año pegado con "/", la Ley no) y caen al número del
propio <span> del listado si la ficha no se pudo leer; el año, si no vino
en "Número:", sale de la fecha de sanción de la ficha, y si tampoco hay eso,
de la fecha de la propia edición.

QUÉ SE VALIDÓ — HISTORIAL RESUMIDO
-------------------------------------------------------------------------------
1. HTML crudo real (Ctrl+U, subido por el usuario) de 2 páginas: la portada
   (31/07/2026, sin Leyes/Decretos ese día) y resumendia.php de 27/07/2026
   (con 1 Ley y 2 Decretos reales) — confirmó la estructura exacta del
   listado y de cada ítem.
2. 6 ediciones adicionales leídas en vivo vía mcp__workspace__web_fetch (22,
   28, 29, 30 jul y 1 ago 2026) — confirmaron que el resto de las secciones
   (Licitaciones, Avisos, etc.) nunca traen estructura de ítem individual,
   que el aviso de "no publicado" es real y detectable, y sumaron 3
   Decretos reales más (1476, 1552, 1553) sin encontrar ningún caso real de
   Decreto Sintetizado o Resolución Provincial con contenido.
3. 2 fichas normativas reales completas (Ley 14465, Decreto 1501/2026) vía
   web_fetch — confirmaron el set de campos etiquetados y el valor real de
   "Jurisdicción:" para cada tipo.
4. 2 PDF reales completos (el de cada ficha de arriba) vía web_fetch —
   confirmaron que el Decreto sale con texto limpio y el formato real del
   articulado (VISTO/CONSIDERANDO/POR ELLO/marca espaciada/ARTÍCULO N°:), y
   que la Ley puede salir con tramos garbled (ver arriba).
5. Todo lo anterior (puntos 1-4) se verificó a mano (sandbox de este entorno
   caído toda la sesión, igual que en la sesión de Santa Cruz) contra las
   cadenas reales devueltas por cada fetch — antes de la corrida real de
   abajo, no se había ejecutado bot_santafe.py ni test_santafe_fixtures.py
   ni una vez.
6. **El usuario corrió el flujo real de punta a punta**
   (`test_santafe_fixtures.py` + `bot_santafe.py 22 --dry-run --todas
   --fecha 2026-07-27`, con debug_santafe.json real) — la validación más
   fuerte hasta ahora. Confirmó que el flujo completo funciona (descubrir
   edición por fecha, parsear Leyes/Decretos, bajar cada ficha normativa,
   bajar y extraer cada PDF, clasificar, armar payload) contra las 3 normas
   reales de esa edición. Expuso 3 bugs reales, los 3 corregidos:
   a) `ver_completo_url` salía None en el test offline (la fixture
      original — HTML real pegado tal cual, no la corrida en vivo — no
      matcheaba con el RE_VER_COMPLETO original). Se lo hizo más tolerante
      (ya no exige que "href" sea el primer atributo pegado a "<a ") y se
      agregó RE_VER_HREF_SIMPLE como respaldo (cualquier href a
      "ver.php?seccion=..." alcanza, sin depender del texto "Ver texto
      completo" ni de la estructura exacta del tag). No afectó ninguna
      norma real (las 3 tenían Link de Acceso, así que url_norma nunca usó
      este campo de respaldo) pero sí hacía fallar el test y dejaría un
      hueco real el día que una norma no tenga ficha normativa.
   b) `texto_completo` de la Ley 14465 real terminaba con "Fabian
      Lionel"/"Maximiliano" sueltos — la continuación del nombre en la
      línea siguiente a "Firmado Digitalmente por {APELLIDO}" (ese PDF
      tiene 2 firmas digitales distintas, cada una en 2 líneas) no
      matcheaba ningún patrón de RE_BOILERPLATE_PDF por sí sola.
      _limpiar_texto_pdf ahora traga hasta 2 líneas cortas después de una
      línea "Firmado Digitalmente por..." (RE_NOMBRE_SUELTO).
   c) El Decreto 1530/2026 real ("Santa Fe Activa") disparó "+2 cuerpo:
      promoción de un agente" por "...promover su desarrollo y
      fortalecimiento..." (sentido genérico de "fomentar", no de ascender
      a un agente) — no cambió el resultado final (terminó en -4, general
      igual) pero es un falso positivo real que podría cambiar el
      resultado en otro caso con menos puntaje negativo de otros lados. Se
      restringió el patrón a la forma reflexiva de decreto
      ("Promuévese"/"Promuévanse"), sacando la alternativa "Promover"
      suelta que era la única capaz de matchear el infinitivo genérico.
      Este mismo patrón laxo está heredado TAL CUAL en Salta/San Juan/San
      Luis/Santa Cruz — no se tocó ahí todavía porque el texto_completo de
      esos bots es más corto (no incluye el PDF entero), así que el riesgo
      real de este mismo falso positivo es menor pero no nulo; queda
      pendiente decidir si conviene aplicar el mismo ajuste en los otros 4.

QUÉ FALTA VALIDAR TODAVÍA
-------------------------------------------------------------------------------
1. Decretos Sintetizados y Resoluciones Provinciales: CERO ejemplos reales
   con contenido (8 ediciones distintas revisadas, todas vacías ahí, y la
   corrida real del usuario tampoco los ejercitó — sólo había Leyes/
   Decretos en la edición usada). Se incluyen por analogía a pedido del
   usuario, pero el formato real (¿tiene "Ref.:"/"Link de Acceso" igual?
   ¿"Jurisdicción:" da el Ministerio puntual en vez de "Poder Ejecutivo"?)
   sigue sin confirmar.
2. El PDF garbled de la Ley 14465 (confirmado real en la corrida del
   usuario, no sólo en el reconocimiento) sigue siendo 1 solo caso real —
   no se sabe si es la norma general para Leyes o un caso puntual de esa
   Ley (documento con Acta Acuerdo interprovincial escaneada de por medio).
   No hay OCR de respaldo todavía — sólo la degradación segura de
   anteponer siempre la Descripción limpia, que en la corrida real quedó
   confirmada funcionando (el campo `sintesis` de la Ley salió limpio pese
   al garbled del PDF).
3. La corrida real fue con una sola edición (27/07/2026, 3 normas: 1 Ley +
   2 Decretos) — falta ver varias ediciones más para ganar confianza en
   PATRONES_INDIVIDUAL/PATRONES_GENERAL contra más casos reales de Santa Fe
   (sólo se vieron 3 normas, todas terminaron GEN).
4. Nunca se probó `--sin-filtro` ni un envío real (sin `--dry-run`) contra
   el backend — la corrida real del usuario fue sólo dry-run.
5. _limpiar_texto_pdf() está armado con las líneas de membrete vistas en 2
   PDF reales de reconocimiento + el de la corrida real (mismos 2 Decretos
   + la misma Ley, ningún documento nuevo) — puede que falte cubrir
   variantes no vistas todavía (otras Leyes, Resoluciones, Decretos más
   viejos con otro formato de membrete).
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
from datetime import date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

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

SITIO = 'https://www.santafe.gov.ar'
BASE_BO = f'{SITIO}/boletinoficial/'

HEADERS_WEB = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
}

REINTENTOS = 3
ESPERA_REINTENTO = 3
ESPERA_ENTRE_ITEMS = 0.5   # pausa entre normas (cada una implica 1-2 pedidos más)
MAX_PAGINAS_PDF = 25       # tope de seguridad al extraer texto de un PDF
UMBRAL_TEXTO_REAL_PDF = 40  # por página; mismo criterio que bot_sanjuan.py
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700

# Secciones del listado (de las 18 totales) que traen normativa oficial con
# un ítem por norma — ver docstring "ALCANCE". Las otras 14 se ignoran.
SECCIONES_NORMATIVA = {
    'LEYES PROVINCIALES',
    'DECRETOS PROVINCIALES',
    'DECRETOS SINTETIZADOS',
    'RESOLUCIONES PROVINCIALES',
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
    return re.sub(r'\s+', ' ', (texto or '')).strip()


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
    """GET de texto (HTML). None si 404/4xx o si fallan todos los reintentos."""
    for intento in range(1, REINTENTOS + 1):
        try:
            r = sesion().get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            if r.status_code == 200:
                r.encoding = r.encoding or 'utf-8'
                return r.text
            if r.status_code < 500:
                return None
        except requests.RequestException as e:
            if intento == REINTENTOS:
                print(f"Aviso: error de red pidiendo {url}: {e}", file=sys.stderr)
                return None
        time.sleep(ESPERA_REINTENTO * intento)
    return None


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
# EDICIÓN: descubrimiento, fecha, detección de "no publicado"
# ===========================================================================
MESES = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SETIEMBRE': 9, 'SEPTIEMBRE': 9, 'OCTUBRE': 10,
    'NOVIEMBRE': 11, 'DICIEMBRE': 12,
}

RE_H1_FECHA = re.compile(
    r'Bolet[íi]n\s+Oficial\s+del\s+\S+\s+(\d{1,2})\s+de\s+([A-Za-zñÑ]+)\s+de\s+(\d{4})',
    re.IGNORECASE)

RE_FECHA_DDMMAAAA = re.compile(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})')

RE_FECHA_ARG = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def obtener_html_edicion(fecha=None):
    """(html, url) de la edición pedida (fecha=None -> última publicada)."""
    url = f'{BASE_BO}resumendia.php?dia={fecha}' if fecha else BASE_BO
    return descargar(url), url


def _fecha_de_edicion(html):
    """Fecha ISO leída del <h1> "Boletín Oficial del {día} {N} de {mes} de
    {año}" (confirmado real en las 2 páginas subidas por el usuario y en las
    6 leídas en vivo). None si no matchea."""
    m = RE_H1_FECHA.search(html or '')
    if not m:
        return None
    dia, mes_txt, anio = m.groups()
    mes = MESES.get(_sin_acentos(mes_txt).upper())
    if not mes:
        return None
    return f'{anio}-{mes:02d}-{int(dia):02d}'


def _no_publicado(html):
    """True si la edición pedida no tiene Boletín (fin de semana/feriado) —
    confirmado real probando 2026-08-01 (sábado)."""
    return 'no fue publicado o no tiene publicaciones' in (html or '').lower()


def _fecha_iso_ddmmaaaa(texto):
    """'24-07-2026' (o con '/') -> '2026-07-24'. None si no matchea."""
    m = RE_FECHA_DDMMAAAA.search(texto or '')
    if not m:
        return None
    d, mes, a = m.groups()
    try:
        return f'{a}-{int(mes):02d}-{int(d):02d}'
    except ValueError:
        return None


# ===========================================================================
# LISTADO DE LA EDICIÓN: secciones -> ítems (Leyes/Decretos/etc.)
# ===========================================================================
RE_SPAN_SECCION = re.compile(r'<span>\s*[IVXLC]+-\s*([^<]+?)\s*</span>', re.IGNORECASE)
RE_SPAN_ITEM = re.compile(r'<span>\s*[IVXLC]+\.\d+\)\s*([^<]+?)\s*</span>', re.IGNORECASE)
RE_LINK_ACCESO = re.compile(r'Link\s+de\s+[Aa]cceso\s*:?\s*(https?://\S+)', re.IGNORECASE)
RE_VER_COMPLETO = re.compile(
    r'''<a\b[^>]*?\bhref\s*=\s*['"]([^'"]+)['"][^>]*>\s*Ver\s+texto\s+completo\s*</a>''',
    re.IGNORECASE)
# Respaldo si lo de arriba no matchea (ej. atributos en otro orden tras el
# re-serializado de BeautifulSoup): cualquier href a ver.php?seccion=... es,
# en la práctica, siempre el link "Ver texto completo" de este listado —
# confirmado real que ese es el único uso de ver.php en toda la página.
RE_VER_HREF_SIMPLE = re.compile(
    r'''href\s*=\s*['"]([^'"]*ver\.php\?seccion=[^'"]*)['"]''', re.IGNORECASE)


def _dividir_por_marcadores(html, patron_span):
    """[(match_o_None, texto_html_hasta_el_próximo_marcador), ...] — el
    primer elemento (match None) es lo que viene ANTES del primer marcador.
    Sirve tanto para partir por sección como, dentro de una sección, por
    ítem — el HTML de esta página es plano (sin un <div> por norma), así que
    partir por regex sobre los propios <span> es más robusto que asumir un
    árbol anidado que no existe."""
    matches = list(patron_span.finditer(html))
    if not matches:
        return [(None, html)]
    partes = [(None, html[:matches[0].start()])]
    for i, m in enumerate(matches):
        fin = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        partes.append((m, html[m.end():fin]))
    return partes


def _td_contenido(soup):
    """El <td> que concatena las 18 secciones — se ubica por contener el
    texto "LEYES PROVINCIALES" (siempre presente, aun vacía; confirmado real
    en las 8 ediciones vistas), no por posición, porque no tiene id/class
    propio."""
    for td in soup.find_all('td'):
        if 'LEYES PROVINCIALES' in td.get_text():
            return td
    return None


def items_de_edicion(html):
    """Lista de dicts (uno por Ley/Decreto/etc. encontrado en las secciones
    de SECCIONES_NORMATIVA) con lo que ya trae el listado: sección, tipo,
    número "crudo" del <span>, texto síntesis (sin recortar), link de acceso
    a la ficha normativa (puede ser None si esa norma no lo trajera) y URL
    de respaldo "Ver texto completo"."""
    soup = BeautifulSoup(html, 'html.parser')
    td = _td_contenido(soup)
    if td is None:
        return []
    html_td = str(td)

    items = []
    for m_sec, resto in _dividir_por_marcadores(html_td, RE_SPAN_SECCION):
        if m_sec is None:
            continue
        titulo_seccion = _compacto(m_sec.group(1)).upper()
        if titulo_seccion not in SECCIONES_NORMATIVA:
            continue
        for m_item, chunk in _dividir_por_marcadores(resto, RE_SPAN_ITEM):
            if m_item is None:
                continue
            texto_item = _compacto(BeautifulSoup(chunk, 'html.parser').get_text(' '))
            m_link = RE_LINK_ACCESO.search(texto_item)
            link_acceso = m_link.group(1).rstrip('.,;') if m_link else None
            m_ver = RE_VER_COMPLETO.search(chunk) or RE_VER_HREF_SIMPLE.search(chunk)
            ver_completo = urljoin(BASE_BO, m_ver.group(1)) if m_ver else None
            titulo_item = _compacto(m_item.group(1))
            partes = titulo_item.split(None, 1)
            tipo = _sin_acentos(partes[0]).upper() if partes else ''
            numero_teaser = partes[1].strip() if len(partes) > 1 else ''
            items.append({
                'seccion': titulo_seccion,
                'tipo': tipo,
                'numero_teaser': numero_teaser,
                'sintesis_teaser': texto_item,
                'link_acceso': link_acceso,
                'ver_completo_url': ver_completo,
            })
    return items


# ===========================================================================
# FICHA NORMATIVA (normativa/item.php) — Número/Fecha/Firmantes/.../Jurisdicción
# ===========================================================================
ETIQUETAS_VALOR = [
    'Fecha del boletín', 'Boletín oficial', 'Número', 'Fecha', 'Gestión',
    'Firmantes', 'Iniciador', 'Expediente', 'Temas', 'Descripción', 'Jurisdicción',
]
ETIQUETAS_LIMITE_SIN_VALOR = [
    'Publicado en el Boletín Oficial de la Provincia',
    'Texto completo',
]

RE_PDF_LINK = re.compile(r'''href=['"]([^'"]*getFile\.php[^'"]*)['"]''', re.IGNORECASE)
RE_ID_NORMATIVA = re.compile(r'[?&]id=(\d+)')


def _campos_normativa(texto_plano):
    """{etiqueta: valor} tomando, para cada etiqueta conocida, el texto
    entre su posición y la de la SIGUIENTE etiqueta conocida (con o sin
    valor propio) — no depende de que estén en <dt>/<dd>, tabla o
    div/span, porque busca sobre el texto ya aplanado (mismo criterio
    defensivo que _texto_antes_de en bot_santacruz.py, necesario acá porque
    esta página se reconoció vía web_fetch, sin HTML crudo propio)."""
    posiciones = []
    for etq in ETIQUETAS_VALOR:
        m = re.search(r'\b' + re.escape(etq) + r'\s*:', texto_plano, re.IGNORECASE)
        if m:
            posiciones.append((m.start(), m.end(), etq, True))
    for etq in ETIQUETAS_LIMITE_SIN_VALOR:
        m = re.search(re.escape(etq), texto_plano, re.IGNORECASE)
        if m:
            posiciones.append((m.start(), m.end(), etq, False))
    posiciones.sort(key=lambda p: p[0])

    campos = {}
    for i, (ini, fin, etq, tiene_valor) in enumerate(posiciones):
        if not tiene_valor:
            continue
        fin_valor = posiciones[i + 1][0] if i + 1 < len(posiciones) else len(texto_plano)
        campos[etq] = _compacto(texto_plano[fin:fin_valor])
    return campos


def obtener_ficha_normativa(url):
    """(campos, pdf_urls) de una ficha normativa/item.php. (\\{\\}, []) si no
    se pudo descargar."""
    html = descargar(url)
    if not html:
        print(f"Aviso: no se pudo descargar la ficha normativa {url}", file=sys.stderr)
        return {}, []
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()
    texto_plano = soup.get_text('\n', strip=True)
    campos = _campos_normativa(texto_plano)
    pdf_urls = [urljoin(url, h) for h in RE_PDF_LINK.findall(html)]
    return campos, pdf_urls


def _id_desde_url(url):
    m = RE_ID_NORMATIVA.search(url or '')
    return m.group(1) if m else None


# ===========================================================================
# PDF DEL TEXTO ÍNTEGRO
# ===========================================================================
RE_BOILERPLATE_PDF = [
    re.compile(r'^.{0,3}\d{4}\s*-\s*A[nñ]o\s+del\b.*$', re.IGNORECASE),
    re.compile(r'^Provincia\s+de\s+Santa\s+Fe\s*-\s*Poder\s+(?:Ejecutivo|Legislativo)\.?$', re.IGNORECASE),
    re.compile(r'^Hoja\s+Adicional\s+de\s+Firmas\.?$', re.IGNORECASE),
    re.compile(r'^Anexo\.?$', re.IGNORECASE),
    re.compile(r'^N[úu]mero\s*:\s*$', re.IGNORECASE),
    re.compile(r'^Referencia\s*:.*$', re.IGNORECASE),
    re.compile(r'^El\s+documento\s+fue\s+importado\s+por\s+el\s+sistema\s+Timb[óo]\.?$', re.IGNORECASE),
    re.compile(r'^Fecha\s*:\s*\d{4}\.\d{2}\.\d{2}.*$', re.IGNORECASE),
    re.compile(r'^Raz[óo]n\s*:\s*Gestion\s+de\s+tramites\b.*$', re.IGNORECASE),
    re.compile(r'^P[áa]g\.?\s*\d+\s*$', re.IGNORECASE),
]

# Caso aparte (no es un patrón de UNA línea): "Firmado Digitalmente por
# {APELLIDO}" viene seguido, en 1 o 2 líneas MÁS, del nombre de pila suelto
# ("Fabian Lionel", "Maximiliano") — confirmado real en debug_santafe.json
# (Ley 14465: quedaban "Fabian Lionel"/"Maximiliano" colgando al final del
# texto_completo porque esas líneas de continuación no matchean ningún
# patrón de la lista de arriba por sí solas). _limpiar_texto_pdf tolera
# hasta 2 líneas cortas después de una línea "Firmado Digitalmente por".
RE_FIRMA_DIGITAL = re.compile(r'^Firmado\s+[Dd]igitalmente\s+por\b.*$', re.IGNORECASE)
RE_NOMBRE_SUELTO = re.compile(r'^[A-ZÁÉÍÓÚÑa-záéíóúñ.\s]{1,45}$')


def _extraer_texto_pdf(pdf_bytes):
    """Texto de cada página con pdfplumber, descartando páginas cuya
    extracción sea demasiado corta (probable página sin capa de texto) —
    mismo umbral/criterio que bot_sanjuan.py. '' si pdfplumber no está
    disponible o el PDF no se pudo abrir."""
    if pdfplumber is None:
        print("Aviso: falta pdfplumber (pip install pdfplumber); texto_completo "
              "quedará sin el articulado del PDF.", file=sys.stderr)
        return ''
    try:
        partes = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for pagina in pdf.pages[:MAX_PAGINAS_PDF]:
                t = pagina.extract_text() or ''
                if len(t) >= UMBRAL_TEXTO_REAL_PDF:
                    partes.append(t)
        return '\n'.join(partes)
    except Exception as e:
        print(f"Aviso: no se pudo extraer texto del PDF: {e}", file=sys.stderr)
        return ''


def _limpiar_texto_pdf(texto):
    """Saca líneas de membrete conocidas (ver RE_BOILERPLATE_PDF / docstring
    "PDF DEL TEXTO ÍNTEGRO") y compacta espacios línea por línea, SIN unir
    párrafos entre sí (conserva un salto de línea por línea real del PDF).
    También traga hasta 2 líneas cortas después de "Firmado Digitalmente
    por..." (el nombre de pila suelto que queda colgando — ver
    RE_NOMBRE_SUELTO)."""
    if not texto:
        return ''
    lineas = []
    tras_firma = 0
    for linea in texto.split('\n'):
        l = linea.strip()
        if not l:
            continue
        if RE_FIRMA_DIGITAL.match(l):
            tras_firma = 2
            continue
        if tras_firma > 0 and RE_NOMBRE_SUELTO.match(l):
            tras_firma -= 1
            continue
        tras_firma = 0
        if any(p.match(l) for p in RE_BOILERPLATE_PDF):
            continue
        lineas.append(_compacto(l))
    return '\n'.join(lineas)


# ===========================================================================
# ARMADO DE UNA NORMA
# ===========================================================================
RE_REF_TEASER = re.compile(
    r'Ref\.?:?\s*(.+?)(?:\s*Link\s+de\s+[Aa]cceso|\s*$)', re.IGNORECASE | re.DOTALL)


def _sintesis_desde_teaser(texto_teaser):
    m = RE_REF_TEASER.search(texto_teaser or '')
    return _compacto(m.group(1)) if m else _compacto(texto_teaser or '')


def _bloque_metadatos(campos, pdf_urls):
    lineas = []
    for etq in ('Firmantes', 'Gestión', 'Iniciador', 'Expediente', 'Temas'):
        v = campos.get(etq)
        if v:
            lineas.append(f'{etq}: {v}')
    if pdf_urls:
        lineas.append('Texto completo (PDF oficial): ' + '; '.join(pdf_urls))
    return '\n'.join(lineas)


def _armar_norma(item, fecha_edicion, campos, pdf_urls, texto_pdf, url_norma):
    """Lógica de armado PURA (sin red) a partir de un ítem del listado y los
    campos/pdf ya obtenidos (o {}/[]/'' si no hubo ficha/PDF disponibles).
    Separada de procesar_norma() a propósito para poder probarla contra
    campos ya conocidos (reales, ver test_santafe_fixtures.py) sin depender
    de la red."""
    tipo = item['tipo'] or 'DECRETO'

    numero_ficha = campos.get('Número', '')
    if '/' in numero_ficha:
        numero, _, anio = numero_ficha.rpartition('/')
        numero = numero.strip()
        anio = anio.strip()
    else:
        numero = numero_ficha.strip() or item['numero_teaser']
        anio = ''

    fecha_sancion = _fecha_iso_ddmmaaaa(campos.get('Fecha', ''))
    if not anio:
        anio = (fecha_sancion or fecha_edicion or '')[:4] or '????'
    fecha = fecha_sancion or fecha_edicion

    emisor = _compacto(campos.get('Jurisdicción', '')).upper()
    if not emisor:
        emisor = ('PODER LEGISLATIVO DE LA PROVINCIA DE SANTA FE' if tipo == 'LEY'
                  else 'PODER EJECUTIVO DE LA PROVINCIA DE SANTA FE')

    descripcion = _compacto(campos.get('Descripción', '')) or \
        _sintesis_desde_teaser(item['sintesis_teaser'])

    bloque_meta = _bloque_metadatos(campos, pdf_urls)
    texto_completo = '\n\n'.join(p for p in (descripcion, bloque_meta, texto_pdf) if p)

    return {
        'id': _id_desde_url(item['link_acceso']) or f"{tipo}-{numero}-{fecha_edicion}",
        'seccion': item['seccion'],
        'tipo': tipo,
        'numero': numero or '?',
        'anio': anio,
        'fecha': fecha,
        'emisor': emisor,
        'sintesis': descripcion,
        'texto_completo': texto_completo,
        'url_norma': url_norma,
    }


def procesar_norma(item, fecha_edicion):
    """Descarga (ficha normativa + PDF) y arma el registro final de una
    norma. Nunca devuelve None — si la ficha normativa no está disponible,
    _armar_norma degrada a lo que ya trae el listado (mismo espíritu que el
    camino de respaldo de bot_santacruz.py, aplicado acá a nivel "de qué
    página confío" en vez de "qué selector confío"). Es la ÚNICA función de
    este módulo que hace red por sí misma para una norma puntual — la
    lógica de armado en sí vive en _armar_norma (sin red, testeable)."""
    url_norma = item['link_acceso'] or item['ver_completo_url'] or BASE_BO

    campos, pdf_urls = ({}, [])
    if item['link_acceso']:
        campos, pdf_urls = obtener_ficha_normativa(item['link_acceso'])

    texto_pdf = ''
    if pdf_urls:
        pdf_bytes = descargar_bytes(pdf_urls[0])
        if pdf_bytes:
            texto_pdf = _limpiar_texto_pdf(_extraer_texto_pdf(pdf_bytes))
        else:
            print(f"Aviso: no se pudo descargar el PDF {pdf_urls[0]}", file=sys.stderr)

    return _armar_norma(item, fecha_edicion, campos, pdf_urls, texto_pdf, url_norma)


# ===========================================================================
# CLASIFICACIÓN INDIVIDUAL / GENERAL
# ===========================================================================
# Heredado del resto de la familia (mismo idioma administrativo argentino),
# con 1 ajuste propio: el patrón de "promoción de un agente" original
# (`Promu[ée]v[ae](?:se)?|Promover`) disparó un falso positivo REAL contra
# el Decreto 1530/2026 de Santa Fe (BO 27/07/2026, "Santa Fe Activa") —
# "...con el propósito de brindar apoyo económico... promover su desarrollo
# y fortalecimiento..." usa "promover" en el sentido genérico de "fomentar",
# no de "ascender a un agente a un cargo superior". No fue un problema en el
# resto de la familia porque su texto_completo es mucho más corto (no
# incluye el PDF entero con todos los "considerando"); acá, con el
# articulado completo del PDF sumado, el patrón laxo tenía mucha más
# superficie para engancharse con el sentido genérico del verbo. Se
# restringió a la forma reflexiva de decreto ("Promuévese"/"Promuévanse"),
# que es como se redactan los ascensos de personal en la práctica — se
# perdería un caso real que use "Promueve"/"Promover" sin el "-se", pero no
# se vio ninguno así en las 3 normas reales revisadas, y es preferible a
# seguir generando falsos positivos con el sentido genérico del verbo.
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
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Santa Fe.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se descubre solo')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--fecha', metavar='YYYY-MM-DD',
                    help='edición puntual por fecha, salta el descubrimiento de la última')
    ap.add_argument('--todas', action='store_true',
                    help='muestra también las individuales, con puntaje y motivos')
    ap.add_argument('--sin-filtro', action='store_true',
                    help='envía también las individuales')
    ap.add_argument('--volcar', action='store_true', help='imprime lo reconocido y sale')
    args = ap.parse_args()

    if args.fecha and not RE_FECHA_ARG.match(args.fecha):
        ap.error(f"--fecha debe tener formato YYYY-MM-DD (se recibió {args.fecha!r})")

    # ---- 1. Ubicar la edición ---------------------------------------------
    html, url_edicion = obtener_html_edicion(args.fecha)
    if not html:
        salida("warning", f"No se pudo descargar {url_edicion} (ver stderr).")
    print(f"Edición: {url_edicion}", file=sys.stderr)

    if _no_publicado(html):
        fecha_boletin = args.fecha or date.today().isoformat()
        salida("success", f"Sin novedades: el {fecha_boletin} no hubo Boletín Oficial "
                          f"publicado en Santa Fe.", total=0)

    fecha_boletin = _fecha_de_edicion(html) or args.fecha
    if not fecha_boletin:
        salida("warning", f"No se pudo determinar la fecha de la edición leída en "
                          f"{url_edicion} (ver stderr).")
    if args.fecha and fecha_boletin != args.fecha:
        print(f"Aviso: se pidió --fecha {args.fecha} pero la página devolvió la edición "
              f"del {fecha_boletin} — se conserva la fecha real leída del <h1>.",
              file=sys.stderr)

    # ---- 2. Enumerar los ítems de Leyes/Decretos/etc. de esa edición ------
    items = items_de_edicion(html)
    print(f"Ítems de normativa encontrados en la edición del {fecha_boletin}: {len(items)}",
          file=sys.stderr)
    if not items:
        salida("success", f"Sin novedades: no se encontraron Leyes/Decretos en la edición "
                          f"del {fecha_boletin}.", total=0)

    # ---- 3. Descargar ficha normativa + PDF y armar cada norma -------------
    normas_todas = []
    for i, item in enumerate(items):
        n = procesar_norma(item, fecha_boletin)
        if i < len(items) - 1:
            time.sleep(ESPERA_ENTRE_ITEMS)
        n['es_individual'], n['puntaje'], n['motivos'] = clasificar_norma(
            n['tipo'], n['sintesis'], n['texto_completo'])
        normas_todas.append(n)

    if args.volcar:
        for n in normas_todas:
            print(f"  [{n['seccion']}] {n['tipo']:10s} N° {n['numero']:>10s}/{n['anio']} "
                  f"fecha={n['fecha'] or '?':10s} emisor={n['emisor'][:50]}", file=sys.stderr)
        salida("success", f"volcado: {len(normas_todas)} normas reconocidas.")

    guardar_debug(json.dumps(normas_todas, ensure_ascii=False, indent=2, default=str),
                  'debug_santafe.json')

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

    if not normas_todas:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Sin novedades: el boletín del {fecha_boletin} no publicó "
                          f"normativa reconocible.", total=0)

    if not a_enviar:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Se procesó el {fecha_boletin}, pero las {len(individuales)} "
                          f"normas encontradas son actos individuales; no se envió "
                          f"ninguna.", total=0)

    # ---- 4. Envío -----------------------------------------------------------
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