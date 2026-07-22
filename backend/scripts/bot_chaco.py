"""
bot_chaco.py
===============================================================================
Scraper del Boletín Oficial Electrónico de la Provincia del Chaco.

Uso normal:
    python bot_chaco.py 5 "https://boletin.chaco.gob.ar/"

Modos de prueba (no tocan el backend):
    python bot_chaco.py 5 "..." --dry-run
    python bot_chaco.py 5 "..." --dry-run --pdf 26-06-26-11404.pdf
    python bot_chaco.py 5 "..." --dry-run --todas
    python bot_chaco.py 5 "..." --dry-run --no-ocr

-------------------------------------------------------------------------------
DESCUBRIMIENTO
-------------------------------------------------------------------------------
A diferencia de Catamarca (SPA), Chaco sirve la grilla de boletines como HTML
plano desde el servidor, así que se lee directo con BeautifulSoup: es una tabla
ordenada del más nuevo al más viejo, con el número, la fecha y el link al PDF en
cada fila. Se toma la primera fila.

-------------------------------------------------------------------------------
EXTRACCIÓN
-------------------------------------------------------------------------------
Toda la lógica de parseo vive en bo_chaco_parser.py (ver ahí el detalle de
secciones, emisores, separación de normas y OCR degradable de anexos-imagen).
Este archivo se ocupa del descubrimiento, la descarga, el filtrado final y el
envío al backend, con el mismo esqueleto que bot_catamarca.py / bot_cordoba.py.

Nota OCR: el OCR de los anexos-imagen (Decretos del PE, Res. Generales de ATP)
requiere Tesseract + poppler, que son binarios del sistema. Si el entorno no los
tiene (p. ej. hosting compartido), el bot NO falla: procesa el texto nativo y
reporta en el mensaje final qué anexos quedaron pendientes de carga manual.
===============================================================================
"""

import os
import re
import io
import sys
import json
import time
import argparse
import tempfile
import requests
from bs4 import BeautifulSoup

# En Windows la consola usa cp1252 por defecto y los print con acentos o '°'
# lanzan UnicodeEncodeError. Forzamos UTF-8 en ambos flujos. El JSON de salida
# ya es ASCII puro (json.dumps escapa), así que esto sólo protege los mensajes
# de diagnóstico a stderr.
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import bo_chaco_parser as parser


# ===========================================================================
# CONFIGURACIÓN (idéntico patrón a los otros bots)
# ===========================================================================
def get_env_clean(key, default=None):
    value = os.getenv(key, default)
    if value:
        value = value.strip().strip('"').strip("'")
    return value


API_KEY_BACKEND = get_env_clean('API_KEY_BACKEND', 'Token_Seguro_Scraper_2026_XyZ!')
URL_HISTORIAL = get_env_clean(
    'URL_HISTORIAL', 'http://localhost/lgc_sgmlo/backend/api/boletin/historial_scraping.php')
URL_GUARDAR_NORMAS = get_env_clean(
    'URL_GUARDAR_NORMAS', 'http://localhost/lgc_sgmlo/backend/api/boletin/ingresar_scraping.php')

HEADERS_WEB = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
}
HEADERS_PDF = dict(HEADERS_WEB, **{'Accept': 'application/pdf,*/*'})

REINTENTOS = 3
ESPERA_REINTENTO = 4

MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700


# ===========================================================================
# AUXILIARES DE BACKEND (idénticos a los otros bots)
# ===========================================================================
def salida(status, message, total=None, extra=None):
    out = {"status": status, "message": message}
    if total is not None:
        out["total_enviadas"] = total
    if extra:
        out.update(extra)
    print(json.dumps(out))
    sys.exit(0)


def verificar_boletin_procesado(id_jurisdiccion, fecha_boletin):
    try:
        payload = {"id_jurisdiccion": id_jurisdiccion, "fecha_boletin": fecha_boletin,
                   "accion": "verificar"}
        headers = {"Authorization": f"Bearer {API_KEY_BACKEND}"}
        res = requests.post(URL_HISTORIAL, json=payload, headers=headers, timeout=10)
        return res.json().get('procesado', False)
    except Exception:
        return False


