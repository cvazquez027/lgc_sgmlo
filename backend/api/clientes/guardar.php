<?php
// 1. CABECERAS DE SEGURIDAD Y CORS (El fix principal)
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS"); // Sumamos OPTIONS
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

// 2. INTERCEPCIÓN DEL PREFLIGHT (Escudo de seguridad CORS)
// Si el navegador solo está "preguntando" si puede pasar, le decimos que sí y cortamos la ejecución.
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
    
    // Capturamos el cuerpo de la petición
    $data = json_decode(file_get_contents("php://input"));

    // 3. VALIDACIÓN DE DATOS OBLIGATORIOS
    if(!empty($data->razon_social) && !empty($data->cuit)) {
        
        $cliente->id_cliente = $data->id_cliente ?? null;
        $cliente->cuit = $data->cuit;
        $cliente->razon_social = $data->razon_social;
        $cliente->nombre_fantasia = $data->nombre_fantasia ?? '';
        
        // Asignación segura del nuevo campo logo_path (si viene, lo sanitizamos)
        $cliente->logo_path = !empty($data->logo_path) ? htmlspecialchars(strip_tags($data->logo_path)) : null;
        
        $cliente->vigente = isset($data->vigente) ? (int)$data->vigente : 1;

        // 4. EJECUCIÓN DEL MODELO
        if($cliente->guardar()) {
            http_response_code(200);
            echo json_encode(["mensaje" => "Cliente procesado con éxito."]);
        } else {
            http_response_code(503);
            echo json_encode(["mensaje" => "Error al guardar el cliente en la base de datos."]);
        }
    } else {
        http_response_code(400);
        echo json_encode(["mensaje" => "Faltan datos obligatorios (CUIT o Razón Social)."]);
    }
} catch (Exception $e) {
    // 5. MANEJO DE ERRORES SEGURO
    http_response_code(500);
    echo json_encode([
        "mensaje" => "Error interno del servidor.", 
        "debug" => $e->getMessage() 
    ]);
}
?>