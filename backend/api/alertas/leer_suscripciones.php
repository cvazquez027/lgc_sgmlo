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

$database = new Database();
$db = $database->getConnection();

try {
    $query = "SELECT id_cliente FROM usuario_suscripcion_cliente WHERE id_usuario = :id_usuario";
    $stmt = $db->prepare($query);
    $stmt->execute([':id_usuario' => $id_usuario]);
    $suscripciones = $stmt->fetchAll(PDO::FETCH_COLUMN);

    http_response_code(200);
    echo json_encode(["suscripciones" => $suscripciones]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al leer suscripciones."]);
}
?>