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

$database = new Database();
$db = $database->getConnection();

$id_cliente = isset($_GET['id_cliente']) ? $_GET['id_cliente'] : null;

if (!$id_cliente) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Falta el ID del cliente."]);
    exit;
}

try {
    // 1. Obtener los establecimientos base
    $query = "SELECT ce.id_cliente_establecimiento, ce.id_cliente, ce.id_jurisdiccion, 
                     j.descripcion AS jurisdiccion_nombre, ce.descripcion, ce.vigente
              FROM cliente_establecimiento ce
              LEFT JOIN jurisdiccion j ON ce.id_jurisdiccion = j.id_jurisdiccion
              WHERE ce.id_cliente = :id_cliente
              ORDER BY ce.descripcion ASC";
    $stmt = $db->prepare($query);
    $stmt->bindParam(':id_cliente', $id_cliente);
    $stmt->execute();

    $establecimientos = [];
    $ids = [];

    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $ids[] = $row['id_cliente_establecimiento'];
        $establecimientos[$row['id_cliente_establecimiento']] = [
            "id_cliente_establecimiento" => $row['id_cliente_establecimiento'],
            "id_cliente" => $row['id_cliente'],
            "id_jurisdiccion" => $row['id_jurisdiccion'],
            "jurisdiccion_nombre" => $row['jurisdiccion_nombre'],
            "descripcion" => html_entity_decode($row['descripcion']),
            "vigente" => $row['vigente'],
            "contactos" => [], // Inicializar array de contactos
            "categorias" => [] // <-- NUEVO: array de categorías
        ];
    }

    // 2. Si hay establecimientos, obtener sus contactos
    if (!empty($ids)) {
        $placeholders = implode(',', array_fill(0, count($ids), '?'));
        
        // Contactos
        $queryContactos = "SELECT id_cliente_establecimiento, id_tipo_contacto, descripcion 
                           FROM datos_contacto 
                           WHERE id_cliente_establecimiento IN ($placeholders) 
                           AND id_cliente_establecimiento IS NOT NULL";
        $stmtContactos = $db->prepare($queryContactos);
        $stmtContactos->execute($ids);
        while ($contacto = $stmtContactos->fetch(PDO::FETCH_ASSOC)) {
            $idEst = $contacto['id_cliente_establecimiento'];
            if (isset($establecimientos[$idEst])) {
                $establecimientos[$idEst]['contactos'][] = [
                    'id_tipo_contacto' => $contacto['id_tipo_contacto'],
                    'valor' => $contacto['descripcion']
                ];
            }
        }

        // Categorías
        $queryCategorias = "SELECT ec.id_cliente_establecimiento, c.id_categoria, c.descripcion
                            FROM categoria_cliente_establecimiento ec
                            JOIN categoria c ON ec.id_categoria = c.id_categoria
                            WHERE ec.id_cliente_establecimiento IN ($placeholders)
                            ORDER BY c.descripcion ASC";
        $stmtCats = $db->prepare($queryCategorias);
        $stmtCats->execute($ids);
        while ($cat = $stmtCats->fetch(PDO::FETCH_ASSOC)) {
            $idEst = $cat['id_cliente_establecimiento'];
            if (isset($establecimientos[$idEst])) {
                $establecimientos[$idEst]['categorias'][] = [
                    'id_categoria' => $cat['id_categoria'],
                    'descripcion' => $cat['descripcion']
                ];
            }
        }
    }

    http_response_code(200);
    echo json_encode(["registros" => array_values($establecimientos)]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al leer establecimientos.", "debug" => $e->getMessage()]);
}
?>