def registrar_boletin_procesado(id_jurisdiccion, fecha_boletin, cantidad):
    try:
        payload = {"id_jurisdiccion": id_jurisdiccion, "fecha_boletin": fecha_boletin,
                   "accion": "registrar", "cantidad_normas": cantidad}
        headers = {"Authorization": f"Bearer {API_KEY_BACKEND}"}
        requests.post(URL_HISTORIAL, json=payload, headers=headers, timeout=10)
    except Exception:
        pass


def guardar_debug(contenido, nombre):
    try:
        with open(nombre, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"Guardado {nombre} para depuración", file=sys.stderr)
    except Exception as e:
        print(f"No se pudo guardar {nombre}: {e}", file=sys.stderr)


# ===========================================================================
# CAPA DE RED
# ===========================================================================
_SESION = None


def obtener_sesion():
    global _SESION
    if _SESION is None:
        _SESION = requests.Session()
        _SESION.headers.update(HEADERS_WEB)
    return _SESION


def get_con_reintentos(url, headers=None, timeout=45):
    sesion = obtener_sesion()
    ultimo = None
    for intento in range(1, REINTENTOS + 1):
        try:
            resp = sesion.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            ultimo = RuntimeError(f"HTTP {resp.status_code} en {url}")
            if resp.status_code not in (403, 408, 429) and resp.status_code < 500:
                break
        except requests.RequestException as e:
            ultimo = RuntimeError(f"Error de red en {url}: {e}")
        if intento < REINTENTOS:
            print(f"AVISO: intento {intento}/{REINTENTOS} falló; reintento…", file=sys.stderr)
            time.sleep(ESPERA_REINTENTO * intento)
    raise ultimo


# ===========================================================================
# DESCUBRIMIENTO DEL BOLETÍN MÁS RECIENTE (grilla HTML)
# ===========================================================================
MESES_INV = {1: '01', 2: '02', 3: '03', 4: '04', 5: '05', 6: '06',
             7: '07', 8: '08', 9: '09', 10: '10', 11: '11', 12: '12'}


def _fecha_grilla_a_iso(txt):
    """'17/7/2026' -> '2026-07-17'."""
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', (txt or '').strip())
    if not m:
        return None
    return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"


def obtener_boletin_mas_reciente(url_portada):
    """
    Devuelve (url_pdf, fecha_iso, numero) de la primera fila de la grilla.
    La grilla viene ordenada del más nuevo al más viejo.
    """
    try:
        resp = get_con_reintentos(url_portada, timeout=45)
    except Exception as e:
        raise RuntimeError(f"No se pudo abrir la portada del boletín: {e}")

    guardar_debug(resp.text, 'debug_chaco_portada.html')
    soup = BeautifulSoup(resp.text, 'html.parser')

    filas = soup.select('tbody tr')
    if not filas:
        # fallback: cualquier fila con un link a .pdf
        filas = [tr for tr in soup.select('tr') if tr.select_one('a[href$=".pdf"]')]
    if not filas:
        raise RuntimeError("No se encontraron filas de boletines en la grilla. "
                           "Revisar debug_chaco_portada.html.")

    for fila in filas:
        link = (fila.select_one('a.boletin_descarga')
                or fila.select_one('a[href$=".pdf"]'))
        if not link or not link.get('href'):
            continue
        url_pdf = link['href'].strip()
        if not url_pdf.startswith('http'):
            base = re.match(r'(https?://[^/]+)', url_portada)
            url_pdf = (base.group(1) if base else '') + \
                      ('' if url_pdf.startswith('/') else '/') + url_pdf

        celda_nro = fila.select_one('td[data-label*="Nro"], td[data-label*="Boletín"], td[data-label*="Boletin"]')
        celda_fecha = fila.select_one('td[data-label*="Fecha"]')
        numero = celda_nro.get_text(strip=True) if celda_nro else None
        # respaldo: número embebido en el nombre del PDF (…-11412-…)
        if not numero:
            m = re.search(r'-(\d{4,6})-', url_pdf)
            numero = m.group(1) if m else None
        fecha_iso = _fecha_grilla_a_iso(celda_fecha.get_text(strip=True)) if celda_fecha else None
        if not fecha_iso:
            m = re.search(r'/(\d{2})-(\d{2})-(\d{2})-', url_pdf)  # dd-mm-yy en el nombre
            if m:
                fecha_iso = f"20{m.group(3)}-{m.group(2)}-{m.group(1)}"

        return url_pdf, fecha_iso, numero

    raise RuntimeError("Ninguna fila de la grilla tenía un enlace a PDF.")


