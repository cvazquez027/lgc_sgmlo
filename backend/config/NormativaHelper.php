<?php
/**
 * NormativaHelper.php
 * ---------------------------------------------------------------------------
 * Lógica central y reutilizable para el procesamiento de normativa de boletines
 * oficiales. TODA la "inteligencia" vive acá, para que agregar un bot nuevo
 * (otra provincia, Paraguay, Uruguay, etc.) NO requiera reimplementar nada.
 *
 * Responsabilidades:
 *   1. normalizarClave()   -> clave canónica para comparar/deduplicar strings.
 *   2. resolverEmisor()    -> dedup robusto de emisores (a prueba de carrera).
 *   3. cargarCategorias()  -> trae categorías vigentes y precompila sus patrones.
 *   4. categorizarTexto()  -> matchea categorías sobre texto (acento-insensible,
 *                             tolerante a plural/singular, soporta sinónimos con '|').
 *   5. migrarCategorias()  -> copia categorías de norma_bo a norma al promover.
 *
 * Diseño: funciones puras / estáticas que reciben la conexión PDO. Sin estado
 * global, sin echo, sin headers. Esto es una librería, no un endpoint.
 * ---------------------------------------------------------------------------
 */

class NormativaHelper
{
    /**
     * LISTA NEGRA de keywords de UNA sola palabra que NO deben flexionar plural.
     * Motivo: su plural colisiona con topónimos o palabras frecuentes y produce
     * falsos positivos. Ej: "aire" -> "aires" matchea "Buenos Aires".
     *
     * Estas keywords se matchean EXACTAS (con límite de palabra), sin sufijo
     * opcional de plural. Solo aplica a categorías de una sola palabra; en frases
     * de 2+ palabras el contexto desambigua y la flexión se mantiene.
     *
     * Los valores van NORMALIZADOS (minúsculas, sin tildes), igual que normalizarClave().
     * Para agregar más casos en el futuro, sumalos acá y listo.
     */
    private static $KEYWORDS_SIN_PLURAL = [
        'aire' => true,   // colisiona con "Buenos Aires"
    ];

    /**
     * Normaliza un string a una CLAVE canónica para comparación/dedup.
     * Reglas (deben coincidir EXACTAMENTE con el backfill SQL de la migración):
     *   - a minúsculas (multibyte-safe)
     *   - quita tildes y diacríticos del español
     *   - reemplaza todo lo que no sea [a-z0-9 espacio] por espacio
     *   - colapsa espacios múltiples y hace trim
     *
     * Ej: "DIRECCIÓN  General, S.A." -> "direccion general s a"
     */
    public static function normalizarClave($texto)
    {
        if ($texto === null) {
            return '';
        }
        $texto = (string)$texto;

        // a) minúsculas multibyte
        $texto = mb_strtolower($texto, 'UTF-8');

        // b) quitar diacríticos. Mapa explícito = sin dependencia de iconv/intl.
        $reemplazos = [
            'á' => 'a', 'à' => 'a', 'ä' => 'a', 'â' => 'a', 'ã' => 'a',
            'é' => 'e', 'è' => 'e', 'ë' => 'e', 'ê' => 'e',
            'í' => 'i', 'ì' => 'i', 'ï' => 'i', 'î' => 'i',
            'ó' => 'o', 'ò' => 'o', 'ö' => 'o', 'ô' => 'o', 'õ' => 'o',
            'ú' => 'u', 'ù' => 'u', 'ü' => 'u', 'û' => 'u',
            'ñ' => 'n', 'ç' => 'c',
        ];
        $texto = strtr($texto, $reemplazos);

        // c) todo lo que no sea letra/dígito/espacio -> espacio
        $texto = preg_replace('/[^a-z0-9 ]+/u', ' ', $texto);

        // d) colapsar espacios y trim
        $texto = preg_replace('/\s+/u', ' ', $texto);

        return trim($texto);
    }

