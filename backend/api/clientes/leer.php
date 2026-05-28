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
include_once '../../models/Cliente.php';

try {
    $database = new Database();
    $db = $database->getConnection();
    $cliente = new Cliente($db);

    $clientesArray = $cliente->leer(); // ahora devuelve un array de clientes con sus contactos

    $respuesta = [
        "registros" => array_values($clientesArray) // Convertir a lista simple
    ];

    http_response_code(200);
    echo json_encode($respuesta);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        "mensaje" => "Error interno al leer el listado de clientes.",
        "debug" => $e->getMessage()
    ]);
}
?>