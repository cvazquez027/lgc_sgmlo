<?php
// 1. Forzar a PHP a mostrar errores en lugar de quedarse en blanco
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// 2. Cabeceras CORS
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// 3. Armar ruta dinámica
$ruta_script = "C:/xampp/htdocs/lgc_sgmlo/backend/scripts/bot_nacion.py";

// Verificamos que el archivo de Python exista
if (!file_exists($ruta_script)) {
    echo json_encode(["status" => "error", "message" => "No se encontró el script en: " . $ruta_script]);
    exit();
}

// 4. EL FIX MÁGICO: Mover a PHP a la carpeta del script antes de ejecutar
$directorio_script = dirname($ruta_script);
chdir($directorio_script); 

// 5. Ejecutar el comando (usamos 'python' para Windows/XAMPP. En el VPS cambialo a 'python3')
// Usamos basename() porque ya estamos ubicados en la carpeta gracias al chdir()
$comando = "python " . escapeshellarg(basename($ruta_script)) . " 2>&1";
$salida = shell_exec($comando);

// 6. LA CURA PARA WINDOWS: Forzar la salida a UTF-8 para que json_encode no se rompa
if ($salida !== null) {
    if (function_exists('mb_convert_encoding')) {
        $salida = mb_convert_encoding($salida, 'UTF-8', 'auto');
    } else {
        $salida = utf8_encode($salida);
    }
}

// 7. Preparar la respuesta
$respuesta = [
    "status" => $salida === null ? "error" : "success",
    "message" => $salida === null ? "No se pudo ejecutar el script." : "Ejecución finalizada.",
    "log" => $salida
];

// 8. Intentar crear el JSON y atrapar el error si vuelve a fallar
$json = json_encode($respuesta);

if ($json === false) {
    // Si json_encode falla por caracteres muy extraños, devolvemos un JSON armado a mano
    echo '{"status": "error", "message": "Error de codificación en PHP: ' . json_last_error_msg() . '"}';
} else {
    echo $json;
}
?>