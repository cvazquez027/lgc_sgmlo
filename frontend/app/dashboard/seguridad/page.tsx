"use client";

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { usePermissions } from "../../hooks/usePermissions";
import Link from "next/link";
import { useToast } from "../../providers/ToastProvider";
import { useConfirm } from "../../providers/ConfirmProvider";

// Catálogo de maestras agrupado por categoría. Agrupar en vez de listar todo plano
// es lo que hace que el navegador siga siendo prolijo a medida que se suman tablas
// (antes era una lista vertical fija; ahora escala mejor tanto en cantidad como en pantalla).
const CATEGORIAS_MAESTRAS = [
  {
    categoria: "Seguridad y Accesos",
    items: [
      { id: "rol", titulo: "Roles de Sistema", icono: "🛡️" },
      { id: "permiso", titulo: "Permisos", icono: "🔑" },
    ],
  },
  {
    categoria: "Normativa",
    items: [
      { id: "tipo_norma", titulo: "Tipos de Norma", icono: "📜" },
      { id: "estado_norma", titulo: "Estados de Norma", icono: "🏷️" },
      { id: "emisor_norma", titulo: "Emisores", icono: "🏛️" },
    ],
  },
  {
    categoria: "Matrices",
    items: [
      { id: "estado_matriz", titulo: "Estados de Matriz", icono: "📊" },
      { id: "tipo_modalidad", titulo: "Tipos de Modalidad", icono: "🏢" },
    ],
  },
  {
    categoria: "Cumplimiento y Contacto",
    items: [
      { id: "estado_cumplimiento", titulo: "Estados de Cumpl.", icono: "✅" },
      { id: "tipo_contacto", titulo: "Tipos de Contacto", icono: "📞" },
    ],
  },
];

// Listado plano derivado del catálogo, para lookups por id (título, ícono, etc.)
const MENU_MAESTRAS = CATEGORIAS_MAESTRAS.flatMap((cat) => cat.items);

// Tablas que no siguen el patrón genérico "descripcion + vigente"
const TABLAS_ESPECIALES = ["emisor_norma"];

interface RegistroMaestro {
  [key: string]: string | number;
}

interface Jurisdiccion {
  id_jurisdiccion: number;
  descripcion: string;
}

// Debe reflejar EXACTAMENTE la lógica de normalizarClave() en guardar.php, para que
// la vista previa en el formulario coincida con lo que finalmente persiste el backend.
const normalizarClave = (texto: string) => {
  return texto
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s]/g, "")
    .replace(/\s+/g, " ")
    .trim();
};

