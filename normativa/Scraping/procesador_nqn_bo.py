import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import urllib3
from db_config import get_db_connection

# Desactivar advertencias de seguridad por certificados SSL inválidos
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) 

def extraer_neuquen_bo():
    print("=== SINCRO DATA V: BOLETÍN OFICIAL NEUQUÉN (FUENTE PRIMARIA) ===")
    
    # 1. LA WHITELIST Y BLACKLIST DE DATAV
    frases_clave = [
        # Ambiente General
        r'recursos naturales', r'ordenamiento territorial', r'ordenamiento ambiental del territorio', r'impacto ambiental', 
        r'residuos peligrosos', r'residuos sólidos', r'residuos patogénicos',
        r'efluentes', r'emisiones gaseosas', r'áreas protegidas', r'área protegida',
        r'flora silvestre', r'fauna silvestre', r'bosques nativos', r'cambio climático',
        r'desarrollo sustentable', r'desarrollo sostenible', r'pasivos ambientales', r'evaluación ambiental',
        r'flora', r'fauna', r'control ambiental', r'protección ambiental',
        
        # Industria Neuquén / Hidrocarburos
        r'hidrocarbur', r'petróleo', r'vaca muerta', r'gasoducto',
        
        # Seguridad e Higiene Laboral
        r'seguridad e higiene', r'higiene y seguridad', r'riesgos del trabajo', 
        r'enfermedades profesionales', r'accidentes de trabajo', r'medicina laboral',
        r'condiciones y medio ambiente de trabajo', r'elementos de protección', 
        r'ergonomía', r'salud ocupacional', r'seguridad industrial', r'ambiente de trabajo', r'nivel de ruido',
        r'ambiente laboral', r'agente de riesgo', r'agentes de riesgo', r'riesgos laborales'
    ]
    patron_whitelist = r'(?i)(' + '|'.join(frases_clave) + r')'
    patron_basura = r'(?i)(designar|desígnase|desígnese|nombramiento|juez|fiscal|magistrado|defensor|expropiaci|donación|pensión|jubilación|bonificación)'

    lista_normas = []
    pagina = 1
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    print("📡 Conectando al Boletín Oficial / Infoleg de Neuquén...")

    while True:
        # URL DEL BUSCADOR DE NEUQUÉN
        url_busqueda = f"https://infoleg.neuquen.gov.ar/busqueda?page={pagina}" 
        
        try:
            # Petición con verify=False para saltar el error de SSL del servidor gubernamental
            r = requests.get(url_busqueda, headers=headers, timeout=20, verify=False)
            
            if r.status_code != 200:
                print(f"❌ Error HTTP {r.status_code} en página {pagina}. Fin del escaneo.")
                break
                
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Buscamos las filas de resultados
            filas = soup.find_all('tr') 
            
            if not filas or len(filas) <= 1: 
                print(f"  └ Fin del recorrido. No hay más datos en la página {pagina}.")
                break
                
            insertables = 0
            
            for fila in filas:
                texto_completo = fila.get_text(separator=" ", strip=True)
                
                # Ignorar encabezados de tabla
                if "Tipo de Norma" in texto_completo or not texto_completo:
                    continue
                
                # --- FILTROS DATAV ---
                if re.search(patron_basura, texto_completo):
                    continue
                if not re.search(patron_whitelist, texto_completo):
                    continue
                    
                # Extraer enlace al PDF o texto oficial
                enlace = fila.find('a', href=True)
                href = enlace['href'] if enlace else ""
                url_completa = f"https://infoleg.neuquen.gov.ar{href}" if href.startswith('/') else href
                
                # --- PARSEO DE METADATOS MEDIANTE REGEX ---
                match_norma = re.search(r'(?i)(Ley|Decreto|Resolución|Disposición)\s*(?:N[.°º]*\s*|Nro\.?\s*)?([0-9\.]+)(?:/(\d+))?', texto_completo)
                
                tipo_norma = "Norma"
                numero = "0"
                anio = "0000"
                
                if match_norma:
                    tipo_norma = match_norma.group(1).capitalize()
                    numero = match_norma.group(2).replace('.', '').strip()
                    anio_norma = match_norma.group(3)
                    if anio_norma:
                        anio = f"20{anio_norma}" if len(anio_norma) == 2 and int(anio_norma) <= 50 else (f"19{anio_norma}" if len(anio_norma) == 2 else anio_norma)

                # Buscar un año de 4 dígitos si no vino en el número
                if anio == "0000":
                    match_anio_texto = re.search(r'\b(19\d{2}|20\d{2})\b', texto_completo)
                    if match_anio_texto:
                        anio = match_anio_texto.group(1)

                es_syh = any(w in texto_completo.lower() for w in ['seguridad', 'higiene', 'riesgo', 'laboral', 'accidente', 'ergonomia'])
                categoria = "Seguridad e Higiene" if es_syh else "Ambiente"

                lista_normas.append({
                    'id_origen': f"NQN-BO-{tipo_norma.upper()}-{numero}-{anio}",
                    'tipo_norma': tipo_norma,
                    'numero': numero,
                    'anio': anio,
                    'fecha_publicacion': f"{anio}-01-01", 
                    'sintesis': texto_completo[:500] + '...',
                    'categoria': categoria,
                    'url_origen': url_completa,
                    'jurisdiccion': 'Neuquén'
                })
                insertables += 1
                
            print(f"    ├ Pág {pagina}: 💾 Útiles guardados en memoria ({insertables})")
            
            pagina += 1
            time.sleep(1) # Pausa ética para no saturar el servidor de Neuquén
            
        except Exception as e:
            print(f"  ❌ Error inesperado: {e}")
            break

    df = pd.DataFrame(lista_normas).drop_duplicates(subset=['id_origen']) if lista_normas else pd.DataFrame()
    print(f"\n✨ Extracción en Neuquén finalizada. Total acumulado para la DB: {len(df)}")
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
    df_nqn = extraer_neuquen_bo()
    guardar_en_db(df_nqn)