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

// Validación estricta de los datos entrantes
if (empty($data->id_norma) || !isset($data->categorias) || !is_array($data->categorias)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan parámetros obligatorios o el formato es incorrecto."]);
    exit();
}

$id_norma = filter_var($data->id_norma, FILTER_VALIDATE_INT);

if (!$id_norma) {
    http_response_code(400);
    echo json_encode(["mensaje" => "ID de norma inválido."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    // Iniciamos transacción para que la operación sea atómica (Todo o Nada)
    $db->beginTransaction();

    // 1. Borramos todas las categorías previas asociadas a esta norma
    $query_delete = "DELETE FROM categoria_norma WHERE id_norma = :id_norma";
    $stmt_delete = $db->prepare($query_delete);
    $stmt_delete->bindParam(":id_norma", $id_norma, PDO::PARAM_INT);
    $stmt_delete->execute();

    // 2. Si enviaron categorías, las insertamos una por una
    if (!empty($data->categorias)) {
        $query_insert = "INSERT INTO categoria_norma (id_norma, id_categoria) VALUES (:id_norma, :id_cat)";
        $stmt_insert = $db->prepare($query_insert);
        
        foreach ($data->categorias as $id_cat_raw) {
            $id_cat = filter_var($id_cat_raw, FILTER_VALIDATE_INT);
            if ($id_cat) {
                $stmt_insert->bindParam(":id_norma", $id_norma, PDO::PARAM_INT);
                $stmt_insert->bindParam(":id_cat", $id_cat, PDO::PARAM_INT);
                $stmt_insert->execute();
            }
        }
    }

    // 3. Confirmamos los cambios
    $db->commit();
    http_response_code(200);
    echo json_encode(["mensaje" => "Categorías sincronizadas exitosamente."]);

} catch (Exception $e) {
    // Si algo falla, revertimos todo para no romper la base de datos
    $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al guardar las categorías.", "error" => $e->getMessage()]);
}
?>