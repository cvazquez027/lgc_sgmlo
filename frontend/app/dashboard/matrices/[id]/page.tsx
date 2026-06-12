"use client";

import { useEffect, useState, useCallback, useMemo, useRef, useLayoutEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { usePermissions } from "../../../hooks/usePermissions"; 
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

// DICCIONARIOS DE COLUMNAS POR TIPO
const COLUMNAS_REGULATORIAS = [
  { id: 'normas', label: 'Normativas (Tipo, Nro, Año)', custom: false },
  { id: 'norma_nivel_jur', label: 'Nivel Jurisdiccional (Norma)', custom: false },
  { id: 'norma_emisor', label: 'Emisor Norma', custom: false },
  { id: 'norma_sintesis', label: 'Síntesis y Categorías', custom: false },
  { id: 'resumen_legal', label: 'Obligación / Resumen Legal', custom: false },
  { id: 'articulos_aplicables', label: 'Artículos Aplicables', custom: false },
  { id: 'interpretacion_aplicacion', label: 'Interpretación Aplicación', custom: false },
  { id: 'id_tipo_modalidad', label: 'Modalidad', custom: false },
  { id: 'obs_modalidad', label: 'Observación Modalidad', custom: false }
];

const COLUMNAS_CUMPLIMIENTO = [
  ...COLUMNAS_REGULATORIAS,
  { id: 'evidencia_cumplimiento', label: 'Requerimiento Evidencia', custom: false },
  { id: 'id_responsable_establecimiento', label: 'Responsable (Sede)', custom: false },
  { id: 'verificacion_cumplimiento', label: 'Notas de Verificación', custom: false },
  { id: 'estado', label: 'Estado Cumplimiento', custom: false },
  { id: 'vencimiento_plazo', label: 'Fecha de Vencimiento', custom: false },
  { id: 'fecha_cumplimiento', label: 'Fecha de Cumplimiento', custom: false },
  { id: 'obs_estado_cumplimiento', label: 'Observaciones Cumplimiento', custom: false },
  { id: 'adjuntos', label: 'Evidencia (Archivos)', custom: false }
];

// COMPONENTES AUXILIARES
const MultiSelectTags = ({ options, selected, onChange, placeholder }: any) => {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const filtered = options.filter((o: any) => 
    o.descripcion?.toLowerCase().includes(query.toLowerCase()) &&
    !selected.includes(o.descripcion)
  );

  const addTag = (tag: string) => {
    if (!selected.includes(tag)) onChange([...selected, tag]);
    setQuery("");
    setIsOpen(false);
  };

  const removeTag = (tag: string) => {
    onChange(selected.filter((t: string) => t !== tag));
  };

  return (
    <div className="relative w-full">
      <div className="flex flex-wrap gap-1 mb-1.5 min-h-6.25">
        {selected.map((tag: string, idx: number) => (
          <span key={idx} className="bg-blue-50 text-blue-700 border border-blue-200 text-[10px] px-2 py-1 rounded flex items-center gap-1 font-bold shadow-sm uppercase tracking-widest">
            {tag}
            <button type="button" onClick={() => removeTag(tag)} className="text-blue-400 hover:text-red-500 font-bold ml-1 transition-colors text-xs">&times;</button>
          </span>
        ))}
      </div>
      <input
        className="w-full text-[11px] p-2 border border-slate-200 rounded outline-none focus:border-lgc-primary bg-white transition-colors"
        placeholder={selected.length === 0 ? placeholder : "+ Buscar y agregar más..."}
        value={query}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setTimeout(() => setIsOpen(false), 200)}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
      />
      {isOpen && filtered.length > 0 && (
        <div className="absolute z-50 w-full bg-white border border-slate-200 shadow-xl rounded-lg max-h-40 overflow-y-auto mt-1 transition-all">
          {filtered.map((o: any) => (
            <div 
              key={o.id} 
              className="p-2 text-[11px] hover:bg-slate-50 text-slate-700 cursor-pointer border-b last:border-0 border-slate-100" 
              onMouseDown={(e: React.MouseEvent) => { e.preventDefault(); addTag(o.descripcion); }}
            >
              {o.descripcion}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const EditableCell = ({ value, onSave, placeholder = "..." }: any) => {
  const [localValue, setLocalValue] = useState(value || '');
  const [isFocused, setIsFocused] = useState(false);
  useEffect(() => { setLocalValue(value || ''); }, [value]);

  return (
    <div className="relative w-full h-12 focus-within:z-50">
      <textarea
        value={localValue}
        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setLocalValue(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => {
          setIsFocused(false);
          if (localValue.trim() !== (value || '').trim()) onSave(localValue.trim());
        }}
        placeholder={placeholder}
        className={`
          text-[11px] p-2.5 rounded-lg outline-none transition-all resize-none text-slate-700
          ${isFocused ? 'absolute -top-2 -left-2 w-[110%] h-32 bg-white border border-lgc-primary shadow-2xl z-50 ring-4 ring-lgc-primary/20' : 'absolute top-0 left-0 w-full h-full bg-slate-50 border border-slate-200 hover:bg-white hover:border-slate-300 overflow-hidden'}
        `}
      />
    </div>
  );
};

// SELECTOR DE NORMAS CON BOTÓN PARA CARGAR NUEVA (MODAL)
const InlineNormSelectorConAutocompletado = ({ selectedNormas, onChange, onAutocompletar, idEstablecimiento, onSolicitarNuevaNorma }: any) => {
  const [tipo, setTipo] = useState('');
  const [nro, setNro] = useState('');
  const [anio, setAnio] = useState('');
  const [resultados, setResultados] = useState<any[]>([]);
  const [mostrarResultados, setMostrarResultados] = useState(false);
  const [buscando, setBuscando] = useState(false);
  const [tiposNorma, setTiposNorma] = useState<any[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchTipos = async () => {
      const token = localStorage.getItem("sgml_token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=tipo_norma`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setTiposNorma(data.registros?.map((t: any) => ({ id: t.id_tipo_norma || t.id, descripcion: t.descripcion })) || []);
    };
    fetchTipos();
  }, []);

  const buscarNormas = useCallback(async () => {
    if (!tipo && !nro && !anio) {
      setResultados([]);
      setMostrarResultados(false);
      return;
    }
    setBuscando(true);
    const token = localStorage.getItem("sgml_token");
    try {
      let url = `${process.env.NEXT_PUBLIC_API_URL}/normativa/leer.php?`;
      const params = new URLSearchParams();
      if (tipo) params.append('tipo', tipo);
      if (nro) params.append('nro', nro);
      if (anio) params.append('anio', anio);
      if (idEstablecimiento) params.append('id_establecimiento', idEstablecimiento.toString());
      url += params.toString();
      
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      setResultados(data.registros || []);
      setMostrarResultados(true);
    } catch (e) {
      console.error(e);
    } finally {
      setBuscando(false);
    }
  }, [tipo, nro, anio, idEstablecimiento]);

  useEffect(() => {
    const delay = setTimeout(() => buscarNormas(), 500);
    return () => clearTimeout(delay);
  }, [tipo, nro, anio, buscarNormas]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setMostrarResultados(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const seleccionarNorma = (norma: any) => {
    const nuevaNorma = {
      id_norma: norma.id_norma,
      tipo_norma: norma.tipo_norma_desc,
      numero: norma.numero,
      anio: norma.anio,
      emisor_desc: norma.emisor_desc,
      nivel_jurisdiccion_desc: norma.nivel_jurisdiccion_desc,
      jurisdiccion_desc: norma.jurisdiccion_desc,
      sintesis: norma.sintesis,
      categorias: norma.categorias,
      url_norma: norma.url_norma
    };
    const nuevasNormas = [...selectedNormas, nuevaNorma];
    onChange(nuevasNormas);
    if (onAutocompletar) onAutocompletar(nuevaNorma);
    setTipo('');
    setNro('');
    setAnio('');
    setResultados([]);
    setMostrarResultados(false);
  };

  const removerNorma = (index: number) => {
    const nuevas = selectedNormas.filter((_: any, i: number) => i !== index);
    onChange(nuevas);
    if (onAutocompletar && nuevas.length === 0) onAutocompletar(null);
  };

  return (
    <div className="relative w-full" ref={containerRef}>
      <div className="flex flex-col gap-1 mb-2">
        {selectedNormas.map((n: any, idx: number) => (
          <span key={idx} className="bg-slate-100 text-slate-700 border border-slate-200 text-[10px] px-2 py-1.5 rounded flex justify-between items-center font-bold tracking-widest w-full">
            <span>{n.tipo_norma} {n.numero}/{n.anio} - {n.emisor_desc}</span>
            <button type="button" onClick={() => removerNorma(idx)} className="text-red-400 hover:text-red-600 bg-red-50 px-1.5 py-0.5 rounded ml-2">×</button>
          </span>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-2 mb-2">
        <select className="text-[11px] p-2 border border-slate-200 rounded outline-none bg-slate-50" value={tipo} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setTipo(e.target.value)}>
          <option value="">Tipo</option>
          {tiposNorma.map((t: any) => <option key={t.id} value={t.descripcion}>{t.descripcion}</option>)}
        </select>
        <input type="text" placeholder="Nro" className="text-[11px] p-2 border border-slate-200 rounded outline-none" value={nro} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNro(e.target.value)} />
        <input type="text" placeholder="Año" className="text-[11px] p-2 border border-slate-200 rounded outline-none" value={anio} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAnio(e.target.value)} />
      </div>
      {mostrarResultados && (
        <div className="absolute z-50 w-full bg-white border border-slate-200 shadow-2xl rounded-xl max-h-64 overflow-y-auto mt-1" style={{ top: '100%', left: 0 }}>
          {buscando && <div className="p-3 text-center text-slate-400 text-xs">Buscando...</div>}
          {!buscando && resultados.length === 0 && (
            <div className="p-3 text-center">
              <p className="text-xs text-slate-500 mb-2">No se encontraron normas con esos filtros.</p>
              <button
                type="button"
                onClick={onSolicitarNuevaNorma}
                className="text-xs text-lgc-primary font-bold hover:underline"
              >
                + Cargar nueva normativa manualmente
              </button>
            </div>
          )}
          {resultados.map((r: any) => (
            <div 
              key={r.id_norma} 
              className="p-3 hover:bg-slate-50 cursor-pointer border-b last:border-0" 
              onMouseDown={() => seleccionarNorma(r)}
            >
              <div className="font-bold text-lgc-primary text-xs">{r.tipo_norma_desc} {r.numero}/{r.anio}</div>
              <div className="text-[10px] text-slate-500 truncate">{r.emisor_desc}</div>
              <div className="text-[10px] text-slate-400 line-clamp-2">{r.sintesis || 'Sin síntesis'}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const InlineNormSelector = ({ selectedNormas, onChange }: any) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (query.trim().length < 1) { setResults([]); return; }
    const timeoutId = setTimeout(async () => {
      const token = localStorage.getItem("sgml_token");
      try {
        let res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/normativa/leer.php?buscar=${query}`, { headers: { Authorization: `Bearer ${token}` } });
        const data = await res.json();
        const qLower = query.toLowerCase();
        setResults((data.registros || []).filter((r: any) => (r.numero && r.numero.toString().toLowerCase().includes(qLower)) || (r.tipo_norma_desc && r.tipo_norma_desc.toLowerCase().includes(qLower))));
      } catch (e) {} 
    }, 400); 
    return () => clearTimeout(timeoutId);
  }, [query]);

  return (
    <div className="relative w-full">
      <div className="flex flex-col gap-1 mb-2">
        {selectedNormas.map((n: any, idx: number) => (
          <span key={idx} className="bg-slate-100 text-slate-700 border border-slate-200 text-[10px] px-2 py-1.5 rounded flex justify-between items-center font-bold tracking-widest w-full">
            <span>{n.tipo_norma_desc || n.tipo_norma} {n.numero}</span>
            <button type="button" onClick={() => onChange(selectedNormas.filter((_:any, i:number) => i !== idx))} className="text-red-400 hover:text-red-600 bg-red-50 px-1.5 py-0.5 rounded ml-2">×</button>
          </span>
        ))}
      </div>
      <input type="text" placeholder="+ Buscar Norma por N°..." className="w-full text-[11px] p-2.5 border border-slate-200 rounded-lg outline-none focus:border-lgc-primary bg-slate-50 hover:bg-white shadow-sm transition-colors" value={query} onChange={(e: React.ChangeEvent<HTMLInputElement>) => { setQuery(e.target.value); setIsOpen(true); }} onFocus={() => { if(query.length > 0) setIsOpen(true); }} />
      {isOpen && results.length > 0 && (
        <div className="absolute top-full left-0 mt-1 w-full bg-white border border-slate-200 shadow-2xl rounded-xl z-50 max-h-48 overflow-y-auto">
          <div className="flex justify-end p-2 bg-slate-50 border-b sticky top-0"><button type="button" onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-red-500 text-[10px] font-bold uppercase tracking-widest">Cerrar</button></div>
          {results.map((r: any) => (
            <div key={r.id_norma} className="p-3 text-[11px] hover:bg-slate-50 cursor-pointer border-b last:border-0" onMouseDown={() => { onChange([...selectedNormas, { id_norma: r.id_norma, tipo_norma: r.tipo_norma_desc || 'NORMA', numero: r.numero, anio: r.anio, emisor_desc: r.emisor_desc, nivel_jurisdiccion_desc: r.nivel_jurisdiccion_desc, jurisdiccion_desc: r.jurisdiccion_desc, sintesis: r.sintesis, categorias: r.categorias, url_norma: r.url_norma }]); setIsOpen(false); setQuery(''); setResults([]); }}>
              <span className="font-bold text-lgc-primary tracking-wider">{r.tipo_norma_desc} {r.numero}/{r.anio}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const SortableConfigItem = ({ col, onRemove }: any) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: col.id });
  const style = { transform: CSS.Transform.toString(transform), transition, zIndex: isDragging ? 50 : 1, opacity: isDragging ? 0.5 : 1, position: isDragging ? 'relative' as 'relative' : 'static' as 'static' };
  return (
    <div ref={setNodeRef} style={style} className="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-lg shadow-sm mb-2 group">
       <div className="flex items-center gap-3">
         <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing text-slate-400 hover:text-lgc-primary touch-none"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" /></svg></div>
         <span className="text-[11px] font-bold uppercase text-slate-700 tracking-widest flex items-center gap-2">
            {col.label} {col.custom && <span className="bg-orange-100 text-orange-600 text-[8px] px-1.5 py-0.5 rounded">CUSTOM</span>}
         </span>
       </div>
       <button onClick={() => onRemove(col.id)} className="text-slate-300 hover:text-red-500" title="Quitar columna"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button>
    </div>
  );
};

// COMPONENTE SORTABLE ROW
const SortableRow = ({ item, columnasVisibles, onUpdate, onDelete, onCopy, canEdit, canEditField, estadosCumplimiento, responsables, tiposModalidad, onOpenEvidencia, forceExpand, isDragDisabled, onSolicitarNuevaNorma, idEstablecimiento }: any) => {
  const [isExpanded, setIsExpanded] = useState(false);
  useEffect(() => { setIsExpanded(forceExpand); }, [forceExpand]);

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: item.id_item_matriz });
  const style = { transform: isDragging && transform ? CSS.Transform.toString(transform) : undefined, transition, opacity: isDragging ? 0.7 : 1, zIndex: isDragging ? 40 : 1 };

  const renderCelda = (colId: string, isReadOnly: boolean) => {
    if (colId.startsWith('custom_')) {
        return isReadOnly 
          ? <div className="text-[11px] p-2.5 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 min-h-12 wrap-break-words">{item[colId] || <span className="italic text-slate-300">—</span>}</div>
          : <EditableCell value={item[colId]} onSave={(val:string) => onUpdate(item.id_item_matriz, colId, val)} placeholder="Valor personalizado..." />;
    }

    switch(colId) {
      case 'resumen_legal':
      case 'articulos_aplicables':
      case 'interpretacion_aplicacion':
      case 'obs_modalidad':
      case 'evidencia_cumplimiento':
      case 'verificacion_cumplimiento':
      case 'obs_estado_cumplimiento':
        return isReadOnly 
          ? <div className="text-[11px] p-2.5 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 min-h-12 wrap-break-words">{item[colId] || <span className="italic text-slate-300">—</span>}</div>
          : <EditableCell value={item[colId]} onSave={(val:string) => onUpdate(item.id_item_matriz, colId, val)} />;
      
      case 'vencimiento_plazo': 
      case 'fecha_cumplimiento':
        return isReadOnly
          ? <div className="text-[11px] p-2.5 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 min-h-12">{item[colId] ? new Date(item[colId]).toLocaleDateString('es-AR') : <span className="italic text-slate-300">—</span>}</div>
          : <input type="date" className="w-full text-[11px] p-2.5 border border-slate-200 hover:border-slate-300 hover:bg-white bg-slate-50 rounded-lg outline-none transition-colors" value={item[colId] || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => onUpdate(item.id_item_matriz, colId, e.target.value)} />;
      
      case 'normas': 
        return isReadOnly
          ? <div className="text-[11px] p-2.5 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 min-h-12 flex flex-col gap-1">{item.normas_vinculadas?.length > 0 ? item.normas_vinculadas.map((n:any, i:number) => <span key={i} className="font-bold">{n.tipo_norma_desc || n.tipo_norma} {n.numero}/{n.anio}</span>) : <span className="italic text-slate-300">—</span>}</div>
          : <InlineNormSelectorConAutocompletado
              selectedNormas={item.normas_vinculadas || []}
              onChange={(normas: any) => onUpdate(item.id_item_matriz, 'normas_vinculadas', normas)}
              onAutocompletar={() => {}} // No es necesario en edición, pero se puede dejar vacío
              idEstablecimiento={idEstablecimiento}
              onSolicitarNuevaNorma={() => onSolicitarNuevaNorma(item)}
            />;
      
      case 'norma_sintesis':
        return (
          <div className="flex flex-col gap-2">
            {(!item.normas_vinculadas || item.normas_vinculadas.length === 0) && <span className="text-[10px] text-slate-400 italic">No hay normas vinculadas</span>}
            {item.normas_vinculadas?.map((n:any, i:number) => (
              <div key={i} className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                <p className="text-[10px] text-slate-600 line-clamp-4 mb-2 leading-relaxed" title={n.sintesis}>{n.sintesis || 'Norma sin síntesis cargada.'}</p>
                {n.categorias && n.categorias.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-2">{n.categorias.map((c:string, idx:number) => <span key={idx} className="bg-white text-lgc-primary border border-lgc-primary/30 text-[9px] font-bold px-1.5 py-0.5 rounded shadow-sm">{c}</span>)}</div>
                )}
                {n.url_norma && <a href={n.url_norma} target="_blank" rel="noopener noreferrer" className="text-[9px] text-lgc-accent font-bold hover:underline flex items-center gap-1"><svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg> Ver Original</a>}
              </div>
            ))}
          </div>
        );
      
      case 'id_tipo_modalidad':
        return isReadOnly
          ? <div className="text-[11px] p-2.5 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 min-h-12">{tiposModalidad.find((t:any) => t.id == item.id_tipo_modalidad)?.descripcion || <span className="italic text-slate-300">—</span>}</div>
          : <select className="w-full text-[11px] p-2.5 border border-slate-200 hover:border-slate-300 bg-slate-50 hover:bg-white rounded-lg outline-none cursor-pointer transition-colors" value={item.id_tipo_modalidad || ''} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => onUpdate(item.id_item_matriz, 'id_tipo_modalidad', e.target.value)}>
              <option value="">Sin Asignar</option>
              {tiposModalidad.map((t: any) => <option key={t.id} value={t.id}>{t.descripcion}</option>)}
            </select>;
      
      case 'id_responsable_establecimiento':
        return isReadOnly
          ? <div className="text-[11px] p-2.5 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 min-h-12">{responsables.find((r:any) => r.id_responsable_establecimiento == item.id_responsable_establecimiento)?.descripcion || <span className="italic text-slate-300">—</span>}</div>
          : <select className="w-full text-[11px] p-2.5 border border-slate-200 hover:border-slate-300 bg-slate-50 hover:bg-white rounded-lg outline-none cursor-pointer transition-colors" value={item.id_responsable_establecimiento || ''} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => onUpdate(item.id_item_matriz, 'id_responsable_establecimiento', e.target.value)}>
              <option value="">Sin Asignar</option>
              {responsables.map((r: any) => <option key={r.id_responsable_establecimiento} value={r.id_responsable_establecimiento}>{r.descripcion}</option>)}
            </select>;
      
      case 'adjuntos':
        return (
          <button onClick={() => onOpenEvidencia(item)} className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2.5 rounded-lg border border-slate-300 text-[10px] font-bold uppercase tracking-widest flex items-center gap-2 transition-colors w-max shadow-sm">
            <svg className="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg> 
            {item.documentos_vinculados?.length || 0} Archivos Cargados
          </button>
        );
      
      case 'norma_emisor':
        const emisores_unicos = Array.from(new Set(item.normas_vinculadas?.map((n:any) => n.emisor_desc).filter(Boolean)));
        return <div className="flex flex-col gap-1 w-full p-1.5">{emisores_unicos.length > 0 ? emisores_unicos.map((emi: any, i: number) => <span key={i} className="text-slate-600 text-[11px] font-bold uppercase truncate" title={emi as string}>• {emi}</span>) : <span className="text-slate-400 text-[10px] italic">Auto</span>}</div>;
      
      case 'norma_nivel_jur':
        const niveles_unicos = Array.from(new Set(item.normas_vinculadas?.map((n:any) => n.nivel_jurisdiccion_desc || n.jurisdiccion_desc).filter(Boolean)));
        return <div className="flex flex-wrap gap-1.5 w-full p-1.5">{niveles_unicos.length > 0 ? niveles_unicos.map((niv: any, i: number) => <span key={i} className="bg-slate-100 border border-slate-200 text-slate-600 text-[10px] font-bold uppercase px-2 py-1 rounded-md shadow-sm">{niv}</span>) : <span className="text-slate-400 text-[10px] italic">Auto</span>}</div>;
      
      case 'estado':
        const color = item.color_hex ? `#${item.color_hex}` : '#cbd5e1';
        return isReadOnly
          ? <div className="text-[10px] font-bold uppercase p-2.5 rounded-lg border min-h-12 flex items-center" style={{ backgroundColor: `${color}10`, color: color, borderColor: `${color}40` }}>{estadosCumplimiento.find((e:any) => e.id == item.id_estado_cumplimiento)?.descripcion || <span className="italic text-slate-300">—</span>}</div>
          : <select className="w-full text-[10px] font-bold uppercase p-2.5 rounded-lg outline-none shadow-sm cursor-pointer border transition-colors" style={{ backgroundColor: `${color}10`, color: color, borderColor: `${color}40` }} value={item.id_estado_cumplimiento || ''} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => onUpdate(item.id_item_matriz, 'id_estado_cumplimiento', e.target.value)}>
              <option value="" disabled>Seleccione...</option>
              {estadosCumplimiento.map((est: any) => <option key={est.id} value={est.id}>{est.descripcion}</option>)}
            </select>;
      
      default: return '-';
    }
  };

  return (
    <div ref={setNodeRef} style={style} className={`flex flex-col bg-white rounded-xl shadow-sm border mb-4 transition-all duration-300 relative ${isDragging ? 'ring-4 ring-lgc-primary/20 border-lgc-primary' : 'border-slate-200 hover:border-slate-300'}`}>
      <div className="flex items-center justify-between p-3.5 bg-white rounded-t-xl cursor-pointer hover:bg-slate-50 transition-colors group" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-center gap-4 flex-1 pr-4 overflow-hidden">
          {canEdit && !isDragDisabled ? (
            <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing text-slate-300 hover:text-lgc-primary touch-none p-1 transition-colors" onClick={(e: React.MouseEvent) => e.stopPropagation()} title="Arrastrar para reordenar">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 8h16M4 16h16" /></svg>
            </div>
          ) : (
            canEdit && isDragDisabled && (
              <div className="text-slate-200 p-1 cursor-not-allowed" title="Ordenamiento deshabilitado con filtros activos" onClick={(e: React.MouseEvent) => e.stopPropagation()}>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 8h16M4 16h16" /></svg>
              </div>
            )
          )}
          <span className="bg-slate-100 text-slate-500 font-bold text-[10px] px-2.5 py-1.5 rounded-md border border-slate-200 shrink-0">
            #{(item.orden !== undefined && item.orden !== null) ? item.orden + 1 : item.id_item_matriz}
          </span>
          <div className="flex flex-col flex-1 min-w-0">
            {item.normas_vinculadas?.map((n:any, idx:number) => (
              <div key={idx} className="flex flex-col gap-0.5">
                <span className="bg-slate-100 border border-slate-200 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded-md shadow-sm inline-block w-fit">
                  {(n.tipo_norma_desc || n.tipo_norma)} {n.numero}/{n.anio} - {n.emisor_desc}
                </span>
                <span className="text-[9px] text-slate-400 truncate">{n.sintesis ? (n.sintesis.length > 60 ? n.sintesis.substring(0,60)+'...' : n.sintesis) : ''}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="flex items-center gap-4 shrink-0 pl-2 border-l border-slate-100">
          {!isExpanded && item.documentos_vinculados?.length > 0 && (
             <span className="flex items-center gap-1.5 bg-blue-50 text-blue-600 border border-blue-100 text-[10px] px-2.5 py-1 rounded-full font-bold shadow-sm">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
                {item.documentos_vinculados.length}
             </span>
          )}
          {!isExpanded && item.color_hex && (
             <div className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: `#${item.color_hex}` }} title="Estado"></div>
          )}
          {canEdit && (
            <div className="flex gap-1">
              <button onClick={(e: React.MouseEvent) => { e.stopPropagation(); if (confirm("¿Eliminar este ítem? Esta acción no se puede deshacer.")) onDelete(item.id_item_matriz); }} className="text-slate-400 hover:text-red-500 p-1" title="Eliminar ítem">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
              </button>
              <button onClick={(e: React.MouseEvent) => { e.stopPropagation(); onCopy(item); }} className="text-slate-400 hover:text-lgc-primary p-1" title="Copiar ítem">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
              </button>
            </div>
          )}
          <div className={`w-8 h-8 flex items-center justify-center rounded-full transition-colors ${isExpanded ? 'bg-slate-100 text-lgc-primary' : 'text-slate-400 group-hover:bg-slate-100'}`}>
            <svg className={`w-5 h-5 transform transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
          </div>
        </div>
      </div>
      
      {isExpanded && (
        <div className="transition-all duration-300 overflow-visible border-t border-slate-100">
          <div className="p-5 md:p-6 bg-slate-50/30 rounded-b-xl">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {columnasVisibles.map((col: any) => (
                <div key={col.id} className="flex flex-col gap-2 group/field">
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest flex items-center gap-1.5 ml-1">
                    {col.label} 
                    {col.custom && <span className="bg-orange-100 text-orange-600 text-[8px] px-1.5 py-0.5 rounded ml-1">CUSTOM</span>}
                  </label>
                  <div className="relative w-full z-10 hover:z-40 focus-within:z-50">
                    {renderCelda(col.id, canEditField ? !canEditField(col.id) : false)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default function WorkspaceMatrizPage() {
  const router = useRouter();
  const params = useParams(); 
  const searchParams = useSearchParams();
  const idMatriz = params.id as string; 
  const { canRead, canEdit } = usePermissions();
  
  const [items, setItems] = useState<any[]>([]);
  const [headerInfo, setHeaderInfo] = useState<any>(null); 
  const [tipoMatriz, setTipoMatriz] = useState<number>(1);
  const [estadoMatriz, setEstadoMatriz] = useState<number>(1);
  const [configColumnas, setConfigColumnas] = useState<any[]>([]);
  const [tempConfig, setTempConfig] = useState<any[]>([]);
  const [nuevaColumna, setNuevaColumna] = useState("");
  
  const [loading, setLoading] = useState(true);
  const [showConfig, setShowConfig] = useState(false);
  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [isSavingRow, setIsSavingRow] = useState(false);
  const [expandAll, setExpandAll] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const quickAddFormRef = useRef<HTMLDivElement>(null);
  const firstInputRef = useRef<HTMLInputElement>(null);
  const mainContainerRef = useRef<HTMLDivElement>(null);
  
  // DICCIONARIOS
  const [estadosCumplimiento, setEstadosCumplimiento] = useState<any[]>([]);
  const [tiposModalidad, setTiposModalidad] = useState<any[]>([]);
  const [responsables, setResponsables] = useState<any[]>([]);
  
  const [tiposNorma, setTiposNorma] = useState<any[]>([]);
  const [emisoresNorma, setEmisoresNorma] = useState<any[]>([]);
  const [estadosNorma, setEstadosNorma] = useState<any[]>([]);
  const [categoriasGlobales, setCategoriasGlobales] = useState<any[]>([]);

  const [idEstablecimiento, setIdEstablecimiento] = useState<number | null>(null);

  // MODAL EVIDENCIAS
  const [itemEvidencia, setItemEvidencia] = useState<any>(null);
  const [evidenciaFile, setEvidenciaFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  // Estado para nueva fila
  const [newRowData, setNewRowData] = useState<any>({
    id_estado_cumplimiento: '',
    id_tipo_modalidad: '',
    normas_vinculadas: [],
    norma_emisor: '',
    norma_nivel_jur: '',
    norma_sintesis: '',
    sintesis_categorias: '',
    url_norma: ''
  });

  // FILTROS AVANZADOS
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [filtros, setFiltros] = useState<any>({
    norma: { tipo: '', nro: '', anio: '', sintesis: '', emisor: '', nivel: '', jurisdiccion: '', categorias: [] as string[] },
    evidencia: '', 
    dinamicos: {} 
  });

  const [isDashboardOpen, setIsDashboardOpen] = useState(false);

  // Botones flotantes de scroll
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  const [itemEnEdicion, setItemEnEdicion] = useState<any>(null);

  // NUEVO: Modal de nueva normativa
  const [showNuevaNormaModal, setShowNuevaNormaModal] = useState(false);
  const [cargandoNuevaNorma, setCargandoNuevaNorma] = useState(false);
  const [nuevaNormaForm, setNuevaNormaForm] = useState({
    id_tipo_norma: "",
    numero: "",
    anio: new Date().getFullYear(),
    id_emisor_norma: "",
    sintesis: "",
    url_norma: "",
    id_estado_norma: "1",
    origen_carga: "Manual",
    fecha_publicacion: ""
  });

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }), useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }));

  // Configurar scroll listener
  useEffect(() => {
    const container = mainContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const scrollTop = container.scrollTop;
      const scrollHeight = container.scrollHeight;
      const clientHeight = container.clientHeight;
      setShowScrollTop(scrollTop > 50);
      setShowScrollBottom(scrollTop + clientHeight < scrollHeight - 50);
    };

    container.addEventListener('scroll', handleScroll);

    // Pequeño delay para que el DOM tenga las alturas reales calculadas
    const timer = setTimeout(handleScroll, 100);

    return () => {
      container.removeEventListener('scroll', handleScroll);
      clearTimeout(timer);
    };
  }, [items, loading]); // ← re-ejecutar cuando cambia el contenido

  const scrollToTop = () => {
    mainContainerRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  };
  const scrollToBottom = () => {
    const container = mainContainerRef.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
  };

  useEffect(() => {
    const shouldOpenConfig = searchParams.get('config') === 'true';
    if (shouldOpenConfig && !showConfig && !loading) {
      setShowConfig(true);
      router.replace(`/dashboard/matrices/${idMatriz}`, { scroll: false });
    }
  }, [searchParams, showConfig, loading, idMatriz, router]);

  const fetchItems = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    try {
      const resH = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/leer.php?id_matriz=${idMatriz}`, { headers: { "Authorization": `Bearer ${token}` } });
      const dataH = await resH.json();
      const info = dataH.registros[0];
      setTipoMatriz(info.id_tipo_matriz);
      setEstadoMatriz(info.id_estado_matriz || 1);
      setHeaderInfo(info);
      setIdEstablecimiento(info.id_cliente_establecimiento);

      const resR = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/responsables/leer_responsables.php?id_establecimiento=${info.id_cliente_establecimiento}`, { headers: { "Authorization": `Bearer ${token}` } });
      const dataR = await resR.json();
      setResponsables(dataR.registros || []);

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/leer_items.php?id_matriz=${idMatriz}`, { headers: { "Authorization": `Bearer ${token}` } });
      const data = await res.json();
      
      let configParsed = data.config_columnas;
      if (typeof configParsed === 'string') {
          try { configParsed = JSON.parse(configParsed); } catch(e) { configParsed = []; }
      }
      if (!Array.isArray(configParsed)) configParsed = [];
      
      const ALL_COLS = info.id_tipo_matriz === 1 ? COLUMNAS_REGULATORIAS : COLUMNAS_CUMPLIMIENTO;
      
      if (configParsed.length > 0) {
          if (typeof configParsed[0] === 'string') {
              configParsed = configParsed.map((idStr:string) => {
                 const match = ALL_COLS.find(c => c.id === idStr);
                 return { 
                     id: idStr, 
                     label: match?.label || (idStr.startsWith('custom_') ? 'Columna Personalizada' : idStr), 
                     custom: idStr.startsWith('custom_') 
                 };
              });
          }
      }
      
      const configFinal = configParsed.length > 0 ? configParsed : ALL_COLS;
      setConfigColumnas(configFinal);
      setTempConfig(configFinal); 
      setItems(data.registros || []);
      
      if (configFinal.length === 0) setShowConfig(true); 
    } catch (err) {} finally { setLoading(false); }
  }, [idMatriz]);

  useEffect(() => {
    const fetchDiccionarios = async () => {
        const token = localStorage.getItem("sgml_token");
        const headers = { "Authorization": `Bearer ${token}` };

        const resE = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=estado_cumplimiento`, { headers });
        const dataE = await resE.json();
        setEstadosCumplimiento(dataE.registros?.map((e:any) => ({ id: e.id_estado_cumplimiento || e.id, descripcion: e.descripcion })) || []);

        const resM = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=tipo_modalidad`, { headers });
        const dataM = await resM.json();
        setTiposModalidad(dataM.registros?.map((e:any) => ({ id: e.id_tipo_modalidad || e.id, descripcion: e.descripcion })) || []);

        const resTN = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=tipo_norma`, { headers });
        const dataTN = await resTN.json();
        setTiposNorma(dataTN.registros?.map((e:any) => ({ id: e.id_tipo_norma || e.id, descripcion: e.descripcion })) || []);

        const resEN = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=emisor_norma`, { headers });
        const dataEN = await resEN.json();
        setEmisoresNorma(dataEN.registros?.map((e:any) => ({ id: e.id_emisor_norma || e.id, descripcion: e.descripcion })) || []);

        const resEstadoNorma = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=estado_norma`, { headers });
        const dataEstadoNorma = await resEstadoNorma.json();
        setEstadosNorma(dataEstadoNorma.registros?.map((e:any) => ({ id: e.id_estado_norma || e.id, descripcion: e.descripcion })) || []);

        const resCat = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=categoria`, { headers });
        const dataCat = await resCat.json();
        setCategoriasGlobales(dataCat.registros?.map((e:any) => ({ id: e.id_categoria || e.id, descripcion: e.descripcion })) || []);
    };
    if (canRead("matriz")) { fetchItems(); fetchDiccionarios(); }
  }, [fetchItems, canRead]);

  const nivelesDisponibles = useMemo(() => {
    const setNiveles = new Set(items.flatMap(i => (i.normas_vinculadas || []).map((n:any) => n.nivel_jurisdiccion_desc)).filter(Boolean));
    return Array.from(setNiveles).map(desc => ({ id: desc, descripcion: desc }));
  }, [items]);

  const jurisdiccionesDisponibles = useMemo(() => {
    const setJur = new Set(items.flatMap(i => (i.normas_vinculadas || []).map((n:any) => n.jurisdiccion_desc)).filter(Boolean));
    return Array.from(setJur).map(desc => ({ id: desc, descripcion: desc }));
  }, [items]);

  const itemsFiltrados = useMemo(() => {
    return items.filter(item => {
      if (Object.values(filtros.norma).some(v => typeof v === 'string' ? v !== '' : (v as string[]).length > 0)) {
         const matchNorma = item.normas_vinculadas?.some((n:any) => {
            if (filtros.norma.tipo && !((n.tipo_norma_desc || n.tipo_norma || '').toLowerCase().includes(filtros.norma.tipo.toLowerCase()))) return false;
            if (filtros.norma.nro && !(n.numero?.toString().includes(filtros.norma.nro))) return false;
            if (filtros.norma.anio && !(n.anio?.toString().includes(filtros.norma.anio))) return false;
            if (filtros.norma.sintesis && !(n.sintesis?.toLowerCase().includes(filtros.norma.sintesis.toLowerCase()))) return false;
            if (filtros.norma.emisor && !(n.emisor_desc?.toLowerCase().includes(filtros.norma.emisor.toLowerCase()))) return false;
            if (filtros.norma.nivel && !(n.nivel_jurisdiccion_desc?.toLowerCase().includes(filtros.norma.nivel.toLowerCase()))) return false;
            if (filtros.norma.jurisdiccion && !(n.jurisdiccion_desc?.toLowerCase().includes(filtros.norma.jurisdiccion.toLowerCase()))) return false;
            
            if (filtros.norma.categorias && filtros.norma.categorias.length > 0) {
               if (!n.categorias) return false;
               const hasAll = filtros.norma.categorias.every((catFilter: string) => 
                  n.categorias.some((c:string) => c.toLowerCase().includes(catFilter.toLowerCase()))
               );
               if (!hasAll) return false;
            }
            return true;
         });
         if (!matchNorma) return false;
      }

      if (filtros.evidencia === 'con' && (!item.documentos_vinculados || item.documentos_vinculados.length === 0)) return false;
      if (filtros.evidencia === 'sin' && (item.documentos_vinculados && item.documentos_vinculados.length > 0)) return false;

      for (const colId in filtros.dinamicos) {
          const searchVal = filtros.dinamicos[colId];
          if (searchVal) {
              let field = colId;
              if (colId === 'estado') field = 'id_estado_cumplimiento';
              
              if (colId === 'estado' || colId === 'id_tipo_modalidad' || colId === 'id_responsable_establecimiento') {
                  if (item[field]?.toString() !== searchVal.toString()) return false;
              } else {
                  const itemVal = item[field] ? item[field].toString().toLowerCase() : '';
                  if (!itemVal.includes(searchVal.toLowerCase())) return false;
              }
          }
      }
      return true;
    });
  }, [items, filtros]);

  // Forzar recálculo de botones flotantes cuando cambia el contenido (items, filtros, expansión)
  useEffect(() => {
    const container = mainContainerRef.current;
    if (!container) return;
    const timeoutId = setTimeout(() => {
      const scrollTop = container.scrollTop;
      const scrollHeight = container.scrollHeight;
      const clientHeight = container.clientHeight;
      setShowScrollTop(scrollTop > 50);
      setShowScrollBottom(scrollTop + clientHeight < scrollHeight - 50);
    }, 150);
    return () => clearTimeout(timeoutId);
  }, [items, itemsFiltrados, expandAll]);

  const hasActiveFilters = Object.values(filtros.norma).some(v => typeof v === 'string' ? v !== '' : (v as string[]).length > 0) || Object.values(filtros.dinamicos).some(v => v !== '') || filtros.evidencia !== '';

  const dashboardMetrics = useMemo(() => {
    const totalNormas = new Set(
      items.flatMap(i => (i.normas_vinculadas || []).map((n: any) => n.id_norma))
    ).size;

    const jurMap: Record<string, number> = {};
    items.forEach(item => {
      (item.normas_vinculadas || []).forEach((n: any) => {
        const jur = n.jurisdiccion_desc || n.nivel_jurisdiccion_desc || 'Sin especificar';
        jurMap[jur] = (jurMap[jur] || 0) + 1;
      });
    });
    const porJurisdiccion = Object.entries(jurMap)
      .map(([nombre, cantidad]) => ({ nombre, cantidad }))
      .sort((a, b) => b.cantidad - a.cantidad);

    const catMap: Record<string, number> = {};
    items.forEach(item => {
      (item.normas_vinculadas || []).forEach((n: any) => {
        (n.categorias || []).forEach((c: string) => {
          catMap[c] = (catMap[c] || 0) + 1;
        });
      });
    });
    const rankingCategorias = Object.entries(catMap)
      .map(([nombre, cantidad]) => ({ nombre, cantidad }))
      .sort((a, b) => b.cantidad - a.cantidad)
      .slice(0, 10);

    const cumplimientoMap: Record<string, { label: string; color: string; cantidad: number }> = {};
    items.forEach(item => {
      const id = item.id_estado_cumplimiento?.toString() || '';
      const label = item.estado_cumplimiento_desc || 'Sin informar';
      const color = item.color_hex ? `#${item.color_hex}` : '#94a3b8';
      if (!cumplimientoMap[id]) cumplimientoMap[id] = { label, color, cantidad: 0 };
      cumplimientoMap[id].cantidad++;
    });
    const porCumplimiento = Object.values(cumplimientoMap).sort((a, b) => b.cantidad - a.cantidad);
    const totalCumplimiento = porCumplimiento.reduce((s, e) => s + e.cantidad, 0);

    return { totalNormas, porJurisdiccion, rankingCategorias, porCumplimiento, totalCumplimiento };
  }, [items]);

  const agregarColumnaCustom = () => {
    if(!nuevaColumna.trim()) return;
    setTempConfig([...tempConfig, { id: `custom_${Date.now()}`, label: nuevaColumna, custom: true }]);
    setNuevaColumna("");
  };

  const guardarConfiguracion = async () => {
    const token = localStorage.getItem("sgml_token");
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/guardar_config.php`, {
      method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ id_matriz: idMatriz, columnas: tempConfig })
    });
    setConfigColumnas(tempConfig); setShowConfig(false);
  };

  const handleUpdateExistingRow = async (itemId: number, field: string, value: any) => {
    const currentItem = items.find(i => i.id_item_matriz === itemId);
    if (!currentItem) return;
    const updatedItem = { ...currentItem, [field]: value };
    setItems(items.map(i => i.id_item_matriz === itemId ? updatedItem : i));
    const payload = { ...updatedItem, id_matriz: idMatriz, normas_vinculadas: updatedItem.normas_vinculadas?.map((n:any) => n.id_norma) || [] };
    const token = localStorage.getItem("sgml_token");
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/guardar_item.php`, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }, body: JSON.stringify(payload) });
    if (field === 'id_estado_cumplimiento' || field === 'normas_vinculadas') fetchItems();
  };

  const handleDeleteItem = async (itemId: number) => {
    if (!confirm("¿Eliminar este ítem? Esta acción no se puede deshacer.")) return;
    const token = localStorage.getItem("sgml_token");
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/eliminar_item.php`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      body: JSON.stringify({ id_item_matriz: itemId })
    });
    if (res.ok) {
      fetchItems();
    } else {
      alert("Error al eliminar el ítem.");
    }
  };

  const handleCopyItem = (item: any) => {
    const nuevasNormas = item.normas_vinculadas?.map((n: any) => ({
      id_norma: n.id_norma,
      tipo_norma: n.tipo_norma_desc || n.tipo_norma,
      numero: n.numero,
      anio: n.anio,
      emisor_desc: n.emisor_desc,
      nivel_jurisdiccion_desc: n.nivel_jurisdiccion_desc,
      jurisdiccion_desc: n.jurisdiccion_desc,
      sintesis: n.sintesis,
      categorias: n.categorias,
      url_norma: n.url_norma
    })) || [];
    setNewRowData({
      id_estado_cumplimiento: item.id_estado_cumplimiento?.toString() || '',
      id_tipo_modalidad: item.id_tipo_modalidad?.toString() || '',
      normas_vinculadas: nuevasNormas,
      norma_emisor: '',
      norma_nivel_jur: '',
      norma_sintesis: '',
      sintesis_categorias: '',
      url_norma: ''
    });
    if (nuevasNormas.length > 0) {
      autocompletarCampos(nuevasNormas[0]);
    }
    setShowQuickAdd(true);
    setTimeout(() => {
      quickAddFormRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      if (firstInputRef.current) firstInputRef.current.focus();
    }, 100);
  };

  const handleSaveNewRow = async () => {
    setIsSavingRow(true);
    const token = localStorage.getItem("sgml_token");
    const payload = {
      id_matriz: idMatriz,
      ...newRowData,
      normas_vinculadas: newRowData.normas_vinculadas.map((n:any) => n.id_norma) || []
    };
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/guardar_item.php`, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }, body: JSON.stringify(payload) });
    if (res.ok) {
      setShowQuickAdd(false);
      setNewRowData({
        id_estado_cumplimiento: estadosCumplimiento[0]?.id || '',
        id_tipo_modalidad: '',
        normas_vinculadas: [],
        norma_emisor: '',
        norma_nivel_jur: '',
        norma_sintesis: '',
        sintesis_categorias: '',
        url_norma: ''
      });
      fetchItems();
    } else {
      alert("Error al guardar el ítem.");
    }
    setIsSavingRow(false);
  };

  const handleUploadEvidencia = async () => {
    if (!evidenciaFile || !itemEvidencia) return;
    setIsUploading(true);
    const token = localStorage.getItem("sgml_token");
    const formData = new FormData();
    formData.append("archivo", evidenciaFile);
    formData.append("id_item_matriz", itemEvidencia.id_item_matriz);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/upload_evidencia.php`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
      });
      await recargarItemEvidencia();
      await fetchItems();
      setEvidenciaFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      console.error(err);
      alert("Error al subir el archivo.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleBorrarEvidencia = async (id_doc: number) => {
    const token = localStorage.getItem("sgml_token");
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/delete_evidencia.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ id_documentacion: id_doc })
      });
      await recargarItemEvidencia();
      await fetchItems();
    } catch (err) {
      console.error(err);
      alert("Error al eliminar el archivo.");
    }
  };

  const recargarItemEvidencia = async () => {
    if (!itemEvidencia) return;
    const token = localStorage.getItem("sgml_token");
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/leer_items.php?id_matriz=${idMatriz}`, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    const data = await res.json();
    const itemActualizado = data.registros?.find((i: any) => i.id_item_matriz === itemEvidencia.id_item_matriz);
    if (itemActualizado) {
      setItemEvidencia(itemActualizado);
    }
  };

  const handleDragEndItems = async (e: any) => {
    const { active, over } = e;
    if (over && active.id !== over.id) {
      const oldIndex = items.findIndex(i => i.id_item_matriz === active.id);
      const newIndex = items.findIndex(i => i.id_item_matriz === over.id);
      const newItems = arrayMove(items, oldIndex, newIndex);
      const itemsConNuevoOrden = newItems.map((item, idx) => ({ ...item, orden: idx }));
      setItems(itemsConNuevoOrden);
      const token = localStorage.getItem("sgml_token");
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/reordenar_items.php`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
          body: JSON.stringify(itemsConNuevoOrden.map((it, idx) => ({ id_item: it.id_item_matriz, orden: idx })))
        });
        if (!res.ok) throw new Error("Error al reordenar en el servidor");
        await fetchItems();
      } catch (err) {
        console.error("Error al reordenar:", err);
        setItems(items);
      }
    }
  };

  const handleSortByJurisdiccion = () => {
    if (!confirm("¿Desea reordenar todos los ítems por Nivel Jurisdiccional (Nacional > Provincial > Municipal)? Esto modificará el orden actual de manera permanente.")) return;
    
    const getJurStr = (item: any) => {
       if (item.normas_vinculadas && item.normas_vinculadas.length > 0) {
          let nivel = item.normas_vinculadas[0].nivel_jurisdiccion_desc || item.normas_vinculadas[0].jurisdiccion_desc || "";
          nivel = nivel.toLowerCase();
          if (nivel.includes('nacional')) return "1_" + nivel;
          if (nivel.includes('provincial')) return "2_" + nivel;
          if (nivel.includes('municipal')) return "3_" + nivel;
          return "4_" + nivel;
       }
       return "5_sin_norma";
    };

    const sortedItems = [...items].sort((a, b) => getJurStr(a).localeCompare(getJurStr(b)));
    const itemsConOrden = sortedItems.map((it, idx) => ({ ...it, orden: idx }));
    setItems(itemsConOrden);
    
    const token = localStorage.getItem("sgml_token");
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/reordenar_items.php`, { 
       method: "POST", 
       headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }, 
       body: JSON.stringify(itemsConOrden.map((it, idx) => ({ id_item: it.id_item_matriz, orden: idx }))) 
    }).catch(err => console.error("Error al ordenar por jurisdicción:", err));
  };

  const autocompletarCampos = (norma: any) => {
    if (!norma) {
      setNewRowData((prev: any) => ({
        ...prev,
        norma_emisor: '',
        norma_nivel_jur: '',
        norma_sintesis: '',
        sintesis_categorias: '',
        url_norma: ''
      }));
      return;
    }
    setNewRowData((prev: any) => ({
      ...prev,
      norma_emisor: norma.emisor_desc || '',
      norma_nivel_jur: norma.nivel_jurisdiccion_desc || norma.jurisdiccion_desc || '',
      sintesis_categorias: norma.sintesis || '',
      url_norma: norma.url_norma || '',
    }));
  };

  // Función para abrir el modal de nueva norma
  const abrirNuevaNormaModal = (itemParaEditar: any = null) => {
    setItemEnEdicion(itemParaEditar);
    setNuevaNormaForm({
      id_tipo_norma: "",
      numero: "",
      anio: new Date().getFullYear(),
      id_emisor_norma: "",
      sintesis: "",
      url_norma: "",
      id_estado_norma: "1",
      origen_carga: "Manual",
      fecha_publicacion: ""
    });
    setShowNuevaNormaModal(true);
  };

  // Función para guardar la nueva norma
  const handleGuardarNuevaNorma = async () => {
    if (!nuevaNormaForm.id_tipo_norma || !nuevaNormaForm.numero || !nuevaNormaForm.anio || !nuevaNormaForm.id_emisor_norma) {
      alert("Complete los campos obligatorios: Tipo, Número, Año y Emisor.");
      return;
    }
    setCargandoNuevaNorma(true);
    const token = localStorage.getItem("sgml_token");
    try {
      // 1. Guardar la norma
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/normativa/guardar.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(nuevaNormaForm)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.mensaje || "Error al guardar la norma.");

      // 2. Obtener la norma recién creada (con todos sus datos)
      const resGet = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/normativa/leer.php?id_norma=${data.id_norma}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const dataGet = await resGet.json();
      const normaCreada = dataGet.registros?.[0];
      if (!normaCreada) throw new Error("No se pudo recuperar la norma creada.");

      // 3. Construir el objeto de norma para el item
      const nuevaNormaParaItem = {
        id_norma: normaCreada.id_norma,
        tipo_norma: normaCreada.tipo_norma_desc,
        numero: normaCreada.numero,
        anio: normaCreada.anio,
        emisor_desc: normaCreada.emisor_desc,
        nivel_jurisdiccion_desc: normaCreada.nivel_jurisdiccion_desc,
        jurisdiccion_desc: normaCreada.jurisdiccion_desc,
        sintesis: normaCreada.sintesis,
        categorias: normaCreada.categorias,
        url_norma: normaCreada.url_norma
      };

      if (itemEnEdicion) {
        // === MODO EDICIÓN DE ÍTEM ===
        const normasActualizadas = [...(itemEnEdicion.normas_vinculadas || []), nuevaNormaParaItem];
        // Actualizar estado local
        const nuevosItems = items.map(i => 
          i.id_item_matriz === itemEnEdicion.id_item_matriz 
            ? { ...i, normas_vinculadas: normasActualizadas }
            : i
        );
        setItems(nuevosItems);
        // Actualizar backend
        await handleUpdateExistingRow(itemEnEdicion.id_item_matriz, 'normas_vinculadas', normasActualizadas);
        setItemEnEdicion(null);
      } else {
        // === MODO NUEVA FILA ===
        setNewRowData((prev: any) => ({
          ...prev,
          normas_vinculadas: [...prev.normas_vinculadas, nuevaNormaParaItem]
        }));
        autocompletarCampos(nuevaNormaParaItem);
      }

      setShowNuevaNormaModal(false);
      alert("Norma creada y agregada correctamente.");

    } catch (error: any) {
      alert("Error: " + error.message);
    } finally {
      setCargandoNuevaNorma(false);
    }
  };

  const renderQuickAddCell = (colId: string) => {
    switch(colId) {
      case 'estado':
        return <select className="w-full text-[11px] p-2.5 border border-lgc-primary rounded-lg outline-none bg-white focus:ring-2 focus:ring-lgc-primary" value={newRowData.id_estado_cumplimiento} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setNewRowData({...newRowData, id_estado_cumplimiento: e.target.value})}>{estadosCumplimiento.map((e: any) => <option key={e.id} value={e.id}>{e.descripcion}</option>)}</select>;
      case 'id_tipo_modalidad':
        return <select className="w-full text-[11px] p-2.5 border border-lgc-primary rounded-lg outline-none bg-white focus:ring-2 focus:ring-lgc-primary" value={newRowData.id_tipo_modalidad || ''} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setNewRowData({...newRowData, id_tipo_modalidad: e.target.value})}><option value="">Sin Asignar</option>{tiposModalidad.map((t: any) => <option key={t.id} value={t.id}>{t.descripcion}</option>)}</select>;
      case 'normas':
        return <InlineNormSelectorConAutocompletado
          selectedNormas={newRowData.normas_vinculadas}
          onChange={(normas: any) => setNewRowData({...newRowData, normas_vinculadas: normas})}
          onAutocompletar={autocompletarCampos}
          idEstablecimiento={idEstablecimiento}
          onSolicitarNuevaNorma={abrirNuevaNormaModal}
        />;
      case 'id_responsable_establecimiento':
        return <select className="w-full text-[11px] p-2.5 border border-lgc-primary rounded-lg outline-none bg-white focus:ring-2 focus:ring-lgc-primary" value={newRowData.id_responsable_establecimiento || ''} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setNewRowData({...newRowData, id_responsable_establecimiento: e.target.value})}><option value="">Sin Asignar</option>{responsables.map((r: any) => <option key={r.id_responsable_establecimiento} value={r.id_responsable_establecimiento}>{r.descripcion}</option>)}</select>;
      case 'adjuntos':
        return <div className="text-[10px] text-slate-400 italic p-2.5 bg-slate-50 rounded-lg border border-dashed text-center">Guardar ítem primero</div>;
      case 'norma_emisor':
        return <input ref={firstInputRef} type="text" className="w-full text-[11px] p-2.5 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 cursor-not-allowed" value={newRowData.norma_emisor || ''} readOnly disabled />;
      case 'norma_nivel_jur':
        return <input type="text" className="w-full text-[11px] p-2.5 bg-slate-100 border border-slate-200 rounded-lg text-slate-500 cursor-not-allowed" value={newRowData.norma_nivel_jur || ''} readOnly disabled />;
      case 'norma_sintesis':
        return (
          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200">
            <p className="text-[11px] text-slate-600 line-clamp-3">{newRowData.sintesis_categorias || 'Seleccione una norma para ver la síntesis.'}</p>
            {newRowData.url_norma && (
              <a href={newRowData.url_norma} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 mt-2 text-[10px] text-lgc-accent font-bold hover:underline">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                Ver Original
              </a>
            )}
          </div>
        );
      case 'vencimiento_plazo':
      case 'fecha_cumplimiento':
        return <input type="date" className="w-full text-[11px] p-2.5 border border-lgc-primary rounded-lg outline-none bg-white focus:ring-2 focus:ring-lgc-primary" value={newRowData[colId] || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewRowData({...newRowData, [colId]: e.target.value})} />;
      default:
        return <input type="text" className="w-full text-[11px] p-2.5 border border-lgc-primary rounded-lg outline-none bg-white focus:ring-2 focus:ring-lgc-primary" value={newRowData[colId] || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewRowData({...newRowData, [colId]: e.target.value})} placeholder="Completar..." />;
    }
  };

  if (loading) return <div className="py-20 flex flex-col items-center justify-center text-lgc-primary font-bold tracking-widest uppercase"><div className="w-10 h-10 border-4 border-lgc-primary border-t-transparent rounded-full animate-spin mb-4"></div>Preparando Workspace...</div>;

  const COLS_CUMPLIMIENTO_IDS = ['evidencia_cumplimiento', 'id_responsable_establecimiento', 'verificacion_cumplimiento', 'estado', 'vencimiento_plazo', 'fecha_cumplimiento', 'obs_estado_cumplimiento', 'adjuntos'];
  const puedeEditarCampo = (colId: string): boolean => {
    if (estadoMatriz === 3) return false;                            
    if (estadoMatriz === 1) return true;                             
    return COLS_CUMPLIMIENTO_IDS.includes(colId) || colId.startsWith('custom_');
  };
  const puedeAgregarFilas = estadoMatriz === 1;
  const puedeConfigurar = estadoMatriz === 1;
  const puedeReordenar = estadoMatriz === 1;

  if (showConfig) {
    const COLUMNAS_BASE = tipoMatriz === 1 ? COLUMNAS_REGULATORIAS : COLUMNAS_CUMPLIMIENTO;
    const columnasDisponibles = COLUMNAS_BASE.filter(c => !tempConfig.find(tc => tc.id === c.id));
    return (
      <div className="bg-white p-8 rounded-2xl shadow-lg border border-slate-200 max-w-5xl mx-auto mt-6 animate-fade-in">
        <h2 className="text-2xl font-heading text-lgc-primary uppercase tracking-tight mb-2">Estructura Visual de la Matriz</h2>
        <p className="text-sm text-slate-500 mb-8">Administrá qué campos conforman las tarjetas de cada ítem.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200">
            <h3 className="text-[10px] font-bold uppercase text-slate-500 tracking-widest mb-4">Campos Disponibles</h3>
            <div className="flex flex-col gap-2 max-h-100 overflow-y-auto custom-scrollbar pr-2">
              {columnasDisponibles.map((col: any) => (
                <button key={col.id} onClick={() => setTempConfig([...tempConfig, col])} className="w-full text-left p-3 bg-white border border-slate-200 rounded-xl hover:border-lgc-primary transition-all text-[11px] font-bold uppercase text-slate-600 shadow-sm flex justify-between group">{col.label} <span className="text-slate-300 group-hover:text-lgc-primary transition-colors">+</span></button>
              ))}
            </div>
            <div className="mt-6 border-t border-slate-200 pt-5">
              <h4 className="text-[9px] font-bold uppercase text-slate-400 mb-3">Crear Columna Libre (Personalizada)</h4>
              <div className="flex gap-2">
                 <input type="text" className="flex-1 p-2.5 text-xs border border-slate-200 rounded-xl outline-none focus:border-lgc-primary" placeholder="Nombre de la columna..." value={nuevaColumna} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNuevaColumna(e.target.value)} />
                 <button onClick={agregarColumnaCustom} className="bg-lgc-accent hover:bg-[#D97920] text-white px-5 rounded-xl text-xs font-bold shadow-md transition-colors">Crear</button>
              </div>
            </div>
          </div>

          <div className="bg-orange-50/50 p-5 rounded-2xl border border-orange-100">
            <h3 className="text-[10px] font-bold uppercase text-orange-600 tracking-widest mb-4">Columnas Visibles (Arrastrar para ordenar)</h3>
            <div className="flex flex-col max-h-125 overflow-y-auto custom-scrollbar pr-2">
              <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(e: any) => { const { active, over } = e; if (over && active.id !== over.id) { const oldI = tempConfig.findIndex((c: any) => c.id === active.id); const newI = tempConfig.findIndex((c: any) => c.id === over.id); setTempConfig(arrayMove(tempConfig, oldI, newI)); } }}>
                <SortableContext items={tempConfig.map((c: any) => c.id)} strategy={verticalListSortingStrategy}>
                  {tempConfig.map((col: any) => <SortableConfigItem key={col.id} col={col} onRemove={(id: string) => setTempConfig(tempConfig.filter((c: any) => c.id !== id))} />)}
                </SortableContext>
              </DndContext>
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-4"><button onClick={() => { setTempConfig(configColumnas || []); setShowConfig(false); }} className="px-6 py-3 text-xs uppercase font-bold text-slate-500 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors">Cancelar</button><button onClick={guardarConfiguracion} className="px-8 py-3 bg-lgc-primary text-white font-bold rounded-xl uppercase text-xs shadow-lg hover:bg-[#006A8A] transition-colors">Guardar Estructura</button></div>
      </div>
    );
  }
  const colsRegulatorias = configColumnas.filter(c => !c.custom && ['resumen_legal', 'articulos_aplicables', 'interpretacion_aplicacion', 'id_tipo_modalidad', 'obs_modalidad'].includes(c.id));
  const colsCumplimiento = configColumnas.filter(c => !c.custom && ['evidencia_cumplimiento', 'id_responsable_establecimiento', 'verificacion_cumplimiento', 'estado', 'vencimiento_plazo', 'fecha_cumplimiento', 'obs_estado_cumplimiento', 'adjuntos'].includes(c.id));
  const colsCustom = configColumnas.filter(c => c.custom);

  return (
    <div className="space-y-4 animate-fade-in flex flex-col h-[calc(100vh-100px)]">
      
      {/* HEADER DINÁMICO */}
      <div className="bg-[#005F78] px-6 py-4 rounded-xl shadow-md flex justify-between items-center shrink-0 border border-[#004D62]">
        <div className="flex items-center gap-5">
          <Link href="/dashboard/matrices" className="text-white/80 hover:text-white transition-colors bg-white/10 hover:bg-white/20 p-2.5 rounded-xl border border-white/20 shadow-inner">
             <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" /></svg>
          </Link>
          
          {headerInfo?.logo_path ? (
            <div className="bg-white p-1.5 rounded-lg shadow-sm">
              <img src={`${process.env.NEXT_PUBLIC_IMG_URL}/${headerInfo.logo_path}`} alt="Cliente Logo" className="h-10 w-auto object-contain" />
            </div>
          ) : (
            <div className="h-12 w-12 bg-white/20 rounded-lg flex items-center justify-center text-white font-bold text-xl uppercase border border-white/30 shrink-0 shadow-sm">
              {headerInfo?.nombre_fantasia?.substring(0, 2) || 'M'}
            </div>
          )}
          
          <div className="flex flex-col">
            <h1 className="text-xl font-heading text-white uppercase tracking-tight flex items-center gap-3">
              {headerInfo?.nombre_fantasia || 'WORKSPACE MATRIZ'}
              <span className="bg-white/20 text-white px-3 py-1 rounded-md text-[11px] tracking-widest font-bold shadow-inner border border-white/30"># {idMatriz}</span>
              <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold tracking-widest uppercase shadow-inner border flex items-center gap-1.5 ${
                estadoMatriz === 2 ? 'bg-emerald-900/60 text-emerald-200 border-emerald-700' :
                estadoMatriz === 3 ? 'bg-slate-700/60 text-slate-300 border-slate-600' :
                'bg-amber-500/30 text-amber-200 border-amber-500/50'
              }`}>
                {estadoMatriz === 3 && <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>}
                {estadoMatriz === 1 ? 'Borrador' : estadoMatriz === 2 ? 'Publicada' : 'Archivada'}
              </span>
            </h1>
            <p className="text-white/80 text-[10px] font-bold tracking-widest uppercase mt-0.5 flex items-center gap-2">
              <span className="truncate max-w-50" title={headerInfo?.establecimiento_desc}>{headerInfo?.establecimiento_desc || 'Sede Principal'}</span>
              <span>•</span>
              <span>{headerInfo?.especialidad_matriz_desc || 'Especialidad'}</span>
              <span>•</span>
              <span>Tipo: {headerInfo?.tipo_matriz_desc || 'Regulatoria'}</span>
              <span>•</span>
              <span>V{headerInfo?.version || 1}.0</span>
              {estadoMatriz === 3 && <><span>•</span><span className="text-white">SOLO LECTURA</span></>}
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          {canEdit("matriz") && puedeConfigurar && (
            <button onClick={() => setShowConfig(true)} className="bg-white/10 hover:bg-white/20 text-white font-bold py-2 px-4 rounded-xl transition-all text-[10px] uppercase tracking-widest border border-white/20 shadow-sm flex items-center gap-2">
               <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>
               Configurar
            </button>
          )}
          <Link href={`/dashboard/matrices/${idMatriz}/preview`} className="bg-white/10 hover:bg-white/20 text-white font-bold py-2 px-4 rounded-xl transition-all text-[10px] uppercase tracking-widest border border-white/20 flex items-center gap-2 shadow-sm">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
            Vista Previa
          </Link>
        </div>
      </div>

      <div ref={mainContainerRef} className="flex-1 overflow-auto custom-scrollbar pb-10 px-1 relative">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 mb-4 transition-all overflow-hidden relative z-20">
          <button
            onClick={() => setIsDashboardOpen(!isDashboardOpen)}
            className="w-full flex items-center justify-between p-4 bg-slate-50 hover:bg-slate-100 transition-colors border-b border-transparent"
          >
            <div className="flex items-center gap-3">
              <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
              <span className="font-bold uppercase text-xs tracking-widest text-slate-600">Resumen y Métricas de la Matriz</span>
              <span className="bg-slate-200 text-slate-500 px-2 py-0.5 rounded text-[10px] font-bold">{items.length} ítems · {dashboardMetrics.totalNormas} normas</span>
            </div>
            <svg className={`w-5 h-5 text-slate-400 transform transition-transform ${isDashboardOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
          </button>

          {isDashboardOpen && (
            <div className="p-5 border-t border-slate-200 bg-white space-y-6">
              <div className={`grid gap-5 ${tipoMatriz === 2 ? 'grid-cols-1 md:grid-cols-3' : 'grid-cols-1 md:grid-cols-2'}`}>
                <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 flex flex-col gap-1">
                  <span className="text-[10px] font-bold uppercase text-slate-400 tracking-widest">Total Normativas</span>
                  <span className="text-3xl font-heading text-lgc-primary">{dashboardMetrics.totalNormas}</span>
                  <span className="text-[10px] text-slate-400">normas únicas vinculadas a la matriz</span>
                </div>
                <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 flex flex-col gap-3">
                  <span className="text-[10px] font-bold uppercase text-slate-400 tracking-widest">Normas por Jurisdicción</span>
                  {dashboardMetrics.porJurisdiccion.length === 0 ? (
                    <span className="text-[11px] text-slate-400 italic">Sin datos de jurisdicción</span>
                  ) : (
                    <div className="flex flex-col gap-2">
                      {dashboardMetrics.porJurisdiccion.map((jur: any) => {
                        const total = dashboardMetrics.totalNormas;
                        const pct = total > 0 ? Math.round((jur.cantidad / total) * 100) : 0;
                        return (
                          <div key={jur.nombre} className="flex flex-col gap-1">
                            <div className="flex justify-between items-center">
                              <span className="text-[10px] font-bold text-slate-600 truncate max-w-[60%]" title={jur.nombre}>{jur.nombre}</span>
                              <span className="text-[10px] font-bold text-slate-500">{jur.cantidad} <span className="text-slate-300 font-normal">({pct}%)</span></span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                              <div className="bg-lgc-primary h-1.5 rounded-full transition-all" style={{ width: `${Math.min(pct, 100)}%` }}></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
                {tipoMatriz === 2 && (
                  <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 flex flex-col gap-3">
                    <span className="text-[10px] font-bold uppercase text-slate-400 tracking-widest">Estado de Cumplimiento</span>
                    {dashboardMetrics.porCumplimiento.length === 0 ? (
                      <span className="text-[11px] text-slate-400 italic">Sin datos</span>
                    ) : (
                      <>
                        <div className="flex items-center gap-4">
                          <div className="shrink-0">
                            {(() => {
                              const size = 80;
                              const r = 30;
                              const cx = size / 2;
                              const cy = size / 2;
                              const circ = 2 * Math.PI * r;
                              let cumOffset = 0;
                              const total = dashboardMetrics.totalCumplimiento;
                              return (
                                <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
                                  {dashboardMetrics.porCumplimiento.map((seg: any, i: number) => {
                                    const pct = seg.cantidad / total;
                                    const dash = pct * circ;
                                    const gap = circ - dash;
                                    const offset = circ - cumOffset;
                                    cumOffset += dash;
                                    return (
                                      <circle
                                        key={i}
                                        r={r} cx={cx} cy={cy}
                                        fill="none"
                                        stroke={seg.color}
                                        strokeWidth="14"
                                        strokeDasharray={`${dash} ${gap}`}
                                        strokeDashoffset={offset}
                                        style={{ transform: 'rotate(-90deg)', transformOrigin: 'center' }}
                                      />
                                    );
                                  })}
                                  <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle" fontSize="11" fontWeight="bold" fill="#334155">{total}</text>
                                  <text x={cx} y={cy + 12} textAnchor="middle" dominantBaseline="middle" fontSize="5.5" fill="#94a3b8">ítems</text>
                                </svg>
                              );
                            })()}
                          </div>
                          <div className="flex flex-col gap-1.5 flex-1 min-w-0">
                            {dashboardMetrics.porCumplimiento.map((seg: any) => {
                              const pct = dashboardMetrics.totalCumplimiento > 0
                                ? Math.round((seg.cantidad / dashboardMetrics.totalCumplimiento) * 100)
                                : 0;
                              return (
                                <div key={seg.label} className="flex items-center gap-2">
                                  <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: seg.color }}></div>
                                  <span className="text-[10px] text-slate-600 font-bold truncate flex-1" title={seg.label}>{seg.label}</span>
                                  <span className="text-[10px] font-bold text-slate-500 shrink-0">{seg.cantidad} <span className="text-slate-300 font-normal">({pct}%)</span></span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                        {(() => {
                          const cumple = dashboardMetrics.porCumplimiento.find((s: any) =>
                            s.label.toLowerCase().includes('cumple') && !s.label.toLowerCase().includes('no') && !s.label.toLowerCase().includes('parcial')
                          );
                          if (!cumple) return null;
                          const pct = dashboardMetrics.totalCumplimiento > 0
                            ? Math.round((cumple.cantidad / dashboardMetrics.totalCumplimiento) * 100)
                            : 0;
                          const colorClass = pct >= 80 ? 'text-emerald-600 bg-emerald-50 border-emerald-200' : pct >= 50 ? 'text-amber-600 bg-amber-50 border-amber-200' : 'text-red-600 bg-red-50 border-red-200';
                          return (
                            <div className={`mt-1 rounded-lg border px-3 py-2 flex items-center gap-2 ${colorClass}`}>
                              <svg className="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                              <span className="text-[11px] font-bold uppercase tracking-widest">Cumplimiento: {pct}%</span>
                            </div>
                          );
                        })()}
                      </>
                    )}
                  </div>
                )}
              </div>

              {dashboardMetrics.rankingCategorias.length > 0 && (
                <div>
                  <h3 className="text-[10px] font-bold uppercase text-slate-400 tracking-widest mb-3 border-b border-slate-100 pb-1.5">Ranking de Categorías incluidas en las Normas</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {dashboardMetrics.rankingCategorias.map((cat: any, idx: number) => {
                      const max = dashboardMetrics.rankingCategorias[0].cantidad;
                      const pct = max > 0 ? Math.round((cat.cantidad / max) * 100) : 0;
                      return (
                        <div key={cat.nombre} className="flex items-center gap-3 bg-slate-50 rounded-lg px-3 py-2 border border-slate-200">
                          <span className="text-[10px] font-bold text-slate-400 w-4 shrink-0 text-right">{idx + 1}</span>
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-[11px] font-bold text-slate-700 truncate" title={cat.nombre}>{cat.nombre}</span>
                              <span className="text-[10px] font-bold text-lgc-primary shrink-0 ml-2">{cat.cantidad}</span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-1">
                              <div className="bg-lgc-primary/60 h-1 rounded-full" style={{ width: `${pct}%` }}></div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 mb-4 transition-all overflow-hidden relative z-20">
           <button onClick={() => setIsFilterOpen(!isFilterOpen)} className="w-full flex items-center justify-between p-4 bg-slate-50 hover:bg-slate-100 transition-colors border-b border-transparent">
              <div className="flex items-center gap-3">
                 <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
                 <span className="font-bold uppercase text-xs tracking-widest text-slate-600">Búsqueda y Filtros Avanzados</span>
                 {hasActiveFilters && <span className="bg-lgc-accent text-white px-2 py-0.5 rounded text-[10px] font-bold uppercase shadow-sm">Activo</span>}
              </div>
              <svg className={`w-5 h-5 text-slate-400 transform transition-transform ${isFilterOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
           </button>
           
           {isFilterOpen && (
              <div className="p-5 border-t border-slate-200 bg-white space-y-6">
                  <div>
                    <h3 className="text-[10px] font-bold uppercase text-blue-600 tracking-widest mb-3 border-b border-blue-100 pb-1">Sección Normativa</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <select className="text-[11px] p-2 border border-slate-200 rounded outline-none bg-white cursor-pointer" value={filtros.norma.tipo} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFiltros({...filtros, norma: {...filtros.norma, tipo: e.target.value}})}>
                         <option value="">Tipo (Todos)</option>
                         {tiposNorma.map((t: any) => <option key={t.id} value={t.descripcion}>{t.descripcion}</option>)}
                      </select>
                      <input type="text" placeholder="Año (4 dígitos)" maxLength={4} onInput={(e: React.FormEvent<HTMLInputElement>) => { e.currentTarget.value = e.currentTarget.value.replace(/\D/g, ''); }} className="text-[11px] p-2 border border-slate-200 rounded outline-none" value={filtros.norma.anio} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFiltros({...filtros, norma: {...filtros.norma, anio: e.target.value}})} />
                      <input type="text" placeholder="Nro" className="text-[11px] p-2 border border-slate-200 rounded outline-none" value={filtros.norma.nro} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFiltros({...filtros, norma: {...filtros.norma, nro: e.target.value}})} />
                      <select className="text-[11px] p-2 border border-slate-200 rounded outline-none bg-white cursor-pointer" value={filtros.norma.emisor} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFiltros({...filtros, norma: {...filtros.norma, emisor: e.target.value}})}>
                         <option value="">Emisor (Todos)</option>
                         {emisoresNorma.map((e: any) => <option key={e.id} value={e.descripcion}>{e.descripcion}</option>)}
                      </select>
                      <select className="text-[11px] p-2 border border-slate-200 rounded outline-none bg-white cursor-pointer" value={filtros.norma.nivel} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFiltros({...filtros, norma: {...filtros.norma, nivel: e.target.value}})}>
                         <option value="">Nivel Jurisd. (Todos)</option>
                         {nivelesDisponibles.map((n: any) => <option key={n.id} value={n.descripcion}>{n.descripcion}</option>)}
                      </select>
                      <select className="text-[11px] p-2 border border-slate-200 rounded outline-none bg-white cursor-pointer" value={filtros.norma.jurisdiccion} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFiltros({...filtros, norma: {...filtros.norma, jurisdiccion: e.target.value}})}>
                         <option value="">Jurisdicción (Todas)</option>
                         {jurisdiccionesDisponibles.map((j: any) => <option key={j.id} value={j.descripcion}>{j.descripcion}</option>)}
                      </select>
                      <div className="col-span-2">
                        <input type="text" placeholder="Buscar por síntesis..." className="w-full text-[11px] p-2 border border-slate-200 rounded outline-none" value={filtros.norma.sintesis} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFiltros({...filtros, norma: {...filtros.norma, sintesis: e.target.value}})} />
                      </div>
                      <div className="col-span-2 md:col-span-4">
                         <MultiSelectTags options={categoriasGlobales} selected={filtros.norma.categorias} onChange={(arr: any) => setFiltros({...filtros, norma: {...filtros.norma, categorias: arr}})} placeholder="Filtrar por categorías (agrega varias)..." />
                      </div>
                    </div>
                  </div>

                  {colsRegulatorias.length > 0 && (
                    <div>
                      <h3 className="text-[10px] font-bold uppercase text-orange-600 tracking-widest mb-3 border-b border-orange-100 pb-1">Sección Regulatoria</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {colsRegulatorias.map((c: any) => {
                           if (c.id === 'id_tipo_modalidad') {
                              return (
                                <select key={c.id} className="text-[11px] p-2 border border-slate-200 rounded outline-none cursor-pointer bg-white" value={filtros.dinamicos[c.id] || ''} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFiltros({...filtros, dinamicos: {...filtros.dinamicos, [c.id]: e.target.value}})}>
                                   <option value="">Modalidad (Todas)</option>
                                   {tiposModalidad.map((t: any) => <option key={t.id} value={t.id}>{t.descripcion}</option>)}
                                </select>
                              );
                           }
                           return <input key={c.id} type="text" placeholder={`${c.label}...`} className="text-[11px] p-2 border border-slate-200 rounded outline-none" value={filtros.dinamicos[c.id] || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFiltros({...filtros, dinamicos: {...filtros.dinamicos, [c.id]: e.target.value}})} />;
                        })}
                      </div>
                    </div>
                  )}

                  {colsCumplimiento.length > 0 && (
                    <div>
                      <h3 className="text-[10px] font-bold uppercase text-emerald-600 tracking-widest mb-3 border-b border-emerald-100 pb-1">Sección De Cumplimiento</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <select className="text-[11px] p-2 border border-slate-200 rounded outline-none font-bold text-slate-600 cursor-pointer bg-white" value={filtros.evidencia} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFiltros({...filtros, evidencia: e.target.value})}>
                           <option value="">Evidencia (Todas)</option>
                           <option value="con">Con Evidencia Cargada</option>
                           <option value="sin">Sin Evidencia</option>
                        </select>
                        {colsCumplimiento.map((c: any) => {
                           if (c.id === 'estado') {
                              return (
                                <select key={c.id} className="text-[11px] p-2 border border-slate-200 rounded outline-none cursor-pointer bg-white" value={filtros.dinamicos[c.id] || ''} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFiltros({...filtros, dinamicos: {...filtros.dinamicos, [c.id]: e.target.value}})}>
                                   <option value="">Estado (Todos)</option>
                                   {estadosCumplimiento.map((e: any) => <option key={e.id} value={e.id}>{e.descripcion}</option>)}
                                </select>
                              );
                           }
                           if (c.id === 'id_responsable_establecimiento') {
                              return (
                                <select key={c.id} className="text-[11px] p-2 border border-slate-200 rounded outline-none cursor-pointer bg-white" value={filtros.dinamicos[c.id] || ''} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFiltros({...filtros, dinamicos: {...filtros.dinamicos, [c.id]: e.target.value}})}>
                                   <option value="">Responsable (Todos)</option>
                                   {responsables.map((r: any) => <option key={r.id_responsable_establecimiento} value={r.id_responsable_establecimiento}>{r.descripcion}</option>)}
                                </select>
                              );
                           }
                           if (c.id === 'vencimiento_plazo' || c.id === 'fecha_cumplimiento') {
                              return <input key={c.id} type="date" title={c.label} className="text-[11px] p-2 border border-slate-200 rounded outline-none text-slate-500 font-bold uppercase cursor-pointer" value={filtros.dinamicos[c.id] || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFiltros({...filtros, dinamicos: {...filtros.dinamicos, [c.id]: e.target.value}})} />;
                           }
                           if (c.id === 'adjuntos') return null; 
                           return <input key={c.id} type="text" placeholder={`${c.label}...`} className="text-[11px] p-2 border border-slate-200 rounded outline-none" value={filtros.dinamicos[c.id] || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFiltros({...filtros, dinamicos: {...filtros.dinamicos, [c.id]: e.target.value}})} />;
                        })}
                      </div>
                    </div>
                  )}

                  {colsCustom.length > 0 && (
                    <div>
                      <h3 className="text-[10px] font-bold uppercase text-purple-600 tracking-widest mb-3 border-b border-purple-100 pb-1">Columnas Personalizadas</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {colsCustom.map((c: any) => (
                           <input key={c.id} type="text" placeholder={`${c.label}...`} className="text-[11px] p-2 border border-purple-200 bg-purple-50/30 rounded outline-none focus:border-purple-400" value={filtros.dinamicos[c.id] || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFiltros({...filtros, dinamicos: {...filtros.dinamicos, [c.id]: e.target.value}})} />
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end pt-2">
                     <button onClick={() => setFiltros({ norma: { tipo: '', nro: '', anio: '', sintesis: '', emisor: '', nivel: '', jurisdiccion: '', categorias: [] }, evidencia: '', dinamicos: {} })} className="text-[10px] font-bold uppercase tracking-widest text-slate-400 hover:text-slate-600 px-4 py-2 bg-slate-100 rounded border border-slate-200 transition-colors">
                        Limpiar Filtros
                     </button>
                  </div>
              </div>
           )}
        </div>

        <div className="bg-[#005F78] px-5 py-3 rounded-xl shadow-sm mb-4 flex justify-between items-center sticky top-0 z-30">
           <div className="flex items-center gap-3">
              <svg className="w-5 h-5 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>
              <span className="text-xs font-bold text-white uppercase tracking-widest">
                 Ítems Registrados ({itemsFiltrados.length})
              </span>
           </div>
           
           <div className="flex gap-4 items-center">
              {hasActiveFilters && (
                <span className="text-[9px] text-orange-200 font-bold uppercase tracking-widest border border-orange-200/30 px-2 py-1 rounded bg-orange-900/20">
                  Ordenamiento Bloqueado (Filtro Activo)
                </span>
              )}
              
              {!hasActiveFilters && canEdit("matriz") && (
                <button 
                  onClick={handleSortByJurisdiccion} 
                  title="Ordenar filas por Nivel Jurisdiccional (Nacional > Provincial > Municipal)"
                  className="text-[10px] text-white bg-white/10 hover:bg-white/20 px-4 py-1.5 rounded-lg border border-white/20 transition-all font-bold uppercase tracking-widest flex items-center gap-2 shadow-inner"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9M3 12h5m0 0l-5-5m5 5v12" /></svg>
                  Ordenar Jur.
                </button>
              )}

              <button 
                onClick={() => setExpandAll(!expandAll)} 
                className="text-[10px] text-white bg-white/10 hover:bg-white/20 px-4 py-1.5 rounded-lg border border-white/20 transition-all font-bold uppercase tracking-widest flex items-center gap-2 shadow-inner"
              >
                <svg 
                  className="w-4 h-4" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  {expandAll ? (
                    // Icono "Contraer" (flechas hacia adentro)
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M9 9L3.75 3.75M9 9v-4.5M9 9H4.5M15 15l5.25 5.25M15 15v4.5M15 15h4.5M9 15l-5.25 5.25M9 15v4.5M9 15H4.5M15 9l5.25-5.25M15 9v-4.5M15 9h4.5" 
                    />
                  ) : (
                    // Icono "Expandir" (flechas hacia afuera)
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M20.25 3.75v4.5m0-4.5h-4.5m4.5 0L15 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 20.25v-4.5m0 4.5h-4.5m4.5 0L15 15" 
                    />
                  )}
                </svg>
                {expandAll ? 'Contraer Todas' : 'Expandir Todas'}
              </button>
           </div>
        </div>

        {/* Botón "Nueva Fila" movido fuera del DndContext y dentro del flujo sticky */}
        {canEdit("matriz") && puedeAgregarFilas && (
          <div className="sticky top-14 z-40 mb-4">
            <button
              onClick={() => {
                setShowQuickAdd(true);
                setTimeout(() => {
                  if (quickAddFormRef.current && mainContainerRef.current) {
                    const container = mainContainerRef.current;
                    const element = quickAddFormRef.current;
                    const elementRect = element.getBoundingClientRect();
                    const containerRect = container.getBoundingClientRect();
                    container.scrollTop += elementRect.top - containerRect.top - 120;
                  }
                }, 100);
              }}
              className="w-full bg-[#e6f7f5] hover:bg-[#ccefec] text-[#005F78] font-bold py-3 rounded-xl transition-all text-[10px] uppercase tracking-widest flex items-center justify-center gap-2 border border-[#005F78]/20 shadow-sm"
            >
              + Nueva Fila
            </button>
          </div>
        )}

        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEndItems}>
          <div className="flex flex-col max-w-7xl mx-auto relative z-10">
            <div className="relative">
              {showQuickAdd && (
                <div ref={quickAddFormRef} className="bg-[#e6f7f5] rounded-2xl shadow-lg border border-[#005F78]/30 p-6 mb-6 animate-fade-in relative overflow-visible">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-[#005F78]/10 rounded-full blur-3xl"></div>
                  <div className="flex items-center justify-between mb-6 border-b border-[#005F78]/20 pb-3 relative z-10">
                    <div className="flex items-center gap-3">
                      <span className="bg-[#005F78] text-white w-8 h-8 rounded-full flex items-center justify-center shadow-md">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" /></svg>
                      </span>
                      <span className="text-sm font-bold text-[#005F78] uppercase tracking-widest">Crear Nueva Fila</span>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => setShowQuickAdd(false)} className="bg-white text-slate-500 px-4 py-2 rounded-lg border border-slate-200 text-xs font-bold uppercase shadow-sm hover:bg-slate-50 transition-colors">Cancelar</button>
                      <button onClick={handleSaveNewRow} disabled={isSavingRow} className="bg-[#005F78] hover:bg-[#004A5E] text-white px-6 py-2 rounded-lg shadow-md text-xs font-bold uppercase flex items-center gap-2 transition-colors disabled:opacity-50">
                        {isSavingRow ? 'Guardando...' : 'Guardar Ítem'}
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 relative z-10">
                    {configColumnas.map((col: any) => (
                      <div key={col.id} className="flex flex-col gap-1.5">
                        <label className="text-[10px] font-bold uppercase text-[#005F78] tracking-widest ml-1">{col.label}</label>
                        {renderQuickAddCell(col.id)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <SortableContext items={itemsFiltrados.map(i => i.id_item_matriz)} strategy={verticalListSortingStrategy}>
                {itemsFiltrados.length === 0 && !showQuickAdd ? (
                  <div className="p-16 text-center text-slate-400 bg-white rounded-2xl border border-slate-200 shadow-sm border-dashed">
                    <svg className="w-12 h-12 mb-3 text-slate-300 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                    <span className="font-bold uppercase tracking-widest text-[11px]">{hasActiveFilters ? 'No hay resultados para estos filtros.' : 'No hay filas en la matriz.'}</span>
                  </div>
                ) : (
                  itemsFiltrados.map(item => (
                    <SortableRow 
                      key={item.id_item_matriz} 
                      item={item} 
                      columnasVisibles={configColumnas} 
                      canEdit={canEdit("matriz") && estadoMatriz !== 3} 
                      canEditField={puedeEditarCampo}
                      onUpdate={handleUpdateExistingRow}
                      onDelete={handleDeleteItem}
                      onCopy={handleCopyItem}
                      estadosCumplimiento={estadosCumplimiento} 
                      responsables={responsables} 
                      tiposModalidad={tiposModalidad} 
                      onOpenEvidencia={setItemEvidencia} 
                      forceExpand={expandAll}
                      isDragDisabled={hasActiveFilters || !puedeReordenar}
                      onSolicitarNuevaNorma={abrirNuevaNormaModal}
                      idEstablecimiento={idEstablecimiento}
                    />
                  ))
                )}
              </SortableContext>
            </div>
          </div>
        </DndContext>

        {showScrollTop && (
          <button
            onClick={scrollToTop}
            className="fixed bottom-20 right-14 bg-lgc-primary text-white p-3 rounded-full shadow-lg hover:bg-[#006A8A] transition-all z-50"
            title="Ir arriba"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
          </button>
        )}
        {showScrollBottom && (
          <button
            onClick={scrollToBottom}
            className="fixed bottom-6 right-14 bg-lgc-primary text-white p-3 rounded-full shadow-lg hover:bg-[#006A8A] transition-all z-50"
            title="Ir abajo"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" /></svg>
          </button>
        )}
      </div>

      {itemEvidencia && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-lgc-primary uppercase mb-4 border-b border-slate-100 pb-3 flex items-center gap-3">
               <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
               Repositorio de Evidencias <span className="bg-slate-100 text-slate-500 px-2 py-0.5 rounded text-xs ml-2">Ítem #{itemEvidencia.id_item_matriz}</span>
            </h3>
            
            <div className="mb-6 bg-slate-50 p-5 rounded-xl border border-slate-200 border-dashed">
               <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-3">Subir nuevo documento probatorio</label>
               <div className="flex gap-3 items-center">
                  <input ref={fileInputRef} type="file" className="flex-1 text-xs file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-lgc-primary/10 file:text-lgc-primary hover:file:bg-lgc-primary/20 transition-all cursor-pointer" onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEvidenciaFile(e.target.files?.[0] || null)} />
                  <button onClick={handleUploadEvidencia} disabled={!evidenciaFile || isUploading} className="bg-lgc-accent hover:bg-[#D97920] text-white px-6 py-2.5 text-xs font-bold rounded-lg shadow-md disabled:opacity-50 transition-colors uppercase tracking-widest flex items-center gap-2">
                     {isUploading ? <><svg className="animate-spin h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Subiendo</> : 'Adjuntar'}
                  </button>
               </div>
            </div>

            <div className="space-y-2.5 max-h-60 overflow-y-auto custom-scrollbar pr-2">
               <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Archivos Vinculados</label>
               {itemEvidencia.documentos_vinculados?.length === 0 ? (
                 <div className="p-6 text-center bg-slate-50 rounded-xl border border-slate-100">
                    <p className="text-xs text-slate-400 italic">No hay evidencias cargadas para este ítem.</p>
                 </div>
               ) : itemEvidencia.documentos_vinculados?.map((doc: any) => (
                 <div key={doc.id_documentacion} className="flex justify-between items-center p-3.5 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-lgc-primary transition-colors group">
                    <div className="flex items-center gap-3 overflow-hidden">
                       <div className="w-8 h-8 rounded bg-blue-50 text-blue-500 flex items-center justify-center shrink-0">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                       </div>
                       <a href={`${process.env.NEXT_PUBLIC_IMG_URL}/${doc.path_archivos}`} target="_blank" className="text-xs text-slate-700 font-bold hover:text-lgc-primary truncate transition-colors" title={doc.nombre_original}>{doc.nombre_original}</a>
                    </div>
                    <button onClick={() => handleBorrarEvidencia(doc.id_documentacion)} className="text-slate-300 hover:text-red-500 hover:bg-red-50 p-2 rounded-lg transition-colors shrink-0" title="Eliminar archivo">
                       <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    </button>
                 </div>
               ))}
            </div>
            
            <div className="mt-8 flex justify-end">
               <button onClick={() => setItemEvidencia(null)} className="bg-slate-100 hover:bg-slate-200 px-8 py-3 rounded-xl text-xs font-bold uppercase text-slate-600 tracking-widest transition-colors shadow-sm">Terminar y Cerrar</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de nueva normativa (estilo mejorado, sin scroll externo) */}
      {showNuevaNormaModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="p-6 bg-slate-50 border-b flex justify-between items-center shrink-0">
              <h2 className="text-xl font-heading text-lgc-primary uppercase tracking-tight">Cargar nueva normativa</h2>
              <button onClick={() => setShowNuevaNormaModal(false)} className="text-slate-400 hover:text-slate-600 text-2xl">&times;</button>
            </div>
            <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Tipo de Norma *</label>
                  <select
                    className="w-full p-3 bg-white border border-lgc-primary rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm"
                    value={nuevaNormaForm.id_tipo_norma}
                    onChange={(e) => setNuevaNormaForm({...nuevaNormaForm, id_tipo_norma: e.target.value})}
                  >
                    <option value="">Seleccione...</option>
                    {tiposNorma.map((t: any) => <option key={t.id} value={t.id}>{t.descripcion}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Número *</label>
                  <input type="text" className="w-full p-3 bg-white border border-lgc-primary rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm" value={nuevaNormaForm.numero} onChange={(e) => setNuevaNormaForm({...nuevaNormaForm, numero: e.target.value})} />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Año *</label>
                  <input type="number" className="w-full p-3 bg-white border border-lgc-primary rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm" value={nuevaNormaForm.anio} onChange={(e) => setNuevaNormaForm({...nuevaNormaForm, anio: parseInt(e.target.value)})} />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Emisor *</label>
                  <select
                    className="w-full p-3 bg-white border border-lgc-primary rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm"
                    value={nuevaNormaForm.id_emisor_norma}
                    onChange={(e) => setNuevaNormaForm({...nuevaNormaForm, id_emisor_norma: e.target.value})}
                  >
                    <option value="">Seleccione...</option>
                    {emisoresNorma.map((e: any) => <option key={e.id} value={e.id}>{e.descripcion}</option>)}
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Síntesis</label>
                  <textarea rows={3} className="w-full p-3 bg-white border border-lgc-primary rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm resize-none" value={nuevaNormaForm.sintesis} onChange={(e) => setNuevaNormaForm({...nuevaNormaForm, sintesis: e.target.value})} />
                </div>
                <div className="md:col-span-2">
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">URL</label>
                  <input type="url" className="w-full p-3 bg-white border border-lgc-primary rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm" value={nuevaNormaForm.url_norma} onChange={(e) => setNuevaNormaForm({...nuevaNormaForm, url_norma: e.target.value})} />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Estado Normativo *</label>
                  <select
                    className="w-full p-3 bg-white border border-lgc-primary rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm"
                    value={nuevaNormaForm.id_estado_norma}
                    onChange={(e) => setNuevaNormaForm({...nuevaNormaForm, id_estado_norma: e.target.value})}
                  >
                    {estadosNorma.map((e: any) => <option key={e.id} value={e.id}>{e.descripcion}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase text-slate-500 tracking-widest block mb-2">Fecha Publicación (opcional)</label>
                  <input type="date" className="w-full p-3 bg-white border border-lgc-primary rounded-lg outline-none focus:ring-2 focus:ring-lgc-primary text-sm" value={nuevaNormaForm.fecha_publicacion || ''} onChange={(e) => setNuevaNormaForm({...nuevaNormaForm, fecha_publicacion: e.target.value})} />
                </div>
              </div>
            </div>
            <div className="p-5 border-t border-slate-100 bg-slate-50 flex justify-end gap-4 shrink-0">
              <button onClick={() => setShowNuevaNormaModal(false)} className="px-6 py-2.5 text-xs uppercase font-bold text-slate-500 bg-white border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors">Cancelar</button>
              <button onClick={handleGuardarNuevaNorma} disabled={cargandoNuevaNorma} className="px-8 py-2.5 bg-lgc-primary text-white font-bold rounded-lg uppercase text-xs shadow-md hover:bg-[#006A8A] transition-all disabled:opacity-50">
                {cargandoNuevaNorma ? "Guardando..." : "Guardar Norma"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}