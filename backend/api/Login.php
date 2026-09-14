<?php
// Cabeceras CORS y de tipo de contenido
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
include_once '../models/Usuario.php';
include_once '../config/JwtHandler.php';

$database = new Database();
$db = $database->getConnection();
$usuario = new Usuario($db);

$data = json_decode(file_get_contents("php://input"));

if (!empty($data->email) && !empty($data->password)) {
    
    $usuario->email = $data->email;
    $stmt = $usuario->obtenerPorEmail();
    
    if ($stmt->rowCount() > 0) {
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($row['vigente'] == 0) {
            http_response_code(401);
            echo json_encode(["mensaje" => "Cuenta inactiva. Contacte al administrador."]);
            exit();
        }

        if (password_verify($data->password, $row['password_hash'])) {
            
            try {
                $ip = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
                $stmt_login = $db->prepare("UPDATE usuario SET ultimo_login = NOW(), ultimo_login_ip = :ip WHERE id_usuario = :id");
                $stmt_login->execute([':ip' => $ip, ':id' => $row['id_usuario']]);
            } catch (Exception $e) { }

            $query_clientes = "SELECT uc.id_cliente, c.nombre_fantasia, c.razon_social 
                               FROM usuario_cliente uc
                               JOIN cliente c ON uc.id_cliente = c.id_cliente
                               WHERE uc.id_usuario = :id_usuario";
            $stmt_clientes = $db->prepare($query_clientes);
            $stmt_clientes->execute([':id_usuario' => $row['id_usuario']]);
            $clientes = $stmt_clientes->fetchAll(PDO::FETCH_ASSOC);

            $id_rol = $row['id_rol']; 
            $permisos_array = [];
            try {
                $query_permisos = "SELECT p.descripcion as nombre_permiso 
                                   FROM permiso p 
                                   INNER JOIN rol_permiso rp ON p.id_permiso = rp.id_permiso 
                                   WHERE rp.id_rol = :id_rol";
                $stmt_permisos = $db->prepare($query_permisos);
                $stmt_permisos->bindParam(":id_rol", $id_rol, PDO::PARAM_INT);
                $stmt_permisos->execute();
                $permisos_array = $stmt_permisos->fetchAll(PDO::FETCH_COLUMN);
            } catch (Exception $e) {}

            $jwtHandler = new JwtHandler();

            if (count($clientes) > 1) {
                $token_temporal = $jwtHandler->generarToken([
                    "id_usuario" => $row['id_usuario'],
                    "email" => $usuario->email,
                    "id_rol" => $id_rol,
                    "estado" => "pendiente_seleccion"
                ]);
                
                http_response_code(200);
                echo json_encode([
                    "mensaje" => "Selección de entorno requerida.",
                    "requiere_seleccion" => true,
                    "token_temporal" => $token_temporal,
                    "clientes" => $clientes
                ]);
            } else {
                $id_cliente_final = count($clientes) === 1 ? $clientes[0]['id_cliente'] : null;

                $token = $jwtHandler->generarToken([
                    "id_usuario" => $row['id_usuario'],
                    "email" => $usuario->email,
                    "id_rol" => $id_rol,
                    "id_cliente" => $id_cliente_final
                ]);
                
                http_response_code(200);
                echo json_encode([
                    "mensaje" => "Login exitoso.",
                    "requiere_seleccion" => false,
                    "token" => $token,
                    "usuario" => [
                        "id_usuario"  => $row['id_usuario'],
                        "nombre"      => $row['nombre'] ?? '',
                        "apellido"    => $row['apellido'] ?? '',
                        "id_rol"      => $id_rol,
                        "id_cliente"  => $id_cliente_final
                    ],
                    "permisos" => $permisos_array,
                    "clientes" => $clientes
                ]);
            }

        } else {
            http_response_code(401);
            echo json_encode(["mensaje" => "Credenciales incorrectas."]);
        }
    } else {
        http_response_code(401);
        echo json_encode(["mensaje" => "Credenciales incorrectas."]);
    }
} else {
    http_response_code(400);
    echo json_encode(["mensaje" => "Datos incompletos. Se requiere email y password."]);
}