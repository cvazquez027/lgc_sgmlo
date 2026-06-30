import os
import requests
import re
import sys
import json
import time
import io
from bs4 import BeautifulSoup
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
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- Argumentos ---
if len(sys.argv) < 3:
    print(json.dumps({"status": "error", "message": "Uso: bot_cordoba.py id_jurisdiccion url_boletin"}))
    sys.exit(1)

ID_JURISDICCION = int(sys.argv[1])
URL_BOLETIN = sys.argv[2]

# --- Configuración desde variables de entorno ---
def get_env_clean(key, default=None):
    value = os.getenv(key, default)
    if value:
        value = value.strip().strip('"').strip("'")
    return value

API_KEY_BACKEND = get_env_clean('API_KEY_BACKEND', 'Token_Seguro_Scraper_2026_XyZ!')
URL_HISTORIAL = get_env_clean('URL_HISTORIAL', 'http://localhost/lgc_sgmlo/backend/api/boletin/historial_scraping.php')
URL_GUARDAR_NORMAS = get_env_clean('URL_GUARDAR_NORMAS', 'http://localhost/lgc_sgmlo/backend/api/boletin/ingresar_scraping.php')

HEADERS_WEB = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================
def salida(status, message, total=None):
    out = {"status": status, "message": message}
    if total is not None:
        out["total_enviadas"] = total
    print(json.dumps(out))
    sys.exit(0)

def verificar_boletin_procesado(fecha_boletin):
    try:
        payload = {"id_jurisdiccion": ID_JURISDICCION, "fecha_boletin": fecha_boletin, "accion": "verificar"}
        headers = {"Authorization": f"Bearer {API_KEY_BACKEND}"}
        res = requests.post(URL_HISTORIAL, json=payload, headers=headers, timeout=10)
        return res.json().get('procesado', False)
    except Exception:
        return False

def registrar_boletin_procesado(fecha_boletin, cantidad):
    try:
        payload = {"id_jurisdiccion": ID_JURISDICCION, "fecha_boletin": fecha_boletin, "accion": "registrar", "cantidad_normas": cantidad}
        headers = {"Authorization": f"Bearer {API_KEY_BACKEND}"}
        requests.post(URL_HISTORIAL, json=payload, headers=headers, timeout=10)
    except Exception:
        pass

def guardar_texto_para_debug(texto, nombre_archivo="debug_cordoba.txt"):
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(texto)
        print(f"✅ Texto guardado en {nombre_archivo} para depuración", file=sys.stderr)
    except Exception as e:
        print(f"❌ Error guardando texto: {e}", file=sys.stderr)

def limpiar_texto(texto):
    if not texto:
        return ""
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def normalizar_emisor(emisor):
    if not emisor:
        return ""
    emisor = re.sub(r'^##?\s*', '', emisor).strip()
    emisor = emisor.upper()
    emisor = emisor.replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
    return emisor

# ============================================================================
# FUNCIONES ESPECÍFICAS PARA CÓRDOBA — PORTADA (HTML)
# ============================================================================
def extraer_fecha_boletin(soup):
    try:
        fecha_div = soup.find('div', class_='titudia')
        if fecha_div:
            texto = fecha_div.get_text(strip=True)
            meses = {
                'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
            }
            match = re.search(r'(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})', texto, re.IGNORECASE)
            if match:
                dia = match.group(1).zfill(2)
                mes_nombre = match.group(2).lower()
                anio = match.group(3)
                mes = meses.get(mes_nombre, '01')
                return f"{anio}-{mes}-{dia}"
        return None
    except Exception:
        return None

def obtener_url_pdf_seccion1(soup):
    try:
        boletin_items = soup.find_all('li')
        for li in boletin_items:
            a = li.find('a')
            if not a:
                continue
            h2 = a.find('h2')
            if not h2:
                continue
            texto = h2.get_text(strip=True)
            if '1° Sección' in texto or 'Legislación' in texto:
                url = a.get('href')
                if url and url.endswith('.pdf'):
                    return url
        return None
    except Exception:
        return None

