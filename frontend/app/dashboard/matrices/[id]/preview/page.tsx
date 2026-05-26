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
  'editable1': 'Campo Editable 1',
  'editable2': 'Campo Editable 2',
  'editable3': 'Campo Editable 3',
  'editable4': 'Campo Editable 4',
  'editable5': 'Campo Editable 5',
};

export default function PreviewMatrizPage() {
  const router = useRouter();
  const params = useParams();
  const idMatriz = params.id as string;
  const { canRead, canEdit } = usePermissions();

  const [items, setItems] = useState<any[]>([]);
  const [config, setConfig] = useState<string[]>([]);
  const [headerInfo, setHeaderInfo] = useState<any>(null);
  
  const [loading, setLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isCopying, setIsCopying] = useState(false);

  // 1. Cargar Datos (Header y Items)
  const fetchData = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return router.push("/");
    
    try {
      setLoading(true);
      // Traemos el Header (Logo, Cliente, Establecimiento)
      const resH = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/leer.php?id_matriz=${idMatriz}`, { 
        headers: { "Authorization": `Bearer ${token}` } 
      });
      const dataH = await resH.json();
      if (dataH.registros && dataH.registros.length > 0) setHeaderInfo(dataH.registros[0]);

      // Traemos los Items y la Configuración de columnas
      const resI = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/leer_items.php?id_matriz=${idMatriz}`, { 
        headers: { "Authorization": `Bearer ${token}` } 
      });
      const dataI = await resI.json();
      
      // Extraer solo los IDs si config_columnas es un array de objetos
      const configData = dataI.config_columnas || [];
      const configIds = Array.isArray(configData) && configData.length > 0 && typeof configData[0] === 'object'
        ? configData.map((col: any) => col.id)
        : configData;
      setConfig(configIds);
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

  // Función para Publicar la Matriz
  const handlePublicar = async () => {
    if (!confirm("¿Confirma que desea PUBLICAR esta matriz? Quedará como versión definitiva vigente y la anterior publicada pasará a archivada.")) return;
    
    try {
        setIsPublishing(true);
        const token = localStorage.getItem("sgml_token");

        // Usamos publicar_matriz_config.php que aplica la transacción de archivado correctamente
        const payload = {
            id_matriz: headerInfo.id_matriz,
            config_columnas: config  // reenviamos la config que ya tenemos cargada
        };

        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/publicar_matriz_config.php`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            fetchData();
        } else {
            const data = await res.json();
            alert("Error al publicar: " + data.mensaje);
        }
    } catch (error) {
        console.error(error);
        alert("Error de conexión al publicar.");
    } finally {
        setIsPublishing(false);
    }
  };

  // Función para copiar una matriz publicada como nueva versión en borrador
  const handleCopiar = async () => {
    if (!confirm(`¿Crear una nueva versión en BORRADOR copiando esta matriz? Se clonarán todos los ítems y normativas. La versión actual (${headerInfo?.version}.0) seguirá publicada hasta que la nueva versión sea publicada.`)) return;

    try {
        setIsCopying(true);
        const token = localStorage.getItem("sgml_token");

        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/copiar_matriz.php`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ id_matriz: headerInfo.id_matriz })
        });

        const data = await res.json();
        if (res.ok && data.id_matriz) {
            alert(`Nueva versión ${data.version}.0 creada en borrador (#${data.id_matriz}). Serás redirigido al nuevo workspace.`);
            router.push(`/dashboard/matrices/${data.id_matriz}`);
        } else {
            alert("Error al copiar: " + (data.mensaje || "Error desconocido"));
        }
    } catch (error) {
        console.error(error);
        alert("Error de conexión al copiar.");
    } finally {
        setIsCopying(false);
    }
  };

  const renderContent = (item: any, colId: string) => {
    switch (colId) {
      case 'normas':
        return (
          <div className="flex flex-col gap-1">
            {item.normas_vinculadas?.map((n: any, i: number) => (
              <span key={i} className="text-[9px] print:text-[7px] font-bold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 w-fit uppercase">
                {n.tipo_norma} {n.numero}/{n.anio}
              </span>
            ))}
          </div>
        );
      case 'estado':
        const color = item.color_hex ? `#${item.color_hex}` : '#cbd5e1';
        return (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-[9px] print:text-[8px] font-bold uppercase border print:border-slate-300" style={{ backgroundColor: `${color}10`, color: color, borderColor: `${color}30` }}>
             {item.estado_cumplimiento_desc}
          </span>
        );
      case 'vencimiento_plazo':
      case 'fecha_cumplimiento':
        return item[colId] ? new Date(item[colId]).toLocaleDateString('es-AR') : '-';
      case 'norma_emisor':
        const emisores = Array.from(new Set(item.normas_vinculadas?.map((n:any) => n.emisor_desc).filter(Boolean)));
        return emisores.join(', ') || '-';
      case 'norma_nivel_jur':
        const niveles = Array.from(new Set(item.normas_vinculadas?.map((n:any) => n.nivel_jurisdiccion_desc || n.jurisdiccion_desc).filter(Boolean)));
        return niveles.join(', ') || '-';
      default:
        // Renderizamos campos JSON dinámicos o campos de texto normales
        return item[colId] || '-';
    }
  };

  if (loading) return <div className="py-20 text-center animate-pulse text-lgc-primary font-bold tracking-widest uppercase">Cargando Documento...</div>;

  // Orientación del PDF Dinámica: Más de 10 columnas = Horizontal (landscape)
  const isLandscape = config.length > 10;

  return (
    <div className={`animate-fade-in flex flex-col h-full bg-slate-50 ${isFullscreen ? 'p-0' : 'space-y-4'}`}>
      
      {/* MAGIA DE CSS PARA EL PDF PERFECTO */}
      <style dangerouslySetInnerHTML={{__html: `
        @media print {
          @page {
            size: ${isLandscape ? 'A4 landscape' : 'A4 portrait'};
            margin: 10mm;
          }
          body {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
            background-color: white !important;
          }
          /* Oculta menú lateral y cabeceras del sistema en impresión */
          aside, header { display: none !important; }
          main { padding: 0 !important; margin: 0 !important; overflow: visible !important; height: auto !important; }
        }
      `}} />

      {/* BARRA DE HERRAMIENTAS (Se oculta sola al imprimir por clases nativas de Next/Tailwind) */}
      {!isFullscreen && (
        <div className="print:hidden bg-white px-5 py-3 rounded-xl shadow-sm border border-slate-200 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-4">
            <Link href={`/dashboard/matrices/${idMatriz}`} className="text-slate-400 hover:text-lgc-primary transition-colors bg-slate-50 p-2 rounded-lg border border-slate-200">
               <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
            </Link>
            <h1 className="text-xl font-heading text-slate-800 uppercase tracking-tight flex items-center gap-3">
               Documento Final 
               <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-widest uppercase shadow-sm border ${
                 headerInfo?.id_estado_matriz === 2
                   ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
                   : headerInfo?.id_estado_matriz === 3
                   ? 'bg-slate-100 text-slate-500 border-slate-300'
                   : 'bg-orange-100 text-orange-700 border-orange-200'
               }`}>
                 {headerInfo?.estado_matriz_desc || 'Borrador'}
               </span>
            </h1>
            {/* Aviso de solo lectura para archivadas */}
            {headerInfo?.id_estado_matriz === 3 && (
              <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-400 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                Solo lectura — Archivada
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <button onClick={toggleFullscreen} className="bg-white hover:bg-slate-50 text-slate-600 font-bold py-2 px-4 rounded-lg transition-all text-[10px] uppercase tracking-widest border border-slate-300 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
              Pantalla Completa
            </button>

            {/* BOTÓN PUBLICAR — solo para borradores (estado 1) */}
            {canEdit("matriz") && headerInfo?.id_estado_matriz === 1 && (
              <button onClick={handlePublicar} disabled={isPublishing} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-4 rounded-lg transition-all shadow-md text-[10px] uppercase tracking-widest flex items-center gap-2 disabled:opacity-50">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                {isPublishing ? 'Publicando...' : 'Publicar Matriz'}
              </button>
            )}

            {/* BOTÓN COPIAR COMO NUEVA VERSIÓN — solo para publicadas (estado 2) */}
            {canEdit("matriz") && headerInfo?.id_estado_matriz === 2 && (
              <button onClick={handleCopiar} disabled={isCopying} className="bg-lgc-accent hover:bg-[#D97920] text-white font-bold py-2 px-4 rounded-lg transition-all shadow-md text-[10px] uppercase tracking-widest flex items-center gap-2 disabled:opacity-50">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                {isCopying ? 'Copiando...' : 'Nueva Versión (Borrador)'}
              </button>
            )}

            {/* BOTÓN DESCARGAR PDF */}
            <button onClick={() => window.print()} className="bg-lgc-primary hover:bg-lgc-hover text-white font-bold py-2 px-4 rounded-lg transition-all shadow-md text-[10px] uppercase tracking-widest flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              Exportar a PDF
            </button>
          </div>
        </div>
      )}

      {/* DOCUMENTO DE LA MATRIZ (Este es el canvas que se imprime) */}
      <div className={`flex-1 bg-white overflow-auto shadow-2xl print:shadow-none print:overflow-visible ${isFullscreen ? 'p-0' : 'rounded-xl mx-auto w-full border border-slate-200 print:border-none'}`}>
        
        {/* ENCABEZADO CORPORATIVO */}
        <div className="p-8 print:p-4 border-b-4 border-lgc-primary flex justify-between items-center gap-6 bg-white">
          <div className="flex items-center gap-6">
            {headerInfo?.logo_path ? (
              <img src={`${process.env.NEXT_PUBLIC_IMG_URL}/${headerInfo.logo_path}`} alt="Cliente Logo" className="h-20 print:h-14 w-auto object-contain" />
            ) : (
              <div className="h-20 w-20 print:h-14 print:w-14 bg-slate-100 rounded-lg flex items-center justify-center text-slate-300 font-bold text-2xl uppercase border-2 border-dashed border-slate-200">
                LOGO
              </div>
            )}
            <div className="h-16 print:h-10 w-px bg-slate-200 hidden md:block"></div>
            <div>
              <h2 className="text-2xl print:text-lg font-heading text-slate-800 uppercase leading-none">{headerInfo?.nombre_fantasia || headerInfo?.razon_social}</h2>
              <p className="text-lgc-primary font-bold text-sm print:text-[10px] uppercase tracking-widest mt-1">{headerInfo?.establecimiento_desc}</p>
              <div className="flex gap-4 mt-2 print:mt-1">
                 <span className="text-[10px] print:text-[8px] font-bold text-slate-500 uppercase tracking-tighter">Esp: {headerInfo?.especialidad_matriz_desc}</span>
                 <span className="text-[10px] print:text-[8px] font-bold text-slate-500 uppercase tracking-tighter">Tipo: {headerInfo?.tipo_matriz_desc}</span>
                 <span className="text-[10px] print:text-[8px] font-bold text-slate-500 uppercase tracking-tighter">Versión: {headerInfo?.version}.0</span>
              </div>
            </div>
          </div>
          
          <div className="text-right">
             <div className="text-[10px] print:text-[8px] font-bold text-slate-400 uppercase tracking-widest mb-1">Emitido por</div>
             <img src="/img/logo_lgc.png" alt="LGC Logo" className="h-10 print:h-6 w-auto opacity-80 ml-auto" onError={(e) => e.currentTarget.style.display = 'none'} />
             <div className="text-[11px] print:text-[8px] font-bold text-slate-800 uppercase mt-2">LGC CONSULTORES</div>
          </div>
        </div>

        {/* CUERPO DE LA MATRIZ (GRILLA) */}
        <div className="p-0">
          {/* Se usa table-auto y anchos mínimos para que el navegador haga el cálculo exacto del PDF */}
          <table className="w-full text-left border-collapse table-auto print:table-fixed print:text-[8px]">
            <thead className="bg-slate-50 print:bg-slate-100 sticky top-0 z-10 border-b border-slate-200 print:table-header-group">
              <tr>
                <th className="p-4 print:p-2 text-[10px] print:text-[7px] font-bold text-slate-600 uppercase tracking-wider border-r border-slate-200 w-10 text-center">#</th>
                {config.map(colId => (
                  <th key={colId} className="p-4 print:p-2 text-[10px] print:text-[7px] font-bold text-slate-600 uppercase tracking-wider border-r border-slate-200 wrap-break-words">
                    {COLUMN_LABELS[colId] || colId}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 print:divide-slate-300 text-[11px] print:text-[8px]">
              {items.length === 0 ? (
                <tr><td colSpan={config.length + 1} className="p-20 text-center text-slate-400 italic">No hay ítems registrados en esta matriz.</td></tr>
              ) : (
                items.map((item, idx) => (
                  <tr key={item.id_item_matriz} className="hover:bg-slate-50/50 transition-colors print:break-inside-avoid">
                    <td className="p-4 print:p-2 font-bold text-slate-400 print:text-slate-600 border-r border-slate-50 print:border-slate-200 text-center">{idx + 1}</td>
                    {config.map(colId => (
                      <td key={colId} className="p-4 print:p-2 align-top text-slate-700 leading-relaxed border-r border-slate-50 print:border-slate-200 wrap-break-words">
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
        <div className="p-8 print:p-4 bg-slate-50 print:bg-white border-t border-slate-100 print:border-slate-300 mt-10 print:mt-0 hidden print:block">
           <div className="flex justify-between text-[10px] print:text-[8px] font-bold text-slate-500 uppercase">
              <span>© {new Date().getFullYear()} LGC Consultores - Documento Legal</span>
              <span>Matriz ID: {idMatriz}</span>
           </div>
        </div>
      </div>

    </div>
  );
}