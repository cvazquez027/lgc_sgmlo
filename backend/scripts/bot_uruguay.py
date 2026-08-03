#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
 DIARIO OFICIAL DE URUGUAY (IMPO)
 id_jurisdiccion 29
===============================================================================

FUENTE — CONFIRMADA REAL ESTA SESIÓN
-------------------------------------------------------------------------------
https://www.impo.com.uy/diariooficial -- página con visor de PDF embebido y
un combo "Sección" (Indice, Documentos, Avisos, Ultimo Momento, Separata). La
página en sí es una shell JS (Blazor-like) que un fetch simple no renderiza
-- pero el visor arma la URL del PDF con un patrón fijo, confirmado real
contra varias fechas/secciones:

    https://www.impo.com.uy/diariooficial/{AAAA}/{MM}/{DD}/{seccion}.pdf

{seccion} in {documentos, avisos, indice, ultimomomento, separata}.

SECCIONES — CONFIRMADO REAL CONTRA 03/08/2026 (hoy) Y 02/08/2026 (domingo)
-------------------------------------------------------------------------------
- documentos.pdf: normativa oficial (Decretos, Leyes, Resoluciones) --
  ÚNICA sección que este bot procesa. Confirmado real: texto nativo
  extraíble (NO escaneado/OCR, a diferencia de Tierra del Fuego/San Luis/
  Misiones), 5 actos reales el 03/08/2026.
- avisos.pdf: avisos judiciales/privados (sucesiones, edictos de Juzgados
  de Familia) -- FUERA DE ALCANCE, mismo criterio que el resto de la
  familia (sólo normativa oficial, nunca avisos de terceros). Confirmado
  real por contenido ("Los señores Jueces Letrados de Familia han
  dispuesto la apertura de las Sucesiones...", con códigos de tasa de
  publicación tipo "01) $ 8428 10/p...").
- indice.pdf: existe como archivo pero devolvió "sin texto extraíble" el
  03/08/2026 -- no se usa (alcanza con documentos.pdf).
- ultimomomento.pdf / separata.pdf: confirmado real que NO existen para
  una fecha normal (Content-Type text/plain vacío, ver más abajo) --
  parecen secciones ocasionales/suplementarias, no parte del ciclo diario.
  No se procesan.

SEÑAL REAL DE "SIN EDICIÓN ESTA FECHA" -- confirmado con un domingo real
-------------------------------------------------------------------------------
Un PDF real siempre viene con Content-Type "application/pdf". Cuando no hay
edición para una fecha/sección (confirmado real: documentos.pdf del
02/08/2026, un domingo), la respuesta es Content-Type "text/plain" con
cuerpo VACÍO -- señal limpia y reutilizable, análoga en espíritu al
mes-sin-carpeta de Tierra del Fuego pero a nivel día (ver
"DESCUBRIMIENTO: SIEMPRE LA ÚLTIMA EDICIÓN DISPONIBLE" más abajo).

ARQUITECTURA: sin clasificación local (mismo criterio que bot_nacion.py / bot_tucuman.py)
-------------------------------------------------------------------------------
Igual que Tucumán: texto nativo (no hay incertidumbre de OCR que amerite un
filtro de confianza local), así que se manda TODO lo reconocido en
"documentos.pdf" tal cual, con los campos ya resueltos, y se deja que
NormativaHelper.php (backend) categorice/deduplique.

DESCUBRIMIENTO: SIEMPRE LA ÚLTIMA EDICIÓN DISPONIBLE -- día a día
-------------------------------------------------------------------------------
A diferencia de Tucumán (sólo expone "la edición de hoy", sin respaldo) y
siguiendo el mismo criterio que Tierra del Fuego (mes a mes) pero a nivel
día: se intenta documentos.pdf de fecha_objetivo (por default hoy) y, si la
respuesta confirma "sin edición" (text/plain vacío -- fin de semana, feriado,
etc.), se prueba el día anterior, hasta MAX_DIAS_ATRAS. Un error de red/HTTP
genuino (no la señal "sin edición") NO se confunde con "sin edición" -- se
distingue a propósito (ver _descargar_seccion) para no ocultar una caída real
del sitio caminando hacia atrás y reportando una fecha vieja como si fuera
normal.

ESTRUCTURA REAL DE "DOCUMENTOS" -- confirmado contra la edición completa del 03/08/2026 (837 líneas de texto, 5 actos)
-------------------------------------------------------------------------------
Mapa real de actos de la edición usada como universo de prueba (via
grep de "^(Decreto|Ley|Resolución) numero$"):

    1. Decreto 171/026            (VISTO/RESULTANDO/CONSIDERANDO/ATENTO)
    2. Ley 20.509                 (Poder Legislativo, sin VISTO/CONSIDERANDO)
    3. Decreto 162/026            (VISTO/RESULTANDO/CONSIDERANDO/ATENTO)
    4. Resolución 1.016/026       (tabular -- ver más abajo, sin VISTO/DECRETA)
    5. Ley 20.508                 (Poder Legislativo, con anexo MdE Suiza)

Ruido de página repetido (encabezado/pie), confirmado en TODA la edición:
"DiarioOficial | Nº 31.969 - agosto 3 de 2026 Documentos {N}" y su variante
espejada "{N} Documentos Nº 31.969 - agosto 3 de 2026 | DiarioOficial" --
en los 2 casos contiene literalmente "DiarioOficial", nunca visto ese texto
dentro del cuerpo real de un acto -- por eso _limpiar_ruido_paginas saca
cualquier línea que lo contenga, sin necesidad de armar el numero de
edición/fecha en el propio regex (que cambiaría cada día).

