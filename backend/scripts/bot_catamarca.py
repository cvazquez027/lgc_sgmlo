"""
bot_catamarca.py
===============================================================================
Scraper del Boletín Oficial y Judicial de la Provincia de Catamarca.

Uso normal (igual que los otros bots del sistema):

    python bot_catamarca.py 4 "https://portal.catamarca.gob.ar/boletin/"

Modos de prueba, que NO tocan el backend:

    python bot_catamarca.py 4 "..." --dry-run
    python bot_catamarca.py 4 "..." --dry-run --pdf Boletin_57.pdf
    python bot_catamarca.py 4 "..." --dry-run --todas     (muestra las descartadas)

-------------------------------------------------------------------------------
CÓMO ENCUENTRA EL BOLETÍN
-------------------------------------------------------------------------------
El portal (portal.catamarca.gob.ar/boletin/) es una SPA de React: el listado de
boletines no viene en el HTML, lo dibuja JavaScript. Por eso NO se scrapea el
HTML —  con requests llegaría vacío — sino que se consulta directamente la API
que usa el propio portal:

    https://api-portal.catamarca.gob.ar/api/v1/boletin_oficial/

El formato de la respuesta se interpreta de manera TOLERANTE (ver
_buscar_pdf / _buscar_valor): en vez de depender de nombres de campo exactos,
se recorre el JSON en profundidad buscando la URL que termina en .pdf, la fecha
y el número. Esto es a propósito: la API es de terceros y puede cambiar los
nombres de sus campos o el envoltorio (JSON:API vs DRF paginado) sin aviso, y
así el bot sigue funcionando. Si algún día deja de encontrarlos, la respuesta
cruda queda guardada en debug_catamarca_api.json para diagnosticar.

-------------------------------------------------------------------------------
CÓMO PARSEA EL PDF
-------------------------------------------------------------------------------
El PDF es de UNA columna y el texto sale limpio y en orden, así que no hace
falta la reconstrucción por posición que necesitó Córdoba. Lo que sí se
aprovecha es que la maqueta usa fuente y color distintos por nivel de título:

    F10 >= 15pt          -> SECCIÓN OFICIAL / JUDICIAL / COMERCIAL / GENERAL
    F10 ~12.9pt          -> subsección (DECRETOS, RESOLUCIONES, EDICTOS DE...)
    F7 (negrita) + AZUL  -> emisor (MINISTERIO DE SALUD, CONTADURÍA GENERAL...)

El color es imprescindible: dentro del cuerpo hay tablas cuyo encabezado también
está en negrita y mayúsculas (ej. "CTA .CTE. N° DENOMINACIÓN ALTA"). Sin mirar
el color esas líneas se confunden con un cambio de emisor y contaminan todas las
normas siguientes. Los títulos reales van en azul institucional; el cuerpo y las
tablas, en negro.

Se escanea sólo la SECCIÓN OFICIAL y se corta al llegar a la SECCIÓN JUDICIAL.
Dentro de la oficial se toman únicamente DECRETOS y RESOLUCIONES: los EDICTOS
DE CANTERAS / MENSURAS / MINAS, el TRIBUNAL DE CUENTAS y el SENADO DE LA NACIÓN
quedan afuera por no ser normativa.
===============================================================================
"""

import os
import re
import io
import sys
import json
import argparse
import time
import requests
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# Forzar UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


# ===========================================================================
# CONFIGURACIÓN
# ===========================================================================
def get_env_clean(key, default=None):
    value = os.getenv(key, default)
    if value:
        value = value.strip().strip('"').strip("'")
    return value


API_KEY_BACKEND = get_env_clean('API_KEY_BACKEND', 'Token_Seguro_Scraper_2026_XyZ!')
URL_HISTORIAL = get_env_clean(
    'URL_HISTORIAL', 'http://localhost/lgc_sgmlo/backend/api/boletin/historial_scraping.php')
URL_GUARDAR_NORMAS = get_env_clean(
    'URL_GUARDAR_NORMAS', 'http://localhost/lgc_sgmlo/backend/api/boletin/ingresar_scraping.php')

API_BASE = 'https://api-portal.catamarca.gob.ar'
API_BOLETINES = API_BASE + '/api/v1/boletin_oficial/'
PORTAL_BASE = 'https://portal.catamarca.gob.ar'
PORTAL_BOLETIN = PORTAL_BASE + '/boletin/'

# El portal tiene una capa de detección de bots adelante. Desde una IP
# residencial no molesta, pero desde el datacenter de un VPS es habitual que
# devuelva 403 si la petición no se parece a la de un navegador real. Por eso
# mandamos el juego completo de cabeceras que emite Chrome, incluidos Referer y
# Origin (la API se consume desde el portal, así que una petición legítima
# SIEMPRE los trae) y las sec-ch-* / sec-fetch-*.
HEADERS_WEB = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-AR,es;q=0.9,es-ES;q=0.8,en;q=0.7',
    # OJO: no fijar Accept-Encoding a mano. requests anuncia sólo los algoritmos
    # que sabe descomprimir (gzip, deflate). Si le pedimos 'br' sin tener
    # instalado el paquete brotli, el servidor responde comprimido con brotli,
    # requests no puede descomprimirlo y el cuerpo queda ilegible.
    'Referer': PORTAL_BOLETIN,
    'Origin': PORTAL_BASE,
    'Connection': 'keep-alive',
    'sec-ch-ua': '"Chromium";v="126", "Not:A-Brand";v="24", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
}

