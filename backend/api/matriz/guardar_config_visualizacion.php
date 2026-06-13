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

// Validar token
$token = '';
if (isset($_SERVER['HTTP_AUTHORIZATION'])) {
    $token = trim(str_ireplace('Bearer', '', $_SERVER['HTTP_AUTHORIZATION']));
}
$jwt = new JwtHandler();
$payload = $jwt->verificar($token);
if (!$payload) {
    http_response_code(401);
    echo json_encode(["mensaje" => "No autorizado."]);
    exit();
}

$data = json_decode(file_get_contents("php://input"));
if (empty($data->id_matriz)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Falta id_matriz."]);
    exit();
}

$id_matriz = (int)$data->id_matriz;
$mostrar_cumplimiento = isset($data->mostrar_cumplimiento) ? (int)$data->mostrar_cumplimiento : 1;
$campo_encabezado_item = isset($data->campo_encabezado_item) ? $data->campo_encabezado_item : 'normas';

$database = new Database();
$db = $database->getConnection();

try {
    $query = "UPDATE matriz SET mostrar_cumplimiento = :mostrar, campo_encabezado_item = :campo WHERE id_matriz = :id";
    $stmt = $db->prepare($query);
    $stmt->bindParam(':mostrar', $mostrar_cumplimiento, PDO::PARAM_INT);
    $stmt->bindParam(':campo', $campo_encabezado_item, PDO::PARAM_STR);
    $stmt->bindParam(':id', $id_matriz, PDO::PARAM_INT);
    $stmt->execute();

    http_response_code(200);
    echo json_encode(["mensaje" => "Configuración guardada correctamente."]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al guardar.", "error" => $e->getMessage()]);
}
?>