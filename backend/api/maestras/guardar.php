<?php
// Cabeceras estrictas CORS
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once dirname(__FILE__) . '/../../config/Database.php';

// 1. DICCIONARIO DE SEGURIDAD (Lista Blanca)
// Define estrictamente las tablas permitidas y sus columnas de ID y Descripción
$tablas_permitidas = [
    'rol' => ['id' => 'id_rol', 'desc' => 'descripcion'],
    'tipo_contacto' => ['id' => 'id_tipo_contacto', 'desc' => 'descripcion'],
    'tipo_norma' => ['id' => 'id_tipo_norma', 'desc' => 'descripcion'],
    'estado_norma' => ['id' => 'id_estado_norma', 'desc' => 'descripcion'],
    'estado_matriz' => ['id' => 'id_estado_matriz', 'desc' => 'descripcion'],
    'estado_cumplimiento' => ['id' => 'id_estado_cumplimiento', 'desc' => 'descripcion'],
    'tipo_modalidad' => ['id' => 'id_tipo_modalidad', 'desc' => 'descripcion'],
    'permiso' => ['id' => 'id_permiso', 'desc' => 'nombre_permiso'] // Tabla con nombre de columna especial
];

// 2. OBTENER Y SANITIZAR DATOS DEL FRONTEND
$data = json_decode(file_get_contents("php://input"));

// Sanitizamos el nombre de la tabla (solo letras y guión bajo)
$tabla_solicitada = isset($data->tabla) ? preg_replace('/[^a-z_]/', '', $data->tabla) : '';

// Verificamos que la tabla exista en nuestra Lista Blanca
if (!array_key_exists($tabla_solicitada, $tablas_permitidas)) {
    http_response_code(403);
    echo json_encode(["mensaje" => "Acceso denegado: Tabla no autorizada para ABM dinámico."]);
    exit();
}

// Extraemos la configuración de la tabla
$config = $tablas_permitidas[$tabla_solicitada];
$campo_id = $config['id'];
$campo_desc = $config['desc'];

// Validamos que venga la descripción (es obligatoria)
if (!isset($data->$campo_desc) || trim($data->$campo_desc) === '') {
    http_response_code(400);
    echo json_encode(["mensaje" => "La descripción o nombre es obligatorio."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

$id_valor = isset($data->$campo_id) && $data->$campo_id !== "" ? (int)$data->$campo_id : null;
$desc_valor = htmlspecialchars(strip_tags(trim($data->$campo_desc))); // Limpieza XSS
$vigente_valor = isset($data->vigente) ? (int)$data->vigente : 1;

try {
    // 3. LÓGICA DE UPSERT (Insertar o Actualizar)
    if ($id_valor) {
        // MODO EDICIÓN (UPDATE)
        // Construimos la query usando los nombres de tabla/columnas aprobados por la Lista Blanca
        $query = "UPDATE " . $tabla_solicitada . " 
                  SET " . $campo_desc . " = :desc, vigente = :vigente 
                  WHERE " . $campo_id . " = :id";
        
        $stmt = $db->prepare($query);
        $stmt->bindParam(":desc", $desc_valor, PDO::PARAM_STR);
        $stmt->bindParam(":vigente", $vigente_valor, PDO::PARAM_INT);
        $stmt->bindParam(":id", $id_valor, PDO::PARAM_INT);
        
        $mensaje_exito = "Registro actualizado correctamente.";

    } else {
        // MODO CREACIÓN (INSERT)
        $query = "INSERT INTO " . $tabla_solicitada . " (" . $campo_desc . ", vigente) 
                  VALUES (:desc, :vigente)";
                  
        $stmt = $db->prepare($query);
        $stmt->bindParam(":desc", $desc_valor, PDO::PARAM_STR);
        $stmt->bindParam(":vigente", $vigente_valor, PDO::PARAM_INT);
        
        $mensaje_exito = "Registro creado correctamente.";
    }

    // 4. EJECUCIÓN
    if ($stmt->execute()) {
        http_response_code(200);
        echo json_encode(["mensaje" => $mensaje_exito]);
    } else {
        throw new Exception("Error al ejecutar la sentencia en la base de datos.");
    }

} catch (Exception $e) {
    http_response_code(500);
    // Para producción se recomienda no exponer $e->getMessage() directamente
    echo json_encode(["mensaje" => "Error interno del servidor al guardar el registro."]);
}
?>