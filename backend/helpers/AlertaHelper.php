<?php
require_once __DIR__ . '/../config/Database.php';
require_once __DIR__ . '/../config/Mailer.php';

class AlertaHelper {
    /**
     * Inserta una alerta en la BD y envía correos a todos los usuarios vigentes del cliente.
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

        // 2. Obtener usuarios vigentes del cliente
        $query_usuarios = "SELECT u.email, u.nombre, u.apellido 
                           FROM usuario u
                           WHERE u.id_cliente = :id_cliente AND u.vigente = 1";
        $stmt_usu = $db->prepare($query_usuarios);
        $stmt_usu->execute([':id_cliente' => $id_cliente]);
        $usuarios = $stmt_usu->fetchAll(PDO::FETCH_ASSOC);

        if (empty($usuarios)) {
            error_log("AlertaHelper: No hay usuarios vigentes para el cliente $id_cliente.");
            return true; // No hay usuarios, pero la alerta ya está guardada
        }
        error_log("AlertaHelper: Se encontraron " . count($usuarios) . " usuarios para notificar.");

        // 3. Enviar correo a cada usuario
        try {
            $mailer = Mailer::getInstance();
            foreach ($usuarios as $user) {
                $email = $user['email'];
                $nombre_completo = trim($user['nombre'] . ' ' . $user['apellido']);
                error_log("AlertaHelper: Intentando enviar correo a $email");
                $resultado = $mailer->enviarAlerta($email, $nombre_completo, $titulo, $mensaje, $url);
                if ($resultado) {
                    error_log("AlertaHelper: Correo enviado a $email");
                } else {
                    error_log("AlertaHelper: FALLÓ el envío a $email");
                }
            }
        } catch (Exception $e) {
            error_log("AlertaHelper: Excepción al enviar correos: " . $e->getMessage());
        }

        return true;
    }
}