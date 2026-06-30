<?php
require_once __DIR__ . '/../vendor/autoload.php';

use Dotenv\Dotenv;

class EnvLoader {
    private static $loaded = false;

    public static function load($path = null) {
        if (self::$loaded) return;

        $path = $path ?: __DIR__ . '/..';
        $dotenv = Dotenv::createImmutable($path);
        $dotenv->load();

        self::$loaded = true;
    }
}