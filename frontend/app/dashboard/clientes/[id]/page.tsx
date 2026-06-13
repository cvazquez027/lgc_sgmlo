"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { usePermissions } from "../../../hooks/usePermissions";
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

interface DatoContacto {
  id_tipo_contacto: string;
  valor: string;
}

interface Establecimiento {
  id_cliente_establecimiento: number;
  descripcion: string;
  jurisdiccion_nombre: string;
  id_jurisdiccion: number;
  vigente: number;
  contactos?: DatoContacto[];
  categorias?: { id_categoria: number; descripcion: string }[]; // <-- NUEVO
}

interface Jurisdiccion {
  id_jurisdiccion: number;
  descripcion: string;
}

interface TipoContacto {
  id_tipo_contacto: number;
  descripcion: string;
}

interface Categoria {
  id_categoria: number;
  descripcion: string;
}

interface Responsable {
  id_responsable_establecimiento: number;
  descripcion: string;
  observacion: string;
  vigente: number;
}

// Subcomponente para el Drag and Drop de las categorías asignadas
const SortableCategoriaItem = ({ cat, onRemove }: { cat: Categoria, onRemove: (id: number) => void }) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: cat.id_categoria });
  const style = { 
    transform: CSS.Transform.toString(transform), 
    transition, 
    zIndex: isDragging ? 50 : 1, 
    opacity: isDragging ? 0.5 : 1, 
    position: isDragging ? 'relative' as 'relative' : 'static' as 'static' 
  };
  
  return (
    <div ref={setNodeRef} style={style} className="flex items-center justify-between p-2.5 bg-white border border-slate-200 rounded-lg shadow-sm mb-2 group hover:border-lgc-primary transition-colors">
       <div className="flex items-center gap-3">
         <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing text-slate-400 hover:text-lgc-primary touch-none">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" /></svg>
         </div>
         <span className="text-xs font-bold text-slate-700">{cat.descripcion}</span>
       </div>
       <button onClick={() => onRemove(cat.id_categoria)} className="text-slate-300 hover:text-red-500 transition-colors bg-slate-50 hover:bg-red-50 p-1.5 rounded" title="Quitar categoría">
         <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
       </button>
    </div>
  );
};

// Subcomponente para el Drag and Drop de los responsables
const SortableResponsableItem = ({ resp, onEdit, onDelete }: { resp: Responsable, onEdit: (r: Responsable) => void, onDelete: (id: number) => void }) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: resp.id_responsable_establecimiento });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 50 : 1,
    opacity: isDragging ? 0.5 : 1,
    position: isDragging ? 'relative' as 'relative' : 'static' as 'static'
  };

  return (
    <div ref={setNodeRef} style={style} className="flex items-center justify-between p-2.5 bg-white border border-slate-200 rounded-lg shadow-sm mb-2 group hover:border-lgc-primary transition-colors">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing text-slate-400 hover:text-lgc-primary touch-none shrink-0">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" /></svg>
        </div>
        <div className="min-w-0">
          <span className="text-xs font-bold text-slate-700 block truncate">{resp.descripcion}</span>
          {resp.observacion && <span className="text-[10px] text-slate-400 block truncate">{resp.observacion}</span>}
        </div>
      </div>
      <div className="flex items-center gap-1 shrink-0 ml-2">
        <button onClick={() => onEdit(resp)} className="text-slate-300 hover:text-lgc-primary transition-colors bg-slate-50 hover:bg-blue-50 p-1.5 rounded" title="Editar responsable">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
        </button>
        <button onClick={() => onDelete(resp.id_responsable_establecimiento)} className="text-slate-300 hover:text-red-500 transition-colors bg-slate-50 hover:bg-red-50 p-1.5 rounded" title="Eliminar responsable">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>
    </div>
  );
};

