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

$data = json_decode(file_get_contents("php://input"));

if (empty($data->id_matriz) || !isset($data->config_columnas)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan parámetros obligatorios."]);
    exit();
}

$id_matriz = filter_var($data->id_matriz, FILTER_VALIDATE_INT);
$config_string = json_encode($data->config_columnas);
json_decode($config_string);

if (json_last_error() !== JSON_ERROR_NONE || $id_matriz === false) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Datos inválidos o malformados."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    // 1. Iniciamos la Transacción (Seguridad ACID)
    $db->beginTransaction();

    // 2. Obtenemos los datos de la matriz que queremos publicar
    $query_info = "SELECT id_cliente_establecimiento, id_tipo_matriz FROM matriz WHERE id_matriz = :id_matriz FOR UPDATE";
    $stmt_info = $db->prepare($query_info);
    $stmt_info->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    $stmt_info->execute();
    $matriz_actual = $stmt_info->fetch(PDO::FETCH_ASSOC);

    if (!$matriz_actual) {
        throw new Exception("La matriz solicitada no existe.");
    }

    // 3. ARCHIVAMOS LA MATRIZ ANTERIOR (Si existe)
    // Pasamos a id_estado_matriz = 3 (Archivada) y vigente = 0 a cualquier matriz del mismo tipo y sede que estuviera vigente (1)
    $query_archivar = "UPDATE matriz 
                       SET id_estado_matriz = 3, vigente = 0 
                       WHERE id_cliente_establecimiento = :est 
                         AND id_tipo_matriz = :tipo 
                         AND id_estado_matriz = 1 
                         AND id_matriz != :id_matriz";
    
    $stmt_archivar = $db->prepare($query_archivar);
    $stmt_archivar->bindParam(":est", $matriz_actual['id_cliente_establecimiento'], PDO::PARAM_INT);
    $stmt_archivar->bindParam(":tipo", $matriz_actual['id_tipo_matriz'], PDO::PARAM_INT);
    $stmt_archivar->execute();

    // 4. PUBLICAMOS LA NUEVA MATRIZ
    $query_publicar = "UPDATE matriz 
                       SET id_estado_matriz = 1, vigente = 1, config_columnas = :config 
                       WHERE id_matriz = :id_matriz";
              
    $stmt_publicar = $db->prepare($query_publicar);
    $stmt_publicar->bindParam(":config", $config_string, PDO::PARAM_STR);
    $stmt_publicar->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    $stmt_publicar->execute();

    // 5. Si todo salió bien, confirmamos los cambios en la Base de Datos
    $db->commit();

    http_response_code(200);
    echo json_encode(["mensaje" => "Matriz publicada exitosamente. La versión anterior ha sido archivada."]);

} catch (Exception $e) {
    // Si algo falla, revertimos TODO (Rollback). Ningún dato queda a medias.
    $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno al publicar.", "error" => $e->getMessage()]);
}
?>