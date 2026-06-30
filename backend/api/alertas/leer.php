<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';
include_once '../../config/JwtHandler.php';

// --- Extracción robusta del token ---
$token = '';
if (isset($_SERVER['HTTP_AUTHORIZATION'])) {
    $token = trim(str_ireplace('Bearer', '', $_SERVER['HTTP_AUTHORIZATION']));
} elseif (function_exists('apache_request_headers')) {
    $requestHeaders = apache_request_headers();
    $requestHeaders = array_combine(array_map('ucwords', array_keys($requestHeaders)), array_values($requestHeaders));
    if (isset($requestHeaders['Authorization'])) {
        $token = trim(str_ireplace('Bearer', '', $requestHeaders['Authorization']));
    }
} else {
    $headers = getallheaders();
    if (isset($headers['Authorization'])) {
        $token = trim(str_ireplace('Bearer', '', $headers['Authorization']));
    }
}

$jwt = new JwtHandler();
$payload = $jwt->verificar($token);
if (!$payload) {
    http_response_code(401);
    echo json_encode(["mensaje" => "No autorizado. Token inválido o expirado."]);
    exit();
}

$payload_array = (array) $payload;
$id_cliente = isset($payload_array['id_cliente']) ? $payload_array['id_cliente'] : null;
$id_usuario = isset($payload_array['id_usuario']) ? $payload_array['id_usuario'] : null;
$rol = isset($payload_array['rol']) ? $payload_array['rol'] : null;
$es_admin = ($id_cliente === null) || ($rol === 'admin' || $rol === 'administrador');

// Filtros opcionales
$incluir_leidas = isset($_GET['incluir_leidas']) && filter_var($_GET['incluir_leidas'], FILTER_VALIDATE_BOOLEAN);
$filtro_cliente = isset($_GET['id_cliente']) ? (int)$_GET['id_cliente'] : null;

$database = new Database();
$db = $database->getConnection();

try {
    // Construir consulta
    $query = "SELECT a.*, 
                     c.nombre_fantasia as cliente_nombre,
                     c.razon_social as cliente_razon
              FROM alerta a
              LEFT JOIN cliente c ON a.id_cliente = c.id_cliente
              WHERE 1=1";
    $params = [];

    if (!$es_admin) {
        // Cliente: solo sus alertas
        if (!$id_cliente) {
            // Si es cliente pero no tiene id_cliente, no debería pasar, pero devolvemos vacío
            http_response_code(200);
            echo json_encode(["alertas" => [], "debug_id_cliente" => null]);
            exit();
        }
        $query .= " AND a.id_cliente = :id_cliente";
        $params[':id_cliente'] = $id_cliente;
    } else {
        // Admin: puede filtrar por cliente si se especifica
        if ($filtro_cliente) {
            $query .= " AND a.id_cliente = :filtro_cliente";
            $params[':filtro_cliente'] = $filtro_cliente;
        }
    }

    if (!$incluir_leidas) {
        $query .= " AND a.leido = 0";
    }

    $query .= " ORDER BY a.fecha_creacion DESC";

    $stmt = $db->prepare($query);
    foreach ($params as $key => $value) {
        $stmt->bindValue($key, $value);
    }
    $stmt->execute();

    $alertas = $stmt->fetchAll(PDO::FETCH_ASSOC);

    http_response_code(200);
    echo json_encode([
        "alertas" => $alertas,
        "debug_es_admin" => $es_admin,
        "debug_id_cliente" => $id_cliente,
        "debug_total" => count($alertas)
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al leer alertas.", "error" => $e->getMessage()]);
}
?>