"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
// Importamos nuestro nuevo guardián de seguridad
import { usePermissions } from "../../hooks/usePermissions";
import Link from "next/link";

interface Usuario {
  id_usuario: number;
  nombre_completo: string;
  email: string;
  rol_nombre: string;
  id_cliente: number;
  razon_social: string;
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

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [roles, setRoles] = useState<Rol[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const router = useRouter();

  // --- INTEGRACIÓN DE SEGURIDAD (CAPA UI) ---
  const { canRead, canEdit } = usePermissions();
  const [isCheckingPerms, setIsCheckingPerms] = useState(true);

  // Damos un pequeño respiro para que el hook lea el localStorage
  // antes de decidir si bloqueamos o no la pantalla.
  useEffect(() => {
    const timer = setTimeout(() => setIsCheckingPerms(false), 100);
    return () => clearTimeout(timer);
  }, []);
  // ------------------------------------------

  // Estados del Modal
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
      
      // 1. Cargar Usuarios
      const resUser = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/usuarios/leer.php`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const dataUser = await resUser.json();
      setUsuarios(dataUser.registros || []);

      // 2. Cargar Roles (para el select)
      const resRoles = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/roles/leer.php`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const dataRoles = await resRoles.json();
      setRoles(dataRoles.registros || []);

      // 3. Cargar Clientes (para el select - Esto evitará el error de FK)
      const resClientes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/clientes/leer.php`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const dataClientes = await resClientes.json();
      setClientes(dataClientes.registros || []);

    } catch (err: any) {
      setError("Error al sincronizar con el servidor");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    // Solo traemos datos si pasó la barrera de seguridad visual
    if (!isCheckingPerms && canRead("usuarios")) {
      fetchData();
    }
  }, [fetchData, isCheckingPerms, canRead]);

  const openCrearModal = () => {
    // Doble validación por si alguien manipula el DOM
    if (!canEdit("usuarios")) return; 
    setModalMode("crear");
    setFormData({ id_usuario: "", nombre: "", apellido: "", email: "", password: "", id_rol: "", id_cliente: "", vigente: 1 });
    setIsModalOpen(true);
  };

  const openEditarModal = (user: Usuario) => {
    if (!canEdit("usuarios")) return;
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
    if (!canEdit("usuarios")) return; // Bloqueo de seguridad

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

      alert(data.mensaje);
      setIsModalOpen(false);
      fetchData(); 
    } catch (err: any) {
      alert("Error crítico: " + err.message);
    } finally {
      setFormLoading(false);
    }
  };

  // --- RENDERIZADO CONDICIONAL DE SEGURIDAD ---
  if (isCheckingPerms) {
    return <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Verificando credenciales de seguridad...</div>;
  }

  // Si no tiene el permiso explícito para leer, le bloqueamos la vista
  if (!canRead("usuarios")) {
    return (
      <div className="flex flex-col items-center justify-center py-32 bg-white rounded-xl shadow-sm border border-red-100">
        <div className="text-red-500 text-6xl mb-4">🔒</div>
        <h2 className="text-2xl font-heading text-slate-800 uppercase tracking-tight mb-2">Acceso Denegado</h2>
        <p className="text-slate-500 font-sans">Su perfil no cuenta con los privilegios necesarios para visualizar este módulo.</p>
      </div>
    );
  }
  // --------------------------------------------

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-white p-6 rounded-xl shadow-sm border border-slate-100">
        {/* BLOQUE NUEVO: Botón de Volver + Título Centrados */}
        <div className="flex items-center gap-3">
          <Link 
            href="/dashboard" 
            className="flex items-center justify-center w-8 h-8 rounded-full text-slate-400 hover:bg-slate-100 hover:text-lgc-primary transition-all group"
            title="Volver al inicio"
          >
            <svg className="w-5 h-5 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <h1 className="text-xl font-bold text-lgc-primary uppercase tracking-wide m-0 leading-none">
            Gestión de Usuarios
          </h1>
        </div>
        
        {/* Solo mostramos el botón si tiene permiso de escritura */}
        {canEdit("usuarios") && (
          <button 
            onClick={openCrearModal}
            className="bg-lgc-primary hover:bg-lgc-accent text-white font-bold py-2.5 px-6 rounded-lg transition-all shadow-md text-xs uppercase tracking-widest"
          >
            + Nuevo Usuario
          </button>
        )}
      </div>

      {loading ? (
        <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Sincronizando base de datos...</div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
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
                    {user.razon_social || "Sin asignar"}
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
                    {/* Botón dinámico según permisos */}
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
        </div>
      )}

      {/* MODAL SISTEMA */}
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
                  <label className="block text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-2">Asignar Cliente/Empresa *</label>
                  <select 
                    required 
                    value={formData.id_cliente} 
                    onChange={(e) => setFormData({...formData, id_cliente: e.target.value})}
                    className="w-full px-4 py-3 bg-white border border-slate-200 rounded-lg outline-none focus:border-lgc-primary font-sans"
                  >
                    <option value="">Seleccione Cliente...</option>
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
    </div>
  );
}