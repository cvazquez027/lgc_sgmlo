"use client";

import { useState, useEffect, useRef } from "react";
import { usePermissions } from "../../app/hooks/usePermissions"; 
import { useRouter } from "next/navigation";

interface ItemMatriz {
  id_item_matriz?: number | string;
  id_matriz: number | string;
  resumen_legal: string;
  articulos_aplicables: string;
  interpretacion_aplicacion: string;
  id_tipo_modalidad: string;
  obs_modalidad: string;
  vencimiento_plazo: string;
  fecha_cumplimiento: string;
  obs_plazo: string;
  proceso_aplica: string;
  detalle_tema: string;
  evidencia_cumplimiento: string;
  responsable_cumplimiento: string;
  verificacion_cumplimiento: string;
  id_estado_cumplimiento: string;
  obs_estado_cumplimiento: string;
  normas_vinculadas: number[];
  documentos_vinculados: number[];
}

export default function ModalItemMatriz({ 
  isOpen, onClose, idMatriz, itemEdit = null, onSaved 
}: { 
  isOpen: boolean; onClose: () => void; idMatriz: string | number; itemEdit?: any; onSaved: () => void;
}) {
  const { canEdit } = usePermissions();
  const router = useRouter();
  
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Estados Buscador Normativas
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedNormsVisual, setSelectedNormsVisual] = useState<any[]>([]); 

  // Estados Evidencias (Tanda 4)
  const [isUploading, setIsUploading] = useState(false);
  const [selectedDocsVisual, setSelectedDocsVisual] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const defaultFormState: ItemMatriz = {
    id_matriz: idMatriz,
    resumen_legal: "",
    articulos_aplicables: "",
    interpretacion_aplicacion: "",
    id_tipo_modalidad: "",
    obs_modalidad: "",
    vencimiento_plazo: "",
    fecha_cumplimiento: "",
    obs_plazo: "",
    proceso_aplica: "",
    detalle_tema: "",
    evidencia_cumplimiento: "",
    responsable_cumplimiento: "",
    verificacion_cumplimiento: "",
    id_estado_cumplimiento: "4", 
    obs_estado_cumplimiento: "",
    normas_vinculadas: [],
    documentos_vinculados: []
  };

  const [formData, setFormData] = useState<ItemMatriz>(defaultFormState);

  useEffect(() => {
    if (itemEdit) {
      setFormData({
        ...defaultFormState,
        id_item_matriz: itemEdit.id_item_matriz,
        resumen_legal: itemEdit.resumen_legal ?? "",
        articulos_aplicables: itemEdit.articulos_aplicables ?? "",
        detalle_tema: itemEdit.detalle_tema ?? "",
        id_estado_cumplimiento: itemEdit.id_estado_cumplimiento?.toString() ?? "4",
        responsable_cumplimiento: itemEdit.responsable_cumplimiento ?? "",
        vencimiento_plazo: itemEdit.vencimiento_plazo ?? "",
        normas_vinculadas: itemEdit.normas_ids ?? [],
        documentos_vinculados: itemEdit.documentos_ids ?? []
      });
      setSelectedNormsVisual(itemEdit.normas_vinculadas ?? []);
      setSelectedDocsVisual(itemEdit.documentos_vinculados ?? []);
    } else {
      setFormData(defaultFormState);
      setSelectedNormsVisual([]);
      setSelectedDocsVisual([]);
      setCurrentStep(1);
    }
  }, [itemEdit, isOpen]);

  // Buscador de normas
  useEffect(() => {
    if (searchTerm.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    const delayDebounceFn = setTimeout(async () => {
      setIsSearching(true);
      try {
        const token = localStorage.getItem("sgml_token");
        const res = await fetch(`http://localhost/lgc_sgmlo/backend/api/matriz/buscar_normas.php?q=${encodeURIComponent(searchTerm)}`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();
        setSearchResults(data.registros || []);
      } catch (error) {
        console.error("Error buscando normativas", error);
      } finally {
        setIsSearching(false);
      }
    }, 400);
    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm]);

  const handleAddNorma = (norma: any) => {
    if (!formData.normas_vinculadas.includes(norma.id_norma)) {
      setFormData(prev => ({ ...prev, normas_vinculadas: [...prev.normas_vinculadas, norma.id_norma] }));
      setSelectedNormsVisual(prev => [...prev, norma]);
    }
    setSearchTerm(""); 
    setSearchResults([]);
  };

  const handleRemoveNorma = (id_norma: number) => {
    setFormData(prev => ({ ...prev, normas_vinculadas: prev.normas_vinculadas.filter(id => id !== id_norma) }));
    setSelectedNormsVisual(prev => prev.filter(n => n.id_norma !== id_norma));
  };

  // --- LÓGICA DE SUBIDA DE EVIDENCIAS (TANDA 4) ---
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      alert("El archivo no puede superar los 5MB.");
      return;
    }

    setIsUploading(true);
    const token = localStorage.getItem("sgml_token");
    const formDataUpload = new FormData();
    formDataUpload.append("archivo", file);

    try {
      const res = await fetch("http://localhost/lgc_sgmlo/backend/api/matriz/subir_documento.php", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }, // FormData no necesita Content-Type, el browser lo pone solo con el boundary
        body: formDataUpload
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.mensaje || "Error al subir");

      // Actualizamos estado y parte visual
      setFormData(prev => ({ ...prev, documentos_vinculados: [...prev.documentos_vinculados, data.id_documentacion] }));
      setSelectedDocsVisual(prev => [...prev, { id_documentacion: data.id_documentacion, nombre_original: data.nombre_original }]);
      
    } catch (error: any) {
      alert("Error: " + error.message);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = ""; // Limpiamos el input
    }
  };

  const handleRemoveDoc = (id_doc: number) => {
    setFormData(prev => ({ ...prev, documentos_vinculados: prev.documentos_vinculados.filter(id => id !== id_doc) }));
    setSelectedDocsVisual(prev => prev.filter(d => d.id_documentacion !== id_doc));
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleNext = () => {
    if (currentStep === 1 && !formData.resumen_legal.trim()) {
      alert("El Resumen Legal es un campo obligatorio para avanzar.");
      return;
    }
    setCurrentStep(prev => prev + 1);
  };

  const handleBack = () => setCurrentStep(prev => prev - 1);

  const saveItemData = async () => {
    const token = localStorage.getItem("sgml_token");
    const res = await fetch("http://localhost/lgc_sgmlo/backend/api/matriz/guardar_item.php", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify(formData)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.mensaje || "Error al guardar el ítem");
    return data;
  };

  const publicarMatriz = async () => {
    const token = localStorage.getItem("sgml_token");
    const res = await fetch("http://localhost/lgc_sgmlo/backend/api/matriz/cambiar_estado.php", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ id_matriz: idMatriz, id_estado_matriz: 1 }) 
    });
    if (!res.ok) throw new Error("Ítem guardado, pero falló la publicación de la matriz.");
  };

  const handleFinalAction = async (action: 'otro' | 'salir' | 'previsualizar') => {
    if (!canEdit("matriz")) return;
    setIsSubmitting(true);

    try {
      await saveItemData(); 

      if (action === 'previsualizar') {
        // Guardamos, cerramos el modal y VAMOS AL PREVIEW
        onSaved(); 
        onClose();
        router.push(`/dashboard/matrices/${idMatriz}/preview`);
      } 
      else if (action === 'salir') {
        onSaved(); onClose(); 
      } 
      else if (action === 'otro') {
        onSaved(); 
        setFormData(defaultFormState); 
        setSelectedNormsVisual([]);
        setSelectedDocsVisual([]);
        setCurrentStep(1); 
      }
    } catch (error: any) {
      alert("Error en la operación: " + error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const stepsDef = [
    { id: 1, title: 'Obligación Legal', icon: '⚖️' },
    { id: 2, title: 'Normativas', icon: '📜' },
    { id: 3, title: 'Cumplimiento', icon: '✅' },
    { id: 4, title: 'Evidencias', icon: '📎' }
  ];

  return (
    <div className="fixed inset-0 bg-slate-900/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="bg-white w-full max-w-5xl rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden border border-slate-200">
        
        {/* HEADER */}
        <div className="p-6 bg-white border-b border-slate-100 flex justify-between items-center relative z-20">
          <div>
            <h2 className="text-2xl font-heading text-lgc-primary uppercase tracking-tight font-bold">
              {itemEdit ? "Modificar Ítem" : "Agregar Nuevo Ítem"}
            </h2>
            <p className="text-sm text-slate-400 mt-1 uppercase tracking-widest font-bold">
              Matriz #{idMatriz} - <span className="text-lgc-primary">Paso {currentStep} de 4</span>
            </p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 p-2 rounded-full transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        {/* STEPPER ESTILO CHEVRON CON CLIP-PATH */}
        <div className="flex w-full bg-[#e2e8f0] h-16 shadow-inner z-10">
          {stepsDef.map((s, idx) => {
            const isActive = currentStep === s.id;
            const isPast = currentStep > s.id;
            
            // Lógica de colores según el mockup
            let bgClass = "bg-[#d1d5db]"; // Gris inactivo por defecto
            let textClass = "text-slate-400 grayscale opacity-50"; 
            
            if (isActive) {
              bgClass = "bg-white";
              textClass = "text-lgc-primary";
            } else if (isPast) {
              bgClass = "bg-[#f1f5f9]"; // Un gris muy clarito para los completados
              textClass = "text-slate-500 opacity-80";
            }

            // Calculamos el clip-path para las flechas (el primero es plano a la izq, el último es plano a la derecha)
            let clipPathStyle = "polygon(calc(100% - 20px) 0%, 100% 50%, calc(100% - 20px) 100%, 0% 100%, 20px 50%, 0% 0%)";
            if (idx === 0) clipPathStyle = "polygon(calc(100% - 20px) 0%, 100% 50%, calc(100% - 20px) 100%, 0% 100%, 0% 0%)";
            if (idx === stepsDef.length - 1) clipPathStyle = "polygon(100% 0%, 100% 100%, 0% 100%, 20px 50%, 0% 0%)";

            return (
              <div 
                key={s.id} 
                className={`relative flex-1 flex flex-col items-center justify-center transition-all duration-300 ${bgClass} ${textClass}`}
                style={{ 
                  clipPath: clipPathStyle,
                  // Añadimos margen negativo sutil para que las flechas encastren perfecto
                  marginLeft: idx === 0 ? '0' : '-10px',
                  zIndex: stepsDef.length - idx 
                }}
              >
                <div className="flex items-center gap-2 px-6">
                  <span className={`text-xl ${isActive ? 'drop-shadow-md' : ''}`}>{s.icon}</span>
                  <span className="text-[10px] uppercase tracking-[0.15em] font-bold hidden md:block">{s.title}</span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex-1 overflow-y-auto p-8 bg-slate-50/50">
          
          {/* PASO 1 */}
          <div className={currentStep === 1 ? 'block animate-fade-in space-y-6' : 'hidden'}>
            <div>
              <label className="text-xs font-bold uppercase text-slate-500 tracking-widest block mb-2">Obligación / Resumen Legal *</label>
              <textarea required name="resumen_legal" value={formData.resumen_legal} onChange={handleChange} rows={6} className="w-full p-4 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm resize-none shadow-sm" placeholder="Describa la obligación concreta..." />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="text-xs font-bold uppercase text-slate-500 tracking-widest block mb-2">Artículos Aplicables</label>
                <input type="text" name="articulos_aplicables" value={formData.articulos_aplicables} onChange={handleChange} className="w-full p-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm shadow-sm" placeholder="Ej: Art. 4, 5 y Anexo II" />
              </div>
              <div>
                <label className="text-xs font-bold uppercase text-slate-500 tracking-widest block mb-2">Detalle / Tema Específico</label>
                <input type="text" name="detalle_tema" value={formData.detalle_tema} onChange={handleChange} className="w-full p-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm shadow-sm" />
              </div>
            </div>
          </div>

          {/* PASO 2: NORMATIVAS */}
          <div className={currentStep === 2 ? 'block animate-fade-in' : 'hidden'}>
            {/* ... (Contenido intacto del buscador predictivo) ... */}
            <div className="space-y-6">
              <div className="relative">
                <label className="text-xs font-bold uppercase text-slate-500 tracking-widest block mb-2">Buscar Normativa en Base de Datos</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                  </span>
                  <input type="text" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="Escriba número, año o tipo (ej. 19587)..." className="w-full p-4 pl-10 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none shadow-sm text-sm" />
                </div>
                {searchTerm.length >= 2 && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-slate-200 rounded-lg shadow-xl z-10 max-h-64 overflow-y-auto">
                    {isSearching ? (
                      <div className="p-4 text-center text-xs text-slate-400 animate-pulse font-bold uppercase tracking-widest">Buscando...</div>
                    ) : searchResults.length === 0 ? (
                      <div className="p-4 text-center text-xs text-slate-400 italic">Sin resultados.</div>
                    ) : (
                      <div className="divide-y divide-slate-100">
                        {searchResults.map(n => (
                          <button key={n.id_norma} type="button" onClick={() => handleAddNorma(n)} className="w-full text-left p-3 hover:bg-slate-50 transition-colors flex justify-between items-center group">
                            <div>
                              <span className="font-bold text-slate-700 text-sm block group-hover:text-lgc-primary">{n.tipo_norma} {n.numero}/{n.anio}</span>
                              <span className="text-[10px] uppercase tracking-widest text-slate-400">{n.emisor || 'Emisor Desconocido'}</span>
                            </div>
                            <span className="text-lgc-primary opacity-0 group-hover:opacity-100"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg></span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
              <div className="bg-white p-5 border border-slate-200 rounded-lg 30[120px]">
                <h4 className="text-[10px] font-bold uppercase text-slate-400 tracking-widest mb-3 border-b border-slate-100 pb-2">Normativas Vinculadas</h4>
                {selectedNormsVisual.length === 0 ? (
                  <p className="text-xs text-slate-400 italic text-center py-4">Aún no ha vinculado ninguna normativa.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {selectedNormsVisual.map(n => (
                      <span key={n.id_norma} className="inline-flex items-center gap-2 bg-lgc-tostado/20 text-lgc-primary border border-lgc-primary/30 text-[11px] font-bold uppercase tracking-widest px-3 py-1.5 rounded shadow-sm">
                        {n.tipo_norma} {n.numero}/{n.anio}
                        <button type="button" onClick={() => handleRemoveNorma(n.id_norma)} className="hover:bg-red-100 hover:text-red-600 rounded-full w-5 h-5 flex items-center justify-center">&times;</button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* PASO 3: CUMPLIMIENTO */}
          <div className={currentStep === 3 ? 'block animate-fade-in space-y-6' : 'hidden'}>
             <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="text-xs font-bold uppercase text-slate-500 tracking-widest block mb-2">Estado de Cumplimiento *</label>
                  <select required name="id_estado_cumplimiento" value={formData.id_estado_cumplimiento} onChange={handleChange} className="w-full p-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm cursor-pointer shadow-sm">
                    <option value="1">Cumple</option>
                    <option value="2">No Cumple</option>
                    <option value="3">En Proceso</option>
                    <option value="4">Sin Informar</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-bold uppercase text-slate-500 tracking-widest block mb-2">Responsable Interno</label>
                  <input type="text" name="responsable_cumplimiento" value={formData.responsable_cumplimiento} onChange={handleChange} className="w-full p-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm shadow-sm" />
                </div>
                <div>
                  <label className="text-xs font-bold uppercase text-slate-500 tracking-widest block mb-2">Vencimiento del Plazo</label>
                  <input type="date" name="vencimiento_plazo" value={formData.vencimiento_plazo} onChange={handleChange} className="w-full p-3 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-lgc-primary outline-none text-sm shadow-sm text-slate-600" />
                </div>
             </div>
          </div>

          {/* PASO 4: EVIDENCIAS (NUEVO DROPZONE) */}
          <div className={currentStep === 4 ? 'block animate-fade-in' : 'hidden'}>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              
              {/* ZONA DE SUBIDA */}
              <div>
                <label className="text-xs font-bold uppercase text-slate-500 tracking-widest block mb-3">Adjuntar Nueva Evidencia</label>
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center bg-white hover:bg-slate-50 transition-colors relative">
                  <input 
                    type="file" 
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                    disabled={isUploading}
                  />
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-12 h-12 bg-lgc-tostado/20 text-lgc-primary rounded-full flex items-center justify-center">
                      {isUploading ? (
                        <svg className="animate-spin w-6 h-6" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                      ) : (
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-bold text-slate-700">{isUploading ? 'Subiendo archivo...' : 'Click o arrastrar para subir'}</p>
                      <p className="text-[10px] text-slate-400 uppercase tracking-widest mt-1">PDF, JPG, PNG o Word (Max. 5MB)</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* LISTA DE ARCHIVOS VINCULADOS */}
              <div>
                <label className="text-xs font-bold uppercase text-slate-500 tracking-widest block mb-3">Evidencias Vinculadas ({selectedDocsVisual.length})</label>
                <div className="bg-white border border-slate-200 rounded-xl min-h-45 p-2 flex flex-col gap-2">
                  {selectedDocsVisual.length === 0 ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-slate-400 italic text-xs">
                      No hay archivos adjuntos.
                    </div>
                  ) : (
                    selectedDocsVisual.map(doc => (
                      <div key={doc.id_documentacion} className="flex justify-between items-center p-3 bg-slate-50 border border-slate-100 rounded-lg group">
                        <div className="flex items-center gap-3 overflow-hidden">
                          <span className="text-lgc-primary bg-white p-2 rounded shadow-sm">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
                          </span>
                          <span className="text-xs font-bold text-slate-600 truncate" title={doc.nombre_original}>{doc.nombre_original}</span>
                        </div>
                        <button type="button" onClick={() => handleRemoveDoc(doc.id_documentacion)} className="text-slate-300 hover:text-red-500 transition-colors p-1" title="Desvincular">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

            </div>
            
            <div className="mt-8 bg-lgc-tostado/10 border border-lgc-tostado/30 p-5 rounded-lg flex items-start gap-4">
               <span className="text-2xl">🚀</span>
               <div>
                 <h4 className="text-sm font-bold text-lgc-primary uppercase tracking-widest mb-1">¡Todo listo para guardar!</h4>
                 <p className="text-xs text-slate-600 leading-relaxed">Seleccione "Guardar y Cargar Otro" para mantener el flujo de trabajo activo, o "Guardar y Previsualizar" para editar como se verá esta matriz al publicarla.</p>
               </div>
            </div>
          </div>

        </div>

        {/* FOOTER */}
        <div className="p-6 border-t border-slate-200 bg-white flex justify-between items-center rounded-b-2xl">
          <div>
            {currentStep > 1 && (
              <button type="button" onClick={handleBack} disabled={isSubmitting || isUploading} className="px-6 py-2.5 text-xs font-bold uppercase tracking-[0.15em] text-slate-500 hover:text-lgc-primary hover:bg-slate-50 border border-transparent hover:border-slate-200 rounded-lg transition-colors flex items-center gap-2">
                &larr; PASO ANTERIOR
              </button>
            )}
          </div>
          
          <div className="flex gap-3">
            {currentStep < 4 ? (
              <button type="button" onClick={handleNext} className="px-8 py-3 bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold uppercase tracking-[0.15em] rounded-lg shadow-md transition-all flex items-center gap-2">
                SIGUIENTE PASO &rarr;
              </button>
            ) : (
              <>
                {!itemEdit && (
                  <button type="button" onClick={() => handleFinalAction('otro')} disabled={isSubmitting || isUploading} className="px-6 py-3 bg-white border border-slate-300 text-slate-600 hover:bg-slate-50 text-[10px] font-bold uppercase tracking-widest rounded-lg transition-all shadow-sm">
                    GUARDAR Y SEGUIR CARGANDO
                  </button>
                )}
                
                <button type="button" onClick={() => handleFinalAction('salir')} disabled={isSubmitting || isUploading} className="px-6 py-3 bg-slate-100 border border-slate-200 text-slate-700 hover:bg-slate-200 text-[10px] font-bold uppercase tracking-widest rounded-lg transition-all">
                  GUARDAR BORRADOR Y SALIR
                </button>
                
                <button type="button" onClick={() => handleFinalAction('previsualizar')} disabled={isSubmitting || isUploading} className="px-8 py-3 bg-lgc-primary hover:bg-[#006A8A] text-white text-[10px] font-bold uppercase tracking-[0.15em] rounded-lg shadow-md transition-all flex items-center gap-2">
                  {isSubmitting ? 'PROCESANDO...' : 'GUARDAR Y PREVISUALIZAR'}
                </button>
              </>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}