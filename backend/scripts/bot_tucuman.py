#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
 BOLETÍN OFICIAL DE LA PROVINCIA DE TUCUMÁN
 id_jurisdiccion 25
===============================================================================

FUENTE — CONFIRMADA REAL EN VIVO ESTA SESIÓN
-------------------------------------------------------------------------------
https://boletin.tucuman.gov.ar -- app Blazor (SGG.BoletinOficial.Core.App).
Todo TEXTO NATIVO, sin PDF escaneado ni OCR (a diferencia del resto reciente
de la familia: Tierra del Fuego, Misiones, San Luis). El usuario subió
tucuman.html (home, CTRL+U) y norma_tucuman.html (detalle de un aviso real,
Decreto 1604/1); ambos confirmados en vivo contra el sitio real durante
esta sesión (misma edición, mismo contenido).

DESCUBRIMIENTO: API JSON, confirmada real en vivo
-------------------------------------------------------------------------------
    GET https://boletin.tucuman.gov.ar/api/frontend/GetAvisosFromTodayBoletin/2

El "2" es la clase "oficial" (confirmado: coincide con el contenido del tab
"Ver avisos oficiales" precargado en el HTML de origen). Hay un "/1" para
"avisos particulares" -- fuera de alcance, mismo criterio que el resto de
la familia (sólo normativa oficial, no avisos de terceros). Forma real de
la respuesta (achicada):

    {
      "boletinDelDia": {"titulo": "Número 31.253 del lunes, 3 de agosto de
                         2026", "numero": null, "fecha": "2026-08-03T08:30:47",
                         "downLoadUrl": "...", "existApiUrl": "..."},
      "tiposAviso": [
        {"tipoAviso": "RESOLUCIONES", "codigo": 7, "avisos": [
            {"detalleBoletinId": 620002,
             "titulo": "RESOLUCIONES N° 80 (SPS) del 21/07/2026",
             "sumario": "SIPROSA. RESOLUCION N.º 80 /SGA, del 21/07/2025.-\r\n...",
             "clase": 0, "hasEdicto": false, "hasAnexo": false},
            ...
        ]},
        {"tipoAviso": "DECRETO", "codigo": 4, "avisos": [...]}
      ]
    }

CONFIRMADO REAL: pese al nombre, "sumario" trae el TEXTO COMPLETO del acto,
no un resumen -- se comparó contra norma_tucuman.html (Decreto 1604/1, HTML
de detalle real subido por el usuario) y coincide palabra por palabra. Un
solo llamado a esta API alcanza para todo (lista + texto completo); no
hace falta pegarle a /Aviso/Detalle/{id}/2 de cada aviso (esa página existe
y tiene la misma info, pero es redundante -- se arma su URL sólo como
url_norma de referencia, nunca se descarga).

BUG EVITADO: los IDs de /Aviso/Detalle NO están particionados por clase
-------------------------------------------------------------------------------
Al buscar más ejemplos reales para ampliar el universo de prueba, se probó
/Aviso/Detalle/619990/2 (un ID más viejo que los de hoy, al azar) esperando
otro aviso oficial de días previos -- resultó ser un aviso PARTICULAR real
("DAVSA CONSTRUCTORA S.A.S.", constitución de sociedad), pese a que la URL
termina en "/2" igual que los oficiales. Conclusión real: ese "/2" final en
/Aviso/Detalle/{id}/2 NO filtra por clase (parece ser sólo un parámetro de
UI para el link "Volver") -- por eso el descubrimiento NUNCA debe basarse
en un rango de IDs, siempre en GetAvisosFromTodayBoletin/2, que sí filtra
bien (confirmado: sólo devolvió DECRETO/RESOLUCIONES reales).

