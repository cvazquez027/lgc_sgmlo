import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import sys
import json
import time
import unicodedata
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 1. ESTO ES CLAVE: Obliga a webdriver-manager a instalar el driver en la carpeta actual, 
# evitando problemas de permisos en la carpeta /home o /root del servidor web.
os.environ['WDM_LOCAL'] = '1' 

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--disable-gpu")
opts.add_argument("--window-size=1920,1080")

# 2. Le indicamos la ruta exacta del binario de Chrome (ruta estándar en Ubuntu/Debian)
opts.binary_location = "/usr/bin/google-chrome" 

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=opts
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Forzar UTF-8
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- Argumentos ---
if len(sys.argv) < 3:
    print(json.dumps({"status": "error", "message": "Uso: bot_caba.py id_jurisdiccion url_boletin"}))
    sys.exit(1)

ID_JURISDICCION = int(sys.argv[1])
URL_BOLETIN = sys.argv[2]

# --- Configuración ---
API_KEY_BACKEND = os.getenv('API_KEY_BACKEND', 'Token_Seguro_Scraper_2026_XyZ!')
URL_HISTORIAL = os.getenv('URL_HISTORIAL', 'http://localhost/lgc_sgmlo/backend/api/boletin/historial_scraping.php')
URL_GUARDAR_NORMAS = os.getenv('URL_GUARDAR_NORMAS', 'http://localhost/lgc_sgmlo/backend/api/boletin/ingresar_scraping.php')

# Cota de tamaño del texto completo enviado por norma.
MAX_TEXTO_COMPLETO = 20000
# Espera máxima (segundos) por cada página de detalle.
TIMEOUT_DETALLE = 20

# ============================================================================
# NOTA DE ARQUITECTURA
# ----------------------------------------------------------------------------
# Este bot ya NO categoriza ni pide el diccionario de categorías.
# Toda la inteligencia (dedup de emisores por clave normalizada, categorización
# sobre texto completo) vive en el backend PHP (NormativaHelper.php).
# El bot solo:
#   1. Scrapea las normas del día (Selenium, porque el sitio bloquea requests).
#   2. Aísla el EMISOR limpio (texto antes del <a> del título de la norma).
#   3. Descarga el TEXTO COMPLETO de cada norma reutilizando el mismo navegador.
#   4. Manda todo crudo al backend.
# ============================================================================


# --- Funciones auxiliares ---
def salida(status, message, total=None):
    out = {"status": status, "message": message}
    if total is not None:
        out["total_enviadas"] = total
    print(json.dumps(out))
    sys.exit(0)


def log_info(msg):
    print(f"INFO: {msg}", file=sys.stderr)


def log_error(msg):
    print(f"ERROR: {msg}", file=sys.stderr)


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


