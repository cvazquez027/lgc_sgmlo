<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

set_time_limit(0);
ini_set('memory_limit', '512M');
ignore_user_abort(true);
ini_set('display_errors', '0');
error_reporting(E_ALL);

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';

function responder($arr, $http = 200) {
    http_response_code($http);
    echo json_encode($arr);
    exit();
}

function extraer_json_de_salida($salida) {
    if ($salida === null) return null;
    $lineas = preg_split('/\r\n|\r|\n/', trim($salida));
    for ($i = count($lineas) - 1; $i >= 0; $i--) {
        $linea = trim($lineas[$i]);
        if ($linea === '' || $linea[0] !== '{') continue;
        $obj = json_decode($linea, true);
        if (json_last_error() === JSON_ERROR_NONE && is_array($obj)) {
            return $obj;
        }
    }
    $obj = json_decode(trim($salida), true);
    if (json_last_error() === JSON_ERROR_NONE && is_array($obj)) {
        return $obj;
    }
    return null;
}

$data = json_decode(file_get_contents("php://input"));
if (empty($data->id_jurisdiccion)) {
    responder(["status" => "error", "message" => "Falta id_jurisdiccion"], 400);
}

$id_jurisdiccion = (int)$data->id_jurisdiccion;

try {
    $database = new Database();
    $db = $database->getConnection();

    $query = "SELECT descripcion, url_boletin, tiene_scraper, nombre_bot FROM jurisdiccion WHERE id_jurisdiccion = :id";
    $stmt = $db->prepare($query);
    $stmt->execute([':id' => $id_jurisdiccion]);
    $jur = $stmt->fetch(PDO::FETCH_ASSOC);
} catch (Exception $e) {
    error_log("EJECUTAR_SCRAPER: Error DB: " . $e->getMessage());
    responder(["status" => "error", "message" => "Error de base de datos."], 500);
}

if (!$jur || $jur['tiene_scraper'] != 1) {
    responder(["status" => "error", "message" => "Jurisdicción no válida o sin scraper habilitado."], 400);
}

$nombre_script = $jur['nombre_bot'];
if (!$nombre_script) {
    responder(["status" => "error", "message" => "La jurisdicción no tiene un script asignado (campo nombre_bot nulo)."], 404);
}

$ruta_base = dirname(__FILE__) . '/../../scripts/';
$ruta_script = $ruta_base . $nombre_script;

if (!file_exists($ruta_script)) {
    responder(["status" => "error", "message" => "No se encontró el script '$nombre_script' para esta jurisdicción."], 404);
}

// --- Determinar el intérprete de Python ---
$python_cmd = '/var/www/matrizonline/backend/.venv/bin/python';

chdir($ruta_base);

// --- Variables de entorno para el script Python ---
// Leer el .env de backend para pasar las URLs al script
$env_file = dirname(__FILE__) . '/../../.env';
$env_vars = [];
if (file_exists($env_file)) {
    $lines = file($env_file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        if (strpos($line, '=') === false) continue;
        list($name, $value) = explode('=', $line, 2);
        $env_vars[trim($name)] = trim($value);
    }
}

// Construir el comando con las variables de entorno
$cmd_env = '';
foreach ($env_vars as $key => $value) {
    // Escapar valores para shell
    $cmd_env .= "export $key=" . escapeshellarg($value) . "; ";
}

$comando = $cmd_env . $python_cmd . " " . escapeshellarg($nombre_script)
         . " " . escapeshellarg($id_jurisdiccion)
         . " " . escapeshellarg($jur['url_boletin'])
         . " 2>&1"; // Redirigir stderr a stdout para capturar todo

error_log("EJECUTAR_SCRAPER: Comando: $comando");

$salida = shell_exec($comando);
error_log("EJECUTAR_SCRAPER: Salida (primeros 1000 chars): " . substr($salida, 0, 1000));

$resultado = extraer_json_de_salida($salida);

if ($resultado !== null) {
    responder($resultado, 200);
} else {
    error_log("EJECUTAR_SCRAPER: No se pudo parsear JSON. Salida completa: $salida");
    responder([
        "status" => "error",
        "message" => "El scraper no devolvió un resultado JSON válido. Revisa los logs.",
        "debug" => substr($salida, 0, 500)
    ], 200);
}
?>