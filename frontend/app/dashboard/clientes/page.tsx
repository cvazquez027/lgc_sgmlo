"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link"; // IMPORTANTE: Agregamos el import de Link
import { usePermissions } from "../../hooks/usePermissions";

interface DatoContacto {
  id_tipo_contacto: string;
  valor: string;
}

interface Cliente {
  id_cliente: number;
  cuit: string;
  razon_social: string;
  nombre_fantasia: string;
  logo_path?: string;
  vigente: number;
  contactos?: DatoContacto[];
}

interface TipoContacto {
  id_tipo_contacto: number;
  descripcion: string;
}

export default function ClientesPage() {
  const router = useRouter();
  
  const { canRead, canEdit } = usePermissions();
  const [isCheckingPerms, setIsCheckingPerms] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsCheckingPerms(false), 100);
    return () => clearTimeout(timer);
  }, []);

  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [tiposContacto, setTiposContacto] = useState<TipoContacto[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [isUploadingLogo, setIsUploadingLogo] = useState(false); 

  const [formData, setFormData] = useState({ 
    id_cliente: "", 
    cuit: "", 
    razon_social: "", 
    nombre_fantasia: "", 
    logo_path: "", 
    vigente: 1,
    contactos: [] as DatoContacto[] 
  });

  const fetchTiposContacto = useCallback(async (token: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=tipo_contacto`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      setTiposContacto(data.registros || []);
    } catch (error) {
      console.error("Error cargando tipos de contacto:", error);
    }
  }, []);

  const fetchClientes = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) { router.push("/"); return; }

    try {
      setLoading(true);
      await fetchTiposContacto(token); 

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/clientes/leer.php`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      setClientes(data.registros || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [router, fetchTiposContacto]);

  useEffect(() => { 
    if (!isCheckingPerms && canRead("clientes")) fetchClientes(); 
  }, [fetchClientes, isCheckingPerms, canRead]);

  // --- LÓGICA DE SUBIDA DE LOGO (Seguridad UX) ---
  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024) {
      alert("El logo no puede superar los 2MB por políticas de optimización.");
      return;
    }

    setIsUploadingLogo(true);
    const token = localStorage.getItem("sgml_token");
    const formDataUpload = new FormData();
    formDataUpload.append("logo", file);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/clientes/subir_logo.php`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formDataUpload
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.mensaje || "Error al subir logo");

      setFormData(prev => ({ ...prev, logo_path: data.logo_path }));
    } catch (error: any) {
      alert("Error: " + error.message);
    } finally {
      setIsUploadingLogo(false);
    }
  };

  const handleAddContacto = () => setFormData(prev => ({ ...prev, contactos: [...prev.contactos, { id_tipo_contacto: "", valor: "" }] }));
  const handleRemoveContacto = (index: number) => setFormData(prev => ({ ...prev, contactos: prev.contactos.filter((_, i) => i !== index) }));
  const handleContactoChange = (index: number, field: keyof DatoContacto, value: string) => {
    setFormData(prev => {
      const nuevosContactos = [...prev.contactos];
      nuevosContactos[index] = { ...nuevosContactos[index], [field]: value };
      return { ...prev, contactos: nuevosContactos };
    });
  };

  const getInputType = (id_tipo: string) => {
    const tipo = tiposContacto.find(t => t.id_tipo_contacto.toString() === id_tipo);
    if (!tipo) return "text";
    const desc = tipo.descripcion.toLowerCase();
    if (desc.includes("mail")) return "email";
    if (desc.includes("tel") || desc.includes("cel")) return "tel";
    if (desc.includes("web") || desc.includes("link")) return "url";
    return "text";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit("clientes")) return; 

    setFormLoading(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/clientes/guardar.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setIsModalOpen(false);
        fetchClientes();
      } else {
        alert("Error al guardar el cliente.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setFormLoading(false);
    }
  };

  if (isCheckingPerms) return <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Verificando credenciales...</div>;
  if (!canRead("clientes")) return <div className="py-32 text-center text-red-500 font-bold text-2xl">Acceso Denegado</div>;

  return (
    <div className="space-y-6 animate-fade-in">
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
            Gestión de Clientes
          </h1>
        </div>

        {canEdit("clientes") && (
          <button 
            onClick={() => { 
              setFormData({id_cliente: "", cuit: "", razon_social: "", nombre_fantasia: "", logo_path: "", vigente: 1, contactos: []}); 
              setIsModalOpen(true); 
            }}
            className="bg-lgc-primary text-white py-2.5 px-6 rounded-lg font-bold text-xs uppercase tracking-widest hover:bg-lgc-accent transition-all shadow-md flex items-center gap-2"
          >
            <span>+</span> Nuevo Cliente
          </button>
        )}
      </div>

      {loading ? (
        <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Sincronizando base de datos...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {clientes.map(cliente => (
            <div key={cliente.id_cliente} className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 hover:border-lgc-primary transition-all group flex flex-col h-full">
              
              <div className="flex justify-between items-start mb-4">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest bg-slate-50 px-2 py-1 rounded">CUIT: {cliente.cuit}</span>
                <span className={`h-2.5 w-2.5 rounded-full ${cliente.vigente ? 'bg-green-500' : 'bg-red-500'}`} title={cliente.vigente ? 'Vigente' : 'Baja'}></span>
              </div>
              
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 rounded-lg border border-slate-200 bg-white shadow-sm flex items-center justify-center overflow-hidden shrink-0">
                  {cliente.logo_path ? (
                    <img src={`${process.env.NEXT_PUBLIC_IMG_URL}/${cliente.logo_path}`} alt={`Logo ${cliente.razon_social}`} className="w-full h-full object-contain p-1" />
                  ) : (
                    <span className="text-xl font-heading font-bold text-slate-300 uppercase">{cliente.razon_social?.charAt(0)}</span>
                  )}
                </div>
                <div>
                  <h3 className="font-heading text-lg text-slate-800 leading-tight group-hover:text-lgc-primary transition-colors">{cliente.razon_social}</h3>
                  <p className="text-xs font-bold text-slate-400 mt-1 uppercase tracking-widest">{cliente.nombre_fantasia || "Sin nombre fantasía"}</p>
                </div>
              </div>

              <div className="flex gap-2 mt-auto pt-4">
                {canEdit("clientes") && (
                  <button 
                    onClick={() => { 
                      setFormData({
                        ...cliente, 
                        id_cliente: cliente.id_cliente.toString(),
                        logo_path: cliente.logo_path || "",
                        contactos: cliente.contactos || [] 
                      }); 
                      setIsModalOpen(true); 
                    }}
                    className="flex-1 text-[10px] text-lgc-primary font-bold uppercase tracking-widest py-2.5 border border-lgc-primary/30 rounded-lg hover:bg-lgc-primary hover:text-white transition-all text-center"
                  >
                    Editar Perfil
                  </button>
                )}
                <button 
                  onClick={() => router.push(`/dashboard/clientes/${cliente.id_cliente}`)}
                  className="flex-1 text-[10px] font-bold uppercase tracking-widest py-2.5 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 transition-all text-center"
                >
                  Establecimientos
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {isModalOpen && canEdit("clientes") && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden my-8 border border-slate-200">
            <div className="p-6 bg-slate-50 border-b flex justify-between items-center sticky top-0 z-10">
              <h2 className="text-xl font-heading text-lgc-primary uppercase tracking-tight">
                {formData.id_cliente ? "Editar Cliente" : "Nuevo Cliente"}
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-2xl">&times;</button>
            </div>

            <form onSubmit={handleSubmit} className="p-8 space-y-6">
              
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b pb-2 mb-4">Datos Fiscales e Identidad</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  
                  <div className="col-span-1 md:col-span-2 bg-slate-50 border border-slate-100 rounded-xl p-4 flex items-center gap-5">
                    <div className="w-16 h-16 rounded-xl border-2 border-dashed border-slate-300 flex items-center justify-center bg-white overflow-hidden shadow-inner shrink-0">
                      {formData.logo_path ? (
                        <img src={`${process.env.NEXT_PUBLIC_IMG_URL}/${formData.logo_path}`} alt="Logo" className="w-full h-full object-contain p-1" />
                      ) : (
                        <svg className="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                      )}
                    </div>
                    <div className="relative flex-1">
                      <input type="file" onChange={handleLogoUpload} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" accept="image/jpeg, image/png, image/webp, image/svg+xml" disabled={isUploadingLogo} />
                      <div className={`px-4 py-2 rounded border text-xs font-bold uppercase tracking-widest flex items-center justify-center gap-2 w-fit transition-colors ${isUploadingLogo ? 'bg-slate-100 border-slate-200 text-slate-400' : 'bg-white border-lgc-primary text-lgc-primary hover:bg-lgc-primary/5'}`}>
                        {isUploadingLogo ? 'Subiendo...' : formData.logo_path ? 'Cambiar Imagen' : 'Subir Imagen'}
                      </div>
                      <p className="text-[9px] text-slate-400 mt-1 uppercase tracking-widest">Formatos permitidos: JPG, PNG o WEBP.</p>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1">Razón Social *</label>
                    <input required className="w-full p-3 bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm" value={formData.razon_social} onChange={e => setFormData({...formData, razon_social: e.target.value})} />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1">CUIT *</label>
                    <input required className="w-full p-3 bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm" value={formData.cuit} onChange={e => setFormData({...formData, cuit: e.target.value})} />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1">Nombre de Fantasía</label>
                    <input className="w-full p-3 bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm" value={formData.nombre_fantasia} onChange={e => setFormData({...formData, nombre_fantasia: e.target.value})} />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1">Estado Operativo *</label>
                    <select className="w-full p-3 bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm" value={formData.vigente} onChange={e => setFormData({...formData, vigente: parseInt(e.target.value)})}>
                      <option value={1}>ACTIVO</option>
                      <option value={0}>BAJA / INACTIVO</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center border-b pb-2 mb-4">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Información de Contacto</h3>
                  <button type="button" onClick={handleAddContacto} className="text-[10px] text-lgc-primary font-bold uppercase tracking-widest hover:text-lgc-accent transition-colors">+ Agregar Medio</button>
                </div>
                
                <div className="space-y-3 max-h-48 overflow-y-auto pr-2">
                  {formData.contactos.length === 0 ? (
                    <p className="text-sm text-slate-400 italic text-center py-4 bg-slate-50 rounded-lg border border-dashed">No hay contactos registrados.</p>
                  ) : (
                    formData.contactos.map((contacto, index) => (
                      <div key={index} className="flex gap-3 items-start animate-fade-in">
                        <select required className="w-1/3 p-3 text-sm bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none" value={contacto.id_tipo_contacto} onChange={(e) => handleContactoChange(index, 'id_tipo_contacto', e.target.value)}>
                          <option value="">Tipo...</option>
                          {tiposContacto.map(tipo => (
                            <option key={tipo.id_tipo_contacto} value={tipo.id_tipo_contacto}>{tipo.descripcion}</option>
                          ))}
                        </select>
                        
                        <input required type={getInputType(contacto.id_tipo_contacto)} placeholder="Valor de contacto..." className="w-full p-3 text-sm bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none" value={contacto.valor} onChange={(e) => handleContactoChange(index, 'valor', e.target.value)} />
                        
                        <button type="button" onClick={() => handleRemoveContacto(index)} className="p-3 text-red-400 hover:text-white hover:bg-red-500 rounded-lg transition-colors shrink-0" title="Eliminar contacto">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="flex gap-4 pt-6 mt-6 border-t border-slate-100">
                <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 py-3 text-xs uppercase tracking-widest font-bold text-slate-400 hover:text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">Cancelar</button>
                <button type="submit" disabled={formLoading} className="flex-1 bg-lgc-primary text-white py-3 rounded-lg font-bold text-xs uppercase tracking-widest shadow-md hover:bg-lgc-accent transition-all">
                  {formLoading ? 'Guardando...' : 'Guardar Cliente'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}