<?php
// Cabeceras CORS y de tipo de contenido
header("Access-Control-Allow-Origin: *"); // En producción, cambiaremos el "*" por "http://tudominio.com"
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST");
header("Access-Control-Max-Age: 3600");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

// Si es una petición OPTIONS (Pre-flight de CORS), salimos temprano
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

// Obtenemos los datos enviados por Next.js en formato JSON
$data = json_decode(file_get_contents("php://input"));

// Validamos que vengan los datos
if (!empty($data->email) && !empty($data->password)) {
    
    $usuario->email = $data->email;
    $stmt = $usuario->obtenerPorEmail();
    
    if ($stmt->rowCount() > 0) {
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        
        // Verificamos si el usuario está vigente
        if ($row['vigente'] == 0) {
            http_response_code(401);
            echo json_encode(["mensaje" => "Cuenta inactiva. Contacte al administrador."]);
            exit();
        }

        // Magia de seguridad: verificamos el hash de la contraseña
        if (password_verify($data->password, $row['password_hash'])) {
            
            // Actualizar último login
            try {
                $ip = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
                $stmt_login = $db->prepare("UPDATE usuario SET ultimo_login = NOW(), ultimo_login_ip = :ip WHERE id_usuario = :id");
                $stmt_login->execute([':ip' => $ip, ':id' => $row['id_usuario']]);
            } catch (Exception $e) { /* No bloqueamos el login si esto falla */ }
            // --- NUEVO: GESTIÓN DE PERMISOS DINÁMICOS ---
            $id_rol = $row['id_rol']; 
            $permisos_array = [];

            try {
                // Buscamos los permisos asignados al rol en la tabla de cruce.
                // Usamos prepared statements para máxima seguridad.
                $query_permisos = "SELECT p.descripcion as nombre_permiso 
                                   FROM permiso p 
                                   INNER JOIN rol_permiso rp ON p.id_permiso = rp.id_permiso 
                                   WHERE rp.id_rol = :id_rol";
                
                $stmt_permisos = $db->prepare($query_permisos);
                $stmt_permisos->bindParam(":id_rol", $id_rol, PDO::PARAM_INT);
                $stmt_permisos->execute();
                
                // PDO::FETCH_COLUMN aplana el resultado a un array simple ["permiso1", "permiso2"]
                $permisos_array = $stmt_permisos->fetchAll(PDO::FETCH_COLUMN);

            } catch (Exception $e) {
                http_response_code(500);
                // ESTO ES SOLO PARA PRUEBAS, LUEGO LO BORRAMOS
                echo json_encode([
                    "mensaje" => "Error de Debug: " . $e->getMessage(),
                    "archivo" => $e->getFile(),
                    "linea" => $e->getLine()
                ]);
            }
            // --------------------------------------------

            $jwtHandler = new JwtHandler();
            
            // Agregamos el id_rol al payload del token. Es una excelente práctica 
            // de seguridad para que el backend sepa quién hace qué sin volver a consultar la DB.
            $token = $jwtHandler->generarToken([
                "id_usuario" => $row['id_usuario'],
                "email" => $usuario->email,
                "id_rol" => $id_rol
            ]);
            
            http_response_code(200);
            
            // Retornamos el Token y la nueva matriz de seguridad al Frontend
            echo json_encode([
                "mensaje" => "Login exitoso.",
                "token" => $token,
                "usuario" => [
                    "id_usuario"  => $row['id_usuario'],
                    "nombre"      => $row['nombre'] ?? '',
                    "apellido"    => $row['apellido'] ?? '',
                    "id_rol"      => $id_rol,
                    "id_cliente"  => $row['id_cliente'] ?? null  // null = usuario interno LGC
                ],
                "permisos" => $permisos_array
            ]);

        } else {
            // Contraseña incorrecta
            http_response_code(401);
            echo json_encode(["mensaje" => "Credenciales incorrectas."]);
        }
    } else {
        // Email no encontrado
        http_response_code(401);
        echo json_encode(["mensaje" => "Credenciales incorrectas."]);
    }
} else {
    // Faltan datos
    http_response_code(400);
    echo json_encode(["mensaje" => "Datos incompletos. Se requiere email y password."]);
}