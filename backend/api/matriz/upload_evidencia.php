<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }

include_once '../../config/Database.php';

if (!isset($_FILES['archivo']) || empty($_POST['id_item_matriz'])) {
    http_response_code(400); echo json_encode(["mensaje" => "Faltan parámetros o el archivo."]); exit();
}

$id_item_matriz = (int)$_POST['id_item_matriz'];
$id_usuario = !empty($_POST['id_usuario']) ? (int)$_POST['id_usuario'] : 1;
$archivo = $_FILES['archivo'];

$directorio_destino = "../../uploads/evidencias/";
if (!is_dir($directorio_destino)) mkdir($directorio_destino, 0777, true);

$extension = pathinfo($archivo['name'], PATHINFO_EXTENSION);
$nombre_fisico = "ev_" . time() . "_" . uniqid() . "." . $extension;
$ruta_completa = $directorio_destino . $nombre_fisico;
$ruta_db = "uploads/evidencias/" . $nombre_fisico;

if (move_uploaded_file($archivo['tmp_name'], $ruta_completa)) {
    $database = new Database(); $db = $database->getConnection();
    try {
        $db->beginTransaction();
        
        // 1. Insertar documentación
        $stmt_doc = $db->prepare("INSERT INTO documentacion (path_archivos, nombre_original, tipo_mime, peso_bytes, id_usuario_subida) VALUES (:ruta, :nombre, :mime, :peso, :user)");
        $stmt_doc->execute([':ruta' => $ruta_db, ':nombre' => $archivo['name'], ':mime' => $archivo['type'], ':peso' => $archivo['size'], ':user' => $id_usuario]);
        $id_doc = $db->lastInsertId();
        
        // 2. Vincular con el ítem
        $stmt_link = $db->prepare("INSERT INTO doc_item_matriz (id_documentacion, id_item_matriz) VALUES (:id_doc, :id_item)");
        $stmt_link->execute([':id_doc' => $id_doc, ':id_item' => $id_item_matriz]);
        
        // 3. --- DISPARADOR DE ALERTA: documento nuevo ---
        // He validado que el ítem existe y obtengo datos para la alerta
        $query_item = "SELECT im.resumen_legal, im.id_matriz, m.id_cliente_establecimiento, ce.id_cliente
                       FROM item_matriz im
                       JOIN matriz m ON im.id_matriz = m.id_matriz
                       JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
                       WHERE im.id_item_matriz = :id_item";
        $stmt_item = $db->prepare($query_item);
        $stmt_item->execute([':id_item' => $id_item_matriz]);
        $item_data = $stmt_item->fetch(PDO::FETCH_ASSOC);
        
        if ($item_data) {
            // Obtener nombre descriptivo de la matriz
            $query_matriz_nombre = "SELECT CONCAT(tm.descripcion, ' - ', em.descripcion, ' - ', ce.descripcion) as nombre_matriz
                                    FROM matriz m
                                    JOIN tipo_matriz tm ON m.id_tipo_matriz = tm.id_tipo_matriz
                                    JOIN especialidad_matriz em ON m.id_especialidad_matriz = em.id_especialidad_matriz
                                    JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
                                    WHERE m.id_matriz = :id_matriz";
            $stmt_nombre = $db->prepare($query_matriz_nombre);
            $stmt_nombre->execute([':id_matriz' => $item_data['id_matriz']]);
            $nombre_matriz = $stmt_nombre->fetchColumn();
            $nombre_matriz = $nombre_matriz ?: "Matriz ID {$item_data['id_matriz']}";
            
            $resumen = $item_data['resumen_legal'] ?: "ítem sin resumen";
            $titulo = "Nuevo documento subido";
            $mensaje = "Se ha subido un nuevo documento al ítem \"{$resumen}\" de la matriz \"{$nombre_matriz}\".";
            $url = "/dashboard/matrices/{$item_data['id_matriz']}?item={$id_item_matriz}";
            $id_cliente = $item_data['id_cliente'];
            
            // Insertar alerta (evito duplicados inmediatos, pero se puede insertar siempre)
            $stmt_alerta = $db->prepare("INSERT INTO alerta (id_cliente, id_matriz, id_item_matriz, tipo, titulo, mensaje, url, fecha_creacion, leido)
                                         VALUES (:id_cliente, :id_matriz, :id_item, 'documento_nuevo', :titulo, :mensaje, :url, NOW(), 0)");
            $stmt_alerta->execute([
                ':id_cliente' => $id_cliente,
                ':id_matriz' => $item_data['id_matriz'],
                ':id_item' => $id_item_matriz,
                ':titulo' => $titulo,
                ':mensaje' => $mensaje,
                ':url' => $url
            ]);
        }
        // --- Fin disparador ---
        
        $db->commit();
        http_response_code(200); echo json_encode(["mensaje" => "Evidencia subida correctamente."]);
    } catch(Exception $e) {
        $db->rollBack(); unlink($ruta_completa);
        http_response_code(500); echo json_encode(["error" => $e->getMessage()]);
    }
} else {
    http_response_code(500); echo json_encode(["mensaje" => "Error de disco al mover archivo."]);
}
?>