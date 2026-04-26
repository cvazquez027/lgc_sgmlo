<?php
require_once 'db_config.php'; 

// 1. Configuración del Paginado
$resultados_por_pagina = 20;
$pagina_actual = isset($_GET['pagina']) && is_numeric($_GET['pagina']) ? (int)$_GET['pagina'] : 1;
if ($pagina_actual < 1) $pagina_actual = 1;
$offset = ($pagina_actual - 1) * $resultados_por_pagina;

// 2. Capturar las variables de los filtros
$f_jurisdiccion = $_GET['jurisdiccion'] ?? '';
$f_categoria    = $_GET['categoria'] ?? '';
$f_texto        = $_GET['texto'] ?? '';
$f_anio         = $_GET['anio'] ?? '';

// 3. Construcción dinámica del WHERE
$where_sql = " WHERE 1=1";
$params = [];
$tipos = "";

if ($f_jurisdiccion !== '') {
    $where_sql .= " AND jurisdiccion = ?";
    $params[] = $f_jurisdiccion;
    $tipos .= "s";
}

if ($f_categoria !== '') {
    $where_sql .= " AND categoria = ?";
    $params[] = $f_categoria;
    $tipos .= "s";
}

if ($f_anio !== '') {
    $where_sql .= " AND anio = ?";
    $params[] = $f_anio;
    $tipos .= "s";
}

if ($f_texto !== '') {
    $where_sql .= " AND (sintesis LIKE ? OR id_origen LIKE ?)";
    $termino_like = "%" . $f_texto . "%";
    $params[] = $termino_like;
    $params[] = $termino_like;
    $tipos .= "ss";
}

// 4. Calcular el total de páginas (Consulta COUNT)
$sql_count = "SELECT COUNT(*) as total FROM normativas" . $where_sql;
$stmt_count = $conn->prepare($sql_count);
if (!empty($params)) {
    $stmt_count->bind_param($tipos, ...$params);
}
$stmt_count->execute();
$total_rows = $stmt_count->get_result()->fetch_assoc()['total'];
$total_paginas = ceil($total_rows / $resultados_por_pagina);
$stmt_count->close();

// 5. Consulta Principal con LIMIT y OFFSET
$sql = "SELECT * FROM normativas" . $where_sql . " ORDER BY anio DESC, fecha_publicacion DESC LIMIT ? OFFSET ?";
$params[] = $resultados_por_pagina;
$params[] = $offset;
$tipos .= "ii";

$stmt = $conn->prepare($sql);
$stmt->bind_param($tipos, ...$params);
$stmt->execute();
$resultado = $stmt->get_result();

