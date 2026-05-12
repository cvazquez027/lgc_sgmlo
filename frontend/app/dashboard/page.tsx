import Link from "next/link";

export default function DashboardHome() {
  const modulos = [
    {
      titulo: "Inicio",
      descripcion: "Panel central y resumen operativo",
      href: "/dashboard",
      icono: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      )
    },
    {
      titulo: "Clientes",
      descripcion: "Gestión de empresas y establecimientos",
      href: "/dashboard/clientes",
      icono: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      )
    },
    {
      titulo: "Boletín Oficial",
      descripcion: "Explorador y alta de normativas legales",
      href: "/dashboard/norma_bo",
      icono: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      )
    },
    {
      titulo: "Normativa",
      descripcion: "Repositorio oficial de normativas y requisitos",
      href: "/dashboard/normativa",
      icono: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
        </svg>
      )
    },
    {
      titulo: "Matrices Legales",
      descripcion: "Asignación de requisitos y control de cumplimiento",
      href: "/dashboard/matrices",
      icono: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )
    },
    {
      titulo: "Usuarios y Seg.",
      descripcion: "Control de accesos y roles del sistema",
      href: "/dashboard/usuarios",
      icono: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      )
    },
    {
      titulo: "Configuración",
      descripcion: "Diccionarios de datos y parámetros generales",
      href: "/dashboard/seguridad",
      icono: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      )
    },
    {
      titulo: "Mi Perfil",
      descripcion: "Mis datos personales y cambio de contraseña",
      href: "/dashboard/perfil",
      icono: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    }
  ];

  return (
    <div className="animate-fade-in font-sans">
      {/* Grid de Módulos (Launchpad)
        Ajustado a lg:grid-cols-4 para forzar el layout de 4x2 
      */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {modulos.map((modulo, index) => (
          <Link 
            key={index}
            href={modulo.href}
            // Ajustes Quirúrgicos: min-h para forzar cuadratura, flex-col clásico, y sombras elevadas (shadow-xl)
            className="group flex flex-col justify-between p-6 sm:p-8 min-h-65 bg-lgc-primary rounded-3xl shadow-xl shadow-lgc-primary/20 border border-white/10 hover:bg-lgc-accent hover:shadow-2xl hover:shadow-lgc-accent/30 transition-all duration-500 transform hover:-translate-y-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-lgc-accent focus-visible:ring-offset-2"
            aria-label={`Ir al módulo de ${modulo.titulo}`}
          >
            {/* Contenedor Superior: Icono y Titulo Apilados para formato más cuadrado */}
            <div className="flex flex-col gap-5">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center bg-white/10 text-white group-hover:bg-white group-hover:text-lgc-accent transition-all duration-500 shrink-0 shadow-inner group-hover:scale-110 origin-left">
                {modulo.icono}
              </div>
              <h2 className="text-xl font-heading font-bold text-white transition-colors duration-300">
                {modulo.titulo}
              </h2>
            </div>
            
            {/* Contenedor Inferior: Descripción y Flecha alineados abajo */}
            <div className="mt-4">
              <p className="text-sm text-white/80 leading-relaxed group-hover:text-white transition-colors duration-300">
                {modulo.descripcion}
              </p>

              <div className="mt-5 flex justify-end">
                <span className="text-white/40 group-hover:text-white transition-colors duration-300 transform group-hover:translate-x-1.5">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}