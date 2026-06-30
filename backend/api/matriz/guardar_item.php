<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(200); exit(); }

// ACTIVAR ERRORES PARA DEPURAR EN RESPUESTA JSON
ini_set('display_errors', 0); // No mostrar en pantalla
error_reporting(E_ALL);
ini_set('log_errors', 1);

include_once '../../config/Database.php';
include_once '../../helpers/AlertaHelperDebug.php'; // VERSIÓN DEBUG

$data = json_decode(file_get_contents("php://input"));

if (empty($data->id_matriz)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Falta la Matriz asociada."]);
    exit();
}

$database = new Database();
$db = $database->getConnection();

$id_item_matriz = !empty($data->id_item_matriz) ? (int)$data->id_item_matriz : null;
$id_matriz = (int)$data->id_matriz;

$resumen_legal = !empty($data->resumen_legal) ? htmlspecialchars(strip_tags(trim($data->resumen_legal))) : null;
$id_estado_cumplimiento = !empty($data->id_estado_cumplimiento) ? (int)$data->id_estado_cumplimiento : 1;
$articulos_aplicables = !empty($data->articulos_aplicables) ? htmlspecialchars(strip_tags(trim($data->articulos_aplicables))) : null;
$interpretacion_aplicacion = !empty($data->interpretacion_aplicacion) ? htmlspecialchars(strip_tags(trim($data->interpretacion_aplicacion))) : null;
$id_tipo_modalidad = !empty($data->id_tipo_modalidad) ? (int)$data->id_tipo_modalidad : null;
$obs_modalidad = !empty($data->obs_modalidad) ? htmlspecialchars(strip_tags(trim($data->obs_modalidad))) : null;
$evidencia_cumplimiento = !empty($data->evidencia_cumplimiento) ? htmlspecialchars(strip_tags(trim($data->evidencia_cumplimiento))) : null;
$verificacion_cumplimiento = !empty($data->verificacion_cumplimiento) ? htmlspecialchars(strip_tags(trim($data->verificacion_cumplimiento))) : null;
$obs_estado_cumplimiento = !empty($data->obs_estado_cumplimiento) ? htmlspecialchars(strip_tags(trim($data->obs_estado_cumplimiento))) : null;
$id_responsable_establecimiento = !empty($data->id_responsable_establecimiento) ? (int)$data->id_responsable_establecimiento : null;
$vencimiento_plazo = (!empty($data->vencimiento_plazo)) ? $data->vencimiento_plazo : null;
$fecha_cumplimiento = (!empty($data->fecha_cumplimiento)) ? $data->fecha_cumplimiento : null;

$dinamicos = [];
foreach ($data as $key => $value) {
    if (strpos($key, 'custom_') === 0) {
        $dinamicos[$key] = htmlspecialchars(strip_tags(trim($value)));
    }
}
$datos_dinamicos = !empty($dinamicos) ? json_encode($dinamicos) : null;

$normas_vinculadas = (isset($data->normas_vinculadas) && is_array($data->normas_vinculadas)) ? $data->normas_vinculadas : [];

$es_nuevo = false;
$estado_anterior = null;
$responsable_anterior = null;
$vencimiento_anterior = null;
$id_cliente = null;
$matriz_publicada = false;
$campo_encabezado = 'resumen_legal';

