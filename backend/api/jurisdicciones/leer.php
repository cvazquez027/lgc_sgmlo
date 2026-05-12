<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';

// CIBERSEGURIDAD: Capturamos el parámetro "niveles" (ej: ?niveles=1,2)
$niveles_param = isset($_GET['niveles']) ? $_GET['niveles'] : null;

$database = new Database();
$db = $database->getConnection();

try {
    $query = "SELECT * FROM jurisdiccion WHERE 1=1";
    
    // Si mandaron niveles, construimos la cláusula IN de forma segura
    if ($niveles_param) {
        // 1. Separamos por coma
        $niveles_array = explode(',', $niveles_param);
        
        // 2. Filtramos estrictamente para que SOLO queden números enteros (Defensa contra Inyección SQL)
        $niveles_seguros = array_filter($niveles_array, function($val) {
            return filter_var($val, FILTER_VALIDATE_INT) !== false;
        });

        // 3. Si sobrevivieron números válidos, armamos la query
        if (!empty($niveles_seguros)) {
            // Creamos los placeholders (?, ?)
            $placeholders = str_repeat('?,', count($niveles_seguros) - 1) . '?';
            $query .= " AND id_nivel_jurisdiccion IN ($placeholders)";
        }
    }
    
    $query .= " ORDER BY id_nivel_jurisdiccion ASC, descripcion ASC";
    
    $stmt = $db->prepare($query);

    // Bind seguro de los parámetros en caso de usar el filtro IN
    if (!empty($niveles_seguros)) {
        // execute() con array mapea cada valor al placeholder '?' correspondiente
        $stmt->execute(array_values($niveles_seguros));
    } else {
        $stmt->execute();
    }
    
    $registros = $stmt->fetchAll(PDO::FETCH_ASSOC);

    http_response_code(200);
    echo json_encode(["registros" => $registros]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno al leer jurisdicciones.", "error" => $e->getMessage()]);
}
?>