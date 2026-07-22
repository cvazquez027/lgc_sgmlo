<?php
/**
 * cron_scraper.php – Ejecuta todos los scrapers activos (cron diario)
 *
 * Uso:
 *   php /var/www/matrizonline/backend/api/boletin/cron_scraper.php
 *
 * -------------------------------------------------------------------------
 * POR QUÉ EJECUTA PYTHON DIRECTAMENTE Y NO POR HTTP
 * -------------------------------------------------------------------------
 * La versión anterior llamaba por cURL a ejecutar_scraper.php, o sea que el
 * cron (que ya corre en el servidor) daba una vuelta innecesaria por el
 * servidor web. Eso funcionaba para los bots rápidos, pero rompía con los que
 * hacen OCR: el bot de Chaco procesa cientos de páginas escaneadas y tarda
 * bastante más que el CURLOPT_TIMEOUT de 600s. Peor todavía, aunque
 * ejecutar_scraper.php declare set_time_limit(0), eso NO anula los timeouts de
 * PHP-FPM (request_terminate_timeout) ni de nginx/Apache
 * (fastcgi_read_timeout / proxy_read_timeout), que suelen estar en 60-300s y
 * matan el proceso igual.
 *
 * Ejecutando el intérprete directamente desde CLI no interviene ningún
 * servidor web, así que no hay más timeouts que el que fijamos acá.
 *
 * ejecutar_scraper.php SIGUE siendo el camino del frontend (botón "ejecutar"),
 * no se toca. Este archivo replica su lógica de armado del comando para que
 * ambos entornos se comporten igual.
 * -------------------------------------------------------------------------
 */

set_time_limit(0);

// Tiempo máximo por bot. Chaco con OCR de ~300 páginas puede tardar bastante;
// el resto termina en segundos. Si un bot se pasa, se lo mata y se sigue con
// el siguiente (nunca se cuelga el cron entero).
$TIMEOUT_BOT = (int)(getenv('SCRAPER_TIMEOUT_BOT') ?: 5400);   // 90 min

$esCli = (php_sapi_name() === 'cli');
if (!$esCli) {
    // Se puede abrir desde el navegador para una prueba rápida, pero los bots
    // largos van a morir por timeout del servidor web. Avisamos en la salida.
    header('Content-Type: application/json; charset=UTF-8');
}

$baseDir    = dirname(__DIR__, 2);              // .../backend
$configPath = $baseDir . '/config/Database.php';
$rutaScripts = $baseDir . '/scripts/';

if (!file_exists($configPath)) {
    fwrite(STDERR, "ERROR: No se encuentra Database.php en $configPath\n");
    echo json_encode(['status' => 'error', 'message' => "No se encuentra Database.php en $configPath"]);
    exit(1);
}

include_once $configPath;

$database = new Database();
$db = $database->getConnection();

$query = "SELECT id_jurisdiccion, descripcion, url_boletin, nombre_bot
          FROM jurisdiccion
          WHERE tiene_scraper = 1 AND nombre_bot IS NOT NULL";
$stmt = $db->prepare($query);
$stmt->execute();
$jurisdicciones = $stmt->fetchAll(PDO::FETCH_ASSOC);

if (empty($jurisdicciones)) {
    echo json_encode(['status' => 'info', 'message' => 'No hay scrapers configurados.']);
    exit(0);
}


/**
 * Intérprete de Python a usar. Mismas rutas que ejecutar_scraper.php para que
 * el cron y el frontend usen exactamente el mismo entorno.
 */
function detectar_python_cmd($baseDir)
{
    $candidatos = [
        '/var/www/matrizonline/backend/.venv/bin/python',  // venv de producción
        $baseDir . '/.venv/bin/python',                    // venv relativo al deploy
    ];
    foreach ($candidatos as $p) {
        if (file_exists($p)) {
            return $p;
        }
    }
    return (stripos(PHP_OS, 'WIN') === 0) ? 'python' : 'python3';
}


/**
 * Lee el .env de backend y devuelve los pares clave/valor, quitando las
 * comillas que suelen envolver los valores.
 */
function cargar_env($baseDir)
{
    $envFile = $baseDir . '/.env';
    $vars = [];
    if (!file_exists($envFile)) {
        return $vars;
    }
    $lineas = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lineas as $linea) {
        $linea = trim($linea);
        if ($linea === '' || strpos($linea, '#') === 0 || strpos($linea, '=') === false) {
            continue;
        }
        list($nombre, $valor) = explode('=', $linea, 2);
        $nombre = trim($nombre);
        $valor  = trim($valor);
        // quitar comillas envolventes: FOO="bar"  ->  bar
        if (strlen($valor) >= 2) {
            $ini = $valor[0];
            $fin = substr($valor, -1);
            if (($ini === '"' && $fin === '"') || ($ini === "'" && $fin === "'")) {
                $valor = substr($valor, 1, -1);
            }
        }
        $vars[$nombre] = $valor;
    }
    return $vars;
}


$python_cmd = detectar_python_cmd($baseDir);
$env_vars   = cargar_env($baseDir);

