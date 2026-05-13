// Archivo: frontend/app/dashboard/layout.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Image from "next/image";
import Link from "next/link";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isLoading, setIsLoading] = useState(true);

  // Estado para controlar si el menú lateral está abierto o cerrado
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // Protección de Ruta Básica
  useEffect(() => {
    const token = localStorage.getItem("sgml_token");
    if (!token) {
      router.push("/");
    } else {
      setIsLoading(false);
    }
  }, [router]);

  const [hayNuevasNormas, setHayNuevasNormas] = useState(false);

  useEffect(() => {
    // Función para consultar al backend
    const checkNuevas = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/boletin/check_nuevas.php`);
        const data = await res.json();
        setHayNuevasNormas(data.hay_nuevas);
      } catch (e) {
        console.error(e);
      }
    };

    checkNuevas(); // Chequea al cargar el menú
    // Si querés que chequee cada 10 minutos automáticamente, descomentá esto:
    // const interval = setInterval(checkNuevas, 600000); 
    // return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("sgml_token");
    router.push("/");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-lgc-primary font-heading text-xl animate-pulse">
        Iniciando entorno seguro...
      </div>
    );
  }

  const menuItems = [
    { 
      name: "Inicio", 
      path: "/dashboard",
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
    },
    { 
      name: "Clientes", 
      path: "/dashboard/clientes",
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
    },
    { 
      name: "Boletín Oficial", 
      path: "/dashboard/norma_bo",
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
    },
    { 
      name: "Normativa", 
      path: "/dashboard/normativa",
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
    },
    { 
      name: "Matrices Legales", 
      path: "/dashboard/matrices",
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
    },
    { 
      name: "Usuarios y Seguridad", 
      path: "/dashboard/usuarios",
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
    },
    { 
      name: "Configuración", 
      path: "/dashboard/seguridad",
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
    },
  ];

  return (
    <div className="flex min-h-screen font-sans bg-slate-50">
      
      {/* MENÚ LATERAL (SIDEBAR) COLAPSABLE */}
      <aside className={`bg-slate-900 text-slate-300 flex flex-col shadow-2xl z-50 transition-all duration-300 shrink-0 ${isMenuOpen ? 'w-60' : 'w-0 overflow-hidden'}`}>
        {/* Contenedor interno fijo para evitar que el texto se aplaste al animarse */}
        <div className="w-60 flex flex-col h-full">
          
          <div className="h-20 flex items-center justify-center bg-slate-900 px-6 shrink-0 border-b border-slate-800/50">
            <Image 
              src="/logo_lgc.png" 
              alt="LGC Global Consulting" 
              width={90} 
              height={30} 
              className="object-contain drop-shadow-lg"
              priority
            />
          </div>

          {/* Ajuste de espaciados (py-4, px-3, space-y-1) para evitar el scroll vertical */}
          <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto custom-scrollbar">
            {menuItems.map((item) => {
              const isActive = pathname.includes(item.path) && (item.path !== '/dashboard' || pathname === '/dashboard');
              return (
                <Link 
                  key={item.name} 
                  href={item.path}
                  onClick={() => window.innerWidth < 768 && setIsMenuOpen(false)} // Auto-cierra en móviles
                  className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-300 font-medium group ${
                    isActive 
                    ? "bg-lgc-primary text-white shadow-lg shadow-lgc-primary/30" 
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <span className={`transition-transform duration-300 ${isActive ? "scale-110 text-white" : "group-hover:scale-110 text-slate-500 group-hover:text-lgc-accent"}`}>
                    {item.icon}
                  </span>
                  <span className="text-sm tracking-wide">{item.name}</span>

                  {item.name === "Boletín Oficial" && hayNuevasNormas && (
                    <span className="absolute right-4 flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-orange-500 shadow-sm border border-slate-900"></span>
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          <div className="p-3 border-t border-slate-800 bg-slate-900/50 shrink-0">
            <button 
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-slate-400 hover:text-white hover:bg-red-500/10 hover:border-red-500/30 border border-transparent rounded-xl transition-all group"
            >
              <svg className="w-5 h-5 text-slate-500 group-hover:text-red-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
              <span>Cerrar Sesión</span>
            </button>
          </div>
        </div>
      </aside>

      {/* CONTENIDO PRINCIPAL */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden relative transition-all duration-300">
        
        <header className="h-20 bg-white/90 backdrop-blur-md border-b border-slate-200 flex items-center justify-between px-6 shadow-sm z-10 sticky top-0 shrink-0">
          <div className="flex items-center gap-4">
            
            {/* BOTÓN HAMBURGUESA */}
            <button 
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="p-2 text-slate-500 hover:text-lgc-primary bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-lgc-primary/50"
              title={isMenuOpen ? "Ocultar Menú" : "Mostrar Menú"}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            <div>
              <h2 className="text-xl font-heading text-lgc-primary font-bold tracking-tight hidden sm:block">
                Sistema de Gestión de Matrices Legales
              </h2>
              <h2 className="text-xl font-heading text-lgc-primary font-bold tracking-tight sm:hidden">
                SGML
              </h2>
              <p className="text-xs text-slate-500 uppercase tracking-widest font-semibold mt-0.5 hidden sm:block">
                LGC Global Consulting
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-lgc-tostado/30 border border-lgc-tostado flex items-center justify-center text-lgc-primary font-bold shadow-sm cursor-pointer hover:bg-lgc-tostado/50 transition-colors" title="Administrador">
              AD
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-auto p-4 md:p-8 bg-slate-50/50">
          <div className="max-w-screen-2xl mx-auto">
            {children}
          </div>
        </div>
      </main>

      {/* OVERLAY PARA MÓVILES (Opcional, oscurece el fondo al abrir en pantallas chicas) */}
      {isMenuOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/50 z-40 md:hidden"
          onClick={() => setIsMenuOpen(false)}
        />
      )}

    </div>
  );
}