// Generar la URL base para los botones de paginación preservando los filtros
$query_params = $_GET;
unset($query_params['pagina']); 
$url_paginacion = '?' . http_build_query($query_params) . '&pagina=';
?>

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buscador Normativo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .badge-pba { background-color: #0dcaf0; color: #000; } 
        .badge-nacional { background-color: #0d6efd; color: #fff; } 
        .badge-caba { background-color: #ffc107; color: #000; } 
        .badge-cordoba { background-color: #fd7e14; color: #fff; } /* Naranja para Córdoba */
        .badge-ambiente { background-color: #198754; color: #fff; } 
        .badge-syh { background-color: #dc3545; color: #fff; } 
        .badge-ambas { background-color: #6c757d; color: #fff; } 
    </style>
</head>
<body class="bg-light">

<div class="container-fluid py-4">
    <h2 class="mb-4">Buscador Normativo</h2>

    <div class="card mb-4 shadow-sm">
        <div class="card-body">
            <form method="GET" action="visualizador.php" class="row g-3 align-items-end">
                
                <div class="col-md-3">
                    <label for="texto" class="form-label fw-bold">Buscar en Síntesis o Norma</label>
                    <input type="text" class="form-control" id="texto" name="texto" placeholder="Ej: impacto ambiental..." value="<?php echo htmlspecialchars($f_texto); ?>">
                </div>

                <div class="col-md-2">
                    <label for="anio" class="form-label fw-bold">Año</label>
                    <input type="number" class="form-control" id="anio" name="anio" placeholder="Ej: 2023" value="<?php echo htmlspecialchars($f_anio); ?>">
                </div>

                <div class="col-md-2">
                    <label for="jurisdiccion" class="form-label fw-bold">Jurisdicción</label>
                    <select class="form-select" id="jurisdiccion" name="jurisdiccion">
                        <option value="">Todas</option>
                        <option value="Nacional" <?php echo ($f_jurisdiccion === 'Nacional') ? 'selected' : ''; ?>>Nacional</option>
                        <option value="PBA" <?php echo ($f_jurisdiccion === 'PBA') ? 'selected' : ''; ?>>PBA</option>
                        <option value="CABA" <?php echo ($f_jurisdiccion === 'CABA') ? 'selected' : ''; ?>>CABA</option>
                        <option value="Córdoba" <?php echo ($f_jurisdiccion === 'Córdoba' || $f_jurisdiccion === 'CBA') ? 'selected' : ''; ?>>Córdoba</option>
                    </select>
                </div>

                <div class="col-md-3">
                    <label for="categoria" class="form-label fw-bold">Categoría</label>
                    <select class="form-select" id="categoria" name="categoria">
                        <option value="">Todas</option>
                        <option value="Ambiente" <?php echo ($f_categoria === 'Ambiente') ? 'selected' : ''; ?>>Ambiente</option>
                        <option value="Seguridad e Higiene" <?php echo ($f_categoria === 'Seguridad e Higiene') ? 'selected' : ''; ?>>Seguridad e Higiene</option>
                        <option value="Ambas" <?php echo ($f_categoria === 'Ambas') ? 'selected' : ''; ?>>Ambas</option>
                    </select>
                </div>

                <div class="col-md-2 d-grid gap-2 d-md-flex">
                    <button type="submit" class="btn btn-primary w-100">Filtrar</button>
                    <a href="visualizador.php" class="btn btn-outline-secondary w-100">Limpiar</a>
                </div>
            </form>
        </div>
    </div>

    <div class="card shadow-sm mb-4">
        <div class="card-header bg-white d-flex justify-content-between align-items-center">
            <h5 class="mb-0">Resultados</h5>
            <span class="badge bg-secondary"><?php echo $total_rows; ?> registros totales</span>
        </div>
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-hover table-striped mb-0 align-middle">
                    <thead class="table-dark">
                        <tr>
                            <th scope="col" style="width: 10%;">Jurisdicción</th>
                            <th scope="col" style="width: 15%;">Norma</th>
                            <th scope="col" style="width: 10%;">Fecha</th>
                            <th scope="col" style="width: 15%;">Categoría</th>
                            <th scope="col" style="width: 40%;">Síntesis</th>
                            <th scope="col" style="width: 10%; text-align: center;">Enlace</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php if ($resultado->num_rows > 0): ?>
                            <?php while($row = $resultado->fetch_assoc()): 
                                $badge_jur = 'bg-secondary';
                                if (strtoupper($row['jurisdiccion']) == 'PBA') $badge_jur = 'badge-pba';
                                elseif (strtoupper($row['jurisdiccion']) == 'NACIONAL') $badge_jur = 'badge-nacional';
                                elseif (strtoupper($row['jurisdiccion']) == 'CABA') $badge_jur = 'badge-caba';
                                elseif (strtoupper($row['jurisdiccion']) == 'CÓRDOBA' || strtoupper($row['jurisdiccion']) == 'CORDOBA' || strtoupper($row['jurisdiccion']) == 'CBA') $badge_jur = 'badge-cordoba';

                                $badge_cat = 'bg-secondary';
                                if ($row['categoria'] == 'Ambiente') $badge_cat = 'badge-ambiente';
                                elseif ($row['categoria'] == 'Seguridad e Higiene') $badge_cat = 'badge-syh';
                                elseif ($row['categoria'] == 'Ambas') $badge_cat = 'badge-ambas';
                            ?>
                            <tr>
                                <td><span class="badge <?php echo $badge_jur; ?> fs-6"><?php echo htmlspecialchars($row['jurisdiccion']); ?></span></td>
                                <td>
                                    <strong><?php echo htmlspecialchars($row['tipo_norma']) . ' ' . htmlspecialchars($row['numero']); ?></strong><br>
                                    <small class="text-muted">Año: <?php echo htmlspecialchars($row['anio']); ?></small>
                                </td>
                                <td><?php $fecha = date_create($row['fecha_publicacion']); echo $fecha ? date_format($fecha, 'd/m/Y') : '-'; ?></td>
                                <td><span class="badge <?php echo $badge_cat; ?>"><?php echo htmlspecialchars($row['categoria']); ?></span></td>
                                <td><p class="mb-0 small" style="display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;"><?php echo htmlspecialchars($row['sintesis']); ?></p></td>
                                <td class="text-center"><a href="<?php echo htmlspecialchars($row['url_origen']); ?>" target="_blank" class="btn btn-sm btn-outline-primary">Ver Oficial</a></td>
                            </tr>
                            <?php endwhile; ?>
                        <?php else: ?>
                            <tr><td colspan="6" class="text-center py-4 text-muted">No se encontraron normativas con los filtros aplicados.</td></tr>
                        <?php endif; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <?php if ($total_paginas > 1): ?>
    <nav aria-label="Navegación de páginas">
        <ul class="pagination justify-content-center">
            <li class="page-item <?php echo ($pagina_actual <= 1) ? 'disabled' : ''; ?>">
                <a class="page-link" href="<?php echo $url_paginacion . ($pagina_actual - 1); ?>">Anterior</a>
            </li>
            
            <?php 
            $inicio_pag = max(1, $pagina_actual - 3);
            $fin_pag = min($total_paginas, $pagina_actual + 3);
            for ($i = $inicio_pag; $i <= $fin_pag; $i++): 
            ?>
                <li class="page-item <?php echo ($i == $pagina_actual) ? 'active' : ''; ?>">
                    <a class="page-link" href="<?php echo $url_paginacion . $i; ?>"><?php echo $i; ?></a>
                </li>
            <?php endfor; ?>

            <li class="page-item <?php echo ($pagina_actual >= $total_paginas) ? 'disabled' : ''; ?>">
                <a class="page-link" href="<?php echo $url_paginacion . ($pagina_actual + 1); ?>">Siguiente</a>
            </li>
        </ul>
    </nav>
    <?php endif; ?>

</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
<?php
$stmt->close();
$conn->close();
?>