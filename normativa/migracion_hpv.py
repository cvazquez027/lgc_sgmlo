import pandas as pd
import mysql.connector
import re
import time
import os
import logging
import zipfile
import io
import requests
import warnings
import unicodedata
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# =====================================================================
# SILENCIADOR ABSOLUTO DE CONSOLA
# =====================================================================
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*duckduckgo_search.*")
os.environ['PYTHONWARNINGS'] = 'ignore'
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
try:
    requests.packages.urllib3.disable_warnings()
except:
    pass

session = requests.Session()
session.verify = False 
session.headers.update({'User-Agent': 'Mozilla/5.0'})

# =====================================================================
# 1. FUNCIONES DE NORMALIZACIÓN Y LIMPIEZA
# =====================================================================
def normalizar_texto(texto):
    if pd.isna(texto) or texto is None: return ""
    texto = str(texto).strip().lower()
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')

def limpiar_codificacion(texto):
    reemplazos = {
        'Ã³': 'ó', 'Ã¡': 'á', 'Ã©': 'é', 'Ã\xad': 'í', 'Ãº': 'ú', 'Ã±': 'ñ', 'Ã': 'í', 
        'Â°': '°', 'Âº': 'º', 'NÂº': 'Nº', 'NÂ°': 'N°', 'NÂ': 'Nº',
        '\xa0': ' ',  
        'N.º': 'Nº', 'N. °': 'Nº', 'n.º': 'nº' 
    }
    texto_limpio = str(texto)
    for corrupto, limpio in reemplazos.items():
        texto_limpio = texto_limpio.replace(corrupto, limpio)
    return texto_limpio

# =====================================================================
# 2. CONFIGURACIÓN DE BD Y DICCIONARIOS
# =====================================================================
db_config = {
    'host': 'localhost',
    'user': 'admin', 
    'password': 'Emma.Tomi_1725', 
    'database': 'sgmlo_db'
}

