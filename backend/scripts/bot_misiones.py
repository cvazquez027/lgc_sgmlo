#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 BOLETÍN OFICIAL DE LA PROVINCIA DE MISIONES  —  id_jurisdiccion (ver tabla)
===============================================================================

Reconocimiento hecho contra el sitio real (`web_fetch` SÍ llega a este
dominio, a diferencia de la mayoría de los boletines provinciales) y contra
el TEXTO REAL de 5 ediciones de 5 meses distintos (13/03, 20/04, 21/05,
24/06 y 29/07 de 2026), bajadas una por una. Lo que sigue no es hipótesis:
es lo que se vio en esas 5 muestras. Lo que NO se vio está marcado explícito
en "QUÉ FALTA VALIDAR" al final.

DESCUBRIMIENTO
--------------
La portada (`https://www.boletindigital.misiones.gov.ar/`) es HTML servido
por un JSF/ICEfaces (con ViewState, botones de postback, etc. — nada de eso
hace falta para lo que necesitamos). Lo único que importa es que la portada
trae, siempre, tarjetas con las últimas 5 ediciones en HTML plano, más nuevo
primero:

    Boletín Nro: 16643
    Del 30/07/2026
    <a href="/boletines/16643 firmado.pdf">DESCARGAR</a>

    Boletín Nro: 16642
    Del 29/07/2026
    <a href="/boletines/16642.pdf">DESCARGAR</a>
    ...

TRAMPA CHICA: la edición más nueva del día a veces tiene el link con un
ESPACIO en el nombre de archivo ("16643 firmado.pdf" en vez de
"16643.pdf") — visto tal cual en el sitio real el 30/07/2026. No se
reconstruye la URL a mano: se toma el `href` tal cual lo trae la tarjeta
(mismo espíritu que La Rioja con `boletin.html`), sólo se url-encodea el
espacio al pedirlo.

El número de boletín es un CORRELATIVO por día hábil (no por fecha como La
Rioja): 16639 (vie 24/07) → 16640 (lun 27/07) → 16641 (mar 28/07) → 16642
(mié 29/07) → 16643 (jue 30/07), +1 por día hábil, saltando fines de semana.
Confirmado además con los otros 4 muestreos: pedir `hoy - N días hábiles`
como número estimado y corregir contra la fecha real de tapa del PDF
devuelto acertó el mes correcto las 4 veces. Como la portada sólo expone las
últimas 5 tarjetas (después hay un botón "VER MÁS" y un "CALENDARIO" con
meses — ambos ICEfaces con postback y ViewState, NO reproducibles con un
`requests.get`/`.post` simple), `--fecha` sólo puede resolver una fecha
dentro de esas últimas ~5 ediciones hábiles. Para reprocesar algo más viejo
existe `--numero N` (arma la URL directo por `/boletines/N.pdf` y lee la
fecha real de la propia tapa del PDF) — pero el número hay que consEGUIRlo
a mano (abriendo el sitio), no se adivina en frío. Ver "QUÉ FALTA VALIDAR".

