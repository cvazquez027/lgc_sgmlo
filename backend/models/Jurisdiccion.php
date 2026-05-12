<?php
class Jurisdiccion {
    private $conn;
    private $table_name = "jurisdiccion";

    public function __construct($db) { $this->conn = $db; }

    public function leer() {
        $query = "SELECT id_jurisdiccion, descripcion FROM " . $this->table_name . " ORDER BY descripcion ASC";
        $stmt = $this->conn->prepare($query);
        $stmt->execute();
        return $stmt;
    }
}