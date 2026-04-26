import pandas as pd
from bs4 import BeautifulSoup
import re
from db_config import get_db_connection

def procesar_html_local(ruta_archivo):
    print("=== SINCRO DATA V: MODO BYPASS LOCAL (CÓRDOBA / NACIÓN) ===")
    
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{ruta_archivo}'.")
        return pd.DataFrame()

    # Reconstrucción del "view-source"
    if '<td class="line-content">' in html_content:
        print("🔍 Formato 'view-source' detectado. Ensamblando el HTML original...")
        soup_preliminar = BeautifulSoup(html_content, 'html.parser')
        lineas = soup_preliminar.find_all('td', class_='line-content')
        html_content = "".join([linea.get_text() for linea in lineas])

    soup = BeautifulSoup(html_content, 'html.parser')
    tablas = soup.find_all('table')
    print(f"📊 Se detectaron {len(tablas)} tablas de normativas.")
    
    lista_normas = []
    registros_procesados = 0

    for tabla in tablas:
        filas = tabla.find_all('tr')
        for fila in filas:
            cols = fila.find_all(['td', 'th'])
            
            if len(cols) >= 4:
                jurisdiccion_raw = cols[0].get_text(strip=True)
                if jurisdiccion_raw.lower() == 'jurisdicción' or not jurisdiccion_raw: 
                    continue
                
                tipo_norma = cols[1].get_text(strip=True).capitalize()
                numero_raw = cols[2].get_text(strip=True).replace('.', '').strip()
                sintesis = cols[3].get_text(strip=True)
                
                enlace_tag = fila.find('a', href=True)
                href = enlace_tag['href'] if enlace_tag else ""
                
                jur_db = 'Córdoba'
                if any(palabra in jurisdiccion_raw.lower() for palabra in ['nación', 'federal', 'cofema', 'nacional']):
                    jur_db = 'Nacional'
                    
                # === NUEVA LÓGICA DE PARSEO ANTI-TRUNCADO ===
                anio = "0000"
                numero = numero_raw
                
                if '/' in numero_raw:
                    partes = numero_raw.split('/', 1)
                    numero = partes[0].strip()
                    anio_raw = partes[1].strip()
                    
                    # Buscamos exactamente 2 o 4 dígitos para el año, ignorando texto basura como "(DEROGADA)"
                    match_anio = re.search(r'(\d{2,4})', anio_raw)
                    if match_anio:
                        anio_extraido = match_anio.group(1)
                        if len(anio_extraido) == 2:
                            anio = f"20{anio_extraido}" if int(anio_extraido) <= 50 else f"19{anio_extraido}"
                        else:
                            anio = anio_extraido
                else:
                    match_anio_url = re.search(r'/([12]\d{3})/', href)
                    if match_anio_url:
                        anio = match_anio_url.group(1)

                # Limpieza extrema del número (Quita "(DEROGADA)" si vino pegado al número en vez del año)
                numero = re.sub(r'\(.*?\)', '', numero).strip() 
                numero = re.sub(r'[^\w\-]', '', numero) # Deja solo letras, números y guiones (ej: "548-E")

                # Validación final de seguridad: Si por algún motivo anio no tiene 4 dígitos numéricos, fuerza "0000"
                if not anio.isdigit() or len(anio) != 4:
                    anio = "0000"
                # ============================================

                prefijo = "CBA" if jur_db == 'Córdoba' else "NAC"
                
                lista_normas.append({
                    'id_origen': f"{prefijo}-{tipo_norma.upper()}-{numero}",
                    'tipo_norma': tipo_norma,
                    'numero': numero,
                    'anio': anio,
                    'fecha_publicacion': f"{anio}-01-01", 
                    'sintesis': sintesis,
                    'categoria': 'Ambiente', 
                    'url_origen': href,
                    'jurisdiccion': jur_db
                })
                registros_procesados += 1

    if not lista_normas:
        return pd.DataFrame()

    df = pd.DataFrame(lista_normas).drop_duplicates(subset=['id_origen'])
    print(f"✅ ¡Extracción exitosa! {len(df)} normativas procesadas limpiamente.")
    return df

def guardar_en_db(df):
    if df.empty: return
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO normativas 
            (id_origen, tipo_norma, numero, anio, fecha_publicacion, sintesis, categoria, url_origen, jurisdiccion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            sintesis=VALUES(sintesis), categoria=VALUES(categoria), url_origen=VALUES(url_origen), jurisdiccion=VALUES(jurisdiccion)
        """
        registros = [tuple(x) for x in df.to_numpy()]
        cursor.executemany(sql, registros)
        conn.commit()
        print(f"💾 {cursor.rowcount} normativas integradas a la base de datos.")
    except Exception as e:
        print(f"❌ Error en MySQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    archivo_html = "normativa_cba.html"
    df_datos = procesar_html_local(archivo_html)
    guardar_en_db(df_datos)