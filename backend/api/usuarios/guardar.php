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
    echo json_encode(["mensaje" => "Acceso denegado."]);
    exit();
}

include_once '../../config/Database.php';

$database = new Database();
$db = $database->getConnection();
$data = json_decode(file_get_contents("php://input"));

// Validaciones básicas
if (!empty($data->email) && !empty($data->nombre) && !empty($data->id_rol)) {
    
    $nombre = htmlspecialchars(strip_tags($data->nombre));
    $apellido = htmlspecialchars(strip_tags($data->apellido ?? ''));
    $email = filter_var($data->email, FILTER_SANITIZE_EMAIL);
    $id_rol = intval($data->id_rol);
    $vigente = isset($data->vigente) ? intval($data->vigente) : 1;

    try {
        // Iniciamos una transacción (o se guarda todo, o no se guarda nada)
        $db->beginTransaction();

        // 1. LÓGICA DE EDICIÓN (UPDATE)
        if (!empty($data->id_usuario)) {
            $id_usuario = intval($data->id_usuario);
            
            // Si mandó una nueva contraseña, la hasheamos y la actualizamos
            if (!empty($data->password)) {
                $password_hash = password_hash($data->password, PASSWORD_BCRYPT);
                $query = "UPDATE usuario SET nombre = :n, apellido = :a, email = :e, password_hash = :p, vigente = :v WHERE id_usuario = :id";
                $stmt = $db->prepare($query);
                $stmt->bindParam(':p', $password_hash);
            } else {
                // Si no mandó contraseña, actualizamos todo menos la contraseña
                $query = "UPDATE usuario SET nombre = :n, apellido = :a, email = :e, vigente = :v WHERE id_usuario = :id";
                $stmt = $db->prepare($query);
            }
            
            $stmt->bindParam(':id', $id_usuario);
            $stmt->bindParam(':n', $nombre);
            $stmt->bindParam(':a', $apellido);
            $stmt->bindParam(':e', $email);
            $stmt->bindParam(':v', $vigente);
            $stmt->execute();

            // Actualizamos la relación del Rol
            // Primero borramos el rol anterior
            $del_rol = $db->prepare("DELETE FROM usuario_rol WHERE id_usuario = :id");
            $del_rol->bindParam(':id', $id_usuario);
            $del_rol->execute();

            // Y asignamos el nuevo
            $ins_rol = $db->prepare("INSERT INTO usuario_rol (id_usuario, id_rol) VALUES (:id_u, :id_r)");
            $ins_rol->bindParam(':id_u', $id_usuario);
            $ins_rol->bindParam(':id_r', $id_rol);
            $ins_rol->execute();

            $db->commit();
            http_response_code(200);
            echo json_encode(["mensaje" => "Usuario actualizado correctamente."]);

        } 
        // 2. LÓGICA DE ALTA (INSERT)
        else {
            if (empty($data->password)) {
                throw new Exception("La contraseña es obligatoria para usuarios nuevos.");
            }
            
            $password_hash = password_hash($data->password, PASSWORD_BCRYPT);
            
            // Insertamos el usuario
            $query = "INSERT INTO usuario (nombre, apellido, email, password_hash, vigente) 
                      VALUES (:n, :a, :e, :p, :v)";
            $stmt = $db->prepare($query);
            $stmt->bindParam(':n', $nombre);
            $stmt->bindParam(':a', $apellido);
            $stmt->bindParam(':e', $email);
            $stmt->bindParam(':p', $password_hash);
            $stmt->bindParam(':v', $vigente);
            $stmt->execute();

            // Obtenemos el ID generado
            $nuevo_id = $db->lastInsertId();

            // Le asignamos el rol
            $ins_rol = $db->prepare("INSERT INTO usuario_rol (id_usuario, id_rol) VALUES (:id_u, :id_r)");
            $ins_rol->bindParam(':id_u', $nuevo_id);
            $ins_rol->bindParam(':id_r', $id_rol);
            $ins_rol->execute();

            $db->commit();
            http_response_code(201);
            echo json_encode(["mensaje" => "Usuario creado correctamente."]);
        }
    } catch (Exception $e) {
        $db->rollBack(); // Si algo falla, deshacemos todo
        http_response_code(503);
        echo json_encode(["mensaje" => "Error al guardar el usuario: " . $e->getMessage()]);
    }
} else {
    http_response_code(400);
    echo json_encode(["mensaje" => "Datos incompletos. Nombre, Email y Rol son obligatorios."]);
}