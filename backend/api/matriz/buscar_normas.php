<?php
// Cabeceras de seguridad y CORS
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';

// Ciberseguridad: Sanitización estricta del término de búsqueda
$q = isset($_GET['q']) ? htmlspecialchars(strip_tags(trim($_GET['q']))) : '';

// Evitamos consultas a la BD si escribieron menos de 2 caracteres (ahorro de recursos)
if (strlen($q) < 2) {
    http_response_code(200);
    echo json_encode(["registros" => []]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    // Buscamos coincidencias en Número, Año, Tipo de Norma o Emisor
    // Usamos LIMIT 15 para no saturar el DOM del frontend con demasiados resultados
    $query = "SELECT 
                n.id_norma, 
                n.numero, 
                n.anio, 
                tn.descripcion as tipo_norma, 
                en.descripcion as emisor
              FROM norma n
              LEFT JOIN tipo_norma tn ON n.id_tipo_norma = tn.id_tipo_norma
              LEFT JOIN emisor_norma en ON n.id_emisor_norma = en.id_emisor_norma
              WHERE (n.numero LIKE :term 
                 OR tn.descripcion LIKE :term 
                 OR n.anio LIKE :term)
              ORDER BY n.anio DESC, n.numero DESC
              LIMIT 15";

    $stmt = $db->prepare($query);
    
    // Los comodines % van por fuera del bindParam por seguridad
    $term = "%{$q}%";
    $stmt->bindParam(":term", $term, PDO::PARAM_STR);
    
    $stmt->execute();
    $registros = $stmt->fetchAll(PDO::FETCH_ASSOC);

    http_response_code(200);
    echo json_encode([
        "mensaje" => "Búsqueda exitosa.",
        "registros" => $registros
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno en la búsqueda.", "error" => $e->getMessage()]);
}
?>