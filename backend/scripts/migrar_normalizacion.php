<?php
/**
 * migrar_normalizacion.php
 * ---------------------------------------------------------------------------
 * Migración ÚNICA e IDEMPOTENTE para:
 *
 *   PASO 1 (tipo_norma):
 *     - Fusiona los IDs duplicados listados en $mapa_fusion más abajo
 *       (remapea FKs en norma_bo y norma, borra el ID viejo). El mapa está
 *       hardcodeado en el script -- no se lee de la base, porque no existe
 *       ninguna columna `comentario` real en tipo_norma; esa columna era
 *       solo una anotación manual en el CSV de referencia.
 *     - Normaliza `descripcion` a MAYÚSCULAS (conserva tildes).
 *     - Agrega/rellena `clave_normalizada` con NormativaHelper::normalizarClave().
 *     - Crea índice único ux_tipo_norma_clave sobre clave_normalizada.
 *
 *   PASO 2 (emisor_norma):
 *     - Recalcula clave_normalizada de TODAS las filas con la fórmula real
 *       (hoy hay filas con un formato "legacy" que nunca matchea en el
 *       resolverEmisor() actual -> genera duplicados fantasma a futuro).
 *     - Detecta duplicados reales que aparecen al recalcular (mismo
 *       id_jurisdiccion + misma clave) y los fusiona: se queda el de mayor
 *       uso combinado en norma+norma_bo (empate -> id más chico).
 *
 * MODO POR DEFECTO: dry-run. Solo imprime un reporte, no modifica nada.
 * Para aplicar de verdad: correr con --aplicar
 *
 *   php migrar_normalizacion.php              # dry-run
 *   php migrar_normalizacion.php --aplicar     # ejecuta la migración real
 *
 * IMPORTANTE: los ALTER TABLE (agregar columna / índice) hacen COMMIT
 * IMPLÍCITO en MySQL/MariaDB. La transacción protege el remapeo de filas,
 * pero NO te salva de un DDL a mitad de camino. Hacé un backup completo
 * (mysqldump) de tipo_norma, emisor_norma, norma y norma_bo ANTES de
 * correr esto con --aplicar. Probá primero en localhost.
 * ---------------------------------------------------------------------------
 */

require_once __DIR__ . '/../config/Database.php';
require_once __DIR__ . '/../config/NormativaHelper.php';

$aplicar = in_array('--aplicar', $argv, true);

function log_linea($msg) { echo $msg . PHP_EOL; }

function contar($db, $sql, $params) {
    $s = $db->prepare($sql);
    $s->execute($params);
    return (int)$s->fetchColumn();
}

function buscarDescripcion(array $filas, $id) {
    foreach ($filas as $f) {
        if ((int)$f['id_tipo_norma'] === (int)$id) {
            return $f['descripcion'];
        }
    }
    return '(id no encontrado: ' . $id . ')';
}

function asegurarColumna(PDO $db, $tabla, $columna, $ddl, $aplicar) {
    $chk = $db->query("SHOW COLUMNS FROM `$tabla` LIKE " . $db->quote($columna));
    if ($chk->rowCount() === 0) {
        log_linea("  [DDL] $ddl");
        if ($aplicar) {
            $db->exec($ddl);
        }
        return true; // se creó (o se crearía)
    }
    return false; // ya existía
}

function asegurarIndiceUnico(PDO $db, $tabla, $nombre, $ddl, $aplicar) {
    $chk = $db->query("SHOW INDEX FROM `$tabla` WHERE Key_name = " . $db->quote($nombre));
    if ($chk->rowCount() === 0) {
        log_linea("  [DDL] $ddl");
        if ($aplicar) {
            $db->exec($ddl);
        }
    } else {
        log_linea("  (índice único '$nombre' ya existe, no se toca)");
    }
}

$database = new Database();
$db = $database->getConnection();

log_linea($aplicar
    ? "=== MODO APLICAR: se van a hacer cambios reales en la base ==="
    : "=== MODO DRY-RUN: solo reporte, no se modifica nada (usá --aplicar para ejecutar) ===");

