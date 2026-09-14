<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST");
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

$database = new Database();
$db = $database->getConnection();
$data = json_decode(file_get_contents("php://input"));

if (!empty($data->email) && !empty($data->nombre) && !empty($data->id_rol)) {
    
    $nombre = htmlspecialchars(strip_tags($data->nombre));
    $apellido = htmlspecialchars(strip_tags($data->apellido ?? ''));
    $email = filter_var($data->email, FILTER_SANITIZE_EMAIL);
    $id_rol = intval($data->id_rol);
    $vigente = isset($data->vigente) ? intval($data->vigente) : 1;
    
    $clientes = isset($data->clientes) && is_array($data->clientes) ? $data->clientes : [];

    try {
        $db->beginTransaction();

        if (!empty($data->id_usuario)) {
            $id_usuario = intval($data->id_usuario);
            
            if (!empty($data->password)) {
                $password_hash = password_hash($data->password, PASSWORD_BCRYPT);
                $query = "UPDATE usuario SET nombre = :n, apellido = :a, email = :e, password_hash = :p, vigente = :v WHERE id_usuario = :id";
                $stmt = $db->prepare($query);
                $stmt->bindParam(':p', $password_hash);
            } else {
                $query = "UPDATE usuario SET nombre = :n, apellido = :a, email = :e, vigente = :v WHERE id_usuario = :id";
                $stmt = $db->prepare($query);
            }
            
            $stmt->bindParam(':id', $id_usuario);
            $stmt->bindParam(':n', $nombre);
            $stmt->bindParam(':a', $apellido);
            $stmt->bindParam(':e', $email);
            $stmt->bindParam(':v', $vigente);
            $stmt->execute();

            $del_rol = $db->prepare("DELETE FROM usuario_rol WHERE id_usuario = :id");
            $del_rol->bindParam(':id', $id_usuario);
            $del_rol->execute();

            $ins_rol = $db->prepare("INSERT INTO usuario_rol (id_usuario, id_rol) VALUES (:id_u, :id_r)");
            $ins_rol->bindParam(':id_u', $id_usuario);
            $ins_rol->bindParam(':id_r', $id_rol);
            $ins_rol->execute();

        } else {
            if (empty($data->password)) {
                throw new Exception("La contraseña es obligatoria para usuarios nuevos.");
            }
            
            $password_hash = password_hash($data->password, PASSWORD_BCRYPT);
            
            $query = "INSERT INTO usuario (nombre, apellido, email, password_hash, vigente) 
                      VALUES (:n, :a, :e, :p, :v)";
            $stmt = $db->prepare($query);
            $stmt->bindParam(':n', $nombre);
            $stmt->bindParam(':a', $apellido);
            $stmt->bindParam(':e', $email);
            $stmt->bindParam(':p', $password_hash);
            $stmt->bindParam(':v', $vigente);
            $stmt->execute();

            $id_usuario = $db->lastInsertId();

            $ins_rol = $db->prepare("INSERT INTO usuario_rol (id_usuario, id_rol) VALUES (:id_u, :id_r)");
            $ins_rol->bindParam(':id_u', $id_usuario);
            $ins_rol->bindParam(':id_r', $id_rol);
            $ins_rol->execute();
        }

        // --- GESTIÓN DE CLIENTES ASIGNADOS ---
        $del_cli = $db->prepare("DELETE FROM usuario_cliente WHERE id_usuario = :id");
        $del_cli->bindParam(':id', $id_usuario);
        $del_cli->execute();

        if (!empty($clientes)) {
            $ins_cli = $db->prepare("INSERT INTO usuario_cliente (id_usuario, id_cliente) VALUES (:id_u, :id_c)");
            foreach ($clientes as $id_c) {
                $ins_cli->execute([
                    ':id_u' => $id_usuario,
                    ':id_c' => $id_c
                ]);
            }
        }

        $db->commit();
        http_response_code(!empty($data->id_usuario) ? 200 : 201);
        echo json_encode(["mensaje" => !empty($data->id_usuario) ? "Usuario actualizado correctamente." : "Usuario creado correctamente."]);
        
    } catch (Exception $e) {
        $db->rollBack(); 
        http_response_code(503);
        echo json_encode(["mensaje" => "Error al guardar el usuario: " . $e->getMessage()]);
    }
} else {
    http_response_code(400);
    echo json_encode(["mensaje" => "Datos incompletos. Nombre, Email y Rol son obligatorios."]);
}