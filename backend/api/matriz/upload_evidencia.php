<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }

include_once '../../config/Database.php';
include_once '../../config/JwtHandler.php';
include_once '../../helpers/AlertaHelper.php';

// --- 1. Validación de archivo y parámetros ---
if (!isset($_FILES['archivo']) || empty($_POST['id_item_matriz'])) {
    http_response_code(400); echo json_encode(["mensaje" => "Faltan parámetros o el archivo."]); exit();
}

$id_item_matriz = (int)$_POST['id_item_matriz'];
$archivo = $_FILES['archivo'];

// --- 2. Extraer usuario del token JWT ---
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
$id_usuario = isset($payload_array['id_usuario']) ? (int)$payload_array['id_usuario'] : null;
$id_cliente = isset($payload_array['id_cliente']) ? $payload_array['id_cliente'] : null;

if (!$id_usuario) {
    http_response_code(403);
    echo json_encode(["mensaje" => "No se pudo identificar al usuario."]);
    exit();
}

// --- 3. Procesar archivo ---
$directorio_destino = "../../uploads/evidencias/";
if (!is_dir($directorio_destino)) mkdir($directorio_destino, 0777, true);

$extension = pathinfo($archivo['name'], PATHINFO_EXTENSION);
$nombre_fisico = "ev_" . time() . "_" . uniqid() . "." . $extension;
$ruta_completa = $directorio_destino . $nombre_fisico;
$ruta_db = "uploads/evidencias/" . $nombre_fisico;

if (!move_uploaded_file($archivo['tmp_name'], $ruta_completa)) {
    http_response_code(500); echo json_encode(["mensaje" => "Error de disco al mover archivo."]); exit();
}

// --- 4. Guardar en base de datos ---
$database = new Database();
$db = $database->getConnection();

try {
    $db->beginTransaction();

    // 4.1 Verificar que el ítem y su matriz existan, y si la matriz está publicada
    $query_estado = "SELECT m.id_matriz, m.id_cliente_establecimiento, m.id_estado_matriz, ce.id_cliente, m.campo_encabezado_item
                     FROM item_matriz im
                     JOIN matriz m ON im.id_matriz = m.id_matriz
                     JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
                     WHERE im.id_item_matriz = :id_item";
    $stmt_estado = $db->prepare($query_estado);
    $stmt_estado->execute([':id_item' => $id_item_matriz]);
    $info = $stmt_estado->fetch(PDO::FETCH_ASSOC);

    if (!$info) {
        throw new Exception("El ítem no existe.");
    }

    $matriz_publicada = ($info['id_estado_matriz'] == 2);
    $id_cliente = $info['id_cliente'];
    $id_matriz = $info['id_matriz'];
    $campo_encabezado = $info['campo_encabezado_item'] ?? 'resumen_legal';

    // 4.2 Insertar documentación
    $stmt_doc = $db->prepare("INSERT INTO documentacion (path_archivos, nombre_original, tipo_mime, peso_bytes, id_usuario_subida) VALUES (:ruta, :nombre, :mime, :peso, :user)");
    $stmt_doc->execute([
        ':ruta' => $ruta_db,
        ':nombre' => $archivo['name'],
        ':mime' => $archivo['type'],
        ':peso' => $archivo['size'],
        ':user' => $id_usuario
    ]);
    $id_doc = $db->lastInsertId();

    // 4.3 Vincular con el ítem
    $stmt_link = $db->prepare("INSERT INTO doc_item_matriz (id_documentacion, id_item_matriz) VALUES (:id_doc, :id_item)");
    $stmt_link->execute([':id_doc' => $id_doc, ':id_item' => $id_item_matriz]);

    // 4.4 Disparador de alerta SOLO si la matriz está publicada
    if ($matriz_publicada && $id_cliente) {
        // Obtener nombre descriptivo de la matriz
        $query_nombre = "SELECT CONCAT(tm.descripcion, ' - ', em.descripcion, ' - ', ce.descripcion) as nombre_matriz
                         FROM matriz m
                         JOIN tipo_matriz tm ON m.id_tipo_matriz = tm.id_tipo_matriz
                         JOIN especialidad_matriz em ON m.id_especialidad_matriz = em.id_especialidad_matriz
                         JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
                         WHERE m.id_matriz = :id_matriz";
        $stmt_nombre = $db->prepare($query_nombre);
        $stmt_nombre->execute([':id_matriz' => $id_matriz]);
        $nombre_matriz = $stmt_nombre->fetchColumn();
        $nombre_matriz = $nombre_matriz ?: "Matriz ID $id_matriz";

        // Obtener descripción del ítem
        $query_item_desc = "SELECT resumen_legal, datos_dinamicos FROM item_matriz WHERE id_item_matriz = :id_item";
        $stmt_desc = $db->prepare($query_item_desc);
        $stmt_desc->execute([':id_item' => $id_item_matriz]);
        $item_data = $stmt_desc->fetch(PDO::FETCH_ASSOC);

        $descripcion_item = '';
        if ($campo_encabezado === 'normas') {
            $query_normas = "SELECT CONCAT(tn.descripcion, ' ', n.numero, '/', n.anio) AS norma_text
                             FROM item_matriz_norma imn
                             JOIN norma n ON imn.id_norma = n.id_norma
                             JOIN tipo_norma tn ON n.id_tipo_norma = tn.id_tipo_norma
                             WHERE imn.id_item_matriz = :id_item";
            $stmt_normas = $db->prepare($query_normas);
            $stmt_normas->execute([':id_item' => $id_item_matriz]);
            $normas = $stmt_normas->fetchAll(PDO::FETCH_COLUMN);
            $descripcion_item = implode(', ', $normas);
        } elseif ($campo_encabezado === 'resumen_legal') {
            $descripcion_item = $item_data['resumen_legal'];
        } elseif (strpos($campo_encabezado, 'custom_') === 0) {
            $dinamicos = json_decode($item_data['datos_dinamicos'], true);
            $descripcion_item = isset($dinamicos[$campo_encabezado]) ? $dinamicos[$campo_encabezado] : $item_data['resumen_legal'];
        } else {
            $descripcion_item = $item_data[$campo_encabezado] ?? $item_data['resumen_legal'];
        }
        if (empty($descripcion_item)) {
            $descripcion_item = $item_data['resumen_legal'] ?: 'ítem sin resumen';
        }

        $titulo = "Nuevo documento subido";
        $mensaje = "Se ha subido un nuevo documento al ítem \"{$descripcion_item}\" de la matriz \"{$nombre_matriz}\".";
        $url = "/dashboard/matrices/{$id_matriz}?item={$id_item_matriz}";

        AlertaHelper::insertarAlerta($db, $id_cliente, $id_matriz, $id_item_matriz, 'documento_nuevo', $titulo, $mensaje, $url);
    }

    $db->commit();
    http_response_code(200);
    echo json_encode(["mensaje" => "Evidencia subida correctamente."]);

} catch (Exception $e) {
    $db->rollBack();
    if (file_exists($ruta_completa)) unlink($ruta_completa);
    http_response_code(500);
    echo json_encode(["error" => $e->getMessage()]);
}