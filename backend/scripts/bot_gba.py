import os
import requests
import re
import sys
import json
from bs4 import BeautifulSoup
from datetime import datetime

# Intentar cargar variables de entorno desde .env
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
    print(json.dumps({"status": "error", "message": "Uso: bot_gba.py id_jurisdiccion url_boletin"}))
    sys.exit(1)

ID_JURISDICCION = int(sys.argv[1])
URL_BOLETIN = sys.argv[2]  # Solo usado para extraer la fecha

# --- Configuración desde variables de entorno ---
API_KEY_BACKEND = os.getenv('API_KEY_BACKEND', 'Token_Seguro_Scraper_2026_XyZ!')
URL_HISTORIAL = os.getenv('URL_HISTORIAL', 'http://localhost/lgc_sgmlo/backend/api/boletin/historial_scraping.php')
URL_GUARDAR_NORMAS = os.getenv('URL_GUARDAR_NORMAS', 'http://localhost/lgc_sgmlo/backend/api/boletin/ingresar_scraping.php')

HEADERS_WEB = {'User-Agent': 'Mozilla/5.0'}

# ============================================================================
# NOTA DE ARQUITECTURA
# ----------------------------------------------------------------------------
# Este bot ya NO categoriza ni pide el diccionario de categorías.
# Toda la inteligencia (dedup de emisores, categorización sobre texto completo)
# vive en el backend PHP (NormativaHelper.php). El bot solo:
#   1. Scrapea las normas del día.
#   2. Descarga el TEXTO COMPLETO de cada norma (campo "texto_completo").
#   3. Manda todo crudo al backend.
# Para crear un bot de otra jurisdicción, copiar esta estructura y reescribir
# solo las funciones de scraping/extracción.
# ============================================================================


# --- Funciones auxiliares ---
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


def extraer_fecha_boletin():
    """Obtiene la fecha del último boletín desde la página principal."""
    try:
        res = requests.get(URL_BOLETIN, headers=HEADERS_WEB, timeout=30)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        fecha_div = soup.find('div', class_='bulletin-date')
        if fecha_div:
            p_tag = fecha_div.find('p', class_='last-bulletin')
            if p_tag:
                strong = p_tag.find('strong')
                if strong:
                    texto = strong.get_text(strip=True)
                    m = re.search(r'(\d{2})/(\d{2})/(\d{4})', texto)
                    if m:
                        dia, mes, anio = m.groups()
                        return f"{anio}-{mes}-{dia}"
        return None
    except Exception:
        return None


def limpiar_emisor(emisor):
    if not emisor:
        return ""
    emisor = re.sub(r'^DE\s+LA\s+', '', emisor, flags=re.IGNORECASE).strip()
    emisor = re.sub(r'^DEL\s+', '', emisor, flags=re.IGNORECASE).strip()
    return emisor


