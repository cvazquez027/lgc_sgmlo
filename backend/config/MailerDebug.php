<?php
require_once __DIR__ . '/../vendor/autoload.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

class MailerDebug {
    private $mail;

    public function __construct() {
        $this->mail = new PHPMailer(true);
        $this->mail->isSMTP();
        // HARDCODEAR CREDENCIALES TEMPORALMENTE (cambiar por las reales de Hostinger)
        $this->mail->Host       = 'smtp.hostinger.com'; // o el que uses
        $this->mail->SMTPAuth   = true;
        $this->mail->Username   = 'info@lamas-gc.com'; // CAMBIAR
        $this->mail->Password   = 'L03g01c02.2026'; // CAMBIAR
        $this->mail->SMTPSecure = PHPMailer::ENCRYPTION_SMTPS;
        $this->mail->Port       = 465;
        $this->mail->setFrom('info@lamas-gc.com', 'SGMLO Debug');
        $this->mail->isHTML(true);
        $this->mail->CharSet = 'UTF-8';
    }

    public function enviar($para, $nombre, $titulo, $mensaje, $url = null) {
        try {
            $this->mail->clearAddresses();
            $this->mail->addAddress($para, $nombre);
            $this->mail->Subject = "📢 Debug SGMLO: $titulo";

            $app_url = 'https://matrizonline.lamas-gc.com'; // HARDCODEAR
            $link = $url ? $app_url . $url : $app_url;

            $html = "<div style='font-family:Arial;max-width:600px;margin:0 auto;border-top:5px solid #005F78;padding:20px;'>
                <h2 style='color:#005F78;'>📌 $titulo</h2>
                <p>Hola <strong>$nombre</strong>,</p>
                <div style='background:#f8f9fa;padding:15px;border-left:4px solid #005F78;margin:15px 0;'>$mensaje</div>
                <p><a href='$link' style='display:inline-block;background:#005F78;color:#fff;padding:10px 20px;text-decoration:none;border-radius:5px;'>Ver en el sistema</a></p>
                <hr><p style='font-size:12px;color:#999;'>Mensaje automático de SGMLO.</p>
            </div>";

            $this->mail->Body = $html;
            $this->mail->AltBody = "$titulo\n\n$mensaje\n\nVer más en: $link";
            return $this->mail->send();
        } catch (Exception $e) {
            return "ERROR: " . $e->getMessage();
        }
    }
}