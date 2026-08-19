<?php
/**
 * backfill_adjuntos_matriz.php
 *
 * Script de mantenimiento (uso único) para copiar los adjuntos (doc_item_matriz)
 * de los ítems de una matriz PUBLICADA hacia los ítems de una matriz en BORRADOR
 * que fue creada con una versión anterior de copiar_matriz.php (la que no
 * copiaba los adjuntos).
 *
 * USO (por línea de comandos, desde el servidor):
 *   php backfill_adjuntos_matriz.php <id_matriz_origen_publicada> <id_matriz_destino_borrador> [--apply]
 *
 * Por defecto corre en modo DRY-RUN (no escribe nada en la base, solo informa
 * qué haría). Agregá --apply para ejecutar los inserts de verdad.
 *
 * Validaciones antes de tocar nada:
 *   - Ambas matrices existen.
 *   - La matriz destino está en estado BORRADOR (id_estado_matriz = 1).
 *   - Ambas matrices pertenecen a la misma combinación de establecimiento,
 *     tipo y especialidad (o sea, son "la misma matriz" en distinta versión).
 *   - Ambas matrices tienen la MISMA CANTIDAD de ítems, en el mismo orden
 *     (orden ASC, id_item_matriz ASC) — que es como los copia copiar_matriz.php.
 *     Si difieren, el script aborta sin tocar nada, porque no se puede saber
 *     con certeza qué ítem del borrador corresponde a cuál del origen.
 *
 * No duplica archivos en disco ni filas de "documentacion": solo agrega el
 * vínculo faltante en doc_item_matriz, igual que copiar_matriz.php hace ahora
 * con las normas (item_matriz_norma).
 *
 * Colocar este archivo en la misma carpeta que copiar_matriz.php para que el
 * include relativo a config/Database.php resuelva correctamente.
 */

if (php_sapi_name() !== 'cli') {
    http_response_code(403);
    die("Este script solo puede ejecutarse por línea de comandos (CLI).\n");
}

include_once '../../config/Database.php';

// --- 1. Parseo de argumentos ---
$args = $argv;
array_shift($args); // nombre del script

$apply = false;
$posicionales = [];
foreach ($args as $arg) {
    if ($arg === '--apply') {
        $apply = true;
    } else {
        $posicionales[] = $arg;
    }
}

if (count($posicionales) < 2) {
    fwrite(STDERR, "Uso: php backfill_adjuntos_matriz.php <id_matriz_origen_publicada> <id_matriz_destino_borrador> [--apply]\n");
    exit(1);
}

$id_origen  = (int) $posicionales[0];
$id_destino = (int) $posicionales[1];

if (!$id_origen || !$id_destino) {
    fwrite(STDERR, "Los IDs de matriz deben ser numéricos.\n");
    exit(1);
}

if ($id_origen === $id_destino) {
    fwrite(STDERR, "La matriz origen y destino no pueden ser la misma.\n");
    exit(1);
}

echo $apply
    ? "Modo: APLICAR CAMBIOS (se van a insertar filas en doc_item_matriz)\n"
    : "Modo: DRY-RUN (solo se informa, no se modifica nada; agregá --apply para ejecutar)\n";
echo "-----------------------------------------------------------\n";

$database = new Database();
$db = $database->getConnection();

