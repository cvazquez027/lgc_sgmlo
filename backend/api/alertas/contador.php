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

// Extraer token
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

// Intentar obtener id_cliente desde el payload (puede ser objeto o array)
if (is_object($payload)) {
    $id_cliente = $payload->id_cliente ?? null;
} elseif (is_array($payload)) {
    $id_cliente = $payload['id_cliente'] ?? null;
} else {
    $id_cliente = null;
}

// Si aún es null, intentar con 'cliente_id' o 'idCliente' (por si acaso)
if ($id_cliente === null && is_object($payload)) {
    $id_cliente = $payload->cliente_id ?? $payload->idCliente ?? null;
} elseif ($id_cliente === null && is_array($payload)) {
    $id_cliente = $payload['cliente_id'] ?? $payload['idCliente'] ?? null;
}

if (!$id_cliente) {
    // No hay cliente asociado al usuario (ej. superadmin)
    echo json_encode(["total" => 0]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

$query = "SELECT COUNT(*) AS total FROM alerta WHERE id_cliente = :id_cliente AND leido = 0";
$stmt = $db->prepare($query);
$stmt->bindParam(':id_cliente', $id_cliente, PDO::PARAM_INT);
$stmt->execute();
$row = $stmt->fetch(PDO::FETCH_ASSOC);

http_response_code(200);
echo json_encode(["total" => (int)$row['total']]);
?>