<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST");
header("Access-Control-Allow-Headers: Content-Type, Authorization");

include_once dirname(__FILE__) . '/../../config/Database.php';

$database = new Database();
$db = $database->getConnection();
$data = json_decode(file_get_contents("php://input"));

if(!empty($data->id_cliente) && !empty($data->descripcion)) {
    try {
        if (!empty($data->id_cliente_establecimiento)) {
            $query = "UPDATE cliente_establecimiento SET id_jurisdiccion=:ij, descripcion=:d, vigente=:v WHERE id_cliente_establecimiento=:id";
            $stmt = $db->prepare($query);
            $stmt->bindParam(':id', $data->id_cliente_establecimiento);
        } else {
            $query = "INSERT INTO cliente_establecimiento (id_cliente, id_jurisdiccion, descripcion, vigente) VALUES (:ic, :ij, :d, :v)";
            $stmt = $db->prepare($query);
            $stmt->bindParam(':ic', $data->id_cliente);
        }
        
        $stmt->bindParam(':ij', $data->id_jurisdiccion);
        $stmt->bindParam(':d', $data->descripcion);
        $stmt->bindParam(':v', $data->vigente);

        if($stmt->execute()) {
            echo json_encode(["mensaje" => "Establecimiento guardado."]);
        }
    } catch (Exception $e) {
        http_response_code(500);
        echo json_encode(["mensaje" => "Error: " . $e->getMessage()]);
    }
}