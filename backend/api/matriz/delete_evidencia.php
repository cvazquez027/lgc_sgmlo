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
if (empty($data->id_documentacion) || empty($data->id_item_matriz)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan id_documentacion e id_item_matriz."]);
    exit();
}

$id_documentacion = (int)$data->id_documentacion;
$id_item_matriz = (int)$data->id_item_matriz;

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

    // 1. Eliminar SOLO la relación puntual de este ítem (no todas las de este documento:
    //    el mismo adjunto puede estar compartido con otras versiones de la matriz)
    $stmt_rel = $db->prepare("DELETE FROM doc_item_matriz WHERE id_documentacion = :id_doc AND id_item_matriz = :id_item");
    $stmt_rel->execute([':id_doc' => $id_documentacion, ':id_item' => $id_item_matriz]);

    if ($stmt_rel->rowCount() === 0) {
        $db->rollBack();
        http_response_code(404);
        echo json_encode(["mensaje" => "El documento no estaba vinculado a ese ítem."]);
        exit();
    }

    // 2. Verificar si el archivo sigue en uso por otra matriz Publicada (2) o Archivada (3).
    //    Si es así, NO se borra el archivo físico ni la fila de documentacion: solo se
    //    quitó el vínculo del ítem actual, y el adjunto sigue disponible para esas matrices.
    $stmt_uso = $db->prepare(
        "SELECT COUNT(*) FROM doc_item_matriz dim
         INNER JOIN item_matriz im ON dim.id_item_matriz = im.id_item_matriz
         INNER JOIN matriz m ON im.id_matriz = m.id_matriz
         WHERE dim.id_documentacion = :id_doc AND m.id_estado_matriz IN (2, 3)"
    );
    $stmt_uso->execute([':id_doc' => $id_documentacion]);
    $usado_en_publicada_o_archivada = (int)$stmt_uso->fetchColumn() > 0;

    if ($usado_en_publicada_o_archivada) {
        $db->commit();
        http_response_code(200);
        echo json_encode(["mensaje" => "Vínculo eliminado. El archivo se conserva porque está en uso en una matriz Publicada o Archivada."]);
        exit();
    }

    // 3. Si nadie más lo usa, verificar que tampoco queden otros vínculos sueltos
    //    (por ejemplo otro ítem de un borrador) antes de borrar de verdad.
    $stmt_otros = $db->prepare("SELECT COUNT(*) FROM doc_item_matriz WHERE id_documentacion = :id_doc");
    $stmt_otros->execute([':id_doc' => $id_documentacion]);
    $quedan_otros_vinculos = (int)$stmt_otros->fetchColumn() > 0;

    if ($quedan_otros_vinculos) {
        $db->commit();
        http_response_code(200);
        echo json_encode(["mensaje" => "Vínculo eliminado. El archivo se conserva porque sigue vinculado a otro ítem."]);
        exit();
    }

    // 4. Nadie más lo usa: recién ahora se borra la fila de documentacion y el archivo físico
    $stmt_doc = $db->prepare("DELETE FROM documentacion WHERE id_documentacion = :id_doc");
    $stmt_doc->execute([':id_doc' => $id_documentacion]);

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