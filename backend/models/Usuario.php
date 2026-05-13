<?php
class Usuario {
    private $conn;
    private $table_name = "usuario";

    // Propiedades del objeto
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

    // --- FIX QUIRÚRGICO PARA LOGIN ---
    public function obtenerPorEmail() {
        // Modificamos la consulta para incluir un JOIN con usuario_rol.
        // Esto permite traer el id_rol que Login.php necesita para 
        // generar el token y buscar los permisos.
        $query = "SELECT 
                    u.id_usuario, 
                    u.nombre, 
                    u.apellido, 
                    u.email, 
                    u.password_hash, 
                    u.id_cliente,
                    u.vigente, 
                    ur.id_rol
                  FROM " . $this->table_name . " u
                  LEFT JOIN usuario_rol ur ON u.id_usuario = ur.id_usuario
                  WHERE u.email = ? 
                  LIMIT 0,1";

        $stmt = $this->conn->prepare($query);

        // Sanitización defensiva
        $this->email = htmlspecialchars(strip_tags($this->email));
        $stmt->bindParam(1, $this->email);

        $stmt->execute();
        return $stmt;
    }

    // Método para listar (usado en backend\api\usuarios\leer.php)
    public function leerTodos() {
        $query = "SELECT 
                    u.id_usuario, 
                    u.nombre, 
                    u.apellido, 
                    u.email, 
                    u.ultimo_login, 
                    u.id_cliente,
                    c.razon_social,
                    u.vigente,
                    r.descripcion as rol_nombre
                  FROM " . $this->table_name . " u
                  LEFT JOIN usuario_rol ur ON u.id_usuario = ur.id_usuario
                  LEFT JOIN rol r ON ur.id_rol = r.id_rol
                  LEFT JOIN cliente c ON u.id_cliente = c.id_cliente
                  ORDER BY u.id_usuario DESC";

        $stmt = $this->conn->prepare($query);
        $stmt->execute();
        return $stmt;
    }
}