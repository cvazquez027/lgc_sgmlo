<?php
require_once __DIR__ . '/../vendor/phpmailer/src/PHPMailer.php';
require_once __DIR__ . '/../vendor/phpmailer/src/SMTP.php';
require_once __DIR__ . '/../vendor/phpmailer/src/Exception.php';
require_once __DIR__ . '/EnvLoader.php';

EnvLoader::load(__DIR__ . '/.env');

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

class Mailer {
    private static $instance = null;
    private $mail;

    private function __construct() {
        EnvLoader::load(__DIR__ . '/../.env');

        $this->mail = new PHPMailer(true);
        $this->mail->isSMTP();
        $this->mail->Host       = getenv('SMTP_HOST');
        $this->mail->SMTPAuth   = true;
        $this->mail->Username   = getenv('SMTP_USER');
        $this->mail->Password   = getenv('SMTP_PASS');
        $this->mail->SMTPSecure = PHPMailer::ENCRYPTION_SMTPS;
        $this->mail->Port       = getenv('SMTP_PORT');
        $this->mail->setFrom(getenv('SMTP_USER'), 'SGMLO - Sistema de Alertas');
        $this->mail->isHTML(true);
        $this->mail->CharSet = 'UTF-8';
    }

    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    public function enviarAlerta($para, $nombre, $titulo, $mensaje, $url = null) {
        try {
            $this->mail->clearAddresses();
            $this->mail->addAddress($para, $nombre);

            $this->mail->Subject = "📢 SGMLO Alerta: $titulo";

            $app_url = rtrim(getenv('APP_URL') ?: 'http://localhost', '/');
            $link = $url ? "$app_url$url" : $app_url;

            $html = "
            <div style='font-family: Arial, sans-serif; max-width: 600px; margin:0 auto; border:1px solid #e0e0e0; border-top: 5px solid #005F78; padding:20px;'>
                <h2 style='color:#005F78;'>📌 $titulo</h2>
                <p style='font-size:16px; line-height:1.5;'>Hola <strong>$nombre</strong>,</p>
                <div style='background:#f8f9fa; padding:15px; border-left:4px solid #005F78; margin:15px 0;'>
                    $mensaje
                </div>
                <p style='font-size:14px;'>
                    <a href='$link' style='display:inline-block; background:#005F78; color:#fff; padding:10px 20px; text-decoration:none; border-radius:5px;'>Ver en el sistema</a>
                </p>
                <hr style='border:0; border-top:1px solid #eee; margin:20px 0;'>
                <p style='font-size:12px; color:#999;'>Este es un mensaje automático del sistema SGMLO. No respondas a este correo.</p>
            </div>";

            $this->mail->Body = $html;
            $this->mail->AltBody = "$titulo\n\n$mensaje\n\nVer más en: $link";

            return $this->mail->send();
        } catch (Exception $e) {
            error_log("Mailer: Error al enviar a $para: " . $e->getMessage());
            return false;
        }
    }
}