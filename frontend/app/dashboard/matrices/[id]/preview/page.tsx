"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { usePermissions } from "../../../../hooks/usePermissions";
import { useToast } from "../../../../providers/ToastProvider";
import { useConfirm } from "../../../../providers/ConfirmProvider";

// Diccionario de etiquetas
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
  'id_tipo_modalidad': 'Modalidad',
  'obs_modalidad': 'Obs. Modalidad',
  'editable1': 'Campo Editable 1',
  'editable2': 'Campo Editable 2',
  'editable3': 'Campo Editable 3',
  'editable4': 'Campo Editable 4',
  'editable5': 'Campo Editable 5',
  'norma_sintesis': 'Síntesis y Categorías',
  'adjuntos': 'Evidencia (Archivos)',
};

// Convierte una URL de imagen a Data URL base64 (para incrustar logos en el PDF).
// Si la imagen no puede descargarse (ej. CORS del backend) devuelve null y el
// PDF se genera igual, simplemente sin ese logo.
async function urlToDataUrl(url: string): Promise<string | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const blob = await res.blob();
    return await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch {
    return null;
  }
}

// Detecta el formato (PNG/JPEG) a partir del Data URL, requerido por jsPDF.addImage
function dataUrlFormat(dataUrl: string): "PNG" | "JPEG" {
  return dataUrl.startsWith("data:image/png") ? "PNG" : "JPEG";
}