def descargar_texto_completo(url_norma):
    """
    Descarga la página de detalle de la norma y extrae el texto completo del cuerpo,
    para que el backend pueda categorizar sobre el contenido real y no solo la síntesis.
    Best-effort: si falla, devuelve "" y el backend cae a categorizar la síntesis.
    """
    try:
        res = requests.get(url_norma, headers=HEADERS_WEB, timeout=30)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        # Intentar acotar al contenedor principal del texto de la norma.
        contenedor = (
            soup.find('div', class_='rule-text')
            or soup.find('div', class_='rule-content')
            or soup.find('article')
            or soup.find('main')
        )
        nodo = contenedor if contenedor else soup

        # Quitar ruido (scripts, estilos, navegación)
        for tag in nodo.find_all(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        texto = nodo.get_text(separator=' ', strip=True)
        texto = re.sub(r'\s+', ' ', texto)
        # Cota de tamaño para no enviar payloads gigantes.
        return texto[:20000]
    except Exception:
        return ""


def extraer_normas_desde_buscador(fecha_iso):
    fecha_dd_mm_aaaa = datetime.strptime(fecha_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    base_url = "https://normas.gba.gob.ar/resultados"
    params = {
        "q[date_ranges][publication_date][gte]": fecha_dd_mm_aaaa,
        "q[date_ranges][publication_date][lte]": fecha_dd_mm_aaaa,
        "q[sort]": "by_publication_date_desc",
        "page": 1
    }
    todas_normas = []
    page = 1
    while True:
        params["page"] = page
        try:
            res = requests.get(base_url, params=params, headers=HEADERS_WEB, timeout=30)
            res.raise_for_status()
        except Exception:
            break
        soup = BeautifulSoup(res.text, 'html.parser')
        cards = soup.find_all('div', class_='card rule-card')
        if not cards:
            break
        for card in cards:
            link = card.find('h3', class_='rule-name')
            if not link:
                continue
            a = link.find('a')
            if not a:
                continue
            url_rel = a.get('href')
            url_norma = f"https://normas.gba.gob.ar{url_rel}"
            titulo = a.get_text(strip=True)
            tipo = ""
            numero = ""
            anio = ""
            partes = titulo.rsplit(' ', 1)
            if len(partes) == 2:
                tipo = partes[0].upper()
                resto = partes[1]
                if '/' in resto:
                    num, ann = resto.split('/')
                    numero = num
                    anio = ann
                else:
                    numero = resto
                    anio = fecha_iso.split('-')[0]
            else:
                tipo = titulo.upper()
                numero = "S/N"
                anio = fecha_iso.split('-')[0]
            tipo = tipo.replace('RESOLUCIÓN', 'RESOLUCION').replace('DISPOSICIÓN', 'DISPOSICION')
            emisor_elem = card.find('h6', class_='rule-source')
            emisor = emisor_elem.get_text(strip=True) if emisor_elem else ""
            if emisor.startswith('del '):
                emisor = emisor[4:]
            emisor = limpiar_emisor(emisor)
            if tipo == "DECRETO":
                emisor = "Poder Ejecutivo Provincial"
            if not emisor:
                emisor = "Poder Ejecutivo Provincial"
            blockquote = card.find('blockquote')
            sintesis = blockquote.get_text(strip=True) if blockquote else ""
            fecha_publicacion = fecha_iso
            for p in card.find_all('p'):
                if 'Fecha de publicación:' in p.get_text():
                    texto = p.get_text(strip=True)
                    m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
                    if m:
                        fecha_publicacion = datetime.strptime(m.group(1), "%d/%m/%Y").strftime("%Y-%m-%d")
                    break

            # Descargar el texto completo de la norma para categorización en backend.
            texto_completo = descargar_texto_completo(url_norma)

            todas_normas.append({
                "tipo": tipo,
                "numero": numero,
                "anio": anio,
                "emisor": emisor,
                "sintesis": sintesis,
                "texto_completo": texto_completo,
                "fecha_publicacion": fecha_publicacion,
                "url": url_norma
            })
        pagination = soup.find('ul', class_='pagination')
        if pagination:
            next_link = pagination.find('a', rel='next')
            if next_link and 'href' in next_link.attrs:
                page += 1
                continue
        break
    return todas_normas


# --- Ejecución principal ---
try:
    fecha_boletin = extraer_fecha_boletin()
    if not fecha_boletin:
        salida("error", "No se pudo determinar la fecha del boletín")

    if verificar_boletin_procesado(fecha_boletin):
        salida("info", f"Boletín del {fecha_boletin} ya fue procesado")

    normas_extraidas = extraer_normas_desde_buscador(fecha_boletin)
    if not normas_extraidas:
        salida("warning", "No se encontraron normas para la fecha")

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
            "texto_completo": n["texto_completo"],
            "url_norma": n["url"]
        })

    payload = {"normas": normas_completas}
    headers_post = {"Authorization": f"Bearer {API_KEY_BACKEND}", "Content-Type": "application/json"}
    res = requests.post(URL_GUARDAR_NORMAS, json=payload, headers=headers_post, timeout=120)
    res.raise_for_status()
    respuesta = res.json()
    registrar_boletin_procesado(fecha_boletin, len(normas_completas))
    salida("success", respuesta.get('mensaje', 'OK'), total=len(normas_completas))

except Exception as e:
    salida("error", str(e))
