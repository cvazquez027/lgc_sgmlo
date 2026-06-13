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

export default function ReportesPage() {
  const router = useRouter();
  const { canRead, canEdit } = usePermissions();
  const toast = useToast();
  const confirm = useConfirm();
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [vencimientos, setVencimientos] = useState<Vencimiento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marcando, setMarcando] = useState(false);
  const hasShownAuthError = useRef(false); // Evita mostrar el mismo error múltiples veces

  const fetchAlertas = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    console.log("🔍 Token JWT (primeros 50 chars):", token?.substring(0, 50));
    
    if (!token) {
      router.push("/");
      return;
    }

    // Decodificar payload del token
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      console.log("🔍 Payload del token JWT:", payload);
      console.log("🔍 id_cliente del token:", payload.id_cliente);
      console.log("🔍 id_usuario del token:", payload.id_usuario);
    } catch(e) {
      console.error("Error decodificando token", e);
    }

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/leer.php`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log("📡 Response status:", res.status);
      
      if (res.status === 401) {
        localStorage.removeItem("sgml_token");
        router.push("/");
        return;
      }
      if (!res.ok) throw new Error(`Error ${res.status}`);
      
      const data = await res.json();
      console.log("📡 Respuesta completa de alertas:", data);
      console.log("📡 Alertas array:", data.alertas);
      console.log("📡 debug_id_cliente:", data.debug_id_cliente);
      console.log("📡 debug_total:", data.debug_total);
      
      setAlertas(data.alertas || []);
      if (data.debug_id_cliente === null) {
        console.warn("⚠️ El token no contiene id_cliente o es nulo.");
      }
      if ((data.alertas || []).length === 0 && data.debug_total === 0) {
        console.info("ℹ️ No hay alertas para este cliente.");
      }
    } catch (err: any) {
      console.error("❌ Error cargando alertas:", err);
      toast.showToast("Error", "No se pudieron cargar las alertas.", "error");
    }
  }, [router, toast]);

  const fetchVencimientos = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/reportes/vencimientos.php`, {
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
      if (error === "No se pudieron cargar los vencimientos.") setError(null);
    } catch (err: any) {
      console.error("Error cargando vencimientos:", err);
      if (err.message !== "Error 401" && !hasShownAuthError.current) {
        setError("No se pudieron cargar los vencimientos.");
        toast.showToast("Error", "No se pudieron cargar los vencimientos.", "error");
      }
    }
  }, [router, toast, error]);

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

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchAlertas(), fetchVencimientos()]);
      setLoading(false);
    };
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Solo se ejecuta una vez al montar el componente

  if (loading) return <div className="py-20 text-center animate-pulse text-lgc-primary">Cargando alertas y vencimientos...</div>;
  if (error) return <div className="bg-red-50 text-red-600 p-6 rounded-xl text-center">⚠️ {error}</div>;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* HEADER ESTILO MATRICES */}
      <div className="bg-[#005F78] text-white p-6 rounded-2xl shadow-lg border border-[#004D62] flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-3">
          <Link 
            href="/dashboard" 
            className="flex items-center justify-center w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 text-white transition-all group"
            title="Volver al inicio"
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

        {alertas.filter(a => !a.leido).length > 0 && (
          <button 
            onClick={marcarTodas} 
            disabled={marcando}
            className="bg-white text-lgc-primary hover:bg-slate-100 font-bold py-2.5 px-5 rounded-lg transition-all text-xs uppercase tracking-widest shadow-md disabled:opacity-50"
          >
            Marcar todas como leídas
          </button>
        )}
      </div>

      {/* Sección de Alertas */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-slate-50 px-6 py-3 border-b border-slate-200">
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-500">Notificaciones recientes</h2>
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
                  {!alerta.leido && (
                    <button
                      onClick={() => marcarComoLeida(alerta.id_alerta)}
                      disabled={marcando}
                      className="text-slate-400 hover:text-slate-600 text-xs font-bold uppercase whitespace-nowrap disabled:opacity-50"
                    >
                      Marcar leída
                    </button>
                  )}
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
                      <td className="p-4 text-xs text-slate-600">{new Date(v.vencimiento_plazo).toLocaleDateString('es-AR')}</td>
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
    </div>
  );
}