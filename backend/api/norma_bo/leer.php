<?php
// Cabeceras estrictas CORS
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once dirname(__FILE__) . '/../../config/Database.php';

// 1. SEGURIDAD: Casteo estricto de variables de paginación
// Si un atacante intenta inyectar texto en 'page' o 'limit', PHP lo convierte a 0 o al valor por defecto.
$page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
$limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 15; // 15 registros por página por defecto
$offset = ($page - 1) * $limit;

// Parámetros de búsqueda opcionales
$search_texto = isset($_GET['q']) ? htmlspecialchars(strip_tags($_GET['q'])) : '';
$filtro_tipo = isset($_GET['id_tipo_norma']) ? (int)$_GET['id_tipo_norma'] : 0;
$filtro_estado = isset($_GET['id_estado_norma']) ? (int)$_GET['id_estado_norma'] : 0;

$database = new Database();
$db = $database->getConnection();

try {
    // 2. CONSTRUCCIÓN DINÁMICA DE LA QUERY SEGURA
    $where_clauses = ["1=1"]; // Base para concatenar ANDs fácilmente
    $params = [];

    // Búsqueda por texto (Aplica a número, año o síntesis)
    if (!empty($search_texto)) {
        $where_clauses[] = "(nb.numero LIKE :search OR nb.anio LIKE :search OR nb.sintesis LIKE :search)";
        $params[':search'] = "%{$search_texto}%";
    }

    // Filtros exactos
    if ($filtro_tipo > 0) {
        $where_clauses[] = "nb.id_tipo_norma = :id_tipo";
        $params[':id_tipo'] = $filtro_tipo;
    }
    if ($filtro_estado > 0) {
        $where_clauses[] = "nb.id_estado_norma = :id_estado";
        $params[':id_estado'] = $filtro_estado;
    }

    $where_sql = implode(" AND ", $where_clauses);

    // 3. CONSULTA PARA EL TOTAL DE REGISTROS (Necesario para que el frontend arme el paginador)
    $query_count = "SELECT COUNT(nb.id_norma_bo) as total FROM norma_bo nb WHERE " . $where_sql;
    $stmt_count = $db->prepare($query_count);
    
    foreach ($params as $key => &$val) {
        $stmt_count->bindParam($key, $val);
    }
    $stmt_count->execute();
    $total_rows = $stmt_count->fetch(PDO::FETCH_ASSOC)['total'];

    // 4. CONSULTA PRINCIPAL OPTIMIZADA CON GROUP_CONCAT
    // Evitamos el problema de "N+1 queries" trayendo todas las categorías asociadas en una sola celda separada por comas.
    $query = "SELECT 
                nb.id_norma_bo, 
                nb.anio, 
                nb.numero, 
                nb.sintesis, 
                nb.url_norma,
                tn.descripcion as tipo_norma, 
                tn.id_tipo_norma,
                en.descripcion as emisor_norma, 
                en.id_emisor_norma,
                es.descripcion as estado_norma, 
                es.id_estado_norma,
                GROUP_CONCAT(c.id_categoria SEPARATOR ',') as categorias_ids,
                GROUP_CONCAT(c.descripcion SEPARATOR '||') as categorias_nombres
              FROM norma_bo nb
              LEFT JOIN tipo_norma tn ON nb.id_tipo_norma = tn.id_tipo_norma
              LEFT JOIN emisor_norma en ON nb.id_emisor_norma = en.id_emisor_norma
              LEFT JOIN estado_norma es ON nb.id_estado_norma = es.id_estado_norma
              LEFT JOIN categoria_norma_bo cnb ON nb.id_norma_bo = cnb.id_norma_bo
              LEFT JOIN categoria c ON cnb.id_categoria = c.id_categoria
              WHERE " . $where_sql . "
              GROUP BY nb.id_norma_bo
              ORDER BY nb.id_norma_bo DESC
              LIMIT :limit OFFSET :offset";

    $stmt = $db->prepare($query);

    // Bindeamos los parámetros de búsqueda dinámicos
    foreach ($params as $key => &$val) {
        $stmt->bindParam($key, $val);
    }
    
    // Bindeamos explícitamente los parámetros de paginación como enteros (Protección SQLi)
    $stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
    $stmt->bindParam(':offset', $offset, PDO::PARAM_INT);
    
    $stmt->execute();
    
    $registros = [];
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        // Formateamos las categorías para que el frontend reciba un array limpio y no un string pegado
        $categorias_array = [];
        if (!empty($row['categorias_ids'])) {
            $ids = explode(',', $row['categorias_ids']);
            $nombres = explode('||', $row['categorias_nombres']);
            
            for ($i = 0; $i < count($ids); $i++) {
                $categorias_array[] = [
                    "id_categoria" => (int)$ids[$i],
                    "descripcion" => $nombres[$i]
                ];
            }
        }

        $registros[] = [
            "id_norma_bo" => (int)$row['id_norma_bo'],
            "norma" => $row['tipo_norma'] . " " . $row['numero'] . "/" . $row['anio'], // Campo virtual amigable
            "anio" => $row['anio'],
            "numero" => $row['numero'],
            "sintesis" => $row['sintesis'],
            "url_norma" => $row['url_norma'],
            "tipo_norma" => ["id" => $row['id_tipo_norma'], "descripcion" => $row['tipo_norma']],
            "emisor_norma" => ["id" => $row['id_emisor_norma'], "descripcion" => $row['emisor_norma']],
            "estado_norma" => ["id" => $row['id_estado_norma'], "descripcion" => $row['estado_norma']],
            "categorias" => $categorias_array
        ];
    }

    // 5. RESPUESTA JSON ESTRUCTURADA
    http_response_code(200);
    echo json_encode([
        "metadatos" => [
            "total_registros" => (int)$total_rows,
            "total_paginas" => ceil($total_rows / $limit),
            "pagina_actual" => $page,
            "limite" => $limit
        ],
        "registros" => $registros
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno en el motor de base de datos."]);
}
?>