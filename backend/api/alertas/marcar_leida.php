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

$data = json_decode(file_get_contents("php://input"));
if (!isset($data->id_alerta) && !isset($data->todas)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Se requiere id_alerta o todas=true"]);
    exit();
}

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
    http_response_code(403);
    echo json_encode(["mensaje" => "Solo clientes pueden marcar alertas."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    if (isset($data->todas) && $data->todas === true) {
        $query = "UPDATE alerta SET leido = 1, fecha_lectura = NOW() WHERE id_cliente = :id_cliente AND leido = 0";
        $stmt = $db->prepare($query);
        $stmt->bindParam(':id_cliente', $id_cliente, PDO::PARAM_INT);
        $stmt->execute();
        echo json_encode(["mensaje" => "Todas las alertas marcadas como leídas."]);
    } else {
        $id_alerta = (int)$data->id_alerta;
        // Verificar que la alerta pertenezca al cliente
        $query_check = "SELECT id_alerta FROM alerta WHERE id_alerta = :id AND id_cliente = :id_cliente";
        $stmt_check = $db->prepare($query_check);
        $stmt_check->execute([':id' => $id_alerta, ':id_cliente' => $id_cliente]);
        if (!$stmt_check->fetch()) {
            http_response_code(403);
            echo json_encode(["mensaje" => "No tienes permiso para modificar esta alerta."]);
            exit();
        }
        $query = "UPDATE alerta SET leido = 1, fecha_lectura = NOW() WHERE id_alerta = :id";
        $stmt = $db->prepare($query);
        $stmt->bindParam(':id', $id_alerta, PDO::PARAM_INT);
        $stmt->execute();
        echo json_encode(["mensaje" => "Alerta marcada como leída."]);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al actualizar.", "error" => $e->getMessage()]);
}
?>