Cada acto real observado sigue el patrón (confirmado en los 5 casos):
    " {N}"                       <- marca de ítem suelta en el margen (se ignora)
    "{Tipo} {numero}"            <- divisor real (ver RE_ACTO)
    "{síntesis oficial pre-escrita, 1-3 líneas}"
    "({código registro IMPO})"   <- ej. "(3.005*R)", "(3.167)" -- interno,
                                     NUNCA confundir con el numero del acto
    ... cuerpo ...

HALLAZGO CLAVE: la síntesis YA viene pre-escrita en la fuente
-------------------------------------------------------------------------------
A diferencia de Tucumán (donde hubo que derivar la síntesis heurísticamente
del CONSIDERANDO, con 3 bugs reales en el camino), acá la línea entre
"{Tipo} {numero}" y el código de registro "(N.NNN)" es un resumen oficial
corto YA escrito por IMPO -- confirmado real en los 5 actos de hoy (ej.
"Dispónese la reglamentación de los criterios para la percepción de la
partida asignada por el art. 598 de la Ley 20.446..."). _sintesis sólo
recorta esa línea, no hace falta ninguna heurística de CONSIDERANDO.

NUMERO / ANIO -- dos formatos reales confirmados, sin partir "numero" (mismo criterio que Tucumán: "dejarlo tal cual")
-------------------------------------------------------------------------------
- Decreto/Resolución: "NNN/0YY" (ej. "171/026", "1.016/026") -- el año
  20YY se deriva de los últimos 2 dígitos tras la barra (ver
  _anio_desde_numero). numero se guarda TAL CUAL ("171/026"), sin partir
  el sufijo -- mismo criterio ya confirmado con el usuario para Tucumán
  (numero puede traer su propio "/algo" con significado propio, no hay
  necesidad de adivinar/partir).
- Ley: "NN.NNN" (ej. "20.509", "20.508") -- SIN año embebido (numeración
  correlativa desde el origen). El año sale de la fecha propia del acto
  (ver _fecha_acto), con respaldo la fecha de la edición.

FECHA PROPIA DEL ACTO -- "Montevideo, DD de MES de YYYY"
-------------------------------------------------------------------------------
Confirmado real en los 2 Decretos y en la Ley 20.509 (fecha de
promulgación del Poder Ejecutivo, la de "Cúmplase..." -- NO la fecha de
"Sala de Sesiones..." del Congreso, que también aparece en las Leyes pero
antes, con formato distinto "en Montevideo, a {D} de {mes} de {AAAA}." --
RE_FECHA_MONTEVIDEO matchea ambas formas, se usa la que aparezca; en la
práctica sólo se vio 1 "Montevideo," con este formato exacto en las Leyes,
la del Cúmplase). Si el acto no trae ninguna fecha propia reconocible
(confirmado real: la Resolución 1.016/026 tabular no tiene ninguna,
"Notifícase..." directo sin fórmula VISTO/CONSIDERANDO) se usa la fecha de
la edición como respaldo.

CASO REAL DISTINTO: RESOLUCIÓN TABULAR (Policía Caminera)
-------------------------------------------------------------------------------
La Resolución 1.016/026 (DIRECCIÓN NACIONAL DE POLICÍA CAMINERA) NO sigue
el patrón VISTO/CONSIDERANDO/DECRETA-o-RESUELVE -- es una notificación
("Notifícase a los propietarios de los vehículos...") seguida de una TABLA
larga (cientos de filas: Matrícula/País/Fecha y Hora/Intersección/
Intervenido/Artículo/Valor en UR), sin verbo operativo reconocible. Esto
NO rompe el divisor de actos (RE_ACTO sigue encontrando el próximo "{Tipo}
{numero}" real después de la tabla entera, confirmado real: encontró "Ley
20.508" justo después de ~366 líneas de tabla) ni la síntesis (la línea
oficial corta sigue estando en el mismo lugar, antes del código de
registro). Sólo afecta el EMISOR: como no hay DECRETA/RESUELVE, _emisor
cae al respaldo "encabezado_previo" (la línea "DIRECCIÓN NACIONAL DE
POLICÍA CAMINERA" que precede al acto en el propio texto) en vez del
verbo operativo. texto_completo para este caso puede ser muy largo (la
tabla entera) -- se apoya en recortar_texto (mismo tope 20.000 caracteres
que el resto de la familia) para no mandar un payload gigante; no se armó
un parser de tabla dedicado (no parece prioritario: el interés real está
en Decretos/Leyes/Resoluciones normativas, no en listados de infracciones
de tránsito).

BUG REAL ENCONTRADO EN LA PRIMERA CORRIDA REAL COMPLETA DEL USUARIO (VPS, 29 "actos" -> 31 reales)
-------------------------------------------------------------------------------
El usuario corrió el bot contra la edición completa real del 03/08/2026
(no la muestra truncada de 837 líneas usada para diseñar la primera
versión) y encontró 29 "actos", de los cuales 18 eran correctos (los 5 ya
conocidos + 3 Decretos más + 9 Resoluciones de A.S.S.E. -- todos con
campos razonables, confirmando que el diseño generaliza bien a actos
nuevos) pero 11 eran basura: "DECRETO N° 81/014 (2014)" repetido 11
veces, con emisor/sintesis siendo fragmentos crudos de fila de tabla
("4.4.2 Conducir manipulando teléfono celular- 3 B141927 2026-07-28
09:41 DE VIANA JOSE JOAQUIN...").

Diagnóstico real (con el debug_uruguay.json real que subió el usuario):
la edición completa trae, después de la última Resolución de A.S.S.E.,
un tramo largo de NOTIFICACIONES DE MULTAS DE TRÁNSITO de varias
Intendencias departamentales (Maldonado/Departamento de Movilidad,
y otras) -- 13 actos reales del tipo "Notificación NNN/026" (ej.
"Notificación 137/026", confirmado real: mismo patrón de sintesis +
código de registro que Decreto/Ley/Resolución -- "Notifícase a los
propietarios de los vehículos... (3.161) INTENDENCIA DE MALDONADO..."),
un 4º tipo real no visto en la muestra original. Como RE_ACTO sólo
reconocía Decreto/Ley/Resolución, estas 13 Notificaciones NUNCA se
reconocían como divisor -- todo ese tramo (cientos de miles de
caracteres, varias tablas de infracciones concatenadas) quedaba
colgado como cuerpo de la última Resolución real anterior (A.S.S.E.
3.475/026). Dentro de ese cuerpo gigante, una fila de infracción
específica ("4.4.2 Conducir manipulando teléfono celular") cita su base
legal en su propia línea, "Decreto 81/014" -- que sí matcheaba RE_ACTO
(mayúscula + "Decreto" + numero con forma NNN/NNN) y generaba un divisor
falso cada vez que esa infracción se repetía en la tabla (11 veces
reales).

Arreglo (2 partes, ver RE_ACTO y VENTANA_VALIDACION_CODIGO):
(1) se agregó "Notificación" a los tipos reconocidos por RE_ACTO -- con
esto los 13 actos reales de este tramo pasan a reconocerse como deben.
(2) además, cualquier candidato de RE_ACTO (de cualquier tipo, no sólo
Decreto) sólo se acepta como divisor real si su propio código de
registro "(N.NNN)" aparece cerca (VENTANA_VALIDACION_CODIGO, 1000
caracteres) -- confirmado real contra los 18 actos ya conocidos (código
siempre dentro de los primeros ~300 caracteres) y contra las 11 citas
"Decreto 81/014" (ninguna tiene un código real cerca) -- esto rechaza
tanto esta cita puntual como cualquier otra cita legal suelta con la
misma forma que pueda aparecer dentro de una tabla en el futuro (mismo
espíritu que el arreglo de "número cruzado de citas internas" de Tierra
del Fuego, pero acá aplicado al DIVISOR de actos, no sólo a un campo).

EMISOR -- del verbo operativo, NUNCA del encabezado de sección (confirmado real, caso Ley 20.509)
-------------------------------------------------------------------------------
Hallazgo real importante: el encabezado de sección que antecede a un acto
NO siempre es su emisor real. Ejemplo confirmado: "Ley 20.509" aparece
justo debajo del encabezado "MINISTERIO DE DEFENSA NACIONAL", pero su
propio texto dice "PODER LEGISLATIVO / El Senado y la Cámara de
Representantes de la República Oriental del Uruguay, reunidos en Asamblea
General, DECRETAN" -- el emisor real es el Poder Legislativo, no ese
Ministerio (que sólo resulta ser el primer refrendante/firmante del
Cúmplase). Por eso _emisor busca el texto INMEDIATAMENTE antes del verbo
operativo (DECRETA/DECRETAN/RESUELVE/RESUELVEN -- estos 2 últimos por
analogía con el resto de la familia, ej. Tucumán, no confirmados todavía
con un ejemplo real de Uruguay, ver "QUÉ FALTA VALIDAR"), recortando
cualquier cláusula VISTO:/RESULTANDO:/CONSIDERANDO:/ATENTO: que haya
quedado arrastrada en la ventana de búsqueda (ver RE_LIMITE_EMISOR y BUG
evitado más abajo). Si no hay verbo operativo reconocible (caso de la
Resolución tabular) se cae al encabezado que antecede al acto en el
propio texto; de última instancia, un genérico "PODER EJECUTIVO".

BUG EVITADO (encontrado en mi propia revisión antes de mostrar el bot, sin corrida real todavía)
-------------------------------------------------------------------------------
Un primer intento de _emisor buscaba "cualquier texto en mayúscula antes
del verbo, hasta 180 caracteres atrás" -- contra el Decreto 171 real esto
agarraba de más: "ATENTO: a lo dispuesto por el artículo 168 numeral 4º de
la Constitución de la República; EL PRESIDENTE DE LA REPÚBLICA actuando en
Consejo de Ministros" (la cláusula ATENTO completa, pegada al emisor real)
porque "ATENTO" también empieza con mayúscula y entraba en la ventana de
180 caracteres. Corregido: se toma una ventana más generosa (400
caracteres) y LUEGO se recorta todo lo que quede antes de la última
cláusula VISTO:/RESULTANDO:/CONSIDERANDO:/ATENTO: reconocida dentro de esa
ventana (o antes del código de registro "(N.NNN)" si no hay ninguna
cláusula, caso de las Leyes) -- así sólo sobrevive el texto pegado
inmediatamente antes del verbo. Contra los 3 casos reales con verbo
operativo (Decreto 171, Decreto 162, Ley 20.509) da: "EL PRESIDENTE DE LA
REPÚBLICA actuando en Consejo de Ministros" (los 2 Decretos) y "PODER
LEGISLATIVO El Senado y la Cámara de Representantes de la República
Oriental del Uruguay, reunidos en Asamblea General," (la Ley) -- ningún
caso arrastra ya la cláusula ATENTO.

QUÉ FALTA VALIDAR (real, pendiente)
-------------------------------------------------------------------------------
- RESUELVE/RESUELVEN como verbo operativo: sólo se confirmó DECRETA/
  DECRETAN en los ejemplos reales de hoy (2 Decretos + 2 Leyes); la única
  Resolución real vista (1.016/026) es la tabular sin verbo. Se incluye
  RESUELVE/RESUELVEN por analogía con el resto de la familia (Tucumán,
  donde sí está confirmado), pero falta un ejemplo real de Uruguay que lo
  ejercite.
- Tipos de acto más allá de Decreto/Ley/Resolución/Notificación (ej.
  Acordada, Disposición) -- no vistos todavía. RE_ACTO sólo reconoce
  estos 4 a propósito (evitar falsos positivos con un patrón demasiado
  genérico); ampliar cuando aparezca un ejemplo real.
- Notificación: sólo se validó que se RECONOCE bien como acto (13 actos
  reales, división correcta -- ver "BUG REAL ENCONTRADO EN LA PRIMERA
  CORRIDA REAL COMPLETA"), con emisor por encabezado_previo (nunca tienen
  DECRETA/RESUELVE). encabezado_previo sólo toma 1 línea hacia atrás
  (ver _dividir_actos) -- confirmado real que el encabezado completo de
  una Notificación puede ser 2 líneas ("INTENDENCIA DE MALDONADO" +
  "DEPARTAMENTO DE MOVILIDAD"), y sólo se captura la más cercana
  ("DEPARTAMENTO DE MOVILIDAD"), perdiendo el organismo padre -- aceptado
  a propósito (ver docstring de _dividir_actos: tomar 2 líneas arrastra
  la firma del acto ANTERIOR en los otros casos reales confirmados, ej.
  Ley 20.509 y Resolución 1.016/026, un problema peor).
- VENTANA_VALIDACION_CODIGO (1000 caracteres): calibrada contra los 18
  actos reales confirmados (código siempre dentro de los primeros ~300
  caracteres) y las 11 citas "Decreto 81/014" reales (ninguna con código
  cerca). Un acto real con una síntesis oficial inusualmente larga
  (>1000 caracteres antes de su propio código de registro) se
  rechazaría por error -- no visto todavía, ningún ejemplo real supera
  los 297 caracteres.
- Texto real de "Decreto 81/014" y su fila de tabla: el debug_uruguay.json
  que compartió el usuario ya tiene ese texto separado como "acto" (el
  bug se detectó y corrigió ANTES de poder guardar el texto crudo previo
  a la división) -- el arreglo se validó con el resto de los actos
  reales de esa corrida (confirmando que el código de registro SÍ
  aparece cerca de todos los actos reales y no cerca de esta cita en
  particular, ver arriba), pero no con una re-corrida real posterior
  a este arreglo todavía.
- Fecha propia de la Ley 20.508: el texto capturado esta sesión llega
  truncado a mitad del anexo (Memorando de Entendimiento con Suiza, un
  límite del tamaño de respuesta de la herramienta de investigación usada
  esta sesión, NO una limitación del bot real -- el bot real lee los bytes
  completos del PDF vía fitz, no pasa por ese límite) -- no se pudo
  confirmar su propia línea "Montevideo, fecha" de Cúmplase dentro de la
  muestra; en ese caso concreto _fecha_acto cae al respaldo (fecha de la
  edición), que puede no coincidir exactamente con la fecha real de
  promulgación (confirmado real en la Ley 20.509 que sí se pudo ver
  completa: promulgada 10/07/2026, publicada recién el 03/08/2026 --
  ~3 semanas de diferencia real entre firma y publicación).
- Sólo 1 tabla real vista (Resolución 1.016/026) -- sin confirmar que el
  divisor de actos siga andando bien si una tabla de este tipo contuviera,
  por azar, texto que matchee "{Tipo} {numero}" en alguna celda (no
  ocurrió en el ejemplo real disponible: son patentes/fechas/artículos,
  ninguna celda tiene forma "Decreto NNN/NNN").
- indice.pdf: no se investigó si en otras fechas sí trae contenido útil
  (hoy vino "sin texto extraíble") -- por ahora no se usa, confirmado con
  el usuario que alcanza con "Documentos".
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
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ===========================================================================
# CONFIGURACIÓN (mismo contrato que el resto de la familia)
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

BASE_URL_URUGUAY = get_env_clean('BASE_URL_URUGUAY', 'https://www.impo.com.uy/diariooficial')
# Ver docstring "DESCUBRIMIENTO: SIEMPRE LA ÚLTIMA EDICIÓN DISPONIBLE" --
# cuántos días hacia atrás probar si la fecha objetivo (por default, hoy)
# no tiene edición de "Documentos" (fin de semana/feriado), antes de darse
# por vencido.
MAX_DIAS_ATRAS = 10

REINTENTOS = 3
ESPERA_REINTENTO = 3
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700


# ===========================================================================
# NORMALIZACIÓN
# ===========================================================================
def _compacto(texto):
    return re.sub(r'\s+', ' ', (texto or '')).strip()


def _sin_acentos(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


MESES_ES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'setiembre': 9, 'septiembre': 9, 'octubre': 10,
    'noviembre': 11, 'diciembre': 12,
}


# ===========================================================================
# DESCARGA — ver docstring "SEÑAL REAL DE 'SIN EDICIÓN ESTA FECHA'"
# ===========================================================================
def _descargar_seccion(fecha, seccion):
    """(contenido_bytes, hubo_edicion) para {seccion}.pdf de la fecha dada.
    hubo_edicion=False + contenido=None -> CONFIRMADO que no hay edición
    para esa fecha/sección (respuesta text/plain vacía, ver docstring --
    señal real confirmada contra un domingo real). hubo_edicion=True +
    contenido=bytes -> PDF real (application/pdf). Levanta RuntimeError si
    tras REINTENTOS intentos no se pudo determinar ninguno de los dos
    casos (error de red/HTTP genuino) -- se distingue a propósito de "sin
    edición" para no confundir una caída real del sitio con un día sin
    publicación (ver _buscar_edicion_documentos)."""
    url = f'{BASE_URL_URUGUAY}/{fecha.year:04d}/{fecha.month:02d}/{fecha.day:02d}/{seccion}.pdf'
    ultimo_error = None
    for intento in range(1, REINTENTOS + 1):
        try:
            r = requests.get(url, timeout=30)
            ctype = r.headers.get('Content-Type', '')
            if r.status_code == 200 and ctype.startswith('application/pdf'):
                return r.content, True
            if ctype.startswith('text/plain'):
                return None, False
            ultimo_error = f'HTTP {r.status_code}, Content-Type={ctype!r}'
        except requests.RequestException as e:
            ultimo_error = str(e)
        if intento < REINTENTOS:
            time.sleep(ESPERA_REINTENTO * intento)
    raise RuntimeError(f"No se pudo determinar el estado de {url} tras {REINTENTOS} "
                       f"intentos ({ultimo_error}).")


def _buscar_edicion_documentos(fecha_objetivo):
    """(fecha_encontrada, pdf_bytes) de la última edición real de
    'Documentos' disponible, empezando en fecha_objetivo y probando hacia
    atrás día a día hasta MAX_DIAS_ATRAS (ver docstring "DESCUBRIMIENTO:
    SIEMPRE LA ÚLTIMA EDICIÓN DISPONIBLE"). (None, None) si se agotó el
    rango sin encontrar ninguna edición real."""
    fecha = fecha_objetivo
    for _ in range(MAX_DIAS_ATRAS):
        contenido, hubo_edicion = _descargar_seccion(fecha, 'documentos')
        if hubo_edicion:
            if fecha != fecha_objetivo:
                print(f"Aviso: 'Documentos' sin edición para {fecha_objetivo.isoformat()}; "
                      f"se usa la última real disponible: {fecha.isoformat()}.", file=sys.stderr)
            return fecha, contenido
        fecha -= timedelta(days=1)
    print(f"Aviso: no se encontró ninguna edición de 'Documentos' en los últimos "
          f"{MAX_DIAS_ATRAS} días hacia atrás desde {fecha_objetivo.isoformat()}.", file=sys.stderr)
    return None, None


def _extraer_texto_pdf(pdf_bytes):
    """Texto nativo completo del PDF (get_text por página, unidas con
    salto de línea) -- ver docstring "FUENTE" (texto nativo, sin OCR)."""
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    try:
        return '\n'.join(page.get_text('text') for page in doc)
    finally:
        doc.close()


# ===========================================================================
# LIMPIEZA DE RUIDO DE PÁGINA — ver docstring "ESTRUCTURA REAL DE DOCUMENTOS"
# ===========================================================================
def _limpiar_ruido_paginas(texto):
    """Saca las líneas de encabezado/pie de página repetidas en cada
    página real -- confirmado real: siempre contienen literalmente
    "DiarioOficial", nunca visto ese texto dentro del cuerpo real de un
    acto."""
    lineas = (texto or '').split('\n')
    return '\n'.join(l for l in lineas if 'DiarioOficial' not in l)


# ===========================================================================
# DIVISIÓN EN ACTOS — ver docstring "ESTRUCTURA REAL DE DOCUMENTOS"
# ===========================================================================
# 4 tipos reales confirmados (Decreto/Ley/Resolución esta sesión + el
# usuario corrió el bot real completo en su VPS y encontró "Notificación"
# -- ver "BUG REAL: CITA LEGAL DENTRO DE TABLA..." más abajo). Ver
# docstring "QUÉ FALTA VALIDAR" para ampliar cuando aparezca un ejemplo
# real de otro tipo (Acordada, Disposición, etc.).
RE_ACTO = re.compile(
    r'^[ \t]*(Decreto|Ley|Resoluci[oó]n|Notificaci[oó]n)\s+([\d][\d./]*)[ \t]*$',
    re.IGNORECASE | re.MULTILINE)

# BUG REAL (corrida real completa del usuario en su VPS, 29 "actos"
# encontrados contra 31 reales -- ver docstring "BUG REAL: CITA LEGAL
# DENTRO DE TABLA CONFUNDIDA CON UN ACTO"): dentro de una tabla larga de
# infracciones de tránsito (Notificación, ver arriba), la fila de la
# infracción "4.4.2 Conducir manipulando teléfono celular" cita su base
# legal "Decreto 81/014" en su propia línea -- matchea RE_ACTO igual que
# un acto real (mayúscula + "Decreto" + numero con forma NNN/NNN), pero
# NO es un acto real: es una cita dentro de una fila de tabla, repetida
# tantas veces como esa infracción aparece (11 veces reales en la corrida
# del usuario, partiendo lo que debería ser un solo tramo de Notificación
# en 11 pedazos falsos con "emisor" y "sintesis" basura -- fragmentos
# crudos de fila de tabla). Confirmado real: LOS 18 actos reales de esa
# misma corrida (Decreto/Ley/Resolución) tienen su código de registro
# "(N.NNN)" (ver RE_CODIGO_REGISTRO) dentro de los primeros ~300
# caracteres; NINGUNA de las 11 citas "Decreto 81/014" tiene un código de
# registro real cerca (confirmado con los datos reales de esa corrida).
# Arreglo: un candidato de RE_ACTO sólo cuenta como divisor real si su
# propio código de registro aparece dentro de esta ventana -- si no,
# se descarta (el texto sigue siendo parte del acto anterior).
VENTANA_VALIDACION_CODIGO = 1000

# BUG REAL evitado (encontrado con el debug_uruguay.json real de esta misma
# corrida, antes de mostrar el arreglo): "encabezado_previo" como "la línea
# no vacía inmediatamente antes" funciona para Ley 20.509/Resolución
# 1.016/026 (donde el encabezado real está pegado, 1 línea antes) pero NO
# para una Notificación real cuya agencia YA fue anunciada por un acto
# anterior de la MISMA agencia y el PDF no vuelve a repetir el encabezado
# -- confirmado real: "Notificación 1.050/026" (misma agencia que la
# Resolución 1.016/026 justo antes, Dirección Nacional de Policía
# Caminera) viene precedida por la FIRMA de esa Resolución anterior
# ("Helio Neves, Subdirector.\n27/07/2026"), no por un encabezado nuevo --
# tomar "la línea de antes" a ciegas daba encabezado_previo="27/07/2026"
# (una fecha, inútil como emisor). Arreglo: en vez de mirar sólo 1 línea
# atrás, se recorre el documento UNA vez identificando líneas con forma de
# encabezado institucional real (empiezan con una palabra conocida --
# PODER/MINISTERIO/INTENDENCIA/DEPARTAMENTO/DIRECCIÓN/ADMINISTRACIÓN/etc.,
# ver RE_ENCABEZADO_INSTITUCIONAL -- confirmado que cubre los 9 encabezados
# reales vistos esta sesión) y a cada acto se le asigna el ÚLTIMO visto
# antes de su propio inicio, sin importar cuántas líneas de tabla/firma
# haya en el medio -- así una Notificación sin encabezado propio hereda
# correctamente el de la última agencia real anunciada (acá, "DIRECCIÓN
# NACIONAL DE POLICÍA CAMINERA"). Cuando 2 líneas institucionales aparecen
# pegadas (confirmado real: "INTENDENCIA DE MALDONADO" seguida
# directamente por "DEPARTAMENTO DE MOVILIDAD") se combinan en 1 solo
# string -- más descriptivo que quedarse sólo con la más cercana.
RE_ENCABEZADO_INSTITUCIONAL = re.compile(
    r'^(PODER|MINISTERIO|INTENDENCIA|DEPARTAMENTO|DIRECCI[OÓ]N|ADMINISTRACI[OÓ]N|'
    r'CONSEJO|JUNTA|COMISI[OÓ]N|INSTITUTO|OFICINA|SECRETAR[IÍ]A)\b.*$',
    re.MULTILINE)


def _encabezados_institucionales(texto_limpio):
    """[(offset, texto), ...] de los encabezados institucionales reales
    del documento, en orden de aparición -- ver comentario arriba de
    RE_ENCABEZADO_INSTITUCIONAL."""
    crudos = list(RE_ENCABEZADO_INSTITUCIONAL.finditer(texto_limpio))
    combinados = []
    i = 0
    while i < len(crudos):
        offset = crudos[i].start()
        partes = [crudos[i].group(0).strip()]
        fin_actual = crudos[i].end()
        j = i + 1
        while j < len(crudos) and not texto_limpio[fin_actual:crudos[j].start()].strip():
            partes.append(crudos[j].group(0).strip())
            fin_actual = crudos[j].end()
            j += 1
        combinados.append((offset, ' - '.join(partes)))
        i = j
    return combinados


def _dividir_actos(texto_limpio):
    """[{'tipo_crudo', 'numero', 'encabezado_previo', 'cuerpo'}, ...] --
    parte texto_limpio en los puntos donde matchea RE_ACTO Y además pasa
    la validación de "tiene código de registro cerca" (ver
    VENTANA_VALIDACION_CODIGO -- descarta citas legales sueltas dentro de
    tablas, confirmado real). Confirmado real: este divisor encuentra
    bien el próximo acto incluso después de una tabla larga de cientos de
    líneas (ver docstring, caso Resolución 1.016/026 -> Ley 20.508).
    'encabezado_previo' es el último encabezado institucional real visto
    antes del match (ver _encabezados_institucionales) -- candidato a
    emisor de respaldo cuando el cuerpo no tiene verbo operativo
    reconocible (ver _emisor; caso real más común: Notificación, que
    nunca tiene DECRETA/RESUELVE)."""
    candidatos = list(RE_ACTO.finditer(texto_limpio))

    validos = []
    for i, m in enumerate(candidatos):
        limite = candidatos[i + 1].start() if i + 1 < len(candidatos) else len(texto_limpio)
        ventana_fin = min(m.end() + VENTANA_VALIDACION_CODIGO, limite)
        if RE_CODIGO_REGISTRO.search(texto_limpio[m.end():ventana_fin]):
            validos.append(m)

    encabezados = _encabezados_institucionales(texto_limpio)

    actos = []
    for i, m in enumerate(validos):
        fin = validos[i + 1].start() if i + 1 < len(validos) else len(texto_limpio)
        cuerpo = texto_limpio[m.end():fin]

        encabezado_previo = ''
        for pos, texto_enc in reversed(encabezados):
            if pos < m.start():
                encabezado_previo = texto_enc
                break

        actos.append({
            'tipo_crudo': m.group(1),
            'numero': m.group(2),
            'encabezado_previo': encabezado_previo,
            'cuerpo': cuerpo,
        })
    return actos


# ===========================================================================
# EXTRACCIÓN DE CAMPOS — ver docstring "NUMERO / ANIO" y "FECHA PROPIA DEL ACTO"
# ===========================================================================
NORMALIZAR_TIPO = {
    'DECRETO': 'DECRETO',
    'LEY': 'LEY',
    'RESOLUCION': 'RESOLUCION',
    'NOTIFICACION': 'NOTIFICACION',  # confirmado real -- ver RE_ACTO
}


def _tipo_norma_desc(tipo_crudo):
    return NORMALIZAR_TIPO.get(_sin_acentos(tipo_crudo or '').upper(),
                                _sin_acentos(tipo_crudo or '').upper())


def _anio_desde_numero(numero):
    """Decreto/Resolución vienen 'NNN/0YY' (ej. '171/026', '1.016/026') --
    los últimos 2 dígitos tras la barra son el año corto (2026). Ley no
    tiene barra ('20.509') -- devuelve None, el año sale de la fecha del
    acto (ver _fecha_acto)."""
    m = re.search(r'/(\d+)$', numero or '')
    if not m:
        return None
    yy = m.group(1)[-2:]
    if len(yy) < 2:
        return None
    return 2000 + int(yy)


RE_FECHA_MONTEVIDEO = re.compile(
    r'Montevideo,\s*(?:a\s+)?(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+de\s+(\d{4})',
    re.IGNORECASE)


def _fecha_acto(cuerpo, fecha_boletin):
    """Fecha ISO propia del acto ('Montevideo, DD de MES de YYYY', ver
    docstring "FECHA PROPIA DEL ACTO") -- si no aparece (confirmado real:
    no todos los actos la tienen, ej. la Resolución 1.016/026 tabular) se
    usa la fecha de la edición como respaldo.

    BUG REAL evitado (encontrado probando contra la Ley 20.509 real, antes
    de mostrar el bot): una Ley trae DOS fechas "Montevideo, ..." reales --
    primero la de "Sala de Sesiones de la Cámara de Senadores, en
    Montevideo, a 7 de julio de 2026" (sesión del Congreso) y DESPUÉS,
    pegada a "Cúmplase, acúsese recibo...", "Montevideo, 10 de Julio de
    2026" (promulgación del Poder Ejecutivo). Un primer intento con
    .search() (primer match) devolvía la fecha del Congreso -- se prefiere
    la ÚLTIMA aparición, que en los 2 casos reales completos (Ley 20.509,
    y los 2 Decretos, que sólo tienen 1 fecha "Montevideo," cada uno) es
    siempre la fecha de promulgación real del acto."""
    matches = list(RE_FECHA_MONTEVIDEO.finditer(cuerpo or ''))
    if matches:
        dia, mes_nombre, anio = matches[-1].groups()
        mes = MESES_ES.get(_sin_acentos(mes_nombre).lower())
        if mes:
            try:
                return date(int(anio), mes, int(dia)).isoformat()
            except ValueError:
                pass
    return fecha_boletin


# Ver docstring "EMISOR" y "BUG EVITADO" -- ventana generosa antes del
# verbo operativo, colon opcional (confirmado real: "DECRETA:" en los
# Decretos, pero "DECRETAN" SIN colon en las Leyes), luego se recorta en
# _emisor todo lo que quede antes de la última cláusula reconocida.
RE_EMISOR_VENTANA = re.compile(
    r'([\s\S]{0,400}?)\s*(?:DECRETA|DECRETAN|RESUELVE|RESUELVEN)\s*:?\s*\n',
    re.IGNORECASE)
# BUG REAL evitado (encontrado probando contra los 2 Decretos reales, antes
# de mostrar el bot): un primer intento cortaba en el FIN DE LÍNEA de la
# cláusula ATENTO/CONSIDERANDO reconocida ("^...ATENTO\s*:.*$") -- pero en
# el texto real esas cláusulas se envuelven en VARIAS líneas físicas ("ATENTO:
# a lo dispuesto por el artículo 168 numeral 4º de la\nConstitución de la
# República;\nEL PRESIDENTE..."), así que el corte quedaba a mitad de la
# cláusula y el emisor salía con la cola pegada: "Constitución de la
# República; EL PRESIDENTE DE LA REPÚBLICA actuando en Consejo de
# Ministros". Corregido: en vez de anclar en la PALABRA de la cláusula, se
# ancla en su PUNTUACIÓN de cierre real -- el "; " seguido de salto de
# línea con el que termina cada punto de VISTO/RESULTANDO/CONSIDERANDO/
# ATENTO en los 2 ejemplos reales completos -- tomando el ÚLTIMO antes del
# verbo (equivalente en espíritu a "próximo Que" de Tucumán, pero acá
# "última cláusula" en vez de "próxima oración"). Para Leyes (sin esas
# cláusulas) se sigue usando el código de registro "(N.NNN)" como límite,
# ver docstring "EMISOR".
RE_LIMITE_EMISOR = re.compile(r';\s*\n|^\s*\([\d][\d.]*\*?R?\)\s*$', re.MULTILINE)
RE_PODER_CANONICO = re.compile(
    r'^(PODER EJECUTIVO|PODER LEGISLATIVO|PODER JUDICIAL)\s*$', re.MULTILINE)

GENERICO_EMISOR = 'PODER EJECUTIVO'


def _emisor(cuerpo, encabezado_previo):
    """Ver docstring "EMISOR" -- el emisor real está pegado inmediatamente
    antes del verbo operativo (DECRETA/RESUELVE), nunca en el encabezado
    de sección que antecede al acto (confirmado real, caso Ley 20.509).
    Si no hay verbo operativo reconocible (confirmado real: Resolución
    1.016/026 tabular) se usa encabezado_previo; de última instancia, un
    genérico."""
    cuerpo = cuerpo or ''
    m = RE_EMISOR_VENTANA.search(cuerpo)
    if m:
        ventana = m.group(1)
        limites = list(RE_LIMITE_EMISOR.finditer(ventana))
        if limites:
            ventana = ventana[limites[-1].end():]
        m_poder = RE_PODER_CANONICO.search(ventana)
        candidato = m_poder.group(1) if m_poder else _compacto(ventana).strip(' ,.-;')
        if candidato:
            return candidato
    if encabezado_previo:
        return encabezado_previo
    return GENERICO_EMISOR


# Ver docstring "HALLAZGO CLAVE: la síntesis ya viene pre-escrita" -- es el
# texto entre el encabezado "Tipo numero" y el próximo código de registro
# interno de IMPO entre paréntesis (ej. "(3.005*R)", "(3.167)").
RE_CODIGO_REGISTRO = re.compile(r'^\s*\([\d][\d.]*\*?R?\)\s*$', re.MULTILINE)
TOPE_SINTESIS_SIN_CODIGO = 500


def _sintesis(cuerpo):
    cuerpo = cuerpo or ''
    m_codigo = RE_CODIGO_REGISTRO.search(cuerpo)
    fin = m_codigo.start() if m_codigo else min(len(cuerpo), TOPE_SINTESIS_SIN_CODIGO)
    return _compacto(cuerpo[:fin])


def _texto_completo(cuerpo):
    """A diferencia de _sintesis, acá interesa mantener el texto legible
    completo (no una sola línea) -- sólo se colapsan 3+ saltos de línea
    seguidos (separación de página/columna) a 2."""
    return re.sub(r'\n{3,}', '\n\n', (cuerpo or '').strip())


def _armar_norma(acto, fecha_boletin, id_jurisdiccion, url_seccion):
    tipo = _tipo_norma_desc(acto['tipo_crudo'])
    numero = acto['numero']
    fecha = _fecha_acto(acto['cuerpo'], fecha_boletin)
    anio = _anio_desde_numero(numero) or int(fecha[:4])
    sintesis = _sintesis(acto['cuerpo']) or f"{tipo} {numero}"
    return {
        "id_jurisdiccion": id_jurisdiccion,
        "emisor": _emisor(acto['cuerpo'], acto['encabezado_previo']),
        "tipo": tipo,
        "numero": numero,
        "anio": str(anio),
        "fecha": fecha,
        "sintesis": sintesis,
        "texto_completo": _texto_completo(acto['cuerpo']),
        "url_norma": url_seccion,
        "_encabezado_previo": acto['encabezado_previo'],  # sólo debug, no se envía
    }


def procesar_texto(texto_pdf, fecha_boletin, id_jurisdiccion, url_seccion):
    """[norma, ...] a partir del texto ya extraído (get_text) del PDF de
    'Documentos' de una edición. [] si no se reconoció ningún acto (ver
    stderr)."""
    texto_limpio = _limpiar_ruido_paginas(texto_pdf)
    actos = _dividir_actos(texto_limpio)
    if not actos:
        print("Aviso: no se reconoció ningún acto (Decreto/Ley/Resolución + numero) "
              "en el texto del PDF.", file=sys.stderr)
    return [_armar_norma(a, fecha_boletin, id_jurisdiccion, url_seccion) for a in actos]


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
    ap = argparse.ArgumentParser(description="Scraper del Diario Oficial de Uruguay (IMPO).")
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?',
                     help='ignorado; la fuente es fija (ver docstring "FUENTE")')
    ap.add_argument('--fecha', help='YYYY-MM-DD; default hoy (ver docstring "DESCUBRIMIENTO")')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--volcar', action='store_true', help='imprime lo reconocido y sale')
    args = ap.parse_args()

    if fitz is None:
        salida("error", "Falta PyMuPDF (fitz) -- pip install pymupdf.")

    if args.fecha:
        try:
            fecha_objetivo = datetime.strptime(args.fecha, '%Y-%m-%d').date()
        except ValueError:
            salida("error", f"--fecha inválida: {args.fecha!r} (formato esperado YYYY-MM-DD).")
    else:
        fecha_objetivo = date.today()

    try:
        fecha_boletin_date, pdf_bytes = _buscar_edicion_documentos(fecha_objetivo)
    except RuntimeError as e:
        salida("error", str(e))

    if fecha_boletin_date is None:
        salida("warning", f"No se encontró ninguna edición de 'Documentos' en los últimos "
                          f"{MAX_DIAS_ATRAS} días hacia atrás desde {fecha_objetivo.isoformat()}.")

    fecha_boletin = fecha_boletin_date.isoformat()
    url_seccion = (f'{BASE_URL_URUGUAY}/{fecha_boletin_date.year:04d}/'
                   f'{fecha_boletin_date.month:02d}/{fecha_boletin_date.day:02d}/documentos.pdf')

    try:
        texto_pdf = _extraer_texto_pdf(pdf_bytes)
    except Exception as e:
        salida("error", f"No se pudo leer el PDF descargado: {e}")

    normas = procesar_texto(texto_pdf, fecha_boletin, args.id_jurisdiccion, url_seccion)

    print(f"Edición: {fecha_boletin} | actos encontrados: {len(normas)}", file=sys.stderr)

    guardar_debug(json.dumps(normas, ensure_ascii=False, indent=2, default=str),
                  'debug_uruguay.json')

    if args.volcar or args.dry_run:
        for n in normas:
            print(f"  {n['tipo']:12s} N° {n['numero']:>10s} ({n['anio']}) "
                  f"fecha={n['fecha']:10s} emisor={n['emisor'][:45]:45s} "
                  f"{n['sintesis'][:50]}", file=sys.stderr)

    if args.volcar:
        salida("success", f"volcado: {len(normas)} actos reconocidos.")

    if not normas:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Sin novedades: no se reconoció ningún acto en la edición del "
                          f"{fecha_boletin}.", total=0)

    if args.dry_run:
        salida("success", "dry-run: no se envió nada al backend.", total=len(normas))

    if verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

    payload = [{
        "id_jurisdiccion": n['id_jurisdiccion'],
        "nombre_emisor": n['emisor'],
        "tipo_norma_desc": n['tipo'],
        "numero": n['numero'],
        "anio": n['anio'],
        "fecha_publicacion": n['fecha'],
        "sintesis": construir_sintesis(n),
        "texto_completo": recortar_texto(n['texto_completo']),
        "url_norma": n['url_norma'],
    } for n in normas]

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