No se encontró (sin ejecutar JS del sitio -- la Biblioteca de Boletines y
el buscador de avisos arman la consulta por script del lado del cliente, y
/js/site.js público viene vacío) una API equivalente para reprocesar un día
puntual del pasado. El universo de prueba de esta sesión es la edición
completa del 03/08/2026 (~21 avisos reales: DECRETO y RESOLUCIONES) más 2
avisos sueltos de otros días encontrados al tantear IDs (una Licitación
Pública de Ministerio de Educación del 23/07/2026, y el aviso particular
recién mencionado, descartado por no ser oficial). No hay soporte para
reprocesar una fecha pasada específica (no hay --fecha como en Tierra del
Fuego): la API sólo expone "la edición de hoy", lo cual alcanza para uso
normal (corrida diaria) pero es una limitación real a tener en cuenta.

ARQUITECTURA: sin clasificación local (mismo criterio que bot_nacion.py)
-------------------------------------------------------------------------------
A diferencia de Tierra del Fuego/Salta/San Juan/etc. (que corren
clasificar_norma() localmente y sólo mandan los actos "generales"), este
bot sigue el patrón más nuevo de bot_nacion.py (confirmado por el usuario
que anda bien en producción): manda TODOS los avisos oficiales tal cual,
con nombre_emisor/tipo/numero/fecha ya resueltos, y deja que
NormativaHelper.php (backend) categorice/deduplique. Tiene sentido para un
sitio de texto nativo con API limpia como este -- no hay la incertidumbre
de OCR que en el resto de la familia amerita un filtro de confianza local.

CAMPOS — decisiones tomadas con el usuario
-------------------------------------------------------------------------------
- numero: se deja TAL CUAL aparece en "titulo" (ej. "1604/1", "30/3", "80",
  "3/1"). El usuario confirmó que no hace falta partir el sufijo "/N" de
  los decretos -- significado real desconocido (¿tomo/serie/área?), no se
  pudo determinar con los ejemplos disponibles, y no vale la pena adivinar.
- anio: NO viene en el número (a diferencia de Tierra del Fuego) -- se
  deriva de la fecha del acto: primero "del DD/MM/YYYY" en el propio
  título (más confiable), y si no está (caso real visto en la lista
  estática: "DECRETO ACUERDO DE NECESIDAD Y URGENCIA N° 3/1", sin fecha en
  el título) se busca la primera "del DD/MM/YYYY" dentro del sumario. Si
  ninguna de las dos aparece, último respaldo es la fecha de la edición.
