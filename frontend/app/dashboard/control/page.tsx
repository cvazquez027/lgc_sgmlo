"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useToast } from "../../providers/ToastProvider";
import { useConfirm } from "../../providers/ConfirmProvider";

interface ControlItem {
  id: number;
  descripcion: string;
  detalle: string | null;
  estado: "pendiente" | "en_curso" | "cumplido";
  porcentaje_avance: number | null;
  orden: number;
  categoria: "matriz" | "bo";
}

export default function ControlProyectoPage() {
  const router = useRouter();
  const toast = useToast();
  const confirm = useConfirm();
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<ControlItem[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editData, setEditData] = useState<Partial<ControlItem>>({});
  const [isAdmin, setIsAdmin] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  // Verificar si es admin (sin id_cliente en el token)
  useEffect(() => {
    const token = localStorage.getItem("sgml_token");
    let admin = false;
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const idCliente = payload.id_cliente || null;
        admin = !idCliente;
      } catch (e) {
        console.error("Error al decodificar token", e);
      }
    }
    setIsAdmin(admin);
    setIsChecking(false);
  }, []);

  const fetchData = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) {
      router.push("/");
      return;
    }
    try {
      setLoading(true);
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/control_proyecto/leer.php`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.status === 401) {
        router.push("/");
        return;
      }
      const data = await res.json();
      setItems(data.registros || []);
    } catch (err) {
      console.error(err);
      toast.showToast("Error", "No se pudieron cargar los datos.", "error");
    } finally {
      setLoading(false);
    }
  }, [router, toast]);

  useEffect(() => {
    if (!isChecking) {
      if (isAdmin) {
        fetchData();
      }
    }
  }, [isChecking, isAdmin, fetchData]);

  // --- Métricas calculadas ---
  const metrics = useMemo(() => {
    const categorias = ["matriz", "bo"];
    const result: Record<string, any> = {};

    categorias.forEach((cat) => {
      const filtered = items.filter((i) => i.categoria === cat);
      const total = filtered.length;
      const conPorcentaje = filtered.filter((i) => i.porcentaje_avance !== null && i.porcentaje_avance !== undefined);
      const sumaPorcentaje = conPorcentaje.reduce((acc, i) => acc + Number(i.porcentaje_avance), 0);
      const promedio = conPorcentaje.length > 0 ? sumaPorcentaje / conPorcentaje.length : 0;

      const estados = ["pendiente", "en_curso", "cumplido"];
      const porEstado = estados.map((est) => ({
        estado: est,
        cantidad: filtered.filter((i) => i.estado === est).length,
      }));

      result[cat] = {
        total,
        promedio,
        porEstado,
      };
    });

    return result;
  }, [items]);

  const handleSave = async (id: number) => {
    if (!isAdmin) return;
    const data = { ...editData, id };
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/control_proyecto/guardar.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(data)
      });
      if (res.ok) {
        toast.showToast("Éxito", "Registro actualizado.", "success");
        setEditingId(null);
        fetchData();
      } else {
        const err = await res.json();
        toast.showToast("Error", err.mensaje || "Error al guardar.", "error");
      }
    } catch (err) {
      console.error(err);
      toast.showToast("Error", "Error de conexión.", "error");
    }
  };

  const handleDelete = async (id: number) => {
    if (!isAdmin) return;
    const ok = await confirm({
      title: "Eliminar",
      message: "¿Estás seguro de eliminar este registro?",
      confirmText: "Eliminar",
      cancelText: "Cancelar"
    });
    if (!ok) return;
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/control_proyecto/eliminar.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ id })
      });
      if (res.ok) {
        toast.showToast("Éxito", "Registro eliminado.", "success");
        fetchData();
      } else {
        const err = await res.json();
        toast.showToast("Error", err.mensaje || "Error al eliminar.", "error");
      }
    } catch (err) {
      console.error(err);
      toast.showToast("Error", "Error de conexión.", "error");
    }
  };

  const handleAddNew = async () => {
    if (!isAdmin) return;
    const newItem = {
      descripcion: "Nuevo ítem",
      detalle: "",
      estado: "pendiente" as const,
      porcentaje_avance: 0,
      orden: items.length,
      categoria: "matriz" as const,
    };
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/control_proyecto/guardar.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newItem)
      });
      if (res.ok) {
        toast.showToast("Éxito", "Nuevo ítem creado.", "success");
        fetchData();
      } else {
        const err = await res.json();
        toast.showToast("Error", err.mensaje || "Error al crear.", "error");
      }
    } catch (err) {
      console.error(err);
      toast.showToast("Error", "Error de conexión.", "error");
    }
  };

  const startEditing = (item: ControlItem) => {
    if (!isAdmin) return;
    setEditingId(item.id);
    setEditData({ ...item });
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditData({});
  };

  const renderCell = (item: ControlItem, field: keyof ControlItem) => {
    const isEditing = editingId === item.id;
    if (isEditing && isAdmin) {
      if (field === "descripcion") {
        return (
          <input
            type="text"
            className="w-full p-1 border border-slate-300 rounded focus:ring-2 focus:ring-lgc-primary outline-none"
            value={editData.descripcion || ""}
            onChange={(e) => setEditData({ ...editData, descripcion: e.target.value })}
          />
        );
      }
      if (field === "detalle") {
        return (
          <input
            type="text"
            className="w-full p-1 border border-slate-300 rounded focus:ring-2 focus:ring-lgc-primary outline-none"
            value={editData.detalle || ""}
            onChange={(e) => setEditData({ ...editData, detalle: e.target.value })}
          />
        );
      }
      if (field === "estado") {
        return (
          <select
            className="w-full p-1 border border-slate-300 rounded focus:ring-2 focus:ring-lgc-primary outline-none"
            value={editData.estado || "pendiente"}
            onChange={(e) => setEditData({ ...editData, estado: e.target.value as any })}
          >
            <option value="pendiente">Pendiente</option>
            <option value="en_curso">En curso</option>
            <option value="cumplido">Cumplido</option>
          </select>
        );
      }
      if (field === "porcentaje_avance") {
        const val = editData.porcentaje_avance !== undefined && editData.porcentaje_avance !== null
          ? Math.round(editData.porcentaje_avance * 100)
          : "";
        return (
          <input
            type="number"
            min="0"
            max="100"
            className="w-full p-1 border border-slate-300 rounded focus:ring-2 focus:ring-lgc-primary outline-none"
            value={val}
            onChange={(e) => {
              const v = e.target.value === "" ? null : parseFloat(e.target.value);
              setEditData({ ...editData, porcentaje_avance: v !== null ? v / 100 : null });
            }}
          />
        );
      }
      if (field === "categoria") {
        return (
          <select
            className="w-full p-1 border border-slate-300 rounded focus:ring-2 focus:ring-lgc-primary outline-none"
            value={editData.categoria || "matriz"}
            onChange={(e) => setEditData({ ...editData, categoria: e.target.value as "matriz" | "bo" })}
          >
            <option value="matriz">Matriz</option>
            <option value="bo">Boletín Oficial</option>
          </select>
        );
      }
    }
    // Vista normal
    if (field === "descripcion") return <span className="font-medium">{item.descripcion}</span>;
    if (field === "detalle") return <span className="text-slate-600">{item.detalle || "—"}</span>;
    if (field === "estado") {
      const colors: Record<string, string> = {
        pendiente: "bg-slate-100 text-slate-600",
        en_curso: "bg-amber-100 text-amber-700",
        cumplido: "bg-green-100 text-green-700"
      };
      const labels: Record<string, string> = {
        pendiente: "Pendiente",
        en_curso: "En curso",
        cumplido: "Cumplido"
      };
      return <span className={`px-2 py-1 rounded-full text-xs font-bold ${colors[item.estado]}`}>{labels[item.estado]}</span>;
    }
    if (field === "porcentaje_avance") {
      const pct = item.porcentaje_avance !== null && item.porcentaje_avance !== undefined
        ? Math.round(item.porcentaje_avance * 100)
        : "—";
      return <span>{pct}%</span>;
    }
    if (field === "categoria") {
      const labels = { matriz: "Matriz", bo: "Boletín Oficial" };
      return <span className="text-xs font-bold uppercase">{labels[item.categoria] || item.categoria}</span>;
    }
    return null;
  };

  if (isChecking) return <div className="py-20 text-center animate-pulse text-lgc-primary">Verificando accesos...</div>;
  if (!isAdmin) return <div className="py-32 text-center text-red-500 font-bold text-2xl">Acceso Denegado</div>;

  return (
    <div className="space-y-4 animate-fade-in">
      {/* HEADER */}
      <div className="bg-[#005F78] text-white px-6 py-4 rounded-xl shadow-md flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="flex items-center justify-center w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 text-white transition-all group">
            <svg className="w-5 h-5 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div className="h-8 w-px bg-white/30 hidden md:block"></div>
          <h1 className="text-xl font-heading font-bold uppercase tracking-tight">Tablero de Control del Proyecto</h1>
        </div>
        {isAdmin && (
          <button
            onClick={handleAddNew}
            className="bg-white text-lgc-primary hover:bg-slate-100 font-bold py-2 px-4 rounded-lg transition-all text-xs uppercase tracking-widest shadow-md flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" /></svg>
            Agregar
          </button>
        )}
      </div>

      {/* RECUADROS DE MÉTRICAS */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Matrices */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-sm font-bold uppercase text-slate-700 tracking-widest">📊 Matrices</h2>
            <span className="text-xs font-bold text-slate-400">{metrics.matriz?.total || 0} ítems</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-500">Avance promedio</span>
                <span className="font-bold text-lgc-primary">
                  {metrics.matriz?.total > 0 ? `${Math.round((metrics.matriz?.promedio || 0) * 100)}%` : '0%'}
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2.5">
                <div
                  className="bg-lgc-primary h-2.5 rounded-full transition-all"
                  style={{ width: `${Math.round((metrics.matriz?.promedio || 0) * 100)}%` }}
                ></div>
              </div>
            </div>
            <div className="flex gap-3 text-xs">
              {metrics.matriz?.porEstado.map((e: any) => {
                const colors = {
                  pendiente: "bg-slate-100 text-slate-600",
                  en_curso: "bg-amber-100 text-amber-700",
                  cumplido: "bg-green-100 text-green-700"
                };
                const labels = {
                  pendiente: "Pendiente",
                  en_curso: "En curso",
                  cumplido: "Cumplido"
                };
                return (
                  <div key={e.estado} className="flex flex-col items-center">
                    <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${colors[e.estado as keyof typeof colors]}`}>
                      {labels[e.estado as keyof typeof labels]}
                    </span>
                    <span className="text-[10px] font-bold text-slate-500 mt-0.5">{e.cantidad}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Boletines Oficiales */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-sm font-bold uppercase text-slate-700 tracking-widest">📰 Boletines Oficiales</h2>
            <span className="text-xs font-bold text-slate-400">{metrics.bo?.total || 0} ítems</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-500">Avance promedio</span>
                <span className="font-bold text-lgc-accent">
                  {metrics.bo?.total > 0 ? `${Math.round((metrics.bo?.promedio || 0) * 100)}%` : '0%'}
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2.5">
                <div
                  className="bg-lgc-accent h-2.5 rounded-full transition-all"
                  style={{ width: `${Math.round((metrics.bo?.promedio || 0) * 100)}%` }}
                ></div>
              </div>
            </div>
            <div className="flex gap-3 text-xs">
              {metrics.bo?.porEstado.map((e: any) => {
                const colors = {
                  pendiente: "bg-slate-100 text-slate-600",
                  en_curso: "bg-amber-100 text-amber-700",
                  cumplido: "bg-green-100 text-green-700"
                };
                const labels = {
                  pendiente: "Pendiente",
                  en_curso: "En curso",
                  cumplido: "Cumplido"
                };
                return (
                  <div key={e.estado} className="flex flex-col items-center">
                    <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${colors[e.estado as keyof typeof colors]}`}>
                      {labels[e.estado as keyof typeof labels]}
                    </span>
                    <span className="text-[10px] font-bold text-slate-500 mt-0.5">{e.cantidad}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* TABLA */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Cargando datos...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-50 text-[10px] uppercase tracking-widest text-slate-500 border-b">
                <tr>
                  <th className="p-4">Categoría</th>
                  <th className="p-4">Descripción</th>
                  <th className="p-4">Detalle</th>
                  <th className="p-4">Estado</th>
                  <th className="p-4">% Avance</th>
                  {isAdmin && <th className="p-4 text-center">Acciones</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.length === 0 ? (
                  <tr><td colSpan={6} className="p-8 text-center text-slate-400 italic">No hay ítems registrados.</td></tr>
                ) : (
                  items.map((item) => {
                    const isEditing = editingId === item.id;
                    return (
                      <tr key={item.id} className={`hover:bg-slate-50 transition ${isEditing ? 'bg-blue-50' : ''}`}>
                        <td className="p-4">{renderCell(item, "categoria")}</td>
                        <td className="p-4">{renderCell(item, "descripcion")}</td>
                        <td className="p-4">{renderCell(item, "detalle")}</td>
                        <td className="p-4">{renderCell(item, "estado")}</td>
                        <td className="p-4">{renderCell(item, "porcentaje_avance")}</td>
                        {isAdmin && (
                          <td className="p-4 text-center">
                            {isEditing ? (
                              <div className="flex justify-center gap-2">
                                <button onClick={() => handleSave(item.id)} className="text-green-600 hover:text-green-800 font-bold text-xs uppercase">Guardar</button>
                                <button onClick={cancelEditing} className="text-slate-400 hover:text-slate-600 font-bold text-xs uppercase">Cancelar</button>
                              </div>
                            ) : (
                              <div className="flex justify-center gap-2">
                                <button onClick={() => startEditing(item)} className="text-blue-500 hover:text-blue-700" title="Editar">
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                                </button>
                                <button onClick={() => handleDelete(item.id)} className="text-red-400 hover:text-red-600" title="Eliminar">
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                </button>
                              </div>
                            )}
                          </td>
                        )}
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
  );
}