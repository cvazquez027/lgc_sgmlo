DELIMITER $$

CREATE TRIGGER trg_categoria_ai AFTER INSERT ON categoria FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('categoria', 'INSERT', NEW.id_categoria, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_categoria', NEW.id_categoria,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_categoria_au AFTER UPDATE ON categoria FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('categoria', 'UPDATE', NEW.id_categoria, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_categoria', NEW.id_categoria,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_categoria_ad AFTER DELETE ON categoria FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('categoria', 'DELETE', OLD.id_categoria, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'id_categoria', OLD.id_categoria,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_categoria_norma_ai AFTER INSERT ON categoria_norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('categoria_norma', 'INSERT', NEW.id_categoria_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_categoria', NEW.id_categoria,'id_categoria_norma', NEW.id_categoria_norma,'id_norma', NEW.id_norma));
END$$

CREATE TRIGGER trg_categoria_norma_au AFTER UPDATE ON categoria_norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('categoria_norma', 'UPDATE', NEW.id_categoria_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_categoria', NEW.id_categoria,'id_categoria_norma', NEW.id_categoria_norma,'id_norma', NEW.id_norma));
END$$

CREATE TRIGGER trg_categoria_norma_ad AFTER DELETE ON categoria_norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('categoria_norma', 'DELETE', OLD.id_categoria_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_categoria', OLD.id_categoria,'id_categoria_norma', OLD.id_categoria_norma,'id_norma', OLD.id_norma));
END$$

CREATE TRIGGER trg_categoria_norma_bo_ai AFTER INSERT ON categoria_norma_bo FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('categoria_norma_bo', 'INSERT', NEW.id_categoria_norma_bo, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_categoria', NEW.id_categoria,'id_categoria_norma_bo', NEW.id_categoria_norma_bo,'id_norma_bo', NEW.id_norma_bo));
END$$

CREATE TRIGGER trg_categoria_norma_bo_au AFTER UPDATE ON categoria_norma_bo FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('categoria_norma_bo', 'UPDATE', NEW.id_categoria_norma_bo, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_categoria', NEW.id_categoria,'id_categoria_norma_bo', NEW.id_categoria_norma_bo,'id_norma_bo', NEW.id_norma_bo));
END$$

CREATE TRIGGER trg_categoria_norma_bo_ad AFTER DELETE ON categoria_norma_bo FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('categoria_norma_bo', 'DELETE', OLD.id_categoria_norma_bo, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_categoria', OLD.id_categoria,'id_categoria_norma_bo', OLD.id_categoria_norma_bo,'id_norma_bo', OLD.id_norma_bo));
END$$

CREATE TRIGGER trg_cliente_ai AFTER INSERT ON cliente FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('cliente', 'INSERT', NEW.id_cliente, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('cuit', NEW.cuit,'id_cliente', NEW.id_cliente,'nombre_fantasia', NEW.nombre_fantasia,'razon_social', NEW.razon_social,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_cliente_au AFTER UPDATE ON cliente FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('cliente', 'UPDATE', NEW.id_cliente, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('cuit', NEW.cuit,'id_cliente', NEW.id_cliente,'nombre_fantasia', NEW.nombre_fantasia,'razon_social', NEW.razon_social,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_cliente_ad AFTER DELETE ON cliente FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('cliente', 'DELETE', OLD.id_cliente, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('cuit', OLD.cuit,'id_cliente', OLD.id_cliente,'nombre_fantasia', OLD.nombre_fantasia,'razon_social', OLD.razon_social,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_cliente_establecimiento_ai AFTER INSERT ON cliente_establecimiento FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('cliente_establecimiento', 'INSERT', NEW.id_cliente_establecimiento, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_cliente', NEW.id_cliente,'id_cliente_establecimiento', NEW.id_cliente_establecimiento,'id_jurisdiccion', NEW.id_jurisdiccion,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_cliente_establecimiento_au AFTER UPDATE ON cliente_establecimiento FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('cliente_establecimiento', 'UPDATE', NEW.id_cliente_establecimiento, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_cliente', NEW.id_cliente,'id_cliente_establecimiento', NEW.id_cliente_establecimiento,'id_jurisdiccion', NEW.id_jurisdiccion,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_cliente_establecimiento_ad AFTER DELETE ON cliente_establecimiento FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('cliente_establecimiento', 'DELETE', OLD.id_cliente_establecimiento, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'id_cliente', OLD.id_cliente,'id_cliente_establecimiento', OLD.id_cliente_establecimiento,'id_jurisdiccion', OLD.id_jurisdiccion,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_configuracion_ai AFTER INSERT ON configuracion FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('configuracion', 'INSERT', NEW.id_configuracion, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('activo', NEW.activo,'descripcion', NEW.descripcion,'fecha_creacion', NEW.fecha_creacion,'fecha_desde', NEW.fecha_desde,'fecha_modificacion', NEW.fecha_modificacion,'id_configuracion', NEW.id_configuracion,'parametro', NEW.parametro,'valor', NEW.valor));
END$$

CREATE TRIGGER trg_configuracion_au AFTER UPDATE ON configuracion FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('configuracion', 'UPDATE', NEW.id_configuracion, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('activo', NEW.activo,'descripcion', NEW.descripcion,'fecha_creacion', NEW.fecha_creacion,'fecha_desde', NEW.fecha_desde,'fecha_modificacion', NEW.fecha_modificacion,'id_configuracion', NEW.id_configuracion,'parametro', NEW.parametro,'valor', NEW.valor));
END$$

CREATE TRIGGER trg_configuracion_ad AFTER DELETE ON configuracion FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('configuracion', 'DELETE', OLD.id_configuracion, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('activo', OLD.activo,'descripcion', OLD.descripcion,'fecha_creacion', OLD.fecha_creacion,'fecha_desde', OLD.fecha_desde,'fecha_modificacion', OLD.fecha_modificacion,'id_configuracion', OLD.id_configuracion,'parametro', OLD.parametro,'valor', OLD.valor));
END$$

CREATE TRIGGER trg_datos_contacto_ai AFTER INSERT ON datos_contacto FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('datos_contacto', 'INSERT', NEW.id_datos_contacto, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'fecha_actualizacion', NEW.fecha_actualizacion,'id_cliente', NEW.id_cliente,'id_cliente_establecimiento', NEW.id_cliente_establecimiento,'id_datos_contacto', NEW.id_datos_contacto,'id_tipo_contacto', NEW.id_tipo_contacto,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_datos_contacto_au AFTER UPDATE ON datos_contacto FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('datos_contacto', 'UPDATE', NEW.id_datos_contacto, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'fecha_actualizacion', NEW.fecha_actualizacion,'id_cliente', NEW.id_cliente,'id_cliente_establecimiento', NEW.id_cliente_establecimiento,'id_datos_contacto', NEW.id_datos_contacto,'id_tipo_contacto', NEW.id_tipo_contacto,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_datos_contacto_ad AFTER DELETE ON datos_contacto FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('datos_contacto', 'DELETE', OLD.id_datos_contacto, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'fecha_actualizacion', OLD.fecha_actualizacion,'id_cliente', OLD.id_cliente,'id_cliente_establecimiento', OLD.id_cliente_establecimiento,'id_datos_contacto', OLD.id_datos_contacto,'id_tipo_contacto', OLD.id_tipo_contacto,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_doc_requisito_matriz_detalle_ai AFTER INSERT ON doc_requisito_matriz_detalle FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('doc_requisito_matriz_detalle', 'INSERT', NEW.id_doc_requisito_matriz_detalle, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_doc_requisito_matriz_detalle', NEW.id_doc_requisito_matriz_detalle,'id_documentacion', NEW.id_documentacion,'id_requisito_matriz_detalle', NEW.id_requisito_matriz_detalle));
END$$

CREATE TRIGGER trg_doc_requisito_matriz_detalle_au AFTER UPDATE ON doc_requisito_matriz_detalle FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('doc_requisito_matriz_detalle', 'UPDATE', NEW.id_doc_requisito_matriz_detalle, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_doc_requisito_matriz_detalle', NEW.id_doc_requisito_matriz_detalle,'id_documentacion', NEW.id_documentacion,'id_requisito_matriz_detalle', NEW.id_requisito_matriz_detalle));
END$$

CREATE TRIGGER trg_doc_requisito_matriz_detalle_ad AFTER DELETE ON doc_requisito_matriz_detalle FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('doc_requisito_matriz_detalle', 'DELETE', OLD.id_doc_requisito_matriz_detalle, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_doc_requisito_matriz_detalle', OLD.id_doc_requisito_matriz_detalle,'id_documentacion', OLD.id_documentacion,'id_requisito_matriz_detalle', OLD.id_requisito_matriz_detalle));
END$$

CREATE TRIGGER trg_documentacion_ai AFTER INSERT ON documentacion FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('documentacion', 'INSERT', NEW.id_documentacion, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('fecha_subida', NEW.fecha_subida,'id_documentacion', NEW.id_documentacion,'id_usuario_subida', NEW.id_usuario_subida,'nombre_original', NEW.nombre_original,'path_archivos', NEW.path_archivos,'peso_bytes', NEW.peso_bytes,'tipo_mime', NEW.tipo_mime,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_documentacion_au AFTER UPDATE ON documentacion FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('documentacion', 'UPDATE', NEW.id_documentacion, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('fecha_subida', NEW.fecha_subida,'id_documentacion', NEW.id_documentacion,'id_usuario_subida', NEW.id_usuario_subida,'nombre_original', NEW.nombre_original,'path_archivos', NEW.path_archivos,'peso_bytes', NEW.peso_bytes,'tipo_mime', NEW.tipo_mime,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_documentacion_ad AFTER DELETE ON documentacion FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('documentacion', 'DELETE', OLD.id_documentacion, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('fecha_subida', OLD.fecha_subida,'id_documentacion', OLD.id_documentacion,'id_usuario_subida', OLD.id_usuario_subida,'nombre_original', OLD.nombre_original,'path_archivos', OLD.path_archivos,'peso_bytes', OLD.peso_bytes,'tipo_mime', OLD.tipo_mime,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_emisor_norma_ai AFTER INSERT ON emisor_norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('emisor_norma', 'INSERT', NEW.id_emisor_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_emisor_norma', NEW.id_emisor_norma,'id_jurisdiccion', NEW.id_jurisdiccion));
END$$

CREATE TRIGGER trg_emisor_norma_au AFTER UPDATE ON emisor_norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('emisor_norma', 'UPDATE', NEW.id_emisor_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_emisor_norma', NEW.id_emisor_norma,'id_jurisdiccion', NEW.id_jurisdiccion));
END$$

CREATE TRIGGER trg_emisor_norma_ad AFTER DELETE ON emisor_norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('emisor_norma', 'DELETE', OLD.id_emisor_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'id_emisor_norma', OLD.id_emisor_norma,'id_jurisdiccion', OLD.id_jurisdiccion));
END$$

CREATE TRIGGER trg_estado_cumplimiento_ai AFTER INSERT ON estado_cumplimiento FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('estado_cumplimiento', 'INSERT', NEW.id_estado_cumplimiento, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('color_hex', NEW.color_hex,'descripcion', NEW.descripcion,'id_estado_cumplimiento', NEW.id_estado_cumplimiento,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_estado_cumplimiento_au AFTER UPDATE ON estado_cumplimiento FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('estado_cumplimiento', 'UPDATE', NEW.id_estado_cumplimiento, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('color_hex', NEW.color_hex,'descripcion', NEW.descripcion,'id_estado_cumplimiento', NEW.id_estado_cumplimiento,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_estado_cumplimiento_ad AFTER DELETE ON estado_cumplimiento FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('estado_cumplimiento', 'DELETE', OLD.id_estado_cumplimiento, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('color_hex', OLD.color_hex,'descripcion', OLD.descripcion,'id_estado_cumplimiento', OLD.id_estado_cumplimiento,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_estado_matriz_ai AFTER INSERT ON estado_matriz FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('estado_matriz', 'INSERT', NEW.id_estado_matriz, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_estado_matriz', NEW.id_estado_matriz,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_estado_matriz_au AFTER UPDATE ON estado_matriz FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('estado_matriz', 'UPDATE', NEW.id_estado_matriz, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_estado_matriz', NEW.id_estado_matriz,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_estado_matriz_ad AFTER DELETE ON estado_matriz FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('estado_matriz', 'DELETE', OLD.id_estado_matriz, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'id_estado_matriz', OLD.id_estado_matriz,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_estado_norma_ai AFTER INSERT ON estado_norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('estado_norma', 'INSERT', NEW.id_estado_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_estado_norma', NEW.id_estado_norma,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_estado_norma_au AFTER UPDATE ON estado_norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('estado_norma', 'UPDATE', NEW.id_estado_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_estado_norma', NEW.id_estado_norma,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_estado_norma_ad AFTER DELETE ON estado_norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('estado_norma', 'DELETE', OLD.id_estado_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'id_estado_norma', OLD.id_estado_norma,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_jurisdiccion_ai AFTER INSERT ON jurisdiccion FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('jurisdiccion', 'INSERT', NEW.id_jurisdiccion, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_jurisdiccion', NEW.id_jurisdiccion,'id_jurisdiccion_sup', NEW.id_jurisdiccion_sup,'id_nivel_jurisdiccion', NEW.id_nivel_jurisdiccion));
END$$

CREATE TRIGGER trg_jurisdiccion_au AFTER UPDATE ON jurisdiccion FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('jurisdiccion', 'UPDATE', NEW.id_jurisdiccion, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_jurisdiccion', NEW.id_jurisdiccion,'id_jurisdiccion_sup', NEW.id_jurisdiccion_sup,'id_nivel_jurisdiccion', NEW.id_nivel_jurisdiccion));
END$$

CREATE TRIGGER trg_jurisdiccion_ad AFTER DELETE ON jurisdiccion FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('jurisdiccion', 'DELETE', OLD.id_jurisdiccion, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'id_jurisdiccion', OLD.id_jurisdiccion,'id_jurisdiccion_sup', OLD.id_jurisdiccion_sup,'id_nivel_jurisdiccion', OLD.id_nivel_jurisdiccion));
END$$

CREATE TRIGGER trg_matriz_ai AFTER INSERT ON matriz FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('matriz', 'INSERT', NEW.id_matriz, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('fecha_desde', NEW.fecha_desde,'id_cliente_establecimiento', NEW.id_cliente_establecimiento,'id_estado_matriz', NEW.id_estado_matriz,'id_matriz', NEW.id_matriz,'version', NEW.version,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_matriz_au AFTER UPDATE ON matriz FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('matriz', 'UPDATE', NEW.id_matriz, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('fecha_desde', NEW.fecha_desde,'id_cliente_establecimiento', NEW.id_cliente_establecimiento,'id_estado_matriz', NEW.id_estado_matriz,'id_matriz', NEW.id_matriz,'version', NEW.version,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_matriz_ad AFTER DELETE ON matriz FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('matriz', 'DELETE', OLD.id_matriz, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('fecha_desde', OLD.fecha_desde,'id_cliente_establecimiento', OLD.id_cliente_establecimiento,'id_estado_matriz', OLD.id_estado_matriz,'id_matriz', OLD.id_matriz,'version', OLD.version,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_matriz_detalle_ai AFTER INSERT ON matriz_detalle FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('matriz_detalle', 'INSERT', NEW.id_matriz_detalle, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_matriz', NEW.id_matriz,'id_matriz_detalle', NEW.id_matriz_detalle,'id_norma', NEW.id_norma,'id_requisito', NEW.id_requisito));
END$$

CREATE TRIGGER trg_matriz_detalle_au AFTER UPDATE ON matriz_detalle FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('matriz_detalle', 'UPDATE', NEW.id_matriz_detalle, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_matriz', NEW.id_matriz,'id_matriz_detalle', NEW.id_matriz_detalle,'id_norma', NEW.id_norma,'id_requisito', NEW.id_requisito));
END$$

CREATE TRIGGER trg_matriz_detalle_ad AFTER DELETE ON matriz_detalle FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('matriz_detalle', 'DELETE', OLD.id_matriz_detalle, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_matriz', OLD.id_matriz,'id_matriz_detalle', OLD.id_matriz_detalle,'id_norma', OLD.id_norma,'id_requisito', OLD.id_requisito));
END$$

CREATE TRIGGER trg_nivel_jurisdiccion_ai AFTER INSERT ON nivel_jurisdiccion FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('nivel_jurisdiccion', 'INSERT', NEW.id_nivel_jurisdiccion, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_nivel_jurisdiccion', NEW.id_nivel_jurisdiccion,'nivel', NEW.nivel,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_nivel_jurisdiccion_au AFTER UPDATE ON nivel_jurisdiccion FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('nivel_jurisdiccion', 'UPDATE', NEW.id_nivel_jurisdiccion, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_nivel_jurisdiccion', NEW.id_nivel_jurisdiccion,'nivel', NEW.nivel,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_nivel_jurisdiccion_ad AFTER DELETE ON nivel_jurisdiccion FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('nivel_jurisdiccion', 'DELETE', OLD.id_nivel_jurisdiccion, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'id_nivel_jurisdiccion', OLD.id_nivel_jurisdiccion,'nivel', OLD.nivel,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_norma_ai AFTER INSERT ON norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('norma', 'INSERT', NEW.id_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('anio', NEW.anio,'fecha_publicacion', NEW.fecha_publicacion,'fecha_ultimo_scraping', NEW.fecha_ultimo_scraping,'id_emisor_norma', NEW.id_emisor_norma,'id_estado_norma', NEW.id_estado_norma,'id_norma', NEW.id_norma,'id_tipo_norma', NEW.id_tipo_norma,'numero', NEW.numero,'origen_carga', NEW.origen_carga,'sintesis', NEW.sintesis,'url_norma', NEW.url_norma));
END$$

CREATE TRIGGER trg_norma_au AFTER UPDATE ON norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('norma', 'UPDATE', NEW.id_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('anio', NEW.anio,'fecha_publicacion', NEW.fecha_publicacion,'fecha_ultimo_scraping', NEW.fecha_ultimo_scraping,'id_emisor_norma', NEW.id_emisor_norma,'id_estado_norma', NEW.id_estado_norma,'id_norma', NEW.id_norma,'id_tipo_norma', NEW.id_tipo_norma,'numero', NEW.numero,'origen_carga', NEW.origen_carga,'sintesis', NEW.sintesis,'url_norma', NEW.url_norma));
END$$

CREATE TRIGGER trg_norma_ad AFTER DELETE ON norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('norma', 'DELETE', OLD.id_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('anio', OLD.anio,'fecha_publicacion', OLD.fecha_publicacion,'fecha_ultimo_scraping', OLD.fecha_ultimo_scraping,'id_emisor_norma', OLD.id_emisor_norma,'id_estado_norma', OLD.id_estado_norma,'id_norma', OLD.id_norma,'id_tipo_norma', OLD.id_tipo_norma,'numero', OLD.numero,'origen_carga', OLD.origen_carga,'sintesis', OLD.sintesis,'url_norma', OLD.url_norma));
END$$

CREATE TRIGGER trg_norma_bo_ai AFTER INSERT ON norma_bo FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('norma_bo', 'INSERT', NEW.id_norma_bo, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('anio', NEW.anio,'fecha_publicacion', NEW.fecha_publicacion,'fecha_ultimo_scraping', NEW.fecha_ultimo_scraping,'id_emisor_norma', NEW.id_emisor_norma,'id_estado_norma', NEW.id_estado_norma,'id_norma_bo', NEW.id_norma_bo,'id_tipo_norma', NEW.id_tipo_norma,'numero', NEW.numero,'origen_carga', NEW.origen_carga,'sintesis', NEW.sintesis,'url_norma', NEW.url_norma));
END$$

CREATE TRIGGER trg_norma_bo_au AFTER UPDATE ON norma_bo FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('norma_bo', 'UPDATE', NEW.id_norma_bo, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('anio', NEW.anio,'fecha_publicacion', NEW.fecha_publicacion,'fecha_ultimo_scraping', NEW.fecha_ultimo_scraping,'id_emisor_norma', NEW.id_emisor_norma,'id_estado_norma', NEW.id_estado_norma,'id_norma_bo', NEW.id_norma_bo,'id_tipo_norma', NEW.id_tipo_norma,'numero', NEW.numero,'origen_carga', NEW.origen_carga,'sintesis', NEW.sintesis,'url_norma', NEW.url_norma));
END$$

CREATE TRIGGER trg_norma_bo_ad AFTER DELETE ON norma_bo FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('norma_bo', 'DELETE', OLD.id_norma_bo, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('anio', OLD.anio,'fecha_publicacion', OLD.fecha_publicacion,'fecha_ultimo_scraping', OLD.fecha_ultimo_scraping,'id_emisor_norma', OLD.id_emisor_norma,'id_estado_norma', OLD.id_estado_norma,'id_norma_bo', OLD.id_norma_bo,'id_tipo_norma', OLD.id_tipo_norma,'numero', OLD.numero,'origen_carga', OLD.origen_carga,'sintesis', OLD.sintesis,'url_norma', OLD.url_norma));
END$$

CREATE TRIGGER trg_permiso_ai AFTER INSERT ON permiso FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('permiso', 'INSERT', NEW.id_permiso, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_permiso', NEW.id_permiso,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_permiso_au AFTER UPDATE ON permiso FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('permiso', 'UPDATE', NEW.id_permiso, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_permiso', NEW.id_permiso,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_permiso_ad AFTER DELETE ON permiso FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('permiso', 'DELETE', OLD.id_permiso, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'id_permiso', OLD.id_permiso,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_requisito_ai AFTER INSERT ON requisito FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('requisito', 'INSERT', NEW.id_requisito, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('articulos_aplicables', NEW.articulos_aplicables,'id_norma', NEW.id_norma,'id_requisito', NEW.id_requisito,'resumen_legal', NEW.resumen_legal));
END$$

CREATE TRIGGER trg_requisito_au AFTER UPDATE ON requisito FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('requisito', 'UPDATE', NEW.id_requisito, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('articulos_aplicables', NEW.articulos_aplicables,'id_norma', NEW.id_norma,'id_requisito', NEW.id_requisito,'resumen_legal', NEW.resumen_legal));
END$$

CREATE TRIGGER trg_requisito_ad AFTER DELETE ON requisito FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('requisito', 'DELETE', OLD.id_requisito, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('articulos_aplicables', OLD.articulos_aplicables,'id_norma', OLD.id_norma,'id_requisito', OLD.id_requisito,'resumen_legal', OLD.resumen_legal));
END$$

CREATE TRIGGER trg_requisito_matriz_detalle_ai AFTER INSERT ON requisito_matriz_detalle FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('requisito_matriz_detalle', 'INSERT', NEW.id_requisito_matriz_detalle, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('detalle_tema', NEW.detalle_tema,'evidencia_cumplimiento', NEW.evidencia_cumplimiento,'fecha_cumplimiento', NEW.fecha_cumplimiento,'id_estado_cumplimiento', NEW.id_estado_cumplimiento,'id_matriz_detalle', NEW.id_matriz_detalle,'id_requisito_matriz_detalle', NEW.id_requisito_matriz_detalle,'id_tipo_modalidad', NEW.id_tipo_modalidad,'interpretacion_aplicacion', NEW.interpretacion_aplicacion,'obs_estado_cumplimiento', NEW.obs_estado_cumplimiento,'obs_modalidad', NEW.obs_modalidad,'obs_plazo', NEW.obs_plazo,'proceso_aplica', NEW.proceso_aplica,'responsable_cumplimiento', NEW.responsable_cumplimiento,'vencimiento_plazo', NEW.vencimiento_plazo,'verificacion_cumplimiento', NEW.verificacion_cumplimiento));
END$$

CREATE TRIGGER trg_requisito_matriz_detalle_au AFTER UPDATE ON requisito_matriz_detalle FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('requisito_matriz_detalle', 'UPDATE', NEW.id_requisito_matriz_detalle, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('detalle_tema', NEW.detalle_tema,'evidencia_cumplimiento', NEW.evidencia_cumplimiento,'fecha_cumplimiento', NEW.fecha_cumplimiento,'id_estado_cumplimiento', NEW.id_estado_cumplimiento,'id_matriz_detalle', NEW.id_matriz_detalle,'id_requisito_matriz_detalle', NEW.id_requisito_matriz_detalle,'id_tipo_modalidad', NEW.id_tipo_modalidad,'interpretacion_aplicacion', NEW.interpretacion_aplicacion,'obs_estado_cumplimiento', NEW.obs_estado_cumplimiento,'obs_modalidad', NEW.obs_modalidad,'obs_plazo', NEW.obs_plazo,'proceso_aplica', NEW.proceso_aplica,'responsable_cumplimiento', NEW.responsable_cumplimiento,'vencimiento_plazo', NEW.vencimiento_plazo,'verificacion_cumplimiento', NEW.verificacion_cumplimiento));
END$$

CREATE TRIGGER trg_requisito_matriz_detalle_ad AFTER DELETE ON requisito_matriz_detalle FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('requisito_matriz_detalle', 'DELETE', OLD.id_requisito_matriz_detalle, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('detalle_tema', OLD.detalle_tema,'evidencia_cumplimiento', OLD.evidencia_cumplimiento,'fecha_cumplimiento', OLD.fecha_cumplimiento,'id_estado_cumplimiento', OLD.id_estado_cumplimiento,'id_matriz_detalle', OLD.id_matriz_detalle,'id_requisito_matriz_detalle', OLD.id_requisito_matriz_detalle,'id_tipo_modalidad', OLD.id_tipo_modalidad,'interpretacion_aplicacion', OLD.interpretacion_aplicacion,'obs_estado_cumplimiento', OLD.obs_estado_cumplimiento,'obs_modalidad', OLD.obs_modalidad,'obs_plazo', OLD.obs_plazo,'proceso_aplica', OLD.proceso_aplica,'responsable_cumplimiento', OLD.responsable_cumplimiento,'vencimiento_plazo', OLD.vencimiento_plazo,'verificacion_cumplimiento', OLD.verificacion_cumplimiento));
END$$

CREATE TRIGGER trg_rol_ai AFTER INSERT ON rol FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('rol', 'INSERT', NEW.id_rol, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_rol', NEW.id_rol,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_rol_au AFTER UPDATE ON rol FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('rol', 'UPDATE', NEW.id_rol, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_rol', NEW.id_rol,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_rol_ad AFTER DELETE ON rol FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('rol', 'DELETE', OLD.id_rol, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'id_rol', OLD.id_rol,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_rol_permiso_ai AFTER INSERT ON rol_permiso FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('rol_permiso', 'INSERT', NEW.id_rol_permiso, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_permiso', NEW.id_permiso,'id_rol', NEW.id_rol,'id_rol_permiso', NEW.id_rol_permiso));
END$$

CREATE TRIGGER trg_rol_permiso_au AFTER UPDATE ON rol_permiso FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('rol_permiso', 'UPDATE', NEW.id_rol_permiso, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_permiso', NEW.id_permiso,'id_rol', NEW.id_rol,'id_rol_permiso', NEW.id_rol_permiso));
END$$

CREATE TRIGGER trg_rol_permiso_ad AFTER DELETE ON rol_permiso FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('rol_permiso', 'DELETE', OLD.id_rol_permiso, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_permiso', OLD.id_permiso,'id_rol', OLD.id_rol,'id_rol_permiso', OLD.id_rol_permiso));
END$$

CREATE TRIGGER trg_tipo_contacto_ai AFTER INSERT ON tipo_contacto FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('tipo_contacto', 'INSERT', NEW.id_tipo_contacto, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_tipo_contacto', NEW.id_tipo_contacto,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_tipo_contacto_au AFTER UPDATE ON tipo_contacto FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('tipo_contacto', 'UPDATE', NEW.id_tipo_contacto, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_tipo_contacto', NEW.id_tipo_contacto,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_tipo_contacto_ad AFTER DELETE ON tipo_contacto FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('tipo_contacto', 'DELETE', OLD.id_tipo_contacto, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'id_tipo_contacto', OLD.id_tipo_contacto,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_tipo_modalidad_ai AFTER INSERT ON tipo_modalidad FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('tipo_modalidad', 'INSERT', NEW.id_tipo_modalidad, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_tipo_modalidad', NEW.id_tipo_modalidad));
END$$

CREATE TRIGGER trg_tipo_modalidad_au AFTER UPDATE ON tipo_modalidad FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('tipo_modalidad', 'UPDATE', NEW.id_tipo_modalidad, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_tipo_modalidad', NEW.id_tipo_modalidad));
END$$

CREATE TRIGGER trg_tipo_modalidad_ad AFTER DELETE ON tipo_modalidad FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('tipo_modalidad', 'DELETE', OLD.id_tipo_modalidad, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'id_tipo_modalidad', OLD.id_tipo_modalidad));
END$$

CREATE TRIGGER trg_tipo_norma_ai AFTER INSERT ON tipo_norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('tipo_norma', 'INSERT', NEW.id_tipo_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_tipo_norma', NEW.id_tipo_norma,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_tipo_norma_au AFTER UPDATE ON tipo_norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('tipo_norma', 'UPDATE', NEW.id_tipo_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', NEW.descripcion,'id_tipo_norma', NEW.id_tipo_norma,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_tipo_norma_ad AFTER DELETE ON tipo_norma FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('tipo_norma', 'DELETE', OLD.id_tipo_norma, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('descripcion', OLD.descripcion,'id_tipo_norma', OLD.id_tipo_norma,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_usuario_ai AFTER INSERT ON usuario FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('usuario', 'INSERT', NEW.id_usuario, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('apellido', NEW.apellido,'email', NEW.email,'fecha_alta', NEW.fecha_alta,'fecha_modificacion', NEW.fecha_modificacion,'id_cliente', NEW.id_cliente,'id_usuario', NEW.id_usuario,'intentos_fallidos', NEW.intentos_fallidos,'nombre', NEW.nombre,'password_hash', NEW.password_hash,'ultimo_login', NEW.ultimo_login,'ultimo_login_ip', NEW.ultimo_login_ip,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_usuario_au AFTER UPDATE ON usuario FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('usuario', 'UPDATE', NEW.id_usuario, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('apellido', NEW.apellido,'email', NEW.email,'fecha_alta', NEW.fecha_alta,'fecha_modificacion', NEW.fecha_modificacion,'id_cliente', NEW.id_cliente,'id_usuario', NEW.id_usuario,'intentos_fallidos', NEW.intentos_fallidos,'nombre', NEW.nombre,'password_hash', NEW.password_hash,'ultimo_login', NEW.ultimo_login,'ultimo_login_ip', NEW.ultimo_login_ip,'vigente', NEW.vigente));
END$$

CREATE TRIGGER trg_usuario_ad AFTER DELETE ON usuario FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('usuario', 'DELETE', OLD.id_usuario, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('apellido', OLD.apellido,'email', OLD.email,'fecha_alta', OLD.fecha_alta,'fecha_modificacion', OLD.fecha_modificacion,'id_cliente', OLD.id_cliente,'id_usuario', OLD.id_usuario,'intentos_fallidos', OLD.intentos_fallidos,'nombre', OLD.nombre,'password_hash', OLD.password_hash,'ultimo_login', OLD.ultimo_login,'ultimo_login_ip', OLD.ultimo_login_ip,'vigente', OLD.vigente));
END$$

CREATE TRIGGER trg_usuario_rol_ai AFTER INSERT ON usuario_rol FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('usuario_rol', 'INSERT', NEW.id_usuario_rol, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_rol', NEW.id_rol,'id_usuario', NEW.id_usuario,'id_usuario_rol', NEW.id_usuario_rol));
END$$

CREATE TRIGGER trg_usuario_rol_au AFTER UPDATE ON usuario_rol FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('usuario_rol', 'UPDATE', NEW.id_usuario_rol, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_rol', NEW.id_rol,'id_usuario', NEW.id_usuario,'id_usuario_rol', NEW.id_usuario_rol));
END$$

CREATE TRIGGER trg_usuario_rol_ad AFTER DELETE ON usuario_rol FOR EACH ROW
BEGIN
  INSERT INTO auditoria (tabla_afectada, accion, id_registro, id_usuario, ip_origen, fecha_evento, datos_json)
  VALUES ('usuario_rol', 'DELETE', OLD.id_usuario_rol, IFNULL(@current_user_id, 1), IFNULL(@current_ip, '127.0.0.1'), NOW(), JSON_OBJECT('id_rol', OLD.id_rol,'id_usuario', OLD.id_usuario,'id_usuario_rol', OLD.id_usuario_rol));
END$$

DELIMITER ;