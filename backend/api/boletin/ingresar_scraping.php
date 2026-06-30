<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

set_time_limit(300);
ini_set('memory_limit', '512M');
error_reporting(E_ALL);
ini_set('display_errors', 1);

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';
include_once '../../config/NormativaHelper.php';

define('SCRAPER_API_KEY', 'Token_Seguro_Scraper_2026_XyZ!');

// Verificar API Key
$headers = getallheaders();
$auth_header = isset($headers['Authorization']) ? $headers['Authorization'] : '';
if (str_replace('Bearer ', '', $auth_header) !== SCRAPER_API_KEY) {
    http_response_code(401);
    echo json_encode(["mensaje" => "Acceso denegado. API Key inválida o ausente."]);
    exit();
}

$input = file_get_contents("php://input");
$data = json_decode($input, true);

if (!isset($data['normas']) || !is_array($data['normas'])) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Formato incorrecto. Se esperaba un array 'normas'."]);
    exit();
}

$normas = $data['normas'];
$total_normas = count($normas);
$solo_categorizadas = isset($data['solo_categorizadas']) ? (bool)$data['solo_categorizadas'] : false;

if ($total_normas === 0) {
    http_response_code(400);
    echo json_encode(["mensaje" => "No hay normas para procesar."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    $db->beginTransaction();

    // --- Cachés ---
    $cache_emisores = [];
    $cache_tipos = [];

    // Pre-cargar tipos existentes
    $stmt_tipos_existentes = $db->prepare("SELECT id_tipo_norma, UPPER(descripcion) as tipo_desc FROM tipo_norma");
    $stmt_tipos_existentes->execute();
    while ($row = $stmt_tipos_existentes->fetch(PDO::FETCH_ASSOC)) {
        $cache_tipos[$row['tipo_desc']] = $row['id_tipo_norma'];
    }
    $stmt_ins_tipo = $db->prepare("INSERT INTO tipo_norma (descripcion, vigente) VALUES (:desc, 1)");

    // Categorías precompiladas
    $categorias_compiladas = NormativaHelper::cargarCategorias($db);

    // Statements de inserción
    $q_norma = "INSERT INTO norma_bo (id_tipo_norma, id_emisor_norma, numero, anio, fecha_publicacion, sintesis, url_norma, id_estado_norma)
                VALUES (:id_tipo, :id_emisor, :numero, :anio, :fecha, :sintesis, :url, 1)";
    $stmt_norma = $db->prepare($q_norma);

    $q_cat = "INSERT INTO categoria_norma_bo (id_norma_bo, id_categoria) VALUES (:id_nbo, :id_cat)";
    $stmt_cat = $db->prepare($q_cat);

    // Combinaciones existentes (para evitar duplicados)
    $combinaciones_existentes = [];
    $stmt_comb = $db->prepare("
        SELECT CONCAT(id_tipo_norma, '|', numero, '|', anio, '|', id_emisor_norma) as clave 
        FROM norma_bo 
        UNION 
        SELECT CONCAT(id_tipo_norma, '|', numero, '|', anio, '|', id_emisor_norma) as clave 
        FROM norma
    ");
    $stmt_comb->execute();
    while ($row = $stmt_comb->fetchColumn()) {
        $combinaciones_existentes[$row] = true;
    }

    // URLs existentes para dedup
    $urls_existentes = [];
    $stmt_urls = $db->prepare("SELECT url_norma FROM norma_bo UNION SELECT url_norma FROM norma");
    $stmt_urls->execute();
    while ($row = $stmt_urls->fetch(PDO::FETCH_ASSOC)) {
        $urls_existentes[$row['url_norma']] = true;
    }

    $id_jurisdiccion = null;
    foreach ($normas as $n) {
        if (isset($n['id_jurisdiccion'])) {
            $id_jurisdiccion = (int)$n['id_jurisdiccion'];
            break;
        }
    }

    $procesadas = 0;
    $omitidas = 0;
    $omitidas_sin_categoria = 0;
    $errores = 0;
    $total_categorias_asignadas = 0;
    $errores_detalles = [];

    foreach ($normas as $index => $norma) {
        try {
            // --- Validar campos obligatorios ---
            if (!isset($norma['tipo_norma_desc']) || empty($norma['tipo_norma_desc'])) {
                throw new Exception("Tipo de norma vacío en índice $index");
            }
            if (!isset($norma['nombre_emisor']) || empty($norma['nombre_emisor'])) {
                throw new Exception("Emisor vacío en índice $index");
            }

            // --- TIPO ---
            $tipo_norma_desc = strtoupper(trim($norma['tipo_norma_desc']));
            if (isset($cache_tipos[$tipo_norma_desc])) {
                $id_tipo = $cache_tipos[$tipo_norma_desc];
            } else {
                $stmt_ins_tipo->execute([':desc' => $tipo_norma_desc]);
                $id_tipo = $db->lastInsertId();
                $cache_tipos[$tipo_norma_desc] = $id_tipo;
            }

            // --- EMISOR ---
            $id_jur = isset($norma['id_jurisdiccion']) ? (int)$norma['id_jurisdiccion'] : $id_jurisdiccion;
            $emisor_desc = trim($norma['nombre_emisor']);
            if ($emisor_desc === '') {
                $emisor_desc = 'PODER EJECUTIVO DE LA CIUDAD DE BUENOS AIRES';
            }
            $id_emisor_final = NormativaHelper::resolverEmisor($db, $id_jur, $emisor_desc, $cache_emisores);
            if (!$id_emisor_final) {
                throw new Exception("No se pudo resolver el emisor '$emisor_desc' para índice $index");
            }

            // --- CAMPOS DE LA NORMA ---
            $numero = isset($norma['numero']) ? htmlspecialchars(strip_tags($norma['numero'])) : 'S/N';
            $anio = isset($norma['anio']) ? filter_var($norma['anio'], FILTER_VALIDATE_INT) : date('Y');
            if ($numero === '' || $numero === null) $numero = 'S/N';
            if ($anio === '' || $anio === null || $anio === false) $anio = (int)date('Y');

            $fecha = isset($norma['fecha_publicacion']) ? htmlspecialchars(strip_tags($norma['fecha_publicacion'])) : date('Y-m-d');
            $url = isset($norma['url_norma']) ? filter_var($norma['url_norma'], FILTER_SANITIZE_URL) : '';
            $sintesis = isset($norma['sintesis']) ? htmlspecialchars(strip_tags($norma['sintesis'])) : '';
            $texto_completo = isset($norma['texto_completo']) ? (string)$norma['texto_completo'] : '';

            // --- Verificación de duplicados por URL ---
            if (!empty($url) && isset($urls_existentes[$url])) {
                $omitidas++;
                continue;
            }

            // --- Verificar combinación única ---
            $clave_unica = "{$id_tipo}|{$numero}|{$anio}|{$id_emisor_final}";
            if (isset($combinaciones_existentes[$clave_unica])) {
                $omitidas++;
                continue;
            }

            // --- Categorización ---
            $texto_a_clasificar = trim($sintesis . ' ' . $texto_completo);
            $cats_detectadas = NormativaHelper::categorizarTexto($texto_a_clasificar, $categorias_compiladas);

            if ($solo_categorizadas && empty($cats_detectadas)) {
                $omitidas_sin_categoria++;
                continue;
            }

            // --- INSERT ---
            $stmt_norma->bindParam(":id_tipo", $id_tipo);
            $stmt_norma->bindParam(":id_emisor", $id_emisor_final);
            $stmt_norma->bindParam(":numero", $numero);
            $stmt_norma->bindParam(":anio", $anio);
            $stmt_norma->bindParam(":fecha", $fecha);
            $stmt_norma->bindParam(":sintesis", $sintesis);
            $stmt_norma->bindParam(":url", $url);
            if (!$stmt_norma->execute()) {
                $errorInfo = $stmt_norma->errorInfo();
                throw new Exception("Error en INSERT: " . $errorInfo[2]);
            }

            $id_norma_bo = $db->lastInsertId();
            $procesadas++;

            // Marcar como ya visto
            if (!empty($url)) {
                $urls_existentes[$url] = true;
            }
            $combinaciones_existentes[$clave_unica] = true;

            // Insertar categorías
            foreach ($cats_detectadas as $id_cat) {
                $stmt_cat->bindValue(":id_nbo", $id_norma_bo, PDO::PARAM_INT);
                $stmt_cat->bindValue(":id_cat", (int)$id_cat, PDO::PARAM_INT);
                $stmt_cat->execute();
                $total_categorias_asignadas++;
            }

        } catch (Exception $e) {
            $errores++;
            $errores_detalles[] = "Índice $index: " . $e->getMessage();
            error_log("INGRESAR_SCRAPING: Error en norma $index: " . $e->getMessage());
            // Continuar con la siguiente norma
        }
    }

    $db->commit();

    // Registrar historial
    if ($procesadas > 0 && isset($normas[0]['fecha_publicacion'])) {
        $fecha_boletin = $normas[0]['fecha_publicacion'];
        $query_historial = "INSERT IGNORE INTO historial_scraping (id_jurisdiccion, fecha_boletin, cantidad_normas)
                            VALUES (:id, :fecha, :cant)";
        $stmt_hist = $db->prepare($query_historial);
        $stmt_hist->execute([
            ':id' => $id_jurisdiccion,
            ':fecha' => $fecha_boletin,
            ':cant' => $procesadas
        ]);
    }

    $mensaje = "Se procesaron $procesadas normas nuevas. Duplicados omitidos: $omitidas. Sin categoría omitidas: $omitidas_sin_categoria. Errores: $errores. Categorías asignadas: $total_categorias_asignadas.";
    if ($errores > 0) {
        $mensaje .= " Primeros errores: " . implode('; ', array_slice($errores_detalles, 0, 5));
    }
    http_response_code(200);
    echo json_encode([
        "mensaje" => $mensaje,
        "procesadas" => $procesadas,
        "omitidas" => $omitidas,
        "omitidas_sin_categoria" => $omitidas_sin_categoria,
        "errores" => $errores,
        "categorias_asignadas" => $total_categorias_asignadas,
        "detalle_errores" => $errores_detalles // opcional, para depuración
    ]);

} catch (Exception $e) {
    $db->rollBack();
    error_log("INGRESAR_SCRAPING: ERROR CRÍTICO: " . $e->getMessage());
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al guardar en la BD.", "error" => $e->getMessage()]);
}
?>