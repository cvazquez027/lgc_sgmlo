import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import sys
import json
import locale

# Configurar locale para español (opcional, usaremos mapeo manual)
meses_es = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

def convertir_fecha_espanol(fecha_str):
    """Convierte '12 de Junio de 2026' a '2026-06-12'"""
    patron = r'(\d+)\s+de\s+([A-Za-záéíóúñ]+)\s+de\s+(\d{4})'
    match = re.search(patron, fecha_str, re.IGNORECASE)
    if match:
        dia = int(match.group(1))
        mes_nombre = match.group(2).lower()
        anio = int(match.group(3))
        mes = meses_es.get(mes_nombre, 0)
        if mes:
            return f"{anio}-{mes:02d}-{dia:02d}"
    return None

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

if len(sys.argv) < 3:
    print(json.dumps({"status": "error", "message": "Uso: bot_nacion.py id_jurisdiccion url_boletin"}))
    sys.exit(1)

ID_JURISDICCION = int(sys.argv[1])
URL_BOLETIN = sys.argv[2]

if ID_JURISDICCION == 1 and URL_BOLETIN.rstrip('/') == 'https://www.boletinoficial.gob.ar':
    URL_BOLETIN = 'https://www.boletinoficial.gob.ar/seccion/primera'

API_KEY_BACKEND = "Token_Seguro_Scraper_2026_XyZ!"
URL_HISTORIAL = "http://localhost/lgc_sgmlo/backend/api/boletin/historial_scraping.php"
URL_LEER_CATEGORIAS = "http://localhost/lgc_sgmlo/backend/api/boletin/leer_categorias_bot.php"
URL_GUARDAR_NORMAS = "http://localhost/lgc_sgmlo/backend/api/boletin/ingresar_scraping.php"

def verificar_boletin_procesado(fecha_boletin):
    try:
        payload = {"id_jurisdiccion": ID_JURISDICCION, "fecha_boletin": fecha_boletin, "accion": "verificar"}
        headers = {"Authorization": f"Bearer {API_KEY_BACKEND}"}
        res = requests.post(URL_HISTORIAL, json=payload, headers=headers, timeout=10)
        data = res.json()
        return data.get('procesado', False)
    except Exception as e:
        print(json.dumps({"status": "warning", "message": f"No se pudo verificar historial: {e}"}))
        return False

