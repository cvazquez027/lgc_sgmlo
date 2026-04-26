import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import math
import calendar
from datetime import datetime
from db_config import get_db_connection

TIPOS_NORMATIVA = {
    'Ley': 'Law',
    'Decreto': 'Decree',
    'Resolución': 'Resolution',
    'Decreto-ley': 'DecreeLaw',
    'Disposición': 'Disposition',
    'Ordenanza general': 'GeneralOrdinance',
    'Resolución conjunta': 'JointResolution'
}

def extraer_pba_filtro_estricto(anio_inicio=1950, anio_fin=2026):
    print(f"=== SINCRO PBA: MODO WHITELIST ESTRICTA ({anio_inicio}-{anio_fin}) ===")
    lista_normas = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    # 1. LA RED GORDA (Lo que le mandamos al servidor de PBA)
    terminos_url = "ambient|sustentable|sostenible|residu|contamina|hidrocarbur|bosque|ecolog|flora|fauna|higiene|seguridad|riesgo|laboral|accidente|ergonomia"
    
    # 2. LA BLACKLIST (Basura y derogadas)
    patron_basura = r'(?i)(designar|desígnase|desígnese|nombramiento|nómbrase|juez|fiscal|magistrado|defensor|expropiaci|donación|pensión|jubilación|bonificación|subvención|interés legislativo|ciudadano ilustre|exención impositiva|concurso de precios|licitación|adjudícase)'
    patron_derogada = r'(?i)\(DEROGADA POR'

    # 3. LA WHITELIST (El filtro de oro - Frases exactas)
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

    for anio in range(anio_inicio, anio_fin + 1):
        print(f"\n📅 [NIVEL 1] Evaluando Año {anio}...")
        res_anio = procesar_query(anio, headers, terminos_url, patron_basura, patron_derogada, patron_whitelist)
        
        if res_anio is not None:
            lista_normas.extend(res_anio)
            continue
            
        print(f"  ⚠️ [NIVEL 2] Año {anio} supera los 190 registros. Subdividiendo por Tipo de Norma...")
        for nombre_tipo, valor_tipo in TIPOS_NORMATIVA.items():
            res_tipo = procesar_query(anio, headers, terminos_url, patron_basura, patron_derogada, patron_whitelist, raw_type=valor_tipo, log_prefix=nombre_tipo)
            
            if res_tipo is not None:
                lista_normas.extend(res_tipo)
                continue
                
            print(f"    🚨 [NIVEL 3] {nombre_tipo} en {anio} supera los 190 registros. Subdividiendo por Meses...")
            for mes in range(1, 13):
                ultimo_dia = calendar.monthrange(anio, mes)[1]
                fecha_gte = f"01%2F{mes:02d}%2F{anio}"
                fecha_lte = f"{ultimo_dia}%2F{mes:02d}%2F{anio}"
                
                res_mes = procesar_query(anio, headers, terminos_url, patron_basura, patron_derogada, patron_whitelist,
                                         raw_type=valor_tipo, fecha_gte=fecha_gte, fecha_lte=fecha_lte, 
                                         log_prefix=f"{nombre_tipo} - Mes {mes}")
                
                if res_mes is not None: 
                    lista_normas.extend(res_mes)
                else:
                    print(f"      ❌ ERROR CRÍTICO: Más de 190 registros en el mes {mes}. Omitiendo excedente.")

    print(f"\n✨ Extracción finalizada. Total acumulado SUPER LIMPIO para DataV: {len(lista_normas)}")
    return pd.DataFrame(lista_normas)

