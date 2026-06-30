<?php
require_once __DIR__ . '/../config/MailerDebug.php';

class AlertaHelperDebug {
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
        if (!$ok) return false;

        // 2. Obtener usuarios (solo para debug, enviaremos a uno fijo)
        $query_usuarios = "SELECT u.email, u.nombre, u.apellido 
                           FROM usuario u
                           WHERE u.id_cliente = :id_cliente AND u.vigente = 1";
        $stmt_usu = $db->prepare($query_usuarios);
        $stmt_usu->execute([':id_cliente' => $id_cliente]);
        $usuarios = $stmt_usu->fetchAll(PDO::FETCH_ASSOC);

        // 3. Enviar correo a TODOS los usuarios (o al menos a christian@datav.com.ar)
        $mailer = new MailerDebug();
        $resultados = [];
        foreach ($usuarios as $user) {
            $nombre_completo = trim($user['nombre'] . ' ' . $user['apellido']);
            $res = $mailer->enviar($user['email'], $nombre_completo, $titulo, $mensaje, $url);
            $resultados[] = ["email" => $user['email'], "resultado" => $res];
        }
        return $resultados;
    }
}