<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }

include_once '../../config/Database.php';
include_once '../../config/JwtHandler.php';

// ---------------------------------------------------------
// EXTRACCIÓN ROBUSTA DEL TOKEN
// ---------------------------------------------------------
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
if (!$jwt->verificar($token)) { 
    http_response_code(401); 
    echo json_encode(["mensaje" => "No autorizado. Token inválido, expirado o ausente."]); 
    exit(); 
}

$data = json_decode(file_get_contents("php://input"));
$id_origen = !empty($data->id_matriz) ? (int)filter_var($data->id_matriz, FILTER_VALIDATE_INT) : 0;
if (!$id_origen) { http_response_code(400); echo json_encode(["mensaje" => "id_matriz requerido"]); exit(); }

$database = new Database();
$db = $database->getConnection();

try {
    $db->beginTransaction();

    // 1. Leer cabecera de la matriz origen (incluyendo TODOS los campos de configuración)
    $stmt_cab = $db->prepare(
        "SELECT id_cliente_establecimiento, id_tipo_matriz, id_especialidad_matriz,
                fecha_desde, config_columnas, version, mostrar_cumplimiento, 
                campo_encabezado_item, columnas_editables_publicada
         FROM matriz WHERE id_matriz = :id"
    );
    $stmt_cab->execute([':id' => $id_origen]);
    $origen = $stmt_cab->fetch(PDO::FETCH_ASSOC);
    if (!$origen) throw new Exception("Matriz origen no encontrada.");

    // --- VALIDACIÓN: Ya existe un borrador con la misma combinación? ---
    $query_check = "SELECT COUNT(*) FROM matriz 
                    WHERE id_cliente_establecimiento = :est
                      AND id_especialidad_matriz = :esp
                      AND id_tipo_matriz = :tipo
                      AND id_estado_matriz = 1
                      AND id_matriz != :id_origen";
    $stmt_check = $db->prepare($query_check);
    $stmt_check->execute([
        ':est' => $origen['id_cliente_establecimiento'],
        ':esp' => $origen['id_especialidad_matriz'],
        ':tipo' => $origen['id_tipo_matriz'],
        ':id_origen' => $id_origen
    ]);
    $existeBorrador = $stmt_check->fetchColumn();

    if ($existeBorrador > 0) {
        $db->rollBack();
        http_response_code(409);
        echo json_encode(["mensaje" => "No se puede copiar la matriz porque ya existe una versión en estado BORRADOR para la misma combinación de establecimiento, especialidad y tipo. Elimine o publique ese borrador antes de crear una nueva versión."]);
        exit();
    }

    // 2. Calcular próxima versión
    $stmt_ver = $db->prepare(
        "SELECT COALESCE(MAX(version), 0) + 1 AS siguiente
         FROM matriz
         WHERE id_cliente_establecimiento = :est
           AND id_tipo_matriz = :tipo
           AND id_especialidad_matriz = :esp"
    );
    $stmt_ver->execute([
        ':est' => $origen['id_cliente_establecimiento'],
        ':tipo' => $origen['id_tipo_matriz'],
        ':esp'  => $origen['id_especialidad_matriz']
    ]);
    $nueva_version = (int)$stmt_ver->fetchColumn();

    // 3. Valores por defecto para la configuración (por si vienen nulos)
    $config_columnas = $origen['config_columnas'] ?? '[]';
    $mostrar_cumplimiento = isset($origen['mostrar_cumplimiento']) ? (int)$origen['mostrar_cumplimiento'] : 1;
    $campo_encabezado_item = $origen['campo_encabezado_item'] ?? 'normas';
    $columnas_editables_publicada = $origen['columnas_editables_publicada'] ?? '[]';

    // 4. Insertar nueva cabecera en estado BORRADOR con TODA la configuración
    $stmt_nueva = $db->prepare(
        "INSERT INTO matriz
            (id_cliente_establecimiento, id_tipo_matriz, id_especialidad_matriz,
             fecha_desde, version, id_estado_matriz, vigente, config_columnas,
             mostrar_cumplimiento, campo_encabezado_item, columnas_editables_publicada)
         VALUES
            (:est, :tipo, :esp, :fecha, :ver, 1, 1, :config,
             :mostrar_cumplimiento, :campo_encabezado, :columnas_editables)"
    );
    $stmt_nueva->execute([
        ':est'    => $origen['id_cliente_establecimiento'],
        ':tipo'   => $origen['id_tipo_matriz'],
        ':esp'    => $origen['id_especialidad_matriz'],
        ':fecha'  => date('Y-m-d'),
        ':ver'    => $nueva_version,
        ':config' => $config_columnas,
        ':mostrar_cumplimiento' => $mostrar_cumplimiento,
        ':campo_encabezado' => $campo_encabezado_item,
        ':columnas_editables' => $columnas_editables_publicada
    ]);
    $id_nueva = (int)$db->lastInsertId();

    // 5. Copiar todos los ítems (incluyendo datos_dinamicos)
    $stmt_items = $db->prepare(
        "SELECT * FROM item_matriz WHERE id_matriz = :id ORDER BY orden ASC, id_item_matriz ASC"
    );
    $stmt_items->execute([':id' => $id_origen]);
    $items = $stmt_items->fetchAll(PDO::FETCH_ASSOC);

    $stmt_ins_item = $db->prepare(
        "INSERT INTO item_matriz
            (id_matriz, orden, resumen_legal, articulos_aplicables, interpretacion_aplicacion,
             id_tipo_modalidad, obs_modalidad, vencimiento_plazo, fecha_cumplimiento,
             evidencia_cumplimiento, verificacion_cumplimiento, id_estado_cumplimiento,
             obs_estado_cumplimiento, id_responsable_establecimiento, datos_dinamicos)
         VALUES
            (:id_matriz, :orden, :resumen_legal, :articulos_aplicables, :interpretacion_aplicacion,
             :id_tipo_modalidad, :obs_modalidad, :vencimiento_plazo, :fecha_cumplimiento,
             :evidencia_cumplimiento, :verificacion_cumplimiento, :id_estado_cumplimiento,
             :obs_estado_cumplimiento, :id_responsable_establecimiento, :datos_dinamicos)"
    );

    $stmt_leer_normas = $db->prepare(
        "SELECT id_norma FROM item_matriz_norma WHERE id_item_matriz = :id_item"
    );
    $stmt_ins_norma = $db->prepare(
        "INSERT INTO item_matriz_norma (id_item_matriz, id_norma) VALUES (:id_item, :id_norma)"
    );

    foreach ($items as $item) {
        $stmt_ins_item->execute([
            ':id_matriz'                    => $id_nueva,
            ':orden'                        => $item['orden'],
            ':resumen_legal'                => $item['resumen_legal'],
            ':articulos_aplicables'         => $item['articulos_aplicables'],
            ':interpretacion_aplicacion'    => $item['interpretacion_aplicacion'],
            ':id_tipo_modalidad'            => $item['id_tipo_modalidad'],
            ':obs_modalidad'                => $item['obs_modalidad'],
            ':vencimiento_plazo'            => $item['vencimiento_plazo'],
            ':fecha_cumplimiento'           => $item['fecha_cumplimiento'],
            ':evidencia_cumplimiento'       => $item['evidencia_cumplimiento'],
            ':verificacion_cumplimiento'    => $item['verificacion_cumplimiento'],
            ':id_estado_cumplimiento'       => $item['id_estado_cumplimiento'],
            ':obs_estado_cumplimiento'      => $item['obs_estado_cumplimiento'],
            ':id_responsable_establecimiento' => $item['id_responsable_establecimiento'],
            ':datos_dinamicos'              => $item['datos_dinamicos']
        ]);
        $id_nuevo_item = (int)$db->lastInsertId();

        // Copiar normas vinculadas
        $stmt_leer_normas->execute([':id_item' => $item['id_item_matriz']]);
        $normas = $stmt_leer_normas->fetchAll(PDO::FETCH_COLUMN);
        foreach ($normas as $id_norma) {
            $stmt_ins_norma->execute([':id_item' => $id_nuevo_item, ':id_norma' => $id_norma]);
        }
    }

    $db->commit();
    http_response_code(200);
    echo json_encode([
        "ok"        => true,
        "id_matriz" => $id_nueva,
        "version"   => $nueva_version,
        "mensaje"   => "Nueva versión creada en borrador (v{$nueva_version})."
    ]);

} catch (Exception $e) {
    if ($db->inTransaction()) $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno al copiar.", "error" => $e->getMessage()]);
}
?>