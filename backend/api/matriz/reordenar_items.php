<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }
include_once '../../config/Database.php';

$data = json_decode(file_get_contents("php://input")); // Espera array: [{id_item: 1, orden: 0}, ...]

$database = new Database(); $db = $database->getConnection();
try {
    $db->beginTransaction();
    $stmt = $db->prepare("UPDATE item_matriz SET orden = :orden WHERE id_item_matriz = :id");
    foreach ($data as $item) {
        $stmt->execute([':orden' => $item->orden, ':id' => $item->id_item]);
    }
    $db->commit();
    http_response_code(200); echo json_encode(["mensaje" => "Reordenado exitosamente."]);
} catch (Exception $e) {
    $db->rollBack(); http_response_code(500); echo json_encode(["error" => $e->getMessage()]);
}
?>