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

// Genera la clave_normalizada a partir de la descripción del emisor:
// todo minúscula, sin tildes/diacríticos, sin signos de puntuación, espacios simples.
// Se calcula SIEMPRE en el servidor (nunca se confía en un valor enviado por el cliente)
// para garantizar consistencia y evitar que se manipule vía payload.
function normalizarClave($texto) {
    $texto = mb_strtolower(trim($texto), 'UTF-8');
    $mapaAcentos = [
        'á' => 'a', 'à' => 'a', 'ä' => 'a', 'â' => 'a', 'ã' => 'a',
        'é' => 'e', 'è' => 'e', 'ë' => 'e', 'ê' => 'e',
        'í' => 'i', 'ì' => 'i', 'ï' => 'i', 'î' => 'i',
        'ó' => 'o', 'ò' => 'o', 'ö' => 'o', 'ô' => 'o', 'õ' => 'o',
        'ú' => 'u', 'ù' => 'u', 'ü' => 'u', 'û' => 'u',
        'ñ' => 'n', 'ç' => 'c'
    ];
    $texto = strtr($texto, $mapaAcentos);
    $texto = preg_replace('/[^a-z0-9\s]/', '', $texto); // saca comas, puntos, etc.
    $texto = preg_replace('/\s+/', ' ', $texto);          // colapsa espacios múltiples
    return trim($texto);
}

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
    'permiso' => ['id' => 'id_permiso', 'desc' => 'nombre_permiso']
];

// Tablas que NO tienen el campo 'vigente' (incluyendo tipo_modalidad)
$tablas_sin_vigente = ['emisor_norma', 'tipo_modalidad'];

// 2. OBTENER Y SANITIZAR DATOS DEL FRONTEND
$data = json_decode(file_get_contents("php://input"));

// Sanitizamos el nombre de la tabla (solo letras y guión bajo)
$tabla_solicitada = isset($data->tabla) ? preg_replace('/[^a-z_]/', '', $data->tabla) : '';

// CASO ESPECIAL: Emisores de Normativa.
// No sigue el patrón genérico descripcion/vigente de la Lista Blanca de abajo:
// tiene FK a jurisdiccion y un campo derivado (clave_normalizada) calculado acá mismo.
if ($tabla_solicitada === 'emisor_norma') {
    if (!isset($data->descripcion) || trim($data->descripcion) === '') {
        http_response_code(400);
        echo json_encode(["mensaje" => "El nombre del emisor es obligatorio."]);
        exit();
    }
    if (!isset($data->id_jurisdiccion) || (int)$data->id_jurisdiccion <= 0) {
        http_response_code(400);
        echo json_encode(["mensaje" => "Debe seleccionar una jurisdicción."]);
        exit();
    }

    $database = new Database();
    $db = $database->getConnection();

    $id_valor = isset($data->id_emisor_norma) && $data->id_emisor_norma !== "" ? (int)$data->id_emisor_norma : null;
    $desc_valor = htmlspecialchars(strip_tags(trim($data->descripcion))); // Limpieza XSS
    $id_jurisdiccion_valor = (int)$data->id_jurisdiccion;
    // La clave_normalizada NUNCA se toma del cliente: se recalcula siempre en el servidor.
    $clave_valor = normalizarClave($desc_valor);

    try {
        if ($id_valor) {
            $query = "UPDATE emisor_norma 
                      SET descripcion = :desc, id_jurisdiccion = :id_jurisdiccion, clave_normalizada = :clave 
                      WHERE id_emisor_norma = :id";
            $stmt = $db->prepare($query);
            $stmt->bindParam(":desc", $desc_valor, PDO::PARAM_STR);
            $stmt->bindParam(":id_jurisdiccion", $id_jurisdiccion_valor, PDO::PARAM_INT);
            $stmt->bindParam(":clave", $clave_valor, PDO::PARAM_STR);
            $stmt->bindParam(":id", $id_valor, PDO::PARAM_INT);
            $mensaje_exito = "Emisor actualizado correctamente.";
        } else {
            $query = "INSERT INTO emisor_norma (descripcion, id_jurisdiccion, clave_normalizada) 
                      VALUES (:desc, :id_jurisdiccion, :clave)";
            $stmt = $db->prepare($query);
            $stmt->bindParam(":desc", $desc_valor, PDO::PARAM_STR);
            $stmt->bindParam(":id_jurisdiccion", $id_jurisdiccion_valor, PDO::PARAM_INT);
            $stmt->bindParam(":clave", $clave_valor, PDO::PARAM_STR);
            $mensaje_exito = "Emisor creado correctamente.";
        }

        if ($stmt->execute()) {
            http_response_code(200);
            echo json_encode(["mensaje" => $mensaje_exito]);
        } else {
            throw new Exception("Error al ejecutar la sentencia en la base de datos.");
        }
    } catch (Exception $e) {
        http_response_code(500);
        echo json_encode(["mensaje" => "Error interno del servidor al guardar el emisor."]);
    }
    exit();
}

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

// Detectar si la tabla tiene columna vigente
$tiene_vigente = !in_array($tabla_solicitada, $tablas_sin_vigente);

try {
    // 3. LÓGICA DE UPSERT (Insertar o Actualizar)
    if ($id_valor) {
        // MODO EDICIÓN (UPDATE)
        $query = "UPDATE " . $tabla_solicitada . " 
                  SET " . $campo_desc . " = :desc";
        $params = [':desc' => $desc_valor, ':id' => $id_valor];
        if ($tiene_vigente) {
            $query .= ", vigente = :vigente";
            $params[':vigente'] = $vigente_valor;
        }
        $query .= " WHERE " . $campo_id . " = :id";
        
        $mensaje_exito = "Registro actualizado correctamente.";

    } else {
        // MODO CREACIÓN (INSERT)
        $campos = $campo_desc;
        $valores = ":desc";
        $params = [':desc' => $desc_valor];
        if ($tiene_vigente) {
            $campos .= ", vigente";
            $valores .= ", :vigente";
            $params[':vigente'] = $vigente_valor;
        }
        $query = "INSERT INTO " . $tabla_solicitada . " (" . $campos . ") VALUES (" . $valores . ")";
        $mensaje_exito = "Registro creado correctamente.";
    }

    // 4. EJECUCIÓN
    $stmt = $db->prepare($query);
    $stmt->execute($params);

    http_response_code(200);
    echo json_encode(["mensaje" => $mensaje_exito]);

} catch (Exception $e) {
    http_response_code(500);
    // Para producción se recomienda no exponer $e->getMessage() directamente
    echo json_encode(["mensaje" => "Error interno del servidor al guardar el registro."]);
}
?>