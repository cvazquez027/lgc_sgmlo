"""
bo_chaco_parser.py
===============================================================================
Parser del Boletín Oficial Electrónico de la Provincia del Chaco.

Es la MITAD OFFLINE del bot: toma un PDF de boletín y devuelve las normas de la
sección "LEGISLACION-NORMATIVA-COMUNICACIONES OFICIALES", clasificadas entre
actos de alcance general e individuales. No toca red ni backend, así que se
prueba directo contra un PDF descargado:

    python bo_chaco_parser.py 26-06-26-11404.pdf
    python bo_chaco_parser.py 26-06-26-11404.pdf --todas
    python bo_chaco_parser.py 26-06-26-11404.pdf --no-ocr

-------------------------------------------------------------------------------
ESTRUCTURA DEL BOLETÍN DE CHACO
-------------------------------------------------------------------------------
El PDF es de UNA columna y se divide en secciones con título centrado en negrita
grande (~14pt): "LEGISLACION-NORMATIVA-COMUNICACIONES OFICIALES", "JUDICIALES".
Sólo nos interesa la primera; se corta al llegar a "JUDICIALES".

Dentro de la sección oficial, las normas se agrupan por EMISOR (encabezado
centrado en negrita: "LA CAMARA DE DIPUTADOS DE LA PROVINCIA DEL CHACO",
"TRIBUNAL DE CUENTAS", "MINISTERIO DE HACIENDA Y FINANZAS", etc.) y se separan
entre sí con una línea "–––– >*< ––––".

Hay TRES tipos de contenido según cómo está incrustado:

  1. Texto nativo (primeras páginas): leyes, resoluciones del Tribunal de
     Cuentas, declaraciones. Se extrae con pdfplumber.

  2. Anexos anunciados como imagen: el cuerpo dice "Con la presente Edición en
     Formato de Imagen ANEXO III conteniendo DECRETOS DEL PODER EJECUTIVO..." y
     después vienen páginas escaneadas. Ahí suelen estar las normas más
     importantes (Decretos del PE, Resoluciones Generales de ATP). Como son
     imágenes, pdfplumber devuelve ~50 caracteres por página (sólo el
     encabezado/pie repetido); hay que pasarles OCR.

  3. Tablas/listados escaneados que NO son normativa (p. ej. listado de jurados
     indígenas). Se ignoran.

-------------------------------------------------------------------------------
OCR DEGRADABLE
-------------------------------------------------------------------------------
El OCR usa Tesseract (binario del sistema) + pdftoppm (poppler). No son
librerías pip; en un hosting compartido normalmente NO se pueden instalar. Por
eso el OCR es OPCIONAL: si las herramientas están, se procesan los anexos-imagen
que anuncian normativa; si no, el parser sigue con el texto nativo y DEJA
CONSTANCIA de qué anexos quedaron pendientes (campo `anexos_pendientes`), para
cargarlos a mano. Nunca aborta por falta de OCR.
===============================================================================
"""

import os
import re
import sys
import shutil
import tempfile
import subprocess
import time

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


# ===========================================================================
# CONSTANTES DE MAQUETA
# ===========================================================================
SECCION_OBJETIVO = 'LEGISLACION-NORMATIVA-COMUNICACIONES OFICIALES'
SECCIONES_CORTE = ('JUDICIALES',)   # dónde termina la sección oficial

TAM_TITULO_SECCION = 13     # el título de sección va en ~14pt
CENTRO_MIN, CENTRO_MAX = 240, 355   # una línea "centrada" cae en esta franja de X
UMBRAL_TEXTO_NATIVO = 120   # menos que esto (sacando furniture) => página imagen

# Encabezado y pie que se repiten en cada página
RE_ENCABEZADO = re.compile(
    r'^(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4}.*EDICION',
    re.IGNORECASE)
RE_PIE = re.compile(r'Oficina Central.*chaco\.gov\.ar', re.IGNORECASE)
RE_NRO_PAGINA = re.compile(r'^-\s*\d+\s*-$')
RE_SEPARADOR = re.compile(r'>\s*\*\s*<')

# Furniture de la cabecera institucional (no es emisor ni norma)
FURNITURE = {
    'PROVINCIA DEL CHACO', 'SECRETARIA GENERAL DE LA GOBERNACION',
    'BOLETÍN OFICIAL ELECTRÓNICO', 'BOLETIN OFICIAL ELECTRONICO',
}
RE_FURNITURE_PREFIJO = re.compile(
    r'^(SUBSECRETARIA DE LEGAL|DIRECCION BOLETIN|Subsecretario:|Director:|s/c\b|E:\d)', re.IGNORECASE)


# ===========================================================================
# ENCABEZADOS DE NORMA
# ===========================================================================
# Leyes: "SANCIONA CON FUERZA DE LEY NRO. 4232-A"
PATRON_LEY = re.compile(r'SANCIONA CON FUERZA DE LEY\s+NRO\.?\s*([\dA-Z\-]+)', re.IGNORECASE)
# Resoluciones del cuerpo: "RESOLUCIÓN Nº 220/25 - ACUERDO SALA I ..."
PATRON_RESOLUCION = re.compile(r'^RESOLUCI[ÓO]N\s+N[º°]\s*([\d]+/[\d]+)', re.IGNORECASE)
# Declaraciones: "DECLARACIÓN Nº 067/2026"
PATRON_DECLARACION = re.compile(r'^DECLARACI[ÓO]N\s+N[º°]\s*([\d]+/[\d]+)', re.IGNORECASE)
# Actas: "ACTA Nº 1 de fecha 22/06/2026" (se exige fecha para no confundir con
# menciones sueltas dentro de un anuncio de anexo)
PATRON_ACTA = re.compile(r'^ACTA\s+N[º°]\s*([\d]+)\s+de\s+fecha', re.IGNORECASE)
# Decretos (vienen por OCR de anexos): "Número:DEC-2026-1421-APP-CHACO"
PATRON_DECRETO = re.compile(r'DEC-(\d{4})-(\d+)-[A-Z\-]+', re.IGNORECASE)
# Resoluciones generales de anexos: "Número:RES-2026-15-20-1"
PATRON_RES_GRAL = re.compile(r'RES-(\d{4})-([\d\-]+)', re.IGNORECASE)