# Cabeceras para pedir el PDF: ahí sí navegamos a un documento, no a una API.
HEADERS_DESCARGA = dict(HEADERS_WEB, **{
    'Accept': 'application/pdf,application/octet-stream,*/*',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
})

REINTENTOS = 3
ESPERA_ENTRE_REINTENTOS = 4   # segundos, se multiplica por el número de intento

MAX_TEXTO_COMPLETO = 20000   # mismo tope que bot_nacion.py
MAX_SINTESIS = 700


# ===========================================================================
# AUXILIARES COMPARTIDOS CON LOS OTROS BOTS
# ===========================================================================
def salida(status, message, total=None):
    out = {"status": status, "message": message}
    if total is not None:
        out["total_enviadas"] = total
    print(json.dumps(out))
    sys.exit(0)


def verificar_boletin_procesado(id_jurisdiccion, fecha_boletin):
    try:
        payload = {"id_jurisdiccion": id_jurisdiccion,
                   "fecha_boletin": fecha_boletin, "accion": "verificar"}
        headers = {"Authorization": f"Bearer {API_KEY_BACKEND}"}
        res = requests.post(URL_HISTORIAL, json=payload, headers=headers, timeout=10)
        return res.json().get('procesado', False)
    except Exception:
        return False


def registrar_boletin_procesado(id_jurisdiccion, fecha_boletin, cantidad):
    try:
        payload = {"id_jurisdiccion": id_jurisdiccion, "fecha_boletin": fecha_boletin,
                   "accion": "registrar", "cantidad_normas": cantidad}
        headers = {"Authorization": f"Bearer {API_KEY_BACKEND}"}
        requests.post(URL_HISTORIAL, json=payload, headers=headers, timeout=10)
    except Exception:
        pass


def guardar_para_debug(contenido, nombre_archivo):
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"Guardado {nombre_archivo} para depuración", file=sys.stderr)
    except Exception as e:
        print(f"Error guardando {nombre_archivo}: {e}", file=sys.stderr)


def limpiar_texto(texto):
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto).strip()


# ---------------------------------------------------------------------------
# CAPA DE RED
# ---------------------------------------------------------------------------
_SESION = None


def obtener_sesion():
    """
    Sesión reutilizada para todas las peticiones al portal.

    Antes de tocar la API hace una visita al portal para recoger las cookies que
    entrega la capa de protección. Un navegador real siempre llega a la API
    después de haber cargado la página, y algunos filtros validan justamente
    eso. Si la visita falla no abortamos: puede que no haga falta.
    """
    global _SESION
    if _SESION is not None:
        return _SESION
    s = requests.Session()
    s.headers.update(HEADERS_WEB)
    try:
        s.get(PORTAL_BOLETIN, timeout=20,
              headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Sec-Fetch-Dest': 'document',
                       'Sec-Fetch-Mode': 'navigate',
                       'Sec-Fetch-Site': 'none'})
    except Exception as e:
        print(f"AVISO: no se pudo precargar el portal ({e}); se sigue igual.", file=sys.stderr)
    _SESION = s
    return s


def _describir_bloqueo(resp):
    """
    Ante un 4xx, identifica quién está bloqueando. Un 403 puede venir de la
    aplicación o de un WAF/CDN intermedio, y la diferencia cambia por completo
    qué hay que hacer: lo primero se arregla en el código, lo segundo no.
    """
    pistas = []
    for cabecera in ('Server', 'CF-Ray', 'CF-Mitigated', 'X-Sucuri-ID', 'X-Powered-By'):
        valor = resp.headers.get(cabecera)
        if valor:
            pistas.append(f"{cabecera}={valor}")
    cuerpo = ''
    try:
        crudo = resp.text or ''
        # Un cuerpo con muchos caracteres de control no es texto útil (respuesta
        # comprimida que no supimos descomprimir, o binario): no lo volcamos.
        ilegibles = sum(1 for c in crudo[:400] if ord(c) < 32 and c not in '\r\n\t')
        if crudo and ilegibles > len(crudo[:400]) * 0.1:
            codificacion = resp.headers.get('Content-Encoding', '?')
            cuerpo = f"(cuerpo ilegible, Content-Encoding={codificacion})"
        else:
            cuerpo = limpiar_texto(re.sub(r'<[^>]+>', ' ', crudo))[:220]
    except Exception:
        pass
    if resp.headers.get('CF-Ray') or 'cloudflare' in (resp.headers.get('Server', '')).lower():
        pistas.append("=> parece Cloudflare: es un bloqueo por reputación de IP, "
                      "no algo que se arregle con cabeceras")
    detalle = '; '.join(pistas)
    if cuerpo:
        detalle += f" | cuerpo: {cuerpo}"
    return detalle


