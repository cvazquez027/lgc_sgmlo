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

-- vínculos ítem<->norma (guard anti-duplicado)
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc24);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc25);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc26);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc27);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc28);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc29);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2788, @nc30);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2816, @nc18);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2821, @nc19);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2821, @nc20);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2822, @nc17);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2833, @nc21);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2877, 2442);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2885, @nc21);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2917, @nc23);
INSERT INTO `item_matriz_norma` (`id_item_matriz`,`id_norma`) VALUES (2917, @nc22);
COMMIT;