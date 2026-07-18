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
include_once '../../config/JwtHandler.php';

// Validar token y permisos (solo admin)
$token = '';
if (isset($_SERVER['HTTP_AUTHORIZATION'])) {
    $token = trim(str_ireplace('Bearer', '', $_SERVER['HTTP_AUTHORIZATION']));
}
$jwt = new JwtHandler();
$payload = $jwt->verificar($token);
if (!$payload) {
    http_response_code(401);
    echo json_encode(["mensaje" => "No autorizado."]);
    exit();
}
$payload_array = (array) $payload;
$id_cliente = isset($payload_array['id_cliente']) ? $payload_array['id_cliente'] : null;
if ($id_cliente) {
    http_response_code(403);
    echo json_encode(["mensaje" => "Acceso denegado."]);
    exit();
}

$data = json_decode(file_get_contents("php://input"));
if (empty($data->ordenes) || !is_array($data->ordenes)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Se requiere un array de órdenes."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    $db->beginTransaction();
    $query = "UPDATE control_proyecto SET orden = :orden WHERE id = :id";
    $stmt = $db->prepare($query);
    foreach ($data->ordenes as $item) {
        $id = (int)$item->id;
        $orden = (int)$item->orden;
        $stmt->bindParam(':orden', $orden, PDO::PARAM_INT);
        $stmt->bindParam(':id', $id, PDO::PARAM_INT);
        $stmt->execute();
    }
    $db->commit();
    http_response_code(200);
    echo json_encode(["mensaje" => "Orden actualizado."]);
} catch (Exception $e) {
    $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al reordenar.", "error" => $e->getMessage()]);
}
?>