<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once dirname(__FILE__) . '/../../config/Database.php';
include_once dirname(__FILE__) . '/../../config/JwtHandler.php';

$jwt = new JwtHandler();
$token = null;

$headers = getallheaders();
if (isset($headers['Authorization'])) {
    $token = trim(str_ireplace('Bearer', '', $headers['Authorization']));
} elseif (isset($_SERVER['HTTP_AUTHORIZATION'])) {
    $token = trim(str_ireplace('Bearer', '', $_SERVER['HTTP_AUTHORIZATION']));
}

if (!$token) {
    http_response_code(401);
    echo json_encode(["mensaje" => "Token no proporcionado."]);
    exit();
}

$payload = $jwt->verificar($token);
if (!$payload) {
    http_response_code(401);
    echo json_encode(["mensaje" => "Token inválido o expirado."]);
    exit();
}

$payload_array = (array) $payload;
$id_cliente = $payload_array['id_cliente'] ?? $payload_array['cliente_id'] ?? $payload_array['idCliente'] ?? null;
$id_usuario = $payload_array['id_usuario'] ?? null;

$database = new Database();
$db = $database->getConnection();

if ($id_cliente) {
    // Cliente normal
    $query = "SELECT COUNT(*) AS total FROM alerta WHERE id_cliente = :id_cliente AND leido = 0";
    $stmt = $db->prepare($query);
    $stmt->bindParam(':id_cliente', $id_cliente, PDO::PARAM_INT);
} else {
    // Administrador (LGC) - Cuenta las alertas de los clientes a los que está suscrito
    $query = "SELECT COUNT(*) AS total FROM alerta a 
              JOIN usuario_suscripcion_cliente s ON a.id_cliente = s.id_cliente 
              WHERE s.id_usuario = :id_usuario AND a.leido = 0";
    $stmt = $db->prepare($query);
    $stmt->bindParam(':id_usuario', $id_usuario, PDO::PARAM_INT);
}

$stmt->execute();
$row = $stmt->fetch(PDO::FETCH_ASSOC);

http_response_code(200);
echo json_encode(["total" => (int)$row['total']]);
?>