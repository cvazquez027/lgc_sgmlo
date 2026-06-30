<?php
// cron_scrapers.php – Ejecuta todos los scrapers activos (para cron diario)
header('Content-Type: application/json; charset=UTF-8');

include_once '../../config/Database.php';

$database = new Database();
$db = $database->getConnection();

// Obtener jurisdicciones con scraper habilitado
$query = "SELECT id_jurisdiccion, descripcion, url_boletin, nombre_bot 
          FROM jurisdiccion 
          WHERE tiene_scraper = 1 AND nombre_bot IS NOT NULL";
$stmt = $db->prepare($query);
$stmt->execute();
$jurisdicciones = $stmt->fetchAll(PDO::FETCH_ASSOC);

if (empty($jurisdicciones)) {
    echo json_encode(['status' => 'info', 'message' => 'No hay scrapers activos para ejecutar.']);
    exit();
}

$resultados = [];
$errores = 0;

foreach ($jurisdicciones as $jur) {
    error_log("CRON: Ejecutando scraper para {$jur['descripcion']} (ID {$jur['id_jurisdiccion']})...");
    
    // Llamar al mismo endpoint que usa el frontend
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, "https://matrizonline.lamas-gc.com/backend/api/boletin/ejecutar_scraper.php");
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(['id_jurisdiccion' => $jur['id_jurisdiccion']]));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 600); // 10 minutos por scraper
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false); // Hostinger puede requerir esto
    
    $respuesta = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_error = curl_error($ch);
    curl_close($ch);
    
    $resultado = [
        'jurisdiccion' => $jur['descripcion'],
        'http_code' => $http_code,
        'respuesta' => json_decode($respuesta, true)
    ];
    
    if ($http_code !== 200 || $curl_error) {
        $errores++;
        $resultado['error'] = $curl_error ?: 'HTTP ' . $http_code;
        error_log("CRON: ERROR en {$jur['descripcion']}: " . ($curl_error ?: "HTTP $http_code"));
    } else {
        error_log("CRON: OK en {$jur['descripcion']}");
    }
    
    $resultados[] = $resultado;
}

$mensaje = $errores === 0 
    ? "Todos los scrapers se ejecutaron correctamente." 
    : "Se completó con $errores error(es). Revisa los logs.";

echo json_encode([
    'status' => $errores === 0 ? 'success' : 'warning',
    'message' => $mensaje,
    'resultados' => $resultados
]);