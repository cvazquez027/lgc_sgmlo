<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

// --- Aumentar límites para procesamiento masivo ---
set_time_limit(0);              // Sin límite de tiempo
ini_set('memory_limit', '2G');  // 2 GB de memoria
ignore_user_abort(true);        // Continuar aunque el navegador cierre

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';
include_once '../../config/NormativaHelper.php';

$data = json_decode(file_get_contents("php://input"));

// Validar parámetros...
$todos = isset($data->todos) ? filter_var($data->todos, FILTER_VALIDATE_BOOLEAN) : false;
$filtros = isset($data->filtros) ? $data->filtros : null;

if (!$todos && (empty($data->ids_normas) || !is_array($data->ids_normas))) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan parámetros."]);
    exit();
}
if (empty($data->accion)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Falta la acción."]);
    exit();
}

$accion = htmlspecialchars(strip_tags($data->accion));
$database = new Database();
$db = $database->getConnection();

try {
    // --- Obtener lista de IDs a procesar ---
    if ($todos && $filtros) {
        list($whereClause, $params) = NormativaHelper::buildScrapingFilters($db, $filtros);
        $query = "SELECT nbo.id_norma_bo 
                  FROM norma_bo nbo
                  INNER JOIN emisor_norma en ON nbo.id_emisor_norma = en.id_emisor_norma
                  $whereClause";
        $stmt = $db->prepare($query);
        foreach ($params as $key => &$val) {
            $stmt->bindParam($key, $val);
        }
        $stmt->execute();
        $ids_normas = $stmt->fetchAll(PDO::FETCH_COLUMN);
    } else {
        $ids_normas = $data->ids_normas;
    }

    $total_ids = count($ids_normas);
    if ($total_ids === 0) {
        echo json_encode(["mensaje" => "No hay normas para procesar.", "procesados" => 0]);
        exit();
    }

    // --- Procesar en lotes de 500 ---
    $lote_tamano = 1000;
    $total_lotes = ceil($total_ids / $lote_tamano);
    $procesados_total = 0;
    $categorias_migradas_total = 0;
    $omitidas_total = 0;

    // Preparar statements (fuera del bucle)
    $q_leer = "SELECT * FROM norma_bo WHERE id_norma_bo = :id_bo FOR UPDATE";
    $stmt_leer = $db->prepare($q_leer);

    $q_insertar = "INSERT INTO norma
        (id_tipo_norma, id_emisor_norma, numero, anio, fecha_publicacion, sintesis, url_norma, id_estado_norma, origen_carga)
        VALUES (:tipo, :emisor, :num, :anio, :fecha, :sintesis, :url, 1, 'Scraping')";
    $stmt_insert = $db->prepare($q_insertar);

    $q_tipo = "SELECT descripcion FROM tipo_norma WHERE id_tipo_norma = :id";
    $stmt_tipo = $db->prepare($q_tipo);

    $q_borrar_cat = "DELETE FROM categoria_norma_bo WHERE id_norma_bo = :id_bo";
    $stmt_b_cat = $db->prepare($q_borrar_cat);

    $q_borrar = "DELETE FROM norma_bo WHERE id_norma_bo = :id_bo";
    $stmt_borrar = $db->prepare($q_borrar);

    // Cargar combinaciones existentes en norma para evitar duplicados
    $combinaciones_existentes = [];
    $stmt_comb = $db->prepare("SELECT CONCAT(id_tipo_norma, '|', numero, '|', anio, '|', id_emisor_norma) as clave FROM norma");
    $stmt_comb->execute();
    while ($row = $stmt_comb->fetchColumn()) {
        $combinaciones_existentes[$row] = true;
    }

    // Bucle por lotes
    for ($lote = 0; $lote < $total_lotes; $lote++) {
        $inicio = $lote * $lote_tamano;
        $lote_ids = array_slice($ids_normas, $inicio, $lote_tamano);

        try {
            $db->beginTransaction();

            foreach ($lote_ids as $id_raw) {
                $id_norma_bo = filter_var($id_raw, FILTER_VALIDATE_INT);
                if (!$id_norma_bo) continue;

                if ($accion === 'promover') {
                    $stmt_leer->execute([':id_bo' => $id_norma_bo]);
                    $norma_bruta = $stmt_leer->fetch(PDO::FETCH_ASSOC);
                    if (!$norma_bruta) continue;

                    $clave = "{$norma_bruta['id_tipo_norma']}|{$norma_bruta['numero']}|{$norma_bruta['anio']}|{$norma_bruta['id_emisor_norma']}";
                    if (isset($combinaciones_existentes[$clave])) {
                        // Duplicado: borrar buffer y continuar
                        $stmt_b_cat->execute([':id_bo' => $id_norma_bo]);
                        $stmt_borrar->execute([':id_bo' => $id_norma_bo]);
                        $omitidas_total++;
                        continue;
                    }
                    /*
                    // Obtener URL específica (opcional)
                    $url_especifica = null;
                    if ($norma_bruta['id_tipo_norma'] && $norma_bruta['numero'] && $norma_bruta['anio']) {
                        $stmt_tipo->execute([':id' => $norma_bruta['id_tipo_norma']]);
                        $tipo_desc = $stmt_tipo->fetchColumn();
                        if ($tipo_desc) {
                            // Llamada a buscar_url_gba.php (ajusta la URL si es necesario)
                            $ch = curl_init();
                            curl_setopt($ch, CURLOPT_URL, "http://localhost/lgc_sgmlo/backend/api/normativa/buscar_url_gba.php");
                            curl_setopt($ch, CURLOPT_POST, 1);
                            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
                                'tipo'   => $tipo_desc,
                                'numero' => $norma_bruta['numero'],
                                'anio'   => $norma_bruta['anio']
                            ]));
                            curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
                            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                            $resp = curl_exec($ch);
                            $resp_data = json_decode($resp, true);
                            if ($resp_data && isset($resp_data['status']) && $resp_data['status'] == 'success') {
                                $url_especifica = $resp_data['url'];
                            }
                            curl_close($ch);
                        }
                    }*/

                    $url_final = $url_especifica ?: $norma_bruta['url_norma'];

                    // Insertar en tabla definitiva
                    $stmt_insert->execute([
                        ':tipo'     => $norma_bruta['id_tipo_norma'],
                        ':emisor'   => $norma_bruta['id_emisor_norma'],
                        ':num'      => $norma_bruta['numero'],
                        ':anio'     => $norma_bruta['anio'],
                        ':fecha'    => $norma_bruta['fecha_publicacion'],
                        ':sintesis' => $norma_bruta['sintesis'],
                        ':url'      => $url_final
                    ]);

                    $id_norma_nueva = (int)$db->lastInsertId();
                    $categorias_migradas_total += NormativaHelper::migrarCategorias($db, $id_norma_bo, $id_norma_nueva);

                    // Marcar combinación como existente para evitar duplicados en este lote
                    $combinaciones_existentes[$clave] = true;
                }

                // Borrar del buffer (siempre)
                $stmt_b_cat->execute([':id_bo' => $id_norma_bo]);
                $stmt_borrar->execute([':id_bo' => $id_norma_bo]);

                $procesados_total++;
            }

            $db->commit();
        } catch (Exception $e) {
            $db->rollBack();
            // Registrar error y continuar con el siguiente lote (o detener según criterio)
            error_log("Error en lote " . ($lote+1) . ": " . $e->getMessage());
            // Opcional: detener todos los lotes si un error es crítico
            // break;
        }

        // Liberar memoria después de cada lote (opcional)
        unset($lote_ids);
    }

    $msg = ($accion === 'promover')
        ? "Promovidas $procesados_total normas. Categorías migradas: $categorias_migradas_total. Omitidas por duplicado: $omitidas_total."
        : "Descartadas $procesados_total normas.";

    http_response_code(200);
    echo json_encode([
        "mensaje" => $msg,
        "procesados" => $procesados_total,
        "categorias_migradas" => $categorias_migradas_total,
        "omitidas_por_duplicado" => $omitidas_total
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error crítico: " . $e->getMessage()]);
}