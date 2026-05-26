<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }

include_once '../../config/Database.php';
$data = json_decode(file_get_contents("php://input"));

if (empty($data->id_documentacion)) { http_response_code(400); exit(); }

$database = new Database(); $db = $database->getConnection();

try {
    $stmt_find = $db->prepare("SELECT path_archivos FROM documentacion WHERE id_documentacion = :id");
    $stmt_find->execute([':id' => $data->id_documentacion]);
    $doc = $stmt_find->fetch(PDO::FETCH_ASSOC);
    
    if ($doc) {
        $ruta_fisica = "../../" . $doc['path_archivos'];
        if (file_exists($ruta_fisica)) unlink($ruta_fisica); 
        
        $stmt_del = $db->prepare("DELETE FROM documentacion WHERE id_documentacion = :id");
        $stmt_del->execute([':id' => $data->id_documentacion]);
        
        http_response_code(200); echo json_encode(["mensaje" => "Evidencia eliminada."]);
    } else {
        http_response_code(404); echo json_encode(["mensaje" => "No encontrado."]);
    }
} catch(Exception $e) {
    http_response_code(500); echo json_encode(["error" => $e->getMessage()]);
}
?>