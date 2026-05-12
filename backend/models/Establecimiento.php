<?php
class Establecimiento {
    private $conn;
    private $table_name = "cliente_establecimiento";

    public function __construct($db) { $this->conn = $db; }

    public function leerPorCliente($id_cliente) {
        $query = "SELECT e.*, j.descripcion as jurisdiccion_nombre 
                  FROM " . $this->table_name . " e
                  LEFT JOIN jurisdiccion j ON e.id_jurisdiccion = j.id_jurisdiccion
                  WHERE e.id_cliente = ? 
                  ORDER BY e.descripcion ASC";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(1, $id_cliente);
        $stmt->execute();
        return $stmt;
    }
}