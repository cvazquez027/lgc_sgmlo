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

    // NUEVO MÉTODO: Para validar el token que llega del frontend
    public function verificar($token) {
        if (empty($token)) {
            return false;
        }

        $partes = explode('.', $token);
        if (count($partes) !== 3) {
            return false; // Token mal formado
        }

        $base64UrlHeader = $partes[0];
        $base64UrlPayload = $partes[1];
        $firmaRecibida = $partes[2];

        // Volvemos a generar la firma con las 2 primeras partes para ver si coincide
        $firmaCalculada = hash_hmac('sha256', $base64UrlHeader . "." . $base64UrlPayload, $this->secret, true);
        $base64UrlFirmaCalculada = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($firmaCalculada));

        // Si la firma coincide, el token es auténtico
        if (hash_equals($base64UrlFirmaCalculada, $firmaRecibida)) {
            // Verificamos si no está expirado
            $payloadDecodificado = json_decode(base64_decode(str_replace(['-', '_'], ['+', '/'], $base64UrlPayload)), true);
            if (isset($payloadDecodificado['exp']) && $payloadDecodificado['exp'] < time()) {
                return false; // Token expirado
            }
            return $payloadDecodificado; // Validado correctamente
        }

        return false; // Firma inválida
    }
}
?>