<?php
// Cabeceras de seguridad y CORS
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Validación Básica del Token (Bearer Token)
$headers = apache_request_headers();
if (!isset($headers['Authorization'])) {
    http_response_code(401);
    echo json_encode(["mensaje" => "Acceso denegado. No se proporcionó token de seguridad."]);
    exit();
}

include_once '../../config/Database.php';
include_once '../../models/Rol.php';

$database = new Database();
$db = $database->getConnection();
$rol = new Rol($db);

$stmt = $rol->leer();
$num = $stmt->rowCount();

if ($num > 0) {
    $roles_arr = array();
    $roles_arr["registros"] = array();

    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        extract($row);
        $rol_item = array(
            "id_rol" => $id_rol,
            "descripcion" => html_entity_decode($descripcion),
            "vigente" => $vigente
        );
        array_push($roles_arr["registros"], $rol_item);
    }

    http_response_code(200);
    echo json_encode($roles_arr);
} else {
    http_response_code(404);
    echo json_encode(["mensaje" => "No se encontraron roles."]);
}