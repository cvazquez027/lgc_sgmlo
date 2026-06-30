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

// --- Extracción robusta del token (igual que en leer.php) ---
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

// Convertir payload a array para acceso uniforme
$payload_array = (array) $payload;
$id_cliente = isset($payload_array['id_cliente']) ? $payload_array['id_cliente'] : null;
$id_usuario = isset($payload_array['id_usuario']) ? $payload_array['id_usuario'] : null;
$rol = isset($payload_array['rol']) ? $payload_array['rol'] : null; // si existe en el token

// Determinar si es administrador (si no tiene id_cliente o si el rol lo indica)
$es_admin = ($id_cliente === null) || ($rol === 'admin' || $rol === 'administrador');

$data = json_decode(file_get_contents("php://input"));
if (!isset($data->id_alerta) && !isset($data->todas)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Se requiere id_alerta o todas=true"]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    if (isset($data->todas) && $data->todas === true) {
        if ($es_admin) {
            // Administrador: marcar todas las alertas (sin restricción de cliente)
            $query = "UPDATE alerta SET leido = 1, fecha_lectura = NOW() WHERE leido = 0";
            $stmt = $db->prepare($query);
        } else {
            // Cliente: solo sus alertas
            $query = "UPDATE alerta SET leido = 1, fecha_lectura = NOW() WHERE id_cliente = :id_cliente AND leido = 0";
            $stmt = $db->prepare($query);
            $stmt->bindParam(':id_cliente', $id_cliente, PDO::PARAM_INT);
        }
        $stmt->execute();
        echo json_encode(["mensaje" => "Todas las alertas marcadas como leídas."]);
    } else {
        $id_alerta = (int)$data->id_alerta;
        if ($es_admin) {
            // Administrador: puede marcar cualquier alerta
            $query = "UPDATE alerta SET leido = 1, fecha_lectura = NOW() WHERE id_alerta = :id";
            $stmt = $db->prepare($query);
            $stmt->bindParam(':id', $id_alerta, PDO::PARAM_INT);
        } else {
            // Cliente: verificar propiedad
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
        }
        $stmt->execute();
        echo json_encode(["mensaje" => "Alerta marcada como leída."]);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al actualizar.", "error" => $e->getMessage()]);
}
?>