-- =========================================================================================
-- SCRIPT DDL: SGMLO (Sistema de Gestión de Matriz Legal Online)
-- Motor: MySQL (Workbench)
-- =========================================================================================

CREATE DATABASE IF NOT EXISTS sgmlo_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sgmlo_db;

SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------
-- MÓDULO 1: Seguridad, Usuarios y Auditoría
-- -----------------------------------------------------
CREATE TABLE cliente (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    cuit VARCHAR(20) NOT NULL,
    razon_social VARCHAR(255) NOT NULL,
    nombre_fantasia VARCHAR(255),
    vigente BOOLEAN DEFAULT TRUE
);

CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NULL, -- NULL si es administrador interno (DataV/LGC)
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    ultimo_login DATETIME,
    ultimo_login_ip VARCHAR(45),
    intentos_fallidos INT DEFAULT 0,
    fecha_alta DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion DATETIME ON UPDATE CURRENT_TIMESTAMP,
    vigente BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente) ON DELETE RESTRICT
);

CREATE TABLE rol (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    vigente BOOLEAN DEFAULT TRUE
);

CREATE TABLE usuario_rol (
    id_usuario_rol INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_rol INT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_rol) REFERENCES rol(id_rol) ON DELETE CASCADE
);

CREATE TABLE permiso (
    id_permiso INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(255) NOT NULL,
    vigente BOOLEAN DEFAULT TRUE
);

CREATE TABLE rol_permiso (
    id_rol_permiso INT AUTO_INCREMENT PRIMARY KEY,
    id_rol INT NOT NULL,
    id_permiso INT NOT NULL,
    FOREIGN KEY (id_rol) REFERENCES rol(id_rol) ON DELETE CASCADE,
    FOREIGN KEY (id_permiso) REFERENCES permiso(id_permiso) ON DELETE CASCADE
);

CREATE TABLE auditoria (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    tabla_afectada VARCHAR(100) NOT NULL,
    accion ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    id_registro INT NOT NULL,
    id_usuario INT NOT NULL,
    ip_origen VARCHAR(45),
    fecha_evento DATETIME DEFAULT CURRENT_TIMESTAMP,
    datos_json JSON NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT
);

CREATE TABLE configuracion (
    id_configuracion INT AUTO_INCREMENT PRIMARY KEY,
    parametro VARCHAR(100) NOT NULL,
    valor TEXT NOT NULL,
    descripcion VARCHAR(255),
    fecha_desde DATETIME,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion DATETIME ON UPDATE CURRENT_TIMESTAMP
);

-- -----------------------------------------------------
-- MÓDULO 2: Clientes y Establecimientos
-- -----------------------------------------------------
CREATE TABLE nivel_jurisdiccion (
    id_nivel_jurisdiccion INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    nivel INT NOT NULL,
    vigente BOOLEAN DEFAULT TRUE
);

CREATE TABLE jurisdiccion (
    id_jurisdiccion INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(255) NOT NULL,
    id_nivel_jurisdiccion INT NOT NULL,
    id_jurisdiccion_sup INT NULL,
    FOREIGN KEY (id_nivel_jurisdiccion) REFERENCES nivel_jurisdiccion(id_nivel_jurisdiccion) ON DELETE RESTRICT,
    FOREIGN KEY (id_jurisdiccion_sup) REFERENCES jurisdiccion(id_jurisdiccion) ON DELETE SET NULL
);

CREATE TABLE cliente_establecimiento (
    id_cliente_establecimiento INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_jurisdiccion INT NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    vigente BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente) ON DELETE CASCADE,
    FOREIGN KEY (id_jurisdiccion) REFERENCES jurisdiccion(id_jurisdiccion) ON DELETE RESTRICT
);

CREATE TABLE tipo_contacto (
    id_tipo_contacto INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    vigente BOOLEAN DEFAULT TRUE
);

