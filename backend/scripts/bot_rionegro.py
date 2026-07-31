#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 BOLETÍN OFICIAL DE LA PROVINCIA DE RÍO NEGRO  —  id_jurisdiccion 17
===============================================================================

DESCUBRIMIENTO
--------------
El sitio de Río Negro expone un endpoint JSON (AJAX) que lista todas las 
ediciones del año categorizadas por mes. Cada elemento tiene su fecha ISO,
el nombre del archivo y la ruta de descarga. 

EXTRACCIÓN
----------
Río Negro utiliza una mezcla de formatos en sus encabezados de normas:
1. Formato GDE: DECTO-2026-701-E-GDERNE-RNE
2. Formato Clásico: Resolución Nº 651 o DECRETO Nº 676.-

Se ignora el sumario saltando hasta la segunda aparición de 'SECCIÓN 
ADMINISTRATIVA' y se frena la lectura al llegar a 'FALLOS' o 'EDICTOS'.
"""

import os
import re
import sys
import json
import time
import argparse
import unicodedata
from datetime import date

import requests
import urllib3

# Desactivamos advertencias de certificados SSL por ser un dominio gubernamental
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ===========================================================================
# CONFIGURACIÓN
# ===========================================================================
def get_env_clean(key, default=None):
    v = os.getenv(key, default)
    if v:
        v = v.strip().strip('"').strip("'")
    return v

API_KEY_BACKEND = get_env_clean('API_KEY_BACKEND', 'Token_Seguro_Scraper_2026_XyZ!')
URL_HISTORIAL = get_env_clean(
    'URL_HISTORIAL', 'http://localhost/lgc_sgmlo/backend/api/boletin/historial_scraping.php')
URL_GUARDAR_NORMAS = get_env_clean(
    'URL_GUARDAR_NORMAS', 'http://localhost/lgc_sgmlo/backend/api/boletin/ingresar_scraping.php')

SITIO = 'https://boletinoficial.rionegro.gov.ar'
# catid=1273 corresponde al año 2026 según el análisis de la API
URL_API = f'{SITIO}/pages/ajax/getBoletinDataJson.php?catid=1273'

HEADERS_WEB = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
    'X-Requested-With': 'XMLHttpRequest'
}

REINTENTOS = 3
ESPERA_REINTENTO = 3
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700

# ===========================================================================
# NORMALIZACIÓN
# ===========================================================================
def _sin_acentos(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

def _compacto(texto):
    return re.sub(r'\s+', ' ', (texto or '')).strip()

def _limpiar_numero(num):
    if num is None:
        return ''
    n = str(num).strip(' .')
    m = re.fullmatch(r'(\d{1,3})\.(\d{3})', n)
    if m:
        n = m.group(1) + m.group(2)
    n = re.sub(r'[^\d]', '', n)
    return n.lstrip('0') or ('0' if n else '')

# ===========================================================================
# DESCUBRIMIENTO WEB (VÍA JSON)
# ===========================================================================
_SESION = None

def sesion():
    global _SESION
    if _SESION is None:
        _SESION = requests.Session()
        _SESION.headers.update(HEADERS_WEB)
    return _SESION

def descargar(url, timeout=45, esperar_pdf=False):
    for intento in range(1, REINTENTOS + 1):
        try:
            r = sesion().get(url, timeout=timeout, verify=False)
            if r.status_code == 404:
                return None
            if r.status_code == 200:
                if not esperar_pdf:
                    return r.text
                return r.content if r.content[:5] == b'%PDF-' else None
            if r.status_code < 500:
                return None
        except requests.RequestException as e:
            if intento == REINTENTOS:
                raise RuntimeError(f"Error de red pidiendo {url}: {e}")
        time.sleep(ESPERA_REINTENTO * intento)
    return None

def listar_boletines_json():
    """Consume la API JSON de Río Negro y devuelve metadatos de los PDFs."""
    respuesta = descargar(URL_API)
    if not respuesta:
        return []
    try:
        data = json.loads(respuesta)
        boletines = []
        if not data or not isinstance(data, list) or 'documentos' not in data[0]:
            return []
            
        meses = data[0]['documentos']
        for mes in meses:
            for elemento in mes.get('elementos', []):
                nombre_archivo = elemento.get('nombre', '')
                fecha_iso = elemento.get('fecha', '')
                ruta_base = elemento.get('ruta', '')
                
                m_numero = re.search(r'(\d+)', nombre_archivo)
                numero = m_numero.group(1) if m_numero else ''
                es_suplemento = 'supl' in nombre_archivo.lower()
                url_pdf = f"{SITIO}{ruta_base}{nombre_archivo}"
                
                boletines.append({
                    'numero': numero,
                    'fecha_iso': fecha_iso,
                    'es_suplemento': es_suplemento,
                    'url': url_pdf,
                    'nombre_archivo': nombre_archivo
                })
        return boletines
    except Exception as e:
        print(f"Error parseando JSON: {e}", file=sys.stderr)
        return []

# ===========================================================================
# LECTURA DEL PDF Y EXTRACCIÓN
# ===========================================================================
# Limpiador de los pies de página para no interrumpir el flujo del texto
RE_PIE_PAGINA = re.compile(
    r'(?:Firmado Digitalmente por[^\n]*\n)?\d{1,2}\s+de\s+[a-z]+\s+de\s+\d{4}\s+BOLETIN\s+OFICIAL\s+Nº\s+\d+\s+\d+', 
    re.IGNORECASE | re.MULTILINE)

def leer_paginas(ruta_pdf):
    if pdfplumber is None:
        raise RuntimeError("Falta pdfplumber: pip install pdfplumber")
    
    paginas = []
    with pdfplumber.open(ruta_pdf) as pdf:
        for page in pdf.pages:
            texto = page.extract_text() or ''
            paginas.append(texto)
            
    cuerpo_completo = '\n'.join(paginas)
    cuerpo_completo = RE_PIE_PAGINA.sub('\n', cuerpo_completo)
    return cuerpo_completo

# Expresiones regulares de captura estrictas para evitar falsos positivos
RE_CABECERA = re.compile(
    r'^[ \t]*(?P<tipo_gde>DECTO|RESOL|DISPO|LEY)-(?P<anio_gde>\d{4})-(?P<numero_gde>\d+)[^\s\n]*'
    r'|'
    r'^[ \t]*(?P<tipo_texto>LEY|DECRETO|RESOLUCI[ÓO]N|DISPOSICI[ÓO]N)\s+N[º°o]?\.?\s*(?P<numero_texto>\d[\d.]*)[ \t]*(?:\r?\n|\.-)',
    re.MULTILINE | re.IGNORECASE)

RE_ARTICULO1 = re.compile(
    r'ART[ÍI]?CULO\s*(?:N[º°]\s*)?1(?!\d)\s*[º°]?\s*[.:,;-]+\s*'
    r'(?P<texto>[\s\S]{0,1200}?)(?=ART[ÍI]?CULO\s*(?:N[º°]\s*)?2(?!\d)|\Z)',
    re.IGNORECASE)

def _organismo_precedente(cuerpo, pos_header):
    antes = cuerpo[:pos_header]
    lineas = antes.split('\n')
    encontradas = []
    for linea in reversed(lineas[-6:]):
        t = linea.strip()
        if not t or t in ['VISTO:', 'CONSIDERANDO:', 'DECRETOS', 'RESOLUCIONES', 'DECRETOS SINTETIZADOS']: break
        if t.isupper() and len(t) > 3:
            encontradas.insert(0, t)
        elif encontradas:
            break
    return _compacto(' '.join(encontradas))

def extraer_normas(cuerpo_completo, fecha_boletin, anio_boletin):
    # Saltamos el sumario buscando la segunda aparición de 'SECCIÓN ADMINISTRATIVA'
    idx_sumario = cuerpo_completo.find('SECCIÓN ADMINISTRATIVA')
    if idx_sumario != -1:
        idx_inicio = cuerpo_completo.find('SECCIÓN ADMINISTRATIVA', idx_sumario + 20)
        if idx_inicio == -1:
            idx_inicio = idx_sumario
    else:
        idx_inicio = 0
        
    bloque_normas = cuerpo_completo[idx_inicio:]
    
    # Cortamos antes de que arranquen los edictos y fallos
    techos = ['\nFALLOS', '\nSECCIÓN JUDICIAL', '\nEDICTOS', '\nLICITACIONES', '\nSECCIÓN COMERCIO', '\nCOMUNICADOS']
    idx_fin = len(bloque_normas)
    for techo in techos:
        idx = bloque_normas.find(techo)
        if idx != -1 and idx < idx_fin:
            idx_fin = idx
            
    bloque_normas = bloque_normas[:idx_fin]

    marcas = []
    for m in RE_CABECERA.finditer(bloque_normas):
        tipo_gde = m.group('tipo_gde')
        if tipo_gde:
            t = tipo_gde.upper()
            if t == 'DECTO': tipo = 'DECRETO'
            elif t == 'RESOL': tipo = 'RESOLUCION'
            elif t == 'DISPO': tipo = 'DISPOSICION'
            else: tipo = t
            numero = m.group('numero_gde')
        else:
            tipo = _sin_acentos((m.group('tipo_texto') or '').upper())
            numero = m.group('numero_texto')
            
        marcas.append([m.start(), m.end(), tipo, _limpiar_numero(numero)])
        
    # Deduplicamos por número de norma
    marcas_filtradas = []
    numeros_vistos = set()
    for m in marcas:
        if m[3] and m[3] not in numeros_vistos:
            marcas_filtradas.append(m)
            numeros_vistos.add(m[3])
    
    normas = []
    for i, (ini, fin_cab, tipo, numero) in enumerate(marcas_filtradas):
        fin_bloque = marcas_filtradas[i+1][0] if i+1 < len(marcas_filtradas) else len(bloque_normas)
        bloque = bloque_normas[fin_cab:fin_bloque]
        
        # Limpieza cosmética del bloque para mejorar la extracción de la síntesis si no hay Artículo 1°
        bloque_limpio = re.sub(r'^[\s\n]*-RNE[\s\n]*', '', bloque)
        bloque_limpio = re.sub(r'^[ \t]*Viedma,.*?\n', '', bloque_limpio)
        
        m_art1 = RE_ARTICULO1.search(bloque)
        sintesis = _compacto(m_art1.group('texto')) if m_art1 else _compacto(bloque_limpio[:400])
        
        emisor = _organismo_precedente(bloque_normas, ini)
        if not emisor:
            emisor = 'PODER EJECUTIVO' if tipo == 'DECRETO' else 'PODER EJECUTIVO'
            
        normas.append({
            'tipo': tipo,
            'numero': numero,
            'anio': str(anio_boletin),
            'sintesis': sintesis,
            'texto_completo': bloque,
            'fecha_publicacion': fecha_boletin,
            'emisor': emisor,
        })
        
    return normas

# ===========================================================================
# BACKEND Y CLASIFICACIÓN
# ===========================================================================
UMBRAL_INDIVIDUAL = 3

PATRONES_INDIVIDUAL = [
    (r'\bDes[íi]gn[ae]se\b',                                  4, 'designación'),
    (r'\bAc[ée]pt[ae]se\b[\s\S]{0,80}\brenuncia\b',           4, 'renuncia'),
    (r'\brenuncia\s+presentada\s+por\b',                      4, 'renuncia'),
    (r'\bPromu[ée]v[ae]se\b',                                 4, 'promoción de un agente'),
    (r'\bContrato\s+de\s+Locaci[óo]n\s+de\s+Servicios\b',     3, 'contrato de personal'),
    (r'\bInstr[úu]yase\s+Sumario\s+Administrativo\b',         4, 'apertura de sumario administrativo a una persona'),
    (r'\bexoneraci[óo]n\b|\bcesant[íi]a\b',                   4, 'sanción expulsiva'),
    (r'\bRecurso\s+Jer[áa]rquico\s+interpuesto\b',            3, 'recurso de un particular'),
    (r'\bOt[óo]rg[au]ese\b[\s\S]{0,60}\bLicencia\b',          3, 'licencia'),
    (r'\bBaja\s+definitiva\b|\bJubilaci[óo]n\b',              3, 'baja / jubilación'),
    (r'\bD\.?N\.?I\.?\s*N?[º°]?\s*[\d.]{6,}',                 1, 'menciona DNI de una persona'),
]

PATRONES_GENERAL = [
    (r'\bCr[ée]a(?:se)?\s+el\b|\bCr[ée]ase\b',                -3, 'creación normativa'),
    (r'\bApru[ée]b[ae](?:nse)?\b[\s\S]{0,60}(?:Reglamento|Manual|Anexo)', -3, 'aprobación normativa'),
    (r'\bDeclara(?:se)?\b[\s\S]{0,60}\bInter[ée]s\b',         -3, 'declaración de interés'),
    (r'\bDer[óo]ganse\b|\bDer[óo]gase\b',                     -3, 'derogación'),
]

def clasificar_norma(tipo, sintesis, texto_completo):
    if tipo == 'LEY':
        return False, -99, ['ley: siempre general']

    puntaje, motivos = 0, []
    art = sintesis or ''
    cuerpo = texto_completo or ''

    for patron, peso, etiqueta in PATRONES_INDIVIDUAL:
        if re.search(patron, art, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'+{peso} síntesis: {etiqueta}')
        elif re.search(patron, cuerpo, re.IGNORECASE):
            medio = max(1, peso // 2)
            puntaje += medio
            motivos.append(f'+{medio} cuerpo: {etiqueta}')

    for patron, peso, etiqueta in PATRONES_GENERAL:
        if re.search(patron, art, re.IGNORECASE) or re.search(patron, cuerpo, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'{peso}: {etiqueta}')

    return (puntaje >= UMBRAL_INDIVIDUAL), puntaje, motivos

def salida(status, message, total=None, extra=None):
    out = {"status": status, "message": message}
    if total is not None: out["total_enviadas"] = total
    if extra: out.update(extra)
    print(json.dumps(out))
    sys.exit(0)

def verificar_boletin_procesado(id_jurisdiccion, fecha_boletin):
    try:
        r = requests.post(URL_HISTORIAL, json={"id_jurisdiccion": id_jurisdiccion, "fecha_boletin": fecha_boletin, "accion": "verificar"}, headers={"Authorization": f"Bearer {API_KEY_BACKEND}"}, timeout=10)
        return r.json().get('procesado', False)
    except Exception:
        return False

def registrar_boletin_procesado(id_jurisdiccion, fecha_boletin, cantidad):
    try:
        requests.post(URL_HISTORIAL, json={"id_jurisdiccion": id_jurisdiccion, "fecha_boletin": fecha_boletin, "accion": "registrar", "cantidad_normas": cantidad}, headers={"Authorization": f"Bearer {API_KEY_BACKEND}"}, timeout=10)
    except Exception:
        pass

def guardar_debug(contenido, nombre):
    try:
        with open(nombre, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"Guardado {nombre} para depuración", file=sys.stderr)
    except Exception:
        pass

def construir_sintesis(norma):
    cuerpo = _compacto(norma.get('sintesis') or '').strip(' .-:')
    if len(cuerpo) > MAX_SINTESIS:
        cuerpo = cuerpo[:MAX_SINTESIS].rsplit(' ', 1)[0] + '…'
    return cuerpo or f"{norma.get('tipo')} {norma.get('numero')}"

def recortar_texto(texto, tope=MAX_TEXTO_COMPLETO):
    texto = texto or ''
    if len(texto) <= tope: return texto
    marca = ' […] '
    cabeza = int((tope - len(marca)) * 0.55)
    cola = tope - len(marca) - cabeza
    return texto[:cabeza] + marca + texto[-cola:]

def url_norma(url_pdf, norma):
    base = f"{norma.get('tipo')}-{norma.get('numero')}-{norma.get('anio')}"
    slug = re.sub(r'[^A-Za-z0-9]+', '-', _sin_acentos(base)).strip('-')
    return f"{url_pdf}#{slug}"

# ===========================================================================
# EJECUCIÓN
# ===========================================================================
def _main():
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Río Negro.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se descubre por la web')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--pdf', metavar='ARCHIVO', help='usar un PDF local (pruebas)')
    ap.add_argument('--fecha', metavar='AAAA-MM-DD', help='fuerza la fecha del boletín a pedir')
    ap.add_argument('--todas', action='store_true', help='muestra individuales')
    ap.add_argument('--sin-filtro', action='store_true', help='envía todo sin filtrar')
    ap.add_argument('--volcar', action='store_true', help='imprime resumen y sale')
    ap.add_argument('--suplemento', action='store_true', help='prioriza el suplemento de esa fecha')
    args = ap.parse_args()

    fecha_boletin = args.fecha
    url_pdf = ''
    ruta_temporal = None
    
    if args.pdf:
        ruta_pdf = args.pdf
        print(f"Usando PDF local: {args.pdf}", file=sys.stderr)
        if not fecha_boletin:
            fecha_boletin = date.today().isoformat()
    else:
        boletines = listar_boletines_json()
        if not boletines:
            salida("error", "No se pudo extraer información de la API de Río Negro.")
        
        candidatos = [b for b in boletines if b['fecha_iso'] == fecha_boletin] if fecha_boletin else boletines
        
        if not candidatos:
            salida("warning", f"No se encontró boletín para la fecha solicitada.")
            
        tarjeta = next((t for t in candidatos if t['es_suplemento'] == args.suplemento), candidatos[0])
        
        fecha_boletin = tarjeta['fecha_iso']
        url_pdf = tarjeta['url']
        
        tipo_str = "SUPLEMENTO" if tarjeta['es_suplemento'] else "NORMAL"
        print(f"Descargando Edición {tarjeta['numero']} ({tipo_str}) del {fecha_boletin} ({url_pdf})...", file=sys.stderr)
        
        contenido = descargar(url_pdf, timeout=120, esperar_pdf=True)
        if not contenido:
            salida("error", f"No se pudo descargar el archivo PDF: {url_pdf}")
            
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.write(contenido)
        tmp.close()
        ruta_pdf = ruta_temporal = tmp.name

    anio_boletin = int(fecha_boletin[:4])

    try:
        cuerpo_completo = leer_paginas(ruta_pdf)
        normas = extraer_normas(cuerpo_completo, fecha_boletin, anio_boletin)
    except Exception as e:
        salida("error", f"No se pudo parsear el boletín: {e}")
    finally:
        if ruta_temporal:
            try:
                os.unlink(ruta_temporal)
            except Exception:
                pass
                
    if args.volcar:
        for n in normas:
            print(f"  {n['tipo']:12s} {n['numero']:>8s}/{n['anio']} {len(n['texto_completo']):6d} car. | {n['emisor'][:35]:35s} | {n['sintesis'][:50]}", file=sys.stderr)
        salida("success", f"volcado: {len(normas)} normas extraídas.")

    for n in normas:
        n['es_individual'], n['puntaje'], n['motivos'] = clasificar_norma(
            n['tipo'], n['sintesis'], n['texto_completo'])

    generales = [n for n in normas if not n['es_individual']]
    individuales = [n for n in normas if n['es_individual']]
    a_enviar = normas if args.sin_filtro else generales

    guardar_debug(json.dumps(normas, ensure_ascii=False, indent=2, default=str), 'debug_rionegro.json')
    print(f"Boletín del {fecha_boletin} | normas: {len(normas)} (generales {len(generales)} / individuales {len(individuales)})", file=sys.stderr)

    if args.dry_run:
        for n in (normas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {n['tipo']:12s} N° {n['numero']:>8s}/{n['anio']} {n['emisor'][:35]:35s} {n['sintesis'][:55]}", file=sys.stderr)
            if args.todas and n.get('motivos'):
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    if fecha_boletin and verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

    if not normas:
        if fecha_boletin:
            registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Sin novedades: el boletín del {fecha_boletin} no publicó Leyes, Decretos o Resoluciones de interés.", total=0)

    if not a_enviar:
        if fecha_boletin:
            registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Se procesó el boletín del {fecha_boletin}, pero todas las normas encontradas son individuales.", total=0)

    payload = [{
        "id_jurisdiccion": args.id_jurisdiccion,
        "nombre_emisor": n['emisor'],
        "tipo_norma_desc": n["tipo"],
        "numero": n["numero"],
        "anio": n["anio"],
        "fecha_publicacion": n.get("fecha_publicacion", fecha_boletin),
        "sintesis": construir_sintesis(n),
        "texto_completo": recortar_texto(n["texto_completo"]),
        "url_norma": url_norma(url_pdf, n),
    } for n in a_enviar]

    try:
        r = requests.post(URL_GUARDAR_NORMAS, json={"normas": payload},
                          headers={"Authorization": f"Bearer {API_KEY_BACKEND}",
                                   "Content-Type": "application/json"}, timeout=120)
        r.raise_for_status()
        respuesta = r.json()
    except Exception as e:
        salida("error", f"Error enviando al backend: {e}")

    if fecha_boletin:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, len(payload))

    salida("success", respuesta.get('mensaje', 'OK') or 'OK', total=len(payload))

if __name__ == '__main__':
    try:
        _main()
    except SystemExit:
        raise
    except Exception as e:
        salida("error", str(e))