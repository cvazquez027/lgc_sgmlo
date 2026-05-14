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

// 1. OBTENER Y PARSEAR DATOS DEL FRONTEND
$data = json_decode(file_get_contents("php://input"));

if (empty($data->id_matriz)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Falta la Matriz asociada."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

// 2. SANITIZACIÓN DE ENTRADA
$id_item_matriz = !empty($data->id_item_matriz) ? (int)$data->id_item_matriz : null;
$id_matriz = (int)$data->id_matriz;

$resumen_legal = !empty($data->resumen_legal) ? htmlspecialchars(strip_tags(trim($data->resumen_legal))) : null;
$id_estado_cumplimiento = !empty($data->id_estado_cumplimiento) ? (int)$data->id_estado_cumplimiento : 1;

$articulos_aplicables = !empty($data->articulos_aplicables) ? htmlspecialchars(strip_tags(trim($data->articulos_aplicables))) : null;
$interpretacion_aplicacion = !empty($data->interpretacion_aplicacion) ? htmlspecialchars(strip_tags(trim($data->interpretacion_aplicacion))) : null;
$id_tipo_modalidad = !empty($data->id_tipo_modalidad) ? (int)$data->id_tipo_modalidad : null;
$obs_modalidad = !empty($data->obs_modalidad) ? htmlspecialchars(strip_tags(trim($data->obs_modalidad))) : null;
$proceso_aplica = !empty($data->proceso_aplica) ? htmlspecialchars(strip_tags(trim($data->proceso_aplica))) : null;
$detalle_tema = !empty($data->detalle_tema) ? htmlspecialchars(strip_tags(trim($data->detalle_tema))) : null;
$evidencia_cumplimiento = !empty($data->evidencia_cumplimiento) ? htmlspecialchars(strip_tags(trim($data->evidencia_cumplimiento))) : null;
$responsable_cumplimiento = !empty($data->responsable_cumplimiento) ? htmlspecialchars(strip_tags(trim($data->responsable_cumplimiento))) : null;
$verificacion_cumplimiento = !empty($data->verificacion_cumplimiento) ? htmlspecialchars(strip_tags(trim($data->verificacion_cumplimiento))) : null;
$obs_estado_cumplimiento = !empty($data->obs_estado_cumplimiento) ? htmlspecialchars(strip_tags(trim($data->obs_estado_cumplimiento))) : null;

// NUEVOS CAMPOS EDITABLES
$editable1 = !empty($data->editable1) ? htmlspecialchars(strip_tags(trim($data->editable1))) : null;
$editable2 = !empty($data->editable2) ? htmlspecialchars(strip_tags(trim($data->editable2))) : null;
$editable3 = !empty($data->editable3) ? htmlspecialchars(strip_tags(trim($data->editable3))) : null;
$editable4 = !empty($data->editable4) ? htmlspecialchars(strip_tags(trim($data->editable4))) : null;
$editable5 = !empty($data->editable5) ? htmlspecialchars(strip_tags(trim($data->editable5))) : null;

$vencimiento_plazo = (!empty($data->vencimiento_plazo)) ? $data->vencimiento_plazo : null;
$fecha_cumplimiento = (!empty($data->fecha_cumplimiento)) ? $data->fecha_cumplimiento : null;

$normas_vinculadas = (isset($data->normas_vinculadas) && is_array($data->normas_vinculadas)) ? $data->normas_vinculadas : [];
$documentos_vinculados = (isset($data->documentos_vinculados) && is_array($data->documentos_vinculados)) ? $data->documentos_vinculados : [];

try {
    $db->beginTransaction();

    if ($id_item_matriz) {
        $query_item = "UPDATE item_matriz SET 
                        id_matriz = :id_matriz, resumen_legal = :resumen_legal, articulos_aplicables = :articulos_aplicables,
                        interpretacion_aplicacion = :interpretacion_aplicacion, id_tipo_modalidad = :id_tipo_modalidad,
                        obs_modalidad = :obs_modalidad, vencimiento_plazo = :vencimiento_plazo, fecha_cumplimiento = :fecha_cumplimiento,
                        proceso_aplica = :proceso_aplica, detalle_tema = :detalle_tema, evidencia_cumplimiento = :evidencia_cumplimiento,
                        responsable_cumplimiento = :responsable_cumplimiento, verificacion_cumplimiento = :verificacion_cumplimiento,
                        id_estado_cumplimiento = :id_estado_cumplimiento, obs_estado_cumplimiento = :obs_estado_cumplimiento,
                        editable1 = :editable1, editable2 = :editable2, editable3 = :editable3, editable4 = :editable4, editable5 = :editable5
                       WHERE id_item_matriz = :id_item_matriz";
        $stmt = $db->prepare($query_item);
        $stmt->bindParam(":id_item_matriz", $id_item_matriz, PDO::PARAM_INT);
    } else {
        $query_item = "INSERT INTO item_matriz 
                        (id_matriz, resumen_legal, articulos_aplicables, interpretacion_aplicacion, id_tipo_modalidad, obs_modalidad, 
                         vencimiento_plazo, fecha_cumplimiento, proceso_aplica, detalle_tema, evidencia_cumplimiento, 
                         responsable_cumplimiento, verificacion_cumplimiento, id_estado_cumplimiento, obs_estado_cumplimiento,
                         editable1, editable2, editable3, editable4, editable5)
                       VALUES 
                        (:id_matriz, :resumen_legal, :articulos_aplicables, :interpretacion_aplicacion, :id_tipo_modalidad, :obs_modalidad, 
                         :vencimiento_plazo, :fecha_cumplimiento, :proceso_aplica, :detalle_tema, :evidencia_cumplimiento, 
                         :responsable_cumplimiento, :verificacion_cumplimiento, :id_estado_cumplimiento, :obs_estado_cumplimiento,
                         :editable1, :editable2, :editable3, :editable4, :editable5)";
        $stmt = $db->prepare($query_item);
    }

    $stmt->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    $stmt->bindParam(":resumen_legal", $resumen_legal, PDO::PARAM_STR);
    $stmt->bindParam(":articulos_aplicables", $articulos_aplicables, PDO::PARAM_STR);
    $stmt->bindParam(":interpretacion_aplicacion", $interpretacion_aplicacion, PDO::PARAM_STR);
    $stmt->bindParam(":id_tipo_modalidad", $id_tipo_modalidad, PDO::PARAM_INT);
    $stmt->bindParam(":obs_modalidad", $obs_modalidad, PDO::PARAM_STR);
    $stmt->bindParam(":vencimiento_plazo", $vencimiento_plazo, PDO::PARAM_STR);
    $stmt->bindParam(":fecha_cumplimiento", $fecha_cumplimiento, PDO::PARAM_STR);
    $stmt->bindParam(":proceso_aplica", $proceso_aplica, PDO::PARAM_STR);
    $stmt->bindParam(":detalle_tema", $detalle_tema, PDO::PARAM_STR);
    $stmt->bindParam(":evidencia_cumplimiento", $evidencia_cumplimiento, PDO::PARAM_STR);
    $stmt->bindParam(":responsable_cumplimiento", $responsable_cumplimiento, PDO::PARAM_STR);
    $stmt->bindParam(":verificacion_cumplimiento", $verificacion_cumplimiento, PDO::PARAM_STR);
    $stmt->bindParam(":id_estado_cumplimiento", $id_estado_cumplimiento, PDO::PARAM_INT);
    $stmt->bindParam(":obs_estado_cumplimiento", $obs_estado_cumplimiento, PDO::PARAM_STR);
    
    // Bindeamos los nuevos campos
    $stmt->bindParam(":editable1", $editable1, PDO::PARAM_STR);
    $stmt->bindParam(":editable2", $editable2, PDO::PARAM_STR);
    $stmt->bindParam(":editable3", $editable3, PDO::PARAM_STR);
    $stmt->bindParam(":editable4", $editable4, PDO::PARAM_STR);
    $stmt->bindParam(":editable5", $editable5, PDO::PARAM_STR);

    $stmt->execute();

    if (!$id_item_matriz) {
        $id_item_matriz = $db->lastInsertId();
    }

    // Sincronización Normas
    $stmt_del_normas = $db->prepare("DELETE FROM item_matriz_norma WHERE id_item_matriz = :id_item_matriz");
    $stmt_del_normas->bindParam(":id_item_matriz", $id_item_matriz, PDO::PARAM_INT);
    $stmt_del_normas->execute();

    if (!empty($normas_vinculadas)) {
        $stmt_ins_norma = $db->prepare("INSERT INTO item_matriz_norma (id_item_matriz, id_norma) VALUES (:id_item_matriz, :id_norma)");
        foreach ($normas_vinculadas as $id_norma) {
            $norma_clean = (int)$id_norma;
            $stmt_ins_norma->bindParam(":id_item_matriz", $id_item_matriz, PDO::PARAM_INT);
            $stmt_ins_norma->bindParam(":id_norma", $norma_clean, PDO::PARAM_INT);
            $stmt_ins_norma->execute();
        }
    }

    // Sincronización Documentos
    $stmt_del_docs = $db->prepare("DELETE FROM doc_item_matriz WHERE id_item_matriz = :id_item_matriz");
    $stmt_del_docs->bindParam(":id_item_matriz", $id_item_matriz, PDO::PARAM_INT);
    $stmt_del_docs->execute();

    if (!empty($documentos_vinculados)) {
        $stmt_ins_doc = $db->prepare("INSERT INTO doc_item_matriz (id_item_matriz, id_documentacion) VALUES (:id_item_matriz, :id_documentacion)");
        foreach ($documentos_vinculados as $id_doc) {
            $doc_clean = (int)$id_doc;
            $stmt_ins_doc->bindParam(":id_item_matriz", $id_item_matriz, PDO::PARAM_INT);
            $stmt_ins_doc->bindParam(":id_documentacion", $doc_clean, PDO::PARAM_INT);
            $stmt_ins_doc->execute();
        }
    }

    $db->commit();
    http_response_code(200);
    echo json_encode(["mensaje" => "Ítem guardado exitosamente.", "id_item_matriz" => $id_item_matriz]);

} catch (Exception $e) {
    $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno al guardar la matriz.", "error" => $e->getMessage()]);
}
?>