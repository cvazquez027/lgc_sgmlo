<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

require_once __DIR__ . '/../../config/Database.php';

$token = null;
if (isset($_SERVER['HTTP_AUTHORIZATION'])) {
    $token = trim($_SERVER['HTTP_AUTHORIZATION']);
} elseif (isset($_SERVER['REDIRECT_HTTP_AUTHORIZATION'])) {
    $token = trim($_SERVER['REDIRECT_HTTP_AUTHORIZATION']);
} elseif (function_exists('apache_request_headers')) {
    $requestHeaders = apache_request_headers();
    if (isset($requestHeaders['Authorization'])) {
        $token = trim($requestHeaders['Authorization']);
    }
}

if ($token) {
    $token = str_replace('Bearer ', '', $token);
} else {
    http_response_code(401);
    echo json_encode(["status" => "error", "message" => "No hay token de acceso."]);
    exit();
}

try {
    $tokenParts = explode('.', $token);
    if(count($tokenParts) < 2) { throw new Exception("Token mal formado."); }

    $payload = json_decode(base64_decode($tokenParts[1]), true);
    $id_usuario = $payload['id_usuario'] ?? $payload['id'] ?? $payload['sub'] ?? null;

    if (!$id_usuario) {
        throw new Exception("ID de usuario no encontrado en el token.");
    }

    $database = new Database();
    $db = $database->getConnection();

    // AQUÍ ESTABA EL ERROR: Cambiado 'usuarios' por 'usuario'
    $query = "SELECT nombre, apellido, email FROM usuario WHERE id_usuario = :id LIMIT 1";
    $stmt = $db->prepare($query);
    $stmt->bindParam(':id', $id_usuario);
    $stmt->execute();

    if ($stmt->rowCount() > 0) {
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        echo json_encode(["status" => "success", "data" => $row]);
    } else {
        echo json_encode(["status" => "error", "message" => "Usuario no encontrado en la base de datos."]);
    }

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["status" => "error", "message" => $e->getMessage()]);
}
?>