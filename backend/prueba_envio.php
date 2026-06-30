<?php
require_once 'config/Mailer.php';

$mailer = Mailer::getInstance();
$resultado = $mailer->enviarAlerta(
    'christian@datav.com.ar',
    'Christian',
    'Prueba desde SGMLO',
    'Este es un correo de prueba. Si llega, la configuración SMTP está correcta.',
    '/dashboard'
);

echo $resultado ? "✅ Correo enviado" : "❌ Falló el envío, revisá logs.";
?>