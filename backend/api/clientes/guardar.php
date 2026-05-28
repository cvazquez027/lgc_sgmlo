<?php
// 1. CABECERAS DE SEGURIDAD Y CORS
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';
include_once '../../models/Cliente.php';

try {
    $database = new Database();
    $db = $database->getConnection();
    $cliente = new Cliente($db);
    
    $data = json_decode(file_get_contents("php://input"));

    if(!empty($data->razon_social) && !empty($data->cuit)) {
        
        $cliente->id_cliente = $data->id_cliente ?? null;
        $cliente->cuit = $data->cuit;
        $cliente->razon_social = $data->razon_social;
        $cliente->nombre_fantasia = $data->nombre_fantasia ?? '';
        $cliente->logo_path = !empty($data->logo_path) ? htmlspecialchars(strip_tags($data->logo_path)) : null;
        $cliente->vigente = isset($data->vigente) ? (int)$data->vigente : 1;
        
        // ---------- NUEVO: Asignar los contactos ----------
        $cliente->contactos = $data->contactos ?? [];
        // ------------------------------------------------

        if($cliente->guardar()) {
            http_response_code(200);
            echo json_encode(["mensaje" => "Cliente y contactos procesados con éxito."]);
        } else {
            http_response_code(503);
            echo json_encode(["mensaje" => "Error al guardar el cliente o sus contactos."]);
        }
    } else {
        http_response_code(400);
        echo json_encode(["mensaje" => "Faltan datos obligatorios (CUIT o Razón Social)."]);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        "mensaje" => "Error interno del servidor.", 
        "debug" => $e->getMessage() 
    ]);
}
?>