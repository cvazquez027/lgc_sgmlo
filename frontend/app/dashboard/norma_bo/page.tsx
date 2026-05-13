"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { usePermissions } from "../../hooks/usePermissions";
import Link from "next/link";

interface Jurisdiccion {
  id_jurisdiccion: number;
  descripcion: string;
  url_boletin: string | null;
  tiene_scraper: number;
}

interface NormaScraping {
  id_norma_bo: number;
  id_estado_norma: number;
  numero: string;
  anio: number;
  fecha_publicacion: string;
  sintesis: string;
  url_norma: string;
  tipo_norma_desc: string;
  emisor_desc: string;
  jurisdiccion_desc: string;
  categorias_detectadas: string | null;
}

export default function BoletinOficialPage() {
  const { canRead, canEdit } = usePermissions();
  const [isCheckingPerms, setIsCheckingPerms] = useState(true);

  // Datos
  const [jurisdicciones, setJurisdicciones] = useState<Jurisdiccion[]>([]);
  const [normasScraping, setNormasScraping] = useState<NormaScraping[]>([]);
  
  // Filtros
  const [selectedJurId, setSelectedJurId] = useState<string>("");
  const [soloCategorizadas, setSoloCategorizadas] = useState<boolean>(false);
  
  // Paginación
  const [itemsPerPage, setItemsPerPage] = useState<number>(30);
  const [currentPage, setCurrentPage] = useState<number>(1);
  
  // Selección múltiple
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // Estados UI
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [loadingData, setLoadingData] = useState(false);
  const [procesando, setProcesando] = useState<boolean>(false);
  const [isScraping, setIsScraping] = useState<boolean>(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsCheckingPerms(false), 100);
    return () => clearTimeout(timer);
  }, []);

  // 1. Cargar el selector de Jurisdicciones
  const fetchJurisdicciones = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/jurisdicciones/leer.php?niveles=1,2`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      setJurisdicciones(data.registros || []);
    } catch (err) {
      console.error("Error cargando jurisdicciones", err);
    } finally {
      setLoadingConfig(false);
    }
  }, []);

  // 2. Traer los datos del scraping (Grilla completa)
  const fetchScrapingData = useCallback(async () => {
    const token = localStorage.getItem("sgml_token");
    setLoadingData(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/boletin/leer_scraping.php`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      setNormasScraping(data.registros || []);
      setSelectedIds([]);
    } catch (error) {
      console.error("Error trayendo scraping", error);
    } finally {
      setLoadingData(false);
    }
  }, []);

  useEffect(() => {
    if (!isCheckingPerms && canRead("boletin")) {
      fetchJurisdicciones();
      fetchScrapingData();
    }
  }, [fetchJurisdicciones, fetchScrapingData, isCheckingPerms, canRead]);

  // Identificar la jurisdicción seleccionada para lógica de UI
  const selectedJur = useMemo(() => 
    jurisdicciones.find(j => j.id_jurisdiccion.toString() === selectedJurId), 
  [jurisdicciones, selectedJurId]);

  // Filtrado dinámico
  const normasFiltradas = useMemo(() => {
    return normasScraping.filter(norma => {
      const matchJur = selectedJurId === "" || norma.jurisdiccion_desc === selectedJur?.descripcion;
      const matchCat = !soloCategorizadas || (norma.categorias_detectadas && norma.categorias_detectadas.trim() !== "");
      return matchJur && matchCat;
    });
  }, [normasScraping, selectedJurId, soloCategorizadas, selectedJur]);

  // Paginación
  const totalPages = Math.ceil(normasFiltradas.length / itemsPerPage);
  const paginatedNormas = normasFiltradas.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  useEffect(() => {
    setCurrentPage(1);
    setSelectedIds([]);
  }, [selectedJurId, soloCategorizadas, itemsPerPage]);

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedIds(paginatedNormas.map(n => n.id_norma_bo));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectOne = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  // 3. Ejecutar el script de Python en el Backend
  const ejecutarScraper = async () => {
    setIsScraping(true);
    const token = localStorage.getItem("sgml_token");
    
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/boletin/ejecutar_scraper.php`, {
        method: 'POST',
        headers: { "Authorization": `Bearer ${token}` }
      });
      
      // 1. En lugar de .json(), pedimos el texto crudo
      const rawText = await res.text();
      
      // 2. Lo imprimimos en la consola para ver qué dice REALMENTE PHP
      console.log("Respuesta cruda de PHP:", rawText);
      
      // 3. Ahora sí intentamos convertirlo a JSON
      try {
          const data = JSON.parse(rawText);
          
          if (data.status === 'success') {
            alert('¡Boletín actualizado con éxito!');
            fetchScrapingData();
          } else {
            alert('Error al raspar: ' + data.message);
            console.error("Log de Python:", data.log);
          }
      } catch (parseError) {
          console.error("No se pudo leer el JSON. El servidor devolvió esto:", rawText);
          alert('Error del servidor: PHP no devolvió un JSON válido. Revisá la consola (F12).');
      }

    } catch (error) {
      console.error("Error conectando con el backend:", error);
      alert('Ocurrió un error al intentar actualizar.');
    } finally {
      setIsScraping(false);
    }
  };

  const handleBulkAction = async (accion: 'promover' | 'descartar') => {
    if (!canEdit("boletin") || selectedIds.length === 0) return;
    
    const confirmMsg = accion === 'descartar' 
      ? `¿Estás seguro de DESCARTAR las ${selectedIds.length} normas seleccionadas?`
      : `¿Promover ${selectedIds.length} normas al repositorio oficial?`;
    
    if (!window.confirm(confirmMsg)) return;

    setProcesando(true);
    const token = localStorage.getItem("sgml_token");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/boletin/procesar_scraping.php`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ ids_normas: selectedIds, accion })
      });
      
      if (res.ok) {
        setNormasScraping(prev => prev.filter(n => !selectedIds.includes(n.id_norma_bo)));
        setSelectedIds([]);
      } else {
        const data = await res.json();
        alert("Error: " + data.mensaje);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setProcesando(false);
    }
  };

  if (isCheckingPerms) return <div className="py-20 text-center text-lgc-primary animate-pulse">Verificando accesos...</div>;
  if (!canRead("boletin")) return <div className="py-32 text-center text-red-500 font-bold text-2xl">Acceso Denegado</div>;

  return (
    <div className="space-y-2 font-sans animate-fade-in flex flex-col h-[calc(100vh-80px)] overflow-hidden">
      
      {/* HEADER COMPACTO */}
      <div className="bg-white px-4 py-2 rounded-xl shadow-sm border border-slate-200 flex flex-row justify-between items-center shrink-0">
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
          <h1 className="text-xl font-heading text-lgc-primary uppercase tracking-tight">BOLETINES OFICIALES</h1>
        </div>
        <div className="flex items-center gap-4">
          
          {/* NUEVO BOTÓN: Solo se muestra si la jurisdicción seleccionada tiene el flag "tiene_scraper" en 1 */}
          {selectedJur && selectedJur.tiene_scraper === 1 && (
            <button 
              onClick={ejecutarScraper} 
              disabled={isScraping}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold uppercase transition-colors shadow-sm border ${
                isScraping 
                  ? 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed' 
                  : 'bg-blue-600 text-white border-blue-700 hover:bg-blue-700'
              }`}
            >
              {isScraping ? (
                <>
                  <svg className="animate-spin h-3.5 w-3.5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  Actualizando...
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                  Actualizar
                </>
              )}
            </button>
          )}

          <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-orange-700 bg-orange-50 px-3 py-1.5 rounded-lg border border-orange-200 hover:bg-orange-100 transition-colors">
            <input 
              type="checkbox" 
              checked={soloCategorizadas} 
              onChange={(e) => setSoloCategorizadas(e.target.checked)}
              className="rounded text-orange-500 focus:ring-orange-500 w-3.5 h-3.5"
            />
            <span>SOLO RELEVANTES</span>
          </label>

          <select 
            className="p-1.5 bg-slate-50 border border-slate-300 rounded-lg outline-none text-xs font-bold text-slate-700 cursor-pointer shadow-sm min-w-50"
            value={selectedJurId}
            onChange={(e) => setSelectedJurId(e.target.value)}
            disabled={loadingConfig}
          >
            <option value="">TODAS LAS JURISDICCIONES</option>
            {jurisdicciones.map(j => (
              <option key={j.id_jurisdiccion} value={j.id_jurisdiccion}>{j.descripcion}</option>
            ))}
          </select>
        </div>
      </div>

      {/* TOOLBAR */}
      <div className="bg-slate-100 p-2 rounded-xl flex justify-between items-center shrink-0 border border-slate-200">
        <div className="flex items-center gap-4 px-2 text-[11px]">
          <span className="font-bold text-slate-600">{normasFiltradas.length} REGISTROS</span>
          <span className="text-slate-400">|</span>
          <span className={selectedIds.length > 0 ? "text-lgc-primary font-bold" : "text-slate-500"}>
            {selectedIds.length} SELECCIONADOS
          </span>
        </div>

        <div className="flex gap-2">
          <button 
            onClick={() => handleBulkAction('descartar')}
            disabled={procesando || selectedIds.length === 0}
            className="bg-white hover:bg-red-50 text-slate-600 hover:text-red-600 border border-slate-300 py-1 px-3 rounded shadow-sm text-[10px] font-bold uppercase transition-all disabled:opacity-50"
          >
            Descartar
          </button>
          <button 
            onClick={() => handleBulkAction('promover')}
            disabled={procesando || selectedIds.length === 0}
            className="bg-lgc-primary hover:bg-lgc-hover text-white py-1 px-3 rounded shadow-sm text-[10px] font-bold uppercase transition-all disabled:opacity-50"
          >
            {procesando ? 'Procesando...' : 'Confirmar y Promover'}
          </button>
        </div>
      </div>

      {/* DATAGRID */}
      <div className="flex-1 bg-white rounded-xl shadow-sm border border-slate-200 overflow-auto relative">
        {loadingData ? (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-20">
            <span className="text-slate-500 font-bold text-xs tracking-widest uppercase animate-pulse">Cargando datos...</span>
          </div>
        ) : paginatedNormas.length === 0 ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 gap-4">
            <span className="text-xs font-bold uppercase">No hay normativas pendientes</span>
            {/* BOTÓN PARA JURISDICCIONES SIN SCRAPER */}
            {selectedJur && selectedJur.tiene_scraper === 0 && selectedJur.url_boletin && (
              <a 
                href={selectedJur.url_boletin} 
                target="_blank" 
                rel="noopener noreferrer"
                className="bg-lgc-primary hover:bg-lgc-hover text-white py-2 px-4 rounded-lg shadow-sm text-[10px] font-bold uppercase transition-all flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                Ver el Boletín Oficial
              </a>
            )}
          </div>
        ) : (
          <table className="w-full text-left border-collapse text-[11px]">
            <thead className="bg-slate-50 sticky top-0 z-10 border-b border-slate-200">
              <tr>
                <th className="py-2 px-3 w-8 text-center">
                  <input 
                    type="checkbox" 
                    className="rounded text-lgc-primary w-3 h-3 cursor-pointer"
                    checked={paginatedNormas.length > 0 && selectedIds.length === paginatedNormas.length}
                    onChange={handleSelectAll}
                  />
                </th>
                <th className="py-2 px-2 font-bold text-slate-500 uppercase w-20">Jurisdicción</th>
                <th className="py-2 px-2 font-bold text-slate-500 uppercase w-24">Tipo / Nro</th>
                <th className="py-2 px-2 font-bold text-slate-500 uppercase w-32">Emisor</th>
                <th className="py-2 px-2 font-bold text-slate-500 uppercase w-16">Fecha</th>
                <th className="py-2 px-2 font-bold text-slate-500 uppercase">Síntesis</th>
                <th className="py-2 px-2 font-bold text-slate-500 uppercase w-40">Categorías</th>
                <th className="py-2 px-2 font-bold text-slate-500 uppercase w-12 text-center">Ver</th>
                <th className="py-2 px-2 font-bold text-slate-500 uppercase w-16 text-center">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {paginatedNormas.map(norma => {
                const isSelected = selectedIds.includes(norma.id_norma_bo);
                const hasMatch = norma.categorias_detectadas && norma.categorias_detectadas.trim() !== "";
                
                return (
                  <tr 
                    key={norma.id_norma_bo} 
                    className={`
                      transition-colors 
                      ${isSelected ? 'bg-blue-50' : hasMatch ? 'bg-orange-400/5' : 'hover:bg-slate-50'}
                    `}
                  >
                    <td className="py-1.5 px-3 text-center">
                      <input 
                        type="checkbox" 
                        className="rounded text-lgc-primary w-3 h-3 cursor-pointer"
                        checked={isSelected}
                        onChange={() => handleSelectOne(norma.id_norma_bo)}
                      />
                    </td>
                    <td className="py-1.5 px-2 font-bold text-slate-700 uppercase">{norma.jurisdiccion_desc}</td>
                    <td className="py-1.5 px-2 font-medium">
                      <span className="text-slate-900">{norma.tipo_norma_desc}</span><br/>
                      <span className="text-slate-400">N° {norma.numero}/{norma.anio}</span>
                    </td>
                    <td className="py-1.5 px-2 text-slate-500 italic truncate max-w-30" title={norma.emisor_desc}>
                      {norma.emisor_desc}
                    </td>
                    <td className="py-1.5 px-2 whitespace-nowrap text-slate-500">
                      {norma.fecha_publicacion ? norma.fecha_publicacion.split(' ')[0].split('-').reverse().join('/') : ''}
                    </td>
                    <td className="py-1.5 px-2 text-slate-600 leading-tight">
                      <div className="line-clamp-2 hover:line-clamp-none transition-all cursor-default">
                        {norma.sintesis}
                      </div>
                    </td>
                    <td className="py-1.5 px-2">
                      <div className="flex flex-wrap gap-1">
                        {norma.categorias_detectadas?.split(',').map((cat, idx) => (
                          <span key={idx} className="bg-slate-100 text-slate-600 border border-slate-200 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase">
                            {cat.trim()}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-1.5 px-2 text-center">
                      {norma.url_norma && (
                        <a href={norma.url_norma} target="_blank" rel="noopener noreferrer" className="text-lgc-primary hover:text-lgc-hover inline-block">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                        </a>
                      )}
                    </td>
                    <td className="py-1.5 px-2 text-center">
                      <span className={`font-bold px-2 py-0.5 rounded text-[9px] ${norma.id_estado_norma === 1 ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                        {norma.id_estado_norma === 1 ? 'VIGENTE' : 'OTRO'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* PAGINADOR */}
      <div className="bg-white px-4 py-2 rounded-xl shadow-sm border border-slate-200 flex justify-between items-center shrink-0 text-[11px]">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-bold uppercase">Mostrar</span>
          <select 
            className="border border-slate-300 rounded p-0.5 text-slate-700 outline-none focus:border-lgc-primary font-bold"
            value={itemsPerPage}
            onChange={(e) => setItemsPerPage(Number(e.target.value))}
          >
            <option value={10}>10</option>
            <option value={30}>30</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>

        <div className="flex items-center gap-6">
          <span className="text-slate-500 font-bold uppercase">
            PÁGINA {currentPage} DE {totalPages || 1}
          </span>
          <div className="flex gap-1">
            <button 
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-4 py-1 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-30 transition-colors font-bold uppercase"
            >
              Ant
            </button>
            <button 
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages || totalPages === 0}
              className="px-4 py-1 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-30 transition-colors font-bold uppercase"
            >
              Sig
            </button>
          </div>
        </div>
      </div>

    </div>
  );
}