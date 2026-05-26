"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { usePermissions } from "../../hooks/usePermissions"; 

interface Matriz {
  id_matriz: number;
  id_cliente_establecimiento: number;
  id_tipo_matriz: number;
  id_especialidad_matriz: number;
  fecha_desde: string;
  version: number;
  id_estado_matriz: number;
  vigente: number;
  estado_matriz_desc?: string; 
  tipo_matriz_desc?: string; 
  especialidad_matriz_desc?: string;
  establecimiento_desc?: string;
  id_cliente?: number;
  nombre_fantasia?: string;
  logo_path?: string;
}

interface Maestra {
  id: string | number;
  descripcion: string;
}

interface Cliente {
  id_cliente: number;
  nombre_fantasia: string;
  razon_social: string;
}

interface Establecimiento {
  id_cliente_establecimiento: number;
  descripcion: string;
}

export default function MatricesPage() {
  const router = useRouter();
  const { canRead, canEdit } = usePermissions();
  const [isCheckingPerms, setIsCheckingPerms] = useState(true);

  // ID de cliente del usuario logueado (null = usuario interno LGC, ve todo)
  const [userClienteId, setUserClienteId] = useState<string | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem("sgml_cliente_id"); // null si usuario interno
    setUserClienteId(raw && raw !== "null" ? raw : null);
  }, []);

  // Datos
  const [matrices, setMatrices] = useState<Matriz[]>([]);
  const [estadosMatriz, setEstadosMatriz] = useState<Maestra[]>([]);
  const [tiposMatriz, setTiposMatriz] = useState<Maestra[]>([]); 
  const [especialidadesMatriz, setEspecialidadesMatriz] = useState<Maestra[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  
  // Filtros de tabla
  const [filtroCliente, setFiltroCliente] = useState<string>("");
  const [filtroEstablecimiento, setFiltroEstablecimiento] = useState<string>("");
  const [filtroEspecialidad, setFiltroEspecialidad] = useState<string>("");
  const [filtroTipo, setFiltroTipo] = useState<string>("");
  const [filtroVigente, setFiltroVigente] = useState<boolean>(true);
  const [establecimientosFiltro, setEstablecimientosFiltro] = useState<Establecimiento[]>([]);

  // Estados UI
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"crear" | "editar">("crear");
  const [formLoading, setFormLoading] = useState(false);
  
  const [formClienteId, setFormClienteId] = useState<string>("");
  const [establecimientosForm, setEstablecimientosForm] = useState<Establecimiento[]>([]);

  const [formData, setFormData] = useState({
    id_matriz: "",
    id_cliente_establecimiento: "",
    id_tipo_matriz: "",
    id_especialidad_matriz: "",
    fecha_desde: new Date().toISOString().split('T')[0], 
    version: 1,
    id_estado_matriz: "1", 
    vigente: 1
  });

  useEffect(() => {
    const timer = setTimeout(() => setIsCheckingPerms(false), 100);
    return () => clearTimeout(timer);
  }, []);

  const fetchDiccionarios = useCallback(async (token: string) => {
    try {
      const resEstados = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=estado_matriz`, { headers: { "Authorization": `Bearer ${token}` } });
      const dataEstados = await resEstados.json();
      if (dataEstados.registros) {
        setEstadosMatriz(dataEstados.registros.map((e: any) => ({ id: e.id_estado_matriz || e.id, descripcion: e.descripcion })));
      }
      
      const resTipos = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=tipo_matriz`, { headers: { "Authorization": `Bearer ${token}` } });
      const dataTipos = await resTipos.json();
      if (dataTipos.registros) {
        setTiposMatriz(dataTipos.registros.map((e: any) => ({ id: e.id_tipo_matriz || e.id, descripcion: e.descripcion })));
      }

      const resEspecialidades = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=especialidad_matriz`, { headers: { "Authorization": `Bearer ${token}` } });
      const dataEspecialidades = await resEspecialidades.json();
      if (dataEspecialidades.registros) {
        setEspecialidadesMatriz(dataEspecialidades.registros.map((e: any) => ({ id: e.id_especialidad_matriz || e.id, descripcion: e.descripcion })));
      }

      const resClientes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/clientes/leer.php`, { headers: { "Authorization": `Bearer ${token}` } });
      const dataClientes = await resClientes.json();
      setClientes(dataClientes.registros || []);
    } catch (err) {
      console.error("Error cargando diccionarios", err);
    }
  }, []);

  const fetchMatrices = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) { router.push("/"); return; }
    try {
      setLoading(true);
      setError("");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/leer.php`, { 
        headers: { "Authorization": `Bearer ${token}` } 
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.mensaje || "Error al conectar con el servidor.");
      setMatrices(data.registros || []);
      if (estadosMatriz.length === 0) fetchDiccionarios(token);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [router, fetchDiccionarios, estadosMatriz.length]);

  useEffect(() => {
    if (!isCheckingPerms && canRead("matriz")) fetchMatrices();
  }, [fetchMatrices, isCheckingPerms, canRead]);

  useEffect(() => {
    if (!filtroCliente) {
      setEstablecimientosFiltro([]);
      setFiltroEstablecimiento("");
      return;
    }
    const token = localStorage.getItem("sgml_token");
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/establecimientos/leer.php?id_cliente=${filtroCliente}`, { headers: { "Authorization": `Bearer ${token}` } })
      .then(res => res.json())
      .then(data => setEstablecimientosFiltro(data.registros || []))
      .catch(err => console.error(err));
  }, [filtroCliente]);

  const loadEstablecimientosForForm = async (idCliente: string) => {
    if (!idCliente) { setEstablecimientosForm([]); return; }
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/establecimientos/leer.php?id_cliente=${idCliente}`, { headers: { "Authorization": `Bearer ${token}` } });
      const data = await res.json();
      setEstablecimientosForm(data.registros || []);
    } catch (error) {
      console.error("Error cargando establecimientos del form", error);
    }
  };

  const handleFormClienteChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setFormClienteId(id);
    setFormData(prev => ({ ...prev, id_cliente_establecimiento: "" }));
    await loadEstablecimientosForForm(id);
  };

  const openCrearModal = () => {
    if (!canEdit("matriz")) return;
    setModalMode("crear");
    setFormClienteId("");
    setEstablecimientosForm([]);
    setFormData({
      id_matriz: "",
      id_cliente_establecimiento: "",
      id_tipo_matriz: "",
      id_especialidad_matriz: "",
      fecha_desde: new Date().toISOString().split('T')[0],
      version: 1,
      id_estado_matriz: "1",
      vigente: 1
    });
    setIsModalOpen(true);
  };

  const openEditarModal = async (matriz: Matriz) => {
    if (!canEdit("matriz")) return;
    setModalMode("editar");
    const idCli = matriz.id_cliente?.toString() || "";
    setFormClienteId(idCli);
    await loadEstablecimientosForForm(idCli);
    setFormData({
      id_matriz: matriz.id_matriz.toString(),
      id_cliente_establecimiento: matriz.id_cliente_establecimiento.toString(),
      id_tipo_matriz: matriz.id_tipo_matriz?.toString() || "",
      id_especialidad_matriz: matriz.id_especialidad_matriz?.toString() || "",
      fecha_desde: matriz.fecha_desde,
      version: matriz.version,
      id_estado_matriz: matriz.id_estado_matriz?.toString() || "1",
      vigente: matriz.vigente
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit("matriz")) return;
    setFormLoading(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/guardar.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.mensaje || "Error al procesar la matriz.");
      setIsModalOpen(false);
      if (modalMode === "crear") {
        router.push(`/dashboard/matrices/${data.id_matriz}`);
      } else {
        fetchMatrices(); 
      }
    } catch (err: any) {
      alert("Error: " + err.message);
    } finally {
      setFormLoading(false);
    }
  };

  const matricesFiltradas = useMemo(() => {
    return matrices.filter(m => {
      // Usuarios externos (con id_cliente): solo ven sus matrices y solo las publicadas
      if (userClienteId) {
        if (m.id_cliente?.toString() !== userClienteId) return false;
        if (m.id_estado_matriz !== 2) return false;
      }
      const mCliente = filtroCliente === "" || m.id_cliente?.toString() === filtroCliente;
      const mEstablecimiento = filtroEstablecimiento === "" || m.id_cliente_establecimiento.toString() === filtroEstablecimiento;
      const mEspecialidad = filtroEspecialidad === "" || m.id_especialidad_matriz?.toString() === filtroEspecialidad;
      const mTipo = filtroTipo === "" || m.id_tipo_matriz.toString() === filtroTipo;
      const mVigente = filtroVigente ? m.vigente === 1 : true;
      return mCliente && mEstablecimiento && mEspecialidad && mTipo && mVigente;
    });
  }, [matrices, filtroCliente, filtroEstablecimiento, filtroEspecialidad, filtroTipo, filtroVigente, userClienteId]);

  if (isCheckingPerms) return <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Verificando credenciales...</div>;
  if (!canRead("matriz")) return <div className="flex flex-col items-center justify-center py-32 bg-white rounded-xl shadow-sm border border-red-100"><div className="text-red-500 text-6xl mb-4">🔒</div><h2 className="text-2xl font-heading text-slate-800 uppercase tracking-tight mb-2">Acceso Denegado</h2></div>;

  return (
    <div className="space-y-4 animate-fade-in">
      
      {/* HEADER PRINCIPAL Y FILTROS INTEGRADOS */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 flex flex-col relative overflow-hidden">
        
        {/* RECUADRO DE TÍTULO AZUL CORPORATIVO Y BOTÓN VOLVER INTEGRADO */}
        <div className="bg-[#005F78] text-white flex flex-col md:flex-row justify-between items-center gap-4 px-5 py-4 border-b border-[#004D62]">
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
              Matrices Legales
            </h1>
          </div>
          {canEdit("matriz") && (
            <button onClick={openCrearModal} className="bg-white text-lgc-primary hover:bg-slate-50 font-bold py-2.5 px-6 rounded-lg transition-all shadow-md text-xs uppercase tracking-widest flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" /></svg>
              Crear Matriz
            </button>
          )}
        </div>

        {/* BARRA DE FILTROS EN BLANCO/GRIS CLARO PARA CONTRASTE */}
        <div className="flex flex-wrap items-center gap-3 px-5 py-4 bg-slate-50">
          <select value={filtroCliente} onChange={e => setFiltroCliente(e.target.value)} className="p-2 bg-white border border-slate-200 rounded text-xs text-slate-700 outline-none focus:border-lgc-primary min-w-45 shadow-sm">
            <option value="">Todos los Clientes</option>
            {clientes.map(c => <option key={c.id_cliente} value={c.id_cliente}>{c.nombre_fantasia || c.razon_social}</option>)}
          </select>
          
          <select value={filtroEstablecimiento} onChange={e => setFiltroEstablecimiento(e.target.value)} disabled={!filtroCliente} className="p-2 bg-white border border-slate-200 rounded text-xs text-slate-700 outline-none focus:border-lgc-primary min-w-45 disabled:opacity-50 shadow-sm">
            <option value="">Todos los Establecimientos</option>
            {establecimientosFiltro.map(e => <option key={e.id_cliente_establecimiento} value={e.id_cliente_establecimiento}>{e.descripcion}</option>)}
          </select>

          <select value={filtroEspecialidad} onChange={e => setFiltroEspecialidad(e.target.value)} className="p-2 bg-white border border-slate-200 rounded text-xs text-slate-700 outline-none focus:border-lgc-primary min-w-37.5 shadow-sm">
            <option value="">Todas las Especialidades</option>
            {especialidadesMatriz.map(e => <option key={e.id} value={e.id}>{e.descripcion}</option>)}
          </select>

          <select value={filtroTipo} onChange={e => setFiltroTipo(e.target.value)} className="p-2 bg-white border border-slate-200 rounded text-xs text-slate-700 outline-none focus:border-lgc-primary min-w-37.5 shadow-sm">
            <option value="">Todos los Tipos</option>
            {tiposMatriz.map(t => <option key={t.id} value={t.id}>{t.descripcion}</option>)}
          </select>

          <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-slate-600 bg-white px-3 py-2 rounded border border-slate-200 hover:bg-slate-50 shadow-sm">
            <input type="checkbox" checked={filtroVigente} onChange={(e) => setFiltroVigente(e.target.checked)} className="rounded text-lgc-primary focus:ring-lgc-primary" />
            <span>SOLO VIGENTES</span>
          </label>
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-600 p-4 rounded-lg text-sm border border-red-200 shadow-sm font-bold uppercase tracking-widest">Error: {error}</div>}

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden min-h-100 flex flex-col">
        {loading ? (
           <div className="flex-1 flex items-center justify-center py-20 text-slate-400 animate-pulse font-heading">Cargando información...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-sans">
              {/* FILA DE TÍTULOS DE LA GRILLA EN AZUL CORPORATIVO */}
              <thead className="bg-lgc-primary text-[10px] uppercase tracking-[0.2em] text-white font-bold border-b border-lgc-primary">
                <tr>
                  <th className="p-4">Cliente</th>
                  <th className="p-4">ID / Versión</th>
                  <th className="p-4">Especialidad</th>
                  <th className="p-4">Tipo</th>
                  <th className="p-4">Establecimiento</th>
                  <th className="p-4">Inicio</th>
                  <th className="p-4">Estado</th>
                  <th className="p-4 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {matricesFiltradas.length === 0 ? (
                  <tr><td colSpan={8} className="p-12 text-center text-slate-400 font-bold uppercase text-xs">No se encontraron matrices.</td></tr>
                ) : (
                  matricesFiltradas.map(matriz => (
                    <tr key={matriz.id_matriz} className="hover:bg-slate-50/50 transition-colors group">
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          {matriz.logo_path ? (
                            <img src={`${process.env.NEXT_PUBLIC_IMG_URL}/${matriz.logo_path}`} alt="Logo" className="w-8 h-8 object-contain rounded-sm" />
                          ) : (
                            <div className="w-8 h-8 bg-slate-200 rounded flex items-center justify-center text-xs text-slate-500 font-bold">{matriz.nombre_fantasia?.charAt(0) || 'C'}</div>
                          )}
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="font-bold text-slate-700 text-xs">#{matriz.id_matriz}</div>
                        <div className="text-[10px] text-slate-400 uppercase tracking-widest mt-0.5">V{matriz.version}.0</div>
                      </td>
                      <td className="p-4 whitespace-nowrap">
                         <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded shadow-sm border ${
                           matriz.id_especialidad_matriz === 1
                             ? 'bg-lgc-accent/10 text-[#6B7A1A] border-lgc-accent/30'
                             : matriz.id_especialidad_matriz === 2
                             ? 'bg-lgc-primary/10 text-[#005F78] border-lgc-primary/30'
                             : 'bg-slate-100 text-slate-600 border-slate-200'
                         }`}>
                           {matriz.especialidad_matriz_desc || "No definido"}
                         </span>
                      </td>
                      <td className="p-4 whitespace-nowrap">
                         <span className="text-[10px] font-bold uppercase tracking-widest text-slate-600 bg-slate-100 border border-slate-200 px-2 py-1 rounded">
                           {matriz.tipo_matriz_desc || "No definido"}
                         </span>
                      </td>
                      <td className="p-4">
                        <div className="font-bold text-slate-800 text-xs uppercase">{matriz.establecimiento_desc || `ID: ${matriz.id_cliente_establecimiento}`}</div>
                      </td>
                      <td className="p-4 text-xs text-slate-600 font-medium">
                        {new Date(matriz.fecha_desde).toLocaleDateString('es-AR')}
                      </td>
                      <td className="p-4">
                        {/* LÓGICA DE ESTADOS POR COLORES */}
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest border ${
                            matriz.id_estado_matriz === 1 ? 'bg-amber-100 text-amber-700 border-amber-300' :
                            matriz.id_estado_matriz === 2 ? 'bg-green-100 text-green-700 border-green-300' :
                            matriz.id_estado_matriz === 3 ? 'bg-slate-100 text-slate-500 border-slate-300' :
                            'bg-slate-50 text-slate-700 border-slate-200'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${
                              matriz.id_estado_matriz === 1 ? 'bg-amber-500' :
                              matriz.id_estado_matriz === 2 ? 'bg-green-500' :
                              matriz.id_estado_matriz === 3 ? 'bg-slate-400' :
                              'bg-slate-500'
                          }`}></span>
                          {matriz.estado_matriz_desc || "SIN ESTADO"}
                        </span>
                      </td>
                      <td className="p-4 text-right flex justify-end gap-2 items-center">
                        {/* LAPIZ OCULTO SI ESTADO ES 2 (Publicada) O 3 (Archivada) */}
                        {canEdit("matriz") && matriz.id_estado_matriz !== 2 && matriz.id_estado_matriz !== 3 && (
                          <button onClick={() => openEditarModal(matriz)} className="text-slate-400 hover:text-lgc-primary transition-colors p-2" title="Editar Propiedades">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                          </button>
                        )}
                        <Link href={`/dashboard/matrices/${matriz.id_matriz}`} className="bg-slate-100 hover:bg-lgc-primary text-slate-600 hover:text-white px-3 py-1.5 rounded border border-slate-200 hover:border-lgc-primary transition-all shadow-sm text-[10px] uppercase tracking-widest font-bold flex items-center gap-2">
                          <span>{matriz.id_estado_matriz === 3 ? "Visualizar" : "Gestionar"}</span>
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {isModalOpen && canEdit("matriz") && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h2 className="text-lg font-heading text-lgc-primary uppercase tracking-tight">
                {modalMode === "crear" ? "Inicializar Matriz" : "Modificar Matriz"}
              </h2>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Cliente *</label>
                  <select required value={formClienteId} onChange={handleFormClienteChange} className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm transition-all cursor-pointer">
                    <option value="">Seleccione Cliente...</option>
                    {clientes.map(c => (<option key={c.id_cliente} value={c.id_cliente}>{c.nombre_fantasia || c.razon_social}</option>))}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Establecimiento *</label>
                  <select required disabled={!formClienteId} value={formData.id_cliente_establecimiento} onChange={e => setFormData({...formData, id_cliente_establecimiento: e.target.value})} className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm transition-all cursor-pointer disabled:opacity-50">
                    <option value="">Seleccione Establecimiento...</option>
                    {establecimientosForm.map(est => (<option key={est.id_cliente_establecimiento} value={est.id_cliente_establecimiento}>{est.descripcion}</option>))}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Especialidad *</label>
                  <select required value={formData.id_especialidad_matriz} onChange={e => setFormData({...formData, id_especialidad_matriz: e.target.value})} className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm cursor-pointer">
                    <option value="">Seleccione especialidad...</option>
                    {especialidadesMatriz.map(e => <option key={e.id} value={e.id}>{e.descripcion}</option>)}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Tipo de Matriz *</label>
                  <select required value={formData.id_tipo_matriz} onChange={e => setFormData({...formData, id_tipo_matriz: e.target.value})} className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm cursor-pointer">
                    <option value="">Seleccione tipo...</option>
                    {tiposMatriz.map(t => <option key={t.id} value={t.id}>{t.descripcion}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Fecha Inicio *</label>
                  <input required type="date" value={formData.fecha_desde} onChange={e => setFormData({...formData, fecha_desde: e.target.value})} className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg outline-none text-sm" />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Versión *</label>
                  <input required type="number" min="1" value={formData.version} onChange={e => setFormData({...formData, version: parseInt(e.target.value)})} className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg outline-none text-sm" />
                </div>
              </div>
              <div className="pt-4 flex gap-3">
                <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 py-2.5 text-xs uppercase font-bold text-slate-500 bg-white border border-slate-200 rounded-lg">Cancelar</button>
                <button type="submit" disabled={formLoading} className="flex-1 bg-lgc-primary text-white py-2.5 rounded-lg text-xs uppercase font-bold shadow-md disabled:opacity-50">Guardar Cambios</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}