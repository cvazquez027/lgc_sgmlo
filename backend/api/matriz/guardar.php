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

if (empty($data->id_cliente_establecimiento) || empty($data->fecha_desde) || empty($data->id_estado_matriz) || empty($data->id_tipo_matriz) || empty($data->id_especialidad_matriz)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan datos obligatorios para crear la cabecera."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

$id_matriz = !empty($data->id_matriz) ? (int)$data->id_matriz : null;
$id_cliente_establecimiento = (int)$data->id_cliente_establecimiento;
$id_estado_matriz = (int)$data->id_estado_matriz;
$id_tipo_matriz = (int)$data->id_tipo_matriz; 
$id_especialidad_matriz = (int)$data->id_especialidad_matriz; 
$vigente = isset($data->vigente) ? (int)$data->vigente : 1;

// Nuevos campos con valores por defecto
$mostrar_cumplimiento = isset($data->mostrar_cumplimiento) ? (int)$data->mostrar_cumplimiento : 1;
$campo_encabezado_item = isset($data->campo_encabezado_item) ? $data->campo_encabezado_item : 'normas';

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
    $db->beginTransaction();

    // *** VALIDACIÓN DE UNICIDAD PARA BORRADORES ***
    $queryCheck = "SELECT COUNT(*) FROM matriz 
                   WHERE id_cliente_establecimiento = :est
                     AND id_especialidad_matriz = :esp
                     AND id_tipo_matriz = :tipo
                     AND id_estado_matriz = 1";
    if ($id_matriz) {
        $queryCheck .= " AND id_matriz != :id_matriz";
    }
    $stmtCheck = $db->prepare($queryCheck);
    $stmtCheck->bindParam(':est', $id_cliente_establecimiento, PDO::PARAM_INT);
    $stmtCheck->bindParam(':esp', $id_especialidad_matriz, PDO::PARAM_INT);
    $stmtCheck->bindParam(':tipo', $id_tipo_matriz, PDO::PARAM_INT);
    if ($id_matriz) {
        $stmtCheck->bindParam(':id_matriz', $id_matriz, PDO::PARAM_INT);
    }
    $stmtCheck->execute();
    $existeBorrador = $stmtCheck->fetchColumn();

    if ($existeBorrador > 0) {
        $db->rollBack();
        http_response_code(409);
        echo json_encode(["mensaje" => "Ya existe una matriz en estado BORRADOR para la misma combinación de establecimiento, especialidad y tipo. No se puede crear otra hasta que la actual sea publicada o eliminada."]);
        exit();
    }

    if ($id_matriz) {
        // Edición: incluir los nuevos campos
        $query = "UPDATE matriz SET 
                    id_cliente_establecimiento = :id_cliente_establecimiento,
                    id_tipo_matriz = :id_tipo_matriz,
                    id_especialidad_matriz = :id_especialidad_matriz,
                    fecha_desde = :fecha_desde,
                    id_estado_matriz = :id_estado_matriz,
                    vigente = :vigente,
                    mostrar_cumplimiento = :mostrar_cumplimiento,
                    campo_encabezado_item = :campo_encabezado_item
                  WHERE id_matriz = :id_matriz";
        $stmt = $db->prepare($query);
        $stmt->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    } else {
        // Creación: calcular próxima versión
        $query_ver = "SELECT COALESCE(MAX(version), 0) + 1 AS siguiente
                      FROM matriz
                      WHERE id_cliente_establecimiento = :est
                        AND id_tipo_matriz = :tipo
                        AND id_especialidad_matriz = :esp";
        $stmt_ver = $db->prepare($query_ver);
        $stmt_ver->execute([
            ':est' => $id_cliente_establecimiento,
            ':tipo' => $id_tipo_matriz,
            ':esp' => $id_especialidad_matriz
        ]);
        $version = (int)$stmt_ver->fetchColumn();

        $query = "INSERT INTO matriz 
                    (id_cliente_establecimiento, id_tipo_matriz, id_especialidad_matriz, fecha_desde, version, id_estado_matriz, vigente, mostrar_cumplimiento, campo_encabezado_item) 
                  VALUES 
                    (:id_cliente_establecimiento, :id_tipo_matriz, :id_especialidad_matriz, :fecha_desde, :version, :id_estado_matriz, :vigente, :mostrar_cumplimiento, :campo_encabezado_item)";
        $stmt = $db->prepare($query);
        $stmt->bindParam(":version", $version, PDO::PARAM_INT);
    }

    $stmt->bindParam(":id_cliente_establecimiento", $id_cliente_establecimiento, PDO::PARAM_INT);
    $stmt->bindParam(":id_tipo_matriz", $id_tipo_matriz, PDO::PARAM_INT);
    $stmt->bindParam(":id_especialidad_matriz", $id_especialidad_matriz, PDO::PARAM_INT);
    $stmt->bindParam(":fecha_desde", $fecha_desde, PDO::PARAM_STR);
    $stmt->bindParam(":id_estado_matriz", $id_estado_matriz, PDO::PARAM_INT);
    $stmt->bindParam(":vigente", $vigente, PDO::PARAM_INT);
    $stmt->bindParam(":mostrar_cumplimiento", $mostrar_cumplimiento, PDO::PARAM_INT);
    $stmt->bindParam(":campo_encabezado_item", $campo_encabezado_item, PDO::PARAM_STR);

    $stmt->execute();

    if (!$id_matriz) {
        $id_matriz = $db->lastInsertId();
    }

    // Lógica de publicación y auto-archivo (si se publica)
    if ($id_estado_matriz === 2) {
        $query_archive = "UPDATE matriz 
                          SET id_estado_matriz = 3 
                          WHERE id_cliente_establecimiento = :est 
                            AND id_tipo_matriz = :tipo 
                            AND id_especialidad_matriz = :esp 
                            AND id_matriz != :id_mat";
        $stmt_arc = $db->prepare($query_archive);
        $stmt_arc->execute([
            ':est' => $id_cliente_establecimiento,
            ':tipo' => $id_tipo_matriz,
            ':esp' => $id_especialidad_matriz,
            ':id_mat' => $id_matriz
        ]);
    }

    $db->commit();

    http_response_code(200);
    echo json_encode([
        "mensaje" => "Cabecera guardada exitosamente.",
        "id_matriz" => $id_matriz
    ]);

} catch (PDOException $e) {
    if ($db->inTransaction()) $db->rollBack();
    if ($e->getCode() == 23000) {
        http_response_code(409);
        echo json_encode(["mensaje" => "Error: Ya existe una Matriz para la especialidad, tipo y sede seleccionados."]);
    } else {
        http_response_code(500);
        echo json_encode(["mensaje" => "Error de base de datos.", "error" => $e->getMessage()]);
    }
} catch (Exception $e) {
    if ($db->inTransaction()) $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno.", "error" => $e->getMessage()]);
}
?>