    /**
     * Resuelve (encuentra o crea) el id_emisor_norma para una jurisdicción dada,
     * deduplicando por clave normalizada. A prueba de condiciones de carrera
     * gracias al índice único (id_jurisdiccion, clave_normalizada) + ON DUPLICATE KEY.
     *
     * Usa un cache pasado por referencia para evitar consultas repetidas dentro
     * de una misma corrida (clave de cache = "{id_jur}|{clave_normalizada}").
     *
     * @param PDO    $db
     * @param int    $id_jurisdiccion
     * @param string $descripcion_cruda  El nombre del emisor tal cual lo manda el bot.
     * @param array  $cache              Cache por referencia.
     * @return int   id_emisor_norma
     */
    public static function resolverEmisor(PDO $db, $id_jurisdiccion, $descripcion_cruda, array &$cache)
    {
        $id_jurisdiccion = (int)$id_jurisdiccion;

        $descripcion = trim((string)$descripcion_cruda);
        if ($descripcion === '') {
            // Fallback genérico. El llamador puede pre-resolver un default mejor
            // (ej. "PODER EJECUTIVO NACIONAL") antes de llamar acá.
            $descripcion = 'SIN EMISOR';
        }

        $clave = self::normalizarClave($descripcion);
        $cacheKey = $id_jurisdiccion . '|' . $clave;

        if (isset($cache[$cacheKey])) {
            return $cache[$cacheKey];
        }

        // 1) Buscar por clave normalizada (no por descripción cruda).
        $stmt = $db->prepare(
            "SELECT id_emisor_norma FROM emisor_norma
             WHERE id_jurisdiccion = :id_jur AND clave_normalizada = :clave
             LIMIT 1"
        );
        $stmt->execute([':id_jur' => $id_jurisdiccion, ':clave' => $clave]);
        $id = $stmt->fetchColumn();

        if ($id) {
            $cache[$cacheKey] = (int)$id;
            return (int)$id;
        }

        // 2) No existe: insertar. ON DUPLICATE KEY protege contra otro proceso
        //    que haya insertado la misma clave en paralelo entre el SELECT y el INSERT.
        $stmt_ins = $db->prepare(
            "INSERT INTO emisor_norma (id_jurisdiccion, descripcion, clave_normalizada)
             VALUES (:id_jur, :desc, :clave)
             ON DUPLICATE KEY UPDATE id_emisor_norma = LAST_INSERT_ID(id_emisor_norma)"
        );
        $stmt_ins->execute([
            ':id_jur' => $id_jurisdiccion,
            ':desc'   => $descripcion,
            ':clave'  => $clave,
        ]);

        // lastInsertId() devuelve el id nuevo, o —gracias a LAST_INSERT_ID() en el
        // UPDATE— el id existente si hubo choque de clave única.
        $id_final = (int)$db->lastInsertId();

        // Defensa adicional: si por alguna razón devolviera 0, releemos.
        if ($id_final === 0) {
            $stmt->execute([':id_jur' => $id_jurisdiccion, ':clave' => $clave]);
            $id_final = (int)$stmt->fetchColumn();
        }

        $cache[$cacheKey] = $id_final;
        return $id_final;
    }

