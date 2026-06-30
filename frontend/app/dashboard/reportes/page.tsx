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
  color_hex?: string;
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marcando, setMarcando] = useState(false);
  const [esAdmin, setEsAdmin] = useState(false);
  const [filtroCliente, setFiltroCliente] = useState<string>("");
  const hasShownAuthError = useRef(false);

  // Modal de creación/edición
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<"crear" | "editar">("crear");
  const [modalLoading, setModalLoading] = useState(false);
  const [formData, setFormData] = useState({
    id_alerta: "",
    id_cliente: "",
    tipo: "",
    titulo: "",
    mensaje: "",
    url: "",
    id_matriz: "",
    id_item_matriz: ""
  });

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

  const fetchAlertas = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) {
      router.push("/");
      return;
    }

    try {
      let url = `${process.env.NEXT_PUBLIC_API_URL}/alertas/leer.php?incluir_leidas=false`;
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
      }
    } catch (err: any) {
      console.error("Error cargando alertas:", err);
      toast.showToast("Error", "No se pudieron cargar las alertas.", "error");
    }
  }, [router, toast, filtroCliente, clientes.length, fetchClientes]);

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
      await fetchAlertas();
      toast.showToast("Éxito", "Alerta marcada como leída.", "success");
    } catch (err) {
      console.error("Error al marcar como leída", err);
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
      await fetchAlertas();
      toast.showToast("Éxito", "Todas las alertas han sido marcadas como leídas.", "success");
    } catch (err) {
      console.error("Error al marcar todas", err);
      toast.showToast("Error", "Error al marcar todas las alertas.", "error");
    } finally {
      setMarcando(false);
    }
  };

  const eliminarAlerta = async (idAlerta: number) => {
    const ok = await confirm({
      title: "Eliminar alerta",
      message: "¿Estás seguro de eliminar esta alerta? Esta acción no se puede deshacer.",
      confirmText: "Eliminar",
      cancelText: "Cancelar"
    });
    if (!ok) return;
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/eliminar.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ id_alerta: idAlerta })
      });
      if (!res.ok) throw new Error("Error al eliminar");
      await fetchAlertas();
      toast.showToast("Éxito", "Alerta eliminada correctamente.", "success");
    } catch (err) {
      console.error("Error al eliminar", err);
      toast.showToast("Error", "Error al eliminar la alerta.", "error");
    }
  };

  const abrirModalCrear = () => {
    setModalMode("crear");
    setFormData({
      id_alerta: "",
      id_cliente: "",
      tipo: "",
      titulo: "",
      mensaje: "",
      url: "",
      id_matriz: "",
      id_item_matriz: ""
    });
    setShowModal(true);
  };

  const abrirModalEditar = (alerta: Alerta) => {
    setModalMode("editar");
    setFormData({
      id_alerta: alerta.id_alerta.toString(),
      id_cliente: alerta.id_cliente.toString(),
      tipo: alerta.tipo,
      titulo: alerta.titulo,
      mensaje: alerta.mensaje,
      url: alerta.url || "",
      id_matriz: alerta.id_matriz?.toString() || "",
      id_item_matriz: alerta.id_item_matriz?.toString() || ""
    });
    setShowModal(true);
  };

  const guardarAlerta = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    const token = localStorage.getItem("sgml_token");
    try {
      if (modalMode === "crear") {
        // Construir payload para creación
        const payload = {
          id_cliente: parseInt(formData.id_cliente),
          tipo: formData.tipo,
          titulo: formData.titulo,
          mensaje: formData.mensaje,
          url: formData.url || null,
          id_matriz: formData.id_matriz ? parseInt(formData.id_matriz) : null,
          id_item_matriz: formData.id_item_matriz ? parseInt(formData.id_item_matriz) : null
        };
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/crear.php`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("Error al crear");
      } else {
        // Modo edición: solo enviamos id_alerta, titulo, mensaje
        const payload = {
          id_alerta: parseInt(formData.id_alerta),
          titulo: formData.titulo,
          mensaje: formData.mensaje
        };
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/editar.php`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("Error al editar");
      }
      await fetchAlertas();
      setShowModal(false);
      toast.showToast("Éxito", modalMode === "crear" ? "Alerta creada." : "Alerta actualizada.", "success");
    } catch (err) {
      console.error(err);
      toast.showToast("Error", "Error al guardar la alerta.", "error");
    } finally {
      setModalLoading(false);
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

  if (loading) return <div className="py-20 text-center animate-pulse text-lgc-primary">Cargando alertas y vencimientos...</div>;
  if (error) return <div className="bg-red-50 text-red-600 p-6 rounded-xl text-center">⚠️ {error}</div>;

  const alertasNoLeidas = alertas.filter(a => !a.leido);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* HEADER */}
      <div className="bg-[#005F78] text-white p-6 rounded-2xl shadow-lg border border-[#004D62] flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-3">
          <Link 
            href="/dashboard" 
            className="flex items-center justify-center w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 text-white transition-all group"
          >
            <svg className="w-5 h-5 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div className="h-8 w-px bg-white/30 hidden md:block"></div>
          <h1 className="text-xl font-heading font-bold uppercase tracking-tight leading-none">
            Alertas y Vencimientos
          </h1>
        </div>

        <div className="flex flex-wrap gap-3 items-center">
          {esAdmin && (
            <>
              <select 
                value={filtroCliente} 
                onChange={(e) => setFiltroCliente(e.target.value)}
                className="bg-white/10 text-white border border-white/20 rounded-lg px-3 py-2 text-xs font-bold uppercase outline-none focus:ring-2 focus:ring-white"
              >
                <option value="">Todos los clientes</option>
                {clientes.map(c => (
                  <option key={c.id_cliente} value={c.id_cliente}>{c.nombre_fantasia || c.razon_social}</option>
                ))}
              </select>
              <button 
                onClick={abrirModalCrear}
                className="bg-white text-lgc-primary hover:bg-slate-100 font-bold py-2.5 px-5 rounded-lg transition-all text-xs uppercase tracking-widest shadow-md"
              >
                + Crear alerta
              </button>
            </>
          )}
          {alertasNoLeidas.length > 0 && !esAdmin && (
            <button 
              onClick={marcarTodas} 
              disabled={marcando}
              className="bg-white text-lgc-primary hover:bg-slate-100 font-bold py-2.5 px-5 rounded-lg transition-all text-xs uppercase tracking-widest shadow-md disabled:opacity-50"
            >
              Marcar todas como leídas
            </button>
          )}
        </div>
      </div>

      {/* Sección de Alertas */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-slate-50 px-6 py-3 border-b border-slate-200 flex justify-between items-center">
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-500">
            Notificaciones recientes {esAdmin && `(${alertas.length})`}
          </h2>
          {esAdmin && (
            <span className="text-[10px] text-slate-400 font-bold uppercase">
              {alertasNoLeidas.length} no leídas
            </span>
          )}
        </div>
        {alertas.length === 0 ? (
          <div className="p-8 text-center text-slate-400 italic">No hay alertas pendientes.</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {alertas.map(alerta => (
              <div key={alerta.id_alerta} className={`p-5 ${!alerta.leido ? 'bg-amber-50/30' : 'bg-white'}`}>
                <div className="flex justify-between items-start gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 flex-wrap">
                      {esAdmin && alerta.cliente_nombre && (
                        <span className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                          {alerta.cliente_nombre}
                        </span>
                      )}
                      <h3 className="font-bold text-slate-800">{alerta.titulo}</h3>
                      {!alerta.leido && (
                        <span className="bg-red-100 text-red-700 text-[9px] font-bold px-2 py-0.5 rounded-full uppercase">Nueva</span>
                      )}
                      <span className="text-[10px] text-slate-400">{new Date(alerta.fecha_creacion).toLocaleString('es-AR')}</span>
                    </div>
                    <p className="text-sm text-slate-600 mt-1">{alerta.mensaje}</p>
                    {alerta.url && (
                      <Link href={alerta.url} className="inline-block mt-2 text-[10px] font-bold text-lgc-primary hover:underline uppercase tracking-widest">
                        Ver detalle →
                      </Link>
                    )}
                  </div>
                  <div className="flex gap-2 shrink-0">
                    {!alerta.leido && (
                      <button
                        onClick={() => marcarComoLeida(alerta.id_alerta)}
                        disabled={marcando}
                        className="text-slate-400 hover:text-slate-600 text-xs font-bold uppercase whitespace-nowrap disabled:opacity-50"
                      >
                        Marcar leída
                      </button>
                    )}
                    {esAdmin && (
                      <>
                        <button
                          onClick={() => abrirModalEditar(alerta)}
                          className="text-blue-500 hover:text-blue-700 text-xs font-bold uppercase"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => eliminarAlerta(alerta.id_alerta)}
                          className="text-red-500 hover:text-red-700 text-xs font-bold uppercase"
                        >
                          Eliminar
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Sección de Vencimientos */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-slate-50 px-6 py-3 border-b border-slate-200">
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-500">Próximos vencimientos (30 días)</h2>
        </div>
        {vencimientos.length === 0 ? (
          <div className="p-8 text-center text-slate-400 italic">No hay vencimientos próximos ni vencidos.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="text-[10px] uppercase tracking-widest text-slate-500 bg-slate-50 border-b">
                <tr>
                  <th className="p-4">Matriz</th>
                  <th className="p-4">Ítem</th>
                  <th className="p-4">Fecha vencimiento</th>
                  <th className="p-4">Estado</th>
                  <th className="p-4"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {vencimientos.map(v => {
                  const esVencido = v.dias_restantes < 0;
                  let estadoClase = "";
                  let estadoTexto = "";
                  if (esVencido) {
                    estadoClase = "text-red-600 bg-red-50 border-red-200";
                    estadoTexto = "Vencido";
                  } else if (v.dias_restantes === 0) {
                    estadoClase = "text-amber-600 bg-amber-50 border-amber-200";
                    estadoTexto = "Vence hoy";
                  } else {
                    estadoClase = "text-amber-600 bg-amber-50 border-amber-200";
                    estadoTexto = `${v.dias_restantes} días`;
                  }
                  return (
                    <tr key={`${v.id_matriz}-${v.id_item_matriz}`} className="hover:bg-slate-50 transition">
                      <td className="p-4 font-bold text-slate-700 text-sm">{v.nombre_matriz}</td>
                      <td className="p-4 text-slate-600 text-xs">{v.item_resumen || "Sin descripción"}</td>
                      <td className="p-4 text-xs text-slate-600">{v.vencimiento_plazo.split('-').reverse().join('/')}</td>
                      <td className="p-4">
                        <span className={`text-[10px] font-bold uppercase px-2 py-1 rounded-full border ${estadoClase}`}>
                          {estadoTexto}
                        </span>
                      </td>
                      <td className="p-4">
                        <Link href={`/dashboard/matrices/${v.id_matriz}?item=${v.id_item_matriz}`} className="text-lgc-primary text-[10px] font-bold uppercase tracking-widest hover:underline">
                          Ver ítem
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal de crear/editar alerta (solo admin) */}
      {showModal && esAdmin && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h2 className="text-lg font-heading text-lgc-primary uppercase tracking-tight">
                {modalMode === "crear" ? "Crear alerta" : "Editar alerta"}
              </h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">&times;</button>
            </div>
            <form onSubmit={guardarAlerta} className="p-6 space-y-4">
              {modalMode === "crear" && (
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Cliente *</label>
                  <select
                    required
                    value={formData.id_cliente}
                    onChange={(e) => setFormData({...formData, id_cliente: e.target.value})}
                    className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm"
                  >
                    <option value="">Seleccione...</option>
                    {clientes.map(c => (
                      <option key={c.id_cliente} value={c.id_cliente}>{c.nombre_fantasia || c.razon_social}</option>
                    ))}
                  </select>
                </div>
              )}
              {modalMode === "editar" && (
                <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded-lg">
                  <p><span className="font-bold">Cliente:</span> {clientes.find(c => c.id_cliente === parseInt(formData.id_cliente))?.nombre_fantasia || formData.id_cliente}</p>
                  <p><span className="font-bold">Tipo:</span> {formData.tipo}</p>
                </div>
              )}
              <div>
                <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Título *</label>
                <input
                  type="text"
                  required
                  value={formData.titulo}
                  onChange={(e) => setFormData({...formData, titulo: e.target.value})}
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm"
                />
              </div>
              <div>
                <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">Mensaje *</label>
                <textarea
                  required
                  rows={3}
                  value={formData.mensaje}
                  onChange={(e) => setFormData({...formData, mensaje: e.target.value})}
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm resize-none"
                />
              </div>
              {modalMode === "crear" && (
                <>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">URL (opcional)</label>
                    <input
                      type="text"
                      value={formData.url}
                      onChange={(e) => setFormData({...formData, url: e.target.value})}
                      className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">ID Matriz (opcional)</label>
                    <input
                      type="number"
                      value={formData.id_matriz}
                      onChange={(e) => setFormData({...formData, id_matriz: e.target.value})}
                      className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-1">ID Item Matriz (opcional)</label>
                    <input
                      type="number"
                      value={formData.id_item_matriz}
                      onChange={(e) => setFormData({...formData, id_item_matriz: e.target.value})}
                      className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm"
                    />
                  </div>
                </>
              )}
              <div className="pt-4 flex gap-3">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-2.5 text-xs uppercase font-bold text-slate-500 bg-white border border-slate-200 rounded-lg">Cancelar</button>
                <button type="submit" disabled={modalLoading} className="flex-1 bg-lgc-primary text-white py-2.5 rounded-lg text-xs uppercase font-bold shadow-md disabled:opacity-50">
                  {modalLoading ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}