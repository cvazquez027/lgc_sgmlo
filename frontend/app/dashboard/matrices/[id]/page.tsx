"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { usePermissions } from "../../../hooks/usePermissions"; 
import ModalItemMatriz from "../../../../components/matriz/ModalItemMatriz"; 
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

// DICCIONARIO MAESTRO
const TODAS_LAS_COLUMNAS = [
  { id: 'resumen_legal', label: 'Obligación / Resumen Legal' },
  { id: 'normas', label: 'Normativas (Tipo, Nro, Año)' },
  { id: 'norma_nivel_jur', label: 'Nivel Jurisdiccional (Norma)' },
  { id: 'norma_emisor', label: 'Emisor de la Norma' },
  { id: 'estado', label: 'Estado Cumplimiento' },
  { id: 'articulos_aplicables', label: 'Artículos Aplicables' },
  { id: 'proceso_aplica', label: 'Proceso que Aplica' },
  { id: 'detalle_tema', label: 'Detalle del Tema' },
  { id: 'responsable_cumplimiento', label: 'Responsable' },
  { id: 'vencimiento_plazo', label: 'Vencimiento' },
  { id: 'evidencia_cumplimiento', label: 'Evidencia' },
  { id: 'verificacion_cumplimiento', label: 'Verificación' },
  { id: 'interpretacion_aplicacion', label: 'Interpretación' },
];

