"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { usePermissions } from "../hooks/usePermissions";

export default function DashboardHome() {
  const { canRead } = usePermissions();
  const router = useRouter();
  const [isCheckingPerms, setIsCheckingPerms] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsCheckingPerms(false), 100);
    return () => clearTimeout(timer);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("sgml_token");
    router.push("/");
  };

  const modulos = [
    {
      titulo: "Clientes",
      descripcion: "Gestión corporativa de empresas y sus establecimientos.",
      href: "/dashboard/clientes",
      permiso: "clientes",
      icono: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      )
    },
    {
      titulo: "Boletín Oficial",
      descripcion: "Explorador inteligente y alta de normativas legales vigentes.",
      href: "/dashboard/norma_bo",
      permiso: "boletin", 
      icono: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      )
    },
    {
      titulo: "Normativa",
      descripcion: "Repositorio oficial centralizado de normativas y requisitos.",
      href: "/dashboard/normativa",
      permiso: "normativa",
      icono: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
        </svg>
      )
    },
    {
      titulo: "Matrices Legales",
      descripcion: "Asignación operativa de requisitos y control de cumplimiento.",
      href: "/dashboard/matrices",
      permiso: "matriz",
      icono: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )
    },
    {
      titulo: "Reportes",
      descripcion: "Exportables de cumplimiento, vencimientos y trámites.",
      href: "/dashboard/reportes",
      permiso: "reportes",
      icono: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      )
    },
    {
      titulo: "Usuarios y Seguridad",
      descripcion: "Control de accesos, roles y auditoría del sistema.",
      href: "/dashboard/usuarios",
      permiso: "usuarios",
      icono: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      )
    },
    {
      titulo: "Configuración",
      descripcion: "Diccionarios de datos y parámetros generales del entorno.",
      href: "/dashboard/seguridad",
      permiso: "maestras",
      icono: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      )
    },
    {
      titulo: "Mi Perfil",
      descripcion: "Actualización de datos personales y credenciales.",
      href: "/dashboard/perfil",
      permiso: null, 
      icono: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    }
  ];

  const modulosFiltrados = modulos.filter(modulo => !modulo.permiso || canRead(modulo.permiso));

  if (isCheckingPerms) {
    return <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Cargando tablero corporativo...</div>;
  }

  return (
    <div className="animate-fade-in font-sans h-full flex flex-col py-2 justify-between">
      
      <div className="flex-1 flex flex-col justify-center my-auto">
        {/* Grid: garantiza 4 columnas en escritorio */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 xl:gap-5 max-w-screen-2xl mx-auto w-full px-4">
          {modulosFiltrados.map((modulo, index) => (
            <Link 
              key={index}
              href={modulo.href}
              className="group relative flex flex-col p-5 bg-[#00455E] rounded-2xl border border-[#005A7A] shadow-[0_4px_10px_rgba(0,34,48,0.45)] hover:shadow-[0_6px_14px_rgba(0,34,48,0.65)] hover:bg-[#00384D] hover:-translate-y-0.5 transition-all duration-300 h-full overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-lgc-primary w-full"
              aria-label={`Acceder al módulo de ${modulo.titulo}`}
            >
              <div className="flex items-start gap-4 mb-3">
                <div className="w-11 h-11 rounded-xl flex items-center justify-center bg-white/10 text-white/70 group-hover:bg-lgc-accent/20 group-hover:text-lgc-accent transition-all duration-300 shrink-0 border border-white/5 group-hover:border-lgc-accent/30 shadow-inner group-hover:scale-110">
                  {modulo.icono}
                </div>
                <div className="flex-1 mt-0.5">
                  <h2 className="text-base sm:text-lg font-heading font-black text-white leading-tight uppercase tracking-tight">
                    {modulo.titulo}
                  </h2>
                </div>
              </div>
              
              <div className="flex flex-col flex-1 justify-between gap-3">
                <p className="text-[11px] sm:text-xs text-[#A8D3E0] leading-relaxed font-medium group-hover:text-white transition-colors duration-300">
                  {modulo.descripcion}
                </p>

                <div className="flex justify-end pt-2.5 border-t border-white/10">
                  <span className="text-white/30 group-hover:text-lgc-accent transition-colors duration-300 transform group-hover:translate-x-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M17 8l4 4m0 0l-4-4m4-4H3" />
                    </svg>
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      <div className="mt-4 flex justify-center shrink-0">
         <button 
           onClick={handleLogout}
           className="flex items-center gap-2.5 px-6 py-2 rounded-full font-bold uppercase tracking-widest text-xs shadow-sm bg-lgc-accent text-white border-2 border-lgc-accent 
           hover:bg-red-800 hover:text-[#FFFBEB] hover:border-2 hover:border-[#FFFBEB] hover:ring-2 hover:ring-red-900 transition-all duration-200 group"
         >
            <svg className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Cerrar Sesión Segura
         </button>
      </div>

    </div>
  );
}