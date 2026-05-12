<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }
include_once '../../config/Database.php';

$data = json_decode(file_get_contents("php://input"));
if (empty($data->id_matriz) || !isset($data->columnas)) { http_response_code(400); exit(); }

$database = new Database(); $db = $database->getConnection();

try {
    $stmt = $db->prepare("UPDATE matriz SET config_columnas = :cols WHERE id_matriz = :id");
    $stmt->execute([':cols' => json_encode($data->columnas), ':id' => $data->id_matriz]);
    http_response_code(200); echo json_encode(["mensaje" => "Configuración guardada."]);
} catch (Exception $e) {
    http_response_code(500); echo json_encode(["error" => $e->getMessage()]);
}
?>