export default function PreviewMatrizPage() {
  const router = useRouter();
  const params = useParams();
  const idMatriz = params.id as string;
  const { canRead, canEdit } = usePermissions();
  const toast = useToast();
  const confirm = useConfirm();

  const [items, setItems] = useState<any[]>([]);
  const [config, setConfig] = useState<any[]>([]);
  const [headerInfo, setHeaderInfo] = useState<any>(null);
  
  const [loading, setLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [isCopying, setIsCopying] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [cumplimientoTotal, setCumplimientoTotal] = useState<number>(0);
  const [estadosCumplimiento, setEstadosCumplimiento] = useState<any[]>([]);

  // --- NUEVO: Control de cliente ---
  const [isUserCliente, setIsUserCliente] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem("sgml_cliente_id");
    setIsUserCliente(!!(raw && raw !== "null"));
  }, []);

  const fetchData = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return router.push("/");
    
    try {
      setLoading(true);
      const resH = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/leer.php?id_matriz=${idMatriz}`, { 
        headers: { "Authorization": `Bearer ${token}` } 
      });
      const dataH = await resH.json();
      if (dataH.registros && dataH.registros.length > 0) setHeaderInfo(dataH.registros[0]);

      const resI = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/leer_items.php?id_matriz=${idMatriz}`, { 
        headers: { "Authorization": `Bearer ${token}` } 
      });
      const dataI = await resI.json();
      
      let configData = dataI.config_columnas;
      if (typeof configData === 'string') {
          try { configData = JSON.parse(configData); } catch(e) { configData = []; }
      }
      if (!Array.isArray(configData)) configData = [];

      let normalizedConfig = [];
      if (configData.length > 0) {
          if (typeof configData[0] === 'string') {
              normalizedConfig = configData.map((id: string) => ({ 
                  id, 
                  label: COLUMN_LABELS[id] || (id.startsWith('custom_') ? 'Columna Personalizada' : id) 
              }));
          } else {
              normalizedConfig = configData;
          }
      } else {
          const isRegulatoria = dataH.registros?.[0]?.id_tipo_matriz === 1;
          const defaultCols = isRegulatoria 
            ? ['normas', 'norma_nivel_jur', 'norma_emisor', 'norma_sintesis', 'resumen_legal', 'articulos_aplicables', 'interpretacion_aplicacion', 'id_tipo_modalidad', 'obs_modalidad']
            : ['normas', 'norma_nivel_jur', 'norma_emisor', 'norma_sintesis', 'resumen_legal', 'articulos_aplicables', 'interpretacion_aplicacion', 'id_tipo_modalidad', 'obs_modalidad', 'evidencia_cumplimiento', 'id_responsable_establecimiento', 'verificacion_cumplimiento', 'estado', 'vencimiento_plazo', 'fecha_cumplimiento', 'obs_estado_cumplimiento', 'adjuntos'];
          normalizedConfig = defaultCols.map((id: string) => ({ id, label: COLUMN_LABELS[id] || id }));
      }

      setConfig(normalizedConfig);
      setItems(dataI.registros || []);

      // Obtener estados de cumplimiento para el gráfico
      const resEst = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/maestras/leer.php?tabla=estado_cumplimiento`, { headers: { "Authorization": `Bearer ${token}` } });
      const dataEst = await resEst.json();
      setEstadosCumplimiento(dataEst.registros || []);

      // Calcular porcentaje de cumplimiento
      const itemsConEstado = dataI.registros || [];
      const totalItems = itemsConEstado.length;
      const cumpleItems = itemsConEstado.filter((item: any) => {
        const estadoDesc = item.estado_cumplimiento_desc?.toLowerCase();
        return estadoDesc === 'cumple';
      }).length;
      setCumplimientoTotal(totalItems > 0 ? Math.round((cumpleItems / totalItems) * 100) : 0);
      
    } catch (err) {
      console.error(err);
      toast.showToast("Error", "Error al cargar los datos de la matriz.", "error");
    } finally {
      setLoading(false);
    }
  }, [idMatriz, router, toast]);

  useEffect(() => {
    if (canRead("matriz")) fetchData();
  }, [fetchData, canRead]);

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

  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  const handlePublicar = async () => {
    const ok = await confirm({
      title: "Publicar matriz",
      message: "¿Confirma que desea PUBLICAR esta matriz? Quedará como versión definitiva vigente y la anterior publicada pasará a archivada.",
      confirmText: "Publicar",
      cancelText: "Cancelar"
    });
    if (!ok) return;
    
    try {
        setIsPublishing(true);
        const token = localStorage.getItem("sgml_token");
        const payload = {
            id_matriz: headerInfo.id_matriz,
            config_columnas: config
        };
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matriz/publicar_matriz_config.php`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            toast.showToast("Éxito", "Matriz publicada correctamente.", "success");
            fetchData();
        } else {
            const data = await res.json();
            toast.showToast("Error", data.mensaje || "Error al publicar la matriz.", "error");
        }
    } catch (error) {
        console.error(error);
        toast.showToast("Error", "Error de conexión al publicar.", "error");
    } finally {
        setIsPublishing(false);
    }
  };

  const handleCopiar = async () => {
    const ok = await confirm({
      title: "Copiar matriz",
      message: `¿Crear una nueva versión en BORRADOR copiando esta matriz? Se clonarán todos los ítems y normativas. La versión actual (${headerInfo?.version}.0) seguirá publicada hasta que la nueva versión sea publicada.`,
      confirmText: "Copiar",
      cancelText: "Cancelar"
    });
    if (!ok) return;

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
            toast.showToast("Éxito", `Nueva versión ${data.version}.0 creada en borrador (#${data.id_matriz}).`, "success");
            router.push(`/dashboard/matrices/${data.id_matriz}`);
        } else {
            toast.showToast("Error", data.mensaje || "Error desconocido al copiar la matriz.", "error");
        }
    } catch (error) {
        console.error(error);
        toast.showToast("Error", "Error de conexión al copiar.", "error");
    } finally {
        setIsCopying(false);
    }
  };

  // Función para renderizar el contenido de una celda (reutilizada para tabla y exportación)
  const renderContent = (item: any, colId: string) => {
    switch (colId) {
      case 'normas':
        return (
          <div className="flex flex-col gap-1.5">
            {item.normas_vinculadas?.map((n: any, i: number) => (
              <div key={i} className="flex items-center gap-1.5 flex-wrap">
                <span className="text-[9px] print:text-[7px] font-bold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 uppercase">
                  {n.tipo_norma_desc || n.tipo_norma} {n.numero}/{n.anio}
                </span>
                {n.url_norma && (
                  <a href={n.url_norma} target="_blank" rel="noopener noreferrer" className="text-lgc-accent hover:text-[#D97920] print:text-blue-600 transition-colors" title="Ver Documento Original">
                    <svg className="w-3.5 h-3.5 print:w-3 print:h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                  </a>
                )}
              </div>
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
      case 'id_tipo_modalidad':
        return item.tipo_modalidad_desc || '-';
      case 'norma_sintesis':
        const normas = item.normas_vinculadas || [];
        if (normas.length === 0) return '-';
        return normas.map((n: any) => (
          <div key={n.id_norma} className="mb-2">
            <p className="text-[10px] text-slate-600 wrap-break-words">{n.sintesis || 'Sin síntesis'}</p>
            {n.categorias && n.categorias.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {n.categorias.map((c: string, idx: number) => (
                  <span key={idx} className="bg-blue-50 text-blue-700 border border-blue-200 text-[8px] font-bold px-1.5 py-0.5 rounded uppercase shadow-sm">
                    {c}
                  </span>
                ))}
              </div>
            )}
          </div>
        ));
      case 'adjuntos':
        const docs = item.documentos_vinculados || [];
        if (docs.length === 0) return '-';
        return docs.map((doc: any) => (
          <div key={doc.id_documentacion} className="text-[10px] text-slate-600">
            <a href={`${process.env.NEXT_PUBLIC_IMG_URL}/${doc.path_archivos}`} target="_blank" rel="noopener noreferrer" className="text-lgc-accent hover:underline">
              {doc.nombre_original}
            </a>
          </div>
        ));
      default:
        return item[colId] || '-';
    }
  };

  // Función para obtener el valor plano de una celda (para exportación)
  const getPlainTextContent = (item: any, colId: string): string => {
    switch (colId) {
      case 'normas':
        const normas = item.normas_vinculadas || [];
        return normas.map((n: any) => `${n.tipo_norma_desc || n.tipo_norma} ${n.numero}/${n.anio}`).join('; ');
      case 'estado':
        return item.estado_cumplimiento_desc || '-';
      case 'id_tipo_modalidad':
        return item.tipo_modalidad_desc || '-';
      case 'norma_sintesis':
        const normas2 = item.normas_vinculadas || [];
        if (normas2.length === 0) return '-';
        return normas2.map((n: any) => {
          let texto = n.sintesis || '';
          if (n.categorias && n.categorias.length > 0) {
            texto += ` (Categorías: ${n.categorias.join(', ')})`;
          }
          return texto;
        }).join('; ');
      case 'adjuntos':
        const docs = item.documentos_vinculados || [];
        if (docs.length === 0) return '-';
        return docs.map((doc: any) => doc.nombre_original).join('; ');
      default:
        const val = item[colId];
        if (val === undefined || val === null) return '-';
        if (typeof val === 'string') return val.replace(/[\n\r]+/g, ' ').replace(/"/g, '""');
        return String(val);
    }
  };

  // Exportar a CSV (Excel)
  const exportToExcel = () => {
    const headers = config.map(col => col.label || COLUMN_LABELS[col.id] || col.id);
    const rows = items.map(item => {
      return config.map(col => {
        let rawValue = getPlainTextContent(item, col.id);
        if (typeof rawValue === 'string') {
          rawValue = rawValue.replace(/[\n\r]+/g, ' ').replace(/"/g, '""');
        }
        return rawValue;
      });
    });
    const csvData = [headers, ...rows];
    const csvContent = csvData.map(row => 
      row.map(cell => `"${cell}"`).join(';')
    ).join('\n');
    const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `matriz_${idMatriz}_${new Date().toISOString().slice(0,19)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Exportar a PDF generando el documento por código (jsPDF + autoTable).
  // Ya no depende del diálogo de impresión del navegador: la orientación y el
  // ancho de columnas se calculan acá, así que ninguna columna queda cortada.
  const exportToPDF = async () => {
    if (isExportingPdf) return;
    setIsExportingPdf(true);
    try {
      const { default: jsPDF } = await import("jspdf");
      const { default: autoTable } = await import("jspdf-autotable");

      // Más de 6 columnas -> horizontal, igual criterio que se usaba para @page print
      const orientation: "landscape" | "portrait" = config.length > 6 ? "landscape" : "portrait";
      const doc = new jsPDF({ orientation, unit: "mm", format: "a4" });

      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 10;
      let cursorY = margin;

      // --- Encabezado corporativo ---
      const [logoDataUrl, lgcLogoDataUrl] = await Promise.all([
        headerInfo?.logo_path
          ? urlToDataUrl(`${process.env.NEXT_PUBLIC_IMG_URL}/${headerInfo.logo_path}`)
          : Promise.resolve(null),
        urlToDataUrl(`${window.location.origin}/logo_lgc.png`),
      ]);

      if (logoDataUrl) {
        try {
          doc.addImage(logoDataUrl, dataUrlFormat(logoDataUrl), margin, cursorY, 20, 20, undefined, "FAST");
        } catch (e) {
          console.warn("No se pudo insertar el logo del cliente en el PDF", e);
        }
      }

      const textX = margin + (logoDataUrl ? 26 : 0);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(14);
      doc.setTextColor(30, 41, 59); // slate-800
      doc.text(String(headerInfo?.nombre_fantasia || headerInfo?.razon_social || ""), textX, cursorY + 6);

      doc.setFontSize(9);
      doc.setTextColor(217, 119, 6); // acento
      doc.text(String(headerInfo?.establecimiento_desc || ""), textX, cursorY + 12);

      doc.setFont("helvetica", "normal");
      doc.setFontSize(7);
      doc.setTextColor(100, 116, 139); // slate-500
      doc.text(
        `Esp: ${headerInfo?.especialidad_matriz_desc || "-"}     Tipo: ${headerInfo?.tipo_matriz_desc || "-"}     Versión: ${headerInfo?.version ?? "-"}.0`,
        textX,
        cursorY + 17
      );

      if (lgcLogoDataUrl) {
        try {
          doc.addImage(lgcLogoDataUrl, dataUrlFormat(lgcLogoDataUrl), pageWidth - margin - 26, cursorY, 26, 9, undefined, "FAST");
        } catch (e) {
          console.warn("No se pudo insertar el logo de LGC en el PDF", e);
        }
      }
      doc.setFontSize(7);
      doc.setTextColor(148, 163, 184);
      doc.text("EMITIDO POR", pageWidth - margin, cursorY + 15, { align: "right" });

      cursorY += 24;

      if (headerInfo?.mostrar_cumplimiento && headerInfo?.id_tipo_matriz === 2) {
        doc.setFontSize(8);
        doc.setTextColor(71, 85, 105);
        doc.text(`Cumplimiento: ${cumplimientoTotal}%`, margin, cursorY);
        cursorY += 6;
      }

      doc.setDrawColor(11, 61, 92);
      doc.setLineWidth(0.8);
      doc.line(margin, cursorY, pageWidth - margin, cursorY);
      cursorY += 4;

      // --- Tabla de datos (reutiliza getPlainTextContent, ya usado en la exportación a Excel) ---
      const head = [["#", ...config.map((c: any) => c.label || COLUMN_LABELS[c.id] || c.id)]];
      const body =
        items.length === 0
          ? [[{ content: "No hay ítems registrados en esta matriz.", colSpan: config.length + 1, styles: { halign: "center" as const, textColor: [148, 163, 184] as [number, number, number] } }]]
          : items.map((item, idx) => [String(idx + 1), ...config.map((c: any) => getPlainTextContent(item, c.id))]);

      autoTable(doc, {
        head,
        body,
        startY: cursorY,
        margin: { left: margin, right: margin, bottom: 14 },
        styles: {
          font: "helvetica",
          fontSize: 7,
          cellPadding: 2,
          overflow: "linebreak", // el texto se ajusta dentro de la columna en vez de cortarse
          valign: "top",
          lineColor: [226, 232, 240],
          lineWidth: 0.1,
        },
        headStyles: {
          fillColor: [241, 245, 249],
          textColor: [51, 65, 85],
          fontStyle: "bold",
          fontSize: 7,
        },
        columnStyles: {
          0: { cellWidth: 8, halign: "center" },
        },
        theme: "grid",
        showHead: "everyPage",
        // autoTable recalcula el ancho de cada columna para que la tabla completa
        // entre siempre dentro del ancho de página disponible (nunca se corta a la derecha)
        tableWidth: "auto",
      });

      // Pie de página con numeración total (se agrega al final porque recién ahí se sabe cuántas páginas hay)
      const totalPages = doc.getNumberOfPages();
      for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFontSize(7);
        doc.setTextColor(148, 163, 184);
        doc.text(`© ${new Date().getFullYear()} Lamas Global Consulting`, margin, pageHeight - 6);
        doc.text(`Página ${i} de ${totalPages}`, pageWidth - margin, pageHeight - 6, { align: "right" });
      }

      doc.save(`matriz_${idMatriz}_${new Date().toISOString().slice(0, 19)}.pdf`);
    } catch (err) {
      console.error(err);
      toast.showToast("Error", "No se pudo generar el PDF.", "error");
    } finally {
      setIsExportingPdf(false);
    }
  };

  if (loading) return <div className="py-20 text-center animate-pulse text-lgc-primary font-bold tracking-widest uppercase">Cargando Documento...</div>;

  const isLandscape = config.length > 6;

  return (
    <div className={`animate-fade-in flex flex-col h-full bg-slate-50 ${isFullscreen ? 'p-0' : 'space-y-4'}`}>
      
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
          aside, header { display: none !important; }
          main { padding: 0 !important; margin: 0 !important; overflow: visible !important; height: auto !important; }
        }
        .scrollbar-thin::-webkit-scrollbar {
          height: 8px;
        }
        .scrollbar-thin::-webkit-scrollbar-track {
          background: #f1f1f1;
          border-radius: 4px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 4px;
        }
        .scrollbar-thin::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}} />

      {!isFullscreen && (
        <div className="print:hidden bg-white px-5 py-3 rounded-xl shadow-sm border border-slate-200 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-4">
            <Link href={`/dashboard/matrices/${idMatriz}`} className="text-slate-400 hover:text-lgc-primary transition-colors bg-slate-50 p-2 rounded-lg border border-slate-200">
               <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
            </Link>
            <h1 className="text-xl font-heading text-slate-800 uppercase tracking-tight flex items-center gap-3">
               PREVISUALIZACIÓN DE LA MATRIZ
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
            {headerInfo?.id_estado_matriz === 3 && (
              <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-400 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                Solo lectura — Archivada
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <button onClick={toggleFullscreen} className="bg-white hover:bg-slate-50 text-slate-600 font-bold py-2 px-4 rounded-lg transition-all text-[10px] uppercase tracking-widest border border-slate-300 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 20.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
              </svg>
              Pantalla Completa
            </button>

            {canEdit("matriz") && headerInfo?.id_estado_matriz === 1 && !isUserCliente && (
              <button onClick={handlePublicar} disabled={isPublishing} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-4 rounded-lg transition-all shadow-md text-[10px] uppercase tracking-widest flex items-center gap-2 disabled:opacity-50">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                {isPublishing ? 'Publicando...' : 'Publicar Matriz'}
              </button>
            )}

            {canEdit("matriz") && headerInfo?.id_estado_matriz === 2 && !isUserCliente && (
              <button onClick={handleCopiar} disabled={isCopying} className="bg-lgc-accent hover:bg-[#D97920] text-white font-bold py-2 px-4 rounded-lg transition-all shadow-md text-[10px] uppercase tracking-widest flex items-center gap-2 disabled:opacity-50">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                {isCopying ? 'Copiando...' : 'Nueva Versión (Borrador)'}
              </button>
            )}

            <button onClick={exportToPDF} disabled={isExportingPdf} className="bg-lgc-primary hover:bg-lgc-hover text-white font-bold py-2 px-4 rounded-lg transition-all shadow-md text-[10px] uppercase tracking-widest flex items-center gap-2 disabled:opacity-50">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              {isExportingPdf ? 'Generando PDF...' : 'Exportar a PDF'}
            </button>
            
            <button onClick={exportToExcel} className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition-all shadow-md text-[10px] uppercase tracking-widest flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              Exportar a Excel
            </button>
          </div>
        </div>
      )}

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
          
          <div className="text-right flex flex-col items-end gap-2">
             {headerInfo?.mostrar_cumplimiento && headerInfo?.id_tipo_matriz === 2 && (
                <div className="flex items-center gap-2 bg-slate-100 rounded-full px-3 py-1">
                  <span className="text-[10px] font-bold uppercase text-slate-600">Cumplimiento:</span>
                  <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div className="h-full bg-lgc-accent" style={{ width: `${cumplimientoTotal}%` }}></div>
                  </div>
                  <span className="text-xs font-bold text-lgc-accent">{cumplimientoTotal}%</span>
                </div>
             )}
             <div className="text-[10px] print:text-[8px] font-bold text-slate-400 uppercase tracking-widest mb-1">Emitido por</div>
             <img src="/logo_lgc.png" alt="Lamas Global Consulting" className="h-10 print:h-6 w-auto opacity-80" onError={(e) => e.currentTarget.style.display = 'none'} />
          </div>
        </div>

        {/* CUERPO DE LA MATRIZ: Tabla con scroll horizontal */}
        <div className="p-0 overflow-x-auto scrollbar-thin">
          <table className="w-full text-left border-collapse table-auto print:table-fixed print:text-[8px] min-w-max">
            <thead className="bg-slate-50 print:bg-slate-100 sticky top-0 z-10 border-b border-slate-200 print:table-header-group">
              <tr>
                <th className="p-4 print:p-2 text-[10px] print:text-[7px] font-bold text-slate-600 uppercase tracking-wider border-r border-slate-200 w-10 text-center">#</th>
                {config.map((col: any) => (
                  <th key={col.id} className="p-4 print:p-2 text-[10px] print:text-[7px] font-bold text-slate-600 uppercase tracking-wider border-r border-slate-200 whitespace-nowrap">
                    {col.label || COLUMN_LABELS[col.id] || col.id}
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
                    <td className="p-4 print:p-2 font-bold text-slate-400 print:text-slate-600 border-r border-slate-50 print:border-slate-200 text-center">{idx+1}</td>
                    {config.map((col: any) => (
                      <td key={col.id} className="p-4 print:p-2 align-top text-slate-700 leading-relaxed border-r border-slate-50 print:border-slate-200 whitespace-normal wrap-break-word min-w-30 max-w-75">
                        {renderContent(item, col.id)}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* PIE DE PÁGINA (solo impresión) */}
        <div className="p-8 print:p-4 bg-slate-50 print:bg-white border-t border-slate-100 print:border-slate-300 mt-10 print:mt-0 hidden print:block">
           <div className="flex justify-between text-[10px] print:text-[8px] font-bold text-slate-500 uppercase">
              <span>© {new Date().getFullYear()} Lamas Global Consulting</span>
           </div>
        </div>
      </div>
    </div>
  );
}