<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }

include_once '../../config/Database.php';

$data = json_decode(file_get_contents("php://input"));
if (empty($data->id_matriz)) {
    http_response_code(400); echo json_encode(["mensaje" => "Falta la Matriz asociada."]); exit();
}

$database = new Database(); $db = $database->getConnection();

$id_item_matriz = !empty($data->id_item_matriz) ? (int)$data->id_item_matriz : null;
$id_matriz = (int)$data->id_matriz;

$resumen_legal = !empty($data->resumen_legal) ? htmlspecialchars(strip_tags(trim($data->resumen_legal))) : null;
$id_estado_cumplimiento = !empty($data->id_estado_cumplimiento) ? (int)$data->id_estado_cumplimiento : 1;
$articulos_aplicables = !empty($data->articulos_aplicables) ? htmlspecialchars(strip_tags(trim($data->articulos_aplicables))) : null;
$interpretacion_aplicacion = !empty($data->interpretacion_aplicacion) ? htmlspecialchars(strip_tags(trim($data->interpretacion_aplicacion))) : null;
$id_tipo_modalidad = !empty($data->id_tipo_modalidad) ? (int)$data->id_tipo_modalidad : null;
$obs_modalidad = !empty($data->obs_modalidad) ? htmlspecialchars(strip_tags(trim($data->obs_modalidad))) : null;
$evidencia_cumplimiento = !empty($data->evidencia_cumplimiento) ? htmlspecialchars(strip_tags(trim($data->evidencia_cumplimiento))) : null;
$verificacion_cumplimiento = !empty($data->verificacion_cumplimiento) ? htmlspecialchars(strip_tags(trim($data->verificacion_cumplimiento))) : null;
$obs_estado_cumplimiento = !empty($data->obs_estado_cumplimiento) ? htmlspecialchars(strip_tags(trim($data->obs_estado_cumplimiento))) : null;
$id_responsable_establecimiento = !empty($data->id_responsable_establecimiento) ? (int)$data->id_responsable_establecimiento : null;
$vencimiento_plazo = (!empty($data->vencimiento_plazo)) ? $data->vencimiento_plazo : null;
$fecha_cumplimiento = (!empty($data->fecha_cumplimiento)) ? $data->fecha_cumplimiento : null;

// MAGIA NO ESTRUCTURADA: Extraemos cualquier variable que empiece con "custom_" al JSON
$dinamicos = [];
foreach ($data as $key => $value) {
    if (strpos($key, 'custom_') === 0) {
        $dinamicos[$key] = htmlspecialchars(strip_tags(trim($value)));
    }
}
$datos_dinamicos = !empty($dinamicos) ? json_encode($dinamicos) : null;

$normas_vinculadas = (isset($data->normas_vinculadas) && is_array($data->normas_vinculadas)) ? $data->normas_vinculadas : [];

