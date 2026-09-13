<?php
require_once __DIR__ . '/../config/Database.php';
require_once __DIR__ . '/../config/Mailer.php';

class AlertaHelper {
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

        // 2. Obtener usuarios vigentes del cliente + Admins suscritos
        $query_usuarios = "
            SELECT email, nombre, apellido 
            FROM usuario 
            WHERE id_cliente = :id_cliente AND vigente = 1
            UNION
            SELECT u.email, u.nombre, u.apellido 
            FROM usuario u
            JOIN usuario_suscripcion_cliente s ON u.id_usuario = s.id_usuario
            WHERE s.id_cliente = :id_cliente AND u.vigente = 1
        ";
        $stmt_usu = $db->prepare($query_usuarios);
        $stmt_usu->execute([':id_cliente' => $id_cliente]);
        $usuarios = $stmt_usu->fetchAll(PDO::FETCH_ASSOC);

        if (empty($usuarios)) {
            return true; 
        }

        // 3. Enviar correo a cada usuario
        try {
            $mailer = Mailer::getInstance();
            foreach ($usuarios as $user) {
                $email = $user['email'];
                $nombre_completo = trim($user['nombre'] . ' ' . $user['apellido']);
                $mailer->enviarAlerta($email, $nombre_completo, $titulo, $mensaje, $url);
            }
        } catch (Exception $e) {
            error_log("AlertaHelper: Excepción al enviar correos: " . $e->getMessage());
        }

        return true;
    }
}