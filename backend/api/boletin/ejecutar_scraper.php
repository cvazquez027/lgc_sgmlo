<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

// --- Robustez para scrapers largos (CABA puede tardar varios minutos) ---
set_time_limit(0);              // sin límite de tiempo de ejecución PHP
ini_set('memory_limit', '512M');
ignore_user_abort(true);        // si el browser corta, el scraper igual termina
// IMPORTANTE: no mostrar errores como HTML; romperían el JSON de respuesta.
ini_set('display_errors', '0');
error_reporting(E_ALL);

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';

/**
 * Devuelve SIEMPRE un JSON limpio y corta la ejecución.
 */
function responder($arr, $http = 200)
{
    http_response_code($http);
    echo json_encode($arr);
    exit();
}

/**
 * Extrae el último objeto JSON válido de una salida que puede venir mezclada
 * con logs, warnings o texto suelto. Los bots imprimen su resultado como un
 * objeto JSON por línea; nos quedamos con el último JSON parseable.
 */
function extraer_json_de_salida($salida)
{
    if ($salida === null) {
        return null;
    }
    $lineas = preg_split('/\r\n|\r|\n/', trim($salida));
    // Recorrer de atrás hacia adelante: el resultado final es lo último que imprime el bot.
    for ($i = count($lineas) - 1; $i >= 0; $i--) {
        $linea = trim($lineas[$i]);
        if ($linea === '' || $linea[0] !== '{') {
            continue;
        }
        $obj = json_decode($linea, true);
        if (json_last_error() === JSON_ERROR_NONE && is_array($obj)) {
            return $obj;
        }
    }
    // Fallback: intentar parsear toda la salida como un único JSON.
    $obj = json_decode(trim($salida), true);
    if (json_last_error() === JSON_ERROR_NONE && is_array($obj)) {
        return $obj;
    }
    return null;
}

/**
 * Determina qué intérprete de Python usar según el entorno.
 * - En Hostinger (prod) existe un venv dedicado con ruta absoluta fija.
 * - En localhost ese venv normalmente no existe, así que caemos a
 *   un comando genérico disponible en el PATH del sistema.
 */
function detectar_python_cmd()
{
    $venv_paths = [
        '/var/www/matrizonline/backend/.venv/bin/python',   // venv de producción (Hostinger)
        dirname(__FILE__) . '/../../.venv/bin/python',       // venv relativo al proyecto (por si cambia el deploy)
    ];
    foreach ($venv_paths as $p) {
        if (file_exists($p)) {
            return $p;
        }
    }
    // Fallback para localhost. 'python' suele bastar en Windows/XAMPP;
    // 'python3' es lo más común en Linux/Mac.
    return (stripos(PHP_OS, 'WIN') === 0) ? 'python' : 'python3';
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
    error_log("=== EJECUTAR_SCRAPER: Error DB: " . $e->getMessage());
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

$python_cmd = detectar_python_cmd();

chdir($ruta_base);

// --- Variables de entorno para el script Python ---
// Leer el .env de backend para pasar URLs/credenciales al script.
// Se aplica tanto en prod como en local si el archivo existe.
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

$cmd_env = '';
foreach ($env_vars as $key => $value) {
    // Escapar valores para shell
    $cmd_env .= "export $key=" . escapeshellarg($value) . "; ";
}

// --- Ejecución del bot ---
// Separamos stdout (donde el bot imprime su JSON) de stderr (logs INFO/ERROR).
// Si se mezclan con 2>&1 los logs pueden romper el parseo del JSON;
// acá redirigimos stderr a un archivo de log y dejamos stdout limpio.
$log_stderr = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'scraper_' . $id_jurisdiccion . '_' . date('Ymd_His') . '.log';

$comando = $cmd_env . escapeshellarg($python_cmd) . " " . escapeshellarg($nombre_script)
         . " " . escapeshellarg($id_jurisdiccion)
         . " " . escapeshellarg($jur['url_boletin'])
         . " 2>" . escapeshellarg($log_stderr);

error_log("=== EJECUTAR_SCRAPER: Comando: $comando");

$salida_stdout = shell_exec($comando);

// Guardar muestra del stdout para depuración.
error_log("=== EJECUTAR_SCRAPER ($nombre_script): stdout(0..500): " . substr((string)$salida_stdout, 0, 500));
error_log("=== EJECUTAR_SCRAPER ($nombre_script): stderr log en: $log_stderr");

$resultado = extraer_json_de_salida($salida_stdout);

if ($resultado !== null) {
    // El bot devolvió un JSON válido (success / warning / info / error).
    responder($resultado, 200);
} else {
    // No hubo JSON parseable: el bot murió antes de imprimir su resultado
    // (timeout, crash de Selenium, OOM...). Devolvemos un JSON de error con
    // pistas, pero SIN romper el contrato JSON con el frontend.
    $stderr_tail = '';
    if (is_file($log_stderr)) {
        $contenido = file_get_contents($log_stderr);
        $stderr_tail = substr(trim($contenido), -800); // últimas líneas del log
    }
    error_log("=== EJECUTAR_SCRAPER ($nombre_script): SIN JSON. stderr tail: " . $stderr_tail);
    responder([
        "status"  => "error",
        "message" => "El scraper no devolvió un resultado válido. Es posible que el proceso se haya interrumpido (revisar el log del servidor).",
        "detalle" => $stderr_tail
    ], 200);
}