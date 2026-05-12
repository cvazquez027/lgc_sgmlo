import requests
import pandas as pd
from datetime import datetime
import re

# ==========================================
# ⚙️ CONFIGURACIÓN DEL SISTEMA
# ==========================================
API_KEY_BACKEND = "Token_Seguro_Scraper_2026_XyZ!"
URL_LEER_CATEGORIAS = "http://localhost/lgc_sgmlo/backend/api/boletin/leer_categorias_bot.php"
URL_GUARDAR_NORMAS = "http://localhost/lgc_sgmlo/backend/api/boletin/ingresar_scraping.php"

ID_EMISOR_CABA = 2 

MAPEO_TIPOS = {
    "LEY": 1,
    "DECRETO": 2,
    "RESOLUCION": 3,
    "DISPOSICION": 4
}
ID_TIPO_DEFECTO = 5

# ==========================================
# 🧠 FUNCIONES DEL MOTOR DINÁMICO
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
            # Patrón para buscar la frase exacta como palabra completa
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

def obtener_url_csv_caba():
    """Busca dinámicamente el CSV oficial ACTUAL en Data GCBA, ignorando históricos."""
    url_api = "https://data.buenosaires.gob.ar/api/3/action/package_search?q=normativa"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url_api, headers=headers, timeout=15)
        data = response.json()
        
        csvs_encontrados = []
        for result in data.get('result', {}).get('results', []):
            for resource in result.get('resources', []):
                nombre = resource.get('name', '').lower()
                if resource.get('format', '').lower() == 'csv' and 'normativa' in nombre:
                    csvs_encontrados.append({
                        'nombre': nombre,
                        'url': resource['url']
                    })
                    
        # 🧠 INTELIGENCIA DE SELECCIÓN:
        for csv in csvs_encontrados:
            nombre_archivo = csv['nombre']
            
            # Filtramos (descartamos) explícitamente los archivos que son recortes históricos
            if '1996' in nombre_archivo or '2007' in nombre_archivo or '2018' in nombre_archivo:
                continue
                
            print(f"🎯 ¡Archivo maestro encontrado!: '{nombre_archivo}'")
            return csv['url']
            
        # Plan B (Fallback por si cambian la forma de nombrar)
        if csvs_encontrados:
            return csvs_encontrados[-1]['url']
            
        return None
    except Exception as e:
        print(f"❌ Error API CKAN CABA: {e}")
        return None