def obtener_diccionarios_bd(cursor):
    diccionarios = {}
    cursor.execute("SELECT id_tipo_norma, descripcion FROM tipo_norma")
    diccionarios['tipo_norma'] = {normalizar_texto(row[1]): row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id_categoria, descripcion FROM categoria")
    diccionarios['categoria'] = {normalizar_texto(row[1]): row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id_jurisdiccion, descripcion FROM jurisdiccion")
    diccionarios['jurisdiccion_nombres'] = {row[0]: normalizar_texto(row[1]) for row in cursor.fetchall()}
    
    diccionarios['emisor'] = {}
    cursor.execute("SELECT id_emisor_norma, id_jurisdiccion, descripcion FROM emisor_norma")
    for row in cursor.fetchall():
        id_em, id_jur, desc = row[0], row[1], normalizar_texto(row[2])
        if id_jur not in diccionarios['emisor']:
            diccionarios['emisor'][id_jur] = {}
        diccionarios['emisor'][id_jur][desc] = id_em
        
    diccionarios['tipo_norma'][normalizar_texto('resolución')] = diccionarios['tipo_norma'].get(normalizar_texto('resolución'), 5)
    diccionarios['tipo_norma'][normalizar_texto('disposición')] = diccionarios['tipo_norma'].get(normalizar_texto('disposición'), 8)
    diccionarios['tipo_norma'][normalizar_texto('decreto-ley')] = diccionarios['tipo_norma'].get(normalizar_texto('decreto-ley'), diccionarios['tipo_norma'].get(normalizar_texto('ley'), 1))
    
    return diccionarios

def resolver_emisor_por_id_jurisdiccion(emisor_raw, id_jur_real, conn, cursor, diccionarios):
    emisor_norm = normalizar_texto(emisor_raw)
    dicc_emi = diccionarios['emisor']
    
    if not emisor_norm:
        emisor_norm = "EMISOR GENERICO"
        
    if id_jur_real not in dicc_emi:
        dicc_emi[id_jur_real] = {}
        
    emisores_locales = dicc_emi[id_jur_real]
    
    if emisor_norm in emisores_locales:
        return emisores_locales[emisor_norm]
        
    for key_db in sorted(emisores_locales.keys(), key=len, reverse=True):
        if len(key_db) > 3 and (key_db in emisor_norm or emisor_norm in key_db):
            return emisores_locales[key_db]
            
    try:
        emisor_original = str(emisor_raw).strip().upper() if emisor_raw else "EMISOR GENERICO"
        cursor.execute("INSERT INTO emisor_norma (descripcion, id_jurisdiccion) VALUES (%s, %s)", (emisor_original, id_jur_real))
        nuevo_id_emisor = cursor.lastrowid
        conn.commit()
        emisores_locales[emisor_norm] = nuevo_id_emisor
        return nuevo_id_emisor
    except:
        conn.rollback()
        return 1

# =====================================================================
# 3. MOTORES DE BÚSQUEDA (CON TRIPLE FILTRO Y SCORING)
# =====================================================================
def descargar_catalogo_infoleg():
    print("📥 [NACIÓN] Montando catálogo oficial de InfoLEG...")
    url_api = "https://datos.jus.gob.ar/api/3/action/package_show?id=base-de-datos-legislativos-infoleg"
    columnas_reales = ['id_norma', 'tipo_norma', 'numero_norma', 'fecha_boletin', 'texto_resumido', 'organismo_origen']
    try:
        response = session.get(url_api, timeout=15)
        url_zip = next((r['url'] for r in response.json().get('result', {}).get('resources', []) 
                       if 'normativa nacional' in r.get('name', '').lower() and 'muestreo' not in r.get('name', '').lower() and r.get('format', '').lower() == 'zip'), None)
        if not url_zip: return None
        r = session.get(url_zip)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            csv_filename = [name for name in z.namelist() if name.endswith('.csv')][0]
            with z.open(csv_filename) as f:
                df_nacion = pd.read_csv(f, usecols=lambda c: c in columnas_reales, encoding='utf-8', low_memory=False)
        
        df_nacion = df_nacion.loc[:, ~df_nacion.columns.str.contains(r'\.')].copy()
        df_nacion['tipo_norma_norm'] = df_nacion['tipo_norma'].astype(str).str.lower().str.strip()
        df_nacion['numero_norm'] = df_nacion['numero_norma'].astype(str).str.strip().str.replace('.0', '', regex=False)
        df_nacion['org_origen_norm'] = df_nacion['organismo_origen'].astype(str).apply(normalizar_texto)
        fechas = pd.to_datetime(df_nacion['fecha_boletin'], errors='coerce')
        df_nacion['anio'] = fechas.dt.year.fillna(0).astype(int).astype(str)
        df_nacion['fecha_publicacion'] = fechas.dt.strftime('%Y-%m-%d').where(fechas.notnull(), None)
        df_nacion['texto_resumido'] = df_nacion['texto_resumido'].fillna("Sin resumen.")
        return df_nacion
    except Exception:
        return None

def buscar_nacion(df_nacion, tipo, numero, anio, emisor_raw):
    if df_nacion is None: return None, "Base InfoLEG offline falló", None, anio
    tipo_buscar = "ley" if "ley" in tipo.lower() else tipo.lower()
    match = df_nacion[(df_nacion['tipo_norma_norm'] == tipo_buscar) & (df_nacion['numero_norm'] == str(numero))]
    
    if not match.empty and anio not in ["S/A", "NULL"]:
        match_anio = match[match['anio'] == str(anio)]
        if not match_anio.empty: match = match_anio
            
    # TRIPLE FILTRO INFOLEG
    if len(match) > 1 and emisor_raw:
        ex = normalizar_texto(emisor_raw)
        
        # 1. Intento DDGS Oráculo
        query = f"{emisor_raw} {tipo} {numero}/{anio if anio not in ['S/A', 'NULL'] else ''} site:servicios.infoleg.gob.ar".replace("NULL", "").strip()
        id_ddgs = None
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=3):
                        m_id = re.search(r'id=(\d+)', r['href'])
                        if m_id:
                            id_ddgs = m_id.group(1)
                            break
        except: pass
        
        if id_ddgs:
            fila_oraculo = match[match['id_norma'].astype(str) == id_ddgs]
            if not fila_oraculo.empty: match = fila_oraculo
                
        # 2. Scoring Local si DDGS falló
        if len(match) > 1:
            keywords = []
            if 'acumar' in ex: keywords.extend(['acumar', 'matanza', 'riachuelo'])
            elif 'opds' in ex or 'ambiente' in ex: keywords.extend(['ambiente', 'sostenible', 'ecologia', 'opds'])
            elif 'agua' in ex: keywords.extend(['agua', 'hidrico'])
            elif 'agrario' in ex: keywords.extend(['agrario', 'agropecuario'])
            
            mejor_puntaje = -1
            mejor_idx = None
            
            for idx, fila in match.iterrows():
                puntaje = 0
                texto_combo = normalizar_texto(str(fila['org_origen_norm']) + " " + str(fila['texto_resumido']))
                if ex in texto_combo: puntaje += 20
                for kw in keywords:
                    if kw and kw in texto_combo: puntaje += 10
                if puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor_idx = idx
                    
            if mejor_puntaje > 0:
                match = match.loc[[mejor_idx]]
            else:
                return None, f"Múltiples normas encontradas, ninguna coincide con el emisor '{emisor_raw}'.", None, anio

    if len(match) > 0:
        fila = match.iloc[0]
        id_origen = fila['id_norma']
        sintesis = str(fila['texto_resumido']).strip()
        fecha_pub = fila['fecha_publicacion'] if pd.notna(fila['fecha_publicacion']) else None
        anio_real = fila['anio'] if fila['anio'] != '0' else anio
        return f"https://servicios.infoleg.gob.ar/infolegInternet/verNorma.do?id={id_origen}", sintesis, fecha_pub, anio_real
        
    return None, "Normativa no encontrada en InfoLEG.", None, anio

TIPOS_PBA = {'ley': 'Law', 'decreto': 'Decree', 'decreto-ley': 'DecreeLaw', 'resolución': 'Resolution', 'disposición': 'Disposition', 'ordenanza': 'GeneralOrdinance'}

def buscar_pba(tipo, numero, anio, emisor_raw):
    raw_type = TIPOS_PBA.get(tipo.lower(), "")
    num = str(numero).strip()
    anio_str = "" if anio in ["S/A", "2010", "NULL"] else str(anio)
    url_search = f"https://normas.gba.gob.ar/resultados?q%5Bterms%5D%5Braw_type%5D={raw_type}&q%5Bterms%5D%5Bnumber%5D={num}&q%5Bterms%5D%5Byear%5D={anio_str}"
    
    tarjeta_elegida = None
    try:
        r = session.get(url_search, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        cards = soup.find_all('div', class_='rule-card')
        
        if not cards and anio_str:
            url_search = f"https://normas.gba.gob.ar/resultados?q%5Bterms%5D%5Braw_type%5D={raw_type}&q%5Bterms%5D%5Bnumber%5D={num}"
            r = session.get(url_search, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            cards = soup.find_all('div', class_='rule-card')

        if cards:
            tarjeta_elegida = cards[0] 
            
            # TRIPLE FILTRO PBA (Scoring)
            if len(cards) > 1 and emisor_raw:
                ex = normalizar_texto(emisor_raw)
                keywords = []
                if 'acumar' in ex: keywords.extend(['acumar', 'matanza', 'riachuelo'])
                elif 'opds' in ex or 'ambiente' in ex: keywords.extend(['ambiente', 'sostenible', 'opds'])
                elif 'agua' in ex: keywords.extend(['agua', 'ada', 'hidrica'])
                elif 'agrario' in ex: keywords.extend(['asuntos agrarios', 'desarrollo agrario'])
                
                mejor_puntaje = -100
                for card in cards:
                    puntaje = 0
                    source = card.find('p', id='rule-source') or card.find('p', class_='rule-source')
                    texto_tarjeta = normalizar_texto(card.get_text(separator=' '))
                    
                    if source:
                        web_source = normalizar_texto(source.get_text())
                        if ex in web_source: puntaje += 50
                    if ex in texto_tarjeta: puntaje += 10
                    for kw in keywords:
                        if kw and kw in texto_tarjeta: puntaje += 5
                        
                    # Castigo brutal si el año no coincide (Mata el bug de PBA)
                    if anio_str:
                        h3 = card.find('h3', class_='rule-name')
                        if h3 and anio_str not in h3.get_text(): puntaje -= 100
                            
                    if puntaje > mejor_puntaje:
                        mejor_puntaje = puntaje
                        tarjeta_elegida = card
                        
                if mejor_puntaje < 0:
                    tarjeta_elegida = None # Es basura, forzamos DDGS
    except: pass
        
    # ORÁCULO DDGS DE EMERGENCIA (Si el buscador PBA trajo basura o colapsó)
    if not tarjeta_elegida:
        emisor_str = emisor_raw if emisor_raw else "Provincia de Buenos Aires"
        query = f"{emisor_str} {tipo} {numero}/{anio_str} site:normas.gba.gob.ar".strip()
        mejor_link = None
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=3):
                        if 'normas.gba.gob.ar' in r['href']:
                            mejor_link = r['href']
                            break
        except: pass
            
        if mejor_link:
             try:
                 r_det = session.get(mejor_link, timeout=15)
                 soup_det = BeautifulSoup(r_det.text, 'html.parser')
                 
                 resumen_header = soup_det.find('h5', string=re.compile('Resumen', re.I)) or soup_det.find('h6', string=re.compile('Resumen', re.I))
                 if resumen_header:
                     nxt = resumen_header.find_next(['p', 'blockquote', 'div'])
                     sintesis = nxt.get_text(strip=True) if nxt else "Sin resumen."
                 else:
                     sintesis = "Sin resumen."
                 
                 def extraer_f(label):
                     span = soup_det.find('span', class_='field-name', string=re.compile(label, re.I))
                     if span:
                         val = span.find_next_sibling('span', class_='field-info')
                         if val: return val.get_text(strip=True)
                     return None
                     
                 f_elegida = extraer_f('Fecha de publicación') or extraer_f('Fecha de promulgación')
                 fecha_pub = None
                 anio_real = anio
                 if f_elegida:
                     m_f = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', f_elegida)
                     if m_f:
                         d, m, y = m_f.groups()
                         fecha_pub = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                         if anio in ["S/A", "NULL"]: anio_real = y
                         
                 return mejor_link, sintesis, fecha_pub, anio_real
             except:
                 pass
        return None, f"Norma ambigua o no encontrada para '{emisor_raw}'.", None, anio

    # Si encontramos tarjeta local correcta, scrapeamos
    if tarjeta_elegida:
        href = tarjeta_elegida.find('h3', class_='rule-name').find('a')['href']
        url_detalle = f"https://normas.gba.gob.ar{href}"
        try:
            r_det = session.get(url_detalle, timeout=15)
            soup_det = BeautifulSoup(r_det.text, 'html.parser')
            
            resumen_header = soup_det.find('h5', string=re.compile('Resumen', re.I)) or soup_det.find('h6', string=re.compile('Resumen', re.I))
            if resumen_header:
                nxt = resumen_header.find_next(['p', 'blockquote', 'div'])
                sintesis = nxt.get_text(strip=True) if nxt else "Sin resumen en portal."
            else:
                sintesis = "Sin resumen en portal."
            
            def extraer_fecha_span(label):
                span_label = soup_det.find('span', class_='field-name', string=re.compile(label, re.I))
                if span_label:
                    span_val = span_label.find_next_sibling('span', class_='field-info')
                    if span_val and span_val.get_text(strip=True): return span_val.get_text(strip=True)
                return None

            fecha_elegida = extraer_fecha_span('Fecha de publicación') or extraer_fecha_span('Fecha de promulgación')
            fecha_pub = None
            anio_real = anio
            
            if fecha_elegida:
                match_fecha = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', fecha_elegida)
                if match_fecha:
                    d, m, y = match_fecha.groups()
                    fecha_pub = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                    if anio in ["S/A", "NULL"]: anio_real = y
            
            if anio in ["S/A", "NULL"] and anio_real in ["S/A", "NULL"]:
                match_href_year = re.search(r'/(\d{4})/', href)
                if match_href_year: anio_real = match_href_year.group(1)

            return url_detalle, sintesis, fecha_pub, anio_real
        except:
            return url_detalle, "Error extrayendo detalle.", None, anio
            
    return None, "Normativa no encontrada en portal PBA.", None, anio

def es_url_municipal_valida(url):
    basuras = ['/busqueda', '/contacto', '/secciones/', 'wp/normativa', 'speedtest', 'drugs', 'carfax']
    if any(b in url.lower() for b in basuras): return False
    return any(d in url.lower() for d in ['canuelas', 'gob.ar', 'gov.ar', 'observatorioamba', 'scribd'])

def procesar_resultado_municipal(href, sintesis, anio):
    fecha_pub = None
    anio_real = anio
    texto_buscar = href + " " + str(sintesis)
    match_fecha = re.search(r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b', texto_buscar)
    if match_fecha:
        d, m, y = match_fecha.groups()
        fecha_pub = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        if anio in ["NULL", "S/A"]: anio_real = y
    else:
        if anio in ["NULL", "S/A"]:
            match_year = re.search(r'\b(19\d{2}|20\d{2})\b', texto_buscar)
            if match_year: anio_real = match_year.group(1)
    return href, sintesis, fecha_pub, anio_real

def buscar_municipal(tipo, numero, anio, nombre_jurisdiccion):
    año_str = f" de {anio}" if anio not in ["S/A", "2010", "NULL"] else ""
    query = f"{tipo} {numero}{año_str} {nombre_jurisdiccion} filetype:pdf"
    query_web = f"{tipo} {numero}{año_str} {nombre_jurisdiccion} site:gob.ar OR site:gov.ar"
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=3):
                    if es_url_municipal_valida(r['href']): return procesar_resultado_municipal(r['href'], "Documento PDF Municipal.", anio)
                time.sleep(1)
                for r in ddgs.text(query_web, max_results=3):
                    if es_url_municipal_valida(r['href']): return procesar_resultado_municipal(r['href'], r.get('body', 'Normativa web municipal.'), anio)
    except: pass
    return None, "Normativa municipal no digitalizada.", None, anio

def extraer_texto_profundo_para_categorias(url_inicial, nivel):
    if not url_inicial or url_inicial == "No hallado" or url_inicial.endswith('.pdf'): return ""
    try:
        r = session.get(url_inicial, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        keywords_links = ['texto actualizado de la norma', 'texto completo de la norma', 'texto original de la norma', 'texto actualizado', 'texto completo']
        url_deep = None
        for a in soup.find_all('a', href=True):
            if any(kw in a.get_text(strip=True).lower() for kw in keywords_links) and not a['href'].endswith('.pdf'):
                url_deep = urljoin(url_inicial, a['href'])
                break

        if url_deep:
            r = session.get(url_deep, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')

        texto = ""
        if nivel == 1:
            bloque = soup.find('div', class_='WordSection1') or soup.find('div', class_='margen')
            if bloque: texto = bloque.get_text(separator=' ', strip=True)
            else:
                for e in soup(["script", "style", "nav", "footer", "header", "aside"]): e.extract()
                texto = soup.get_text(separator=' ', strip=True)
        elif nivel == 2:
            bloque = soup.find('div', class_='document-text') or soup.find('div', class_='card-body')
            if bloque: texto = bloque.get_text(separator=' ', strip=True)
            else:
                for e in soup(["script", "style", "nav", "footer", "header", "aside"]): e.extract()
                texto = soup.get_text(separator=' ', strip=True)
                
        return texto.lower()
    except Exception:
        return ""

def texto_contiene_categoria(texto, categoria_db):
    if not texto: return False
    cat = normalizar_texto(categoria_db)
    if cat == "aire":
        texto_sin_bsas = normalizar_texto(texto).replace("buenos aires", "")
        return bool(re.search(r'\baire(s)?\b', texto_sin_bsas))
    elif cat == "agua":
        return bool(re.search(r'\bagua(s)?\b', normalizar_texto(texto)))
    else:
        return cat in normalizar_texto(texto)

# =====================================================================
# 4. EXTRACCIÓN DE NORMAS (REGEX ELÁSTICA V2)
# =====================================================================
def extraer_norma_unica(texto):
    normas = []
    texto_reparado = limpiar_codificacion(texto)
    
    patron = re.compile(
        r'\b(decreto[\s-]*ley|dec[\s-]*ley|ley|decreto|resoluci[óo]n|res\.?|dec\.?|disposici[óo]n|disp\.?|ordenanza|ord\.?|norma)\b'
        r'(?:[\s\-]*(?:nacional|provincial|general|reglamentario|n[.\s°ºa-z]+|numero|número|del|año|conjunta|nag))*'
        r'\s*(\d+(?:\.\d+)?)\s*[a-zA-Z]*\s*[/-]\s*(\d+)', 
        re.IGNORECASE
    )
    for m in patron.finditer(texto_reparado):
        t_raw = m.group(1).lower().strip()
        if re.match(r'decreto[\s-]*ley|dec[\s-]*ley', t_raw): t = 'Decreto-Ley'
        elif t_raw in ['res', 'res.', 'resolucion', 'resolución']: t = 'Resolución'
        elif t_raw in ['disp', 'disp.', 'disposicion', 'disposición']: t = 'Disposición'
        elif t_raw in ['dec', 'dec.', 'decreto']: t = 'Decreto'
        elif t_raw in ['ord', 'ord.', 'ordenanza']: t = 'Ordenanza'
        elif t_raw == 'norma': t = 'Norma'
        else: t = t_raw.capitalize()
            
        a_str = m.group(3)
        a = ("19" + a_str if int(a_str)>50 else "20" + a_str) if len(a_str)==2 else (a_str if len(a_str)==4 else "NULL")
        normas.append((t, str(m.group(2)).replace('.', ''), a))
        
    patron_simple = re.compile(
        r'(?<!decreto[\s-])(?<!dec[\s-])(?<!decreto)(?<!dec)\b(ley|norma)\b'
        r'(?:[\s\-]*(?:nacional|provincial|general|reglamentario|n[.\s°ºa-z]+|numero|número|conjunta|nag))*'
        r'\s*(\d+(?:\.\d+)?)\b(?!\s*[/-]\s*\d+)', 
        re.IGNORECASE
    )
    for m in patron_simple.finditer(texto_reparado):
        numero = m.group(2).replace('.', '')
        if not any(n == numero for t, n, a in normas):
            tipo_simple = 'Norma' if m.group(1).lower() == 'norma' else 'Ley'
            normas.append((tipo_simple, numero, "NULL"))
            
    return normas

# =====================================================================
# 5. NÚCLEO: LECTURA XLSX Y SISTEMA DE DEBUGGING
# =====================================================================
def procesar_excel_normalizado(ruta_archivo):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SET @current_user_id = 1;") 
    
    diccionarios = obtener_diccionarios_bd(cursor)
    df_nacion = descargar_catalogo_infoleg()
    
    print("\n🚀 LEYENDO MATRIZ NORMALIZADA (.XLSX)...")
    try:
        df_excel = pd.read_excel(ruta_archivo, engine='openpyxl')
    except Exception as e:
        print(f"Error crítico al leer el Excel: {e}")
        return
        
    df_excel.columns = [str(c).strip().lower() for c in df_excel.columns]
    
    col_nivel = next((c for c in df_excel.columns if 'nivel' in c), None)
    col_id_jur = next((c for c in df_excel.columns if 'id_jurisdiccion' in c), None)
    col_emisor = next((c for c in df_excel.columns if 'emisor' in c), None)
    col_norma = next((c for c in df_excel.columns if 'normativa' in c), None)
    
    total_filas = len(df_excel)
    print(f"📊 {total_filas} registros detectados para procesar.")
    
    exitos = 0
    registro_errores = []
    
    for index, row in df_excel.iterrows():
        fila_real = index + 2
        
        nivel_raw = row.get(col_nivel, 1) if col_nivel else 1
        try:
            nivel = int(float(nivel_raw))
        except:
            nivel = 1
            
        id_jur_raw = row.get(col_id_jur, None)
        try:
            id_jur_real = int(float(id_jur_raw))
        except:
            id_jur_real = 1 if nivel == 1 else (2 if nivel == 2 else 26)
            
        emisor_raw = str(row.get(col_emisor, '')) if col_emisor else ''
        celda_norma = str(row.get(col_norma, '')) if col_norma else ''
        
        if pd.isna(celda_norma) or celda_norma.strip() == '': 
            registro_errores.append(f"Fila {fila_real}: Celda vacía.")
            continue
            
        normas_detectadas = extraer_norma_unica(celda_norma)
        
        if not normas_detectadas:
            registro_errores.append(f"Fila {fila_real}: Formato irreconocible ('{celda_norma}')")
            continue
            
        tipo_texto, numero, anio_excel = normas_detectadas[0]
        id_tipo_norma = diccionarios['tipo_norma'].get(normalizar_texto(tipo_texto), 1) 
        
        id_emisor_norma = resolver_emisor_por_id_jurisdiccion(emisor_raw, id_jur_real, conn, cursor, diccionarios)
        
        print(f"\n[{fila_real}] Procesando: {tipo_texto.upper()} {numero}/{anio_excel}")
        
        link, sintesis, fecha_pub, anio_real = None, "", None, anio_excel
        if nivel == 1:
            link, sintesis, fecha_pub, anio_real = buscar_nacion(df_nacion, tipo_texto, numero, anio_excel, emisor_raw)
        elif nivel == 2:
            link, sintesis, fecha_pub, anio_real = buscar_pba(tipo_texto, numero, anio_excel, emisor_raw)
        elif nivel == 3:
            nombre_jurisdiccion = diccionarios['jurisdiccion_nombres'].get(id_jur_real, '')
            link, sintesis, fecha_pub, anio_real = buscar_municipal(tipo_texto, numero, anio_excel, nombre_jurisdiccion)
            time.sleep(1)
            
        texto_profundo = extraer_texto_profundo_para_categorias(link, nivel) if link else ""
        
        if len(sintesis) > 600: sintesis = sintesis[:597] + "..."
        if link and len(link) > 500: link = link[:497] + "..."
        anio_int = int(anio_real) if anio_real and str(anio_real).isdigit() and int(anio_real) > 1800 else None

        # PREVENCIÓN DE BASURA: Si el script rechazó la norma por ambigüedad
        if not link and ("ambigua" in sintesis or "encontrada" in sintesis):
            registro_errores.append(f"Fila {fila_real}: {sintesis}")
            continue

        if anio_int is None:
            cursor.execute("SELECT id_norma_bo FROM norma_bo WHERE id_tipo_norma = %s AND id_emisor_norma = %s AND numero = %s AND anio IS NULL", (id_tipo_norma, id_emisor_norma, numero))
        else:
            cursor.execute("SELECT id_norma_bo FROM norma_bo WHERE id_tipo_norma = %s AND id_emisor_norma = %s AND numero = %s AND anio = %s", (id_tipo_norma, id_emisor_norma, numero, anio_int))
            
        row_existente = cursor.fetchone()
        
        try:
            if row_existente:
                id_norma_insertada = row_existente[0]
                if link or fecha_pub:
                    sql_update = """UPDATE norma_bo 
                                    SET sintesis = COALESCE(%s, sintesis), 
                                        url_norma = COALESCE(%s, url_norma), 
                                        fecha_publicacion = COALESCE(%s, fecha_publicacion) 
                                    WHERE id_norma_bo = %s"""
                    cursor.execute(sql_update, (sintesis, link, fecha_pub, id_norma_insertada))
                print(f"   [UPDATE] Norma actualizada (ID: {id_norma_insertada})")
                exitos += 1
            else:
                sql_insert = """INSERT INTO norma_bo 
                                (id_tipo_norma, id_emisor_norma, numero, anio, fecha_publicacion, sintesis, url_norma, id_estado_norma, origen_carga) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, 1, 'Scraping')"""
                cursor.execute(sql_insert, (id_tipo_norma, id_emisor_norma, numero, anio_int, fecha_pub, sintesis, link))
                id_norma_insertada = cursor.lastrowid
                print(f"   [INSERT] Nueva norma insertada (ID: {id_norma_insertada})")
                exitos += 1
            
            cursor.execute("SELECT id_categoria FROM categoria_norma_bo WHERE id_norma_bo = %s", (id_norma_insertada,))
            categorias_existentes = {r[0] for r in cursor.fetchall()}
            
            for cat_desc, id_categoria in diccionarios['categoria'].items():
                if id_categoria not in categorias_existentes:
                    if texto_contiene_categoria(texto_profundo, cat_desc):
                        cursor.execute("INSERT INTO categoria_norma_bo (id_norma_bo, id_categoria) VALUES (%s, %s)", (id_norma_insertada, id_categoria))
                        
            conn.commit()
            
        except mysql.connector.Error as err:
            registro_errores.append(f"Fila {fila_real}: Error al guardar ({err})")
            conn.rollback()

    cursor.close()
    conn.close()
    
    print("\n" + "="*50)
    print("🏁 REPORTE FINAL DE MIGRACIÓN")
    print("="*50)
    print(f"✅ Normas procesadas con éxito: {exitos} de {total_filas}")
    
    if registro_errores:
        print(f"⚠️ Normas descartadas: {len(registro_errores)}")
        for error in registro_errores:
            print(error)
    else:
        print("🎉 ¡Migración perfecta! 0 errores.")
    print("="*50 + "\n")

# EJECUCIÓN DIRECTA SOBRE EXCEL
ruta = "HPV_IFA_Matriz normalizada.xlsx"
procesar_excel_normalizado(ruta)