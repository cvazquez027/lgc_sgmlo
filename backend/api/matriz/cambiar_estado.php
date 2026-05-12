<?php
// Cabeceras de seguridad y CORS
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

// Validación de entrada: exigimos ambos IDs
if (empty($data->id_matriz) || empty($data->id_estado_matriz)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan parámetros obligatorios (id_matriz, id_estado_matriz)."]);
    exit();
}

$id_matriz = filter_var($data->id_matriz, FILTER_VALIDATE_INT);
$id_estado_matriz = filter_var($data->id_estado_matriz, FILTER_VALIDATE_INT);

if ($id_matriz === false || $id_estado_matriz === false) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Los parámetros deben ser numéricos."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    $query = "UPDATE matriz SET id_estado_matriz = :id_estado_matriz WHERE id_matriz = :id_matriz";
    $stmt = $db->prepare($query);
    
    $stmt->bindParam(":id_estado_matriz", $id_estado_matriz, PDO::PARAM_INT);
    $stmt->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    
    if($stmt->execute()) {
        http_response_code(200);
        echo json_encode(["mensaje" => "Estado de la matriz actualizado correctamente."]);
    } else {
        throw new Exception("No se pudo ejecutar la actualización.");
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno al actualizar estado.", "error" => $e->getMessage()]);
}
?>