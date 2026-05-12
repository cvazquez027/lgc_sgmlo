<?php
class Cliente {
    private $conn;
    private $table_name = "cliente";

    // Propiedades públicas que mapean las columnas de la tabla
    public $id_cliente;
    public $cuit;
    public $razon_social;
    public $nombre_fantasia;
    public $logo_path; // <-- NUEVO: Agregamos la propiedad para el logo
    public $vigente;

    public function __construct($db) { 
        $this->conn = $db; 
    }

    public function leer() {
        // Obtenemos todos los datos, incluido el logo_path automáticamente por el *
        $query = "SELECT * FROM " . $this->table_name . " ORDER BY razon_social ASC";
        $stmt = $this->conn->prepare($query);
        $stmt->execute();
        return $stmt;
    }

    public function guardar() {
        // CIBERSEGURIDAD: Sanitización estricta de las propiedades antes de armar el statement
        // Esto previene Cross-Site Scripting (XSS) si los datos se muestran luego en el frontend
        $this->cuit = htmlspecialchars(strip_tags($this->cuit));
        $this->razon_social = htmlspecialchars(strip_tags($this->razon_social));
        $this->nombre_fantasia = htmlspecialchars(strip_tags($this->nombre_fantasia));
        $this->logo_path = $this->logo_path ? htmlspecialchars(strip_tags($this->logo_path)) : null;
        $this->vigente = htmlspecialchars(strip_tags($this->vigente));

        if (!empty($this->id_cliente)) {
            // MODO EDICIÓN (UPDATE)
            // Agregamos logo_path=:logo a la consulta
            $query = "UPDATE " . $this->table_name . " 
                      SET cuit=:cuit, razon_social=:rs, nombre_fantasia=:nf, logo_path=:logo, vigente=:v 
                      WHERE id_cliente=:id";
            
            $stmt = $this->conn->prepare($query);
            
            // Sanitizamos y vinculamos el ID
            $this->id_cliente = htmlspecialchars(strip_tags($this->id_cliente));
            $stmt->bindParam(':id', $this->id_cliente);
        } else {
            // MODO CREACIÓN (INSERT)
            // Agregamos logo_path a las columnas y :logo a los valores
            $query = "INSERT INTO " . $this->table_name . " 
                        (cuit, razon_social, nombre_fantasia, logo_path, vigente) 
                      VALUES 
                        (:cuit, :rs, :nf, :logo, :v)";
            
            $stmt = $this->conn->prepare($query);
        }
        
        // Vinculamos el resto de los parámetros de forma segura
        $stmt->bindParam(':cuit', $this->cuit);
        $stmt->bindParam(':rs', $this->razon_social);
        $stmt->bindParam(':nf', $this->nombre_fantasia);
        $stmt->bindParam(':logo', $this->logo_path); // <-- NUEVO: Vinculamos la ruta del logo
        $stmt->bindParam(':v', $this->vigente);
        
        // Ejecutamos la transacción
        if($stmt->execute()) {
            return true;
        }
        
        // Manejo de errores silencioso en producción (puedes hacer log del error aquí si falla)
        return false;
    }
}
?>