try {
    // --- 2. Validar que ambas matrices existan y sean compatibles ---
    $stmt_matriz = $db->prepare(
        "SELECT id_matriz, id_cliente_establecimiento, id_tipo_matriz, id_especialidad_matriz,
                id_estado_matriz, version
         FROM matriz WHERE id_matriz = :id"
    );

    $stmt_matriz->execute([':id' => $id_origen]);
    $origen = $stmt_matriz->fetch(PDO::FETCH_ASSOC);
    if (!$origen) {
        fwrite(STDERR, "No existe la matriz origen (id_matriz = {$id_origen}).\n");
        exit(1);
    }

    $stmt_matriz->execute([':id' => $id_destino]);
    $destino = $stmt_matriz->fetch(PDO::FETCH_ASSOC);
    if (!$destino) {
        fwrite(STDERR, "No existe la matriz destino (id_matriz = {$id_destino}).\n");
        exit(1);
    }

    if ((int) $destino['id_estado_matriz'] !== 1) {
        fwrite(STDERR, "La matriz destino (id_matriz = {$id_destino}) no está en estado BORRADOR (id_estado_matriz actual: {$destino['id_estado_matriz']}). Se aborta por seguridad.\n");
        exit(1);
    }

    $mismaCombinacion =
        $origen['id_cliente_establecimiento'] === $destino['id_cliente_establecimiento'] &&
        $origen['id_tipo_matriz'] === $destino['id_tipo_matriz'] &&
        $origen['id_especialidad_matriz'] === $destino['id_especialidad_matriz'];

    if (!$mismaCombinacion) {
        fwrite(STDERR, "Las matrices {$id_origen} y {$id_destino} no comparten establecimiento/tipo/especialidad. Revisá los IDs antes de continuar; se aborta por seguridad.\n");
        exit(1);
    }

    echo "Origen  : id_matriz={$id_origen}  versión={$origen['version']}  (estado {$origen['id_estado_matriz']})\n";
    echo "Destino : id_matriz={$id_destino}  versión={$destino['version']}  (estado {$destino['id_estado_matriz']})\n";
    echo "-----------------------------------------------------------\n";

    // --- 3. Traer los ítems de ambas matrices en el mismo orden que usa copiar_matriz.php ---
    $stmt_items = $db->prepare(
        "SELECT id_item_matriz FROM item_matriz
         WHERE id_matriz = :id_matriz
         ORDER BY orden ASC, id_item_matriz ASC"
    );

    $stmt_items->execute([':id_matriz' => $id_origen]);
    $items_origen = $stmt_items->fetchAll(PDO::FETCH_COLUMN);

    $stmt_items->execute([':id_matriz' => $id_destino]);
    $items_destino = $stmt_items->fetchAll(PDO::FETCH_COLUMN);

    $n_origen = count($items_origen);
    $n_destino = count($items_destino);

    if ($n_origen === 0) {
        echo "La matriz origen no tiene ítems. Nada para copiar.\n";
        exit(0);
    }

    if ($n_origen !== $n_destino) {
        fwrite(STDERR, "La cantidad de ítems no coincide: origen tiene {$n_origen}, destino tiene {$n_destino}.\n");
        fwrite(STDERR, "No se puede mapear cada ítem del borrador con su correspondiente del origen de forma segura. Se aborta sin modificar nada.\n");
        fwrite(STDERR, "IDs origen : " . implode(', ', $items_origen) . "\n");
        fwrite(STDERR, "IDs destino: " . implode(', ', $items_destino) . "\n");
        exit(1);
    }

    echo "Ítems a procesar: {$n_origen}\n";
    echo "-----------------------------------------------------------\n";

    // --- 4. Consultas reutilizables ---
    // Adjuntos vigentes del ítem origen
    $stmt_docs_origen = $db->prepare(
        "SELECT dim.id_documentacion, d.nombre_original
         FROM doc_item_matriz dim
         INNER JOIN documentacion d ON dim.id_documentacion = d.id_documentacion
         WHERE dim.id_item_matriz = :id_item AND d.vigente = 1"
    );

    // Adjuntos que YA tiene vinculados el ítem destino (para no duplicar)
    $stmt_docs_destino = $db->prepare(
        "SELECT id_documentacion FROM doc_item_matriz WHERE id_item_matriz = :id_item"
    );

    $stmt_ins_doc = $db->prepare(
        "INSERT INTO doc_item_matriz (id_documentacion, id_item_matriz) VALUES (:id_doc, :id_item)"
    );

    // --- 5. Recorrer ítems por posición y copiar adjuntos faltantes ---
    $total_copiados = 0;
    $total_ya_existian = 0;
    $items_con_cambios = 0;

    if ($apply) {
        $db->beginTransaction();
    }

    for ($i = 0; $i < $n_origen; $i++) {
        $id_item_origen  = $items_origen[$i];
        $id_item_destino = $items_destino[$i];

        $stmt_docs_origen->execute([':id_item' => $id_item_origen]);
        $docs_origen = $stmt_docs_origen->fetchAll(PDO::FETCH_ASSOC);

        if (empty($docs_origen)) {
            continue; // este ítem no tiene adjuntos vigentes, no hay nada que copiar
        }

        $stmt_docs_destino->execute([':id_item' => $id_item_destino]);
        $ya_vinculados = $stmt_docs_destino->fetchAll(PDO::FETCH_COLUMN);
        $ya_vinculados = array_map('intval', $ya_vinculados);

        $faltantes = [];
        foreach ($docs_origen as $doc) {
            if (!in_array((int) $doc['id_documentacion'], $ya_vinculados, true)) {
                $faltantes[] = $doc;
            }
        }

        if (empty($faltantes)) {
            $total_ya_existian += count($docs_origen);
            continue;
        }

        echo "Ítem origen {$id_item_origen} -> ítem destino {$id_item_destino}: ";
        echo count($faltantes) . " adjunto(s) a copiar";
        if (count($docs_origen) > count($faltantes)) {
            echo " (" . (count($docs_origen) - count($faltantes)) . " ya estaban)";
        }
        echo "\n";

        foreach ($faltantes as $doc) {
            echo "    - {$doc['nombre_original']} (id_documentacion={$doc['id_documentacion']})\n";
            if ($apply) {
                $stmt_ins_doc->execute([
                    ':id_doc'  => $doc['id_documentacion'],
                    ':id_item' => $id_item_destino
                ]);
            }
            $total_copiados++;
        }

        $items_con_cambios++;
    }

    if ($apply) {
        $db->commit();
    }

    echo "-----------------------------------------------------------\n";
    echo "Ítems con adjuntos nuevos: {$items_con_cambios}\n";
    echo "Adjuntos " . ($apply ? "copiados" : "a copiar") . ": {$total_copiados}\n";
    echo "Adjuntos que ya estaban vinculados (sin cambios): {$total_ya_existian}\n";

    if (!$apply && $total_copiados > 0) {
        echo "\nEsto fue un DRY-RUN, no se modificó la base. Volvé a ejecutar con --apply para aplicar los cambios.\n";
    }

} catch (Exception $e) {
    if ($db->inTransaction()) {
        $db->rollBack();
    }
    fwrite(STDERR, "Error: " . $e->getMessage() . "\n");
    exit(1);
}