# Anuncios de anexo-imagen con normativa
PATRON_ANEXO = re.compile(
    r'(?:Con la presente Edici[óo]n en Formato de Imagen|CON LA PRESENTE EDICION EN FORMATO DE IMAGEN)'
    r'\s+(ANEXO\s+[IVX]+)\s+(?:conteniendo|CONTENIENDO)\s+(.{0,120})',
    re.IGNORECASE | re.DOTALL)
# Un anexo trae normativa si su descripción menciona esto:
RE_ANEXO_NORMATIVO = re.compile(r'DECRETO|RESOLUCI[ÓO]N', re.IGNORECASE)

MESES = {'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
         'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
         'septiembre': '09', 'setiembre': '09', 'octubre': '10',
         'noviembre': '11', 'diciembre': '12'}


# ===========================================================================
# CLASIFICACIÓN: ACTO GENERAL vs INDIVIDUAL
# ---------------------------------------------------------------------------
# Igual criterio que Catamarca: el boletín mezcla normativa general con actos
# que afectan a una persona determinada (multas y rendiciones del Tribunal de
# Cuentas contra agentes nombrados, designaciones/bajas de funcionarios, retiros
# voluntarios). Esos no son normativa de interés y arrastran datos personales.
# Puntaje: individual si llega al umbral. Un DNI solo NO decide (pesa +1).
# ===========================================================================
UMBRAL_INDIVIDUAL = 2

PATRONES_INDIVIDUALES = [
    (r'BAJA DE AUTORIDAD',                                    3, 'baja de autoridad'),
    (r'DESIGNACI[ÓO]N DE AUTORIDADES',                        3, 'designación de autoridad'),
    (r'Dej[ae]se sin efecto[\s\S]{0,60}designaci[óo]n',       3, 'cese de designación'),
    (r'Design[ae]se[\s\S]{0,40}en el cargo',                  3, 'designación'),
    (r'RETIRO VOLUNTARIO',                                    3, 'retiro voluntario'),
    (r'Impone\s+(?:multa|sanci[óo]n)',                        3, 'multa individual'),
    (r'aplica(?:r|se)?\s+(?:una\s+)?multa',                   3, 'multa individual'),
    (r'formul[ao]\s+cargo',                                   2, 'cargo pecuniario'),
    (r'RENDICION DE CUENTAS[\s\S]{0,80}(?:Sr\.|Sra\.|agente|D\.N\.I|DNI)', 2, 'rendición nominada'),
    (r'NOTIFICA al\s+(?:Sr\.|Sra\.)',                         3, 'notificación individual'),
    (r'Lib[eé]r[ae]\s+de\s+responsabilidad',                  2, 'liberación individual'),
]

PATRONES_GENERALES = [
    (r'SANCIONA CON FUERZA DE LEY',                          -6, 'ley provincial'),
    (r'Instit[úu]yese',                                       -3, 'institúyese (general)'),
    (r'Declárase de utilidad pública',                        -4, 'expropiación por ley'),
    (r'Sustituir los ANEXOS',                                 -3, 'modifica anexos normativos'),
    (r'Ratif[íi]case el Contrato',                            -3, 'ratifica contrato'),
    (r'DE INTER[ÉE]S (?:MUNICIPAL|PROVINCIAL|GENERAL)',       -3, 'declaración de interés'),
    (r'ADHERIR a',                                            -2, 'adhesión'),
    (r'comenzar[áa] a regir a partir',                        -2, 'vigencia general'),
]

RE_DOCUMENTO = re.compile(r'\b(?:DNI|D\.N\.I|CUIL|CUIT)\b', re.IGNORECASE)

# Emisores cuya producción es, por su naturaleza, acto administrativo interno y
# no normativa de interés general. El Tribunal de Cuentas publica casi
# exclusivamente rendiciones de cuentas y multas nominadas; se marcan todas como
# individuales por emisor.
EMISORES_SIEMPRE_INDIVIDUAL = re.compile(r'TRIBUNAL DE CUENTAS', re.IGNORECASE)

# Los decretos del PE traen un campo "Referencia:" que resume el acto y que el
# OCR lee limpio. Es la señal MÁS confiable para clasificar (mucho mejor que
# buscar palabras en el cuerpo, que viene con ruido de OCR). Si la referencia
# encaja acá, es acto individual sí o sí.
REFERENCIAS_INDIVIDUALES = re.compile(
    r'BAJA DE AUTORIDAD|DESIGNACI[ÓO]N DE AUTORIDAD|RETIRO VOLUNTARIO|SUBROGANCIA|'
    r'CESANT[ÍI]A|PROMOCI[ÓO]N DEL PERSONAL|LICENCIA|RENUNCIA|'
    r'PASE A (?:RETIRO|DISPONIBILIDAD)|RECONOCIMIENTO DE SERVICIOS',
    re.IGNORECASE)


