<?php
// Cargar EnvLoader
require_once __DIR__ . '/config/EnvLoader.php';
EnvLoader::load(__DIR__);

// Cargar Mailer
require_once __DIR__ . '/config/Mailer.php';

echo "=== PRUEBA DE ENVÍO SMTP ===\n";
echo "SMTP_HOST: " . getenv('SMTP_HOST') . "\n";
echo "SMTP_USER: " . getenv('SMTP_USER') . "\n";
echo "SMTP_PORT: " . getenv('SMTP_PORT') . "\n";
echo "SMTP_PASS: " . (getenv('SMTP_PASS') ? '*** configurada ***' : 'NO CONFIGURADA') . "\n\n";

$mailer = Mailer::getInstance();
$resultado = $mailer->enviarAlerta(
    'christian@datav.com.ar',
    'Christian',
    'Prueba desde Hostinger',
    'Este es un mensaje de prueba para verificar la configuración SMTP.',
    '/dashboard'
);

if ($resultado) {
    echo "✅ Correo enviado correctamente a christian@datav.com.ar\n";
} else {
    echo "❌ Falló el envío. Revisá los logs de error.\n";
}
?>