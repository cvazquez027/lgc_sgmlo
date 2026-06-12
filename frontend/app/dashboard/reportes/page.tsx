"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { usePermissions } from "../../hooks/usePermissions";

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
  const { canRead } = usePermissions();
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [vencimientos, setVencimientos] = useState<Vencimiento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marcando, setMarcando] = useState(false);

  const fetchAlertas = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) {
      router.push("/");
      return;
    }
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/leer.php`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      const data = await res.json();
      setAlertas(data.alertas || []);
    } catch (err: any) {
      console.error("Error cargando alertas:", err);
      setError("No se pudieron cargar las alertas.");
    }
  }, [router]);

  const fetchVencimientos = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/reportes/vencimientos.php`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      const data = await res.json();
      setVencimientos(data.vencimientos || []);
    } catch (err: any) {
      console.error("Error cargando vencimientos:", err);
      setError("No se pudieron cargar los vencimientos.");
    }
  }, []);

  const marcarComoLeida = async (idAlerta: number) => {
    setMarcando(true);
    const token = localStorage.getItem("sgml_token");
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/marcar_leida.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ id_alerta: idAlerta })
      });
      await fetchAlertas();
    } catch (err) {
      console.error("Error al marcar como leída", err);
    } finally {
      setMarcando(false);
    }
  };

  const marcarTodas = async () => {
    if (!confirm("¿Marcar todas las alertas como leídas?")) return;
    setMarcando(true);
    const token = localStorage.getItem("sgml_token");
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/marcar_leida.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ todas: true })
      });
      await fetchAlertas();
    } catch (err) {
      console.error("Error al marcar todas", err);
    } finally {
      setMarcando(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      await Promise.all([fetchAlertas(), fetchVencimientos()]);
      setLoading(false);
    };
    loadData();
  }, [fetchAlertas, fetchVencimientos]);

  if (loading) return <div className="py-20 text-center animate-pulse text-lgc-primary">Cargando alertas y vencimientos...</div>;
  if (error) return <div className="bg-red-50 text-red-600 p-6 rounded-xl text-center">⚠️ {error}</div>;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Cabecera */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex justify-between items-center flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-heading text-lgc-primary uppercase tracking-tight">Alertas y Vencimientos</h1>
          <p className="text-slate-500 text-sm mt-1">Notificaciones y fechas críticas de tus matrices</p>
        </div>
        {alertas.filter(a => !a.leido).length > 0 && (
          <button onClick={marcarTodas} disabled={marcando} className="bg-lgc-accent text-white px-4 py-2 rounded-lg text-xs font-bold uppercase hover:bg-[#D97920] transition disabled:opacity-50">
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