"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { usePermissions } from "../../hooks/usePermissions";
import Link from "next/link";
import { useToast } from "../../providers/ToastProvider";
import { useConfirm } from "../../providers/ConfirmProvider";

interface Usuario {
  id_usuario: number;
  nombre_completo: string;
  email: string;
  rol_nombre: string;
  id_cliente: number | null;
  razon_social: string | null;
  vigente: number;
}

interface Rol {
  id_rol: number;
  descripcion: string;
}

interface Cliente {
  id_cliente: number;
  razon_social: string;
}

interface AuditoriaLog {
  id_auditoria: number;
  tabla_afectada: string;
  accion: string;
  id_registro: number;
  id_usuario: number;
  usuario_nombre: string | null;
  ip_origen: string;
  fecha_evento: string;
  datos_json: any;
}

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [roles, setRoles] = useState<Rol[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [logs, setLogs] = useState<AuditoriaLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"usuarios" | "auditoria">("usuarios");
  const router = useRouter();

  const { canRead, canEdit } = usePermissions();
  const canViewAudit = canRead("auditoria");
  const toast = useToast();
  const confirm = useConfirm(); // reservado para futuras acciones destructivas

  const [isCheckingPerms, setIsCheckingPerms] = useState(true);
  const [selectedAuditLog, setSelectedAuditLog] = useState<AuditoriaLog | null>(null);
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsCheckingPerms(false), 100);
    return () => clearTimeout(timer);
  }, []);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"crear" | "editar">("crear");
  const [formLoading, setFormLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    id_usuario: "",
    nombre: "",
    apellido: "",
    email: "",
    password: "",
    id_rol: "",
    id_cliente: "",
    vigente: 1
  });

  const fetchData = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) { router.push("/"); return; }

    try {
      setLoading(true);
      
      const resUser = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/usuarios/leer.php`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const dataUser = await resUser.json();
      if (!resUser.ok) throw new Error(dataUser.mensaje || "Error al cargar usuarios");
      setUsuarios(dataUser.registros || []);

      const resRoles = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/roles/leer.php`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const dataRoles = await resRoles.json();
      setRoles(dataRoles.registros || []);

      const resClientes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/clientes/leer.php`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const dataClientes = await resClientes.json();
      setClientes(dataClientes.registros || []);

    } catch (err: any) {
      console.error(err);
      toast.showToast("Error", err.message || "Error al cargar datos", "error");
    } finally {
      setLoading(false);
    }
  }, [router, toast]);

  const fetchAuditoria = useCallback(async () => {
    if (!canViewAudit) return;
    const token = localStorage.getItem("sgml_token");
    if (!token) { router.push("/"); return; }
    try {
      setLoading(true);
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auditoria/leer.php?limit=200`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.mensaje || "Error al cargar auditoría");
      setLogs(data.registros || []);
    } catch (err: any) {
      console.error("Error cargando auditoría", err);
      toast.showToast("Error", err.message, "error");
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [canViewAudit, router, toast]);

  useEffect(() => {
    if (!isCheckingPerms && canRead("usuarios")) {
      if (activeTab === "usuarios") {
        fetchData();
      } else if (activeTab === "auditoria" && canViewAudit) {
        fetchAuditoria();
      }
    }
  }, [fetchData, fetchAuditoria, isCheckingPerms, canRead, activeTab, canViewAudit]);

  const openCrearModal = () => {
    if (!canEdit("usuarios")) {
      toast.showToast("Permiso denegado", "No tienes permiso para crear usuarios", "warning");
      return;
    }
    setModalMode("crear");
    setFormData({ id_usuario: "", nombre: "", apellido: "", email: "", password: "", id_rol: "", id_cliente: "", vigente: 1 });
    setIsModalOpen(true);
  };

  const openEditarModal = (user: Usuario) => {
    if (!canEdit("usuarios")) {
      toast.showToast("Permiso denegado", "No tienes permiso para editar usuarios", "warning");
      return;
    }
    setModalMode("editar");
    const nombres = user.nombre_completo.split(" ");
    const rolId = roles.find(r => r.descripcion === user.rol_nombre)?.id_rol.toString() || "";

    setFormData({
      id_usuario: user.id_usuario.toString(),
      nombre: nombres[0] || "",
      apellido: nombres.slice(1).join(" ") || "",
      email: user.email,
      password: "", 
      id_rol: rolId,
      id_cliente: user.id_cliente?.toString() || "",
      vigente: user.vigente
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit("usuarios")) {
      toast.showToast("Permiso denegado", "No tienes permiso para realizar esta acción", "warning");
      return;
    }

    setFormLoading(true);
    const token = localStorage.getItem("sgml_token");

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/usuarios/guardar.php`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(formData),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.mensaje || "Error en la operación");

      toast.showToast("Éxito", data.mensaje || "Usuario guardado correctamente", "success");
      setIsModalOpen(false);
      fetchData(); 
    } catch (err: any) {
      toast.showToast("Error", err.message, "error");
    } finally {
      setFormLoading(false);
    }
  };

  const getAccionBadge = (accion: string) => {
    switch (accion) {
      case 'INSERT': return <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs font-bold">INSERT</span>;
      case 'UPDATE': return <span className="bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full text-xs font-bold">UPDATE</span>;
      case 'DELETE': return <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded-full text-xs font-bold">DELETE</span>;
      default: return <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded-full text-xs font-bold">{accion}</span>;
    }
  };

  if (isCheckingPerms) {
    return <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Verificando credenciales de seguridad...</div>;
  }

  if (!canRead("usuarios")) {
    return (
      <div className="flex flex-col items-center justify-center py-32 bg-white rounded-xl shadow-sm border border-red-100">
        <div className="text-red-500 text-6xl mb-4">🔒</div>
        <h2 className="text-2xl font-heading text-slate-800 uppercase tracking-tight mb-2">Acceso Denegado</h2>
        <p className="text-slate-500 font-sans">Su perfil no cuenta con los privilegios necesarios para visualizar este módulo.</p>
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
            Gestión de Usuarios y Seguridad
          </h1>
        </div>
        
        {activeTab === "usuarios" && canEdit("usuarios") && (
          <button 
            onClick={openCrearModal}
            className="bg-white text-lgc-primary hover:bg-slate-50 font-bold py-2.5 px-6 rounded-lg transition-all shadow-md text-xs uppercase tracking-widest flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" /></svg>
            Nuevo Usuario
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 bg-white rounded-t-xl">
        <nav className="flex space-x-6 px-6" aria-label="Tabs">
          <button
            onClick={() => setActiveTab("usuarios")}
            className={`py-3 px-1 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "usuarios"
                ? "border-lgc-primary text-lgc-primary"
                : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
            }`}
          >
            Usuarios del Sistema
          </button>
          {canViewAudit && (
            <button
              onClick={() => setActiveTab("auditoria")}
              className={`py-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === "auditoria"
                  ? "border-lgc-primary text-lgc-primary"
                  : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
              }`}
            >
              Auditoría de Cambios
            </button>
          )}
        </nav>
      </div>

      {/* Contenido de la pestaña Usuarios */}
      {activeTab === "usuarios" && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          {loading ? (
            <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Sincronizando base de datos...</div>
          ) : (
            <table className="w-full text-left font-sans">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-400 text-[10px] uppercase tracking-[0.2em]">
                  <th className="p-5 font-bold">Identidad</th>
                  <th className="p-5 font-bold">Empresa / Cliente</th>
                  <th className="p-5 font-bold">Rol</th>
                  <th className="p-5 font-bold">Estado</th>
                  <th className="p-5 font-bold text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {usuarios.map((user) => (
                  <tr key={user.id_usuario} className="hover:bg-slate-50/50 transition-colors">
                    <td className="p-5">
                      <div className="font-bold text-slate-700">{user.nombre_completo}</div>
                      <div className="text-xs text-slate-400">{user.email}</div>
                    </td>
                    <td className="p-5 text-sm text-slate-600 font-medium">
                      {user.razon_social ? (
                         <span>{user.razon_social}</span>
                      ) : (
                         <span className="text-xs font-bold text-lgc-primary uppercase tracking-widest bg-lgc-primary/10 px-2 py-1 rounded">Usuario Interno</span>
                      )}
                    </td>
                    <td className="p-5 text-xs">
                      <span className="bg-slate-100 text-slate-600 px-2 py-1 rounded font-bold uppercase tracking-tighter">
                        {user.rol_nombre}
                      </span>
                    </td>
                    <td className="p-5 text-xs">
                      <span className={`px-3 py-1 rounded-full font-bold ${user.vigente === 1 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {user.vigente === 1 ? 'ACTIVO' : 'BAJA'}
                      </span>
                    </td>
                    <td className="p-5 text-right">
                      {canEdit("usuarios") ? (
                        <button onClick={() => openEditarModal(user)} className="text-lgc-primary hover:text-lgc-accent text-xs font-bold uppercase tracking-widest">
                          Editar
                        </button>
                      ) : (
                        <span className="text-slate-300 text-[10px] font-bold uppercase tracking-widest cursor-not-allowed">
                          Solo Lectura
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Contenido de la pestaña Auditoría */}
      {activeTab === "auditoria" && (
        canViewAudit ? (
          <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-x-auto">
            {loading ? (
              <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Cargando historial de auditoría...</div>
            ) : logs.length === 0 ? (
              <div className="py-20 text-center text-slate-400">No se encontraron registros de auditoría.</div>
            ) : (
              <table className="w-full text-left font-sans text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 text-[10px] uppercase tracking-wider">
                    <th className="p-3">Fecha</th>
                    <th className="p-3">Usuario</th>
                    <th className="p-3">Tabla</th>
                    <th className="p-3">Acción</th>
                    <th className="p-3">ID Registro</th>
                    <th className="p-3">IP Origen</th>
                    <th className="p-3">Detalle</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {logs.map((log) => (
                    <tr key={log.id_auditoria} className="hover:bg-slate-50/50">
                      <td className="p-3 whitespace-nowrap text-xs">
                        {new Date(log.fecha_evento).toLocaleString()}
                      </td>
                      <td className="p-3 text-xs font-medium">
                        {log.usuario_nombre || `Usuario #${log.id_usuario}`}
                      </td>
                      <td className="p-3 text-xs font-mono">
                        {log.tabla_afectada}
                      </td>
                      <td className="p-3">
                        {getAccionBadge(log.accion)}
                      </td>
                      <td className="p-3 text-xs">
                        {log.id_registro}
                      </td>
                      <td className="p-3 text-xs font-mono">
                        {log.ip_origen || '-'}
                      </td>
                      <td className="p-3">
                        <button
                          onClick={() => {
                            setSelectedAuditLog(log);
                            setIsAuditModalOpen(true);
                          }}
                          className="text-lgc-primary hover:text-lgc-accent text-xs font-bold uppercase tracking-widest"
                        >
                          Ver JSON
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        ) : (
          <div className="bg-white p-12 text-center rounded-xl shadow-sm border border-red-100">
            <div className="text-red-500 text-4xl mb-2">🔒</div>
            <p className="text-slate-500">No tienes permiso para ver la auditoría.</p>
          </div>
        )
      )}

      {/* Modal de creación/edición de usuarios */}
      {isModalOpen && canEdit("usuarios") && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden border border-slate-200">
            <div className="p-6 bg-slate-50 border-b flex justify-between items-center">
              <h2 className="text-xl font-heading text-lgc-primary uppercase tracking-tight">
                {modalMode === "crear" ? "Registrar Usuario" : "Modificar Perfil"}
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-2xl">&times;</button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-8 space-y-5">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2">Nombre</label>
                  <input required type="text" value={formData.nombre} onChange={(e) => setFormData({...formData, nombre: e.target.value})} className="w-full px-4 py-3 bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none" />
                </div>
                <div>
                  <label className="block text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2">Apellido</label>
                  <input type="text" value={formData.apellido} onChange={(e) => setFormData({...formData, apellido: e.target.value})} className="w-full px-4 py-3 bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2">Email Corporativo</label>
                  <input required type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} className="w-full px-4 py-3 bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none" />
                </div>
                <div>
                  <label className="block text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2">Contraseña</label>
                  <input 
                    type="password" 
                    placeholder={modalMode === "crear" ? "Obligatoria" : "Opcional (solo si cambia)"}
                    required={modalMode === "crear"} 
                    value={formData.password} 
                    onChange={(e) => setFormData({...formData, password: e.target.value})} 
                    className="w-full px-4 py-3 bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none" 
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6 border-t border-slate-100 pt-5">
                <div>
                  <label className="block text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2">Asignar Cliente/Empresa</label>
                  <select 
                    value={formData.id_cliente} 
                    onChange={(e) => setFormData({...formData, id_cliente: e.target.value})}
                    className="w-full px-4 py-3 bg-white border border-slate-200 rounded-lg outline-none focus:border-lgc-primary font-sans"
                  >
                    <option value="">Seleccione Cliente (Opcional)...</option>
                    {clientes.map(c => (
                      <option key={c.id_cliente} value={c.id_cliente}>{c.razon_social}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2">Rol Asignado *</label>
                  <select 
                    required 
                    value={formData.id_rol} 
                    onChange={(e) => setFormData({...formData, id_rol: e.target.value})}
                    className="w-full px-4 py-3 bg-white border border-slate-200 rounded-lg outline-none focus:border-lgc-primary font-sans"
                  >
                    <option value="">Seleccione Rol...</option>
                    {roles.map(r => (
                      <option key={r.id_rol} value={r.id_rol}>{r.descripcion}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="pt-6 flex gap-4">
                <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 py-3 text-xs uppercase tracking-widest font-bold text-slate-400 hover:text-slate-600 transition-colors">Cancelar</button>
                <button type="submit" disabled={formLoading} className="flex-1 bg-lgc-primary text-white py-3 rounded-lg text-xs uppercase tracking-widest font-bold shadow-lg hover:bg-lgc-accent transition-all">
                  {formLoading ? "Procesando..." : "Guardar Cambios"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal para visualizar JSON de auditoría */}
      {isAuditModalOpen && selectedAuditLog && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white w-full max-w-3xl rounded-2xl shadow-2xl overflow-hidden border border-slate-200">
            <div className="p-6 bg-slate-50 border-b flex justify-between items-center">
              <div>
                <h2 className="text-lg font-heading text-lgc-primary uppercase tracking-tight">
                  Detalle del cambio - {selectedAuditLog.tabla_afectada} #{selectedAuditLog.id_registro}
                </h2>
                <p className="text-xs text-slate-500 mb-2">
                  Contenido del registro afectado ({selectedAuditLog.tabla_afectada} ID {selectedAuditLog.id_registro}):
                </p>
              </div>
              <button onClick={() => setIsAuditModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-2xl">&times;</button>
            </div>
            <div className="p-6 max-h-[70vh] overflow-auto">
              <pre className="text-xs bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto">
                {JSON.stringify(selectedAuditLog.datos_json, null, 2)}
              </pre>
            </div>
            <div className="p-4 bg-slate-50 border-t flex justify-end">
              <button onClick={() => setIsAuditModalOpen(false)} className="px-5 py-2 bg-lgc-primary text-white rounded-lg text-xs uppercase tracking-widest hover:bg-lgc-accent transition-all">Cerrar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}