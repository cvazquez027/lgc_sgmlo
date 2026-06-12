<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

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

$token = str_replace('Bearer ', '', $headers['Authorization']);
include_once '../../config/JwtHandler.php';
$jwt = new JwtHandler();
$payload = $jwt->verificar($token);
if (!$payload) {
    http_response_code(401);
    echo json_encode(["mensaje" => "Token inválido o expirado."]);
    exit();
}

include_once '../../config/Database.php';
$database = new Database();
$db = $database->getConnection();

$limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 200;
$offset = isset($_GET['offset']) ? (int)$_GET['offset'] : 0;

$query = "SELECT a.id_auditoria, a.tabla_afectada, a.accion, a.id_registro, 
                 a.id_usuario, a.ip_origen, a.fecha_evento, a.datos_json,
                 CONCAT(u.nombre, ' ', u.apellido) as usuario_nombre
          FROM auditoria a
          LEFT JOIN usuario u ON a.id_usuario = u.id_usuario
          ORDER BY a.fecha_evento DESC
          LIMIT :limit OFFSET :offset";

$stmt = $db->prepare($query);
$stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
$stmt->bindParam(':offset', $offset, PDO::PARAM_INT);
$stmt->execute();

$rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

foreach ($rows as &$row) {
    if (!empty($row['datos_json'])) {
        $decoded = json_decode($row['datos_json'], true);
        if (json_last_error() === JSON_ERROR_NONE) {
            $row['datos_json'] = $decoded;
        } else {
            $row['datos_json'] = ['error' => 'No se pudo decodificar el JSON', 'raw' => $row['datos_json']];
        }
    } else {
        $row['datos_json'] = null;
    }
}

http_response_code(200);
echo json_encode([
    "registros" => $rows,
    "total" => count($rows)
]);
?>