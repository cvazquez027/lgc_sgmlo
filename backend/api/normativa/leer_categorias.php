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

// Ciberseguridad: Validamos que el ID de la norma venga en la URL y sea válido
$id_norma = isset($_GET['id_norma']) ? filter_var($_GET['id_norma'], FILTER_VALIDATE_INT) : false;

if (!$id_norma) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Se requiere un ID de norma válido."]);
    exit();
}

try {
    $database = new Database();
    $db = $database->getConnection();

    // Cruzamos la tabla puente con la maestra de categorías
    $query = "SELECT c.id_categoria, c.descripcion 
              FROM categoria c
              INNER JOIN categoria_norma cn ON c.id_categoria = cn.id_categoria
              WHERE cn.id_norma = :id_norma
              ORDER BY c.descripcion ASC";
              
    $stmt = $db->prepare($query);
    $stmt->bindParam(":id_norma", $id_norma, PDO::PARAM_INT);
    $stmt->execute();
    
    $registros = $stmt->fetchAll(PDO::FETCH_ASSOC);

    http_response_code(200);
    echo json_encode([
        "mensaje" => "Categorías recuperadas exitosamente.",
        "registros" => $registros
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno del servidor.", "error" => $e->getMessage()]);
}
?>