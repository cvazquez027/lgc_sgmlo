"use client";

import { useEffect, useState, useCallback } from "react";
import { usePermissions } from "../../hooks/usePermissions";

interface Norma {
  id_norma: number;
  numero: string;
  anio: number;
  fecha_publicacion: string;
  sintesis: string;
  url_norma: string;
  origen_carga: string;
  id_tipo_norma: number;
  tipo_norma_desc: string;
  id_emisor_norma: number;
  emisor_desc: string;
  id_estado_norma: number;
  estado_desc: string;
}

interface Diccionario {
  id: string | number;
  descripcion: string;
}

export default function NormativaOficialPage() {
  const { canRead, canEdit } = usePermissions();
  const [isCheckingPerms, setIsCheckingPerms] = useState(true);

  const [normas, setNormas] = useState<Norma[]>([]);
  const [tipos, setTipos] = useState<Diccionario[]>([]);
  const [emisores, setEmisores] = useState<Diccionario[]>([]);
  const [estados, setEstados] = useState<Diccionario[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const defaultForm = {
    id_norma: "",
    id_tipo_norma: "",
    id_emisor_norma: "",
    numero: "",
    anio: new Date().getFullYear(),
    fecha_publicacion: "",
    sintesis: "",
    url_norma: "",
    id_estado_norma: "1", // Generalmente 1 = Vigente
    origen_carga: "Manual"
  };

  const [formData, setFormData] = useState(defaultForm);

  useEffect(() => {
    const timer = setTimeout(() => setIsCheckingPerms(false), 100);
    return () => clearTimeout(timer);
  }, []);

  const fetchDiccionarios = useCallback(async (token: string) => {
    try {
      const [resTipos, resEmisores, resEstados] = await Promise.all([
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=tipo_norma`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=emisor_norma`, { headers: { "Authorization": `Bearer ${token}` } }),
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=estado_norma`, { headers: { "Authorization": `Bearer ${token}` } })
      ]);

      const [dataTipos, dataEmisores, dataEstados] = await Promise.all([
        resTipos.json(), resEmisores.json(), resEstados.json()
      ]);

      setTipos(dataTipos.registros?.map((e:any) => ({ id: e.id_tipo_norma, descripcion: e.descripcion })) || []);
      setEmisores(dataEmisores.registros?.map((e:any) => ({ id: e.id_emisor_norma, descripcion: e.descripcion })) || []);
      setEstados(dataEstados.registros?.map((e:any) => ({ id: e.id_estado_norma, descripcion: e.descripcion })) || []);
    } catch (err) {
      console.error("Error cargando diccionarios", err);
    }
  }, []);

  const fetchData = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return;

    try {
      setLoading(true);
      await fetchDiccionarios(token);
      
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/normativa/leer.php`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      setNormas(data.registros || []);
    } catch (err) {
      console.error("Error cargando normas", err);
    } finally {
      setLoading(false);
    }
  }, [fetchDiccionarios]);

  useEffect(() => {
    if (!isCheckingPerms && canRead("normativa")) fetchData();
  }, [fetchData, isCheckingPerms, canRead]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit("normativa")) return;

    setFormLoading(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/normativa/guardar.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setIsModalOpen(false);
        fetchData();
      } else {
        alert("Ocurrió un error al guardar la normativa.");
      }
    } catch (error) {
      console.error(error);
    } finally {
      setFormLoading(false);
    }
  };

  // Filtrado rápido en el cliente (Accesibilidad y UX)
  const normasFiltradas = normas.filter(n => 
    n.numero?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    n.sintesis?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    n.emisor_desc?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isCheckingPerms) return <div className="py-20 text-center text-lgc-primary animate-pulse">Verificando credenciales...</div>;
  if (!canRead("normativa")) return <div className="py-32 text-center text-red-500 font-bold text-2xl">Acceso Denegado</div>;

  return (
    <div className="space-y-6 font-sans animate-fade-in">
      {/* Encabezado y Barra de Búsqueda */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-white p-6 rounded-2xl shadow-sm border border-slate-100 gap-4">
        <div>
          <h1 className="text-2xl font-heading text-lgc-primary uppercase tracking-tight">Normativa Oficial</h1>
          <p className="text-slate-500 text-sm mt-0.5">Base depurada de leyes, decretos y resoluciones</p>
        </div>
        
        <div className="flex gap-4 w-full md:w-auto">
          <input 
            type="text" 
            placeholder="Buscar por número, emisor o síntesis..." 
            className="w-full md:w-64 p-2.5 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none transition-all"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
          {canEdit("normativa") && (
            <button 
                onClick={() => { setFormData(defaultForm); setIsModalOpen(true); }}
                className="bg-lgc-primary text-white py-2.5 px-6 rounded-lg font-bold text-xs uppercase tracking-widest hover:bg-[#006A8A] transition-all shadow-md shrink-0 whitespace-nowrap"
            >
              + Alta Manual
            </button>
          )}
        </div>
      </div>

      {/* Grilla de Datos */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 font-bold uppercase tracking-widest animate-pulse">Cargando base normativa...</div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-slate-50 text-[10px] uppercase tracking-[0.2em] text-slate-400 font-bold border-b border-slate-200">
              <tr>
                <th className="p-5">Norma</th>
                <th className="p-5">Emisor / Fecha</th>
                <th className="p-5 w-1/3">Síntesis</th>
                <th className="p-5">Estado</th>
                <th className="p-5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {normasFiltradas.length === 0 ? (
                <tr><td colSpan={5} className="p-10 text-center text-slate-400 italic">No se encontraron normativas.</td></tr>
              ) : (
                normasFiltradas.map(norma => (
                  <tr key={norma.id_norma} className="hover:bg-slate-50/50 transition-colors align-top group">
                    <td className="p-5">
                      <div className="font-bold text-slate-700 text-sm group-hover:text-lgc-primary transition-colors">
                        {norma.tipo_norma_desc} {norma.numero}
                      </div>
                      <div className="text-[10px] text-slate-400 uppercase tracking-widest mt-1">Año {norma.anio}</div>
                      {norma.origen_carga === 'Scraping' && (
                        <span className="inline-block mt-2 text-[8px] bg-blue-50 text-blue-500 border border-blue-200 px-1.5 py-0.5 rounded uppercase font-bold tracking-widest">Bot / Scraper</span>
                      )}
                    </td>
                    <td className="p-5">
                      <div className="text-xs font-bold text-slate-600 uppercase tracking-widest">{norma.emisor_desc}</div>
                      <div className="text-[10px] text-slate-500 mt-1">{norma.fecha_publicacion ? new Date(norma.fecha_publicacion).toLocaleDateString('es-AR') : '-'}</div>
                    </td>
                    <td className="p-5">
                      <p className="text-xs text-slate-600 line-clamp-2" title={norma.sintesis}>{norma.sintesis || 'Sin síntesis registrada.'}</p>
                      {norma.url_norma && (
                        <a href={norma.url_norma} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 mt-2 text-[10px] text-lgc-accent font-bold uppercase tracking-widest hover:underline">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                          Ver Doc. Original
                        </a>
                      )}
                    </td>
                    <td className="p-5">
                        <span className={`px-2.5 py-1 rounded-full text-[9px] font-bold uppercase tracking-widest border ${norma.estado_desc?.includes('Vigente') ? 'bg-green-50 text-green-700 border-green-200' : 'bg-slate-50 text-slate-600 border-slate-200'}`}>
                            {norma.estado_desc || 'SIN ESTADO'}
                        </span>
                    </td>
                    <td className="p-5 text-right">
                      {canEdit("normativa") && (
                        <button 
                          onClick={() => { 
                            setFormData({
                              id_norma: norma.id_norma.toString(),
                              id_tipo_norma: norma.id_tipo_norma?.toString() || "",
                              id_emisor_norma: norma.id_emisor_norma?.toString() || "",
                              numero: norma.numero || "",
                              anio: norma.anio,
                              fecha_publicacion: norma.fecha_publicacion || "",
                              sintesis: norma.sintesis || "",
                              url_norma: norma.url_norma || "",
                              id_estado_norma: norma.id_estado_norma?.toString() || "1",
                              origen_carga: norma.origen_carga
                            }); 
                            setIsModalOpen(true); 
                          }}
                          className="text-slate-400 hover:text-lgc-primary bg-white border border-slate-200 p-2 rounded transition-all shadow-sm"
                          aria-label={`Editar norma ${norma.numero}`}
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* MODAL DE EDICIÓN / ALTA */}
      {isModalOpen && canEdit("normativa") && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white w-full max-w-3xl rounded-2xl shadow-2xl overflow-hidden my-8 border border-slate-200">
            <div className="p-6 bg-slate-50 border-b flex justify-between items-center sticky top-0 z-10">
              <div>
                <h2 className="text-xl font-heading text-lgc-primary uppercase tracking-tight">
                  {formData.id_norma ? "Modificar Normativa" : "Alta de Normativa"}
                </h2>
                <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold mt-1">Gestión del repositorio oficial</p>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 text-2xl transition-colors">&times;</button>
            </div>

            <form onSubmit={handleSubmit} className="p-8 space-y-6">
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Tipo de Norma *</label>
                  <select required className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm" value={formData.id_tipo_norma} onChange={e => setFormData({...formData, id_tipo_norma: e.target.value})}>
                    <option value="">Seleccione...</option>
                    {tipos.map(t => <option key={t.id} value={t.id}>{t.descripcion}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Número *</label>
                  <input required type="text" className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm" placeholder="Ej: 19587" value={formData.numero} onChange={e => setFormData({...formData, numero: e.target.value})} />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Año *</label>
                  <input required type="number" min="1900" max={new Date().getFullYear() + 1} className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm" value={formData.anio} onChange={e => setFormData({...formData, anio: parseInt(e.target.value)})} />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Emisor / Jurisdicción *</label>
                  <select required className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm" value={formData.id_emisor_norma} onChange={e => setFormData({...formData, id_emisor_norma: e.target.value})}>
                    <option value="">Seleccione...</option>
                    {emisores.map(e => <option key={e.id} value={e.id}>{e.descripcion}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Estado Normativo *</label>
                  <select required className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm" value={formData.id_estado_norma} onChange={e => setFormData({...formData, id_estado_norma: e.target.value})}>
                    {estados.map(e => <option key={e.id} value={e.id}>{e.descripcion}</option>)}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Síntesis / Título de la Norma</label>
                <textarea rows={3} className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm resize-none" placeholder="Breve descripción del objeto de la norma..." value={formData.sintesis} onChange={e => setFormData({...formData, sintesis: e.target.value})} />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Fecha de Publicación BO</label>
                  <input type="date" className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm text-slate-600" value={formData.fecha_publicacion} onChange={e => setFormData({...formData, fecha_publicacion: e.target.value})} />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">URL Documento Original</label>
                  <input type="url" className="w-full p-3 bg-white border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm shadow-sm" placeholder="https://..." value={formData.url_norma} onChange={e => setFormData({...formData, url_norma: e.target.value})} />
                </div>
              </div>

              <div className="flex gap-4 pt-6 mt-6 border-t border-slate-100">
                <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 py-3 text-xs uppercase tracking-widest font-bold text-slate-400 hover:text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">Cancelar</button>
                <button type="submit" disabled={formLoading} className="flex-1 bg-lgc-primary text-white py-3 rounded-lg font-bold text-xs uppercase tracking-widest shadow-md hover:bg-[#006A8A] transition-all">
                  {formLoading ? 'Guardando...' : 'Confirmar y Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}