try {
    $db->beginTransaction();

    if ($id_item_matriz) {
        // MODO EDICIÓN: NO se modifica el orden
        $query_item = "UPDATE item_matriz SET 
                        id_matriz = :id_matriz, resumen_legal = :resumen_legal, articulos_aplicables = :articulos_aplicables,
                        interpretacion_aplicacion = :interpretacion_aplicacion, id_tipo_modalidad = :id_tipo_modalidad,
                        obs_modalidad = :obs_modalidad, vencimiento_plazo = :vencimiento_plazo, fecha_cumplimiento = :fecha_cumplimiento,
                        evidencia_cumplimiento = :evidencia_cumplimiento, verificacion_cumplimiento = :verificacion_cumplimiento,
                        id_estado_cumplimiento = :id_estado_cumplimiento, obs_estado_cumplimiento = :obs_estado_cumplimiento,
                        id_responsable_establecimiento = :id_responsable, datos_dinamicos = :datos_dinamicos
                       WHERE id_item_matriz = :id_item_matriz";
        $stmt = $db->prepare($query_item);
        $stmt->bindValue(":id_item_matriz", $id_item_matriz, PDO::PARAM_INT);
    } else {
        // MODO CREACIÓN: Calcular el próximo orden para esta matriz
        $query_max_orden = "SELECT COALESCE(MAX(orden), -1) + 1 AS siguiente_orden FROM item_matriz WHERE id_matriz = :id_matriz";
        $stmt_max = $db->prepare($query_max_orden);
        $stmt_max->execute([':id_matriz' => $id_matriz]);
        $siguiente_orden = (int)$stmt_max->fetchColumn();

        $query_item = "INSERT INTO item_matriz 
                        (id_matriz, orden, resumen_legal, articulos_aplicables, interpretacion_aplicacion, id_tipo_modalidad, obs_modalidad, 
                         vencimiento_plazo, fecha_cumplimiento, evidencia_cumplimiento, verificacion_cumplimiento, 
                         id_estado_cumplimiento, obs_estado_cumplimiento, id_responsable_establecimiento, datos_dinamicos)
                       VALUES 
                        (:id_matriz, :orden, :resumen_legal, :articulos_aplicables, :interpretacion_aplicacion, :id_tipo_modalidad, :obs_modalidad, 
                         :vencimiento_plazo, :fecha_cumplimiento, :evidencia_cumplimiento, :verificacion_cumplimiento, 
                         :id_estado_cumplimiento, :obs_estado_cumplimiento, :id_responsable, :datos_dinamicos)";
        $stmt = $db->prepare($query_item);
        $stmt->bindValue(":orden", $siguiente_orden, PDO::PARAM_INT);
    }

    // Parámetros comunes a INSERT y UPDATE
    $stmt->bindValue(":id_matriz", $id_matriz, PDO::PARAM_INT);
    $stmt->bindValue(":resumen_legal", $resumen_legal, is_null($resumen_legal) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":articulos_aplicables", $articulos_aplicables, is_null($articulos_aplicables) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":interpretacion_aplicacion", $interpretacion_aplicacion, is_null($interpretacion_aplicacion) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":id_tipo_modalidad", $id_tipo_modalidad, is_null($id_tipo_modalidad) ? PDO::PARAM_NULL : PDO::PARAM_INT);
    $stmt->bindValue(":obs_modalidad", $obs_modalidad, is_null($obs_modalidad) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":vencimiento_plazo", $vencimiento_plazo, is_null($vencimiento_plazo) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":fecha_cumplimiento", $fecha_cumplimiento, is_null($fecha_cumplimiento) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":evidencia_cumplimiento", $evidencia_cumplimiento, is_null($evidencia_cumplimiento) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":verificacion_cumplimiento", $verificacion_cumplimiento, is_null($verificacion_cumplimiento) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":id_estado_cumplimiento", $id_estado_cumplimiento, PDO::PARAM_INT);
    $stmt->bindValue(":obs_estado_cumplimiento", $obs_estado_cumplimiento, is_null($obs_estado_cumplimiento) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":id_responsable", $id_responsable_establecimiento, is_null($id_responsable_establecimiento) ? PDO::PARAM_NULL : PDO::PARAM_INT);
    $stmt->bindValue(":datos_dinamicos", $datos_dinamicos, is_null($datos_dinamicos) ? PDO::PARAM_NULL : PDO::PARAM_STR);

    $stmt->execute();
    if (!$id_item_matriz) $id_item_matriz = $db->lastInsertId();

    // Gestión de normas vinculadas
    $stmt_del_normas = $db->prepare("DELETE FROM item_matriz_norma WHERE id_item_matriz = :id_item_matriz");
    $stmt_del_normas->execute([':id_item_matriz' => $id_item_matriz]);

    if (!empty($normas_vinculadas)) {
        $stmt_ins_norma = $db->prepare("INSERT INTO item_matriz_norma (id_item_matriz, id_norma) VALUES (:id_item_matriz, :id_norma)");
        foreach ($normas_vinculadas as $id_norma) {
            $stmt_ins_norma->execute([':id_item_matriz' => $id_item_matriz, ':id_norma' => (int)$id_norma]);
        }
    }

    $db->commit();
    http_response_code(200);
    echo json_encode(["mensaje" => "Ítem guardado exitosamente.", "id_item_matriz" => $id_item_matriz]);

} catch (Exception $e) {
    $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno al guardar.", "error" => $e->getMessage()]);
}
?>