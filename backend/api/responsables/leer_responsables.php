<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }

include_once '../../config/Database.php';

$id_establecimiento = isset($_GET['id_establecimiento']) ? filter_var($_GET['id_establecimiento'], FILTER_VALIDATE_INT) : false;

if (!$id_establecimiento) {
    http_response_code(400);
    echo json_encode(["mensaje" => "ID de establecimiento requerido."]);
    exit();
}

try {
    $database = new Database();
    $db = $database->getConnection();

    $query = "SELECT id_responsable_establecimiento, descripcion, observacion, vigente 
              FROM responsable_establecimiento 
              WHERE id_establecimiento = :id_est 
              ORDER BY orden ASC";
              
    $stmt = $db->prepare($query);
    $stmt->execute([':id_est' => $id_establecimiento]);
    
    echo json_encode([
        "mensaje" => "Responsables recuperados.",
        "registros" => $stmt->fetchAll(PDO::FETCH_ASSOC)
    ]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al consultar responsables.", "error" => $e->getMessage()]);
}
?>