<?php
class Rol {
    private $conn;
    private $table_name = "rol";

    public $id_rol;
    public $descripcion;
    public $vigente;

    public function __construct($db) {
        $this->conn = $db;
    }

    // Método para leer todos los roles
    public function leer() {
        $query = "SELECT id_rol, descripcion, vigente 
                  FROM " . $this->table_name . " 
                  ORDER BY descripcion ASC";

        $stmt = $this->conn->prepare($query);
        $stmt->execute();

        return $stmt;
    }
}