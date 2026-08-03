#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
 BOLETÍN OFICIAL DE TIERRA DEL FUEGO, ANTÁRTIDA E ISLAS DEL ATLÁNTICO SUR
 id_jurisdiccion 24
===============================================================================

FUENTE — SIN SISTEMA OFICIAL FUNCIONANDO, SE USA UN DRIVE PÚBLICO
-------------------------------------------------------------------------------
El sistema propio de la provincia (https://recursosweb.tierradelfuego.gob.ar/
webapps/decoley/index.php, linkeado desde https://www.tierradelfuego.gob.ar/
boletin-oficial/) está confirmado por el usuario como no funcional / sin
ediciones 2026 cargadas. En su lugar, la propia web oficial deriva a una
carpeta de Google Drive pública donde se sube cada edición en PDF:

    https://drive.google.com/drive/folders/12GrKybtm4cWyS6Ib_DnbwKAQ6JvQHCU6

Estructura confirmada real por el usuario (y por el listado del conector de
Drive usado en esta sesión para reconocimiento -- ver más abajo "CÓMO SE
RECONOCIÓ", ese conector NO es el mecanismo de producción, sólo se usó para
explorar): carpeta año ("2026") -> carpeta mes ("07 - Julio", número de 2
dígitos + " - " + nombre de mes con inicial mayúscula) -> archivos
"B.O. NNNN.pdf" (con o sin espacio/punto variable), numerados
secuencialmente, el de mayor número es el más reciente. Existe además una
carpeta "SUMARIO 2026" con un PDF índice de todas las ediciones del año,
pero el usuario confirmó que ese índice se actualiza con demora ("no tiene
los últimos 2 [boletines]") -- por eso NO se usa como mecanismo de
descubrimiento, sólo queda anotado acá por si en el futuro sirve como
segunda fuente para completar metadatos.

DESCUBRIMIENTO EN PRODUCCIÓN — GOOGLE DRIVE API v3 CON API KEY
-------------------------------------------------------------------------------
La carpeta es pública ("cualquiera con el link"), así que la API de Drive
(v3) permite listar/descargar sin OAuth, sólo con una API key de un
proyecto de Google Cloud (gratis, se pide una vez -- ver GOOGLE_DRIVE_API_KEY
más abajo). Esto NO se pudo probar en vivo dentro de esta sesión: mi propio
sandbox de desarrollo tiene bloqueado por allowlist tanto drive.google.com
como las descargas directas (403 blocked-by-allowlist, confirmado real
contra varias URLs de Drive), y la key todavía no existía al escribir este
módulo (el usuario la estaba generando en paralelo). El código de
descubrimiento/descarga (_drive_listar / _descargar_drive_streaming) sigue
el contrato documentado de la API de Google (GET
https://www.googleapis.com/drive/v3/files con ?q=...&key=... para listar,
?alt=media&key=... para bajar el binario) pero NO tiene una corrida real
propia que lo confirme -- es lo primero a validar apenas haya
GOOGLE_DRIVE_API_KEY (con --dry-run alcanza para ver si encuentra la
carpeta/año/mes/archivo correctos antes de tocar el backend).

DESCUBRIMIENTO: SIEMPRE LA ÚLTIMA EDICIÓN DISPONIBLE (no "la de hoy") — confirmado real
-------------------------------------------------------------------------------
Bug real encontrado por el usuario corriendo desde el front (producción, sin
--fecha): el 03/08/2026 el bot avisó que no pudo encontrar la última versión
porque _ultima_edicion_en_carpeta exigía la carpeta EXACTA del mes de
fecha_objetivo (default date.today() cuando no hay --fecha), y agosto
todavía no tenía carpeta/archivos en Drive -- la provincia no había subido
nada de agosto, la última edición real seguía siendo B.O. 6136 (31/07). Es
el mismo síntoma que ya había aparecido antes en esta sesión ("Aviso: no se
encontró la carpeta del mes (Agosto 2026) en Drive.") y calza con el propio
índice SUMARIO, que confirma que la publicación va con demora (ver arriba,
"no tiene los últimos 2 [boletines]").

Corregido: _ultima_edicion_en_carpeta ya NO exige que el mes de
fecha_objetivo tenga carpeta/archivos -- arranca ahí y, si no encuentra nada
válido, prueba mes a mes hacia atrás (con acarreo de año) hasta
MESES_ATRAS_MAXIMO (12) antes de darse por vencido. Esto se aplica siempre,
tanto con --fecha explícito como con el default (hoy), así que una corrida
sin --fecha (el caso real del front/cron de producción) siempre trae la
verdadera última edición publicada, sin importar si el mes calendario
actual ya tiene algo subido. La lógica de "¿ya se procesó?" (estado local
_leer_estado/_escribir_estado + verificar_boletin_procesado contra el
backend, ambas preexistentes y sin cambios) sigue siendo la que decide,
sobre esa última edición real, si hace falta procesarla de nuevo o no.

TAMAÑO Y VARIABILIDAD DE LOS PDF — CONFIRMADO REAL
-------------------------------------------------------------------------------
El usuario reportó pesos "como 300 MB" y confirmó real que la edición del
31/07/2026 (N° 6136, la muestra de 25 páginas que se analizó) tiene 305
páginas; la edición del día anterior pesaba "31 mb" -- variación real de
más de 10x de un día a otro, no hay tamaño fijo asumible. El visor propio
de Drive no pudo abrir el archivo de 300+MB (confirmado por el usuario) --
la única vía viable es descarga directa vía API + streaming a disco (ver
_descargar_drive_streaming), nunca a memoria.

QUÉ SE RECONOCIÓ REAL: LA MUESTRA DE 25 PÁGINAS (edición N° 6136, 31/07/2026)
-------------------------------------------------------------------------------
El usuario subió las primeras 25 páginas de la última edición (de 305
totales) como PDF. Reconocimiento hecho con PyMuPDF (fitz) porque el
pipeline de Read de este entorno no pudo abrir el PDF directo (poppler:
"No display font for Symbol/ArialUnicode") -- PyMuPDF sí lo abrió sin
problema y es la librería elegida para todo el módulo (reemplaza a
pdfplumber, que usan el resto de los bots de la familia; acá no aplica
porque el contenido es imagen, no texto de columnas).

Composición real de esas 25 páginas: págs. 1-3 son la Resolución del
Ministerio de Obras y Servicios Públicos (Expte. MOSP-E-61817-2026,
Licitación Privada N° 02/2026); págs. 4-25 (el resto de TODA la muestra) son
un aviso + anexo (Pliego de Bases y Condiciones) de ESA MISMA Resolución --
es decir, en 25 páginas reales sólo se vio UN acto administrativo completo.
Esto es la base del hallazgo central del plan (ver "CLASIFICACIÓN DE
PÁGINA" abajo): en este boletín, un acto corto puede venir con un anexo
desproporcionadamente largo, y eso -- no la cantidad de actos -- es lo que
probablemente explica el peso/página-count tan variable día a día.

CLASIFICACIÓN DE PÁGINA: NORMA (escaneada) vs. ANEXO (vectorial) —
CONFIRMADO REAL EN 1 TRANSICIÓN
-------------------------------------------------------------------------------
Págs. 1-3 (el acto): cada página tiene 2-3 imágenes JPEG incrustadas reales
(confirmado con page.get_images(full=True) -- página 2 trae una imagen de
948x1171px que es el escaneo real de todo el cuerpo del acto). Págs. 4-25
(el anexo/Pliego): CERO imágenes incrustadas en las 22 páginas (confirmado
real, get_images() devuelve lista vacía en las 22), pero el contenido SÍ es
visualmente texto nítido -- porque no es un escaneo, es contenido
vectorial nativo (confirmado con page.get_drawings(): 4198 trazos
vectoriales en la página 5) generado digitalmente (probablemente exportado
de Word/LibreOffice) sin mapeo de texto real a Unicode (get_text() no
devuelve nada útil ahí). Ambos tipos de página "se ven" como texto
perfecto al ojo, pero son técnicamente muy distintos.

Esta diferencia -- ¿tiene la página alguna imagen incrustada, sí o no? -- es
la señal usada por _bloques_norma para separar qué páginas son candidatas a
contener el cuerpo real de un acto (se las OCRea) de cuáles son anexo (NO
se OCRean, sólo se cuenta cuántas hay -- ver más abajo). Es una señal
barata (no hace falta abrir/renderizar nada, sólo mirar los metadatos de la
página) y coincide exactamente con el cambio real de tamaño/orientación de
página visto en la muestra (A4 vertical 595x842 en 1-3, Letter apaisado
792x612 en 4-25) -- ambas señales coinciden en el mismo corte, lo que da
más confianza. SIN CONFIRMAR: si esta señal se sostiene en ediciones sin
Pliegos/anexos grandes, o si algún acto futuro viene también como
contenido vectorial en vez de escaneado (en ese caso, esta versión del bot
lo trataría como anexo y lo perdería -- ver "QUÉ FALTA VALIDAR").

EXTRACCIÓN HÍBRIDA POR PÁGINA: TEXTO VECTORIAL (encabezado) + OCR (cuerpo)
-------------------------------------------------------------------------------
Hallazgo real no anticipado en el plan original: dentro de una página de
tipo "norma" (con imagen incrustada), el encabezado de cada acto ("DECRETO
N° 367", fecha "29-07-26", el rótulo de color "RESOLUCIÓN" / "MINISTERIO DE
OBRAS Y SERVICIOS PÚBLICOS", y la línea "Ushuaia, Viernes 31 de Julio de
2026") NO forma parte de la imagen escaneada -- es texto vectorial real,
agregado aparte (probablemente por el sistema de publicación del boletín
como una plantilla sobre el escaneo del acto en sí). Confirmado real
extrayendo page.get_text("words") de la página 1 y viendo esas líneas con
coordenadas y contenido correctos -- mientras que la imagen incrustada más
grande de esa misma página (extraída y OCReada por separado) arranca recién
en "VISTO el Expediente...", sin el encabezado. Por eso _texto_pagina_norma
combina las DOS fuentes por página: el texto vectorial real (barato, sin
OCR, 100% preciso -- se usa sólo para pescar el encabezado con
RE_HEADER_NORMA/RE_FECHA_PORTADA) + el OCR de la imagen incrustada más
grande (para el cuerpo VISTO/CONSIDERANDO/DECRETA-o-RESUELVE/firma).

ADVERTENCIA REAL: en esta misma página 1, page.get_text() también devuelve
texto SUELTO de una edición anterior (encabezado "AÑO XXXIV - Ushuaia,
Lunes 02 de Enero de 2025 - N° 5363" mezclado con el contenido real y
correcto de la edición actual) -- se confirmó que es sólo esa línea de
masthead vieja (no un "DECRETO N° ..." viejo duplicado que pudiera
confundir la extracción del encabezado real), pero es evidencia de que este
PDF se arma reciclando una plantilla con objetos de texto de ediciones
previas sin limpiar del todo. RE_HEADER_NORMA / RE_FECHA_PORTADA buscan
patrones específicos (no "cualquier texto"), así que en la muestra
disponible este ruido no generó falsos positivos -- pero es una fuente de
riesgo real a tener en cuenta si aparecen síntomas raros en producción.

AMBIGÜEDAD REAL SIN RESOLVER: EL "DECRETO N° 367" NO PARECE SER EL TIPO
NI EL NÚMERO PROPIO DEL ACTO
-------------------------------------------------------------------------------
El único acto de la muestra trae el rótulo "DECRETO N° 367" en texto
vectorial, PERO el rótulo de color inmediatamente debajo dice "RESOLUCIÓN"
y el cuerpo cierra con "EL MINISTRO DE OBRAS Y SERVICIOS PÚBLICOS RESUELVE"
(no "DECRETA") -- es decir, es una Resolución, no un Decreto, a pesar de la
etiqueta. En ningún lugar de las 3 páginas del acto aparece un número de
Resolución propio (tipo "RESOLUCIÓN N° X"). La hipótesis más razonable es
que "DECRETO N° 367" sea un correlativo interno/administrativo del sistema
de publicación del boletín (una numeración única para todos los actos
publicados, sin relación con el tipo legal real de cada uno) -- pero esto
es UNA HIPÓTESIS, no algo confirmado, porque sólo hay 1 ejemplo. Se optó
por: TIPO se toma del rótulo de color (RESOLUCIÓN/DECRETO/LEY/DISPOSICIÓN,
ver RE_TIPO_BANNER) y del verbo operativo del cuerpo como respaldo
(DECRETA/RESUELVE/SANCIONA -- ver _tipo_desde_cuerpo), NUNCA de la palabra
que acompaña a "N°" en el encabezado; NÚMERO sí se toma de esa línea
("367") por ser el único número disponible, aunque su rótulo diga
"DECRETO" incluso cuando el tipo real es otro. Esto puede estar mal --
qué significa realmentee ese número y si el tipo real tiene ADEMÁS su
propio número en otro lado es la duda más importante pendiente de validar
contra una edición con más de un acto (ver "QUÉ FALTA VALIDAR").

BUG REAL: ORIENTACIÓN DE LA IMAGEN CRUDA (corregido, ver DPI_RENDER_OCR)
-------------------------------------------------------------------------------
Contra la edición completa real (6136, 305 páginas) apareció un bug que la
muestra de 25 páginas no mostraba: doc.extract_image() puede devolver los
bytes de una imagen incrustada en una orientación DISTINTA a como se ve
realmente en la página, porque el PDF le aplica una rotación/transformación
al mostrarla que extract_image() no aplica (la bypasea). Síntoma real
confirmado: OCR sobre los bytes crudos de la página 49 daba texto en
español reconocible pero desordenado/mal leído; la MISMA página, renderizada
con page.get_pixmap() (que sí aplica esa transformación siempre) y luego
OCReada, salió perfecta. Recortar la imagen cruda en mitades no lo arreglaba
(descartando la hipótesis de "columnas confundidas") -- sólo renderizar la
página lo resuelve. Por eso _texto_pagina_norma renderiza con
page.get_pixmap(dpi=DPI_RENDER_OCR) en vez de extraer+OCRear la imagen
incrustada cruda.

BUG REAL: PÁGINA APAISADA = 2 MEDIAS PÁGINAS ESCANEADAS LADO A LADO
-------------------------------------------------------------------------------
Encontrado al resolver el bug anterior: en la corrida real completa, cada
página de tipo "norma" que es APAISADA (ancho > alto -- confirmado real:
792x612pt, el mismo tamaño "Letter apaisado" ya visto en los anexos
vectoriales de la muestra chica) resulta ser en realidad 2 medias páginas
físicas escaneadas independientes, puestas lado a lado en una sola página
de PDF (no 1 página de contenido corrido) -- p.ej. la página separadora de
la sección "RESOLUCIONES ... N° 183 a 215" a la izquierda + el inicio de la
Resolución 183 a la derecha; más adelante, el cierre de la Resolución 183 a
la izquierda + el inicio completo de la 184 a la derecha. Si se OCRea la
página apaisada COMPLETA de una sola vez, Tesseract a veces (no siempre --
parece depender de cuán parecidas en densidad/ancho de columna son ambas
mitades) confunde su propia segmentación automática y trata las 2 mitades
como si fueran 2 columnas de UN solo documento, intercalando líneas de
ambas -- confirmado real: los artículos de cierre de la Resolución 183 y el
VISTO/CONSIDERANDO de la 184 salieron mezclados línea por línea,
ilegibles. Las páginas VERTICALES (retrato, ancho < alto -- p.ej. las 3
páginas del acto 367) no tienen este problema, son 1 sola página real.

Arreglo: _texto_pagina_norma, cuando la página es apaisada, la corta en
mitad izquierda/derecha (page.get_pixmap con clip=fitz.Rect(...)) y OCREA
CADA MITAD POR SEPARADO, concatenando izquierda + derecha (ese es el orden
de lectura real). Confirmado real en A/B contra la misma página: la versión
cortada salió perfectamente ordenada y legible en ambos casos probados
(la página "segura" que ya salía bien entera, y la que salía mezclada
entera) -- cortar nunca empeoró el resultado, así que se aplica siempre que
la página es apaisada, sin intentar adivinar caso por caso si hace falta.

CONVENCIÓN B: ACTOS SIN BANNER VECTORIAL, ENCABEZADO EN EL CUERPO ESCANEADO
-------------------------------------------------------------------------------
Todo el diseño original de _dividir_normas / _campos_norma / _tipo_desde_bloque
/ _emisor_desde_cuerpo estaba hecho sólo contra el acto 367 (Convención A:
banner vectorial de color "TIPO N° NUMERO" + fecha "dd-mm-aa" como texto
vectorial aparte, cuerpo escaneado que arranca directo en "VISTO..."). La
corrida real completa mostró que NO es la única convención: las
Resoluciones S.C.A.G. (Secretaría de Coordinación Administrativa del
Gobernador) 183 a 215 -- 33 actos en un solo tramo real, precedidos por una
página separadora "RESOLUCIONES / SECRETARÍA DE COORDINACIÓN
ADMINISTRATIVA DEL GOBERNADOR / N° 183 a 215 / Año 2026" -- NO tienen
ningún banner vectorial: el ÚNICO encabezado es la primera línea del propio
cuerpo escaneado, "USHUAIA," (o "RÍO GRANDE," / "TOLHUIN," según qué
localidad se cita) seguida de la fecha, en 2 formatos reales distintos:
abreviado ("0 2 JUN. 2026", con basura de OCR real y variable pegada entre
los 2 dígitos del día -- espacio, o incluso un "!" suelto, ver
RE_FECHA_ABREV_CAPTURA) o completo con día de semana opcional ("martes 28
de julio de 2026", visto en el Acta de Preadjudicación de IPVyH). El acto
cierra, pegado a la firma, con "RESOLUCIÓN [SIGLA] N° {numero} /{año, 4
dígitos}.-" (confirmado real: "RESOLUCIÓN S.C.A.G. N° 183 /2026.-") --
distinguible de las citas a OTRAS normas dentro del propio CONSIDERANDO
porque esas usan año abreviado de 2 dígitos ("Decretos Provinciales N°
3226/23"), nunca 4.

RE_CIUDAD_FECHA / RE_DIVISOR_NORMA usan esa línea "CIUDAD, fecha" como
divisor alternativo (además del banner de Convención A, nunca en
reemplazo); RE_NUMERO_CIERRE pesca el número+año de cierre. Riesgo real
evaluado y descartado: el cuerpo de la Resolución 183 menciona "saliendo de
la ciudad de Ushuaia, Provincia de Tierra del Fuego" en medio de una
oración -- como el patrón exige la fecha COMPLETA inmediatamente después de
la coma, "Provincia de..." nunca matchea y no genera un corte falso ahí
(confirmado real, no partió el acto 183 en 2).

LIMITACIÓN REAL ACEPTADA: el número de cierre a veces pierde dígitos en el
OCR incluso con la página ya separada en mitades y renderizada a 200 DPI
(confirmado real: "RESOLUCIÓN S.C.A.G. N°1 /2026.-" en vez de "N° 184",
sólo 1 de 3 dígitos sobrevivió) -- _campos_norma exige mínimo 2 dígitos
para aceptar ese número, así que un caso así queda '?' en vez de un valor
corto y con mucha confianza de estar mal. De igual forma, el AÑO de la
fecha de apertura ocasionalmente se lee mal por 1 dígito (confirmado real:
"2026" leído "2025" en 2 de 12 actos de una corrida real de prueba, un
error clásico de confusión 5/6 en la fuente de este sello en particular).
Ninguno de los dos se corrige a ciegas (mismo criterio que el resto de
RE_GRADO_* en _limpiar_texto_ocr: preferir un error visible/'?' antes que
una corrección especulativa que podría estar compensando para el lado
equivocado en otro caso real). El emisor y la síntesis, en cambio, salieron
correctos en el 100% de los 12 actos reales probados en este tramo (ver
QUÉ FALTA VALIDAR) -- son campos más robustos al ruido de OCR porque no
dependen de leer bien 3-4 caracteres puntuales.

CONVENCIÓN C: NOTA-AT / ACTA DE PREADJUDICACIÓN (vista, NO manejada aún)
-------------------------------------------------------------------------------
Página 291 real (IPVyH -- Instituto Provincial de Vivienda y Hábitat)
mostró un tercer formato: "NOTA-AT-2858-2026" + título "ACTA DE
PREADJUDICACIÓN" + "Ushuaia, martes 28 de julio de 2026" (formato de fecha
completo, cubierto por RE_CIUDAD_FECHA/_FECHA_LARGA_PAT) -- pero el TIPO de
acto ("ACTA DE PREADJUDICACIÓN") no es DECRETO/RESOLUCIÓN/LEY/DISPOSICIÓN,
así que ni RE_TIPO_BANNER ni el verbo operativo (RESUELVE/DECRETA) lo
reconocen -- _tipo_desde_bloque cae al default 'RESOLUCION', que es
probablemente incorrecto para este caso. Si RE_CIUDAD_FECHA lo separa bien
como bloque (probable, no confirmado con una corrida real completa sobre
esa página) igual se envía, sólo con el tipo mal etiquetado -- pendiente de
un ejemplo real más para decidir si hace falta un tipo nuevo o si alcanza
con ajustar PATRONES_INDIVIDUAL/GENERAL para que "ACTA DE PREADJUDICACIÓN"
clasifique razonable aunque el campo tipo diga RESOLUCION.

BUGS REALES ENCONTRADOS EN LA PRIMERA CORRIDA COMPLETA (305 PÁGINAS)
-------------------------------------------------------------------------------
Con los 3 arreglos de arriba (rotación, página apaisada, Convención B) el
usuario corrió el bot contra la edición completa real y encontró 40 actos
(subiendo de 12, todos rotos, en la corrida anterior a esos arreglos) --
pero 5 problemas más salieron a la luz, sólo visibles contra el documento
ENTERO (nunca aparecieron en las muestras chicas):

(1) ENCABEZADO REPETIDO POR PÁGINA: cuando un acto de Convención A ocupa
2+ páginas, su banner "TIPO N° NUMERO" a veces se reimprime en cada
página (no sólo en la primera) -- confirmado real: el acto 367 (3
páginas) salió partido en 3 "actos", uno de ellos sólo el rótulo+roster
de ministros de la página 1 (sin cuerpo real todavía en esa página).

(2) FALSO POSITIVO DEL PROPIO MASTHEAD: la fecha del masthead del
boletín ("Ushuaia, Viernes 31 de Julio de 2026", repetida en CADA
página) tiene la misma forma que un encabezado de Convención B ("CIUDAD,
fecha completa") y se colaba como acto fantasma.

Arreglo de (1) y (2): RE_DIVISOR_NORMA (y el filtro de _dividir_normas,
que ahora REUSA RE_DIVISOR_NORMA en vez de RE_HEADER_NORMA/RE_CIUDAD_FECHA
sueltas) exige que "VISTO" aparezca cerca del encabezado -- ventana de
~220 caracteres para Convención A (deja margen a un banner largo entre
encabezado y VISTO, medido real contra el acto 367) y ~40 para Convención
B (el VISTO real siempre viene pegado, 1 salto de línea). Esto también
excluyó, como beneficio colateral, edictos judiciales/electorales que
también abren con "Ciudad, fecha" pero nunca traen VISTO cerca.

(3) NÚMERO CRUZADO DE CITAS INTERNAS: el CONSIDERANDO de un acto de
Convención B casi siempre cita OTRAS normas con la misma forma "RESOLUCIÓN
[SIGLA] N° numero/año" -- a veces con año de 4 dígitos también, no sólo
abreviado de 2 (confirmado real: "Resolución M.E. N° 148/2024" citada
como fundamento legal en 3 actos reales DISTINTOS, todos terminando con
numero=148 en vez de su propio número real). Arreglo: RE_NUMERO_CIERRE
usa el ÚLTIMO match dentro del bloque, no el primero -- el cierre
verdadero siempre está pegado a la firma, al final. De paso se encontró
una 4ta variante real de símbolo de grado mal leído: "N>" (mayor-que,
además de *，?，”，"，').

(4) ANEXO/ACTA CONTABLE/EDICTO COLADO COMO ACTO FALSO: páginas de
Pliego/Anexo técnico (con una imagen incrustada -- diagramas, tablas --
suficientemente grande para pasar AREA_MINIMA_IMAGEN_NORMA) que NO son
un acto real, sin ningún encabezado reconocible, se mandaban igual como
acto genérico ("RESOLUCION ?/2026", emisor genérico) por el fallback "sin
divisor -> mandar como 1 solo acto". Confirmado real en 3 formas
distintas: especificaciones técnicas de un Pliego (tablas de
conductores), una rendición contable de Fondo Permanente, y una nota de
un Juzgado Electoral sobre estados contables de un partido político.
Arreglo: ese fallback ahora exige además que el bloque contenga alguna de
VISTO/CONSIDERANDO/RESUELVE/DECRETA/SANCIONA/ARTÍCULO (ver
RE_PARECE_ACTO) -- señal barata de que es un acto administrativo real
aunque su encabezado propio haya salido ilegible del OCR.

(5) SÍNTESIS CRUZADA ENTRE ACTOS DISTINTOS: cuando un bloque no tiene
NINGUNO de los cierres de CONSIDERANDO esperados (típico de la Convención
C -- cierra con "SUGIERE" en vez de "RESUELVE"/"DECRETA"/"Por ello"), la
captura no perezosa de RE_CONSIDERANDO seguía creciendo sin límite y
terminaba agarrando contenido de un acto/aviso TOTALMENTE distinto,
publicado miles de caracteres más adelante en el mismo bloque de varias
páginas -- confirmado real: el Acta de Preadjudicación de IPVyH (página
291) terminó con la síntesis de un Aviso de licitación no relacionado.
Arreglo: se agregó "SUGIERE" como terminador reconocido (corta el Acta en
el lugar correcto, mucho antes del Aviso) MÁS un tope duro de 15.000
caracteres como red de seguridad de último recurso para cualquier cierre
todavía no visto -- el tope tuvo que ser generoso a propósito: un tope
más chico (2500) rompía el CONSIDERANDO real más largo confirmado (acto
367, 7546 caracteres hasta su propio "Por ello:").

De 40 actos "encontrados" en esa corrida, con estos 5 arreglos aplicados
contra el mismo texto real (re-procesado, no una corrida nueva contra el
PDF) el conteo bajó a 30 -- los 10 que se fueron eran justamente los 3
pedazos duplicados del acto 367 (ahora 1) + las 3 citas cruzadas de
numero=148 (ahora números reales distintos, no eliminadas, sólo
corregidas) + 4 páginas de anexo/rendición/edicto que ya no se mandan
como actos falsos.

OCR — TESSERACT + MODELO EN ESPAÑOL, VALIDADO REAL
-------------------------------------------------------------------------------
Se probó Tesseract 4.1.1 sobre la imagen incrustada de la página 2 (JPEG
948x1171px, ~110-150 DPI efectivos) primero con el modelo en inglés (proxy,
porque el paquete de idioma español no venía instalado en este sandbox) y
el resultado ya era muy legible, con errores sólo en tildes -- esperable
por usar el modelo equivocado. Después se consiguió el modelo real en
español SIN necesitar root: `apt-get download tesseract-ocr-spa` (a
diferencia de `apt-get install`, `download` sólo baja el .deb a disco, no
toca la base de datos de dpkg, así que no pide privilegios) + `dpkg-deb -x`
para extraer el .traineddata del .deb sin instalarlo. Con el modelo real en
español, el mismo texto salió prácticamente perfecto -- tildes correctas
("aprobación", "Energía Eléctrica", "Resolución"), sólo 2 artefactos
menores y sistemáticos: el símbolo "°" se lee a veces como "*" o "?"
pegado a "N" o a un número (ver RE_GRADO_* en _limpiar_texto_ocr) -- el
resto es ruido de OCR genérico sin patrón corregible (errores sueltos de
1 carácter en palabras aisladas, ver "esta imbuido" -> ninguna corrección
específica, es ruido de fondo esperable e inevitable de cualquier OCR, ni
Santiago del Estero -que no usa OCR- tiene ese tipo de error).

En PRODUCCIÓN (servidor del usuario, con root real) el paquete se instala
normal: `apt-get install tesseract-ocr-spa`, sin necesidad del rodeo de
`download` + extracción manual que hizo falta acá sólo por no tener sudo en
este sandbox. TESSERACT_LANG/TESSDATA_PREFIX son configurables por env var
por si hace falta un idioma o una ruta de datos distinta; TESSDATA_PREFIX
puede quedar vacío en producción (tesseract usa su ubicación estándar sola).

SÍNTESIS — HEURÍSTICA NUEVA, DISTINTA AL RESTO DE LA FAMILIA
-------------------------------------------------------------------------------
Esta edición no tiene una línea "Referencia:" como Santiago del Estero.
_sintesis_desde_cuerpo intenta, en orden: (1) el texto entre comillas después
de "denominados:"/"denominado:" (frecuente en actos de obra pública/
licitación -- confirmado real: `denominados: "SUMINISTRO ELÉCTRICO A PLANTA
DEPURADORA EN LA MARGEN SUR, RÍO GRANDE"`); si no aparece, (2) la primera
oración "Que ..." del bloque CONSIDERANDO (fórmula casi universal en actos
administrativos argentinos, más genérica que "denominados:" pero no
probada contra otros tipos de acto reales -- sólo se vio éste); si tampoco
hay CONSIDERANDO reconocible, (3) "{TIPO} {NUMERO}/{AÑO}" como en el resto
de la familia. SIN VALIDAR contra un Decreto de personal/designación real
(fraseología probablemente muy distinta a un acto de obra pública).

DESCARGA Y ESTADO LOCAL — EVITAR RE-DESCARGAR 300+MB SIN NECESIDAD
-------------------------------------------------------------------------------
A diferencia del resto de la familia, acá una corrida "no hay nada nuevo"
NO es gratis: si no hubiera forma de saber de antemano que ya se procesó
la última edición, cada corrida (aunque no haya edición nueva) bajaría el
PDF completo igual. Para evitar eso, el bot guarda el número de la última
edición ya procesada con éxito en un archivo de estado local (ver
ARCHIVO_ESTADO, junto al script por default) y lo compara contra el número
más alto listado en Drive ANTES de descargar nada -- sólo se descarga si
el número de Drive es mayor. Esto es una optimización propia del bot
(nunca se descarga de más), separada e independiente del chequeo estándar
de verificar_boletin_procesado contra el backend (que sigue siendo la
verdad final para no reenviar normas -- por si el archivo de estado local
se pierde/reinicia en un redeploy, ese chequeo contra el backend sigue
evitando duplicados aunque el archivo local no exista).

QUÉ SE VALIDÓ CONTRA LA EDICIÓN REAL COMPLETA (6136, 305 páginas, 31/07/2026)
-------------------------------------------------------------------------------
- GOOGLE_DRIVE_API_KEY contra la carpeta real: CONFIRMADO funcionando
  (descubrimiento año/mes/archivo + descarga streaming, con la key real del
  usuario).
- Un segundo (y tercer, ..., decimosegundo) acto real en la misma edición:
  CONFIRMADO -- ver "CONVENCIÓN B" arriba. RE_DIVISOR_NORMA separa bien
  corridas largas de actos (probado real contra 12 actos consecutivos,
  Resoluciones S.C.A.G. 183-19x).
- El bug de orientación de imagen cruda y el de página apaisada = 2 medias
  páginas (ver ambos arriba): CONFIRMADOS y arreglados, con A/B real.
- Emisor y síntesis de la Convención B: CONFIRMADOS correctos en el 100%
  de los 12 actos reales probados en el tramo 183-19x.
- Corrida real COMPLETA contra las 305 páginas (no una muestra): pasó de
  12 bloques (10 rotos) a 40 actos, y con los 5 arreglos de "BUGS REALES
  ENCONTRADOS EN LA PRIMERA CORRIDA COMPLETA" (ver abajo) a 30 actos
  limpios -- sin duplicados, sin números cruzados entre actos distintos,
  sin páginas de anexo/rendición/edicto coladas como actos falsos.

QUÉ FALTA VALIDAR (real, pendiente)
-------------------------------------------------------------------------------
- Qué es realmente el número "367" del único acto de Convención A visto
  (¿correlativo interno? ¿el verdadero número de Decreto/Resolución? --
  ver "AMBIGÜEDAD REAL SIN RESOLVER"). Sigue sin verse un segundo ejemplo
  de esta convención para comparar.
- Un Decreto real (firmado "DECRETA", no "RESUELVE") para confirmar que
  RE_TIPO_BANNER / _tipo_desde_cuerpo lo reconocen bien.
- Convención C (NOTA-AT / ACTA DE PREADJUDICACIÓN, página 291) -- vista
  pero no probada con una corrida real completa sobre esa página, ver
  arriba.
- Fraseología real de un acto de personal (designación/renuncia/sumario)
  contra PATRONES_INDIVIDUAL (reusado tal cual del resto de la familia,
  nunca ejercitado contra un ejemplo de Tierra del Fuego -- las
  Resoluciones S.C.A.G. vistas son todas de comisión de servicio/viáticos,
  un tipo de acto distinto).
- Estabilidad de la señal "página con imagen = norma" en ediciones sin
  anexos grandes, o con anexos que SÍ vienen escaneados (en vez de
  vectoriales) -- en ese caso se OCRearían de más (no se pierde nada, pero
  se procesa innecesariamente).
- Pérdida ocasional de dígitos del OCR en el número de cierre y el año de
  apertura de la Convención B (ver "LIMITACIÓN REAL ACEPTADA" arriba) --
  aceptado tal cual, no se intentó corregir a ciegas.
===============================================================================
"""

import io
import os
import re
import sys
import json
import time
import argparse
import tempfile
import unicodedata
import subprocess
from datetime import date, datetime

import requests

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


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

# Ver docstring "DESCUBRIMIENTO EN PRODUCCIÓN" -- generada por el usuario en
# Google Cloud Console, sólo necesita Drive API v3 habilitada (contenido
# público, no hace falta OAuth).
GOOGLE_DRIVE_API_KEY = get_env_clean('GOOGLE_DRIVE_API_KEY', 'AIzaSyDJZDXTxD-k6AfwTgD5T7RSyu9awwYMsZo')
CARPETA_RAIZ_DRIVE = get_env_clean('CARPETA_RAIZ_DRIVE_TDF', '12GrKybtm4cWyS6Ib_DnbwKAQ6JvQHCU6')
DRIVE_API_BASE = 'https://www.googleapis.com/drive/v3'
# Ver docstring "DESCUBRIMIENTO: SIEMPRE LA ÚLTIMA EDICIÓN DISPONIBLE" --
# cuántos meses hacia atrás probar si el mes objetivo (por default, hoy)
# todavía no tiene carpeta/archivos en Drive, antes de darse por vencido.
MESES_ATRAS_MAXIMO = 12

TESSERACT_LANG = get_env_clean('TESSERACT_LANG', 'spa')
# Vacío por default: en producción (con tesseract-ocr-spa instalado por
# apt) no hace falta -- ver docstring "OCR".
TESSDATA_PREFIX = get_env_clean('TESSDATA_PREFIX', '')

ARCHIVO_ESTADO = get_env_clean(
    'ARCHIVO_ESTADO_TDF',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '.ultimo_numero_tierradelfuego.txt'))

REINTENTOS = 3
ESPERA_REINTENTO = 3
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700

# DPI para renderizar una página completa antes de OCRearla -- ver docstring
# "BUG REAL: ORIENTACIÓN DE LA IMAGEN CRUDA". 200 da una resolución igual o
# mejor que la de las imágenes incrustadas originales (~150-180 DPI
# efectivos medidos reales) sin generar archivos temporales enormes.
DPI_RENDER_OCR = 200


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


NOMBRE_MES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
}
MES_NUMERO = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SETIEMBRE': 9, 'SEPTIEMBRE': 9, 'OCTUBRE': 10,
    'NOVIEMBRE': 11, 'DICIEMBRE': 12,
    # Abreviaturas de 3 letras -- confirmado real en el formato de fecha de
    # la Convención B (ver docstring), p.ej. "USHUAIA, 02 JUN. 2026".
    'ENE': 1, 'FEB': 2, 'MAR': 3, 'ABR': 4, 'MAY': 5, 'JUN': 6,
    'JUL': 7, 'AGO': 8, 'SET': 9, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DIC': 12,
}


def _anio_completo(yy):
    """'26' -> 2026. Umbral arbitrario pero razonable para el rango de años
    en que este bot va a estar en uso."""
    n = int(yy)
    return 2000 + n if n <= 79 else 1900 + n


# ===========================================================================
# GOOGLE DRIVE — DESCUBRIMIENTO Y DESCARGA (ver docstring, sin confirmar en vivo)
# ===========================================================================
def _drive_listar(parent_id, solo_carpetas=False, timeout=30):
    """[{'id', 'name', 'mimeType', 'size', 'modifiedTime'}, ...] de los
    hijos directos de parent_id. None si falla la llamada (sin key, error
    de red, permiso, etc.) -- distinto de [] = la carpeta existe y está
    vacía."""
    if not GOOGLE_DRIVE_API_KEY:
        print("Aviso: falta GOOGLE_DRIVE_API_KEY.", file=sys.stderr)
        return None
    q = f"'{parent_id}' in parents and trashed = false"
    if solo_carpetas:
        q += " and mimeType = 'application/vnd.google-apps.folder'"
    params = {
        'q': q,
        'key': GOOGLE_DRIVE_API_KEY,
        'fields': 'nextPageToken, files(id,name,mimeType,size,modifiedTime)',
        'pageSize': 200,
    }
    url = f'{DRIVE_API_BASE}/files'
    archivos = []
    for intento in range(1, REINTENTOS + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code != 200:
                if r.status_code < 500:
                    print(f"Aviso: Drive API {r.status_code} listando {parent_id}: "
                          f"{r.text[:200]}", file=sys.stderr)
                    return None
                raise requests.RequestException(f'HTTP {r.status_code}')
            data = r.json()
            archivos.extend(data.get('files', []))
            page_token = data.get('nextPageToken')
            while page_token:
                params['pageToken'] = page_token
                r2 = requests.get(url, params=params, timeout=timeout)
                if r2.status_code != 200:
                    break
                data2 = r2.json()
                archivos.extend(data2.get('files', []))
                page_token = data2.get('nextPageToken')
            return archivos
        except requests.RequestException as e:
            if intento == REINTENTOS:
                print(f"Aviso: error de red en Drive API: {e}", file=sys.stderr)
                return None
            time.sleep(ESPERA_REINTENTO * intento)
    return None


def _buscar_subcarpeta(parent_id, nombre_contiene):
    """id de la primera subcarpeta directa de parent_id cuyo nombre
    contenga nombre_contiene (sin acentos, case-insensitive). None si no
    está o si falla la consulta."""
    hijos = _drive_listar(parent_id, solo_carpetas=True)
    if hijos is None:
        return None
    objetivo = _sin_acentos(nombre_contiene).upper()
    for h in hijos:
        if objetivo in _sin_acentos(h['name']).upper():
            return h['id']
    return None


RE_NUMERO_ARCHIVO = re.compile(r'B\.?\s*O\.?\s*(\d+)', re.IGNORECASE)


def _archivos_boletin_en_mes(anio, mes_numero):
    """[(numero, archivo_drive_dict), ...] ordenado de mayor a menor
    número, de los "B.O. NNNN.pdf" reales dentro de la carpeta año/mes.
    [] si la carpeta de año o de mes no existe, está vacía, o ningún
    archivo matcheó el patrón esperado (ver stderr para el motivo
    puntual) -- cualquiera de estos casos es normal/esperable cuando se
    usa esta función para "tantear" un mes que todavía no tiene nada
    publicado, ver _ultima_edicion_en_carpeta."""
    carpeta_anio = _buscar_subcarpeta(CARPETA_RAIZ_DRIVE, str(anio))
    if not carpeta_anio:
        print(f"Aviso: no se encontró la carpeta del año {anio} en Drive.", file=sys.stderr)
        return []

    nombre_mes = NOMBRE_MES[mes_numero]
    carpeta_mes = _buscar_subcarpeta(carpeta_anio, nombre_mes)
    if not carpeta_mes:
        print(f"Aviso: no se encontró la carpeta del mes ({nombre_mes} {anio}) en Drive.",
              file=sys.stderr)
        return []

    archivos = _drive_listar(carpeta_mes)
    if not archivos:
        print(f"Aviso: la carpeta {anio}/{nombre_mes} no devolvió archivos.", file=sys.stderr)
        return []

    candidatos = []
    for a in archivos:
        if not a['name'].lower().endswith('.pdf'):
            continue
        m = RE_NUMERO_ARCHIVO.search(a['name'])
        if m:
            candidatos.append((int(m.group(1)), a))
    if not candidatos:
        print(f"Aviso: ningún archivo en {anio}/{nombre_mes} matcheó el patrón "
              f"'B.O. NNNN.pdf'.", file=sys.stderr)
        return []
    candidatos.sort(key=lambda t: t[0], reverse=True)
    return candidatos


def _ultima_edicion_en_carpeta(fecha_objetivo):
    """(archivo_drive_dict, numero) del "B.O. NNNN.pdf" de mayor número
    REALMENTE disponible en Drive -- ver docstring "DESCUBRIMIENTO:
    SIEMPRE LA ÚLTIMA EDICIÓN DISPONIBLE". Arranca en el mes de
    fecha_objetivo y, si ese mes todavía no tiene carpeta o archivos
    (p.ej. recién empezó el mes y la provincia no subió nada nuevo),
    sigue probando mes a mes hacia atrás (con acarreo de año) hasta
    MESES_ATRAS_MAXIMO en vez de fallar. (None, None) si no se encontró
    ninguna edición real en ningún mes probado (ver stderr para el
    detalle mes a mes)."""
    anio, mes = fecha_objetivo.year, fecha_objetivo.month
    for _ in range(MESES_ATRAS_MAXIMO):
        candidatos = _archivos_boletin_en_mes(anio, mes)
        if candidatos:
            numero, archivo = candidatos[0]
            if (anio, mes) != (fecha_objetivo.year, fecha_objetivo.month):
                print(f"Aviso: {NOMBRE_MES[fecha_objetivo.month]} {fecha_objetivo.year} "
                      f"todavía sin ediciones; se usa la última real disponible, "
                      f"{NOMBRE_MES[mes]} {anio} (B.O. {numero}).", file=sys.stderr)
            return archivo, numero
        mes -= 1
        if mes == 0:
            mes, anio = 12, anio - 1
    print(f"Aviso: no se encontró ninguna edición en los últimos {MESES_ATRAS_MAXIMO} "
          f"meses hacia atrás desde {NOMBRE_MES[fecha_objetivo.month]} {fecha_objetivo.year}.",
          file=sys.stderr)
    return None, None


def _descargar_drive_streaming(file_id, destino, timeout=300):
    """Descarga file_id a destino en disco, en streaming -- ver docstring
    "DESCARGA Y ESTADO LOCAL" (nunca a memoria, los PDF acá pueden pesar
    300+MB). True si se pudo."""
    url = f'{DRIVE_API_BASE}/files/{file_id}'
    params = {'key': GOOGLE_DRIVE_API_KEY, 'alt': 'media'}
    for intento in range(1, REINTENTOS + 1):
        try:
            with requests.get(url, params=params, stream=True, timeout=timeout) as r:
                if r.status_code != 200:
                    print(f"Aviso: descarga Drive HTTP {r.status_code} (intento {intento})",
                          file=sys.stderr)
                    if r.status_code < 500:
                        return False
                else:
                    with open(destino, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                f.write(chunk)
                    return True
        except requests.RequestException as e:
            print(f"Aviso: error de red descargando de Drive: {e} (intento {intento})",
                  file=sys.stderr)
        time.sleep(ESPERA_REINTENTO * intento)
    return False


# ===========================================================================
# ESTADO LOCAL — evitar redescargar si no hay edición nueva (ver docstring)
# ===========================================================================
def _leer_estado():
    try:
        with open(ARCHIVO_ESTADO, 'r', encoding='utf-8') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def _escribir_estado(numero):
    try:
        with open(ARCHIVO_ESTADO, 'w', encoding='utf-8') as f:
            f.write(str(numero))
    except OSError as e:
        print(f"Aviso: no se pudo guardar el estado local: {e}", file=sys.stderr)


# ===========================================================================
# CLASIFICACIÓN DE PÁGINA: NORMA (imagen incrustada) vs. ANEXO (vectorial)
# ver docstring "CLASIFICACIÓN DE PÁGINA"
# ===========================================================================
# Área mínima (ancho x alto en píxeles) para que una imagen incrustada
# cuente como "posible escaneo de cuerpo de acto" -- BUG REAL encontrado en
# la primera corrida completa (edición 6136, 305 páginas): páginas de
# portada/aviso puramente vectoriales (igual que el Pliego, ver docstring
# "CLASIFICACIÓN DE PÁGINA") pueden tener escudos/sellos chicos incrustados
# como parte del membrete (confirmado real: página 4 de la muestra --el
# "AVISO" de la Licitación-- tiene 3 imágenes chicas, 20x365/350x366/
# 259x296, ningún escaneo real) -- con el chequeo original ("¿tiene AL
# MENOS 1 imagen?") esas páginas se colaban como bloque-norma, se OCReaba
# un logo de 350x366px y salía texto basura irreconocible (confirmado real
# en producción: 10 de 12 "actos" de la corrida completa del usuario eran
# justamente esto). Los escaneos reales confirmados miden 948x379 (parcial,
# 359.292px²) y 948x1171 / 945x1175 (completos, ~1.11M px²) -- bien por
# encima de cualquier logo/sello visto. El corte queda a mitad de camino
# entre el logo más grande confirmado (350x366 = 128.100px²) y el escaneo
# real más chico confirmado (359.292px²); es un umbral basado en pocos
# ejemplos reales, puede necesitar ajuste si aparece un caso límite nuevo.
AREA_MINIMA_IMAGEN_NORMA = 300_000


def _pagina_tiene_imagen(page):
    for img in page.get_images(full=True):
        ancho, alto = img[2], img[3]
        if ancho * alto >= AREA_MINIMA_IMAGEN_NORMA:
            return True
    return False


def _bloques_norma(doc):
    """[(pageidx_ini, pageidx_fin_excl), ...] de corridas consecutivas de
    páginas con al menos una imagen incrustada de tamaño real de escaneo
    (ver AREA_MINIMA_IMAGEN_NORMA -- descarta logos/sellos chicos de
    membrete)."""
    bloques = []
    ini = None
    for i in range(len(doc)):
        tiene = _pagina_tiene_imagen(doc[i])
        if tiene and ini is None:
            ini = i
        elif not tiene and ini is not None:
            bloques.append((ini, i))
            ini = None
    if ini is not None:
        bloques.append((ini, len(doc)))
    return bloques


# ===========================================================================
# EXTRACCIÓN POR PÁGINA: TEXTO VECTORIAL (encabezado) + OCR (cuerpo)
# ver docstring "EXTRACCIÓN HÍBRIDA POR PÁGINA"
# ===========================================================================
def _imagen_principal_pagina(doc, page):
    """(bytes, extensión, ancho, alto) de la imagen incrustada más grande
    (por área) de la página -- es la que trae el escaneo real del cuerpo
    del acto (ver docstring). Ancho/alto vienen gratis del propio
    extract_image (no hace falta decodificar la imagen aparte para
    diagnóstico -- ver procesar_pdf_local). (None, None, None, None) si la
    página no tiene ninguna."""
    imgs = page.get_images(full=True)
    if not imgs:
        return None, None, None, None
    mejor, mejor_area = None, 0
    for img in imgs:
        try:
            info = doc.extract_image(img[0])
        except Exception:
            continue
        area = info.get('width', 0) * info.get('height', 0)
        if area > mejor_area:
            mejor_area = area
            mejor = info
    if mejor is None:
        return None, None, None, None
    return mejor['image'], mejor['ext'], mejor['width'], mejor['height']


def _ocr_bytes_imagen(datos, ext):
    """Corre tesseract sobre los bytes de una imagen ya extraída. '' si
    falla (nunca levanta -- una página que falla no debe tumbar todo el
    boletín)."""
    tmp_in = tmp_out_base = None
    try:
        with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as f:
            f.write(datos)
            tmp_in = f.name
        tmp_out_base = tmp_in + '_ocr'
        env = os.environ.copy()
        if TESSDATA_PREFIX:
            env['TESSDATA_PREFIX'] = TESSDATA_PREFIX
        subprocess.run(
            ['tesseract', tmp_in, tmp_out_base, '-l', TESSERACT_LANG],
            check=True, capture_output=True, timeout=120, env=env)
        with open(tmp_out_base + '.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Aviso: OCR falló en una página: {e}", file=sys.stderr)
        return ''
    finally:
        for p in (tmp_in, (tmp_out_base + '.txt') if tmp_out_base else None):
            if p:
                try:
                    os.remove(p)
                except OSError:
                    pass


def _texto_vectorial_relevante(page):
    """Texto real (no OCR) de la página, tal cual lo da PyMuPDF -- incluye
    el encabezado del acto (banner + "TIPO N° NUMERO  fecha") si está en
    esta página, y potencialmente ruido de plantilla reciclada (ver
    docstring "ADVERTENCIA REAL"). Devuelve TODO el texto de la página, sin
    filtrar -- usado sólo para _fecha_edicion_portada (que sí filtra con su
    propio patrón anclado). Para el cuerpo de una norma se usa
    _fragmentos_utiles_vectorial en cambio (ver más abajo), que sí
    descarta el ruido."""
    try:
        return page.get_text('text') or ''
    except Exception:
        return ''


RE_FECHA_SUELTA = re.compile(r'^\d{2}-\d{2}-\d{2}$')


def _fragmentos_utiles_vectorial(texto):
    """Sólo las líneas de texto vectorial que son señal real de encabezado
    de acto: la línea "TIPO N° NUMERO" (RE_HEADER_NORMA) -- con su fecha
    "dd-mm-aa" pegada si está en la MISMA línea, o tomada de la línea
    siguiente si vino separada (confirmado real: en la muestra "DECRETO N°
    367" y "29-07-26" son 2 líneas de texto vectorial distintas, no 1 --
    ver RE_FECHA_SUELTA) -- y, si aparece, el banner de 2 líneas "TIPO" +
    emisor (RE_TIPO_BANNER) justo debajo. Descarta todo lo demás (roster de
    funcionarios, masthead, texto suelto de una edición anterior reciclada
    en la misma plantilla, ver docstring "ADVERTENCIA REAL"). Evita que
    texto_completo se infle con el listado completo de ministros en cada
    norma."""
    lineas = (texto or '').split('\n')
    utiles = []
    for i, linea in enumerate(lineas):
        l = linea.strip()
        if not l:
            continue
        if RE_HEADER_NORMA.match(l):
            utiles.append(l)
            if not re.search(r'\d{2}-\d{2}-\d{2}', l) and i + 1 < len(lineas) \
                    and RE_FECHA_SUELTA.match(lineas[i + 1].strip()):
                utiles.append(lineas[i + 1].strip())
        elif RE_TIPO_BANNER.match(l) and i + 1 < len(lineas) and lineas[i + 1].strip():
            utiles.append(l)
            utiles.append(lineas[i + 1].strip())
    return '\n'.join(utiles)


def _texto_pagina_norma(doc, pageidx):
    """Texto combinado de una página de bloque-norma: fragmentos útiles del
    encabezado real (vectorial, cuando existe) + OCR de la página RENDERIZADA
    -- ver docstring "EXTRACCIÓN HÍBRIDA POR PÁGINA", "BUG REAL: ORIENTACIÓN
    DE LA IMAGEN CRUDA" y "BUG REAL: PÁGINA APAISADA = 2 MEDIAS PÁGINAS
    LADO A LADO". A propósito NO se usan los bytes crudos de la imagen
    incrustada (extract_image() puede devolver la imagen en una orientación
    distinta a como se ve en la página -- renderizar con get_pixmap() sí
    aplica siempre la rotación/transformación correcta).

    Además, cuando la página es apaisada (ancho > alto), es -- confirmado
    real -- 2 medias páginas escaneadas independientes puestas lado a lado
    en una sola página de PDF (no 1 página de contenido normal), así que
    se corta en mitad izquierda/derecha y se OCRea cada mitad por separado,
    concatenando izquierda + derecha (izquierda es la que viene antes en el
    orden de lectura real: o bien una página separadora + el inicio de un
    acto, o bien el cierre de un acto + el inicio del siguiente). OCRear la
    página apaisada COMPLETA de una sola vez, sin cortar, puede hacer que
    Tesseract confunda su propia segmentación automática de columnas y
    intercale líneas de las 2 mitades como si fueran 2 columnas de UN solo
    documento -- confirmado real: página con el cierre de la Resolución
    S.C.A.G. 183 (mitad izquierda) + el inicio completo de la 184 (mitad
    derecha) salió con los artículos de UNA mezclados línea por línea con
    los VISTO/CONSIDERANDO de la OTRA. Separar antes de OCRear lo evitó por
    completo en la misma página (A/B real)."""
    page = doc[pageidx]
    encabezado = _fragmentos_utiles_vectorial(_texto_vectorial_relevante(page))
    r = page.rect
    if r.width > r.height:
        mitad = r.width / 2
        izq = fitz.Rect(r.x0, r.y0, r.x0 + mitad, r.y1)
        der = fitz.Rect(r.x0 + mitad, r.y0, r.x1, r.y1)
        pix_izq = page.get_pixmap(dpi=DPI_RENDER_OCR, clip=izq)
        pix_der = page.get_pixmap(dpi=DPI_RENDER_OCR, clip=der)
        texto_ocr = (_ocr_bytes_imagen(pix_izq.tobytes('png'), 'png') + '\n' +
                     _ocr_bytes_imagen(pix_der.tobytes('png'), 'png'))
    else:
        pix = page.get_pixmap(dpi=DPI_RENDER_OCR)
        texto_ocr = _ocr_bytes_imagen(pix.tobytes('png'), 'png')
    return (encabezado + '\n' + texto_ocr) if encabezado else texto_ocr


def _ocr_bloque(doc, pageidx_ini, pageidx_fin):
    partes = [_texto_pagina_norma(doc, i) for i in range(pageidx_ini, pageidx_fin)]
    return '\n'.join(p for p in partes if p.strip())


# ===========================================================================
# LIMPIEZA DE TEXTO OCR — ver docstring "OCR"
# ===========================================================================
# "N" + símbolo de grado mal leído pegado a un número -- confirmado real en
# OCR con modelo spa en varias formas: "N* 1733" / "N? 346" (asterisco/
# signo de pregunta), comilla doble curva de cierre "N” 02/2026" / "N”
# 24037347" (6 apariciones reales en un solo acto), y "N>" (mayor-que --
# confirmado real en el cierre "RESOLUCIÓN S.C.A.G.N> 19 1 /2026.-": sin
# este agregado, RE_NUMERO_CIERRE no reconocía el cierre VERDADERO del
# acto y terminaba usando una cita interna anterior como si fuera el
# número propio, ver docstring de RE_NUMERO_CIERRE) -- todas -> "N° ...".
RE_GRADO_TRAS_N = re.compile(r'\bN[°ºª*?”"″>]\s*(?=\d)', re.IGNORECASE)
# Símbolo de grado como ordinal tras un número, mal leído de varias formas
# reales distintas -- confirmado en la muestra: "9?" (signo de pregunta,
# "artículo 9? de la Ley"), comilla doble curva de apertura O cierre
# ("ARTÍCULO 1".-" / "6”.-", inconsistente incluso dentro del mismo acto),
# comilla doble RECTA ("ARTÍCULO 1".-", confirmado real -- Tesseract no fue
# consistente ni siquiera en qué tipo de comilla usa) y comilla simple
# ("5'.-") -- todas variantes de la misma fórmula "ARTÍCULO N°.-" /
# "artículo N°," / "N°." -> "N°" en todos los casos. Se usan \x/\u en vez
# de pegar los caracteres literales para no depender de qué comilla usa
# este código fuente como delimitador de string. Acotado a cuando sigue
# palabra en minúscula (continúa la oración), ".-" (cierre de artículo) o
# "." / "," sueltos, para no enganchar un signo de pregunta o una comilla
# de cierre real de fin de frase en otro contexto. NO se incluye "%" a
# propósito: se vio 1 caso real ("9% inciso a)" en vez de "9° inciso a)")
# pero un presupuesto de obra pública puede tener porcentajes legítimos
# (anticipos, descuentos) -- parece más arriesgado corregir "%" a ciegas
# que dejar ese caso puntual sin corregir (prosa de todos modos legible/
# entendible tal cual queda).
RE_GRADO_TRAS_NUM = re.compile(
    r"(?<=\d)[°ºª?“”″\x27\x22](?=\s+[a-záéíóúñ]|\.-|[.,])")


def _limpiar_texto_ocr(texto):
    if not texto:
        return ''
    texto = _guiones(texto)
    texto = RE_GRADO_TRAS_N.sub('N° ', texto)
    texto = RE_GRADO_TRAS_NUM.sub('°', texto)
    lineas = [_compacto(l) for l in texto.split('\n')]
    return '\n'.join(l for l in lineas if l)


# ===========================================================================
# DIVISIÓN EN NORMAS Y EXTRACCIÓN DE CAMPOS
# ===========================================================================
# Encabezado real (vectorial) de cada acto -- ver docstring "AMBIGÜEDAD REAL
# SIN RESOLVER": la palabra que acompaña "N°" acá NO se usa como tipo (no es
# confiable), sólo se usa para separar un acto de otro y capturar el número
# + fecha.
RE_HEADER_NORMA = re.compile(
    r'^\s*(?:DECRETO|RESOLUCI[OÓ]N|LEY|DISPOSICI[OÓ]N)\s+N[°ºª]\s*(\d+)'
    r'(?:\s+(\d{2})-(\d{2})-(\d{2}))?',
    re.IGNORECASE | re.MULTILINE)


# Encabezado real (cuerpo OCReado) de la CONVENCIÓN B -- ver docstring
# "CONVENCIÓN B: ACTOS SIN BANNER VECTORIAL, ENCABEZADO EN EL CUERPO
# ESCANEADO". A diferencia de RE_HEADER_NORMA (banner vectorial "TIPO N°
# NUMERO", Convención A), acá el ÚNICO marcador de "acá empieza un acto
# nuevo" es la propia primera línea del cuerpo escaneado: "USHUAIA," /
# "RÍO GRANDE," / "TOLHUIN," seguido de la fecha -- confirmado real en 5
# actos (Resoluciones S.C.A.G. 183 a 186 y el Acta de Preadjudicación de
# IPVyH) en 2 formatos de fecha distintos: abreviado ("0 2 JUN. 2026" --
# el espacio suelto entre los 2 dígitos del día es real, parece ser del
# propio sello/timbrado, no un error de OCR nuevo) o completo con día de
# semana opcional ("martes 28 de julio de 2026"). Requiere la fecha
# COMPLETA inmediatamente después de la coma -- a propósito, para no
# confundir esto con una mención suelta de la ciudad en medio del cuerpo
# (confirmado real: "saliendo de la ciudad de Ushuaia, Provincia de Tierra
# del Fuego" aparece en el cuerpo de la Resolución 183 y NO debe
# interpretarse como el inicio de un acto nuevo -- "Provincia de..." nunca
# matchea el patrón de fecha, así que ese caso real no genera falso
# positivo). El día trae a veces basura de OCR pegada ENTRE sus 2 dígitos
# (confirmado real: "0! 2 JUN, 2026" con un "!" suelto, además de "0 2" con
# espacio simple y "02" sin espacio -- parece ruido del propio
# sello/timbrado de fecha, no de la fuente del resto de la página), por
# eso el separador entre dígitos tolera hasta 2 caracteres sueltos de
# espacio/puntuación, no sólo un espacio.
_FECHA_ABREV_PAT = r'\d[\s!.,]{0,2}\d\s+[A-ZÁÉÍÓÚÑ]{3,4}\.?,?\s+\d{4}'
_FECHA_LARGA_PAT = r'(?:[a-záéíóúñ]+\s+)?\d{1,2}\s+de\s+[a-záéíóúñ]+\s+de\s+\d{4}'
RE_CIUDAD_FECHA = re.compile(
    r'^\s*(USHUAIA|R[IÍ]O\s+GRANDE|TOLHUIN)\s*,\s*(' +
    _FECHA_ABREV_PAT + '|' + _FECHA_LARGA_PAT + ')',
    re.IGNORECASE | re.MULTILINE)
RE_FECHA_ABREV_CAPTURA = re.compile(
    r'(\d)[\s!.,]{0,2}(\d)\s+([A-ZÁÉÍÓÚÑ]{3,4})\.?,?\s+(\d{4})', re.IGNORECASE)
RE_FECHA_LARGA_CAPTURA = re.compile(
    r'(?:[a-záéíóúñ]+\s+)?(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})', re.IGNORECASE)

# Identificador de cierre real de la Convención B, pegado a la firma:
# "RESOLUCIÓN [SIGLA] N° {numero} /{año, 4 dígitos}.-" -- confirmado real
# ("RESOLUCIÓN S.C.A.G. N° 183 /2026.-", "...N° 184/2026.-"). Es el ÚNICO
# lugar donde el acto trae su propio número completo en la Convención B (el
# número de página/esquina como "183" que aparece cerca del encabezado es
# la marca de continuidad del expediente, no un dato confiable por sí
# solo -- ver docstring). Distinguible de las citas internas a OTRAS normas
# dentro del CONSIDERANDO porque esas usan año abreviado de 2 dígitos
# ("N° 3226/23"), nunca 4. OCR real a veces pierde 1-2 dígitos del número
# acá (confirmado real: "N°1 /2026" en vez de "N° 184/2026", aparente
# pérdida de caracteres sin patrón corregible) -- por eso _campos_norma
# exige mínimo 2 dígitos para aceptar este número (ver más abajo), si no
# se descarta antes que quedarse con un valor corto y probablemente
# incompleto.
RE_NUMERO_CIERRE = re.compile(
    r'RESOLUCI[OÓ]N\.?\s*[A-Z.]{0,12}\s*N[°ºª?]\s*([\d\s]{1,6}?)\s*/\s*(\d{4})',
    re.IGNORECASE)

# Exige "VISTO" cerca -- ver docstring "BUG REAL: ENCABEZADO REPETIDO POR
# PÁGINA Y FALSO POSITIVO DEL PROPIO MASTHEAD". Sin esto, 2 problemas reales
# confirmados en la corrida completa: (1) cuando un acto de Convención A
# ocupa 2+ páginas, el banner "TIPO N° NUMERO" a veces se reimprime en cada
# página (no sólo en la primera) -- sin exigir VISTO cerca, cada
# reimpresión se toma como un acto nuevo y el mismo acto se manda partido
# en varios pedazos (confirmado real: acto 367 partido en 3, uno de ellos
# sólo el rótulo+roster de ministros de la página 1, sin VISTO cerca
# porque en esa página el cuerpo real todavía no empezó); (2) la propia
# fecha del masthead ("Ushuaia, Viernes 31 de Julio de 2026", repetida en
# CADA página del boletín) tiene la MISMA forma que el encabezado de la
# Convención B ("CIUDAD, fecha completa") y sin este filtro se toma como
# el inicio de un acto fantasma (confirmado real). Ventanas distintas por
# convención, medidas contra texto real: Convención A deja ~77 caracteres
# de banner entre el encabezado y VISTO (ver FIXTURE_RESOLUCION_367), acá
# se da margen a 220; Convención B trae VISTO pegado casi inmediato (~1
# carácter, un salto de línea) en todos los casos reales vistos, 40 alcanza
# de sobra y en cambio excluye el masthead (que en la corrida real queda a
# ~69 caracteres del próximo VISTO real, de otro acto) y edictos
# judiciales/electorales que también empiezan con "Ciudad, fecha" pero
# nunca traen VISTO cerca (confirmado real: aviso del Juzgado Electoral
# sobre estados contables de un partido político, colado con un número
# inventado antes de este arreglo).
RE_DIVISOR_NORMA = re.compile(
    r'(?=^\s*(?:DECRETO|RESOLUCI[OÓ]N|LEY|DISPOSICI[OÓ]N)\s+N[°ºª]\s*\d+'
    r'[\s\S]{0,220}?\bVISTO\b)|'
    r'(?=^\s*(?:USHUAIA|R[IÍ]O\s+GRANDE|TOLHUIN)\s*,\s*(?:' +
    _FECHA_ABREV_PAT + '|' + _FECHA_LARGA_PAT + r')[\s\S]{0,40}?\bVISTO\b)',
    re.IGNORECASE | re.MULTILINE)

# Tipo real: rótulo de color (banner) que antecede al encabezado -- más
# confiable que la palabra pegada a "N°" (ver docstring). Sólo la palabra
# sola en su línea, como se vio real.
RE_TIPO_BANNER = re.compile(
    r'^\s*(DECRETO|RESOLUCI[OÓ]N|LEY|DISPOSICI[OÓ]N)\s*$', re.IGNORECASE | re.MULTILINE)

# Verbo operativo del cuerpo, respaldo/confirmación del tipo real -- ver
# docstring.
RE_DECRETA = re.compile(r'\bDECRETA\s*:', re.IGNORECASE)
RE_RESUELVE = re.compile(r'\bRESUELVE\s*:', re.IGNORECASE)
RE_SANCIONA = re.compile(r'SANCIONA\s+CON\s+FUERZA\s+DE\s+LEY', re.IGNORECASE)

# Anclado a "BOLETIN OFICIAL" (título grande, una sola vez por página real
# de masthead) seguido de la línea de fecha -- a propósito, NO un patrón
# suelto de "Ushuaia, {fecha}" solo: la página 1 real tiene además una línea
# de masthead VIEJA reciclada de una edición anterior ("AÑO XXXIV -
# Ushuaia, Lunes 02 de Enero de 2025 - N° 5363", confirmado real) que un
# patrón sin anclar matchearía primero y daría la fecha de edición
# equivocada -- ver docstring "ADVERTENCIA REAL".
RE_FECHA_PORTADA = re.compile(
    r'BOLETIN\s+OFICIAL\s*\n\s*Ushuaia,\s*[A-ZÁÉÍÓÚÑa-záéíóúñ]+\s+(\d{1,2})\s+de\s+'
    r'([A-ZÁÉÍÓÚÑa-záéíóúñ]+)\s+de\s+(\d{4})',
    re.IGNORECASE)

# Título real del firmante + su área, inmediatamente antes del verbo
# operativo -- generalizado esta sesión (antes sólo cubría "MINISTRO DE
# X RESUELVE" en una sola línea, Convención A/acto 367). \s ya matchea
# saltos de línea sin re.DOTALL, así que esto también cubre la Convención
# B real, que viene en 2-3 líneas de OCR distintas: "LA SECRETARIA DE
# COORDINACIÓN ADMINISTRATIVA\nDEL GOBERNADOR\nRESUELVE:". Sólo
# MINISTRO/A y SECRETARIO/A tienen ejemplo real hasta ahora -- ver
# _emisor_desde_cuerpo para el mapeo título persona -> institución.
RE_EMISOR_TITULO = re.compile(
    r'\b(?:EL|LA)\s+(MINISTR[OA]|SECRETARI[OA])\s+DE\s+'
    r'([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s,./]*?)\s*(?:RESUELVE|DECRETA)\s*:',
    re.IGNORECASE)

# Se agregó 'SUGIERE' (cierre real de la Convención C -- ver docstring
# "BUG REAL: SÍNTESIS CRUZADA...") y fin-de-string como terminadores, más
# un tope duro de caracteres (.{1,15000}?) como red de seguridad de último
# recurso. IMPORTANTE: el tope tiene que quedar POR ENCIMA del
# CONSIDERANDO real más largo confirmado (acto 367, 7546 caracteres hasta
# su propio 'Por ello:') -- un tope más chico (se probó 2500 primero)
# ROMPE ese caso real: al no poder cerrar dentro del tope en el
# CONSIDERANDO verdadero, el regex "salta" a la próxima palabra suelta
# "considerandos" más adelante en el propio texto (dentro de "de acuerdo a
# los considerandos que anteceden", una mención de pasada en el
# ARTÍCULO 1°, no un encabezado real) y arma la síntesis de ahí, vacía o
# mal. El caso que motivó el tope (Acta de Preadjudicación de IPVyH,
# arrastraba la síntesis de un Aviso no relacionado ~4272 caracteres más
# adelante) en realidad se arregla solo con el terminador 'SUGIERE' propio
# de esa acta, que aparece a los 2910 caracteres de su CONSIDERANDO --
# ANTES de llegar al Aviso -- así que un tope generoso (por encima de 367)
# no reintroduce ese bug; sólo hace falta como último resorte si en el
# futuro aparece un acto sin NINGÚN cierre reconocido.
RE_CONSIDERANDO = re.compile(
    r'CONSIDERANDO\s*:?\s*(.{1,15000}?)(?=\bPor\s+ello\b|\bEL\s+(?:GOBERNADOR|MINISTR[OA])\b|'
    r'\bLA\s+LEGISLATURA\b|\bDECRETA\s*:|\bRESUELVE\s*:|\bSUGIERE\b|$)',
    re.IGNORECASE | re.DOTALL)
RE_DENOMINADOS = re.compile(r'denominad[oa]s?\s*:?\s*[“"]([^”"]+)[”"]', re.IGNORECASE)
RE_PRIMER_QUE = re.compile(r'\bQue\s+(.+?)\.', re.DOTALL)

# Señal mínima de que un bloque sin divisor reconocido IGUAL parece ser un
# acto administrativo real (candidato al fallback "mandar como 1 solo
# acto", ver procesar_pdf_local) -- ver docstring "BUG REAL: ANEXO/ACTA
# CONTABLE/EDICTO COLADO COMO ACTO FALSO". Sin este chequeo, CUALQUIER
# página con imagen suficientemente grande (ver AREA_MINIMA_IMAGEN_NORMA)
# que no matcheara ningún divisor se mandaba igual como acto genérico
# ('RESOLUCION ?/2026', emisor genérico) -- confirmado real en la corrida
# completa: páginas de Pliego/Anexo técnico (tablas de conductores,
# "ACTA DE RECEPCIÓN DEFINITIVA", "PLANOS CONFORME OBRA"), una rendición
# contable de Fondo Permanente, y una nota de un Juzgado Electoral sobre
# estados contables de un partido político -- NINGUNO de estos es un acto
# administrativo real, y ninguno de ellos contiene ninguna de estas
# palabras. Un Decreto/Resolución/Ley real, aunque su encabezado propio
# haya salido ilegible del OCR, casi siempre conserva al menos UNA de
# éstas en el cuerpo (son palabras cortas, comunes y muy redundantes --
# más robustas al ruido de OCR que un número o una fecha puntual).
RE_PARECE_ACTO = re.compile(
    r'\bVISTO\b|\bCONSIDERANDO\b|\bRESUELVE\b|\bDECRETA\b|\bSANCIONA\b|\bART[IÍ]CULO\b',
    re.IGNORECASE)


def _fecha_edicion_portada(texto_pagina1):
    """Fecha ISO leída de 'Ushuaia, {día} de {mes} de {año}' (texto
    vectorial real de la 1ra página del bloque-norma inicial, no hace
    falta OCR -- ver docstring). None si no matchea."""
    m = RE_FECHA_PORTADA.search(texto_pagina1 or '')
    if not m:
        return None
    dia, mes_txt, anio = m.groups()
    mes = MES_NUMERO.get(_sin_acentos(mes_txt).upper())
    if not mes:
        return None
    return f'{anio}-{mes:02d}-{int(dia):02d}'


def _fecha_desde_texto(fragmento):
    """ISO a partir del fragmento de fecha ya recortado por RE_CIUDAD_FECHA
    (grupo 2) -- prueba el formato abreviado ("0 2 JUN. 2026") y si no
    matchea, el completo ("28 de julio de 2026"). None si ninguno matchea o
    si el nombre de mes no se reconoce (ver docstring "CONVENCIÓN B")."""
    m = RE_FECHA_ABREV_CAPTURA.match(fragmento)
    if m:
        d1, d2, mes_txt, anio = m.groups()
        mes = MES_NUMERO.get(_sin_acentos(mes_txt).upper())
        if mes:
            return f'{anio}-{mes:02d}-{d1}{d2}'
    m = RE_FECHA_LARGA_CAPTURA.match(fragmento)
    if m:
        dia, mes_txt, anio = m.groups()
        mes = MES_NUMERO.get(_sin_acentos(mes_txt).upper())
        if mes:
            return f'{anio}-{mes:02d}-{int(dia):02d}'
    return None


def _dividir_normas(texto):
    """Bloques de texto, uno por acto, separados en el encabezado real --
    "TIPO N° NUMERO ..." (Convención A) o "USHUAIA/RÍO GRANDE/TOLHUIN,
    {fecha}" (Convención B, ver docstring). Descarta cualquier fragmento
    que no empiece con uno de los dos encabezados reconocidos CON "VISTO"
    cerca (ver RE_DIVISOR_NORMA) -- a propósito se reusa RE_DIVISOR_NORMA
    (no RE_HEADER_NORMA/RE_CIUDAD_FECHA sueltas) para este chequeo: el
    fragmento ANTES del primer split real (si lo hay) queda con el
    contenido crudo de esa porción del texto, y sin exigir el mismo
    requisito de VISTO cerca acá, ese fragmento líder puede arrancar con
    un encabezado real pero SIN VISTO cerca (repetido en una página previa
    del mismo acto, sin cuerpo propio todavía -- ver docstring "BUG REAL:
    ENCABEZADO REPETIDO POR PÁGINA") y colarse igual como acto fantasma."""
    partes = RE_DIVISOR_NORMA.split(texto)
    return [p for p in partes if RE_DIVISOR_NORMA.match(p.strip())]


def _tipo_desde_bloque(bloque):
    """Tipo real del acto -- banner de color primero, verbo operativo del
    cuerpo como respaldo/confirmación (ver docstring "AMBIGÜEDAD REAL SIN
    RESOLVER"). 'RESOLUCION' por default si no se pudo determinar ninguno
    de los dos (es el único tipo confirmado real en la muestra)."""
    m_banner = RE_TIPO_BANNER.search(bloque)
    if m_banner:
        return _sin_acentos(m_banner.group(1)).upper()
    if RE_SANCIONA.search(bloque):
        return 'LEY'
    if RE_DECRETA.search(bloque):
        return 'DECRETO'
    if RE_RESUELVE.search(bloque):
        return 'RESOLUCION'
    return 'RESOLUCION'


def _emisor_desde_cuerpo(tipo, bloque):
    if tipo == 'LEY' or RE_SANCIONA.search(bloque):
        return ('PODER LEGISLATIVO DE LA PROVINCIA DE TIERRA DEL FUEGO, '
                'ANTÁRTIDA E ISLAS DEL ATLÁNTICO SUR')
    if tipo == 'DECRETO' and RE_DECRETA.search(bloque):
        return ('PODER EJECUTIVO DE LA PROVINCIA DE TIERRA DEL FUEGO, '
                'ANTÁRTIDA E ISLAS DEL ATLÁNTICO SUR')
    m = RE_EMISOR_TITULO.search(bloque)
    if m:
        # Título de la PERSONA firmante -> nombre de la INSTITUCIÓN (ver
        # docstring): "MINISTRO/A" -> "MINISTERIO", "SECRETARIO/A" ->
        # "SECRETARÍA" (con tilde -- a propósito NO se usa la tilde tal
        # cual la trajo el OCR, que es inconsistente con los acentos, ver
        # docstring "OCR").
        titulo = _sin_acentos(m.group(1)).upper()
        institucion = 'MINISTERIO' if titulo.startswith('MINISTR') else 'SECRETARÍA'
        return f'{institucion} DE {_compacto(m.group(2)).upper()}'
    return ('GOBIERNO DE LA PROVINCIA DE TIERRA DEL FUEGO, '
            'ANTÁRTIDA E ISLAS DEL ATLÁNTICO SUR')


def _sintesis_desde_cuerpo(bloque):
    """Ver docstring 'SÍNTESIS — HEURÍSTICA NUEVA'. Si no se encontró un
    CONSIDERANDO reconocible, usa sólo un PREFIJO acotado del bloque (no el
    bloque entero) como red de seguridad adicional -- mismo motivo que el
    tope de RE_CONSIDERANDO."""
    m_cons = RE_CONSIDERANDO.search(bloque)
    tramo = m_cons.group(1) if m_cons else bloque[:15000]
    m_denom = RE_DENOMINADOS.search(tramo)
    if m_denom:
        return _compacto(m_denom.group(1))
    m_que = RE_PRIMER_QUE.search(tramo)
    if m_que:
        return _compacto(m_que.group(1)) + '.'
    return ''


def _campos_norma(bloque):
    """Campos parseados (sin red/OCR) de un bloque ya dividido por
    _dividir_normas -- prueba primero la Convención A (encabezado
    vectorial "TIPO N° NUMERO fecha") y si no matchea, la Convención B
    (encabezado en el cuerpo "CIUDAD, fecha" + cierre "RESOLUCIÓN [SIGLA]
    N° numero /año" -- ver docstring "CONVENCIÓN B")."""
    bloque = bloque.strip()
    m_header = RE_HEADER_NORMA.match(bloque)
    if m_header:
        numero = m_header.group(1)
        fecha_acto = None
        if m_header.group(2):
            dd, mm, yy = m_header.group(2), m_header.group(3), m_header.group(4)
            fecha_acto = f'{_anio_completo(yy)}-{mm}-{dd}'
    else:
        numero = ''
        fecha_acto = None
        m_ciudad = RE_CIUDAD_FECHA.match(bloque)
        if m_ciudad:
            fecha_acto = _fecha_desde_texto(m_ciudad.group(2))
        # ÚLTIMO match, no el primero -- ver docstring de RE_NUMERO_CIERRE.
        # El CONSIDERANDO casi siempre cita OTRAS normas con la misma forma
        # "RESOLUCIÓN [SIGLA] N° numero/año" (a veces con año de 4 dígitos
        # también, no sólo abreviado de 2 -- confirmado real: "Resolución
        # M.E. N° 148/2024" citada como fundamento en 3 actos reales
        # DISTINTOS, todos con su propio número real distinto de 148) --
        # el cierre VERDADERO del acto siempre es el ÚLTIMO, pegado a la
        # firma al final del bloque.
        _matches_cierre = list(RE_NUMERO_CIERRE.finditer(bloque))
        m_cierre = _matches_cierre[-1] if _matches_cierre else None
        if m_cierre:
            digitos = re.sub(r'\D', '', m_cierre.group(1))
            # Mínimo 2 dígitos para aceptar -- ver docstring de
            # RE_NUMERO_CIERRE (el OCR real a veces pierde dígitos acá; un
            # número corto es casi seguro incompleto, mejor '?' honesto que
            # un valor corto con mucha confianza de estar mal).
            if len(digitos) >= 2:
                numero = digitos
            if not fecha_acto:
                # Sin fecha de apertura reconocida -- al menos el año del
                # cierre es mejor que nada; se combina con mes/día
                # desconocidos más abajo (_armar_norma cae a fecha_edicion
                # si fecha_acto queda None, así que sólo vale la pena
                # fijarlo si de verdad tenemos algo útil que aportar aparte
                # del año solo -- se deja en None a propósito, el año solo
                # sin mes/día no es una fecha ISO válida).
                pass

    tipo = _tipo_desde_bloque(bloque)
    emisor = _emisor_desde_cuerpo(tipo, bloque)
    sintesis = _sintesis_desde_cuerpo(bloque)

    return {
        'tipo': tipo,
        'numero': numero,
        'fecha_acto': fecha_acto,
        'emisor': emisor,
        'sintesis': sintesis,
        'cuerpo': _compacto(bloque),
    }


def _armar_norma(campos, fecha_edicion, url_referencia):
    """Armado puro (sin red) de una norma a partir de los campos ya
    parseados -- separado para poder testearlo con fixtures fijas."""
    tipo = campos['tipo']
    numero = campos['numero'] or '?'
    fecha = campos['fecha_acto'] or fecha_edicion
    anio = (fecha or '????')[:4]
    sintesis = campos['sintesis'] or f'{tipo} {numero}/{anio}'

    return {
        'id': f'{tipo}-{numero}-{anio}-{fecha_edicion}',
        'tipo': tipo,
        'numero': numero,
        'anio': anio,
        'fecha': fecha,
        'emisor': campos['emisor'],
        'sintesis': sintesis,
        'texto_completo': campos['cuerpo'],
        'url_norma': url_referencia,
    }


def procesar_pdf_local(ruta_pdf, url_referencia):
    """[normas] de un PDF ya descargado en disco. Todo el trabajo es local
    (PyMuPDF + tesseract), no depende de red. None si no se pudo determinar
    la fecha de edición (estructura de portada inesperada -- no se manda
    nada, mismo criterio que el resto de la familia)."""
    if fitz is None:
        raise RuntimeError('falta PyMuPDF (pip install pymupdf)')
    doc = fitz.open(ruta_pdf)
    try:
        bloques_paginas = _bloques_norma(doc)
        print(f"Bloques candidatos a norma (con imagen incrustada): "
              f"{len(bloques_paginas)} de {len(doc)} páginas totales", file=sys.stderr)
        if not bloques_paginas:
            return None, None

        fecha_edicion = _fecha_edicion_portada(_texto_vectorial_relevante(doc[bloques_paginas[0][0]]))

        normas = []
        for ini, fin in bloques_paginas:
            # Diagnóstico: rango de páginas (1-indexado) + dimensiones de la
            # imagen principal de cada página del bloque -- para poder ver
            # en stderr si un bloque "candidato a norma" en realidad es un
            # logo/sello/imagen chica sin relación con el cuerpo escaneado
            # real (ver docstring "QUÉ FALTA VALIDAR").
            _dims_diag = []
            for _pi in range(ini, fin):
                _datos_diag, _ext_diag, _w_diag, _h_diag = _imagen_principal_pagina(doc, doc[_pi])
                _dims_diag.append(f'{_w_diag}x{_h_diag}' if _datos_diag else 'sin imagen')
            print(f"  bloque páginas {ini+1}-{fin} ({fin-ini} pág.), imagen principal "
                  f"por página: {', '.join(_dims_diag)}", file=sys.stderr)

            texto_bloque = _limpiar_texto_ocr(_ocr_bloque(doc, ini, fin))
            bloques_texto = _dividir_normas(texto_bloque)
            if not bloques_texto and texto_bloque.strip() and RE_PARECE_ACTO.search(texto_bloque):
                # No se encontró ningún encabezado reconocible, pero el
                # bloque SÍ tiene señales de ser un acto real (VISTO/
                # CONSIDERANDO/RESUELVE/DECRETA/SANCIONA/ARTÍCULO en algún
                # lado) -- se manda igual como 1 solo acto en vez de
                # perderlo, con tipo/número best-effort. Si NO hay ninguna
                # de esas señales, el bloque se descarta en vez de mandarse
                # como acto genérico falso -- ver docstring RE_PARECE_ACTO.
                bloques_texto = [texto_bloque]
            for b in bloques_texto:
                norma = _armar_norma(_campos_norma(b), fecha_edicion, url_referencia)
                norma['_paginas_origen'] = f'{ini+1}-{fin}'  # sólo debug, no se envía al backend
                normas.append(norma)
        return fecha_edicion, normas
    finally:
        doc.close()


# ===========================================================================
# CLASIFICACIÓN INDIVIDUAL / GENERAL -- heredado tal cual del resto de la
# familia (mismo idioma administrativo argentino). Nunca ejercitado contra
# un ejemplo real de Tierra del Fuego -- ver docstring "QUÉ FALTA VALIDAR".
# ===========================================================================
UMBRAL_INDIVIDUAL = 3

PATRONES_INDIVIDUAL = [
    (r'\bDes[íi]gn(?:[ae]se|a|ar)\b', 4, 'designación'),
    (r'\bAc[ée]pt(?:[ae]se|a|ar)\b[\s\S]{0,80}\brenuncia\b', 4, 'renuncia'),
    (r'\brenuncia\s+presentada\s+por\b', 4, 'renuncia'),
    (r'\bPromu[ée]v(?:ese|anse)\b', 4, 'promoción de un agente (reflexivo: Promuévese/Promuévanse)'),
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
    (r'\bDer[óo]ganse\b|\bDer[óo]gase\b', -3, 'derogación'),
    (r'\bHomolog(?:ase|uese|a|ar)\b', -2, 'homologación de resolución'),
    (r'\bAdjud[íi]c(?:ase|a|ar)\b', -2, 'adjudicación de contratación/obra'),
    (r'\bApru[ée]base\b[\s\S]{0,60}\bPliego\b', -2, 'aprobación de pliego de licitación'),
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
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de Tierra del Fuego.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se descubre vía Drive')
    ap.add_argument('--fecha', help='YYYY-MM-DD; default hoy. Si ese mes todavía no tiene '
                                     'ediciones en Drive, se busca hacia atrás la última real '
                                     'disponible (ver _ultima_edicion_en_carpeta)')
    ap.add_argument('--pdf-local', help='(debug) usar este PDF ya descargado en vez de Drive')
    ap.add_argument('--solo-descubrir', action='store_true',
                    help='ubica el PDF en Drive (año/mes/número) y sale SIN descargar -- '
                         'para probar GOOGLE_DRIVE_API_KEY rápido, sin esperar la '
                         'descarga completa (puede pesar 300+MB)')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--todas', action='store_true',
                    help='muestra también las individuales, con puntaje y motivos')
    ap.add_argument('--sin-filtro', action='store_true',
                    help='envía también las individuales')
    ap.add_argument('--volcar', action='store_true', help='imprime lo reconocido y sale')
    args = ap.parse_args()

    fecha_objetivo = (datetime.strptime(args.fecha, '%Y-%m-%d').date()
                      if args.fecha else date.today())

    # ---- 1. Ubicar + descargar el PDF (o usar --pdf-local para debug) ----
    if args.pdf_local:
        ruta_pdf = args.pdf_local
        url_referencia = f'file://{os.path.abspath(ruta_pdf)}'
        numero_edicion = None
    else:
        archivo, numero_edicion = _ultima_edicion_en_carpeta(fecha_objetivo)
        if not archivo:
            salida("warning", "No se pudo ubicar la última edición en Drive (ver stderr).")

        if args.solo_descubrir:
            salida("success", f"Encontrado: {archivo['name']} (id={archivo['id']}, "
                              f"{archivo.get('size', '?')} bytes, "
                              f"modificado={archivo.get('modifiedTime', '?')}). "
                              f"No se descargó nada (--solo-descubrir).")

        numero_previo = _leer_estado()
        if numero_previo is not None and numero_edicion <= numero_previo:
            salida("info", f"Sin novedades: última edición ya procesada ({numero_previo}) "
                           f">= última en Drive ({numero_edicion}).")

        print(f"Edición a procesar: B.O. {numero_edicion} ({archivo.get('size', '?')} bytes)",
              file=sys.stderr)
        destino = os.path.join(tempfile.gettempdir(), f"bo_tdf_{numero_edicion}.pdf")
        tamano_esperado = archivo.get('size')
        ya_descargado = (os.path.exists(destino) and tamano_esperado
                         and os.path.getsize(destino) == int(tamano_esperado))
        if ya_descargado:
            print(f"Ya estaba descargado en {destino} (mismo tamaño que Drive), "
                  f"no se vuelve a bajar.", file=sys.stderr)
        elif not _descargar_drive_streaming(archivo['id'], destino):
            salida("warning", f"No se pudo descargar B.O. {numero_edicion} de Drive (ver stderr).")
        ruta_pdf = destino
        url_referencia = (f'https://drive.google.com/file/d/{archivo["id"]}/view')

    try:
        fecha_boletin, normas_todas = procesar_pdf_local(ruta_pdf, url_referencia)
    except RuntimeError as e:
        salida("error", str(e))
    finally:
        # En modos de prueba (--dry-run/--volcar) NO se borra: son 300+MB,
        # no tiene sentido re-descargar en cada intento mientras se está
        # iterando contra bugs reales (ver arriba, "ya_descargado"). En una
        # corrida real (sin esos flags) sí se limpia, como el resto de la
        # familia.
        if not args.pdf_local and not (args.dry_run or args.volcar):
            try:
                os.remove(ruta_pdf)
            except OSError:
                pass

    if normas_todas is None:
        salida("warning", "No se encontraron páginas con contenido de norma en el PDF "
                          "(estructura inesperada; no se envió nada).")

    if not fecha_boletin:
        fecha_boletin = fecha_objetivo.isoformat()
        print(f"Aviso: no se pudo leer la fecha de portada; se usa la fecha objetivo "
              f"({fecha_boletin}).", file=sys.stderr)

    print(f"Edición: {fecha_boletin} | actos encontrados: {len(normas_todas)}", file=sys.stderr)

    for n in normas_todas:
        n['es_individual'], n['puntaje'], n['motivos'] = clasificar_norma(
            n['tipo'], n['sintesis'], n['texto_completo'])

    if args.volcar:
        for n in normas_todas:
            print(f"  {n['tipo']:12s} N° {n['numero']:>8s}/{n['anio']} "
                  f"fecha={n['fecha'] or '?':10s} emisor={n['emisor'][:55]}", file=sys.stderr)
        salida("success", f"volcado: {len(normas_todas)} actos reconocidos.")

    guardar_debug(json.dumps(normas_todas, ensure_ascii=False, indent=2, default=str),
                  'debug_tierradelfuego.json')

    if not normas_todas:
        if numero_edicion is not None:
            _escribir_estado(numero_edicion)
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Sin novedades: el boletín del {fecha_boletin} no publicó "
                          f"normativa reconocible.", total=0)

    generales = [n for n in normas_todas if not n['es_individual']]
    individuales = [n for n in normas_todas if n['es_individual']]
    a_enviar = normas_todas if args.sin_filtro else generales

    print(f"Boletín {fecha_boletin} | actos: {len(normas_todas)} "
          f"(generales {len(generales)} / individuales {len(individuales)})", file=sys.stderr)

    if args.dry_run:
        for n in (normas_todas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {n['tipo']:12s} N° {n['numero']:>8s}/{n['anio']} "
                  f"{n['emisor'][:40]:40s} {n['sintesis'][:50]}", file=sys.stderr)
            if args.todas and n.get('motivos'):
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    if verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        if numero_edicion is not None:
            _escribir_estado(numero_edicion)
        salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

    if not a_enviar:
        if numero_edicion is not None:
            _escribir_estado(numero_edicion)
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Se procesó el {fecha_boletin}, pero los {len(individuales)} "
                          f"actos encontrados son individuales; no se envió ninguno.", total=0)

    # ---- Envío -----------------------------------------------------------
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

    if numero_edicion is not None:
        _escribir_estado(numero_edicion)
    registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, len(payload))
    salida("success", respuesta.get('mensaje', 'OK') or 'OK', total=len(payload))


if __name__ == '__main__':
    try:
        _main()
    except SystemExit:
        raise
    except Exception as e:
        salida("error", f"Error inesperado: {e}")