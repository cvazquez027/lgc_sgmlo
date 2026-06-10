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

$jwt = new JwtHandler();
$token = null;
if (isset($_SERVER['HTTP_AUTHORIZATION'])) {
    $token = trim(str_ireplace('Bearer', '', $_SERVER['HTTP_AUTHORIZATION']));
}
if (!$jwt->verificar($token)) {
    http_response_code(401);
    echo json_encode(["mensaje" => "No autorizado."]);
    exit();
}

$payload = $jwt->obtenerPayload($token);
$id_cliente = $payload->id_cliente ?? null;
if (!$id_cliente) {
    echo json_encode(["alertas" => []]);
    exit();
}

// Parámetros: incluir leídas (opcional)
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
echo json_encode(["alertas" => $alertas]);
?>