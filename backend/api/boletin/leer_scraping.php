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

// Parámetros de paginación
$page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
$limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 30;
$offset = ($page - 1) * $limit;

// Filtros existentes
$id_jurisdiccion = isset($_GET['id_jurisdiccion']) && $_GET['id_jurisdiccion'] !== '' ? filter_var($_GET['id_jurisdiccion'], FILTER_VALIDATE_INT) : null;
$soloCategorizadas = isset($_GET['soloCategorizadas']) && filter_var($_GET['soloCategorizadas'], FILTER_VALIDATE_BOOLEAN);

// NUEVOS FILTROS
$searchText = isset($_GET['q']) ? trim($_GET['q']) : '';
$filtroTipo = isset($_GET['id_tipo_norma']) && $_GET['id_tipo_norma'] !== '' ? (int)$_GET['id_tipo_norma'] : null;
$filtroEmisor = isset($_GET['id_emisor_norma']) && $_GET['id_emisor_norma'] !== '' ? (int)$_GET['id_emisor_norma'] : null;

// CATEGORÍAS MÚLTIPLES (recibe como array)
$filtroCategorias = isset($_GET['id_categoria']) ? $_GET['id_categoria'] : [];
if (!is_array($filtroCategorias)) {
    $filtroCategorias = array_filter([$filtroCategorias]);
}

$fechaDesde = isset($_GET['fecha_desde']) && $_GET['fecha_desde'] !== '' ? $_GET['fecha_desde'] : null;
$fechaHasta = isset($_GET['fecha_hasta']) && $_GET['fecha_hasta'] !== '' ? $_GET['fecha_hasta'] : null;

$database = new Database();
$db = $database->getConnection();

try {
    $where = [];
    $params = [];

    // 1. Filtro por jurisdicción
    if ($id_jurisdiccion) {
        $where[] = "en.id_jurisdiccion = :id_jur";
        $params[':id_jur'] = $id_jurisdiccion;
    }

    // 2. Filtro "solo categorizadas"
    if ($soloCategorizadas) {
        $where[] = "EXISTS (SELECT 1 FROM categoria_norma_bo cnbo2 WHERE cnbo2.id_norma_bo = nbo.id_norma_bo)";
    }

    // 3. Búsqueda por texto (mejorada)
    if (!empty($searchText)) {
        $searchParam = "%{$searchText}%";
        $where[] = "(nbo.numero LIKE :search1 OR CAST(nbo.anio AS CHAR) LIKE :search2 OR nbo.sintesis LIKE :search3)";
        $params[':search1'] = $searchParam;
        $params[':search2'] = $searchParam;
        $params[':search3'] = $searchParam;
    }

    // 4. Filtro por tipo de norma
    if ($filtroTipo) {
        $where[] = "nbo.id_tipo_norma = :id_tipo";
        $params[':id_tipo'] = $filtroTipo;
    }

    // 5. Filtro por emisor
    if ($filtroEmisor) {
        $where[] = "nbo.id_emisor_norma = :id_emisor";
        $params[':id_emisor'] = $filtroEmisor;
    }

    // 6. Filtro por categorías múltiples (acumulables)
    if (!empty($filtroCategorias)) {
        $placeholders = [];
        foreach ($filtroCategorias as $idx => $catId) {
            $catId = (int)$catId;
            if ($catId > 0) {
                $key = ":id_cat_{$idx}";
                $placeholders[] = $key;
                $params[$key] = $catId;
            }
        }
        if (!empty($placeholders)) {
            $where[] = "EXISTS (SELECT 1 FROM categoria_norma_bo cnbo3 
                        WHERE cnbo3.id_norma_bo = nbo.id_norma_bo 
                        AND cnbo3.id_categoria IN (" . implode(',', $placeholders) . "))";
        }
    }

    // 7. Filtro por rango de fechas
    if ($fechaDesde) {
        $where[] = "nbo.fecha_publicacion >= :fecha_desde";
        $params[':fecha_desde'] = $fechaDesde;
    }
    if ($fechaHasta) {
        $where[] = "nbo.fecha_publicacion <= :fecha_hasta";
        $params[':fecha_hasta'] = $fechaHasta;
    }

    $whereClause = empty($where) ? "" : "WHERE " . implode(" AND ", $where);

    // Total de registros
    $query_count = "SELECT COUNT(DISTINCT nbo.id_norma_bo) as total 
                    FROM norma_bo nbo
                    INNER JOIN emisor_norma en ON nbo.id_emisor_norma = en.id_emisor_norma
                    INNER JOIN jurisdiccion j ON en.id_jurisdiccion = j.id_jurisdiccion
                    $whereClause";
    $stmt_count = $db->prepare($query_count);
    foreach ($params as $key => &$val) {
        $stmt_count->bindParam($key, $val);
    }
    $stmt_count->execute();
    $total = (int)$stmt_count->fetchColumn();

    // Datos paginados
    $query = "SELECT 
                nbo.*, 
                tn.descripcion as tipo_norma_desc,
                en.descripcion as emisor_desc,
                j.descripcion as jurisdiccion_desc,
                GROUP_CONCAT(c.descripcion SEPARATOR ', ') as categorias_detectadas
              FROM norma_bo nbo
              LEFT JOIN tipo_norma tn ON nbo.id_tipo_norma = tn.id_tipo_norma
              INNER JOIN emisor_norma en ON nbo.id_emisor_norma = en.id_emisor_norma
              INNER JOIN jurisdiccion j ON en.id_jurisdiccion = j.id_jurisdiccion
              LEFT JOIN categoria_norma_bo cnbo ON nbo.id_norma_bo = cnbo.id_norma_bo
              LEFT JOIN categoria c ON cnbo.id_categoria = c.id_categoria
              $whereClause
              GROUP BY nbo.id_norma_bo
              ORDER BY nbo.fecha_publicacion DESC, nbo.id_norma_bo DESC
              LIMIT :limit OFFSET :offset";

    $stmt = $db->prepare($query);
    foreach ($params as $key => &$val) {
        $stmt->bindParam($key, $val);
    }
    $stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
    $stmt->bindParam(':offset', $offset, PDO::PARAM_INT);
    $stmt->execute();

    $registros = $stmt->fetchAll(PDO::FETCH_ASSOC);

    http_response_code(200);
    echo json_encode([
        "registros" => $registros,
        "total" => $total,
        "page" => $page,
        "limit" => $limit
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno del servidor.", "error" => $e->getMessage()]);
}
?>