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
if ($id_cliente) {
    http_response_code(403);
    echo json_encode(["mensaje" => "Acceso denegado. Solo administradores pueden modificar el tablero de control."]);
    exit();
}

$data = json_decode(file_get_contents("php://input"));

$id = isset($data->id) ? (int)$data->id : null;
$descripcion = isset($data->descripcion) ? trim($data->descripcion) : '';
$detalle = isset($data->detalle) ? trim($data->detalle) : null;
$estado = isset($data->estado) ? $data->estado : 'pendiente';
$porcentaje_avance = isset($data->porcentaje_avance) ? (float)$data->porcentaje_avance : null;
$orden = isset($data->orden) ? (int)$data->orden : 0;
$categoria = isset($data->categoria) ? $data->categoria : null;

if (empty($descripcion)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "La descripción es obligatoria."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    if ($id) {
        $query = "UPDATE control_proyecto 
                  SET descripcion = :desc, detalle = :det, estado = :est, 
                      porcentaje_avance = :pct, orden = :ord, categoria = :cat
                  WHERE id = :id AND vigente = 1";
        $stmt = $db->prepare($query);
        $stmt->bindParam(':desc', $descripcion);
        $stmt->bindParam(':det', $detalle);
        $stmt->bindParam(':est', $estado);
        $stmt->bindParam(':pct', $porcentaje_avance);
        $stmt->bindParam(':ord', $orden);
        $stmt->bindParam(':cat', $categoria);
        $stmt->bindParam(':id', $id, PDO::PARAM_INT);
        $stmt->execute();
        $mensaje = "Registro actualizado.";
    } else {
        $query = "INSERT INTO control_proyecto (descripcion, detalle, estado, porcentaje_avance, orden, categoria) 
                  VALUES (:desc, :det, :est, :pct, :ord, :cat)";
        $stmt = $db->prepare($query);
        $stmt->bindParam(':desc', $descripcion);
        $stmt->bindParam(':det', $detalle);
        $stmt->bindParam(':est', $estado);
        $stmt->bindParam(':pct', $porcentaje_avance);
        $stmt->bindParam(':ord', $orden);
        $stmt->bindParam(':cat', $categoria);
        $stmt->execute();
        $id = $db->lastInsertId();
        $mensaje = "Registro creado.";
    }

    http_response_code(200);
    echo json_encode(["mensaje" => $mensaje, "id" => $id]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al guardar.", "error" => $e->getMessage()]);
}
?>