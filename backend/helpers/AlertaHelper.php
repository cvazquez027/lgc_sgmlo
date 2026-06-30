<?php
require_once __DIR__ . '/../config/Database.php';
require_once __DIR__ . '/../config/Mailer.php';

class AlertaHelper {
    /**
     * Inserta una alerta en la BD y envía correo a christian@datav.com.ar (pruebas)
     */
    public static function insertarAlerta($db, $id_cliente, $id_matriz, $id_item_matriz, $tipo, $titulo, $mensaje, $url) {
        // 1. Insertar en BD
        $stmt = $db->prepare("INSERT INTO alerta (id_cliente, id_matriz, id_item_matriz, tipo, titulo, mensaje, url, fecha_creacion, leido)
                              VALUES (:id_cliente, :id_matriz, :id_item, :tipo, :titulo, :mensaje, :url, NOW(), 0)");
        $ok = $stmt->execute([
            ':id_cliente' => $id_cliente,
            ':id_matriz' => $id_matriz,
            ':id_item' => $id_item_matriz,
            ':tipo' => $tipo,
            ':titulo' => $titulo,
            ':mensaje' => $mensaje,
            ':url' => $url
        ]);
        if (!$ok) {
            error_log("AlertaHelper: Falló la inserción en BD.");
            return false;
        }
        error_log("AlertaHelper: Alerta insertada en BD (ID cliente: $id_cliente, tipo: $tipo)");

        // 2. Enviar correo SOLO a christian@datav.com.ar (para pruebas)
        try {
            $mailer = Mailer::getInstance();
            $email = 'christian@datav.com.ar';
            $nombre = 'Christian Vazquez';
            error_log("AlertaHelper: Intentando enviar correo a $email");
            $resultado = $mailer->enviarAlerta($email, $nombre, $titulo, $mensaje, $url);
            if ($resultado) {
                error_log("AlertaHelper: Correo enviado a $email");
            } else {
                error_log("AlertaHelper: FALLÓ el envío a $email");
            }
        } catch (Exception $e) {
            error_log("AlertaHelper: Excepción al enviar correo: " . $e->getMessage());
        }

        return true;
    }
}