    /**
     * Resuelve (encuentra o crea) el id_tipo_norma para una descripción dada,
     * deduplicando por clave normalizada. Calco de resolverEmisor(), pero sin
     * partición por jurisdicción: tipo_norma es una lista global compartida
     * por todos los bots.
     *
     * Requiere que exista un índice único sobre `clave_normalizada` en
     * tipo_norma (lo crea la migración migrar_normalizacion.php) para que el
     * ON DUPLICATE KEY funcione como protección ante condiciones de carrera.
     *
     * Usa un cache pasado por referencia para evitar consultas repetidas
     * dentro de una misma corrida (clave de cache = clave_normalizada).
     *
     * @param PDO    $db
     * @param string $descripcion_cruda  El tipo tal cual lo manda el bot
     *                                   ("Resolucion", "RESOLUCIÓN", etc).
     * @param array  $cache              Cache por referencia.
     * @return int   id_tipo_norma
     */
    public static function resolverTipoNorma(PDO $db, $descripcion_cruda, array &$cache)
    {
        $descripcion = trim((string)$descripcion_cruda);
        if ($descripcion === '') {
            $descripcion = 'SIN TIPO';
        }
        // Igual que el resto de tipo_norma: se guarda en mayúsculas (con tildes).
        $descripcion_mayus = mb_strtoupper($descripcion, 'UTF-8');

        $clave = self::normalizarClave($descripcion_mayus);

        if (isset($cache[$clave])) {
            return $cache[$clave];
        }

        // 1) Buscar por clave normalizada (no por descripción cruda).
        $stmt = $db->prepare(
            "SELECT id_tipo_norma FROM tipo_norma WHERE clave_normalizada = :clave LIMIT 1"
        );
        $stmt->execute([':clave' => $clave]);
        $id = $stmt->fetchColumn();

        if ($id) {
            $cache[$clave] = (int)$id;
            return (int)$id;
        }

        // 2) No existe: insertar. ON DUPLICATE KEY protege contra otro proceso
        //    que haya insertado la misma clave en paralelo entre el SELECT y
        //    el INSERT (dos bots corriendo al mismo tiempo, por ejemplo).
        $stmt_ins = $db->prepare(
            "INSERT INTO tipo_norma (descripcion, vigente, clave_normalizada)
             VALUES (:desc, 1, :clave)
             ON DUPLICATE KEY UPDATE id_tipo_norma = LAST_INSERT_ID(id_tipo_norma)"
        );
        $stmt_ins->execute([
            ':desc'  => $descripcion_mayus,
            ':clave' => $clave,
        ]);

        $id_final = (int)$db->lastInsertId();

        if ($id_final === 0) {
            $stmt->execute([':clave' => $clave]);
            $id_final = (int)$stmt->fetchColumn();
        }

        $cache[$clave] = $id_final;
        return $id_final;
    }

    /**
     * Carga las categorías vigentes y precompila un patrón regex por cada una.
     *
     * Cada categoría:
     *   - Su 'descripcion' puede contener sinónimos separados por '|'
     *     (ej. "PCBs | Bifenilos policlorados"). Cada sinónimo se vuelve una
     *     alternativa: si CUALQUIERA matchea, la categoría aplica.
     *   - Cada sinónimo se normaliza (sin tildes, minúsculas) y se convierte en
     *     un patrón que tolera plural/singular en cada palabra significativa
     *     (residuo <-> residuos, peligroso <-> peligrosos).
     *
     * Devuelve: [ ['id' => int, 'regex' => string], ... ]
     */
    public static function cargarCategorias(PDO $db)
    {
        $stmt = $db->prepare("SELECT id_categoria, descripcion FROM categoria WHERE vigente = 1");
        $stmt->execute();
        $filas = $stmt->fetchAll(PDO::FETCH_ASSOC);

        $compiladas = [];
        foreach ($filas as $cat) {
            $id_cat = (int)$cat['id_categoria'];
            $sinonimos = explode('|', $cat['descripcion']);

            $alternativas = [];
            foreach ($sinonimos as $sin) {
                $patron = self::construirPatronFrase($sin);
                if ($patron !== '') {
                    $alternativas[] = $patron;
                }
            }
            if (empty($alternativas)) {
                continue;
            }

            // Regex final: (alt1|alt2|...), case-insensitive, unicode.
            // El texto contra el que se matchea YA viene normalizado, así que
            // no necesitamos /i, pero lo dejamos por robustez.
            $regex = '/(?:' . implode('|', $alternativas) . ')/u';
            $compiladas[] = ['id' => $id_cat, 'regex' => $regex];
        }

        return $compiladas;
    }