# ===========================================================================
# ARMADO DE NORMAS PARA EL BACKEND
# ===========================================================================
# Encabezado crudo con que arrancan los decretos OCR-eados:
#   "Número:DEC-2026-1424-APP-CHACO RESISTENCIA, CHACO Viernes 19 de Junio de 2026
#    Referencia: RATIFICA CONTRATO VISTO: ..."
# Para la síntesis no aporta (esos datos ya van en tipo/numero/fecha), así que se
# recorta y se arranca por el VISTO, que es donde empieza el contenido real.
RE_ENCABEZADO_OCR = re.compile(
    r'^\s*N[úu]mero:\s*(?:DEC|RES)-[\dA-Z\-]+.*?(?:Referencia:\s*.*?)?(?=VISTO)',
    re.IGNORECASE | re.DOTALL)


def _construir_sintesis(texto, tipo, numero, referencia=None):
    """
    Arma la síntesis que se muestra en la interfaz.

    Para los decretos que vienen por OCR se antepone el campo 'Referencia' (que
    resume el acto en pocas palabras: "RATIFICA CONTRATO", "ADJUDICA LICITACIÓN
    PÚBLICA") y se quita el encabezado crudo del OCR, que es metadato ilegible.
    """
    cuerpo = texto or ''
    recortado = RE_ENCABEZADO_OCR.sub('', cuerpo, count=1)
    # sólo aceptar el recorte si dejó contenido con sustancia
    if len(recortado.strip()) > 80:
        cuerpo = recortado
    cuerpo = cuerpo.strip(' .-:')

    if referencia:
        ref = referencia.strip(' .-:')
        # evitar duplicar la referencia si el cuerpo ya arranca con ella
        if ref and not cuerpo.upper().startswith(ref.upper()[:20]):
            cuerpo = f"{ref} — {cuerpo}" if cuerpo else ref

    if len(cuerpo) > MAX_SINTESIS:
        cuerpo = cuerpo[:MAX_SINTESIS].rsplit(' ', 1)[0] + '…'
    return cuerpo or f"{tipo} {numero}"


def url_norma(url_pdf, tipo, numero):
    """
    Chaco no tiene URL individual por norma (todas viven en el mismo PDF), así
    que se manda la URL del PDF + un fragmento único por norma. Es necesario
    porque ingresar_scraping.php deduplica también por url_norma exacta: sin el
    fragmento, en cuanto una norma quedara guardada bloquearía a las demás.
    """
    slug = re.sub(r'[^A-Za-z0-9]+', '-', f"{tipo}-{numero}").strip('-')
    return f"{url_pdf}#{slug}"


