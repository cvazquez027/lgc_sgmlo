#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 BOLETÍN OFICIAL DE LA PROVINCIA DE MENDOZA  —  id_jurisdiccion 14
===============================================================================

EL CASO MÁS FÁCIL DE TODOS LOS SCRAPERS: no hay que leer ningún PDF.
El sitio público (`informacionoficial.mendoza.gob.ar/boletinoficial/`) arma
todo con JavaScript contra una API interna de Mendoza
(`portalgateway.mendoza.gov.ar/api/boe/...`) que devuelve HTML ya estructurado
—y, mejor todavía, el detalle de cada norma viene con el CUERPO COMPLETO ya
como texto (no como imagen de PDF), con Origen/emisor y fecha ya sueltos.
Se descubrió toda la API a mano con el usuario, probando cada endpoint con
`curl` desde su máquina (ver el intercambio en el chat) — no hay nada acá
basado en documentación oficial, es ingeniería inversa del tráfico real.

LOS CUATRO ENDPOINTS (todos bajo https://portalgateway.mendoza.gov.ar/api/boe)
--------------------------------------------------------------------------------
1. GET  /current
   Sin parámetros. Devuelve el `<div id="boe-header">` de la ÚLTIMA edición:
   fecha (`data-boe-date`, formato DD/MM/AAAA), número (`data-boe-nro`) y el
   link a la edición impresa completa en PDF.

2. POST /find      body: fecha=AAAA-MM-DD
   Igual que `/current` pero para una fecha cualquiera — y lo mejor: si esa
   fecha no tuvo edición (fin de semana, feriado), la propia API resuelve a
   la edición más cercana y devuelve SU fecha real, no un 404. No hace falta
   adivinar el número de boletín a partir de la fecha: se pide una vez y listo.

3. POST /index     body: fecha=AAAA-MM-DD&numero=NNNNN
   ambos parámetros son obligatorios (sin `numero` tira 400). Devuelve el
   `<div id="boe-body">` completo de esa edición, con DOS acordeones:

     - "Sección General" (id="seccionGeneral"): lo que nos interesa. Adentro,
       un sub-acordeón por tipo (visto: DECRETOS, RESOLUCIONES, ORDENANZAS,
       DECRETOS MUNICIPALES — varía según qué se publicó ese día). Cada
       norma es un <li> con: el link "Tema" (que trae en sus atributos
       data-id, data-fecha ISO y data-version — la clave para pedir el
       detalle), el número ("Decreto Nro.", "Resolución Nro.", etc.), la
       fecha en DD/MM/AAAA (redundante con data-fecha) y el Origen (el
       organismo emisor, ¡ya resuelto, sin adivinar nada del cuerpo!).

     - "Sección Particular" (id="seccionParticular"): el equivalente a la
       Sección Comercial/Edictos de otras provincias — Contratos Sociales,
       Convocatorias, Irrigación y Minas, Remates, Concursos y Quiebras,
       Títulos Supletorios, Notificaciones, Sucesorios, Mensuras, Aviso Ley
       19.550, Licitaciones, Fe de Erratas. Se ignora por completo: es la
       parte de "Edictos" que cuenta el encabezado de la edición aparte de
       "Normas" ("23 Normas y 102 Edictos").

4. POST /detail    body: tipo_busqueda=norma&norma_edicto_id=<data-id>&
                         fecha_desde=<data-fecha>&fecha_hasta=&
                         tipo_boletin=2&numero=
   Con el `data-id` de cada `<li>` de la Sección General, esto devuelve el
   detalle completo: el cuerpo de la norma YA COMO TEXTO (con sus <p>,
   entidades HTML y todo — nada de imagen ni columnas ni negrita falsa) y,
   mejor todavía, el link directo al PDF de ESA norma puntual
   ("Texto Publicado" → `https://boe.mendoza.gov.ar/publico/pdf_pedido/<hash>`),
   no sólo a la edición completa. Ese es el `url_norma` que se manda al
   backend — no hace falta armar ningún fragmento (#TIPO-NUMERO-ANIO) como en
   las otras provincias, acá cada norma tiene su propia URL real y estable.

   `fecha_desde` en el pedido es la fecha PROPIA de la norma (data-fecha),
   no la fecha de la edición — así arma el pedido el propio sitio, se
   replica igual. `tipo_boletin=2` y `fecha_hasta`/`numero` vacíos son fijos,
   así los manda el frontend siempre.

QUÉ NO HAY QUE ADIVINAR ACÁ (a diferencia de TODAS las otras provincias)
--------------------------------------------------------------------------
- Año: sale directo de `data-fecha` (ISO completo, AAAA-MM-DD). Nunca hace
  falta mirar el código de la norma ni la fecha del boletín.
- Emisor: viene resuelto en "Origen". Nunca hay que leer "EL MINISTRO DE...
  RESUELVE:" en el cuerpo ni mantener una tabla de siglas.
- Deduplicación entre organismos con el mismo número (la trampa de Jujuy): se
  resuelve sola, porque el Origen ya viene específico por registro (incluso
  entre distintas Municipalidades con el mismo número de Decreto Municipal).
- Corte de la parte normativa: no hace falta cortar un PDF por banners ni
  por sumario — "Sección General" y "Sección Particular" ya vienen separadas
  por el propio sitio en dos <div> distintos.

SÍNTESIS
--------
El campo "Tema" del listado casi nunca es una síntesis real: la mayoría de
las veces es un número de expediente ("EX-2025-05613756-GDEMZA-GOBIERNO"),
no una descripción. La síntesis se arma, como en el resto de las provincias,
del Artículo 1º del cuerpo (que si llega por `/detail`). El formato del
Artículo acá usa guion en vez de dos puntos ("Artículo 1º - Autorícese..."),
así que el regex acepta guion, dos puntos o punto como separador.

TIPO Y NUMERACIÓN
------------------
El tipo de norma sale del título del sub-acordeón (DECRETOS→DECRETO,
RESOLUCIONES→RESOLUCION, ORDENANZAS→ORDENANZA, DECRETOS MUNICIPALES→DECRETO
MUNICIPAL), no de la etiqueta "Nro." de cada ítem (que varía: "Decreto
Nro.", "Resolución Nro.", "Decreto Municipal Nro.") — más consistente. Si en
el futuro aparece un rubro nuevo no visto (por ejemplo LEYES, que no salió
en ninguna de las muestras), se lo mapea igual por si acaso y, si no está en
el mapa, se cae a un singular a las patadas (le saca la S final) con un
aviso por stderr para que se note y se pueda agregar al mapa.

FLAGS
-----
    --dry-run          no envía nada
    --fecha AAAA-MM-DD  pide esa fecha (si no hubo edición ese día, la API
                        resuelve sola a la más cercana)
    --numero N          si ya se sabe el número de boletín, salta el paso
                        de --fecha/--find (más rápido, útil para reintentar)
    --indice ARCHIVO    usa un HTML de /api/boe/index ya guardado (pruebas
                        del parser sin pegarle al sitio)
    --sin-detalle       no pide /detail por cada norma (más rápido para
                        --volcar; sin esto no hay síntesis real ni url_norma
                        específica, sólo lo que trae el listado)
    --todas             muestra también las individuales, con puntaje y motivos
    --sin-filtro         envía todo sin filtrar
    --volcar             imprime lo encontrado y sale

===============================================================================
QUÉ FALTA VALIDAR
===============================================================================
1. Nunca se vio el rubro LEYES en Sección General (las 2 ediciones de
   muestra sólo trajeron Decretos/Resoluciones, y una tercera trajo también
   Ordenanzas/Decretos Municipales). Si aparece, se lo mapea por nombre
   igual, pero no hay muestra real para confirmar que "/detail" funcione
   igual para ese tipo.
2. Actos individuales: la única muestra de cuerpo completo que se vio
   (Decreto 880, autorización de misión oficial a funcionarios con DNI) es
   un caso límite — menciona personas y DNI pero no es una designación ni
   una renuncia. El clasificador (compartido con el resto de las provincias)
   lo deja del lado "general" con puntaje bajo; falta calibrar con más
   muestras reales de Mendoza.
3. No se probó el volumen real de pedidos por edición (una por norma, vía
   /detail) contra el sitio en producción corriendo muchos días seguidos —
   en las pruebas manuales anduvo bien, pero conviene que el primer par de
   corridas del cron se miren con atención por si hay algún límite de tasa.
===============================================================================
"""

import os
import re
import sys
import json
import time
import argparse
from datetime import date

import socket

try:
    import urllib3.util.connection as _urllib3_conn
    _urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
except Exception:
    pass
# El 503 ("No server is available to handle this request", típico de un
# balanceador IIS/ARR con algún nodo caído) apareció SÓLO en clientes
# .NET/Python (Invoke-WebRequest de PowerShell y este mismo script), nunca
# en curl.exe real de CMD — el patrón clásico de una red con IPv6 roto o mal
# balanceado, donde los clientes que prefieren IPv6 caen en un nodo enfermo
# y curl (que en Windows suele preferir IPv4) lo esquiva. Forzar IPv4 acá es
# la corrección estándar para este caso; si el problema fuera otra cosa
# (un proxy, por ejemplo) esta línea no hace ningún daño.

import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

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

API_MENDOZA = 'https://portalgateway.mendoza.gov.ar/api/boe'

HEADERS_API = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': '*/*',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Origin': 'https://informacionoficial.mendoza.gob.ar',
    'Referer': 'https://informacionoficial.mendoza.gob.ar/',
    'Content-Type': 'application/x-www-form-urlencoded',
}

REINTENTOS = 3
ESPERA_REINTENTO = 3
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700

RUBRO_A_TIPO = {
    'DECRETOS': 'DECRETO',
    'RESOLUCIONES': 'RESOLUCION',
    'ORDENANZAS': 'ORDENANZA',
    'DECRETOS MUNICIPALES': 'DECRETO MUNICIPAL',
    'LEYES': 'LEY',                    # nunca visto en las muestras; por las dudas
    'RESOLUCIONES MUNICIPALES': 'RESOLUCION MUNICIPAL',   # ídem
}


def _tipo_de_rubro(rubro):
    rubro = (rubro or '').strip().upper()
    if rubro in RUBRO_A_TIPO:
        return RUBRO_A_TIPO[rubro]
    print(f"Aviso: rubro '{rubro}' no está en el mapa conocido, "
          f"se usa un singular improvisado.", file=sys.stderr)
    return rubro[:-1] if rubro.endswith('S') else rubro


def _compacto(texto):
    return re.sub(r'\s+', ' ', (texto or '')).strip()


# ===========================================================================
# LLAMADAS A LA API
# ===========================================================================
_SESION = None


def sesion():
    global _SESION
    if _SESION is None:
        _SESION = requests.Session()
        _SESION.headers.update(HEADERS_API)
    return _SESION


def _post(endpoint, data, timeout=45):
    url = f'{API_MENDOZA}/{endpoint}'
    for intento in range(1, REINTENTOS + 1):
        try:
            r = sesion().post(url, data=data, timeout=timeout)
            if 200 <= r.status_code < 300:
                return r.text
            if r.status_code == 400:
                raise RuntimeError(f"{endpoint} rechazó los parámetros {data}: {r.text[:300]}")
            print(f"Aviso: POST {endpoint} {data} devolvió HTTP {r.status_code}: "
                  f"{r.text[:300]!r}", file=sys.stderr)
            if r.status_code < 500:
                return None
        except requests.RequestException as e:
            if intento == REINTENTOS:
                raise RuntimeError(f"Error de red pidiendo {endpoint}: {e}")
        time.sleep(ESPERA_REINTENTO * intento)
    return None


def _get(endpoint, timeout=45):
    url = f'{API_MENDOZA}/{endpoint}'
    for intento in range(1, REINTENTOS + 1):
        try:
            r = sesion().get(url, timeout=timeout)
            if 200 <= r.status_code < 300:
                return r.text
            print(f"Aviso: GET {endpoint} devolvió HTTP {r.status_code}: "
                  f"{r.text[:300]!r}", file=sys.stderr)
            if r.status_code < 500:
                return None
        except requests.RequestException as e:
            if intento == REINTENTOS:
                raise RuntimeError(f"Error de red pidiendo {endpoint}: {e}")
        time.sleep(ESPERA_REINTENTO * intento)
    return None


RE_BOE_HEADER = re.compile(
    r'data-boe-date="(?P<dia>\d{2})/(?P<mes>\d{2})/(?P<anio>\d{4})"\s+'
    r'data-boe-nro="(?P<numero>\d+)"')
RE_LINK_IMPRESA = re.compile(r'href="(?P<url>https://boe\.mendoza\.gov\.ar/[^"]*verpdf/\d+)"')
RE_CONTADOR = re.compile(r'(?P<normas>\d+)\s*Normas?\s+y\s+(?P<edictos>\d+)\s*Edictos?', re.IGNORECASE)


def _parsear_boe_header(html):
    """De /current o /find: (fecha_iso, numero, url_edicion_impresa, contador)."""
    if not html:
        return None, None, None, None
    m = RE_BOE_HEADER.search(html)
    if not m:
        print(f"Aviso: la respuesta llegó (HTTP 200) pero no se reconoció el "
              f"encabezado boe-header. Primeros 300 caracteres: {html[:300]!r}",
              file=sys.stderr)
        return None, None, None, None
    fecha_iso = f"{m.group('anio')}-{m.group('mes')}-{m.group('dia')}"
    numero = m.group('numero')
    m2 = RE_LINK_IMPRESA.search(html)
    url_impresa = m2.group('url') if m2 else None
    m3 = RE_CONTADOR.search(html)
    contador = (int(m3.group('normas')), int(m3.group('edictos'))) if m3 else (None, None)
    return fecha_iso, numero, url_impresa, contador


def descubrir_ultimo():
    html = _get('current')
    return _parsear_boe_header(html)


def descubrir_por_fecha(fecha_iso):
    html = _post('find', {'fecha': fecha_iso})
    return _parsear_boe_header(html)


# ===========================================================================
# LISTADO (Sección General)
# ===========================================================================
def listar_normas(fecha_iso, numero):
    """[{'rubro','tipo','numero','anio','fecha','data_id','tema'}] de todas
    las normas de la Sección General de esa edición (ignora Sección
    Particular por completo). Devuelve también el html crudo por si hace
    falta para --volcar."""
    html = _post('index', {'fecha': fecha_iso, 'numero': numero})
    return parsear_indice(html), html


def parsear_indice(html):
    if not html or BeautifulSoup is None:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    seccion_general = soup.find('div', id='seccionGeneral')
    if not seccion_general:
        return []

    normas = []
    for boton in seccion_general.find_all('button', class_='accordion-button'):
        target = (boton.get('data-bs-target') or '').lstrip('#')
        if not target:
            continue
        rubro = _compacto(boton.get_text())
        contenedor = seccion_general.find('div', id=target)
        if not contenedor:
            continue
        tipo = _tipo_de_rubro(rubro)

        for li in contenedor.find_all('li', class_='list-group-item'):
            a = li.find('a', class_='boe-detail')
            if not a:
                continue
            data_id = a.get('data-id')
            data_fecha = a.get('data-fecha')      # ya viene en AAAA-MM-DD
            tema = _compacto(a.get_text())

            numero_norma = _campo_li(li, r'Nro\.?\s*$')
            origen = _campo_li(li, r'^Origen:?$')

            normas.append({
                'rubro': rubro, 'tipo': tipo,
                'numero': _compacto(numero_norma).rstrip('.'),
                'anio': (data_fecha or '')[:4],
                'fecha': data_fecha,
                'data_id': data_id,
                'tema': tema,
                'emisor': origen or '',
            })
    return normas


def _campo_li(li, patron_etiqueta):
    """Texto que sigue a un <strong> cuyo texto matchea `patron_etiqueta`,
    hasta el próximo <br> o <strong>. Sirve para leer 'Decreto Nro.',
    'Resolución Nro.', 'Origen:', etc. sin depender de la etiqueta exacta."""
    for strong in li.find_all('strong'):
        if re.search(patron_etiqueta, _compacto(strong.get_text()), re.IGNORECASE):
            partes = []
            for sib in strong.next_siblings:
                nombre = getattr(sib, 'name', None)
                if nombre in ('br', 'strong'):
                    break
                partes.append(sib.get_text() if hasattr(sib, 'get_text') else str(sib))
            return _compacto(''.join(partes))
    return ''


# ===========================================================================
# DETALLE (cuerpo completo + PDF individual)
# ===========================================================================
RE_MARCA_RESOLUTIVA = re.compile(r'^[ \t]*(RESUELVE|DISPONE|DECRETA)\s*:?\s*$',
                                 re.IGNORECASE | re.MULTILINE)

RE_ARTICULO1 = re.compile(
    r'Art(?:[íi]?culo|\.)\s*1(?!\d)\s*(?:er|ro|[º°])?\s*\)?\.?\s*[-:]?\s*'
    r'(?P<texto>[\s\S]+?)'
    r'(?=Art(?:[íi]?culo|\.)\s*2(?!\d)\s*(?:do|[º°])?\s*\)?\.?\s*[-:]|\Z)',
    re.IGNORECASE)


RE_ART1_PELADO = re.compile(r'\A\s*1(?!\d)\s*(?:er|ro|[º°])?\s*\)\s*', re.IGNORECASE)
RE_ART2_PELADO = re.compile(r'\b2(?!\d)\s*(?:do|[º°])?\s*\)', re.IGNORECASE)


def _sintesis_de_texto(texto):
    """
    El Artículo 1º real es el primero que aparece DESPUÉS de la marca
    "RESUELVE:"/"DISPONE:"/"DECRETA" (sola en su renglón, como siempre
    antecede al articulado) — si se busca desde el principio del texto, una
    cita a "el Artículo 1 del Anexo II de..." dentro de un considerando se
    confunde con el real (se vio en una Resolución real de Dirección
    General de Escuelas). Se toma la ÚLTIMA marca por si hay más de una.

    Caso más raro todavía (visto una vez, Departamento Gral. de Irrigación):
    el propio artículo 1º viene numerado "pelado" ("1°) Rectifíquese...",
    sin la palabra "Artículo"/"Art." adelante) y en la MISMA oración cita el
    "Art. 1°" de otra resolución — si no se prioriza el pelado cuando está
    anclado justo al principio del articulado, se termina extrayendo la cita
    en vez del propio.
    """
    texto = texto or ''
    inicio = 0
    ultima_marca = None
    for m in RE_MARCA_RESOLUTIVA.finditer(texto):
        ultima_marca = m
    if ultima_marca:
        inicio = ultima_marca.end()

    resto = texto[inicio:]
    m_pelado = RE_ART1_PELADO.match(resto)
    if m_pelado:
        cierre = RE_ART2_PELADO.search(resto[m_pelado.end():])
        fin = m_pelado.end() + cierre.start() if cierre else len(resto)
        return _compacto(resto[m_pelado.end():fin])

    m = RE_ARTICULO1.search(texto, inicio)
    if not m and inicio:
        # no había marca clara o no se encontró después: probar en todo el texto
        m = RE_ARTICULO1.search(texto)
    if m:
        return _compacto(m.group('texto'))
    return _compacto(texto[:400])


def obtener_detalle(data_id, fecha_iso):
    """(texto_completo, url_pdf_norma) para una norma puntual, vía /detail.
    Devuelve ('', None) si falla — se loguea aparte, no se corta el resto
    del boletín por una sola norma que no traiga detalle."""
    payload = {
        'tipo_busqueda': 'norma',
        'norma_edicto_id': data_id,
        'fecha_desde': fecha_iso or '',
        'fecha_hasta': '',
        'tipo_boletin': '2',
        'numero': '',
    }
    try:
        html = _post('detail', payload)
    except RuntimeError as e:
        print(f"Aviso: /detail falló para id={data_id}: {e}", file=sys.stderr)
        return '', None
    if not html or BeautifulSoup is None:
        return '', None

    soup = BeautifulSoup(html, 'html.parser')
    url_pdf = None
    for a in soup.find_all('a', href=True):
        if 'pdf_pedido' in a['href']:
            url_pdf = a['href']
            break
    cuerpo_div = soup.find('div', id='detail-body')
    texto = cuerpo_div.get_text('\n', strip=True) if cuerpo_div else ''
    return texto, url_pdf


# ===========================================================================
# CLASIFICACIÓN INDIVIDUAL / GENERAL
# ===========================================================================
# Mismos patrones que el resto de las provincias (mismo idioma
# administrativo). Sin muestra real de un acto claramente individual de
# Mendoza para calibrar — ver "QUÉ FALTA VALIDAR".
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
    (r'\bmisi[óo]n\s+oficial\b',                              2, 'misión oficial a funcionarios puntuales'),
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


# ===========================================================================
# BACKEND (mismo contrato que el resto de los bots)
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
        r = requests.post(URL_HISTORIAL,
                          json={"id_jurisdiccion": id_jurisdiccion,
                                "fecha_boletin": fecha_boletin, "accion": "verificar"},
                          headers={"Authorization": f"Bearer {API_KEY_BACKEND}"}, timeout=10)
        return r.json().get('procesado', False)
    except Exception:
        return False


def registrar_boletin_procesado(id_jurisdiccion, fecha_boletin, cantidad):
    try:
        requests.post(URL_HISTORIAL,
                      json={"id_jurisdiccion": id_jurisdiccion, "fecha_boletin": fecha_boletin,
                            "accion": "registrar", "cantidad_normas": cantidad},
                      headers={"Authorization": f"Bearer {API_KEY_BACKEND}"}, timeout=10)
    except Exception:
        pass


def guardar_debug(contenido, nombre):
    try:
        with open(nombre, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"Guardado {nombre} para depuración", file=sys.stderr)
    except Exception as e:
        print(f"No se pudo guardar {nombre}: {e}", file=sys.stderr)


def construir_sintesis(norma):
    cuerpo = _compacto(norma.get('sintesis') or '').strip(' .-:')
    if len(cuerpo) > MAX_SINTESIS:
        cuerpo = cuerpo[:MAX_SINTESIS].rsplit(' ', 1)[0] + '…'
    return cuerpo or f"{norma.get('tipo')} {norma.get('numero')}"


def recortar_texto(texto, tope=MAX_TEXTO_COMPLETO):
    texto = texto or ''
    if len(texto) <= tope:
        return texto
    marca = ' […] '
    cabeza = int((tope - len(marca)) * 0.55)
    cola = tope - len(marca) - cabeza
    return texto[:cabeza] + marca + texto[-cola:]


# ===========================================================================
# EJECUCIÓN
# ===========================================================================
def _main():
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Mendoza.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se descubre por la API')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--fecha', metavar='AAAA-MM-DD', help='pide esa fecha (la API resuelve '
                    'sola a la edición más cercana si no hubo boletín ese día)')
    ap.add_argument('--numero', type=int, help='si ya se sabe el número de boletín')
    ap.add_argument('--indice', metavar='ARCHIVO',
                    help='usar un HTML de /api/boe/index ya guardado (pruebas)')
    ap.add_argument('--sin-detalle', action='store_true',
                    help='no pide /detail por norma (sin síntesis real ni url_norma específica)')
    ap.add_argument('--todas', action='store_true',
                    help='muestra también las individuales, con puntaje y motivos')
    ap.add_argument('--sin-filtro', action='store_true', help='envía todo sin filtrar')
    ap.add_argument('--volcar', action='store_true', help='imprime lo encontrado y sale')
    args = ap.parse_args()

    fecha_boletin = args.fecha
    numero_boletin = args.numero
    url_edicion_impresa = None

    # ---- 1. Ubicar la edición ------------------------------------------------
    if args.indice:
        with open(args.indice, encoding='utf-8') as f:
            html_indice = f.read()
        fecha_boletin = fecha_boletin or 'desconocida'
        print(f"Usando índice local: {args.indice}", file=sys.stderr)
    else:
        try:
            if numero_boletin and fecha_boletin:
                pass  # ya se sabe todo, no hace falta /current ni /find
            elif fecha_boletin:
                fecha_boletin, numero_boletin, url_edicion_impresa, contador = \
                    descubrir_por_fecha(fecha_boletin)
            else:
                fecha_boletin, numero_boletin, url_edicion_impresa, contador = descubrir_ultimo()
        except RuntimeError as e:
            salida("error", str(e))

        if not fecha_boletin or not numero_boletin:
            salida("warning", "No se pudo determinar la edición a procesar.")

        print(f"Boletín Nº {numero_boletin} del {fecha_boletin}"
              + (f" — {url_edicion_impresa}" if url_edicion_impresa else ''), file=sys.stderr)

        try:
            _, html_indice = listar_normas(fecha_boletin, numero_boletin)
        except RuntimeError as e:
            salida("error", str(e))

    # ---- 2. Parsear la Sección General ---------------------------------------
    listado = parsear_indice(html_indice)
    if not listado:
        salida("warning", f"No se reconoció ninguna norma en la Sección General "
                          f"del boletín Nº {numero_boletin} ({fecha_boletin}). "
                          f"¿La API cambió de formato?")

    por_rubro = {}
    for n in listado:
        por_rubro.setdefault(n['rubro'], 0)
        por_rubro[n['rubro']] += 1
    print(f"Sección General: {len(listado)} normas ({', '.join(f'{v} {k}' for k, v in por_rubro.items())})",
          file=sys.stderr)

    if args.volcar:
        for n in listado:
            print(f"  [{n['rubro']}] {n['tipo']:20s} {n['numero']:>8s}/{n['anio']} "
                  f"id={n['data_id']} {n['emisor'][:35]:35s} {n['tema'][:40]}", file=sys.stderr)
        salida("success", f"volcado: {len(listado)} normas en Sección General.")

    # ---- 3. Traer el detalle de cada una --------------------------------------
    normas = []
    sin_detalle = 0
    for n in listado:
        texto, url_pdf = ('', None)
        if not args.sin_detalle:
            texto, url_pdf = obtener_detalle(n['data_id'], n['fecha'])
            if not texto:
                sin_detalle += 1
        n['texto_completo'] = texto
        n['sintesis'] = _sintesis_de_texto(texto) if texto else n['tema']
        n['url_norma'] = url_pdf
        normas.append(n)
    if sin_detalle:
        print(f"Aviso: {sin_detalle} normas no trajeron detalle (se manda igual, "
              f"con el 'Tema' del listado como síntesis y sin URL específica).",
              file=sys.stderr)

    for n in normas:
        n['es_individual'], n['puntaje'], n['motivos'] = clasificar_norma(
            n['tipo'], n['sintesis'], n['texto_completo'])

    generales = [n for n in normas if not n['es_individual']]
    individuales = [n for n in normas if n['es_individual']]
    a_enviar = normas if args.sin_filtro else generales

    guardar_debug(json.dumps(normas, ensure_ascii=False, indent=2, default=str), 'debug_mendoza.json')
    print(f"Boletín Nº {numero_boletin} del {fecha_boletin} | normas: {len(normas)} "
          f"(generales {len(generales)} / individuales {len(individuales)})", file=sys.stderr)

    if args.dry_run:
        for n in (normas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {n['tipo']:20s} N° {n['numero']:>8s}/{n['anio']} "
                  f"{n['emisor'][:30]:30s} {n['sintesis'][:50]}", file=sys.stderr)
            if args.todas and n.get('motivos'):
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    if not a_enviar:
        salida("warning", f"Las {len(individuales)} normas del boletín son actos "
                          f"individuales; no se envió ninguna.")

    if fecha_boletin and verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

    # ---- 4. Envío -----------------------------------------------------------
    payload = [{
        "id_jurisdiccion": args.id_jurisdiccion,
        "nombre_emisor": n['emisor'] or 'PODER EJECUTIVO',
        "tipo_norma_desc": n["tipo"],
        "numero": n["numero"],
        "anio": n["anio"],
        "fecha_publicacion": n["fecha"],
        "sintesis": construir_sintesis(n),
        "texto_completo": recortar_texto(n["texto_completo"]),
        "url_norma": n["url_norma"] or f"https://boe.mendoza.gov.ar/#{n['data_id']}",
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