# ============================================================================
# EXTRACCIÓN DE TEXTO DEL PDF — consciente de columnas y de "bandas"
# ----------------------------------------------------------------------------
# El BOE de Córdoba maqueta el PDF a 2 columnas estilo diario. Usar
# pdfplumber "ingenuamente" (page.extract_text()) intercala palabras de
# ambas columnas en la misma línea de texto (ej: una línea del "VISTO" de
# una norma se pega con una línea de otra norma de la columna vecina).
# Eso era la causa real de que se detectaran 18 normas en vez de 11: el
# recuadro SUMARIO de la portada quedaba mezclado en el cuerpo y, además,
# cortes de columna a mitad de oración generaban falsos inicios de norma
# (ej. "Decreto N° 3999/E/67..." quedando como si fuera un encabezado).
#
# Acá reconstruimos el orden de lectura real palabra por palabra:
#   1) cada palabra se asigna a columna izquierda o derecha según su X,
#   2) la página se separa en "bandas" verticales que arrancan en cada
#      encabezado de norma o de emisor — esto es necesario porque una
#      norma corta y la siguiente pueden compartir página maquetadas
#      como cajas de 2 columnas independientes (se ve, por ejemplo, entre
#      la Resolución 849 y la Resolución 238 de esta misma edición: la
#      849 termina en la columna derecha de "su" banda y recién ahí
#      arranca la banda de la 238, en vez de llenarse toda la columna
#      derecha de la página antes de pasar a la siguiente norma),
#   3) dentro de cada banda: toda la columna izquierda y luego toda la
#      columna derecha, de arriba hacia abajo.
# ============================================================================

TOP_MARGIN = 85    # excluye el encabezado de página que se repite arriba (~top<76)
BOTTOM_MARGIN = 800  # excluye el pie "BOLETIN OFICIAL... N" (~top>804)

PATRON_EMISOR = re.compile(
    r'^\s*(MINISTERIO\s+DE\s+[A-ZÁÉÍÓÚÑ\s]+|ENTE\s+REGULADOR\s+DE\s+SERVICIOS\s+PÚBLICOS|PODER\s+EJECUTIVO)'
)
# Variante "línea completa" (sin texto colgando después) — sirve para detectar
# encabezados reales de sección/emisor, a diferencia de referencias sueltas
# dentro de un párrafo (ese matiz es justamente el bug del script anterior:
# usaba re.IGNORECASE y .match(), así que una línea de cuerpo que arrancaba
# por wrap de ancho de columna, ej. "Ministerio de Educación;", también
# disparaba un cambio de emisor).
PATRON_EMISOR_COMPLETO = re.compile(
    r'^\s*(MINISTERIO\s+DE\s+[A-ZÁÉÍÓÚÑ\s]+|ENTE\s+REGULADOR\s+DE\s+SERVICIOS\s+PÚBLICOS|PODER\s+EJECUTIVO)\s*$'
)
PATRON_NORMA_COMPLETO = re.compile(
    r'^(Ley|Resoluci[oó]n(?:\s+General)?|Decreto|Decisi[oó]n Administrativa|Disposici[oó]n|Acta|Comunicaci[oó]n)'
    r'\s*N[°º]\s*([\d\.]+)(?:\s*-\s*Letra:\s*([A-Za-z]))?\s*$',
    re.IGNORECASE
)
FURNITURE_SUMARIO = {'legislación y', 'legislación y normativas', 'normativas', 'seccion', 'sección'}


def _es_inicio_de_banda(texto):
    """Una línea de la columna izquierda que es un encabezado real de norma
    o de emisor siempre arranca una "caja" de texto nueva (ver nota arriba)."""
    t = texto.strip()
    return bool(PATRON_NORMA_COMPLETO.match(t) or PATRON_EMISOR_COMPLETO.match(t))


