<?php
class Usuario {
    private $conn;
    private $table_name = "usuario";

    public $id_usuario;
    public $nombre;
    public $apellido;
    public $email;
    public $password;
    public $id_rol;
    public $vigente;

    public function __construct($db) {
        $this->conn = $db;
    }

    public function obtenerPorEmail() {
        $query = "SELECT 
                    u.id_usuario, 
                    u.nombre, 
                    u.apellido, 
                    u.email, 
                    u.password_hash, 
                    u.vigente, 
                    ur.id_rol
                  FROM " . $this->table_name . " u
                  LEFT JOIN usuario_rol ur ON u.id_usuario = ur.id_usuario
                  WHERE u.email = ? 
                  LIMIT 0,1";

        $stmt = $this->conn->prepare($query);
        $this->email = htmlspecialchars(strip_tags($this->email));
        $stmt->bindParam(1, $this->email);
        $stmt->execute();
        return $stmt;
    }

    public function leerTodos() {
        $query = "SELECT 
                    u.id_usuario, 
                    u.nombre, 
                    u.apellido, 
                    u.email, 
                    u.ultimo_login, 
                    GROUP_CONCAT(c.razon_social SEPARATOR ' | ') as razon_social,
                    GROUP_CONCAT(uc.id_cliente SEPARATOR ',') as id_clientes,
                    u.vigente,
                    r.descripcion as rol_nombre
                  FROM " . $this->table_name . " u
                  LEFT JOIN usuario_rol ur ON u.id_usuario = ur.id_usuario
                  LEFT JOIN rol r ON ur.id_rol = r.id_rol
                  LEFT JOIN usuario_cliente uc ON u.id_usuario = uc.id_usuario
                  LEFT JOIN cliente c ON uc.id_cliente = c.id_cliente
                  GROUP BY u.id_usuario, u.nombre, u.apellido, u.email, u.ultimo_login, u.vigente, r.descripcion
                  ORDER BY u.id_usuario DESC";

        $stmt = $this->conn->prepare($query);
        $stmt->execute();
        return $stmt;
    }
}