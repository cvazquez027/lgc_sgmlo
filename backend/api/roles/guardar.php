<?php
// Cabeceras de seguridad y CORS
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Validación de Token
$headers = apache_request_headers();
if (!isset($headers['Authorization'])) {
    http_response_code(401);
    echo json_encode(["mensaje" => "Acceso denegado. No se proporcionó token."]);
    exit();
}

include_once '../../config/Database.php';

$database = new Database();
$db = $database->getConnection();

$data = json_decode(file_get_contents("php://input"));

// Validamos que venga al menos la descripción
if (!empty($data->descripcion)) {
    $descripcion = htmlspecialchars(strip_tags($data->descripcion));
    // Si viene vigente (1 o 0), lo tomamos, sino por defecto 1 (Activo)
    $vigente = isset($data->vigente) ? intval($data->vigente) : 1;
    
    // Si viene un ID, es una EDICIÓN (UPDATE)
    if (!empty($data->id_rol)) {
        $id_rol = intval($data->id_rol);
        $query = "UPDATE rol SET descripcion = :descripcion, vigente = :vigente WHERE id_rol = :id_rol";
        $stmt = $db->prepare($query);
        $stmt->bindParam(':id_rol', $id_rol);
        $stmt->bindParam(':descripcion', $descripcion);
        $stmt->bindParam(':vigente', $vigente);
        
        if ($stmt->execute()) {
            http_response_code(200);
            echo json_encode(["mensaje" => "Rol actualizado correctamente."]);
        } else {
            http_response_code(503);
            echo json_encode(["mensaje" => "Error al actualizar el rol."]);
        }
    } 
    // Si NO viene ID, es un ALTA (INSERT)
    else {
        $query = "INSERT INTO rol (descripcion, vigente) VALUES (:descripcion, :vigente)";
        $stmt = $db->prepare($query);
        $stmt->bindParam(':descripcion', $descripcion);
        $stmt->bindParam(':vigente', $vigente);
        
        if ($stmt->execute()) {
            http_response_code(201);
            echo json_encode(["mensaje" => "Rol creado correctamente."]);
        } else {
            http_response_code(503);
            echo json_encode(["mensaje" => "Error al crear el rol."]);
        }
    }
} else {
    http_response_code(400);
    echo json_encode(["mensaje" => "Datos incompletos. La descripción es obligatoria."]);
}