// Componente para multiselect de categorías en filtros
const MultiSelectCategorias = ({ options, selected, onChange, placeholder }: any) => {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Cerrar menú al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Opciones filtradas: excluir ya seleccionadas y que coincidan con query
  const filtered = options.filter((o: any) => {
    const matchesQuery = o.descripcion?.toLowerCase().includes(query.toLowerCase());
    const alreadySelected = selected.some((s: any) => s.id_categoria === o.id_categoria);
    return matchesQuery && !alreadySelected;
  });

  const addTag = (cat: any) => {
    if (!selected.some((s: any) => s.id_categoria === cat.id_categoria)) {
      onChange([...selected, cat]);
    }
    setQuery("");        // Limpiar búsqueda
    setIsOpen(false);    // Cerrar menú
    // Mantener el foco en el input para seguir escribiendo
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const removeTag = (cat: any) => {
    onChange(selected.filter((s: any) => s.id_categoria !== cat.id_categoria));
    // Al quitar una categoría, reabrir menú si hay query o estaba abierto
    if (!isOpen) setIsOpen(true);
  };

  const handleFocus = () => {
    setIsOpen(true);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    if (!isOpen) setIsOpen(true);  // Si estaba cerrado, lo abrimos al escribir
  };

  return (
    <div className="relative w-full" ref={containerRef}>
      <div className="flex flex-wrap gap-1 mb-1.5 min-h-6.25">
        {selected.map((cat: any) => (
          <span key={cat.id_categoria} className="bg-blue-50 text-blue-700 border border-blue-200 text-[10px] px-2 py-1 rounded flex items-center gap-1 font-bold shadow-sm uppercase tracking-widest">
            {cat.descripcion}
            <button type="button" onClick={() => removeTag(cat)} className="text-blue-400 hover:text-red-500 font-bold ml-1 transition-colors text-xs">&times;</button>
          </span>
        ))}
      </div>
      <input
        ref={inputRef}
        className="w-full text-[11px] p-2 border border-slate-200 rounded outline-none focus:border-lgc-primary bg-white transition-colors"
        placeholder={selected.length === 0 ? placeholder : "+ Buscar y agregar más..."}
        value={query}
        onFocus={handleFocus}
        onChange={handleChange}
      />
      {isOpen && filtered.length > 0 && (
        <div className="absolute z-50 w-full bg-white border border-slate-200 shadow-xl rounded-lg max-h-40 overflow-y-auto mt-1">
          {filtered.map((cat: any) => (
            <div
              key={cat.id_categoria}
              className="p-2 text-[11px] hover:bg-slate-50 text-slate-700 cursor-pointer border-b last:border-0 border-slate-100"
              onMouseDown={(e) => { e.preventDefault(); addTag(cat); }}
            >
              {cat.descripcion}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default function EstablecimientosPage() {
  const { id } = useParams(); 
  const router = useRouter();
  
  const { canRead, canEdit } = usePermissions();
  const [isCheckingPerms, setIsCheckingPerms] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsCheckingPerms(false), 100);
    return () => clearTimeout(timer);
  }, []);

  const [establecimientos, setEstablecimientos] = useState<Establecimiento[]>([]);
  const [jurisdicciones, setJurisdicciones] = useState<Jurisdiccion[]>([]);
  const [tiposContacto, setTiposContacto] = useState<TipoContacto[]>([]);
  const [todasLasCategorias, setTodasLasCategorias] = useState<Categoria[]>([]); // <-- para filtros
  
  const [clienteActual, setClienteActual] = useState<{ nombre_fantasia: string, logo_path: string | null } | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  
  const [formData, setFormData] = useState({ 
    id_cliente_establecimiento: "", 
    id_jurisdiccion: "", 
    descripcion: "", 
    vigente: 1,
    contactos: [] as DatoContacto[]
  });

  // --- NUEVOS ESTADOS PARA MODAL DE CATEGORÍAS ---
  const [isCategoriasModalOpen, setIsCategoriasModalOpen] = useState(false);
  const [establecimientoSeleccionado, setEstablecimientoSeleccionado] = useState<Establecimiento | null>(null);
  const [categoriasAsignadas, setCategoriasAsignadas] = useState<Categoria[]>([]);
  const [searchCat, setSearchCat] = useState("");
  const [savingCategorias, setSavingCategorias] = useState(false);

  // --- NUEVOS ESTADOS PARA MODAL DE RESPONSABLES ---
  const [isResponsablesModalOpen, setIsResponsablesModalOpen] = useState(false);
  const [establecimientoResponsables, setEstablecimientoResponsables] = useState<Establecimiento | null>(null);
  const [responsables, setResponsables] = useState<Responsable[]>([]);
  const [loadingResponsables, setLoadingResponsables] = useState(false);
  const [savingResponsable, setSavingResponsable] = useState(false);
  const [formResponsable, setFormResponsable] = useState<{ id_responsable_establecimiento: string; descripcion: string; observacion: string; vigente: number } | null>(null);

  // --- ESTADOS DE FILTROS ---
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [filtros, setFiltros] = useState({
    descripcion: "",
    id_jurisdiccion: "",
    vigente: "todos", // "todos", "1", "0"
    categorias: [] as Categoria[] // array de objetos { id, descripcion }
  });

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  // Cargar todas las categorías globales para usar en el filtro
  const fetchCategoriasGlobales = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=categoria`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      const cats = data.registros?.map((c: any) => ({
        id_categoria: c.id_categoria || c.id,
        descripcion: c.descripcion
      })) || [];
      setTodasLasCategorias(cats);
    } catch (err) {
      console.error("Error cargando categorías globales:", err);
    }
  }, []);

  const fetchData = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) { router.push("/"); return; }

    try {
      setLoading(true);
      
      const [resEst, resJur, resTipos, resClientes] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/establecimientos/leer.php?id_cliente=${id}`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/jurisdicciones/leer.php`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=tipo_contacto`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/clientes/leer.php`, { headers: { "Authorization": `Bearer ${token}` } })
      ]);

      const [dataEst, dataJur, dataTipos, dataClientes] = await Promise.all([
        resEst.json(), resJur.json(), resTipos.json(), resClientes.json()
      ]);

      // El backend ahora devuelve categorías en cada registro
      setEstablecimientos(dataEst.registros || []);
      setJurisdicciones(dataJur.registros || []);
      setTiposContacto(dataTipos.registros || []);
      
      if (dataClientes.registros) {
        const clienteFind = dataClientes.registros.find((c: any) => c.id_cliente.toString() === id);
        if (clienteFind) {
          setClienteActual({
            nombre_fantasia: clienteFind.nombre_fantasia || clienteFind.razon_social,
            logo_path: clienteFind.logo_path
          });
        }
      }
      
    } catch (error) {
      console.error("Error al sincronizar datos:", error);
    } finally {
      setLoading(false);
    }
  }, [id, router]);

  useEffect(() => { 
    if (!isCheckingPerms && canRead("clientes")) {
      fetchData();
      fetchCategoriasGlobales();
    }
  }, [fetchData, fetchCategoriasGlobales, isCheckingPerms, canRead]);

  // Lógica de filtrado
  const establecimientosFiltrados = useMemo(() => {
    return establecimientos.filter(est => {
      // Filtro descripción
      if (filtros.descripcion.trim() !== "" && !est.descripcion.toLowerCase().includes(filtros.descripcion.toLowerCase())) return false;
      
      // Filtro jurisdicción
      if (filtros.id_jurisdiccion !== "" && est.id_jurisdiccion.toString() !== filtros.id_jurisdiccion) return false;
      
      // Filtro estado vigente
      if (filtros.vigente !== "todos" && est.vigente.toString() !== filtros.vigente) return false;
      
      // Filtro categorías (AND: todas las categorías seleccionadas deben estar presentes)
      if (filtros.categorias.length > 0) {
        const categoriasEst = est.categorias?.map(c => c.id_categoria) || [];
        const todasPresentes = filtros.categorias.every(catFiltro => 
          categoriasEst.includes(catFiltro.id_categoria)
        );
        if (!todasPresentes) return false;
      }
      
      return true;
    });
  }, [establecimientos, filtros]);

  const handleAddContacto = () => setFormData(prev => ({ ...prev, contactos: [...prev.contactos, { id_tipo_contacto: "", valor: "" }] }));
  const handleRemoveContacto = (index: number) => setFormData(prev => ({ ...prev, contactos: prev.contactos.filter((_, i) => i !== index) }));
  const handleContactoChange = (index: number, field: keyof DatoContacto, value: string) => {
    setFormData(prev => {
      const nuevosContactos = [...prev.contactos];
      nuevosContactos[index] = { ...nuevosContactos[index], [field]: value };
      return { ...prev, contactos: nuevosContactos };
    });
  };

  const getInputType = (id_tipo: string) => {
    const tipo = tiposContacto.find(t => t.id_tipo_contacto.toString() === id_tipo);
    if (!tipo) return "text";
    const desc = tipo.descripcion.toLowerCase();
    if (desc.includes("mail")) return "email";
    if (desc.includes("tel") || desc.includes("cel")) return "tel";
    if (desc.includes("web") || desc.includes("link")) return "url";
    return "text";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit("clientes")) return;

    setFormLoading(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/establecimientos/guardar.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ ...formData, id_cliente: id }) 
      });
      if (res.ok) {
        setIsModalOpen(false);
        fetchData();
      } else {
        alert("Ocurrió un error al guardar la sede.");
      }
    } catch (error) {
      console.error(error);
    } finally {
      setFormLoading(false);
    }
  };

  // --- LÓGICA DEL MODAL DE CATEGORÍAS ---
  const abrirModalCategorias = async (est: Establecimiento) => {
    setEstablecimientoSeleccionado(est);
    setIsCategoriasModalOpen(true);
    setSearchCat("");
    
    const token = localStorage.getItem("sgml_token");
    if (!token) return;

    try {
      // 1. Cargamos TODAS las categorías maestras
      const resMaestras = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=categoria`, { headers: { "Authorization": `Bearer ${token}` } });
      const dataMaestras = await resMaestras.json();
      const todas = dataMaestras.registros?.map((c:any) => ({ id_categoria: c.id_categoria || c.id, descripcion: c.descripcion })) || [];
      setTodasLasCategorias(todas); // Actualizar global también

      // 2. Cargamos las categorías ya asignadas a este establecimiento
      const resAsignadas = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/establecimientos/leer_categorias.php?id_cliente_establecimiento=${est.id_cliente_establecimiento}`, { headers: { "Authorization": `Bearer ${token}` } });
      const dataAsignadas = await resAsignadas.json();
      
      if (dataAsignadas.registros) {
        const asignadas = dataAsignadas.registros.map((c: any) => ({
          id_categoria: c.id_categoria,
          descripcion: c.descripcion
        }));
        setCategoriasAsignadas(asignadas);
      } else {
        setCategoriasAsignadas([]);
      }
    } catch (err) {
      console.error("Error al cargar categorías:", err);
    }
  };

  const handleDragEndCategorias = (event: any) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = categoriasAsignadas.findIndex(c => c.id_categoria === active.id);
      const newIndex = categoriasAsignadas.findIndex(c => c.id_categoria === over.id);
      setCategoriasAsignadas(arrayMove(categoriasAsignadas, oldIndex, newIndex));
    }
  };

  const moverADerecha = (cat: Categoria) => {
    setCategoriasAsignadas(prev => [...prev, cat]);
  };

  const moverAIzquierda = (id_cat: number) => {
    setCategoriasAsignadas(prev => prev.filter(c => c.id_categoria !== id_cat));
  };

  const moverTodasADerecha = (disponiblesFiltradas: Categoria[]) => {
    setCategoriasAsignadas(prev => [...prev, ...disponiblesFiltradas]);
  };

  const moverTodasAIzquierda = () => {
    setCategoriasAsignadas([]);
  };

  const guardarCategorias = async () => {
    setSavingCategorias(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const payload = {
        id_cliente_establecimiento: establecimientoSeleccionado?.id_cliente_establecimiento,
        categorias: categoriasAsignadas.map(c => c.id_categoria)
      };

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/establecimientos/guardar_categorias.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setIsCategoriasModalOpen(false);
        fetchData(); // Recargar para actualizar las categorías en la tabla
      } else {
        alert("Error al guardar categorías.");
      }
    } catch (error) {
      console.error(error);
    } finally {
      setSavingCategorias(false);
    }
  };

  // --- LÓGICA DEL MODAL DE RESPONSABLES ---
  const abrirModalResponsables = async (est: Establecimiento) => {
    setEstablecimientoResponsables(est);
    setIsResponsablesModalOpen(true);
    setFormResponsable(null);
    await cargarResponsables(est.id_cliente_establecimiento);
  };

  const cargarResponsables = async (id_est: number) => {
    setLoadingResponsables(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/responsables/leer_responsables.php?id_establecimiento=${id_est}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      setResponsables(data.registros || []);
    } catch (err) {
      console.error("Error al cargar responsables:", err);
    } finally {
      setLoadingResponsables(false);
    }
  };

  const handleDragEndResponsables = async (event: any) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = responsables.findIndex(r => r.id_responsable_establecimiento === active.id);
    const newIndex = responsables.findIndex(r => r.id_responsable_establecimiento === over.id);
    const reordenados = arrayMove(responsables, oldIndex, newIndex);
    setResponsables(reordenados);
    const token = localStorage.getItem("sgml_token");
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/responsables/guardar_responsable.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ accion: "reordenar", orden: reordenados.map(r => r.id_responsable_establecimiento) })
      });
    } catch (err) {
      console.error("Error al reordenar:", err);
    }
  };

  const handleEliminarResponsable = async (id: number) => {
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/responsables/guardar_responsable.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ accion: "borrar", id_responsable_establecimiento: id })
      });
      const data = await res.json();
      if (res.status === 409) {
        alert(`⚠️ ${data.mensaje}`);
      } else if (res.ok) {
        setResponsables(prev => prev.filter(r => r.id_responsable_establecimiento !== id));
      } else {
        alert("Error al eliminar el responsable.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleGuardarResponsable = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formResponsable || !establecimientoResponsables) return;
    setSavingResponsable(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const payload = {
        accion: "guardar",
        id_establecimiento: establecimientoResponsables.id_cliente_establecimiento,
        id_responsable_establecimiento: formResponsable.id_responsable_establecimiento || undefined,
        descripcion: formResponsable.descripcion,
        observacion: formResponsable.observacion,
        vigente: formResponsable.vigente
      };
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/responsables/guardar_responsable.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setFormResponsable(null);
        await cargarResponsables(establecimientoResponsables.id_cliente_establecimiento);
      } else {
        alert("Error al guardar el responsable.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSavingResponsable(false);
    }
  };

  // Limpiar filtros
  const limpiarFiltros = () => {
    setFiltros({
      descripcion: "",
      id_jurisdiccion: "",
      vigente: "todos",
      categorias: []
    });
  };

  // Verificar si hay filtros activos
  const hayFiltrosActivos = useMemo(() => {
    return filtros.descripcion !== "" ||
           filtros.id_jurisdiccion !== "" ||
           filtros.vigente !== "todos" ||
           filtros.categorias.length > 0;
  }, [filtros]);

  if (isCheckingPerms) return <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Verificando credenciales de seguridad...</div>;
  if (!canRead("clientes")) return <div className="py-32 text-center text-red-500 font-bold text-2xl">Acceso Denegado</div>;

  return (
    <div className="space-y-6 font-sans animate-fade-in">
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="text-slate-400 hover:text-lgc-primary transition-colors text-sm font-bold uppercase tracking-widest flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          Volver a Clientes
        </button>
      </div>

      {/* HEADER CON FONDO PRINCIPAL */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-lgc-primary p-6 rounded-2xl shadow-lg gap-4">
        <div className="flex items-center gap-4">
          {clienteActual?.logo_path ? (
            <div className="w-14 h-14 rounded-xl border border-slate-200 bg-white flex items-center justify-center overflow-hidden shrink-0 shadow-sm">
              <img src={`${process.env.NEXT_PUBLIC_IMG_URL}/${clienteActual.logo_path}`} alt="Logo" className="w-full h-full object-contain p-1" />
            </div>
          ) : (
            <div className="w-14 h-14 rounded-xl border border-slate-200 bg-white flex items-center justify-center shrink-0 shadow-sm">
              <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
            </div>
          )}
          <div>
            <h1 className="text-2xl font-heading text-white uppercase tracking-tight flex items-center gap-2">
              ESTABLECIMIENTOS
              <span className="bg-white/20 text-white px-3 py-0.5 rounded-full text-sm font-normal tracking-normal">
                {establecimientosFiltrados.length}
              </span>
            </h1>
            <p className="text-white/70 text-sm mt-0.5">
              Gestionando sedes de <strong className="text-white font-bold uppercase tracking-widest text-[10px] bg-white/20 px-2 py-1 rounded ml-1">{clienteActual?.nombre_fantasia || `Cliente #${id}`}</strong>
            </p>
          </div>
        </div>
        
        {canEdit("clientes") && (
          <button 
              onClick={() => { 
                setFormData({id_cliente_establecimiento: "", id_jurisdiccion: "", descripcion: "", vigente: 1, contactos: []}); 
                setIsModalOpen(true); 
              }}
              className="bg-white text-lgc-primary py-2.5 px-6 rounded-lg font-bold text-xs uppercase tracking-widest hover:bg-white/70 hover:text-lgc-primary transition-all shadow-md shrink-0 flex items-center gap-2"
          >
            <span>+</span> Agregar Establecimiento
          </button>
        )}
      </div>

      {/* SECCIÓN DE FILTROS PLEGABLE */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <button
          onClick={() => setIsFilterOpen(!isFilterOpen)}
          className="w-full flex items-center justify-between p-4 bg-slate-50 hover:bg-slate-100 transition-colors"
        >
          <div className="flex items-center gap-3">
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
            <span className="font-bold uppercase text-xs tracking-widest text-slate-600">Filtros de búsqueda</span>
            {hayFiltrosActivos && (
              <span className="bg-lgc-accent text-white px-2 py-0.5 rounded text-[10px] font-bold uppercase shadow-sm">Activo</span>
            )}
          </div>
          <svg className={`w-5 h-5 text-slate-400 transform transition-transform ${isFilterOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
        </button>

        {isFilterOpen && (
          <div className="p-5 border-t border-slate-200 bg-white space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Filtro descripción */}
              <div>
                <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Descripción</label>
                <input
                  type="text"
                  className="w-full text-[11px] p-2 border border-slate-200 rounded outline-none focus:border-lgc-primary"
                  placeholder="Nombre o descripción..."
                  value={filtros.descripcion}
                  onChange={e => setFiltros({...filtros, descripcion: e.target.value})}
                />
              </div>

              {/* Filtro jurisdicción */}
              <div>
                <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Jurisdicción</label>
                <select
                  className="w-full text-[11px] p-2 border border-slate-200 rounded outline-none bg-white cursor-pointer"
                  value={filtros.id_jurisdiccion}
                  onChange={e => setFiltros({...filtros, id_jurisdiccion: e.target.value})}
                >
                  <option value="">Todas</option>
                  {jurisdicciones.map(j => (
                    <option key={j.id_jurisdiccion} value={j.id_jurisdiccion}>{j.descripcion}</option>
                  ))}
                </select>
              </div>

              {/* Filtro estado */}
              <div>
                <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Estado</label>
                <select
                  className="w-full text-[11px] p-2 border border-slate-200 rounded outline-none bg-white cursor-pointer"
                  value={filtros.vigente}
                  onChange={e => setFiltros({...filtros, vigente: e.target.value})}
                >
                  <option value="todos">Todos</option>
                  <option value="1">Activos</option>
                  <option value="0">Inactivos</option>
                </select>
              </div>

              {/* Filtro categorías (multiselect) */}
              <div className="lg:col-span-2">
                <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Categorías (todas deben coincidir)</label>
                <MultiSelectCategorias
                  options={todasLasCategorias}
                  selected={filtros.categorias}
                  onChange={(cats: Categoria[]) => setFiltros({...filtros, categorias: cats})}
                  placeholder="Seleccionar categorías..."
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={limpiarFiltros}
                className="text-[10px] font-bold uppercase tracking-widest text-slate-400 hover:text-slate-600 px-4 py-2 bg-slate-100 rounded border border-slate-200 transition-colors"
              >
                Limpiar filtros
              </button>
            </div>
          </div>
        )}
      </div>

      {loading ? (
        <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Cargando establecimientos...</div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-lgc-primary text-[10px] uppercase tracking-[0.2em] text-white font-bold">
              <tr>
                <th className="p-5">Descripción de la Planta/Sede</th>
                <th className="p-5">Jurisdicción</th>
                <th className="p-5">Categorías</th>
                <th className="p-5">Estado</th>
                <th className="p-5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {establecimientosFiltrados.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-10 text-center text-slate-400 italic">No hay establecimientos que coincidan con los filtros.</td>
                </tr>
              ) : (
                establecimientosFiltrados.map(est => (
                  <tr key={est.id_cliente_establecimiento} className="hover:bg-slate-50/50 transition-colors group">
                    <td className="p-5 font-bold text-slate-700 text-sm">{est.descripcion}</td>
                    <td className="p-5 text-xs text-slate-500 font-medium uppercase tracking-widest">{est.jurisdiccion_nombre}</td>
                    <td className="p-5">
                      <div className="flex flex-wrap gap-1.5">
                        {est.categorias && est.categorias.length > 0 ? (
                          est.categorias.slice(0, 3).map(cat => (
                            <span key={cat.id_categoria} className="bg-blue-50 text-blue-700 border border-blue-200 text-[9px] font-bold px-2 py-0.5 rounded-full shadow-sm uppercase tracking-wider">
                              {cat.descripcion}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-slate-400 italic">—</span>
                        )}
                        {est.categorias && est.categorias.length > 3 && (
                          <span className="bg-slate-100 text-slate-600 border border-slate-200 text-[9px] font-bold px-2 py-0.5 rounded-full shadow-sm">
                            +{est.categorias.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="p-5">
                        <span className={`px-2.5 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest border ${est.vigente ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
                            {est.vigente ? 'OPERATIVO' : 'INACTIVO'}
                        </span>
                     </td>
                    <td className="p-5 text-right">
                      {canEdit("clientes") ? (
                        <div className="flex justify-end gap-2">
                          <button 
                            onClick={() => abrirModalCategorias(est)}
                            className="text-slate-400 hover:text-lgc-primary bg-white border border-slate-200 p-2 rounded transition-all shadow-sm flex items-center gap-2"
                            title="Asignar Categorías y Rubros"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
                          </button>
                          <button
                            onClick={() => abrirModalResponsables(est)}
                            className="text-slate-400 hover:text-lgc-primary bg-white border border-slate-200 p-2 rounded transition-all shadow-sm flex items-center gap-2"
                            title="Gestionar Responsables"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                          </button>
                          <button 
                            onClick={() => { 
                              setFormData({
                                id_cliente_establecimiento: est.id_cliente_establecimiento.toString(),
                                descripcion: est.descripcion,
                                id_jurisdiccion: est.id_jurisdiccion.toString(),
                                vigente: est.vigente,
                                contactos: est.contactos || [] 
                              }); 
                              setIsModalOpen(true); 
                            }}
                            className="text-slate-400 hover:text-lgc-primary bg-white border border-slate-200 p-2 rounded transition-all shadow-sm"
                            title="Editar Sede"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                          </button>
                        </div>
                      ) : (
                        <span className="text-slate-300 text-[10px] font-bold uppercase tracking-widest cursor-not-allowed">Solo Lectura</span>
                      )}
                     </td>
                   </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* --- MODAL ESTÁNDAR DE EDICIÓN DE ESTABLECIMIENTO (sin cambios) --- */}
      {isModalOpen && canEdit("clientes") && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden my-8 border border-slate-200">
            <div className="p-6 bg-slate-50 border-b flex justify-between items-center sticky top-0 z-10">
              <h2 className="text-xl font-heading text-lgc-primary uppercase tracking-tight">
                {formData.id_cliente_establecimiento ? "Editar Sede" : "Nueva Sede Operativa"}
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-2xl">&times;</button>
            </div>

            <form onSubmit={handleSubmit} className="p-8 space-y-6">
              
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b pb-2 mb-4">Datos Operativos</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="md:col-span-2">
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Nombre / Descripción de la Sede *</label>
                    <input required className="w-full p-3 bg-slate-50 border rounded-lg outline-none focus:border-lgc-primary focus:ring-2 focus:ring-lgc-primary text-sm" placeholder="Ej: Planta Industrial Pilar" value={formData.descripcion} onChange={e => setFormData({...formData, descripcion: e.target.value})} />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Jurisdicción Aplicable *</label>
                    <select required className="w-full p-3 bg-slate-50 border rounded-lg outline-none focus:border-lgc-primary focus:ring-2 focus:ring-lgc-primary text-sm cursor-pointer" value={formData.id_jurisdiccion} onChange={e => setFormData({...formData, id_jurisdiccion: e.target.value})}>
                      <option value="">Seleccione...</option>
                      {jurisdicciones.map(j => (
                        <option key={j.id_jurisdiccion} value={j.id_jurisdiccion}>{j.descripcion}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Estado *</label>
                    <select className="w-full p-3 bg-slate-50 border rounded-lg outline-none focus:border-lgc-primary focus:ring-2 focus:ring-lgc-primary text-sm cursor-pointer" value={formData.vigente} onChange={e => setFormData({...formData, vigente: parseInt(e.target.value)})}>
                      <option value={1}>OPERATIVO</option>
                      <option value={0}>INACTIVO</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center border-b pb-2 mb-4">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Contacto Directo de Sede</h3>
                  <button type="button" onClick={handleAddContacto} className="text-[10px] text-lgc-primary font-bold uppercase tracking-widest hover:text-lgc-accent transition-colors">+ Agregar Medio</button>
                </div>
                
                <div className="space-y-3 max-h-48 overflow-y-auto pr-2">
                  {formData.contactos.length === 0 ? (
                    <p className="text-sm text-slate-400 italic text-center py-4 bg-slate-50 rounded-lg border border-dashed">No hay contactos registrados en esta sede.</p>
                  ) : (
                    formData.contactos.map((contacto, index) => (
                      <div key={index} className="flex gap-3 items-start animate-fade-in">
                        <select required className="w-1/3 p-3 text-sm bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none cursor-pointer" value={contacto.id_tipo_contacto} onChange={(e) => handleContactoChange(index, 'id_tipo_contacto', e.target.value)}>
                          <option value="">Tipo...</option>
                          {tiposContacto.map(tipo => (
                            <option key={tipo.id_tipo_contacto} value={tipo.id_tipo_contacto}>{tipo.descripcion}</option>
                          ))}
                        </select>
                        
                        <input required type={getInputType(contacto.id_tipo_contacto)} placeholder="Valor..." className="grow p-3 text-sm bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none" value={contacto.valor} onChange={(e) => handleContactoChange(index, 'valor', e.target.value)} />
                        
                        <button type="button" onClick={() => handleRemoveContacto(index)} className="p-3 text-red-400 hover:text-white hover:bg-red-500 rounded-lg transition-colors shrink-0" title="Eliminar contacto">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="flex gap-4 pt-6 mt-6 border-t border-slate-100">
                <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 py-3 text-xs uppercase tracking-widest font-bold text-slate-400 hover:text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">Cancelar</button>
                <button type="submit" disabled={formLoading} className="flex-1 bg-lgc-primary text-white py-3 rounded-lg font-bold text-xs uppercase tracking-widest shadow-md hover:bg-lgc-accent transition-all">
                  {formLoading ? 'Guardando...' : 'Guardar Sede'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- MODAL ASIGNACIÓN DE CATEGORÍAS (sin cambios) --- */}
      {isCategoriasModalOpen && establecimientoSeleccionado && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden border border-slate-200 flex flex-col max-h-[90vh]">
            <div className="p-6 bg-slate-50 border-b flex justify-between items-center shrink-0">
              <div>
                <h2 className="text-xl font-heading text-lgc-primary uppercase tracking-tight flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
                  Categorización de Sede
                </h2>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">
                  Definiendo perfil normativo para: <span className="text-slate-600">{establecimientoSeleccionado.descripcion}</span>
                </p>
              </div>
              <button onClick={() => setIsCategoriasModalOpen(false)} className="text-slate-400 hover:text-red-500 text-2xl transition-colors">&times;</button>
            </div>

            <div className="p-6 flex-1 overflow-hidden flex flex-col md:flex-row gap-6 bg-white min-h-100">
              
              {/* PANEL IZQUIERDO: DISPONIBLES */}
              <div className="flex-1 flex flex-col border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                <div className="bg-slate-50 p-3 border-b border-slate-200 flex flex-col gap-2">
                  <div className="flex justify-between items-center">
                    <h3 className="text-[10px] font-bold uppercase text-slate-500 tracking-widest">Categorías Disponibles</h3>
                    <span className="bg-slate-200 text-slate-600 text-[10px] font-bold px-2 py-0.5 rounded">{todasLasCategorias.filter(c => !categoriasAsignadas.some(as => as.id_categoria === c.id_categoria)).length}</span>
                  </div>
                  <input 
                    type="text" 
                    placeholder="Buscar rubro o categoría..." 
                    value={searchCat}
                    onChange={e => setSearchCat(e.target.value)}
                    className="w-full text-xs p-2 border border-slate-300 rounded outline-none focus:border-lgc-primary bg-white"
                  />
                </div>
                <div className="flex-1 overflow-y-auto p-2 bg-slate-50/50">
                  {todasLasCategorias.filter(c => !categoriasAsignadas.some(as => as.id_categoria === c.id_categoria) && c.descripcion.toLowerCase().includes(searchCat.toLowerCase())).length === 0 ? (
                    <div className="text-center text-xs text-slate-400 italic p-6">No hay categorías que coincidan.</div>
                  ) : (
                    todasLasCategorias.filter(c => !categoriasAsignadas.some(as => as.id_categoria === c.id_categoria) && c.descripcion.toLowerCase().includes(searchCat.toLowerCase())).map(cat => (
                      <button 
                        key={cat.id_categoria} 
                        onClick={() => moverADerecha(cat)}
                        className="w-full text-left p-2.5 bg-white border border-slate-200 rounded-lg hover:border-lgc-primary hover:text-lgc-primary transition-all text-xs font-bold text-slate-600 flex justify-between items-center group mb-2 shadow-sm"
                      >
                        {cat.descripcion}
                        <svg className="w-4 h-4 text-slate-300 group-hover:text-lgc-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                      </button>
                    ))
                  )}
                </div>
              </div>

              {/* BOTONERA CENTRAL */}
              <div className="flex md:flex-col justify-center gap-3 shrink-0 py-4">
                 <button 
                   onClick={() => moverTodasADerecha(todasLasCategorias.filter(c => !categoriasAsignadas.some(as => as.id_categoria === c.id_categoria) && c.descripcion.toLowerCase().includes(searchCat.toLowerCase())))} 
                   disabled={todasLasCategorias.filter(c => !categoriasAsignadas.some(as => as.id_categoria === c.id_categoria) && c.descripcion.toLowerCase().includes(searchCat.toLowerCase())).length === 0}
                   className="bg-slate-100 hover:bg-lgc-primary hover:text-white text-slate-500 p-2 rounded-lg transition-colors disabled:opacity-30 border border-slate-200 shadow-sm"
                   title="Mover todas a la derecha"
                 >
                   <svg className="w-5 h-5 hidden md:block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" /></svg>
                   <svg className="w-5 h-5 md:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 13l-7 7-7-7m14-8l-7 7-7-7" /></svg>
                 </button>
                 <button 
                   onClick={moverTodasAIzquierda} 
                   disabled={categoriasAsignadas.length === 0}
                   className="bg-slate-100 hover:bg-red-500 hover:text-white text-slate-500 p-2 rounded-lg transition-colors disabled:opacity-30 border border-slate-200 shadow-sm"
                   title="Quitar todas"
                 >
                   <svg className="w-5 h-5 hidden md:block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" /></svg>
                   <svg className="w-5 h-5 md:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 11l7-7 7 7M5 19l7-7 7 7" /></svg>
                 </button>
              </div>

              {/* PANEL DERECHO: ASIGNADAS (SORTABLE) */}
              <div className="flex-1 flex flex-col border border-lgc-primary/30 rounded-xl overflow-hidden shadow-sm bg-lgc-primary/5">
                <div className="bg-white p-3 border-b border-lgc-primary/20">
                  <div className="flex justify-between items-center mb-1">
                    <h3 className="text-[10px] font-bold uppercase text-lgc-primary tracking-widest">Asignadas a la Sede</h3>
                    <span className="bg-lgc-primary text-white text-[10px] font-bold px-2 py-0.5 rounded">{categoriasAsignadas.length}</span>
                  </div>
                  <p className="text-[9px] text-slate-500 uppercase tracking-widest">Arrastrá para ordenar por prioridad</p>
                </div>
                <div className="flex-1 overflow-y-auto p-2">
                  {categoriasAsignadas.length === 0 ? (
                    <div className="text-center text-xs text-slate-400 italic p-6 flex flex-col items-center gap-2">
                      <svg className="w-8 h-8 text-slate-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
                      Seleccioná categorías del panel izquierdo.
                    </div>
                  ) : (
                    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEndCategorias}>
                      <SortableContext items={categoriasAsignadas.map(c => c.id_categoria)} strategy={verticalListSortingStrategy}>
                        {categoriasAsignadas.map(cat => (
                           <SortableCategoriaItem key={cat.id_categoria} cat={cat} onRemove={moverAIzquierda} />
                        ))}
                      </SortableContext>
                    </DndContext>
                  )}
                </div>
              </div>
            </div>

            {/* PIE DEL MODAL */}
            <div className="p-5 border-t border-slate-100 bg-slate-50 flex justify-end gap-4 shrink-0">
               <button onClick={() => setIsCategoriasModalOpen(false)} className="px-6 py-2.5 text-xs uppercase font-bold text-slate-500 bg-white border border-slate-200 hover:bg-slate-100 transition-colors rounded-lg">
                 Cancelar
               </button>
               <button onClick={guardarCategorias} disabled={savingCategorias} className="px-8 py-2.5 bg-lgc-primary hover:bg-lgc-accent text-white font-bold rounded-lg uppercase text-xs shadow-md disabled:opacity-50 flex items-center gap-2 transition-colors">
                 {savingCategorias ? (
                   <><svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Guardando...</>
                 ) : (
                   <><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg> Guardar Categorización</>
                 )}
               </button>
            </div>
          </div>
        </div>
      )}

      {/* --- MODAL GESTIÓN DE RESPONSABLES (sin cambios) --- */}
      {isResponsablesModalOpen && establecimientoResponsables && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden border border-slate-200 flex flex-col max-h-[90vh]">

            {/* CABECERA */}
            <div className="p-6 bg-slate-50 border-b flex justify-between items-center shrink-0">
              <div>
                <h2 className="text-xl font-heading text-lgc-primary uppercase tracking-tight flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                  Responsables de Sede
                </h2>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">
                  Sede: <span className="text-slate-600">{establecimientoResponsables.descripcion}</span>
                </p>
              </div>
              <button onClick={() => { setIsResponsablesModalOpen(false); setFormResponsable(null); }} className="text-slate-400 hover:text-red-500 text-2xl transition-colors">&times;</button>
            </div>

            {/* CUERPO */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-white">

              {/* FORMULARIO INLINE PARA CREAR / EDITAR */}
              {formResponsable !== null ? (
                <form onSubmit={handleGuardarResponsable} className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4 animate-fade-in">
                  <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b pb-2">
                    {formResponsable.id_responsable_establecimiento ? "Editar Responsable" : "Nuevo Responsable"}
                  </h3>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Nombre / Cargo *</label>
                    <input
                      required
                      className="w-full p-3 bg-white border rounded-lg outline-none focus:border-lgc-primary focus:ring-2 focus:ring-lgc-primary text-sm"
                      placeholder="Ej: Gerencia de Sistemas"
                      value={formResponsable.descripcion}
                      onChange={e => setFormResponsable(prev => prev ? { ...prev, descripcion: e.target.value } : prev)}
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Observación</label>
                    <input
                      className="w-full p-3 bg-white border rounded-lg outline-none focus:border-lgc-primary focus:ring-2 focus:ring-lgc-primary text-sm"
                      placeholder="Información adicional (opcional)"
                      value={formResponsable.observacion}
                      onChange={e => setFormResponsable(prev => prev ? { ...prev, observacion: e.target.value } : prev)}
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Estado</label>
                    <select
                      className="w-full p-3 bg-white border rounded-lg outline-none focus:border-lgc-primary text-sm cursor-pointer"
                      value={formResponsable.vigente}
                      onChange={e => setFormResponsable(prev => prev ? { ...prev, vigente: parseInt(e.target.value) } : prev)}
                    >
                      <option value={1}>ACTIVO</option>
                      <option value={0}>INACTIVO</option>
                    </select>
                  </div>
                  <div className="flex gap-3 pt-2">
                    <button type="button" onClick={() => setFormResponsable(null)} className="flex-1 py-2.5 text-xs uppercase tracking-widest font-bold text-slate-400 hover:text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors">
                      Cancelar
                    </button>
                    <button type="submit" disabled={savingResponsable} className="flex-1 bg-lgc-primary text-white py-2.5 rounded-lg font-bold text-xs uppercase tracking-widest shadow-md hover:bg-lgc-accent transition-all disabled:opacity-50">
                      {savingResponsable ? 'Guardando...' : 'Guardar Responsable'}
                    </button>
                  </div>
                </form>
              ) : (
                <button
                  onClick={() => setFormResponsable({ id_responsable_establecimiento: "", descripcion: "", observacion: "", vigente: 1 })}
                  className="w-full py-2.5 border border-dashed border-slate-300 rounded-xl text-xs font-bold uppercase tracking-widest text-slate-400 hover:text-lgc-primary hover:border-lgc-primary transition-colors flex items-center justify-center gap-2"
                >
                  <span className="text-lg leading-none">+</span> Agregar Responsable
                </button>
              )}

              {/* LISTA ORDENABLE */}
              <div>
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-[10px] font-bold uppercase text-slate-500 tracking-widest">Responsables Asignados</h3>
                  <span className="bg-lgc-primary text-white text-[10px] font-bold px-2 py-0.5 rounded">{responsables.length}</span>
                </div>
                {loadingResponsables ? (
                  <div className="py-8 text-center text-lgc-primary font-heading text-sm animate-pulse">Cargando...</div>
                ) : responsables.length === 0 ? (
                  <div className="py-8 text-center text-xs text-slate-400 italic border border-dashed border-slate-200 rounded-xl">
                    No hay responsables registrados para esta sede.
                  </div>
                ) : (
                  <>
                    <p className="text-[9px] text-slate-400 uppercase tracking-widest mb-2">Arrastrá para ordenar por prioridad</p>
                    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEndResponsables}>
                      <SortableContext items={responsables.map(r => r.id_responsable_establecimiento)} strategy={verticalListSortingStrategy}>
                        {responsables.map(resp => (
                          <SortableResponsableItem
                            key={resp.id_responsable_establecimiento}
                            resp={resp}
                            onEdit={(r) => setFormResponsable({ id_responsable_establecimiento: r.id_responsable_establecimiento.toString(), descripcion: r.descripcion, observacion: r.observacion || "", vigente: r.vigente })}
                            onDelete={handleEliminarResponsable}
                          />
                        ))}
                      </SortableContext>
                    </DndContext>
                  </>
                )}
              </div>
            </div>

            {/* PIE DEL MODAL */}
            <div className="p-5 border-t border-slate-100 bg-slate-50 flex justify-end shrink-0">
              <button onClick={() => { setIsResponsablesModalOpen(false); setFormResponsable(null); }} className="px-8 py-2.5 bg-lgc-primary hover:bg-lgc-accent text-white font-bold rounded-lg uppercase text-xs shadow-md transition-colors">
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}