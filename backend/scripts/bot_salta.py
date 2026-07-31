#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 BOLETÍN OFICIAL DE LA PROVINCIA DE SALTA  —  id_jurisdiccion 18
===============================================================================

POR QUÉ ESTE BOT NO PARSEA EL PDF (a diferencia de La Rioja/Jujuy/La Pampa)
-----------------------------------------------------------------------------
El usuario pidió expresamente bajar los PDF de ejemplo
(boletindigital/2026/22238.pdf y anexodigital/2026/22238.pdf) y se hizo:
ambos se descargaron y se leyeron (vía fetch, no hubo acceso de red desde el
sandbox de bash a boletinoficialsalta.gob.ar, igual que con casi todos los
demás sitios de gobierno provinciales).

Pero en el reconocimiento apareció algo mejor que el PDF: el sitio tiene un
navegador de ediciones en HTML plano, sin JavaScript de por medio, que ya
viene troceado por norma:

    https://boletinoficialsalta.gob.ar/NavegacionRapida.php?tipo1=A&nro_edicion=0

Esto da, para la ÚLTIMA edición (nro_edicion=0) o cualquier edición puntual
(nro_edicion=<número>), un listado completo por rubro (DECRETOS, DECISIONES
ADMINISTRATIVAS, RESOLUCIONES DELEGADAS, RESOLUCIONES, ACORDADAS,
DISPOSICIONES, y también los rubros que NO son normativa: LICITACIONES
PUBLICAS, ADJUDICACIONES SIMPLES, CONTRATACIONES ABREVIADAS, CONCESIONES DE
AGUA PUBLICA, CONVOCATORIAS A AUDIENCIAS PUBLICAS, AVISOS ADMINISTRATIVOS,
NOTIFICACIONES ADMINISTRATIVAS...). Cada ítem trae N°, fecha propia, sigla
del emisor y título, y un link a:

    https://boletinoficialsalta.gob.ar/instrumento.php?tabla=D|443/26&data=22235

que devuelve la norma COMPLETA ya como texto (VISTO/CONSIDERANDO/POR
ELLO/DECRETA|DECIDE|RESUELVE|DISPONE/ARTÍCULO 1º.../firma), con el nombre
COMPLETO del organismo emisor (no la sigla) y la fecha de publicación real
del boletín donde salió. Es exactamente el mismo tipo de dato que da la API
de Mendoza (portalgateway.mendoza.gov.ar/api/boe) — nada de columnas, nada de
negrita falsa, nada de recortar por gutter. Por eso este bot sigue la
arquitectura de bot_mendoza.py (índice + detalle por HTTP) y NO la de
bot_larioja.py (PDF con pdfplumber).

El PDF (boletindigital) se comprobó que sólo sirve como respaldo/impresión —
cada instrumento.php linkea al PDF completo de la edición donde se publicó,
pero el texto operativo ya está en instrumento.php. Y el anexodigital,
comprobado contra el ejemplar real del 22238, es pura tabla/anexo (cuadro
tarifario de COSAYSA, nómina de guardias del Poder Judicial): NO son normas
con Artículo 1º propio, son anexos DE normas que ya están en la Sección
Administrativa (el propio anexo lo dice: "ENTE REGULADOR... RESOLUCIÓN Nº
1219/26" y "CORTE DE JUSTICIA... ACORDADA Nº 14704/26" son justamente dos de
las normas que este bot ya captura por NavegacionRapida.php). No hay
normativa que viva SÓLO en el anexo y no en la Sección Administrativa.

DESCUBRIMIENTO: nro_edicion=0 = "la última"
-----------------------------------------------------------------------------
    https://boletinoficialsalta.gob.ar/NavegacionRapida.php?tipo1=A&nro_edicion=0

devuelve siempre la última edición publicada. Se probó en vivo (31/07/2026,
mismo día de este desarrollo) y devolvió exactamente "Boletín N° 22238
Salta, Viernes 31 de Julio de 2026" — la MISMA edición que el usuario dio
como ejemplo de "hoy". No hace falta pasar por boletin_suplemento.php (esa
página, en este reconocimiento, quedó pegada varios días — parece cacheada
del lado del servidor — mientras que NavegacionRapida.php sí reflejó el día
real en cada pedido).

El número de edición es CORRELATIVO y sube ~1 por día hábil (Lun-Vie), sin
huecos vistos en la ventana de muestra: 22233=Vie 24/07, 22235=Mar 28/07,
22238=Vie 31/07 — exactamente 6 números para 6 días hábiles corridos
(24,27,28,29,30,31). No se puede reconstruir la URL de una fecha vieja
directo (a diferencia de La Rioja); hay que "caminar" desde una edición
conocida (ver --fecha más abajo).

LAS 5 SECCIONES DEL SITIO (tipo1) — sólo 2 tienen normativa
-----------------------------------------------------------------------------
Comprobado contra la edición 22238 (y 22235 para General, que resultó tener
la última edición con contenido más vieja) las 5 secciones:

  A = Administrativa  -> SÍ tiene normativa (Decretos, Decisiones
                          Administrativas, Resoluciones (Delegadas y no),
                          Acordadas, Disposiciones) MEZCLADA con avisos/
                          licitaciones/notificaciones. Es la única que
                          SIEMPRE se consulta.
  M = Municipal        -> normativa municipal CUANDO se publica (se vio
                          "NO EXISTE SECCIÓN MUNICIPAL EN ESTA FECHA" en el
                          ejemplar de muestra — no es error, es que esa
                          edición no trajo nada de municipios). Se consulta
                          siempre igual, por si acaso; el mapeo de sus
                          rubros (ORDENANZAS, DECRETOS MUNICIPALES...) es
                          por ANALOGÍA con Mendoza, sin muestra real.
  J = Judicial         -> 100% edictos (Sucesorios, Posesiones Veinteañales,
                          Edictos de Quiebras, Edictos Judiciales). NUNCA
                          normativa. No se consulta.
  C = Comercial        -> 100% avisos privados (Constituciones de Sociedad,
                          Asambleas Comerciales, Avisos Comerciales). NUNCA
                          normativa. No se consulta.
  G = General          -> Asambleas de Entidades Civiles, Recaudaciones
                          diarias. NUNCA normativa en la muestra vista. No
                          se consulta.

