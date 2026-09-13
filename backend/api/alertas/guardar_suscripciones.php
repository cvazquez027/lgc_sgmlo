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

$token = '';
if (isset($_SERVER['HTTP_AUTHORIZATION'])) {
    $token = trim(str_ireplace('Bearer', '', $_SERVER['HTTP_AUTHORIZATION']));
} else {
    $headers = getallheaders();
    if (isset($headers['Authorization'])) {
        $token = trim(str_ireplace('Bearer', '', $headers['Authorization']));
    }
}

$jwt = new JwtHandler();
$payload = $jwt->verificar($token);
if (!$payload) {
    http_response_code(401);
    echo json_encode(["mensaje" => "No autorizado."]);
    exit();
}

$payload_array = (array) $payload;
$id_usuario = isset($payload_array['id_usuario']) ? $payload_array['id_usuario'] : null;

$data = json_decode(file_get_contents("php://input"));
if (!isset($data->suscripciones) || !is_array($data->suscripciones)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Se requiere un array de suscripciones."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    $db->beginTransaction();

    // Eliminar las suscripciones actuales
    $query_del = "DELETE FROM usuario_suscripcion_cliente WHERE id_usuario = :id_usuario";
    $stmt_del = $db->prepare($query_del);
    $stmt_del->execute([':id_usuario' => $id_usuario]);

    // Insertar las nuevas
    if (!empty($data->suscripciones)) {
        $query_ins = "INSERT INTO usuario_suscripcion_cliente (id_usuario, id_cliente) VALUES (:id_usuario, :id_cliente)";
        $stmt_ins = $db->prepare($query_ins);
        foreach ($data->suscripciones as $id_cliente) {
            $stmt_ins->execute([':id_usuario' => $id_usuario, ':id_cliente' => $id_cliente]);
        }
    }

    $db->commit();
    http_response_code(200);
    echo json_encode(["mensaje" => "Suscripciones actualizadas correctamente."]);
} catch (Exception $e) {
    $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al guardar suscripciones.", "error" => $e->getMessage()]);
}
?>