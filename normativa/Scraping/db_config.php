<?php
// Parámetros de conexión
$host = 'localhost';
$db   = 'gestion_lgc';
$user = 'admin';
$pass = 'Emma.Tomi_1725';

// Crear la conexión usando MySQLi
$conn = new mysqli($host, $user, $pass, $db);

// Verificar si hubo un error al conectar
if ($conn->connect_error) {
    die("Error de conexión a MySQL: " . $conn->connect_error);
}

// IMPORTANTE: Setear el charset a utf8mb4 
// Esto asegura que las tildes y las 'ñ' de las leyes se vean perfectas en la web
$conn->set_charset("utf8mb4");
?>