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

// --- Extracción robusta del token ---
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
$id_usuario = isset($payload_array['id_usuario']) ? $payload_array['id_usuario'] : null;
$id_cliente = isset($payload_array['id_cliente']) ? $payload_array['id_cliente'] : null;
$es_admin = ($id_cliente === null); // si no tiene id_cliente, es administrador

if (!$id_usuario) {
    http_response_code(403);
    echo json_encode(["mensaje" => "No se pudo identificar al usuario."]);
    exit();
}

$data = json_decode(file_get_contents("php://input"));
if (empty($data->id_documentacion)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Falta id_documentacion."]);
    exit();
}

$id_documentacion = (int)$data->id_documentacion;

$database = new Database();
$db = $database->getConnection();

try {
    // Obtener el registro de documentación
    $query = "SELECT path_archivos, id_usuario_subida FROM documentacion WHERE id_documentacion = :id_doc";
    $stmt = $db->prepare($query);
    $stmt->execute([':id_doc' => $id_documentacion]);
    $doc = $stmt->fetch(PDO::FETCH_ASSOC);

    if (!$doc) {
        http_response_code(404);
        echo json_encode(["mensaje" => "Documento no encontrado."]);
        exit();
    }

    // Si es cliente, verificar que sea el propietario
    if (!$es_admin) {
        if ($doc['id_usuario_subida'] != $id_usuario) {
            http_response_code(403);
            echo json_encode(["mensaje" => "No tienes permiso para eliminar este archivo. Solo el usuario que lo subió puede eliminarlo."]);
            exit();
        }
    }

    // Iniciar transacción
    $db->beginTransaction();

    // 1. Eliminar la relación en doc_item_matriz
    $stmt_rel = $db->prepare("DELETE FROM doc_item_matriz WHERE id_documentacion = :id_doc");
    $stmt_rel->execute([':id_doc' => $id_documentacion]);

    // 2. Eliminar el registro de documentación
    $stmt_doc = $db->prepare("DELETE FROM documentacion WHERE id_documentacion = :id_doc");
    $stmt_doc->execute([':id_doc' => $id_documentacion]);

    // 3. Eliminar el archivo físico
    $ruta_archivo = '../../' . $doc['path_archivos'];
    if (file_exists($ruta_archivo)) {
        unlink($ruta_archivo);
    }

    $db->commit();

    http_response_code(200);
    echo json_encode(["mensaje" => "Evidencia eliminada correctamente."]);

} catch (Exception $e) {
    if ($db->inTransaction()) $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al eliminar.", "error" => $e->getMessage()]);
}
?>