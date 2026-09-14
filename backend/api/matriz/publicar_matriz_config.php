<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';
include_once '../../helpers/AlertaHelper.php';

$data = json_decode(file_get_contents("php://input"));

if (empty($data->id_matriz) || !isset($data->config_columnas)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan parámetros obligatorios."]);
    exit();
}

$id_matriz     = filter_var($data->id_matriz, FILTER_VALIDATE_INT);
$config_string = json_encode($data->config_columnas);

if ($id_matriz === false || $config_string === false || json_last_error() !== JSON_ERROR_NONE) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Datos inválidos o malformados."]);
    exit();
}

$db = null;

try {
    $database = new Database();
    $db = $database->getConnection();

    $db->beginTransaction();

    // 1. Obtener datos de la matriz (el FOR UPDATE bloquea solo la fila de 'matriz')
    $query_info = "SELECT id_cliente_establecimiento, id_tipo_matriz, id_especialidad_matriz, version, campo_encabezado_item
                   FROM matriz WHERE id_matriz = :id_matriz FOR UPDATE";
    $stmt_info = $db->prepare($query_info);
    $stmt_info->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    $stmt_info->execute();
    $matriz_actual = $stmt_info->fetch(PDO::FETCH_ASSOC);

    if (!$matriz_actual) {
        throw new Exception("La matriz solicitada no existe.");
    }

    // Validar que tenga al menos un ítem
    $query_items_count = "SELECT COUNT(*) FROM item_matriz WHERE id_matriz = :id_matriz";
    $stmt_count = $db->prepare($query_items_count);
    $stmt_count->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    $stmt_count->execute();
    $total_items = (int)$stmt_count->fetchColumn();

    if ($total_items === 0) {
        $db->rollBack();
        http_response_code(400);
        echo json_encode(["mensaje" => "No se puede publicar la matriz porque no tiene ningún ítem asociado. Agregue al menos un ítem antes de publicar."]);
        exit();
    }

    // 2. Archivar versión anterior publicada
    $query_archivar = "UPDATE matriz
                       SET id_estado_matriz = 3, vigente = 0
                       WHERE id_cliente_establecimiento = :est
                         AND id_tipo_matriz = :tipo
                         AND id_especialidad_matriz = :especialidad
                         AND id_estado_matriz = 2
                         AND id_matriz != :id_matriz";
    $stmt_archivar = $db->prepare($query_archivar);
    $stmt_archivar->execute([
        ':est'          => $matriz_actual['id_cliente_establecimiento'],
        ':tipo'         => $matriz_actual['id_tipo_matriz'],
        ':especialidad' => $matriz_actual['id_especialidad_matriz'],
        ':id_matriz'    => $id_matriz
    ]);

    // 3. Publicar la nueva matriz
    $query_publicar = "UPDATE matriz
                       SET id_estado_matriz = 2, vigente = 1, config_columnas = :config
                       WHERE id_matriz = :id_matriz";
    $stmt_publicar = $db->prepare($query_publicar);
    $stmt_publicar->bindParam(":config", $config_string, PDO::PARAM_STR);
    $stmt_publicar->bindParam(":id_matriz", $id_matriz, PDO::PARAM_INT);
    $stmt_publicar->execute();

    // 4. Cliente + nombre de la matriz en una sola consulta (antes eran dos)
    //    LEFT JOIN en tipo/especialidad para no perder el id_cliente si alguno faltara.
    $query_contexto = "SELECT ce.id_cliente,
                              CONCAT(tm.descripcion, ' - ', em.descripcion, ' - ', ce.descripcion) AS nombre_matriz
                       FROM matriz m
                       JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
                       LEFT JOIN tipo_matriz tm        ON m.id_tipo_matriz = tm.id_tipo_matriz
                       LEFT JOIN especialidad_matriz em ON m.id_especialidad_matriz = em.id_especialidad_matriz
                       WHERE m.id_matriz = :id_matriz";
    $stmt_contexto = $db->prepare($query_contexto);
    $stmt_contexto->execute([':id_matriz' => $id_matriz]);
    $contexto   = $stmt_contexto->fetch(PDO::FETCH_ASSOC);
    $id_cliente = $contexto ? $contexto['id_cliente'] : null;

    if ($id_cliente) {
        $nombre_matriz = (!empty($contexto['nombre_matriz'])) ? $contexto['nombre_matriz'] : "Matriz ID $id_matriz";
        $version       = $matriz_actual['version'];
        $titulo        = "Nueva versión de matriz publicada";
        $mensaje       = "La matriz \"{$nombre_matriz}\" ha sido publicada en su versión {$version}.0. Ya está disponible para consulta.";
        $url           = "/dashboard/matrices/{$id_matriz}";

        // Una alerta fallida NO debe tumbar la publicación: se registra en el log y se sigue.
        try {
            AlertaHelper::insertarAlerta($db, $id_cliente, $id_matriz, null, 'nueva_version_matriz', $titulo, $mensaje, $url, true);
        } catch (Throwable $e) {
            error_log("publicar_matriz_config: alerta de publicación fallida (matriz $id_matriz): " . $e->getMessage());
        }

        // 5. Vencimientos próximos (zona horaria Argentina)
        //    El NOT EXISTS reemplaza la consulta de duplicados que antes corría una vez por ítem.
        $campo_encabezado = $matriz_actual['campo_encabezado_item'] ?? 'resumen_legal';

        $query_items = "SELECT im.id_item_matriz, im.vencimiento_plazo, im.resumen_legal, im.datos_dinamicos
                        FROM item_matriz im
                        WHERE im.id_matriz = :id_matriz
                          AND im.vencimiento_plazo IS NOT NULL
                          AND im.vencimiento_plazo BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                          AND NOT EXISTS (
                                SELECT 1 FROM alerta a
                                WHERE a.id_item_matriz = im.id_item_matriz
                                  AND a.tipo = 'vencimiento_proximo'
                                  AND a.fecha_creacion > DATE_SUB(NOW(), INTERVAL 7 DAY)
                          )";
        $stmt_venc = $db->prepare($query_items);
        $stmt_venc->execute([':id_matriz' => $id_matriz]);
        $items_venc = $stmt_venc->fetchAll(PDO::FETCH_ASSOC);

        if (!empty($items_venc)) {

            // Normas de todos los ítems en una sola consulta (antes: una por ítem).
            // Nota: GROUP_CONCAT trunca a group_concat_max_len (1024 por defecto).
            $normas_por_item = [];
            if ($campo_encabezado === 'normas') {
                $ids_items    = array_column($items_venc, 'id_item_matriz');
                $placeholders = implode(',', array_fill(0, count($ids_items), '?'));

                $query_normas = "SELECT imn.id_item_matriz,
                                        GROUP_CONCAT(CONCAT(tn.descripcion, ' ', n.numero, '/', n.anio)
                                                     ORDER BY n.anio, n.numero SEPARATOR ', ') AS normas_text
                                 FROM item_matriz_norma imn
                                 JOIN norma n      ON imn.id_norma = n.id_norma
                                 JOIN tipo_norma tn ON n.id_tipo_norma = tn.id_tipo_norma
                                 WHERE imn.id_item_matriz IN ($placeholders)
                                 GROUP BY imn.id_item_matriz";
                $stmt_normas = $db->prepare($query_normas);
                $stmt_normas->execute($ids_items);
                foreach ($stmt_normas->fetchAll(PDO::FETCH_ASSOC) as $fila) {
                    $normas_por_item[$fila['id_item_matriz']] = $fila['normas_text'];
                }
            }

            $tz  = new DateTimeZone('America/Argentina/Buenos_Aires');
            $hoy = new DateTime('today', $tz);

            foreach ($items_venc as $item) {
                // Descripción del ítem según campo_encabezado
                if ($campo_encabezado === 'normas') {
                    $descripcion_item = $normas_por_item[$item['id_item_matriz']] ?? '';
                } elseif ($campo_encabezado === 'resumen_legal') {
                    $descripcion_item = $item['resumen_legal'];
                } elseif (strpos($campo_encabezado, 'custom_') === 0) {
                    $dinamicos        = json_decode($item['datos_dinamicos'], true);
                    $descripcion_item = isset($dinamicos[$campo_encabezado]) ? $dinamicos[$campo_encabezado] : $item['resumen_legal'];
                } else {
                    $descripcion_item = $item[$campo_encabezado] ?? $item['resumen_legal'];
                }
                if (empty($descripcion_item)) {
                    $descripcion_item = $item['resumen_legal'] ?: 'Ítem sin descripción';
                }

                $fecha_formateada = date('d/m/Y', strtotime($item['vencimiento_plazo']));

                $venc = new DateTime($item['vencimiento_plazo'], $tz);
                $venc->setTime(0, 0, 0);
                $dias = (int)$hoy->diff($venc)->format('%r%a');

                if ($dias >= 0 && $dias <= 30) {
                    $titulo_venc  = "Vencimiento próximo";
                    $mensaje_venc = ($dias == 0)
                        ? "El ítem \"{$descripcion_item}\" vence HOY ({$fecha_formateada})."
                        : "El ítem \"{$descripcion_item}\" tiene vencimiento el {$fecha_formateada} (dentro de {$dias} días).";
                    $url_venc = "/dashboard/matrices/{$id_matriz}?item={$item['id_item_matriz']}";

                    try {
                        AlertaHelper::insertarAlerta($db, $id_cliente, $id_matriz, $item['id_item_matriz'], 'vencimiento_proximo', $titulo_venc, $mensaje_venc, $url_venc, true);
                    } catch (Throwable $e) {
                        error_log("publicar_matriz_config: alerta de vencimiento fallida (ítem {$item['id_item_matriz']}): " . $e->getMessage());
                    }
                }
            }
        }
    }

    $db->commit();

    // 6. Correos FUERA de la transacción: el SMTP ya no mantiene locks abiertos
    //    ni puede hacer fallar una publicación que ya está confirmada.
    try {
        AlertaHelper::enviarPendientes($db);
    } catch (Throwable $e) {
        error_log("publicar_matriz_config: fallo al notificar por correo (matriz $id_matriz): " . $e->getMessage());
    }

    http_response_code(200);
    echo json_encode(["mensaje" => "Matriz publicada exitosamente. La versión anterior ha sido archivada."]);

} catch (Throwable $e) {
    if ($db instanceof PDO && $db->inTransaction()) {
        $db->rollBack();
    }
    AlertaHelper::limpiarPendientes();   // no notificar algo que se revirtió

    error_log("publicar_matriz_config: " . $e->getMessage() . " en " . $e->getFile() . ":" . $e->getLine());

    http_response_code(500);
    echo json_encode(["mensaje" => "Error interno al publicar.", "error" => $e->getMessage()]);
}