def procesar_query(anio, headers, terminos, patron_basura, patron_derogada, patron_whitelist, raw_type="", fecha_gte="", fecha_lte="", log_prefix="General"):
    lista_local = []
    pagina = 1
    total_paginas = 1 

    while pagina <= total_paginas:
        param_year = "" if fecha_gte else anio
        url = (
            f"https://normas.gba.gob.ar/resultados?page={pagina}&"
            f"q%5Bterms%5D%5Braw_type%5D={raw_type}&q%5Bterms%5D%5Bnumber%5D=&q%5Bterms%5D%5Byear%5D={param_year}&"
            f"q%5Bwithout_words%5D=&q%5Bwith_some_words%5D={terminos}&"
            f"q%5Bdate_ranges%5D%5Bpublication_date%5D%5Bgte%5D={fecha_gte}&q%5Bdate_ranges%5D%5Bpublication_date%5D%5Blte%5D={fecha_lte}&"
            f"q%5Bsort%5D=by_match_desc"
        )

        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code != 200: break
            soup = BeautifulSoup(r.text, 'html.parser')
            
            if pagina == 1:
                p_total = soup.find('p', class_='total')
                if p_total:
                    match = re.search(r'de\s+([\d\.]+)\s+resultados', p_total.text)
                    if match:
                        total_resultados = int(match.group(1).replace('.', ''))
                        # EL CORTAFUEGOS DE 190 REGISTROS
                        if total_resultados > 190: return None 
                        total_paginas = math.ceil(total_resultados / 10)
                    else: break 
                else: break 

            cards = soup.find_all('div', class_='rule-card')
            if not cards: break

            insertables = 0
            descartados_blacklist = 0
            descartados_whitelist = 0

            for card in cards:
                title_tag = card.find('h3', class_='rule-name').find('a')
                if not title_tag: continue
                
                texto_norma = title_tag.get_text(strip=True)
                href = title_tag['href']

                resumen_header = card.find('h6', string=re.compile('Resumen', re.I))
                sintesis = ""
                if resumen_header:
                    blockquote = resumen_header.find_next('blockquote')
                    if blockquote: sintesis = " ".join(blockquote.get_text(strip=True).split())

                texto_completo = f"{texto_norma} {sintesis}"
                
                # --- FILTROS ---
                # 1. Filtro Blacklist / Derogadas
                if re.search(patron_basura, texto_completo) or re.search(patron_derogada, texto_completo):
                    descartados_blacklist += 1
                    continue

                # 2. Filtro Whitelist (Frases exactas)
                if not re.search(patron_whitelist, texto_completo):
                    descartados_whitelist += 1
                    continue
                # ---------------

                fecha_tag = card.find('span', class_='field-info')
                fecha_raw = fecha_tag.get_text(strip=True) if fecha_tag else ""

                parts = href.split('/')
                tipo_extraido = parts[2].capitalize() if len(parts) > 2 else "Norma"
                anio_ley = parts[3] if len(parts) > 3 else "0000"
                num_ley = parts[4] if len(parts) > 4 else "0"

                # Clasificación DataV
                es_syh = any(w in sintesis.lower() for w in ['seguridad', 'higiene', 'riesgo', 'laboral', 'accidente', 'ocupacional', 'ergonomia'])
                categoria = "Seguridad e Higiene" if es_syh else "Ambiente"

                lista_local.append({
                    'id_origen': f"PBA-{tipo_extraido.upper()}-{anio_ley}-{num_ley}",
                    'tipo_norma': tipo_extraido,
                    'numero': num_ley,
                    'anio': anio_ley,
                    'fecha_publicacion': format_fecha(fecha_raw) or f"{anio_ley}-01-01", 
                    'sintesis': sintesis,
                    'categoria': categoria,
                    'url_origen': f"https://normas.gba.gob.ar{href}",
                    'jurisdiccion': 'PBA'
                })
                insertables += 1
            
            print(f"    ├ Pág {pagina}/{total_paginas}: 🗑️ Blacklist({descartados_blacklist}) | 🛡️ Sin Frase({descartados_whitelist}) | 💾 Útiles({insertables})")
            pagina += 1
            time.sleep(0.5) 

        except Exception as e:
            print(f"  ❌ Error: {e}")
            break

    return lista_local

def format_fecha(f):
    try: return datetime.strptime(f, '%d/%m/%Y').strftime('%Y-%m-%d')
    except: return None

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
    df_pba = extraer_pba_filtro_estricto(2020, 2026) 
    guardar_en_db(df_pba)