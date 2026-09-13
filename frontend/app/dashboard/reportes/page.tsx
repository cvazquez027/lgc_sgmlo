"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { usePermissions } from "../../hooks/usePermissions";
import { useToast } from "../../providers/ToastProvider";
import { useConfirm } from "../../providers/ConfirmProvider";

interface Alerta {
  id_alerta: number;
  id_cliente: number;
  id_matriz: number | null;
  id_item_matriz: number | null;
  tipo: string;
  titulo: string;
  mensaje: string;
  fecha_creacion: string;
  leido: boolean;
  url: string | null;
  cliente_nombre?: string;
  cliente_razon?: string;
}

interface Vencimiento {
  id_matriz: number;
  nombre_matriz: string;
  id_item_matriz: number;
  item_resumen: string;
  vencimiento_plazo: string;
  dias_restantes: number;
  estado_desc: string;
}

interface Cliente {
  id_cliente: number;
  nombre_fantasia: string;
  razon_social: string;
}

export default function ReportesPage() {
  const router = useRouter();
  const { canRead, canEdit } = usePermissions();
  const toast = useToast();
  const confirm = useConfirm();
  
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [vencimientos, setVencimientos] = useState<Vencimiento[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [suscripciones, setSuscripciones] = useState<number[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marcando, setMarcando] = useState(false);
  const [guardandoSusc, setGuardandoSusc] = useState(false);
  
  const [esAdmin, setEsAdmin] = useState(false);
  const [filtroCliente, setFiltroCliente] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"alertas" | "vencimientos" | "suscripciones">("alertas");
  const hasShownAuthError = useRef(false);

  const fetchClientes = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/clientes/leer.php`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setClientes(data.registros || []);
    } catch (err) {
      console.error("Error cargando clientes", err);
    }
  }, []);

  const fetchSuscripciones = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/leer_suscripciones.php`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSuscripciones(data.suscripciones.map(Number));
      }
    } catch (err) {
      console.error("Error cargando suscripciones", err);
    }
  }, []);

  const fetchAlertas = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) {
      router.push("/");
      return;
    }
    try {
      let url = `${process.env.NEXT_PUBLIC_API_URL}/alertas/leer.php?incluir_leidas=true`;
      if (filtroCliente) {
        url += `&id_cliente=${filtroCliente}`;
      }
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.status === 401) {
        localStorage.removeItem("sgml_token");
        router.push("/");
        return;
      }
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      setAlertas(data.alertas || []);
      setEsAdmin(data.debug_es_admin || false);
      if (data.debug_es_admin && clientes.length === 0) {
        fetchClientes();
        fetchSuscripciones();
      }
    } catch (err: any) {
      console.error("Error cargando alertas:", err);
      toast.showToast("Error", "No se pudieron cargar las alertas.", "error");
    }
  }, [router, toast, filtroCliente, clientes.length, fetchClientes, fetchSuscripciones]);

  const fetchVencimientos = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return;
    try {
      let url = `${process.env.NEXT_PUBLIC_API_URL}/reportes/vencimientos.php`;
      if (filtroCliente) {
        url += `?id_cliente=${filtroCliente}`;
      }
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.status === 401) {
        localStorage.removeItem("sgml_token");
        router.push("/");
        return;
      }
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      setVencimientos(data.vencimientos || []);
    } catch (err: any) {
      console.error("Error cargando vencimientos:", err);
      if (!hasShownAuthError.current) {
        toast.showToast("Error", "No se pudieron cargar los vencimientos.", "error");
        hasShownAuthError.current = true;
      }
    }
  }, [router, toast, filtroCliente]);

  const marcarComoLeida = async (idAlerta: number) => {
    setMarcando(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/marcar_leida.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ id_alerta: idAlerta })
      });
      if (!res.ok) throw new Error("Error al marcar como leída");
      setAlertas(alertas.map(a => a.id_alerta === idAlerta ? { ...a, leido: true } : a));
    } catch (err) {
      toast.showToast("Error", "Error al marcar la alerta.", "error");
    } finally {
      setMarcando(false);
    }
  };

  const marcarTodas = async () => {
    const ok = await confirm({
      title: "Marcar todas como leídas",
      message: "¿Estás seguro de marcar todas las alertas como leídas?",
      confirmText: "Marcar todas",
      cancelText: "Cancelar"
    });
    if (!ok) return;
    setMarcando(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/marcar_leida.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ todas: true })
      });
      if (!res.ok) throw new Error("Error al marcar todas");
      setAlertas(alertas.map(a => ({ ...a, leido: true })));
      toast.showToast("Éxito", "Todas las alertas han sido marcadas como leídas.", "success");
    } catch (err) {
      toast.showToast("Error", "Error al marcar todas las alertas.", "error");
    } finally {
      setMarcando(false);
    }
  };

  const toggleSuscripcion = async (idCliente: number) => {
    const nuevasSusc = suscripciones.includes(idCliente)
      ? suscripciones.filter(id => id !== idCliente)
      : [...suscripciones, idCliente];
    
    setSuscripciones(nuevasSusc);
  };

  const guardarSuscripciones = async () => {
    setGuardandoSusc(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/guardar_suscripciones.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ suscripciones })
      });
      if (!res.ok) throw new Error("Error al guardar suscripciones");
      toast.showToast("Éxito", "Tus preferencias de notificación han sido actualizadas.", "success");
      fetchAlertas();
    } catch (error) {
      toast.showToast("Error", "Hubo un problema al guardar las suscripciones.", "error");
    } finally {
      setGuardandoSusc(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchAlertas(), fetchVencimientos()]);
      setLoading(false);
    };
    loadData();
  }, [fetchAlertas, fetchVencimientos]);

  if (loading) return <div className="py-20 text-center animate-pulse text-lgc-primary">Cargando Centro de Control...</div>;
  if (error) return <div className="bg-red-50 text-red-600 p-6 rounded-xl text-center">⚠️ {error}</div>;

  const alertasNoLeidas = alertas.filter(a => !a.leido);
  const alertasLeidas = alertas.filter(a => a.leido);

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      {/* HEADER PRINCIPAL */}
      <div className="bg-slate-900 text-white p-8 rounded-3xl shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 opacity-10 pointer-events-none">
          <svg className="w-64 h-64 transform translate-x-16 -translate-y-16" fill="currentColor" viewBox="0 0 24 24"><path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm-1-11v6h2v-6h-2zm0-4v2h2V7h-2z" /></svg>
        </div>
        
        <div className="flex items-center gap-4 relative z-10">
          <Link 
            href="/dashboard" 
            className="flex items-center justify-center w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 text-white transition-all group shrink-0"
            title="Volver al inicio"
          >
            <svg className="w-5 h-5 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div className="h-10 w-px bg-white/20 hidden md:block shrink-0"></div>

          <div className="bg-white/10 p-3 rounded-2xl shrink-0">
            <svg className="w-8 h-8 text-lgc-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-black uppercase tracking-tight">Centro de Control</h1>
            <p className="text-slate-400 text-[10px] md:text-xs uppercase tracking-widest font-bold mt-1">Seguimiento de novedades y plazos</p>
          </div>
        </div>

        {esAdmin && (
          <div className="relative z-10 w-full md:w-auto">
            <select 
              value={filtroCliente} 
              onChange={(e) => setFiltroCliente(e.target.value)}
              className="w-full md:w-64 bg-slate-800 text-white border border-slate-700 rounded-xl px-4 py-3 text-xs font-bold uppercase outline-none focus:ring-2 focus:ring-lgc-accent shadow-inner transition-all appearance-none cursor-pointer"
            >
              <option value="">Filtro: Todos los clientes</option>
              {clientes.map(c => (
                <option key={c.id_cliente} value={c.id_cliente}>{c.nombre_fantasia || c.razon_social}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* PESTAÑAS DE NAVEGACIÓN */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200">
        <button 
          onClick={() => setActiveTab("alertas")} 
          className={`px-6 py-4 text-xs font-bold uppercase tracking-widest transition-all border-b-2 ${activeTab === "alertas" ? "border-lgc-primary text-lgc-primary" : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50"}`}
        >
          Notificaciones
          {alertasNoLeidas.length > 0 && (
            <span className="ml-2 bg-red-500 text-white px-2 py-0.5 rounded-full text-[10px]">{alertasNoLeidas.length}</span>
          )}
        </button>
        <button 
          onClick={() => setActiveTab("vencimientos")} 
          className={`px-6 py-4 text-xs font-bold uppercase tracking-widest transition-all border-b-2 ${activeTab === "vencimientos" ? "border-lgc-primary text-lgc-primary" : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50"}`}
        >
          Agenda de Vencimientos
        </button>
        {esAdmin && (
          <button 
            onClick={() => setActiveTab("suscripciones")} 
            className={`px-6 py-4 text-xs font-bold uppercase tracking-widest transition-all border-b-2 ${activeTab === "suscripciones" ? "border-lgc-primary text-lgc-primary" : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50"}`}
          >
            Ajustes de Seguimiento
          </button>
        )}
      </div>

      {/* CONTENIDO PESTAÑA: ALERTAS */}
      {activeTab === "alertas" && (
        <div className="space-y-6 animate-fade-in">
          <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-slate-200">
            <p className="text-xs text-slate-500 uppercase tracking-widest font-bold">
              Historial de movimientos y avisos del sistema
            </p>
            {alertasNoLeidas.length > 0 && (
              <button 
                onClick={marcarTodas} 
                disabled={marcando}
                className="text-xs font-bold uppercase tracking-widest text-lgc-primary hover:text-[#004D62] flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                Marcar Todo Leído
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {alertas.length === 0 ? (
              <div className="col-span-full py-16 text-center text-slate-400 flex flex-col items-center gap-3">
                <svg className="w-12 h-12 text-slate-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" /></svg>
                No tienes notificaciones pendientes de leer.
              </div>
            ) : (
              <>
                {/* Renderizamos primero las no leídas */}
                {alertasNoLeidas.map(alerta => (
                  <div key={alerta.id_alerta} className="bg-white rounded-2xl shadow-md border border-lgc-primary/20 p-6 flex flex-col relative overflow-hidden transition-transform hover:-translate-y-1">
                    <div className="absolute top-0 left-0 w-1 h-full bg-lgc-primary"></div>
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex gap-2 items-center flex-wrap">
                        <span className="bg-lgc-primary text-white text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded">NUEVA</span>
                        {esAdmin && alerta.cliente_nombre && (
                          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest border border-slate-200 px-2 py-1 rounded">{alerta.cliente_nombre}</span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 font-bold whitespace-nowrap">{new Date(alerta.fecha_creacion).toLocaleDateString('es-AR')}</span>
                    </div>
                    <h3 className="font-bold text-slate-800 text-sm mb-2">{alerta.titulo}</h3>
                    <p className="text-xs text-slate-600 mb-4 flex-1">{alerta.mensaje}</p>
                    <div className="flex justify-between items-center pt-4 border-t border-slate-100">
                      {alerta.url ? (
                        <Link href={alerta.url} className="text-[10px] font-bold uppercase tracking-widest text-lgc-accent hover:underline">Ir al detalle →</Link>
                      ) : <span></span>}
                      <button onClick={() => marcarComoLeida(alerta.id_alerta)} disabled={marcando} className="text-slate-400 hover:text-green-600 bg-slate-50 hover:bg-green-50 p-2 rounded-full transition-colors" title="Marcar como leída">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                      </button>
                    </div>
                  </div>
                ))}
                
                {/* Renderizamos las ya leídas con otro estilo */}
                {alertasLeidas.map(alerta => (
                  <div key={alerta.id_alerta} className="bg-slate-50 rounded-2xl shadow-sm border border-slate-200 p-6 flex flex-col opacity-80 hover:opacity-100 transition-opacity">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex gap-2 items-center flex-wrap">
                        {esAdmin && alerta.cliente_nombre && (
                          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest bg-white border border-slate-200 px-2 py-1 rounded">{alerta.cliente_nombre}</span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 font-bold whitespace-nowrap">{new Date(alerta.fecha_creacion).toLocaleDateString('es-AR')}</span>
                    </div>
                    <h3 className="font-bold text-slate-600 text-sm mb-2">{alerta.titulo}</h3>
                    <p className="text-xs text-slate-500 mb-4 flex-1 line-clamp-3">{alerta.mensaje}</p>
                    <div className="flex justify-between items-center pt-4 border-t border-slate-200/50">
                      {alerta.url ? (
                        <Link href={alerta.url} className="text-[10px] font-bold uppercase tracking-widest text-slate-400 hover:text-slate-600 hover:underline">Ir al detalle →</Link>
                      ) : <span></span>}
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
      )}

      {/* CONTENIDO PESTAÑA: VENCIMIENTOS */}
      {activeTab === "vencimientos" && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden animate-fade-in">
          {vencimientos.length === 0 ? (
            <div className="py-24 text-center flex flex-col items-center gap-4">
               <svg className="w-16 h-16 text-slate-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
               <div>
                  <h3 className="text-lg font-bold text-slate-700">Agenda libre</h3>
                  <p className="text-sm text-slate-500 mt-1">No hay vencimientos próximos ni elementos vencidos en los registros.</p>
               </div>
            </div>
          ) : (
            <table className="w-full text-left">
              <thead className="bg-slate-50 border-b border-slate-200 text-[10px] uppercase tracking-widest text-slate-500 font-bold">
                <tr>
                  <th className="p-5 w-1/4">Matriz Normativa</th>
                  <th className="p-5 w-2/4">Asunto / Ítem</th>
                  <th className="p-5 text-center">Fecha Plazo</th>
                  <th className="p-5 text-center">Estado</th>
                  <th className="p-5 text-center">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {vencimientos.map(v => {
                  const esVencido = v.dias_restantes < 0;
                  let dotColor = esVencido ? 'bg-red-500' : 'bg-amber-400';
                  let estadoTexto = esVencido ? 'Vencido' : v.dias_restantes === 0 ? 'Vence Hoy' : `Faltan ${v.dias_restantes} días`;
                  
                  return (
                    <tr key={`${v.id_matriz}-${v.id_item_matriz}`} className="hover:bg-slate-50/50 transition-colors group">
                      <td className="p-5">
                        <span className="font-bold text-slate-700 text-xs">{v.nombre_matriz}</span>
                      </td>
                      <td className="p-5">
                        <p className="text-slate-600 text-xs line-clamp-2">{v.item_resumen || "Sin descripción"}</p>
                      </td>
                      <td className="p-5 text-center">
                        <span className="font-bold text-slate-700 text-xs">{v.vencimiento_plazo.split('-').reverse().join('/')}</span>
                      </td>
                      <td className="p-5 text-center">
                        <div className="inline-flex items-center gap-2 bg-white border border-slate-200 px-3 py-1.5 rounded-full shadow-sm">
                          <span className={`w-2 h-2 rounded-full ${dotColor} animate-pulse`}></span>
                          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-600">{estadoTexto}</span>
                        </div>
                      </td>
                      <td className="p-5 text-center">
                        <Link href={`/dashboard/matrices/${v.id_matriz}?item=${v.id_item_matriz}`} className="inline-flex p-2 bg-white text-lgc-primary border border-slate-200 rounded-lg hover:bg-lgc-primary hover:text-white transition-colors shadow-sm group-hover:shadow-md" title="Inspeccionar Ítem">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* CONTENIDO PESTAÑA: SUSCRIPCIONES (SOLO ADMIN LGC) */}
      {esAdmin && activeTab === "suscripciones" && (
        <div className="animate-fade-in space-y-6">
          <div className="bg-white p-6 md:p-8 rounded-2xl shadow-sm border border-slate-200 flex flex-col md:flex-row gap-8 items-center justify-between">
            <div className="flex-1">
              <h2 className="text-xl font-heading font-bold text-slate-800 mb-2">Recibir correos de Clientes</h2>
              <p className="text-sm text-slate-500 leading-relaxed">
                Seleccioná las empresas de las que querés recibir alertas por correo electrónico y notificaciones en tu Centro de Control. Esta configuración es personal y solo afectará a tu usuario ({localStorage.getItem("sgml_user") ? JSON.parse(localStorage.getItem("sgml_user")!).email : 'Admin'}).
              </p>
            </div>
            <div className="shrink-0 w-full md:w-auto">
              <button 
                onClick={guardarSuscripciones}
                disabled={guardandoSusc}
                className="w-full md:w-auto bg-lgc-primary hover:bg-[#004D62] text-white px-8 py-3.5 rounded-xl font-bold uppercase tracking-widest text-xs shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {guardandoSusc ? (
                   <><svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Guardando...</>
                ) : "Guardar Preferencias"}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {clientes.map(cliente => {
              const estaSuscrito = suscripciones.includes(cliente.id_cliente);
              return (
                <div 
                  key={cliente.id_cliente}
                  onClick={() => toggleSuscripcion(cliente.id_cliente)}
                  className={`p-5 rounded-2xl border-2 transition-all cursor-pointer flex items-center justify-between gap-4 ${estaSuscrito ? 'bg-blue-50/50 border-lgc-primary shadow-sm' : 'bg-white border-slate-100 hover:border-slate-300'}`}
                >
                  <div className="flex items-center gap-4 truncate">
                     <div className={`w-10 h-10 rounded-full flex items-center justify-center font-black shrink-0 transition-colors ${estaSuscrito ? 'bg-lgc-primary text-white' : 'bg-slate-100 text-slate-400'}`}>
                        {(cliente.nombre_fantasia || cliente.razon_social).substring(0,2).toUpperCase()}
                     </div>
                     <div className="truncate">
                        <h4 className={`font-bold truncate text-sm ${estaSuscrito ? 'text-lgc-primary' : 'text-slate-700'}`}>
                          {cliente.nombre_fantasia || cliente.razon_social}
                        </h4>
                        <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold mt-0.5 truncate">{cliente.razon_social}</p>
                     </div>
                  </div>
                  
                  {/* Custom Toggle Switch */}
                  <div className={`w-11 h-6 rounded-full shrink-0 relative transition-colors ${estaSuscrito ? 'bg-lgc-primary' : 'bg-slate-200'}`}>
                     <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all shadow-sm ${estaSuscrito ? 'left-6' : 'left-1'}`}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

    </div>
  );
}