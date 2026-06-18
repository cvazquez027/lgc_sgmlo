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

$data = json_decode(file_get_contents("php://input"));
if (empty($data->id_jurisdiccion)) {
    http_response_code(400);
    echo json_encode(["status" => "error", "message" => "Falta id_jurisdiccion"]);
    exit();
}

$id_jurisdiccion = (int)$data->id_jurisdiccion;

$database = new Database();
$db = $database->getConnection();

$query = "SELECT descripcion, url_boletin, tiene_scraper, nombre_bot FROM jurisdiccion WHERE id_jurisdiccion = :id";
$stmt = $db->prepare($query);
$stmt->execute([':id' => $id_jurisdiccion]);
$jur = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$jur || $jur['tiene_scraper'] != 1) {
    http_response_code(400);
    echo json_encode(["status" => "error", "message" => "Jurisdicción no válida o sin scraper habilitado."]);
    exit();
}

$nombre_script = $jur['nombre_bot'];
if (!$nombre_script) {
    http_response_code(404);
    echo json_encode(["status" => "error", "message" => "La jurisdicción no tiene un script asignado (campo nombre_bot nulo)."]);
    exit();
}

//Prueba
$ruta_base = dirname(__FILE__) . '/../../scripts/';
$ruta_script = $ruta_base . $nombre_script;

if (!file_exists($ruta_script)) {
    http_response_code(404);
    echo json_encode(["status" => "error", "message" => "No se encontró el script '$nombre_script' para esta jurisdicción."]);
    exit();
}

// Ejecutar script
chdir($ruta_base);
$comando = "/usr/bin/python3 " . escapeshellarg($nombre_script) . " " . escapeshellarg($id_jurisdiccion) . " " . escapeshellarg($jur['url_boletin']) . " 2>&1";
$salida = shell_exec($comando);

// Intentar decodificar la salida como JSON
$resultado = json_decode($salida, true);
if (json_last_error() === JSON_ERROR_NONE) {
    echo json_encode($resultado);
} else {
    // Si no es JSON, devolver error con el texto crudo (pero asegurar JSON)
    echo json_encode(["status" => "error", "message" => "El script no devolvió JSON válido.", "raw" => $salida]);
}
?>