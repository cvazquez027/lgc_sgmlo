<?php
require_once __DIR__ . '/../config/Database.php';
require_once __DIR__ . '/../config/Mailer.php';

class AlertaHelper {

    /** Alertas cuyo envío de correo quedó diferido hasta después del commit */
    private static $pendientes = [];

    /** Caché de destinatarios por id_cliente (evita repetir la query dentro de bucles) */
    private static $cacheDestinatarios = [];

    /**
     * Inserta la alerta en BD y (opcionalmente) notifica por correo.
     *
     * @param bool $diferirEnvio  true  => solo inserta en BD y encola el correo.
     *                                     Llamar luego a enviarPendientes() DESPUÉS del commit.
     *                            false => comportamiento original (inserta y envía en el acto).
     */
    public static function insertarAlerta($db, $id_cliente, $id_matriz, $id_item_matriz, $tipo, $titulo, $mensaje, $url, $diferirEnvio = false) {
        // 1. Insertar en BD
        $stmt = $db->prepare("INSERT INTO alerta (id_cliente, id_matriz, id_item_matriz, tipo, titulo, mensaje, url, fecha_creacion, leido)
                              VALUES (:id_cliente, :id_matriz, :id_item, :tipo, :titulo, :mensaje, :url, NOW(), 0)");
        $ok = $stmt->execute([
            ':id_cliente' => $id_cliente,
            ':id_matriz'  => $id_matriz,
            ':id_item'    => $id_item_matriz,
            ':tipo'       => $tipo,
            ':titulo'     => $titulo,
            ':mensaje'    => $mensaje,
            ':url'        => $url
        ]);

        if (!$ok) {
            error_log("AlertaHelper: Falló la inserción en BD (cliente $id_cliente, tipo $tipo).");
            return false;
        }

        // 2. Notificación: diferida o inmediata
        if ($diferirEnvio) {
            self::$pendientes[] = [
                'id_cliente' => $id_cliente,
                'titulo'     => $titulo,
                'mensaje'    => $mensaje,
                'url'        => $url
            ];
            return true;
        }

        self::enviarCorreos($db, $id_cliente, $titulo, $mensaje, $url);
        return true;
    }

    /**
     * Envía los correos encolados. Llamar SIEMPRE fuera de la transacción (después del commit),
     * así el SMTP no mantiene abiertos los locks de la BD.
     *
     * @return int Cantidad de correos efectivamente enviados.
     */
    public static function enviarPendientes($db) {
        if (empty(self::$pendientes)) {
            return 0;
        }

        $pendientes = self::$pendientes;
        self::$pendientes = [];   // se vacía primero para evitar reenvíos si algo falla

        $enviados = 0;
        foreach ($pendientes as $p) {
            $enviados += self::enviarCorreos($db, $p['id_cliente'], $p['titulo'], $p['mensaje'], $p['url']);
        }
        return $enviados;
    }

    /** Descarta la cola de correos. Llamar tras un rollBack para no notificar algo que no se guardó. */
    public static function limpiarPendientes() {
        self::$pendientes = [];
        return true;
    }

    /** Cantidad de alertas encoladas pendientes de notificación. */
    public static function contarPendientes() {
        return count(self::$pendientes);
    }

    /**
     * Usuarios vigentes del cliente + admins suscritos. Resultado cacheado por request.
     */
    public static function obtenerDestinatarios($db, $id_cliente) {
        if (isset(self::$cacheDestinatarios[$id_cliente])) {
            return self::$cacheDestinatarios[$id_cliente];
        }

        // IMPORTANTE: con prepares nativos (ATTR_EMULATE_PREPARES = false) PDO no permite
        // reutilizar el mismo placeholder nombrado dentro de una query. Por eso se usan dos
        // placeholders distintos con el mismo valor. Reusar :id_cliente producía
        // SQLSTATE[HY093] Invalid parameter number.
        $query_usuarios = "
            SELECT email, nombre, apellido
            FROM usuario
            WHERE id_cliente = :id_cliente_1 AND vigente = 1
            UNION
            SELECT u.email, u.nombre, u.apellido
            FROM usuario u
            JOIN usuario_suscripcion_cliente s ON u.id_usuario = s.id_usuario
            WHERE s.id_cliente = :id_cliente_2 AND u.vigente = 1
        ";

        try {
            $stmt_usu = $db->prepare($query_usuarios);
            $stmt_usu->execute([
                ':id_cliente_1' => $id_cliente,
                ':id_cliente_2' => $id_cliente
            ]);
            $usuarios = $stmt_usu->fetchAll(PDO::FETCH_ASSOC);
        } catch (Throwable $e) {
            error_log("AlertaHelper: no se pudieron obtener destinatarios del cliente $id_cliente: " . $e->getMessage());
            $usuarios = [];
        }

        self::$cacheDestinatarios[$id_cliente] = $usuarios;
        return $usuarios;
    }

    /**
     * Envío real de los correos. Un fallo individual no corta el resto.
     */
    private static function enviarCorreos($db, $id_cliente, $titulo, $mensaje, $url) {
        $usuarios = self::obtenerDestinatarios($db, $id_cliente);
        if (empty($usuarios)) {
            return 0;
        }

        try {
            $mailer = Mailer::getInstance();
        } catch (Throwable $e) {
            error_log("AlertaHelper: no se pudo inicializar el Mailer: " . $e->getMessage());
            return 0;
        }

        $enviados = 0;
        foreach ($usuarios as $user) {
            try {
                $nombre_completo = trim($user['nombre'] . ' ' . $user['apellido']);
                $mailer->enviarAlerta($user['email'], $nombre_completo, $titulo, $mensaje, $url);
                $enviados++;
            } catch (Throwable $e) {
                error_log("AlertaHelper: falló el envío a {$user['email']}: " . $e->getMessage());
            }
        }
        return $enviados;
    }
}
