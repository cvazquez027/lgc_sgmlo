<?php
class JwtHandler {
    private $secret;

    public function __construct() {
        // ¡IMPORTANTE! En el futuro pasaremos esto a un archivo .env.
        // Por ahora usamos una clave fuerte harcodeada para el desarrollo.
        $this->secret = "LgC_Sgml0_S3cr3t_K3y_2026!#"; 
    }

    public function generarToken($datosUsuario) {
        // 1. Cabecera (Header): Indica que es un JWT usando el algoritmo HS256
        $header = json_encode(['typ' => 'JWT', 'alg' => 'HS256']);
        
        // 2. Carga útil (Payload): Los datos del usuario y la fecha de expiración
        $payload = json_encode(array_merge($datosUsuario, [
            'iat' => time(), // Fecha de emisión (Issued At)
            'exp' => time() + (60 * 60 * 8) // Expira en 8 horas
        ]));

        // Codificamos en Base64Url (formato seguro para URLs)
        $base64UrlHeader = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($header));
        $base64UrlPayload = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($payload));

        // 3. Firma (Signature): El sello de seguridad que evita que el token sea modificado
        $firma = hash_hmac('sha256', $base64UrlHeader . "." . $base64UrlPayload, $this->secret, true);
        $base64UrlFirma = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($firma));

        // Devolvemos las 3 partes unidas por un punto
        return $base64UrlHeader . "." . $base64UrlPayload . "." . $base64UrlFirma;
    }
}