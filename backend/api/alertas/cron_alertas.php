<?php
// cron_alertas.php – Ejecutar diariamente (ej. a las 6 AM)
// Usar __DIR__ para rutas absolutas
require_once __DIR__ . '/../../config/Database.php';
require_once __DIR__ . '/../../helpers/AlertaHelper.php';

$database = new Database();
$db = $database->getConnection();

// Obtener matrices publicadas
$query_matrices = "SELECT m.id_matriz, m.campo_encabezado_item, c.id_cliente
                   FROM matriz m
                   JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
                   JOIN cliente c ON ce.id_cliente = c.id_cliente
                   WHERE m.id_estado_matriz = 2";
$stmt = $db->prepare($query_matrices);
$stmt->execute();
$matrices = $stmt->fetchAll(PDO::FETCH_ASSOC);

// Zona horaria Argentina para todos los cálculos
$tz = new DateTimeZone('America/Argentina/Buenos_Aires');

foreach ($matrices as $mat) {
    $id_matriz = $mat['id_matriz'];
    $id_cliente = $mat['id_cliente'];
    $campo_encabezado = $mat['campo_encabezado_item'] ?? 'resumen_legal';

    // --- Alertas por vencimiento de ítems ---
    $query_items = "SELECT id_item_matriz, vencimiento_plazo, resumen_legal, datos_dinamicos
                    FROM item_matriz
                    WHERE id_matriz = :id_matriz AND vencimiento_plazo IS NOT NULL";
    $stmt_items = $db->prepare($query_items);
    $stmt_items->bindParam(':id_matriz', $id_matriz, PDO::PARAM_INT);
    $stmt_items->execute();
    $items = $stmt_items->fetchAll(PDO::FETCH_ASSOC);

    foreach ($items as $item) {
        $fecha_vencimiento = $item['vencimiento_plazo'];
        if (!$fecha_vencimiento) continue;

        // Calcular días con zona horaria Argentina
        $hoy = new DateTime('today', $tz);
        $venc = new DateTime($fecha_vencimiento, $tz);
        $venc->setTime(0, 0, 0);
        $diff = $hoy->diff($venc);
        $dias_diff = (int)$diff->format('%r%a');

        // Solo nos interesa si está vencido o dentro de los próximos 30 días
        if ($dias_diff < -30 || $dias_diff > 30) continue;

        $tipo = null;
        $titulo = '';
        $mensaje = '';
        $dias_mostrar = abs($dias_diff);

        // Obtener descripción del ítem
        $descripcion_item = '';
        if ($campo_encabezado === 'normas') {
            $query_normas = "SELECT CONCAT(tn.descripcion, ' ', n.numero, '/', n.anio) AS norma_text
                             FROM item_matriz_norma imn
                             JOIN norma n ON imn.id_norma = n.id_norma
                             JOIN tipo_norma tn ON n.id_tipo_norma = tn.id_tipo_norma
                             WHERE imn.id_item_matriz = :id_item";
            $stmt_normas = $db->prepare($query_normas);
            $stmt_normas->execute([':id_item' => $item['id_item_matriz']]);
            $normas = $stmt_normas->fetchAll(PDO::FETCH_COLUMN);
            $descripcion_item = implode(', ', $normas);
        } elseif ($campo_encabezado === 'resumen_legal') {
            $descripcion_item = $item['resumen_legal'];
        } elseif (strpos($campo_encabezado, 'custom_') === 0) {
            $dinamicos = json_decode($item['datos_dinamicos'], true);
            $descripcion_item = isset($dinamicos[$campo_encabezado]) ? $dinamicos[$campo_encabezado] : $item['resumen_legal'];
        } else {
            $descripcion_item = $item[$campo_encabezado] ?? $item['resumen_legal'];
        }
        if (empty($descripcion_item)) {
            $descripcion_item = $item['resumen_legal'] ?: 'Ítem sin descripción';
        }

        $fecha_formateada = date('d/m/Y', strtotime($fecha_vencimiento));

        if ($dias_diff < 0) {
            $tipo = 'vencimiento_vencido';
            $titulo = 'Vencimiento superado';
            $mensaje = "El ítem \"{$descripcion_item}\" tiene su fecha de vencimiento ({$fecha_formateada}) superada hace {$dias_mostrar} días.";
        } elseif ($dias_diff >= 0 && $dias_diff <= 30) {
            $tipo = 'vencimiento_proximo';
            $titulo = 'Vencimiento próximo';
            if ($dias_diff == 0) {
                $mensaje = "El ítem \"{$descripcion_item}\" vence HOY ({$fecha_formateada}).";
            } else {
                $mensaje = "El ítem \"{$descripcion_item}\" vence en {$dias_diff} días ({$fecha_formateada}).";
            }
        }

        if ($tipo) {
            // Evitar duplicados en los últimos 7 días
            $check = "SELECT id_alerta FROM alerta 
                      WHERE id_cliente = :id_cliente AND id_item_matriz = :id_item AND tipo = :tipo 
                      AND fecha_creacion > DATE_SUB(NOW(), INTERVAL 7 DAY)";
            $stmt_check = $db->prepare($check);
            $stmt_check->execute([
                ':id_cliente' => $id_cliente,
                ':id_item' => $item['id_item_matriz'],
                ':tipo' => $tipo
            ]);
            if (!$stmt_check->fetch()) {
                $url = "/dashboard/matrices/{$id_matriz}?item={$item['id_item_matriz']}";
                // Usar AlertaHelper para insertar y enviar correos
                AlertaHelper::insertarAlerta($db, $id_cliente, $id_matriz, $item['id_item_matriz'], $tipo, $titulo, $mensaje, $url);
            }
        }
    }
}

echo json_encode(["mensaje" => "Cron ejecutado correctamente."]);
?>