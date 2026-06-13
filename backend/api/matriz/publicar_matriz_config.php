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
    $db->beginTransaction();

    // 1. Obtener datos de la matriz
    $query_info = "SELECT id_cliente_establecimiento, id_tipo_matriz, id_especialidad_matriz, version 
                   FROM matriz WHERE id_matriz = :id_matriz FOR UPDATE";
    $stmt_info = $db->prepare($query_info);
    $stmt_info->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    $stmt_info->execute();
    $matriz_actual = $stmt_info->fetch(PDO::FETCH_ASSOC);

    if (!$matriz_actual) {
        throw new Exception("La matriz solicitada no existe.");
    }

    // *** VALIDACIÓN: La matriz debe tener al menos un ítem para poder publicarse ***
    $query_items_count = "SELECT COUNT(*) FROM item_matriz WHERE id_matriz = :id_matriz";
    $stmt_count = $db->prepare($query_items_count);
    $stmt_count->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    $stmt_count->execute();
    $total_items = (int)$stmt_count->fetchColumn();

    if ($total_items === 0) {
        $db->rollBack();
        http_response_code(400);
        echo json_encode(["mensaje" => "No se puede publicar la matriz porque no tiene ningún ítem asociado. Agregue al menos un ítem antes de publicar."]);
        exit();
    }

    // 2. Archivar versión anterior publicada
    $query_archivar = "UPDATE matriz 
                       SET id_estado_matriz = 3, vigente = 0 
                       WHERE id_cliente_establecimiento = :est 
                         AND id_tipo_matriz = :tipo 
                         AND id_especialidad_matriz = :especialidad
                         AND id_estado_matriz = 2 
                         AND id_matriz != :id_matriz";
    $stmt_archivar = $db->prepare($query_archivar);
    $stmt_archivar->bindParam(":est", $matriz_actual['id_cliente_establecimiento'], PDO::PARAM_INT);
    $stmt_archivar->bindParam(":tipo", $matriz_actual['id_tipo_matriz'], PDO::PARAM_INT);
    $stmt_archivar->bindParam(":especialidad", $matriz_actual['id_especialidad_matriz'], PDO::PARAM_INT);
    $stmt_archivar->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    $stmt_archivar->execute();

    // 3. Publicar la nueva matriz
    $query_publicar = "UPDATE matriz 
                       SET id_estado_matriz = 2, vigente = 1, config_columnas = :config 
                       WHERE id_matriz = :id_matriz";
    $stmt_publicar = $db->prepare($query_publicar);
    $stmt_publicar->bindParam(":config", $config_string, PDO::PARAM_STR);
    $stmt_publicar->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    $stmt_publicar->execute();

    // 4. --- DISPARADOR DE ALERTA: nueva versión publicada ---
    $query_cliente = "SELECT ce.id_cliente 
                      FROM matriz m
                      JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
                      WHERE m.id_matriz = :id_matriz";
    $stmt_cliente = $db->prepare($query_cliente);
    $stmt_cliente->execute([':id_matriz' => $id_matriz]);
    $id_cliente = $stmt_cliente->fetchColumn();
    
    if ($id_cliente) {
        $query_nombre = "SELECT CONCAT(tm.descripcion, ' - ', em.descripcion, ' - ', ce.descripcion) as nombre_matriz
                         FROM matriz m
                         JOIN tipo_matriz tm ON m.id_tipo_matriz = tm.id_tipo_matriz
                         JOIN especialidad_matriz em ON m.id_especialidad_matriz = em.id_especialidad_matriz
                         JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
                         WHERE m.id_matriz = :id_matriz";
        $stmt_nombre = $db->prepare($query_nombre);
        $stmt_nombre->execute([':id_matriz' => $id_matriz]);
        $nombre_matriz = $stmt_nombre->fetchColumn();
        $nombre_matriz = $nombre_matriz ?: "Matriz ID $id_matriz";
        
        $version = $matriz_actual['version'];
        $titulo = "Nueva versión de matriz publicada";
        $mensaje = "La matriz \"{$nombre_matriz}\" ha sido publicada en su versión {$version}.0. Ya está disponible para consulta.";
        $url = "/dashboard/matrices/{$id_matriz}";
        
        $stmt_alerta = $db->prepare("INSERT INTO alerta (id_cliente, id_matriz, tipo, titulo, mensaje, url, fecha_creacion, leido)
                                     VALUES (:id_cliente, :id_matriz, 'nueva_version_matriz', :titulo, :mensaje, :url, NOW(), 0)");
        $stmt_alerta->execute([
            ':id_cliente' => $id_cliente,
            ':id_matriz' => $id_matriz,
            ':titulo' => $titulo,
            ':mensaje' => $mensaje,
            ':url' => $url
        ]);
    }
    
    // 5. Verificar vencimientos próximos inmediatamente
    $query_vencimientos = "SELECT im.id_item_matriz, im.vencimiento_plazo, im.resumen_legal
                           FROM item_matriz im
                           WHERE im.id_matriz = :id_matriz
                             AND im.vencimiento_plazo IS NOT NULL
                             AND im.vencimiento_plazo BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)";
    $stmt_venc = $db->prepare($query_vencimientos);
    $stmt_venc->execute([':id_matriz' => $id_matriz]);
    $items_venc = $stmt_venc->fetchAll(PDO::FETCH_ASSOC);
    
    foreach ($items_venc as $item) {
        $check_duplicate = "SELECT COUNT(*) FROM alerta 
                            WHERE id_item_matriz = :id_item 
                              AND tipo = 'vencimiento_proximo' 
                              AND fecha_creacion > DATE_SUB(NOW(), INTERVAL 7 DAY)";
        $stmt_check = $db->prepare($check_duplicate);
        $stmt_check->execute([':id_item' => $item['id_item_matriz']]);
        $existe = $stmt_check->fetchColumn();
        
        if (!$existe && $id_cliente) {
            $dias = (new DateTime($item['vencimiento_plazo']))->diff(new DateTime())->days;
            $titulo_venc = "Vencimiento próximo";
            $mensaje_venc = "El ítem \"{$item['resumen_legal']}\" tiene vencimiento el {$item['vencimiento_plazo']} (dentro de {$dias} días).";
            $url_venc = "/dashboard/matrices/{$id_matriz}?item={$item['id_item_matriz']}";
            
            $stmt_insert_venc = $db->prepare("INSERT INTO alerta (id_cliente, id_matriz, id_item_matriz, tipo, titulo, mensaje, url, fecha_creacion, leido)
                                              VALUES (:id_cliente, :id_matriz, :id_item, 'vencimiento_proximo', :titulo, :mensaje, :url, NOW(), 0)");
            $stmt_insert_venc->execute([
                ':id_cliente' => $id_cliente,
                ':id_matriz' => $id_matriz,
                ':id_item' => $item['id_item_matriz'],
                ':titulo' => $titulo_venc,
                ':mensaje' => $mensaje_venc,
                ':url' => $url_venc
            ]);
        }
    }

    $db->commit();
    http_response_code(200);
    echo json_encode(["mensaje" => "Matriz publicada exitosamente. La versión anterior ha sido archivada."]);

} catch (Exception $e) {
    if ($db->inTransaction()) $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno al publicar.", "error" => $e->getMessage()]);
}
?>