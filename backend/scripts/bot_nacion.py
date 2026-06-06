import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import sys

# Forzar a Python a escupir los prints en UTF-8 sin importar lo que diga Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    
# ==========================================
# ⚙️ CONFIGURACIÓN DEL SISTEMA
# ==========================================
API_KEY_BACKEND = "Token_Seguro_Scraper_2026_XyZ!"
URL_LEER_CATEGORIAS = "http://localhost/lgc_sgmlo/backend/api/boletin/leer_categorias_bot.php"
URL_GUARDAR_NORMAS = "http://localhost/lgc_sgmlo/backend/api/boletin/ingresar_scraping.php"

# ID de la Jurisdicción (Nación)
ID_JURISDICCION_NACION = 1 

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

    # 2. TRANSFORM: Extracción Inteligente
    normas_procesadas = []
    
    # REGEX MAESTRO: Detecta N°, Nro, y soporta Comunicación "A"
    patron_tipos = r'^(Decreto Sintetizado|Decreto|Decisión Administrativa|Resolución Conjunta|Resolución Sintetizada|Resolución|Disposición Sintetizada|Disposición|Ley|Acuerdo|Acta|Circular|Comunicación(?:\s+"[A-Z0-9]+")?|Convenio|Directiva|Instrucción|Providencia|Recomendación|Reglamento|Aviso Oficial|Aviso)\s*(?:N[°º]\s*|Nro\.?\s*|N\.\s*)?(\d+|S/N)?(?:/(\d{4}))?'
    
    for link_tag in avisos:
        # Usamos un separador para aislar los bloques HTML y no mezclar Emisor con Tipo
        texto_completo = link_tag.get_text(separator=' | ', strip=True)
        if not texto_completo:
            continue
            
        url_completa = f"https://www.boletinoficial.gob.ar{link_tag.get('href')}"
        
        # Dividimos el texto en partes analizando las etiquetas HTML ocultas
        partes = [p.strip() for p in texto_completo.split(' | ') if p.strip()]
        
        matches_encontrados = []
        
        # Escaneamos bloque por bloque buscando la norma
        for i, part in enumerate(partes):
            m = re.search(patron_tipos, part, re.IGNORECASE)
            if m:
                matches_encontrados.append({
                    'index': i,
                    'tipo': m.group(1).upper().strip(),
                    'numero': m.group(2) if m.group(2) else "S/N",
                    'anio': m.group(3) if m.group(3) else str(datetime.now().year),
                    'raw': part
                })
                
        if matches_encontrados:
            # Si hay varias, filtramos "Aviso Oficial" para darle prioridad a "Comunicación"
            principales = [m for m in matches_encontrados if "AVISO" not in m['tipo']]
            if principales:
                elegido = principales[-1] # Tomamos la más específica (Ej: Comunicación "A")
            else:
                elegido = matches_encontrados[0] # Si solo hay Avisos, tomamos ese
                
            tipo_norma_desc = elegido['tipo']
            numero = elegido['numero']
            anio = elegido['anio']
            
            # Búsqueda Inteligente del Emisor (Suele ser el bloque anterior a la norma)
            idx = elegido['index']
            nombre_emisor = "PODER EJECUTIVO NACIONAL"
            if idx > 0:
                candidato = partes[idx - 1]
                # Si el bloque anterior era una fecha, buscamos uno más atrás
                if re.match(r'^\d{2}/\d{2}/\d{4}$', candidato) and idx > 1:
                    candidato = partes[idx - 2]
                nombre_emisor = candidato.strip()
            elif idx == 0 and len(partes) > 1:
                nombre_emisor = partes[1].strip()
                
        else:
            # Fallback en caso de formato desconocido
            tipo_norma_desc = "AVISO OFICIAL"
            numero = "S/N"
            anio = str(datetime.now().year)
            nombre_emisor = "PODER EJECUTIVO NACIONAL"
            
        # Limpieza final de caracteres extraños en el Emisor
        nombre_emisor = re.sub(r'^[^A-ZÁÉÍÓÚÑ]+', '', nombre_emisor, flags=re.IGNORECASE).strip()
        if not nombre_emisor or len(nombre_emisor) < 3:
            nombre_emisor = "PODER EJECUTIVO NACIONAL"
            
        # Síntesis
        sintesis_final = texto_completo.replace(' | ', ' ')
        if "ANEXO" in sintesis_final.upper():
            sintesis_final = f"ANEXO - Referente a {tipo_norma_desc} {numero} - " + sintesis_final
            
        categorias_detectadas = categorizar_texto(sintesis_final, diccionario_categorias)
        
        norma_formateada = {
            "id_jurisdiccion": ID_JURISDICCION_NACION,
            "nombre_emisor": nombre_emisor,
            "tipo_norma_desc": tipo_norma_desc, # Enviamos el STRING completo (Ej: COMUNICACIÓN "A")
            "numero": numero,
            "anio": anio,
            "fecha_publicacion": fecha_hoy_str,
            "sintesis": sintesis_final,
            "url_norma": url_completa,
            "categorias": categorias_detectadas
        }
        normas_procesadas.append(norma_formateada)

    if not normas_procesadas:
        print("ℹ️ No se pudo extraer información útil del HTML.")
        return

    # 3. LOAD: Enviar al Backend PHP
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