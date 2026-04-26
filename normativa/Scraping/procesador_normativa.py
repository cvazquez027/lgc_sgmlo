import requests
import pandas as pd
import zipfile
import io
from db_config import get_db_connection

def obtener_url_zip_infoleg():
    url_api = "https://datos.jus.gob.ar/api/3/action/package_show?id=base-de-datos-legislativos-infoleg"
    try:
        response = requests.get(url_api, timeout=10)
        data = response.json()
        for resource in data.get('result', {}).get('resources', []):
            nombre = resource.get('name', '').lower()
            if 'normativa nacional' in nombre and 'muestreo' not in nombre and resource.get('format', '').lower() == 'zip':
                return resource['url']
        return None
    except Exception as e:
        print(f"Error API Nación: {e}")
        return None

def procesar_y_filtrar_nacional(url_zip):
    print("Descargando y filtrando normativa Nacional...")
    columnas_reales = ['id_norma', 'tipo_norma', 'numero_norma', 'fecha_boletin', 'texto_resumido']
    try:
        r = requests.get(url_zip)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            csv_filename = [name for name in z.namelist() if name.endswith('.csv')][0]
            with z.open(csv_filename) as f:
                df = pd.read_csv(f, usecols=lambda c: c in columnas_reales, encoding='utf-8', low_memory=False)
        
        df = df.loc[:, ~df.columns.str.contains('\.')].copy()
        df = df.rename(columns={'id_norma': 'id_origen', 'numero_norma': 'numero', 'fecha_boletin': 'fecha_publicacion', 'texto_resumido': 'sintesis'})
        
        fechas = pd.to_datetime(df['fecha_publicacion'], errors='coerce')
        df['anio'] = fechas.dt.year.astype('Int64')
        df['fecha_publicacion'] = fechas.dt.strftime('%Y-%m-%d')
        df['url_origen'] = df['id_origen'].apply(lambda x: f"https://servicios.infoleg.gob.ar/infolegInternet/verNorma.do?id={x}")
        df['jurisdiccion'] = 'Nacional'
        df['sintesis'] = df['sintesis'].fillna('')

        patron_amb = r'\bimpacto ambiental\b|\bpresupuestos mínimos\b|\bevaluación ambiental\b|\bdesarrollo sustentable\b|\bresiduos peligrosos\b'
        patron_syh = r'\bhigiene y seguridad\b|\bseguridad e higiene\b|\briesgos del trabajo\b|\baccidente laboral\b|\bEPP\b'

        mask_amb = df['sintesis'].str.contains(patron_amb, regex=True, case=False)
        mask_syh = df['sintesis'].str.contains(patron_syh, regex=True, case=False)

        df_filtrado = df[mask_amb | mask_syh].copy()
        df_filtrado['categoria'] = 'Ambas'
        df_filtrado.loc[mask_amb & ~mask_syh, 'categoria'] = 'Ambiente'
        df_filtrado.loc[~mask_amb & mask_syh, 'categoria'] = 'Seguridad e Higiene'

        return df_filtrado
    except Exception as e:
        print(f"Error Procesamiento Nación: {e}")
        return None

def guardar_nacional(df):
    if df is None or df.empty: return
    conexion = get_db_connection()
    if not conexion: return
    try:
        cursor = conexion.cursor()
        sql = "INSERT INTO normativas (id_origen, tipo_norma, numero, anio, fecha_publicacion, sintesis, categoria, url_origen, jurisdiccion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE sintesis=VALUES(sintesis), categoria=VALUES(categoria), url_origen=VALUES(url_origen)"
        df_sql = df[['id_origen', 'tipo_norma', 'numero', 'anio', 'fecha_publicacion', 'sintesis', 'categoria', 'url_origen', 'jurisdiccion']].astype(object).where(pd.notnull(df), None)
        cursor.executemany(sql, [tuple(x) for x in df_sql.to_numpy()])
        conexion.commit()
        print(f"Nación: {cursor.rowcount} filas afectadas.")
    finally:
        conexion.close()

if __name__ == "__main__":
    url = obtener_url_zip_infoleg()
    if url: guardar_nacional(procesar_y_filtrar_nacional(url))