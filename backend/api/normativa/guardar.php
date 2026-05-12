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

// Validación de campos requeridos mínimos
if (empty($data->id_tipo_norma) || empty($data->id_emisor_norma) || empty($data->id_estado_norma)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan datos obligatorios (Tipo, Emisor o Estado)."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    $id_norma = !empty($data->id_norma) ? filter_var($data->id_norma, FILTER_VALIDATE_INT) : null;
    
    // Ciberseguridad: Sanitización estricta
    $id_tipo_norma = filter_var($data->id_tipo_norma, FILTER_VALIDATE_INT);
    $id_emisor_norma = filter_var($data->id_emisor_norma, FILTER_VALIDATE_INT);
    $id_estado_norma = filter_var($data->id_estado_norma, FILTER_VALIDATE_INT);
    $numero = htmlspecialchars(strip_tags($data->numero ?? ''));
    $anio = filter_var($data->anio ?? date('Y'), FILTER_VALIDATE_INT);
    $fecha_publicacion = htmlspecialchars(strip_tags($data->fecha_publicacion ?? ''));
    $sintesis = htmlspecialchars(strip_tags($data->sintesis ?? ''));
    $url_norma = filter_var($data->url_norma ?? '', FILTER_SANITIZE_URL);
    $origen_carga = $data->origen_carga ?? 'Manual'; // Por defecto desde el CRUD es Manual

    if ($id_norma) {
        $query = "UPDATE norma SET 
                    id_tipo_norma = :tipo, id_emisor_norma = :emisor, numero = :num, 
                    anio = :anio, fecha_publicacion = :fecha, sintesis = :sintesis, 
                    url_norma = :url, id_estado_norma = :estado
                  WHERE id_norma = :id";
        $stmt = $db->prepare($query);
        $stmt->bindParam(":id", $id_norma);
    } else {
        $query = "INSERT INTO norma 
                    (id_tipo_norma, id_emisor_norma, numero, anio, fecha_publicacion, sintesis, url_norma, id_estado_norma, origen_carga) 
                  VALUES 
                    (:tipo, :emisor, :num, :anio, :fecha, :sintesis, :url, :estado, :origen)";
        $stmt = $db->prepare($query);
        $stmt->bindParam(":origen", $origen_carga);
    }

    $stmt->bindParam(":tipo", $id_tipo_norma);
    $stmt->bindParam(":emisor", $id_emisor_norma);
    $stmt->bindParam(":num", $numero);
    $stmt->bindParam(":anio", $anio);
    $stmt->bindParam(":fecha", $fecha_publicacion);
    $stmt->bindParam(":sintesis", $sintesis);
    $stmt->bindParam(":url", $url_norma);
    $stmt->bindParam(":estado", $id_estado_norma);

    $stmt->execute();

    http_response_code(200);
    echo json_encode(["mensaje" => "Normativa guardada exitosamente."]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al guardar.", "error" => $e->getMessage()]);
}
?>