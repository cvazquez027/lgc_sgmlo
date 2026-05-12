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

// 1. Validar que llegó un archivo
if (!isset($_FILES['archivo']) || $_FILES['archivo']['error'] !== UPLOAD_ERR_OK) {
    http_response_code(400);
    echo json_encode(["mensaje" => "No se recibió ningún archivo o hubo un error en la subida."]);
    exit();
}

$archivo = $_FILES['archivo'];

// 2. CIBERSEGURIDAD: Validación estricta
$max_size = 5 * 1024 * 1024; // 5 MB máximo
if ($archivo['size'] > $max_size) {
    http_response_code(400);
    echo json_encode(["mensaje" => "El archivo supera el límite de 5MB."]);
    exit();
}

// Validar MIME Type real (no confiamos en la extensión)
$finfo = finfo_open(FILEINFO_MIME_TYPE);
$mime_type = finfo_file($finfo, $archivo['tmp_name']);
finfo_close($finfo);

$allowed_mimes = [
    'application/pdf', 
    'image/jpeg', 
    'image/png', 
    'application/msword', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
];

if (!in_array($mime_type, $allowed_mimes)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Tipo de archivo no permitido. Solo se aceptan PDFs, Word o Imágenes."]);
    exit();
}

// 3. Renombrado seguro (Prevenir Directory Traversal y sobrescritura)
$extension = pathinfo($archivo['name'], PATHINFO_EXTENSION);
// Sanitizar el nombre original quitando caracteres raros
$nombre_original = preg_replace('/[^a-zA-Z0-9-_\.]/', '_', $archivo['name']); 
$nombre_seguro = uniqid('evidencia_', true) . '.' . $extension;

// Ruta absoluta de guardado (Ajustá si tu servidor requiere otra ruta)
$directorio_destino = dirname(__DIR__, 2) . '/uploads/'; 

// Si no existe la carpeta, la intentamos crear (por seguridad, lo ideal es crearla a mano)
if (!is_dir($directorio_destino)) {
    mkdir($directorio_destino, 0755, true);
}

$ruta_final = $directorio_destino . $nombre_seguro;
$path_db = 'uploads/' . $nombre_seguro; // Lo que guardamos en la BD (ruta relativa)

// 4. Mover el archivo e insertar en Base de Datos
if (move_uploaded_file($archivo['tmp_name'], $ruta_final)) {
    
    $database = new Database();
    $db = $database->getConnection();
    
    // Por ahora, como no hemos extraído el ID del token JWT, usaremos un usuario hardcodeado (ej. 1).
    // TODO: En producción, extraer ID del usuario desde el JWT.
    $id_usuario_subida = 1; 

    try {
        $query = "INSERT INTO documentacion (path_archivos, nombre_original, tipo_mime, peso_bytes, id_usuario_subida) 
                  VALUES (:path, :nombre, :mime, :peso, :usuario)";
        $stmt = $db->prepare($query);
        
        $stmt->bindParam(":path", $path_db, PDO::PARAM_STR);
        $stmt->bindParam(":nombre", $nombre_original, PDO::PARAM_STR);
        $stmt->bindParam(":mime", $mime_type, PDO::PARAM_STR);
        $stmt->bindParam(":peso", $archivo['size'], PDO::PARAM_INT);
        $stmt->bindParam(":usuario", $id_usuario_subida, PDO::PARAM_INT);
        
        $stmt->execute();
        $id_documentacion = $db->lastInsertId();

        http_response_code(200);
        echo json_encode([
            "mensaje" => "Archivo subido exitosamente.",
            "id_documentacion" => $id_documentacion,
            "nombre_original" => $nombre_original
        ]);
    } catch (Exception $e) {
        // Si falla la BD, borramos el archivo físico para no dejar basura
        unlink($ruta_final);
        http_response_code(500);
        echo json_encode(["mensaje" => "Error de base de datos.", "error" => $e->getMessage()]);
    }

} else {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al mover el archivo al servidor."]);
}
?>