export default function SeguridadPage() {
  const router = useRouter();
  const { canRead, canEdit } = usePermissions();
  const toast = useToast();
  const confirm = useConfirm(); // aunque no se usa en esta pantalla, se deja por si se agrega eliminación después

  const [isCheckingPerms, setIsCheckingPerms] = useState(true);
  const [tablaActiva, setTablaActiva] = useState<string>(MENU_MAESTRAS[0].id);
  const [registros, setRegistros] = useState<RegistroMaestro[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"crear" | "editar">("crear");
  const [formLoading, setFormLoading] = useState(false);
  const [formData, setFormData] = useState({ id: "", descripcion: "", vigente: 1, id_jurisdiccion: "" });
  const [filtroMenu, setFiltroMenu] = useState("");

  // Jurisdicciones: se cargan bajo demanda, recién cuando el usuario entra a Emisores
  const [jurisdicciones, setJurisdicciones] = useState<Jurisdiccion[]>([]);
  const [loadingJurisdicciones, setLoadingJurisdicciones] = useState(false);

  const esTablaEspecial = TABLAS_ESPECIALES.includes(tablaActiva);

  useEffect(() => {
    const timer = setTimeout(() => setIsCheckingPerms(false), 100);
    return () => clearTimeout(timer);
  }, []);

  const getPrimaryKeyName = () => `id_${tablaActiva}`;

  const fetchData = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) { router.push("/"); return; }
    try {
      setLoading(true);
      setError("");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=${tablaActiva}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.mensaje || "Acceso denegado o error de lectura.");
      setRegistros(data.registros || []);
    } catch (err: any) {
      const msg = err.message;
      setError(msg);
      toast.showToast("Error", msg, "error");
    } finally {
      setLoading(false);
    }
  }, [router, tablaActiva, toast]);

  const fetchJurisdicciones = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return;
    try {
      setLoadingJurisdicciones(true);
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=jurisdiccion`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.mensaje || "No se pudo cargar el listado de jurisdicciones.");
      setJurisdicciones(data.registros || []);
    } catch (err: any) {
      toast.showToast("Error", err.message, "error");
    } finally {
      setLoadingJurisdicciones(false);
    }
  }, [toast]);

  useEffect(() => {
    if (!isCheckingPerms && canRead("maestras")) fetchData();
  }, [fetchData, isCheckingPerms, canRead, tablaActiva]);

  useEffect(() => {
    if (!isCheckingPerms && canRead("maestras") && tablaActiva === "emisor_norma" && jurisdicciones.length === 0 && !loadingJurisdicciones) {
      fetchJurisdicciones();
    }
  }, [isCheckingPerms, canRead, tablaActiva, jurisdicciones.length, loadingJurisdicciones, fetchJurisdicciones]);

  const openCrearModal = () => {
    if (!canEdit("maestras")) return;
    setModalMode("crear");
    setFormData({ id: "", descripcion: "", vigente: 1, id_jurisdiccion: "" });
    setIsModalOpen(true);
  };

  const openEditarModal = (registro: RegistroMaestro) => {
    if (!canEdit("maestras")) return;
    setModalMode("editar");
    const pkName = getPrimaryKeyName();
    const idValue = registro[pkName];
    setFormData({
      id: String(idValue ?? ''),
      descripcion: String(registro['descripcion'] || ""),
      vigente: Number(registro.vigente ?? 1),
      id_jurisdiccion: String(registro['id_jurisdiccion'] ?? ''),
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit("maestras")) return;

    if (esTablaEspecial && !formData.id_jurisdiccion) {
      toast.showToast("Error", "Debe seleccionar una jurisdicción.", "error");
      return;
    }

    setFormLoading(true);
    const token = localStorage.getItem("sgml_token");
    const pkName = getPrimaryKeyName();

    // Emisores no maneja "vigente"; en cambio, viaja el id_jurisdiccion.
    const payload: Record<string, any> = esTablaEspecial
      ? {
          tabla: tablaActiva,
          [pkName]: formData.id,
          descripcion: formData.descripcion,
          id_jurisdiccion: formData.id_jurisdiccion,
        }
      : {
          tabla: tablaActiva,
          [pkName]: formData.id,
          descripcion: formData.descripcion,
          vigente: formData.vigente,
        };

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/guardar.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.mensaje || "Error al procesar la solicitud.");
      setIsModalOpen(false);
      toast.showToast("Éxito", "Registro guardado correctamente.", "success");
      fetchData();
    } catch (err: any) {
      toast.showToast("Error", err.message, "error");
    } finally {
      setFormLoading(false);
    }
  };

  // Navegador en una sola fila: aplanamos el catálogo pero conservamos la marca de
  // "primero de su categoría" para poder dibujar un separador sutil entre grupos
  // sin necesitar una fila propia por categoría (eso es lo que hacía crecer la cabecera).
  const itemsMenu = useMemo(() => {
    const q = filtroMenu.trim().toLowerCase();
    const resultado: { item: (typeof MENU_MAESTRAS)[number]; nuevoGrupo: boolean }[] = [];
    CATEGORIAS_MAESTRAS.forEach((cat) => {
      const itemsCat = cat.items.filter((item) => !q || item.titulo.toLowerCase().includes(q));
      itemsCat.forEach((item, idx) => resultado.push({ item, nuevoGrupo: idx === 0 }));
    });
    return resultado;
  }, [filtroMenu]);

  const scrollMenuRef = useRef<HTMLDivElement>(null);
  const scrollMenu = (direccion: 1 | -1) => {
    scrollMenuRef.current?.scrollBy({ left: direccion * 220, behavior: "smooth" });
  };

  const tituloActivo = MENU_MAESTRAS.find((m) => m.id === tablaActiva)?.titulo;

  // Render condicional de seguridad
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

  return (
    <div className="space-y-4 animate-fade-in">
      {/* HEADER UNIFICADO (estilo Matrices) */}
      <div className="bg-[#005F78] text-white flex flex-col md:flex-row justify-between items-center gap-4 px-5 py-4 border-b border-[#004D62] rounded-t-xl">
        <div className="flex items-center gap-4">
          <Link 
            href="/dashboard" 
            className="flex items-center justify-center w-9 h-9 rounded-full bg-white/20 hover:bg-white/30 text-white transition-all shadow-sm group"
            title="Volver al inicio"
          >
            <svg className="w-5 h-5 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div className="h-8 w-px bg-white/30 hidden md:block"></div>
          <h1 className="text-xl font-heading font-bold uppercase tracking-tight m-0 leading-none">
            Configuración
          </h1>
        </div>
      </div>

      {/* NAVEGADOR DE MAESTRAS: una sola fila deslizable + buscador. Reemplaza al menú lateral
          fijo (y a la grilla por categorías): gana ancho para la tabla, mantiene la cabecera
          baja y compacta, y escala mejor a medida que se agregan tablas —simplemente se desliza,
          en vez de crecer en altura—. Sin salirse de la estética existente (tarjetas rounded-xl /
          shadow-sm / paleta slate+lgc, íconos en badge circular, estado activo elevado). */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4">
        <div className="flex items-center justify-between gap-3 mb-3">
          <h3 className="text-[10px] uppercase tracking-[0.2em] font-bold text-slate-400 shrink-0">Tablas Maestras</h3>
          <div className="relative w-40 sm:w-56 shrink-0">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 10a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={filtroMenu}
              onChange={(e) => setFiltroMenu(e.target.value)}
              placeholder="Buscar..."
              className="w-full pl-9 pr-8 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-lgc-primary focus:border-lgc-primary outline-none transition-all"
            />
            {filtroMenu && (
              <button
                onClick={() => setFiltroMenu("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-500 text-lg leading-none"
                title="Limpiar búsqueda"
              >
                &times;
              </button>
            )}
          </div>
        </div>

        {itemsMenu.length === 0 ? (
          <p className="text-sm text-slate-400 italic py-2">No hay tablas que coincidan con la búsqueda.</p>
        ) : (
          <div className="relative flex items-center gap-1">
            <button
              onClick={() => scrollMenu(-1)}
              className="hidden sm:flex shrink-0 w-8 h-8 rounded-full bg-slate-50 hover:bg-lgc-primary/10 border border-slate-200 items-center justify-center text-slate-400 hover:text-lgc-primary transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-lgc-primary/50"
              title="Ver anteriores"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
              </svg>
            </button>

            <div
              ref={scrollMenuRef}
              className="flex items-center gap-2 overflow-x-auto scroll-smooth snap-x snap-mandatory py-1 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden"
            >
              {itemsMenu.map(({ item, nuevoGrupo }, i) => {
                const activo = tablaActiva === item.id;
                return (
                  <div key={item.id} className="flex items-center gap-2 shrink-0 snap-start">
                    {nuevoGrupo && i !== 0 && <span className="w-px h-8 bg-slate-100 mx-1 shrink-0" />}
                    <button
                      onClick={() => setTablaActiva(item.id)}
                      className={`flex items-center gap-2 pl-2 pr-4 py-2 rounded-lg text-sm font-semibold border whitespace-nowrap transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-lgc-primary/50 ${
                        activo
                          ? 'bg-lgc-primary text-white border-lgc-primary shadow-md -translate-y-0.5'
                          : 'bg-white text-slate-600 border-slate-200 hover:border-lgc-primary/40 hover:bg-slate-50 hover:-translate-y-0.5'
                      }`}
                    >
                      <span className={`w-7 h-7 rounded-full flex items-center justify-center text-sm shrink-0 ${
                        activo ? 'bg-white/20' : 'bg-slate-100'
                      }`}>
                        {item.icono}
                      </span>
                      {item.titulo}
                    </button>
                  </div>
                );
              })}
            </div>

            <button
              onClick={() => scrollMenu(1)}
              className="hidden sm:flex shrink-0 w-8 h-8 rounded-full bg-slate-50 hover:bg-lgc-primary/10 border border-slate-200 items-center justify-center text-slate-400 hover:text-lgc-primary transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-lgc-primary/50"
              title="Ver siguientes"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* ÁREA DE TRABAJO */}
      <div className="w-full bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden flex flex-col min-h-125">
        <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
          <h2 className="text-lg font-heading text-slate-700">{tituloActivo}</h2>
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
                  <th className="p-5 font-bold w-48">{esTablaEspecial ? 'Jurisdicción' : 'Estado'}</th>
                  <th className="p-5 font-bold text-right w-24">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {registros.length === 0 ? (
                  <tr><td colSpan={4} className="p-8 text-center text-slate-400 italic">No se encontraron datos en esta tabla.</td></tr>
                ) : (
                  registros.map((reg, index) => {
                    const pk = getPrimaryKeyName();
                    const desc = reg['descripcion'];
                    return (
                      <tr key={`${pk}-${index}`} className="hover:bg-slate-50/50 transition-colors">
                        <td className="p-5 text-xs text-slate-400 font-medium">#{String(reg[pk])}</td>
                        <td className="p-5 font-bold text-slate-700">{String(desc)}</td>
                        <td className="p-5">
                          {esTablaEspecial ? (
                            <span className="px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest bg-lgc-tostado/20 text-lgc-primary">
                              {String(reg['jurisdiccion_desc'] ?? 'Sin Jurisdicción')}
                            </span>
                          ) : (
                            <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest ${reg.vigente == 1 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                              {reg.vigente == 1 ? 'Vigente' : 'Baja'}
                            </span>
                          )}
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

      {/* MODAL */}
      {isModalOpen && canEdit("maestras") && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h2 className="text-xl font-heading text-lgc-primary uppercase tracking-tight">
                {modalMode === "crear" ? "Registrar" : "Modificar"} {tituloActivo}
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
            </div>
            <form onSubmit={handleSubmit} className="p-8 space-y-6">
              <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-widest">Tabla Afectada</span>
                <code className="text-xs text-lgc-primary font-bold">{tablaActiva}</code>
              </div>
              <div>
                <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">
                  {tablaActiva === 'permiso' ? 'Descripción (ej: leer_clientes)' : tablaActiva === 'emisor_norma' ? 'Nombre del Emisor' : 'Descripción / Nombre'} *
                </label>
                <input 
                  type="text" 
                  required
                  value={formData.descripcion}
                  onChange={(e) => setFormData({...formData, descripcion: e.target.value})}
                  className="w-full p-3 bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary focus:border-lgc-primary outline-none transition-all text-sm"
                  placeholder={tablaActiva === 'emisor_norma' ? 'Ej: Ministerio de Educación, Tecnología y Ciencia' : 'Escriba aquí...'}
                />
              </div>

              {esTablaEspecial ? (
                <>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Jurisdicción *</label>
                    <select
                      required
                      value={formData.id_jurisdiccion}
                      onChange={(e) => setFormData({...formData, id_jurisdiccion: e.target.value})}
                      disabled={loadingJurisdicciones}
                      className="w-full p-3 bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary focus:border-lgc-primary outline-none transition-all text-sm disabled:opacity-60"
                    >
                      <option value="" disabled>{loadingJurisdicciones ? "Cargando jurisdicciones..." : "Seleccione una jurisdicción"}</option>
                      {jurisdicciones.map((j) => (
                        <option key={j.id_jurisdiccion} value={j.id_jurisdiccion}>{j.descripcion}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Clave Normalizada</label>
                    <div className="w-full p-3 bg-slate-100 border border-slate-200 rounded-lg text-sm text-slate-500 font-mono">
                      {formData.descripcion
                        ? normalizarClave(formData.descripcion)
                        : <span className="italic text-slate-300">se genera automáticamente</span>}
                    </div>
                    <p className="text-[10px] text-slate-400 mt-1.5">Se calcula sola a partir del nombre: minúsculas, sin tildes ni símbolos.</p>
                  </div>
                </>
              ) : (
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
              )}

              <div className="pt-4 flex gap-4 border-t border-slate-100 mt-6">
                <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 py-3 text-xs uppercase tracking-widest font-bold text-slate-400 hover:text-slate-600 transition-colors">
                  Cancelar
                </button>
                <button type="submit" disabled={formLoading} className="flex-1 bg-lgc-primary hover:bg-lgc-accent text-white py-3 rounded-lg text-xs uppercase tracking-widest font-bold shadow-lg transition-all disabled:opacity-70">
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