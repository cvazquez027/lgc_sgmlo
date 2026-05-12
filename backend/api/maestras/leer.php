<?php
// Cabeceras estrictas CORS y de tipo de contenido
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once dirname(__FILE__) . '/../../config/Database.php';

// 1. DICCIONARIO DE SEGURIDAD (Whitelist)
// Solo se pueden consultar estas tablas exactas, y solo se devuelven estas columnas.
$tablas_permitidas = [
    'rol' => ['id' => 'id_rol', 'cols' => 'id_rol, descripcion, vigente'],
    'permiso' => ['id' => 'id_permiso', 'cols' => 'id_permiso, descripcion, vigente'],
    'tipo_contacto' => ['id' => 'id_tipo_contacto', 'cols' => 'id_tipo_contacto, descripcion, vigente'],
    'tipo_norma' => ['id' => 'id_tipo_norma', 'cols' => 'id_tipo_norma, descripcion, vigente'],
    'estado_norma' => ['id' => 'id_estado_norma', 'cols' => 'id_estado_norma, descripcion, vigente'],
    'estado_matriz' => ['id' => 'id_estado_matriz', 'cols' => 'id_estado_matriz, descripcion, vigente'],
    'tipo_matriz' => ['id' => 'id_tipo_matriz', 'cols' => 'id_tipo_matriz, descripcion, vigente'], // <-- ¡AGREGADO AQUÍ!
    'estado_cumplimiento' => ['id' => 'id_estado_cumplimiento', 'cols' => 'id_estado_cumplimiento, descripcion, vigente'],
    'tipo_modalidad' => ['id' => 'id_tipo_modalidad', 'cols' => 'id_tipo_modalidad, descripcion'],
    'nivel_jurisdiccion' => ['id' => 'id_nivel_jurisdiccion', 'cols' => 'id_nivel_jurisdiccion, descripcion, nivel, vigente']
];

// Capturamos el parámetro sanitizado
$tabla_solicitada = isset($_GET['tabla']) ? preg_replace('/[^a-zA-Z_]/', '', $_GET['tabla']) : '';

// 2. VALIDACIÓN ESTRICTA
if (!array_key_exists($tabla_solicitada, $tablas_permitidas)) {
    http_response_code(403);
    echo json_encode(["mensaje" => "Acceso denegado: Operación no permitida o tabla inexistente."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();
$config = $tablas_permitidas[$tabla_solicitada];

try {
    // 3. CONSTRUCCIÓN SEGURA DE LA QUERY
    // Como $tabla_solicitada y $config['cols'] vienen directo de nuestro código duro, es 100% seguro.
    $query = "SELECT " . $config['cols'] . " FROM " . $tabla_solicitada . " ORDER BY descripcion ASC";
    
    $stmt = $db->prepare($query);
    $stmt->execute();
    
    $registros = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    http_response_code(200);
    echo json_encode([
        "tabla" => $tabla_solicitada,
        "registros" => $registros
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno del servidor al consultar la maestra."]);
}
?>