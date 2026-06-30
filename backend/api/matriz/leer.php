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

$database = new Database();
$db = $database->getConnection();

$id_cliente_establecimiento = isset($_GET['id_cliente_establecimiento']) ? filter_var($_GET['id_cliente_establecimiento'], FILTER_VALIDATE_INT) : null;
$id_matriz = isset($_GET['id_matriz']) ? filter_var($_GET['id_matriz'], FILTER_VALIDATE_INT) : null;

try {
    // Agregamos el COUNT de items
    $query = "SELECT 
                m.id_matriz, 
                m.id_cliente_establecimiento, 
                m.id_tipo_matriz,
                m.id_especialidad_matriz,
                m.fecha_desde, 
                m.version, 
                m.id_estado_matriz, 
                m.vigente,
                m.mostrar_cumplimiento,
                m.campo_encabezado_item,
                m.columnas_editables_publicada, 
                em.descripcion as estado_matriz_desc,
                tm.descripcion as tipo_matriz_desc,
                esp.descripcion as especialidad_matriz_desc,
                ce.descripcion as establecimiento_desc,
                c.id_cliente,
                c.nombre_fantasia,
                c.logo_path,
                COUNT(im.id_item_matriz) as total_items
              FROM matriz m
              LEFT JOIN estado_matriz em ON m.id_estado_matriz = em.id_estado_matriz
              LEFT JOIN tipo_matriz tm ON m.id_tipo_matriz = tm.id_tipo_matriz
              LEFT JOIN especialidad_matriz esp ON m.id_especialidad_matriz = esp.id_especialidad_matriz
              LEFT JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
              LEFT JOIN cliente c ON ce.id_cliente = c.id_cliente
              LEFT JOIN item_matriz im ON m.id_matriz = im.id_matriz
              WHERE 1=1";

    if ($id_cliente_establecimiento) {
        $query .= " AND m.id_cliente_establecimiento = :id_cliente_establecimiento";
    }
    if ($id_matriz) {
        $query .= " AND m.id_matriz = :id_matriz";
    }

    $query .= " GROUP BY m.id_matriz ORDER BY m.fecha_desde DESC";
    $stmt = $db->prepare($query);

    if ($id_cliente_establecimiento) {
        $stmt->bindParam(":id_cliente_establecimiento", $id_cliente_establecimiento, PDO::PARAM_INT);
    }
    if ($id_matriz) {
        $stmt->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    }

    $stmt->execute();
    $registros = $stmt->fetchAll(PDO::FETCH_ASSOC);

    http_response_code(200);
    echo json_encode(["registros" => $registros]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al leer.", "error" => $e->getMessage()]);
}
?>