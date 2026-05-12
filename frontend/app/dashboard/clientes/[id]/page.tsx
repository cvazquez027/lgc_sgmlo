"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import { usePermissions } from "../../../hooks/usePermissions";

interface DatoContacto {
  id_tipo_contacto: string;
  valor: string;
}

interface Establecimiento {
  id_cliente_establecimiento: number;
  descripcion: string;
  jurisdiccion_nombre: string;
  id_jurisdiccion: number;
  vigente: number;
  contactos?: DatoContacto[];
}

interface Jurisdiccion {
  id_jurisdiccion: number;
  descripcion: string;
}

interface TipoContacto {
  id_tipo_contacto: number;
  descripcion: string;
}

export default function EstablecimientosPage() {
  const { id } = useParams(); 
  const router = useRouter();
  
  const { canRead, canEdit } = usePermissions();
  const [isCheckingPerms, setIsCheckingPerms] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsCheckingPerms(false), 100);
    return () => clearTimeout(timer);
  }, []);

  const [establecimientos, setEstablecimientos] = useState<Establecimiento[]>([]);
  const [jurisdicciones, setJurisdicciones] = useState<Jurisdiccion[]>([]);
  const [tiposContacto, setTiposContacto] = useState<TipoContacto[]>([]);
  
  // Estado para la identidad corporativa del cliente
  const [clienteActual, setClienteActual] = useState<{ nombre_fantasia: string, logo_path: string | null } | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  
  const [formData, setFormData] = useState({ 
    id_cliente_establecimiento: "", 
    id_jurisdiccion: "", 
    descripcion: "", 
    vigente: 1,
    contactos: [] as DatoContacto[]
  });

  const fetchData = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) { router.push("/"); return; }

    try {
      setLoading(true);
      
      // Añadimos el fetch de clientes para obtener la identidad de la cabecera
      const [resEst, resJur, resTipos, resClientes] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/establecimientos/leer.php?id_cliente=${id}`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/jurisdicciones/leer.php`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=tipo_contacto`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/clientes/leer.php`, { headers: { "Authorization": `Bearer ${token}` } })
      ]);

      const [dataEst, dataJur, dataTipos, dataClientes] = await Promise.all([
        resEst.json(), resJur.json(), resTipos.json(), resClientes.json()
      ]);

      setEstablecimientos(dataEst.registros || []);
      setJurisdicciones(dataJur.registros || []);
      setTiposContacto(dataTipos.registros || []);
      
      // Filtramos para quedarnos con el nombre y logo del cliente actual
      if (dataClientes.registros) {
        const clienteFind = dataClientes.registros.find((c: any) => c.id_cliente.toString() === id);
        if (clienteFind) {
          setClienteActual({
            nombre_fantasia: clienteFind.nombre_fantasia || clienteFind.razon_social,
            logo_path: clienteFind.logo_path
          });
        }
      }
      
    } catch (error) {
      console.error("Error al sincronizar datos:", error);
    } finally {
      setLoading(false);
    }
  }, [id, router]);

  useEffect(() => { 
    if (!isCheckingPerms && canRead("clientes")) fetchData(); 
  }, [fetchData, isCheckingPerms, canRead]);

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
      const res = await fetch("http://localhost/lgc_sgmlo/backend/api/establecimientos/guardar.php", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ ...formData, id_cliente: id }) 
      });
      if (res.ok) {
        setIsModalOpen(false);
        fetchData();
      } else {
        alert("Ocurrió un error al guardar la sede.");
      }
    } catch (error) {
      console.error(error);
    } finally {
      setFormLoading(false);
    }
  };

  if (isCheckingPerms) return <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Verificando credenciales de seguridad...</div>;
  if (!canRead("clientes")) return <div className="py-32 text-center text-red-500 font-bold text-2xl">Acceso Denegado</div>;

  return (
    <div className="space-y-6 font-sans animate-fade-in">
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="text-slate-400 hover:text-lgc-primary transition-colors text-sm font-bold uppercase tracking-widest flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
          Volver a Clientes
        </button>
      </div>

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-white p-6 rounded-2xl shadow-sm border border-slate-100 gap-4">
        
        {/* HEADER DE ESTABLECIMIENTOS CON IDENTIDAD DEL CLIENTE */}
        <div className="flex items-center gap-4">
          {clienteActual?.logo_path ? (
            <div className="w-14 h-14 rounded-xl border border-slate-200 bg-white shadow-sm flex items-center justify-center overflow-hidden shrink-0">
              <img src={`http://localhost/lgc_sgmlo/backend/${clienteActual.logo_path}`} alt="Logo" className="w-full h-full object-contain p-1" />
            </div>
          ) : (
            <div className="w-14 h-14 rounded-xl border border-slate-200 bg-slate-50 shadow-sm flex items-center justify-center shrink-0">
               <svg className="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
            </div>
          )}
          
          <div>
            <h1 className="text-2xl font-heading text-lgc-primary uppercase tracking-tight">Establecimientos / Sedes</h1>
            <p className="text-slate-500 text-sm mt-0.5">
              Gestionando establecimientos de <strong className="text-slate-700 font-bold uppercase tracking-widest text-[10px] bg-slate-100 px-2 py-1 rounded ml-1">{clienteActual?.nombre_fantasia || `Cliente #${id}`}</strong>
            </p>
          </div>
        </div>
        
        {canEdit("clientes") && (
          <button 
              onClick={() => { 
                setFormData({id_cliente_establecimiento: "", id_jurisdiccion: "", descripcion: "", vigente: 1, contactos: []}); 
                setIsModalOpen(true); 
              }}
              className="bg-lgc-accent text-white py-2.5 px-6 rounded-lg font-bold text-xs uppercase tracking-widest hover:bg-lgc-primary transition-all shadow-md shrink-0 flex items-center gap-2"
          >
            <span>+</span> Agregar Sede
          </button>
        )}
      </div>

      {loading ? (
        <div className="py-20 text-center text-lgc-primary font-heading animate-pulse">Cargando establecimientos...</div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-slate-50 text-[10px] uppercase tracking-[0.2em] text-slate-400 font-bold border-b border-slate-200">
              <tr>
                <th className="p-5">Descripción de la Planta/Sede</th>
                <th className="p-5">Jurisdicción</th>
                <th className="p-5">Estado</th>
                <th className="p-5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {establecimientos.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-10 text-center text-slate-400 italic">No hay establecimientos registrados para este cliente.</td>
                </tr>
              ) : (
                establecimientos.map(est => (
                  <tr key={est.id_cliente_establecimiento} className="hover:bg-slate-50/50 transition-colors">
                    <td className="p-5 font-bold text-slate-700 text-sm">{est.descripcion}</td>
                    <td className="p-5 text-xs text-slate-500 font-medium uppercase tracking-widest">{est.jurisdiccion_nombre}</td>
                    <td className="p-5">
                        <span className={`px-2.5 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest border ${est.vigente ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
                            {est.vigente ? 'OPERATIVO' : 'INACTIVO'}
                        </span>
                    </td>
                    <td className="p-5 text-right">
                      {canEdit("clientes") ? (
                        <button 
                          onClick={() => { 
                            setFormData({
                              id_cliente_establecimiento: est.id_cliente_establecimiento.toString(),
                              descripcion: est.descripcion,
                              id_jurisdiccion: est.id_jurisdiccion.toString(),
                              vigente: est.vigente,
                              contactos: est.contactos || [] 
                            }); 
                            setIsModalOpen(true); 
                          }}
                          className="text-slate-400 hover:text-lgc-primary bg-white border border-slate-200 p-2 rounded transition-all shadow-sm"
                          title="Editar Sede"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                        </button>
                      ) : (
                        <span className="text-slate-300 text-[10px] font-bold uppercase tracking-widest cursor-not-allowed">Solo Lectura</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {isModalOpen && canEdit("clientes") && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden my-8 border border-slate-200">
            <div className="p-6 bg-slate-50 border-b flex justify-between items-center sticky top-0 z-10">
              <h2 className="text-xl font-heading text-lgc-primary uppercase tracking-tight">
                {formData.id_cliente_establecimiento ? "Editar Sede" : "Nueva Sede Operativa"}
              </h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-2xl">&times;</button>
            </div>

            <form onSubmit={handleSubmit} className="p-8 space-y-6">
              
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b pb-2 mb-4">Datos Operativos</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="md:col-span-2">
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Nombre / Descripción de la Sede *</label>
                    <input required className="w-full p-3 bg-slate-50 border rounded-lg outline-none focus:border-lgc-primary focus:ring-2 focus:ring-lgc-primary text-sm" placeholder="Ej: Planta Industrial Pilar" value={formData.descripcion} onChange={e => setFormData({...formData, descripcion: e.target.value})} />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Jurisdicción Aplicable *</label>
                    <select required className="w-full p-3 bg-slate-50 border rounded-lg outline-none focus:border-lgc-primary focus:ring-2 focus:ring-lgc-primary text-sm cursor-pointer" value={formData.id_jurisdiccion} onChange={e => setFormData({...formData, id_jurisdiccion: e.target.value})}>
                      <option value="">Seleccione...</option>
                      {jurisdicciones.map(j => (
                        <option key={j.id_jurisdiccion} value={j.id_jurisdiccion}>{j.descripcion}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Estado *</label>
                    <select className="w-full p-3 bg-slate-50 border rounded-lg outline-none focus:border-lgc-primary focus:ring-2 focus:ring-lgc-primary text-sm cursor-pointer" value={formData.vigente} onChange={e => setFormData({...formData, vigente: parseInt(e.target.value)})}>
                      <option value={1}>OPERATIVO</option>
                      <option value={0}>INACTIVO</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center border-b pb-2 mb-4">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Contacto Directo de Sede</h3>
                  <button type="button" onClick={handleAddContacto} className="text-[10px] text-lgc-primary font-bold uppercase tracking-widest hover:text-lgc-accent transition-colors">+ Agregar Medio</button>
                </div>
                
                <div className="space-y-3 max-h-48 overflow-y-auto pr-2">
                  {formData.contactos.length === 0 ? (
                    <p className="text-sm text-slate-400 italic text-center py-4 bg-slate-50 rounded-lg border border-dashed">No hay contactos registrados en esta sede.</p>
                  ) : (
                    formData.contactos.map((contacto, index) => (
                      <div key={index} className="flex gap-3 items-start animate-fade-in">
                        <select required className="w-1/3 p-3 text-sm bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none cursor-pointer" value={contacto.id_tipo_contacto} onChange={(e) => handleContactoChange(index, 'id_tipo_contacto', e.target.value)}>
                          <option value="">Tipo...</option>
                          {tiposContacto.map(tipo => (
                            <option key={tipo.id_tipo_contacto} value={tipo.id_tipo_contacto}>{tipo.descripcion}</option>
                          ))}
                        </select>
                        
                        <input required type={getInputType(contacto.id_tipo_contacto)} placeholder="Valor..." className="grow p-3 text-sm bg-slate-50 border rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none" value={contacto.valor} onChange={(e) => handleContactoChange(index, 'valor', e.target.value)} />
                        
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
                  {formLoading ? 'Guardando...' : 'Guardar Sede'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}