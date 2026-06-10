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
if (empty($data->id_item_matriz)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "ID de ítem requerido."]);
    exit();
}

$id_item_matriz = (int)$data->id_item_matriz;

$database = new Database();
$db = $database->getConnection();

try {
    // Verificar que la matriz asociada esté en estado borrador (id_estado_matriz = 1)
    $checkQuery = "SELECT m.id_estado_matriz 
                   FROM item_matriz im
                   JOIN matriz m ON im.id_matriz = m.id_matriz
                   WHERE im.id_item_matriz = :id_item";
    $checkStmt = $db->prepare($checkQuery);
    $checkStmt->execute([':id_item' => $id_item_matriz]);
    $estado = $checkStmt->fetchColumn();
    
    if ($estado !== false && $estado != 1) {
        http_response_code(403);
        echo json_encode(["mensaje" => "Solo se pueden eliminar ítems de matrices en estado 'Borrador'."]);
        exit();
    }
    
    $db->beginTransaction();
    // Eliminar el ítem (las relaciones en item_matriz_norma y doc_item_matriz se eliminan por CASCADE si configurado, sino manual)
    $stmt = $db->prepare("DELETE FROM item_matriz WHERE id_item_matriz = :id");
    $stmt->execute([':id' => $id_item_matriz]);
    $db->commit();
    http_response_code(200);
    echo json_encode(["mensaje" => "Ítem eliminado correctamente."]);
} catch (Exception $e) {
    $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al eliminar.", "error" => $e->getMessage()]);
}
?>