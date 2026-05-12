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

// CIBERSEGURIDAD: Esta clave la usarás en tu script de Python. 
// En un entorno de producción real, esto debería ir en un archivo .env
define('SCRAPER_API_KEY', 'Token_Seguro_Scraper_2026_XyZ!');

// 1. Verificación del Token (API Key)
$headers = apache_request_headers();
$auth_header = isset($headers['Authorization']) ? $headers['Authorization'] : '';

if (str_replace('Bearer ', '', $auth_header) !== SCRAPER_API_KEY) {
    http_response_code(401);
    echo json_encode(["mensaje" => "Acceso denegado. API Key inválida o ausente."]);
    exit();
}

$data = json_decode(file_get_contents("php://input"), true);

// 2. Validación de formato de entrada
if (!isset($data['normas']) || !is_array($data['normas'])) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Formato incorrecto. Se esperaba un array 'normas'."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    // CIBERSEGURIDAD Y PERFORMANCE: Usamos Transacciones ACID.
    $db->beginTransaction();

    // Preparamos las consultas de inserción
    $query_norma = "INSERT INTO norma_bo 
        (id_tipo_norma, id_emisor_norma, numero, anio, fecha_publicacion, sintesis, url_norma, id_estado_norma, origen_carga) 
        VALUES (:id_tipo, :id_emisor, :numero, :anio, :fecha, :sintesis, :url, :id_estado, 'Scraping')";
    $stmt_norma = $db->prepare($query_norma);

    $query_cat = "INSERT INTO categoria_norma_bo (id_norma_bo, id_categoria) VALUES (:id_nbo, :id_cat)";
    $stmt_cat = $db->prepare($query_cat);

    // Consultas para la gestión dinámica de emisores
    $stmt_check_emisor = $db->prepare("SELECT id_emisor_norma FROM emisor_norma WHERE descripcion = :desc AND id_jurisdiccion = :jur");
    $stmt_ins_emisor = $db->prepare("INSERT INTO emisor_norma (descripcion, id_jurisdiccion) VALUES (:desc, :jur)");

    $procesadas = 0;

    foreach ($data['normas'] as $norma) {
        // 1. Gestión dinámica del Emisor
        $nombre_emisor = htmlspecialchars(strip_tags($norma['nombre_emisor']));
        $id_jurisdiccion = filter_var($norma['id_jurisdiccion'], FILTER_VALIDATE_INT);

        // Buscar si existe el emisor para esta jurisdicción
        $stmt_check_emisor->execute([':desc' => $nombre_emisor, ':jur' => $id_jurisdiccion]);
        $emisor = $stmt_check_emisor->fetch(PDO::FETCH_ASSOC);

        if ($emisor) {
            $id_emisor_final = $emisor['id_emisor_norma'];
        } else {
            // Si no existe, lo creamos automáticamente
            $stmt_ins_emisor->execute([':desc' => $nombre_emisor, ':jur' => $id_jurisdiccion]);
            $id_emisor_final = $db->lastInsertId();
        }

        // 2. Procesamiento de la Norma
        $id_tipo = filter_var($norma['id_tipo_norma'], FILTER_VALIDATE_INT);
        $numero = htmlspecialchars(strip_tags($norma['numero']));
        $anio = filter_var($norma['anio'], FILTER_VALIDATE_INT);
        $fecha = htmlspecialchars(strip_tags($norma['fecha_publicacion']));
        $sintesis = htmlspecialchars(strip_tags($norma['sintesis']));
        $url = htmlspecialchars(strip_tags($norma['url_norma']));
        $id_estado = 1; // Vigente por defecto

        $stmt_norma->bindParam(":id_tipo", $id_tipo);
        $stmt_norma->bindParam(":id_emisor", $id_emisor_final);
        $stmt_norma->bindParam(":numero", $numero);
        $stmt_norma->bindParam(":anio", $anio);
        $stmt_norma->bindParam(":fecha", $fecha);
        $stmt_norma->bindParam(":sintesis", $sintesis);
        $stmt_norma->bindParam(":url", $url);
        $stmt_norma->bindParam(":id_estado", $id_estado);
        
        $stmt_norma->execute();
        $id_norma_bo = $db->lastInsertId();

        // 3. Inserción de Categorías
        if (isset($norma['categorias']) && is_array($norma['categorias'])) {
            foreach ($norma['categorias'] as $id_categoria) {
                $id_cat = filter_var($id_categoria, FILTER_VALIDATE_INT);
                if ($id_cat) {
                    $stmt_cat->bindParam(":id_nbo", $id_norma_bo);
                    $stmt_cat->bindParam(":id_cat", $id_cat);
                    $stmt_cat->execute();
                }
            }
        }
        $procesadas++;
    }

    $db->commit();
    http_response_code(200);
    echo json_encode(["mensaje" => "Lote procesado exitosamente. $procesadas normas e emisores gestionados."]);

} catch (Exception $e) {
    $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error procesando el scraping.", "error" => $e->getMessage()]);
}
?>