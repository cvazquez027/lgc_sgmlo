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

try {
    $database = new Database();
    $db = $database->getConnection();

    // Consulta optimizada con JOINs para traer la información legible
    $query = "SELECT 
                n.id_norma, n.numero, n.anio, n.fecha_publicacion, 
                n.sintesis, n.url_norma, n.origen_carga,
                n.id_tipo_norma, tn.descripcion as tipo_norma_desc,
                n.id_emisor_norma, en.descripcion as emisor_desc,
                n.id_estado_norma, esn.descripcion as estado_desc
              FROM norma n
              LEFT JOIN tipo_norma tn ON n.id_tipo_norma = tn.id_tipo_norma
              LEFT JOIN emisor_norma en ON n.id_emisor_norma = en.id_emisor_norma
              LEFT JOIN estado_norma esn ON n.id_estado_norma = esn.id_estado_norma
              ORDER BY n.anio DESC, n.numero DESC";
              
    $stmt = $db->prepare($query);
    $stmt->execute();
    
    $registros = $stmt->fetchAll(PDO::FETCH_ASSOC);

    http_response_code(200);
    echo json_encode([
        "mensaje" => "Normativas recuperadas exitosamente.",
        "registros" => $registros
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno del servidor.", "error" => $e->getMessage()]);
}
?>