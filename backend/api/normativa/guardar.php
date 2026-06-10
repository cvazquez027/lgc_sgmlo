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

if (empty($data->id_tipo_norma) || empty($data->numero) || empty($data->anio) || empty($data->id_emisor_norma)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan datos obligatorios (tipo, número, año, emisor)."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

$id_norma = !empty($data->id_norma) ? (int)$data->id_norma : null;
$id_tipo_norma = (int)$data->id_tipo_norma;
$id_emisor_norma = (int)$data->id_emisor_norma;
$numero = htmlspecialchars(strip_tags(trim($data->numero)));
$anio = (int)$data->anio;
$fecha_publicacion = !empty($data->fecha_publicacion) ? $data->fecha_publicacion : null;
$sintesis = !empty($data->sintesis) ? htmlspecialchars(strip_tags(trim($data->sintesis))) : null;
$url_norma = !empty($data->url_norma) ? filter_var($data->url_norma, FILTER_SANITIZE_URL) : null;
$id_estado_norma = !empty($data->id_estado_norma) ? (int)$data->id_estado_norma : 1;
$origen_carga = !empty($data->origen_carga) ? htmlspecialchars(strip_tags($data->origen_carga)) : "Manual";

try {
    if ($id_norma) {
        $query = "UPDATE norma SET 
                    id_tipo_norma = :id_tipo,
                    id_emisor_norma = :id_emisor,
                    numero = :numero,
                    anio = :anio,
                    fecha_publicacion = :fecha,
                    sintesis = :sintesis,
                    url_norma = :url,
                    id_estado_norma = :id_estado,
                    origen_carga = :origen
                  WHERE id_norma = :id_norma";
        $stmt = $db->prepare($query);
        $stmt->bindParam(':id_norma', $id_norma, PDO::PARAM_INT);
    } else {
        $query = "INSERT INTO norma 
                    (id_tipo_norma, id_emisor_norma, numero, anio, fecha_publicacion, sintesis, url_norma, id_estado_norma, origen_carga)
                  VALUES 
                    (:id_tipo, :id_emisor, :numero, :anio, :fecha, :sintesis, :url, :id_estado, :origen)";
        $stmt = $db->prepare($query);
    }

    $stmt->bindParam(':id_tipo', $id_tipo_norma, PDO::PARAM_INT);
    $stmt->bindParam(':id_emisor', $id_emisor_norma, PDO::PARAM_INT);
    $stmt->bindParam(':numero', $numero, PDO::PARAM_STR);
    $stmt->bindParam(':anio', $anio, PDO::PARAM_INT);
    $stmt->bindParam(':fecha', $fecha_publicacion, is_null($fecha_publicacion) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindParam(':sintesis', $sintesis, is_null($sintesis) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindParam(':url', $url_norma, is_null($url_norma) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindParam(':id_estado', $id_estado_norma, PDO::PARAM_INT);
    $stmt->bindParam(':origen', $origen_carga, PDO::PARAM_STR);

    $stmt->execute();

    if (!$id_norma) {
        $id_norma = $db->lastInsertId();
    }

    http_response_code(200);
    echo json_encode(["mensaje" => "Norma guardada exitosamente.", "id_norma" => $id_norma]);

} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al guardar.", "error" => $e->getMessage()]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno.", "error" => $e->getMessage()]);
}
?>