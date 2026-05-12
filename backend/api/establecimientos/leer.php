<?php
// 1. Cabeceras CORS Completas
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

// 2. Atajar la petición Pre-flight (OPTIONS)
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once dirname(__FILE__) . '/../../config/Database.php';
include_once dirname(__FILE__) . '/../../models/Establecimiento.php';

$database = new Database();
$db = $database->getConnection();
$establecimiento = new Establecimiento($db);

$id_cliente = isset($_GET['id_cliente']) ? $_GET['id_cliente'] : null;

if ($id_cliente) {
    $stmt = $establecimiento->leerPorCliente($id_cliente);
    $establecimientos_arr = array();
    $establecimientos_arr["registros"] = array();

    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        extract($row);
        $item = array(
            "id_cliente_establecimiento" => $id_cliente_establecimiento,
            "id_cliente" => $id_cliente,
            "id_jurisdiccion" => $id_jurisdiccion,
            "jurisdiccion_nombre" => $jurisdiccion_nombre,
            "descripcion" => html_entity_decode($descripcion),
            "vigente" => $vigente
        );
        array_push($establecimientos_arr["registros"], $item);
    }

    http_response_code(200);
    echo json_encode($establecimientos_arr);
} else {
    http_response_code(400);
    echo json_encode(["mensaje" => "Falta el ID del cliente."]);
}