CÓMO SE ARMA CADA ÍTEM DEL LISTADO
-----------------------------------------------------------------------------
Dos formatos de línea, confirmados contra ediciones reales (22235, 22238):

  Directo (Decretos, Decisiones Administrativas, Resoluciones Delegadas,
  Resoluciones ministeriales):
      "N° 443 DEL 23/07/2026 - S.G.G. - DECLARA DE INTERÉS PROVINCIAL..."

  Con ID interno (Resoluciones/Disposiciones/Acordadas de organismos
  autárquicos — Ente Regulador, Corte de Justicia, Dirección Grl. de
  Rentas, etc. — que en el sitio viven en una tabla genérica de "avisos"
  con un ID correlativo propio, ADEMÁS del número real de la norma):
      "N° 100138473 - Nº 1219 DEL 30/07/2026 - ENTE REGULADOR DE LOS
       SERVICIOS PÚBLICOS - AUTORIZA ACTUALIZACIÓN TARIFARIA..."

El tipo de norma sale del RUBRO (encabezado de sección: "DECRETOS",
"RESOLUCIONES DELEGADAS", etc.), nunca del ID interno — el mismo mecanismo
que usa Mendoza con sus sub-acordeones. Cualquier rubro que no esté en
RUBRO_A_TIPO se descarta sin más (licitaciones, adjudicaciones,
contrataciones, concesiones de agua, convocatorias a audiencia,
notificaciones y avisos administrativos — ninguno es normativa con
Artículo 1º).

EMISOR: se prefiere el nombre completo del CUERPO de instrumento.php
-----------------------------------------------------------------------------
El listado sólo da una sigla ("S.G.G.", "M.G.J.", "M.E.y S.P.") para
Decretos/Decisiones/Resoluciones ministeriales — no hay en todo el sitio una
tabla pública de siglas -> nombre completo (se revisó autoridades.php: sólo
tiene 3 fotos, Gobernador/Secretaria General/Directora del Boletín, nada de
organigrama). Pero el propio texto de instrumento.php trae el nombre
COMPLETO del organismo pegado justo después de "TIPO Nº <número>":

    DECRETO Nº 443                              DECISION ADMINISTRATIVA Nº 283
    SECRETARÍA GENERAL DE LA GOBERNACIÓN   <-    MINISTERIO DE GOBIERNO Y JUSTICIA
    Expediente Nº 0010226-127659/2026-0          Expte. Nº 334-107771/2026-0

Confirmado real contra 6 tipos de norma (Decreto, Decisión Administrativa,
Resolución Delegada x2, Resolución ministerial, Resolución/Disposición de
organismo autárquico): "M.E.y C." = MINISTERIO DE EDUCACIÓN Y CULTURA,
"M.SEG." = MINISTERIO DE SEGURIDAD, "J.G.M." = JEFATURA DE GABINETE DE
MINISTROS, "M.D.S." = MINISTERIO DE DESARROLLO SOCIAL, "M.E.y S.P." =
MINISTERIO DE ECONOMIA Y SERVICIOS PUBLICOS.