try {
    $db->beginTransaction();

    // Obtener datos de la matriz
    $query_matriz = "SELECT m.id_cliente_establecimiento, m.id_estado_matriz, m.campo_encabezado_item, ce.id_cliente
                     FROM matriz m
                     JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
                     WHERE m.id_matriz = :id_matriz";
    $stmt_matriz = $db->prepare($query_matriz);
    $stmt_matriz->execute([':id_matriz' => $id_matriz]);
    $matriz_data = $stmt_matriz->fetch(PDO::FETCH_ASSOC);
    if (!$matriz_data) {
        throw new Exception("Matriz no encontrada.");
    }
    $id_cliente = (int)$matriz_data['id_cliente'];
    $matriz_publicada = ($matriz_data['id_estado_matriz'] == 2);
    $campo_encabezado = $matriz_data['campo_encabezado_item'] ?? 'resumen_legal';

    // Obtener valores actuales del ítem si es UPDATE
    if ($id_item_matriz) {
        $query_old = "SELECT id_estado_cumplimiento, id_responsable_establecimiento, vencimiento_plazo, resumen_legal, datos_dinamicos
                      FROM item_matriz WHERE id_item_matriz = :id_item";
        $stmt_old = $db->prepare($query_old);
        $stmt_old->execute([':id_item' => $id_item_matriz]);
        $old_data = $stmt_old->fetch(PDO::FETCH_ASSOC);
        if ($old_data) {
            $estado_anterior = (int)$old_data['id_estado_cumplimiento'];
            $responsable_anterior = $old_data['id_responsable_establecimiento'] ? (int)$old_data['id_responsable_establecimiento'] : null;
            $vencimiento_anterior = $old_data['vencimiento_plazo'];
        }
    }

    // Guardar ítem
    if ($id_item_matriz) {
        $query_item = "UPDATE item_matriz SET 
                        id_matriz = :id_matriz, resumen_legal = :resumen_legal, articulos_aplicables = :articulos_aplicables,
                        interpretacion_aplicacion = :interpretacion_aplicacion, id_tipo_modalidad = :id_tipo_modalidad,
                        obs_modalidad = :obs_modalidad, vencimiento_plazo = :vencimiento_plazo, fecha_cumplimiento = :fecha_cumplimiento,
                        evidencia_cumplimiento = :evidencia_cumplimiento, verificacion_cumplimiento = :verificacion_cumplimiento,
                        id_estado_cumplimiento = :id_estado_cumplimiento, obs_estado_cumplimiento = :obs_estado_cumplimiento,
                        id_responsable_establecimiento = :id_responsable, datos_dinamicos = :datos_dinamicos
                       WHERE id_item_matriz = :id_item_matriz";
        $stmt = $db->prepare($query_item);
        $stmt->bindValue(":id_item_matriz", $id_item_matriz, PDO::PARAM_INT);
    } else {
        $query_max_orden = "SELECT COALESCE(MAX(orden), -1) + 1 AS siguiente_orden FROM item_matriz WHERE id_matriz = :id_matriz";
        $stmt_max = $db->prepare($query_max_orden);
        $stmt_max->execute([':id_matriz' => $id_matriz]);
        $siguiente_orden = (int)$stmt_max->fetchColumn();

        $query_item = "INSERT INTO item_matriz 
                        (id_matriz, orden, resumen_legal, articulos_aplicables, interpretacion_aplicacion, id_tipo_modalidad, obs_modalidad, 
                         vencimiento_plazo, fecha_cumplimiento, evidencia_cumplimiento, verificacion_cumplimiento, 
                         id_estado_cumplimiento, obs_estado_cumplimiento, id_responsable_establecimiento, datos_dinamicos)
                       VALUES 
                        (:id_matriz, :orden, :resumen_legal, :articulos_aplicables, :interpretacion_aplicacion, :id_tipo_modalidad, :obs_modalidad, 
                         :vencimiento_plazo, :fecha_cumplimiento, :evidencia_cumplimiento, :verificacion_cumplimiento, 
                         :id_estado_cumplimiento, :obs_estado_cumplimiento, :id_responsable, :datos_dinamicos)";
        $stmt = $db->prepare($query_item);
        $stmt->bindValue(":orden", $siguiente_orden, PDO::PARAM_INT);
        $es_nuevo = true;
    }

    $stmt->bindValue(":id_matriz", $id_matriz, PDO::PARAM_INT);
    $stmt->bindValue(":resumen_legal", $resumen_legal, is_null($resumen_legal) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":articulos_aplicables", $articulos_aplicables, is_null($articulos_aplicables) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":interpretacion_aplicacion", $interpretacion_aplicacion, is_null($interpretacion_aplicacion) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":id_tipo_modalidad", $id_tipo_modalidad, is_null($id_tipo_modalidad) ? PDO::PARAM_NULL : PDO::PARAM_INT);
    $stmt->bindValue(":obs_modalidad", $obs_modalidad, is_null($obs_modalidad) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":vencimiento_plazo", $vencimiento_plazo, is_null($vencimiento_plazo) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":fecha_cumplimiento", $fecha_cumplimiento, is_null($fecha_cumplimiento) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":evidencia_cumplimiento", $evidencia_cumplimiento, is_null($evidencia_cumplimiento) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":verificacion_cumplimiento", $verificacion_cumplimiento, is_null($verificacion_cumplimiento) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":id_estado_cumplimiento", $id_estado_cumplimiento, PDO::PARAM_INT);
    $stmt->bindValue(":obs_estado_cumplimiento", $obs_estado_cumplimiento, is_null($obs_estado_cumplimiento) ? PDO::PARAM_NULL : PDO::PARAM_STR);
    $stmt->bindValue(":id_responsable", $id_responsable_establecimiento, is_null($id_responsable_establecimiento) ? PDO::PARAM_NULL : PDO::PARAM_INT);
    $stmt->bindValue(":datos_dinamicos", $datos_dinamicos, is_null($datos_dinamicos) ? PDO::PARAM_NULL : PDO::PARAM_STR);

    $stmt->execute();
    if ($es_nuevo) $id_item_matriz = $db->lastInsertId();

    // Gestión de normas
    $stmt_del_normas = $db->prepare("DELETE FROM item_matriz_norma WHERE id_item_matriz = :id_item_matriz");
    $stmt_del_normas->execute([':id_item_matriz' => $id_item_matriz]);

    if (!empty($normas_vinculadas)) {
        $stmt_ins_norma = $db->prepare("INSERT INTO item_matriz_norma (id_item_matriz, id_norma) VALUES (:id_item_matriz, :id_norma)");
        foreach ($normas_vinculadas as $id_norma) {
            $stmt_ins_norma->execute([':id_item_matriz' => $id_item_matriz, ':id_norma' => (int)$id_norma]);
        }
    }

    $db->commit();

    // --- DISPARADORES DE ALERTAS CON CORREOS (DEBUG) ---
    $resultados_correo = [];
    if ($matriz_publicada && $id_cliente) {
        $query_item_desc = "SELECT resumen_legal, datos_dinamicos, orden FROM item_matriz WHERE id_item_matriz = :id_item";
        $stmt_item = $db->prepare($query_item_desc);
        $stmt_item->execute([':id_item' => $id_item_matriz]);
        $item_data = $stmt_item->fetch(PDO::FETCH_ASSOC);
        $orden = $item_data['orden'] ?? 0;
        $descripcion_item = obtenerDescripcionItem($db, $id_item_matriz, $campo_encabezado, $item_data);

        // Cambio de estado
        if (!$es_nuevo && $estado_anterior !== null && $estado_anterior != $id_estado_cumplimiento) {
            $nombre_estado_anterior = obtenerNombreEstado($db, $estado_anterior);
            $nombre_estado_nuevo = obtenerNombreEstado($db, $id_estado_cumplimiento);
            $titulo = "Cambio de estado de cumplimiento en ítem #{$orden}";
            $mensaje = "El ítem \"{$descripcion_item}\" ha cambiado de estado de '{$nombre_estado_anterior}' a '{$nombre_estado_nuevo}'.";
            $url = "/dashboard/matrices/{$id_matriz}?item={$id_item_matriz}";
            $res = AlertaHelperDebug::insertarAlerta($db, $id_cliente, $id_matriz, $id_item_matriz, 'cambio_estado_cumplimiento', $titulo, $mensaje, $url);
            $resultados_correo[] = ["tipo" => "cambio_estado", "resultado" => $res];
        }

        // Responsable
        $responsable_cambio = false;
        if ($es_nuevo && $id_responsable_establecimiento !== null) {
            $responsable_cambio = true;
        } elseif (!$es_nuevo && $responsable_anterior != $id_responsable_establecimiento) {
            $responsable_cambio = true;
        }
        if ($responsable_cambio) {
            $titulo = "Responsable asignado/modificado en ítem #{$orden}";
            $mensaje = "El responsable del ítem \"{$descripcion_item}\" ha sido modificado.";
            $url = "/dashboard/matrices/{$id_matriz}?item={$id_item_matriz}";
            $res = AlertaHelperDebug::insertarAlerta($db, $id_cliente, $id_matriz, $id_item_matriz, 'responsable_asignado', $titulo, $mensaje, $url);
            $resultados_correo[] = ["tipo" => "responsable", "resultado" => $res];
        }

        // Vencimiento
        $fecha_cambio = false;
        if ($es_nuevo && $vencimiento_plazo !== null) {
            $fecha_cambio = true;
        } elseif (!$es_nuevo && $vencimiento_anterior != $vencimiento_plazo && $vencimiento_plazo !== null) {
            $fecha_cambio = true;
        }
        if ($fecha_cambio) {
            $stmt_check = $db->prepare("SELECT COUNT(*) FROM alerta 
                                        WHERE id_item_matriz = :id_item 
                                          AND tipo = 'vencimiento_proximo' 
                                          AND fecha_creacion > DATE_SUB(NOW(), INTERVAL 7 DAY)");
            $stmt_check->execute([':id_item' => $id_item_matriz]);
            $existe = (int)$stmt_check->fetchColumn();

            if (!$existe) {
                $tz = new DateTimeZone('America/Argentina/Buenos_Aires');
                $hoy = new DateTime('today', $tz);
                $venc = new DateTime($vencimiento_plazo, $tz);
                $venc->setTime(0, 0, 0);
                $diff = $hoy->diff($venc);
                $dias = (int)$diff->format('%r%a');

                if ($dias >= 0 && $dias <= 30) {
                    $fecha_formateada = date('d/m/Y', strtotime($vencimiento_plazo));
                    $titulo_venc = "Vencimiento próximo";
                    if ($dias == 0) {
                        $mensaje_venc = "El ítem \"{$descripcion_item}\" vence HOY ({$fecha_formateada}).";
                    } else {
                        $mensaje_venc = "El ítem \"{$descripcion_item}\" tiene vencimiento el {$fecha_formateada} (dentro de {$dias} días).";
                    }
                    $url_venc = "/dashboard/matrices/{$id_matriz}?item={$id_item_matriz}";
                    $res = AlertaHelperDebug::insertarAlerta($db, $id_cliente, $id_matriz, $id_item_matriz, 'vencimiento_proximo', $titulo_venc, $mensaje_venc, $url_venc);
                    $resultados_correo[] = ["tipo" => "vencimiento", "resultado" => $res];
                }
            }
        }
    }

    http_response_code(200);
    echo json_encode([
        "mensaje" => "Ítem guardado exitosamente.",
        "id_item_matriz" => $id_item_matriz,
        "debug_correos" => $resultados_correo // Esto te dirá si los correos se enviaron o fallaron
    ]);

} catch (Exception $e) {
    if ($db->inTransaction()) $db->rollBack();
    http_response_code(500);
    echo json_encode([
        "mensaje" => "Error interno al guardar.",
        "error" => $e->getMessage(),
        "trace" => $e->getTraceAsString()
    ]);
}

// ========== FUNCIONES AUXILIARES ==========
function obtenerDescripcionItem($db, $id_item_matriz, $campo_encabezado, $item_data) {
    if ($campo_encabezado === 'normas') {
        $query = "SELECT CONCAT(tn.descripcion, ' ', n.numero, '/', n.anio) AS norma_text
                  FROM item_matriz_norma imn
                  JOIN norma n ON imn.id_norma = n.id_norma
                  JOIN tipo_norma tn ON n.id_tipo_norma = tn.id_tipo_norma
                  WHERE imn.id_item_matriz = :id_item";
        $stmt = $db->prepare($query);
        $stmt->execute([':id_item' => $id_item_matriz]);
        $normas = $stmt->fetchAll(PDO::FETCH_COLUMN);
        return implode(', ', $normas) ?: 'Ítem sin normas';
    } elseif ($campo_encabezado === 'resumen_legal') {
        return $item_data['resumen_legal'] ?: 'Ítem sin resumen';
    } elseif (strpos($campo_encabezado, 'custom_') === 0) {
        $dinamicos = json_decode($item_data['datos_dinamicos'], true);
        return isset($dinamicos[$campo_encabezado]) ? $dinamicos[$campo_encabezado] : ($item_data['resumen_legal'] ?: 'Ítem sin descripción');
    } else {
        return $item_data['resumen_legal'] ?: 'Ítem sin descripción';
    }
}

function obtenerNombreEstado($db, $id_estado) {
    $stmt = $db->prepare("SELECT descripcion FROM estado_cumplimiento WHERE id_estado_cumplimiento = :id");
    $stmt->execute([':id' => $id_estado]);
    $nombre = $stmt->fetchColumn();
    return $nombre ?: "Estado #$id_estado";
}
?>