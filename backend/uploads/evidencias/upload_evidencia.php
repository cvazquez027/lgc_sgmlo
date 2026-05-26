<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }

include_once '../../config/Database.php';

// Validar que venga el archivo y el ID del ítem
if (!isset($_FILES['archivo']) || empty($_POST['id_item_matriz']) || empty($_POST['id_usuario'])) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan parámetros o el archivo."]);
    exit();
}

$id_item_matriz = (int)$_POST['id_item_matriz'];
$id_usuario = (int)$_POST['id_usuario']; // En el front lo sacamos del token JWT
$archivo = $_FILES['archivo'];

$directorio_destino = "../../uploads/evidencias/";
if (!is_dir($directorio_destino)) {
    mkdir($directorio_destino, 0777, true);
}

// Generar nombre único físico para evitar colisiones
$extension = pathinfo($archivo['name'], PATHINFO_EXTENSION);
$nombre_fisico = "evidencia_" . time() . "_" . uniqid() . "." . $extension;
$ruta_completa = $directorio_destino . $nombre_fisico;
$ruta_db = "uploads/evidencias/" . $nombre_fisico;

if (move_uploaded_file($archivo['tmp_name'], $ruta_completa)) {
    $database = new Database();
    $db = $database->getConnection();
    
    try {
        $db->beginTransaction();
        
        // 1. Insertar en tabla maestra de documentación
        $stmt_doc = $db->prepare("INSERT INTO documentacion (path_archivos, nombre_original, tipo_mime, peso_bytes, id_usuario_subida) 
                                  VALUES (:ruta, :nombre, :mime, :peso, :user)");
        $stmt_doc->execute([
            ':ruta' => $ruta_db,
            ':nombre' => $archivo['name'],
            ':mime' => $archivo['type'],
            ':peso' => $archivo['size'],
            ':user' => $id_usuario
        ]);
        $id_doc = $db->lastInsertId();
        
        // 2. Vincular con el item de la matriz
        $stmt_link = $db->prepare("INSERT INTO doc_item_matriz (id_documentacion, id_item_matriz) VALUES (:id_doc, :id_item)");
        $stmt_link->execute([':id_doc' => $id_doc, ':id_item' => $id_item_matriz]);
        
        $db->commit();
        http_response_code(200);
        echo json_encode([
            "mensaje" => "Evidencia subida correctamente.",
            "documento" => [
                "id_documentacion" => $id_doc,
                "nombre_original" => $archivo['name'],
                "path_archivos" => $ruta_db,
                "peso_bytes" => $archivo['size']
            ]
        ]);
    } catch(Exception $e) {
        $db->rollBack();
        unlink($ruta_completa); // Borrar archivo físico si falla BD
        http_response_code(500);
        echo json_encode(["error" => $e->getMessage()]);
    }
} else {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al mover el archivo subido."]);
}
?>