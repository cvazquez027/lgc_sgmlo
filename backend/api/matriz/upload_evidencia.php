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
$id_usuario = !empty($_POST['id_usuario']) ? (int)$_POST['id_usuario'] : 1; // Por defecto usuario 1 si no llega
$archivo = $_FILES['archivo'];

// Carpeta donde se guardan (Asegurate de crear la carpeta uploads/evidencias en la raíz con permisos)
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
        $stmt_doc = $db->prepare("INSERT INTO documentacion (path_archivos, nombre_original, tipo_mime, peso_bytes, id_usuario_subida) VALUES (:ruta, :nombre, :mime, :peso, :user)");
        $stmt_doc->execute([':ruta' => $ruta_db, ':nombre' => $archivo['name'], ':mime' => $archivo['type'], ':peso' => $archivo['size'], ':user' => $id_usuario]);
        $id_doc = $db->lastInsertId();
        
        $stmt_link = $db->prepare("INSERT INTO doc_item_matriz (id_documentacion, id_item_matriz) VALUES (:id_doc, :id_item)");
        $stmt_link->execute([':id_doc' => $id_doc, ':id_item' => $id_item_matriz]);
        
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