Las Resoluciones/Disposiciones de organismos AUTÁRQUICOS (Ente Regulador,
Inspección General de Personas Jurídicas — las del patrón "con ID interno"
del listado) NO tienen "Expte./Expediente Nº" como línea propia, van directo
de la línea del organismo a "VISTO" — confirmado real. Por eso el cierre de
la extracción acepta Expte./Expediente O "VISTO", lo que aparezca primero.
Para estos casos en particular tampoco hace falta: el listado YA trae el
nombre completo ("ENTE REGULADOR DE LOS SERVICIOS PÚBLICOS", "DIRECCIÓN
GENERAL DE RENTAS"...), así que aunque la extracción del cuerpo no
encuentre nada, el fallback a la sigla del listado ya es el nombre completo.

Si la extracción del cuerpo falla igual (formato inesperado, o
--sin-detalle), se cae a la sigla/nombre del listado, y como último recurso
a "PODER EJECUTIVO".

SÍNTESIS: Artículo 1º, igual que el resto de las provincias — salvo Acordadas
-----------------------------------------------------------------------------
Mismo mecanismo que Jujuy/La Rioja/Mendoza: se busca la ÚLTIMA marca
resolutiva y se toma el Artículo 1º posterior a esa marca. Confirmado real:
Decretos y Resoluciones (Delegadas o no) usan "RESUELVE:"/"DECRETA:",
Decisiones Administrativas usan "DECIDE:".

Las ACORDADAS DE LA CORTE DE JUSTICIA son distintas en dos sentidos, los dos
confirmados reales contra la Acordada 14704/26:
  1. Al ser un cuerpo colegiado (varios jueces), la marca resolutiva está en
     PLURAL: "Por ello ACORDARON:" (no "ACUERDA:" en singular, que era la
     hipótesis sin confirmar de la primera versión de este bot).
  2. No usan "ARTÍCULO 1º.-": numeran sus puntos con romanos ("I. APROBAR
     el Anexo que integra la presente... II. COMUNICAR a quienes
     corresponda..."). Como RE_ARTICULO1 nunca va a matchear ahí, la
     síntesis cae al texto que sigue a la marca resolutiva tal cual (que
     para una Acordada arranca justo en "I. APROBAR...", así que funciona
     bien igual sin necesitar un regex de números romanos aparte).

--fecha ES BEST-EFFORT (sin navegador para confirmar el formulario real)
-----------------------------------------------------------------------------
edicionesanteriores.php tiene "BUSCAR POR FECHA", pero la extensión de
Chrome no estaba disponible en esta sesión para inspeccionar los nombres
reales de los campos del formulario, y el fetch de texto plano no conserva
atributos de <input>. En vez de adivinar nombres de parámetros, --fecha se
resuelve caminando desde la última edición conocida: se estima el número
por cantidad de días hábiles de diferencia y se ajusta de a 1 comparando la
fecha real de cada edición probada (hasta 15 intentos). Es más lento que un
endpoint de búsqueda directo, pero no depende de adivinar nada que no se
pudo confirmar. Para uso diario (cron, sin --fecha) esto no se usa nunca:
nro_edicion=0 alcanza y ya se probó en vivo.

FLAGS
-----
    --dry-run         no envía nada
    --numero N         edición puntual por número (salta el descubrimiento
                       de "última"; tiene prioridad sobre --fecha)
    --fecha AAAA-MM-DD  best-effort, ver arriba
    --indice ARCHIVO   HTML de NavegacionRapida.php (sección Administrativa)
                       ya guardado, para probar el parser sin pegarle al
                       sitio
    --sin-detalle      no pide instrumento.php por norma (más rápido para
                       --volcar; sin esto no hay síntesis real, texto
                       completo ni emisor completo — sólo lo del listado)
    --todas            muestra también las individuales, con puntaje/motivos
    --sin-filtro       envía todo sin filtrar
    --volcar           imprime lo reconocido en el listado y sale (no pide
                       instrumento.php)

===============================================================================
VALIDADO CONTRA PRODUCCIÓN (31/07/2026, Boletín Nº 22238, --dry-run --todas)
===============================================================================
La primera versión de este bot se escribió sin poder correrla contra el
sitio real (sandbox sin salida de red a dominios de gobierno). El usuario la
corrió en su servidor y mandó el debug_salta.json real; esa corrida
encontró 3 bugs reales, ya corregidos acá:

1. texto_completo traía el MENÚ DE NAVEGACIÓN completo pegado adelante
   (~700 caracteres: "Inicio Ediciones Anteriores Búsquedas Leyes
   Decretos...") para las 9 normas de la corrida, porque get_text() no
   tiene forma de distinguir el contenido del menú sin una etiqueta propia
   confirmada. Se corrigió recortando desde "Publicado en el Boletín..."
   (metadato presente en las 9 muestras). Sólo se había notado como
   síntoma visible en la Acordada (ver punto 2), pero afectaba a las 9 por
   igual.
2. Las ACORDADAS no matchean nada de lo que se había previsto: ni la marca
   resolutiva ("ACORDARON:", no "ACUERDA:" — es un cuerpo colegiado) ni la
   numeración por artículos (usan romanos: "I. APROBAR..."). Sin el fix del
   punto 1, esto hacía que la síntesis cayera al texto[:400] == puro menú
   de navegación. Corregido: RE_MARCA_RESOLUTIVA ahora incluye ACORDARON, y
   _sintesis_de_texto cae al texto posterior a la marca (no a texto[:400])
   cuando no hay "ARTÍCULO 1º".
3. El clasificador sólo toleraba el verbo en forma refleja ("Acéptase") o
   presente ("Acepta"), pero el Artículo 1º real casi siempre lo redacta en
   INFINITIVO ("Aceptar... la renuncia...", visto real en 2 Resoluciones
   Delegadas) — sin el infinitivo, el patrón no matcheaba en síntesis y
   caía a mitad de puntaje por cuerpo. Mismo problema en "Otorga(se) +
   beneficio" cuando el Artículo 1º intercala una cláusula entre el verbo y
   la palabra "beneficio" (visto real: "Otórgase, a partir de la fecha de
   su notificación, el beneficio..." — a esa norma casi le hizo perder el
   umbral de individual). Ambos corregidos con tolerancia de forma verbal y
   de distancia entre palabras.

Con estos 3 fixes se volvió a correr contra la MISMA edición real (22238):
de las 9 normas, clasificación correcta en las 9 (4 generales / 5
individuales — el Decreto 449, que antes salía mal clasificado, ahora da
individual con el peso completo). La Acordada quedó con su síntesis real
("I. APROBAR el Anexo que integra la presente...") y se mantiene general —
es una modificación de nómina de guardias, no un acto sobre una persona
puntual.

El ítem que había quedado "sin formato" en la corrida anterior resultó ser
un caso distinto, no un bug: "N° 100138394 - COMISIÓN DE JUSTICIA, ACUERDOS
Y DESIGNACIONES DE LA CÁMARA DE SENADORES... - ESTABLECE FECHA PARA
AUDIENCIA PÚBLICA..." — un anuncio de una comisión legislativa fijando
fecha de audiencia, filed bajo el rubro RESOLUCIONES pero sin número de
resolución propio (a diferencia de todos los demás ítems de esa edición).
Se agregó RE_ITEM_SIN_NUMERO para reconocer y loguear este caso aparte
("excluido, sin número propio de norma") en vez de contarlo junto con
posibles bugs reales de parseo ("sin formato").

===============================================================================
QUÉ FALTA VALIDAR
===============================================================================
1. LEYES y DECRETOS-LEYES: no aparecieron en ninguna de las ediciones vistas
   (22235, 22238). Se mapean igual en RUBRO_A_TIPO por las dudas (mismo
   criterio que Mendoza con sus rubros nunca vistos), pero el formato de
   instrumento.php para una Ley (¿VISTO/CONSIDERANDO igual, o el texto
   sancionado por la Legislatura viene distinto? ¿tiene "ARTÍCULO 1º" o
   numera distinto, como las Acordadas?) no se pudo confirmar.
2. Sección Municipal: la única muestra la tuvo vacía ("NO EXISTE SECCIÓN
   MUNICIPAL EN ESTA FECHA"). El mapeo ORDENANZAS/DECRETOS MUNICIPALES/
   RESOLUCIONES MUNICIPALES es por analogía con Mendoza, sin ver un ítem
   real de Salta.
3. --fecha: heurística de caminata (ver arriba), no un endpoint confirmado.
   Puede tardar varios pedidos y, si hay algún feriado no contemplado en la
   estimación inicial, puede necesitar más de los 15 intentos permitidos
   (ahí devuelve None y el bot avisa en vez de arriesgar la fecha
   equivocada). No se probó todavía contra un caso real.
4. No se vio ningún caso de paginación dentro de NavegacionRapida.php (todas
   las normas de la edición aparecen en una sola página); si algún día una
   edición tiene muchísimas más normas que las vistas, esto no está
   confirmado.
5. El parser del listado (rubro = texto suelto en mayúsculas fuera de un
   <a>) funcionó bien contra el sitio real, pero sigue sin haberse
   inspeccionado el HTML crudo (Chrome no estaba disponible en la sesión
   original). Si algún día deja de reconocer rubros que antes andaban,
   revisar ahí primero.
===============================================================================
"""

import os
import re
import sys
import json
import time
import argparse
import unicodedata
from datetime import datetime, timedelta

import requests

try:
    from bs4 import BeautifulSoup, NavigableString
except ImportError:
    BeautifulSoup = None
    NavigableString = None

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

SITIO = 'https://boletinoficialsalta.gob.ar'
URL_NAVEGACION = f'{SITIO}/NavegacionRapida.php'

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

MESES_NUM = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'setiembre': 9, 'octubre': 10,
    'noviembre': 11, 'diciembre': 12,
}

# Rubro (encabezado tal como aparece en NavegacionRapida.php) -> tipo_norma_desc
# que se manda al backend. Confirmados contra ediciones reales (22235, 22238):
# DECRETOS, DECISIONES ADMINISTRATIVAS, RESOLUCIONES DELEGADAS, RESOLUCIONES,
# ACORDADAS, DISPOSICIONES. El resto (LEYES, DECRETOS-LEYES y los 3 rubros de
# Municipal) son mapeos "por las dudas", sin muestra real — ver "QUÉ FALTA
# VALIDAR" en el docstring. Cualquier rubro que NO esté acá se descarta como
# no-normativo (licitaciones, adjudicaciones, contrataciones, concesiones de
# agua, convocatorias a audiencia, notificaciones y avisos administrativos).
RUBRO_A_TIPO = {
    'DECRETOS': 'DECRETO',
    'DECISIONES ADMINISTRATIVAS': 'DECISION ADMINISTRATIVA',
    'RESOLUCIONES DELEGADAS': 'RESOLUCION DELEGADA',
    'RESOLUCIONES': 'RESOLUCION',
    'ACORDADAS': 'ACORDADA',
    'DISPOSICIONES': 'DISPOSICION',
    'LEYES': 'LEY',                        # nunca visto en las 2 muestras; por las dudas
    'DECRETOS-LEYES': 'DECRETO LEY',       # ídem
    'DECRETOS LEYES': 'DECRETO LEY',       # variante sin guion, por las dudas
    # Sección Municipal — nunca vista con contenido (la muestra la tenía
    # vacía). Mapeo por analogía con bot_mendoza.py.
    'ORDENANZAS': 'ORDENANZA',
    'DECRETOS MUNICIPALES': 'DECRETO MUNICIPAL',
    'RESOLUCIONES MUNICIPALES': 'RESOLUCION MUNICIPAL',
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


def _limpiar_numero_salta(num):
    """'443' -> '443'; '618D' -> '618D' (conserva el sufijo de "Delegada");
    '08' -> '8' (saca ceros a la izquierda sólo si es puramente numérico)."""
    n = (num or '').strip(' .')
    if n.isdigit():
        return n.lstrip('0') or '0'
    return n.upper()


def _fecha_iso(dia, mes_nombre, anio):
    mes = MESES_NUM.get(_sin_acentos((mes_nombre or '').lower()))
    if not mes:
        return None
    try:
        return datetime(int(anio), mes, int(dia)).date().isoformat()
    except ValueError:
        return None


def _url_absoluta(href):
    href = href or ''
    if href.startswith('http://') or href.startswith('https://'):
        return href
    if href.startswith('/'):
        return SITIO + href
    return f'{SITIO}/{href}'


def _quitar_prefijo_icono(texto):
    """El texto de cada <a> puede traer un ícono/flecha antes de 'N°' (no se
    pudo confirmar qué tag es sin HTML crudo). En vez de asumir nada, se
    recorta todo lo anterior a la primera 'N°'/'Nº' real."""
    m = re.search(r'N[º°]', texto or '')
    return texto[m.start():] if m else (texto or '')


# ===========================================================================
# LISTADO (NavegacionRapida.php) — el oráculo, con link a cada norma
# ===========================================================================
RE_METADATOS_EDICION = re.compile(
    r'Bolet[íi]n\s*N[º°]\s*(?P<numero>\d+)\s+Salta,\s*\w+\s+(?P<dia>\d{1,2})\s+de\s+'
    r'(?P<mes>[A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+de\s+(?P<anio>\d{4})', re.IGNORECASE)

# Encabezado de rubro: línea suelta, íntegramente en mayúsculas, que no está
# dentro de un <a>. "SECCIÓN ..." y "NO EXISTE SECCIÓN..." se excluyen aparte.
RE_RUBRO = re.compile(r'^[A-ZÁÉÍÓÚÑ0-9º°.\-\s]{4,60}$')
RE_SECCION_O_VACIO = re.compile(r'^(SECCI[ÓO]N\b|NO\s+EXISTE\b)', re.IGNORECASE)

# Patrón "con ID interno": N° <id> - Nº <numero real> DEL <fecha> - <EMISOR> - <TITULO>
RE_ITEM_CON_ID = re.compile(
    r'^N[º°]\.?\s*(?P<id_interno>\d+)\s*-\s*N[º°]\.?\s*(?P<numero>[\w./]+)\s+DEL\s+'
    r'(?P<dia>\d{2})/(?P<mes>\d{2})/(?P<anio>\d{4})\s*-\s*(?P<emisor>[^-]+?)\s*-\s*'
    r'(?P<titulo>.+)$', re.IGNORECASE)

# Patrón "directo": N° <numero> DEL <fecha> - <EMISOR> - <TITULO>
RE_ITEM_DIRECTO = re.compile(
    r'^N[º°]\.?\s*(?P<numero>[\w./]+)\s+DEL\s+(?P<dia>\d{2})/(?P<mes>\d{2})/(?P<anio>\d{4})\s*-\s*'
    r'(?P<emisor>[^-]+?)\s*-\s*(?P<titulo>.+)$', re.IGNORECASE)

# Patrón "sin número propio": N° <id> - <organismo> - <detalle>, SIN ningún
# "Nº <numero> DEL <fecha>" incrustado. Confirmado real (edición 22238,
# rubro RESOLUCIONES): "N° 100138394 - COMISIÓN DE JUSTICIA, ACUERDOS Y
# DESIGNACIONES DE LA CÁMARA DE SENADORES... - ESTABLECE FECHA PARA
# AUDIENCIA PÚBLICA..." — un anuncio de una comisión legislativa fijando
# fecha de audiencia, sin número de resolución propio (a diferencia de
# TODOS los demás ítems de rubros normativos vistos, que sí lo tienen). No
# es una norma con identidad numero/año -> se excluye a propósito. Sirve
# sólo para distinguir en el log "esto se descartó a propósito" de "esto no
# matcheó nada y puede ser un bug real del parser".
RE_ITEM_SIN_NUMERO = re.compile(r'^N[º°]\.?\s*\d+\s*-\s*.+$', re.IGNORECASE)


def parsear_listado(html):
    """[{'rubro','href','texto'}] en el orden del documento. Camina todos los
    nodos del <body> sin depender de clases CSS puntuales (ver nota en el
    docstring principal: no hubo forma de inspeccionar el HTML crudo del
    sitio en esta sesión). Regla: cualquier <a href="instrumento.php..."> es
    un ítem; cualquier texto suelto en MAYÚSCULAS que no esté dentro de un
    <a> es el rubro vigente hasta el próximo encabezado."""
    if BeautifulSoup is None:
        raise RuntimeError("Falta beautifulsoup4: pip install beautifulsoup4")
    soup = BeautifulSoup(html, 'html.parser')
    raiz = soup.body or soup
    items = []
    rubro_actual = None
    for el in raiz.descendants:
        if getattr(el, 'name', None) == 'a':
            href = el.get('href') or ''
            if 'instrumento.php' not in href:
                continue
            texto = _compacto(el.get_text(' '))
            if texto:
                items.append({'rubro': rubro_actual, 'href': href, 'texto': texto})
        elif NavigableString is not None and isinstance(el, NavigableString):
            if el.find_parent('a') is not None:
                continue
            txt = _compacto(str(el))
            if txt and RE_RUBRO.match(txt) and not RE_SECCION_O_VACIO.match(txt):
                rubro_actual = txt
    return items


def obtener_edicion(tipo1, nro_edicion):
    """Trae NavegacionRapida.php para (tipo1, nro_edicion). nro_edicion=0
    pide la última publicada. Devuelve (numero_edicion, fecha_iso, items,
    html); items=[] si la sección no se publicó esa fecha (no es error:
    p.ej. Municipal casi siempre viene vacía)."""
    url = f'{URL_NAVEGACION}?tipo1={tipo1}&nro_edicion={nro_edicion}'
    html = descargar(url)
    if not html:
        return None, None, [], html
    texto_plano = BeautifulSoup(html, 'html.parser').get_text(' ') if BeautifulSoup else html
    m = RE_METADATOS_EDICION.search(texto_plano)
    if not m:
        return None, None, [], html
    numero_edicion = m.group('numero')
    fecha_iso = _fecha_iso(m.group('dia'), m.group('mes'), m.group('anio'))
    items = parsear_listado(html)
    return numero_edicion, fecha_iso, items, html


def _dias_habiles_entre(a, b):
    """Días hábiles (Lun-Vie) estrictamente entre las fechas a y b (a <= b,
    sin incluir los extremos)."""
    if a >= b:
        return 0
    dias = 0
    cursor = a + timedelta(days=1)
    while cursor < b:
        if cursor.weekday() < 5:
            dias += 1
        cursor += timedelta(days=1)
    return dias


def resolver_edicion_por_fecha(fecha_objetivo_iso):
    """Best-effort: ver docstring principal ("--fecha ES BEST-EFFORT"). No
    hay endpoint de búsqueda por fecha confirmado; se estima el número por
    días hábiles de diferencia contra la última edición y se ajusta de a 1
    comparando la fecha real de cada candidato, hasta 15 intentos."""
    numero_actual, fecha_actual, _, _ = obtener_edicion('A', 0)
    if not numero_actual or not fecha_actual:
        return None, None
    objetivo = datetime.strptime(fecha_objetivo_iso, '%Y-%m-%d').date()
    actual = datetime.strptime(fecha_actual, '%Y-%m-%d').date()
    if objetivo == actual:
        return numero_actual, fecha_actual

    menor, mayor = (objetivo, actual) if objetivo < actual else (actual, objetivo)
    salto = _dias_habiles_entre(menor, mayor) + 1
    estimado = int(numero_actual) + (salto if objetivo > actual else -salto)

    probados = set()
    candidato = max(1, estimado)
    for _ in range(15):
        if candidato <= 0 or candidato in probados:
            break
        probados.add(candidato)
        num, fecha, _, _ = obtener_edicion('A', candidato)
        if not num or not fecha:
            candidato -= 1
            continue
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
        if fecha_dt == objetivo:
            return num, fecha
        candidato += 1 if fecha_dt < objetivo else -1
    return None, None


# ===========================================================================
# DETALLE (instrumento.php) — texto completo + emisor completo
# ===========================================================================
RE_FECHA_DATELINE = re.compile(
    r'SALTA\s*,\s*\d{1,2}\s+de\s+[A-Za-zÁÉÍÓÚáéíóúñÑ]+\s+de\s+\d\.?\d{3}', re.IGNORECASE)

# Metadato que el propio sitio genera para CUALQUIER tipo de instrumento
# (confirmado en las 9 normas reales de la corrida del 31/07/2026: Decretos y
# Decisiones dicen "Publicado en el Boletín N°...", Resoluciones/Acordadas
# dicen "Publicado en el Boletín OFICIAL N°..." — con "Oficial" de más). Es
# el ancla más confiable para saber dónde termina el menú de navegación y
# empieza el contenido real (ver obtener_detalle).
RE_PUBLICADO_EN = re.compile(
    r'Publicado\s+en\s+el\s+Bolet[íi]n\s*(?:Oficial\s*)?N[º°]', re.IGNORECASE)

# RESUELVE/DISPONE/DECRETA/DECIDE: confirmados reales. ACUERDA/ACORDARON:
# las Acordadas de la Corte de Justicia (cuerpo colegiado) usan la 3ª persona
# del PLURAL ("ACORDARON:"), no "ACUERDA:" — confirmado real en la Acordada
# 14704/26 ("DIJERON: ... Por ello ACORDARON: I. APROBAR..."). Se agregan
# RESUELVEN/DISPONEN/DECRETAN/DECIDEN por si algún otro cuerpo colegiado
# (Cámaras Legislativas, Tribunales) los usa — sin muestra real de esos.
RE_MARCA_RESOLUTIVA = re.compile(
    r'^[ \t]*(RESUELVEN?|DISPONEN?|DECRETAN?|DECIDEN?|ACUERDA|ACORDARON)\s*:?\s*$',
    re.IGNORECASE | re.MULTILINE)

RE_ARTICULO1 = re.compile(
    r'ART[ÍI]?CULO\s*(?:N[º°]\s*)?1(?!\d)\s*[ºo°]?\s*[.\-:)]+\s*'
    r'(?P<texto>[\s\S]{0,1200}?)'
    r'(?=ART[ÍI]?CULO\s*(?:N[º°]\s*)?2(?!\d)|\Z)', re.IGNORECASE)


def _recortar_menu_navegacion(texto):
    """El HTML de instrumento.php no tiene (no se pudo confirmar sin HTML
    crudo) una etiqueta propia para el contenedor de contenido, así que
    get_text() trae también el menú de navegación completo (Inicio,
    Búsquedas, Índices, Institucional...) pegado ANTES del título de la
    norma — confirmado real: las 9 normas de la corrida del 31/07/2026
    traían ~700 caracteres de menú al principio de texto_completo. Eso sólo
    se notó como bug visible en una Acordada (cuya síntesis, al no matchear
    "ARTÍCULO 1º", caía al fallback texto[:400] y traía puro menú) pero
    afectaba a las 9 por igual (texto_completo con basura adelante).

    Se recorta buscando "Publicado en el Boletín..." (metadato del sitio,
    presente en las 9 muestras reales, así que es el ancla preferida). Si no
    aparece, se avisa por stderr y se devuelve el texto tal cual — mejor
    mandar con basura adelante que romper el bot."""
    m = RE_PUBLICADO_EN.search(texto)
    if m:
        return texto[m.start():]
    return None


def obtener_detalle(href):
    """Texto completo de instrumento.php (ya sin el menú de navegación), o
    '' si falla (no corta el resto del boletín por una sola norma sin
    detalle)."""
    url = _url_absoluta(href)
    try:
        html = descargar(url)
    except RuntimeError as e:
        print(f"Aviso: instrumento.php falló para {url}: {e}", file=sys.stderr)
        return ''
    if not html:
        return ''
    texto = BeautifulSoup(html, 'html.parser').get_text('\n') if BeautifulSoup else html
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    recortado = _recortar_menu_navegacion(texto)
    if recortado is None:
        print(f"Aviso: no se encontró 'Publicado en el Boletín...' en {url}; "
              f"texto_completo puede traer el menú de navegación pegado adelante.",
              file=sys.stderr)
        return texto
    return recortado


def extraer_emisor_completo(texto_detalle, numero_esperado):
    """Nombre completo del organismo, tal como aparece en el propio cuerpo
    de instrumento.php (entre 'TIPO Nº <numero>' y 'Expte./Expediente Nº').
    Más confiable que la sigla del listado. None si no matchea (formato
    inesperado o tipo con ID interno nunca confirmado — ver "QUÉ FALTA
    VALIDAR"); en ese caso el llamador cae a la sigla del listado."""
    if not texto_detalle or not numero_esperado:
        return None
    inicio = 0
    m_fecha = RE_FECHA_DATELINE.search(texto_detalle)
    if m_fecha:
        inicio = m_fecha.end()
    # Cierre del nombre del organismo: "Expte./Expediente Nº" en Decretos/
    # Decisiones Administrativas/Resoluciones ministeriales (confirmado
    # real); pero las Resoluciones/Disposiciones de organismos autárquicos
    # (Ente Regulador, Inspección Gral. de Personas Jurídicas — patrón "con
    # ID interno" del listado) NO traen esa línea, van directo a "VISTO" —
    # confirmado real (Resolución 1219/26 y Resolución 06/2026, ninguna
    # tiene "Expediente Nº" como línea propia). Se acepta cualquiera de los
    # dos como cierre; para esos casos igual no hace falta: el listado ya
    # trae el nombre completo del organismo y ese es el fallback.
    patron = re.compile(
        r'N[º°]\.?\s*' + re.escape(numero_esperado) +
        r'\s*[\r\n]*\s*(?P<emisor>[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9.,\'"()/\s-]{4,120}?)\s*'
        r'(?:Expte\.?|Expediente|VISTO)\b', re.IGNORECASE)
    m = patron.search(texto_detalle, inicio)
    if not m:
        return None
    emisor = _compacto(m.group('emisor'))
    return emisor if len(emisor) >= 5 else None


def _sintesis_de_texto(texto):
    """Síntesis a partir del Artículo 1º, como en el resto de las
    provincias. Si no hay "ARTÍCULO 1º" (confirmado real: las Acordadas de
    la Corte de Justicia no usan artículos, numeran sus puntos con romanos
    — "ACORDARON: I. APROBAR el Anexo... II. COMUNICAR...") se cae al texto
    que sigue a la ÚLTIMA marca resolutiva encontrada, que para esas
    Acordadas ya arranca en el punto I y sirve perfectamente como síntesis.
    Sólo si tampoco hubo ninguna marca resolutiva se usan los primeros 400
    caracteres del texto (ya sin menú de navegación, gracias a
    obtener_detalle/_recortar_menu_navegacion)."""
    texto = texto or ''
    inicio = 0
    ultima_marca = None
    for m in RE_MARCA_RESOLUTIVA.finditer(texto):
        ultima_marca = m
    if ultima_marca:
        inicio = ultima_marca.end()
    m = RE_ARTICULO1.search(texto, inicio)
    if not m and inicio:
        m = RE_ARTICULO1.search(texto)
    if m:
        return _compacto(m.group('texto'))
    if inicio:
        return _compacto(texto[inicio:inicio + 500])
    return _compacto(texto[:400])


# ===========================================================================
# CLASIFICACIÓN INDIVIDUAL / GENERAL
# ===========================================================================
# Mismo set base que La Rioja/Mendoza (mismo idioma administrativo argentino),
# más 3 patrones agregados a partir de títulos reales vistos en Salta
# (renta vitalicia, retiro voluntario, "otorga beneficio").
UMBRAL_INDIVIDUAL = 3

PATRONES_INDIVIDUAL = [
    # Ojo: el TÍTULO del listado usa presente ("DESIGNA", "ACEPTA RENUNCIA")
    # pero el Artículo 1º real —que es lo que se usa como síntesis— casi
    # siempre lo redacta en INFINITIVO ("Designar...", "Aceptar... la
    # renuncia..."), confirmado real contra 623D/624D: la primera versión de
    # este bot sólo toleraba la forma refleja (-se) y el presente (-a), y
    # "Aceptar" no matcheaba ninguna de las dos -> el patrón caía a
    # `cuerpo` a mitad de puntaje en vez de `síntesis` a puntaje completo.
    # Se agrega el infinitivo (-ar) a los dos.
    (r'\bDes[íi]gn(?:[ae]se|a|ar)\b', 4, 'designación'),
    (r'\bAc[ée]pt(?:[ae]se|a|ar)\b[\s\S]{0,80}\brenuncia\b', 4, 'renuncia'),
    (r'\brenuncia\s+presentada\s+por\b', 4, 'renuncia'),
    # "Promover" es irregular (diptonga a "promuev-" sólo en presente/
    # subjuntivo, no en infinitivo) — el infinitivo necesita su propia
    # alternativa, no alcanza con agregar un sufijo a la raíz "promuev".
    (r'\b(?:Promu[ée]v[ae](?:se)?|Promover)\b', 4, 'promoción de un agente'),
    (r'\bContrato\s+de\s+Locaci[óo]n\s+de\s+Servicios\b', 3, 'contrato de personal'),
    (r'\bprestaci[óo]n\s+de\s+servicios\s+en\s+car[áa]cter\s+de\s+colaboraci[óo]n\b',
     3, 'prestación de servicios en carácter de colaboración'),
    (r'\bInstr[úu]yase\s+Sumario\s+Administrativo\b', 4, 'sumario administrativo'),
    (r'\bexoneraci[óo]n\b|\bcesant[íi]a\b', 4, 'sanción expulsiva'),
    (r'\bRecurso\s+Jer[áa]rquico\s+interpuesto\b', 3, 'recurso de un particular'),
    # Confirmado real (Decreto 449/26): el Artículo 1º intercala una cláusula
    # entre el verbo y "beneficio" ("Otórgase, a partir de la fecha de su
    # notificación, el beneficio...") — sin tolerancia de por medio, este
    # patrón no matcheaba en síntesis y cayó a mitad de puntaje por cuerpo,
    # lo que casi le hizo perder el umbral de individual a esa norma.
    (r'\bOt[oó]rg(?:[ae]se|a|ar)\b[\s\S]{0,60}\b[Bb]eneficio\b', 3, 'beneficio a una persona'),
    (r'\bRenta\s+Vitalicia\b', 3, 'renta vitalicia (beneficio individual)'),
    (r'\bretiro\s+voluntario\b|\bpase\s+a\s+situaci[óo]n\s+de\s+retiro\b', 3, 'retiro/pase a retiro'),
    (r'\bBaja\s+definitiva\b|\bJubilaci[óo]n\b', 3, 'baja / jubilación'),
    (r'\bOt[óo]rg(?:[ae]se|a|ar)\b[\s\S]{0,60}\bLicencia\b', 3, 'licencia'),
    (r'\bD\.?N\.?I\.?\s*N?[º°]?\s*[\d.]{6,}', 1, 'menciona DNI de una persona'),
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


# ===========================================================================
# EJECUCIÓN
# ===========================================================================
def _main():
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Salta.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se descubre por NavegacionRapida.php')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--numero', type=int,
                    help='edición puntual por número (prioridad sobre --fecha)')
    ap.add_argument('--fecha', metavar='AAAA-MM-DD', help='best-effort, ver docstring')
    ap.add_argument('--indice', metavar='ARCHIVO',
                    help='HTML de NavegacionRapida.php (Administrativa) ya guardado, pruebas')
    ap.add_argument('--sin-detalle', action='store_true',
                    help='no pide instrumento.php por norma (sin síntesis/emisor completo)')
    ap.add_argument('--todas', action='store_true',
                    help='muestra también las individuales, con puntaje y motivos')
    ap.add_argument('--sin-filtro', action='store_true', help='envía todo sin filtrar')
    ap.add_argument('--volcar', action='store_true', help='imprime lo reconocido y sale')
    args = ap.parse_args()

    numero_edicion = None
    fecha_boletin = None
    items_muni = []

    # ---- 1. Ubicar la edición y su listado -----------------------------------
    if args.indice:
        with open(args.indice, encoding='utf-8') as f:
            html_local = f.read()
        items_admin = parsear_listado(html_local)
        numero_edicion = 'local'
        fecha_boletin = args.fecha or 'desconocida'
        print(f"Usando índice local: {args.indice}", file=sys.stderr)
    else:
        if args.numero:
            numero_edicion, fecha_boletin, items_admin, _ = obtener_edicion('A', args.numero)
        elif args.fecha:
            numero_edicion, fecha_boletin = resolver_edicion_por_fecha(args.fecha)
            if not numero_edicion:
                salida("warning", f"No se pudo ubicar una edición para la fecha {args.fecha} "
                                  f"(búsqueda por fecha es best-effort; probar con --numero).")
            _, _, items_admin, _ = obtener_edicion('A', numero_edicion)
        else:
            numero_edicion, fecha_boletin, items_admin, _ = obtener_edicion('A', 0)

        if not numero_edicion:
            salida("warning", "No se pudo determinar la edición a procesar "
                              "(NavegacionRapida.php no devolvió el encabezado esperado).")

        print(f"Boletín Nº {numero_edicion} del {fecha_boletin}", file=sys.stderr)
        _, _, items_muni, _ = obtener_edicion('M', numero_edicion)

    # ---- 2. Filtrar por rubro conocido ---------------------------------------
    listado = []
    rubros_excluidos = {}
    for it in items_admin + items_muni:
        rubro = (it.get('rubro') or '').strip().upper()
        tipo = RUBRO_A_TIPO.get(rubro)
        if not tipo:
            rubros_excluidos[rubro] = rubros_excluidos.get(rubro, 0) + 1
            continue
        listado.append({**it, 'tipo': tipo, 'rubro': rubro})

    print(f"Administrativa+Municipal: {len(listado)} ítems en rubros normativos reconocidos.",
          file=sys.stderr)
    if rubros_excluidos:
        detalle = ', '.join(f"{r} x{c}" for r, c in sorted(rubros_excluidos.items()))
        print(f"Descartados por rubro no-normativo: {detalle}", file=sys.stderr)

    # ---- 3. Parsear cada línea (número/fecha propia/sigla/título) -----------
    normas_crudas = []
    sin_formato = 0
    for it in listado:
        texto_norm = _guiones(_quitar_prefijo_icono(it['texto']))
        m = RE_ITEM_CON_ID.match(texto_norm) or RE_ITEM_DIRECTO.match(texto_norm)
        if not m:
            if RE_ITEM_SIN_NUMERO.match(texto_norm):
                # No es un bug de parseo: es un ítem sin número propio de
                # norma (ver RE_ITEM_SIN_NUMERO), se descarta a propósito.
                print(f"  excluido, sin número propio de norma [{it['rubro']}]: "
                      f"{texto_norm[:110]!r}", file=sys.stderr)
            else:
                sin_formato += 1
                print(f"  sin formato [{it['rubro']}]: {texto_norm[:120]!r}", file=sys.stderr)
            continue
        gd = m.groupdict()
        normas_crudas.append({
            'tipo': it['tipo'], 'rubro': it['rubro'],
            'numero': _limpiar_numero_salta(gd['numero']), 'anio': gd['anio'],
            'fecha': f"{gd['anio']}-{gd['mes']}-{gd['dia']}",
            'emisor_abrev': _compacto(gd['emisor']), 'titulo': _compacto(gd['titulo']),
            'href': it['href'],
        })
    if sin_formato:
        print(f"Aviso: {sin_formato} ítems normativos no matchearon ninguno de los 2 "
              f"formatos de línea conocidos y se descartaron.", file=sys.stderr)

    if args.volcar:
        for n in normas_crudas:
            print(f"  [{n['rubro']}] {n['tipo']:24s} {n['numero']:>8s}/{n['anio']} "
                  f"{n['emisor_abrev'][:25]:25s} {n['titulo'][:60]}", file=sys.stderr)
        salida("success", f"volcado: {len(normas_crudas)} normas reconocidas "
                          f"({len(rubros_excluidos)} rubros no-normativos descartados).")

    # ---- 4. Detalle (texto completo, emisor completo, síntesis) -------------
    normas = []
    sin_detalle = 0
    for n in normas_crudas:
        texto_completo = ''
        emisor_completo = None
        if not args.sin_detalle:
            texto_completo = obtener_detalle(n['href'])
            if texto_completo:
                emisor_completo = extraer_emisor_completo(texto_completo, n['numero'])
            else:
                sin_detalle += 1
        n['texto_completo'] = texto_completo
        n['sintesis'] = _sintesis_de_texto(texto_completo) if texto_completo else n['titulo']
        n['emisor'] = emisor_completo or n['emisor_abrev'] or 'PODER EJECUTIVO'
        n['url_norma'] = _url_absoluta(n['href'])
        normas.append(n)
    if sin_detalle:
        print(f"Aviso: {sin_detalle} normas no trajeron detalle de instrumento.php (se "
              f"mandan igual, con el título del listado como síntesis y la sigla abreviada "
              f"como emisor).", file=sys.stderr)

    # ---- 5. Clasificación -----------------------------------------------------
    for n in normas:
        n['es_individual'], n['puntaje'], n['motivos'] = clasificar_norma(
            n['tipo'], n['sintesis'], n['texto_completo'] or n['titulo'])

    generales = [n for n in normas if not n['es_individual']]
    individuales = [n for n in normas if n['es_individual']]
    a_enviar = normas if args.sin_filtro else generales

    guardar_debug(json.dumps(normas, ensure_ascii=False, indent=2, default=str), 'debug_salta.json')
    print(f"Boletín Nº {numero_edicion} del {fecha_boletin} | normas: {len(normas)} "
          f"(generales {len(generales)} / individuales {len(individuales)})", file=sys.stderr)

    if args.dry_run:
        for n in (normas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {n['tipo']:24s} N° {n['numero']:>8s}/{n['anio']} "
                  f"{n['emisor'][:30]:30s} {n['sintesis'][:55]}", file=sys.stderr)
            if args.todas and n.get('motivos'):
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    fecha_valida = fecha_boletin and fecha_boletin != 'desconocida'

    if fecha_valida and verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

    if not normas:
        if fecha_valida:
            registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Sin novedades: el boletín Nº {numero_edicion} del {fecha_boletin} "
                          f"no publicó normativa en Administrativa/Municipal.", total=0)

    if not a_enviar:
        if fecha_valida:
            registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Se procesó el boletín Nº {numero_edicion}, pero las "
                          f"{len(individuales)} normas encontradas son actos individuales; "
                          f"no se envió ninguna.", total=0)

    # ---- 6. Envío ---------------------------------------------------------------
    payload = [{
        "id_jurisdiccion": args.id_jurisdiccion,
        "nombre_emisor": n['emisor'],
        "tipo_norma_desc": n['tipo'],
        "numero": n['numero'],
        "anio": n['anio'],
        "fecha_publicacion": n['fecha'],
        "sintesis": construir_sintesis(n),
        "texto_completo": recortar_texto(n['texto_completo'] or n['titulo']),
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
        salida("error", str(e))