ESTRUCTURA DEL PDF
-------------------
Página 1 (tapa): nómina de AUTORIDADES, cita legal fija ("LEY IV - Nº 1 -
APARECE LOS DÍAS HÁBILES"), la línea de metadatos:

    AÑO LXIX Nº 16642 POSADAS, MIÉRCOLES 29 DE JULIO DE 2026 EDICIÓN DE 17 PÁGINAS

y el SUMARIO — el oráculo de cobertura, análogo al cuadro RESUMEN de La
Rioja pero mucho más descriptivo: una línea por cada rubro/organismo
publicado, con su tipo, número(s) y el rango de páginas:

    Decretos Sintetizados N°s.: 2129, 2137, 2138 y 2139/25 .....Pág. 2 y 3.
    Municipalidad de Garupá: Resolución N° 243 ..................Pág. 4.
    Superior Tribunal de Justicia: Acordada N° 84 ................Pág. 4 y 5.
    Sociedades:....................................................Pág. 5 a 9.
    Edictos:........................................................Pág. 9 a 14.
    Subastas: ......................................................Pág. 14.
    Convocatorias:..................................................Pág. 14 a 17.

El SUMARIO está en Title Case ("Decretos Sintetizados"); los encabezados
reales dentro del cuerpo están SIEMPRE en mayúsculas completas ("DECRETO N°
2129"). Esto se aprovecha a propósito: los regex que buscan encabezados en
el CUERPO son case-sensitive (sin IGNORECASE) para no confundirse con citas
en Title Case dentro de la prosa ("...de la Ley VII - N° 11 (antes Ley N°
2.303)" aparece width mitad de un considerando, no es un encabezado nuevo).

Página 2 en adelante: "PRIMERA SECCIÓN" (normativa real) y, más adelante,
"SEGUNDA SECCIÓN" (Sociedades/Edictos/Subastas/Convocatorias — avisos
privados, se descarta igual que en el resto de las provincias). A diferencia
de La Rioja, NO hay trampa de columnas: el texto de cada página, con
`pdfplumber` liso (`extract_text()`), sale en el orden de lectura correcto
en las 5 muestras (se verificó leyendo artículos completos de punta a punta
sin cortes a mitad de oración). Ver igual la advertencia en "QUÉ FALTA
VALIDAR": esto se confirmó contra el TEXTO ya extraído por `web_fetch`, no
contra `pdfplumber` corriendo acá mismo (el sandbox no tiene salida de red
al dominio) — si alguna vez aparece un artículo cortado a la mitad, es la
señal de que sí hace falta portar la lógica de columnas de La Rioja.

DOS TIPOS DE DECRETO, UN SOLO FORMATO DE ENCABEZADO
------------------------------------------------------
El sumario distingue "Decretos Sintetizados" (varios, cortos, resúmenes de
decretos ya firmados hace tiempo — los 4 de la muestra de julio son todos
del 14/10/2025 publicados el 29/07/2026) de "Decreto Completo" (uno solo,
puede ocupar veintipico de páginas: el Decreto 654 de la muestra de mayo
ocupa las páginas 2 a 24 de una edición de 47). Ambos usan el MISMO
encabezado en el cuerpo ("DECRETO N° <numero>"), así que no hace falta
distinguirlos para extraer — sólo importa para el oráculo, y ahí tampoco:
`parsear_sumario` matchea "Decreto(s) (Completo(s)|Sintetizado(s))?" por
igual.

EL SUMARIO NO ES UN TECHO ÚNICO: HAY RUIDO INTERCALADO EN LA PRIMERA SECCIÓN
--------------------------------------------------------------------------------
A diferencia de La Rioja (donde alcanza con un único "techo" a partir del
cual se descarta todo), acá aparecen bloques que NO son normativa
INTERCALADOS entre normas reales, todavía dentro de la Primera Sección:

  - "EXPEDIENTES A SENTENCIA": un juzgado informa expedientes pendientes de
    sentencia (sin Artículo 1º/2º, no es normativa). Visto en 2 de las 5
    muestras, y en la de marzo aparece ANTES de una Disposición real — o
    sea, no sirve como techo final, hay que tratarlo como un corte más.
  - "COMUNICADO DE PRENSA" (del Superior Tribunal de Justicia): un aviso de
    audiencia, tampoco es normativa. Visto 1 vez, también intercalado antes
    de contenido real.

Por eso el corte de cada norma no es "hasta el próximo encabezado o hasta un
techo fijo": es "hasta el próximo punto de corte que sea CUALQUIERA de
(a) el próximo encabezado de norma, (b) el próximo título de ruido conocido,
(c) el principio de SEGUNDA SECCIÓN" — se arma una lista única de cortes y
se in usa. "SEGUNDA SECCIÓN" sí apareció en las 5/5 muestras como techo
final confiable.

EL TRUCO DE LAS LETRAS ESPACIADAS EN LA FÓRMULA RESOLUTIVA
----------------------------------------------------------------
Confirmado contra el PDF real (texto extraído, no una hipótesis): la fórmula
que antecede al articulado de Resoluciones/Disposiciones a veces sale con
cada letra separada por un espacio, cuando está sola en su renglón:

    LA MINISTRA DE TRABAJO Y EMPLEO
    R E S U E L V E:

    EL SUBSECRETARIO DE TRANSPORTE...
    D I S P O N E:

pero OTRAS VECES, cuando sigue en la misma línea que el cargo, sale normal:

    ...EL MINISTRO DE ECOLOGÍA Y RECURSOS NATURALES RENOVABLES RESUELVE:
    ARTICULO 1°.- LLÁMASE a Concurso...

`_patron_espaciado()` arma un patrón que tolera espacios opcionales entre
cada letra (con `[ \\t]*`, que matchea también con CERO espacios), así que
un solo regex cubre las dos formas sin duplicar nada.

EMISOR: LA LÍNEA EN MAYÚSCULAS QUE ANTECEDE AL ENCABEZADO
----------------------------------------------------------------
Mejor señal que "EL/LA <CARGO> RESUELVE" (que obliga a adivinar cómo pasar
de cargo a organismo, como hace La Rioja): acá el propio cuerpo trae el
organismo ya escrito, en su propia línea, justo antes del encabezado:

    RESOLUCIONES
    MINISTERIO DE TRABAJO Y EMPLEO
    RESOLUCIÓN Nº 052

    DISPOSICIONES
    MINISTERIO DE INDUSTRIA
    DIRECCIÓN GENERAL DE MINAS Y GEOLOGÍA
    DISPOSICIÓN Nº 23/26-AM

`_organismo_precedente()` junta las líneas en mayúsculas que anteceden
directo al encabezado (parando en la primera línea que sea un título de
sección conocido como "RESOLUCIONES"/"DISPOSICIONES"/etc.), y sólo si no
encuentra nada cae al mecanismo de "cargo antes de RESUELVE/DISPONE" estilo
La Rioja, y de ahí a un default por tipo. Para DECRETO no hay línea de
organismo (van directo de "DECRETOS SINTETIZADOS"/"DECRETOS COMPLETOS" al
encabezado): cae directo a PODER EJECUTIVO, igual que en el resto de las
provincias.

NÚMERO Y AÑO DE CADA NORMA
------------------------------
- El encabezado puede traer sufijos pegados al número: "DISPOSICIÓN Nº
  23/26-AM" (año corto + sigla de oficina), "43/2025-AM" (año largo). El
  regex del encabezado los reconoce pero NO los captura como parte del
  número — sólo el número limpio.
- El año de cada norma sale, en orden de preferencia, de: (1) la fecha
  propia pegada al encabezado ("POSADAS, 14 de Octubre de 2025.-" /
  "GARUPÁ, Misiones, 22 de Julio de 2026.-" — CUALQUIER localidad, no sólo
  Posadas, porque las resoluciones municipales llevan su propia ciudad);
  (2) el sufijo de año que a veces trae el propio número en el SUMARIO
  ("2139/25" — OJO: NO se propaga al resto de la lista, ver más abajo);
  (3) el año del boletín como último recurso.
- TRAMPA CHICA: el año a veces sale con punto de miles, igual que un número
  de norma: "POSADAS, 10 de Febrero de 2.026.-" (con punto) conviviendo con
  "POSADAS, 22 de Junio de 2026.-" (sin punto) en muestras distintas. El
  regex de fecha tolera el punto opcional.
- TRAMPA GRANDE DESCARTADA A PROPÓSITO: en la muestra de marzo, el sumario
  trae "Decretos Sintetizados N°s.: 1826, 1867, 1869/25, 171, 175, 215" — el
  sufijo "/25" está pegado a un número del MEDIO de la lista, no al último
  como en la muestra de julio. Por eso NO se asume que el sufijo de año se
  comparte con toda la lista (a diferencia de La Rioja, donde "Año 2026"
  sí aplicaba a todo el rubro): acá cada número se resuelve con su propio
  sufijo si lo tiene, y si no, con la fecha propia del cuerpo — nunca se
  contagia el año de un hermano de lista.

ACORDADA: EL NÚMERO VIENE ESCRITO EN PALABRAS
-------------------------------------------------
Única muestra vista (Superior Tribunal de Justicia, Acordada N° 84):

    ACORDADA NÚMERO OCHENTA Y CUATRO: En la Ciudad de Posadas...

El número no sale en dígitos en el cuerpo. En vez de escribir un conversor
de números en letras para un solo caso confirmado, se resuelve por
POSICIÓN: se empareja cada "ACORDADA" encontrada en el cuerpo (en orden de
aparición) con las Acordadas que anuncia el SUMARIO (que sí trae el número
en dígitos), en el mismo orden. Si el cuerpo alguna vez trae el número en
dígitos directo ("ACORDADA N° 84:"), se usa ese sin pasar por el sumario.

LICITACIONES / SOCIEDADES / EDICTOS / SUBASTAS / CONVOCATORIAS — afuera
-----------------------------------------------------------------------------
Igual que en el resto de las provincias: avisos privados o llamados a
licitación, no normativa con Artículo 1º/2º. Todos caen dentro o después de
"SEGUNDA SECCIÓN", así que el corte en ese título ya los deja afuera sin
necesidad de nombrarlos uno por uno.

FLAGS
-----
    --dry-run         no envía nada
    --pdf ARCHIVO      usa un PDF local (pruebas)
    --texto ARCHIVO    usa un .txt con el texto YA EXTRAÍDO de tapa+cuerpo
                       (busca "PRIMERA SECCIÓN" para separar tapa/cuerpo;
                       sirve para probar sumario + cuerpo juntos sin bajar
                       ningún PDF)
    --fecha AAAA-MM-DD  busca esa fecha entre las tarjetas de la portada
                       (sólo cubre las últimas ediciones hábiles visibles)
    --numero N         pide `/boletines/N.pdf` directo (para reprocesar una
                       edición vieja de la que ya se consiguió el número a
                       mano); la fecha se lee de la propia tapa del PDF
    --todas            muestra también las individuales, con puntaje y motivos
    --sin-filtro       envía todo sin filtrar
    --volcar           imprime sumario/bloques encontrados y sale

===============================================================================
QUÉ FALTA VALIDAR
===============================================================================
1. LEY: ninguna de las 5 muestras trajo una Ley publicada (sólo citas a
   leyes ya existentes dentro de considerandos, en Title Case, que el
   parser ignora a propósito). El código soporta el tipo (encabezado "LEY
   N° X", emisor PODER LEGISLATIVO) pero sin muestra real que lo confirme.
2. Acto individual (designación, renuncia, cesantía, etc.): ninguna de las
   30+ normas de las 5 muestras es de alcance individual — son
   reasignaciones presupuestarias, una fijación de Unidad Tributaria
   municipal, escalas salariales, viabilidad ambiental de una obra, un
   llamado a concurso interno y una acordada de procedimiento. El
   clasificador reutiliza los mismos patrones que el resto de las
   provincias (mismo idioma administrativo) pero no se pudo calibrar con un
   caso real de Misiones.
3. Columnas en el PDF: se descartó la trampa de La Rioja en base al TEXTO
   que devolvió `web_fetch` sobre los 5 PDFs reales (se leyeron artículos
   completos sin cortes a mitad de oración), no corriendo `pdfplumber`
   directamente acá (sin salida de red al dominio desde este sandbox). Si
   en producción aparece un artículo roto a la mitad, es la señal de que
   hace falta portar `texto_de_pagina()` de La Rioja.
4. Ruido intercalado más allá de "EXPEDIENTES A SENTENCIA" / "COMUNICADO DE
   PRENSA": son los dos únicos tipos vistos en 5 muestras. Si aparece un
   tercer tipo de aviso no-normativo intercalado en Primera Sección y no
   está en `RUIDO_TITULOS`, su texto se pegaría como cola de la norma
   anterior en vez de cortarse — no rompe el envío, ensucia `texto_completo`.
5. `--fecha` más allá de la última semana hábil: la portada sólo expone 5
   tarjetas; "VER MÁS" y "CALENDARIO" son botones ICEfaces con ViewState
   (no reproducibles con `requests` simple). Para backfill más viejo hay que
   conseguir el número de boletín a mano y usar `--numero`.
6. El patrón "16643 firmado.pdf" (con espacio) para la edición del día: se
   vio una sola vez (30/07/2026). No se sabe si es porque esa edición
   todavía no se había archivado del todo, si el espacio desaparece al otro
   día, o si es un caso aislado. No importa para el flujo normal (siempre
   se usa el href tal cual lo da la tarjeta, nunca se reconstruye), pero si
   `--numero` apunta a la edición de HOY podría fallar por este motivo.
===============================================================================
"""

import os
import re
import sys
import json
import time
import argparse
import unicodedata
from datetime import date, datetime

import requests

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

SITIO = 'https://www.boletindigital.misiones.gov.ar'
URL_HOME = f'{SITIO}/'

HEADERS_WEB = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/pdf;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
}

REINTENTOS = 3
ESPERA_REINTENTO = 3
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700

MESES_NUM = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'setiembre': 9, 'octubre': 10,
    'noviembre': 11, 'diciembre': 12,
}

# Títulos de sección conocidos (para no confundirlos con una línea de
# organismo al buscar el emisor hacia atrás del encabezado).
SECCIONES_CONOCIDAS = {
    'DECRETOS SINTETIZADOS', 'DECRETOS COMPLETOS', 'DECRETO COMPLETO',
    'DECRETO SINTETIZADO', 'RESOLUCIONES', 'DISPOSICIONES', 'MUNICIPALIDADES',
    'LEYES', 'ACORDADAS', 'PRIMERA SECCIÓN', 'SEGUNDA SECCIÓN', 'SUMARIO',
}

# Títulos de bloques SIN articulado (no son normativa) que pueden aparecer
# INTERCALADOS dentro de la Primera Sección, entre normas reales. Ver
# docstring: "EL SUMARIO NO ES UN TECHO ÚNICO".
RUIDO_TITULOS = ['EXPEDIENTES A SENTENCIA', 'COMUNICADO DE PRENSA']


# ===========================================================================
# NORMALIZACIÓN
# ===========================================================================
def _sin_acentos(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def _compacto(texto):
    return re.sub(r'\s+', ' ', (texto or '')).strip()


def _limpiar_numero(num):
    """'2129' -> '2129'; '23/26-AM' (ya recortado a '23') -> '23';
    '1.088' -> '1088' (punto de miles). El llamador ya debe haber cortado
    cualquier sufijo de año/oficina antes de pasar acá."""
    if num is None:
        return ''
    n = str(num).strip(' .')
    m = re.fullmatch(r'(\d{1,3})\.(\d{3})', n)
    if m:
        n = m.group(1) + m.group(2)
    n = re.sub(r'[^\d]', '', n)
    return n.lstrip('0') or ('0' if n else '')


def _fecha_iso(dia, mes_nombre, anio):
    mes = MESES_NUM.get(_sin_acentos((mes_nombre or '').lower()))
    if not mes:
        return None
    try:
        return date(int(anio), mes, int(dia)).isoformat()
    except (ValueError, TypeError):
        return None


def _patron_espaciado(palabra):
    """ 'RESUELVE' -> tolera tanto 'RESUELVE' como 'R E S U E L V E'.
    Confirmado contra el PDF real: la fórmula resolutiva de Resoluciones y
    Disposiciones a veces sale con las letras separadas por espacio cuando
    está sola en su renglón (ver docstring). `[ \\t]*` matchea también con
    cero espacios, así que un solo patrón cubre ambas formas sin duplicar
    nada ni arriesgar falsos positivos nuevos."""
    return r'[ \t]*'.join(re.escape(c) for c in palabra)


# ===========================================================================
# LECTURA DEL PDF
# ===========================================================================
RE_ENCABEZADO_PAGINA = re.compile(
    r'^(?:P[áa]g\.\s*\d+\s+BOLET[ÍI]N OFICIAL[^\n]*'
    r'|[^\n]*BOLET[ÍI]N OFICIAL\s*N[ºo°]?\s*\d+\s*P[áa]g\.\s*\d+)\s*$',
    re.MULTILINE)


def leer_paginas(ruta_pdf):
    """[texto_tapa, texto_pag2, texto_pag3, ...]. No se vio trampa de
    columnas en las 5 muestras (ver docstring) así que se usa
    `extract_text()` liso; sólo se le saca el renglón de encabezado
    repetido de cada página del cuerpo (cosmético, no afecta el parseo)."""
    if pdfplumber is None:
        raise RuntimeError("Falta pdfplumber: pip install pdfplumber")
    paginas = []
    with pdfplumber.open(ruta_pdf) as pdf:
        for i, page in enumerate(pdf.pages):
            texto = page.extract_text() or ''
            if i > 0:
                texto = RE_ENCABEZADO_PAGINA.sub('', texto)
            paginas.append(texto)
    return paginas


# ===========================================================================
# METADATOS DE TAPA
# ===========================================================================
RE_TAPA_METADATOS = re.compile(
    r'A[ÑN]O\s+[IVXLCDM]+\s+N[ºo°]\s*(?P<numero>[\d.]+)\s+\w+,\s*\w+\s+'
    r'(?P<dia>\d{1,2})\s+DE\s+(?P<mes>[A-ZÁÉÍÓÚÑ]+)\s+DE\s+(?P<anio>\d{4})'
    r'\s+EDICI[ÓO]N\s+DE\s+(?P<paginas>\d+)\s+P[ÁA]GINAS',
    re.IGNORECASE)


def metadatos_tapa(texto_tapa):
    m = RE_TAPA_METADATOS.search(texto_tapa or '')
    if not m:
        return None, None
    fecha = _fecha_iso(m.group('dia'), m.group('mes'), m.group('anio'))
    return fecha, _limpiar_numero(m.group('numero'))


# ===========================================================================
# SUMARIO (el oráculo de cobertura)
# ===========================================================================
# El sumario está en Title Case ("Decretos Sintetizados"), a diferencia de
# los encabezados del cuerpo (mayúsculas completas) — por eso este regex sí
# lleva IGNORECASE, y los del cuerpo (más abajo) no.
RE_SUMARIO_ITEM = re.compile(
    r'(?P<tipo>Decretos?|Resoluciones|Resoluci[óo]n|Disposiciones|Disposici[óo]n|Leyes|Ley|Acordadas?)'
    r'[^\d]{0,50}?'  # Saltea hasta 50 caracteres no numéricos
    r'(?P<lista>\d+(?:[\d.,\s\ty/\-]*?\d(?:/\d{2,4})?)?)' # Atrapa la lista de números
    r'(?=\s*(?:[.\-_]{2,}|…|P[áa]g|\n|$))', # Frena en puntos, guiones, "Pág" o final de línea
    re.IGNORECASE)

def _tipo_normalizado(crudo):
    t = _sin_acentos((crudo or '').upper())
    if t.startswith('DECRET'):
        return 'DECRETO'
    if t.startswith('RESOLUC'):
        return 'RESOLUCION'
    if t.startswith('DISPOSIC'):
        return 'DISPOSICION'
    if t.startswith('LEY'):
        return 'LEY'
    if t.startswith('ACORDAD'):
        return 'ACORDADA'
    return t


def _partir_lista_numeros(lista_cruda):
    """
    '2129, 2137, 2138 y 2139/25' -> [('2129',None),('2137',None),('2138',None),('2139','2025')]
    '1826, 1867, 1869/25, 171, 175, 215' -> el /25 sólo se aplica a 1869,
    NUNCA se contagia a los demás números de la lista (confirmado con esta
    muestra real: el sufijo puede estar pegado a un número del medio, no
    siempre al último — ver docstring).
    """
    if not lista_cruda:
        return []
    partes = re.split(r'\s*,\s*|\s+y\s+', lista_cruda.strip())
    resultado = []
    for p in partes:
        p = p.strip(' .\n')
        if not p:
            continue
        anio = None
        m = re.search(r'/\s*(\d{2,4})\s*(?:-[A-Za-zÁÉÍÓÚÑáéíóúñ]+)?\s*$', p)
        if m:
            a = m.group(1)
            anio = ('20' + a) if len(a) == 2 else a
            p = p[:m.start()]
        numero = _limpiar_numero(p)
        if numero:
            resultado.append((numero, anio))
    return resultado


def parsear_sumario(texto_tapa):
    """[{'tipo','numero','anio'}] tal como los anuncia el SUMARIO de tapa."""
    # A veces pdfplumber lee "SUMARIO" de forma extraña. Si no lo encuentra, 
    # forzamos a escanear toda la primera página desde el principio (idx1 = 0).
    idx1 = texto_tapa.rfind('SUMARIO')
    if idx1 == -1:
        idx1 = 0
    
    m_fin = re.search(r'P[áa]g\.\s*\d+\s*BOLET[ÍI]N', texto_tapa[idx1:], re.IGNORECASE)
    fin = idx1 + m_fin.start() if m_fin else len(texto_tapa)
    bloque = texto_tapa[idx1:fin]

    esperadas = []
    for m in RE_SUMARIO_ITEM.finditer(bloque):
        tipo = _tipo_normalizado(m.group('tipo'))
        for numero, anio in _partir_lista_numeros(m.group('lista')):
            esperadas.append({'tipo': tipo, 'numero': numero, 'anio': anio})
    
    return esperadas


# ===========================================================================
# ENCABEZADOS DEL CUERPO
# ===========================================================================
# Case-sensitive a propósito (sin IGNORECASE): los encabezados reales están
# SIEMPRE en mayúsculas completas; las citas a otras normas dentro de la
# prosa de un considerando aparecen en Title Case ("de la Ley VII - N° 11")
# y así no matchean por accidente.
RE_CABECERA = re.compile(
    r'^[ \t]*(?P<tipo>LEY|DECRETO|RESOLUCI[ÓO]N|DISPOSICI[ÓO]N)\s+'
    r'N[º°]\.?\s*'
    r'(?P<numero>\d[\d.]*)'
    r'(?:\s*/\s*\d{2,4})?'
    r'(?:\s*-\s*[A-ZÁÉÍÓÚÑ]{1,8})?'
    r'[ \t]*$',
    re.MULTILINE)

# La Acordada NO sale sola en su renglón: arranca un párrafo directo
# ("ACORDADA NÚMERO OCHENTA Y CUATRO: En la Ciudad de Posadas..."). El
# número puede venir en dígitos (no visto, pero soportado por las dudas) o
# en palabras (el único caso real visto) — si viene en palabras se resuelve
# después por posición contra el sumario, ver `resolver_numeros_acordada`.
RE_ACORDADA = re.compile(
    r'^[ \t]*ACORDADA\s+(?:N[º°]\.?\s*(?P<numero>\d[\d.]*)|N[ÚU]MERO\s+[A-ZÁÉÍÓÚÑ\s]+?)\s*:',
    re.MULTILINE)

RE_SEGUNDA_SECCION = re.compile(r'^[ \t]*SEGUNDA SECCI[ÓO]N[ \t]*$', re.MULTILINE)

RE_RUIDO = re.compile(
    r'^[ \t]*(?:' + '|'.join(re.escape(t) for t in RUIDO_TITULOS) + r')[ \t]*$',
    re.MULTILINE)

RE_FECHA_NORMA = re.compile(
    r'^[ \t]*[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{2,45}?,\s*(?:Misiones,\s*)?'
    r'(?P<dia>\d{1,2})\s+de\s+(?P<mes>[A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+de\s+'
    r'(?P<anio>\d\.?\d{3})',
    re.IGNORECASE | re.MULTILINE)


def cortar_en_segunda_seccion(cuerpo):
    m = RE_SEGUNDA_SECCION.search(cuerpo)
    if m:
        return cuerpo[:m.start()]
    print("Aviso: no se encontró 'SEGUNDA SECCIÓN' en el cuerpo; se usa el "
          "texto completo (riesgo de incluir Sociedades/Edictos/Convocatorias "
          "si el layout de esta edición cambió).", file=sys.stderr)
    return cuerpo


def encontrar_marcas(cuerpo):
    """[[inicio, fin_cabecera, tipo, numero], ...] de LEY/DECRETO/RESOLUCION/DISPOSICION."""
    marcas = []
    for m in RE_CABECERA.finditer(cuerpo):
        marcas.append([m.start(), m.end(), _tipo_normalizado(m.group('tipo')),
                       _limpiar_numero(m.group('numero'))])
    return marcas


def encontrar_acordadas(cuerpo):
    marcas = []
    for m in RE_ACORDADA.finditer(cuerpo):
        numero = m.group('numero')
        numero = _limpiar_numero(numero) if numero else None
        marcas.append([m.start(), m.end(), 'ACORDADA', numero])
    return marcas


def resolver_numeros_acordada(marcas_acordada, esperadas):
    """El cuerpo casi siempre trae el número de la Acordada escrito en
    palabras, no en dígitos (ver docstring). Se empareja por POSICIÓN con
    las Acordadas que anuncia el sumario, en el mismo orden de aparición."""
    pendientes = [e['numero'] for e in esperadas if e['tipo'] == 'ACORDADA']
    i = 0
    resueltas = []
    for marca in marcas_acordada:
        if marca[3]:
            resueltas.append(marca)
            continue
        if i < len(pendientes):
            marca[3] = pendientes[i]
            i += 1
            resueltas.append(marca)
        else:
            print("Aviso: se encontró una ACORDADA sin número en el cuerpo "
                  "y no quedaban Acordadas sin emparejar en el sumario; se "
                  "descarta (no se puede mandar sin número).", file=sys.stderr)
    return resueltas


# ===========================================================================
# SÍNTESIS
# ===========================================================================
_ART1 = (r'ART[ÍI]?CULO\s*(?:N[º°]\s*)?1(?!\d)\s*[º°]?\s*[.:,;-]+\s*'
         r'(?P<texto>[\s\S]{0,1200}?)(?=ART[ÍI]?CULO\s*(?:N[º°]\s*)?2(?!\d)|\Z)')
RE_ARTICULO1 = re.compile(_ART1, re.IGNORECASE)

# Las Acordadas no numeran "ARTÍCULO 1º/2º" sino "PRIMERO:"/"SEGUNDO:".
RE_PRIMERO = re.compile(
    r'\bPRIMERO\s*:\s*(?P<texto>[\s\S]{0,1200}?)(?=\bSEGUNDO\s*:|\Z)',
    re.IGNORECASE)


def _sintesis_de_bloque(bloque):
    m = RE_ARTICULO1.search(bloque)
    if m:
        return _compacto(m.group('texto'))
    m2 = RE_PRIMERO.search(bloque)
    if m2:
        return _compacto(m2.group('texto'))
    return _compacto(bloque[:400])


# ===========================================================================
# EMISOR
# ===========================================================================
def _es_linea_organismo(linea):
    t = linea.strip().rstrip(':').strip()
    if len(t) < 3 or t.upper() in SECCIONES_CONOCIDAS:
        return False
    letras = [c for c in t if c.isalpha()]
    if len(letras) < 3:
        return False
    return all(c == c.upper() for c in letras)


def _organismo_precedente(cuerpo, pos_header):
    """Junta las líneas en mayúsculas que anteceden directo al encabezado
    (p.ej. 'MINISTERIO DE INDUSTRIA' + 'DIRECCIÓN GENERAL DE MINAS Y
    GEOLOGÍA'), parando en la primera línea que sea un título de sección
    conocido, en blanco, o que ya no esté en mayúsculas."""
    antes = cuerpo[:pos_header]
    lineas = antes.split('\n')
    encontradas = []
    for linea in reversed(lineas[-8:]):
        if _es_linea_organismo(linea):
            encontradas.insert(0, linea.strip())
        elif encontradas:
            break
        elif linea.strip() != '':
            break
    return _compacto(' '.join(encontradas))


_RESOLUTIVO = '|'.join(_patron_espaciado(p) for p in ('DECRETA', 'RESUELVE', 'DISPONE'))
RE_CARGO = re.compile(
    r'^[ \t]*(?P<cargo>(?:EL|LA)\s+[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9.,;()\'"\s/e-]{5,120}?)'
    r':?\s*(?:\n\s*)?(?:' + _RESOLUTIVO + r')\s*:', re.MULTILINE)

_MAPA_CARGO_ORGANISMO = {
    'MINISTRO': 'MINISTERIO', 'MINISTRA': 'MINISTERIO',
    'SECRETARIO': 'SECRETARÍA', 'SECRETARIA': 'SECRETARÍA',
    'DIRECTOR': 'DIRECCIÓN', 'DIRECTORA': 'DIRECCIÓN',
    'SUBSECRETARIO': 'SUBSECRETARÍA', 'SUBSECRETARIA': 'SUBSECRETARÍA',
}


def _cargo_a_organismo(cargo):
    texto = _compacto(cargo).upper()
    for palabra, base in _MAPA_CARGO_ORGANISMO.items():
        if texto.startswith(palabra + ' ') or texto == palabra:
            return (base + ' ' + texto[len(palabra):].lstrip()).strip()
    return None


def emisor_de_norma(tipo, cuerpo, pos_header):
    if tipo == 'DECRETO':
        return 'PODER EJECUTIVO'
        
    organismo = _organismo_precedente(cuerpo, pos_header)
    if organismo:
        return organismo

    m = RE_CARGO.search(cuerpo[pos_header:pos_header + 4000])
    if m:
        cargo = _compacto(m.group('cargo')).strip(' .,-')
        cargo_sin_articulo = re.sub(r'^(EL|LA)\s+', '', cargo, flags=re.IGNORECASE).strip()
        org = _cargo_a_organismo(cargo_sin_articulo)
        if org:
            return org
        if cargo_sin_articulo:
            return cargo_sin_articulo.upper()

    if tipo == 'LEY':
        return 'PODER LEGISLATIVO'
    if tipo == 'ACORDADA':
        return 'SUPERIOR TRIBUNAL DE JUSTICIA'
    return 'PODER EJECUTIVO'


# ===========================================================================
# CLASIFICACIÓN INDIVIDUAL / GENERAL
# ===========================================================================
# Mismos patrones que el resto de las provincias (mismo idioma
# administrativo). Sin muestra real de acto individual en Misiones — ver
# "QUÉ FALTA VALIDAR".
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
    (r'\bLL[ÁA]MASE\s+a\s+Concurso\b',                        -2, 'llamado a concurso (proceso, no persona puntual)'),
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


# ===========================================================================
# ARMADO DE NORMAS
# ===========================================================================
def extraer_normas(cuerpo_primera_seccion, esperadas, fecha_boletin, anio_boletin):
    marcas = encontrar_marcas(cuerpo_primera_seccion)
    marcas_acordada = resolver_numeros_acordada(
        encontrar_acordadas(cuerpo_primera_seccion), esperadas)
    todas = sorted(marcas + marcas_acordada, key=lambda m: m[0])

    ruido = [m.start() for m in RE_RUIDO.finditer(cuerpo_primera_seccion)]
    cortes = sorted(set([m[0] for m in todas] + ruido + [len(cuerpo_primera_seccion)]))

    normas = []
    for (ini, fin_cab, tipo, numero) in todas:
        fin_bloque = next((c for c in cortes if c > fin_cab), len(cuerpo_primera_seccion))
        if fin_bloque <= fin_cab:
            continue
        bloque = cuerpo_primera_seccion[fin_cab:fin_bloque]
        if not bloque.strip():
            continue

        anio = None
        fecha_norma = fecha_boletin
        m_fecha = RE_FECHA_NORMA.search(bloque[:200])
        if m_fecha:
            anio_bruto = m_fecha.group('anio').replace('.', '')
            iso = _fecha_iso(m_fecha.group('dia'), m_fecha.group('mes'), anio_bruto)
            if iso:
                fecha_norma = iso
                anio = anio_bruto
        if not anio:
            for e in esperadas:
                if e['tipo'] == tipo and e['numero'] == numero and e.get('anio'):
                    anio = e['anio']
                    break
        if not anio:
            anio = str(anio_boletin)

        sintesis = _sintesis_de_bloque(bloque)
        normas.append({
            'tipo': tipo, 'numero': numero, 'anio': anio,
            'sintesis': sintesis, 'texto_completo': bloque,
            'fecha_publicacion': fecha_norma,
            'emisor': emisor_de_norma(tipo, cuerpo_primera_seccion, ini),
        })
    return normas


def comparar_con_sumario(esperadas, normas):
    """Compara sólo por número (no por tipo): el sumario ya trae el tipo
    explícito por ítem así que en general coincide, pero comparar sólo por
    número es más robusto igual (mismo criterio que el resto de los bots)."""
    extraidas = {n['numero'] for n in normas}
    return [e for e in esperadas if e['numero'] not in extraidas]


# ===========================================================================
# DESCUBRIMIENTO
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
            r = sesion().get(url, timeout=timeout)
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


RE_TARJETA = re.compile(
    r'Bolet.*?Nro:\s*(?P<numero>\d+)\s*<br\s*/?>\s*Del\s*'
    r'<span[^>]*>(?P<fecha>\d{2}/\d{2}/\d{4})</span>.*?'
    r'href="(?P<href>/boletines/[^"]+?\.pdf)"',
    re.IGNORECASE | re.DOTALL)


def _url_absoluta(href):
    href = href.strip()
    url = href if href.startswith('http') else SITIO + (href if href.startswith('/') else '/' + href)
    return url.replace(' ', '%20')


def _fecha_ddmmaaaa_a_iso(fecha):
    try:
        return datetime.strptime(fecha, '%d/%m/%Y').date().isoformat()
    except ValueError:
        return None


def listar_tarjetas_home():
    """[{'numero','fecha_iso','href','url'}, ...] de las tarjetas visibles
    en la portada, más nueva primero. Sólo cubre lo que la portada expone
    de entrada (últimas ediciones hábiles) — ver 'QUÉ FALTA VALIDAR' sobre
    VER MÁS / CALENDARIO."""
    html = descargar(URL_HOME)
    if not html:
        return []
    tarjetas = []
    for m in RE_TARJETA.finditer(html):
        fecha_iso = _fecha_ddmmaaaa_a_iso(m.group('fecha'))
        href = m.group('href')
        tarjetas.append({
            'numero': _limpiar_numero(m.group('numero')),
            'fecha_iso': fecha_iso,
            'href': href,
            'url': _url_absoluta(href),
        })
    return tarjetas


def buscar_ultimo_boletin():
    tarjetas = listar_tarjetas_home()
    return tarjetas[0] if tarjetas else None


def buscar_por_fecha_en_home(fecha_iso):
    tarjetas = listar_tarjetas_home()
    for t in tarjetas:
        if t['fecha_iso'] == fecha_iso:
            return t
    return None


def construir_url_por_numero(numero):
    return f'{SITIO}/boletines/{numero}.pdf'


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


def url_norma(url_pdf, norma):
    base = f"{norma.get('tipo')}-{norma.get('numero')}-{norma.get('anio')}"
    slug = re.sub(r'[^A-Za-z0-9]+', '-', _sin_acentos(base)).strip('-')
    return f"{url_pdf}#{slug}"


# ===========================================================================
# EJECUCIÓN
# ===========================================================================
def _main():
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Misiones.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se descubre por la portada')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--pdf', metavar='ARCHIVO', help='usar un PDF local (pruebas)')
    ap.add_argument('--texto', metavar='ARCHIVO',
                    help='usar un .txt con tapa+cuerpo ya extraído (busca "PRIMERA '
                         'SECCIÓN" para separar; prueba sumario + cuerpo sin bajar PDF)')
    ap.add_argument('--fecha', metavar='AAAA-MM-DD',
                    help='busca esa fecha entre las tarjetas de la portada (rango limitado)')
    ap.add_argument('--numero', metavar='N', help='pide /boletines/N.pdf directo')
    ap.add_argument('--todas', action='store_true',
                    help='muestra también las individuales, con puntaje y motivos')
    ap.add_argument('--sin-filtro', action='store_true', help='envía todo sin filtrar')
    ap.add_argument('--volcar', action='store_true', help='imprime sumario y bloques y sale')
    args = ap.parse_args()

    anio_boletin = date.today().year
    fecha_boletin = args.fecha
    numero_edicion = None
    url_pdf = ''
    texto_tapa = ''
    ruta_temporal = None
    paginas = None

    # ---- 1. Conseguir el boletín -------------------------------------------
    if args.texto:
        with open(args.texto, encoding='utf-8') as f:
            contenido = f.read()
        idx = contenido.find('PRIMERA SECCIÓN')
        if idx == -1:
            paginas = [contenido, '']
            print("Aviso: no se encontró 'PRIMERA SECCIÓN' en el .txt; se usa "
                  "todo como cuerpo sin tapa (sin oráculo de sumario).", file=sys.stderr)
        else:
            paginas = [contenido[:idx], contenido[idx:]]
        print(f"Usando texto local: {args.texto}", file=sys.stderr)
    elif args.pdf:
        ruta_pdf = args.pdf
        print(f"Usando PDF local: {args.pdf}", file=sys.stderr)
    elif args.numero:
        url_pdf = construir_url_por_numero(args.numero)
        print(f"Pidiendo boletín Nº {args.numero} directo: {url_pdf}", file=sys.stderr)
        contenido = descargar(url_pdf, timeout=90, esperar_pdf=True)
        if not contenido:
            salida("warning", f"No se pudo descargar {url_pdf}.")
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.write(contenido)
        tmp.close()
        ruta_pdf = ruta_temporal = tmp.name
    else:
        if fecha_boletin:
            tarjeta = buscar_por_fecha_en_home(fecha_boletin)
            if not tarjeta:
                salida("warning", f"La fecha {fecha_boletin} no está entre las ediciones "
                                  f"que expone la portada ahora mismo. Para una fecha más "
                                  f"vieja, conseguí el número de boletín a mano y usá --numero.")
        else:
            tarjeta = buscar_ultimo_boletin()
            if not tarjeta:
                salida("warning", "No se pudo leer la portada del Boletín Digital de Misiones.")

        fecha_boletin = tarjeta['fecha_iso']
        url_pdf = tarjeta['url']
        print(f"Boletín Nº {tarjeta['numero']} del {fecha_boletin}: {url_pdf}", file=sys.stderr)

        contenido = descargar(url_pdf, timeout=90, esperar_pdf=True)
        if not contenido:
            salida("warning", f"No se pudo descargar el PDF de {url_pdf}.")
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.write(contenido)
        tmp.close()
        ruta_pdf = ruta_temporal = tmp.name

    # ---- 2. Parsear -----------------------------------------------------------
    try:
        if paginas is None:
            paginas = leer_paginas(ruta_pdf)
        texto_tapa = paginas[0]
        fecha_tapa, num_tapa = metadatos_tapa(texto_tapa)
        fecha_boletin = fecha_boletin or fecha_tapa
        numero_edicion = num_tapa
        anio_boletin = int((fecha_boletin or '')[:4] or anio_boletin)

        cuerpo_completo = '\n'.join(paginas[1:])
        cuerpo_primera_seccion = cortar_en_segunda_seccion(cuerpo_completo)

        esperadas = parsear_sumario(texto_tapa)
        normas = extraer_normas(cuerpo_primera_seccion, esperadas, fecha_boletin, anio_boletin)
    except Exception as e:
        salida("error", f"No se pudo parsear el boletín: {e}")
    finally:
        if ruta_temporal:
            try:
                os.unlink(ruta_temporal)
            except Exception:
                pass

    faltantes = comparar_con_sumario(esperadas, normas)
    print(f"Sumario de tapa: anuncia {len(esperadas)} normas, se extrajeron "
          f"{len(normas)} ({len(faltantes)} faltantes)", file=sys.stderr)
    for f in faltantes[:15]:
        print(f"  FALTA  {f['tipo']} {f['numero']}", file=sys.stderr)

    if args.volcar:
        print(f"--- PDF: {len(paginas)} páginas | edición Nº {numero_edicion} | "
              f"fecha {fecha_boletin} ---", file=sys.stderr)
        print(f"--- {len(esperadas)} normas anunciadas por el sumario ---", file=sys.stderr)
        for e in esperadas:
            print(f"  {e['tipo']:12s} {e['numero']:>8s}  año={e.get('anio')}", file=sys.stderr)
        print(f"--- {len(normas)} normas extraídas ---", file=sys.stderr)
        for n in normas:
            print(f"  {n['tipo']:12s} {n['numero']:>8s}/{n['anio']} "
                  f"{len(n['texto_completo']):6d} car. | {n['emisor'][:35]:35s} | "
                  f"{n['sintesis'][:50]}", file=sys.stderr)
        salida("success", f"volcado: {len(esperadas)} anunciadas, {len(normas)} extraídas.")

    for n in normas:
        n['es_individual'], n['puntaje'], n['motivos'] = clasificar_norma(
            n['tipo'], n['sintesis'], n['texto_completo'])

    generales = [n for n in normas if not n['es_individual']]
    individuales = [n for n in normas if n['es_individual']]
    a_enviar = normas if args.sin_filtro else generales

    guardar_debug(json.dumps(normas, ensure_ascii=False, indent=2, default=str), 'debug_misiones.json')
    print(f"Boletín del {fecha_boletin} (Nº {numero_edicion}) | normas: {len(normas)} "
          f"(generales {len(generales)} / individuales {len(individuales)})", file=sys.stderr)

    if args.dry_run:
        for n in (normas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {n['tipo']:12s} N° {n['numero']:>8s}/{n['anio']} "
                  f"{n['emisor'][:35]:35s} {n['sintesis'][:55]}", file=sys.stderr)
            if args.todas and n.get('motivos'):
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    if fecha_boletin and verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

    if not normas:
        if esperadas:
            salida("warning", f"El sumario de tapa anuncia {len(esperadas)} normas pero "
                              f"no se reconoció ninguna en el cuerpo del boletín "
                              f"({fecha_boletin}). Revisar el parser.")
        if fecha_boletin:
            registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Sin novedades: el boletín del {fecha_boletin} no publicó "
                          f"Leyes, Decretos, Resoluciones, Disposiciones ni Acordadas.", total=0)

    if not a_enviar:
        if fecha_boletin:
            registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Se procesó el boletín del {fecha_boletin}, pero las "
                          f"{len(individuales)} normas encontradas son actos "
                          f"individuales; no se envió ninguna.", total=0)

    # ---- 3. Envío -----------------------------------------------------------
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

    mensaje = respuesta.get('mensaje', 'OK') or 'OK'
    extra = None
    if faltantes:
        detalle = ', '.join(f"{f['tipo']} {f['numero']}" for f in faltantes[:10])
        extra = {
            "advertencia": f"El sumario de tapa anuncia {len(faltantes)} normas que no se extrajeron: {detalle}",
            "faltantes_sumario": len(faltantes),
        }
        print("ADVERTENCIA: " + extra["advertencia"], file=sys.stderr)

    salida("success", mensaje, total=len(payload), extra=extra)


if __name__ == '__main__':
    try:
        _main()
    except SystemExit:
        raise
    except Exception as e:
        salida("error", str(e))