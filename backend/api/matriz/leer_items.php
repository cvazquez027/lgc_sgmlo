<?php
// Cabeceras CORS estandarizadas
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS, PUT, DELETE");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

// Responder al Preflight de los navegadores
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';

// CIBERSEGURIDAD: Validación estricta
$id_matriz = isset($_GET['id_matriz']) ? filter_var($_GET['id_matriz'], FILTER_VALIDATE_INT) : false;

if (!$id_matriz) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Se requiere el parámetro numérico 'id_matriz'."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    // 1. LEER CABECERA (Para obtener la config de columnas)
    $stmt_matriz = $db->prepare("SELECT config_columnas FROM matriz WHERE id_matriz = :id");
    $stmt_matriz->execute([':id' => $id_matriz]);
    $matriz_info = $stmt_matriz->fetch(PDO::FETCH_ASSOC);

    // 2. LEER ÍTEMS (Ordenados por la nueva columna 'orden')
    $query_items = "SELECT 
                        im.*, 
                        ec.descripcion as estado_cumplimiento_desc,
                        ec.color_hex,
                        tm.descripcion as tipo_modalidad_desc
                    FROM item_matriz im
                    LEFT JOIN estado_cumplimiento ec ON im.id_estado_cumplimiento = ec.id_estado_cumplimiento
                    LEFT JOIN tipo_modalidad tm ON im.id_tipo_modalidad = tm.id_tipo_modalidad
                    WHERE im.id_matriz = :id_matriz
                    ORDER BY im.orden ASC, im.id_item_matriz ASC";
    
    $stmt_items = $db->prepare($query_items);
    $stmt_items->execute([':id_matriz' => $id_matriz]);

    $items = [];

    // MODIFICACIÓN: Expandimos la consulta para traer el Emisor y la Jurisdicción (Nivel)
    $query_normas = "SELECT 
                        n.id_norma, 
                        n.numero, 
                        n.anio, 
                        tn.descripcion as tipo_norma,
                        en.descripcion as emisor_desc,
                        j.descripcion as jurisdiccion_desc,
                        nj.descripcion as nivel_jurisdiccion_desc
                     FROM item_matriz_norma imn
                     INNER JOIN norma n ON imn.id_norma = n.id_norma
                     LEFT JOIN tipo_norma tn ON n.id_tipo_norma = tn.id_tipo_norma
                     LEFT JOIN emisor_norma en ON n.id_emisor_norma = en.id_emisor_norma
                     LEFT JOIN jurisdiccion j ON en.id_jurisdiccion = j.id_jurisdiccion
                     LEFT JOIN nivel_jurisdiccion nj ON j.id_nivel_jurisdiccion = nj.id_nivel_jurisdiccion
                     WHERE imn.id_item_matriz = :id_item_matriz";
    
    $stmt_normas = $db->prepare($query_normas);

    $query_docs = "SELECT d.id_documentacion, d.nombre_original, d.path_archivos, d.tipo_mime, d.peso_bytes
                   FROM doc_item_matriz dim
                   INNER JOIN documentacion d ON dim.id_documentacion = d.id_documentacion
                   WHERE dim.id_item_matriz = :id_item_matriz AND d.vigente = 1";
    $stmt_docs = $db->prepare($query_docs);

    while ($row = $stmt_items->fetch(PDO::FETCH_ASSOC)) {
        $id_item = $row['id_item_matriz'];

        // Cargar Normas (Ahora con emisores y niveles)
        $stmt_normas->execute([':id_item_matriz' => $id_item]);
        $row['normas_vinculadas'] = $stmt_normas->fetchAll(PDO::FETCH_ASSOC);
        $row['normas_ids'] = array_column($row['normas_vinculadas'], 'id_norma');

        // Cargar Documentos
        $stmt_docs->execute([':id_item_matriz' => $id_item]);
        $row['documentos_vinculados'] = $stmt_docs->fetchAll(PDO::FETCH_ASSOC);
        $row['documentos_ids'] = array_column($row['documentos_vinculados'], 'id_documentacion');

        $items[] = $row;
    }

    http_response_code(200);
    echo json_encode([
        "mensaje" => "Datos recuperados.",
        "config_columnas" => $matriz_info['config_columnas'] ? json_decode($matriz_info['config_columnas']) : null,
        "total_items" => count($items),
        "registros" => $items
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno al leer los datos.", "debug" => $e->getMessage()]);
}
?>