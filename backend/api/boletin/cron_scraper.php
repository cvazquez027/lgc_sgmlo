<?php
// cron_scraper.php – Ejecuta todos los scrapers activos (cron diario)
// Para depuración: php /var/www/matrizonline/backend/api/boletin/cron_scraper.php

header('Content-Type: application/json; charset=UTF-8');

// Usar __DIR__ para rutas absolutas
$baseDir = dirname(__DIR__, 2); // sube dos niveles desde /api/boletin/ a /backend/
$configPath = $baseDir . '/config/Database.php';

if (!file_exists($configPath)) {
    die("ERROR: No se encuentra Database.php en " . $configPath . "\n");
}

include_once $configPath;

$database = new Database();
$db = $database->getConnection();

// Obtener jurisdicciones con scraper habilitado y nombre_bot no nulo
$query = "SELECT id_jurisdiccion, descripcion, url_boletin, nombre_bot 
          FROM jurisdiccion 
          WHERE tiene_scraper = 1 AND nombre_bot IS NOT NULL";
$stmt = $db->prepare($query);
$stmt->execute();
$jurisdicciones = $stmt->fetchAll(PDO::FETCH_ASSOC);

if (empty($jurisdicciones)) {
    echo json_encode(['status' => 'info', 'message' => 'No hay scrapers configurados.']);
    exit();
}

$resultados = [];
$total_ok = 0;
$total_error = 0;

foreach ($jurisdicciones as $jur) {
    error_log("CRON_SCRAPER: Iniciando scraper para {$jur['descripcion']} (ID {$jur['id_jurisdiccion']})...");
    
    // Llamar al mismo endpoint que usa el frontend (ejecutar_scraper.php)
    $url = 'https://matrizonline.lamas-gc.com/backend/api/boletin/ejecutar_scraper.php';
    $payload = json_encode(['id_jurisdiccion' => (int)$jur['id_jurisdiccion']]);
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 600); // 10 minutos máximo por scraper
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    
    $respuesta = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_error = curl_error($ch);
    curl_close($ch);
    
    if ($curl_error) {
        $resultados[] = [
            'jurisdiccion' => $jur['descripcion'],
            'status' => 'ERROR',
            'curl_error' => $curl_error
        ];
        $total_error++;
        error_log("CRON_SCRAPER: Error CURL para {$jur['descripcion']}: $curl_error");
        continue;
    }
    
    $data = json_decode($respuesta, true);
    
    if ($http_code === 200 && isset($data['status']) && $data['status'] === 'success') {
        $resultados[] = [
            'jurisdiccion' => $jur['descripcion'],
            'status' => 'OK',
            'message' => $data['message'] ?? '',
            'total_enviadas' => $data['total_enviadas'] ?? 0,
            'procesadas' => $data['procesadas'] ?? 0,
            'errores' => $data['errores'] ?? 0
        ];
        $total_ok++;
        error_log("CRON_SCRAPER: OK para {$jur['descripcion']} - " . ($data['message'] ?? ''));
    } else {
        $resultados[] = [
            'jurisdiccion' => $jur['descripcion'],
            'status' => 'ERROR',
            'http_code' => $http_code,
            'respuesta' => $respuesta
        ];
        $total_error++;
        error_log("CRON_SCRAPER: ERROR HTTP $http_code para {$jur['descripcion']}: $respuesta");
    }
}

// Resumen
$resumen = [
    'status' => 'success',
    'message' => "Cron de scrapers ejecutado. OK: $total_ok, ERROR: $total_error",
    'total_ok' => $total_ok,
    'total_error' => $total_error,
    'resultados' => $resultados
];

echo json_encode($resumen, JSON_PRETTY_PRINT);
error_log("CRON_SCRAPER: Finalizado. " . json_encode($resumen));
?>