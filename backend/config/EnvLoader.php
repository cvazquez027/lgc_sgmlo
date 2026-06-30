<?php
class EnvLoader {
    private static $loaded = false;

    public static function load($path) {
        if (self::$loaded) return;

        $file = rtrim($path, '/') . '/.env';
        if (!file_exists($file)) {
            error_log("EnvLoader: .env no encontrado en $file");
            return;
        }

        $lines = file($file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        foreach ($lines as $line) {
            if (strpos(trim($line), '#') === 0) continue;
            if (strpos($line, '=') === false) continue;

            list($name, $value) = explode('=', $line, 2);
            $name = trim($name);
            $value = trim($value);

            // Si el valor tiene comillas, las quitamos
            if (preg_match('/^"(.*)"$/', $value, $matches)) {
                $value = $matches[1];
            }
            if (preg_match("/^'(.*)'$/", $value, $matches)) {
                $value = $matches[1];
            }

            if (!getenv($name)) {
                putenv("$name=$value");
                $_ENV[$name] = $value;
                $_SERVER[$name] = $value;
            }
        }
        self::$loaded = true;
        error_log("EnvLoader: .env cargado desde $file");
    }
}