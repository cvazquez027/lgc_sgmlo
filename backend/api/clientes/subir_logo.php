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

// 1. Validar que llegó un archivo
if (!isset($_FILES['logo']) || $_FILES['logo']['error'] !== UPLOAD_ERR_OK) {
    http_response_code(400);
    echo json_encode(["mensaje" => "No se recibió ningún logo o hubo un error en la subida."]);
    exit();
}

$archivo = $_FILES['logo'];

// 2. CIBERSEGURIDAD: Validación de tamaño (Max 2MB para logos)
$max_size = 2 * 1024 * 1024; 
if ($archivo['size'] > $max_size) {
    http_response_code(400);
    echo json_encode(["mensaje" => "El logo es demasiado pesado. El máximo permitido es 2MB."]);
    exit();
}

// 3. CIBERSEGURIDAD: Validar MIME Type real (firma binaria)
$finfo = finfo_open(FILEINFO_MIME_TYPE);
$mime_type = finfo_file($finfo, $archivo['tmp_name']);
finfo_close($finfo);

// Permitimos JPG, PNG, WEBP y SVG
$allowed_mimes = [
    'image/jpeg', 
    'image/png', 
    'image/webp',
    'image/svg+xml'
];

if (!in_array($mime_type, $allowed_mimes)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Formato no permitido. Solo se aceptan imágenes (JPG, PNG, WEBP, SVG)."]);
    exit();
}

// 4. Renombrado Seguro
$extension = pathinfo($archivo['name'], PATHINFO_EXTENSION);
// Generamos un nombre único y difícil de adivinar
$nombre_seguro = uniqid('logo_', true) . '.' . $extension;

// Ruta absoluta donde se guardará físicamente
$directorio_destino = dirname(__DIR__, 2) . '/uploads/logos_clientes/'; 

// Si la carpeta no existe, la creamos de forma segura
if (!is_dir($directorio_destino)) {
    mkdir($directorio_destino, 0755, true);
}

$ruta_final = $directorio_destino . $nombre_seguro;
// Ruta que guardaremos en la base de datos (relativa al backend)
$path_db = 'uploads/logos_clientes/' . $nombre_seguro; 

// 5. Mover el archivo
if (move_uploaded_file($archivo['tmp_name'], $ruta_final)) {
    http_response_code(200);
    echo json_encode([
        "mensaje" => "Logo subido exitosamente.",
        "logo_path" => $path_db
    ]);
} else {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al guardar el logo en el servidor."]);
}
?>