def _detectar_split_columna(pdf):
    """Detecta dinámicamente el X donde se separan las 2 columnas, buscando
    el mayor "hueco" horizontal en la franja central de la página. Si no
    hay un hueco confiable (ej. una edición a una sola columna), no separa."""
    anchos = []
    huecos = []
    for page in pdf.pages:
        anchos.append(page.width)
        try:
            palabras = page.extract_words(keep_blank_chars=False, use_text_flow=False)
        except Exception:
            continue
        xs = sorted(w['x0'] for w in palabras if TOP_MARGIN < w['top'] < BOTTOM_MARGIN)
        centro_ini, centro_fin = page.width * 0.35, page.width * 0.65
        for a, b in zip(xs, xs[1:]):
            if centro_ini < a < centro_fin:
                huecos.append((b - a, (a + b) / 2))
    ancho_pagina = max(anchos) if anchos else 612.0
    if not huecos:
        return ancho_pagina + 1  # sin separación de columnas detectable
    huecos.sort(reverse=True)
    mejor_hueco, split_x = huecos[0]
    if mejor_hueco < 8:
        return ancho_pagina + 1  # hueco poco confiable -> tratar como 1 columna
    return split_x


def _agrupar_en_lineas(palabras):
    """Agrupa palabras (ya filtradas a UNA columna) en líneas de texto,
    devolviendo [(top, texto_linea), ...] ordenado de arriba hacia abajo."""
    palabras_ordenadas = sorted(palabras, key=lambda w: (round(w['top']), w['x0']))
    lineas, top_actual, linea_actual = [], None, []
    for w in palabras_ordenadas:
        t = round(w['top'] / 3) * 3
        if top_actual is None or abs(t - top_actual) <= 3:
            linea_actual.append(w)
            top_actual = top_actual if top_actual is not None else t
        else:
            lineas.append((top_actual, linea_actual))
            linea_actual = [w]
            top_actual = t
    if linea_actual:
        lineas.append((top_actual, linea_actual))
    resultado = []
    for top, linea in lineas:
        linea_ordenada = sorted(linea, key=lambda w: w['x0'])
        resultado.append((top, ' '.join(w['text'] for w in linea_ordenada)))
    return resultado


def _quitar_recuadro_sumario(lineas_top):
    """Quita el bloque contiguo del recuadro SUMARIO de la portada (si
    aparece en esta columna), incluyendo los títulos de sección que lo
    preceden y las entradas "Tipo N° X ... Pág. N" que lo siguen.
    Recibe y devuelve una lista de (top, texto)."""
    out = list(lineas_top)
    idx_sumario = None
    for i, (_, l) in enumerate(out):
        if l.strip().upper() == 'SUMARIO':
            idx_sumario = i
            break
    if idx_sumario is None:
        return out
    inicio = idx_sumario
    while inicio - 1 >= 0 and out[inicio - 1][1].strip().lower() in FURNITURE_SUMARIO:
        inicio -= 1
    fin = idx_sumario + 1
    while fin < len(out):
        l = out[fin][1].strip()
        if l == '' or re.search(r'Pág\.\s*\d+\s*$', l, re.IGNORECASE) or PATRON_EMISOR.match(l):
            fin += 1
            continue
        break
    return out[:inicio] + out[fin:]