def get_con_reintentos(url, headers=None, params=None, timeout=45, intentos=REINTENTOS):
    """GET con reintentos y, si falla, un mensaje que explique el porqué."""
    sesion = obtener_sesion()
    ultimo = None
    for intento in range(1, intentos + 1):
        try:
            resp = sesion.get(url, headers=headers, params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp
            ultimo = RuntimeError(
                f"HTTP {resp.status_code} en {url} :: {_describir_bloqueo(resp)}")
            # 4xx que no sea 403/429 no se arregla reintentando
            if resp.status_code not in (403, 408, 429) and resp.status_code < 500:
                break
        except requests.RequestException as e:
            ultimo = RuntimeError(f"Error de red en {url}: {e}")
        if intento < intentos:
            espera = ESPERA_ENTRE_REINTENTOS * intento
            print(f"AVISO: intento {intento}/{intentos} falló; reintento en {espera}s.",
                  file=sys.stderr)
            time.sleep(espera)
    raise ultimo


def normalizar_emisor(emisor):
    """Mayúsculas sin tildes, igual que el resto del sistema (la Ñ se conserva)."""
    if not emisor:
        return ""
    emisor = re.sub(r'^##?\s*', '', emisor).strip().upper()
    for acento, plano in (('Á', 'A'), ('É', 'E'), ('Í', 'I'), ('Ó', 'O'), ('Ú', 'U')):
        emisor = emisor.replace(acento, plano)
    return emisor


# ---------------------------------------------------------------------------
# Emisores que YA existen en producción para Catamarca con otra redacción.
#
# El backend deduplica por clave_normalizada (minúsculas, sin tildes, sólo
# alfanumérico). Esas filas llevan el sufijo "de Catamarca", así que el nombre
# que produce este bot generaría una clave distinta y, por lo tanto, una fila
# nueva para el MISMO organismo. El alias evita ese duplicado devolviendo la
# descripción exacta ya cargada.
#
# Clave del diccionario: lo que produce normalizar_emisor().
# Valor: la descripción tal cual está en la tabla emisor_norma.
# ---------------------------------------------------------------------------
ALIAS_EMISOR = {
    'MINISTERIO DE AGUA, ENERGIA Y MEDIO AMBIENTE':
        'Ministerio de Agua, Energía y Medio Ambiente de Catamarca',
    'LEGISLATURA DE LA PROVINCIA':
        'Legislatura de la Provincia de Catamarca',
}


def resolver_emisor(emisor_crudo):
    """Normaliza y, si corresponde, reusa la redacción ya existente en la base."""
    normalizado = normalizar_emisor(emisor_crudo)
    if not normalizado:
        return ""
    return ALIAS_EMISOR.get(normalizado, normalizado)


# ===========================================================================
# DESCUBRIMIENTO DEL BOLETÍN VÍA API
# ===========================================================================
RE_PDF = re.compile(r'\.pdf($|\?)', re.IGNORECASE)
RE_FECHA_ISO = re.compile(r'^\d{4}-\d{2}-\d{2}')

# El endpoint devuelve JSON:API. Un registro real se ve así:
#
#   {"type":"Boletin","id":"2964",
#    "attributes":{"numero":"57","fecha":"2026-07-17",
#                  "archivo":"https://.../Boletin_57_A7G3KkU.pdf",
#                  "publicado":"2026-07-17T07:30:00",
#                  "fecha_creado":"2026-07-16T12:07:30"},
#    "relationships":{"instrumento":{"data":{"type":"Instrumento","id":"5"}}}}
#
# Ojo con "fecha": conviven "fecha", "publicado" y "fecha_creado", y esta última
# suele ser del día ANTERIOR (el boletín se carga la víspera). Por eso se lee la
# clave exacta y sólo se cae a la búsqueda recursiva si no existe.
CAMPO_PDF = 'archivo'
CAMPO_FECHA = 'fecha'
CAMPO_NUMERO = 'numero'
CAMPO_PUBLICADO = 'publicado'

# El endpoint NO devuelve sólo el boletín regular: mezcla Suplementos, Separatas
# y Ediciones Complementarias, que tienen otra estructura interna (sin SUMARIO
# ni SECCIÓN OFICIAL). Si el bot agarrara uno de esos, el parser no encontraría
# nada y se saltearía en silencio el boletín real del día. Por eso se filtra por
# el nombre del instrumento, resuelto desde el bloque "included" de la respuesta.
INSTRUMENTO_BOLETIN = 'BOLETIN OFICIAL Y JUDICIAL'


def _norm_txt(s):
    s = (s or '').strip().upper()
    for a, b in (('Á', 'A'), ('É', 'E'), ('Í', 'I'), ('Ó', 'O'), ('Ú', 'U')):
        s = s.replace(a, b)
    return re.sub(r'\s+', ' ', s)


def _attrs(registro):
    """En JSON:API los campos viven bajo 'attributes'; toleramos que no."""
    if isinstance(registro, dict):
        a = registro.get('attributes')
        if isinstance(a, dict):
            return a
        return registro
    return {}


def _instrumento_id(registro):
    try:
        return str(registro['relationships']['instrumento']['data']['id'])
    except (KeyError, TypeError):
        return None


def _mapa_instrumentos(payload):
    """id -> nombre, a partir del bloque 'included' (viene con include=instrumento)."""
    mapa = {}
    for item in (payload.get('included') or []) if isinstance(payload, dict) else []:
        if item.get('type') == 'Instrumento':
            mapa[str(item.get('id'))] = _attrs(item).get('nombre')
    return mapa


def _iter_valores(obj, ruta=()):
    """Recorre un JSON anidado devolviendo (ruta_de_claves, valor) para cada hoja."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_valores(v, ruta + (str(k),))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _iter_valores(v, ruta + (str(i),))
    else:
        yield ruta, obj


def _buscar_pdf(registro):
    """Primera URL .pdf que aparezca en el registro, sin importar cómo se llame el campo."""
    for _, valor in _iter_valores(registro):
        if isinstance(valor, str) and RE_PDF.search(valor):
            if valor.startswith('http'):
                return valor
            return API_BASE + ('' if valor.startswith('/') else '/') + valor
    return None


def _buscar_valor(registro, nombres, validador=None):
    """Valor cuya clave contenga alguno de `nombres` (y opcionalmente valide)."""
    for ruta, valor in _iter_valores(registro):
        if not ruta:
            continue
        clave = ruta[-1].lower()
        if any(n in clave for n in nombres) and valor not in (None, ''):
            if validador is None or validador(valor):
                return valor
    return None


def _registros_de(payload):
    """Extrae la lista de boletines sea cual sea el envoltorio (JSON:API o DRF)."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for clave in ('data', 'results', 'items', 'objects'):
            valor = payload.get(clave)
            if isinstance(valor, list):
                return valor
        if payload.get('id') or payload.get('attributes'):
            return [payload]
    return []


def obtener_boletin_mas_reciente():
    """
    Devuelve (url_pdf, fecha_iso, numero) del boletín más reciente publicado.
    Lanza RuntimeError con un mensaje accionable si algo no se puede resolver.
    """
    params = {'ordering': '-fecha', 'page_size': 20, 'include': 'instrumento'}
    try:
        res = get_con_reintentos(API_BOLETINES, params=params, timeout=45)
        payload = res.json()
    except Exception as e:
        raise RuntimeError(f"No se pudo consultar la API del boletín: {e}")

    # Guardamos siempre la respuesta cruda: si la API cambia de forma, esto es
    # lo único que hace falta para saber qué pasó.
    try:
        guardar_para_debug(json.dumps(payload, ensure_ascii=False, indent=2),
                           'debug_catamarca_api.json')
    except Exception:
        pass

    registros = _registros_de(payload)
    if not registros:
        raise RuntimeError(
            "La API respondió pero no se reconoció ninguna lista de boletines. "
            "Revisar debug_catamarca_api.json.")

    instrumentos = _mapa_instrumentos(payload)
    objetivo = _norm_txt(INSTRUMENTO_BOLETIN)
    hoy = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    def fecha_de(reg):
        a = _attrs(reg)
        valor = a.get(CAMPO_FECHA)
        if isinstance(valor, str) and RE_FECHA_ISO.match(valor):
            return valor
        return _buscar_valor(reg, ('fecha', 'date'),
                             lambda v: isinstance(v, str) and RE_FECHA_ISO.match(v)) or ''

    def es_boletin_regular(reg):
        # Si no se puede resolver el instrumento, no descartamos: preferimos
        # intentar el parseo antes que saltear el boletín del día por las dudas.
        iid = _instrumento_id(reg)
        if iid is None or not instrumentos:
            return True
        nombre = instrumentos.get(iid)
        if nombre is None:
            return True
        return _norm_txt(nombre) == objetivo

    def ya_publicado(reg):
        pub = _attrs(reg).get(CAMPO_PUBLICADO)
        if isinstance(pub, str) and RE_FECHA_ISO.match(pub):
            return pub <= hoy      # el boletín se carga la víspera; no lo tomamos antes de hora
        return True

    candidatos = sorted(registros, key=fecha_de, reverse=True)
    descartados = []

    for reg in candidatos:
        a = _attrs(reg)
        if not es_boletin_regular(reg):
            descartados.append(f"{fecha_de(reg)[:10]} instrumento="
                               f"{instrumentos.get(_instrumento_id(reg))!r}")
            continue
        if not ya_publicado(reg):
            descartados.append(f"{fecha_de(reg)[:10]} aún no publicado "
                               f"({a.get(CAMPO_PUBLICADO)})")
            continue

        url_pdf = a.get(CAMPO_PDF) if isinstance(a.get(CAMPO_PDF), str) else None
        if not (url_pdf and RE_PDF.search(url_pdf)):
            url_pdf = _buscar_pdf(reg)
        if not url_pdf:
            descartados.append(f"{fecha_de(reg)[:10]} sin PDF")
            continue
        if not url_pdf.startswith('http'):
            url_pdf = API_BASE + ('' if url_pdf.startswith('/') else '/') + url_pdf

        numero = a.get(CAMPO_NUMERO)
        if numero is None:
            numero = _buscar_valor(reg, ('numero', 'number', 'nro'),
                                   lambda v: str(v).strip().isdigit())

        if descartados:
            print("Saltados: " + "; ".join(descartados[:5]), file=sys.stderr)
        return url_pdf, (fecha_de(reg)[:10] or None), (str(numero) if numero is not None else None)

    raise RuntimeError(
        "Ningún registro de la API resultó ser un boletín regular publicado con PDF. "
        + (f"Descartados: {'; '.join(descartados[:5])}. " if descartados else "")
        + "Revisar debug_catamarca_api.json.")


# ===========================================================================
# MAQUETA DEL PDF
# ===========================================================================
FUENTE_TITULO = 'CIDFont+F10'
FUENTE_NEGRITA = 'CIDFont+F7'
TAM_SECCION = 15
AZUL_TITULO = (0.0, 0.439216, 0.752941)

RE_ENCABEZADO_PAGINA = re.compile(
    r'^Boletín Oficial y Judicial N\.?[°º]\s*\d+\s+\d+\s+\d{1,2}/\d{1,2}/\d{4}\s*$')

SUBSECCIONES_NORMATIVA = {'DECRETOS', 'RESOLUCIONES'}

PATRON_DECRETO = re.compile(r'^Decreto\s+(.*?)N\.?[°º]\s*(\d+)\s*[-–]\s*(.*)$')
PATRON_RES_NUMERO = re.compile(
    r'^N\.?[°º]\s*(\d+)\s*[–-]\s*(\d{1,2}-\d{1,2}-\d{4})\s*[–-]\s*(.*)$')
PATRON_RES_CODIGO = re.compile(
    r'^(RES[A-Z]*)-(\d{4})-([A-Z0-9#\-]+?)\s*[–-]\s*(\d{1,2}-\d{1,2}-\d{4})\s*[–-]\s*(.*)$')
PATRON_FECHA_DECRETO = re.compile(
    r'San Fernando del Valle de Catamarca,\s*(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+(?:de\s+)?(\d{4})',
    re.IGNORECASE)

MESES = {'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
         'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
         'septiembre': '09', 'setiembre': '09', 'octubre': '10',
         'noviembre': '11', 'diciembre': '12'}

# Los decretos no llevan título de emisor: lo indican con una sigla en su propio
# número (Decreto "G.S.yJ." N.° 774). Si aparece un ministerio nuevo, se agrega acá.
SIGLAS_EMISOR = {
    'G.S.yJ.': 'MINISTERIO DE GOBIERNO, SEGURIDAD Y JUSTICIA',
    'E.yT.': 'MINISTERIO DE EDUCACION Y TRABAJO',
    'H.yO.P.': 'MINISTERIO DE HACIENDA Y OBRA PUBLICA',
    'S.': 'MINISTERIO DE SALUD',
    'D.S.': 'MINISTERIO DE DESARROLLO SOCIAL',
    'D.P.': 'MINISTERIO DE DESARROLLO PRODUCTIVO',
    'V.yU.': 'MINISTERIO DE VIVIENDA Y URBANIZACION',
    'A.E.yM.A.': 'MINISTERIO DE AGUA, ENERGIA Y MEDIO AMBIENTE',
    'M.': 'MINISTERIO DE MINERIA',
    'C.T.yD.': 'MINISTERIO DE CULTURA, TURISMO Y DEPORTE',
    'I.R.L.yT.': 'MINISTERIO DE INTEGRACION REGIONAL, LOGISTICA Y TRANSPORTE',
}

# Los decretos conjuntos ("H.yO.P. (P.) - E.yT.") se atribuyen al ministerio
# principal, el marcado con (P). Guardar el nombre compuesto crearía un emisor
# nuevo por cada combinación posible y fragmentaría la tabla emisor_norma.
# Poner en False si preferís conservar el nombre completo.
EMISOR_CONJUNTO_SOLO_PRINCIPAL = True

EMISOR_POR_DEFECTO = 'PODER EJECUTIVO PROVINCIAL'


# ===========================================================================
# CLASIFICACIÓN: ACTO GENERAL vs ACTO INDIVIDUAL
# ---------------------------------------------------------------------------
# El boletín mezcla normativa de alcance general con actos que afectan a una
# persona determinada (subsidios a pacientes, bajas, cesantías, designaciones).
# Estos últimos no son normativa de interés y además arrastran datos personales
# y de salud, así que no se cargan.
#
# El criterio es por puntaje: se considera individual si el total llega al
# UMBRAL. La sola mención de un DNI NO alcanza para descartar — hay normas
# generales que nombran personas (el alta de firmantes de cuentas bancarias
# menciona decenas de DNI y es un acto administrativo general) — por eso pesa
# apenas +1 y nunca decide sola.
#
# Para ajustar el comportamiento alcanza con tocar estas tablas.
# ===========================================================================
UMBRAL_INDIVIDUAL = 2

PATRONES_INDIVIDUALES = [
    (r'destinad[oa]s?\s+a(?:l|\s+la)?\s+paciente',            3, 'subsidio a paciente'),
    (r'para\s+(?:el|la)\s+paciente',                          3, 'subsidio a paciente'),
    (r'otorgar\s+un\s+subsidio',                              2, 'subsidio'),
    (r'Disp[óo]nese\s+la\s+BAJA',                             3, 'baja de agente'),
    (r'Disp[óo]ngase\s+la\s+Cesant[íi]a',                     3, 'cesantía'),
    (r'Recurso\s+de\s+Alzada\s+interpuesto\s+por',            3, 'recurso individual'),
    (r'Afectar\s+a\s+partir',                                 3, 'afectación de agente'),
    (r'Reub[íi]case\s+presupuestariamente\s+a',               3, 'reubicación de agente'),
    (r'Des[íi]gnase\s+en\s+el\s+cargo',                       2, 'designación'),
    (r'horas\s+extras[\s\S]{0,60}a\s+los\s+agentes',          3, 'horas extras nominadas'),
    (r'Cambio\s+Cuerpo\s+y\s+Escalaf[óo]n',                   3, 'cambio de escalafón'),
    (r'beneficiari[oa]\s+del\s+Programa\s+Federal',           1, 'beneficiario nominado'),
    (r'Rectificar[\s\S]{0,160}Documento\s+Nacional\s+de\s+Identidad',
                                                              3, 'rectifica dato personal'),
]

PATRONES_GENERALES = [
    (r'Modif[íi]case\s+los\s+cr[ée]ditos\s+presupuestarios',  -4, 'crédito presupuestario'),
    (r'Aprobar\s+el\s+Concurso\s+de\s+Precios',               -4, 'compra / licitación'),
    (r'Conf[íi]rmase\s+en\s+todas\s+sus\s+partes\s+el\s+Convenio',
                                                              -4, 'convenio con municipio'),
    (r'Ot[óo]rgase\s+a\s+los\s+beneficiarios\s+del\s+Programa',
                                                              -4, 'programa colectivo'),
    (r'Modif[íi]case\s+la\s+Planta\s+de\s+Personal',          -3, 'planta de personal'),
    (r'Registro\s+Nacional\s+de\s+Prestadores',               -4, 'habilitación de prestador'),
    (r'cambio\s+de\s+denominaci[óo]n',                        -4, 'cambio de denominación'),
    (r'Alta\s+de\s+Firmantes',                                -3, 'firmantes de cuentas'),
    (r'dar\s+de\s+Alta\s+como\s+Responsables\s+Firmantes',    -3, 'firmantes de cuentas'),
    (r'car[áa]cter\s+del\s+aporte\s+extraordinario',          -4, 'aporte a municipios'),
]

RE_DOCUMENTO = re.compile(r'\b(?:DNI|D\.N\.I|CUIL|CUIT)\b', re.IGNORECASE)


def clasificar_norma(texto):
    """Devuelve (es_individual, puntaje, motivos)."""
    puntaje = 0
    motivos = []
    for patron, peso, etiqueta in PATRONES_INDIVIDUALES:
        if re.search(patron, texto, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'+{peso} {etiqueta}')
    for patron, peso, etiqueta in PATRONES_GENERALES:
        if re.search(patron, texto, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'{peso} {etiqueta}')
    documentos = len(RE_DOCUMENTO.findall(texto))
    if documentos:
        puntaje += 1
        motivos.append(f'+1 menciona DNI/CUIL ({documentos})')
    return (puntaje >= UMBRAL_INDIVIDUAL), puntaje, motivos


# ===========================================================================
# EXTRACCIÓN DE LÍNEAS
# ===========================================================================
def _color_de_linea(pagina, top):
    return {c.get('non_stroking_color') for c in pagina.chars if abs(c['top'] - top) < 2}


def _lineas_de_pagina(pagina):
    palabras = pagina.extract_words(extra_attrs=['fontname', 'size'])
    palabras.sort(key=lambda w: (round(w['top'] / 3), w['x0']))

    grupos, actual, top_actual = [], [], None
    for w in palabras:
        t = round(w['top'] / 3) * 3
        if top_actual is None or abs(t - top_actual) <= 3:
            actual.append(w)
            top_actual = top_actual if top_actual is not None else t
        else:
            grupos.append(actual)
            actual, top_actual = [w], t
    if actual:
        grupos.append(actual)

    resultado = []
    for grupo in grupos:
        grupo.sort(key=lambda w: w['x0'])
        resultado.append({
            'texto': ' '.join(w['text'] for w in grupo),
            'fuentes': {w['fontname'] for w in grupo},
            'tam': round(max(w['size'] for w in grupo), 1),
            'azul': _color_de_linea(pagina, grupo[0]['top']) == {AZUL_TITULO},
        })
    return resultado


def leer_lineas_pdf(origen):
    """`origen` puede ser una ruta local o bytes ya descargados."""
    if pdfplumber is None:
        raise RuntimeError(
            "Falta el paquete 'pdfplumber' (pip install pdfplumber). Es "
            "imprescindible: la detección de títulos usa fuente y color, que el "
            "texto plano no conserva.")
    fuente = io.BytesIO(origen) if isinstance(origen, (bytes, bytearray)) else origen
    lineas = []
    with pdfplumber.open(fuente) as pdf:
        for nro, pagina in enumerate(pdf.pages):
            for linea in _lineas_de_pagina(pagina):
                linea['pagina'] = nro
                lineas.append(linea)
    return lineas


def _rango_seccion_oficial(lineas):
    inicio = fin = None
    for i, l in enumerate(lineas):
        if FUENTE_TITULO in l['fuentes'] and l['tam'] >= TAM_SECCION:
            titulo = l['texto'].strip().upper()
            if titulo == 'SECCIÓN OFICIAL' and inicio is None:
                inicio = i
            elif inicio is not None and titulo.startswith('SECCIÓN'):
                fin = i
                break
    if inicio is None:
        return None, None
    return inicio, (fin if fin is not None else len(lineas))


def _es_titulo_emisor(linea):
    t = linea['texto'].strip()
    return (linea['fuentes'] == {FUENTE_NEGRITA} and linea['azul']
            and t.isupper() and len(t) < 70)


def _emisor_desde_sigla(sigla):
    s = (sigla or '').strip().rstrip('-').strip()
    if not s:
        return None
    if s in SIGLAS_EMISOR:
        return SIGLAS_EMISOR[s]
    nombres = []
    for parte in [p.strip() for p in re.split(r'\s*-\s*', s) if p.strip()]:
        base = re.sub(r'\s*\(P\.?\)\s*', '', parte).strip()
        if base in SIGLAS_EMISOR:
            nombres.append(SIGLAS_EMISOR[base])
    if not nombres:
        return None
    if EMISOR_CONJUNTO_SOLO_PRINCIPAL:
        return nombres[0]
    return ' - '.join(nombres)


# ===========================================================================
# PARSEO DE NORMAS
# ===========================================================================
def _construir_sintesis(texto, tipo, numero):
    cuerpo = texto.strip(' .-')
    if len(cuerpo) > MAX_SINTESIS:
        cuerpo = cuerpo[:MAX_SINTESIS].rsplit(' ', 1)[0] + '…'
    return cuerpo or f"{tipo} {numero}"


def parsear_normas(origen_pdf):
    """
    Devuelve la lista de normas de la SECCIÓN OFICIAL (DECRETOS y RESOLUCIONES),
    ya clasificadas. No filtra: eso lo decide el llamador.
    """
    lineas = leer_lineas_pdf(origen_pdf)
    inicio, fin = _rango_seccion_oficial(lineas)
    if inicio is None:
        return []

    # --- Paso 1: encabezados ---------------------------------------------
    subseccion = None
    emisor_bloque = None
    encabezados = []

    for i in range(inicio, fin):
        linea = lineas[i]
        t = linea['texto'].strip()
        if not t or RE_ENCABEZADO_PAGINA.match(t):
            continue

        if FUENTE_TITULO in linea['fuentes'] and linea['tam'] < TAM_SECCION:
            # La última norma de la subsección que se cierra termina acá; si no,
            # se comería los EDICTOS / TRIBUNAL DE CUENTAS / SENADO que siguen.
            # Sólo la primera vez: los títulos posteriores no deben correr el tope.
            if encabezados and encabezados[-1].get('tope') is None:
                encabezados[-1]['tope'] = i
            subseccion = t.upper()
            emisor_bloque = None
            continue

        if _es_titulo_emisor(linea):
            emisor_bloque = t
            continue

        if subseccion not in SUBSECCIONES_NORMATIVA:
            continue

        if subseccion == 'DECRETOS':
            m = PATRON_DECRETO.match(t)
            if m:
                encabezados.append({
                    'idx': i, 'tipo': 'DECRETO', 'numero': m.group(2), 'anio': None,
                    'emisor': _emisor_desde_sigla(m.group(1)), 'fecha_cruda': None,
                    'pendiente': m.group(3).strip().lower().startswith('pendiente'),
                    'tope': None,
                })
                continue

        if subseccion == 'RESOLUCIONES':
            m = PATRON_RES_NUMERO.match(t)
            if m:
                encabezados.append({
                    'idx': i, 'tipo': 'RESOLUCION', 'numero': m.group(1), 'anio': None,
                    'emisor': emisor_bloque, 'fecha_cruda': m.group(2),
                    'pendiente': False, 'tope': None,
                })
                continue
            m = PATRON_RES_CODIGO.match(t)
            if m:
                # "RESOL-2026-41-E-CAT-SFP#MHOP": el año va aparte y el número es
                # el tramo intermedio. El último segmento es el código del
                # organismo (SFP#MHOP), que ya queda representado en el emisor.
                segmentos = m.group(3).split('-')
                numero = '-'.join(segmentos[:-1]) if len(segmentos) > 1 else m.group(3)
                encabezados.append({
                    'idx': i, 'tipo': 'RESOLUCION', 'numero': numero, 'anio': m.group(2),
                    'emisor': emisor_bloque, 'fecha_cruda': m.group(4),
                    'pendiente': False, 'tope': None,
                })
                continue

    # --- Paso 2: cuerpo de cada norma -------------------------------------
    normas = []
    for k, h in enumerate(encabezados):
        tope = encabezados[k + 1]['idx'] if k + 1 < len(encabezados) else fin
        if h.get('tope') is not None:
            tope = min(tope, h['tope'])

        cuerpo = []
        for x in range(h['idx'], tope):
            linea = lineas[x]
            t = linea['texto'].strip()
            if not t or RE_ENCABEZADO_PAGINA.match(t):
                continue
            if FUENTE_TITULO in linea['fuentes']:
                continue
            if _es_titulo_emisor(linea):
                continue
            cuerpo.append(t)
        texto = limpiar_texto(' '.join(cuerpo))

        if h['fecha_cruda']:
            d, mes, anio = h['fecha_cruda'].split('-')
            fecha = f"{anio}-{mes.zfill(2)}-{d.zfill(2)}"
            anio = h['anio'] or anio
        else:
            mf = PATRON_FECHA_DECRETO.search(texto)
            if mf:
                anio = mf.group(3)
                fecha = f"{anio}-{MESES.get(mf.group(2).lower(), '01')}-{mf.group(1).zfill(2)}"
            else:
                anio, fecha = None, None

        es_individual, puntaje, motivos = clasificar_norma(texto)

        normas.append({
            'tipo': h['tipo'],
            'numero': h['numero'],
            'anio': anio,
            'emisor': resolver_emisor(h['emisor']) or EMISOR_POR_DEFECTO,
            'fecha_publicacion': fecha,
            'texto_completo': texto[:MAX_TEXTO_COMPLETO],
            'sintesis': _construir_sintesis(texto, h['tipo'], h['numero']),
            'pendiente': h['pendiente'],
            'es_individual': es_individual,
            'puntaje': puntaje,
            'motivos': motivos,
        })
    return normas


def url_norma(url_pdf, tipo, numero):
    """
    Catamarca no tiene URL individual por norma: todas viven en el mismo PDF.
    Se manda la URL del PDF más un fragmento (#...) que identifica a la norma.
    Es necesario porque ingresar_scraping.php deduplica también por url_norma
    EXACTA además de tipo+numero+año+emisor: si todas compartieran la misma URL,
    en cuanto UNA quedara guardada las demás quedarían bloqueadas aunque fueran
    normas distintas. El fragmento no afecta la descarga del PDF.
    """
    slug = re.sub(r'[^A-Za-z0-9]+', '-', f"{tipo}-{numero}").strip('-')
    return f"{url_pdf}#{slug}"


# ===========================================================================
# EJECUCIÓN
# ===========================================================================
def _main():
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Catamarca.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', default='https://portal.catamarca.gob.ar/boletin/')
    ap.add_argument('--dry-run', action='store_true',
                    help='Parsea y muestra el resultado sin enviar nada al backend')
    ap.add_argument('--pdf', metavar='ARCHIVO',
                    help='Usar un PDF local en vez de descargarlo (para pruebas)')
    ap.add_argument('--todas', action='store_true',
                    help='En --dry-run, mostrar también las normas individuales')
    args = ap.parse_args()

    # 1. Ubicar el boletín y su PDF
    if args.pdf:
        origen, url_pdf, fecha_boletin, numero_boletin = args.pdf, args.pdf, None, None
        print(f"Usando PDF local: {args.pdf}", file=sys.stderr)
    else:
        try:
            url_pdf, fecha_boletin, numero_boletin = obtener_boletin_mas_reciente()
        except RuntimeError as e:
            salida("error", str(e))
        print(f"Boletín N° {numero_boletin or '?'} del {fecha_boletin or '?'}", file=sys.stderr)
        print(f"PDF: {url_pdf}", file=sys.stderr)

        if not args.dry_run and fecha_boletin:
            if verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
                salida("info", f"Boletín del {fecha_boletin} ya fue procesado")

        try:
            resp = get_con_reintentos(url_pdf, headers=HEADERS_DESCARGA, timeout=120)
            origen = resp.content
        except Exception as e:
            salida("error", f"No se pudo descargar el PDF: {e}")

    # 2. Parsear
    try:
        todas = parsear_normas(origen)
    except Exception as e:
        salida("error", f"No se pudo parsear el PDF: {e}")

    con_contenido = [n for n in todas if not n['pendiente']]
    generales = [n for n in con_contenido if not n['es_individual']]
    individuales = [n for n in con_contenido if n['es_individual']]

    if not con_contenido:
        salida("warning", "No se encontraron normas en la SECCIÓN OFICIAL del PDF")

    guardar_para_debug(
        '\n\n'.join(f"[{'IND' if n['es_individual'] else 'GEN'}] {n['tipo']} N° {n['numero']} "
                    f"({n['emisor']}, {n['fecha_publicacion']})\n{n['texto_completo']}"
                    for n in con_contenido),
        'debug_catamarca.txt')

    print(f"Normas con contenido: {len(con_contenido)} "
          f"(generales {len(generales)} / individuales {len(individuales)})", file=sys.stderr)

    # 3. Modo prueba
    if args.dry_run:
        for n in (con_contenido if args.todas else generales):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {n['tipo']:11s} N° {n['numero']:10s} "
                  f"{n['fecha_publicacion'] or '-':11s} {n['emisor'][:44]:44s} "
                  f"{len(n['texto_completo']):6d} car.")
            if args.todas and n['motivos']:
                print(f"      {'; '.join(n['motivos'])}")
        salida("success", "dry-run: no se envió nada al backend", total=len(generales))

    if not generales:
        salida("warning",
               f"Las {len(individuales)} normas del boletín son actos individuales; no se envió ninguna")

    # 4. Armar payload y enviar
    normas_completas = [{
        "id_jurisdiccion": args.id_jurisdiccion,
        "nombre_emisor": n["emisor"],
        "tipo_norma_desc": n["tipo"],
        "numero": n["numero"],
        "anio": n["anio"],
        "fecha_publicacion": n["fecha_publicacion"],
        "sintesis": n["sintesis"],
        "texto_completo": n["texto_completo"],
        "url_norma": url_norma(url_pdf, n["tipo"], n["numero"]),
    } for n in generales]

    try:
        headers_post = {"Authorization": f"Bearer {API_KEY_BACKEND}",
                        "Content-Type": "application/json"}
        res = requests.post(URL_GUARDAR_NORMAS, json={"normas": normas_completas},
                            headers=headers_post, timeout=120)
        res.raise_for_status()
        respuesta = res.json()
    except Exception as e:
        salida("error", f"Error enviando al backend: {e}")

    if fecha_boletin:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, len(normas_completas))

    salida("success", respuesta.get('mensaje', 'OK'), total=len(normas_completas))


if __name__ == '__main__':
    try:
        _main()
    except SystemExit:
        raise
    except Exception as e:
        salida("error", str(e))