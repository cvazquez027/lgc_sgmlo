#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
===============================================================================
 BOLETÍN OFICIAL DE LA PROVINCIA DE SAN JUAN  —  id_jurisdiccion 19
===============================================================================

POR QUÉ ESTE BOT SÍ PARSEA UN PDF, Y POR QUÉ ADEMÁS HACE OCR
-----------------------------------------------------------------------------
El usuario encontró que el sitio (https://boletinoficial.sanjuan.gob.ar/) es
un SPA en JavaScript que consume:

    POST https://syrahapi.sanjuan.gob.ar/data
    {"site":"dlc.tramites.boletinoficial","tipo":"DLC","results":10}

y que esa llamada devuelve los últimos 10 boletines, cada uno con un link a
un PDF de la edición COMPLETA (no por norma). Su hipótesis fue que esos PDF
están escaneados y hace falta OCR, pidiendo expresamente que se analice antes
de construir el bot.

No se pudo reproducir esa llamada (es POST y el sandbox de este desarrollo no
tiene salida de red hacia dominios .gob.ar; el fetch de sólo-GET tampoco
sirve para un POST con body). En cambio, se encontró independientemente el
archivo histórico del Boletín en el Joomla/K2 legado que respalda al mismo
organismo:

    https://contenido.sanjuan.gob.ar/index.php?option=com_k2&view=item&id=<ID>:cualquier-cosa&Itemid=148

Este sitio SÍ se pudo pedir directo (sin JavaScript, HTML plano) y se
descargaron y leyeron 3 PDF reales completos (18/03/2020, 23/07/2026,
29/07/2026, 30/07/2026) para confirmar la hipótesis del usuario. Conclusión,
confirmada leyendo el texto extraído de los 4 PDF:

  - La edición de 2020 tiene TEXTO REAL de punta a punta (se pudo leer cada
    Decreto completo, con Artículo 1º y firma, extrayendo el PDF sin OCR).
  - Las 3 ediciones de 2026 (formato vigente) son un PDF HÍBRIDO: la
    carátula de autoridades, los encabezados de página ("Boletín Oficial /
    Pág. 295.508 San Juan, Jueves 30 de Julio de 2026") y los títulos de
    rubro ("DECRETOS", "RESOLUCIONES", "LEYES"...) SÍ son texto real
    (se extraen perfecto sin OCR) — pero el CUERPO de cada norma (el
    Decreto/Resolución/Ley en sí) está insertado como IMAGEN dentro del PDF:
    extract_text() de esas páginas devuelve vacío o casi vacío, mientras que
    el mismo extractor sí trae completo el texto de las páginas de
    encabezado. Esto es consistente con un flujo de trabajo donde cada
    organismo manda su norma ya firmada/escaneada y el Boletín arma un PDF
    maestro pegando esas páginas como imagen, agregando por su cuenta la
    numeración y los títulos de sección como texto real.

Conclusión práctica: el usuario tenía razón. Hace falta OCR para el cuerpo de
las normas, pero NO para encontrar dónde está cada rubro dentro del PDF (eso
sale gratis, del texto real). Este bot combina las dos cosas:

    1. pdfplumber extrae texto real de CADA página → sirve para ubicar en
       qué páginas empieza y termina cada rubro (DECRETOS, RESOLUCIONES...).
    2. Para las páginas que caen dentro de un rubro con normativa Y no
       trajeron texto real (< 60 caracteres después de sacar el membrete),
       se renderiza esa página a imagen (pypdfium2) y se le corre OCR en
       español (pytesseract + tesseract-ocr-spa).

Si algún día San Juan vuelve a publicar con texto real completo (como en
2020), el bot lo detecta solo (no le hace falta OCR a una página que ya
tiene texto real) y anda más rápido sin cambiar una línea.

DEPENDENCIA DE SISTEMA — ESTO NO SE INSTALA CON pip SOLO
-----------------------------------------------------------------------------
El OCR necesita el binario de Tesseract instalado en el servidor (VPS), no
sólo el paquete de Python. En Debian/Ubuntu:

    apt install tesseract-ocr tesseract-ocr-spa

Sin esto, el bot NO rompe: detecta que OCR no está disponible, sigue
funcionando con el texto real que haya (puede ser 0 normas si toda la
normativa de esa edición está en páginas-imagen), y devuelve status
"warning" avisando exactamente qué instalar — sin registrar el boletín como
procesado, para poder reintentar el mismo día una vez instalado.
Paquetes de Python nuevos que si hacen falta (pip): pdfplumber, pypdfium2,
pytesseract, Pillow.

DESCUBRIMIENTO DE LA EDICIÓN — SIN ATAJO DE "ÚLTIMA", A DIFERENCIA DE SALTA
-----------------------------------------------------------------------------
A diferencia de boletinoficialsalta.gob.ar (que tiene nro_edicion=0 = "la
última", confirmado real), este sitio K2 no tiene un endpoint así. Lo que
SÍ tiene, confirmado real:

  - Cada edición es un ítem K2 con un ID numérico correlativo
    (https://contenido.sanjuan.gob.ar/index.php?option=com_k2&view=item&id=<ID>:x&Itemid=148,
    el "slug" después de los dos puntos puede ser cualquier cosa, el sitio
    lo ignora y sirve por ID igual).
  - El ID sube de a 1 por cada edición publicada. En la ventana de muestra
    (22/07/2026 a 30/07/2026) subió exactamente 1 por día HÁBIL, sin
    publicar fin de semana — aunque el pie de página de las ediciones 2026
    dice "Aparece los días hábiles y no hábiles según Ley N° 2037-A", en la
    práctica observada real se siguió saltando sábados y domingos.
  - Cada edición publicada HOY describe el boletín de AYER (mismo patrón de
    1 día de atraso que se vio en Salta): el ítem consultado el 31/07/2026
    ya existente más nuevo fue el del 30/07/2026 (id 10729); el id 10730
    (que hubiera sido el del 31/07) todavía no existía al momento de este
    desarrollo.
  - La categoría con el listado completo
    (?option=com_k2&view=itemlist&task=category&id=48) e también existe,
    pero quedó pegada varios días atrás en las pruebas (parece cacheada del
    lado del servidor) mientras que pedir un ID puntual SÍ refleja el
    estado real al instante. Por eso este bot NUNCA usa esa categoría para
    descubrir la última edición — sólo sirve como archivo navegable para un
    humano.

Sin un atajo tipo nro_edicion=0, este bot ubica CUALQUIER edición (la última
o una vieja por --fecha) con el mismo mecanismo: una constante ANCLA
(ANCLA_ID_K2, ANCLA_FECHA) confirmada real al momento de este desarrollo,
una estimación por proporción de días hábiles desde esa ancla, y una
caminata que confirma/ajusta pidiendo ediciones reales hasta encontrar la
fecha buscada (o, para "la última", hasta pegar contra un ID que todavía no
existe). Es el mismo principio que resolver_edicion_por_fecha en
bot_salta.py, sólo que acá se usa siempre, no sólo para --fecha. La ANCLA
puede quedar desactualizada con los meses; no rompe nada, la caminata la
corrige sola, sólo tarda algún pedido más (tope MAX_INTENTOS_CAMINATA).

RUBROS CONFIRMADOS REALES (y los que no)
-----------------------------------------------------------------------------
Vistos reales, con contenido, en las 3 ediciones de 2026 revisadas:
    LEYES, DECRETOS, RESOLUCIONES, ORDENANZAS (normativa que este bot manda)
    NOTIFICACIONES, EDICTOS DE MINAS, LICITACIONES, CONVOCATORIAS,
    EDICTOS JUDICIALES, REMATES, RAZÓN SOCIAL, SUCESORIOS, USUCAPIÓN,
    PRESCRIPCIÓN ADQUISITIVA, RECAUDACIÓN DIARIA (avisos/edictos de
    terceros, NUNCA normativa — se reconocen y se descartan a propósito)

NUNCA vistos en las 3 muestras, mapeados "por las dudas" igual (mismo
criterio que Salta con Leyes/Municipal): DECISIONES ADMINISTRATIVAS,
ACORDADAS (de la Corte de Justicia — el organigrama de autoridades sí
incluye un Presidente de la Corte, así que debería existir en algún
boletín), DISPOSICIONES, DECRETOS-LEYES.

Además, por si aparece un rubro que este bot no conoce (ninguno de los de
arriba): cualquier página cuyo texto real, sin membrete, sea una línea corta
íntegramente en mayúsculas se trata como un posible encabezado de rubro
NUEVO — corta la racha del rubro anterior (para no mezclar sus páginas con
las del rubro desconocido) y avisa por stderr con el texto visto, para poder
agregarlo a RUBROS_NORMATIVA si corresponde. Es la misma lógica defensiva
que RE_RUBRO en bot_salta.py.

CÓMO SE ARMA CADA NORMA DENTRO DE UN RUBRO
-----------------------------------------------------------------------------
La única muestra con texto real de un cuerpo de norma completo es la de
2020: "DECRETO N° 2174 -MTyC- 10-12-19 / ARTÍCULO 1°-Desígnese...". Los
metadatos de una edición 2026 (campo "Información adicional" de un ítem K2,
cuando el sitio lo carga — no siempre) confirman que la convención de
número sigue vigente en 2026: "DECRETOS: N° 0046 - 2026 / N° 0047 - 2025" y
"Leyes: LEY N° 2828-H-08/07/2026". De acá sale el patrón que separa una
norma de la siguiente dentro del texto (real u OCR) de un rubro:

    <TIPO> N° <numero> -<SIGLA>- <DD-MM-AA o DD/MM/AAAA>

RE_NORMA_HEADER está escrito a partir de ESTA única muestra real de 2020 más
el patrón de numeración visto en los metadatos 2026 (que usa una sigla de
una sola letra para Leyes, "H" — probablemente por "Honorable Legislatura",
al no venir del Poder Ejecutivo como los Decretos). No hay ninguna muestra
real de cómo se ve este encabezado DESPUÉS de pasar por OCR (ver "QUÉ FALTA
VALIDAR" — es, con diferencia, el punto más débil de este bot).

SÍNTESIS Y EMISOR
-----------------------------------------------------------------------------
Síntesis: mismo mecanismo que el resto de las provincias (Artículo 1º
después de la última marca resolutiva). Se agrega "SANCIONAN CON FUERZA DE
LEY" como marca resolutiva propia de las Leyes (redacción típica argentina:
"LA CÁMARA DE DIPUTADOS Y EL SENADO... SANCIONAN CON FUERZA DE LEY:"),
sin confirmar contra una Ley real de San Juan.

Emisor: el listado de autoridades de la carátula (repetido en las 3
ediciones 2026) da el nombre completo de cada Ministerio, pero en NINGÚN
lado del sitio aparece la sigla de 2 o 3 letras pegada a ese nombre — así
que el diccionario SIGLAS_EMISOR de este bot es una ADIVINANZA (iniciales
del nombre completo del Ministerio) sin confirmar, salvo 3 siglas viejas
que sí aparecieron reales en la muestra de 2020 (MTyC, MOSP, MPyDE — puede
que ya no se usen, el gabinete cambió de nombre entre 2020 y 2026). Si la
sigla extraída no está en el diccionario, se manda tal cual viene (mejor
una sigla sin desarrollar que un emisor inventado mal).

FLAGS
-----
    --dry-run       no envía nada
    --fecha AAAA-MM-DD   edición puntual por fecha (ancla + caminata)
    --id-k2 N       ítem K2 puntual, salta el descubrimiento por fecha
    --pdf ARCHIVO   usa un PDF ya descargado (pruebas offline, sin pegarle
                    al sitio); no da url_norma real, sólo para --dry-run
    --sin-ocr       no renderiza ni corre OCR; sólo usa texto real embebido
                    (rápido, útil para probar la ubicación de rubros)
    --dpi N         resolución de renderizado para OCR (default 300)
    --todas         muestra también las individuales, con puntaje/motivos
    --sin-filtro    envía también las individuales (NO afecta el filtro de
                    normas municipales — rubro ORDENANZAS —, que se excluye
                    siempre; ver "SÓLO PROVINCIA, NO MUNICIPIOS" más abajo)
    --volcar        imprime las normas reconocidas (con su página de PDF) y
                    sale sin pedir nada más

===============================================================================
VALIDADO CONTRA UN PDF REAL (edición 30/07/2026, subida por el usuario)
===============================================================================
La primera versión de este bot se escribió sin poder correr OCR real ni una
vez (el sandbox original no tenía forma de bajar los bytes del PDF). El
usuario subió el PDF real más nuevo antes de probarlo él mismo, y se instaló
tesseract-ocr-spa en el sandbox bajando el .deb de un mirror de Ubuntu y
extrayéndolo con dpkg-deb -x (sin apt/root) para poder correr OCR real
contra las 22 páginas normativas de esa edición (DECRETOS, RESOLUCIONES,
ORDENANZAS — esta edición no trajo LEYES). Eso encontró 9 bugs reales, ya
corregidos acá:

1. El formato de encabezado NO es uno solo: la muestra de 2020 (única con
   la que se había diseñado RE_NORMA_HEADER) resultó ser sólo UNO de al
   menos 3 formatos reales — Decretos del Poder Ejecutivo ("DECRETO N°
   0046 -SESyOP- 2026"), Resoluciones de organismos autárquicos como el
   E.P.R.E. ("Resolución E.P.R.E." en una línea, "N° 0777" en la
   siguiente), y Ordenanzas municipales que ni siquiera tienen encabezado
   propio (llegan como "la Ordenanza N° 2347/26" dentro de la nota de
   elevación del Concejo Deliberante). Se reemplazó RE_NORMA_HEADER por
   RE_NORMA_CANDIDATA (más permisivo, sin exigir sigla/fecha pegadas) +
   _es_encabezado_real (ver punto 4) para separar los 3 formatos.
2. La fecha NO viene pegada al número en ningún formato real (sólo a veces
   un año). Se separó en RE_DATELINE, que busca "SAN JUAN, <fecha>" aparte
   — con dos variantes reales confirmadas: mes abreviado con punto ("15
   ENE. 2026") y mes completo sin "de" antes del año ("28 de Julio 2026").
3. El símbolo "N°" es lo más inconsistente que devuelve Tesseract en este
   Boletín: salió real como "N*", "N'U+" (así, cuatro caracteres) y "NO",
   las tres en la MISMA página. RE_NORMA_CANDIDATA ahora tolera cualquier
   ruido corto entre "N" y el número en vez de exigir °/º.
4. Falsos positivos: el cuerpo de una norma cita constantemente otras
   normas ("de la Ley N° 257-R", "del Decreto Reglamentario N° 1293-1984-
   R"), indistinguibles de un encabezado real mirando sólo TIPO+N°+número.
   El filtro que sí funcionó contra las 4 páginas reales de muestra: un
   encabezado real SIEMPRE tiene "VISTO" (no "CONSIDERANDO" — ver el
   comentario de RE_VISTO_CERCA, una primera versión que aceptaba
   cualquiera de los dos dejaba pasar citas dentro del propio párrafo de
   VISTO de una norma) a menos de 220 caracteres después.
5. Ese mismo filtro tenía un bug de sustring: buscaba "VISTO" sin \b, así
   que "previstos" (con "visto" adentro) lo activaba igual. Se agregó \b.
6. texto_completo se aplastaba a una sola línea (_compacto), lo que rompía
   RE_MARCA_RESOLUTIVA (^...$ en modo MULTILINE, busca "DECRETA:"/
   "RESUELVE:" solas en su propia línea) — la síntesis siempre caía al
   título del encabezado en vez del Artículo 1º real. Se separó
   _compacto_lineas (conserva saltos de línea) de _compacto (para texto
   corto de una sola línea, como los logs).
7. La página divisora de un rubro (la que dice "DECRETOS" en grande) tiene
   su propio bug de membrete: el orden de extracción de pdfplumber ahí da
   "Boletín Oficial" + "DECRETOS" + "Pág. NNN San Juan, fecha", con el
   título de rubro INTERCALADO entre las dos mitades del membrete. Un
   regex que exige las dos mitades pegadas no matchea nada, y esa página
   (sólo membrete + título, ~74 caracteres) quedaba por ENCIMA del umbral
   de "ya tiene texto real" — así que el bot se saltaba el OCR de esa
   página exacta, la que además tenía la primera norma del rubro
   arrancando ahí mismo. Se separó RE_MEMBRETE en dos regex independientes
   (uno por mitad) para que no dependan de estar pegadas.
8. "DECRETO" pegado sin espacio a lo que sigue ("DECRETON>U:-0047" en vez
   de "DECRETO N° 0047") no matcheaba: el \b que exigía RE_NORMA_CANDIDATA
   DESPUÉS del tipo no existe entre "O" y "N" cuando están pegados. Se
   sacó ese \b (se conserva el de ANTES del tipo).
9. La sigla del emisor se guarda en mayúsculas pero SIGLAS_EMISOR tiene
   claves con mayúsculas Y minúsculas mezcladas ("MTyC") — nunca
   matcheaba. Búsqueda ahora case-insensitive.

Con estos 9 fixes, la edición real completa (22 páginas OCR, sin acceso a
producción — el PDF lo subió el usuario, no se descubrió por el sitio) dio
8 normas: Decreto 0046 (cesantía de un agente — INDIVIDUAL, correcto),
Decreto 0047 (designación — INDIVIDUAL, correcto), Resolución 777 del
E.P.R.E. (emplazamiento a una empresa — GENERAL, correcto), y 5
Ordenanzas/Decretos municipales de promulgación/derogación (GENERAL,
correcto). Se agregó además una red de seguridad (posibles_perdidas_por_
rubro): si un rubro tiene más "VISTO" que encabezados reconocidos, avisa
por stderr en vez de perder esa norma en silencio — pasó una sola vez en
las 22 páginas, un Decreto cuyo tipo Tesseract leyó como "pecreron" (así,
irreconocible para cualquier regex razonable).

Lo que ESTO NO prueba: que el descubrimiento de la edición (ancla +
caminata contra contenido.sanjuan.gob.ar) siga funcionando en producción —
el PDF de esta prueba se subió a mano con --pdf, nunca se volvió a pegarle
al sitio real después de la primera ronda de reconocimiento.

===============================================================================
CONFIRMADO EN PRODUCCIÓN REAL (corrida del usuario, 30/07/2026, su VPS)
===============================================================================
El usuario corrió el bot de verdad contra el sitio real (no un PDF subido a
mano): `bot_sanjuan.py 19 --volcar` y después `--dry-run --todas`. El
descubrimiento por ancla+caminata se autocorrigió solo de la estimación
"10730" al ID real "10729" (edición 30/07/2026 — la MISMA que se había
probado en el sandbox con --pdf), y "Páginas en rubros normativos: 22
(texto real: 0, OCR: 22)" / "Normas reconocidas: 8" calzaron EXACTO con la
prueba de sandbox. Esto confirma el punto pendiente que antes encabezaba
esta lista (si el descubrimiento en vivo seguía funcionando): sí funciona.

Pero una lectura detallada del debug_sanjuan.json de esa corrida (el
volcado completo con texto_completo de las 8 normas, no la consola
resumida) encontró 3 bugs reales más — invisibles en el sandbox porque
ninguna de las 4 páginas de muestra usadas para los 9 fixes anteriores
tenía estos casos puntuales. Ya corregidos y re-validados contra el mismo
OCR real cacheado en esta sesión (test_produccion_sanjuan.py y
test_produccion_sanjuan_full.py, guardados junto a este archivo):

10. FUSIÓN DE NORMA HUÉRFANA / SECUESTRO DE SÍNTESIS (el más grave de los
    tres). Cuando una norma no se reconoce (el aviso de "VISTO sin
    encabezado" del punto 4/9 de más arriba), su contenido NO se perdía
    en silencio como se pensaba: el span de la norma RECONOCIDA anterior
    se cortaba "hasta la próxima candidata RECONOCIDA", así que la norma
    huérfana intercalada quedaba con su cuerpo ENTERO pegado al final de
    la anterior. Y como _sintesis_de_texto toma la ÚLTIMA marca
    resolutiva ("DECRETA:"/"RESUELVE:") de todo el texto, si la huérfana
    tenía la suya propia, la síntesis reportada para la norma ANTERIOR
    terminaba siendo el Artículo 1° de la huérfana — mal atribuida a otro
    número de norma, con nombre/DNI/CUIL de otra persona. Confirmado
    real: el Decreto "0047" (pensión a María Susana Muñoz, CUIL
    27-05740784-6) reportaba como síntesis "Designase en el cargo
    vacante... al Presbítero Mario Luis Estrada Pelaytay..." — en
    realidad el Decreto "0048" (encabezado ilegible: "pecreroN-- 0048"),
    fusionado adentro de "0047". Mismo patrón en la Ordenanza "2347/26"
    (nombra una plaza "Javier Oscar Provenzano"), que reportaba como
    síntesis la promulgación del Decreto municipal "N ? 0934" fusionado
    adentro suyo.
    Fix: además del aviso ya existente, los VISTO huérfanos ahora también
    actúan como límite de corte para la norma anterior — con dos guardas
    (ver _limite_desde_visto_huerfano) para no cortar por una "visto"
    suelta como palabra común dentro del cuerpo de una norma real: sólo
    cuenta si hay un salto de párrafo cerca Y el tramo hasta el VISTO es
    corto y trae un dígito (parece un intento de encabezado, no prosa
    corrida). Además, el hueco entre "N" y el número en RE_NORMA_CANDIDATA
    no toleraba ruido con ESPACIOS de por medio ("N ? 0934" es
    espacio-ruido-espacio; antes sólo se toleraba ruido pegado tipo
    "N*U:0047"); con el hueco ampliado (N[^\d]{0,8}? en vez de
    N\S{0,6}?\s*), "DECRETO N ? 0934" ahora se reconoce COMO CANDIDATA
    PROPIA — mejor que sólo evitar la fusión, se recupera como norma
    independiente. Re-testeado contra la edición real completa: esto sube
    el conteo de 8 a 9 normas reconocidas (aparece el Decreto 0934, que
    antes no figuraba en ningún lado, ni siquiera en los avisos).

11. "BOLETÍN OFICIAL" SE BORRABA TAMBIÉN DEL CUERPO LEGÍTIMO. El fix del
    punto 7 de más arriba (separar el corte de membrete en dos regex
    independientes) traía un efecto secundario no visto hasta leer el
    debug_sanjuan.json completo: RE_MEMBRETE_1 borraba "Boletín Oficial"
    en CUALQUIER posición de la página, pero esa frase también es texto
    legal legítimo en el cierre estándar de casi cualquier norma ("...
    dese al Boletín Oficial para su publicación", "Publíquese en el
    Boletín Oficial de la Provincia..."). Confirmado real: "ARTÍCULO 2.-
    Comuníquese y dese al para su publicación." (Decreto 0046) y
    "Publíquese en el de la Provincia de San Juan." (Resolución 0777) —
    a las dos les faltaba "Boletín Oficial" en el medio, mutiladas.
    Fix: el corte de RE_MEMBRETE_1 ahora sólo se aplica si aparece
    dentro de los primeros ~150 caracteres de la página (el membrete
    real SIEMPRE está al principio, arriba de todo); una aparición más
    adentro se deja intacta. Riesgo residual conocido y aceptado: una
    norma brevísima que arranque casi en la cima de una página nueva Y
    tenga su cierre dentro de esos primeros 150 caracteres podría seguir
    mutilándose — caso de borde mucho más angosto que el bug sistemático
    que reemplaza (afectaba prácticamente TODAS las normas, en cualquier
    posición).

12. SÍNTESIS DE LA ORDENANZA 2347/26 CAÍA A UN FALLBACK MENOS PRECISO. Ya
    arreglado el punto 10, la síntesis de 2347/26 dejó de ser la fusión
    del Decreto 0934 — pero tampoco encontraba su propio Artículo 1°
    ("Impóngase el nombre 'JAVIER OSCAR PROVENZANO'..."): el OCR trajo
    "Artículo 1%:" (con "%" como ruido de marcador ordinal), y "%" no
    estaba en la clase de caracteres tolerada por RE_ARTICULO1. Se agregó
    "%" a esa clase (ya venía acumulando variantes reales: "*", "'U+",
    "O" suelta, comilla tipográfica). Con esto, la síntesis de 2347/26
    ahora sí es su propio Artículo 1°.

13. CLASIFICACIÓN GENERAL/INDIVIDUAL: FALTABA EL VERBO "ACUÉRDASE". Al
    corregir el punto 10, la síntesis correcta del Decreto 0047 pasó a
    ser "Acuérdase el beneficio de pensión a la Señora Maria Susana
    Muñoz, CUIL N* 27-05740784-6..." — una pensión a una persona
    nombrada, con CUIL, debería clasificar INDIVIDUAL sin dudar. Pero
    PATRONES_INDIVIDUAL sólo reconocía "Otórguese/Otorgar...beneficio",
    no "Acuérdase...beneficio" (mismo molde reflexivo-impersonal, verbo
    distinto) — sumaba sólo +1 (por matchear la versión débil en el
    CUERPO, no en la síntesis) contra un umbral de 3, y clasificaba
    GENERAL una norma que claramente no lo es. (Nota: con el punto 10 SIN
    corregir, esta norma clasificaba IND igual, pero por accidente — la
    síntesis robada del Decreto 0048, una designación, prendía el patrón
    de designación por otro motivo. Corregido el punto 10, hacía falta
    este fix aparte para que siguiera clasificando IND, ahora por el
    motivo correcto.) Se agregó un patrón nuevo para "Acuérdase/
    Acuérdanse...beneficio". Re-testeado: el Decreto 0047 vuelve a
    clasificar INDIVIDUAL, ahora con síntesis Y motivo correctos.

Con estos 4 fixes adicionales, la edición real 30/07/2026 (re-testeada
contra el mismo OCR cacheado, reconstruyendo paginas_por_rubro página por
página) da 9 normas — generales 7 / individuales 2 — sin ningún otro
cambio respecto a lo que el usuario ya vio en su corrida real (mismos
avisos, misma clasificación en las otras 7 normas que ya estaban bien).

El usuario corrió estos 4 fixes contra el sitio real (misma edición
30/07/2026, sin --pdf) y confirmó byte a byte: mismos 9 avisos/conteos que
en el sandbox, Decreto 0047 con síntesis y motivo correctos ("+3 síntesis:
beneficio a una persona (acuérdase)"), Decreto 0934 recuperado como norma
propia. También confirmó que el SyntaxWarning por escapes inválidos en el
docstring (ver más abajo) ya no aparece.

===============================================================================
SÓLO PROVINCIA, NO MUNICIPIOS
===============================================================================
14. NORMAS MUNICIPALES SE ESTABAN ENVIANDO COMO SI FUERAN DE LA PROVINCIA.
    El usuario notó, mirando el debug_sanjuan.json de su propia corrida
    real, que varias de las 9 normas eran en realidad municipales: la
    Ordenanza "2347/26" y su Decreto promulgatorio "0934" son de la
    Municipalidad de SARMIENTO; la Ordenanza "1"/1718 y el Decreto
    "57/2026.-" son de CALINGASTA; la Ordenanza "6229-2026" y el Decreto
    "2088" son de POCITO — 6 de las 9 normas de esa edición, todas del
    rubro ORDENANZAS. Esto pasa porque el Boletín Oficial de la Provincia
    publica, como servicio, las ordenanzas de los municipios de San Juan
    (que no tienen su propio boletín) junto con el Decreto del Intendente
    que las promulga — pero eso no las convierte en normativa de la
    Provincia. "Ordenanza" es, en la convención administrativa argentina,
    un instrumento EXCLUSIVAMENTE municipal (lo dicta un Concejo
    Deliberante); ninguna provincia legisla por Ordenanza.
    El problema para filtrarlas: los Decretos promulgatorios municipales
    (0934, 57/2026, 2088) tienen tipo='DECRETO' — el mismo valor que un
    Decreto PROVINCIAL real (0046, 0047) — así que no se pueden distinguir
    por tipo. Lo que sí los distingue siempre es el rubro: esos 3 Decretos
    quedaron con rubro='ORDENANZAS' (heredado de la página del PDF donde
    aparecen, dentro de la sección de Ordenanzas), nunca 'DECRETOS'. Se
    agregó RUBROS_MUNICIPALES = {'ORDENANZAS'} y un filtro en _main que
    excluye esas normas del envío al backend SIEMPRE (no depende de
    --sin-filtro, que es un eje distinto: individual/general vs. este,
    que es un límite de alcance/jurisdicción). Quedan igual en
    debug_sanjuan.json con un campo nuevo, es_provincial=false, para
    poder revisarlas sin perderlas de vista — y aparece un aviso por
    stderr contando cuántas se excluyeron y cuáles.
    Efecto secundario que esto resuelve de yapa: el usuario también notó
    que el emisor "CD" (de "Concejo Deliberante", extraído de citas tipo
    "1718-CD-2026") quedaba feo y ambiguo mostrado como nombre de emisor.
    Como las 2 normas que mostraban "CD" (la Ordenanza "1" y el Decreto
    "57/2026.-", ambas de Calingasta) son justamente municipales, quedan
    excluidas por este mismo fix — no hizo falta arreglar la resolución
    de "CD" a "Concejo Deliberante" por separado.
    Nota de alcance: esto asume que TODO lo publicado bajo rubro
    ORDENANZAS es municipal y NADA en los demás rubros normativos lo es
    — válido según la convención legal argentina (y confirmado en la
    única edición real inspeccionada), pero no probado contra más
    ediciones ni contra la posibilidad remota de un error de
    categorización del propio Boletín.

===============================================================================
QUÉ FALTA VALIDAR TODAVÍA
===============================================================================
1. El filtro de municipales (punto 14) sólo se probó contra la edición
   30/07/2026 (misma que ya se usó para todo lo anterior) reconstruida a
   mano desde el OCR cacheado — falta confirmarlo contra una corrida real
   nueva del usuario, e idealmente contra una edición que también tenga
   LEYES/ACORDADAS/DISPOSICIONES para confirmar que esos rubros tampoco
   traen contenido municipal mezclado (nunca se vio ninguno de esos 3
   rubros en las ediciones reales inspeccionadas hasta ahora).
2. SIGLAS_EMISOR sigue siendo mayormente adivinado (ver más arriba). Bajo
   impacto: si dos siglas distintas mapean al mismo nombre completo por
   error, puede pisar normas distintas en el dedup del backend.
3. ACORDADAS / DISPOSICIONES / DECISIONES ADMINISTRATIVAS / DECRETOS-LEYES
   / LEYES: la edición de prueba no trajo ninguna. El aviso de "rubro
   desconocido" debería avisar si aparecen con un nombre distinto al
   mapeado acá.
4. Emisor de Ordenanzas municipales: cae a "PODER EJECUTIVO" por defecto
   (no hay sigla corta en el formato de "Concejo Deliberante de
   Municipalidad de X"; sería más correcto usar el nombre del municipio
   del membrete, no implementado).
5. --fecha: la caminata nunca se probó contra un caso real.
6. El supuesto "1 día de atraso" se vio en 3 ediciones seguidas reales,
   pero no qué pasa un lunes (¿la del viernes sale recién el lunes, o hay
   edición de fin de semana?).
7. Tesseract instalado en el VPS del usuario: en este sandbox se instaló
   "a mano" (bajando el .deb, sin apt) para poder probar; en el VPS real
   hace falta `apt install tesseract-ocr tesseract-ocr-spa` de verdad.
===============================================================================
"""

import io
import os
import re
import sys
import json
import time
import html as html_lib
import argparse
import unicodedata
from datetime import datetime, date

import requests

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

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

SITIO_CONTENIDO = 'https://contenido.sanjuan.gob.ar'
URL_ITEM_K2 = f'{SITIO_CONTENIDO}/index.php'

HEADERS_WEB = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
}

REINTENTOS = 3
ESPERA_REINTENTO = 3
MAX_TEXTO_COMPLETO = 20000
MAX_SINTESIS = 700

# Ancla confirmada real al momento de este desarrollo (31/07/2026): el ítem
# K2 10729 es el Boletín del 30/07/2026, y el 10730 todavía no existía. Ver
# "DESCUBRIMIENTO DE LA EDICIÓN" en el docstring principal — se puede quedar
# vieja con los meses, no rompe nada, la caminata la corrige (más lento).
ANCLA_ID_K2 = 10729
ANCLA_FECHA = date(2026, 7, 30)
PASO_ID_POR_DIA = 5 / 7  # ediciones sólo en días hábiles, observado real
MAX_INTENTOS_CAMINATA = 25

UMBRAL_TEXTO_REAL = 60  # caracteres; por debajo, se asume página-imagen
OCR_DPI_DEFAULT = 300

# Rubro (encabezado tal como aparece en el PDF) -> tipo_norma_desc que se
# manda al backend. Confirmados reales (ediciones 23, 29 y 30/07/2026):
# LEYES, DECRETOS, RESOLUCIONES, ORDENANZAS. El resto es mapeo "por las
# dudas" — ver "RUBROS CONFIRMADOS REALES" en el docstring.
RUBROS_NORMATIVA = {
    'LEYES': 'LEY',
    'DECRETOS-LEYES': 'DECRETO LEY',
    'DECRETOS LEYES': 'DECRETO LEY',
    'DECRETOS': 'DECRETO',
    'DECISIONES ADMINISTRATIVAS': 'DECISION ADMINISTRATIVA',
    'RESOLUCIONES': 'RESOLUCION',
    'ACORDADAS': 'ACORDADA',
    'DISPOSICIONES': 'DISPOSICION',
    'ORDENANZAS': 'ORDENANZA',
}

# Reconocidos pero descartados a propósito (avisos/edictos de terceros,
# nunca normativa) — confirmados reales salvo aviso en contrario.
RUBROS_NO_NORMATIVA = {
    'NOTIFICACIONES', 'EDICTOS DE MINAS', 'LICITACIONES', 'CONVOCATORIAS',
    'EDICTOS JUDICIALES', 'REMATES', 'RAZON SOCIAL', 'SUCESORIOS',
    'USUCAPION', 'PRESCRIPCION ADQUISITIVA', 'RECAUDACION DIARIA',
}

# "Ordenanza" es, en la convención administrativa argentina, un instrumento
# EXCLUSIVAMENTE municipal (lo dicta un Concejo Deliberante) — ninguna
# provincia legisla por Ordenanza. Confirmado real en la edición 30/07/2026:
# el rubro ORDENANZAS del Boletín no trae sólo Ordenanzas de Concejos
# Deliberantes (Sarmiento, Calingasta, Pocito, todas municipios de San Juan)
# sino TAMBIÉN los Decretos municipales que las promulgan (firmados por el
# "Intendente Municipal", no por "EL GOBERNADOR DE LA PROVINCIA") — el
# Boletín provincial los publica como servicio, pero no son normativa de la
# Provincia. Como esos Decretos promulgatorios tienen tipo='DECRETO' (mismo
# valor que un Decreto provincial real), NO se los puede distinguir por
# tipo — el rubro es la única marca confiable, y en la práctica separa
# perfecto: los 3 rubros con contenido provincial real vistos hasta ahora
# (DECRETOS, RESOLUCIONES, y por transitividad LEYES/DECISIONES
# ADMINISTRATIVAS/ACORDADAS/DISPOSICIONES) nunca traen Ordenanzas ni
# Decretos municipales mezclados. Usado en _main para NO enviar estas
# normas al backend (siguen apareciendo en debug_sanjuan.json con
# es_provincial=false, para poder revisarlas sin perderlas de vista).
RUBROS_MUNICIPALES = {'ORDENANZAS'}

_TODOS_LOS_RUBROS = sorted(
    list(RUBROS_NORMATIVA) + list(RUBROS_NO_NORMATIVA), key=len, reverse=True)


# ===========================================================================
# NORMALIZACIÓN
# ===========================================================================
GUIONES = {ord('–'): '-', ord('—'): '-', ord('‐'): '-', ord('‑'): '-', ord('−'): '-'}


def _guiones(texto):
    return (texto or '').translate(GUIONES)


def _sin_acentos(s):
    s = unicodedata.normalize('NFD', s or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


# Comparación sin acentos: RUBROS_NO_NORMATIVA está escrito sin tilde
# ("RAZON SOCIAL"), pero el texto real trae "RAZÓN SOCIAL" con tilde — sin
# esto nunca matcheaba y esas páginas cascaban al aviso de "rubro
# desconocido" (inofensivo para el resultado final, ya que de cualquier
# forma no son normativa, pero ensuciaba el log). Se busca sin acentos y se
# devuelve la clave ORIGINAL (con o sin acento, tal como está en
# RUBROS_NORMATIVA/RUBROS_NO_NORMATIVA) para no romper los lookups que
# dependen de esas claves exactas (p.ej. paginas_por_rubro).
_RUBROS_SIN_ACENTO_A_ORIGINAL = [(_sin_acentos(r), r) for r in _TODOS_LOS_RUBROS]


def _compacto(texto):
    return re.sub(r'\s+', ' ', (texto or '')).strip()


def _url_absoluta_contenido(href):
    href = href or ''
    if href.startswith('http://') or href.startswith('https://'):
        return href
    if href.startswith('/'):
        return SITIO_CONTENIDO + href
    return f'{SITIO_CONTENIDO}/{href}'


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
    """GET de texto/HTML, con reintentos. None si 404 o error definitivo."""
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


def descargar_binario(url, timeout=120):
    """GET de bytes (el PDF de la edición), con reintentos."""
    for intento in range(1, REINTENTOS + 1):
        try:
            r = sesion().get(url, timeout=timeout)
            if r.status_code == 404:
                return None
            if r.status_code == 200:
                return r.content
            if r.status_code < 500:
                return None
        except requests.RequestException as e:
            if intento == REINTENTOS:
                raise RuntimeError(f"Error de red descargando {url}: {e}")
        time.sleep(ESPERA_REINTENTO * intento)
    return None


# ===========================================================================
# DESCUBRIMIENTO DE LA EDICIÓN (ítems K2 de contenido.sanjuan.gob.ar)
# ===========================================================================
RE_TITULO_EDICION = re.compile(
    r'BOLET[ÍI]N\s+OFICIAL\s+DE\s+(?P<dia>\d{1,2})/(?P<mes>\d{1,2})/(?P<anio>\d{4})',
    re.IGNORECASE)
RE_LINK_DESCARGA = re.compile(r'href=["\']([^"\']*task=download[^"\']*)["\']', re.IGNORECASE)


def obtener_edicion_k2(id_k2):
    """(fecha_iso, url_pdf, html) del ítem K2 <id_k2>, o (None, None, None)
    si no existe (edición futura todavía no publicada, o hueco). El "slug"
    después de los dos puntos en la URL no importa, confirmado real."""
    url = f'{URL_ITEM_K2}?option=com_k2&view=item&id={id_k2}:x&Itemid=148'
    try:
        pagina = descargar(url)
    except RuntimeError as e:
        print(f"Aviso: falló pedido al ítem K2 {id_k2}: {e}", file=sys.stderr)
        return None, None, None
    if not pagina:
        return None, None, None
    m = RE_TITULO_EDICION.search(pagina)
    if not m:
        return None, None, None
    try:
        fecha_iso = datetime(
            int(m.group('anio')), int(m.group('mes')), int(m.group('dia'))).date().isoformat()
    except ValueError:
        return None, None, None
    m_link = RE_LINK_DESCARGA.search(pagina)
    url_pdf = _url_absoluta_contenido(html_lib.unescape(m_link.group(1))) if m_link else None
    return fecha_iso, url_pdf, pagina


def _estimar_id(fecha_objetivo):
    delta = (fecha_objetivo - ANCLA_FECHA).days
    return ANCLA_ID_K2 + round(delta * PASO_ID_POR_DIA)


def resolver_edicion_por_fecha_k2(fecha_objetivo_iso):
    """Ancla + caminata (ver docstring principal). None, None, None si no se
    encuentra en MAX_INTENTOS_CAMINATA pedidos."""
    objetivo = datetime.strptime(fecha_objetivo_iso, '%Y-%m-%d').date()
    candidato = max(1, _estimar_id(objetivo))
    print(f"Estimando edición del {fecha_objetivo_iso} en el ítem K2 {candidato} "
          f"(ancla: {ANCLA_ID_K2} = {ANCLA_FECHA.isoformat()})", file=sys.stderr)
    probados = set()
    for _ in range(MAX_INTENTOS_CAMINATA):
        if candidato <= 0 or candidato in probados:
            break
        probados.add(candidato)
        fecha_iso, url_pdf, _ = obtener_edicion_k2(candidato)
        if not fecha_iso:
            candidato -= 1
            continue
        fecha_dt = datetime.strptime(fecha_iso, '%Y-%m-%d').date()
        if fecha_dt == objetivo:
            return candidato, fecha_iso, url_pdf
        candidato += 1 if fecha_dt < objetivo else -1
    return None, None, None


def obtener_ultima_edicion_k2():
    """Estima el ítem K2 de hoy y camina hasta el último que exista de
    verdad (ver "DESCUBRIMIENTO DE LA EDICIÓN" en el docstring: acá no hay
    atajo tipo nro_edicion=0 de Salta, así que "la última" también se
    resuelve con ancla + caminata)."""
    hoy = date.today()
    candidato = max(1, _estimar_id(hoy))
    print(f"Estimando la última edición cerca del ítem K2 {candidato} "
          f"(ancla: {ANCLA_ID_K2} = {ANCLA_FECHA.isoformat()})", file=sys.stderr)
    fecha_iso, url_pdf, _ = obtener_edicion_k2(candidato)

    intentos = 0
    if fecha_iso:
        while intentos < MAX_INTENTOS_CAMINATA:
            sig_fecha, sig_pdf, _ = obtener_edicion_k2(candidato + 1)
            if not sig_fecha:
                break
            candidato += 1
            fecha_iso, url_pdf = sig_fecha, sig_pdf
            intentos += 1
    else:
        while intentos < MAX_INTENTOS_CAMINATA and not fecha_iso:
            candidato -= 1
            if candidato <= 0:
                return None, None, None
            fecha_iso, url_pdf, _ = obtener_edicion_k2(candidato)
            intentos += 1

    if not fecha_iso:
        return None, None, None
    return candidato, fecha_iso, url_pdf


# ===========================================================================
# PDF: texto real por página + mapeo de rubros + OCR de respaldo
# ===========================================================================
# Dos patrones separados, no uno solo. Bug real encontrado probando la
# página divisora de DECRETOS del PDF subido: en esa página el orden de
# extracción de pdfplumber da "Boletín Oficial" + "DECRETOS" (título del
# rubro) + "Pág. NNN San Juan, fecha" — con el título de rubro INTERCALADO
# entre las dos mitades del membrete. Un solo regex que exige "Boletín
# Oficial" pegado a "San Juan, fecha" no matchea nada ahí, y la página
# entera (74 caracteres: cabecera + "DECRETOS" + pie) queda por encima de
# UMBRAL_TEXTO_REAL → el bot la trataba como "ya tiene texto real" y se
# saltaba el OCR de esa página, perdiendo el Decreto que arrancaba ahí
# mismo. Separando el corte de "Boletín Oficial" del corte de "Pág. San
# Juan, fecha" cada uno se saca solo, sin importar qué haya en el medio.
RE_MEMBRETE_1 = re.compile(r'Bolet[íi]n\s+Oficial', re.IGNORECASE)
RE_MEMBRETE_2 = re.compile(
    r'(?:P[áa]g\.\s*[\d.]+\s+)?'
    r'San\s+Juan,\s*\w+\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\s*'
    r'(?:P[áa]g\.\s*[\d.]+)?',
    re.IGNORECASE)

RE_LINEA_TODO_MAYUSCULAS = re.compile(r'^[A-ZÁÉÍÓÚÑ0-9º°.,\-\s]{3,50}$')

_OCR_DISPONIBLE = None


def _compacto_lineas(texto):
    """Como _compacto, pero CONSERVA los saltos de línea (sólo aplasta
    espacios/tabs dentro de cada línea y baja 3+ líneas en blanco seguidas
    a 2). Hace falta para texto_completo: RE_MARCA_RESOLUTIVA busca
    "DECRETA:"/"RESUELVE:" solas en su propia línea con ^...$ en modo
    MULTILINE — si el texto se aplasta a una sola línea (como hacía
    _compacto), esas anclas nunca matchean y la síntesis cae siempre al
    título del encabezado en lugar del Artículo 1º real (bug real
    encontrado probando esto contra OCR real)."""
    texto = texto or ''
    lineas = [re.sub(r'[ \t]+', ' ', ln).strip() for ln in texto.split('\n')]
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(lineas)).strip()


def _quitar_membrete(texto):
    t = _guiones(texto or '')
    # RE_MEMBRETE_1 sólo se saca si aparece cerca del ARRANQUE de la
    # página: es el título que se repite arriba de todas las páginas, así
    # que ahí sí es membrete. Bug real encontrado en el volcado de
    # producción (30/07/2026): "Boletín Oficial" es también texto legal
    # legítimo dentro del cierre estándar de casi cualquier norma
    # ("...dese al Boletín Oficial para su publicación", "Publíquese en
    # el Boletín Oficial de la Provincia..."), y un corte incondicional
    # (en cualquier posición) dejaba esas frases mutiladas ("dese al
    # para su publicación"). Cortar sólo cuando aparece dentro de los
    # primeros ~150 caracteres de la página deja intacta esa segunda
    # aparición, más adentro del cuerpo.
    m1 = RE_MEMBRETE_1.search(t)
    if m1 and m1.start() <= 150:
        t = t[:m1.start()] + ' ' + t[m1.end():]
    t = RE_MEMBRETE_2.sub(' ', t)
    return _compacto_lineas(t)


def _detectar_encabezado_rubro(texto_pagina_limpio):
    t = _sin_acentos(texto_pagina_limpio.upper())
    for rubro_sin_acento, rubro_original in _RUBROS_SIN_ACENTO_A_ORIGINAL:
        if re.search(r'\b' + re.escape(rubro_sin_acento) + r'\b', t):
            return rubro_original
    return None


def _parece_encabezado_desconocido(texto_pagina_limpio):
    t = texto_pagina_limpio.strip()
    return bool(t) and len(t) <= 50 and bool(RE_LINEA_TODO_MAYUSCULAS.match(t))


def _verificar_ocr_disponible():
    global _OCR_DISPONIBLE
    if _OCR_DISPONIBLE is not None:
        return _OCR_DISPONIBLE
    if pytesseract is None or pdfium is None:
        print("Aviso: falta pypdfium2 y/o pytesseract (pip install pypdfium2 pytesseract "
              "Pillow); no habrá OCR en esta corrida.", file=sys.stderr)
        _OCR_DISPONIBLE = False
        return False
    try:
        idiomas = pytesseract.get_languages(config='')
        _OCR_DISPONIBLE = 'spa' in idiomas
        if not _OCR_DISPONIBLE:
            print("Aviso: tesseract está instalado pero falta el paquete de idioma "
                  "español. Instalar con: apt install tesseract-ocr-spa", file=sys.stderr)
    except Exception as e:
        _OCR_DISPONIBLE = False
        print(f"Aviso: OCR no disponible ({e}). Instalar con: apt install tesseract-ocr "
              f"tesseract-ocr-spa", file=sys.stderr)
    return _OCR_DISPONIBLE


def _ocr_pagina(pdfium_doc, indice_pagina, dpi):
    try:
        pagina = pdfium_doc[indice_pagina]
        bitmap = pagina.render(scale=dpi / 72)
        img = bitmap.to_pil()
        return pytesseract.image_to_string(img, lang='spa') or ''
    except Exception as e:
        print(f"Aviso: falló OCR en página {indice_pagina + 1}: {e}", file=sys.stderr)
        return ''


def _procesar_pdf(pdf_bytes, dpi, sin_ocr):
    """{rubro_normativo: [(indice_pagina, texto), ...]} + contadores. El
    texto de cada página es real si alcanzó UMBRAL_TEXTO_REAL, si no (y hay
    OCR disponible) es el resultado de OCR."""
    if pdfplumber is None:
        raise RuntimeError("Falta pdfplumber: pip install pdfplumber")

    paginas_por_rubro = {r: [] for r in RUBROS_NORMATIVA}
    rubro_actual = None
    paginas_texto_real = 0
    paginas_ocr = 0
    avisados = set()

    pdfium_doc = None
    if not sin_ocr and pdfium is not None:
        try:
            pdfium_doc = pdfium.PdfDocument(pdf_bytes)
        except Exception as e:
            print(f"Aviso: no se pudo abrir el PDF con pypdfium2 ({e}); sin OCR "
                  f"disponible para esta corrida.", file=sys.stderr)

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, pagina in enumerate(pdf.pages):
            texto = _quitar_membrete(pagina.extract_text() or '')
            rubro_pagina = _detectar_encabezado_rubro(texto)
            if rubro_pagina:
                rubro_actual = rubro_pagina
            elif _parece_encabezado_desconocido(texto) and texto not in avisados:
                avisados.add(texto)
                print(f"Aviso: posible encabezado de rubro NO reconocido en página "
                      f"{i + 1}: {texto[:60]!r} (si es normativa, agregarlo a "
                      f"RUBROS_NORMATIVA)", file=sys.stderr)
                rubro_actual = f'(desconocido: {texto[:40]})'

            if rubro_actual not in RUBROS_NORMATIVA:
                continue

            if len(texto) >= UMBRAL_TEXTO_REAL:
                paginas_texto_real += 1
                paginas_por_rubro[rubro_actual].append((i, texto))
            elif not sin_ocr and pdfium_doc is not None and _verificar_ocr_disponible():
                texto_ocr = _quitar_membrete(_ocr_pagina(pdfium_doc, i, dpi))
                if texto_ocr:
                    paginas_ocr += 1
                paginas_por_rubro[rubro_actual].append((i, texto_ocr))
            else:
                paginas_por_rubro[rubro_actual].append((i, ''))

    return paginas_por_rubro, paginas_texto_real, paginas_ocr


def _construir_bloque_rubro(paginas_texto):
    """(texto_concatenado, cortes) — cortes = [(offset_inicio, indice_pagina), ...]
    para poder mapear la posición de una norma encontrada a su página real
    del PDF (sirve para armar el link #page=N)."""
    partes = []
    cortes = []
    offset = 0
    for idx, texto in paginas_texto:
        cortes.append((offset, idx))
        partes.append(texto)
        offset += len(texto) + 1
    return '\n'.join(partes), cortes


def _pagina_de_offset(cortes, offset):
    pagina = cortes[0][1] if cortes else 0
    for ini, idx in cortes:
        if ini <= offset:
            pagina = idx
        else:
            break
    return pagina


# ===========================================================================
# NORMAS: separar cada una dentro del texto (real u OCR) de su rubro
# ===========================================================================
# Reescrito contra OCR REAL (edición 30/07/2026, subida por el usuario) —
# la primera versión estaba basada en una única muestra de 2020 sin OCR de
# por medio, y resultó demasiado rígida. Cuatro páginas reales de OCR (dos
# Decretos, una Resolución del E.P.R.E., una Ordenanza municipal) mostraron
# TRES formatos de encabezado distintos según quién emite la norma:
#
#   Decreto (Poder Ejecutivo):  "DECRETO N'U+ 0046 — SESyOP — 2026"
#                                (el "N°" salió OCR como "N'U+"; en otro
#                                Decreto de la misma página salió "N*" —
#                                Tesseract no es consistente ni DENTRO de
#                                la misma página)
#   Resolución (E.P.R.E.,
#   organismo autárquico):      "Resolución E.P.R.E.\n\nNO 0777\n..."
#                                (sigla ANTES del número, en minúscula-con-
#                                mayúscula "Resolución", no todo mayúscula)
#   Ordenanza (Concejo
#   Deliberante municipal):     "Elevo a su consideración la Ordenanza
#                                N° 2347/26, sancionada por este Concejo
#                                Deliberante." — no hay encabezado propio,
#                                el número aparece DENTRO de la nota de
#                                elevación.
#
# Ninguno de los 3 tiene fecha completa pegada al número (sólo a veces un
# año). La fecha real está aparte, en una línea "SAN JUAN, <fecha>" que
# también varía: "15 ENE. 2026" (mes abreviado + punto) vs "28 de Julio
# 2026" (mes completo, sin "de" antes del año). Por eso ahora la fecha se
# busca por separado (RE_DATELINE) en vez de exigirla pegada al encabezado.
#
# El problema nuevo que esto trae: el cuerpo de una norma cita constantemente
# OTRAS normas ("de la Ley N° 257-R", "del Decreto Reglamentario N°
# 1293-1984-R") con una forma que es indistinguible de un encabezado real
# con sólo mirar TIPO+N°+número. La distinción que sí se sostuvo en las 4
# muestras reales: un encabezado real SIEMPRE tiene "VISTO" o
# "CONSIDERANDO" a menos de ~220 caracteres después (arranca el cuerpo de
# la norma ahí mismo); una cita dentro de otro párrafo, no. RE_NORMA_CANDIDATA
# encuentra todos los TIPO+N°+número posibles; _es_encabezado_real descarta
# los que no tienen VISTO cerca.
#
# Ojo: el filtro usa sólo "VISTO", NO "CONSIDERANDO" — una primera versión
# aceptaba cualquiera de los dos y dejaba pasar falsos positivos reales:
# las citas DENTRO del propio párrafo de VISTO de una norma («la Ley
# Provincial N° 524-A y su Decreto Reglamentario N° 387/96», «Ley
# Provincial N° 430») quedan seguidas de cerca por el "CONSIDERANDO:" que
# cierra ESE MISMO párrafo, así que "algún VISTO o CONSIDERANDO cerca" no
# alcanza para distinguirlas de un encabezado real. "VISTO" solo sí lo
# hace: para un encabezado real es siempre lo próximo que aparece; para una
# cita dentro del propio VISTO, lo que sigue es CONSIDERANDO, no VISTO de
# nuevo. Confirmado contra las 4 páginas reales de OCR (8 citas
# descartadas correctamente, 0 encabezados reales perdidos).
# Sin \b DESPUÉS del tipo (sólo antes): visto real, Tesseract a veces pega
# el tipo directo con lo que sigue sin espacio — "DECRETON>U:-0047" en vez
# de "DECRETO N° 0047" — y un \b ahí exige una frontera de palabra entre
# "O" y "N" que en ese caso no existe, perdiendo la norma entera sin que
# ni siquiera aparezca como candidata rechazada. El \b de ADELANTE sí se
# mantiene, para no matchear el tipo como sufijo de otra palabra.
#
# El hueco entre "N" y el número (antes "N\S{0,6}?\s*") asumía ruido
# pegado y DESPUÉS espacio ("N°  0047" -> "N" + "°" + espacios). Bug real
# encontrado en el volcado de producción (30/07/2026): "DECRETO N * 0934"
# (espacio, ruido, espacio) no matcheaba nada, porque \S no puede
# consumir el espacio que viene justo después de la "N" -- la norma
# entera (el decreto que promulga la Ordenanza 2347/26) quedaba sin
# reconocer y su contenido terminaba pegado adentro de la norma anterior
# (ver _limite_desde_visto_huerfano). "N[^\d]{0,8}?" tolera cualquier
# mezcla de ruido Y espacios en cualquier orden entre la "N" y el primer
# dígito, sin perder los casos que ya andaban bien.
RE_NORMA_CANDIDATA = re.compile(
    r'\b(?P<tipo_crudo>LEY|DECRETO(?:[\s-]LEY)?|RESOLUCI[ÓOo]N(?:\s+DELEGADA)?|'
    r'DECISI[ÓOo]N\s+ADMINISTRATIVA|ACORDADA|DISPOSICI[ÓOo]N|ORDENANZA)'
    r'[\s\S]{0,25}?N[^\d]{0,8}?(?P<numero>\d[\d./-]*)',
    re.IGNORECASE)

RE_VISTO_CERCA = re.compile(r'\bVISTO\b', re.IGNORECASE)
VENTANA_VISTO = 220

# Siglas: dos formas vistas reales — "-SESyOP-" (Decretos, entre guiones,
# después del número) y "E.P.R.E." (organismos autárquicos, con puntos,
# ANTES del número). Best-effort: si no aparece ninguna de las dos formas
# cerca (p.ej. Ordenanzas municipales, donde el "emisor" es el nombre del
# Concejo Deliberante y no una sigla corta), sigla queda vacía y
# _resolver_emisor cae a 'PODER EJECUTIVO'.
RE_SIGLA_GUION = re.compile(r'[-–—]\s*(?P<sigla>[A-Za-zÑñ][A-Za-zÑñ.]{1,14})\s*[-–—]')
RE_SIGLA_PUNTOS = re.compile(r'\b(?P<sigla>[A-Z]\.(?:[A-Z]\.){1,5})')

MESES_3 = {
    'ENE': 1, 'FEB': 2, 'MAR': 3, 'ABR': 4, 'MAY': 5, 'JUN': 6,
    'JUL': 7, 'AGO': 8, 'SEP': 9, 'SET': 9, 'OCT': 10, 'NOV': 11, 'DIC': 12,
}
# Tolera "SAN JUAN, 1 5 ENE. 2026" (Tesseract mete un espacio de más en el
# día) y "SAN JUAN, 28 de Julio 2026" (mes completo, sin "de" antes del año).
RE_DATELINE = re.compile(
    r'SAN\s+JUAN,?\s*(?P<dia>\d\s?\d?)\s*\.?\s*(?:de\s+)?'
    r'(?P<mes>[A-ZÁÉÍÓÚa-zñáéíóú]{3,12})\.?\s*(?:de\s+)?(?P<anio>(?:19|20)\d{2})',
    re.IGNORECASE)

_TIPO_CRUDO_A_TIPO = {
    'LEY': 'LEY', 'DECRETO': 'DECRETO', 'DECRETO LEY': 'DECRETO LEY',
    'DECRETO-LEY': 'DECRETO LEY', 'RESOLUCION': 'RESOLUCION',
    'RESOLUCION DELEGADA': 'RESOLUCION DELEGADA',
    'DECISION ADMINISTRATIVA': 'DECISION ADMINISTRATIVA',
    'ACORDADA': 'ACORDADA', 'DISPOSICION': 'DISPOSICION', 'ORDENANZA': 'ORDENANZA',
}


def _normalizar_tipo_crudo(tipo_crudo):
    t = _compacto(_sin_acentos(tipo_crudo or '')).upper()
    return _TIPO_CRUDO_A_TIPO.get(t, t)


def _fecha_norma_iso(dia, mes, anio):
    try:
        d, m, a = int(dia), int(mes), int(anio)
        if a < 100:
            a += 2000
        return date(a, m, d).isoformat()
    except (ValueError, TypeError):
        return None


def _es_encabezado_real(texto_blob, fin_match):
    ventana = texto_blob[fin_match:fin_match + VENTANA_VISTO]
    return bool(RE_VISTO_CERCA.search(ventana))


def _limite_desde_visto_huerfano(blob, pos_visto):
    r"""Punto de corte para un VISTO "huérfano" (uno que no es el propio de
    ninguna candidata reconocida — ver el comentario grande en
    _normas_de_edicion). Las normas, aunque el OCR deje su encabezado
    irreconocible, siempre arrancan en un bloque nuevo separado por
    espacio vertical en el PDF original — la idea es cortar ahí.

    Ojo: el bloque de encabezado en sí suele traer VARIOS saltos de
    párrafo propios (tipo+número en una línea, fecha en la siguiente,
    cada una separada por línea en blanco — visto real: "pecreroN--
    0048\n\nSANJUAN, 15 ENE, 2026\n\nVISTO:"), así que no alcanza con
    tomar el ÚLTIMO salto antes del VISTO: ese suele ser el que separa la
    fecha del VISTO mismo, dejando afuera el "pecreroN-- 0048" (el único
    fragmento con el número de la norma perdida). Por eso se recorre
    desde el salto más CERCANO al VISTO hacia atrás, y se toma el primero
    cuyo tramo completo (desde ese salto hasta el VISTO) todavía "parece"
    un encabezado — corto y con al menos un dígito (el intento de número
    de norma) —, no sólo el segmento inmediatamente anterior al salto.
    Esto también sirve de guarda contra cortar por una "visto" suelta
    como palabra común dentro del cuerpo de una norma real: si no hay
    ningún salto de párrafo cuyo tramo completo parezca encabezado,
    devuelve None y no se usa como límite (más vale no cortar que cortar
    de más y truncar el final de una norma real)."""
    ini_ventana = max(0, pos_visto - VENTANA_VISTO)
    tramo = blob[ini_ventana:pos_visto]
    saltos = list(re.finditer(r'\n[ \t]*\n', tramo))
    for salto in reversed(saltos):
        corte_relativo = salto.end()
        resto = tramo[corte_relativo:]
        if resto and len(resto) <= 200 and re.search(r'\d', resto):
            return ini_ventana + corte_relativo
    return None


def _fecha_desde_dateline(texto_norma):
    m = RE_DATELINE.search(texto_norma)
    if not m:
        return None
    dia_txt = re.sub(r'\s+', '', m.group('dia'))
    mes_num = MESES_3.get(_sin_acentos(m.group('mes')).upper()[:3])
    if not mes_num:
        return None
    return _fecha_norma_iso(dia_txt, mes_num, m.group('anio'))


def _extraer_sigla(texto_despues_del_numero):
    ventana = texto_despues_del_numero[:150]
    m = RE_SIGLA_GUION.search(ventana)
    if m:
        return m.group('sigla').strip('. ')
    m = RE_SIGLA_PUNTOS.search(ventana)
    if m:
        return m.group('sigla').strip('. ')
    return ''


def _normas_de_edicion(paginas_por_rubro, fecha_boletin_iso):
    anio_edicion = (fecha_boletin_iso or '')[:4]
    normas = []
    sin_formato_por_rubro = {}
    posibles_perdidas_por_rubro = {}
    for rubro, tipo_rubro in RUBROS_NORMATIVA.items():
        paginas = paginas_por_rubro.get(rubro) or []
        if not paginas:
            continue
        blob, cortes = _construir_bloque_rubro(paginas)
        candidatas = [m for m in RE_NORMA_CANDIDATA.finditer(blob)
                      if _es_encabezado_real(blob, m.end())]

        # Red de seguridad: toda norma real trae su propio "VISTO" (es
        # justamente el ancla de _es_encabezado_real). Si el bloque tiene
        # MÁS "VISTO" que encabezados reconocidos, alguna norma quedó sin
        # detectar — visto real: un Decreto cuyo tipo salió de Tesseract
        # como "pecreron" en vez de "DECRETO", irreconocible para
        # cualquier tolerancia razonable de regex. No se intenta
        # reconstruir esa norma (el número también suele salir ilegible en
        # estos casos extremos) — sólo se avisa, para que quede visible en
        # vez de perderse sin dejar rastro.
        vistos_huerfanos = [vm.start() for vm in RE_VISTO_CERCA.finditer(blob)
                             if not any(0 <= vm.start() - c.end() <= VENTANA_VISTO
                                        for c in candidatas)]
        if vistos_huerfanos:
            posibles_perdidas_por_rubro[rubro] = len(vistos_huerfanos)

        if not candidatas:
            if blob.strip():
                sin_formato_por_rubro[rubro] = len(blob.strip())
            continue

        # Límites de corte extra en los VISTO huérfanos "creíbles" (ver
        # _limite_desde_visto_huerfano). Bug real confirmado en el
        # volcado de producción (30/07/2026): sin esto, el span de la
        # norma reconocida se cortaba siempre "hasta la próxima candidata
        # RECONOCIDA" — así que una norma huérfana intercalada entre dos
        # reconocidas quedaba con su cuerpo entero pegado al FINAL de la
        # anterior. Y como _sintesis_de_texto toma la ÚLTIMA marca
        # resolutiva ("DECRETA:"/"RESUELVE:") de todo el texto, si esa
        # norma huérfana tenía la suya propia, la síntesis reportada para
        # la norma ANTERIOR terminaba siendo en realidad el Artículo 1°
        # de la norma huérfana — mal atribuida a otro número de norma.
        # Confirmado en esa misma corrida real: el Decreto "0047" (una
        # pensión a favor de María Susana Muñoz) reportó como síntesis la
        # designación de un capellán policial, que en realidad era el
        # Decreto "0048" (encabezado ilegible para OCR: "pecreroN--
        # 0048"), fusionado adentro de "0047" por este motivo. Mismo
        # patrón en la Ordenanza "2347/26", que se tragó el Decreto
        # promulgatorio "N * 0934" (ver también el fix de
        # RE_NORMA_CANDIDATA más arriba, que además ahora sí reconoce ese
        # caso puntual como candidata propia).
        limites_extra = set()
        for pos in vistos_huerfanos:
            corte = _limite_desde_visto_huerfano(blob, pos)
            if corte is not None:
                limites_extra.add(corte)
        limites = sorted({c.start() for c in candidatas} | limites_extra | {len(blob)})

        for j, m in enumerate(candidatas):
            ini = m.start()
            fin = next(L for L in limites if L > ini)
            texto_norma = _compacto_lineas(blob[ini:fin])
            pagina_pdf = _pagina_de_offset(cortes, ini)
            fecha_iso = _fecha_desde_dateline(blob[ini:min(ini + 400, fin)])
            sigla = _extraer_sigla(blob[m.end():m.end() + 150])
            normas.append({
                'tipo': _normalizar_tipo_crudo(m.group('tipo_crudo')) or tipo_rubro,
                'rubro': rubro,
                'numero': m.group('numero').strip(' .'),
                'anio': (fecha_iso or '')[:4] or anio_edicion or '????',
                'fecha': fecha_iso or fecha_boletin_iso,
                'sigla': sigla.upper(),
                'texto_completo': texto_norma,
                'pagina_pdf': pagina_pdf,
            })
    return normas, sin_formato_por_rubro, posibles_perdidas_por_rubro


# ===========================================================================
# SÍNTESIS (Artículo 1º, igual que el resto de las provincias)
# ===========================================================================
RE_MARCA_RESOLUTIVA = re.compile(
    r'^[ \t]*(RESUELVEN?|DISPONEN?|DECRETAN?|DECIDEN?|ACUERDA|ACORDARON|'
    r'SANCIONAN?\s+CON\s+FUERZA\s+DE\s+LEY)\s*:?\s*$',
    re.IGNORECASE | re.MULTILINE)

# El marcador de grado/ordinal (°/º) es lo más inconsistente que devuelve
# Tesseract en este boletín — visto real como "*", "'U+", "O" sueltas, "%"
# (encontrado en la Ordenanza 2347/26 del volcado de producción real:
# "Artículo 1%:") y una comilla tipográfica de cierre ("1”.-" en vez de
# "1º.-"); por eso la clase de caracteres de acá es deliberadamente ancha.
# "ARTÍCULO" en sí también puede salir con ruido en el medio (visto real:
# "ARTÍC:'LO" en vez de "ARTÍCULO", perdió la "U"); para ese caso puntual
# no hay tolerancia que alcance sin arriesgar falsos positivos, así que se
# acepta que _sintesis_de_texto caiga a su segundo fallback (texto después
# de la marca resolutiva) — que en la práctica da un resultado igual de
# legible.
RE_ARTICULO1 = re.compile(
    r'ART[ÍI]?CULO\s*(?:N[º°]\s*)?1(?!\d)\s*[ºo°*%"\'“”‘’]{0,2}\s*[.\-:)]+\s*'
    r'(?P<texto>[\s\S]{0,1200}?)'
    r'(?=ART[ÍI]?CULO\s*(?:N[º°]\s*)?2(?!\d)|\Z)', re.IGNORECASE)


def _sintesis_de_texto(texto):
    texto = texto or ''
    inicio = 0
    ultima_marca = None
    for m in RE_MARCA_RESOLUTIVA.finditer(texto):
        ultima_marca = m
    if ultima_marca:
        inicio = ultima_marca.end()
    m = RE_ARTICULO1.search(texto, inicio)
    if not m and inicio:
        m = RE_ARTICULO1.search(texto)
    if m:
        return _compacto(m.group('texto'))
    if inicio:
        return _compacto(texto[inicio:inicio + 500])
    return _compacto(texto[:400])


# ===========================================================================
# EMISOR — diccionario best-effort, ver docstring ("SÍNTESIS Y EMISOR")
# ===========================================================================
SIGLAS_EMISOR = {
    # Confirmadas reales (muestra 2020; puede que ya no se usen en 2026):
    'MTyC': 'MINISTERIO DE TURISMO Y CULTURA',
    'MOSP': 'MINISTERIO DE OBRAS Y SERVICIOS PÚBLICOS',
    'MPyDE': 'MINISTERIO DE PRODUCCIÓN Y DESARROLLO ECONÓMICO',
    # Adivinadas a partir del organigrama 2026 visto en la carátula de
    # autoridades (nunca confirmadas junto a su sigla real):
    'MG': 'MINISTERIO DE GOBIERNO',
    'MFyDH': 'MINISTERIO DE LA FAMILIA Y DEL DESARROLLO HUMANO',
    'ME': 'MINISTERIO DE EDUCACIÓN',
    'MEFyH': 'MINISTERIO DE ECONOMÍA, FINANZAS Y HACIENDA',
    'MPTeI': 'MINISTERIO DE PRODUCCIÓN, TRABAJO E INNOVACIÓN',
    'MS': 'MINISTERIO DE SALUD',
    'MTCyD': 'MINISTERIO DE TURISMO, CULTURA Y DEPORTE',
    'MIAyE': 'MINISTERIO DE INFRAESTRUCTURA, AGUA Y ENERGÍA',
    'MM': 'MINISTERIO DE MINERÍA',
    'H': 'HONORABLE LEGISLATURA',  # visto en "LEY N° 2828-H..."
}
# La sigla se guarda en mayúsculas (normas['sigla']) para no depender de que
# el OCR acierte la capitalización exacta de "MTyC" vs "MTYC"/"Mtyc" — así
# que la búsqueda en SIGLAS_EMISOR también tiene que ser case-insensitive
# (si no, "MTYC" nunca matchea la clave 'MTyC' del diccionario de arriba,
# bug real encontrado probando este bot contra un PDF de prueba).
_SIGLAS_EMISOR_UPPER = {k.upper(): v for k, v in SIGLAS_EMISOR.items()}


def _resolver_emisor(sigla):
    if not sigla:
        return 'PODER EJECUTIVO'
    return _SIGLAS_EMISOR_UPPER.get(sigla.upper(), sigla.upper())


# ===========================================================================
# CLASIFICACIÓN INDIVIDUAL / GENERAL
# ===========================================================================
# Mismo set base que La Rioja/Mendoza/Salta (mismo idioma administrativo
# argentino) — ver bot_salta.py para el historial de ajustes de cada patrón.
UMBRAL_INDIVIDUAL = 3

PATRONES_INDIVIDUAL = [
    (r'\bDes[íi]gn(?:[ae]se|a|ar)\b', 4, 'designación'),
    (r'\bAc[ée]pt(?:[ae]se|a|ar)\b[\s\S]{0,80}\brenuncia\b', 4, 'renuncia'),
    (r'\brenuncia\s+presentada\s+por\b', 4, 'renuncia'),
    (r'\b(?:Promu[ée]v[ae](?:se)?|Promover)\b', 4, 'promoción de un agente'),
    (r'\bContrato\s+de\s+Locaci[óo]n\s+de\s+Servicios\b', 3, 'contrato de personal'),
    (r'\bInstr[úu]yase\s+Sumario\s+Administrativo\b', 4, 'sumario administrativo'),
    (r'\bexoneraci[óo]n\b|\bcesant[íi]a\b', 4, 'sanción expulsiva'),
    (r'\bRecurso\s+Jer[áa]rquico\s+interpuesto\b', 3, 'recurso de un particular'),
    (r'\bOt[oó]rg(?:[ae]se|a|ar)\b[\s\S]{0,60}\b[Bb]eneficio\b', 3, 'beneficio a una persona'),
    # "Acuérdase" es el otro verbo real visto para conceder un beneficio
    # (pensión) — mismo molde reflexivo-impersonal que "Otórguese", pero
    # como NO estaba en ningún patrón, un Decreto real de pensión (30/07/
    # 2026, "Acuérdase el beneficio de pensión a la Señora Maria Susana
    # Muñoz...") sólo sumaba +1 por matchear la versión débil en el
    # CUERPO ("... corresponde otorgar el beneficio...", en el
    # CONSIDERANDO) y se quedaba corto del umbral -- clasificaba GENERAL
    # una norma de pensión a una persona nombrada, con CUIL y todo.
    (r'\bAcu[eé]rd(?:ase|anse|a|an|o)\b[\s\S]{0,60}\b[Bb]eneficio\b', 3, 'beneficio a una persona (acuérdase)'),
    (r'\bretiro\s+voluntario\b|\bpase\s+a\s+situaci[óo]n\s+de\s+retiro\b', 3, 'retiro/pase a retiro'),
    (r'\bBaja\s+definitiva\b|\bJubilaci[óo]n\b', 3, 'baja / jubilación'),
    (r'\bOt[óo]rg(?:[ae]se|a|ar)\b[\s\S]{0,60}\bLicencia\b', 3, 'licencia'),
    (r'\bD\.?N\.?I\.?\s*N?[º°]?\s*[\d.]{6,}', 1, 'menciona DNI de una persona'),
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
    if tipo in ('LEY', 'DECRETO LEY'):
        return False, -99, ['ley/decreto-ley: siempre general']

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
    ap = argparse.ArgumentParser(description='Scraper del Boletín Oficial de San Juan.')
    ap.add_argument('id_jurisdiccion', type=int)
    ap.add_argument('url_boletin', nargs='?', help='ignorado; se descubre solo')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--fecha', metavar='AAAA-MM-DD', help='ancla + caminata, ver docstring')
    ap.add_argument('--id-k2', type=int, metavar='N',
                    help='ítem K2 puntual (salta el descubrimiento por fecha)')
    ap.add_argument('--pdf', metavar='ARCHIVO',
                    help='usa un PDF ya descargado (pruebas offline, sin url_norma real)')
    ap.add_argument('--sin-ocr', action='store_true',
                    help='no renderiza ni corre OCR; sólo texto real embebido')
    ap.add_argument('--dpi', type=int, default=OCR_DPI_DEFAULT, help='resolución para OCR')
    ap.add_argument('--todas', action='store_true',
                    help='muestra también las individuales, con puntaje y motivos')
    ap.add_argument('--sin-filtro', action='store_true',
                    help='envía también las individuales (no afecta el filtro de '
                         'municipales, que siempre se excluyen)')
    ap.add_argument('--volcar', action='store_true', help='imprime lo reconocido y sale')
    args = ap.parse_args()

    fecha_boletin = None
    url_pdf = None
    id_k2 = None

    # ---- 1. Ubicar la edición y bajar el PDF ---------------------------------
    if args.pdf:
        with open(args.pdf, 'rb') as f:
            pdf_bytes = f.read()
        fecha_boletin = args.fecha or 'desconocida'
        print(f"Usando PDF local: {args.pdf}", file=sys.stderr)
    else:
        if args.id_k2:
            fecha_boletin, url_pdf, _ = obtener_edicion_k2(args.id_k2)
            id_k2 = args.id_k2
        elif args.fecha:
            id_k2, fecha_boletin, url_pdf = resolver_edicion_por_fecha_k2(args.fecha)
        else:
            id_k2, fecha_boletin, url_pdf = obtener_ultima_edicion_k2()

        if not fecha_boletin or not url_pdf:
            salida("warning", "No se pudo ubicar la edición a procesar en "
                              "contenido.sanjuan.gob.ar (ver stderr para el detalle).")

        print(f"Boletín del {fecha_boletin} (ítem K2 {id_k2}): {url_pdf}", file=sys.stderr)
        try:
            pdf_bytes = descargar_binario(url_pdf)
        except RuntimeError as e:
            salida("error", str(e))
        if not pdf_bytes:
            salida("error", f"No se pudo descargar el PDF de la edición: {url_pdf}")

    # ---- 2. Procesar el PDF: mapa de rubros + texto real/OCR por página -----
    try:
        paginas_por_rubro, n_texto_real, n_ocr = _procesar_pdf(pdf_bytes, args.dpi, args.sin_ocr)
    except Exception as e:
        salida("error", f"Error procesando el PDF: {e}")

    total_paginas_normativa = sum(len(v) for v in paginas_por_rubro.values())
    print(f"Páginas en rubros normativos: {total_paginas_normativa} "
          f"(texto real: {n_texto_real}, OCR: {n_ocr})", file=sys.stderr)

    ocr_hizo_falta_pero_no_disponible = (
        not args.sin_ocr and n_ocr == 0 and
        any(paginas_por_rubro.values()) and
        n_texto_real < total_paginas_normativa and
        not _verificar_ocr_disponible()
    )

    # ---- 3. Separar normas dentro de cada rubro ------------------------------
    normas_crudas, sin_formato_por_rubro, posibles_perdidas_por_rubro = _normas_de_edicion(
        paginas_por_rubro, fecha_boletin if fecha_boletin != 'desconocida' else None)

    print(f"Normas reconocidas: {len(normas_crudas)}", file=sys.stderr)
    if sin_formato_por_rubro:
        for rubro, chars in sin_formato_por_rubro.items():
            print(f"Aviso: el rubro {rubro} tiene {chars} caracteres de texto pero ninguno "
                  f"matcheó el formato de encabezado de norma esperado (RE_NORMA_CANDIDATA). "
                  f"Puede ser ruido de OCR — revisar con --volcar.", file=sys.stderr)
    if posibles_perdidas_por_rubro:
        for rubro, cantidad in posibles_perdidas_por_rubro.items():
            print(f"Aviso: el rubro {rubro} tiene {cantidad} 'VISTO' sin encabezado "
                  f"reconocible cerca — probablemente ruido de OCR severo en el nombre del "
                  f"tipo de esa/s norma/s (p.ej. 'DECRETO' leído como otra palabra). Esa "
                  f"norma no se pudo recuperar; revisar manualmente esa página del PDF.",
                  file=sys.stderr)

    if args.volcar:
        for n in normas_crudas:
            print(f"  [{n['rubro']}] {n['tipo']:22s} N° {n['numero']:>10s} "
                  f"{n['fecha'] or '?':10s} sigla={n['sigla']:8s} "
                  f"pág.PDF={n['pagina_pdf'] + 1:<4d} {n['texto_completo'][:70]!r}",
                  file=sys.stderr)
        salida("success", f"volcado: {len(normas_crudas)} normas reconocidas.")

    if ocr_hizo_falta_pero_no_disponible:
        salida("warning", "Hay páginas en rubros normativos sin texto real embebido "
                          "(probablemente escaneadas) y el OCR no está disponible en este "
                          "servidor. Instalar: apt install tesseract-ocr tesseract-ocr-spa "
                          "(y pip install pytesseract pypdfium2 Pillow si falta). No se "
                          "registra el boletín como procesado, para poder reintentar.")

    # ---- 4. Síntesis, emisor, clasificación ----------------------------------
    # (n['tipo'] ya viene normalizado desde _normas_de_edicion)
    normas_todas = []
    for n in normas_crudas:
        n['sintesis'] = _sintesis_de_texto(n['texto_completo'])
        n['emisor'] = _resolver_emisor(n['sigla'])
        n['url_norma'] = f"{url_pdf}#page={n['pagina_pdf'] + 1}" if url_pdf else (args.pdf or '')
        n['es_individual'], n['puntaje'], n['motivos'] = clasificar_norma(
            n['tipo'], n['sintesis'], n['texto_completo'])
        n['es_provincial'] = n['rubro'] not in RUBROS_MUNICIPALES
        normas_todas.append(n)

    # Filtro de jurisdicción: nunca se envían normas municipales (ver
    # RUBROS_MUNICIPALES) bajo el id_jurisdiccion de la Provincia. No
    # depende de --sin-filtro (ese flag es sobre individual/general, un
    # eje distinto) — esto es un límite de alcance, no un criterio de
    # negocio opcional. Quedan igual en debug_sanjuan.json (es_provincial
    # =false) para poder revisarlas, pero nunca se cuentan ni se mandan.
    normas = [n for n in normas_todas if n['es_provincial']]
    normas_municipales = [n for n in normas_todas if not n['es_provincial']]
    if normas_municipales:
        detalle = '; '.join(f"{n['tipo']} N° {n['numero']} ({n['emisor']})"
                             for n in normas_municipales)
        print(f"Aviso: se excluyeron {len(normas_municipales)} norma(s) de nivel MUNICIPAL "
              f"(rubro {'/'.join(sorted(RUBROS_MUNICIPALES))}) — San Juan publica ordenanzas "
              f"municipales y sus decretos promulgatorios en el mismo Boletín, pero "
              f"id_jurisdiccion={args.id_jurisdiccion} es sólo la Provincia: {detalle}. No se "
              f"envían (quedan en debug_sanjuan.json con es_provincial=false).", file=sys.stderr)

    generales = [n for n in normas if not n['es_individual']]
    individuales = [n for n in normas if n['es_individual']]
    a_enviar = normas if args.sin_filtro else generales

    guardar_debug(json.dumps(normas_todas, ensure_ascii=False, indent=2, default=str), 'debug_sanjuan.json')
    print(f"Boletín del {fecha_boletin} | normas provinciales: {len(normas)} (generales "
          f"{len(generales)} / individuales {len(individuales)})"
          + (f" | municipales excluidas: {len(normas_municipales)}" if normas_municipales else ''),
          file=sys.stderr)

    if args.dry_run:
        for n in (normas if args.todas else a_enviar):
            marca = 'IND' if n['es_individual'] else 'GEN'
            print(f"[{marca}] {n['tipo']:22s} N° {n['numero']:>10s} {n['emisor'][:30]:30s} "
                  f"{n['sintesis'][:55]}", file=sys.stderr)
            if args.todas and n.get('motivos'):
                print(f"        ({n['puntaje']:+d}) {'; '.join(n['motivos'])}", file=sys.stderr)
        salida("success", "dry-run: no se envió nada al backend.", total=len(a_enviar))

    fecha_valida = fecha_boletin and fecha_boletin != 'desconocida'

    if fecha_valida and verificar_boletin_procesado(args.id_jurisdiccion, fecha_boletin):
        salida("info", f"El boletín del {fecha_boletin} ya fue procesado.")

    if not normas:
        if fecha_valida:
            registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Sin novedades: el boletín del {fecha_boletin} no publicó "
                          f"normativa reconocible en los rubros consultados.", total=0)

    if not a_enviar:
        if fecha_valida:
            registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, 0)
        salida("success", f"Se procesó el boletín del {fecha_boletin}, pero las "
                          f"{len(individuales)} normas encontradas son actos individuales; "
                          f"no se envió ninguna.", total=0)

    # ---- 5. Envío -------------------------------------------------------------
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

    if fecha_valida:
        registrar_boletin_procesado(args.id_jurisdiccion, fecha_boletin, len(payload))

    salida("success", respuesta.get('mensaje', 'OK') or 'OK', total=len(payload))


if __name__ == '__main__':
    try:
        _main()
    except SystemExit:
        raise
    except Exception as e:
        salida("error", str(e))