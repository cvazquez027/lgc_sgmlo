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

$data = json_decode(file_get_contents("php://input"));

// Ahora esperamos un array de IDs: ids_normas
if (empty($data->ids_normas) || !is_array($data->ids_normas) || empty($data->accion)) {
    http_response_code(400);
    echo json_encode(["mensaje" => "Faltan parámetros obligatorios o formato incorrecto."]);
    exit();
}

$accion = htmlspecialchars(strip_tags($data->accion)); // "promover" o "descartar"

$database = new Database();
$db = $database->getConnection();

try {
    $db->beginTransaction();

    $q_leer = "SELECT * FROM norma_bo WHERE id_norma_bo = :id_bo FOR UPDATE";
    $stmt_leer = $db->prepare($q_leer);

    $q_insertar = "INSERT INTO norma 
        (id_tipo_norma, id_emisor_norma, numero, anio, fecha_publicacion, sintesis, url_norma, id_estado_norma, origen_carga) 
        VALUES (:tipo, :emisor, :num, :anio, :fecha, :sintesis, :url, 1, 'Scraping')";
    $stmt_insert = $db->prepare($q_insertar);

    $q_borrar_cat = "DELETE FROM categoria_norma_bo WHERE id_norma_bo = :id_bo";
    $stmt_b_cat = $db->prepare($q_borrar_cat);

    $q_borrar = "DELETE FROM norma_bo WHERE id_norma_bo = :id_bo";
    $stmt_borrar = $db->prepare($q_borrar);

    $procesados = 0;

    foreach ($data->ids_normas as $id_raw) {
        $id_norma_bo = filter_var($id_raw, FILTER_VALIDATE_INT);
        if (!$id_norma_bo) continue;

        if ($accion === 'promover') {
            $stmt_leer->execute([':id_bo' => $id_norma_bo]);
            $norma_bruta = $stmt_leer->fetch(PDO::FETCH_ASSOC);
            if ($norma_bruta) {
                // Intentar obtener URL específica
                $url_especifica = null;
                if ($norma_bruta['id_tipo_norma'] && $norma_bruta['numero'] && $norma_bruta['anio']) {
                    $query_tipo = "SELECT descripcion FROM tipo_norma WHERE id_tipo_norma = :id";
                    $stmt_t = $db->prepare($query_tipo);
                    $stmt_t->execute([':id' => $norma_bruta['id_tipo_norma']]);
                    $tipo_desc = $stmt_t->fetchColumn();
                    if ($tipo_desc) {
                        $ch = curl_init();
                        curl_setopt($ch, CURLOPT_URL, "http://localhost/lgc_sgmlo/backend/api/normativa/buscar_url_gba.php");
                        curl_setopt($ch, CURLOPT_POST, 1);
                        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(['tipo' => $tipo_desc, 'numero' => $norma_bruta['numero'], 'anio' => $norma_bruta['anio']]));
                        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
                        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                        $resp = curl_exec($ch);
                        $data = json_decode($resp, true);
                        if ($data && $data['status'] == 'success') {
                            $url_especifica = $data['url'];
                        }
                        curl_close($ch);
                    }
                }
                $url_final = $url_especifica ?: $norma_bruta['url_norma']; // fallback al PDF
                $stmt_insert->execute([
                    ':tipo' => $norma_bruta['id_tipo_norma'],
                    ':emisor' => $norma_bruta['id_emisor_norma'],
                    ':num' => $norma_bruta['numero'],
                    ':anio' => $norma_bruta['anio'],
                    ':fecha' => $norma_bruta['fecha_publicacion'],
                    ':sintesis' => $norma_bruta['sintesis'],
                    ':url' => $url_final
                ]);
            }
        }

        // Borrado del buffer temporal (para ambas acciones)
        $stmt_b_cat->execute([':id_bo' => $id_norma_bo]);
        $stmt_borrar->execute([':id_bo' => $id_norma_bo]);
        
        $procesados++;
    }

    $db->commit();
    http_response_code(200);
    $msg = $accion === 'promover' ? "$procesados normativas promovidas exitosamente." : "$procesados normativas descartadas.";
    echo json_encode(["mensaje" => $msg]);

} catch (Exception $e) {
    $db->rollBack();
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al procesar la normativa.", "error" => $e->getMessage()]);
}
?>