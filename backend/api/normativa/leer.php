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

$database = new Database();
$db = $database->getConnection();

try {
    $query = "SELECT n.*, 
                     tn.descripcion AS tipo_norma_desc,
                     en.descripcion AS emisor_desc,
                     j.descripcion AS jurisdiccion_desc,
                     nj.descripcion AS nivel_jurisdiccion_desc,
                     est.descripcion AS estado_desc
              FROM norma n
              LEFT JOIN tipo_norma tn ON n.id_tipo_norma = tn.id_tipo_norma
              LEFT JOIN emisor_norma en ON n.id_emisor_norma = en.id_emisor_norma
              LEFT JOIN jurisdiccion j ON en.id_jurisdiccion = j.id_jurisdiccion
              LEFT JOIN nivel_jurisdiccion nj ON j.id_nivel_jurisdiccion = nj.id_nivel_jurisdiccion
              LEFT JOIN estado_norma est ON n.id_estado_norma = est.id_estado_norma
              ORDER BY n.anio DESC, n.numero ASC";
    
    $stmt = $db->prepare($query);
    $stmt->execute();
    
    $normas = [];
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        // Obtener categorías asociadas (si existen)
        $queryCats = "SELECT c.descripcion 
                      FROM categoria_norma nc
                      JOIN categoria c ON nc.id_categoria = c.id_categoria
                      WHERE nc.id_norma = ?";
        $stmtCats = $db->prepare($queryCats);
        $stmtCats->execute([$row['id_norma']]);
        $categorias = $stmtCats->fetchAll(PDO::FETCH_COLUMN);
        
        $row['categorias'] = $categorias;
        $normas[] = $row;
    }
    
    http_response_code(200);
    echo json_encode(["registros" => $normas]);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al leer normativa.", "debug" => $e->getMessage()]);
}
?>