def crear_driver():
    """Crea e inicializa un Chrome headless reutilizable."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    opts.binary_location = "/usr/bin/google-chrome"
    return webdriver.Chrome(service=service, options=chrome_options)


def cargar_boletin(driver, url):
    """Navega al boletín y devuelve el HTML renderizado de la portada."""
    log_info(f"Navegando a {url}")
    driver.get(url)
    log_info("Esperando a que cargue el contenido...")
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.divSeccion[seccion='Poder Ejecutivo'], div.divOrganismo, div.divTipoNorma")
            )
        )
        log_info("Contenido cargado correctamente")
    except Exception as e:
        log_error(f"Timeout esperando contenido: {e}")
        time.sleep(5)
    html = driver.page_source
    log_info(f"HTML obtenido, longitud: {len(html)}")
    return html


def descargar_texto_completo(driver, url_norma, ventana_principal):
    """
    Abre la página de detalle de la norma en una pestaña nueva (reutilizando el
    navegador Selenium, que ya pasó el bloqueo anti-bot), extrae el cuerpo y
    cierra la pestaña. Best-effort: si algo falla, devuelve "".
    """
    if not url_norma:
        return ""
    try:
        driver.switch_to.new_window('tab')
        driver.set_page_load_timeout(TIMEOUT_DETALLE)
        try:
            driver.get(url_norma)
        except Exception:
            # Timeout de carga: seguimos con lo que haya en page_source.
            pass
        time.sleep(1)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Intentar acotar al contenedor del texto de la norma; si no, todo el body.
        contenedor = (
            soup.find('div', id='cuerpoNorma')
            or soup.find('div', class_='norma')
            or soup.find('div', id='contenido')
            or soup.find('article')
            or soup.find('main')
            or soup.body
            or soup
        )
        for tag in contenedor.find_all(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        texto = contenedor.get_text(separator=' ', strip=True)
        texto = re.sub(r'\s+', ' ', texto)
        return texto[:MAX_TEXTO_COMPLETO]
    except Exception as e:
        log_error(f"No se pudo bajar texto completo de {url_norma}: {e}")
        return ""
    finally:
        # Cerrar la pestaña de detalle y volver a la principal.
        try:
            driver.close()
            driver.switch_to.window(ventana_principal)
        except Exception:
            pass


def extraer_fecha_boletin(soup):
    """Extrae la fecha del boletín desde el título h3."""
    try:
        titulo_h3 = soup.find('h3', id='boletinTit')
        if titulo_h3:
            texto = titulo_h3.get_text(strip=True)
            log_info(f"Título encontrado: {texto}")
            match = re.search(r'(\d{2})/(\d{2})/(\d{4})', texto)
            if match:
                dia, mes, anio = match.groups()
                return f"{anio}-{mes}-{dia}"
        texto_pagina = soup.get_text()
        matches = re.findall(r'(\d{2})/(\d{2})/(\d{4})', texto_pagina)
        if matches:
            dia, mes, anio = matches[0]
            log_info(f"Fecha encontrada en texto: {dia}/{mes}/{anio}")
            return f"{anio}-{mes}-{dia}"
        return None
    except Exception as e:
        log_error(f"Error en extraer_fecha_boletin: {e}")
        return None


def limpiar_emisor(emisor_raw):
    """
    Normaliza superficialmente el emisor para que el dedup del backend funcione
    bien. El backend hace la normalización fuerte (sin tildes, etc.); acá solo
    limpiamos espacios y capitalizamos de forma prolija.
    """
    emisor = re.sub(r'\s+', ' ', emisor_raw).strip()
    # Sacar dos puntos o guiones colgando al final.
    emisor = re.sub(r'[\s:;,\-–—]+$', '', emisor).strip()
    if not emisor:
        return "Poder Ejecutivo de la Ciudad de Buenos Aires"
    # Capitalización por palabra, respetando preposiciones/artículos en minúscula.
    minus = {'de', 'del', 'la', 'las', 'los', 'y', 'e', 'en', 'el'}
    palabras = emisor.split()
    out = []
    for i, w in enumerate(palabras):
        wl = w.lower()
        if i != 0 and wl in minus:
            out.append(wl)
        else:
            out.append(wl.capitalize())
    return ' '.join(out)


def extraer_emisor_desde_p(p_tag, a_tag):
    """
    El emisor es el texto que está ANTES del <a> dentro del <p>.
    Recorremos los nodos hijos del <p> hasta toparnos con el <a> y juntamos
    solo el texto previo. Esto evita el bug de mezclar emisor + tipo/numero +
    síntesis en un mismo campo.
    """
    fragmentos = []
    for nodo in p_tag.children:
        # Si llegamos al <a> del título de la norma, frenamos.
        if nodo is a_tag:
            break
        if getattr(nodo, 'name', None) == 'a':
            break
        # Texto plano
        if isinstance(nodo, str):
            fragmentos.append(nodo)
        else:
            # Otro tag previo al <a> (ej. <strong>EMISOR</strong>)
            fragmentos.append(nodo.get_text(separator=' ', strip=True))
    texto = ' '.join(f.strip() for f in fragmentos if f and f.strip())
    return texto


# Tipos de norma reconocidos en CABA. Se prueban del más LARGO al más corto
# para que "Resolución Comunal" gane sobre "Resolución".
TIPOS_NORMA_CABA = [
    'Resolución Conjunta',
    'Resolución Comunal',
    'Resolución General',
    'Resolución',
    'Disposición para Inscripción de CAA',
    'Disposición Conjunta',
    'Disposición',
    'Decreto',
    'Decisión Administrativa',
    'Acta',
    'Comunicación',
    'Ley',
]


def _quitar_tildes_upper(t):
    """Mayúsculas sin tildes, preservando la Ñ. Genérico (no lista fija)."""
    t = t.upper().strip()
    t = t.replace('Ñ', '\x00')  # proteger la eñe
    t = unicodedata.normalize('NFD', t)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return t.replace('\x00', 'Ñ')


def parsear_tipo_numero_anio(texto_link, fecha_boletin):
    """
    Extrae (tipo, numero, anio) del título de la norma de forma robusta.

    Maneja los casos problemáticos de CABA:
      - "Resolución de Presidencia N.º 19.518.681/COMUNA6/26"
            -> ('RESOLUCION', '19518681', '2026')
      - "Resolución Comunal N° 5/COMUNA6/2026"
            -> ('RESOLUCION COMUNAL', '5', '2026')  (tipo largo gana)
      - Año de 2 dígitos (/26 -> 2026), prefijos N° / N.º / Nº / Nro / N.
      - Números con puntos de miles (19.518.681 -> 19518681)
      - Palabras intermedias ("de Presidencia", "de Firma Conjunta")
    """
    txt = (texto_link or '').strip()
    anio_default = fecha_boletin[:4] if fecha_boletin else str(datetime.now().year)

    # 1) TIPO: el nombre más largo que matchee al inicio.
    tipo = None
    resto = txt
    for cand in sorted(TIPOS_NORMA_CABA, key=len, reverse=True):
        m = re.match(re.escape(cand), txt, re.IGNORECASE)
        if m:
            tipo = _quitar_tildes_upper(cand)
            resto = txt[m.end():]
            break
    if not tipo:
        return ("OTRO", "S/N", anio_default)

    # 2) Saltar hasta el prefijo de número (N° / N.º / Nº / Nro / N.) si existe.
    m_pref = re.search(r'N\s*[°º\.]?\s*º?\s*', resto, re.IGNORECASE)
    resto_num = resto[m_pref.end():] if m_pref else resto

    # 3) NÚMERO: primer bloque de dígitos (con puntos de miles), sin los puntos.
    m_num = re.search(r'(\d[\d\.]*)', resto_num)
    numero = m_num.group(1).replace('.', '') if m_num else "S/N"

    # 4) AÑO: último /AA o /AAAA al final del título. /26 -> 2026.
    anio = anio_default
    m_anio = re.search(r'/(\d{2,4})\s*$', txt)
    if m_anio:
        a = m_anio.group(1)
        anio = ('20' + a) if len(a) == 2 else a

    return (tipo, numero, anio)


def parsear_norma_caba(div_organismo, fecha_boletin):
    """Extrae los datos de una norma desde un div con clase 'divOrganismo'."""
    try:
        p_tag = div_organismo.find('p')
        if not p_tag:
            return None

        # 1. Link del título de la norma
        link = p_tag.find('a', href=True) or div_organismo.find('a', href=True)
        if not link:
            return None

        url_norma = link.get('href')
        if url_norma and not url_norma.startswith('http'):
            url_norma = f"https://boletinoficial.buenosaires.gob.ar{url_norma}"

        texto_link = link.get_text(strip=True)

        # 2. EMISOR: solo el texto previo al <a> (arreglo del bug).
        emisor_raw = extraer_emisor_desde_p(p_tag, link)
        if not emisor_raw:
            emisor_raw = "Poder Ejecutivo de la Ciudad de Buenos Aires"
        emisor = limpiar_emisor(emisor_raw)

        # 3. Tipo, número y año (parser robusto)
        tipo, numero, anio = parsear_tipo_numero_anio(texto_link, fecha_boletin)

        # 4. Síntesis: lo que viene después del <br> dentro del <p>
        sintesis = ""
        if p_tag.find('br'):
            contenido = str(p_tag)
            partes_sintesis = re.split(r'<br\s*/?>', contenido, maxsplit=1)
            if len(partes_sintesis) > 1:
                sintesis_html = partes_sintesis[1]
                sintesis_html = re.sub(r'<a[^>]*>.*?</a>', '', sintesis_html)
                sintesis_html = re.sub(r'<[^>]+>', ' ', sintesis_html)
                sintesis = ' '.join(sintesis_html.split()).strip()
                sintesis = re.sub(r'\s*Anexo\s*-\s*.*$', '', sintesis, flags=re.IGNORECASE).strip()

        if not sintesis:
            sintesis = texto_link

        return {
            "tipo": tipo,
            "numero": numero,
            "anio": anio,
            "emisor": emisor,
            "sintesis": sintesis,
            "fecha_publicacion": fecha_boletin,
            "url": url_norma
        }
    except Exception as e:
        log_error(f"Error parseando norma: {e}")
        return None


def extraer_normas_desde_html(soup, fecha_boletin):
    """Extrae todas las normas de la sección 'Poder Ejecutivo'."""
    normas = []
    try:
        seccion_pe = soup.find('div', class_='divSeccion', attrs={'seccion': 'Poder Ejecutivo'})
        if not seccion_pe:
            for div in soup.find_all('div', class_='divSeccion'):
                if div.get('seccion') == 'Poder Ejecutivo':
                    seccion_pe = div
                    break

        if not seccion_pe:
            log_error("No se encontró la sección 'Poder Ejecutivo'")
            with open('debug_caba_selenium.html', 'w', encoding='utf-8') as f:
                f.write(str(soup)[:10000])
            return normas

        divs_organismo = seccion_pe.find_all('div', class_='divOrganismo')
        log_info(f"Encontrados {len(divs_organismo)} divsOrganismo")

        for div in divs_organismo:
            norma_data = parsear_norma_caba(div, fecha_boletin)
            if norma_data:
                normas.append(norma_data)
    except Exception as e:
        log_error(f"Error en extraer_normas_desde_html: {e}")

    return normas


# --- Ejecución principal ---
driver = None
try:
    log_info(f"Iniciando bot_caba.py con ID={ID_JURISDICCION}, URL={URL_BOLETIN}")

    driver = crear_driver()
    html_content = cargar_boletin(driver, URL_BOLETIN)
    if not html_content:
        salida("error", "No se pudo obtener el contenido del boletín con Selenium")

    soup = BeautifulSoup(html_content, 'html.parser')
    log_info("HTML parseado correctamente")

    fecha_boletin = extraer_fecha_boletin(soup)
    if not fecha_boletin:
        fecha_boletin = datetime.now().strftime("%Y-%m-%d")
        log_info(f"Usando fecha actual como fallback: {fecha_boletin}")
    log_info(f"Fecha del boletín: {fecha_boletin}")

    if verificar_boletin_procesado(fecha_boletin):
        log_info(f"Boletín del {fecha_boletin} ya fue procesado")
        salida("info", f"Boletín del {fecha_boletin} ya fue procesado")

    normas_extraidas = extraer_normas_desde_html(soup, fecha_boletin)
    log_info(f"Normas extraídas: {len(normas_extraidas)}")
    if not normas_extraidas:
        salida("warning", "No se encontraron normas para la fecha")

    # Descargar el texto completo de cada norma reutilizando el navegador.
    ventana_principal = driver.current_window_handle
    for i, n in enumerate(normas_extraidas):
        n["texto_completo"] = descargar_texto_completo(driver, n["url"], ventana_principal)
        if (i + 1) % 10 == 0:
            log_info(f"Texto completo descargado: {i + 1}/{len(normas_extraidas)}")

    # Preparar payload (sin categorías: las calcula el backend).
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
            "texto_completo": n.get("texto_completo", ""),
            "url_norma": n["url"]
        })

    payload = {"normas": normas_completas}
    headers_post = {"Authorization": f"Bearer {API_KEY_BACKEND}", "Content-Type": "application/json"}

    # Timeout amplio: con ~200+ normas, el backend procesa todo en una transacción
    # y puede tardar. (connect_timeout, read_timeout)
    res_post = requests.post(URL_GUARDAR_NORMAS, json=payload, headers=headers_post, timeout=(15, 600))
    res_post.raise_for_status()
    respuesta = res_post.json()

    registrar_boletin_procesado(fecha_boletin, len(normas_completas))
    salida("success", respuesta.get('mensaje', 'OK'), total=len(normas_completas))

except Exception as e:
    log_error(f"Error: {e}")
    import traceback
    log_error(traceback.format_exc())
    salida("error", str(e))
finally:
    if driver:
        try:
            driver.quit()
            log_info("WebDriver cerrado")
        except Exception:
            pass
