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
    
    // Convertimos un string vacío a NULL real de base de datos
    $id_cliente = !empty($data->id_cliente) ? intval($data->id_cliente) : null;

    try {
        $db->beginTransaction();

        if (!empty($data->id_usuario)) {
            $id_usuario = intval($data->id_usuario);
            
            if (!empty($data->password)) {
                $password_hash = password_hash($data->password, PASSWORD_BCRYPT);
                // Agregamos id_cliente al UPDATE
                $query = "UPDATE usuario SET nombre = :n, apellido = :a, email = :e, password_hash = :p, vigente = :v, id_cliente = :c WHERE id_usuario = :id";
                $stmt = $db->prepare($query);
                $stmt->bindParam(':p', $password_hash);
            } else {
                // Agregamos id_cliente al UPDATE sin password
                $query = "UPDATE usuario SET nombre = :n, apellido = :a, email = :e, vigente = :v, id_cliente = :c WHERE id_usuario = :id";
                $stmt = $db->prepare($query);
            }
            
            $stmt->bindParam(':id', $id_usuario);
            $stmt->bindParam(':n', $nombre);
            $stmt->bindParam(':a', $apellido);
            $stmt->bindParam(':e', $email);
            $stmt->bindParam(':v', $vigente);
            // El PDO::PARAM_NULL es clave para que guarde un NULL real
            $stmt->bindValue(':c', $id_cliente, is_null($id_cliente) ? PDO::PARAM_NULL : PDO::PARAM_INT);
            $stmt->execute();

            $del_rol = $db->prepare("DELETE FROM usuario_rol WHERE id_usuario = :id");
            $del_rol->bindParam(':id', $id_usuario);
            $del_rol->execute();

            $ins_rol = $db->prepare("INSERT INTO usuario_rol (id_usuario, id_rol) VALUES (:id_u, :id_r)");
            $ins_rol->bindParam(':id_u', $id_usuario);
            $ins_rol->bindParam(':id_r', $id_rol);
            $ins_rol->execute();

            $db->commit();
            http_response_code(200);
            echo json_encode(["mensaje" => "Usuario actualizado correctamente."]);

        } 
        else {
            if (empty($data->password)) {
                throw new Exception("La contraseña es obligatoria para usuarios nuevos.");
            }
            
            $password_hash = password_hash($data->password, PASSWORD_BCRYPT);
            
            // Agregamos id_cliente al INSERT
            $query = "INSERT INTO usuario (nombre, apellido, email, password_hash, vigente, id_cliente) 
                      VALUES (:n, :a, :e, :p, :v, :c)";
            $stmt = $db->prepare($query);
            $stmt->bindParam(':n', $nombre);
            $stmt->bindParam(':a', $apellido);
            $stmt->bindParam(':e', $email);
            $stmt->bindParam(':p', $password_hash);
            $stmt->bindParam(':v', $vigente);
            $stmt->bindValue(':c', $id_cliente, is_null($id_cliente) ? PDO::PARAM_NULL : PDO::PARAM_INT);
            $stmt->execute();

            $nuevo_id = $db->lastInsertId();

            $ins_rol = $db->prepare("INSERT INTO usuario_rol (id_usuario, id_rol) VALUES (:id_u, :id_r)");
            $ins_rol->bindParam(':id_u', $nuevo_id);
            $ins_rol->bindParam(':id_r', $id_rol);
            $ins_rol->execute();

            $db->commit();
            http_response_code(201);
            echo json_encode(["mensaje" => "Usuario creado correctamente."]);
        }
    } catch (Exception $e) {
        $db->rollBack(); 
        http_response_code(503);
        echo json_encode(["mensaje" => "Error al guardar el usuario: " . $e->getMessage()]);
    }
} else {
    http_response_code(400);
    echo json_encode(["mensaje" => "Datos incompletos. Nombre, Email y Rol son obligatorios."]);
}