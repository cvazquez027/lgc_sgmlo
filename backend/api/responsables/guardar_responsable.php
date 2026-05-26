<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }

include_once '../../config/Database.php';

$data = json_decode(file_get_contents("php://input"));
$database = new Database();
$db = $database->getConnection();

try {
    // --- BORRAR ---
    if ($data->accion === 'borrar') {
        // Validar si está en uso en item_matriz
        $chk = $db->prepare("SELECT COUNT(*) FROM item_matriz WHERE id_responsable_establecimiento = :id");
        $chk->execute([':id' => $data->id_responsable_establecimiento]);
        if ($chk->fetchColumn() > 0) {
            http_response_code(409);
            echo json_encode(["mensaje" => "Este responsable está siendo utilizado en un ítem de matriz y no puede borrarse."]);
            exit();
        }
        $stmt = $db->prepare("DELETE FROM responsable_establecimiento WHERE id_responsable_establecimiento = :id");
        $stmt->execute([':id' => $data->id_responsable_establecimiento]);
        echo json_encode(["mensaje" => "Eliminado correctamente."]);
    }
    
    // --- REORDENAR ---
    else if ($data->accion === 'reordenar') {
        $db->beginTransaction();
        $stmt = $db->prepare("UPDATE responsable_establecimiento SET orden = :orden WHERE id_responsable_establecimiento = :id");
        foreach ($data->orden as $index => $id) {
            $stmt->execute([':orden' => $index, ':id' => $id]);
        }
        $db->commit();
        echo json_encode(["mensaje" => "Orden actualizado."]);
    }

    // --- GUARDAR / EDITAR ---
    else {
        if (!empty($data->id_responsable_establecimiento)) {
            // EDITAR
            $stmt = $db->prepare("UPDATE responsable_establecimiento SET descripcion = :desc, observacion = :obs, vigente = :vig WHERE id_responsable_establecimiento = :id");
            $stmt->execute([':desc' => $data->descripcion, ':obs' => $data->observacion, ':vig' => $data->vigente, ':id' => $data->id_responsable_establecimiento]);
        } else {
            // CREAR
            $stmt = $db->prepare("INSERT INTO responsable_establecimiento (id_establecimiento, descripcion, observacion, vigente) VALUES (:id_est, :desc, :obs, :vig)");
            $stmt->execute([':id_est' => $data->id_establecimiento, ':desc' => $data->descripcion, ':obs' => $data->observacion, ':vig' => $data->vigente]);
        }
        echo json_encode(["mensaje" => "Guardado correctamente."]);
    }

} catch (Exception $e) {
    if (isset($db) && $db->inTransaction()) $db->rollBack();
    http_response_code(500);
    echo json_encode(["error" => $e->getMessage()]);
}
?>