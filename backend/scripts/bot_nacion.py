import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import sys
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

if len(sys.argv) < 3:
    print(json.dumps({"status": "error", "message": "Uso: bot_nacion.py id_jurisdiccion url_boletin"}))
    sys.exit(1)

ID_JURISDICCION = int(sys.argv[1])
URL_BOLETIN = sys.argv[2]

API_KEY_BACKEND = os.getenv('API_KEY_BACKEND', 'Token_Seguro_Scraper_2026_XyZ!')
URL_HISTORIAL = os.getenv('URL_HISTORIAL', 'http://localhost/lgc_sgmlo/backend/api/boletin/historial_scraping.php')
URL_GUARDAR_NORMAS = os.getenv('URL_GUARDAR_NORMAS', 'http://localhost/lgc_sgmlo/backend/api/boletin/ingresar_scraping.php')

HEADERS_WEB = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml'
}

if ID_JURISDICCION == 1 and URL_BOLETIN.rstrip('/') == 'https://www.boletinoficial.gob.ar':
    URL_BOLETIN = 'https://www.boletinoficial.gob.ar/seccion/primera'

# ============================================================================
# NOTA DE ARQUITECTURA
# ----------------------------------------------------------------------------
# Este bot ya NO categoriza ni pide el diccionario de categorías.
# Toda la inteligencia (dedup de emisores, categorización sobre texto completo)
# vive en el backend PHP (NormativaHelper.php). El bot solo scrapea, descarga
# el TEXTO COMPLETO de cada aviso y manda todo crudo.
# ============================================================================


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


def convertir_fecha_espanol(fecha_str):
    meses_es = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }
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


def extraer_fecha_boletin(soup):
    fecha_div = soup.find('div', class_='fecha-ultima-edicion')
    if fecha_div:
        h6 = fecha_div.find('h6', class_='text-primary-alt')
        if h6:
            texto_fecha = h6.get_text(strip=True)
            texto_fecha = re.sub(r'<.*?>', '', texto_fecha)
            fecha_iso = convertir_fecha_espanol(texto_fecha)
            if fecha_iso:
                return fecha_iso
    texto_pagina = soup.get_text()
    match = re.search(r'(\d{1,2})\s+de\s+([A-Za-záéíóúñ]+)\s+de\s+(\d{4})', texto_pagina, re.IGNORECASE)
    if match:
        return convertir_fecha_espanol(match.group(0))
    match2 = re.search(r'(\d{2})/(\d{2})/(\d{4})', texto_pagina)
    if match2:
        dia, mes, anio = match2.groups()
        return f"{anio}-{mes}-{dia}"
    hoy = datetime.now().strftime("%Y-%m-%d")
    print(json.dumps({"status": "warning", "message": f"No se pudo extraer fecha del HTML, usando fecha actual: {hoy}"}))
    return hoy


def descargar_texto_completo(url_norma):
    """
    Descarga el detalle del aviso y extrae su texto completo, para que el backend
    categorice sobre el contenido real. Best-effort: si falla devuelve "".
    """
    try:
        res = requests.get(url_norma, headers=HEADERS_WEB, timeout=30)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        contenedor = (
            soup.find('div', id='cuerpoDetalleAviso')
            or soup.find('div', class_='avisoDetalle')
            or soup.find('article')
            or soup.find('main')
        )
        nodo = contenedor if contenedor else soup

        for tag in nodo.find_all(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        texto = nodo.get_text(separator=' ', strip=True)
        texto = re.sub(r'\s+', ' ', texto)
        return texto[:20000]
    except Exception:
        return ""


def ejecutar_bot_nacion():
    try:
        res_web = requests.get(URL_BOLETIN, headers=HEADERS_WEB, timeout=15)
        res_web.raise_for_status()
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Error de conexión: {e}"}))
        return

    soup = BeautifulSoup(res_web.text, 'html.parser')
    avisos = soup.find_all('a', href=re.compile(r'/detalleAviso/primera/'))

    if not avisos:
        print(json.dumps({"status": "warning", "message": "No se encontraron avisos"}))
        return

    fecha_boletin = extraer_fecha_boletin(soup)
    if not fecha_boletin:
        print(json.dumps({"status": "error", "message": "No se pudo determinar la fecha del boletín. Abortando."}))
        return

    if verificar_boletin_procesado(fecha_boletin):
        print(json.dumps({"status": "info", "message": f"Boletín del {fecha_boletin} ya fue procesado."}))
        return

    normas_procesadas = []
    patron_tipos = r'^(Decreto Sintetizado|Decreto|Decisión Administrativa|Resolución Conjunta|Resolución Sintetizada|Resolución General|Resolución|Disposición Sintetizada|Disposición|Ley|Acuerdo|Acta|Circular|Comunicación(?:\s+"[A-Z0-9]+")?|Convenio|Directiva|Instrucción|Providencia|Recomendación|Reglamento|Aviso Oficial|Aviso)\s*(?:N[°º]\s*|Nro\.?\s*|N\.\s*)?(\d+|S/N)?(?:/(\d{4}))?'

    for link_tag in avisos:
        texto_completo_link = link_tag.get_text(separator=' | ', strip=True)
        if not texto_completo_link:
            continue

        url_completa = f"https://www.boletinoficial.gob.ar{link_tag.get('href')}"
        partes = [p.strip() for p in texto_completo_link.split(' | ') if p.strip()]

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

        sintesis_final = texto_completo_link.replace(' | ', ' ')
        if "ANEXO" in sintesis_final.upper():
            sintesis_final = f"ANEXO - Referente a {tipo_norma_desc} {numero} - " + sintesis_final

        # Descargar el cuerpo completo del aviso para categorización en backend.
        cuerpo_completo = descargar_texto_completo(url_completa)

        normas_procesadas.append({
            "id_jurisdiccion": ID_JURISDICCION,
            "nombre_emisor": nombre_emisor,
            "tipo_norma_desc": tipo_norma_desc,
            "numero": numero,
            "anio": anio,
            "fecha_publicacion": fecha_boletin,
            "sintesis": sintesis_final,
            "texto_completo": cuerpo_completo,
            "url_norma": url_completa
        })

    if not normas_procesadas:
        print(json.dumps({"status": "warning", "message": "No se extrajo ninguna norma"}))
        return

    paquete_json = {"normas": normas_procesadas}
    headers_post = {"Authorization": f"Bearer {API_KEY_BACKEND}", "Content-Type": "application/json"}
    try:
        res_backend = requests.post(URL_GUARDAR_NORMAS, json=paquete_json, headers=headers_post, timeout=120)
        res_backend.raise_for_status()
        respuesta = res_backend.json()
        registrar_boletin_procesado(fecha_boletin, len(normas_procesadas))
        print(json.dumps({"status": "success", "message": respuesta.get('mensaje', 'OK'), "total_enviadas": len(normas_procesadas)}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Error al enviar: {e}"}))


if __name__ == "__main__":
    ejecutar_bot_nacion()