// Prefijo de variables de entorno para el comando. En Linux (que es donde
// corre el cron) /bin/sh entiende 'export'.
$cmd_env = '';
foreach ($env_vars as $clave => $valor) {
    $cmd_env .= 'export ' . $clave . '=' . escapeshellarg($valor) . '; ';
}

// ¿Está disponible `timeout` (coreutils)? Es lo que garantiza que un bot
// trabado no deje el cron colgado para siempre.
$tiene_timeout = (trim((string)shell_exec('command -v timeout 2>/dev/null')) !== '');

$resultados  = [];
$total_ok    = 0;
$total_error = 0;

foreach ($jurisdicciones as $jur) {
    $id     = (int)$jur['id_jurisdiccion'];
    $nombre = $jur['descripcion'];
    $script = $jur['nombre_bot'];
    $url    = (string)$jur['url_boletin'];

    error_log("CRON_SCRAPER: Iniciando $nombre (ID $id) -> $script");

    $rutaScript = $rutaScripts . $script;
    if (!file_exists($rutaScript)) {
        $resultados[] = [
            'jurisdiccion' => $nombre,
            'status'  => 'ERROR',
            'message' => "No se encontró el script '$script' en $rutaScripts",
        ];
        $total_error++;
        error_log("CRON_SCRAPER: ERROR - script inexistente: $rutaScript");
        continue;
    }

    // stderr va a un log aparte: el bot imprime su JSON por stdout y los
    // mensajes de progreso por stderr. Si se mezclaran, el JSON no parsea.
    $logStderr = sys_get_temp_dir() . DIRECTORY_SEPARATOR
               . 'scraper_' . $id . '_' . date('Ymd_His') . '.log';

    $prefijo_timeout = $tiene_timeout ? ('timeout ' . $TIMEOUT_BOT . 's ') : '';

    $comando = 'cd ' . escapeshellarg($rutaScripts) . '; '
             . $cmd_env
             . $prefijo_timeout
             . escapeshellarg($python_cmd) . ' '
             . escapeshellarg($script) . ' '
             . escapeshellarg((string)$id) . ' '
             . escapeshellarg($url)
             . ' 2>' . escapeshellarg($logStderr);

    $inicio = microtime(true);
    $lineas = [];
    $rc = 0;
    exec($comando, $lineas, $rc);
    $segundos = round(microtime(true) - $inicio, 1);

    $stdout = trim(implode("\n", $lineas));
    $data   = json_decode($stdout, true);

    if ($rc === 124) {
        // 124 = `timeout` mató el proceso
        $resultados[] = [
            'jurisdiccion' => $nombre,
            'status'   => 'ERROR',
            'message'  => "El bot superó el límite de {$TIMEOUT_BOT}s y fue interrumpido.",
            'segundos' => $segundos,
            'log'      => $logStderr,
        ];
        $total_error++;
        error_log("CRON_SCRAPER: TIMEOUT en $nombre tras {$segundos}s. Log: $logStderr");
        continue;
    }

    if (!is_array($data) || !isset($data['status'])) {
        $resultados[] = [
            'jurisdiccion' => $nombre,
            'status'   => 'ERROR',
            'message'  => 'El scraper no devolvió un JSON válido.',
            'exit_code' => $rc,
            'stdout'   => mb_substr($stdout, 0, 500),
            'segundos' => $segundos,
            'log'      => $logStderr,
        ];
        $total_error++;
        error_log("CRON_SCRAPER: ERROR en $nombre (exit $rc). Log: $logStderr");
        continue;
    }

    if ($data['status'] === 'success') {
        $resultados[] = [
            'jurisdiccion'   => $nombre,
            'status'         => 'OK',
            'message'        => $data['message'] ?? '',
            'total_enviadas' => $data['total_enviadas'] ?? 0,
            'segundos'       => $segundos,
        ];
        $total_ok++;
        error_log("CRON_SCRAPER: OK $nombre ({$segundos}s) - " . ($data['message'] ?? ''));
    } else {
        // info / warning / error informados por el propio bot
        $esFallo = ($data['status'] === 'error');
        $resultados[] = [
            'jurisdiccion' => $nombre,
            'status'   => strtoupper($data['status']),
            'message'  => $data['message'] ?? '',
            'segundos' => $segundos,
            'log'      => $esFallo ? $logStderr : null,
        ];
        if ($esFallo) {
            $total_error++;
        } else {
            $total_ok++;   // 'info'/'warning' no son fallas (p.ej. boletín ya procesado)
        }
        error_log("CRON_SCRAPER: {$data['status']} en $nombre - " . ($data['message'] ?? ''));
    }
}

$resumen = [
    'status'      => 'success',
    'message'     => "Cron de scrapers ejecutado. OK: $total_ok, ERROR: $total_error",
    'fecha'       => date('Y-m-d H:i:s'),
    'total_ok'    => $total_ok,
    'total_error' => $total_error,
    'resultados'  => $resultados,
];

echo json_encode($resumen, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n";
error_log('CRON_SCRAPER: Finalizado. ' . json_encode($resumen, JSON_UNESCAPED_UNICODE));