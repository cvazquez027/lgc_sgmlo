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
  color_estado?: string;
}

export default function ReportesPage() {
  const router = useRouter();
  const { canRead } = usePermissions();
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [vencimientos, setVencimientos] = useState<Vencimiento[]>([]);
  const [loading, setLoading] = useState(true);
  const [marcando, setMarcando] = useState(false);

  const fetchAlertas = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/leer.php`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();
    if (res.ok) setAlertas(data.alertas || []);
  }, []);

  const fetchVencimientos = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/reportes/vencimientos.php`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();
    if (res.ok) setVencimientos(data.vencimientos || []);
  }, []);

  const marcarComoLeida = async (idAlerta: number) => {
    setMarcando(true);
    const token = localStorage.getItem("sgml_token");
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/marcar_leida.php`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ id_alerta: idAlerta })
    });
    await fetchAlertas();
    setMarcando(false);
  };

  const marcarTodas = async () => {
    if (!confirm("¿Marcar todas las alertas como leídas?")) return;
    setMarcando(true);
    const token = localStorage.getItem("sgml_token");
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/marcar_leida.php`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ todas: true })
    });
    await fetchAlertas();
    setMarcando(false);
  };

  useEffect(() => {
    fetchAlertas();
    fetchVencimientos();
    setLoading(false);
  }, [fetchAlertas, fetchVencimientos]);

  if (loading) return <div className="py-20 text-center animate-pulse text-lgc-primary">Cargando alertas...</div>;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Cabecera */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-heading text-lgc-primary uppercase tracking-tight">Alertas y Vencimientos</h1>
          <p className="text-slate-500 text-sm mt-1">Notificaciones y fechas críticas de tus matrices</p>
        </div>
        {alertas.filter(a => !a.leido).length > 0 && (
          <button onClick={marcarTodas} disabled={marcando} className="bg-lgc-accent text-white px-4 py-2 rounded-lg text-xs font-bold uppercase hover:bg-[#D97920] transition">
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
                      className="text-slate-400 hover:text-slate-600 text-xs font-bold uppercase whitespace-nowrap"
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
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-500">Próximos vencimientos</h2>
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
                  const estaProximo = v.dias_restantes >= 0 && v.dias_restantes <= 30;
                  let estadoClase = "";
                  if (esVencido) estadoClase = "text-red-600 bg-red-50 border-red-200";
                  else if (estaProximo) estadoClase = "text-amber-600 bg-amber-50 border-amber-200";
                  else estadoClase = "text-green-600 bg-green-50 border-green-200";
                  return (
                    <tr key={`${v.id_matriz}-${v.id_item_matriz}`} className="hover:bg-slate-50 transition">
                      <td className="p-4 font-bold text-slate-700 text-sm">{v.nombre_matriz}</td>
                      <td className="p-4 text-slate-600 text-xs">{v.item_resumen || "Sin descripción"}</td>
                      <td className="p-4 text-xs text-slate-600">{new Date(v.vencimiento_plazo).toLocaleDateString('es-AR')}</td>
                      <td className="p-4">
                        <span className={`text-[10px] font-bold uppercase px-2 py-1 rounded-full border ${estadoClase}`}>
                          {esVencido ? "Vencido" : v.dias_restantes === 0 ? "Vence hoy" : `${v.dias_restantes} días`}
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