def clasificar_norma(texto, emisor=None, referencia=None):
    """Devuelve (es_individual, puntaje, motivos)."""
    if emisor and EMISORES_SIEMPRE_INDIVIDUAL.search(emisor):
        return True, UMBRAL_INDIVIDUAL, ['emisor de actos internos (Tribunal de Cuentas)']
    # La Referencia del decreto manda si es concluyente.
    if referencia and REFERENCIAS_INDIVIDUALES.search(referencia):
        return True, UMBRAL_INDIVIDUAL, [f'referencia individual: {referencia[:40]}']
    puntaje = 0
    motivos = []
    for patron, peso, etiqueta in PATRONES_INDIVIDUALES:
        if re.search(patron, texto, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'+{peso} {etiqueta}')
    for patron, peso, etiqueta in PATRONES_GENERALES:
        if re.search(patron, texto, re.IGNORECASE):
            puntaje += peso
            motivos.append(f'{peso} {etiqueta}')
    docs = len(RE_DOCUMENTO.findall(texto))
    if docs:
        puntaje += 1
        motivos.append(f'+1 menciona DNI/CUIL ({docs})')
    return (puntaje >= UMBRAL_INDIVIDUAL), puntaje, motivos


# ===========================================================================
# DISPONIBILIDAD DE OCR
# ===========================================================================
def ocr_disponible():
    """True si están Tesseract y pdftoppm. No lanza: sólo informa."""
    return bool(shutil.which('tesseract') and shutil.which('pdftoppm'))


def _ocr_paginas(ruta_pdf, paginas_1based, idioma='spa'):
    """Compatibilidad: OCR simple de una lista de páginas (sin optimización)."""
    return _ocr_lista(ruta_pdf, paginas_1based, idioma=idioma)


def _correr(cmd, timeout, env=None):
    """
    Ejecuta un comando matándolo de verdad si vence el timeout.

    En Windows dos cosas conspiran: (1) capture_output usa hilos lectores que se
    cuelgan leyendo el stdout de un proceso trabado, por eso mandamos stdout y
    stderr a DEVNULL; (2) Popen.kill() mata sólo el proceso lanzado, pero
    Tesseract puede dejar subprocesos vivos, así que en Windows matamos el ÁRBOL
    completo con taskkill /T. Si aun así no muere, hay un segundo intento.
    """
    creationflags = 0
    if os.name == 'nt':
        # CREATE_NEW_PROCESS_GROUP permite señalizar el grupo entero.
        creationflags = getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=creationflags, env=env)
    try:
        p.communicate(timeout=timeout)
        return p.returncode == 0
    except subprocess.TimeoutExpired:
        _matar_arbol(p)
        raise


def _matar_arbol(p):
    """Mata el proceso y todos sus hijos, de forma robusta en Windows y Unix."""
    try:
        if os.name == 'nt':
            # taskkill /T mata el árbol; /F fuerza. Silencioso.
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(p.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=15)
        else:
            p.kill()
    except Exception:
        try:
            p.kill()
        except Exception:
            pass
    try:
        p.communicate(timeout=10)
    except Exception:
        pass


def _buscar_png(tmp, prefijo_base):
    """Encuentra el PNG que pdftoppm generó a partir de un prefijo dado.
    pdftoppm agrega '-NN' (número de página) al prefijo, p.ej. 'top11' -> 'top11-11.png'."""
    cands = [f for f in os.listdir(tmp)
             if f.startswith(prefijo_base) and f.endswith('.png')]
    return os.path.join(tmp, cands[0]) if cands else None


# Límite del lado mayor del PNG renderizado. pdftoppm -scale-to garantiza que la
# imagen nunca sea gigantesca, sin necesidad de que PIL la cargue para
# reescalarla (cargar un PNG enorme con PIL fue lo que colgó la página 68).
LADO_MAX = 2200


def _render_png(ruta_pdf, nro, tmp, dpi, timeout):
    """
    Renderiza una página a PNG con el lado mayor acotado a LADO_MAX píxeles.
    Usa -scale-to de pdftoppm en vez de -r: así el propio pdftoppm limita el
    tamaño y nunca genera un PNG monstruoso, evitando que cualquier carga
    posterior con PIL se cuelgue.
    """
    prefijo_base = f'full{nro}'
    prefijo = os.path.join(tmp, prefijo_base)
    ok = _correr(['pdftoppm', '-f', str(nro), '-l', str(nro),
                  '-scale-to', str(LADO_MAX), '-png', ruta_pdf, prefijo],
                 timeout=timeout)
    if not ok:
        return None
    return _buscar_png(tmp, prefijo_base)


def _render_franja_superior(ruta_pdf, nro, tmp, timeout):
    """
    Renderiza SÓLO la franja superior de la página, directamente con pdftoppm
    (-x -y -W -H recortan en píxeles sobre la imagen escalada). Evita cargar la
    página completa en PIL para recortarla, que es lo que se colgaba.

    Se renderiza la página a un tamaño chico (LADO_MAX) y se recorta la banda
    superior (~22%). Como pdftoppm hace el recorte al vuelo, el PNG resultante
    es diminuto y Tesseract lo procesa en un instante.
    """
    prefijo_base = f'top{nro}'
    prefijo = os.path.join(tmp, prefijo_base)
    # 48% superior: el 'Número:DEC-' viene después del membrete de fecha/edición
    # que encabeza cada página, así que una franja chica no lo alcanza.
    alto_franja = int(LADO_MAX * 0.48)
    ok = _correr(['pdftoppm', '-f', str(nro), '-l', str(nro),
                  '-scale-to', str(LADO_MAX),
                  '-x', '0', '-y', '0', '-W', str(LADO_MAX), '-H', str(alto_franja),
                  '-png', ruta_pdf, prefijo], timeout=timeout)
    if not ok:
        return None
    return _buscar_png(tmp, prefijo_base)


