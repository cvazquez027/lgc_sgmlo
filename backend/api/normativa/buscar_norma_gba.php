<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

$data = json_decode(file_get_contents("php://input"));

if (empty($data->tipo) || empty($data->numero) || empty($data->anio)) {
    http_response_code(400);
    echo json_encode(["status" => "error", "message" => "Faltan parámetros obligatorios: tipo, numero, anio"]);
    exit();
}

$tipo = strtoupper(trim($data->tipo));
$numero = $data->numero;
$anio = (int)$data->anio;
$emisor_referencia = isset($data->emisor) ? strtoupper(trim($data->emisor)) : null;

$map_tipos = [
    'DECRETO' => 'Decree',
    'RESOLUCION' => 'Resolution',
    'DISPOSICION' => 'Disposition',
    'LEY' => 'Law',
    'DECRETO-LEY' => 'DecreeLaw',
    'RESOLUCION FIRMA CONJUNTA' => 'JointResolution',
    'RESOLUCION CONJUNTA' => 'JointResolution',
];

$tipo_busqueda = $map_tipos[$tipo] ?? 'Decree';

$url_busqueda = "https://normas.gba.gob.ar/resultados?q%5Bterms%5D%5Braw_type%5D=" . urlencode($tipo_busqueda) 
                . "&q%5Bterms%5D%5Bnumber%5D=" . urlencode($numero) 
                . "&q%5Bterms%5D%5Byear%5D=" . $anio 
                . "&q%5Bsort%5D=by_publication_date_desc";

$opts = [
    'http' => [
        'method' => 'GET',
        'header' => "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n"
    ]
];
$context = stream_context_create($opts);
$html = file_get_contents($url_busqueda, false, $context);
if ($html === false) {
    http_response_code(500);
    echo json_encode(["status" => "error", "message" => "Error al consultar normas.gba.gob.ar"]);
    exit();
}

// Extraer todos los resultados usando regex (más simple que DOM)
$resultados = [];
$card_pattern = '/<div class="card-content">(.*?)<\/div>\s*<\/div>/s';
preg_match_all($card_pattern, $html, $cards);

foreach ($cards[1] as $card) {
    // URL y título
    if (preg_match('/<h3 class="card-title rule-name"><a href="([^"]+)">([^<]+)<\/a>/', $card, $title_match)) {
        $url_rel = $title_match[1];
        $url_completa = "https://normas.gba.gob.ar" . $url_rel;
        $titulo = $title_match[2];
    } else {
        continue;
    }
    // Emisor
    $emisor = '';
    if (preg_match('/<h6 class="rule-source">(.*?)<\/h6>/', $card, $source_match)) {
        $emisor = trim(str_replace('del ', '', $source_match[1]));
    }
    // Resumen
    $sintesis = '';
    if (preg_match('/<blockquote>(.*?)<\/blockquote>/s', $card, $res_match)) {
        $sintesis = trim($res_match[1]);
    }
    // Fecha
    $fecha = '';
    if (preg_match('/Fecha de publicación:\s*<\/span>\s*<span[^>]*>([^<]+)<\/span>/', $card, $fecha_match)) {
        $fecha = trim($fecha_match[1]);
    }
    
    $resultados[] = [
        'url' => $url_completa,
        'titulo' => $titulo,
        'emisor' => $emisor,
        'sintesis' => $sintesis,
        'fecha_publicacion' => $fecha
    ];
}

if (empty($resultados)) {
    echo json_encode(["status" => "not_found", "message" => "No se encontraron resultados"]);
    exit();
}

// Función para normalizar strings (quitar acentos, mayúsculas, caracteres especiales)
function normalizar($str) {
    $str = mb_strtoupper($str, 'UTF-8');
    $str = str_replace(['Á','É','Í','Ó','Ú','Ñ'], ['A','E','I','O','U','N'], $str);
    $str = preg_replace('/[^A-Z0-9 ]/', '', $str);
    return trim($str);
}

$mejor_resultado = null;
$mejor_score = -1;

foreach ($resultados as $res) {
    $score = 0;
    if ($emisor_referencia) {
        $emisor_ref_norm = normalizar($emisor_referencia);
        $emisor_res_norm = normalizar($res['emisor']);
        if ($emisor_res_norm === $emisor_ref_norm) {
            $score = 100;
        } elseif (strpos($emisor_res_norm, $emisor_ref_norm) !== false) {
            $score = 70;
        } elseif (strpos($emisor_ref_norm, $emisor_res_norm) !== false) {
            $score = 60;
        } else {
            // Comparar palabras clave
            $score = 0;
        }
    } else {
        $score = 50;
    }
    if ($score > $mejor_score) {
        $mejor_score = $score;
        $mejor_resultado = $res;
    }
}

if ($mejor_resultado) {
    echo json_encode([
        "status" => "success",
        "url" => $mejor_resultado['url'],
        "emisor" => $mejor_resultado['emisor'],
        "sintesis" => $mejor_resultado['sintesis'],
        "fecha_publicacion" => $mejor_resultado['fecha_publicacion']
    ]);
} else {
    echo json_encode(["status" => "not_found"]);
}
?>