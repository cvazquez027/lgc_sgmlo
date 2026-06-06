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

// CIBERSEGURIDAD: API Key del bot
define('SCRAPER_API_KEY', 'Token_Seguro_Scraper_2026_XyZ!');

// 1. Verificación del Token
$headers = apache_request_headers();
$auth_header = isset($headers['Authorization']) ? $headers['Authorization'] : '';

if (str_replace('Bearer ', '', $auth_header) !== SCRAPER_API_KEY) {
    http_response_code(401);
    echo json_encode(["mensaje" => "Acceso denegado. API Key inválida o ausente."]);
    exit();
}

$data = json_decode(file_get_contents("php://input"), true);

if (!isset($data['normas']) || !is_array($data['normas'])) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Formato incorrecto. Se esperaba un array 'normas'."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

try {
    $db->beginTransaction();

    // -------------------------------------------------------------
    // STATEMENTS PREPARADOS PARA OPTIMIZAR EL BUCLE
    // -------------------------------------------------------------
    
    // Motor dinámico para EMISOR
    $stmt_emisor = $db->prepare("SELECT id_emisor_norma FROM emisor_norma WHERE UPPER(descripcion) = :desc AND id_jurisdiccion = :id_jur");
    $stmt_ins_emisor = $db->prepare("INSERT INTO emisor_norma (descripcion, id_jurisdiccion) VALUES (:desc, :id_jur)");

    // Motor dinámico para TIPO DE NORMA
    $stmt_tipo = $db->prepare("SELECT id_tipo_norma FROM tipo_norma WHERE UPPER(descripcion) = :desc");
    $stmt_ins_tipo = $db->prepare("INSERT INTO tipo_norma (descripcion, vigente) VALUES (:desc, 1)");

    // Inserción de la norma en el Buffer
    $q_norma = "INSERT INTO norma_bo (id_tipo_norma, id_emisor_norma, numero, anio, fecha_publicacion, sintesis, url_norma, id_estado_norma) VALUES (:id_tipo, :id_emisor, :numero, :anio, :fecha, :sintesis, :url, :id_estado)";
    $stmt_norma = $db->prepare($q_norma);

    $q_cat = "INSERT INTO categoria_norma_bo (id_norma_bo, id_categoria) VALUES (:id_nbo, :id_cat)";
    $stmt_cat = $db->prepare($q_cat);

    $procesadas = 0;

    foreach ($data['normas'] as $norma) {
        $id_jurisdiccion = filter_var($norma['id_jurisdiccion'], FILTER_VALIDATE_INT);
        if (!$id_jurisdiccion) continue;

        // --- 1. PROCESAR TIPO DE NORMA DINÁMICO ---
        $tipo_norma_desc = isset($norma['tipo_norma_desc']) ? strtoupper(trim($norma['tipo_norma_desc'])) : 'OTRO';
        
        $stmt_tipo->execute([':desc' => $tipo_norma_desc]);
        $row_tipo = $stmt_tipo->fetch(PDO::FETCH_ASSOC);
        
        if ($row_tipo) {
            $id_tipo = $row_tipo['id_tipo_norma'];
        } else {
            // Si el tipo no existe en la BD (ej. AVISO OFICIAL), lo agrega automáticamente
            $stmt_ins_tipo->execute([':desc' => $tipo_norma_desc]);
            $id_tipo = $db->lastInsertId();
        }

        // --- 2. PROCESAR EMISOR DINÁMICO ---
        $emisor_desc = strtoupper(trim($norma['nombre_emisor']));
        $stmt_emisor->execute([':desc' => $emisor_desc, ':id_jur' => $id_jurisdiccion]);
        $row_emisor = $stmt_emisor->fetch(PDO::FETCH_ASSOC);

        if ($row_emisor) {
            $id_emisor_final = $row_emisor['id_emisor_norma'];
        } else {
            $stmt_ins_emisor->execute([':desc' => $emisor_desc, ':id_jur' => $id_jurisdiccion]);
            $id_emisor_final = $db->lastInsertId();
        }

        // --- 3. INSERCIÓN DE NORMA_BO ---
        $numero = htmlspecialchars(strip_tags($norma['numero']));
        $anio = filter_var($norma['anio'], FILTER_VALIDATE_INT);
        $fecha = htmlspecialchars(strip_tags($norma['fecha_publicacion']));
        $url = filter_var($norma['url_norma'], FILTER_SANITIZE_URL);
        $sintesis = htmlspecialchars(strip_tags($norma['sintesis']));
        $id_estado = 1; // Vigente

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

        // --- 4. INSERCIÓN DE CATEGORÍAS ---
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
    echo json_encode(["mensaje" => "Se procesaron $procesadas normas exitosamente."]);

} catch (Exception $e) {
    $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al guardar en la BD.", "error" => $e->getMessage()]);
}
?>