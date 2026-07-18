<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';

// Filtros (mismos que en leer_scraping)
$id_jurisdiccion = isset($_GET['id_jurisdiccion']) && $_GET['id_jurisdiccion'] !== '' ? filter_var($_GET['id_jurisdiccion'], FILTER_VALIDATE_INT) : null;
$soloCategorizadas = isset($_GET['soloCategorizadas']) && filter_var($_GET['soloCategorizadas'], FILTER_VALIDATE_BOOLEAN);
$fechaDesde = isset($_GET['fecha_desde']) && $_GET['fecha_desde'] !== '' ? $_GET['fecha_desde'] : null;
$fechaHasta = isset($_GET['fecha_hasta']) && $_GET['fecha_hasta'] !== '' ? $_GET['fecha_hasta'] : null;
$searchText = isset($_GET['q']) ? trim($_GET['q']) : '';

$database = new Database();
$db = $database->getConnection();

try {
    // Construir condiciones WHERE (reutilizando la lógica de leer_scraping)
    $where = [];
    $params = [];

    if ($id_jurisdiccion) {
        $where[] = "en.id_jurisdiccion = :id_jur";
        $params[':id_jur'] = $id_jurisdiccion;
    }
    if ($soloCategorizadas) {
        $where[] = "EXISTS (SELECT 1 FROM categoria_norma_bo cnbo2 WHERE cnbo2.id_norma_bo = nbo.id_norma_bo)";
    }
    if (!empty($searchText)) {
        $searchParam = "%{$searchText}%";
        $where[] = "(nbo.numero LIKE :search1 OR CAST(nbo.anio AS CHAR) LIKE :search2 OR nbo.sintesis LIKE :search3)";
        $params[':search1'] = $searchParam;
        $params[':search2'] = $searchParam;
        $params[':search3'] = $searchParam;
    }
    if ($fechaDesde) {
        $where[] = "nbo.fecha_publicacion >= :fecha_desde";
        $params[':fecha_desde'] = $fechaDesde;
    }
    if ($fechaHasta) {
        $where[] = "nbo.fecha_publicacion <= :fecha_hasta";
        $params[':fecha_hasta'] = $fechaHasta;
    }

    $whereClause = empty($where) ? "" : "WHERE " . implode(" AND ", $where);

    // 1. Tipos de norma únicos presentes en norma_bo
    $query_tipos = "SELECT DISTINCT nbo.id_tipo_norma, tn.descripcion
                    FROM norma_bo nbo
                    INNER JOIN emisor_norma en ON nbo.id_emisor_norma = en.id_emisor_norma
                    LEFT JOIN tipo_norma tn ON nbo.id_tipo_norma = tn.id_tipo_norma
                    $whereClause
                    AND nbo.id_tipo_norma IS NOT NULL
                    ORDER BY tn.descripcion ASC";
    $stmt_tipos = $db->prepare($query_tipos);
    foreach ($params as $key => &$val) {
        $stmt_tipos->bindParam($key, $val);
    }
    $stmt_tipos->execute();
    $tipos = $stmt_tipos->fetchAll(PDO::FETCH_ASSOC);

    // 2. Emisores únicos presentes en norma_bo
    $query_emisores = "SELECT DISTINCT nbo.id_emisor_norma, en.descripcion
                       FROM norma_bo nbo
                       INNER JOIN emisor_norma en ON nbo.id_emisor_norma = en.id_emisor_norma
                       $whereClause
                       AND nbo.id_emisor_norma IS NOT NULL
                       ORDER BY en.descripcion ASC";
    $stmt_emisores = $db->prepare($query_emisores);
    foreach ($params as $key => &$val) {
        $stmt_emisores->bindParam($key, $val);
    }
    $stmt_emisores->execute();
    $emisores = $stmt_emisores->fetchAll(PDO::FETCH_ASSOC);

    // 3. Categorías únicas presentes en norma_bo (a través de categoria_norma_bo)
    $query_categorias = "SELECT DISTINCT c.id_categoria, c.descripcion
                         FROM categoria_norma_bo cnbo
                         INNER JOIN norma_bo nbo ON cnbo.id_norma_bo = nbo.id_norma_bo
                         INNER JOIN emisor_norma en ON nbo.id_emisor_norma = en.id_emisor_norma
                         INNER JOIN categoria c ON cnbo.id_categoria = c.id_categoria
                         $whereClause
                         ORDER BY c.descripcion ASC";
    $stmt_categorias = $db->prepare($query_categorias);
    foreach ($params as $key => &$val) {
        $stmt_categorias->bindParam($key, $val);
    }
    $stmt_categorias->execute();
    $categorias = $stmt_categorias->fetchAll(PDO::FETCH_ASSOC);

    http_response_code(200);
    echo json_encode([
        "tipos" => $tipos,
        "emisores" => $emisores,
        "categorias" => $categorias
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al obtener filtros disponibles.", "error" => $e->getMessage()]);
}
?>