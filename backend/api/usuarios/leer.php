<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

$headers = apache_request_headers();
if (!isset($headers['Authorization'])) {
    http_response_code(401);
    echo json_encode(["mensaje" => "Acceso denegado."]);
    exit();
}

include_once '../../config/Database.php';
include_once '../../models/Usuario.php';

$database = new Database();
$db = $database->getConnection();
$usuario = new Usuario($db);

$stmt = $usuario->leerTodos();
$num = $stmt->rowCount();

if ($num > 0) {
    $usuarios_arr = array();
    $usuarios_arr["registros"] = array();

    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        extract($row);
        $usuario_item = array(
            "id_usuario" => $id_usuario,
            "nombre_completo" => html_entity_decode($nombre . " " . $apellido),
            "email" => $email,
            "rol_nombre" => isset($rol_nombre) ? $rol_nombre : "Sin Rol",
            // Agregamos estos dos campos (asegurate que tu SELECT los traiga)
            "id_cliente" => isset($id_cliente) ? $id_cliente : null,
            "razon_social" => isset($razon_social) ? $razon_social : null,
            "ultimo_login" => isset($ultimo_login) ? $ultimo_login : null,
            "vigente" => $vigente
        );
        array_push($usuarios_arr["registros"], $usuario_item);
    }

    http_response_code(200);
    echo json_encode($usuarios_arr);
} else {
    http_response_code(200); 
    echo json_encode(["registros" => []]);
}