<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST");
header("Access-Control-Max-Age: 3600");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../config/Database.php';
include_once '../config/JwtHandler.php';

$token = '';
if (isset($_SERVER['HTTP_AUTHORIZATION'])) {
    $token = trim(str_ireplace('Bearer', '', $_SERVER['HTTP_AUTHORIZATION']));
} else {
    $headers = getallheaders();
    if (isset($headers['Authorization'])) {
        $token = trim(str_ireplace('Bearer', '', $headers['Authorization']));
    }
}

$jwtHandler = new JwtHandler();
$payload = $jwtHandler->verificar($token);

if (!$payload) {
    http_response_code(401);
    echo json_encode(["mensaje" => "Token inválido o expirado."]);
    exit();
}

$payload_array = (array) $payload;

if (!isset($payload_array['id_usuario'])) {
    http_response_code(403);
    echo json_encode(["mensaje" => "Token no válido para esta operación."]);
    exit();
}

$data = json_decode(file_get_contents("php://input"));

if (!empty($data->id_cliente)) {
    $id_cliente_seleccionado = (int) $data->id_cliente;
    $id_usuario = $payload_array['id_usuario'];
    
    $database = new Database();
    $db = $database->getConnection();
    
    try {
        $query_check = "SELECT id_cliente FROM usuario_cliente WHERE id_usuario = :id_usuario AND id_cliente = :id_cliente";
        $stmt_check = $db->prepare($query_check);
        $stmt_check->execute([
            ':id_usuario' => $id_usuario,
            ':id_cliente' => $id_cliente_seleccionado
        ]);
        
        if ($stmt_check->rowCount() > 0) {
            
            $query_usuario = "SELECT u.nombre, u.apellido, ur.id_rol 
                              FROM usuario u
                              LEFT JOIN usuario_rol ur ON u.id_usuario = ur.id_usuario
                              WHERE u.id_usuario = :id_usuario LIMIT 1";
            $stmt_user = $db->prepare($query_usuario);
            $stmt_user->execute([':id_usuario' => $id_usuario]);
            $row_user = $stmt_user->fetch(PDO::FETCH_ASSOC);

            $id_rol = $row_user['id_rol'];

            $permisos_array = [];
            $query_permisos = "SELECT p.descripcion as nombre_permiso 
                               FROM permiso p 
                               INNER JOIN rol_permiso rp ON p.id_permiso = rp.id_permiso 
                               WHERE rp.id_rol = :id_rol";
            $stmt_permisos = $db->prepare($query_permisos);
            $stmt_permisos->bindParam(":id_rol", $id_rol, PDO::PARAM_INT);
            $stmt_permisos->execute();
            $permisos_array = $stmt_permisos->fetchAll(PDO::FETCH_COLUMN);

            $token_final = $jwtHandler->generarToken([
                "id_usuario" => $id_usuario,
                "email" => $payload_array['email'],
                "id_rol" => $id_rol,
                "id_cliente" => $id_cliente_seleccionado
            ]);
            
            http_response_code(200);
            echo json_encode([
                "mensaje" => "Entorno seleccionado correctamente.",
                "token" => $token_final,
                "usuario" => [
                    "id_usuario"  => $id_usuario,
                    "nombre"      => $row_user['nombre'] ?? '',
                    "apellido"    => $row_user['apellido'] ?? '',
                    "id_rol"      => $id_rol,
                    "id_cliente"  => $id_cliente_seleccionado
                ],
                "permisos" => $permisos_array
            ]);

        } else {
            http_response_code(403);
            echo json_encode(["mensaje" => "No tiene acceso al entorno seleccionado."]);
        }
    } catch (Exception $e) {
        http_response_code(500);
        echo json_encode(["mensaje" => "Error interno en el servidor.", "error" => $e->getMessage()]);
    }
} else {
    http_response_code(400);
    echo json_encode(["mensaje" => "Debe seleccionar un cliente."]);
}
?>