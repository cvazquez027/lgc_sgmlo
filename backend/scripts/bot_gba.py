import requests
import re
import sys
import json
from bs4 import BeautifulSoup
from datetime import datetime

# Forzar UTF-8
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- Argumentos ---
if len(sys.argv) < 3:
    print(json.dumps({"status": "error", "message": "Uso: bot_gba.py id_jurisdiccion url_boletin"}))
    sys.exit(1)

ID_JURISDICCION = int(sys.argv[1])
URL_BOLETIN = sys.argv[2]  # Solo usado para extraer la fecha

API_KEY_BACKEND = "Token_Seguro_Scraper_2026_XyZ!"
URL_HISTORIAL = "https://matrizonline.lamas-gc-com/backend/api/boletin/historial_scraping.php"
URL_LEER_CATEGORIAS = "https://matrizonline.lamas-gc-com/backend/api/boletin/leer_categorias_bot.php"
URL_GUARDAR_NORMAS = "https://matrizonline.lamas-gc-com/backend/api/boletin/ingresar_scraping.php"

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
    except:
        return False

def registrar_boletin_procesado(fecha_boletin, cantidad):
    try:
        payload = {"id_jurisdiccion": ID_JURISDICCION, "fecha_boletin": fecha_boletin, "accion": "registrar", "cantidad_normas": cantidad}
        headers = {"Authorization": f"Bearer {API_KEY_BACKEND}"}
        requests.post(URL_HISTORIAL, json=payload, headers=headers, timeout=10)
    except:
        pass

def obtener_diccionario_categorias():
    headers = {"Authorization": f"Bearer {API_KEY_BACKEND}"}
    try:
        res = requests.get(URL_LEER_CATEGORIAS, headers=headers, timeout=10)
        data = res.json().get('categorias', [])
        dic = {}
        for cat in data:
            id_cat = cat['id_categoria']
            frase = cat['descripcion'].strip()
            dic[id_cat] = re.compile(r'\b' + re.escape(frase) + r'\b', re.IGNORECASE)
        return dic
    except:
        return {}

def categorizar_texto(texto, dic):
    if not texto: return []
    encontradas = set()
    for id_cat, regex in dic.items():
        if regex.search(str(texto)):
            encontradas.add(id_cat)
    return list(encontradas)

def extraer_fecha_boletin():
    """Obtiene la fecha del último boletín desde la página principal."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(URL_BOLETIN, headers=headers, timeout=30)
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
    except Exception as e:
        return None

def limpiar_emisor(emisor):
    """Elimina prefijos no deseados como 'DE LA ' y normaliza espacios."""
    if not emisor:
        return ""
    # Eliminar "DE LA " (insensible a mayúsculas/minúsculas) del inicio
    emisor = re.sub(r'^DE\s+LA\s+', '', emisor, flags=re.IGNORECASE).strip()
    # También eliminar "DEL " si apareciera (por consistencia)
    emisor = re.sub(r'^DEL\s+', '', emisor, flags=re.IGNORECASE).strip()
    return emisor

def extraer_normas_desde_buscador(fecha_iso):
    """Realiza la búsqueda en normas.gba.gob.ar y extrae todas las normas de todas las páginas."""
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
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    while True:
        params["page"] = page
        try:
            res = requests.get(base_url, params=params, headers=headers, timeout=30)
            res.raise_for_status()
        except Exception as e:
            break
        
        soup = BeautifulSoup(res.text, 'html.parser')
        cards = soup.find_all('div', class_='card rule-card')
        if not cards:
            break
        
        for card in cards:
            # Enlace y título
            link = card.find('h3', class_='rule-name')
            if not link:
                continue
            a = link.find('a')
            if not a:
                continue
            url_rel = a.get('href')
            url_norma = f"https://normas.gba.gob.ar{url_rel}"
            titulo = a.get_text(strip=True)
            
            # Parsear tipo, número y año desde el título
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
            
            # Normalizar tipo (eliminar acentos)
            tipo = tipo.replace('RESOLUCIÓN', 'RESOLUCION').replace('DISPOSICIÓN', 'DISPOSICION')
            
            # Extraer emisor
            emisor_elem = card.find('h6', class_='rule-source')
            emisor = emisor_elem.get_text(strip=True) if emisor_elem else ""
            if emisor.startswith('del '):
                emisor = emisor[4:]
            
            # --- MEJORA 1: Limpiar prefijos no deseados ---
            emisor = limpiar_emisor(emisor)
            
            # --- MEJORA 2: Para decretos, forzar emisor específico ---
            if tipo == "DECRETO":
                emisor = "Poder Ejecutivo Provincial"
            # Si el emisor quedó vacío, asignar valor por defecto (no debería ocurrir)
            if not emisor:
                emisor = "Poder Ejecutivo Provincial"
            
            # Extraer resumen
            blockquote = card.find('blockquote')
            sintesis = blockquote.get_text(strip=True) if blockquote else ""
            
            # Extraer fecha de publicación
            fecha_publicacion = fecha_iso
            for p in card.find_all('p'):
                if 'Fecha de publicación:' in p.get_text():
                    texto = p.get_text(strip=True)
                    m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
                    if m:
                        fecha_publicacion = datetime.strptime(m.group(1), "%d/%m/%Y").strftime("%Y-%m-%d")
                    break
            
            todas_normas.append({
                "tipo": tipo,
                "numero": numero,
                "anio": anio,
                "emisor": emisor,
                "sintesis": sintesis,
                "fecha_publicacion": fecha_publicacion,
                "url": url_norma
            })
        
        # Paginación
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
    # 1. Obtener fecha del boletín
    fecha_boletin = extraer_fecha_boletin()
    if not fecha_boletin:
        salida("error", "No se pudo determinar la fecha del boletín")
    
    # 2. Verificar historial
    if verificar_boletin_procesado(fecha_boletin):
        salida("info", f"Boletín del {fecha_boletin} ya fue procesado")
    
    # 3. Extraer normas desde el buscador
    normas_extraidas = extraer_normas_desde_buscador(fecha_boletin)
    if not normas_extraidas:
        salida("warning", "No se encontraron normas para la fecha")
    
    # 4. Obtener diccionario de categorías
    categorias = obtener_diccionario_categorias()
    
    # 5. Construir el array de normas a enviar
    normas_completas = []
    for n in normas_extraidas:
        cats = categorizar_texto(n["sintesis"], categorias) if categorias else []
        normas_completas.append({
            "id_jurisdiccion": ID_JURISDICCION,
            "nombre_emisor": n["emisor"],
            "tipo_norma_desc": n["tipo"],
            "numero": n["numero"],
            "anio": n["anio"],
            "fecha_publicacion": n["fecha_publicacion"],
            "sintesis": n["sintesis"],
            "url_norma": n["url"],
            "categorias": cats
        })
    
    # 6. Enviar al backend
    payload = {"normas": normas_completas}
    headers_post = {"Authorization": f"Bearer {API_KEY_BACKEND}", "Content-Type": "application/json"}
    res = requests.post(URL_GUARDAR_NORMAS, json=payload, headers=headers_post, timeout=30)
    res.raise_for_status()
    respuesta = res.json()
    
    # 7. Registrar historial
    registrar_boletin_procesado(fecha_boletin, len(normas_completas))
    
    # 8. Éxito
    salida("success", respuesta.get('mensaje', 'OK'), total=len(normas_completas))
    
except Exception as e:
    salida("error", str(e))