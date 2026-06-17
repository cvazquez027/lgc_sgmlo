<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';
define('SCRAPER_API_KEY', 'Token_Seguro_Scraper_2026_XyZ!');

// Verificar API Key
$headers = apache_request_headers();
$auth_header = isset($headers['Authorization']) ? $headers['Authorization'] : '';
if (str_replace('Bearer ', '', $auth_header) !== SCRAPER_API_KEY) {
    http_response_code(401);
    echo json_encode(["status" => "error", "message" => "API Key inválida"]);
    exit();
}

$data = json_decode(file_get_contents("php://input"), true);
if (!isset($data['id_jurisdiccion']) || !isset($data['fecha_boletin'])) {
    http_response_code(400);
    echo json_encode(["status" => "error", "message" => "Faltan parámetros"]);
    exit();
}

$id_jurisdiccion = (int)$data['id_jurisdiccion'];
$fecha_boletin = $data['fecha_boletin']; // formato YYYY-MM-DD
$accion = $data['accion'] ?? 'verificar'; // 'verificar' o 'registrar'

$database = new Database();
$db = $database->getConnection();

if ($accion === 'verificar') {
    $query = "SELECT COUNT(*) as total FROM historial_scraping WHERE id_jurisdiccion = :id AND fecha_boletin = :fecha";
    $stmt = $db->prepare($query);
    $stmt->execute([':id' => $id_jurisdiccion, ':fecha' => $fecha_boletin]);
    $existe = (int)$stmt->fetchColumn() > 0;
    echo json_encode(["status" => "success", "procesado" => $existe]);
} elseif ($accion === 'registrar') {
    $cantidad = isset($data['cantidad_normas']) ? (int)$data['cantidad_normas'] : null;
    // Usamos INSERT IGNORE para evitar duplicados
    $query = "INSERT IGNORE INTO historial_scraping (id_jurisdiccion, fecha_boletin, cantidad_normas, fecha_procesamiento) 
              VALUES (:id, :fecha, :cant, NOW())";
    $stmt = $db->prepare($query);
    $stmt->execute([':id' => $id_jurisdiccion, ':fecha' => $fecha_boletin, ':cant' => $cantidad]);
    echo json_encode(["status" => "success", "message" => "Historial registrado"]);
} else {
    http_response_code(400);
    echo json_encode(["status" => "error", "message" => "Acción no válida"]);
}
?>