CREATE TABLE datos_contacto (
    id_datos_contacto INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_cliente_establecimiento INT NULL,
    id_tipo_contacto INT NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    fecha_actualizacion DATETIME ON UPDATE CURRENT_TIMESTAMP,
    vigente BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_cliente) REFERENCES cliente(id_cliente) ON DELETE CASCADE,
    FOREIGN KEY (id_cliente_establecimiento) REFERENCES cliente_establecimiento(id_cliente_establecimiento) ON DELETE CASCADE,
    FOREIGN KEY (id_tipo_contacto) REFERENCES tipo_contacto(id_tipo_contacto) ON DELETE RESTRICT
);

-- -----------------------------------------------------
-- MÓDULO 3: Motor de Normativa y Scraping
-- -----------------------------------------------------
CREATE TABLE categoria (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(255) NOT NULL,
    vigente BOOLEAN DEFAULT TRUE
);

CREATE TABLE tipo_norma (
    id_tipo_norma INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    vigente BOOLEAN DEFAULT TRUE
);

CREATE TABLE estado_norma (
    id_estado_norma INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    vigente BOOLEAN DEFAULT TRUE
);

CREATE TABLE emisor_norma (
    id_emisor_norma INT AUTO_INCREMENT PRIMARY KEY,
    id_jurisdiccion INT NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    FOREIGN KEY (id_jurisdiccion) REFERENCES jurisdiccion(id_jurisdiccion) ON DELETE RESTRICT
);

CREATE TABLE norma (
    id_norma INT AUTO_INCREMENT PRIMARY KEY,
    id_tipo_norma INT NOT NULL,
    id_emisor_norma INT NOT NULL,
    numero VARCHAR(50),
    anio INT,
    fecha_publicacion DATE,
    sintesis TEXT,
    url_norma VARCHAR(500),
    id_estado_norma INT NOT NULL,
    origen_carga ENUM('Manual', 'Scraping') DEFAULT 'Manual',
    fecha_ultimo_scraping DATETIME NULL,
    FOREIGN KEY (id_tipo_norma) REFERENCES tipo_norma(id_tipo_norma) ON DELETE RESTRICT,
    FOREIGN KEY (id_emisor_norma) REFERENCES emisor_norma(id_emisor_norma) ON DELETE RESTRICT,
    FOREIGN KEY (id_estado_norma) REFERENCES estado_norma(id_estado_norma) ON DELETE RESTRICT
);

CREATE TABLE categoria_norma (
    id_categoria_norma INT AUTO_INCREMENT PRIMARY KEY,
    id_norma INT NOT NULL,
    id_categoria INT NOT NULL,
    FOREIGN KEY (id_norma) REFERENCES norma(id_norma) ON DELETE CASCADE,
    FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria) ON DELETE CASCADE
);

CREATE TABLE norma_bo (
    id_norma_bo INT AUTO_INCREMENT PRIMARY KEY,
    id_tipo_norma INT NOT NULL,
    id_emisor_norma INT NOT NULL,
    numero VARCHAR(50),
    anio INT,
    fecha_publicacion DATE,
    sintesis TEXT,
    url_norma VARCHAR(500),
    id_estado_norma INT NOT NULL,
    origen_carga ENUM('Manual', 'Scraping') DEFAULT 'Scraping',
    fecha_ultimo_scraping DATETIME NULL,
    FOREIGN KEY (id_tipo_norma) REFERENCES tipo_norma(id_tipo_norma) ON DELETE RESTRICT,
    FOREIGN KEY (id_emisor_norma) REFERENCES emisor_norma(id_emisor_norma) ON DELETE RESTRICT,
    FOREIGN KEY (id_estado_norma) REFERENCES estado_norma(id_estado_norma) ON DELETE RESTRICT
);

CREATE TABLE categoria_norma_bo (
    id_categoria_norma_bo INT AUTO_INCREMENT PRIMARY KEY,
    id_norma_bo INT NOT NULL,
    id_categoria INT NOT NULL,
    FOREIGN KEY (id_norma_bo) REFERENCES norma_bo(id_norma_bo) ON DELETE CASCADE,
    FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria) ON DELETE CASCADE
);

-- -----------------------------------------------------
-- MÓDULO 4: Matriz Legal Operativa
-- -----------------------------------------------------
CREATE TABLE estado_matriz (
    id_estado_matriz INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    vigente BOOLEAN DEFAULT TRUE
);

