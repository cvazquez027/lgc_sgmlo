import pandas as pd
from bs4 import BeautifulSoup
import re
from db_config import get_db_connection

def procesar_saij_masivo(ruta_archivo):
    print("=== SINCRO DATA V: MODO SAIJ MASIVO LOCAL (CÓRDOBA) ===")
    
    try:
        # Abrimos el archivo gigante. BS4 lo procesa en RAM sin colgarse.
        with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{ruta_archivo}'.")
        return pd.DataFrame()

    print("⏳ Analizando la estructura del HTML (esto puede demorar unos segundos)...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Cada normativa está en una etiqueta <li> con clase 'result-item'
    items = soup.find_all('li', class_='result-item')
    print(f"📊 Se detectaron {len(items)} registros totales en el archivo.")
    
    lista_normas = []
    
    # --- LA WHITELIST Y BLACKLIST ---
    frases_clave = [
        # Ambiente
        r'recursos naturales', r'ordenamiento territorial', r'ordenamiento ambiental del territorio', r'impacto ambiental', 
        r'residuos peligrosos', r'residuos sólidos', r'residuos patogénicos',
        r'efluentes', r'emisiones gaseosas', r'áreas protegidas', r'área protegida'
        r'flora silvestre', r'fauna silvestre', r'bosques nativos', r'cambio climático',
        r'desarrollo sustentable', r'desarrollo sostenible', r'pasivos ambientales', r'evaluación ambiental',
        r'flora', r'fauna', r'control ambiental', r'protección ambiental'
        # SyH
        r'seguridad e higiene', r'higiene y seguridad', r'riesgos del trabajo', 
        r'enfermedades profesionales', r'accidentes de trabajo', r'medicina laboral',
        r'condiciones y medio ambiente de trabajo', r'elementos de protección', 
        r'ergonomía', r'salud ocupacional', r'seguridad industrial', r'ambiente de trabajo', r'nivel de ruido',
        r'ambiente laboral', r'agente de riesgo', r'agentes de riesgo', r'riesgos laborales'
    ]
    patron_whitelist = r'(?i)(' + '|'.join(frases_clave) + r')'
    patron_basura = r'(?i)(designar|desígnase|desígnese|nombramiento|juez|fiscal|magistrado|defensor|expropiaci|donación|pensión|jubilación|bonificación)'

    descartados_derogada = 0
    descartados_basura = 0
    descartados_whitelist = 0
    insertables = 0

    for item in items:
        # Extraemos las etiquetas <dt> que contienen la meta-información y la síntesis
        dts = item.find_all('dt', class_='descr-colapsado')
        if not dts: continue
        
        meta_text = dts[0].get_text(strip=True) # Ej: "Ley 6.392. Córdoba 17/4/1980. Derogada"
        
        # 1. FILTRO EXACTO: Ignorar las derogadas
        if re.search(r'(?i)derogada', meta_text):
            descartados_derogada += 1
            continue

        a_tag = item.find('a')
        if not a_tag: continue
        
        titulo = a_tag.get_text(strip=True)
        href = a_tag.get('href', '')
        
        # Si hay un segundo <dt>, suele ser el resumen extendido de la norma
        sintesis_extra = dts[1].get_text(strip=True) if len(dts) > 1 else ""
        texto_completo = f"{titulo} {sintesis_extra} {meta_text}"
        
        # 2. FILTROS DATAV (Basura y Frases Exactas)
        if re.search(patron_basura, texto_completo):
            descartados_basura += 1
            continue
            
        if not re.search(patron_whitelist, texto_completo):
            descartados_whitelist += 1
            continue
            
        # --- PARSEO DE METADATOS ---
        # Detecta "DECRETO 63/2021" o "Ley N. 6.613"
        match_norma = re.search(r'(?i)(Ley|Decreto|Resolución|Disposición)\s*(?:N[.°º]*\s*|Nro\.?\s*)?([0-9\.]+)(?:/(\d+))?', meta_text)
        
        tipo_norma = "Norma"
        numero = "0"
        anio = "0000"
        
        if match_norma:
            tipo_norma = match_norma.group(1).capitalize()
            numero = match_norma.group(2).replace('.', '').strip()
            anio_norma = match_norma.group(3) # Puede ser None si es Ley (no llevan año en el número)
            if anio_norma:
                anio = f"20{anio_norma}" if len(anio_norma) == 2 and int(anio_norma) <= 50 else (f"19{anio_norma}" if len(anio_norma) == 2 else anio_norma)

        # Extraemos la fecha exacta de publicación (Ej: 17/4/1980)
        fecha_publicacion = "0000-00-00"
        match_fecha = re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', meta_text)
        if match_fecha:
            anio = match_fecha.group(3) if anio == "0000" else anio
            fecha_publicacion = f"{match_fecha.group(3)}-{match_fecha.group(2).zfill(2)}-{match_fecha.group(1).zfill(2)}"
        else:
            fecha_publicacion = f"{anio}-01-01"

        # Categorización
        es_syh = any(w in texto_completo.lower() for w in ['seguridad', 'higiene', 'riesgo', 'laboral', 'accidente', 'ergonomia'])
        categoria = "Seguridad e Higiene" if es_syh else "Ambiente"
        
        # Corrección y limpieza extrema del enlace
        url_completa = f"https://www.saij.gob.ar{href}" if href.startswith('/') else href
        # Cortamos la URL en el signo '?' para descartar toda la basura de parámetros del SAIJ
        url_completa = url_completa.split('?')[0]

        lista_normas.append({
            'id_origen': f"CBA-SAIJ-{tipo_norma.upper()}-{numero}-{anio}",
            'tipo_norma': tipo_norma,
            'numero': numero,
            'anio': anio,
            'fecha_publicacion': fecha_publicacion, 
            'sintesis': texto_completo[:500] + ('...' if len(texto_completo) > 500 else ''),
            'categoria': categoria,
            'url_origen': url_completa,
            'jurisdiccion': 'Córdoba'
        })
        insertables += 1

    print("\n=== RESUMEN DE PROCESAMIENTO ===")
    print(f"Total Registros Leídos: {len(items)}")
    print(f"🚫 Descartados (Derogadas): {descartados_derogada}")
    print(f"🗑️ Descartados (Basura/Expropiaciones): {descartados_basura}")
    print(f"🛡️ Descartados (No son SyH o Ambiente): {descartados_whitelist}")
    print(f"✅ ÚTILES PARA DATAV: {insertables}")
    
    if not lista_normas:
        return pd.DataFrame()

    df = pd.DataFrame(lista_normas).drop_duplicates(subset=['id_origen'])
    return df

def guardar_en_db(df):
    if df.empty: 
        print("📭 No hay registros nuevos para guardar.")
        return
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        sql = """
            INSERT INTO normativas 
            (id_origen, tipo_norma, numero, anio, fecha_publicacion, sintesis, categoria, url_origen, jurisdiccion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            sintesis=VALUES(sintesis), categoria=VALUES(categoria), url_origen=VALUES(url_origen)
        """
        registros = [tuple(x) for x in df.to_numpy()]
        cursor.executemany(sql, registros)
        conn.commit()
        print(f"💾 Guardado completado: {cursor.rowcount} registros procesados en MySQL.")
    except Exception as e:
        print(f"❌ Error al guardar en base de datos: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Asegurate de que el nombre del archivo sea correcto
    df_saij = procesar_saij_masivo("SAIJ.html")
    guardar_en_db(df_saij)