# ==========================================
# 🚀 EJECUCIÓN PRINCIPAL: ETL
# ==========================================
def ejecutar_bot_caba():
    # Para forzar una fecha (Descomentá y cambiá si querés probar)
    # fecha_hoy_str = '2024-03-01'  
    fecha_hoy_str = datetime.now().strftime('%Y-%m-%d')
    print(f"\n[{datetime.now()}] 🤖 Iniciando Bot CABA para la fecha: {fecha_hoy_str}")
    
    diccionario_categorias = obtener_diccionario_categorias()
    if not diccionario_categorias: return
    
    url_csv = obtener_url_csv_caba()
    if not url_csv:
        print("❌ No se pudo localizar el CSV oficial de CABA.")
        return
        
    print(f"📥 Descargando y procesando dataset maestro (2019-Actualidad)...")
    
    try:
        # 1. EXTRACT INVENCIBLE Y DEFINITIVO: 
        # Descubrimos que el GCBA usa el "pipe" (|) como separador en este dataset.
        df = pd.read_csv(url_csv, sep='|', encoding='utf-8', low_memory=False, on_bad_lines='skip', dtype=str)

        cols_reales = df.columns.tolist()
        print(f"🛠️ Columnas reales detectadas: {cols_reales}")

        # Limpiamos columnas basura (las famosas "Unnamed" o columnas vacías)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # AUTO-MAPEO: Buscamos nombres de columnas tolerando variaciones
        cols_lower = [c.lower() for c in df.columns]
        
        def find_col(posibles):
            for p in posibles:
                for i, c in enumerate(cols_lower):
                    if c == p: return df.columns[i] # Devolvemos el nombre real con mayúsculas/minúsculas originales
            return None
        
        col_id = find_col(['norma_id', 'id_norma', 'id_origen', 'id', 'idnorma'])
        col_tipo = find_col(['norma_tipo', 'tipo_norma', 'tipo', 'tiponorma', 'clase_norma'])
        col_numero = find_col(['norma_numero', 'numero_norma', 'numero', 'numeronorma', 'nro_norma'])
        col_fecha = find_col(['norma_fecha_publicacion', 'fecha_publicacion', 'fecha', 'fechapublicacion', 'fecha_boletin'])
        col_sintesis = find_col(['norma_sintesis', 'sintesis', 'resumen', 'descripcion', 'normasintesis'])
        
        if not all([col_id, col_tipo, col_fecha]):
            print(f"❌ Faltan columnas clave. Detectadas: ID={col_id}, Tipo={col_tipo}, Fecha={col_fecha}")
            return
            
        # Renombramos usando las columnas que el bot adivinó
        df = df.rename(columns={
            col_id: 'id_origen', 
            col_tipo: 'tipo_norma', 
            col_numero: 'numero', 
            col_fecha: 'fecha_publicacion', 
            col_sintesis: 'sintesis'
        })
        
        # Estandarizamos fechas
        fechas = pd.to_datetime(df['fecha_publicacion'], errors='coerce')
        
        # --- 🔦 RADAR DE FECHAS ---
        fechas_validas = fechas.dropna()
        if not fechas_validas.empty:
            fecha_maxima = fechas_validas.max().strftime('%Y-%m-%d')
            ultimas_fechas = fechas_validas.dt.strftime('%Y-%m-%d').sort_values(ascending=False).unique()[:5]
            print(f"📅 El archivo llega hasta el: {fecha_maxima}")
            print(f"📅 Top 5 fechas recientes: {ultimas_fechas.tolist()}")
        else:
            print("⚠️ ATENCIÓN: No hay fechas válidas.")
        # --------------------------

        df['anio'] = fechas.dt.year.fillna(datetime.now().year).astype(int)
        df['fecha_publicacion'] = fechas.dt.strftime('%Y-%m-%d')
        
        # 2. TRANSFORM (Filtro Rápido): Nos quedamos SOLO con las de hoy
        df_hoy = df[df['fecha_publicacion'] == fecha_hoy_str].copy()
        
    except Exception as e:
        print(f"❌ Error al procesar el CSV con Pandas: {e}")
        return

    if df_hoy.empty:
        print(f"ℹ️ No hay normas publicadas el {fecha_hoy_str} en el portal de datos.")
        # SUGERENCIA: Si la consola te dice que llega hasta otra fecha, copiala y cambiala arriba.
        return
        
    print(f"🔍 Se filtraron {len(df_hoy)} normas del día. Aplicando Inteligencia Legal...")
    
    normas_procesadas = []
    
    for _, row in df_hoy.iterrows():
        tipo_texto = str(row.get('tipo_norma', '')).upper().strip()
        sintesis = str(row.get('sintesis', ''))
        if sintesis.lower() == 'nan' or not sintesis: sintesis = 'Sin síntesis registrada'
        
        id_origen = str(row.get('id_origen', ''))
        numero = str(row.get('numero', 'S/N'))
        if numero.lower() == 'nan': numero = 'S/N'
        
        anio_norma = row.get('anio')
        id_tipo = MAPEO_TIPOS.get(tipo_texto, ID_TIPO_DEFECTO)
        
        # Categorizamos dinámicamente con las 121 reglas de tu base de datos
        categorias_detectadas = categorizar_texto(sintesis, diccionario_categorias)
        
        url_oficial = f"https://boletinoficial.buenosaires.gob.ar/normativaba/norma/{id_origen}" if id_origen and id_origen.lower() != 'nan' else ""

        norma_formateada = {
            "id_tipo_norma": id_tipo,
            "id_emisor_norma": ID_EMISOR_CABA,
            "numero": numero,
            "anio": int(anio_norma),
            "fecha_publicacion": fecha_hoy_str,
            "sintesis": sintesis,
            "url_norma": url_oficial,
            "categorias": categorias_detectadas
        }
        normas_procesadas.append(norma_formateada)

    # 3. LOAD: Enviar paquete al Backend Seguro
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
            print(f"Detalle devuelto por PHP: {res_backend.text}")

if __name__ == "__main__":
    ejecutar_bot_caba()