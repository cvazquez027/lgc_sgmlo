<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';
define('SCRAPER_API_KEY', 'Token_Seguro_Scraper_2026_XyZ!');

// Ciberseguridad: Validamos que solo nuestro bot de Python pueda leer esto
$headers = apache_request_headers();
$auth_header = isset($headers['Authorization']) ? $headers['Authorization'] : '';
if (str_replace('Bearer ', '', $auth_header) !== SCRAPER_API_KEY) {
    http_response_code(401);
    echo json_encode(["mensaje" => "Acceso denegado al Bot."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    // Traemos las categorías vigentes. La descripción será nuestra palabra clave.
    $query = "SELECT id_categoria, descripcion FROM categoria WHERE vigente = 1";
    $stmt = $db->prepare($query);
    $stmt->execute();
    
    $registros = $stmt->fetchAll(PDO::FETCH_ASSOC);

    http_response_code(200);
    echo json_encode(["categorias" => $registros]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno.", "error" => $e->getMessage()]);
}
?>