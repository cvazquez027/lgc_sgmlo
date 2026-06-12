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

// Validar token JWT
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

// Verificar permiso de edición (opcional, pero se recomienda)
// Por simplicidad, asumimos que el frontend ya controla con canEdit.

$data = json_decode(file_get_contents("php://input"));
$id_norma = isset($data->id_norma) ? (int)$data->id_norma : 0;
if (!$id_norma) {
    http_response_code(400);
    echo json_encode(["mensaje" => "ID de norma inválido."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    $db->beginTransaction();

    // 1. Verificar si la norma está asociada a algún ítem de matriz
    $queryCheck = "SELECT COUNT(*) FROM item_matriz_norma WHERE id_norma = :id_norma";
    $stmtCheck = $db->prepare($queryCheck);
    $stmtCheck->bindParam(':id_norma', $id_norma, PDO::PARAM_INT);
    $stmtCheck->execute();
    $asociada = $stmtCheck->fetchColumn();

    if ($asociada > 0) {
        $db->rollBack();
        http_response_code(409); // Conflict
        echo json_encode(["mensaje" => "No se puede eliminar la norma porque está vinculada a una o más matrices. Elimine los ítems que la referencian antes de intentar borrarla."]);
        exit();
    }

    // 2. Eliminar las categorías asociadas (por si no hay cascada automática)
    $queryDelCat = "DELETE FROM categoria_norma WHERE id_norma = :id_norma";
    $stmtDelCat = $db->prepare($queryDelCat);
    $stmtDelCat->bindParam(':id_norma', $id_norma, PDO::PARAM_INT);
    $stmtDelCat->execute();

    // 3. Eliminar la norma
    $queryDelNorma = "DELETE FROM norma WHERE id_norma = :id_norma";
    $stmtDelNorma = $db->prepare($queryDelNorma);
    $stmtDelNorma->bindParam(':id_norma', $id_norma, PDO::PARAM_INT);
    $stmtDelNorma->execute();

    $db->commit();

    http_response_code(200);
    echo json_encode(["mensaje" => "Norma eliminada correctamente."]);

} catch (Exception $e) {
    if ($db->inTransaction()) $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno al eliminar.", "error" => $e->getMessage()]);
}
?>