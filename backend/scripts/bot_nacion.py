import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# ==========================================
# ⚙️ CONFIGURACIÓN DEL SISTEMA
# ==========================================
API_KEY_BACKEND = "Token_Seguro_Scraper_2026_XyZ!"
URL_LEER_CATEGORIAS = "http://localhost/lgc_sgmlo/backend/api/boletin/leer_categorias_bot.php"
URL_GUARDAR_NORMAS = "http://localhost/lgc_sgmlo/backend/api/boletin/ingresar_scraping.php"

# ID de la Jurisdicción (Nación)
ID_JURISDICCION_NACION = 1 

MAPEO_TIPOS = {
    "LEY": 1,
    "DECRETO": 2,
    "RESOLUCION": 3,
    "DISPOSICION": 4,
    "DECISION ADMINISTRATIVA": 5
}
ID_TIPO_DEFECTO = 5

# ==========================================
# 🧠 MOTOR DE CATEGORIZACIÓN DINÁMICO
# ==========================================
def obtener_diccionario_categorias():
    print("📡 Obteniendo categorías dinámicas desde la Base de Datos...")
    headers = {"Authorization": f"Bearer {API_KEY_BACKEND}"}
    try:
        res = requests.get(URL_LEER_CATEGORIAS, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json().get('categorias', [])
        
        diccionario = {}
        for cat in data:
            id_cat = cat['id_categoria']
            frase_clave = cat['descripcion'].strip()
            patron_regex = r'\b' + re.escape(frase_clave) + r'\b'
            diccionario[id_cat] = re.compile(patron_regex, re.IGNORECASE)
            
        print(f"✅ Se compilaron {len(diccionario)} reglas de búsqueda exactas.")
        return diccionario
    except Exception as e:
        print(f"❌ Error al obtener categorías del backend: {e}")
        return {}

def categorizar_texto(texto, diccionario_regex):
    if not texto: return []
    categorias_encontradas = set()
    texto_str = str(texto)
    for id_cat, regex in diccionario_regex.items():
        if regex.search(texto_str):
            categorias_encontradas.add(id_cat)
    return list(categorias_encontradas)

# ==========================================
# 🚀 EJECUCIÓN PRINCIPAL: SCRAPING BORA
# ==========================================
def ejecutar_bot_nacion():
    fecha_hoy_str = datetime.now().strftime('%Y-%m-%d')
    print(f"\n[{datetime.now()}] 🤖 Iniciando Bot NACIÓN para la fecha: {fecha_hoy_str}")
    
    diccionario_categorias = obtener_diccionario_categorias()
    if not diccionario_categorias: return
    
    # 1. EXTRACT: Scrapeamos la web del BORA (Primera Sección)
    URL_BORA = "https://www.boletinoficial.gob.ar/seccion/primera"
    print(f"📥 Entrando a la web oficial: {URL_BORA}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml'
        }
        res_web = requests.get(URL_BORA, headers=headers, timeout=15)
        res_web.raise_for_status()
    except Exception as e:
        print(f"❌ Error al conectar con la web de Nación: {e}")
        return

    soup = BeautifulSoup(res_web.text, 'html.parser')
    
    # Buscamos todos los enlaces a avisos en la primera sección
    avisos = soup.find_all('a', href=re.compile(r'/detalleAviso/primera/'))
    
    if not avisos:
        print("⚠️ No se encontraron normativas en el HTML.")
        return
        
    print(f"🔍 Se encontraron {len(avisos)} normativas potenciales. Procesando...")

    # 2. TRANSFORM: Recortamos y limpiamos
    normas_procesadas = []
    
    for link_tag in avisos:
        texto_completo = link_tag.text.strip()
        if not texto_completo:
            continue
            
        url_completa = f"https://www.boletinoficial.gob.ar{link_tag.get('href')}"
        
        # Extraer información del texto
        # Formato típico: "ORGANISMO Tipo N°/año CODIGO - Descripción"
        # Ejemplo: "MINISTERIO DE SALUD Decreto 326/2026 DECTO-2026-326-APN-PTE - Desígnase..."
        
        # Extraer organismo emisor (primera parte antes del tipo de norma)
        nombre_emisor = "PODER EJECUTIVO NACIONAL"
        
        # Buscar el tipo de norma y número
        match_tipo_numero = re.search(r'(Decreto|Decisión Administrativa|Resolución|Disposición|Ley|Aviso)\s+(\d+)/\d{4}', texto_completo, re.IGNORECASE)
        
        if match_tipo_numero:
            tipo_texto = match_tipo_numero.group(1).upper()
            numero = match_tipo_numero.group(2)  # Solo el número, sin el año
            
            # Extraer el organismo emisor (todo lo que está antes del tipo)
            pos_tipo = match_tipo_numero.start()
            if pos_tipo > 0:
                nombre_emisor = texto_completo[:pos_tipo].strip().upper()
        else:
            # Si no se encuentra el patrón estándar, buscar solo números
            match_numero = re.search(r'(\d+)/\d{4}', texto_completo)
            if match_numero:
                tipo_texto = "AVISO"
                numero = match_numero.group(1)  # Solo el número, sin el año
            else:
                tipo_texto = "AVISO"
                numero = "S/N"
        
        # Normalizar el tipo de norma para el mapeo
        tipo_normalizado = tipo_texto.replace("Ó", "O").upper()
        if "RESOLUCION" in tipo_normalizado:
            tipo_normalizado = "RESOLUCION"
        elif "DECISION" in tipo_normalizado:
            tipo_normalizado = "DECISION ADMINISTRATIVA"
        elif "DISPOSICION" in tipo_normalizado:
            tipo_normalizado = "DISPOSICION"
        elif "DECRETO" in tipo_normalizado:
            tipo_normalizado = "DECRETO"
        elif "LEY" in tipo_normalizado:
            tipo_normalizado = "LEY"
            
        id_tipo = MAPEO_TIPOS.get(tipo_normalizado, ID_TIPO_DEFECTO)
        
        # Gestión de Anexos y Síntesis
        sintesis_final = texto_completo
        if "ANEXO" in texto_completo.upper():
            sintesis_final = f"ANEXO - Referente a {tipo_texto} {numero}"
        
        # Categorización Dinámica
        categorias_detectadas = categorizar_texto(sintesis_final, diccionario_categorias)
        
        norma_formateada = {
            "id_jurisdiccion": ID_JURISDICCION_NACION,
            "nombre_emisor": nombre_emisor,
            "id_tipo_norma": id_tipo,
            "numero": numero,
            "anio": datetime.now().year,
            "fecha_publicacion": fecha_hoy_str,
            "sintesis": sintesis_final,
            "url_norma": url_completa,
            "categorias": categorias_detectadas
        }
        normas_procesadas.append(norma_formateada)

    if not normas_procesadas:
        print("ℹ️ No se pudo extraer información útil del HTML.")
        return

    # 3. LOAD: Enviar al Backend
    paquete_json = {"normas": normas_procesadas}
    headers_post = {"Authorization": f"Bearer {API_KEY_BACKEND}", "Content-Type": "application/json"}
    
    print(f"📤 Enviando {len(normas_procesadas)} normas procesadas al servidor PHP...")
    try:
        res_backend = requests.post(URL_GUARDAR_NORMAS, json=paquete_json, headers=headers_post)
        res_backend.raise_for_status()
        print(f"✅ ¡Éxito! {res_backend.json().get('mensaje')}")
    except Exception as e:
        print(f"❌ Error al insertar en la base de datos: {e}")
        if 'res_backend' in locals():
            print(f"Detalle: {res_backend.text}")

if __name__ == "__main__":
    ejecutar_bot_nacion()