// -------------------------------------------------------------
// COMPONENTE: CELDA EXPANDIBLE (MAGIA UX - OPTIMIZADA)
// -------------------------------------------------------------
const EditableCell = ({ value, onSave, placeholder = "..." }: any) => {
  const [localValue, setLocalValue] = useState(value || '');
  const [isFocused, setIsFocused] = useState(false);

  useEffect(() => { setLocalValue(value || ''); }, [value]);

  return (
    <div className="relative w-full min-w-35 h-9">
      <textarea
        value={localValue}
        onChange={e => setLocalValue(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => {
          setIsFocused(false);
          if (localValue.trim() !== (value || '').trim()) onSave(localValue.trim());
        }}
        placeholder={placeholder}
        className={`
          text-[11px] p-2 rounded outline-none transition-all resize-none text-slate-700
          ${isFocused 
            ? 'absolute -top-1.25 -left-1.25 w-70 h-30 bg-white border border-lgc-primary shadow-2xl z-100 ring-4 ring-lgc-primary/20' 
            : 'absolute top-0 left-0 w-full h-full bg-transparent border border-transparent hover:bg-slate-50 hover:border-slate-300 overflow-hidden'
          }
        `}
      />
    </div>
  );
};

// -------------------------------------------------------------
// COMPONENTE: BUSCADOR DE NORMATIVA INLINE (CON FILTRO FRONTEND)
// -------------------------------------------------------------
const InlineNormSelector = ({ selectedNormas, onChange }: any) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (query.trim().length < 1) {
      setResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    const timeoutId = setTimeout(async () => {
      const token = localStorage.getItem("sgml_token");
      try {
        let res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/normativa/leer.php?buscar=${query}`, { headers: { Authorization: `Bearer ${token}` } });
        const data = await res.json();
        
        // FILTRO DE SEGURIDAD FRONTEND: Por si el backend ignora el '?buscar='
        const registrosBackend = data.registros || [];
        const qLower = query.toLowerCase();
        
        const registrosFiltrados = registrosBackend.filter((r: any) => 
          (r.numero && r.numero.toString().toLowerCase().includes(qLower)) ||
          (r.sintesis && r.sintesis.toLowerCase().includes(qLower)) ||
          (r.tipo_norma_desc && r.tipo_norma_desc.toLowerCase().includes(qLower))
        );

        setResults(registrosFiltrados);
      } catch (e) {
        console.error("Error al buscar normativa:", e);
      } finally {
        setIsSearching(false);
      }
    }, 400); 

    return () => clearTimeout(timeoutId);
  }, [query]);

  return (
    <div className="relative w-full min-w-45">
      <div className="flex flex-col gap-1 mb-1">
        {selectedNormas.map((n: any, idx: number) => (
          <span key={idx} className="bg-slate-100 text-slate-700 border border-slate-200 text-[9px] px-1.5 py-1 rounded flex justify-between items-center font-bold tracking-widest w-full">
            <span>{n.tipo_norma} {n.numero}</span>
            <button type="button" onClick={() => onChange(selectedNormas.filter((_:any, i:number) => i !== idx))} className="text-red-400 hover:text-red-600 bg-red-50 hover:bg-red-100 px-1 rounded ml-2">×</button>
          </span>
        ))}
      </div>
      <input
        type="text"
        placeholder={isSearching ? "Buscando..." : "+ Buscar N° o título..."}
        className="w-full text-[10px] p-1.5 border border-slate-300 rounded outline-none focus:border-lgc-primary bg-white shadow-sm"
        value={query}
        onChange={e => {
          setQuery(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => { if(query.length > 0) setIsOpen(true); }}
      />
      
      {isOpen && results.length > 0 && (
        <div className="absolute top-full left-0 mt-1 w-87.5 bg-white border border-slate-200 shadow-2xl rounded-lg z-100 max-h-48 overflow-y-auto">
          <div className="flex justify-between items-center p-2 bg-slate-50 border-b border-slate-100 sticky top-0">
             <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Resultados ({results.length})</span>
             <button type="button" onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-red-500 text-[10px] font-bold">Cerrar</button>
          </div>
          {results.map((r: any) => (
            <div key={r.id_norma} className="p-2.5 text-[10px] hover:bg-slate-50 cursor-pointer border-b border-slate-100 transition-colors"
                 onMouseDown={() => {
                    onChange([...selectedNormas, { 
                      id_norma: r.id_norma, 
                      tipo_norma: r.tipo_norma_desc || 'NORMA', 
                      numero: r.numero, 
                      anio: r.anio,
                      emisor_desc: r.emisor_desc,
                      nivel_jurisdiccion_desc: r.nivel_jurisdiccion_desc,
                      jurisdiccion_desc: r.jurisdiccion_desc
                    }]);
                    setIsOpen(false);
                    setQuery('');
                    setResults([]);
                 }}>
              <span className="font-bold text-lgc-primary">{r.tipo_norma_desc} {r.numero}/{r.anio}</span>
              <div className="text-slate-500 truncate mt-0.5">{r.sintesis}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// -------------------------------------------------------------
// COMPONENTE: ITEM ORDENABLE PARA LA PANTALLA DE CONFIGURACIÓN
// -------------------------------------------------------------
const SortableConfigItem = ({ colId, title, onRemove }: { colId: string, title?: string, onRemove: (id:string)=>void }) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: colId });
  const style = { transform: CSS.Transform.toString(transform), transition, zIndex: isDragging ? 50 : 1, opacity: isDragging ? 0.5 : 1, position: isDragging ? 'relative' as 'relative' : 'static' as 'static' };
  
  return (
    <div ref={setNodeRef} style={style} className="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-lg shadow-sm mb-2 group">
       <div className="flex items-center gap-3">
         <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing text-slate-400 hover:text-lgc-primary touch-none">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" /></svg>
         </div>
         <span className="text-[11px] font-bold uppercase text-slate-700 tracking-widest">{title}</span>
       </div>
       <button onClick={() => onRemove(colId)} className="text-slate-300 hover:text-red-500 transition-colors" title="Quitar columna">
         <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
       </button>
    </div>
  );
};

// -------------------------------------------------------------
// COMPONENTE: FILA ARRASTRABLE PARA EL WORKSPACE (GRILLA)
// -------------------------------------------------------------
const SortableRow = ({ item, columnasVisibles, onUpdate, onEdit, canEdit, estadosCumplimiento }: any) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: item.id_item_matriz });
  
  const style = {
    transform: isDragging && transform ? CSS.Transform.toString(transform) : undefined,
    transition,
    opacity: isDragging ? 0.5 : 1,
    backgroundColor: isDragging ? '#f8fafc' : 'transparent',
    position: (isDragging ? 'relative' : 'static') as any,
    zIndex: isDragging ? 40 : 1, 
  };

  const renderCelda = (colId: string) => {
    switch(colId) {
      case 'resumen_legal':
      case 'articulos_aplicables':
      case 'proceso_aplica':
      case 'detalle_tema':
      case 'responsable_cumplimiento':
      case 'evidencia_cumplimiento':
      case 'verificacion_cumplimiento':
      case 'interpretacion_aplicacion':
        return <EditableCell value={item[colId]} onSave={(val:string) => onUpdate(item.id_item_matriz, colId, val)} />;
      
      case 'vencimiento_plazo': 
        return <input type="date" className="text-[11px] p-1 border-transparent hover:border-slate-300 rounded outline-none bg-transparent" value={item.vencimiento_plazo || ''} onChange={(e) => onUpdate(item.id_item_matriz, colId, e.target.value)} />;
      
      case 'normas': 
        return <InlineNormSelector selectedNormas={item.normas_vinculadas || []} onChange={(normas:any) => onUpdate(item.id_item_matriz, 'normas_vinculadas', normas)} />;

      case 'norma_emisor':
        const emisores_unicos = Array.from(new Set(item.normas_vinculadas?.map((n:any) => n.emisor_desc).filter(Boolean)));
        return (
          <div className="flex flex-col gap-1 w-full min-w-30">
            {emisores_unicos.length > 0 ? emisores_unicos.map((emi: any, i: number) => (
              <span key={i} className="text-slate-600 text-[10px] font-bold uppercase truncate" title={emi as string}>• {emi}</span>
            )) : <span className="text-slate-300 text-[10px] italic">-</span>}
          </div>
        );

      case 'norma_nivel_jur':
        const niveles_unicos = Array.from(new Set(item.normas_vinculadas?.map((n:any) => n.nivel_jurisdiccion_desc || n.jurisdiccion_desc).filter(Boolean)));
        return (
          <div className="flex flex-col gap-1 w-full min-w-30">
            {niveles_unicos.length > 0 ? niveles_unicos.map((niv: any, i: number) => (
              <span key={i} className="bg-blue-50 text-blue-700 border border-blue-200 text-[9px] font-bold uppercase tracking-widest px-2 py-1 rounded w-max">{niv}</span>
            )) : <span className="text-slate-300 text-[10px] italic">-</span>}
          </div>
        );

      case 'estado':
        const color = item.color_hex ? `#${item.color_hex}` : '#cbd5e1';
        return (
          <div className="relative min-w-30">
             <select 
               className="w-full text-[9px] font-bold uppercase p-1.5 rounded outline-none shadow-sm cursor-pointer border"
               style={{ backgroundColor: `${color}10`, color: color, borderColor: `${color}30` }}
               value={item.id_estado_cumplimiento || ''}
               onChange={e => onUpdate(item.id_item_matriz, 'id_estado_cumplimiento', e.target.value)}
             >
               <option value="" disabled>Seleccione...</option>
               {estadosCumplimiento.map((est: any) => (
                 <option key={est.id} value={est.id}>{est.descripcion}</option>
               ))}
             </select>
          </div>
        );
      default: return '-';
    }
  };

  return (
    <tr ref={setNodeRef} style={style} className="hover:bg-slate-50/80 transition-colors border-b border-slate-100 group align-top">
      {canEdit && (
        <td className="p-3 w-8 cursor-grab active:cursor-grabbing text-slate-300 hover:text-lgc-primary touch-none" {...attributes} {...listeners}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" /></svg>
        </td>
      )}
      <td className="p-3 w-12"><span className="font-bold text-slate-400 text-[10px]">#{item.id_item_matriz}</span></td>
      
      {columnasVisibles.map((col: string) => (
        <td key={col} className="p-2 align-top">{renderCelda(col)}</td>
      ))}
      
      {canEdit && (
        <td className="p-3 text-right">
          <button onClick={() => onEdit(item)} className="text-slate-400 hover:text-lgc-primary bg-white border border-slate-200 p-1.5 rounded transition-all shadow-sm" title="Edición Profunda (Archivos)">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
          </button>
        </td>
      )}
    </tr>
  );
};

export default function WorkspaceMatrizPage() {
  const router = useRouter();
  const params = useParams(); 
  const idMatriz = params.id as string; 
  const { canRead, canEdit } = usePermissions();
  
  const [items, setItems] = useState<any[]>([]);
  const [configColumnas, setConfigColumnas] = useState<string[] | null>(null);
  
  // UI States
  const [loading, setLoading] = useState(true);
  const [showConfig, setShowConfig] = useState(false);
  const [tempConfig, setTempConfig] = useState<string[]>([]);
  
  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [itemAEditar, setItemAEditar] = useState<any | null>(null);

  // Fila Rápida y Diccionarios
  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [isSavingRow, setIsSavingRow] = useState(false);
  const [estadosCumplimiento, setEstadosCumplimiento] = useState<any[]>([]);

  const blankRowData = {
    resumen_legal: '',
    articulos_aplicables: '',
    proceso_aplica: '',
    detalle_tema: '',
    responsable_cumplimiento: '',
    vencimiento_plazo: '',
    evidencia_cumplimiento: '',
    verificacion_cumplimiento: '',
    interpretacion_aplicacion: '',
    id_estado_cumplimiento: '',
    normas_vinculadas: [] 
  };
  const [newRowData, setNewRowData] = useState<any>(blankRowData);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const fetchItems = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/leer_items.php?id_matriz=${idMatriz}`, { headers: { "Authorization": `Bearer ${token}` } });
      const data = await res.json();
      setConfigColumnas(data.config_columnas || []);
      setTempConfig(data.config_columnas || ['resumen_legal', 'normas', 'estado']); 
      setItems(data.registros || []);
      if (!data.config_columnas) setShowConfig(true); 
    } catch (err) { console.error(err); } finally { setLoading(false); }
  }, [idMatriz]);

  useEffect(() => {
    const fetchEstados = async () => {
        const token = localStorage.getItem("sgml_token");
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=estado_cumplimiento`, { headers: { "Authorization": `Bearer ${token}` } });
            const data = await res.json();
            const estados = data.registros.map((e:any) => ({ id: e.id_estado_cumplimiento || e.id, descripcion: e.descripcion }));
            setEstadosCumplimiento(estados);
            if (estados.length > 0) setNewRowData((p: any) => ({ ...p, id_estado_cumplimiento: estados[0].id }));
        } catch(e) {}
    };
    if (canRead("matriz")) { fetchItems(); fetchEstados(); }
  }, [fetchItems, canRead]);

  const guardarConfiguracion = async () => {
    const token = localStorage.getItem("sgml_token");
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/guardar_config.php`, {
        method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ id_matriz: idMatriz, columnas: tempConfig })
      });
      setConfigColumnas(tempConfig);
      setShowConfig(false);
    } catch (err) { alert("Error al guardar config"); }
  };

  // -------------------------------------------------------------
  // GUARDADO MÁGICO (Auto-Save para Filas Existentes)
  // -------------------------------------------------------------
  const handleUpdateExistingRow = async (itemId: number, field: string, value: any) => {
    const currentItem = items.find(i => i.id_item_matriz === itemId);
    if (!currentItem) return;

    const updatedItem = { ...currentItem, [field]: value };
    setItems(items.map(i => i.id_item_matriz === itemId ? updatedItem : i));

    const payload = {
      ...updatedItem,
      id_matriz: idMatriz,
      normas_vinculadas: updatedItem.normas_vinculadas?.map((n:any) => n.id_norma) || [],
      documentos_vinculados: updatedItem.documentos_vinculados?.map((d:any) => d.id_documentacion) || []
    };

    const token = localStorage.getItem("sgml_token");
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/guardar_item.php`, {
       method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
       body: JSON.stringify(payload)
    });
    
    if (field === 'id_estado_cumplimiento' || field === 'normas_vinculadas') fetchItems();
  };

  // -------------------------------------------------------------
  // GUARDADO DE LA FILA NUEVA
  // -------------------------------------------------------------
  const handleSaveNewRow = async () => {
    setIsSavingRow(true);
    const token = localStorage.getItem("sgml_token");
    
    const payload = { 
      id_matriz: idMatriz, 
      ...newRowData,
      normas_vinculadas: newRowData.normas_vinculadas.map((n:any) => n.id_norma)
    };

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/guardar_item.php`, {
        method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setShowQuickAdd(false);
        setNewRowData({ ...blankRowData, id_estado_cumplimiento: estadosCumplimiento[0]?.id || '' });
        fetchItems(); 
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSavingRow(false);
    }
  };

  const handleDragEndItems = async (event: any) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = items.findIndex(i => i.id_item_matriz === active.id);
      const newIndex = items.findIndex(i => i.id_item_matriz === over.id);
      const newItems = arrayMove(items, oldIndex, newIndex);
      setItems(newItems);

      const payload = newItems.map((it, idx) => ({ id_item: it.id_item_matriz, orden: idx }));
      const token = localStorage.getItem("sgml_token");
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/matriz/reordenar_items.php`, {
        method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify(payload)
      });
    }
  };

  const handleDragEndColumnas = (event: any) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = tempConfig.indexOf(active.id);
      const newIndex = tempConfig.indexOf(over.id);
      setTempConfig(arrayMove(tempConfig, oldIndex, newIndex));
    }
  };

  const renderQuickAddCell = (colId: string) => {
    switch(colId) {
      case 'estado':
         return (
           <select className="w-full text-[11px] p-2 border border-blue-200 rounded outline-none focus:border-blue-400 bg-white font-bold text-slate-600 uppercase shadow-sm" value={newRowData.id_estado_cumplimiento} onChange={e => setNewRowData({...newRowData, id_estado_cumplimiento: e.target.value})}>
              {estadosCumplimiento.map((e: any) => <option key={e.id} value={e.id}>{e.descripcion}</option>)}
           </select>
         );
      case 'normas':
         return <InlineNormSelector selectedNormas={newRowData.normas_vinculadas} onChange={(normas:any) => setNewRowData({...newRowData, normas_vinculadas: normas})} />;
      case 'norma_emisor':
      case 'norma_nivel_jur':
         return <div className="text-[9px] text-slate-400 font-bold uppercase tracking-widest bg-slate-100 p-2 rounded text-center border border-slate-200 mt-1">Automático</div>;
      case 'vencimiento_plazo':
         return <input type="date" className="w-full text-[11px] p-2 border border-blue-200 rounded outline-none focus:border-blue-400 bg-white text-slate-600 shadow-sm" value={newRowData.vencimiento_plazo} onChange={e => setNewRowData({...newRowData, vencimiento_plazo: e.target.value})} />;
      default:
         return <input type="text" className="w-full text-[11px] p-2 border border-blue-200 rounded outline-none focus:border-blue-400 bg-white text-slate-600 shadow-sm" value={(newRowData as any)[colId] || ''} onChange={e => setNewRowData({...newRowData, [colId]: e.target.value})} placeholder="..." />;
    }
  };

  if (loading) return <div className="py-20 text-center animate-pulse text-lgc-primary font-bold tracking-widest uppercase">Cargando Workspace...</div>;

  if (showConfig) {
    const columnasDisponibles = TODAS_LAS_COLUMNAS.filter(c => !tempConfig.includes(c.id));
    return (
      <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200 max-w-4xl mx-auto mt-6 animate-fade-in">
        <h2 className="text-2xl font-heading text-lgc-primary uppercase tracking-tight mb-2">Estructura Visual de la Matriz</h2>
        <p className="text-slate-500 mb-6 text-sm">Seleccioná los campos haciendo clic en "Agregar" y definí en qué orden querés ver las columnas arrastrándolas de arriba hacia abajo.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <h3 className="text-[10px] font-bold uppercase text-slate-500 tracking-widest mb-4 flex justify-between">
              <span>Campos Disponibles</span>
              <span className="bg-slate-200 text-slate-600 px-2 py-0.5 rounded">{columnasDisponibles.length}</span>
            </h3>
            <div className="flex flex-col gap-2 max-h-100 overflow-y-auto pr-1">
              {columnasDisponibles.map(col => (
                <button key={col.id} onClick={() => setTempConfig([...tempConfig, col.id])} className="w-full text-left p-3 bg-white border border-slate-200 rounded-lg hover:border-lgc-primary hover:text-lgc-primary transition-all text-[11px] font-bold uppercase text-slate-600 flex justify-between items-center group shadow-sm">
                  {col.label} <svg className="w-4 h-4 text-slate-300 group-hover:text-lgc-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-orange-50/50 p-4 rounded-xl border border-orange-100">
            <h3 className="text-[10px] font-bold uppercase text-orange-600 tracking-widest mb-4 flex justify-between">
              <span>Columnas Visibles (Ordenadas)</span>
              <span className="bg-orange-200 text-orange-700 px-2 py-0.5 rounded">{tempConfig.length}</span>
            </h3>
            <div className="flex flex-col max-h-100 overflow-y-auto pr-1">
              <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEndColumnas}>
                <SortableContext items={tempConfig} strategy={verticalListSortingStrategy}>
                  {tempConfig.map(colId => (
                      <SortableConfigItem key={colId} colId={colId} title={TODAS_LAS_COLUMNAS.find(c => c.id === colId)?.label} onRemove={(id: string) => setTempConfig(tempConfig.filter(c => c !== id))} />
                  ))}
                </SortableContext>
              </DndContext>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-4 border-t border-slate-100 pt-6">
          <button onClick={() => { setTempConfig(configColumnas || []); setShowConfig(false); }} className="px-6 py-2.5 text-xs uppercase font-bold text-slate-500 bg-white border border-slate-200 rounded-lg">Cancelar</button>
          <button onClick={guardarConfiguracion} disabled={tempConfig.length === 0} className="px-8 py-2.5 bg-lgc-primary text-white font-bold rounded-lg uppercase text-xs shadow-md disabled:opacity-50 flex items-center gap-2"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>Guardar Configuración</button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in flex flex-col h-[calc(100vh-100px)]">
      
      {/* HEADER COMPACTO */}
      <div className="bg-white px-5 py-3 rounded-xl shadow-sm border border-slate-200 flex justify-between items-center shrink-0">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/matrices" className="text-slate-400 hover:text-lgc-primary transition-colors bg-slate-50 p-2 rounded-lg border border-slate-200"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg></Link>
          <h1 className="text-xl font-heading text-slate-800 uppercase tracking-tight flex items-center gap-3">
            <span className="text-lgc-primary">Workspace</span> <span className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded text-xs tracking-widest font-bold"># {idMatriz}</span>
          </h1>
        </div>
        <div className="flex gap-2">
          {canEdit("matriz") && (
            <>
              <button onClick={() => setShowConfig(true)} className="bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold py-2 px-4 rounded-lg transition-all text-[10px] uppercase tracking-widest border border-slate-300">Configurar Columnas</button>
              <Link href={`/dashboard/matrices/${idMatriz}/preview`} className="bg-white hover:bg-slate-50 text-slate-600 font-bold py-2 px-4 rounded-lg transition-all text-[10px] uppercase tracking-widest border border-slate-300 flex items-center gap-2 shadow-sm"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>Vista Previa </Link>
              <button onClick={() => setShowQuickAdd(true)} className="bg-lgc-primary hover:bg-lgc-hover text-white font-bold py-2 px-4 rounded-lg transition-all shadow-md text-[10px] uppercase tracking-widest flex items-center gap-2"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>Fila Nueva</button>
            </>
          )}
        </div>
      </div>

      {/* DATA GRID DND */}
      <div className="flex-1 bg-white rounded-xl shadow-sm border border-slate-200 overflow-auto relative">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEndItems}>
          <table className="w-full text-left font-sans min-w-max">
            <thead className="bg-slate-50 sticky top-0 z-30 shadow-sm border-b border-slate-200">
              <tr className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
                {canEdit("matriz") && <th className="p-3 w-8"></th>}
                <th className="p-3 w-12">ID</th>
                {configColumnas?.map(colId => <th key={colId} className="p-3">{TODAS_LAS_COLUMNAS.find(c => c.id === colId)?.label}</th>)}
                {canEdit("matriz") && <th className="p-3 text-right">Acción</th>}
              </tr>
            </thead>
            <tbody className="bg-white">
              
              {/* FILA RÁPIDA (INLINE CREATION) */}
              {showQuickAdd && (
                <tr className="bg-blue-50/40 border-b border-blue-100 animate-fade-in align-top shadow-inner">
                  {canEdit("matriz") && <td className="p-3 w-8"></td>}
                  <td className="p-3 w-12"><span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest">NUEVA</span></td>
                  {configColumnas?.map(colId => <td key={colId} className="p-2">{renderQuickAddCell(colId)}</td>)}
                  {canEdit("matriz") && (
                    <td className="p-2 text-right">
                       <div className="flex justify-end gap-1 mt-1">
                         <button onClick={handleSaveNewRow} disabled={isSavingRow} className="bg-green-500 hover:bg-green-600 text-white p-2 rounded shadow-sm disabled:opacity-50"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg></button>
                         <button onClick={() => setShowQuickAdd(false)} className="bg-slate-200 hover:bg-slate-300 text-slate-600 p-2 rounded shadow-sm"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button>
                       </div>
                    </td>
                  )}
                </tr>
              )}

              <SortableContext items={items.map(i => i.id_item_matriz)} strategy={verticalListSortingStrategy}>
                {items.length === 0 && !showQuickAdd ? (
                  <tr><td colSpan={15} className="p-10 text-center text-slate-400 font-bold uppercase text-[10px] tracking-widest">No hay filas en la matriz. Empezá agregando una.</td></tr>
                ) : (
                  items.map(item => (
                    <SortableRow key={item.id_item_matriz} item={item} columnasVisibles={configColumnas} canEdit={canEdit("matriz")} onUpdate={handleUpdateExistingRow} onEdit={(it: any) => { setItemAEditar(it); setIsModalOpen(true); }} estadosCumplimiento={estadosCumplimiento} />
                  ))
                )}
              </SortableContext>
            </tbody>
          </table>
        </DndContext>
      </div>

      {/* MODAL DE EDICIÓN PROFUNDA (Para archivos) */}
      {isModalOpen && (
        <ModalItemMatriz isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} idMatriz={idMatriz} itemEdit={itemAEditar} onSaved={fetchItems} />
      )}
    </div>
  );
}