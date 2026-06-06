<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';

$data = json_decode(file_get_contents("php://input"));
if (empty($data->id_matriz)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "ID de matriz requerido."]);
    exit();
}

$id_matriz = (int)$data->id_matriz;

$database = new Database();
$db = $database->getConnection();

try {
    // Verificar que la matriz existe y está en estado borrador (1)
    $checkQuery = "SELECT id_estado_matriz FROM matriz WHERE id_matriz = :id";
    $stmtCheck = $db->prepare($checkQuery);
    $stmtCheck->execute([':id' => $id_matriz]);
    $matriz = $stmtCheck->fetch(PDO::FETCH_ASSOC);
    
    if (!$matriz) {
        http_response_code(404);
        echo json_encode(["mensaje" => "Matriz no encontrada."]);
        exit();
    }
    
    if ($matriz['id_estado_matriz'] != 1) {
        http_response_code(403);
        echo json_encode(["mensaje" => "Solo se pueden eliminar matrices en estado 'Borrador'."]);
        exit();
    }
    
    // Eliminar la matriz (los items se eliminarán en cascada por FK)
    $deleteQuery = "DELETE FROM matriz WHERE id_matriz = :id";
    $stmtDelete = $db->prepare($deleteQuery);
    $stmtDelete->execute([':id' => $id_matriz]);
    
    http_response_code(200);
    echo json_encode(["mensaje" => "Matriz eliminada correctamente."]);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al eliminar.", "error" => $e->getMessage()]);
}
?>