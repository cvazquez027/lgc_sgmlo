import requests
import pandas as pd
from db_config import get_db_connection

def obtener_url_csv_caba():
    url_api = "https://data.buenosaires.gob.ar/api/3/action/package_search?q=normativa"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url_api, headers=headers, timeout=15)
        data = response.json()
        for result in data.get('result', {}).get('results', []):
            for resource in result.get('resources', []):
                if resource.get('format', '').lower() == 'csv' and 'normativa' in resource.get('name', '').lower():
                    return resource['url']
        return None
    except Exception as e:
        print(f"Error API CABA: {e}")
        return None

def procesar_y_filtrar_caba(url_csv):
    print("Descargando y filtrando normativa CABA...")
    mapeo = {'norma_id': 'id_origen', 'norma_tipo': 'tipo_norma', 'norma_numero': 'numero', 'norma_fecha_publicacion': 'fecha_publicacion', 'norma_sintesis': 'sintesis'}
    try:
        df = pd.read_csv(url_csv, usecols=list(mapeo.keys()), encoding='utf-8', low_memory=False)
        df = df.rename(columns=mapeo)
        
        fechas = pd.to_datetime(df['fecha_publicacion'], dayfirst=True, errors='coerce')
        df['anio'] = fechas.dt.year.astype('Int64')
        df['fecha_publicacion'] = fechas.dt.strftime('%Y-%m-%d')
        df['url_origen'] = df['id_origen'].apply(lambda x: f"https://boletinoficial.buenosaires.gob.ar/normativaba/norma/{x}")
        df['jurisdiccion'] = 'CABA'
        df['sintesis'] = df['sintesis'].fillna('')

        patron_amb = r'\bimpacto ambiental\b|\bpresupuestos mínimos\b|\bevaluación ambiental\b|\bdesarrollo sustentable\b|\bresiduos peligrosos\b'
        patron_syh = r'\bhigiene y seguridad\b|\bseguridad e higiene\b|\bcondiciones y medio ambiente de trabajo\b|\briesgos del trabajo\b|\bEPP\b'

        mask_amb = df['sintesis'].str.contains(patron_amb, regex=True, case=False)
        mask_syh = df['sintesis'].str.contains(patron_syh, regex=True, case=False)

        df_filtrado = df[mask_amb | mask_syh].copy()
        df_filtrado['categoria'] = 'Ambas'
        df_filtrado.loc[mask_amb & ~mask_syh, 'categoria'] = 'Ambiente'
        df_filtrado.loc[~mask_amb & mask_syh, 'categoria'] = 'Seguridad e Higiene'

        return df_filtrado
    except Exception as e:
        print(f"Error Procesamiento CABA: {e}")
        return None

def guardar_caba(df):
    if df is None or df.empty: return
    conexion = get_db_connection()
    if not conexion: return
    try:
        cursor = conexion.cursor()
        sql = "INSERT INTO normativas (id_origen, tipo_norma, numero, anio, fecha_publicacion, sintesis, categoria, url_origen, jurisdiccion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE sintesis=VALUES(sintesis), categoria=VALUES(categoria), url_origen=VALUES(url_origen)"
        df_sql = df[['id_origen', 'tipo_norma', 'numero', 'anio', 'fecha_publicacion', 'sintesis', 'categoria', 'url_origen', 'jurisdiccion']].astype(object).where(pd.notnull(df), None)
        cursor.executemany(sql, [tuple(x) for x in df_sql.to_numpy()])
        conexion.commit()
        print(f"CABA: {cursor.rowcount} filas afectadas.")
    finally:
        conexion.close()

if __name__ == "__main__":
    url = obtener_url_csv_caba()
    if url: guardar_caba(procesar_y_filtrar_caba(url))