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

// Extraer token
$token = '';
if (isset($_SERVER['HTTP_AUTHORIZATION'])) {
    $token = trim(str_ireplace('Bearer', '', $_SERVER['HTTP_AUTHORIZATION']));
} elseif (function_exists('apache_request_headers')) {
    $requestHeaders = apache_request_headers();
    $requestHeaders = array_combine(array_map('ucwords', array_keys($requestHeaders)), array_values($requestHeaders));
    if (isset($requestHeaders['Authorization'])) {
        $token = trim(str_ireplace('Bearer', '', $requestHeaders['Authorization']));
    }
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
    echo json_encode(["mensaje" => "No autorizado. Token inválido o expirado."]);
    exit();
}

// Convertir payload a array si es objeto
$payload_array = (array) $payload;
$id_cliente = isset($payload_array['id_cliente']) ? $payload_array['id_cliente'] : null;
$id_usuario = isset($payload_array['id_usuario']) ? $payload_array['id_usuario'] : null;

// Si aún no se obtuvo id_cliente, intentar como propiedad del objeto (por si acaso)
if ($id_cliente === null && property_exists($payload, 'id_cliente')) {
    $id_cliente = $payload->id_cliente;
}
if ($id_usuario === null && property_exists($payload, 'id_usuario')) {
    $id_usuario = $payload->id_usuario;
}

// Log en archivo de errores de PHP (útil para debugging)
error_log("=== [ALERTAS] id_cliente desde payload: " . ($id_cliente ?? 'null'));
error_log("=== [ALERTAS] id_usuario desde payload: " . ($id_usuario ?? 'null'));

if (!$id_cliente) {
    // No lanzamos error, devolvemos vacío con debug
    echo json_encode([
        "alertas" => [],
        "debug_id_cliente" => null,
        "debug_payload" => $payload_array,
        "mensaje" => "No se encontró id_cliente en el token"
    ]);
    exit();
}

$incluir_leidas = isset($_GET['incluir_leidas']) && filter_var($_GET['incluir_leidas'], FILTER_VALIDATE_BOOLEAN);

$database = new Database();
$db = $database->getConnection();

$query = "SELECT * FROM alerta WHERE id_cliente = :id_cliente";
if (!$incluir_leidas) {
    $query .= " AND leido = 0";
}
$query .= " ORDER BY fecha_creacion DESC";

$stmt = $db->prepare($query);
$stmt->bindParam(':id_cliente', $id_cliente, PDO::PARAM_INT);
$stmt->execute();

$alertas = $stmt->fetchAll(PDO::FETCH_ASSOC);

http_response_code(200);
echo json_encode([
    "alertas" => $alertas,
    "debug_id_cliente" => $id_cliente,
    "debug_total" => count($alertas)
]);
?>