"use client";

import { useState, useEffect, useCallback } from 'react';

/**
 * Hook de Seguridad LGC
 * Gestiona y valida los permisos del usuario almacenados localmente.
 */
export function usePermissions() {
    const [permisos, setPermisos] = useState<string[]>([]);

    useEffect(() => {
        // 1. Recuperamos los permisos al cargar el componente
        // (Esto asume que en tu pantalla de Login hiciste: 
        // localStorage.setItem('sgml_permisos', JSON.stringify(data.permisos)))
        const storedPermisos = localStorage.getItem('sgml_permisos');
        
        if (storedPermisos) {
            try {
                setPermisos(JSON.parse(storedPermisos));
            } catch (error) {
                console.error("Error de seguridad: Permisos corruptos en almacenamiento local.");
                // Si alguien manipuló el localStorage a mano, vaciamos por seguridad
                setPermisos([]); 
            }
        }
    }, []);

    // 2. Función base para buscar si existe un permiso exacto
    const hasPermission = useCallback((permiso: string) => {
        // Por diseño, si somos el "Super Admin" absoluto, podríamos hacer un bypass aquí,
        // pero lo más seguro es que incluso el Admin tenga los permisos listados.
        return permisos.includes(permiso);
    }, [permisos]);

    // 3. Helpers semánticos para hacer el código más limpio en las pantallas
    // Convierte canRead("usuarios") en una búsqueda de "leer_usuarios"
    const canRead = useCallback((modulo: string) => {
        return hasPermission(`leer_${modulo}`);
    }, [hasPermission]);

    const canEdit = useCallback((modulo: string) => {
        return hasPermission(`editar_${modulo}`);
    }, [hasPermission]);

    return { 
        permisos,     // El array completo por si necesitamos depurar
        hasPermission, // Validación estricta
        canRead,      // Validador de lectura
        canEdit       // Validador de escritura/modificación
    };
}