CREATE TABLE matriz (
    id_matriz INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente_establecimiento INT NOT NULL,
    fecha_desde DATE NOT NULL,
    version INT DEFAULT 1,
    id_estado_matriz INT NOT NULL,
    vigente BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_cliente_establecimiento) REFERENCES cliente_establecimiento(id_cliente_establecimiento) ON DELETE CASCADE,
    FOREIGN KEY (id_estado_matriz) REFERENCES estado_matriz(id_estado_matriz) ON DELETE RESTRICT
);

CREATE TABLE estado_cumplimiento (
    id_estado_cumplimiento INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL,
    color_hex VARCHAR(10),
    vigente BOOLEAN DEFAULT TRUE
);

CREATE TABLE tipo_modalidad (
    id_tipo_modalidad INT AUTO_INCREMENT PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL
);

CREATE TABLE requisito (
    id_requisito INT AUTO_INCREMENT PRIMARY KEY,
    id_norma INT NOT NULL,
    resumen_legal TEXT NOT NULL,
    articulos_aplicables VARCHAR(255),
    FOREIGN KEY (id_norma) REFERENCES norma(id_norma) ON DELETE CASCADE
);

CREATE TABLE matriz_detalle (
    id_matriz_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_matriz INT NOT NULL,
    id_norma INT NOT NULL,
    id_requisito INT NOT NULL,
    FOREIGN KEY (id_matriz) REFERENCES matriz(id_matriz) ON DELETE CASCADE,
    FOREIGN KEY (id_norma) REFERENCES norma(id_norma) ON DELETE RESTRICT,
    FOREIGN KEY (id_requisito) REFERENCES requisito(id_requisito) ON DELETE RESTRICT
);

CREATE TABLE requisito_matriz_detalle (
    id_requisito_matriz_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_matriz_detalle INT NOT NULL,
    interpretacion_aplicacion TEXT,
    id_tipo_modalidad INT NULL,
    obs_modalidad TEXT,
    vencimiento_plazo DATE,
    fecha_cumplimiento DATE,
    obs_plazo TEXT,
    proceso_aplica VARCHAR(255),
    detalle_tema VARCHAR(255),
    evidencia_cumplimiento TEXT,
    responsable_cumplimiento VARCHAR(255),
    verificacion_cumplimiento TEXT,
    id_estado_cumplimiento INT NOT NULL,
    obs_estado_cumplimiento TEXT,
    FOREIGN KEY (id_matriz_detalle) REFERENCES matriz_detalle(id_matriz_detalle) ON DELETE CASCADE,
    FOREIGN KEY (id_tipo_modalidad) REFERENCES tipo_modalidad(id_tipo_modalidad) ON DELETE SET NULL,
    FOREIGN KEY (id_estado_cumplimiento) REFERENCES estado_cumplimiento(id_estado_cumplimiento) ON DELETE RESTRICT
);

-- -----------------------------------------------------
-- MÓDULO 5: Gestión Documental
-- -----------------------------------------------------
CREATE TABLE documentacion (
    id_documentacion INT AUTO_INCREMENT PRIMARY KEY,
    path_archivos VARCHAR(500) NOT NULL,
    nombre_original VARCHAR(255) NOT NULL,
    tipo_mime VARCHAR(100),
    peso_bytes INT,
    id_usuario_subida INT NOT NULL,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    vigente BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_usuario_subida) REFERENCES usuario(id_usuario) ON DELETE RESTRICT
);

CREATE TABLE doc_requisito_matriz_detalle (
    id_doc_requisito_matriz_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_documentacion INT NOT NULL,
    id_requisito_matriz_detalle INT NOT NULL,
    FOREIGN KEY (id_documentacion) REFERENCES documentacion(id_documentacion) ON DELETE CASCADE,
    FOREIGN KEY (id_requisito_matriz_detalle) REFERENCES requisito_matriz_detalle(id_requisito_matriz_detalle) ON DELETE CASCADE
);

SET FOREIGN_KEY_CHECKS = 1;