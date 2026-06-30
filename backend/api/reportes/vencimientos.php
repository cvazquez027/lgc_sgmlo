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
include_once '../../config/JwtHandler.php';

// --- Extracción robusta del token ---
$token = '';
if (isset($_SERVER['HTTP_AUTHORIZATION'])) {
    $token = trim(str_ireplace('Bearer', '', $_SERVER['HTTP_AUTHORIZATION']));
} elseif (function_exists('apache_request_headers')) {
    $requestHeaders = apache_request_headers();
    $requestHeaders = array_combine(array_map('ucwords', array_keys($requestHeaders)), array_values($requestHeaders));
    if (isset($requestHeaders['Authorization'])) {
        $token = trim(str_ireplace('Bearer', '', $requestHeaders['Authorization']));
    }
} else {
    $headers = getallheaders();
    if (isset($headers['Authorization'])) {
        $token = trim(str_ireplace('Bearer', '', $headers['Authorization']));
    }
}

$jwt = new JwtHandler();
$payload = $jwt->verificar($token);
if (!$payload) {
    http_response_code(401);
    echo json_encode(["mensaje" => "No autorizado."]);
    exit();
}

$payload_array = (array) $payload;
$id_cliente = isset($payload_array['id_cliente']) ? $payload_array['id_cliente'] : null;
$rol = isset($payload_array['rol']) ? $payload_array['rol'] : null;
$es_admin = ($id_cliente === null) || ($rol === 'admin' || $rol === 'administrador');

$database = new Database();
$db = $database->getConnection();

try {
    // Construir consulta para obtener ítems con vencimiento de matrices publicadas
    $query = "SELECT 
                m.id_matriz,
                CONCAT(tm.descripcion, ' - ', em.descripcion, ' - ', ce.descripcion) AS nombre_matriz,
                im.id_item_matriz,
                im.resumen_legal,
                im.vencimiento_plazo,
                ec.descripcion AS estado_desc,
                ec.color_hex,
                DATEDIFF(im.vencimiento_plazo, CURDATE()) AS dias_restantes,
                -- Obtener el campo de encabezado según la configuración de la matriz
                CASE 
                    WHEN m.campo_encabezado_item = 'normas' THEN (
                        SELECT GROUP_CONCAT(CONCAT(tn.descripcion, ' ', n.numero, '/', n.anio) SEPARATOR ', ')
                        FROM item_matriz_norma imn
                        JOIN norma n ON imn.id_norma = n.id_norma
                        JOIN tipo_norma tn ON n.id_tipo_norma = tn.id_tipo_norma
                        WHERE imn.id_item_matriz = im.id_item_matriz
                    )
                    WHEN m.campo_encabezado_item IS NOT NULL AND m.campo_encabezado_item != '' THEN (
                        -- Para campos personalizados o específicos, se obtiene el valor de datos_dinamicos o columna directa
                        -- Simplificamos: si el campo es 'resumen_legal', lo usamos; si es 'custom_*', lo extraemos de datos_dinamicos
                        CASE 
                            WHEN m.campo_encabezado_item = 'resumen_legal' THEN im.resumen_legal
                            WHEN m.campo_encabezado_item LIKE 'custom_%' THEN JSON_UNQUOTE(JSON_EXTRACT(im.datos_dinamicos, CONCAT('$.\"', m.campo_encabezado_item, '\"')))
                            ELSE NULL
                        END
                    )
                    ELSE im.resumen_legal
                END AS item_resumen
              FROM item_matriz im
              JOIN matriz m ON im.id_matriz = m.id_matriz
              JOIN tipo_matriz tm ON m.id_tipo_matriz = tm.id_tipo_matriz
              JOIN especialidad_matriz em ON m.id_especialidad_matriz = em.id_especialidad_matriz
              JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
              LEFT JOIN estado_cumplimiento ec ON im.id_estado_cumplimiento = ec.id_estado_cumplimiento
              WHERE m.id_estado_matriz = 2
                AND im.vencimiento_plazo IS NOT NULL";

    $params = [];

    if (!$es_admin) {
        if (!$id_cliente) {
            http_response_code(200);
            echo json_encode(["vencimientos" => []]);
            exit();
        }
        // Cliente: solo sus matrices
        $query .= " AND ce.id_cliente = :id_cliente";
        $params[':id_cliente'] = $id_cliente;
    } else {
        // Admin: puede filtrar por cliente si se pasa en GET
        if (isset($_GET['id_cliente']) && $_GET['id_cliente'] !== '') {
            $query .= " AND ce.id_cliente = :filtro_cliente";
            $params[':filtro_cliente'] = (int)$_GET['id_cliente'];
        }
    }

    // Ordenar por días restantes (primero los más urgentes)
    $query .= " ORDER BY dias_restantes ASC";

    $stmt = $db->prepare($query);
    foreach ($params as $key => $value) {
        $stmt->bindValue($key, $value);
    }
    $stmt->execute();

    $vencimientos = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // Limpiar valores nulos y formatear
    foreach ($vencimientos as &$v) {
        if ($v['item_resumen'] === null) {
            $v['item_resumen'] = $v['resumen_legal'] ?: 'Ítem sin descripción';
        }
        unset($v['resumen_legal']); // ya no lo necesitamos
    }

    http_response_code(200);
    echo json_encode(["vencimientos" => $vencimientos]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al obtener vencimientos.", "error" => $e->getMessage()]);
}
?>