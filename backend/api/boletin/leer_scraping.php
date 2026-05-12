<?php
// Cabeceras de seguridad y CORS
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';

// Ahora id_jurisdiccion es opcional
$id_jurisdiccion = isset($_GET['id_jurisdiccion']) && $_GET['id_jurisdiccion'] !== '' ? filter_var($_GET['id_jurisdiccion'], FILTER_VALIDATE_INT) : null;

$database = new Database();
$db = $database->getConnection();

try {
    $whereClause = "";
    $params = [];

    if ($id_jurisdiccion) {
        $whereClause = "WHERE en.id_jurisdiccion = :id_jur";
        $params[':id_jur'] = $id_jurisdiccion;
    }

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
              ORDER BY nbo.fecha_publicacion DESC, nbo.id_norma_bo DESC";
              
    $stmt = $db->prepare($query);
    $stmt->execute($params);
    
    $registros = $stmt->fetchAll(PDO::FETCH_ASSOC);

    http_response_code(200);
    echo json_encode(["registros" => $registros]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno del servidor.", "error" => $e->getMessage()]);
}
?>