def _extraer_lineas_pagina(page, split_x):
    """Devuelve las líneas de texto de UNA página, en orden de lectura real
    (ver explicación de "bandas" más arriba)."""
    palabras = page.extract_words(keep_blank_chars=False, use_text_flow=False)
    cuerpo = [w for w in palabras if TOP_MARGIN < w['top'] < BOTTOM_MARGIN]
    col_izq = [w for w in cuerpo if w['x0'] < split_x]
    col_der = [w for w in cuerpo if w['x0'] >= split_x]

    lineas_izq = _quitar_recuadro_sumario(_agrupar_en_lineas(col_izq))
    lineas_der = _quitar_recuadro_sumario(_agrupar_en_lineas(col_der))

    bandas_inicio = sorted(set(
        [float('-inf')] + [top for top, texto in lineas_izq if _es_inicio_de_banda(texto)]
    ))

    def _banda_de(top):
        banda = 0
        for i, inicio in enumerate(bandas_inicio):
            if top >= inicio:
                banda = i
        return banda

    bandas = {i: {'L': [], 'R': []} for i in range(len(bandas_inicio))}
    for top, texto in lineas_izq:
        bandas[_banda_de(top)]['L'].append(texto)
    for top, texto in lineas_der:
        bandas[_banda_de(top)]['R'].append(texto)

    resultado = []
    for i in range(len(bandas_inicio)):
        resultado.extend(bandas[i]['L'])
        resultado.extend(bandas[i]['R'])
    return resultado


def extraer_lineas_pdf(url_pdf):
    """Descarga el PDF y devuelve la lista de líneas de texto del documento
    completo, en orden de lectura real. Lista vacía si falla algo (el
    detalle se imprime a stderr para debug)."""
    if pdfplumber is None:
        print("❌ Falta el paquete 'pdfplumber' (pip install pdfplumber). "
              "Es imprescindible para leer el PDF a 2 columnas del BOE de Córdoba; "
              "sin posicionamiento por palabra no se puede reconstruir el orden de lectura.",
              file=sys.stderr)
        return []
    try:
        response = requests.get(url_pdf, headers=HEADERS_WEB, timeout=60)
        response.raise_for_status()
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            split_x = _detectar_split_columna(pdf)
            lineas = []
            for page in pdf.pages:
                lineas.extend(_extraer_lineas_pagina(page, split_x))
        return lineas
    except Exception as e:
        print(f"Error al descargar/parsear PDF: {e}", file=sys.stderr)
        return []

# ============================================================================
# PARSEO DE NORMAS
# ============================================================================
MESES = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
    'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
}
# Fecha de pie de norma: "Córdoba, dd de mes de aaaa" — el "de" antes del año
# es opcional porque las Resoluciones Generales del ERSEP a veces lo omiten
# ("Córdoba, 29 de Junio 2026").
PATRON_FECHA = re.compile(
    r'Córdoba,?\s*(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s*(?:de\s+)?(\d{4})',
    re.IGNORECASE
)


def _url_norma(url_pdf, tipo, numero):
    """
    Córdoba no tiene una URL individual por norma (las 11 normas del día
    viven en el mismo PDF de sección), así que la "url_norma" que mandamos
    es la del PDF + un fragmento (#...) que identifica a la norma puntual.
    Esto importa porque ingresar_scraping.php también deduplica por
    url_norma EXACTA, además de tipo+numero+año+emisor: si mandáramos la
    misma URL para las 11, en cuanto UNA quedara guardada en norma_bo (o
    en norma), las otras 10 —aunque sean tipo/numero distintos— quedarían
    bloqueadas igual, solo por compartir la URL del PDF. El fragmento no
    afecta la descarga del PDF (el navegador lo ignora al abrir el link).
    """
    slug = re.sub(r'[^A-Za-z0-9]+', '-', f"{tipo}-{numero}").strip('-')
    return f"{url_pdf}#{slug}"


def _unir_con_guiones(lineas):
    """Une las líneas de un bloque en un único texto, reconstruyendo
    palabras cortadas por guion de fin de línea (ej. "Ges-" + "tión" ->
    "Gestión") en vez de dejar el guion suelto, y normaliza espacios."""
    texto = ''
    for linea in lineas:
        l = linea.strip()
        if not l:
            continue
        if texto and re.search(r'[A-Za-zÁÉÍÓÚÑáéíóúñ]-$', texto) and re.match(r'^[A-Za-zÁÉÍÓÚÑáéíóúñ]', l):
            texto = texto[:-1] + l
        elif texto:
            texto += ' ' + l
        else:
            texto = l
    return limpiar_texto(texto)


