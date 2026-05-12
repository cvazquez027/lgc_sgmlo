<?php
// Cabeceras estrictas CORS y protección
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

// Respuesta rápida al Pre-flight de CORS
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once dirname(__FILE__) . '/../../config/Database.php';

// 1. OBTENER Y PARSEAR DATOS DEL FRONTEND
$data = json_decode(file_get_contents("php://input"));

// Validación de campos obligatorios básicos
if (
    empty($data->numero) || 
    empty($data->anio) || 
    empty($data->id_tipo_norma) || 
    empty($data->id_emisor_norma) || 
    empty($data->id_estado_norma)
) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Datos incompletos. Faltan campos obligatorios de la norma."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

// 2. SANITIZACIÓN EXTREMA (Defensa en Profundidad)
$id_norma_bo = !empty($data->id_norma_bo) ? (int)$data->id_norma_bo : null;
$anio = (int)$data->anio;
$numero = htmlspecialchars(strip_tags(trim($data->numero)));
$id_tipo_norma = (int)$data->id_tipo_norma;
$id_emisor_norma = (int)$data->id_emisor_norma;
$id_estado_norma = (int)$data->id_estado_norma;
$sintesis = !empty($data->sintesis) ? htmlspecialchars(strip_tags(trim($data->sintesis))) : null;

// Validación específica para URL para prevenir XSS a través de enlaces maliciosos
$url_norma = !empty($data->url_norma) ? filter_var(trim($data->url_norma), FILTER_SANITIZE_URL) : null;

// Aseguramos que el array de categorías sea válido
$categorias = (isset($data->categorias) && is_array($data->categorias)) ? $data->categorias : [];

try {
    // 3. INICIO DE TRANSACCIÓN ACID
    // A partir de aquí, la base de datos "congela" los cambios hasta el commit final.
    $db->beginTransaction();

    if ($id_norma_bo) {
        // --- MODO EDICIÓN (UPDATE) ---
        $query_norma = "UPDATE norma_bo 
                        SET anio = :anio, 
                            numero = :numero, 
                            sintesis = :sintesis, 
                            url_norma = :url_norma, 
                            id_tipo_norma = :id_tipo_norma, 
                            id_emisor_norma = :id_emisor_norma, 
                            id_estado_norma = :id_estado_norma 
                        WHERE id_norma_bo = :id_norma_bo";
        
        $stmt = $db->prepare($query_norma);
        $stmt->bindParam(":id_norma_bo", $id_norma_bo, PDO::PARAM_INT);

    } else {
        // --- MODO CREACIÓN (INSERT) ---
        // Se asume origen_carga = 'Manual' al ingresar desde el frontend
        $query_norma = "INSERT INTO norma_bo 
                        (origen_carga, anio, numero, sintesis, url_norma, id_tipo_norma, id_emisor_norma, id_estado_norma) 
                        VALUES 
                        ('Manual', :anio, :numero, :sintesis, :url_norma, :id_tipo_norma, :id_emisor_norma, :id_estado_norma)";
        
        $stmt = $db->prepare($query_norma);
    }

    // Bindeamos los parámetros comunes a ambas operaciones
    $stmt->bindParam(":anio", $anio, PDO::PARAM_INT);
    $stmt->bindParam(":numero", $numero, PDO::PARAM_STR);
    $stmt->bindParam(":sintesis", $sintesis, PDO::PARAM_STR);
    $stmt->bindParam(":url_norma", $url_norma, PDO::PARAM_STR);
    $stmt->bindParam(":id_tipo_norma", $id_tipo_norma, PDO::PARAM_INT);
    $stmt->bindParam(":id_emisor_norma", $id_emisor_norma, PDO::PARAM_INT);
    $stmt->bindParam(":id_estado_norma", $id_estado_norma, PDO::PARAM_INT);

    $stmt->execute();

    // Si es creación, obtenemos el ID que la base de datos le acaba de asignar
    if (!$id_norma_bo) {
        $id_norma_bo = $db->lastInsertId();
    }

    // 4. LÓGICA DE TABLA DE CRUCE (CATEGORÍAS)
    // Primero, en un UPDATE, limpiamos todas las categorías viejas para evitar duplicados o huérfanas
    $query_clean_cats = "DELETE FROM categoria_norma_bo WHERE id_norma_bo = :id_norma_bo";
    $stmt_clean = $db->prepare($query_clean_cats);
    $stmt_clean->bindParam(":id_norma_bo", $id_norma_bo, PDO::PARAM_INT);
    $stmt_clean->execute();

    // Segundo, insertamos el nuevo listado limpio que envió React
    if (!empty($categorias)) {
        $query_insert_cat = "INSERT INTO categoria_norma_bo (id_norma_bo, id_categoria) VALUES (:id_norma_bo, :id_categoria)";
        $stmt_insert_cat = $db->prepare($query_insert_cat);

        foreach ($categorias as $id_cat) {
            $cat_limpia = (int)$id_cat; // Blindaje extra de cast a entero por cada iteración
            $stmt_insert_cat->bindParam(":id_norma_bo", $id_norma_bo, PDO::PARAM_INT);
            $stmt_insert_cat->bindParam(":id_categoria", $cat_limpia, PDO::PARAM_INT);
            $stmt_insert_cat->execute();
        }
    }

    // 5. CIERRE SEGURO (COMMIT)
    // Si llegamos hasta esta línea, significa que ni el UPDATE/INSERT ni los recálculos de categorías fallaron.
    $db->commit();

    http_response_code(200);
    echo json_encode([
        "mensaje" => "La norma y su clasificación técnica se guardaron exitosamente.",
        "id_norma_bo" => $id_norma_bo
    ]);

} catch (Exception $e) {
    // 6. MANEJO DE DESASTRES (ROLLBACK)
    // Falló algo. Deshacemos todo para mantener la integridad de la base de datos.
    $db->rollBack();
    
    http_response_code(500);
    // Para entornos de producción, solemos loguear el $e->getMessage() en un archivo oculto,
    // y al frontend solo le mandamos un error genérico para no exponer la arquitectura.
    error_log("Error guardando norma_bo: " . $e->getMessage()); 
    echo json_encode(["mensaje" => "Ocurrió un error crítico al guardar. Los cambios fueron revertidos."]);
}
?>