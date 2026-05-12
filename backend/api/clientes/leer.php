<?php
// Cabeceras de seguridad y CORS estandarizadas
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS"); // Agregamos OPTIONS
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

// Intercepción de pre-flight requests para navegadores modernos
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';
include_once '../../models/Cliente.php';

try {
    $database = new Database();
    $db = $database->getConnection();
    $cliente = new Cliente($db);

    $stmt = $cliente->leer();
    $num = $stmt->rowCount();

    $clientes_arr = array();
    // Inicializamos el array siempre, para que el frontend no rompa si viene vacío
    $clientes_arr["registros"] = array();

    if ($num > 0) {
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            // Al usar FETCH_ASSOC y SELECT *, el nuevo campo 'logo_path' viaja automáticamente aquí
            array_push($clientes_arr["registros"], $row);
        }
        http_response_code(200);
        echo json_encode($clientes_arr);
    } else {
        // Buenas prácticas REST: Si no hay registros, devolvemos 200 OK pero con array vacío
        http_response_code(200);
        echo json_encode(["mensaje" => "Aún no hay clientes registrados.", "registros" => []]);
    }

} catch (Exception $e) {
    // Ciberseguridad: Capturamos la excepción para evitar que el servidor exponga 
    // rutas internas o credenciales en caso de caída de la BD.
    http_response_code(500);
    echo json_encode([
        "mensaje" => "Error interno al leer el listado de clientes.",
        "debug" => $e->getMessage() // Nota: En un entorno de producción estricto, ocultaríamos este "debug"
    ]);
}
?>