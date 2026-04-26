import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import urllib3
from db_config import get_db_connection

# Desactivamos advertencias SSL por certificados vencidos
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. TÉRMINOS PARA EL BUSCADOR DE JUJUY ---
# Usamos una lista corta para consultar al servidor y no saturarlo con 40 peticiones
frases_buscador = [
    'residuos', 'efluentes'
]

# --- 2. LA ZARANDA DATAV (Whitelist y Blacklist Estricta) ---
# Esto filtra el texto real de lo que devuelva el buscador
frases_clave = [
    r'recursos naturales', r'ordenamiento territorial', r'ordenamiento ambiental del territorio', r'impacto ambiental', 
    r'residuos peligrosos', r'residuos sólidos', r'residuos patogénicos',
    r'efluentes', r'emisiones gaseosas', r'áreas protegidas', r'área protegida',
    r'flora silvestre', r'fauna silvestre', r'bosques nativos', r'cambio climático',
    r'desarrollo sustentable', r'desarrollo sostenible', r'pasivos ambientales', r'evaluación ambiental',
    r'flora', r'fauna', r'control ambiental', r'protección ambiental',
    r'hidrocarbur', r'petróleo', r'vaca muerta', r'gasoducto',
    r'seguridad e higiene', r'higiene y seguridad', r'riesgos del trabajo', 
    r'enfermedades profesionales', r'accidentes de trabajo', r'medicina laboral',
    r'condiciones y medio ambiente de trabajo', r'elementos de protección', 
    r'ergonomía', r'salud ocupacional', r'seguridad industrial', r'ambiente de trabajo', r'nivel de ruido',
    r'ambiente laboral', r'agente de riesgo', r'agentes de riesgo', r'riesgos laborales'
]
patron_whitelist = r'(?i)(' + '|'.join(frases_clave) + r')'
patron_basura = r'(?i)(designar|desígnase|desígnese|nombramiento|juez|fiscal|magistrado|defensor|expropiaci|donación|pensión|jubilación|bonificación)'

def extraer_jujuy_calibrado():
    print("=== SINCRO DATA V: BOLETÍN OFICIAL JUJUY (FUENTE PRIMARIA) ===")
    lista_normas = []
    urls_procesadas = set() # Sistema Anti-Duplicados en memoria
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    for termino in frases_buscador:
        # Categorías: 13 = Leyes, 11 = Decretos
        for cat_id in ['13', '11']:
            tipo_label = "Ley" if cat_id == '13' else "Decreto"
            pagina = 1
            
            print(f"\n🔍 Buscando '{termino}' en {tipo_label}s...")

            while True:
                # URL con paginador de WordPress (paged=X)
                url = f"https://boletinoficial.jujuy.gob.ar/?s={termino.replace(' ', '+')}&cat={cat_id}&paged={pagina}"
                
                try:
                    r = requests.get(url, headers=headers, verify=False, timeout=30)
                    if r.status_code != 200:
                        break
                    
                    soup = BeautifulSoup(r.text, 'html.parser')
                    
                    # CORRECCIÓN 1: Buscar en el div correcto
                    entradas = soup.find_all('div', class_='entry')
                    
                    # Si no hay entradas, terminamos la paginación para este término
                    if not entradas:
                        break

                    insertables = 0

                    for art in entradas:
                        h3_title = art.find('h3', class_='entry-title')
                        div_content = art.find('div', class_='entry-content')
                        
                        if not h3_title or not div_content:
                            continue

                        # Extracción de URL
                        enlace = h3_title.find('a')
                        if not enlace: continue
                        url_norma = enlace.get('href', '')

                        # Evitar procesar el mismo link dos veces
                        if url_norma in urls_procesadas:
                            continue
                        urls_procesadas.add(url_norma)

                        # CORRECCIÓN 2: Separar Título del Boletín y Texto de la Norma
                        titulo_boletin = h3_title.get_text(strip=True)
                        texto_completo = div_content.get_text(separator=" ", strip=True)

                        # --- FILTROS DATAV ---
                        if re.search(patron_basura, texto_completo):
                            continue
                        if not re.search(patron_whitelist, texto_completo):
                            continue

                        # --- PARSEO DE METADATOS ---
                        fecha_pub = "2000-01-01"
                        anio = "2000"
                        match_fecha = re.search(r'(\d{2})/(\d{2})/(\d{4})', titulo_boletin)
                        if match_fecha:
                            fecha_pub = f"{match_fecha.group(3)}-{match_fecha.group(2)}-{match_fecha.group(1)}"
                            anio = match_fecha.group(3)

                        # CORRECCIÓN 4: Extraer el Nro de Ley/Decreto del texto, no del título
                        numero = "0"
                        match_num = re.search(fr'(?i){tipo_label}\s*(?:N[.°º]*\s*|Nro\.?\s*)?([0-9\.]+)', texto_completo)
                        if match_num:
                            numero = match_num.group(1).replace('.', '').strip()

                        # Categorización
                        es_syh = any(w in texto_completo.lower() for w in ['seguridad', 'higiene', 'riesgo', 'laboral', 'accidente', 'ergonomia'])
                        categoria = "Seguridad e Higiene" if es_syh else "Ambiente"

                        lista_normas.append({
                            'id_origen': f"JUJ-{tipo_label.upper()}-{numero}-{anio}",
                            'jurisdiccion': 'Jujuy',
                            'tipo_norma': tipo_label,
                            'numero': numero,
                            'anio': anio,
                            'fecha_publicacion': fecha_pub,
                            'sintesis': texto_completo[:1500] + '...', # Guardamos una buena porción de la síntesis
                            'categoria': categoria,
                            'url_origen': url_norma
                        })
                        insertables += 1

                    if insertables > 0:
                        print(f"    ├ Pág {pagina}: 💾 Útiles guardados en memoria ({insertables})")
                    
                    pagina += 1
                    time.sleep(1) # Pausa ética
                    
                except Exception as e:
                    print(f"  ❌ Error inesperado: {e}")
                    break

    df = pd.DataFrame(lista_normas)
    print(f"\n✨ Extracción en Jujuy finalizada. Total acumulado para la DB: {len(df)}")
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
            (id_origen, jurisdiccion, tipo_norma, numero, anio, fecha_publicacion, sintesis, categoria, url_origen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            sintesis=VALUES(sintesis), categoria=VALUES(categoria), url_origen=VALUES(url_origen)
        """
        # Aseguramos el orden correcto de las columnas para la inserción
        registros = []
        for index, row in df.iterrows():
            registros.append((
                row['id_origen'], row['jurisdiccion'], row['tipo_norma'], 
                row['numero'], row['anio'], row['fecha_publicacion'], 
                row['sintesis'], row['categoria'], row['url_origen']
            ))
            
        cursor.executemany(sql, registros)
        conn.commit()
        print(f"💾 Guardado completado: {cursor.rowcount} registros procesados en MySQL.")
    except Exception as e:
        print(f"❌ Error al guardar en base de datos: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    df_jujuy = extraer_jujuy_calibrado()
    guardar_en_db(df_jujuy)