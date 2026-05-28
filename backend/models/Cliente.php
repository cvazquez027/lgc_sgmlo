<?php
class Cliente {
    private $conn;
    private $table_name = "cliente";

    public $id_cliente;
    public $cuit;
    public $razon_social;
    public $nombre_fantasia;
    public $logo_path;
    public $vigente;
    public $contactos; // <-- Nuevo: recibirá el array de contactos desde el front

    public function __construct($db) { 
        $this->conn = $db; 
    }

    /**
     * Lee todos los clientes y sus respectivos contactos.
     * Devuelve un array de clientes, cada uno con una propiedad "contactos".
     */
    public function leer() {
        // Primero obtenemos los datos básicos del cliente
        $query = "SELECT * FROM " . $this->table_name . " ORDER BY razon_social ASC";
        $stmt = $this->conn->prepare($query);
        $stmt->execute();
        
        $clientes = [];
        while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
            $row['contactos'] = []; // Inicializamos array de contactos
            $clientes[$row['id_cliente']] = $row;
        }

        if (!empty($clientes)) {
            // Segundo query: obtener todos los contactos de estos clientes
            $ids = implode(',', array_keys($clientes));
            $queryContactos = "SELECT id_cliente, id_tipo_contacto, descripcion 
                               FROM datos_contacto 
                               WHERE id_cliente IN ($ids) AND id_cliente_establecimiento IS NULL";
            $stmtContactos = $this->conn->prepare($queryContactos);
            $stmtContactos->execute();
            while ($contacto = $stmtContactos->fetch(PDO::FETCH_ASSOC)) {
                $idCliente = $contacto['id_cliente'];
                $clientes[$idCliente]['contactos'][] = [
                    'id_tipo_contacto' => $contacto['id_tipo_contacto'],
                    'valor' => $contacto['descripcion']
                ];
            }
        }

        return $clientes; // Retornamos un array asociativo, luego en leer.php lo convertimos en el formato esperado
    }

    /**
     * Guarda (inserta o actualiza) un cliente y sus contactos.
     */
    public function guardar() {
        // Sanitización
        $this->cuit = htmlspecialchars(strip_tags($this->cuit));
        $this->razon_social = htmlspecialchars(strip_tags($this->razon_social));
        $this->nombre_fantasia = htmlspecialchars(strip_tags($this->nombre_fantasia));
        $this->logo_path = $this->logo_path ? htmlspecialchars(strip_tags($this->logo_path)) : null;
        $this->vigente = htmlspecialchars(strip_tags($this->vigente));

        $esNuevo = empty($this->id_cliente);
        $idCliente = null;

        if (!$esNuevo) {
            // MODO EDICIÓN (UPDATE)
            $query = "UPDATE " . $this->table_name . " 
                      SET cuit=:cuit, razon_social=:rs, nombre_fantasia=:nf, logo_path=:logo, vigente=:v 
                      WHERE id_cliente=:id";
            $stmt = $this->conn->prepare($query);
            $this->id_cliente = htmlspecialchars(strip_tags($this->id_cliente));
            $stmt->bindParam(':id', $this->id_cliente);
            $stmt->bindParam(':cuit', $this->cuit);
            $stmt->bindParam(':rs', $this->razon_social);
            $stmt->bindParam(':nf', $this->nombre_fantasia);
            $stmt->bindParam(':logo', $this->logo_path);
            $stmt->bindParam(':v', $this->vigente);
            
            if ($stmt->execute()) {
                $idCliente = $this->id_cliente;
            } else {
                return false;
            }
        } else {
            // MODO CREACIÓN (INSERT)
            $query = "INSERT INTO " . $this->table_name . " 
                        (cuit, razon_social, nombre_fantasia, logo_path, vigente) 
                      VALUES 
                        (:cuit, :rs, :nf, :logo, :v)";
            $stmt = $this->conn->prepare($query);
            $stmt->bindParam(':cuit', $this->cuit);
            $stmt->bindParam(':rs', $this->razon_social);
            $stmt->bindParam(':nf', $this->nombre_fantasia);
            $stmt->bindParam(':logo', $this->logo_path);
            $stmt->bindParam(':v', $this->vigente);
            
            if ($stmt->execute()) {
                $idCliente = $this->conn->lastInsertId();
                $this->id_cliente = $idCliente; // actualizamos la propiedad
            } else {
                return false;
            }
        }

        // --- Gestión de contactos ---
        // Primero eliminamos los contactos actuales de este cliente (si existen)
        if ($this->eliminarContactos($idCliente)) {
            // Luego insertamos los nuevos contactos (si vienen)
            if (!empty($this->contactos) && is_array($this->contactos)) {
                return $this->guardarContactos($idCliente, $this->contactos);
            }
            return true;
        }
        return false;
    }

    /**
     * Elimina todos los contactos de un cliente (solo los que pertenecen al cliente, no a establecimientos)
     */
    private function eliminarContactos($id_cliente) {
        $query = "DELETE FROM datos_contacto WHERE id_cliente = :id_cliente AND id_cliente_establecimiento IS NULL";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':id_cliente', $id_cliente);
        return $stmt->execute();
    }

    /**
     * Inserta un array de contactos para un cliente
     * @param int $id_cliente
     * @param array $contactos Array de objetos con id_tipo_contacto y valor
     */
    private function guardarContactos($id_cliente, $contactos) {
        $query = "INSERT INTO datos_contacto (id_cliente, id_tipo_contacto, descripcion, vigente) 
                  VALUES (:id_cliente, :id_tipo, :descripcion, 1)";
        $stmt = $this->conn->prepare($query);
        
        foreach ($contactos as $contacto) {
            // Validar que tenga los campos necesarios
            if (empty($contacto->id_tipo_contacto) || !isset($contacto->valor)) continue;
            
            $id_tipo = htmlspecialchars(strip_tags($contacto->id_tipo_contacto));
            $descripcion = htmlspecialchars(strip_tags($contacto->valor));
            
            $stmt->bindParam(':id_cliente', $id_cliente);
            $stmt->bindParam(':id_tipo', $id_tipo);
            $stmt->bindParam(':descripcion', $descripcion);
            
            if (!$stmt->execute()) {
                return false;
            }
        }
        return true;
    }
}
?>