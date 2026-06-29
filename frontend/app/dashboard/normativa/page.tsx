"use client";

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { usePermissions } from "../../hooks/usePermissions";
import Link from "next/link";
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useToast } from "../../providers/ToastProvider";
import { useConfirm } from "../../providers/ConfirmProvider";

interface Norma {
  id_norma: number;
  numero: string;
  anio: number;
  fecha_publicacion: string;
  sintesis: string;
  url_norma: string;
  origen_carga: string;
  id_tipo_norma: number;
  tipo_norma_desc: string;
  id_emisor_norma: number;
  emisor_desc: string;
  id_estado_norma: number;
  estado_desc: string;
  nivel_jurisdiccion_desc?: string;
  jurisdiccion_desc?: string;
  categorias?: string[];
}

interface Diccionario {
  id: string | number;
  descripcion: string;
}

interface Categoria {
  id_categoria: number;
  descripcion: string;
}

// --- NANO-COMPONENTES PARA FILTROS AVANZADOS (exactamente como estaban) ---
const SearchableSelect = ({ options, value, onChange, placeholder }: any) => {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (value) {
      const selected = options.find((o: any) => o.id === value);
      if (selected) setQuery(selected.descripcion);
      else setQuery("");
    } else {
      setQuery("");
    }
  }, [value, options]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filtered = options.filter((o: any) => 
    o.descripcion?.toLowerCase().includes(query.toLowerCase())
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    onChange("");
    if (!isOpen) setIsOpen(true);
  };

  const selectOption = (id: number | string, desc: string) => {
    setQuery(desc);
    onChange(id);
    setIsOpen(false);
    inputRef.current?.focus();
  };

  return (
    <div className="relative w-full" ref={containerRef}>
      <input
        ref={inputRef}
        className="w-full text-[11px] p-2.5 border border-slate-200 rounded-lg outline-none focus:border-lgc-primary bg-slate-50 hover:bg-white transition-colors"
        placeholder={placeholder}
        value={query}
        onFocus={() => setIsOpen(true)}
        onChange={handleChange}
      />
      {isOpen && filtered.length > 0 && (
        <div className="absolute z-50 w-full bg-white border border-slate-200 shadow-xl rounded-lg max-h-40 overflow-y-auto mt-1">
          {filtered.map((o: any) => (
            <div 
              key={o.id} 
              className="p-2 text-[11px] hover:bg-slate-50 text-slate-700 cursor-pointer border-b last:border-0 border-slate-100" 
              onMouseDown={(e) => { e.preventDefault(); selectOption(o.id, o.descripcion); }}
            >
              {o.descripcion}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const MultiSelectCategorias = ({ options, selected, onChange, placeholder }: any) => {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filtered = options.filter((o: any) => 
    o.descripcion?.toLowerCase().includes(query.toLowerCase()) &&
    !selected.includes(o.descripcion)
  );

  const addTag = (desc: string) => {
    if (!selected.includes(desc)) {
      onChange([...selected, desc]);
    }
    setQuery("");
    setIsOpen(false);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const removeTag = (desc: string) => {
    onChange(selected.filter((t: string) => t !== desc));
    if (!isOpen) setIsOpen(true);
  };

  const handleFocus = () => {
    setIsOpen(true);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    if (!isOpen) setIsOpen(true);
  };

  return (
    <div className="relative w-full" ref={containerRef}>
      <div className="flex flex-wrap gap-1 mb-1.5 min-h-6.25px">
        {selected.map((tag: string, idx: number) => (
          <span key={idx} className="bg-blue-50 text-blue-700 border border-blue-200 text-[10px] px-2 py-1 rounded flex items-center gap-1 font-bold shadow-sm uppercase tracking-widest">
            {tag}
            <button type="button" onClick={() => removeTag(tag)} className="text-blue-400 hover:text-red-500 font-bold ml-1 transition-colors text-xs">
              &times;
            </button>
          </span>
        ))}
      </div>
      <input
        ref={inputRef}
        className="w-full text-[11px] p-2.5 border border-slate-200 rounded-lg outline-none focus:border-lgc-primary bg-slate-50 hover:bg-white transition-colors"
        placeholder={selected.length === 0 ? placeholder : "+ Buscar y agregar más..."}
        value={query}
        onFocus={handleFocus}
        onChange={handleChange}
      />
      {isOpen && filtered.length > 0 && (
        <div className="absolute z-50 w-full bg-white border border-slate-200 shadow-xl rounded-lg max-h-40 overflow-y-auto mt-1">
          {filtered.map((o: any) => (
            <div 
              key={o.id} 
              className="p-2 text-[11px] hover:bg-slate-50 text-slate-700 cursor-pointer border-b last:border-0 border-slate-100" 
              onMouseDown={(e) => { e.preventDefault(); addTag(o.descripcion); }}
            >
              {o.descripcion}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

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
    <div ref={setNodeRef} style={style} className="flex items-center justify-between p-2.5 bg-white border border-slate-200 rounded-lg shadow-sm mb-2 group hover:border-lgc-primary transition-colors animate-fade-in">
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

// --- COMPONENTE PRINCIPAL ---
export default function NormativaOficialPage() {
  const { canRead, canEdit } = usePermissions();
  const toast = useToast();
  const confirm = useConfirm();
  const [isCheckingPerms, setIsCheckingPerms] = useState(true);

  // --- ESTADOS (TODOS LOS QUE TENÍAS) ---
  const [normas, setNormas] = useState<Norma[]>([]);
  const [tipos, setTipos] = useState<Diccionario[]>([]);
  const [emisores, setEmisores] = useState<Diccionario[]>([]);
  const [niveles, setNiveles] = useState<Diccionario[]>([]);
  const [estados, setEstados] = useState<Diccionario[]>([]);
  const [categoriasGlobales, setCategoriasGlobales] = useState<Diccionario[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  
  const [searchTerm, setSearchTerm] = useState("");
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [filtros, setFiltros] = useState({
    tipo: '', 
    nro: '', 
    anio: '', 
    sintesis: '', 
    emisor: '',        
    id_emisor: '',     
    nivel: '', 
    jurisdiccion: '', 
    categorias: [] as string[]
  });

  // Paginación (nuevo)
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const pageSizeOptions = [10, 30, 50, 100];
  const [totalItems, setTotalItems] = useState(0);

  const defaultForm = {
    id_norma: "",
    id_tipo_norma: "",
    id_emisor_norma: "",
    numero: "",
    anio: new Date().getFullYear(),
    fecha_publicacion: "",
    sintesis: "",
    url_norma: "",
    id_estado_norma: "1", 
    origen_carga: "Manual"
  };

  const [formData, setFormData] = useState(defaultForm);

  const [isCategoriasModalOpen, setIsCategoriasModalOpen] = useState(false);
  const [normaSeleccionada, setNormaSeleccionada] = useState<Norma | null>(null);
  const [todasLasCategorias, setTodasLasCategorias] = useState<Categoria[]>([]);
  const [categoriasAsignadas, setCategoriasAsignadas] = useState<Categoria[]>([]);
  const [searchCat, setSearchCat] = useState("");
  const [savingCategorias, setSavingCategorias] = useState(false);

  // Flechas flotantes (nuevo)
  const mainContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  // --- EFECTO INICIAL (igual que antes) ---
  useEffect(() => {
    const timer = setTimeout(() => setIsCheckingPerms(false), 100);
    return () => clearTimeout(timer);
  }, []);

  // --- Carga de diccionarios (igual) ---
  const fetchDiccionarios = useCallback(async (token: string) => {
    try {
      const [resTipos, resEmisores, resEstados, resCat, resNiveles] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=tipo_norma`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=emisor_norma`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=estado_norma`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=categoria`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=nivel_jurisdiccion`, { headers: { "Authorization": `Bearer ${token}` } })
      ]);

      if (!resTipos.ok || !resEmisores.ok || !resEstados.ok || !resCat.ok || !resNiveles.ok) {
        throw new Error("Error al obtener datos de maestras");
      }

      const [dataTipos, dataEmisores, dataEstados, dataCat, dataNiveles] = await Promise.all([
        resTipos.json(), resEmisores.json(), resEstados.json(), resCat.json(), resNiveles.json()
      ]);

      setTipos(dataTipos.registros?.map((e:any) => ({ id: e.id_tipo_norma || e.id, descripcion: e.descripcion })) || []);
      setEmisores(dataEmisores.registros?.map((e:any) => ({ id: e.id_emisor_norma || e.id, descripcion: e.descripcion })) || []);
      setEstados(dataEstados.registros?.map((e:any) => ({ id: e.id_estado_norma || e.id, descripcion: e.descripcion })) || []);
      setCategoriasGlobales(dataCat.registros?.map((c:any) => ({ id: c.id_categoria || c.id, descripcion: c.descripcion })) || []);
      setNiveles(dataNiveles.registros?.map((e:any) => ({ id: e.id_nivel_jurisdiccion || e.id, descripcion: e.descripcion })) || []);
    } catch (err) {
      console.error("Error cargando diccionarios", err);
      toast.showToast("Error", "No se pudieron cargar los diccionarios.", "error");
    }
  }, [toast]);

  // --- CARGA DE DATOS CON PAGINACIÓN SERVER-SIDE (NUEVO) ---
  const fetchData = useCallback(async (page?: number, limit?: number) => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return;

    const p = page || currentPage;
    const l = limit || pageSize;

    try {
      setLoading(true);
      if (tipos.length === 0) await fetchDiccionarios(token);

      const params = new URLSearchParams();
      params.append('page', String(p));
      params.append('limit', String(l));
      if (searchTerm) params.append('buscar', searchTerm);
      if (filtros.tipo) params.append('tipo', filtros.tipo);
      if (filtros.nro) params.append('nro', filtros.nro);
      if (filtros.anio) params.append('anio', filtros.anio);
      if (filtros.sintesis) params.append('sintesis', filtros.sintesis);
      if (filtros.id_emisor) params.append('id_emisor', filtros.id_emisor);
      if (filtros.nivel) params.append('nivel', filtros.nivel);
      if (filtros.jurisdiccion) params.append('jurisdiccion', filtros.jurisdiccion);
      if (filtros.categorias.length > 0) {
        for (const cat of filtros.categorias) {
          const catObj = categoriasGlobales.find(c => c.descripcion === cat);
          if (catObj) params.append('categorias[]', String(catObj.id));
        }
      }

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/normativa/leer.php?${params.toString()}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Error al obtener normas");
      const data = await res.json();
      setNormas(data.registros || []);
      setTotalItems(data.total || 0);
    } catch (err) {
      console.error("Error cargando normas", err);
      toast.showToast("Error", "No se pudieron cargar las normas.", "error");
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, searchTerm, filtros, fetchDiccionarios, toast, tipos.length, categoriasGlobales]);

  // --- EFECTOS PARA CARGAR AL INICIAR Y CUANDO CAMBIAN FILTROS (actualizados) ---
  useEffect(() => {
    if (!isCheckingPerms && canRead("normativa")) {
      fetchData(1, pageSize);
    }
  }, [isCheckingPerms, canRead]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isCheckingPerms && canRead("normativa")) {
      setCurrentPage(1);
      fetchData(1, pageSize);
    }
  }, [searchTerm, filtros, pageSize]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isCheckingPerms && canRead("normativa") && currentPage > 1) {
      fetchData(currentPage, pageSize);
    }
  }, [currentPage]); // eslint-disable-line react-hooks/exhaustive-deps

  // --- EFECTO PARA SCROLL (nuevo, mejorado) ---
  useEffect(() => {
    const container = mainContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const scrollTop = container.scrollTop;
      const scrollHeight = container.scrollHeight;
      const clientHeight = container.clientHeight;
      setShowScrollTop(scrollTop > 50);
      setShowScrollBottom(scrollTop + clientHeight < scrollHeight - 50);
    };

    container.addEventListener('scroll', handleScroll);
    // También calcular al cargar y al redimensionar
    window.addEventListener('resize', handleScroll);
    // Ejecutar una vez al montar
    const timer = setTimeout(handleScroll, 200);
    return () => {
      container.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleScroll);
      clearTimeout(timer);
    };
  }, [normas, loading]);

  const scrollToTop = () => { mainContainerRef.current?.scrollTo({ top: 0, behavior: 'smooth' }); };
  const scrollToBottom = () => { const container = mainContainerRef.current; if (container) container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' }); };

  // --- TODAS LAS FUNCIONES DE MODALES Y MANEJADORES (exactamente como estaban) ---
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit("normativa")) return;
    setFormLoading(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/normativa/guardar.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setIsModalOpen(false);
        fetchData(currentPage, pageSize);
        toast.showToast("Éxito", "Norma guardada correctamente.", "success");
      } else {
        const data = await res.json();
        toast.showToast("Error", data.mensaje || "Error al guardar la normativa.", "error");
      }
    } catch (error) {
      console.error(error);
      toast.showToast("Error", "Error de conexión al guardar.", "error");
    } finally {
      setFormLoading(false);
    }
  };

  const abrirModalCategorias = async (norma: Norma) => {
    setNormaSeleccionada(norma);
    setIsCategoriasModalOpen(true);
    setSearchCat("");
    const token = localStorage.getItem("sgml_token");
    if (!token) return;
    try {
      const resMaestras = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=categoria`, { headers: { "Authorization": `Bearer ${token}` } });
      const dataMaestras = await resMaestras.json();
      const todas = dataMaestras.registros?.map((c:any) => ({ id_categoria: c.id_categoria || c.id, descripcion: c.descripcion })) || [];
      setTodasLasCategorias(todas);

      const resAsignadas = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/normativa/leer_categorias.php?id_norma=${norma.id_norma}`, { headers: { "Authorization": `Bearer ${token}` } });
      const dataAsignadas = await resAsignadas.json();
      if (dataAsignadas.registros) {
        setCategoriasAsignadas(dataAsignadas.registros.map((c: any) => ({ id_categoria: c.id_categoria, descripcion: c.descripcion })));
      } else {
        setCategoriasAsignadas([]);
      }
    } catch (err) {
      console.error("Error al cargar categorías:", err);
      toast.showToast("Error", "No se pudieron cargar las categorías.", "error");
    }
  };

  const handleDeleteNorma = async (norma: Norma) => {
    const mensaje = norma.categorias && norma.categorias.length > 0
      ? `¿Está seguro que desea eliminar la norma ${norma.tipo_norma_desc} ${norma.numero}? Se eliminarán también las categorías asociadas.`
      : `¿Está seguro que desea eliminar la norma ${norma.tipo_norma_desc} ${norma.numero}?`;
    const ok = await confirm({
      title: "Eliminar norma",
      message: mensaje,
      confirmText: "Eliminar",
      cancelText: "Cancelar"
    });
    if (!ok) return;
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/normativa/eliminar.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ id_norma: norma.id_norma })
      });
      const data = await res.json();
      if (res.ok) {
        fetchData(currentPage, pageSize);
        toast.showToast("Éxito", "Norma eliminada correctamente.", "success");
      } else {
        toast.showToast("Error", data.mensaje || "Error al eliminar la norma.", "error");
      }
    } catch (error) {
      console.error(error);
      toast.showToast("Error", "Error de conexión al eliminar.", "error");
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

  const moverADerecha = (cat: Categoria) => setCategoriasAsignadas(prev => [...prev, cat]);
  const moverAIzquierda = (id_cat: number) => setCategoriasAsignadas(prev => prev.filter(c => c.id_categoria !== id_cat));
  const moverTodasADerecha = (disponiblesFiltradas: Categoria[]) => setCategoriasAsignadas(prev => [...prev, ...disponiblesFiltradas]);
  const moverTodasAIzquierda = () => setCategoriasAsignadas([]);

  const guardarCategorias = async () => {
    setSavingCategorias(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const payload = { id_norma: normaSeleccionada?.id_norma, categorias: categoriasAsignadas.map(c => c.id_categoria) };
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/normativa/guardar_categorias.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setIsCategoriasModalOpen(false);
        fetchData(currentPage, pageSize);
        toast.showToast("Éxito", "Categorías guardadas correctamente.", "success");
      } else {
        const data = await res.json();
        toast.showToast("Error", data.mensaje || "Error al guardar categorías.", "error");
      }
    } catch (error) {
      console.error(error);
      toast.showToast("Error", "Error de conexión al guardar categorías.", "error");
    } finally {
      setSavingCategorias(false);
    }
  };

  const IDsAsignados = categoriasAsignadas.map(c => c.id_categoria);
  const categoriasDisponibles = todasLasCategorias.filter(c => !IDsAsignados.includes(c.id_categoria));
  const categoriasDisponiblesFiltradas = categoriasDisponibles.filter(c => c.descripcion.toLowerCase().includes(searchCat.toLowerCase()));

  const nivelesDisponibles = useMemo(() => {
    const setNiveles = new Set(normas.map(n => n.nivel_jurisdiccion_desc).filter(Boolean));
    return Array.from(setNiveles).map((desc, i) => ({ id: desc, descripcion: desc }));
  }, [normas]);

  const jurisdiccionesDisponibles = useMemo(() => {
    const setJur = new Set(normas.map(n => n.jurisdiccion_desc).filter(Boolean));
    return Array.from(setJur).map((desc, i) => ({ id: desc, descripcion: desc }));
  }, [normas]);

  // --- LÓGICA DE PAGINACIÓN (nueva) ---
  const totalPages = Math.ceil(totalItems / pageSize);
  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(totalPages);
    } else if (totalPages === 0) {
      setCurrentPage(1);
    }
  }, [totalPages, currentPage]);

  const handlePageSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPageSize(Number(e.target.value));
    setCurrentPage(1);
  };

  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const renderPageButtons = () => {
    const maxButtons = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);
    if (endPage - startPage + 1 < maxButtons) {
      startPage = Math.max(1, endPage - maxButtons + 1);
    }
    const pages = [];
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    return (
      <div className="flex gap-1">
        {pages.map(page => (
          <button
            key={page}
            onClick={() => goToPage(page)}
            className={`px-3 py-1 text-xs rounded transition-colors ${
              page === currentPage
                ? 'bg-lgc-primary text-white'
                : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {page}
          </button>
        ))}
      </div>
    );
  };

  const hasActiveFilters = Object.values(filtros).some(v => 
    typeof v === 'string' ? v !== '' : (Array.isArray(v) ? v.length > 0 : false)
  );

  // --- RENDER ---
  if (isCheckingPerms) return <div className="py-20 text-center text-lgc-primary animate-pulse">Verificando credenciales...</div>;
  if (!canRead("normativa")) return <div className="py-32 text-center text-red-500 font-bold text-2xl">Acceso Denegado</div>;

  return (
    <div className="space-y-6 font-sans animate-fade-in relative z-10 h-screen flex flex-col overflow-hidden">
      
      {/* HEADER (sin cambios) */}
      <div className="bg-[#005F78] text-white p-6 rounded-2xl shadow-lg border border-[#004D62] flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="flex items-center justify-center w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 text-white transition-all group">
            <svg className="w-5 h-5 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          </Link>
          <div className="h-8 w-px bg-white/30 hidden md:block"></div>
          <h1 className="text-2xl font-heading uppercase tracking-tight">Base Actualizada de Normativa</h1>
        </div>
        <div className="flex gap-3 w-full md:w-auto shrink-0">
          <input 
            type="text" 
            placeholder="Búsqueda rápida..." 
            className="w-full md:w-72 p-2.5 text-sm bg-white/10 text-white placeholder-white/50 border border-white/20 rounded-lg focus:ring-2 focus:ring-white outline-none transition-all shadow-inner"
            value={searchTerm}
            onChange={e => { setSearchTerm(e.target.value); setCurrentPage(1); }}
          />
          {canEdit("normativa") && (
            <button 
                onClick={() => { setFormData(defaultForm); setIsModalOpen(true); }}
                className="bg-white text-lgc-primary py-2.5 px-6 rounded-lg font-bold text-xs uppercase tracking-widest hover:bg-slate-100 transition-all shadow-md shrink-0 whitespace-nowrap"
            >
              + Alta Manual
            </button>
          )}
        </div>
      </div>

      {/* FILTROS (sin cambios) */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 transition-all overflow-hidden relative z-20 shrink-0">
         <button onClick={() => setIsFilterOpen(!isFilterOpen)} className="w-full flex items-center justify-between p-4 bg-slate-50 hover:bg-slate-100 transition-colors border-b border-transparent">
            <div className="flex items-center gap-3">
               <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
               <span className="font-bold uppercase text-xs tracking-widest text-slate-600">Búsqueda y Filtros Avanzados</span>
               {hasActiveFilters && <span className="bg-lgc-accent text-white px-2 py-0.5 rounded text-[10px] font-bold uppercase shadow-sm">Filtros Activos</span>}
            </div>
            <svg className={`w-5 h-5 text-slate-400 transform transition-transform ${isFilterOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
         </button>
         
         {isFilterOpen && (
            <div className="p-6 border-t border-slate-200 bg-white space-y-6">
                <div className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    <select className="text-[11px] p-2.5 border border-slate-200 rounded-lg outline-none focus:border-lgc-primary bg-slate-50 hover:bg-white transition-colors cursor-pointer" value={filtros.tipo} onChange={e => setFiltros({...filtros, tipo: e.target.value})}>
                       <option value="">Tipo Norma (Todos)</option>
                       {tipos.map(t => <option key={t.id} value={t.descripcion}>{t.descripcion}</option>)}
                    </select>
                    <input type="text" placeholder="Nro de Norma" className="text-[11px] p-2.5 border border-slate-200 rounded-lg outline-none focus:border-lgc-primary bg-slate-50 hover:bg-white transition-colors" value={filtros.nro} onChange={e => setFiltros({...filtros, nro: e.target.value})} />
                    <input type="text" placeholder="Año" maxLength={4} className="text-[11px] p-2.5 border border-slate-200 rounded-lg outline-none focus:border-lgc-primary bg-slate-50 hover:bg-white transition-colors" value={filtros.anio} onInput={(e) => { e.currentTarget.value = e.currentTarget.value.replace(/\D/g, ''); }} onChange={e => setFiltros({...filtros, anio: e.target.value})} />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    <select className="text-[11px] p-2.5 border border-slate-200 rounded-lg outline-none focus:border-lgc-primary bg-slate-50 hover:bg-white transition-colors cursor-pointer" value={filtros.nivel} onChange={e => setFiltros({...filtros, nivel: e.target.value})}>
                      <option value="">Nivel de Jurisdicción (Todos)</option>
                      {niveles.map(n => <option key={n.id} value={n.descripcion}>{n.descripcion}</option>)}
                    </select>
                    <SearchableSelect options={jurisdiccionesDisponibles} value={filtros.jurisdiccion} onChange={(val:string) => setFiltros({...filtros, jurisdiccion: val})} placeholder="Jurisdicción..." />
                    <SearchableSelect options={emisores} value={filtros.id_emisor} onChange={(val:string) => setFiltros({...filtros, id_emisor: val})} placeholder="Emisor Normativo..." />
                  </div>
                  <div className="grid grid-cols-1">
                    <MultiSelectCategorias options={categoriasGlobales} selected={filtros.categorias} onChange={(arr:string[]) => setFiltros({...filtros, categorias: arr})} placeholder="Filtrar por categorías..." />
                  </div>
                </div>
                <div className="flex justify-between items-center pt-2 gap-4 border-t border-slate-100 mt-4">
                   <div className="text-[10px] text-slate-400 font-bold uppercase tracking-widest bg-slate-50 px-3 py-1.5 rounded border border-slate-200 shadow-inner">
                     Resultados: <span className="text-lgc-primary font-black text-xs">{totalItems}</span> normas encontradas
                   </div>
                   <button onClick={() => setFiltros({ tipo: '', nro: '', anio: '', sintesis: '', emisor: '', id_emisor: '', nivel: '', jurisdiccion: '', categorias: [] })} className="text-[10px] font-bold uppercase tracking-widest text-slate-500 hover:text-slate-700 px-5 py-2.5 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition-colors shadow-sm whitespace-nowrap">
                      Limpiar Filtros
                   </button>
                </div>
            </div>
         )}
      </div>

      {/* CONTENEDOR CON SCROLL Y FLECHAS */}
      <div ref={mainContainerRef} className="flex-1 overflow-auto custom-scrollbar pb-10 relative min-h-0">
        {loading ? (
          <div className="py-20 text-center text-slate-400 font-bold uppercase tracking-widest animate-pulse">Cargando base normativa...</div>
        ) : (
          <>
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden relative z-10">
              <table className="w-full text-left">
                <thead className="bg-lgc-primary text-white text-[10px] uppercase tracking-[0.2em] font-bold border-b border-lgc-primary sticky top-0 z-10">
                  <tr>
                    <th className="p-5">Norma</th>
                    <th className="p-5">Emisor / Fecha</th>
                    <th className="p-5 w-1/3">Síntesis y Categorías</th>
                    <th className="p-5">Estado</th>
                    <th className="p-5 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {normas.length === 0 ? (
                    <tr><td colSpan={5} className="p-10 text-center text-slate-400 italic">No se encontraron normativas con los filtros aplicados.</td></tr>
                  ) : (
                    normas.map(norma => (
                      <tr key={norma.id_norma} className="hover:bg-slate-50/80 transition-colors align-top group">
                        <td className="p-5">
                          <div className="font-bold text-slate-700 text-sm group-hover:text-lgc-primary transition-colors">
                            {norma.tipo_norma_desc} {norma.numero}
                          </div>
                          <div className="text-[10px] text-slate-400 uppercase tracking-widest mt-1">Año {norma.anio}</div>
                          {norma.origen_carga === 'Scraping' && (
                            <span className="inline-block mt-2 text-[8px] bg-blue-50 text-blue-500 border border-blue-200 px-1.5 py-0.5 rounded uppercase font-bold tracking-widest">Bot / Scraper</span>
                          )}
                        </td>
                        <td className="p-5">
                          <div className="text-xs font-bold text-slate-600 uppercase tracking-widest leading-tight">{norma.emisor_desc}</div>
                          <div className="text-[10px] text-slate-500 mt-1">{norma.fecha_publicacion ? new Date(norma.fecha_publicacion).toLocaleDateString('es-AR') : '-'}</div>
                        </td>
                        <td className="p-5">
                          <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed" title={norma.sintesis}>{norma.sintesis || 'Sin síntesis registrada.'}</p>
                          {norma.categorias && norma.categorias.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-3">
                              {norma.categorias.map((c, idx) => (
                                <span key={idx} className="bg-blue-50 text-blue-700 border border-blue-200 text-[8px] font-bold px-1.5 py-0.5 rounded uppercase shadow-sm tracking-widest animate-fade-in">
                                  {c}
                                </span>
                              ))}
                            </div>
                          )}
                          {norma.url_norma && (
                            <a href={norma.url_norma} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 mt-3 text-[10px] text-lgc-accent font-bold uppercase tracking-widest hover:underline">
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                              Ver Doc. Original
                            </a>
                          )}
                        </td>
                        <td className="p-5">
                          <span className={`px-2.5 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest border shadow-inner ${norma.estado_desc?.includes('Vigente') ? 'bg-green-50 text-green-700 border-green-200' : 'bg-slate-50 text-slate-600 border-slate-200'}`}>
                            {norma.estado_desc || 'SIN ESTADO'}
                          </span>
                        </td>
                        <td className="p-5 text-right">
                          {canEdit("normativa") && (
                            <div className="flex justify-end gap-2">
                              <button onClick={() => abrirModalCategorias(norma)} className="text-slate-400 hover:text-[#006A8A] bg-white border border-slate-200 p-2 rounded transition-all shadow-sm group-hover:shadow-md" title="Asignar Categorías">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
                              </button>
                              <button onClick={() => { setFormData({ id_norma: norma.id_norma.toString(), id_tipo_norma: norma.id_tipo_norma?.toString() || "", id_emisor_norma: norma.id_emisor_norma?.toString() || "", numero: norma.numero || "", anio: norma.anio, fecha_publicacion: norma.fecha_publicacion || "", sintesis: norma.sintesis || "", url_norma: norma.url_norma || "", id_estado_norma: norma.id_estado_norma?.toString() || "1", origen_carga: norma.origen_carga }); setIsModalOpen(true); }} className="text-slate-400 hover:text-lgc-primary bg-white border border-slate-200 p-2 rounded transition-all shadow-sm group-hover:shadow-md" title="Editar Norma">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                              </button>
                              <button onClick={() => handleDeleteNorma(norma)} className="text-slate-400 hover:text-red-500 bg-white border border-slate-200 p-2 rounded transition-all shadow-sm group-hover:shadow-md" title="Eliminar Norma">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* PAGINADOR */}
            {totalItems > 0 && (
              <div className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-white p-4 rounded-xl shadow-sm border border-slate-200 mt-4">
                <div className="text-xs text-slate-500">
                  Mostrando <span className="font-bold">{Math.min((currentPage-1)*pageSize + 1, totalItems)}</span> a{' '}
                  <span className="font-bold">{Math.min(currentPage*pageSize, totalItems)}</span> de{' '}
                  <span className="font-bold">{totalItems}</span> normas
                </div>
                <div className="flex items-center gap-4 flex-wrap justify-center">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Filas por página:</span>
                    <select value={pageSize} onChange={handlePageSizeChange} className="text-xs p-1.5 border border-slate-200 rounded-lg bg-white focus:border-lgc-primary outline-none">
                      {pageSizeOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => goToPage(currentPage - 1)} disabled={currentPage === 1} className="px-3 py-1 text-xs rounded bg-white border border-slate-200 text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition-colors">Anterior</button>
                    {renderPageButtons()}
                    <button onClick={() => goToPage(currentPage + 1)} disabled={currentPage === totalPages} className="px-3 py-1 text-xs rounded bg-white border border-slate-200 text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition-colors">Siguiente</button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* FLECHAS FLOTANTES */}
      {showScrollTop && (
        <button onClick={scrollToTop} className="fixed bottom-14 right-14 bg-lgc-primary text-white p-3 rounded-full shadow-lg hover:bg-[#006A8A] transition-all z-50" title="Ir arriba">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
        </button>
      )}
      {showScrollBottom && (
        <button onClick={scrollToBottom} className="fixed bottom-6 right-14 bg-lgc-primary text-white p-3 rounded-full shadow-lg hover:bg-[#006A8A] transition-all z-50" title="Ir abajo">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" /></svg>
        </button>
      )}

      {/* MODALES (exactamente como estaban, sin cambios) */}
      {isModalOpen && canEdit("normativa") && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto animate-fade-in">
          <div className="bg-white w-full max-w-3xl rounded-2xl shadow-2xl overflow-hidden my-8 border border-slate-200">
            <div className="p-6 bg-slate-50 border-b flex justify-between items-center sticky top-0 z-10">
              <div>
                <h2 className="text-xl font-heading text-lgc-primary uppercase tracking-tight">
                  {formData.id_norma ? "Modificar Normativa" : "Alta de Normativa"}
                </h2>
                <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold mt-1">Gestión del repositorio oficial</p>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-2xl transition-colors">&times;</button>
            </div>

            <form onSubmit={handleSubmit} className="p-8 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Tipo de Norma *</label>
                  <select required className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm cursor-pointer" value={formData.id_tipo_norma} onChange={e => setFormData({...formData, id_tipo_norma: e.target.value})}>
                    <option value="">Seleccione...</option>
                    {tipos.map(t => <option key={t.id} value={t.id}>{t.descripcion}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Número *</label>
                  <input required type="text" className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm" placeholder="Ej: 19587" value={formData.numero} onChange={e => setFormData({...formData, numero: e.target.value})} />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Año *</label>
                  <input required type="number" min="1900" max={new Date().getFullYear() + 1} className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm" value={formData.anio} onChange={e => setFormData({...formData, anio: parseInt(e.target.value)})} />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div className="md:col-span-2">
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Emisor / Jurisdicción *</label>
                  <select required className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-[11px] font-bold shadow-sm cursor-pointer" value={formData.id_emisor_norma} onChange={e => setFormData({...formData, id_emisor_norma: e.target.value})}>
                    <option value="">Seleccione...</option>
                    {emisores.map(e => <option key={e.id} value={e.id} title={e.descripcion}>{e.descripcion}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Estado Normativo *</label>
                  <select required className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm cursor-pointer" value={formData.id_estado_norma} onChange={e => setFormData({...formData, id_estado_norma: e.target.value})}>
                    {estados.map(e => <option key={e.id} value={e.id}>{e.descripcion}</option>)}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Síntesis / Título de la Norma</label>
                <textarea rows={3} className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm resize-none" placeholder="Breve descripción del objeto de la norma..." value={formData.sintesis} onChange={e => setFormData({...formData, sintesis: e.target.value})} />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Fecha de Publicación BO</label>
                  <input type="date" className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm text-slate-600 cursor-pointer" value={formData.fecha_publicacion} onChange={e => setFormData({...formData, fecha_publicacion: e.target.value})} />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">URL Documento Original</label>
                  <input type="url" className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm" placeholder="https://..." value={formData.url_norma} onChange={e => setFormData({...formData, url_norma: e.target.value})} />
                </div>
              </div>

              <div className="flex gap-4 pt-6 mt-6 border-t border-slate-100">
                <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 py-3 text-xs uppercase tracking-widest font-bold text-slate-400 hover:text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">Cancelar</button>
                <button type="submit" disabled={formLoading} className="flex-1 bg-lgc-primary text-white py-3 rounded-lg font-bold text-xs uppercase tracking-widest shadow-md hover:bg-[#006A8A] transition-all disabled:opacity-50">
                  {formLoading ? 'Guardando...' : 'Confirmar y Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isCategoriasModalOpen && normaSeleccionada && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden border border-slate-200 flex flex-col max-h-[90vh]">
            <div className="p-6 bg-slate-50 border-b flex justify-between items-center shrink-0">
              <div>
                <h2 className="text-xl font-heading text-lgc-primary uppercase tracking-tight flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
                  Categorización de Norma
                </h2>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">
                  Definiendo perfil para: <span className="text-slate-600">{normaSeleccionada.tipo_norma_desc} {normaSeleccionada.numero}</span>
                </p>
              </div>
              <button onClick={() => setIsCategoriasModalOpen(false)} className="text-slate-400 hover:text-red-500 text-2xl transition-colors">&times;</button>
            </div>

            <div className="p-6 flex-1 overflow-hidden flex flex-col md:flex-row gap-6 bg-white min-h-100">
              {/* PANEL IZQUIERDO */}
              <div className="flex-1 flex flex-col border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                <div className="bg-slate-50 p-3 border-b border-slate-200 flex flex-col gap-2">
                  <div className="flex justify-between items-center">
                    <h3 className="text-[10px] font-bold uppercase text-slate-500 tracking-widest">Categorías Disponibles</h3>
                    <span className="bg-slate-200 text-slate-600 text-[10px] font-bold px-2 py-0.5 rounded shadow-inner">{categoriasDisponiblesFiltradas.length}</span>
                  </div>
                  <input 
                    type="text" 
                    placeholder="Buscar categoría..." 
                    value={searchCat}
                    onChange={e => setSearchCat(e.target.value)}
                    className="w-full text-xs p-2.5 border border-slate-300 rounded-lg outline-none focus:border-lgc-primary bg-white shadow-sm"
                  />
                </div>
                <div className="flex-1 overflow-y-auto p-2 bg-slate-50/50 scrollbar-thin">
                  {categoriasDisponiblesFiltradas.length === 0 ? (
                    <div className="text-center text-xs text-slate-400 italic p-6">No hay categorías que coincidan.</div>
                  ) : (
                    categoriasDisponiblesFiltradas.map(cat => (
                      <button 
                        key={cat.id_categoria} 
                        onClick={() => moverADerecha(cat)}
                        className="w-full text-left p-2.5 bg-white border border-slate-200 rounded-lg hover:border-lgc-primary hover:text-lgc-primary transition-all text-xs font-bold text-slate-600 flex justify-between items-center group mb-2 shadow-sm"
                      >
                        {cat.descripcion}
                        <svg className="w-4 h-4 text-slate-300 group-hover:text-lgc-primary transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                      </button>
                    ))
                  )}
                </div>
              </div>

              {/* BOTONERA CENTRAL */}
              <div className="flex md:flex-col justify-center gap-3 shrink-0 py-4">
                 <button 
                   onClick={() => moverTodasADerecha(categoriasDisponiblesFiltradas)} 
                   disabled={categoriasDisponiblesFiltradas.length === 0}
                   className="bg-slate-100 hover:bg-[#006A8A] hover:text-white text-slate-500 p-2 rounded-lg transition-colors disabled:opacity-30 border border-slate-200 shadow-sm disabled:cursor-not-allowed"
                   title="Mover todas a la derecha"
                 >
                   <svg className="w-5 h-5 hidden md:block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" /></svg>
                   <svg className="w-5 h-5 md:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 13l-7 7-7-7m14-8l-7 7-7-7" /></svg>
                 </button>
                 <button 
                   onClick={moverTodasAIzquierda} 
                   disabled={categoriasAsignadas.length === 0}
                   className="bg-slate-100 hover:bg-red-500 hover:text-white text-slate-500 p-2 rounded-lg transition-colors disabled:opacity-30 border border-slate-200 shadow-sm disabled:cursor-not-allowed"
                   title="Quitar todas"
                 >
                   <svg className="w-5 h-5 hidden md:block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" /></svg>
                   <svg className="w-5 h-5 md:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 11l7-7 7 7M5 19l7-7 7 7" /></svg>
                 </button>
              </div>

              {/* PANEL DERECHO */}
              <div className="flex-1 flex flex-col border border-[#006A8A]/30 rounded-xl overflow-hidden shadow-sm bg-[#006A8A]/5">
                <div className="bg-white p-3 border-b border-[#006A8A]/20">
                  <div className="flex justify-between items-center mb-1">
                    <h3 className="text-[10px] font-bold uppercase text-[#006A8A] tracking-widest">Asignadas a la Norma</h3>
                    <span className="bg-[#006A8A] text-white text-[10px] font-bold px-2 py-0.5 rounded shadow-inner">{categoriasAsignadas.length}</span>
                  </div>
                  <p className="text-[9px] text-slate-500 uppercase tracking-widest">Arrastrá para ordenar por prioridad</p>
                </div>
                <div className="flex-1 overflow-y-auto p-2 scrollbar-thin">
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

            <div className="p-5 border-t border-slate-100 bg-slate-50 flex justify-end gap-4 shrink-0 relative z-10">
               <button onClick={() => setIsCategoriasModalOpen(false)} className="px-6 py-2.5 text-xs uppercase font-bold text-slate-500 bg-white border border-slate-200 hover:bg-slate-100 transition-colors rounded-lg shadow-sm">
                 Cancelar
               </button>
               <button onClick={guardarCategorias} disabled={savingCategorias} className="px-8 py-2.5 bg-lgc-primary hover:bg-[#006A8A] text-white font-bold rounded-lg uppercase text-xs shadow-md disabled:opacity-50 flex items-center gap-2 transition-colors disabled:cursor-not-allowed">
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
    </div>
  );
}