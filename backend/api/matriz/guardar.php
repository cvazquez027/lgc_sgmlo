<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';

$data = json_decode(file_get_contents("php://input"));

// Ciberseguridad: Agregamos id_tipo_matriz a las validaciones obligatorias
if (empty($data->id_cliente_establecimiento) || empty($data->fecha_desde) || empty($data->id_estado_matriz) || empty($data->id_tipo_matriz)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan datos obligatorios para crear la cabecera."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

$id_matriz = !empty($data->id_matriz) ? (int)$data->id_matriz : null;
$id_cliente_establecimiento = (int)$data->id_cliente_establecimiento;
$id_estado_matriz = (int)$data->id_estado_matriz;
$id_tipo_matriz = (int)$data->id_tipo_matriz; // Nuevo campo sanitizado
$version = !empty($data->version) ? (int)$data->version : 1;
$vigente = isset($data->vigente) ? (int)$data->vigente : 1;

$fecha_desde = null;
$date_obj = DateTime::createFromFormat('Y-m-d', $data->fecha_desde);
if ($date_obj && $date_obj->format('Y-m-d') === $data->fecha_desde) {
    $fecha_desde = $data->fecha_desde;
} else {
    http_response_code(400);
    echo json_encode(["mensaje" => "Formato de fecha inválido."]);
    exit();
}

try {
    if ($id_matriz) {
        // ACTUALIZAR MATRIZ EXISTENTE
        $query = "UPDATE matriz SET 
                    id_cliente_establecimiento = :id_cliente_establecimiento,
                    id_tipo_matriz = :id_tipo_matriz,
                    fecha_desde = :fecha_desde,
                    version = :version,
                    id_estado_matriz = :id_estado_matriz,
                    vigente = :vigente
                  WHERE id_matriz = :id_matriz";
        $stmt = $db->prepare($query);
        $stmt->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    } else {
        // CREAR NUEVA MATRIZ
        $query = "INSERT INTO matriz 
                    (id_cliente_establecimiento, id_tipo_matriz, fecha_desde, version, id_estado_matriz, vigente) 
                  VALUES 
                    (:id_cliente_establecimiento, :id_tipo_matriz, :fecha_desde, :version, :id_estado_matriz, :vigente)";
        $stmt = $db->prepare($query);
    }

    $stmt->bindParam(":id_cliente_establecimiento", $id_cliente_establecimiento, PDO::PARAM_INT);
    $stmt->bindParam(":id_tipo_matriz", $id_tipo_matriz, PDO::PARAM_INT);
    $stmt->bindParam(":fecha_desde", $fecha_desde, PDO::PARAM_STR);
    $stmt->bindParam(":version", $version, PDO::PARAM_INT);
    $stmt->bindParam(":id_estado_matriz", $id_estado_matriz, PDO::PARAM_INT);
    $stmt->bindParam(":vigente", $vigente, PDO::PARAM_INT);

    $stmt->execute();

    if (!$id_matriz) {
        $id_matriz = $db->lastInsertId();
    }

    http_response_code(200);
    echo json_encode([
        "mensaje" => "Cabecera guardada exitosamente.",
        "id_matriz" => $id_matriz
    ]);

} catch (PDOException $e) {
    // CIBERSEGURIDAD / UX: Capturamos violaciones de índices únicos (Código 23000)
    if ($e->getCode() == 23000) {
        http_response_code(409); // 409 Conflict
        echo json_encode([
            "mensaje" => "Error: Ya existe una Matriz con esta Versión para la especialidad y sede seleccionada. Por favor, asigne un número de versión superior (ej: Versión " . ($version + 1) . ")."
        ]);
    } else {
        http_response_code(500);
        echo json_encode(["mensaje" => "Error de base de datos.", "error" => $e->getMessage()]);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno.", "error" => $e->getMessage()]);
}
?>