#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
 BOLETÍN OFICIAL E IMPRENTA DE LA PROVINCIA DE SANTA CRUZ  —  id_jurisdiccion 21
===============================================================================

ADVERTENCIA GENERAL — CONFIANZA MIXTA SEGÚN LA PARTE DEL BOT
-------------------------------------------------------------------------------
El usuario mandó HTML crudo (Ctrl+U / view-source) de DOS páginas reales: la
portada /legislacion y la página individual del Decreto N° 0624/2026
(/legislacion/decretos-sintetizados/58460). Eso confirmó con certeza las
clases K2 estándar del template de norma — .itemHeader, .itemTitle,
.itemIntroText, .itemFullText — y el parser (_extraer_k2) las usa
directamente vía selectores CSS, igual que San Luis. Es el camino PRIMARIO.
El resto del reconocimiento — página de tag de una edición, paginado, y el
contenido de las otras 4 normas usadas para validar emisor/marca
resolutiva/numeración de artículo — se hizo con mcp__workspace__web_fetch
(HTML ya convertido a texto, sin clases CSS), así que ese texto se usó para
un camino de RESPALDO basado en patrones de texto plano (_extraer_texto_plano,
ya validado con 5 fixtures), que sólo se activa si una página no trae las
clases K2 esperadas (por ejemplo si alguna categoría nunca vista —
Leyes/Acuerdos/Declaraciones/Decretos Completos— usa una plantilla distinta).
Sigue habiendo menos certeza que San Luis en dos puntos puntuales: el
paginado de la página de tag y las categorías sin ningún ejemplo real — ver
"QUÉ FALTA VALIDAR" al final.

SITIO Y ARQUITECTURA — MUY DISTINTA AL RESTO DE LA FAMILIA
-------------------------------------------------------------------------------
No hay "un boletín = un documento". El sitio es Joomla + K2, y cada norma es
su propio ítem/artículo, publicado en una de estas categorías (confirmado
real, están en el menú "Legislación" y cada una tiene su propia URL):

  /legislacion/leyes                      -> LEY
  /legislacion/decretos-completos         -> DECRETO (texto íntegro)
  /legislacion/decretos-sintetizados      -> DECRETO (ver más abajo)
  /legislacion/resoluciones-completas     -> RESOLUCION
  /legislacion/resoluciones-sintetizadas  -> RESOLUCION
  /legislacion/declaraciones              -> DECLARACION
  /legislacion/acuerdos                   -> ACUERDO
  /legislacion/disposiciones-completas    -> DISPOSICION
  /legislacion/disposiciones-sintetizadas -> DISPOSICION

"Completos" vs "Sintetizados" NO son dos versiones de las MISMAS normas —
son conjuntos disjuntos confirmados reales (comparé los números de
"Resoluciones Completas" contra "Resoluciones Sintetizadas" de la misma
edición: I.D.U.V. y N°301-E-/SANTACRUZ-PCAP sólo aparecen en Sintetizadas;
H.C.D. y M.P.C.eI. sólo en Completas). Cada emisor/trámite parece ir siempre
por el mismo canal. Y pese al nombre, "Sintetizados" NO significa que falte
el texto completo en la página de la norma — el único Decreto Sintetizado
que se pudo ver entero (0624/2026) tenía el texto íntegro del articulado,
sólo que sin el preámbulo VISTO/CONSIDERANDO/"decreta" ceremonial (ver más
abajo). Este bot trata "Completos" y "Sintetizados" de un mismo tipo como
la MISMA fuente de normativa (mismo tipo_norma_desc), simplemente hay que
mirar las dos categorías para no perderse la mitad.

Además de Legislación, el mismo sitio tiene Avisos Oficiales, Sociedades y
Avisos Judiciales, y Contrataciones (edictos, avisos, licitaciones, etc.) —
confirmado real que comparten el mismo esquema de "edición" (tag "BO NNNN")
que Legislación, pero NO son normativa del Estado, son avisos de terceros o
trámites administrativos sin valor normativo. Se descartan por completo
filtrando por URL: sólo interesan links que empiecen con "/legislacion/".

DESCUBRIMIENTO DE LA EDICIÓN — MECANISMO "BO NNNN", NO FECHA NI NÚMERO DE PDF
-------------------------------------------------------------------------------
Confirmado real: la portada /legislacion (y de hecho CUALQUIER página del
sitio) trae en la barra lateral un bloque fijo:

  <span class="moduleItemDateCreated">Edición del 30 Julio 2026</span>
  <div class="moduleItemTags text-center">
      <a href="/legislacion/tag/BO%206140">BO 6140</a>
  </div>

Éste SÍ se leyó en HTML crudo (viene en santacruz.html, no por web_fetch),
así que el selector `.moduleItemTags a` está confirmado real. De ahí sale
el número de "Boletín Oficial" vigente (6140) — el resto del descubrimiento
consiste en enumerar todas las normas etiquetadas con ese número.

TODAS las normas (de TODAS las secciones, no sólo Legislación) publicadas en
una edición comparten el tag "BO NNNN" — confirmado real navegando
https://boletinoficial.santacruz.gob.ar/legislacion/tag/BO%206140: la
primera página trae Edictos/Avisos/Convocatorias (no interesan), y el sitio
avisa "Página 1 de 6" (10 ítems por página, ~60 en total para BO 6140,
mezclando todas las secciones). _items_de_edicion pagina hasta el final
usando el "Página X de Y" que el propio sitio informa, y descarta todo lo
que no sea link a "/legislacion/...".

DATO IMPORTANTE: el tag de una norma puede NO coincidir con la fecha en la
que aparece en un listado "recientes". Confirmado real: la portada
/legislacion trae un widget de "últimas normas" que mezcla ediciones
distintas (se vieron ítems reales fechados 28, 29 y 30 de julio 2026 todos
juntos ahí), pero cada norma, dentro de su propia página, trae su BO real
en una línea "CATEGORÍA / publicado el FECHA / BO NNNN" — por ejemplo el
Decreto 0624/2026 aparecía en ese listado de portada pero su BO real es
6138, no 6140. Por eso este bot NO usa ese listado de portada para nada:
sólo lo usa (indirectamente, vía el mismo bloque lateral) para encontrar el
NÚMERO de la última edición, y de ahí en más todo sale de la página de tag
de ESE número puntual.

Otro dato real: la home redirige a una página con el listado de "el mes
actual" (como San Luis), pero para Santa Cruz no hace falta lidiar con eso
para nada — el widget "Edición del ... / BO NNNN" da directo el número de
la ÚLTIMA edición sin importar en qué mes estemos parado.

ESTRUCTURA DE LA PÁGINA DE UNA NORMA — CONFIRMADA REAL EN 5 EJEMPLOS
-------------------------------------------------------------------------------
Se leyeron enteras (vía web_fetch, texto real, no inventado):
  - DECRETO N° 0624/2026 (Sintetizado, MSA, BO 6138)
  - RESOLUCIÓN H.C.D.-N° 0141/2026 (Completa, BO 6138)
  - DISPOSICIÓN E.M.G.-N° 02/2026 (Completa, BO 6140)
  - DISPOSICIÓN M.E.yM./S.E.R.H.-N° 00032/2026 (Completa, BO 6140)
  - DISPOSICIÓN M.P.C.eI./S.E.P.yA.-N° 0118/2026 - P1/3 (Completa, BO 6140)

Las 5 comparten exactamente esta forma (texto plano de la página):

  {CATEGORÍA} / publicado el {fecha} / BO {número}
  {TIPO} [SIGLA-]N° {número}[/{año}][ - P{n}/{m}]      <- título (1a vez)
  {SÍNTESIS EN UNA LÍNEA, MAYÚSCULA-CON-GUIONES}       <- newsintro
  **{TIPO} N° {número}**                               <- título (repetido, en negrita)
  RÍO GALLEGOS, {fecha en palabras}.-
  [V I S T O : ... CONSIDERANDO: ... POR ELLO:]        <- sólo en las "Completas" vistas
  {LÍNEA DEL FUNCIONARIO/ORGANISMO A CARGO}
  {VERBO ESPACIADO EN LETRAS} :                        <- "D I S P O N E :", "R E S U E L V E :"
  {ARTICULADO}                                         <- 3 convenciones de numeración distintas, ver abajo
  {FIRMA: nombre, cargo, [Ministerio], Provincia de Santa Cruz}

