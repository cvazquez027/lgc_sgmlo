<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

include_once '../../config/Database.php';

$database = new Database();
$db = $database->getConnection();

// Parámetros
$id_norma = isset($_GET['id_norma']) ? (int)$_GET['id_norma'] : null;
$tipo = isset($_GET['tipo']) ? trim($_GET['tipo']) : '';
$nro = isset($_GET['nro']) ? trim($_GET['nro']) : '';
$anio = isset($_GET['anio']) ? (int)$_GET['anio'] : null;
$buscar = isset($_GET['buscar']) ? trim($_GET['buscar']) : '';
$id_establecimiento = isset($_GET['id_establecimiento']) ? (int)$_GET['id_establecimiento'] : null;

try {
    $sql = "SELECT n.*, 
                     tn.descripcion AS tipo_norma_desc,
                     en.descripcion AS emisor_desc,
                     j.descripcion AS jurisdiccion_desc,
                     nj.descripcion AS nivel_jurisdiccion_desc,
                     est.descripcion AS estado_desc
              FROM norma n
              LEFT JOIN tipo_norma tn ON n.id_tipo_norma = tn.id_tipo_norma
              LEFT JOIN emisor_norma en ON n.id_emisor_norma = en.id_emisor_norma
              LEFT JOIN jurisdiccion j ON en.id_jurisdiccion = j.id_jurisdiccion
              LEFT JOIN nivel_jurisdiccion nj ON j.id_nivel_jurisdiccion = nj.id_nivel_jurisdiccion
              LEFT JOIN estado_norma est ON n.id_estado_norma = est.id_estado_norma
              WHERE 1=1";
    
    $params = [];

    if ($id_norma) {
        $sql .= " AND n.id_norma = :id_norma";
        $params[':id_norma'] = $id_norma;
    }
    if (!empty($tipo)) {
        $sql .= " AND tn.descripcion LIKE :tipo";
        $params[':tipo'] = "%$tipo%";
    }
    if (!empty($nro)) {
        $sql .= " AND n.numero LIKE :nro";
        $params[':nro'] = "%$nro%";
    }
    if (!empty($anio)) {
        $sql .= " AND n.anio = :anio";
        $params[':anio'] = $anio;
    }
    if (!empty($buscar)) {
        $sql .= " AND (tn.descripcion LIKE :buscar1 OR n.numero LIKE :buscar2 OR n.anio LIKE :buscar3 OR en.descripcion LIKE :buscar4)";
        $like = "%$buscar%";
        $params[':buscar1'] = $like;
        $params[':buscar2'] = $like;
        $params[':buscar3'] = $like;
        $params[':buscar4'] = $like;
    }

    if ($id_establecimiento) {
        $queryJur = "SELECT ce.id_jurisdiccion, j.id_nivel_jurisdiccion, j.id_jurisdiccion_sup
                     FROM cliente_establecimiento ce
                     LEFT JOIN jurisdiccion j ON ce.id_jurisdiccion = j.id_jurisdiccion
                     WHERE ce.id_cliente_establecimiento = :id_est";
        $stmtJur = $db->prepare($queryJur);
        $stmtJur->execute([':id_est' => $id_establecimiento]);
        $jurInfo = $stmtJur->fetch(PDO::FETCH_ASSOC);
        
        if ($jurInfo) {
            $jurisdiccionesPermitidas = [$jurInfo['id_jurisdiccion']];
            if ($jurInfo['id_jurisdiccion_sup']) {
                $jurisdiccionesPermitidas[] = $jurInfo['id_jurisdiccion_sup'];
                if (!in_array(1, $jurisdiccionesPermitidas)) {
                    $jurisdiccionesPermitidas[] = 1;
                }
            }
            $jurConditions = [];
            foreach ($jurisdiccionesPermitidas as $i => $jurId) {
                $placeholder = ":jur$i";
                $jurConditions[] = "en.id_jurisdiccion = $placeholder";
                $params[$placeholder] = $jurId;
            }
            $sql .= " AND (" . implode(" OR ", $jurConditions) . ")";
        }
    }

    $sql .= " ORDER BY n.anio DESC, n.numero ASC";
    
    $stmt = $db->prepare($sql);
    $stmt->execute($params);
    
    $normas = [];
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $queryCats = "SELECT c.descripcion 
                      FROM categoria_norma nc
                      JOIN categoria c ON nc.id_categoria = c.id_categoria
                      WHERE nc.id_norma = ?";
        $stmtCats = $db->prepare($queryCats);
        $stmtCats->execute([$row['id_norma']]);
        $categorias = $stmtCats->fetchAll(PDO::FETCH_COLUMN);
        $row['categorias'] = $categorias;
        $normas[] = $row;
    }
    
    http_response_code(200);
    echo json_encode(["registros" => $normas]);
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["mensaje" => "Error al leer normativa.", "debug" => $e->getMessage()]);
}
?>