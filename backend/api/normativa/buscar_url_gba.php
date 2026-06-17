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
    echo json_encode(["status" => "error", "message" => "Faltan parámetros"]);
    exit();
}

$tipo = strtoupper(trim($data->tipo));
$numero = $data->numero;
$anio = (int)$data->anio;

// Mapeo de tipos al valor que espera el formulario de normas.gba.gob.ar
$map = [
    'DECRETO' => 'Decree',
    'RESOLUCION' => 'Resolution',
    'DISPOSICION' => 'Disposition',
    'LEY' => 'Law',
    'DECRETO-LEY' => 'DecreeLaw',
    'RESOLUCION FIRMA CONJUNTA' => 'JointResolution',
    'RESOLUCION CONJUNTA' => 'JointResolution',
];

$tipo_param = $map[$tipo] ?? 'Decree';

$url_busqueda = "https://normas.gba.gob.ar/resultados?q%5Bterms%5D%5Braw_type%5D=" . urlencode($tipo_param) . "&q%5Bterms%5D%5Bnumber%5D=" . urlencode($numero) . "&q%5Bterms%5D%5Byear%5D=" . $anio . "&q%5Bsort%5D=by_publication_date_desc";

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

// Buscar el enlace en la página de resultados
preg_match('/<h3 class="card-title rule-name"><a href="([^"]+)">/', $html, $matches);
if (isset($matches[1])) {
    $url_norma = "https://normas.gba.gob.ar" . $matches[1];
    echo json_encode(["status" => "success", "url" => $url_norma]);
} else {
    echo json_encode(["status" => "not_found", "url" => null]);
}
?>