try {
    if ($aplicar) {
        $db->beginTransaction();
    }

    // =======================================================================
    // PASO 1: tipo_norma
    // =======================================================================
    log_linea("\n--- PASO 1: tipo_norma ---");

    asegurarColumna(
        $db,
        'tipo_norma',
        'clave_normalizada',
        "ALTER TABLE tipo_norma ADD COLUMN clave_normalizada VARCHAR(255) NULL AFTER descripcion",
        $aplicar
    );

    $stmt = $db->query("SELECT id_tipo_norma, descripcion FROM tipo_norma");
    $filas_tipo = $stmt->fetchAll(PDO::FETCH_ASSOC);

    // ------------------------------------------------------------------
    // Mapa de fusión (id_viejo => id_canónico).
    //
    // `comentario` NO es una columna real de tipo_norma: fue una anotación
    // manual tuya en el CSV para que yo entendiera el criterio de fusión.
    // Por eso el mapa queda hardcodeado acá, derivado de esa columna, en
    // vez de leerse de la base. Si en algún momento agregás/sacás tipos
    // duplicados, actualizá esta lista a mano.
    //
    // "id_viejo (descripcion tal como estaba en tu CSV)" => id_canónico
    // ------------------------------------------------------------------
    $mapa_fusion = [
        55 => 4,   // DECISION ADMINISTRATIVA          -> Decisión Administrativa
        40 => 8,   // DISPOSICION                       -> Disposición
        41 => 5,   // RESOLUCION                        -> Resolución
        49 => 5,   // RESOLUCION 1 SIN                  -> Resolución
        26 => 5,   // RESOLUCION 430                    -> Resolución
        27 => 5,   // RESOLUCION 431                    -> Resolución
        42 => 6,   // RESOLUCION CONJUNTA               -> Resolución Conjunta
        43 => 14,  // RESOLUCION GENERAL                -> Resolución General
        45 => 23,  // RESOLUCION SINTETIZADA            -> RESOLUCIÓN SINTETIZADA
    ];

    // Descripciones esperadas (tal como estaban en el CSV que me pasaste),
    // solo para el chequeo defensivo de abajo. Si la tabla cambió desde
    // entonces, el chequeo avisa y esa fusión puntual se salta en vez de
    // arriesgarse a fusionar el tipo equivocado.
    $desc_esperada = [
        55 => 'DECISION ADMINISTRATIVA', 4  => 'Decisión Administrativa',
        40 => 'DISPOSICION',             8  => 'Disposición',
        41 => 'RESOLUCION',              5  => 'Resolución',
        49 => 'RESOLUCION 1 SIN',
        26 => 'RESOLUCION 430',
        27 => 'RESOLUCION 431',
        42 => 'RESOLUCION CONJUNTA',     6  => 'Resolución Conjunta',
        43 => 'RESOLUCION GENERAL',      14 => 'Resolución General',
        45 => 'RESOLUCION SINTETIZADA',  23 => 'RESOLUCIÓN SINTETIZADA',
    ];

    // Chequeo defensivo: si algún id del mapa ya no existe en la tabla, o
    // existe pero con una descripción distinta a la que vimos en el CSV,
    // se salta esa fusión puntual (no se aplica a ciegas) y se avisa.
    $mapa_fusion_validado = [];
    foreach ($mapa_fusion as $viejo => $nuevo) {
        $desc_actual_viejo = buscarDescripcion($filas_tipo, $viejo);
        $desc_actual_nuevo = buscarDescripcion($filas_tipo, $nuevo);

        if ($desc_actual_viejo === '(id no encontrado: ' . $viejo . ')') {
            log_linea("  (aviso) id=$viejo ya no existe en tipo_norma (¿fusión corrida antes?). Se omite.");
            continue;
        }
        if ($desc_actual_nuevo === '(id no encontrado: ' . $nuevo . ')') {
            log_linea("  *** ALERTA: id_canónico=$nuevo (destino de id=$viejo) no existe en la tabla. Se omite esta fusión. ***");
            continue;
        }
        if (isset($desc_esperada[$viejo]) && strcasecmp(trim($desc_actual_viejo), $desc_esperada[$viejo]) !== 0) {
            log_linea("  *** ALERTA: id=$viejo tiene descripcion '$desc_actual_viejo', distinta a la esperada '{$desc_esperada[$viejo]}'. Se omite esta fusión, revisar a mano. ***");
            continue;
        }
        $mapa_fusion_validado[$viejo] = $nuevo;
    }
    $mapa_fusion = $mapa_fusion_validado;

    if (empty($mapa_fusion)) {
        log_linea("  No quedaron fusiones para aplicar (ver avisos arriba, o ya se corrió antes).");
    }

    foreach ($mapa_fusion as $viejo => $nuevo) {
        // Resolver cadenas de fusión por si algún día A->B->C
        $destino = $nuevo;
        $visitados = [$viejo];
        while (isset($mapa_fusion[$destino]) && !in_array($destino, $visitados, true)) {
            $visitados[] = $destino;
            $destino = $mapa_fusion[$destino];
        }

        $desc_viejo = buscarDescripcion($filas_tipo, $viejo);
        $desc_nuevo = buscarDescripcion($filas_tipo, $destino);

        $n_bo = contar($db, "SELECT COUNT(*) FROM norma_bo WHERE id_tipo_norma = ?", [$viejo]);
        $n_n  = contar($db, "SELECT COUNT(*) FROM norma WHERE id_tipo_norma = ?", [$viejo]);

        log_linea("  Fusionar id=$viejo ('$desc_viejo')  ->  id=$destino ('$desc_nuevo')  [norma_bo: $n_bo, norma: $n_n]");

        if ($aplicar) {
            $db->prepare("UPDATE norma_bo SET id_tipo_norma = ? WHERE id_tipo_norma = ?")->execute([$destino, $viejo]);
            $db->prepare("UPDATE norma SET id_tipo_norma = ? WHERE id_tipo_norma = ?")->execute([$destino, $viejo]);
            $db->prepare("DELETE FROM tipo_norma WHERE id_tipo_norma = ?")->execute([$viejo]);
        }
    }

    // Normalizar descripcion a MAYÚSCULAS + recalcular clave_normalizada
    // para todos los sobrevivientes (los que NO se fusionaron).
    $stmt2 = $db->query("SELECT id_tipo_norma, descripcion FROM tipo_norma");
    $sobrevivientes = $stmt2->fetchAll(PDO::FETCH_ASSOC);

    $claves_vistas = [];
    $actualizados = 0;
    foreach ($sobrevivientes as $s) {
        if (isset($mapa_fusion[(int)$s['id_tipo_norma']])) {
            continue; // por si el dry-run no lo "borró" todavía, no lo tocamos
        }
        $desc_mayus = mb_strtoupper(trim($s['descripcion']), 'UTF-8');
        $clave = NormativaHelper::normalizarClave($desc_mayus);

        if (isset($claves_vistas[$clave])) {
            log_linea("  *** ALERTA: colisión inesperada de clave '$clave' entre id={$s['id_tipo_norma']} e id={$claves_vistas[$clave]}. NO se aplica, revisar a mano. ***");
            continue;
        }
        $claves_vistas[$clave] = $s['id_tipo_norma'];

        if ($aplicar) {
            $db->prepare("UPDATE tipo_norma SET descripcion = ?, clave_normalizada = ? WHERE id_tipo_norma = ?")
               ->execute([$desc_mayus, $clave, $s['id_tipo_norma']]);
        }
        $actualizados++;
    }
    log_linea("  tipo_norma sobrevivientes normalizados: $actualizados");

    // El índice único se crea recién acá, cuando ya no puede haber colisiones.
    asegurarIndiceUnico(
        $db,
        'tipo_norma',
        'ux_tipo_norma_clave',
        "ALTER TABLE tipo_norma ADD UNIQUE INDEX ux_tipo_norma_clave (clave_normalizada)",
        $aplicar
    );

    // =======================================================================
    // PASO 2: emisor_norma
    // =======================================================================
    log_linea("\n--- PASO 2: emisor_norma ---");

    $stmt3 = $db->query("SELECT id_emisor_norma, id_jurisdiccion, descripcion FROM emisor_norma");
    $emisores = $stmt3->fetchAll(PDO::FETCH_ASSOC);

    // Agrupar por (id_jurisdiccion, clave_correcta) para encontrar duplicados
    // reales que hoy están "escondidos" por el formato legacy de clave_normalizada.
    $grupos = [];
    foreach ($emisores as $e) {
        $clave = NormativaHelper::normalizarClave($e['descripcion']);
        $key = $e['id_jurisdiccion'] . '|' . $clave;
        $grupos[$key][] = $e + ['clave' => $clave];
    }

    $ids_fusionados = [];
    $total_fusiones = 0;

    foreach ($grupos as $grupo) {
        if (count($grupo) <= 1) {
            continue;
        }

        // Elegir "ganador": mayor uso combinado en norma_bo + norma;
        // empate -> id más chico (más antiguo).
        $mejor = null;
        $mejor_uso = -1;
        foreach ($grupo as $e) {
            $uso = contar($db, "SELECT COUNT(*) FROM norma_bo WHERE id_emisor_norma = ?", [$e['id_emisor_norma']])
                 + contar($db, "SELECT COUNT(*) FROM norma WHERE id_emisor_norma = ?", [$e['id_emisor_norma']]);
            if ($uso > $mejor_uso
                || ($uso === $mejor_uso && ($mejor === null || (int)$e['id_emisor_norma'] < (int)$mejor['id_emisor_norma']))) {
                $mejor = $e;
                $mejor_uso = $uso;
            }
        }

        foreach ($grupo as $e) {
            if ((int)$e['id_emisor_norma'] === (int)$mejor['id_emisor_norma']) {
                continue;
            }
            $total_fusiones++;
            $ids_fusionados[(int)$e['id_emisor_norma']] = true;
            log_linea("  Fusionar emisor id={$e['id_emisor_norma']} ('{$e['descripcion']}')  ->  id={$mejor['id_emisor_norma']} ('{$mejor['descripcion']}')  [jurisdiccion {$e['id_jurisdiccion']}]");

            if ($aplicar) {
                $db->prepare("UPDATE norma_bo SET id_emisor_norma = ? WHERE id_emisor_norma = ?")->execute([$mejor['id_emisor_norma'], $e['id_emisor_norma']]);
                $db->prepare("UPDATE norma SET id_emisor_norma = ? WHERE id_emisor_norma = ?")->execute([$mejor['id_emisor_norma'], $e['id_emisor_norma']]);
                $db->prepare("DELETE FROM emisor_norma WHERE id_emisor_norma = ?")->execute([$e['id_emisor_norma']]);
            }
        }
    }
    log_linea("  Total fusiones de emisor_norma: $total_fusiones");

    // Recalcular clave_normalizada correcta para todos los sobrevivientes
    // (incluye a los que no se fusionaron pero tenían el formato "legacy").
    $stmt4 = $db->query("SELECT id_emisor_norma, descripcion FROM emisor_norma");
    $sobrevivientes_em = $stmt4->fetchAll(PDO::FETCH_ASSOC);

    $corregidas = 0;
    foreach ($sobrevivientes_em as $e) {
        if (isset($ids_fusionados[(int)$e['id_emisor_norma']])) {
            continue;
        }
        $clave_correcta = NormativaHelper::normalizarClave($e['descripcion']);
        if ($aplicar) {
            $db->prepare("UPDATE emisor_norma SET clave_normalizada = ? WHERE id_emisor_norma = ?")
               ->execute([$clave_correcta, $e['id_emisor_norma']]);
        }
        $corregidas++;
    }
    log_linea("  clave_normalizada recalculada en $corregidas emisores.");

    // Confirmar que el índice único (id_jurisdiccion, clave_normalizada) existe.
    $chk = $db->query("SHOW INDEX FROM emisor_norma WHERE Column_name = 'clave_normalizada'");
    if ($chk->rowCount() === 0) {
        log_linea("  *** ATENCIÓN: no se detectó ningún índice sobre clave_normalizada en emisor_norma. ***");
        log_linea("  El código (NormativaHelper::resolverEmisor) asume que existe un índice único");
        log_linea("  (id_jurisdiccion, clave_normalizada). Si no existe, creá uno manualmente, ej.:");
        log_linea("    ALTER TABLE emisor_norma ADD UNIQUE INDEX ux_emisor_jur_clave (id_jurisdiccion, clave_normalizada);");
    } else {
        log_linea("  Índice sobre clave_normalizada en emisor_norma: OK (ya existe).");
    }

    if ($aplicar) {
        $db->commit();
        log_linea("\n=== COMMIT OK. Migración aplicada. ===");
    } else {
        log_linea("\n=== DRY-RUN terminado. No se modificó nada. Revisá el reporte y corré con --aplicar cuando estés listo. ===");
    }

} catch (Exception $ex) {
    if ($aplicar && $db->inTransaction()) {
        $db->rollBack();
    }
    log_linea("\nERROR: " . $ex->getMessage());
    exit(1);
}