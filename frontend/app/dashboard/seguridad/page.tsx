"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { usePermissions } from "../../hooks/usePermissions";
import Link from "next/link";

// Definimos la estructura de nuestro menú de Maestras
const MENU_MAESTRAS = [
  { id: 'rol', titulo: 'Roles de Sistema', icono: '🛡️' },
  { id: 'permiso', titulo: 'Permisos', icono: '🔑' },
  { id: 'tipo_contacto', titulo: 'Tipos de Contacto', icono: '📞' },
  { id: 'tipo_norma', titulo: 'Tipos de Norma', icono: '📜' },
  { id: 'estado_norma', titulo: 'Estados de Norma', icono: '🏷️' },
  { id: 'estado_matriz', titulo: 'Estados de Matriz', icono: '📊' },
  { id: 'estado_cumplimiento', titulo: 'Estados de Cumpl.', icono: '✅' },
  { id: 'tipo_modalidad', titulo: 'Tipos de Modalidad', icono: '🏢' },
];

// Interfaz genérica para cualquier registro maestro
interface RegistroMaestro {
  [key: string]: string | number; // Permite cualquier clave (id_rol, id_tipo_norma, etc.)
}

export default function SeguridadPage() {
  const router = useRouter();
  
  // --- SEGURIDAD ---
  const { canRead, canEdit } = usePermissions();
  const [isCheckingPerms, setIsCheckingPerms] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsCheckingPerms(false), 100);
    return () => clearTimeout(timer);
  }, []);
  // -----------------

  const [tablaActiva, setTablaActiva] = useState<string>(MENU_MAESTRAS[0].id);
  const [registros, setRegistros] = useState<RegistroMaestro[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Estados del Modal Dinámico
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"crear" | "editar">("crear");
  const [formLoading, setFormLoading] = useState(false);
  
  // Guardamos un objeto genérico para el formulario
  const [formData, setFormData] = useState<{ id: string | number, descripcion: string, vigente: number }>({ 
    id: "", 
    descripcion: "", 
    vigente: 1 
  });

  const fetchData = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) { router.push("/"); return; }

    try {
      setLoading(true);
      setError("");
      // Le pegamos a nuestro endpoint seguro con Lista Blanca
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=${tablaActiva}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.mensaje || "Acceso denegado o error de lectura.");
      }
      
      setRegistros(data.registros || []);
    } catch (err: any) {
      setError(err.message);
      setRegistros([]); // Limpiamos por seguridad
    } finally {
      setLoading(false);
    }
  }, [router, tablaActiva]);

  useEffect(() => {
    // Si cambia la tabla activa en el menú, volvemos a buscar datos
    if (!isCheckingPerms && canRead("maestras")) {
      fetchData();
    }
  }, [fetchData, isCheckingPerms, canRead, tablaActiva]);

  // Funciones Dinámicas para el Modal
  // Como la columna ID cambia (id_rol, id_tipo_norma), necesitamos inferirla
  const getPrimaryKeyName = () => `id_${tablaActiva}`;

  const openCrearModal = () => {
    if (!canEdit("maestras")) return;
    setModalMode("crear");
    setFormData({ id: "", descripcion: "", vigente: 1 });
    setIsModalOpen(true);
  };

  const openEditarModal = (registro: RegistroMaestro) => {
    if (!canEdit("maestras")) return;
    setModalMode("editar");
    
    // Extraemos el valor del ID dinámicamente usando el nombre de la clave primaria
    const pkName = getPrimaryKeyName();
    const idValue = registro[pkName] as string | number;
    
    // Ahora todas las tablas usan la columna "descripcion" de forma unificada
    const descripcionStr = registro['descripcion'];

    setFormData({ 
      id: idValue, 
      descripcion: String(descripcionStr || ""), 
      vigente: Number(registro.vigente ?? 1) 
    });
    
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit("maestras")) return;

    setFormLoading(true);
    const token = localStorage.getItem("sgml_token");

    // Preparamos el payload limpio y unificado
    const pkName = getPrimaryKeyName();
    
    const payload = {
      tabla: tablaActiva,
      [pkName]: formData.id,
      descripcion: formData.descripcion,
      vigente: formData.vigente
    };

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/guardar.php`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.mensaje || "Error al procesar la solicitud.");

      setIsModalOpen(false);
      fetchData(); 
    } catch (err: any) {
      alert("Error: " + err.message);
    } finally {
      setFormLoading(false);
    }
  };

  // --- RENDERIZADOS CONDICIONALES DE SEGURIDAD ---
  if (isCheckingPerms) {
    return <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Verificando seguridad...</div>;
  }

  if (!canRead("maestras")) {
    return (
      <div className="flex flex-col items-center justify-center py-32 bg-white rounded-xl shadow-sm border border-red-100">
        <div className="text-red-500 text-6xl mb-4">🔒</div>
        <h2 className="text-2xl font-heading text-slate-800 uppercase tracking-tight mb-2">Panel Restringido</h2>
        <p className="text-slate-500 font-sans">No cuenta con privilegios para modificar diccionarios y configuraciones base.</p>
      </div>
    );
  }
  // -----------------------------------------------

  return (
    <div className="space-y-6">
      
      {/* BLOQUE NUEVO: Botón de Volver + Título Centrados */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
        <div className="flex items-center gap-3">
          <Link 
            href="/dashboard" 
            className="flex items-center justify-center w-8 h-8 rounded-full text-slate-400 hover:bg-slate-100 hover:text-lgc-primary transition-all group"
            title="Volver al inicio"
          >
            <svg className="w-5 h-5 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <h1 className="text-xl font-bold text-lgc-primary uppercase tracking-wide m-0 leading-none">
            Panel de Configuración Base
          </h1>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-6 items-start">
        
        {/* MENÚ LATERAL (Sidebar) */}
        <div className="w-full md:w-64 shrink-0 bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-100">
            <h3 className="text-[10px] uppercase tracking-[0.2em] font-bold text-slate-400">Tablas Maestras</h3>
          </div>
          <div className="flex flex-col">
            {MENU_MAESTRAS.map((item) => (
              <button
                key={item.id}
                onClick={() => setTablaActiva(item.id)}
                className={`flex items-center gap-3 px-5 py-4 text-sm font-semibold transition-all ${
                  tablaActiva === item.id 
                    ? 'bg-lgc-tostado/20 text-lgc-primary border-r-4 border-lgc-primary' 
                    : 'text-slate-600 hover:bg-slate-50 hover:text-lgc-primary'
                }`}
              >
                <span>{item.icono}</span>
                {item.titulo}
              </button>
            ))}
          </div>
        </div>

        {/* ÁREA DE TRABAJO (Tabla de la derecha) */}
        <div className="grow w-full bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden flex flex-col h-full min-h-125">
          
          {/* Toolbar de la tabla */}
          <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
            <h2 className="text-lg font-heading text-slate-700">
              {MENU_MAESTRAS.find(m => m.id === tablaActiva)?.titulo}
            </h2>
            
            {canEdit("maestras") && (
              <button 
                onClick={openCrearModal}
                className="bg-lgc-primary hover:bg-lgc-accent text-white font-bold py-2 px-5 rounded-lg transition-all text-[10px] uppercase tracking-widest shadow-md"
              >
                + Nuevo Registro
              </button>
            )}
          </div>

          {error && (
            <div className="m-5 bg-red-50 text-red-600 p-4 rounded-lg text-sm border border-red-100 flex items-center gap-2">
              <span className="font-bold uppercase tracking-widest text-[10px]">Error:</span> {error}
            </div>
          )}

          {loading ? (
            <div className="flex-1 flex items-center justify-center text-lgc-primary font-heading animate-pulse">Consultando base de datos...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left font-sans">
                <thead>
                  <tr className="bg-white border-b border-slate-200 text-slate-400 text-[10px] uppercase tracking-[0.2em]">
                    <th className="p-5 font-bold w-20">ID</th>
                    <th className="p-5 font-bold">Descripción / Nombre</th>
                    <th className="p-5 font-bold w-32">Estado</th>
                    <th className="p-5 font-bold text-right w-24">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {registros.length === 0 ? (
                    <tr><td colSpan={4} className="p-8 text-center text-slate-400 italic">No se encontraron datos en esta tabla.</td></tr>
                  ) : (
                    registros.map((reg, index) => {
                      const pk = getPrimaryKeyName();
                      const desc = reg['descripcion']; // Unificado y directo
                      
                      return (
                        <tr key={`${pk}-${index}`} className="hover:bg-slate-50/50 transition-colors">
                          <td className="p-5 text-xs text-slate-400 font-medium">
                            #{String(reg[pk])}
                          </td>
                          <td className="p-5 font-bold text-slate-700">
                            {String(desc)}
                          </td>
                          <td className="p-5">
                            <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest ${reg.vigente == 1 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                              {reg.vigente == 1 ? 'Vigente' : 'Baja'}
                            </span>
                          </td>
                          <td className="p-5 text-right">
                            {canEdit("maestras") ? (
                              <button onClick={() => openEditarModal(reg)} className="text-lgc-primary hover:text-lgc-accent text-[10px] font-bold uppercase tracking-widest transition-colors">Editar</button>
                            ) : (
                              <span className="text-slate-300 text-[10px] font-bold uppercase tracking-widest cursor-not-allowed">Solo Lectura</span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* MODAL GENÉRICO DE ABM */}
      {isModalOpen && canEdit("maestras") && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h2 className="text-xl font-heading text-lgc-primary uppercase tracking-tight">
                {modalMode === "crear" ? "Registrar" : "Modificar"} {MENU_MAESTRAS.find(m => m.id === tablaActiva)?.titulo}
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-8 space-y-6">
              
              {/* Info de debug visual para el usuario */}
              <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-widest">Tabla Afectada</span>
                <code className="text-xs text-lgc-primary font-bold">{tablaActiva}</code>
              </div>

              <div>
                <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">
                  {tablaActiva === 'permiso' ? 'Descripción (ej: leer_clientes)' : 'Descripción / Nombre'} *
                </label>
                <input 
                  type="text" 
                  required
                  value={formData.descripcion}
                  onChange={(e) => setFormData({...formData, descripcion: e.target.value})}
                  className="w-full p-3 bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary focus:border-lgc-primary outline-none transition-all text-sm"
                  placeholder="Escriba aquí..."
                />
              </div>

              <div>
                <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Vigencia *</label>
                <select 
                  value={formData.vigente}
                  onChange={(e) => setFormData({...formData, vigente: parseInt(e.target.value)})}
                  className="w-full p-3 bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary focus:border-lgc-primary outline-none transition-all text-sm"
                >
                  <option value={1}>ACTIVO / VIGENTE</option>
                  <option value={0}>INACTIVO / DADO DE BAJA</option>
                </select>
              </div>

              <div className="pt-4 flex gap-4 border-t border-slate-100 mt-6">
                <button 
                  type="button" 
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 py-3 text-xs uppercase tracking-widest font-bold text-slate-400 hover:text-slate-600 transition-colors"
                >
                  Cancelar
                </button>
                <button 
                  type="submit" 
                  disabled={formLoading}
                  className="flex-1 bg-lgc-primary hover:bg-lgc-accent text-white py-3 rounded-lg text-xs uppercase tracking-widest font-bold shadow-lg transition-all disabled:opacity-70"
                >
                  {formLoading ? "Procesando..." : "Guardar Registro"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}