- nombre_emisor: no es un campo directo de la API, se infiere:
    * Cualquier tipo que empiece con "DECRETO" -> "PODER EJECUTIVO"
      (confirmado real: el cuerpo del Decreto 1604/1 firma "EL VICE
      GOBERNADOR DE LA PROVINCIA EN EJERCICIO DEL PODER EJECUTIVO ...
      DECRETA" -- sólo este ejemplo real visto, no se probó un Decreto
      firmado directamente por el Gobernador sin "en ejercicio").
    * RESOLUCION/RESOLUCIONES -> primera palabra/frase antes del propio
      "RESOLUCION" al inicio del sumario (confirmado real: "SIPROSA.
      RESOLUCION N.º 80..." -> emisor SIPROSA), con respaldo la sigla
      entre paréntesis del título (ej. "(SPS)") y de última instancia un
      genérico de provincia. Sólo este ejemplo real visto -- ver "QUÉ
      FALTA VALIDAR".
- sintesis: primer punto completo tras CONSIDERANDO (no la primera
  oración -- ver BUG REAL más abajo), tolerando tanto "CONSIDERANDO:\n
  Que ..." (convención vista en el resto de la familia) como "CONSIDERANDO
  que:\n..." (real, ver SIPROSA/Resolución 80).
- tipo_norma_desc: normalizado a singular ("RESOLUCIONES" -> "RESOLUCION"),
  confirmado con el usuario. El resto de los tipos vistos (DECRETO,
  DECRETO ACUERDO, DECRETO ACUERDO DE NECESIDAD Y URGENCIA) ya vienen
  singulares, no se tocan.

BUGS REALES ENCONTRADOS Y CORREGIDOS ESTA SESIÓN
-------------------------------------------------------------------------------
(1, antes de mostrárselo al usuario) Primer intento de _sintesis cortaba
en el primer punto/punto y coma tras CONSIDERANDO. Probado contra el texto
real completo del Decreto 1604 (único sumario 100% completo disponible en
ese momento), dio sintesis='a fs' -- el español administrativo argentino
abrevia todo el tiempo con punto ("fs." de fojas, "N°"/"N.º", etc.), así
que "primer punto" casi nunca es el fin real de la oración.

(2, primera corrida real completa, 37 avisos vía debug_tucuman.json) El
arreglo de (1) cortaba en el próximo renglón que empieza con "Que" (así
están armados los CONSIDERANDO de Convención "Que, ..." por punto, ver
IPVYDU) o en el próximo párrafo en blanco -- pero la Resolución 80
(SIPROSA) y la Resolución 11 (Junta Electoral) reales vinieron con el
CONSIDERANDO en PROSA CONTINUA (sin "Que" repetido, sin párrafos en
blanco), así que ese límite no se cumplía nunca y la búsqueda entera
fallaba -> sintesis vacía -> 2 de 37 avisos reales caían al respaldo
genérico "TIPO NUMERO" en vez de tener una síntesis real.

Corregido con una heurística de fin de oración real (punto seguido de
espacio+mayúscula o fin de texto, con lista corta de abreviaturas de
título excluidas -- Sr/Sra/Dr/Dra/Ing/Lic/Prof/Gral, ver "QUÉ FALTA
VALIDAR"), tomando el límite que aparezca primero entre esta heurística y
el "próximo Que" -- cubre ambas convenciones reales vistas sin tener que
elegir una a ciegas. Confirmado contra los 4 casos reales disponibles
(Decreto 1604, SIPROSA 80, IPVYDU 1473, JET 11): los 4 dan una oración
completa y no vacía.

(3, segunda corrida real completa, debug_tucumanNEW.json) El arreglo de
(2) todavía cortaba corto en casos reales como "D.N.I. N° 23.311.295":
"N" de "N°" es mayúscula, y el chequeo de (2) no distinguía eso de una
oración nueva de verdad -- daba sintesis="...MARTINEZ GUSTAVO MIGUEL
D.N.I." en vez de la oración completa (2 de 37 avisos reales de esta
corrida, ambos I.P.V. Y D.U. con "D.N.I." puntuado así). Corregido
excluyendo puntualmente "N°"/"Nº"/"N." como inicio de oración -- en este
idioma administrativo, Expte./Art./Resolución/Decreto/D.N.I. casi siempre
terminan justo antes de un "N°", nunca es el inicio real de una oración
nueva. Confirmado contra los 37 avisos reales de ambas corridas: 0
vacías, 0 cortadas en una abreviatura conocida. Ver
test_tucuman_fixtures.py.

QUÉ FALTA VALIDAR (real, pendiente)
-------------------------------------------------------------------------------
- Heurística de emisor para RESOLUCIONES: sólo 1 ejemplo real (SIPROSA).
- Un Decreto firmado directamente por el Gobernador (no "en ejercicio" por
  el Vice) -- confirmar que el emisor sigue siendo "PODER EJECUTIVO".
- hasEdicto/hasAnexo: todos los ejemplos reales vistos traen ambos en
  false -- no se sabe qué cambia en la respuesta cuando alguno da true
  (¿el sumario queda incompleto? ¿hay que bajar un adjunto aparte?). No se
  pudo probar, sin ejemplo real con alguno en true.
- DECRETO ACUERDO / DECRETO ACUERDO DE NECESIDAD Y URGENCIA: sólo vistos
  en el título de la lista estática subida por el usuario, ningún
  "sumario" completo real todavía (la corrida en vivo de esta sesión no
  tuvo ninguno) -- la extracción de tipo/numero debería andar igual
  (mismo patrón "TIPO N° numero"), pero el cuerpo real no está confirmado.
- Fecha del acto ausente en el título con RESPALDO desde el sumario: sin
  ejemplo real completo que ejercite esa rama (ver arriba, "DECRETO
  ACUERDO DE NECESIDAD Y URGENCIA N° 3/1").
- Discrepancia real vista entre la fecha del título ("del 21/07/2026") y
  la fecha citada al inicio del propio sumario de la misma Resolución 80
  ("del 21/07/2025", un año antes) -- se prioriza la del título tal cual
  viene (ver "CAMPOS"), no se investigó más a fondo.
- La lista de abreviaturas excluidas en RE_LIMITE_FIN_ORACION (Sr/Sra/Dr/
  Dra/Ing/Lic/Prof/Gral) es la observada en los ejemplos reales de esta
  sesión, no exhaustiva -- una abreviatura de título NO listada, seguida
  de un nombre propio, puede cortar la síntesis antes de tiempo (falso
  positivo de fin de oración). Bajo impacto (la síntesis queda más corta,
  no vacía ni incorrecta), pero vale ampliar la lista si aparece un caso
  real. La exclusión de "N°/Nº/N." (ver BUG #3) es más general y ya cubre
  el caso más frecuente visto (Expte./Art./D.N.I./Resolución/Decreto
  seguidos de un número).
- Resolución N° 2265/2026 (I.P.V. Y D.U.) apareció 2 veces en la primera
  corrida real, con texto_completo IDÉNTICO pero distinto detalleBoletinId
  (620022 y 620023) -- confirmado que es un duplicado real del sitio de
  origen (no un bug de este bot: ambos son avisos genuinamente distintos
  en la respuesta de la API, con el mismo contenido). No se agregó
  deduplicación propia todavía -- a confirmar con el usuario si conviene
  filtrar duplicados exactos (mismo tipo+numero+anio+texto_completo)
  antes de enviar, o si preferible mandar ambos tal cual vienen y dejar
  que el backend decida.
- Emisor con formato inconsistente entre avisos reales del MISMO
  organismo: se vio tanto "I.P.V. Y D.U." como "I.P.V.YD.U." (sin
  espacios) como encabezado real de distintas Resoluciones del Instituto
  Provincial de Vivienda y Desarrollo Urbano (12 de 37 avisos de la
  primera corrida real eran de este organismo). _emisor extrae ambas
  formas tal cual vienen (fiel a la fuente, mismo criterio que "numero"),
  sin normalizar a un nombre canónico -- si el backend dedupea por nombre
  de emisor, esto podría generar 2 registros distintos para el mismo
  organismo. No se normalizó unilateralmente porque no está claro cuál
  sería la forma canónica preferida (¿sigla "IPVYDU"? ¿nombre completo
  "INSTITUTO PROVINCIAL DE VIVIENDA Y DESARROLLO URBANO", visto en el
  cuerpo de ambas Resoluciones? ¿tal cual viene?) -- a confirmar con el
  usuario si hace falta.
===============================================================================
"""

import os
import re
import sys
import json
import time
import argparse
from datetime import datetime

import requests

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

BASE_URL_TUCUMAN = get_env_clean('BASE_URL_TUCUMAN', 'https://boletin.tucuman.gov.ar')
# Ver docstring "DESCUBRIMIENTO" -- "2" = clase oficial, confirmado real.
API_AVISOS_HOY = f'{BASE_URL_TUCUMAN}/api/frontend/GetAvisosFromTodayBoletin/2'

REINTENTOS = 3
ESPERA_REINTENTO = 3
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700


# ===========================================================================
# NORMALIZACIÓN
# ===========================================================================
def _compacto(texto):
    return re.sub(r'\s+', ' ', (texto or '')).strip()


# ===========================================================================
# DESCARGA DE LA LISTA DEL DÍA — ver docstring "DESCUBRIMIENTO"
# ===========================================================================
def _obtener_avisos_hoy():
    """dict crudo de la API, o None si falló la consulta (ver stderr)."""
    for intento in range(1, REINTENTOS + 1):
        try:
            r = requests.get(API_AVISOS_HOY, timeout=20)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if intento == REINTENTOS:
                print(f"Aviso: error consultando {API_AVISOS_HOY}: {e}", file=sys.stderr)
                return None
            time.sleep(ESPERA_REINTENTO * intento)
        except ValueError as e:  # respuesta no era JSON válido
            print(f"Aviso: respuesta no-JSON de {API_AVISOS_HOY}: {e}", file=sys.stderr)
            return None
    return None


# ===========================================================================
# EXTRACCIÓN DE CAMPOS — ver docstring "CAMPOS"
# ===========================================================================
# Orden de alternativas: las compuestas ANTES que "DECRETO" solo, para que
# el regex no se quede corto (ej. "DECRETO ACUERDO..." tiene que probarse
# antes que "DECRETO" a secas, si no el resto de la frase queda afuera).
RE_TIPO_NUMERO = re.compile(
    r'^(DECRETO\s+ACUERDO\s+DE\s+NECESIDAD\s+Y\s+URGENCIA|DECRETO\s+ACUERDO|DECRETO|'
    r'RESOLUCIONES|RESOLUCI[OÓ]N|LEY|DISPOSICI[OÓ]N)\s*N[°ºª]?\s*([\d./]+)'
    r'(?:\s*\(([A-ZÁÉÍÓÚÑ]+)\))?'
    r'(?:\s*del\s+(\d{2}/\d{2}/\d{4}))?',
    re.IGNORECASE)

NORMALIZAR_TIPO = {
    'RESOLUCIONES': 'RESOLUCION',  # confirmado con el usuario, ver docstring "CAMPOS"
}


def _tipo_numero_sigla_fecha(titulo):
    """(tipo, numero, sigla_o_None, fecha_ddmmyyyy_o_None) parseados del
    campo "titulo" de un aviso (ej. "RESOLUCIONES N° 80 (SPS) del
    21/07/2026"). tipo=None si no matcheó ningún tipo conocido -- ver
    procesar_respuesta() para el respaldo en ese caso."""
    m = RE_TIPO_NUMERO.match(_compacto(titulo))
    if not m:
        return None, '', None, None
    tipo = NORMALIZAR_TIPO.get(m.group(1).upper(), m.group(1).upper())
    return tipo, m.group(2), m.group(3), m.group(4)


def _fecha_iso_desde_ddmmyyyy(fecha_dmy):
    try:
        return datetime.strptime(fecha_dmy, '%d/%m/%Y').date().isoformat()
    except (ValueError, TypeError):
        return None


RE_FECHA_EN_SUMARIO = re.compile(r'\bdel?\s+(\d{2}/\d{2}/\d{4})')


def _fecha_acto(fecha_titulo_dmy, sumario):
    """Fecha ISO del acto: primero la del título (más confiable); si no
    está (ver docstring, caso real "DECRETO ACUERDO DE NECESIDAD Y
    URGENCIA N° 3/1" sin fecha en el título) se busca la primera
    "del DD/MM/YYYY" dentro del propio sumario. None si ninguna aparece."""
    if fecha_titulo_dmy:
        return _fecha_iso_desde_ddmmyyyy(fecha_titulo_dmy)
    m = RE_FECHA_EN_SUMARIO.search(sumario or '')
    if m:
        return _fecha_iso_desde_ddmmyyyy(m.group(1))
    return None


GENERICO_EMISOR = 'GOBIERNO DE LA PROVINCIA DE TUCUMÁN'

# Confirmado real: "SIPROSA. RESOLUCION N.º 80 /SGA, del 21/07/2025.-" ->
# emisor SIPROSA. Sólo este ejemplo real, ver docstring "QUÉ FALTA VALIDAR".
RE_EMISOR_RESOLUCION = re.compile(
    r'^\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s.]{1,60}?)\.\s*RESOLUCI[OÓ]N', re.IGNORECASE)


def _emisor(tipo, sumario, sigla):
    """Ver docstring "CAMPOS" -- nombre_emisor no es un campo directo de
    la API, se infiere del propio tipo/texto."""
    if tipo and tipo.startswith('DECRETO'):
        return 'PODER EJECUTIVO'
    if tipo and tipo.startswith('RESOLUCION'):
        m = RE_EMISOR_RESOLUCION.match(sumario or '')
        if m:
            return _compacto(m.group(1)).upper()
        if sigla:
            return sigla
    return GENERICO_EMISOR


# BUG REAL #1 (corregido, ver test_tucuman_fixtures.py): un primer intento
# cortaba en el primer punto/punto y coma, lo cual en español administra-
# tivo argentino cae casi siempre en una abreviatura ("fs." = fojas,
# "N°"/"N.º", etc.) y no en el fin real de la oración -- contra el Decreto
# 1604 real esto daba sintesis='a fs' (2 caracteres útiles).
#
# BUG REAL #2 (corregido, encontrado en la primera corrida real completa
# contra 37 avisos): el primer arreglo cortaba en el próximo renglón que
# empieza con "Que" (así están armados los CONSIDERANDO de Convención
# "Que, ..." por punto, ver IPVYDU) o en el próximo párrafo en blanco --
# pero la Resolución 80 (SIPROSA) y la Resolución 11 (Junta Electoral)
# real vinieron con el CONSIDERANDO en PROSA CONTINUA, sin "Que" repetido
# y sin párrafos en blanco, así que ese límite nunca se cumplía dentro del
# tope y toda la búsqueda fallaba -> sintesis vacía -> caía al respaldo
# "TIPO NUMERO" para 2 de 37 avisos reales.
#
# Corregido con una heurística de fin de oración real (no sólo "próximo
# Que"): un punto cuenta como fin de oración si sigue espacio+mayúscula o
# fin de texto, salvo que la palabra anterior sea una abreviatura común de
# título (Sr/Sra/Dr/Dra/Ing/Lic/Prof/Gral -- riesgo aceptado de falso
# positivo si aparece una NO listada, ver docstring "QUÉ FALTA VALIDAR").
# Se toma el límite que aparezca PRIMERO entre esta heurística y el
# "próximo Que" (cubre ambas convenciones reales sin preferir una a
# ciegas). Confirmado contra los 4 casos reales disponibles: Decreto 1604,
# SIPROSA 80, IPVYDU 1473 y JET 11 -- los 4 dan una oración completa y no
# vacía.
RE_CONSIDERANDO_INICIO = re.compile(r'CONSIDERANDO\s*:?\s*(?:que\s*[,:]?\s*)?', re.IGNORECASE)
RE_LIMITE_PROXIMO_QUE = re.compile(r'\r?\n\s*Que\b|\r?\n\s*\r?\n', re.IGNORECASE)
# BUG REAL #3 (ver docstring "BUGS REALES"): "D.N.I. N° 23.311.295" cortaba
# la síntesis en "D.N.I." porque "N" (de "N°") es mayúscula y el chequeo
# original no distinguía eso de una oración nueva de verdad. Excluye
# puntualmente "N°"/"Nº"/"N." como inicio de oración -- cubre Expte./Art./
# Resolución/Decreto/D.N.I., que en este idioma administrativo casi
# siempre terminan justo antes de un "N°".
RE_LIMITE_FIN_ORACION = re.compile(
    r'(?<!\bSr)(?<!\bSra)(?<!\bDr)(?<!\bDra)(?<!\bIng)(?<!\bLic)(?<!\bProf)(?<!\bGral)'
    r'\.(?=\s+(?![Nn][°º.])[A-ZÁÉÍÓÚÑ]|\s*$)')
TOPE_SINTESIS_CONSIDERANDO = 1200


def _sintesis(sumario):
    """Primer punto/oración completo del CONSIDERANDO (ver comentario de
    arriba). Cadena vacía si no hay CONSIDERANDO reconocible (el llamador
    arma el respaldo "TIPO NUMERO/ANIO", ver _armar_norma)."""
    sumario = sumario or ''
    m_inicio = RE_CONSIDERANDO_INICIO.search(sumario)
    if not m_inicio:
        return ''
    resto = sumario[m_inicio.end():m_inicio.end() + TOPE_SINTESIS_CONSIDERANDO]
    fin = len(resto)
    m_que = RE_LIMITE_PROXIMO_QUE.search(resto)
    if m_que:
        fin = min(fin, m_que.start())
    m_punto = RE_LIMITE_FIN_ORACION.search(resto)
    if m_punto:
        fin = min(fin, m_punto.end())
    return _compacto(resto[:fin])


def _armar_norma(aviso, tipo, numero, sigla, fecha_dmy, fecha_boletin, id_jurisdiccion):
    sumario = (aviso.get('sumario') or '').replace('\r\n', '\n').strip()
    fecha = _fecha_acto(fecha_dmy, sumario) or fecha_boletin
    sintesis = _sintesis(sumario) or f"{tipo} {numero or '?'}"
    return {
        "id_jurisdiccion": id_jurisdiccion,
        "emisor": _emisor(tipo, sumario, sigla),
        "tipo": tipo,
        "numero": numero or '?',
        "anio": fecha[:4],
        "fecha": fecha,
        "sintesis": sintesis,
        "texto_completo": sumario,
        "url_norma": f"{BASE_URL_TUCUMAN}/Aviso/Detalle/{aviso.get('detalleBoletinId')}/2",
        "_id_origen": aviso.get('detalleBoletinId'),  # sólo debug, no se envía
        "_titulo_origen": aviso.get('titulo'),  # sólo debug, no se envía
    }


def procesar_respuesta(data, id_jurisdiccion):
    """(fecha_boletin, [norma, ...]) a partir del JSON crudo de
    _obtener_avisos_hoy(). (None, None) si la respuesta no tuvo la forma
    esperada (sin boletinDelDia.fecha)."""
    if not isinstance(data, dict):
        return None, None
    boletin = data.get('boletinDelDia') or {}
    fecha_raw = boletin.get('fecha')
    if not fecha_raw:
        return None, None
    fecha_boletin = fecha_raw.split('T')[0]

    normas = []
    for grupo in (data.get('tiposAviso') or []):
        tipo_grupo = NORMALIZAR_TIPO.get(_compacto(grupo.get('tipoAviso', '')).upper(),
                                          _compacto(grupo.get('tipoAviso', '')).upper())
        for aviso in (grupo.get('avisos') or []):
            tipo, numero, sigla, fecha_dmy = _tipo_numero_sigla_fecha(aviso.get('titulo', ''))
            if not tipo:
                # No matcheó ningún tipo conocido en el título propio del
                # aviso -- se usa el encabezado del grupo como respaldo en
                # vez de perder el aviso (ver docstring "QUÉ FALTA VALIDAR",
                # puede venir abreviado para tipos compuestos).
                tipo = tipo_grupo or 'AVISO OFICIAL'
            normas.append(_armar_norma(aviso, tipo, numero, sigla, fecha_dmy,
                                        fecha_boletin, id_jurisdiccion))
    return fecha_boletin, normas


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
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Tucumán.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?',
                    help='ignorado; la fuente es fija (ver docstring "DESCUBRIMIENTO")')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--volcar', action='store_true', help='imprime lo reconocido y sale')
    args = ap.parse_args()

    data = _obtener_avisos_hoy()
    if data is None:
        salida("warning", "No se pudo consultar la API de avisos de Tucumán (ver stderr).")

    fecha_boletin, normas = procesar_respuesta(data, args.id_jurisdiccion)
    if not fecha_boletin:
        salida("warning", "La respuesta de la API no tuvo la forma esperada "
                          "(sin boletinDelDia.fecha).")

    print(f"Edición: {fecha_boletin} | avisos oficiales encontrados: {len(normas)}",
          file=sys.stderr)

    guardar_debug(json.dumps(normas, ensure_ascii=False, indent=2, default=str),
                  'debug_tucuman.json')

    if args.volcar or args.dry_run:
        for n in normas:
            # OJO: numero puede traer su propia barra (ej. "1604/1", ver
            # docstring "CAMPOS") -- se separa de anio con paréntesis, no
            # con otra barra, para no leerlo ambiguo en esta salida.
            print(f"  {n['tipo']:14s} N° {n['numero']:>8s} ({n['anio']}) "
                  f"fecha={n['fecha']:10s} emisor={n['emisor'][:45]:45s} "
                  f"{n['sintesis'][:50]}", file=sys.stderr)

    if args.volcar:
        salida("success", f"volcado: {len(normas)} avisos reconocidos.")

    if not normas:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Sin novedades: el boletín del {fecha_boletin} no publicó "
                          f"avisos oficiales.", total=0)

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