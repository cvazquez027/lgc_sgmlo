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
    echo json_encode(["mensaje" => "Solo administradores pueden editar alertas."]);
    exit();
}

$data = json_decode(file_get_contents("php://input"));
if (empty($data->id_alerta) || empty($data->titulo) || empty($data->mensaje)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan datos: id_alerta, titulo, mensaje."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    $query = "UPDATE alerta SET titulo = :titulo, mensaje = :mensaje WHERE id_alerta = :id";
    $stmt = $db->prepare($query);
    $stmt->execute([
        ':id' => (int)$data->id_alerta,
        ':titulo' => $data->titulo,
        ':mensaje' => $data->mensaje
    ]);

    http_response_code(200);
    echo json_encode(["mensaje" => "Alerta actualizada correctamente."]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al actualizar.", "error" => $e->getMessage()]);
}
?>