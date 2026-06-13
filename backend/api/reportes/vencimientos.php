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

// Extracción robusta del token
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
    echo json_encode(["mensaje" => "No autorizado."]);
    exit();
}

$id_cliente = $payload->id_cliente ?? null;
if (!$id_cliente) {
    echo json_encode(["vencimientos" => []]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

$dias_limite = 30;

$query = "SELECT 
            m.id_matriz,
            CONCAT(tm.descripcion, ' - ', em.descripcion, ' - ', ce.descripcion) AS nombre_matriz,
            im.id_item_matriz,
            im.resumen_legal AS item_resumen,
            im.vencimiento_plazo,
            DATEDIFF(im.vencimiento_plazo, CURDATE()) AS dias_restantes,
            ec.descripcion AS estado_desc,
            ec.color_hex
          FROM item_matriz im
          JOIN matriz m ON im.id_matriz = m.id_matriz
          JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
          JOIN cliente c ON ce.id_cliente = c.id_cliente
          JOIN tipo_matriz tm ON m.id_tipo_matriz = tm.id_tipo_matriz
          JOIN especialidad_matriz em ON m.id_especialidad_matriz = em.id_especialidad_matriz
          LEFT JOIN estado_cumplimiento ec ON im.id_estado_cumplimiento = ec.id_estado_cumplimiento
          WHERE c.id_cliente = :id_cliente
            AND m.id_estado_matriz = 2
            AND im.vencimiento_plazo IS NOT NULL
            AND im.vencimiento_plazo <= DATE_ADD(CURDATE(), INTERVAL :dias_limite DAY)
          ORDER BY im.vencimiento_plazo ASC";

$stmt = $db->prepare($query);
$stmt->bindParam(':id_cliente', $id_cliente, PDO::PARAM_INT);
$stmt->bindParam(':dias_limite', $dias_limite, PDO::PARAM_INT);
$stmt->execute();

$vencimientos = $stmt->fetchAll(PDO::FETCH_ASSOC);
http_response_code(200);
echo json_encode(["vencimientos" => $vencimientos]);
?>