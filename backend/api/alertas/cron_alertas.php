<?php
// cron_alertas.php – Ejecutar diariamente (por ejemplo, a las 6 AM)
// Configuración de conexión a BD (puedes incluir Database.php)
require_once '../../config/Database.php';

$database = new Database();
$db = $database->getConnection();

// 1. Obtener todas las matrices publicadas (id_estado_matriz = 2)
$query_matrices = "SELECT m.id_matriz, m.id_cliente_establecimiento, c.id_cliente, c.nombre_fantasia
                   FROM matriz m
                   JOIN cliente_establecimiento ce ON m.id_cliente_establecimiento = ce.id_cliente_establecimiento
                   JOIN cliente c ON ce.id_cliente = c.id_cliente
                   WHERE m.id_estado_matriz = 2";
$stmt = $db->prepare($query_matrices);
$stmt->execute();
$matrices = $stmt->fetchAll(PDO::FETCH_ASSOC);

$fecha_hoy = date('Y-m-d');
$dias_proximos = 30;

foreach ($matrices as $mat) {
    $id_matriz = $mat['id_matriz'];
    $id_cliente = $mat['id_cliente'];
    $nombre_cliente = $mat['nombre_fantasia'];

    // --- Alertas por vencimiento de ítems ---
    $query_items = "SELECT id_item_matriz, vencimiento_plazo, resumen_legal, estado_cumplimiento_desc
                    FROM item_matriz im
                    LEFT JOIN estado_cumplimiento ec ON im.id_estado_cumplimiento = ec.id_estado_cumplimiento
                    WHERE id_matriz = :id_matriz AND vencimiento_plazo IS NOT NULL";
    $stmt_items = $db->prepare($query_items);
    $stmt_items->bindParam(':id_matriz', $id_matriz, PDO::PARAM_INT);
    $stmt_items->execute();
    $items = $stmt_items->fetchAll(PDO::FETCH_ASSOC);

    foreach ($items as $item) {
        $fecha_vencimiento = $item['vencimiento_plazo'];
        if (!$fecha_vencimiento) continue;
        $dias_diff = (strtotime($fecha_vencimiento) - strtotime($fecha_hoy)) / (60*60*24);
        $tipo = null;
        $titulo = '';
        $mensaje = '';
        if ($dias_diff < 0) {
            $tipo = 'vencimiento_vencido';
            $titulo = 'Vencimiento superado';
            $mensaje = "El ítem '{$item['resumen_legal']}' tiene su fecha de vencimiento ({$fecha_vencimiento}) ya superada.";
        } elseif ($dias_diff <= $dias_proximos) {
            $tipo = 'vencimiento_proximo';
            $titulo = 'Vencimiento próximo';
            $mensaje = "El ítem '{$item['resumen_legal']}' vence en {$dias_diff} días ({$fecha_vencimiento}).";
        }
        if ($tipo) {
            // Evitar duplicados en los últimos 7 días para el mismo ítem
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
                $insert = "INSERT INTO alerta (id_cliente, id_matriz, id_item_matriz, tipo, titulo, mensaje, url) 
                           VALUES (:id_cliente, :id_matriz, :id_item, :tipo, :titulo, :mensaje, :url)";
                $stmt_ins = $db->prepare($insert);
                $stmt_ins->execute([
                    ':id_cliente' => $id_cliente,
                    ':id_matriz' => $id_matriz,
                    ':id_item' => $item['id_item_matriz'],
                    ':tipo' => $tipo,
                    ':titulo' => $titulo,
                    ':mensaje' => $mensaje,
                    ':url' => $url
                ]);
            }
        }
    }

    // --- Alertas por bajo cumplimiento (menos del 50%) ---
    $query_porcentaje = "SELECT 
                            COUNT(*) AS total,
                            SUM(CASE WHEN id_estado_cumplimiento = 1 THEN 1 ELSE 0 END) AS cumplen
                         FROM item_matriz WHERE id_matriz = :id_matriz";
    $stmt_porc = $db->prepare($query_porcentaje);
    $stmt_porc->bindParam(':id_matriz', $id_matriz, PDO::PARAM_INT);
    $stmt_porc->execute();
    $stats = $stmt_porc->fetch(PDO::FETCH_ASSOC);
    $total_items = $stats['total'];
    if ($total_items > 0) {
        $porcentaje = round(($stats['cumplen'] / $total_items) * 100);
        if ($porcentaje < 50) {
            $check = "SELECT id_alerta FROM alerta 
                      WHERE id_cliente = :id_cliente AND id_matriz = :id_matriz AND tipo = 'bajo_cumplimiento'
                      AND fecha_creacion > DATE_SUB(NOW(), INTERVAL 30 DAY)";
            $stmt_check = $db->prepare($check);
            $stmt_check->execute([':id_cliente' => $id_cliente, ':id_matriz' => $id_matriz]);
            if (!$stmt_check->fetch()) {
                $titulo = "Bajo nivel de cumplimiento";
                $mensaje = "La matriz ha alcanzado solo un {$porcentaje}% de cumplimiento (por debajo del 50%).";
                $url = "/dashboard/matrices/{$id_matriz}";
                $insert = "INSERT INTO alerta (id_cliente, id_matriz, tipo, titulo, mensaje, url) 
                           VALUES (:id_cliente, :id_matriz, 'bajo_cumplimiento', :titulo, :mensaje, :url)";
                $stmt_ins = $db->prepare($insert);
                $stmt_ins->execute([
                    ':id_cliente' => $id_cliente,
                    ':id_matriz' => $id_matriz,
                    ':titulo' => $titulo,
                    ':mensaje' => $mensaje,
                    ':url' => $url
                ]);
            }
        }
    }
}

echo json_encode(["mensaje" => "Cron ejecutado correctamente."]);
?>