def _construir_sintesis(texto_completo, tipo, numero, max_chars=700):
    """Síntesis corta para mostrar al usuario: el VISTO/CONSIDERANDO hasta
    antes de la parte resolutiva, recortado a un largo razonable. El texto
    completo (para categorizar) se manda aparte, sin recortar tanto."""
    m = re.search(r'RESUELVE\s*:', texto_completo)
    cuerpo = texto_completo[:m.start()] if m else texto_completo
    cuerpo = cuerpo.strip(' .-')
    if len(cuerpo) > max_chars:
        cuerpo = cuerpo[:max_chars].rsplit(' ', 1)[0] + '…'
    if not cuerpo:
        cuerpo = f"{tipo} {numero}"
    return cuerpo


def parsear_normas(lineas, fecha_boletin, url_pdf):
    """
    Recorre las líneas del PDF (ya en orden de lectura real) y arma una
    lista de normas: tipo, numero, anio, emisor, sintesis, texto_completo,
    fecha_publicacion.
    """
    # --- Paso 1: ubicar cada encabezado de norma y el emisor vigente en
    # ese punto (el emisor se actualiza con cada encabezado de sección que
    # vamos cruzando, ej. "MINISTERIO DE EDUCACIÓN") ---
    encabezados = []
    emisor_actual = None
    i = 0
    total = len(lineas)
    while i < total:
        linea = lineas[i].strip()

        m_emisor = PATRON_EMISOR.match(linea)
        if m_emisor:
            texto_emisor = linea
            # Títulos largos a veces se parten en 2 líneas, ej:
            #   "ENTE REGULADOR DE SERVICIOS PÚBLICOS"
            #   "- ERSEP"
            if i + 1 < total:
                siguiente = lineas[i + 1].strip()
                if re.match(r'^-\s*[A-ZÁÉÍÓÚÑ]+\s*$', siguiente):
                    texto_emisor = f"{linea} {siguiente}"
                    i += 1
            emisor_actual = normalizar_emisor(texto_emisor)
            i += 1
            continue

        m_norma = PATRON_NORMA_COMPLETO.match(linea)
        if m_norma:
            tipo_raw = m_norma.group(1).strip()
            num = m_norma.group(2).strip()
            letra = m_norma.group(3)
            numero = f"{num} - Letra:{letra.upper()}" if letra else num
            encabezados.append({
                'idx': i,
                'tipo_raw': tipo_raw,
                'numero': numero,
                'emisor': emisor_actual,
            })
        i += 1

    # --- Paso 2: para cada norma, su bloque de texto va desde justo
    # después de su encabezado hasta justo antes del próximo encabezado
    # (o hasta el final del documento, para la última norma) ---
    normas = []
    for idx_h, h in enumerate(encabezados):
        inicio = h['idx'] + 1
        fin = encabezados[idx_h + 1]['idx'] if idx_h + 1 < len(encabezados) else total
        bloque = lineas[inicio:fin]

        # Normalizar tipo (mismo criterio que usa el resto del sistema)
        tipo = tipo_raw_norm = h['tipo_raw'].upper()
        if tipo_raw_norm == "RESOLUCIÓN":
            tipo = "RESOLUCION"
        elif tipo_raw_norm == "RESOLUCIÓN GENERAL":
            tipo = "RESOLUCION GENERAL"

        # Fecha de la norma: primera ocurrencia de "Córdoba, dd de mes [de] aaaa"
        # dentro del bloque; si no aparece, usamos la fecha del boletín.
        anio = fecha_boletin.split('-')[0]
        fecha_encontrada = None
        for linea_b in bloque:
            mf = PATRON_FECHA.search(linea_b)
            if mf:
                dia = mf.group(1).zfill(2)
                mes_nombre = mf.group(2).lower()
                mes = MESES.get(mes_nombre)
                if mes:
                    anio = mf.group(3)
                    fecha_encontrada = f"{anio}-{mes}-{dia}"
                    break
        if not fecha_encontrada:
            fecha_encontrada = fecha_boletin

        texto_completo = _unir_con_guiones(bloque)
        if not texto_completo:
            texto_completo = f"{tipo} {h['numero']}"
        # Tope de tamaño por norma (igual criterio que bot_nacion.py)
        texto_completo = texto_completo[:20000]

        sintesis = _construir_sintesis(texto_completo, tipo, h['numero'])

        emisor = h['emisor'] or "PODER EJECUTIVO PROVINCIAL"

        normas.append({
            "tipo": tipo,
            "numero": h['numero'],
            "anio": anio,
            "emisor": emisor,
            "sintesis": sintesis,
            "texto_completo": texto_completo,
            "fecha_publicacion": fecha_encontrada,
            "url_norma": _url_norma(url_pdf, tipo, h['numero']),
        })

    return normas

# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================
try:
    # 1. Obtener HTML de la portada
    session = requests.Session()
    session.headers.update(HEADERS_WEB)

    # Primera visita para obtener cookies
    session.get(URL_BOLETIN, timeout=10)

    response = session.get(URL_BOLETIN, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # 2. Extraer fecha del boletín
    fecha_boletin = extraer_fecha_boletin(soup)
    if not fecha_boletin:
        salida("error", "No se pudo determinar la fecha del boletín")

    print(f"📅 Fecha del boletín: {fecha_boletin}", file=sys.stderr)

    # 3. Verificar si ya fue procesado
    if verificar_boletin_procesado(fecha_boletin):
        salida("info", f"Boletín del {fecha_boletin} ya fue procesado")

    # 4. Obtener URL del PDF de la 1° Sección
    url_pdf = obtener_url_pdf_seccion1(soup)
    if not url_pdf:
        salida("error", "No se encontró el PDF de la 1° Sección")

    print(f"📄 Descargando PDF: {url_pdf}", file=sys.stderr)

    # 5. Descargar y extraer las líneas de texto del PDF (orden de lectura real)
    lineas_pdf = extraer_lineas_pdf(url_pdf)
    if not lineas_pdf:
        salida("error", "No se pudo extraer texto del PDF")

    # 6. GUARDAR TEXTO PARA DEPURACIÓN (ya reconstruido/legible, no el crudo de pdfplumber)
    guardar_texto_para_debug('\n'.join(lineas_pdf), "debug_cordoba.txt")

    # 7. Parsear normas desde las líneas
    normas_extraidas = parsear_normas(lineas_pdf, fecha_boletin, url_pdf)
    if not normas_extraidas:
        salida("warning", "No se encontraron normas en el PDF")

    print(f"📋 Normas extraídas: {len(normas_extraidas)}", file=sys.stderr)

    # 8. Preparar payload para el backend
    normas_completas = []
    for n in normas_extraidas:
        normas_completas.append({
            "id_jurisdiccion": ID_JURISDICCION,
            "nombre_emisor": n["emisor"],
            "tipo_norma_desc": n["tipo"],
            "numero": n["numero"],
            "anio": n["anio"],
            "fecha_publicacion": n["fecha_publicacion"],
            "sintesis": n["sintesis"],
            "texto_completo": n["texto_completo"],  # Texto completo de la norma, para categorizar en el backend
            "url_norma": n["url_norma"]  # URL del PDF + fragmento único por norma (ver _url_norma)
        })

    # 9. Enviar al backend
    payload = {"normas": normas_completas}
    headers_post = {"Authorization": f"Bearer {API_KEY_BACKEND}", "Content-Type": "application/json"}
    res = requests.post(URL_GUARDAR_NORMAS, json=payload, headers=headers_post, timeout=120)
    res.raise_for_status()
    respuesta = res.json()

    # 10. Registrar en historial
    registrar_boletin_procesado(fecha_boletin, len(normas_completas))

    salida("success", respuesta.get('mensaje', 'OK'), total=len(normas_completas))

except Exception as e:
    salida("error", str(e))