    /**
     * Construye el patrón regex de UNA frase clave, tolerante a plural/singular.
     * - Normaliza la frase (sin tildes, minúsculas, espacios colapsados).
     * - Cada palabra de >=3 letras admite sufijo opcional 's' o 'es'.
     * - Usa límites de palabra para no matchear dentro de otra palabra.
     *
     * Ej: "residuo peligroso" -> \bresiduo(?:e?s)?\s+peligroso(?:e?s)?\b
     */
    private static function construirPatronFrase($frase)
    {
        $frase = self::normalizarClave($frase);
        if ($frase === '') {
            return '';
        }

        $palabras = array_values(array_filter(explode(' ', $frase), function ($x) {
            return $x !== '';
        }));
        if (empty($palabras)) {
            return '';
        }

        // ¿Es una keyword de UNA sola palabra incluida en la lista negra?
        // En ese caso se matchea exacta, sin flexión de plural (evita falsos
        // positivos como "aire" dentro de "Buenos Aires").
        $es_monopalabra = (count($palabras) === 1);
        $en_lista_negra = $es_monopalabra && isset(self::$KEYWORDS_SIN_PLURAL[$palabras[0]]);

        $partes = [];
        foreach ($palabras as $p) {
            // Palabras cortas (de, la, en, y...), numéricas, o en lista negra:
            // sin flexión de plural.
            if (!$en_lista_negra && mb_strlen($p, 'UTF-8') >= 4 && !ctype_digit($p)) {
                // Llevamos la palabra a su RAÍZ singular y hacemos el plural opcional,
                // para que el match sea simétrico: la categoría puede venir en plural
                // ("residuos") y el texto en singular ("residuo"), o viceversa.
                $raiz = self::raizSingular($p);
                $partes[] = preg_quote($raiz, '/') . '(?:e?s)?';
            } else {
                $partes[] = preg_quote($p, '/');
            }
        }

        // Separador entre palabras: uno o más espacios.
        return '\b' . implode('\s+', $partes) . '\b';
    }

    /**
     * Devuelve la raíz singular aproximada de una palabra ya normalizada.
     * Heurística simple para español (sin diccionario):
     *   - termina en "es" (>=5 letras) -> saca "es"   (motores -> motor)
     *   - termina en "s"  (>=4 letras) -> saca "s"    (residuos -> residuo)
     * No es morfología perfecta, pero alcanza para que el plural sea opcional
     * de forma simétrica al recompilar con (?:e?s)?.
     */
    private static function raizSingular($palabra)
    {
        $len = mb_strlen($palabra, 'UTF-8');
        if ($len >= 5 && substr($palabra, -2) === 'es') {
            return substr($palabra, 0, -2);
        }
        if ($len >= 4 && substr($palabra, -1) === 's') {
            return substr($palabra, 0, -1);
        }
        return $palabra;
    }

    /**
     * Categoriza un texto contra las categorías precompiladas.
     *
     * @param string $texto         Texto a clasificar (síntesis + cuerpo completo).
     * @param array  $categorias    Salida de cargarCategorias().
     * @return int[] Lista de id_categoria detectadas (sin duplicados).
     */
    public static function categorizarTexto($texto, array $categorias)
    {
        if ($texto === null || $texto === '' || empty($categorias)) {
            return [];
        }

        // Normalizamos el texto UNA vez. Así el matching es accent/case-insensible
        // de forma consistente con cómo construimos los patrones.
        $texto_norm = self::normalizarClave($texto);
        if ($texto_norm === '') {
            return [];
        }

        $encontradas = [];
        foreach ($categorias as $cat) {
            if (preg_match($cat['regex'], $texto_norm)) {
                $encontradas[$cat['id']] = true; // dedup por clave
            }
        }

        return array_keys($encontradas);
    }