CONFIRMADO CON HTML CRUDO (Decreto 0624/2026, /legislacion/decretos-
sintetizados/58460): el contenedor de cada bloque es una clase K2 estándar,
no hace falta adivinarla por texto:
  <div class="itemHeader">      CATEGORÍA / publicado el FECHA / BO NNNN
  <h2 class="itemTitle">        TIPO [SIGLA-]N° número[/año]
  <div class="itemIntroText">   síntesis (== "newsintro" de la portada)
  <div class="itemFullText">    cuerpo completo, como una serie de <div
                                 style="text-align:..."> hermanos, uno por
                                 párrafo (NO son <p>) — _lineas_de usa
                                 exactamente esos hijos directos como líneas.
El bloque "AUTORIDADES" estático vive en un <tfoot id="pie"> aparte,
estructuralmente FUERA de .itemFullText — con el selector puesto, en
principio ni hace falta recortarlo (_recortar_cuerpo se deja igual como red
de seguridad, por si algún otro template lo mete adentro).
_extraer_k2 usa estas 4 clases directamente; si faltan (plantilla de
categoría distinta a la vista) se cae a _extraer_texto_plano, el diseño
original con los patrones de texto de abajo.

Puntos importantes confirmados (por texto, vía web_fetch, en 5 normas):
  - El VERBO de la marca resolutiva viene con espacios entre cada letra
    ("D I S P O N E :", "R E S U E L V E :") — probablemente por una clase
    CSS de letter-spacing en el original. _buscar_marca_resolutiva lo
    detecta juntando corridas de letras sueltas separadas por espacios y
    comparando contra una lista de verbos conocidos, no con el patrón
    exacto de espaciado (por si el espaciado varía).
  - La numeración del articulado NO es uniforme — se vieron 3 formas reales
    distintas en 3 normas distintas: "Artículo 1°.- RECHAZAR..." (con la
    palabra completa, H.C.D.), "1°) RENOVAR..." (con paréntesis, S.E.R.H.),
    "1°.- CONCLUIR..." (con guion, sin la palabra "Artículo", S.E.P.yA.).
    Por esto este bot NO intenta extraer "Artículo 1" como hacen
    bot_sanjuan.py/bot_sanluis.py — sería frágil con 3 convenciones
    distintas conviviendo. En cambio usa DIRECTAMENTE la síntesis de una
    sola línea que ya trae la página (el "newsintro"), que es un resumen
    ya redactado por la Dirección del Boletín y está SIEMPRE presente,
    sea cual sea la convención de numeración del cuerpo.
  - El Decreto Sintetizado visto (0624/2026) NO tuvo NINGÚN VISTO/
    CONSIDERANDO/marca resolutiva — pasó directo de "Expediente
    MSA-N°990.898/25.-" a las cláusulas operativas ("EXCEPTÚASE...",
    "AUTORÍZASE...", "FACÚLTASE..."). No se pudo confirmar si esto es la
    norma general de "Decretos Sintetizados" o un caso puntual — sólo hay
    1 ejemplo real. _buscar_marca_resolutiva simplemente no encuentra nada
    en ese caso y el bot cae al siguiente método de emisor (ver abajo).
  - "Decretos Completos" y "Leyes"/"Acuerdos"/"Declaraciones" no tuvieron
    NINGÚN ítem real disponible para inspeccionar (las 3 categorías
    devolvían "Sin datos" al momento de este reconocimiento) — se mapean
    igual "por las dudas", sin confirmación real de su estructura interna.
  - Bloque de firma real, 2 formas vistas: "**NOMBRE**  Cargo  Provincia de
    Santa Cruz" (2 líneas) y "**NOMBRE**  Cargo  Ministerio de X  Provincia
    de Santa Cruz" (3 líneas) — siempre termina con "Provincia de Santa
    Cruz", que se usa como límite defensivo adicional del cuerpo.
  - Después del bloque de firma de LA norma, todas las páginas repiten un
    bloque ESTÁTICO de autoridades vigentes ("AUTORIDADES / Gobernador |
    Claudio VIDAL / Ministra Secretaría General de la Gobernación | ...")
    que NO tiene nada que ver con la norma puntual — es el mismo en las 5
    páginas vistas. _recortar_cuerpo corta ahí (por la palabra
    "AUTORIDADES") para no arrastrarlo como si fuera parte del texto.

EMISOR — MISMA IDEA QUE SAN LUIS, AHORA SOBRE LÍNEAS/PÁRRAFO REALES
-------------------------------------------------------------------------------
Confirmado real en 4 de las 5 normas (todas menos el Decreto): la línea
INMEDIATAMENTE antes de la marca resolutiva nombra al funcionario/organismo
a cargo — "El Poder Legislativo de la Provincia de Santa Cruz" (H.C.D.),
"LA ESCRIBANA MAYOR DE GOBIERNO DE LA PROVINCIA DE SANTA CRUZ" (E.M.G.),
"EL SECRETARIO DE ESTADO DE RECURSOS HÍDRICOS" (S.E.R.H.), "EL SECRETARIO
DE ESTADO DE PESCA Y ACUICULTURA" (S.E.P.yA.) — y en los 4 casos coincide
con lo que dice después el bloque de firma. _emisor_desde_lineas toma esa
línea, recorriendo los párrafos de .itemFullText uno por uno (o, si viene
del camino de respaldo de texto plano, tratando todo el cuerpo como una
sola "línea" con una ventana acotada a 120 caracteres). No se pudo
confirmar con HTML crudo si en Disposiciones/Resoluciones el nombre del
funcionario comparte <div> con el verbo espaciado o está en un <div>
propio — _emisor_desde_lineas cubre ambos casos. Si no aparece (como en el
único Decreto visto), se cae a:
  1. Un campo "JURISDICCIÓN: {ministerio}" que trae el cuerpo del Decreto
     (confirmado real, 1 sólo ejemplo: "JURISDICCIÓN: Ministerio de Salud y
     Ambiente"). RE_JURISDICCION es best-effort, no revalidado.
  2. La sigla del título (lo que va entre el tipo y "N°", ej. "M.P.C.eI./
     S.E.P.yA.") contra un diccionario chico de siglas CONFIRMADAS reales
     por aparecer explícitas en los bloques de firma ya vistos: H.C.D. =
     Honorable Cámara de Diputados, E.M.G. = Escribanía Mayor de Gobierno,
     M.P.C.eI. = Ministerio de la Producción, Comercio e Industria, M.E.yM.
     = Ministerio de Energía y Minería, S.E.R.H. = Secretaría de Estado de
     Recursos Hídricos, S.E.P.yA. = Secretaría de Estado de Pesca y
     Acuicultura, M.S.A. = Ministerio de Salud y Ambiente. El resto de
     siglas que aparecieron en los listados (M.E.F.I., I.D.U.V., S.E.T.,
     SGG, etc.) NO se pudieron confirmar contra un bloque de firma real,
     así que no están en el diccionario — si aparecen, el bot usa la
     sigla cruda como emisor (igual que San Juan/San Luis con siglas
     desconocidas).
  3. Si es un DECRETO y nada de lo anterior dio resultado: "GOBERNADOR DE
     LA PROVINCIA" — es quien constitucionalmente firma todo Decreto en
     cualquier provincia argentina, mismo criterio que bot_sanluis.py.

NÚMERO, SIGLA Y AÑO — salen del título, mismo mecanismo que San Luis
-------------------------------------------------------------------------------
"DECRETO N° 0624/2026" -> sigla vacía, número 0624, año 2026.
"DISPOSICIÓN M.P.C.eI./S.E.P.yA.-N° 0118/2026 - P1/3" -> sigla
"M.P.C.eI./S.E.P.yA.", número "0118 - P1/3" (se conserva el sufijo de
parte pegado al número: son notificaciones separadas de un mismo trámite,
cada una con su propio número de item/URL, así que se listan como normas
distintas pero el "- P1/3" queda visible para que no se confundan con
duplicados exactos), año 2026.
"RESOLUCIÓN N° 301-E-/SANTACRUZ-PCAP/2026 - P2/3" -> caso más raro, con
guiones dentro del propio número antes de la sigla; _partir_titulo no
intenta separar eso con precisión quirúrgica, prioriza no romper y deja
todo el bloque N°-hasta-año como "número" si no encuentra un patrón de
sigla limpio antes del "N°".

URL_NORMA — a diferencia de San Luis, ACÁ SÍ hay una URL propia por norma
-------------------------------------------------------------------------------
Cada norma tiene su propia página confirmada real
(/legislacion/{categoria-slug}/{id}, ej. /legislacion/decretos-sintetizados/
58460) — no hace falta ningún truco de fragmento como el "#page=N" de San
Juan, ni comparte URL entre normas como San Luis. Esto también significa
que el bug de deduplicación por URL en ingresar_scraping.php (el que
truncaba San Luis a 1 sola norma insertada) NO debería repetirse acá,
aunque igual conviene tener el fix de ese archivo ya aplicado (deduplicar
por tipo+número+año+emisor, no por URL) porque es estrictamente más
correcto en cualquier caso.

Dato real adicional: pedir una norma con el slug de categoría "equivocado"
(ej. pedir /legislacion/resoluciones-sintetizadas/58585 cuando en realidad
esa id es una Disposición Completa) NO da error — Joomla resuelve por id y
listo, ignora el slug de la URL. Por eso _items_de_edicion no intenta
adivinar el slug: usa tal cual el que vino en el link de la página de tag.

QUÉ SE VALIDÓ — HISTORIAL RESUMIDO
-------------------------------------------------------------------------------
1. Fixtures iniciales (texto vía web_fetch, 5 normas): confirmaron el diseño
   de texto plano original (hoy _extraer_texto_plano, camino de respaldo).
   2 bugs corregidos ahí: tipo con acento colado, sigla perdiendo el punto
   final.
2. El usuario mandó HTML crudo real del Decreto 0624/2026, lo que permitió
   reescribir el camino primario (_extraer_k2) con selectores CSS reales
   (.itemHeader/.itemTitle/.itemIntroText/.itemFullText) en vez de
   heurísticas de texto. 1 bug corregido ahí: _recortar_cuerpo aplastaba a
   espacios los saltos de línea entre párrafos.
3. **El usuario corrió el bot de verdad contra el sitio en vivo**
   (`--dry-run --todas`, BO 6140, 22 normas reales, debug_santacruz.json) —
   ésta es la validación más fuerte hasta ahora, con HTML real de producción
   en vez de texto de muestra. Confirmó que _extraer_k2 funciona de punta a
   punta para Decretos, Disposiciones y Resoluciones reales, y expuso un bug
   real: en 12 de las 22 normas (todas las Resoluciones H.C.D. y todas las
   Disposiciones/Resoluciones S.E.P.yA./M.P.C.eI. con marca resolutiva) el
   emisor salía contaminado con la línea de trámite inmediatamente anterior
   ("SANCIONADO: 28/05/2026 El Poder Legislativo..." en vez de sólo "El
   Poder Legislativo..."; "...atento a Dictamen SAJ-N°...; EL SECRETARIO..."
   en vez de sólo "EL SECRETARIO..."). Causa confirmada: la marca resolutiva
   está SOLA en su propio párrafo en la mayoría de estos casos reales (no
   comparte <div> con el nombre del funcionario), y el código anterior
   juntaba ciegamente las 2 líneas previas sin filtrar líneas de trámite.
   Esto también reveló, contra la misma corrida, el caso contrario: la
   Disposición E.M.G. 02/2026 (que SÍ venía funcionando bien) tiene el
   nombre del emisor partido en 2 párrafos reales consecutivos ("LA
   ESCRIBANA MAYOR DE GOBIERNO" / "DE LA PROVINCIA DE SANTA CRUZ") que hay
   que juntar — por lo que la solución no podía ser simplemente "tomar sólo
   la última línea". _emisor_desde_lineas se reescribió para recolectar
   hacia atrás los párrafos consecutivos que NO sean una línea de trámite
   conocida (_RE_LINEA_NO_EMISOR: PROYECTO N°, SANCIONADO:, POR ELLO (y
   variantes con más texto después, ej. "Por ello y atento a Dictamen..."),
   VISTO, CONSIDERANDO, NOTA, EXPEDIENTE, fechas sueltas), parando en la
   primera que sí lo sea. test_santacruz_fixtures.py se actualizó para usar
   el `texto_completo` REAL de 4 de estas 22 normas (58567, 58670, 58585,
   58532) — como ese campo ya venía separado por '\n' uno por párrafo real,
   se pudo reconstruir el cuerpo_parrafos EXACTO sin inventar ningún
   desglose, a diferencia de fixtures anteriores.
4. La misma corrida mostró 6 normas más (Turismo, Compras, I.D.U.V.) sin
   marca resolutiva, donde el emisor cae a la sigla cruda por no estar en
   SIGLAS_EMISOR (ej. "I.D.U.V.", "M.E.F.I./S.C.YC.P." tal cual, sin
   desarrollar). No es un bug -- es el fallback esperado para siglas no
   confirmadas -- pero se aprovechó para agregar 4 entradas nuevas: I.D.U.V.
   y M.E.F.I. confirmadas por búsqueda web contra los sitios oficiales
   (iduv.gob.ar, mefi.gob.ar); S.E.T. y S.C.yC.P. confirmadas directamente
   en el propio bloque de firma de las normas reales vistas ("Secretaría de
   Estado de Turismo", "Subsecretaría de Compras y Contrataciones
   Públicas"). De paso se invirtió el orden de búsqueda en las siglas
   compuestas (M.P.C.eI./S.E.T., M.E.F.I./S.C.yC.P., etc.) para preferir la
   unidad más específica (la última) en vez de quedarse en el ministerio
   genérico (la primera) cuando ambas están en el diccionario.
5. El usuario, revisando el mismo debug_santacruz.json a mano, encontró 2
   problemas más de forma (no de extracción, la línea correcta ya se
   estaba encontrando):
   a) El emisor sacado del cuerpo nombraba al TITULAR del cargo ("El
      Secretario de Estado de Pesca y Acuicultura") en vez de a la
      OFICINA ("Secretaría de Estado de Pesca y Acuicultura") — mismo
      patrón ya resuelto en bot_sanluis.py. Se agregó
      ROL_CUERPO_A_OFICINA + RE_EMISOR_CUERPO_ROL + _limpiar_titular_
      emisor(), con MINISTRO/MINISTRA y ESCRIBANO/ESCRIBANA agregados
      (confirmados reales acá, no estaban en la versión de San Luis) y
      soporte para "MAYOR" opcional ("Escribano MAYOR DE Gobierno").
   b) Un caso que SÍ ya era institucional ("El Poder Legislativo de la
      Provincia de Santa Cruz") quedaba con el artículo inicial y sin
      mayúsculas, inconsistente con el resto de los emisores (que nunca
      llevan "El "/"La " adelante). Se agregó RE_ARTICULO_INICIAL como
      segundo paso dentro de _limpiar_titular_emisor: si el texto no es
      un rol+dependencia conocido, igual se le saca un artículo inicial
      (El/La/Los/Las) y se fuerza a mayúsculas.
   Los 3 casos (a, b, y el fix de _emisor_desde_lineas del punto 3) se
   confirmaron con una corrida real del usuario contra el sitio en vivo
   después de cada corrección — no quedó ninguno pendiente de confirmar
   en producción, salvo la ejecución del test en sandbox (ver abajo).

QUÉ FALTA VALIDAR TODAVÍA
-------------------------------------------------------------------------------
1. El fix de _emisor_desde_lineas y las 4 siglas nuevas se revisaron a mano,
   línea por línea, contra los datos reales de debug_santacruz.json (no
   inventados) — pero por una caída del sandbox en esta sesión no se
   alcanzó a re-ejecutar test_santacruz_fixtures.py todavía para confirmar
   los "OK" en verdad. Falta correrlo una vez más (en sandbox o en la
   máquina del usuario) antes de darlo por cerrado.
2. Nunca se corrió el flujo completo (descubrir edición + paginar tag +
   bajar cada norma + clasificar + armar payload + envío real al backend)
   de punta a punta — la corrida real que sí se hizo fue con --dry-run, sin
   insertar en la base todavía.
3. Leyes, Acuerdos, Declaraciones, Decretos Completos: sin ningún ejemplo
   real todavía (no aparecieron en BO 6138 ni BO 6140) — tampoco se sabe si
   usan las mismas clases K2, aunque es lo esperable en un sitio K2 (una
   única plantilla de ítem compartida entre categorías del mismo
   componente).
4. La marca resolutiva espaciada en letras: confirmada real en 2 verbos
   (DISPONE, RESUELVE, ahora en 6+ normas reales entre las dos corridas) —
   DECRETA, ACUERDA, DECLARA, SANCIONA siguen sin confirmar, por analogía.
5. Los Decretos vistos (Sintetizados) siguen sin ningún caso real con VISTO/
   CONSIDERANDO/marca resolutiva — todos resuelven el emisor vía
   JURISDICCIÓN:. Si algún Decreto real la tuviera, el emisor saldría por
   ese camino en cambio — no debería cambiar el resultado, pero no está
   confirmado.
6. El paginado de la página de tag (`?start=N`, "Página X de Y") sigue sin
   confirmarse con HTML crudo — se reconoció por texto vía web_fetch (la
   corrida real del usuario sí lo ejercitó indirectamente -- encontró 22
   normas de Legislación en BO 6140 -- pero no se inspeccionó el HTML de
   esa página puntualmente).
7. PATRONES_INDIVIDUAL/PATRONES_GENERAL son los mismos heredados de San
   Juan/San Luis. La corrida real (--todas) los ejercitó contra 22 normas
   reales con resultados razonables a simple vista (sumarios administrativos
   y designaciones marcados IND, resoluciones de fondo marcadas GEN), pero
   no se auditó cada clasificación individualmente contra el criterio
   editorial real del usuario.
8. No hay forma de "--html archivo.html" para probar offline como en San
   Luis: cada corrida real pega contra el sitio en vivo.
===============================================================================
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
from bs4 import BeautifulSoup

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

SITIO = 'https://boletinoficial.santacruz.gob.ar'

HEADERS_WEB = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
}

REINTENTOS = 3
ESPERA_REINTENTO = 3
ESPERA_ENTRE_ITEMS = 0.4  # pausa entre pedidos de páginas de norma individuales
MAX_PAGINAS_TAG = 15      # tope de seguridad al paginar /legislacion/tag/BO%20N
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700

# slug de categoría (tal como aparece en la URL) -> tipo_norma_desc.
CATEGORIAS_NORMATIVA = {
    'leyes': 'LEY',
    'decretos-completos': 'DECRETO',
    'decretos-sintetizados': 'DECRETO',
    'resoluciones-completas': 'RESOLUCION',
    'resoluciones-sintetizadas': 'RESOLUCION',
    'declaraciones': 'DECLARACION',
    'acuerdos': 'ACUERDO',
    'disposiciones-completas': 'DISPOSICION',
    'disposiciones-sintetizadas': 'DISPOSICION',
}


# ===========================================================================
# NORMALIZACIÓN
# ===========================================================================
GUIONES = {ord('–'): '-', ord('—'): '-', ord('‐'): '-', ord('‑'): '-', ord('−'): '-'}


def _guiones(texto):
    return (texto or '').translate(GUIONES)


def _sin_acentos(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def _compacto(texto):
    return re.sub(r'\s+', ' ', (texto or '')).strip()


# ===========================================================================
# DESCARGA
# ===========================================================================
_SESION = None


def sesion():
    global _SESION
    if _SESION is None:
        _SESION = requests.Session()
        _SESION.headers.update(HEADERS_WEB)
    return _SESION


def descargar(url, timeout=45):
    for intento in range(1, REINTENTOS + 1):
        try:
            r = sesion().get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            if r.status_code == 200:
                return r.text
            if r.status_code < 500:
                return None
        except requests.RequestException as e:
            if intento == REINTENTOS:
                raise RuntimeError(f"Error de red pidiendo {url}: {e}")
        time.sleep(ESPERA_REINTENTO * intento)
    return None


# ===========================================================================
# DESCUBRIMIENTO DE LA EDICIÓN
# ===========================================================================
def obtener_numero_ultima_edicion():
    """Lee la portada /legislacion y devuelve el número de "BO NNNN" del
    bloque lateral fijo "Edición del ... / BO NNNN" (confirmado real en
    santacruz.html, selector `.moduleItemTags a`). None si no se encuentra."""
    html = descargar(f'{SITIO}/legislacion')
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    a = soup.select_one('.moduleItemTags a')
    if not a:
        return None
    m = re.search(r'BO\s*(\d+)', a.get_text(' ', strip=True), re.IGNORECASE)
    return m.group(1) if m else None


RE_HREF_NORMA = re.compile(r'^/legislacion/([a-z0-9-]+)/(\d+)$')
RE_PAGINA_DE = re.compile(r'P[aá]gina\s+\d+\s+de\s+(\d+)', re.IGNORECASE)


def _hrefs_legislacion(html):
    """{id: slug_categoria} de todos los <a href="/legislacion/slug/id">
    en la página (sirve tanto para la página de tag como, en principio,
    para cualquier listado). Se descartan a propósito los links a
    /avisos-oficiales/, /sociedades-y-avisos-judiciales/ y
    /contrataciones/, que comparten el mismo tag "BO NNNN" pero no son
    normativa del Estado."""
    soup = BeautifulSoup(html, 'html.parser')
    hallados = {}
    for a in soup.find_all('a', href=True):
        m = RE_HREF_NORMA.match(a['href'])
        if m:
            hallados[int(m.group(2))] = m.group(1)
    return hallados


def items_de_edicion(numero_bo):
    """{id: slug_categoria} de TODAS las normas (de Legislación solamente)
    etiquetadas con BO {numero_bo}, paginando la página de tag hasta el
    final. Usa el "Página X de Y" que el propio sitio informa (confirmado
    real: 6 páginas de 10 ítems para BO 6140) en vez de adivinar cuándo
    parar, con MAX_PAGINAS_TAG como tope de seguridad por si ese texto no
    aparece o el sitio cambia el paginado."""
    url0 = f'{SITIO}/legislacion/tag/BO%20{numero_bo}'
    html0 = descargar(url0)
    if not html0:
        return {}
    todos = _hrefs_legislacion(html0)
    soup0 = BeautifulSoup(html0, 'html.parser')
    m_pag = RE_PAGINA_DE.search(soup0.get_text(' ', strip=True))
    total_paginas = min(int(m_pag.group(1)), MAX_PAGINAS_TAG) if m_pag else 1
    for pagina in range(1, total_paginas):
        html = descargar(f'{url0}?start={pagina * 10}')
        if html:
            todos.update(_hrefs_legislacion(html))
        time.sleep(ESPERA_ENTRE_ITEMS)
    return todos


# ===========================================================================
# PARSEO DE UNA NORMA INDIVIDUAL
# ===========================================================================
MESES = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SETIEMBRE': 9, 'SEPTIEMBRE': 9, 'OCTUBRE': 10,
    'NOVIEMBRE': 11, 'DICIEMBRE': 12,
}

CATEGORIA_TEXTO = {
    'Leyes': 'leyes', 'Decretos Completos': 'decretos-completos',
    'Decretos Sintetizados': 'decretos-sintetizados',
    'Resoluciones Completas': 'resoluciones-completas',
    'Resoluciones Sintetizadas': 'resoluciones-sintetizadas',
    'Declaraciones': 'declaraciones', 'Acuerdos': 'acuerdos',
    'Disposiciones Completas': 'disposiciones-completas',
    'Disposiciones Sintetizadas': 'disposiciones-sintetizadas',
}
RE_CABECERA = re.compile(
    r'(?P<categoria>' + '|'.join(re.escape(c) for c in CATEGORIA_TEXTO) + r')'
    r'\s*/\s*publicado el\s+(?P<dia>\d{1,2})\s+(?P<mes>[A-Za-zñÑ]+)\s+(?P<anio>\d{4})'
    r'\s*/\s*BO\s*(?P<bo>\d+)')

RE_TITULO = re.compile(
    r'\b(?P<tipo>LEY|DECRETO|RESOLUCI[OÓ]N|DISPOSICI[OÓ]N|ACUERDO|DECLARACI[OÓ]N)\b'
    r'(?P<sigla>[^\n]{0,60}?)N[º°]\s*(?P<numyanio>[\w./\-]+(?:\s*-\s*P\d+\s*/\s*\d+)?)',
    re.IGNORECASE)

RE_DATELINE = re.compile(
    r'R[IÍ]O\s+GALLEGOS,\s*(?P<dia>\d{1,2})\s+de\s+(?P<mes>[A-Za-zñÑ]+)(?:\s+de)?\s+(?P<anio>\d{4})',
    re.IGNORECASE)

VERBOS_MARCA = {'DISPONE', 'DISPONEN', 'RESUELVE', 'RESUELVEN', 'DECRETA', 'DECRETAN',
                'ACUERDA', 'ACUERDAN', 'DECLARA', 'DECLARAN', 'SANCIONA', 'SANCIONAN'}
RE_MARCA_ESPACIADA = re.compile(r'\b([A-ZÁÉÍÓÚÑ](?:\s[A-ZÁÉÍÓÚÑ]){3,})\s*:')

RE_JURISDICCION = re.compile(
    r'JURISDICCI[OÓ]N\s*:\s*(?P<nombre>[^\n\-]+?)(?:\s*-\s*SAF|\s*-\s*Sector|\.-|\n|$)',
    re.IGNORECASE)


_TIPO_A_CANONICO = {
    'LEY': 'LEY', 'DECRETO': 'DECRETO', 'RESOLUCION': 'RESOLUCION',
    'DISPOSICION': 'DISPOSICION', 'ACUERDO': 'ACUERDO', 'DECLARACION': 'DECLARACION',
}


def _partir_titulo(m_titulo):
    """A partir del match de RE_TITULO devuelve (tipo, sigla, numero, anio).
    tipo se normaliza SIN acento (RESOLUCIÓN -> RESOLUCION) para que sea
    consistente con el resto de la familia de bots. La sigla sólo recorta
    espacios y el guion separador que quedó pegado antes de "N°" — NO
    recorta puntos finales, porque son parte de la sigla misma (ej.
    "H.C.D." terminaría como "H.C.D" si se los sacara, perdiendo la
    abreviatura real)."""
    tipo_crudo = _sin_acentos(m_titulo.group('tipo')).upper()
    tipo = _TIPO_A_CANONICO.get(tipo_crudo, tipo_crudo)
    sigla = re.sub(r'[\s\-]+$', '', m_titulo.group('sigla').strip())
    numyanio = m_titulo.group('numyanio').strip()
    m_anio = re.search(r'/(\d{4})\s*$', numyanio)
    if m_anio:
        anio = m_anio.group(1)
        numero = numyanio[:m_anio.start()].strip()
    else:
        anio = ''
        numero = numyanio
    return tipo, sigla, numero, anio


def _buscar_marca_resolutiva(texto):
    """Busca una corrida de letras sueltas separadas por espacios que, sin
    los espacios, sea un verbo resolutivo conocido (VERBOS_MARCA) — la
    marca viene con letter-spacing real en las 5 normas vistas
    ("D I S P O N E :", "R E S U E L V E :"). Devuelve el match o None."""
    for m in RE_MARCA_ESPACIADA.finditer(texto):
        if m.group(1).replace(' ', '') in VERBOS_MARCA:
            return m
    return None


def _texto_el(el):
    """Texto compacto (un solo espacio entre palabras, sin guiones de
    corte de línea) de un elemento de BeautifulSoup."""
    return _compacto(_guiones(el.get_text(' ', strip=True)))


def _lineas_de(el):
    """Texto de cada hijo directo de `el` como una línea propia — refleja
    la estructura real confirmada de .itemFullText (una serie de <div
    style="text-align:...​"> hermanos, uno por párrafo, visto en el HTML
    crudo del Decreto 0624/2026). Si el elemento no tiene hijos-etiqueta
    directos con texto (plantilla distinta a la vista), se cae a separar
    por saltos de línea del propio get_text."""
    hijos = [_texto_el(h) for h in el.find_all(recursive=False)]
    hijos = [h for h in hijos if h]
    if hijos:
        return hijos
    return [l for l in (_compacto(_guiones(l)) for l in
                         el.get_text('\n', strip=True).split('\n')) if l]


def _texto_antes_de(texto, pos):
    """Texto inmediatamente antes de la posición `pos` en `texto`,
    cortando en el separador de oración más cercano (.;:) dentro de una
    ventana de 160 caracteres hacia atrás. Así, tanto si `texto` es un
    párrafo corto (un <div> de .itemFullText) como si es el cuerpo entero
    sin dividir (camino de respaldo de texto plano), no se arrastra la
    oración anterior completa por error — es la misma lógica que ya
    estaba probada contra las 5 muestras reales antes de este refactor."""
    ventana = texto[max(0, pos - 160):pos]
    m = re.search(r'[.;:]\s*([^.;:]{3,120})$', ventana)
    candidato = m.group(1) if m else ventana[-120:]
    return _compacto(candidato)


# Líneas de trámite que pueden quedar como "párrafo anterior" a la marca
# resolutiva sin ser parte del emisor -- CONFIRMADO real contra una
# corrida en producción (--dry-run --todas, BO 6140, 22/07/2026):
#   - Resoluciones H.C.D. (144/145/146): "PROYECTO N° .../2026" y
#     "SANCIONADO: {fecha}" son cada una su propio párrafo, ANTES del
#     párrafo del emisor real ("El Poder Legislativo de la Provincia de
#     Santa Cruz").
#   - Disposiciones/Resoluciones S.E.P.yA./M.P.C.eI.: "Por ello y atento
#     a Dictamen SAJ-N° .../26, emitido por la Subsecretaría de Asuntos
#     Jurídicos, obrante a fojas .../...;" es su propio párrafo, ANTES
#     del párrafo del emisor real ("EL SECRETARIO DE ESTADO DE PESCA Y
#     ACUICULTURA" / "LA MINISTRA DE LA PRODUCCIÓN, COMERCIO E
#     INDUSTRIA").
# Coincide con "^POR\s+ELLO" incluso cuando sigue más texto después (a
# diferencia del match exacto anterior, que sólo pescaba "POR ELLO:"
# solo y se perdía "Por ello y atento a Dictamen...").
_RE_LINEA_NO_EMISOR = re.compile(
    r'^(?:\d{1,2}[/.]\d{1,2}[/.]\d{2,4}\b|POR\s+ELLO\b|Y\s+ATENTO\s+A\s+ELLO\b|'
    r'ATENTO\s+A\s+ELLO\b|POR\s+TANTO\b|POR\s+TODO\s+ELLO\b|VISTO\b|'
    r'Y\s+CONSIDERANDO\b|CONSIDERANDO\b|SANCIONADO\b|PROYECTO\b|NOTA\b|'
    r'EXPEDIENTE\b|DADA\s+EN\s+SALA\b)',
    re.IGNORECASE)


def _emisor_desde_lineas(lineas):
    """Recorre `lineas` (una por párrafo, ver _lineas_de — o, en el
    camino de respaldo de texto plano, una lista de un solo elemento con
    todo el cuerpo) buscando la marca resolutiva espaciada. Si la marca
    comparte línea/párrafo con más texto antes suyo (ej. "EL SECRETARIO
    DE ESTADO DE RECURSOS HÍDRICOS   D I S P O N E :" en un sólo <div>, o
    en todo el cuerpo sin dividir), ese texto previo — recortado con
    _texto_antes_de — es el emisor, salvo que sea en sí una línea de
    trámite (_RE_LINEA_NO_EMISOR).

    Si la marca está sola en su línea (CONFIRMADO real en producción para
    H.C.D. y S.E.P.yA./M.P.C.eI., ver comentario de _RE_LINEA_NO_EMISOR),
    se recolectan hacia atrás los párrafos consecutivos que NO sean línea
    de trámite, parando en el primero que sí lo sea. Esto es a propósito
    distinto de "tomar sólo la última línea": el nombre del emisor puede
    venir partido en 2 párrafos consecutivos (CONFIRMADO real: Disposición
    E.M.G. 02/2026 trae "LA ESCRIBANA MAYOR DE GOBIERNO" y "DE LA
    PROVINCIA DE SANTA CRUZ" en dos <div> separados, y hay que juntar
    ambos) — por eso no alcanza con parar en la primera línea de trámite
    Y ADEMÁS quedarse sólo con la más cercana a la marca; hay que juntar
    TODAS las líneas válidas encontradas antes de esa parada. El bug real
    que este diseño reemplaza era juntar ciegamente las últimas 2 líneas
    sin filtrar trámite, lo que colaba "SANCIONADO: fecha" o "Por ello y
    atento a Dictamen..." adelante del emisor real. Devuelve '' si no se
    encontró marca alguna o si sólo hay líneas de trámite antes de ella."""
    for i, linea in enumerate(lineas):
        m = _buscar_marca_resolutiva(linea)
        if not m:
            continue
        antes_en_linea = _texto_antes_de(linea, m.start())
        if len(antes_en_linea) >= 4 and not _RE_LINEA_NO_EMISOR.match(antes_en_linea):
            return antes_en_linea
        recolectadas = []
        for j in range(i - 1, max(-1, i - 4), -1):
            candidato = lineas[j]
            if not candidato or _buscar_marca_resolutiva(candidato) \
                    or _RE_LINEA_NO_EMISOR.match(candidato):
                break
            recolectadas.insert(0, candidato)
        return _compacto(' '.join(recolectadas))[:200].strip()
    return ''


# Mismo patrón ya usado en bot_sanluis.py (mismo idioma administrativo
# argentino): el cuerpo de la norma suele nombrar al TITULAR del cargo
# ("El Secretario de Estado de Pesca y Acuicultura", "La Ministra de la
# Producción...") en vez de a la OFICINA en sí ("Secretaría de Estado de
# Pesca y Acuicultura", "Ministerio de la Producción..."). CONFIRMADO real
# que hace falta contra la corrida en producción (BO 6140): 8 Disposiciones
# S.E.P.yA., 1 Disposición S.E.R.H., 2 Resoluciones M.P.C.eI. y 1
# Disposición E.M.G. traían el nombre del titular tal cual salía del
# cuerpo. A diferencia de San Luis, acá se agregaron MINISTRO/MINISTRA y
# ESCRIBANO/ESCRIBANA (confirmados reales en esta corrida) y el patrón
# admite un "MAYOR" opcional antes de "DE" para cubrir "Escribano MAYOR DE
# Gobierno" -> "Escribanía MAYOR DE Gobierno".
ROL_CUERPO_A_OFICINA = {
    'DIRECTOR': 'DIRECCIÓN', 'DIRECTORA': 'DIRECCIÓN',
    'SUBDIRECTOR': 'SUBDIRECCIÓN', 'SUBDIRECTORA': 'SUBDIRECCIÓN',
    'SECRETARIO': 'SECRETARÍA', 'SECRETARIA': 'SECRETARÍA',
    'SUBSECRETARIO': 'SUBSECRETARÍA', 'SUBSECRETARIA': 'SUBSECRETARÍA',
    'MINISTRO': 'MINISTERIO', 'MINISTRA': 'MINISTERIO',
    'ESCRIBANO': 'ESCRIBANÍA', 'ESCRIBANA': 'ESCRIBANÍA',
    'COORDINADOR': 'COORDINACIÓN', 'COORDINADORA': 'COORDINACIÓN',
    'ADMINISTRADOR': 'ADMINISTRACIÓN', 'ADMINISTRADORA': 'ADMINISTRACIÓN',
    'JEFE': 'JEFATURA', 'JEFA': 'JEFATURA',
    'INTERVENTOR': 'INTERVENCIÓN', 'INTERVENTORA': 'INTERVENCIÓN',
    'PRESIDENTE': 'PRESIDENCIA', 'PRESIDENTA': 'PRESIDENCIA',
}
RE_EMISOR_CUERPO_ROL = re.compile(
    r'^(?:EL|LA)\s+(?:(?:SE[ÑN]ORA?|SRA?\.)\s+)?'
    r'(?P<rol>' + '|'.join(ROL_CUERPO_A_OFICINA) + r')'
    r'\s+(?P<resto>(?:MAYOR\s+)?DE\b.*)$',
    re.IGNORECASE)

# Segundo paso, para cuando el texto NO es un rol+dependencia (no matchea
# RE_EMISOR_CUERPO_ROL) pero igual arranca con artículo -- confirmado real:
# "El Poder Legislativo de la Provincia de Santa Cruz" (usuario reportó que
# quedaba mal así). "Poder Legislativo" ya es en sí un nombre institucional
# (como "Poder Ejecutivo", "Poder Judicial"), sólo sobra el artículo
# inicial para que quede en la misma forma que el resto de los emisores de
# esta familia de bots (ninguno de los valores de SIGLAS_EMISOR ni de
# ROL_CUERPO_A_OFICINA lleva "El "/"La " adelante).
RE_ARTICULO_INICIAL = re.compile(r'^(?:EL|LA|LOS|LAS)\s+', re.IGNORECASE)


def _limpiar_titular_emisor(texto):
    """Convierte "El Secretario de Estado de X" -> "Secretaría de Estado
    de X" (nombra la OFICINA, no a quien la ocupa) vía
    RE_EMISOR_CUERPO_ROL. Si el texto no es un rol+dependencia conocido
    (ej. "El Poder Legislativo..."), igual se le saca el artículo inicial
    (RE_ARTICULO_INICIAL) para que quede en la misma forma que el resto
    de los emisores. No toca "Gobernador": es un cargo constitucional en
    sí mismo, no un rol+dependencia genérico (mismo criterio que San
    Luis) — y "Gobernador" tampoco lleva artículo adelante en el texto
    real, así que RE_ARTICULO_INICIAL no tiene nada que sacarle. El
    resultado final siempre queda en mayúsculas, igual que el resto de
    los emisores de esta familia de bots."""
    t = _compacto(texto or '')
    m = RE_EMISOR_CUERPO_ROL.match(t)
    if m:
        oficina = ROL_CUERPO_A_OFICINA[m.group('rol').upper()]
        t = _compacto(f"{oficina} {m.group('resto')}")
    else:
        t = RE_ARTICULO_INICIAL.sub('', t)
    return t.upper()


SIGLAS_EMISOR = {
    'H.C.D.': 'HONORABLE CÁMARA DE DIPUTADOS',
    'E.M.G.': 'ESCRIBANÍA MAYOR DE GOBIERNO',
    'M.P.C.eI.': 'MINISTERIO DE LA PRODUCCIÓN, COMERCIO E INDUSTRIA',
    'M.E.yM.': 'MINISTERIO DE ENERGÍA Y MINERÍA',
    'S.E.R.H.': 'SECRETARÍA DE ESTADO DE RECURSOS HÍDRICOS',
    'S.E.P.yA.': 'SECRETARÍA DE ESTADO DE PESCA Y ACUICULTURA',
    'M.S.A.': 'MINISTERIO DE SALUD Y AMBIENTE',
    # Agregados tras revisar una corrida real en producción (BO 6140):
    # I.D.U.V. y M.E.F.I. confirmados por búsqueda web (sitios oficiales
    # iduv.gob.ar / mefi.gob.ar); S.E.T. y S.C.yC.P. confirmados
    # directamente en el propio texto de la norma (bloque de firma real
    # de las Disposiciones 014/015 y 531 vistas: "Secretaría de Estado de
    # Turismo" y "Subsecretaría de Compras y Contrataciones Públicas").
    'I.D.U.V.': 'INSTITUTO DE DESARROLLO URBANO Y VIVIENDA',
    'M.E.F.I.': 'MINISTERIO DE ECONOMÍA, FINANZAS E INFRAESTRUCTURA',
    'S.E.T.': 'SECRETARÍA DE ESTADO DE TURISMO',
    'S.C.yC.P.': 'SUBSECRETARÍA DE COMPRAS Y CONTRATACIONES PÚBLICAS',
}
_SIGLAS_EMISOR_NORM = {_sin_acentos(k).upper(): v for k, v in SIGLAS_EMISOR.items()}


def _resolver_emisor(tipo, sigla, emisor_cuerpo, texto_cuerpo):
    if emisor_cuerpo:
        return _limpiar_titular_emisor(emisor_cuerpo)
    if tipo == 'DECRETO':
        m = RE_JURISDICCION.search(texto_cuerpo)
        if m:
            # _limpiar_titular_emisor ya deja el resultado en mayúsculas
            return _limpiar_titular_emisor(m.group('nombre'))
    # reversed(): en las 4 siglas compuestas confirmadas reales
    # (M.P.C.eI./S.E.P.yA., M.E.yM./S.E.R.H., M.P.C.eI./S.E.T.,
    # M.E.F.I./S.C.yC.P.) el orden es siempre "unidad madre / unidad
    # específica" -- si ambas están en el diccionario, preferir la más
    # específica (la última) da un emisor más útil que quedarse en el
    # ministerio genérico.
    for segmento in reversed(re.split(r'[/]', sigla)):
        clave = _sin_acentos(segmento.strip(' .-')).upper()
        # los valores del diccionario están sin normalizar -- comparar
        # también la clave normalizada contra una version normalizada
        for k_orig, v in SIGLAS_EMISOR.items():
            if _sin_acentos(k_orig).upper().strip('.') == clave.strip('.'):
                return v
    if tipo == 'DECRETO':
        return 'GOBERNADOR DE LA PROVINCIA'
    return sigla.upper() if sigla else 'PODER EJECUTIVO'


def _recortar_cuerpo(texto):
    """Corta antes del bloque estático "AUTORIDADES" si aparece. Con
    HTML crudo se confirmó que ese bloque vive en un <tfoot> separado,
    fuera de .itemFullText — así que en el camino K2 esto normalmente no
    debería encontrar nada y es sólo una red de seguridad; en el camino
    de texto plano (toda la página junta) sigue siendo necesario.
    Compacta espacios DENTRO de cada línea pero conserva los saltos de
    línea entre párrafos (si los hay, ej. viniendo de _lineas_de) — no
    usa _compacto() sobre el texto entero porque eso aplastaría los '\\n'
    a espacios y perdería la separación real por párrafo."""
    m = re.search(r'\bAUTORIDADES\b', texto)
    if m:
        texto = texto[:m.start()]
    lineas = [_compacto(l) for l in texto.split('\n')]
    return '\n'.join(l for l in lineas if l)


def _fecha_iso_de(texto):
    m = RE_DATELINE.search(texto)
    if not m:
        return None
    mes_num = MESES.get(_sin_acentos(m.group('mes')).upper())
    if not mes_num:
        return None
    try:
        return date(int(m.group('anio')), mes_num, int(m.group('dia'))).isoformat()
    except ValueError:
        return None


def _extraer_k2(soup, url):
    """Camino primario: usa las clases K2 confirmadas reales contra el
    HTML crudo del Decreto 0624/2026 (.itemHeader, .itemTitle,
    .itemIntroText, .itemFullText). Devuelve None si falta alguna de las
    3 imprescindibles (header/título/cuerpo — la síntesis es opcional)
    para que procesar_norma() se caiga al camino de texto plano."""
    el_header = soup.select_one('.itemHeader')
    el_titulo = soup.select_one('.itemTitle')
    el_intro = soup.select_one('.itemIntroText')
    el_cuerpo = soup.select_one('.itemFullText')
    if el_header is None or el_titulo is None or el_cuerpo is None:
        return None

    texto_header = _texto_el(el_header)
    m_cab = RE_CABECERA.search(texto_header)
    if not m_cab:
        print(f"Aviso: no se reconoció categoría/fecha/BO en itemHeader de {url}: "
              f"{texto_header[:120]!r}", file=sys.stderr)
        return None

    texto_titulo = _texto_el(el_titulo)
    m_tit = RE_TITULO.search(texto_titulo)
    if not m_tit:
        print(f"Aviso: no se reconoció el título en itemTitle de {url}: "
              f"{texto_titulo!r}", file=sys.stderr)
        return None
    tipo, sigla, numero, anio_titulo = _partir_titulo(m_tit)

    sintesis = _texto_el(el_intro) if el_intro else ''
    cuerpo_lineas = _lineas_de(el_cuerpo)
    cuerpo = _recortar_cuerpo('\n'.join(cuerpo_lineas))

    return {
        'categoria': m_cab.group('categoria'), 'bo': m_cab.group('bo'),
        'tipo': tipo, 'sigla': sigla, 'numero': numero, 'anio_titulo': anio_titulo,
        'sintesis': sintesis, 'cuerpo': cuerpo, 'cuerpo_lineas': cuerpo_lineas,
        'fecha': _fecha_iso_de(cuerpo),
    }


def _extraer_texto_plano(soup, url):
    """Camino de respaldo (el diseño original, validado con 5 muestras de
    texto real pero sin HTML crudo propio): busca los mismos datos en el
    texto plano de toda la página, por si alguna categoría todavía no
    vista (Leyes, Acuerdos, Declaraciones) usa una plantilla K2 distinta
    sin las clases itemHeader/itemTitle/itemFullText. Menor confianza que
    _extraer_k2 — sólo se usa si ese camino no reconoce la página."""
    texto = _guiones(soup.get_text(' ', strip=True))

    m_cab = RE_CABECERA.search(texto)
    if not m_cab:
        print(f"Aviso: no se reconoció la cabecera categoría/fecha/BO en {url}",
              file=sys.stderr)
        return None

    resto = texto[m_cab.end():]
    m_tit1 = RE_TITULO.search(resto)
    if not m_tit1:
        print(f"Aviso: no se reconoció el título de la norma en {url}", file=sys.stderr)
        return None
    tipo, sigla, numero, anio_titulo = _partir_titulo(m_tit1)

    despues_titulo = resto[m_tit1.end():]
    m_tit2 = RE_TITULO.search(despues_titulo)
    m_fecha_fallback = RE_DATELINE.search(despues_titulo)
    fin_sintesis = len(despues_titulo)
    if m_tit2:
        fin_sintesis = min(fin_sintesis, m_tit2.start())
    if m_fecha_fallback:
        fin_sintesis = min(fin_sintesis, m_fecha_fallback.start())
    sintesis = _compacto(despues_titulo[:fin_sintesis])

    cuerpo_desde = m_tit2.end() if m_tit2 else 0
    cuerpo_crudo = despues_titulo[cuerpo_desde:]
    cuerpo = _recortar_cuerpo(cuerpo_crudo)

    return {
        'categoria': m_cab.group('categoria'), 'bo': m_cab.group('bo'),
        'tipo': tipo, 'sigla': sigla, 'numero': numero, 'anio_titulo': anio_titulo,
        'sintesis': sintesis, 'cuerpo': cuerpo, 'cuerpo_lineas': [cuerpo],
        'fecha': _fecha_iso_de(cuerpo) or _fecha_iso_de(despues_titulo),
    }


def procesar_norma(id_norma, slug_categoria):
    """Descarga y parsea una norma puntual. Devuelve un dict o None si la
    página no se pudo interpretar. Intenta primero con las clases K2
    confirmadas reales contra HTML crudo (_extraer_k2); si la plantilla
    de esa categoría no las trae, se cae a heurísticas de texto plano
    (_extraer_texto_plano, el diseño original, validado sólo con texto de
    muestra vía web_fetch — no con HTML crudo propio)."""
    url = f'{SITIO}/legislacion/{slug_categoria}/{id_norma}'
    html = descargar(url)
    if not html:
        print(f"Aviso: no se pudo descargar {url}", file=sys.stderr)
        return None

    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()

    datos = _extraer_k2(soup, url)
    if datos is None:
        datos = _extraer_texto_plano(soup, url)
    if datos is None:
        return None

    emisor_cuerpo = _emisor_desde_lineas(datos['cuerpo_lineas'])
    emisor = _resolver_emisor(datos['tipo'], datos['sigla'], emisor_cuerpo, datos['cuerpo'])

    return {
        'id': id_norma,
        'seccion': datos['categoria'],
        'slug_categoria': slug_categoria,
        'tipo': datos['tipo'],
        'sigla': datos['sigla'],
        'numero': datos['numero'],
        'anio': datos['anio_titulo'] or (datos['fecha'] or '')[:4] or '????',
        'fecha': datos['fecha'],
        'bo': datos['bo'],
        'emisor': emisor,
        'sintesis': datos['sintesis'],
        'texto_completo': datos['cuerpo'],
        'url_norma': url,
    }


# ===========================================================================
# CLASIFICACIÓN INDIVIDUAL / GENERAL
# ===========================================================================
# Heredado tal cual de bot_sanjuan.py/bot_sanluis.py (mismo idioma
# administrativo argentino). NO revisado todavía contra normas reales de
# Santa Cruz — ver "QUÉ FALTA VALIDAR" en el docstring principal.
UMBRAL_INDIVIDUAL = 3

PATRONES_INDIVIDUAL = [
    (r'\bDes[íi]gn(?:[ae]se|a|ar)\b', 4, 'designación'),
    (r'\bAc[ée]pt(?:[ae]se|a|ar)\b[\s\S]{0,80}\brenuncia\b', 4, 'renuncia'),
    (r'\brenuncia\s+presentada\s+por\b', 4, 'renuncia'),
    (r'\b(?:Promu[ée]v[ae](?:se)?|Promover)\b', 4, 'promoción de un agente'),
    (r'\bContrato\s+de\s+(?:Locaci[óo]n|Prestaci[óo]n)\s+de\s+Servicios?\b', 3, 'contrato de personal'),
    (r'\bInstr[úu]yase\s+Sumario\s+Administrativo\b', 4, 'sumario administrativo'),
    (r'\bexoneraci[óo]n\b|\bcesant[íi]a\b', 4, 'sanción expulsiva'),
    (r'\bsumario\s+administrativo\b', 2, 'sumario administrativo (mención)'),
    (r'\bRecurso\s+Jer[áa]rquico\s+interpuesto\b', 3, 'recurso de un particular'),
    (r'\bOt[oó]rg(?:[ae]se|a|ar)\b[\s\S]{0,60}\b[Bb]eneficio\b', 3, 'beneficio a una persona'),
    (r'\bAcu[eé]rd(?:ase|anse|a|an|o)\b[\s\S]{0,60}\b[Bb]eneficio\b', 3, 'beneficio a una persona (acuérdase)'),
    (r'\bretiro\s+voluntario\b|\bpase\s+a\s+situaci[óo]n\s+de\s+retiro\b', 3, 'retiro/pase a retiro'),
    (r'\bBaja\s+definitiva\b|\bJubilaci[óo]n\b', 3, 'baja / jubilación'),
    (r'\bOt[óo]rg(?:[ae]se|a|ar)\b[\s\S]{0,60}\bLicencia\b', 3, 'licencia'),
    (r'\bSANCIONAR\b[\s\S]{0,60}\bmulta\b', 3, 'sanción de multa a una persona'),
    (r'\bD\.?N\.?I\.?\s*N?\s*[º°]?\s*[\d.]{6,}', 1, 'menciona DNI de una persona'),
]

PATRONES_GENERAL = [
    (r'\bPromu[úu]lg', -5, 'promulgación de ley'),
    (r'\bCr[ée]a(?:se)?\s+el\b|\bCr[ée]ase\b', -3, 'creación normativa'),
    (r'\bDeclara(?:se)?\b[\s\S]{0,60}\bInter[ée]s\s+Provincial\b', -4, 'declaración de interés provincial'),
    (r'\bApru[ée]b[ae](?:nse)?\b[\s\S]{0,60}(?:Reglamento|Manual|Anexo|Convenio)\b', -3, 'aprobación normativa/convenio'),
    (r'\bactualizaci[óo]n\s+tarifaria\b|\bcuadro\s+tarifario\b', -3, 'actualización tarifaria general'),
    (r'\bDer[óo]ganse\b|\bDer[óo]gase\b', -3, 'derogación'),
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
# BACKEND (mismo contrato que el resto de la familia de bots)
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
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Santa Cruz.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se descubre solo')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--bo', type=int, metavar='N',
                    help='edición puntual por número de Boletín Oficial, salta el descubrimiento')
    ap.add_argument('--todas', action='store_true',
                    help='muestra también las individuales, con puntaje y motivos')
    ap.add_argument('--sin-filtro', action='store_true',
                    help='envía también las individuales')
    ap.add_argument('--volcar', action='store_true', help='imprime lo reconocido y sale')
    args = ap.parse_args()

    # ---- 1. Ubicar la edición ---------------------------------------------
    numero_bo = str(args.bo) if args.bo else obtener_numero_ultima_edicion()
    if not numero_bo:
        salida("warning", "No se pudo determinar el número de Boletín Oficial vigente "
                          "en boletinoficial.santacruz.gob.ar (ver stderr).")
    print(f"Boletín Oficial N° {numero_bo}: {SITIO}/legislacion/tag/BO%20{numero_bo}",
          file=sys.stderr)

    # ---- 2. Enumerar los ítems de Legislación de esa edición ---------------
    items = items_de_edicion(numero_bo)
    print(f"Ítems de Legislación encontrados en BO {numero_bo}: {len(items)}", file=sys.stderr)
    if not items:
        salida("success", f"Sin novedades: no se encontraron normas de Legislación en "
                          f"BO {numero_bo}.", total=0)

    # ---- 3. Descargar y parsear cada norma ---------------------------------
    normas_todas = []
    fecha_boletin = None
    for i, (id_norma, slug) in enumerate(sorted(items.items())):
        if slug not in CATEGORIAS_NORMATIVA:
            print(f"Aviso: categoría desconocida {slug!r} (id {id_norma}) — no está en "
                  f"CATEGORIAS_NORMATIVA, se omite.", file=sys.stderr)
            continue
        n = procesar_norma(id_norma, slug)
        if i < len(items) - 1:
            time.sleep(ESPERA_ENTRE_ITEMS)
        if n is None:
            continue
        if n['bo'] != numero_bo:
            print(f"Aviso: {n['url_norma']} dice BO {n['bo']} en vez de {numero_bo} "
                  f"(discrepancia entre el tag usado para encontrarla y su propio "
                  f"encabezado) — se conserva igual.", file=sys.stderr)
        if n['fecha']:
            fecha_boletin = fecha_boletin or n['fecha']
        n['es_individual'], n['puntaje'], n['motivos'] = clasificar_norma(
            n['tipo'], n['sintesis'], n['texto_completo'])
        normas_todas.append(n)

    if not fecha_boletin:
        # Fallback: sin ninguna fecha parseada de ninguna norma, usar hoy
        # sólo para no dejar fecha_boletin en None (impacta el registro de
        # historial y el nombre visible del boletín en los mensajes).
        fecha_boletin = date.today().isoformat()
        print("Aviso: no se pudo determinar la fecha del boletín desde ninguna norma "
              "(ver 'RÍO GALLEGOS, ...'); se usa la fecha de hoy como reemplazo.",
              file=sys.stderr)

    if args.volcar:
        for n in normas_todas:
            print(f"  [{n['seccion']}] {n['tipo']:12s} N° {n['numero']:>14s} "
                  f"sigla={n['sigla']:20s} fecha={n['fecha'] or '?':10s} "
                  f"emisor={n['emisor'][:40]}", file=sys.stderr)
        salida("success", f"volcado: {len(normas_todas)} normas reconocidas.")

    guardar_debug(json.dumps(normas_todas, ensure_ascii=False, indent=2, default=str),
                  'debug_santacruz.json')

    generales = [n for n in normas_todas if not n['es_individual']]
    individuales = [n for n in normas_todas if n['es_individual']]
    a_enviar = normas_todas if args.sin_filtro else generales

    print(f"Boletín {fecha_boletin} (BO {numero_bo}) | normas: {len(normas_todas)} "
          f"(generales {len(generales)} / individuales {len(individuales)})", file=sys.stderr)

    if args.dry_run:
        for n in (normas_todas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {n['tipo']:12s} N° {n['numero']:>14s} {n['emisor'][:40]:40s} "
                  f"{n['sintesis'][:50]}", file=sys.stderr)
            if args.todas and n.get('motivos'):
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    if verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        salida("info", f"El boletín del {fecha_boletin} (BO {numero_bo}) ya fue procesado.")

    if not normas_todas:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Sin novedades: el boletín BO {numero_bo} no publicó normativa "
                          f"reconocible.", total=0)

    if not a_enviar:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Se procesó BO {numero_bo}, pero las {len(individuales)} normas "
                          f"encontradas son actos individuales; no se envió ninguna.", total=0)

    # ---- 4. Envío -------------------------------------------------------------
    payload = [{
        "id_jurisdiccion": args.id_jurisdiccion,
        "nombre_emisor": n['emisor'],
        "tipo_norma_desc": n['tipo'],
        "numero": n['numero'],
        "anio": n['anio'],
        "fecha_publicacion": n['fecha'] or fecha_boletin,
        "sintesis": construir_sintesis(n),
        "texto_completo": recortar_texto(n['texto_completo']),
        "url_norma": n['url_norma'],
    } for n in a_enviar]

    try:
        r = requests.post(URL_GUARDAR_NORMAS, json={"normas": payload},
                          headers={"Authorization": f"Bearer {API_KEY_BACKEND}",
                                   "Content-Type": "application/json"}, timeout=120)
        r.raise_for_status()
        respuesta = r.json()
    except Exception as e:
        salida("error", f"Error enviando al backend: {e}")

    registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, len(payload))
    salida("success", respuesta.get('mensaje', 'OK') or 'OK', total=len(payload))


if __name__ == '__main__':
    try:
        _main()
    except SystemExit:
        raise
    except Exception as e:
        salida("error", f"Error inesperado: {e}")