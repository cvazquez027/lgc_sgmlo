<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Ajusta la ruta según tu estructura
include_once dirname(__FILE__) . '/../../config/Database.php';
include_once dirname(__FILE__) . '/../../config/JwtHandler.php';

$jwt = new JwtHandler();
$token = null;

// Extraer token del header Authorization
$headers = getallheaders();
if (isset($headers['Authorization'])) {
    $token = trim(str_ireplace('Bearer', '', $headers['Authorization']));
} elseif (isset($_SERVER['HTTP_AUTHORIZATION'])) {
    $token = trim(str_ireplace('Bearer', '', $_SERVER['HTTP_AUTHORIZATION']));
}

if (!$jwt->verificar($token)) {
    http_response_code(401);
    echo json_encode(["mensaje" => "Token inválido o no autorizado."]);
    exit();
}

$payload = $jwt->verificar($token);
$id_cliente = $payload->id_cliente ?? null;

if (!$id_cliente) {
    echo json_encode(["count" => 0]);
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
echo json_encode(["count" => (int)$row['total']]);
?>