def registrar_boletin_procesado(fecha_boletin, cantidad):
    try:
        payload = {"id_jurisdiccion": ID_JURISDICCION, "fecha_boletin": fecha_boletin, "accion": "registrar", "cantidad_normas": cantidad}
        headers = {"Authorization": f"Bearer {API_KEY_BACKEND}"}
        requests.post(URL_HISTORIAL, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(json.dumps({"status": "warning", "message": f"No se pudo registrar historial: {e}"}))

def obtener_diccionario_categorias():
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
        return diccionario
    except Exception as e:
        return {}

def categorizar_texto(texto, diccionario_regex):
    if not texto: return []
    categorias_encontradas = set()
    texto_str = str(texto)
    for id_cat, regex in diccionario_regex.items():
        if regex.search(texto_str):
            categorias_encontradas.add(id_cat)
    return list(categorias_encontradas)

def extraer_fecha_boletin(soup):
    """Extrae la fecha del boletín desde el HTML específico del BORA."""
    # Buscar el div con clase 'fecha-ultima-edicion'
    fecha_div = soup.find('div', class_='fecha-ultima-edicion')
    if fecha_div:
        # Buscar el <h6> que contiene la fecha
        h6 = fecha_div.find('h6', class_='text-primary-alt')
        if h6:
            # El texto puede estar dentro de <b> o directamente
            texto_fecha = h6.get_text(strip=True)
            # Remover posibles etiquetas internas
            texto_fecha = re.sub(r'<.*?>', '', texto_fecha)
            fecha_iso = convertir_fecha_espanol(texto_fecha)
            if fecha_iso:
                return fecha_iso
    # Fallback: buscar cualquier texto que parezca una fecha en español
    texto_pagina = soup.get_text()
    match = re.search(r'(\d{1,2})\s+de\s+([A-Za-záéíóúñ]+)\s+de\s+(\d{4})', texto_pagina, re.IGNORECASE)
    if match:
        return convertir_fecha_espanol(match.group(0))
    return None

def ejecutar_bot_nacion():
    diccionario_categorias = obtener_diccionario_categorias()
    if not diccionario_categorias:
        print(json.dumps({"status": "error", "message": "No se pudieron obtener categorías"}))
        return

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml'
        }
        res_web = requests.get(URL_BOLETIN, headers=headers, timeout=15)
        res_web.raise_for_status()
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Error de conexión: {e}"}))
        return

    soup = BeautifulSoup(res_web.text, 'html.parser')
    avisos = soup.find_all('a', href=re.compile(r'/detalleAviso/primera/'))

    if not avisos:
        print(json.dumps({"status": "warning", "message": "No se encontraron avisos"}))
        return

    # --- EXTRAER FECHA REAL DEL BOLETÍN (una sola vez) ---
    fecha_boletin = extraer_fecha_boletin(soup)
    if not fecha_boletin:
        print(json.dumps({"status": "error", "message": "No se pudo determinar la fecha del boletín. Abortando."}))
        return

    # --- VERIFICAR SI ESTE BOLETÍN YA FUE PROCESADO ---
    if verificar_boletin_procesado(fecha_boletin):
        print(json.dumps({"status": "info", "message": f"Boletín del {fecha_boletin} ya fue procesado anteriormente. No se enviarán normas."}))
        return

    normas_procesadas = []
    patron_tipos = r'^(Decreto Sintetizado|Decreto|Decisión Administrativa|Resolución Conjunta|Resolución Sintetizada|Resolución General|Resolución|Disposición Sintetizada|Disposición|Ley|Acuerdo|Acta|Circular|Comunicación(?:\s+"[A-Z0-9]+")?|Convenio|Directiva|Instrucción|Providencia|Recomendación|Reglamento|Aviso Oficial|Aviso)\s*(?:N[°º]\s*|Nro\.?\s*|N\.\s*)?(\d+|S/N)?(?:/(\d{4}))?'

    for link_tag in avisos:
        texto_completo = link_tag.get_text(separator=' | ', strip=True)
        if not texto_completo:
            continue

        url_completa = f"https://www.boletinoficial.gob.ar{link_tag.get('href')}"
        partes = [p.strip() for p in texto_completo.split(' | ') if p.strip()]

        # Extraer tipo, número, emisor
        matches_encontrados = []
        for i, part in enumerate(partes):
            m = re.search(r'^(Resolución General)\s*(?:N[°º]\s*|Nro\.?\s*|N\.\s*)?(\d+|S/N)?(?:/(\d{4}))?', part, re.IGNORECASE)
            if not m:
                m = re.search(patron_tipos, part, re.IGNORECASE)
            if m:
                tipo = m.group(1).upper().strip()
                if tipo == "RESOLUCIÓN GENERAL":
                    tipo = "RESOLUCION GENERAL"
                matches_encontrados.append({
                    'index': i,
                    'tipo': tipo,
                    'numero': m.group(2) if m.group(2) else "S/N",
                    'anio': m.group(3) if m.group(3) else str(datetime.now().year),
                    'raw': part
                })

        if matches_encontrados:
            principales = [m for m in matches_encontrados if "AVISO" not in m['tipo']]
            elegido = principales[-1] if principales else matches_encontrados[0]
            tipo_norma_desc = elegido['tipo']
            numero = elegido['numero']
            anio = elegido['anio']

            idx = elegido['index']
            nombre_emisor = "PODER EJECUTIVO NACIONAL"
            if idx > 0:
                candidato = partes[idx - 1]
                if re.match(r'^\d{2}/\d{2}/\d{4}$', candidato) and idx > 1:
                    candidato = partes[idx - 2]
                nombre_emisor = candidato.strip()
            elif idx == 0 and len(partes) > 1:
                nombre_emisor = partes[1].strip()
        else:
            tipo_norma_desc = "AVISO OFICIAL"
            numero = "S/N"
            anio = str(datetime.now().year)
            nombre_emisor = "PODER EJECUTIVO NACIONAL"

        nombre_emisor = re.sub(r'^[^A-ZÁÉÍÓÚÑ]+', '', nombre_emisor, flags=re.IGNORECASE).strip()
        if not nombre_emisor or len(nombre_emisor) < 3:
            nombre_emisor = "PODER EJECUTIVO NACIONAL"

        sintesis_final = texto_completo.replace(' | ', ' ')
        if "ANEXO" in sintesis_final.upper():
            sintesis_final = f"ANEXO - Referente a {tipo_norma_desc} {numero} - " + sintesis_final

        categorias_detectadas = categorizar_texto(sintesis_final, diccionario_categorias)

        normas_procesadas.append({
            "id_jurisdiccion": ID_JURISDICCION,
            "nombre_emisor": nombre_emisor,
            "tipo_norma_desc": tipo_norma_desc,
            "numero": numero,
            "anio": anio,
            "fecha_publicacion": fecha_boletin,
            "sintesis": sintesis_final,
            "url_norma": url_completa,
            "categorias": categorias_detectadas
        })

    if not normas_procesadas:
        print(json.dumps({"status": "warning", "message": "No se extrajo ninguna norma"}))
        return

    # Enviar al backend
    paquete_json = {"normas": normas_procesadas}
    headers_post = {"Authorization": f"Bearer {API_KEY_BACKEND}", "Content-Type": "application/json"}
    try:
        res_backend = requests.post(URL_GUARDAR_NORMAS, json=paquete_json, headers=headers_post)
        res_backend.raise_for_status()
        respuesta = res_backend.json()
        registrar_boletin_procesado(fecha_boletin, len(normas_procesadas))
        print(json.dumps({"status": "success", "message": respuesta.get('mensaje', 'OK'), "total_enviadas": len(normas_procesadas)}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Error al enviar: {e}"}))

if __name__ == "__main__":
    ejecutar_bot_nacion()