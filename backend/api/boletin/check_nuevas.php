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

$database = new Database();
$db = $database->getConnection();

try {
    // LÓGICA DE NEGOCIO: ¿Existe alguna norma en el "buffer" (norma_bo) que esté categorizada?
    // Usamos EXISTS porque es la instrucción SQL más rápida y segura para preguntas de "Sí/No".
    $query = "SELECT EXISTS (
                SELECT 1 
                FROM norma_bo nbo 
                INNER JOIN categoria_norma_bo cnbo ON nbo.id_norma_bo = cnbo.id_norma_bo
              ) as hay_nuevas";
              
    $stmt = $db->prepare($query);
    $stmt->execute();
    
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    $hay_nuevas = (bool)$row['hay_nuevas'];

    http_response_code(200);
    echo json_encode([
        "hay_nuevas" => $hay_nuevas,
        "mensaje" => $hay_nuevas ? "Hay normativas categorizadas de interés pendientes de revisión." : "Al día."
    ]);

} catch (Exception $e) {
    // Manejo de errores sin exponer la estructura de la DB
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno del servidor.", "error" => $e->getMessage()]);
}
?>