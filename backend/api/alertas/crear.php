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
    echo json_encode(["mensaje" => "No autorizado."]);
    exit();
}

$payload_array = (array) $payload;
$id_cliente = isset($payload_array['id_cliente']) ? $payload_array['id_cliente'] : null;
$rol = isset($payload_array['rol']) ? $payload_array['rol'] : null;
$es_admin = ($id_cliente === null) || ($rol === 'admin' || $rol === 'administrador');

if (!$es_admin) {
    http_response_code(403);
    echo json_encode(["mensaje" => "Solo administradores pueden crear alertas."]);
    exit();
}

$data = json_decode(file_get_contents("php://input"));
if (empty($data->id_cliente) || empty($data->tipo) || empty($data->titulo) || empty($data->mensaje)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan datos obligatorios: id_cliente, tipo, titulo, mensaje."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    $query = "INSERT INTO alerta (id_cliente, id_matriz, id_item_matriz, tipo, titulo, mensaje, url, fecha_creacion, leido)
              VALUES (:id_cliente, :id_matriz, :id_item, :tipo, :titulo, :mensaje, :url, NOW(), 0)";
    $stmt = $db->prepare($query);
    $stmt->execute([
        ':id_cliente' => (int)$data->id_cliente,
        ':id_matriz' => !empty($data->id_matriz) ? (int)$data->id_matriz : null,
        ':id_item' => !empty($data->id_item_matriz) ? (int)$data->id_item_matriz : null,
        ':tipo' => $data->tipo,
        ':titulo' => $data->titulo,
        ':mensaje' => $data->mensaje,
        ':url' => !empty($data->url) ? $data->url : null
    ]);

    $id_alerta = $db->lastInsertId();

    http_response_code(200);
    echo json_encode(["mensaje" => "Alerta creada correctamente.", "id_alerta" => $id_alerta]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al crear alerta.", "error" => $e->getMessage()]);
}
?>