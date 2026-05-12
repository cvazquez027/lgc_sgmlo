"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { usePermissions } from "../../../../hooks/usePermissions";

// Diccionario de etiquetas (para que los encabezados de tabla coincidan con el workspace)
const COLUMN_LABELS: Record<string, string> = {
  'resumen_legal': 'Obligación / Resumen Legal',
  'normas': 'Normativas',
  'norma_nivel_jur': 'Jurisdicción',
  'norma_emisor': 'Emisor',
  'estado': 'Estado',
  'articulos_aplicables': 'Artículos',
  'proceso_aplica': 'Proceso',
  'detalle_tema': 'Detalle',
  'responsable_cumplimiento': 'Responsable',
  'vencimiento_plazo': 'Vencimiento',
  'evidencia_cumplimiento': 'Evidencia',
  'verificacion_cumplimiento': 'Verificación',
  'interpretacion_aplicacion': 'Interpretación',
};

export default function PreviewMatrizPage() {
  const router = useRouter();
  const params = useParams();
  const idMatriz = params.id as string;
  const { canRead } = usePermissions();

  const [items, setItems] = useState<any[]>([]);
  const [config, setConfig] = useState<string[]>([]);
  const [headerInfo, setHeaderInfo] = useState<any>(null);
  
  const [loading, setLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // 1. Cargar Datos (Header y Items)
  const fetchData = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return router.push("/");
    
    try {
      setLoading(true);
      // Traemos el Header (Logo, Cliente, Establecimiento)
      const resH = await fetch(`http://localhost/lgc_sgmlo/backend/api/matriz/leer.php?id_matriz=${idMatriz}`, { 
        headers: { "Authorization": `Bearer ${token}` } 
      });
      const dataH = await resH.json();
      if (dataH.registros && dataH.registros.length > 0) setHeaderInfo(dataH.registros[0]);

      // Traemos los Items y la Configuración de columnas
      const resI = await fetch(`http://localhost/lgc_sgmlo/backend/api/matriz/leer_items.php?id_matriz=${idMatriz}`, { 
        headers: { "Authorization": `Bearer ${token}` } 
      });
      const dataI = await resI.json();
      setConfig(dataI.config_columnas || []);
      setItems(dataI.registros || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [idMatriz, router]);

  useEffect(() => {
    if (canRead("matriz")) fetchData();
  }, [fetchData, canRead]);

  // Alternar Pantalla Completa
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
        setIsFullscreen(false);
      }
    }
  };

  // Escuchar cambio de fullscreen (tecla ESC)
  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  const renderContent = (item: any, colId: string) => {
    switch (colId) {
      case 'normas':
        return (
          <div className="flex flex-col gap-1">
            {item.normas_vinculadas?.map((n: any, i: number) => (
              <span key={i} className="text-[9px] font-bold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 w-fit uppercase">
                {n.tipo_norma} {n.numero}/{n.anio}
              </span>
            ))}
          </div>
        );
      case 'estado':
        const color = item.color_hex ? `#${item.color_hex}` : '#cbd5e1';
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-[9px] font-bold uppercase border" style={{ backgroundColor: `${color}10`, color: color, borderColor: `${color}30` }}>
             {item.estado_cumplimiento_desc}
          </span>
        );
      case 'vencimiento_plazo':
        return item.vencimiento_plazo ? new Date(item.vencimiento_plazo).toLocaleDateString('es-AR') : '-';
      case 'norma_emisor':
        const emisores = Array.from(new Set(item.normas_vinculadas?.map((n:any) => n.emisor_desc).filter(Boolean)));
        return emisores.join(', ') || '-';
      case 'norma_nivel_jur':
        const niveles = Array.from(new Set(item.normas_vinculadas?.map((n:any) => n.nivel_jurisdiccion_desc || n.jurisdiccion_desc).filter(Boolean)));
        return niveles.join(', ') || '-';
      default:
        return item[colId] || '-';
    }
  };

  if (loading) return <div className="py-20 text-center animate-pulse text-lgc-primary font-bold tracking-widest uppercase">Cargando Previsualización...</div>;

  return (
    <div className={`animate-fade-in flex flex-col h-full bg-slate-50 ${isFullscreen ? 'p-0' : 'space-y-4'}`}>
      
      {/* BARRA DE HERRAMIENTAS (No se imprime) */}
      {!isFullscreen && (
        <div className="bg-white px-5 py-3 rounded-xl shadow-sm border border-slate-200 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-4">
            <Link href={`/dashboard/matrices/${idMatriz}`} className="text-slate-400 hover:text-lgc-primary transition-colors bg-slate-50 p-2 rounded-lg border border-slate-200">
               <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
            </Link>
            <h1 className="text-xl font-heading text-slate-800 uppercase tracking-tight">Previsualización de Matriz</h1>
          </div>
          <div className="flex gap-2">
            <button onClick={toggleFullscreen} className="bg-white hover:bg-slate-50 text-slate-600 font-bold py-2 px-4 rounded-lg transition-all text-[10px] uppercase tracking-widest border border-slate-300 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
              Pantalla Completa
            </button>
            <button onClick={() => window.print()} className="bg-lgc-primary hover:bg-lgc-hover text-white font-bold py-2 px-4 rounded-lg transition-all shadow-md text-[10px] uppercase tracking-widest flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" /></svg>
              Imprimir / PDF
            </button>
          </div>
        </div>
      )}

      {/* DOCUMENTO DE LA MATRIZ */}
      <div className={`flex-1 bg-white overflow-auto shadow-2xl ${isFullscreen ? 'p-0' : 'rounded-xl mx-auto w-full border border-slate-200'}`}>
        
        {/* ENCABEZADO CORPORATIVO */}
        <div className="p-8 border-b-4 border-lgc-primary flex flex-col md:flex-row justify-between items-center gap-6 bg-white">
          <div className="flex items-center gap-6">
            {headerInfo?.logo_path ? (
              <img src={`http://localhost/lgc_sgmlo/backend/${headerInfo.logo_path}`} alt="Cliente Logo" className="h-20 w-auto object-contain" />
            ) : (
              <div className="h-20 w-20 bg-slate-100 rounded-lg flex items-center justify-center text-slate-300 font-bold text-2xl uppercase border-2 border-dashed border-slate-200">
                LOGO
              </div>
            )}
            <div className="h-16 w-px bg-slate-200 hidden md:block"></div>
            <div>
              <h2 className="text-2xl font-heading text-slate-800 uppercase leading-none">{headerInfo?.nombre_fantasia || headerInfo?.razon_social}</h2>
              <p className="text-lgc-primary font-bold text-sm uppercase tracking-widest mt-1">{headerInfo?.establecimiento_desc}</p>
              <div className="flex gap-4 mt-2">
                 <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Matriz Legal: {headerInfo?.tipo_matriz_desc}</span>
                 <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Versión: {headerInfo?.version}.0</span>
              </div>
            </div>
          </div>
          
          <div className="text-right">
             <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 text-center md:text-right">Emitido por</div>
             <img src="/img/logo_lgc.png" alt="LGC Logo" className="h-10 w-auto opacity-80" onError={(e) => e.currentTarget.style.display = 'none'} />
             <div className="text-[11px] font-bold text-slate-800 uppercase mt-2">LGC CONSULTORES</div>
          </div>
        </div>

        {/* CUERPO DE LA MATRIZ (GRILLA) */}
        <div className="p-0">
          <table className="w-full text-left border-collapse table-auto">
            <thead className="bg-slate-50 sticky top-0 z-10 border-b border-slate-200">
              <tr>
                <th className="p-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider border-r border-slate-100 w-12 text-center">#</th>
                {config.map(colId => (
                  <th key={colId} className="p-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider border-r border-slate-100">
                    {COLUMN_LABELS[colId] || colId}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-[11px]">
              {items.length === 0 ? (
                <tr><td colSpan={config.length + 1} className="p-20 text-center text-slate-400 italic">No hay ítems registrados en esta matriz.</td></tr>
              ) : (
                items.map((item, idx) => (
                  <tr key={item.id_item_matriz} className="hover:bg-slate-50/50 transition-colors">
                    <td className="p-4 font-bold text-slate-400 border-r border-slate-50 text-center">{idx + 1}</td>
                    {config.map(colId => (
                      <td key={colId} className="p-4 align-top text-slate-700 leading-relaxed border-r border-slate-50 max-w-xs md:max-w-sm lg:max-w-md">
                        {renderContent(item, colId)}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* PIE DE PÁGINA (Solo para impresión) */}
        <div className="p-8 bg-slate-50 border-t border-slate-100 mt-10 hidden print:block">
           <div className="flex justify-between text-[10px] font-bold text-slate-400 uppercase">
              <span>© {new Date().getFullYear()} LGC Consultores - Gestión de Cumplimiento Legal</span>
              <span>Página 1 de 1</span>
           </div>
        </div>
      </div>

    </div>
  );
}