def _ocr_imagen(entrada, tmp, nro, idioma, timeout, psm='6'):
    """OCR de un PNG ya renderizado (Tesseract a archivo, no stdout-pipe)."""
    if not entrada or not os.path.exists(entrada):
        return ''
    salida_txt = os.path.join(tmp, f'ocr{nro}')
    entorno = dict(os.environ, OMP_THREAD_LIMIT='1')  # evita cuelgues por multihilo
    _correr(['tesseract', entrada, salida_txt, '-l', idioma, '--psm', psm],
            timeout=timeout, env=entorno)
    archivo = salida_txt + '.txt'
    if os.path.exists(archivo):
        with open(archivo, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    return ''


RE_MARCADOR_DECRETO = re.compile(r'N[úu]mero:\s*(?:DEC|RES)-', re.IGNORECASE)


def _ocr_lista(ruta_pdf, paginas_1based, idioma='spa', dpi=None,
               timeout_pagina=60, presupuesto_total=None):
    """OCR completo de una lista de páginas (fallback sin optimización)."""
    resultado = {}
    if not paginas_1based:
        return resultado
    dpi = dpi or int(os.getenv('CHACO_OCR_DPI', '200'))
    tmp = tempfile.mkdtemp(prefix='chaco_ocr_')
    inicio = time.time()
    try:
        for i, nro in enumerate(paginas_1based, 1):
            if presupuesto_total and (time.time() - inicio) > presupuesto_total:
                print(f"AVISO: OCR alcanzó el presupuesto de {presupuesto_total}s; "
                      f"quedan {len(paginas_1based) - i + 1} página(s) sin procesar.",
                      file=sys.stderr)
                break
            try:
                print(f"OCR: página {nro} ({i}/{len(paginas_1based)})…", file=sys.stderr)
                png = _render_png(ruta_pdf, nro, tmp, dpi, timeout_pagina)
                if png:
                    resultado[nro] = _ocr_imagen(png, tmp, nro, idioma, timeout_pagina)
            except subprocess.TimeoutExpired:
                print(f"AVISO: OCR de la página {nro} excedió {timeout_pagina}s; se saltea.",
                      file=sys.stderr)
            except Exception as e:
                print(f"AVISO: OCR falló en página {nro}: {e}", file=sys.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return resultado


def _ocr_secuencial(ruta_pdf, paginas_1based, idioma='spa', dpi=None,
                    timeout_pagina=60, presupuesto_total=None):
    """
    OCR secuencial de las páginas-imagen, de corrido.

    Es la versión simple y robusta: OCR-ea las páginas de anexo una tras otra,
    en orden, hasta terminarlas todas o agotar el presupuesto de tiempo. Sin
    mapeos previos ni saltos: eso se probó y resultó más lento y frágil.

    Lo que corta el ruido no es saltar páginas acá, sino el recorte por la firma
    del Gobernador que se hace luego, en _extraer_normas_de_ocr: el cuerpo legal
    de cada decreto termina en la firma, y los anexos escaneados posteriores se
    descartan al armar la norma. Así, aunque OCR-eemos esas páginas, su ruido no
    entra en la base.

    Mejoras que sí valieron la pena y se conservan:
      - pdftoppm con -scale-to (no -r): el PNG nunca es gigantesco, lo que evita
        que PIL/OCR se cuelguen en una página escaneada a alta resolución.
      - timeout por página con kill del árbol de procesos en Windows.
      - presupuesto total configurable (CHACO_OCR_PRESUPUESTO): si se agota, se
        deja lo procesado y se sigue; nada aborta el scraper.
    """
    resultado = {}
    if not paginas_1based:
        return resultado
    timeout_pagina = int(os.getenv('CHACO_OCR_TIMEOUT_PAGINA', str(timeout_pagina)))
    tmp = tempfile.mkdtemp(prefix='chaco_ocr_')
    inicio = time.time()
    total = len(paginas_1based)
    try:
        for i, nro in enumerate(paginas_1based, 1):
            if presupuesto_total and (time.time() - inicio) > presupuesto_total:
                print(f"AVISO: OCR alcanzó el presupuesto de {presupuesto_total}s; "
                      f"quedan {total - i + 1} página(s) sin procesar "
                      f"(subí CHACO_OCR_PRESUPUESTO si querés todas).", file=sys.stderr)
                break
            try:
                print(f"OCR: página {nro} ({i}/{total})…", file=sys.stderr)
                png = _render_png(ruta_pdf, nro, tmp, dpi, timeout_pagina)
                if not png:
                    continue
                resultado[nro] = _ocr_imagen(png, tmp, nro, idioma, timeout_pagina)
            except subprocess.TimeoutExpired:
                print(f"AVISO: OCR de la página {nro} excedió el tiempo; se saltea.",
                      file=sys.stderr)
            except Exception as e:
                print(f"AVISO: OCR falló en página {nro}: {e}", file=sys.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return resultado


# ===========================================================================
# EXTRACCIÓN DE LÍNEAS CON ESTILO
# ===========================================================================
def _lineas_de_pagina(pagina):
    palabras = pagina.extract_words(extra_attrs=['fontname', 'size'])
    palabras.sort(key=lambda w: (round(w['top'] / 3), w['x0']))
    grupos, actual, top = [], [], None
    for w in palabras:
        t = round(w['top'] / 3) * 3
        if top is None or abs(t - top) <= 3:
            actual.append(w)
            top = top if top is not None else t
        else:
            grupos.append(actual)
            actual, top = [w], t
    if actual:
        grupos.append(actual)
    res = []
    for g in grupos:
        g.sort(key=lambda w: w['x0'])
        x0 = min(w['x0'] for w in g)
        x1 = max(w['x1'] for w in g)
        res.append({
            'texto': ' '.join(w['text'] for w in g),
            'bold': any('Bold' in w['fontname'] for w in g),
            'centro': (x0 + x1) / 2,
            'tam': round(max(w['size'] for w in g), 1),
        })
    return res


def _texto_real(pagina):
    """Texto de la página sin encabezado/pie repetidos (para medir si es imagen)."""
    t = pagina.extract_text() or ''
    fuera = []
    for l in t.split('\n'):
        s = l.strip()
        if not s or RE_ENCABEZADO.match(s) or RE_PIE.search(s) or RE_NRO_PAGINA.match(s):
            continue
        if s in FURNITURE or RE_FURNITURE_PREFIJO.match(s):
            continue
        fuera.append(s)
    return '\n'.join(fuera)


def _es_titulo_emisor(linea):
    t = linea['texto'].strip()
    if not (linea['bold'] and CENTRO_MIN < linea['centro'] < CENTRO_MAX):
        return False
    if not t.isupper() or len(t) < 12 or len(t) > 75:
        return False
    if re.search(r'N[º°]|NRO|EDICION|E:\d|ARTÍCULO|SANCIONA', t):
        return False
    if t in FURNITURE or t == SECCION_OBJETIVO:
        return False
    # subtítulos de contenido, no emisores (van dentro de una norma judicial)
    if re.search(r'LISTADO|CIRCUNSCRIPCI|PUEBLO QOM', t):
        return False
    return True


# ===========================================================================
# PARSEO PRINCIPAL
# ===========================================================================
def parsear_normas(ruta_pdf, usar_ocr=True):
    """
    Devuelve dict con:
      - 'normas': lista de normas de la sección oficial, clasificadas.
      - 'anexos_pendientes': anexos-imagen con normativa que no se pudieron
        procesar (OCR no disponible), para carga manual.
      - 'ocr_usado': bool.
    """
    if pdfplumber is None:
        raise RuntimeError("Falta 'pdfplumber' (pip install pdfplumber).")

    with pdfplumber.open(ruta_pdf) as pdf:
        n_pag = len(pdf.pages)

        # --- Clasificar páginas: nativa vs imagen ---
        es_imagen = {}
        texto_pag = {}
        for i, pagina in enumerate(pdf.pages):
            real = _texto_real(pagina)
            texto_pag[i] = real
            es_imagen[i] = len(real) < UMBRAL_TEXTO_NATIVO

        # --- Ubicar dónde termina la sección oficial (primera "JUDICIALES") ---
        # Se busca en las páginas nativas; la sección oficial siempre arranca al
        # inicio del boletín.
        fin_seccion_pag = n_pag
        for i in range(n_pag):
            if es_imagen[i]:
                continue
            for l in _lineas_de_pagina(pdf.pages[i]):
                if l['texto'].strip().upper() in SECCIONES_CORTE and l['tam'] >= TAM_TITULO_SECCION:
                    fin_seccion_pag = i
                    break
            if fin_seccion_pag != n_pag:
                break

        # --- Detectar anexos anunciados con normativa ---
        texto_completo_doc = '\n'.join(texto_pag[i] for i in range(n_pag))
        anexos_norm = []
        for nombre, desc in PATRON_ANEXO.findall(texto_completo_doc):
            if RE_ANEXO_NORMATIVO.search(desc):
                anexos_norm.append((nombre.strip().upper(), re.sub(r'\s+', ' ', desc).strip()))

        # --- Recolectar líneas nativas de la sección oficial ---
        lineas = []
        for i in range(min(fin_seccion_pag + 1, n_pag)):
            if es_imagen[i]:
                continue
            for l in _lineas_de_pagina(pdf.pages[i]):
                s = l['texto'].strip()
                if not s or RE_ENCABEZADO.match(s) or RE_PIE.search(s) or RE_NRO_PAGINA.match(s):
                    continue
                if s in FURNITURE or RE_FURNITURE_PREFIJO.match(s):
                    continue
                lineas.append(l)

        # Cortar en el título JUDICIALES (dentro de las líneas)
        recorte = []
        for l in lineas:
            if l['texto'].strip().upper() in SECCIONES_CORTE and l['tam'] >= TAM_TITULO_SECCION:
                break
            recorte.append(l)
        lineas = [l for l in recorte if l['texto'].strip().upper() != SECCION_OBJETIVO]

        normas = _extraer_normas_de_lineas(lineas)

        # --- OCR de anexos-imagen con normativa ---
        anexos_pendientes = []
        ocr_usado = False
        if anexos_norm:
            paginas_imagen = [i + 1 for i in range(n_pag) if es_imagen[i]]
            if usar_ocr and ocr_disponible() and paginas_imagen:
                ocr_usado = True
                presupuesto = int(os.getenv('CHACO_OCR_PRESUPUESTO', '1800'))
                # OCR optimizado: OCR-ea el cuerpo de cada decreto completo y
                # saltea los anexos escaneados posteriores a cada firma.
                textos_ocr = _ocr_secuencial(ruta_pdf, paginas_imagen,
                                             presupuesto_total=presupuesto)
                normas += _extraer_normas_de_ocr(textos_ocr)
            else:
                motivo = ('OCR deshabilitado' if not usar_ocr
                          else 'Tesseract/pdftoppm no disponibles')
                for nombre, desc in anexos_norm:
                    anexos_pendientes.append({'anexo': nombre, 'contenido': desc, 'motivo': motivo})

    return {'normas': normas, 'anexos_pendientes': anexos_pendientes, 'ocr_usado': ocr_usado}


def _extraer_normas_de_lineas(lineas):
    """Recorre las líneas nativas agrupando por emisor y separando por >*<."""
    normas = []
    emisor_actual = None
    bloque = []
    subtitulo_previo = []   # líneas centradas que preceden a la norma (título temático)

    def cerrar_bloque():
        if not bloque:
            return
        texto = _unir(bloque)
        if not texto.strip():
            return
        tipo, numero = _detectar_tipo_numero(texto, bloque)
        if tipo is None:
            return  # no es una norma (edicto, comunicación suelta)
        fecha, anio = _detectar_fecha(texto)
        es_ind, punt, mot = clasificar_norma(texto, emisor_actual)
        normas.append({
            'tipo': tipo, 'numero': numero, 'anio': anio,
            'emisor': emisor_actual, 'fecha_publicacion': fecha,
            'texto_completo': texto, 'origen': 'nativo',
            'es_individual': es_ind, 'puntaje': punt, 'motivos': mot,
        })

    for l in lineas:
        s = l['texto'].strip()
        if RE_SEPARADOR.search(s):
            cerrar_bloque()
            bloque = []
            continue
        if _es_titulo_emisor(l):
            # nuevo emisor: cierra lo que venía
            cerrar_bloque()
            bloque = []
            emisor_actual = _normalizar_emisor(s)
            continue
        # Un encabezado de norma también cierra la norma anterior: el Tribunal de
        # Cuentas encadena decenas de "RESOLUCIÓN Nº ..." sin separador >*< entre
        # ellas, así que sin esto todas se fundirían en una sola.
        if _es_encabezado_de_norma(s) and bloque:
            cerrar_bloque()
            bloque = [s]
            continue
        bloque.append(s)
    cerrar_bloque()
    return normas


def _es_encabezado_de_norma(s):
    """True si la línea abre una nueva norma (para cortar el bloque anterior)."""
    return bool(PATRON_RESOLUCION.match(s) or PATRON_DECLARACION.match(s)
                or PATRON_ACTA.match(s) or PATRON_LEY.search(s))


def _extraer_normas_de_ocr(textos_ocr):
    """
    De los textos OCR de anexos, arma normas por documento. Cada decreto/res
    empieza en 'Número:DEC-...' o 'Número:RES-...'. Los agrupa aunque se
    extiendan por varias páginas.

    Punto clave: un decreto puede venir seguido de sus ANEXOS escaneados a mano
    (contratos, modelos, planillas) que ocupan decenas de páginas y que el OCR
    lee como ruido. El cuerpo legal del decreto TERMINA en la firma del
    Gobernador; todo lo posterior es anexo y se descarta. Sin este corte, el
    último decreto de cada tanda se tragaba cientos de miles de caracteres.
    """
    normas = []
    paginas = [textos_ocr[k] for k in sorted(textos_ocr)]
    texto = '\n'.join(paginas)
    marcadores = list(re.finditer(r'N[úu]mero:\s*((?:DEC|RES)-[\dA-Z\-]+)', texto, re.IGNORECASE))
    for idx, m in enumerate(marcadores):
        ini = m.start()
        fin = marcadores[idx + 1].start() if idx + 1 < len(marcadores) else len(texto)
        bloque = texto[ini:fin]
        codigo = m.group(1).upper()
        md = PATRON_DECRETO.search(codigo)
        mr = PATRON_RES_GRAL.search(codigo)
        if md:
            tipo, anio, numero = 'DECRETO', md.group(1), md.group(2)
        elif mr:
            tipo, anio, numero = 'RESOLUCION GENERAL', mr.group(1), mr.group(2)
        else:
            continue

        cuerpo = _recortar_en_firma(bloque)
        cuerpo = _limpiar_ruido_ocr(cuerpo)
        referencia = _referencia_ocr(bloque)
        emisor = _emisor_desde_ocr(bloque)
        fecha, anio_f = _detectar_fecha(cuerpo, anio_esperado=anio)
        anio = anio_f or anio
        es_ind, punt, mot = clasificar_norma(cuerpo, emisor, referencia)
        normas.append({
            'tipo': tipo, 'numero': numero, 'anio': anio, 'emisor': emisor,
            'fecha_publicacion': fecha, 'texto_completo': cuerpo, 'origen': 'ocr',
            'referencia': referencia,
            'es_individual': es_ind, 'puntaje': punt, 'motivos': mot,
        })
    return normas


# Firma del Gobernador: cierra el cuerpo legal del decreto; lo que sigue es anexo.
# El nombre del gobernador es la señal más fuerte; "Gobernador Provincia del
# Chaco" solo se usa como respaldo porque también aparece en membretes de anexos.
RE_FIRMA_GOBERNADOR = re.compile(r'LEANDRO\s+C[EÉ]SAR\s+ZDERO', re.IGNORECASE)
RE_DECRETA = re.compile(r'\bDECRETA\s*:', re.IGNORECASE)


def _recortar_en_firma(bloque):
    """
    Bloque hasta el final de la PRIMERA firma del Gobernador que aparezca luego
    de la cláusula 'DECRETA:'. Esa firma cierra el cuerpo legal; lo que sigue
    (contratos, modelos, planillas escaneadas) es anexo y se descarta.

    Se toma la primera y no la última porque el nombre del gobernador puede
    reaparecer en membretes de los anexos escaneados.
    """
    desde = 0
    md = RE_DECRETA.search(bloque)
    if md:
        desde = md.end()
    m = RE_FIRMA_GOBERNADOR.search(bloque, desde)
    if m:
        # incluir "LEANDRO CESAR ZDERO Gobernador Provincia del Chaco"
        return bloque[:min(len(bloque), m.end() + 45)]
    return bloque


def _referencia_ocr(bloque):
    """Campo 'Referencia:' del decreto (resumen OCR-limpio del acto)."""
    m = re.search(r'Referencia:\s*(.+?)\s+VISTO', bloque, re.IGNORECASE | re.DOTALL)
    if not m:
        # sin VISTO detrás: tomar hasta el salto lógico (número, fin de línea larga)
        m = re.search(r'Referencia:\s*([^\n]{3,80}?)(?:\s+N[°º*]\s|\s{2,}|$)', bloque, re.IGNORECASE)
    if not m:
        return ''
    ref = re.sub(r'\s+', ' ', m.group(1)).strip(' .-:')
    return ref.upper()[:80]


# Ruido de OCR sobre escaneos de baja calidad: rachas de tokens de 1-3 símbolos
# sueltos ("A Ds EDO o A Ni IA DEDO ON Us").
RE_RUIDO_OCR = re.compile(r'(?:\b[A-Za-z0-9]{1,3}\b[\s\.\|\-—]+){6,}')


def _limpiar_ruido_ocr(texto):
    texto = RE_RUIDO_OCR.sub(' ', texto)
    texto = re.sub(
        r'-\s*\d+\s*-\s*(?:Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)'
        r'\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\s+EDICION\s+N[°º*”]?\s*[\d.]+',
        ' ', texto, flags=re.IGNORECASE)
    return _limpiar(texto)


# ===========================================================================
# HELPERS
# ===========================================================================
def _unir(lineas):
    """Une líneas reconstruyendo palabras cortadas por guion de fin de renglón."""
    out = ''
    for l in lineas:
        s = l.strip()
        if not s:
            continue
        if out and re.search(r'[A-Za-zÁÉÍÓÚÑáéíóúñ]-$', out) and re.match(r'^[a-záéíóúñ]', s):
            out = out[:-1] + s
        elif out:
            out += ' ' + s
        else:
            out = s
    return _limpiar(out)


def _limpiar(t):
    return re.sub(r'\s+', ' ', t or '').strip()


def _detectar_tipo_numero(texto, bloque):
    """Determina tipo y número de una norma nativa. None si no es norma."""
    m = PATRON_LEY.search(texto)
    if m:
        return 'LEY', m.group(1).upper()
    # los patrones de resolución/declaración/acta aplican al inicio de alguna línea
    for s in bloque:
        s = s.strip()
        mr = PATRON_RESOLUCION.match(s)
        if mr:
            return 'RESOLUCION', mr.group(1)
        md = PATRON_DECLARACION.match(s)
        if md:
            return 'DECLARACION', md.group(1)
        ma = PATRON_ACTA.match(s)
        if ma:
            return 'ACTA', ma.group(1)
    return None, None


ANIO_MIN, ANIO_MAX = 2000, 2035   # rango sano; descarta años mal leídos por OCR


def _detectar_fecha(texto, anio_esperado=None):
    """
    Fecha de la norma en ISO.

    - Descarta años fuera de [ANIO_MIN, ANIO_MAX]: el OCR sobre escaneos de baja
      calidad produce años imposibles (se vio "2027" en un decreto de 2026).
    - Si se conoce el año esperado (del código DEC-AAAA-...), prefiere la
      candidata de ese año — típicamente la fecha del encabezado del decreto,
      que es la real — en vez de cualquier fecha suelta del cuerpo.
    - Sin año esperado, toma la más reciente dentro del rango válido.
    """
    candidatas = []  # (iso, anio)
    for m in re.finditer(r'(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚáéíóúñ]+)\s+de\s+(\d{4})', texto, re.IGNORECASE):
        mes = MESES.get(m.group(2).lower())
        if mes:
            candidatas.append((f"{m.group(3)}-{mes}-{m.group(1).zfill(2)}", int(m.group(3))))
    for m in re.finditer(r'(?:de\s+fecha\s+)?(\d{1,2})/(\d{1,2})/(\d{4})', texto, re.IGNORECASE):
        candidatas.append((f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}", int(m.group(3))))

    candidatas = [c for c in candidatas if ANIO_MIN <= c[1] <= ANIO_MAX]

    if not candidatas:
        iso = _fecha_en_letras(texto)
        if iso:
            return iso, iso[:4]
        return None, None

    if anio_esperado:
        try:
            ae = int(anio_esperado)
            del_anio = [c for c in candidatas if c[1] == ae]
            if del_anio:
                return del_anio[0]  # la primera del año esperado = fecha del encabezado
        except (TypeError, ValueError):
            pass

    iso, anio = max(candidatas, key=lambda c: c[1])
    return iso, str(anio)


# Números en palabras para fechas de leyes
_UNIDADES = {'un': 1, 'uno': 1, 'primero': 1, 'dos': 2, 'tres': 3, 'cuatro': 4,
             'cinco': 5, 'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10,
             'once': 11, 'doce': 12, 'trece': 13, 'catorce': 14, 'quince': 15,
             'dieciséis': 16, 'dseis': 16, 'diecisiete': 17, 'dieciocho': 18,
             'diecinueve': 19, 'veinte': 20, 'veintiuno': 21, 'veintidós': 22,
             'veintitrés': 23, 'veinticuatro': 24, 'veinticinco': 25,
             'veintiséis': 26, 'veintisiete': 27, 'veintiocho': 28,
             'veintinueve': 29, 'treinta': 30, 'treinta y uno': 31}
_DECENAS = {'treinta': 30, 'cuarenta': 40}


def _fecha_en_letras(texto):
    m = re.search(
        r'a los\s+([a-záéíóúñ]+(?:\s+y\s+[a-záéíóúñ]+)?)\s+d[íi]as?\s+del\s+mes\s+de\s+'
        r'([a-záéíóúñ]+)\s+del?\s+año\s+dos\s+mil\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)',
        texto, re.IGNORECASE)
    if not m:
        return None
    dia = _palabra_a_num(m.group(1).lower())
    mes = MESES.get(m.group(2).lower())
    anio_resto = _palabra_a_num(m.group(3).lower())
    if not (dia and mes and anio_resto is not None):
        return None
    anio = 2000 + anio_resto
    return f"{anio}-{mes}-{str(dia).zfill(2)}"


def _palabra_a_num(p):
    p = p.strip()
    if p in _UNIDADES:
        return _UNIDADES[p]
    # "treinta y uno", "veinti..." ya cubiertos; combinaciones decena+unidad
    m = re.match(r'(treinta|cuarenta)\s+y\s+([a-záéíóúñ]+)', p)
    if m and m.group(1) in _DECENAS and m.group(2) in _UNIDADES:
        return _DECENAS[m.group(1)] + _UNIDADES[m.group(2)]
    return _UNIDADES.get(p)


def _normalizar_emisor(emisor):
    if not emisor:
        return ""
    e = re.sub(r'\s+', ' ', emisor).strip().upper()
    for a, b in (('Á', 'A'), ('É', 'E'), ('Í', 'I'), ('Ó', 'O'), ('Ú', 'U')):
        e = e.replace(a, b)
    return e


def _emisor_desde_ocr(bloque):
    """Emisor de un anexo OCR: encabezado de organismo o Poder Ejecutivo."""
    if re.search(r'Poder Ejecutivo|EL GOBERNADOR', bloque, re.IGNORECASE):
        return 'PODER EJECUTIVO'
    m = re.search(r'(ADMINISTRACI[ÓO]N TRIBUTARIA PROVINCIAL|MINISTERIO DE [A-ZÁÉÍÓÚÑ ]+)', bloque)
    if m:
        return _normalizar_emisor(m.group(1))
    return 'PODER EJECUTIVO'


def normas_a_cargar(ruta_pdf, incluir_individuales=False, usar_ocr=True):
    r = parsear_normas(ruta_pdf, usar_ocr=usar_ocr)
    normas = [n for n in r['normas'] if incluir_individuales or not n['es_individual']]
    return normas, r['anexos_pendientes'], r['ocr_usado']


# ===========================================================================
# CLI
# ===========================================================================
def _main():
    import argparse
    ap = argparse.ArgumentParser(description='Parser del Boletín Oficial de Chaco (sección oficial).')
    ap.add_argument('pdf')
    ap.add_argument('--todas', action='store_true', help='incluir normas individuales')
    ap.add_argument('--no-ocr', action='store_true', help='no intentar OCR de anexos-imagen')
    args = ap.parse_args()

    r = parsear_normas(args.pdf, usar_ocr=not args.no_ocr)
    normas = r['normas']
    generales = [n for n in normas if not n['es_individual']]
    individuales = [n for n in normas if n['es_individual']]

    print(f"OCR usado: {'sí' if r['ocr_usado'] else 'no'}")
    print(f"Normas detectadas : {len(normas)}  (generales {len(generales)} / individuales {len(individuales)})")
    if r['anexos_pendientes']:
        print(f"Anexos-imagen SIN procesar (carga manual): {len(r['anexos_pendientes'])}")
        for a in r['anexos_pendientes']:
            print(f"   - {a['anexo']}: {a['contenido']}  [{a['motivo']}]")
    print()
    for n in (normas if args.todas else generales):
        marca = 'IND' if n['es_individual'] else 'GEN'
        via = n['origen'].upper()
        print(f"[{marca}/{via}] {n['tipo']:18s} N° {str(n['numero']):12s} "
              f"{str(n['fecha_publicacion'] or '-'):11s} {str(n['emisor'] or '-')[:42]:42s} "
              f"{len(n['texto_completo']):5d} car.")
        if args.todas and n['motivos']:
            print(f"        {'; '.join(n['motivos'])}")


if __name__ == '__main__':
    _main()