-- CIRION lote 2: normas nuevas + vínculos a ítems ya cargados (IDs reales).
-- Anti-duplicados de normas y de vínculos. Ejecutar de corrido.
START TRANSACTION;

-- normas nuevas
-- decreto 2020/2007
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '2020', '2007', NULL, 'Decreto reglamentario de la Ley 2214 de Residuos Peligrosos de la CABA. Reglamenta la generación, manipulación, almacenamiento, transporte, tratamiento y disposición final de residuos peligrosos, el Registro de Generadores, Operadores y Transportistas y el Certificado de Gestión.', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/anexos/drl2214.html', 1, 'Manual', NOW());
SET @nc17 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc17, 8);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc17, 85);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc17, 96);
-- decreto 639/2007
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '639', '2007', NULL, 'Decreto reglamentario de la Ley 1854 (Basura Cero / Gestión Integral de Residuos Sólidos Urbanos) de la CABA. Regula la separación en origen y la disposición inicial selectiva en fracciones de residuos húmedos y secos.', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/anexos/drl1854.html', 1, 'Manual', NOW());
SET @nc18 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc18, 85);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc18, 97);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc18, 98);
-- decreto 1886/2001
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '1886', '2001', NULL, 'Decreto reglamentario de la Ley 154 de Residuos Patogénicos de la CABA. Regula la generación, manipulación, transporte, tratamiento y disposición final de los residuos patogénicos.', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/anexos/drl154.html', 1, 'Manual', NOW());
SET @nc19 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc19, 85);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc19, 95);
-- decreto 706/2005
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '706', '2005', NULL, 'Modifica la reglamentación de la Ley 154 de Residuos Patogénicos de la CABA (Decreto 1886/01), en materia de gestión de residuos patogénicos.', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/anexos/drl154.html', 1, 'Manual', NOW());
SET @nc20 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc20, 85);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc20, 95);
-- decreto 51/2018
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '51', '2018', NULL, 'Decreto reglamentario de la Ley 5920 de la CABA, que pone en vigencia el Sistema de Autoprotección (planes de prevención y respuesta ante emergencias). Autoridad: Dirección General de Defensa Civil.', 'https://boletinoficial.buenosaires.gob.ar/normativaba/norma/385850', 1, 'Manual', NOW());
SET @nc21 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc21, 18);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc21, 47);
-- ley 27159/2015
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(1, 1, '27159', '2015', '2015-07-01', 'Regula un sistema de prevención integral de eventos por muerte súbita en espacios públicos y privados de acceso público, para reducir la morbimortalidad de origen cardiovascular. Obliga a instalar Desfibriladores Externos Automáticos (DEA), señalizarlos y capacitar al personal en RCP y su uso. Crea el Registro Nacional de DEA.', 'https://www.argentina.gob.ar/normativa/nacional/ley-27159-249563', 1, 'Manual', NOW());
SET @nc22 := LAST_INSERT_ID();
-- decreto 402/2022
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 2, '402', '2022', '2022-07-13', 'Reglamenta la Ley 27159 de prevención integral de la muerte súbita. Designa al Ministerio de Salud de la Nación como autoridad de aplicación, define los espacios cardioasistidos y la obligatoriedad de contar con al menos un DEA en lugares con circulación diaria superior a 1000 personas.', 'https://www.argentina.gob.ar/normativa/nacional/decreto-402-2022-368050', 1, 'Manual', NOW());
SET @nc23 := LAST_INSERT_ID();
-- ley 1708/None — Modificación del Código de Habilitaciones y Verificaciones (artículo/anexo específico a verificar).
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(1, 16, '1708', NULL, NULL, 'Modifica el Código de Habilitaciones y Verificaciones de la Ciudad Autónoma de Buenos Aires, en materia de requisitos de habilitación de actividades y obras.', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/ley1708.html', 1, 'Manual', NOW());
SET @nc24 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc24, 61);
-- ley 1822/None — Modificación del Código de Habilitaciones y Verificaciones (artículo/anexo específico a verificar).
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(1, 16, '1822', NULL, NULL, 'Modifica el Código de Habilitaciones y Verificaciones de la Ciudad Autónoma de Buenos Aires, en materia de requisitos de habilitación de actividades y obras.', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/ley1822.html', 1, 'Manual', NOW());
SET @nc25 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc25, 61);
-- ley 2156/None — Modificación del Código de Habilitaciones y Verificaciones (artículo/anexo específico a verificar).
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(1, 16, '2156', NULL, NULL, 'Modifica el Código de Habilitaciones y Verificaciones de la Ciudad Autónoma de Buenos Aires, en materia de requisitos de habilitación de actividades y obras.', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/ley2156.html', 1, 'Manual', NOW());
SET @nc26 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc26, 61);
-- ley 2287/None — Modificación del Código de Habilitaciones y Verificaciones (artículo/anexo específico a verificar).
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(1, 16, '2287', NULL, NULL, 'Modifica el Código de Habilitaciones y Verificaciones de la Ciudad Autónoma de Buenos Aires, en materia de requisitos de habilitación de actividades y obras.', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/ley2287.html', 1, 'Manual', NOW());
SET @nc27 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc27, 61);
-- ley 2581/None — Modificación del Código de Habilitaciones y Verificaciones (artículo/anexo específico a verificar).
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(1, 16, '2581', NULL, NULL, 'Modifica el Código de Habilitaciones y Verificaciones de la Ciudad Autónoma de Buenos Aires, en materia de requisitos de habilitación de actividades y obras.', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/ley2581.html', 1, 'Manual', NOW());
SET @nc28 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc28, 61);
-- ley 3039/None — Modificación del Código de Habilitaciones y Verificaciones (artículo/anexo específico a verificar).
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(1, 16, '3039', NULL, NULL, 'Modifica el Código de Habilitaciones y Verificaciones de la Ciudad Autónoma de Buenos Aires, en materia de requisitos de habilitación de actividades y obras.', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/ley3039.html', 1, 'Manual', NOW());
SET @nc29 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc29, 61);
-- ley 3271/None — Modificación del Código de Habilitaciones y Verificaciones (artículo/anexo específico a verificar).
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(1, 16, '3271', NULL, NULL, 'Modifica el Código de Habilitaciones y Verificaciones de la Ciudad Autónoma de Buenos Aires, en materia de requisitos de habilitación de actividades y obras.', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/ley3271.html', 1, 'Manual', NOW());
SET @nc30 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc30, 61);
-- ordenanza 33266/None — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(9, 338, '33266', NULL, NULL, '[Síntesis provisional tomada de la matriz — verificar] Habilitacion', NULL, 1, 'Manual', NOW());
SET @nc31 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc31, 61);
-- disposicion 8444/2007 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(8, 18, '8444', '2007', NULL, '[Síntesis provisional tomada de la matriz — verificar] Habilitacion', NULL, 1, 'Manual', NOW());
SET @nc32 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc32, 61);
-- ley 4040/None — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(1, 16, '4040', NULL, NULL, '[Síntesis provisional tomada de la matriz — verificar] Ambiente', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/ley4040.html', 1, 'Manual', NOW());
SET @nc33 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc33, 9);
-- ley 3393/None — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(1, 16, '3393', NULL, NULL, '[Síntesis provisional tomada de la matriz — verificar] Ambiente', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/ley3393.html', 1, 'Manual', NOW());
SET @nc34 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc34, 9);
-- ley 3579/None — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(1, 16, '3579', NULL, NULL, '[Síntesis provisional tomada de la matriz — verificar] Ambiente', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/ley3579.html', 1, 'Manual', NOW());
SET @nc35 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc35, 9);
-- resolucion conjunta 244/2000 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(6, 18, '244', '2000', NULL, '[Síntesis provisional tomada de la matriz — verificar] Ambiente', NULL, 1, 'Manual', NOW());
SET @nc36 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc36, 9);
-- resolucion conjunta 103/2015 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(6, 18, '103', '2015', NULL, '[Síntesis provisional tomada de la matriz — verificar] Ambiente', NULL, 1, 'Manual', NOW());
SET @nc37 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc37, 9);
-- ley 6598/2022 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(1, 16, '6598', '2022', NULL, '[Síntesis provisional tomada de la matriz — verificar] Ley 3871 y Ley CABA 6598/2022: LEGISLATURA DE CABA \nModifíca el varios artículos de la Ley 3871 sobre el "Plan de Adaptación y Mitigación del Cambio Climático de la Ciudad Autónoma de Buenos Aires" .', 'http://www2.cedom.gob.ar/es/legislacion/normas/leyes/ley6598.html', 1, 'Manual', NOW());
SET @nc38 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc38, 25);
-- decreto 220/2007 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '220', '2007', NULL, '[Síntesis provisional tomada de la matriz — verificar] Ambiente', NULL, 1, 'Manual', NOW());
SET @nc39 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc39, 9);
-- resolucion conjunta 199/2023 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(6, 18, '199', '2023', NULL, '[Síntesis provisional tomada de la matriz — verificar] Ordenameinto Ambiental del Territorio (OAT)/Institucional', NULL, 1, 'Manual', NOW());
SET @nc40 := LAST_INSERT_ID();
-- resolucion conjunta 978/2012 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(6, 18, '978', '2012', NULL, '[Síntesis provisional tomada de la matriz — verificar] Ambiente', NULL, 1, 'Manual', NOW());
SET @nc41 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc41, 9);
-- decreto 705/2011 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '705', '2011', NULL, '[Síntesis provisional tomada de la matriz — verificar] Ambiente', NULL, 1, 'Manual', NOW());
SET @nc42 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc42, 9);
-- decreto 827/2015 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '827', '2015', NULL, '[Síntesis provisional tomada de la matriz — verificar] Ambiente', NULL, 1, 'Manual', NOW());
SET @nc43 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc43, 9);
-- resolucion conjunta 2/2015 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(6, 18, '2', '2015', NULL, '[Síntesis provisional tomada de la matriz — verificar] Ambiente', NULL, 1, 'Manual', NOW());
SET @nc44 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc44, 9);
-- decreto 202/2005 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '202', '2005', NULL, '[Síntesis provisional tomada de la matriz — verificar] Ambiente', NULL, 1, 'Manual', NOW());
SET @nc45 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc45, 9);
-- resolucion conjunta 6/2011 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(6, 18, '6', '2011', NULL, '[Síntesis provisional tomada de la matriz — verificar] Ambiente', NULL, 1, 'Manual', NOW());
SET @nc46 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc46, 9);
-- ordenanza 36352/None — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(9, 338, '36352', NULL, NULL, '[Síntesis provisional tomada de la matriz — verificar] Deben llevarse a cabo desinfecciones y desratizaciones mediante empresas registradas y con Director Tecnico habilitado por APRA.\nLa Resolucion 452/18 ha derogado la Disposicion 710-14 que en su articulo 1 establecida: la obligatoriedad para consorcistas, representantes y/o administradores del Consorcio de Propiedad Horizontal, establecimientos públicos y privados, de contar con el Certificado de Desinfección y Desinfestación (CEDyT) en forma mensual,', NULL, 1, 'Manual', NOW());
SET @nc47 := LAST_INSERT_ID();
-- decreto 8151/None — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '8151', NULL, NULL, '[Síntesis provisional tomada de la matriz — verificar] Deben llevarse a cabo desinfecciones y desratizaciones mediante empresas registradas y con Director Tecnico habilitado por APRA.\nLa Resolucion 452/18 ha derogado la Disposicion 710-14 que en su articulo 1 establecida: la obligatoriedad para consorcistas, representantes y/o administradores del Consorcio de Propiedad Horizontal, establecimientos públicos y privados, de contar con el Certificado de Desinfección y Desinfestación (CEDyT) en forma mensual,', NULL, 1, 'Manual', NOW());
SET @nc48 := LAST_INSERT_ID();
-- disposicion 705/2015 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(8, 18, '705', '2015', NULL, '[Síntesis provisional tomada de la matriz — verificar] Deben llevarse a cabo desinfecciones y desratizaciones mediante empresas registradas y con Director Tecnico habilitado por APRA.\nLa Resolucion 452/18 ha derogado la Disposicion 710-14 que en su articulo 1 establecida: la obligatoriedad para consorcistas, representantes y/o administradores del Consorcio de Propiedad Horizontal, establecimientos públicos y privados, de contar con el Certificado de Desinfección y Desinfestación (CEDyT) en forma mensual,', NULL, 1, 'Manual', NOW());
SET @nc49 := LAST_INSERT_ID();
-- ordenanza 45593/None — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(9, 338, '45593', NULL, NULL, '[Síntesis provisional tomada de la matriz — verificar] Se estabecen como obligaciones: 1 Contratar a una empresa habilitada a fin de realizar la limpieza de los tanques de agua, en forma trimestral. 2 Requerir la entrega del Certificado de Limpieza y Desinfección de Tanques de Agua Potable (CLDTAP)\nLa Resolucion 452/18 ha derogado la Disposicion 710-14 que en su articulo 1 establecida: la obligatoriedad para consorcistas, representantes y/o administradores del Consorcio de Propiedad Horizontal, establecimientos públicos y privados, de contar con el Certificado de Desinfección y Desinfestación (CEDyT) en forma mensual,', NULL, 1, 'Manual', NOW());
SET @nc50 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc50, 5);
-- decreto 2045/1993 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '2045', '1993', NULL, '[Síntesis provisional tomada de la matriz — verificar] Se estabecen como obligaciones: 1 Contratar a una empresa habilitada a fin de realizar la limpieza de los tanques de agua, en forma trimestral. 2 Requerir la entrega del Certificado de Limpieza y Desinfección de Tanques de Agua Potable (CLDTAP)\nLa Resolucion 452/18 ha derogado la Disposicion 710-14 que en su articulo 1 establecida: la obligatoriedad para consorcistas, representantes y/o administradores del Consorcio de Propiedad Horizontal, establecimientos públicos y privados, de contar con el Certificado de Desinfección y Desinfestación (CEDyT) en forma mensual,', NULL, 1, 'Manual', NOW());
SET @nc51 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc51, 5);
-- resolucion conjunta 452/2018 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(6, 18, '452', '2018', NULL, '[Síntesis provisional tomada de la matriz — verificar] Se estabecen como obligaciones: 1 Contratar a una empresa habilitada a fin de realizar la limpieza de los tanques de agua, en forma trimestral. 2 Requerir la entrega del Certificado de Limpieza y Desinfección de Tanques de Agua Potable (CLDTAP)\nLa Resolucion 452/18 ha derogado la Disposicion 710-14 que en su articulo 1 establecida: la obligatoriedad para consorcistas, representantes y/o administradores del Consorcio de Propiedad Horizontal, establecimientos públicos y privados, de contar con el Certificado de Desinfección y Desinfestación (CEDyT) en forma mensual,', NULL, 1, 'Manual', NOW());
SET @nc52 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc52, 5);
-- resolucion conjunta 35/2015 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(6, 18, '35', '2015', NULL, '[Síntesis provisional tomada de la matriz — verificar] Mediante estas normas se establece todo el sistema de Regulacion para Sistemas contra Incendios. Entre otras cosas se dispone:\n-Aprobación de la incorporación de códigos de respuesta rápida "QR" en las tarjetas identificatorias de extintores (matafuegos),  Verificar que los mismos poseen las tarjetas con su correspondiente codigo\n-Se establece  el procedimiento para el mantenimiento de las Instalaciones Fijas Contra Incendios, los lineamientos para el desarrollo de dichas tareas, y establecer la obligatoriedad del uso del Libro Digital de Inspección.\n- Se Establéce como plazo de vencimiento el 31 de Marzo de cada año, para el pago de la tasa referida en la Ley Tarifaria vigente, en relación al servicio de registro de mantenimiento de instalaciones fijas contra incendio.\n- Creación del Sistema de Autoprotección. Planes de Evacuación y Simulacro. Control de Riesgos. Creaci{on del Registro de Profesionales para la elaboración y puesta a prueba de los Sistemas de Autoprotección, en el que se inscribirán los sujetos que elaboren y presenten ante la Autoridad de Aplicación, dichos sistemas.\n-Clasificación de Edificios, Establecimientos y Predios según Criterios de Riesgo\n-Creacion del Registro de Fabricantes, Reparadores y Recargadores de Extintores (matafuegos) y equipos contra incendios.\n-Las instalaciones fijas contra incendio (IFCI) deben ser fabricadas, reparadas, instaladas y mantenidas por personas físicas y/o jurídicas inscriptas en el "Registro de Fabricantes, Reparadores e Instaladores de Instalaciones Fijas contra Incendios"\n-Establece que todas las actuaciones que se hayan iniciado solicitando la aprobación de un Plan de Evacuación y Simulacro en los términos de la Ley 1346, en el período comprendido entre los años 2007 y mediados de 2013, al  momento de su vencimiento anual, si estuvieses circulando en formato papel, deberá iniciarse nuevamente en formato digital, como expediente electrónico.', NULL, 1, 'Manual', NOW());
SET @nc53 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc53, 18);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc53, 67);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc53, 69);
-- disposicion 1772/2015 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(8, 18, '1772', '2015', NULL, '[Síntesis provisional tomada de la matriz — verificar] Mediante estas normas se establece todo el sistema de Regulacion para Sistemas contra Incendios. Entre otras cosas se dispone:\n-Aprobación de la incorporación de códigos de respuesta rápida "QR" en las tarjetas identificatorias de extintores (matafuegos),  Verificar que los mismos poseen las tarjetas con su correspondiente codigo\n-Se establece  el procedimiento para el mantenimiento de las Instalaciones Fijas Contra Incendios, los lineamientos para el desarrollo de dichas tareas, y establecer la obligatoriedad del uso del Libro Digital de Inspección.\n- Se Establéce como plazo de vencimiento el 31 de Marzo de cada año, para el pago de la tasa referida en la Ley Tarifaria vigente, en relación al servicio de registro de mantenimiento de instalaciones fijas contra incendio.\n- Creación del Sistema de Autoprotección. Planes de Evacuación y Simulacro. Control de Riesgos. Creaci{on del Registro de Profesionales para la elaboración y puesta a prueba de los Sistemas de Autoprotección, en el que se inscribirán los sujetos que elaboren y presenten ante la Autoridad de Aplicación, dichos sistemas.\n-Clasificación de Edificios, Establecimientos y Predios según Criterios de Riesgo\n-Creacion del Registro de Fabricantes, Reparadores y Recargadores de Extintores (matafuegos) y equipos contra incendios.\n-Las instalaciones fijas contra incendio (IFCI) deben ser fabricadas, reparadas, instaladas y mantenidas por personas físicas y/o jurídicas inscriptas en el "Registro de Fabricantes, Reparadores e Instaladores de Instalaciones Fijas contra Incendios"\n-Establece que todas las actuaciones que se hayan iniciado solicitando la aprobación de un Plan de Evacuación y Simulacro en los términos de la Ley 1346, en el período comprendido entre los años 2007 y mediados de 2013, al  momento de su vencimiento anual, si estuvieses circulando en formato papel, deberá iniciarse nuevamente en formato digital, como expediente electrónico.', NULL, 1, 'Manual', NOW());
SET @nc54 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc54, 18);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc54, 67);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc54, 69);
-- disposicion 8806/2015 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(8, 18, '8806', '2015', NULL, '[Síntesis provisional tomada de la matriz — verificar] Mediante estas normas se establece todo el sistema de Regulacion para Sistemas contra Incendios. Entre otras cosas se dispone:\n-Aprobación de la incorporación de códigos de respuesta rápida "QR" en las tarjetas identificatorias de extintores (matafuegos),  Verificar que los mismos poseen las tarjetas con su correspondiente codigo\n-Se establece  el procedimiento para el mantenimiento de las Instalaciones Fijas Contra Incendios, los lineamientos para el desarrollo de dichas tareas, y establecer la obligatoriedad del uso del Libro Digital de Inspección.\n- Se Establéce como plazo de vencimiento el 31 de Marzo de cada año, para el pago de la tasa referida en la Ley Tarifaria vigente, en relación al servicio de registro de mantenimiento de instalaciones fijas contra incendio.\n- Creación del Sistema de Autoprotección. Planes de Evacuación y Simulacro. Control de Riesgos. Creaci{on del Registro de Profesionales para la elaboración y puesta a prueba de los Sistemas de Autoprotección, en el que se inscribirán los sujetos que elaboren y presenten ante la Autoridad de Aplicación, dichos sistemas.\n-Clasificación de Edificios, Establecimientos y Predios según Criterios de Riesgo\n-Creacion del Registro de Fabricantes, Reparadores y Recargadores de Extintores (matafuegos) y equipos contra incendios.\n-Las instalaciones fijas contra incendio (IFCI) deben ser fabricadas, reparadas, instaladas y mantenidas por personas físicas y/o jurídicas inscriptas en el "Registro de Fabricantes, Reparadores e Instaladores de Instalaciones Fijas contra Incendios"\n-Establece que todas las actuaciones que se hayan iniciado solicitando la aprobación de un Plan de Evacuación y Simulacro en los términos de la Ley 1346, en el período comprendido entre los años 2007 y mediados de 2013, al  momento de su vencimiento anual, si estuvieses circulando en formato papel, deberá iniciarse nuevamente en formato digital, como expediente electrónico.', NULL, 1, 'Manual', NOW());
SET @nc55 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc55, 18);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc55, 67);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc55, 69);
-- disposicion 35/2016 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(8, 18, '35', '2016', NULL, '[Síntesis provisional tomada de la matriz — verificar] Mediante estas normas se establece todo el sistema de Regulacion para Sistemas contra Incendios. Entre otras cosas se dispone:\n-Aprobación de la incorporación de códigos de respuesta rápida "QR" en las tarjetas identificatorias de extintores (matafuegos),  Verificar que los mismos poseen las tarjetas con su correspondiente codigo\n-Se establece  el procedimiento para el mantenimiento de las Instalaciones Fijas Contra Incendios, los lineamientos para el desarrollo de dichas tareas, y establecer la obligatoriedad del uso del Libro Digital de Inspección.\n- Se Establéce como plazo de vencimiento el 31 de Marzo de cada año, para el pago de la tasa referida en la Ley Tarifaria vigente, en relación al servicio de registro de mantenimiento de instalaciones fijas contra incendio.\n- Creación del Sistema de Autoprotección. Planes de Evacuación y Simulacro. Control de Riesgos. Creaci{on del Registro de Profesionales para la elaboración y puesta a prueba de los Sistemas de Autoprotección, en el que se inscribirán los sujetos que elaboren y presenten ante la Autoridad de Aplicación, dichos sistemas.\n-Clasificación de Edificios, Establecimientos y Predios según Criterios de Riesgo\n-Creacion del Registro de Fabricantes, Reparadores y Recargadores de Extintores (matafuegos) y equipos contra incendios.\n-Las instalaciones fijas contra incendio (IFCI) deben ser fabricadas, reparadas, instaladas y mantenidas por personas físicas y/o jurídicas inscriptas en el "Registro de Fabricantes, Reparadores e Instaladores de Instalaciones Fijas contra Incendios"\n-Establece que todas las actuaciones que se hayan iniciado solicitando la aprobación de un Plan de Evacuación y Simulacro en los términos de la Ley 1346, en el período comprendido entre los años 2007 y mediados de 2013, al  momento de su vencimiento anual, si estuvieses circulando en formato papel, deberá iniciarse nuevamente en formato digital, como expediente electrónico.', NULL, 1, 'Manual', NOW());
SET @nc56 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc56, 18);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc56, 67);
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc56, 69);
-- resolucion conjunta 326/2013 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(6, 18, '326', '2013', NULL, '[Síntesis provisional tomada de la matriz — verificar] Energía', NULL, 1, 'Manual', NOW());
SET @nc57 := LAST_INSERT_ID();
INSERT INTO `categoria_norma` (`id_norma`,`id_categoria`) VALUES (@nc57, 50);
-- disposicion 1/2023 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(8, 18, '1', '2023', NULL, '[Síntesis provisional tomada de la matriz — verificar] PROGRAMA DE SEGURIDAD PARA OBRAS DE CONSTRUCCIÓN', NULL, 1, 'Manual', NOW());
SET @nc58 := LAST_INSERT_ID();
-- decreto 711/2021 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '711', '2021', NULL, '[Síntesis provisional tomada de la matriz — verificar] PROGRAMAS DE FORMACIÓN, EMPLEO E INTERMEDIACIÓN LABORAL', NULL, 1, 'Manual', NOW());
SET @nc59 := LAST_INSERT_ID();
-- decreto 669/2019 — Síntesis provisional del Excel; emisor/URL a confirmar.
INSERT INTO `norma` (`id_tipo_norma`,`id_emisor_norma`,`numero`,`anio`,`fecha_publicacion`,`sintesis`,`url_norma`,`id_estado_norma`,`origen_carga`,`fecha_actualizacion`) VALUES
(2, 338, '669', '2019', NULL, '[Síntesis provisional tomada de la matriz — verificar] Riesgos de Trabajo', NULL, 1, 'Manual', NOW());
SET @nc60 := LAST_INSERT_ID();

-- vínculos ítem<->norma (guard anti-duplicado)
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc31);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc24);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc25);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc26);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc27);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc32);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc28);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc29);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc30);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2789, @nc33);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2789, @nc34);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2791, @nc35);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2793, @nc36);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2793, @nc37);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2795, @nc38);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2796, @nc39);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2798, @nc40);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2816, @nc18);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2816, @nc41);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2819, @nc42);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2821, @nc19);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2821, @nc20);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2821, @nc43);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2822, @nc17);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2828, @nc44);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2829, @nc45);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2830, @nc46);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2831, @nc47);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2831, @nc48);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2831, @nc49);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2832, @nc50);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2832, @nc51);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2832, @nc52);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2833, @nc53);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2833, @nc54);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2833, @nc55);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2833, @nc56);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2833, @nc21);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2834, @nc52);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2834, @nc57);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2877, 2442);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2885, @nc21);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2917, @nc23);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2917, @nc22);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2936, @nc59);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2976, @nc60);
COMMIT;