# ===========================================================================
# EJECUCIÓN
# ===========================================================================
def _main():
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Chaco.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', default='https://boletin.chaco.gob.ar/')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--pdf', metavar='ARCHIVO', help='usar un PDF local (para pruebas)')
    ap.add_argument('--todas', action='store_true', help='en dry-run, mostrar individuales')
    ap.add_argument('--no-ocr', action='store_true', help='no intentar OCR de anexos-imagen')
    args = ap.parse_args()

    # 1. Ubicar el PDF
    if args.pdf:
        ruta_local = args.pdf
        url_pdf = args.pdf
        fecha_boletin = None
        numero_boletin = None
        print(f"Usando PDF local: {args.pdf}", file=sys.stderr)
    else:
        try:
            url_pdf, fecha_boletin, numero_boletin = obtener_boletin_mas_reciente(args.url_boletin)
        except RuntimeError as e:
            salida("error", str(e))
        print(f"Boletín N° {numero_boletin or '?'} del {fecha_boletin or '?'}", file=sys.stderr)
        print(f"PDF: {url_pdf}", file=sys.stderr)

        if not args.dry_run and fecha_boletin:
            if verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
                salida("info", f"Boletín del {fecha_boletin} ya fue procesado")

        # descargar a archivo temporal (el OCR necesita una ruta en disco)
        try:
            resp = get_con_reintentos(url_pdf, headers=HEADERS_PDF, timeout=120)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            tmp.write(resp.content)
            tmp.close()
            ruta_local = tmp.name
        except Exception as e:
            salida("error", f"No se pudo descargar el PDF: {e}")

    # 2. Parsear (con OCR degradable)
    try:
        resultado = parser.parsear_normas(ruta_local, usar_ocr=not args.no_ocr)
    except Exception as e:
        salida("error", f"No se pudo parsear el PDF: {e}")

    todas = resultado['normas']
    generales = [n for n in todas if not n['es_individual']]
    individuales = [n for n in todas if n['es_individual']]
    pendientes = resultado['anexos_pendientes']

    # aviso de OCR no disponible cuando había anexos con normativa
    nota_ocr = ""
    if pendientes:
        detalle = "; ".join(f"{a['anexo']} ({a['contenido'][:60]})" for a in pendientes)
        nota_ocr = (f" Quedaron {len(pendientes)} anexo(s) en imagen sin procesar por "
                    f"falta de OCR, para carga manual: {detalle}.")

    guardar_debug(
        json.dumps(todas, ensure_ascii=False, indent=2, default=str),
        'debug_chaco.json')

    if not todas and not pendientes:
        salida("warning", "No se encontraron normas en la sección oficial del PDF.")

    print(f"Normas: {len(todas)} (generales {len(generales)} / individuales {len(individuales)}) "
          f"| OCR usado: {resultado['ocr_usado']} | anexos pendientes: {len(pendientes)}",
          file=sys.stderr)

    # 3. Modo prueba
    if args.dry_run:
        for n in (todas if args.todas else generales):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}/{n['origen'].upper()}] {n['tipo']:18s} N° {str(n['numero']):12s} "
                  f"{str(n['fecha_publicacion'] or '-'):11s} {str(n['emisor'] or '-')[:40]:40s} "
                  f"{len(n['texto_completo']):5d} car.", file=sys.stderr)
        if pendientes:
            print("\nAnexos-imagen pendientes (carga manual):", file=sys.stderr)
            for a in pendientes:
                print(f"   - {a['anexo']}: {a['contenido']}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend." + nota_ocr,
               total=len(generales))

    if not generales:
        salida("warning",
               f"Las {len(individuales)} normas del boletín son actos individuales; "
               f"no se envió ninguna." + nota_ocr)

    # 4. Payload y envío
    normas_completas = [{
        "id_jurisdiccion": args.id_jurisdiccion,
        "nombre_emisor": n["emisor"] or "PODER EJECUTIVO",
        "tipo_norma_desc": n["tipo"],
        "numero": n["numero"],
        "anio": n["anio"],
        "fecha_publicacion": n["fecha_publicacion"],
        "sintesis": _construir_sintesis(n["texto_completo"], n["tipo"], n["numero"],
                                        n.get("referencia")),
        "texto_completo": n["texto_completo"][:MAX_TEXTO_COMPLETO],
        "url_norma": url_norma(url_pdf, n["tipo"], n["numero"]),
    } for n in generales]

    try:
        headers_post = {"Authorization": f"Bearer {API_KEY_BACKEND}",
                        "Content-Type": "application/json"}
        res = requests.post(URL_GUARDAR_NORMAS, json={"normas": normas_completas},
                            headers=headers_post, timeout=120)
        res.raise_for_status()
        respuesta = res.json()
    except Exception as e:
        salida("error", f"Error enviando al backend: {e}")

    if fecha_boletin:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, len(normas_completas))

    salida("success", (respuesta.get('mensaje', 'OK') or 'OK') + nota_ocr,
           total=len(normas_completas))


if __name__ == '__main__':
    try:
        _main()
    except SystemExit:
        raise
    except Exception as e:
        salida("error", str(e))