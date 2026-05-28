<?php
// Cabeceras CORS
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once dirname(__FILE__) . '/../../config/Database.php';

$database = new Database();
$db = $database->getConnection();

$data = json_decode(file_get_contents("php://input"));

// Validaciones básicas
if (empty($data->id_cliente) || empty($data->descripcion)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan datos obligatorios (id_cliente, descripcion)."]);
    exit;
}

try {
    $db->beginTransaction();

    $id_cliente = $data->id_cliente;
    $descripcion = $data->descripcion;
    $id_jurisdiccion = $data->id_jurisdiccion ?? null;
    $vigente = $data->vigente ?? 1;
    $contactos = $data->contactos ?? [];

    // Variable para almacenar el ID del establecimiento (nuevo o existente)
    $id_establecimiento = null;

    if (!empty($data->id_cliente_establecimiento)) {
        // === MODO EDICIÓN ===
        $id_establecimiento = $data->id_cliente_establecimiento;
        $query = "UPDATE cliente_establecimiento 
                  SET id_jurisdiccion = :ij, descripcion = :d, vigente = :v 
                  WHERE id_cliente_establecimiento = :id";
        $stmt = $db->prepare($query);
        $stmt->bindParam(':id', $id_establecimiento);
        $stmt->bindParam(':ij', $id_jurisdiccion);
        $stmt->bindParam(':d', $descripcion);
        $stmt->bindParam(':v', $vigente);
        $stmt->execute();
    } else {
        // === MODO CREACIÓN ===
        $query = "INSERT INTO cliente_establecimiento (id_cliente, id_jurisdiccion, descripcion, vigente) 
                  VALUES (:ic, :ij, :d, :v)";
        $stmt = $db->prepare($query);
        $stmt->bindParam(':ic', $id_cliente);
        $stmt->bindParam(':ij', $id_jurisdiccion);
        $stmt->bindParam(':d', $descripcion);
        $stmt->bindParam(':v', $vigente);
        $stmt->execute();
        $id_establecimiento = $db->lastInsertId();
    }

    // === GESTIÓN DE CONTACTOS ===
    // 1. Eliminar contactos existentes para este establecimiento
    $deleteQuery = "DELETE FROM datos_contacto 
                    WHERE id_cliente_establecimiento = :id_est 
                    AND id_cliente_establecimiento IS NOT NULL";
    $deleteStmt = $db->prepare($deleteQuery);
    $deleteStmt->bindParam(':id_est', $id_establecimiento);
    $deleteStmt->execute();

    // 2. Insertar los nuevos contactos (si vienen)
    if (!empty($contactos) && is_array($contactos)) {
        $insertQuery = "INSERT INTO datos_contacto 
                        (id_cliente, id_cliente_establecimiento, id_tipo_contacto, descripcion, vigente) 
                        VALUES (:id_cliente, :id_est, :id_tipo, :desc, 1)";
        $insertStmt = $db->prepare($insertQuery);
        
        foreach ($contactos as $contacto) {
            if (empty($contacto->id_tipo_contacto) || !isset($contacto->valor)) continue;
            
            $id_tipo = htmlspecialchars(strip_tags($contacto->id_tipo_contacto));
            $valor = htmlspecialchars(strip_tags($contacto->valor));
            
            $insertStmt->bindParam(':id_cliente', $id_cliente);
            $insertStmt->bindParam(':id_est', $id_establecimiento);
            $insertStmt->bindParam(':id_tipo', $id_tipo);
            $insertStmt->bindParam(':desc', $valor);
            $insertStmt->execute();
        }
    }

    $db->commit();
    http_response_code(200);
    echo json_encode(["mensaje" => "Establecimiento y contactos guardados correctamente."]);

} catch (Exception $e) {
    $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al guardar: " . $e->getMessage()]);
}
?>