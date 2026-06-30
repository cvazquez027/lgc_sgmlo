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

// ---------------------------------------------------------
// EXTRACCIÓN ROBUSTA DEL TOKEN (igual que en leer.php)
// ---------------------------------------------------------
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
    echo json_encode(["mensaje" => "No autorizado. Token inválido, expirado o ausente."]);
    exit();
}

// ---------------------------------------------------------
// PROCESAR DATOS
// ---------------------------------------------------------
$data = json_decode(file_get_contents("php://input"));
if (empty($data->id_matriz)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Falta id_matriz."]);
    exit();
}

$id_matriz = (int)$data->id_matriz;
$mostrar_cumplimiento = isset($data->mostrar_cumplimiento) ? (int)$data->mostrar_cumplimiento : 1;
$campo_encabezado_item = isset($data->campo_encabezado_item) ? $data->campo_encabezado_item : 'normas';

// --- PROCESAR columnas_editables_publicada: convertir a JSON correctamente ---
$columnas_editables = $data->columnas_editables_publicada ?? null;
if (is_array($columnas_editables)) {
    $columnas_editables_json = json_encode($columnas_editables);
} elseif (is_object($columnas_editables)) {
    // Si es un objeto (stdClass), lo convertimos a array y luego a JSON
    $columnas_editables_json = json_encode((array) $columnas_editables);
} elseif (is_string($columnas_editables)) {
    // Si ya es string, validamos que sea JSON válido
    $decoded = json_decode($columnas_editables, true);
    if (json_last_error() === JSON_ERROR_NONE && is_array($decoded)) {
        $columnas_editables_json = $columnas_editables; // ya es JSON válido
    } else {
        $columnas_editables_json = '[]';
    }
} else {
    $columnas_editables_json = '[]';
}

$database = new Database();
$db = $database->getConnection();

try {
    $query = "UPDATE matriz SET 
                mostrar_cumplimiento = :mostrar, 
                campo_encabezado_item = :campo, 
                columnas_editables_publicada = :columnas_editables 
              WHERE id_matriz = :id";
    $stmt = $db->prepare($query);
    $stmt->bindParam(':mostrar', $mostrar_cumplimiento, PDO::PARAM_INT);
    $stmt->bindParam(':campo', $campo_encabezado_item, PDO::PARAM_STR);
    $stmt->bindParam(':columnas_editables', $columnas_editables_json, PDO::PARAM_STR);
    $stmt->bindParam(':id', $id_matriz, PDO::PARAM_INT);
    $stmt->execute();

    http_response_code(200);
    echo json_encode(["mensaje" => "Configuración guardada correctamente."]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al guardar.", "error" => $e->getMessage()]);
}
?>