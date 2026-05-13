<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);

header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

require_once __DIR__ . '/../../config/Database.php';

$token = null;
if (isset($_SERVER['HTTP_AUTHORIZATION'])) $token = trim($_SERVER['HTTP_AUTHORIZATION']);
elseif (isset($_SERVER['REDIRECT_HTTP_AUTHORIZATION'])) $token = trim($_SERVER['REDIRECT_HTTP_AUTHORIZATION']);
elseif (function_exists('apache_request_headers')) {
    $req = apache_request_headers();
    if (isset($req['Authorization'])) $token = trim($req['Authorization']);
}

if (!$token) {
    echo json_encode(["status" => "error", "message" => "Acceso denegado."]);
    exit();
}

$token = str_replace('Bearer ', '', $token);
$tokenParts = explode('.', $token);
$payload = json_decode(base64_decode($tokenParts[1]), true);
$id_usuario = $payload['id_usuario'] ?? $payload['id'] ?? $payload['sub'] ?? null;

if (!$id_usuario) {
    echo json_encode(["status" => "error", "message" => "Token inválido."]);
    exit();
}

$data = json_decode(file_get_contents("php://input"));

if(empty($data->nombre) || empty($data->email)) {
    echo json_encode(["status" => "error", "message" => "El nombre y el correo son obligatorios."]);
    exit();
}

try {
    $database = new Database();
    $db = $database->getConnection();

    // AQUÍ ESTABA EL ERROR: Cambiado 'usuarios' por 'usuario'
    if (!empty($data->password)) {
        $password_hash = password_hash($data->password, PASSWORD_DEFAULT);
        $query = "UPDATE usuario 
                  SET nombre = :nombre, 
                      apellido = :apellido, 
                      email = :email, 
                      password_hash = :password,
                      fecha_modificacion = NOW()
                  WHERE id_usuario = :id";
        $stmt = $db->prepare($query);
        $stmt->bindParam(':password', $password_hash);
    } else {
        $query = "UPDATE usuario 
                  SET nombre = :nombre, 
                      apellido = :apellido, 
                      email = :email,
                      fecha_modificacion = NOW()
                  WHERE id_usuario = :id";
        $stmt = $db->prepare($query);
    }

    $stmt->bindParam(':nombre', $data->nombre);
    $apellido = isset($data->apellido) ? $data->apellido : "";
    $stmt->bindParam(':apellido', $apellido);
    $stmt->bindParam(':email', $data->email);
    $stmt->bindParam(':id', $id_usuario);

    if ($stmt->execute()) {
        echo json_encode(["status" => "success", "message" => "Perfil actualizado."]);
    } else {
        echo json_encode(["status" => "error", "message" => "No se pudo actualizar."]);
    }

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["status" => "error", "message" => "Error BD: " . $e->getMessage()]);
}
?>