    /**
     * Migra las categorías de una norma del buffer (categoria_norma_bo) a la
     * tabla definitiva (categoria_norma) al promover.
     *
     * Hace un INSERT ... SELECT en una sola operación (sin loop PHP).
     *
     * @param PDO $db
     * @param int $id_norma_bo   Origen (buffer).
     * @param int $id_norma      Destino (norma definitiva recién creada).
     * @return int Cantidad de categorías migradas.
     */
    public static function migrarCategorias(PDO $db, $id_norma_bo, $id_norma)
    {
        $id_norma_bo = (int)$id_norma_bo;
        $id_norma    = (int)$id_norma;

        $stmt = $db->prepare(
            "INSERT INTO categoria_norma (id_norma, id_categoria)
             SELECT :id_norma, id_categoria
             FROM categoria_norma_bo
             WHERE id_norma_bo = :id_bo"
        );
        $stmt->execute([':id_norma' => $id_norma, ':id_bo' => $id_norma_bo]);

        return $stmt->rowCount();
    }
    
    /**
     * Construye la cláusula WHERE y los parámetros para filtrar normas_bo
     * a partir de un objeto de filtros (igual que en leer_scraping.php)
     *
     * @param PDO   $db
     * @param object $filtros  (con propiedades: id_jurisdiccion, soloCategorizadas, q, id_tipo_norma, id_emisor_norma, id_categoria[], fecha_desde, fecha_hasta)
     * @return array [$whereClause, $params]
     */
    public static function buildScrapingFilters($db, $filtros) {
        $where = [];
        $params = [];

        if (!empty($filtros->id_jurisdiccion)) {
            $where[] = "en.id_jurisdiccion = :id_jur";
            $params[':id_jur'] = $filtros->id_jurisdiccion;
        }
        if (!empty($filtros->soloCategorizadas)) {
            $where[] = "EXISTS (SELECT 1 FROM categoria_norma_bo cnbo2 WHERE cnbo2.id_norma_bo = nbo.id_norma_bo)";
        }
        if (!empty($filtros->q)) {
            $searchParam = "%{$filtros->q}%";
            $where[] = "(nbo.numero LIKE :search1 OR CAST(nbo.anio AS CHAR) LIKE :search2 OR nbo.sintesis LIKE :search3)";
            $params[':search1'] = $searchParam;
            $params[':search2'] = $searchParam;
            $params[':search3'] = $searchParam;
        }
        if (!empty($filtros->id_tipo_norma)) {
            $where[] = "nbo.id_tipo_norma = :id_tipo";
            $params[':id_tipo'] = $filtros->id_tipo_norma;
        }
        if (!empty($filtros->id_emisor_norma)) {
            $where[] = "nbo.id_emisor_norma = :id_emisor";
            $params[':id_emisor'] = $filtros->id_emisor_norma;
        }
        if (!empty($filtros->id_categoria) && is_array($filtros->id_categoria)) {
            $placeholders = [];
            foreach ($filtros->id_categoria as $idx => $catId) {
                $key = ":id_cat_{$idx}";
                $placeholders[] = $key;
                $params[$key] = $catId;
            }
            if (!empty($placeholders)) {
                $where[] = "EXISTS (SELECT 1 FROM categoria_norma_bo cnbo3 
                            WHERE cnbo3.id_norma_bo = nbo.id_norma_bo 
                            AND cnbo3.id_categoria IN (" . implode(',', $placeholders) . "))";
            }
        }
        if (!empty($filtros->fecha_desde)) {
            $where[] = "nbo.fecha_publicacion >= :fecha_desde";
            $params[':fecha_desde'] = $filtros->fecha_desde;
        }
        if (!empty($filtros->fecha_hasta)) {
            $where[] = "nbo.fecha_publicacion <= :fecha_hasta";
            $params[':fecha_hasta'] = $filtros->fecha_hasta;
        }

        $whereClause = empty($where) ? "" : "WHERE " . implode(" AND ", $where);
        return [$whereClause, $params];
    }
}