"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function ReportesPage() {
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    setIsReady(true);
  }, []);

  return (
    <div className={`flex flex-col h-[calc(100vh-100px)] animate-fade-in overflow-hidden ${isReady ? 'opacity-100' : 'opacity-0'}`}>
      
      {/* HEADER AZUL (ESTILO MATRICES) */}
      <div className="bg-lgc-primary px-6 py-4 rounded-xl shadow-md flex justify-between items-center shrink-0 border border-lgc-primary mb-4">
        <div className="flex items-center gap-5">
          <button 
            onClick={() => router.push("/dashboard")} 
            className="text-white hover:text-white transition-colors bg-white/10 hover:bg-white/20 p-2.5 rounded-xl border border-white/20 shadow-inner"
            title="Volver al inicio"
          >
             <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
             </svg>
          </button>
          <div className="flex flex-col">
            <h1 className="text-xl font-heading text-white uppercase tracking-tight">REPORTES Y ALERTAS</h1>
            <p className="text-white/70 text-[10px] font-bold tracking-widest uppercase mt-0.5">Centro de control y seguimiento</p>
          </div>
        </div>
      </div>

      {/* CONTENIDO PRINCIPAL (Centrado y sin scroll) */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 flex flex-col items-center justify-center text-center max-w-lg w-full">
          <div className="w-20 h-20 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mb-6">
            <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          
          <h2 className="text-xl font-bold text-slate-800 mb-2">
            Sección en Desarrollo
          </h2>
          <p className="text-slate-500 leading-relaxed mb-8">
            Estamos trabajando para integrar tu centro de control. Próximamente podrás visualizar aquí todos los reportes, alertas críticas y métricas de cumplimiento de tu matriz legal.
          </p>
          
          <div className="px-6 py-2 bg-amber-50 text-amber-700 text-xs font-bold uppercase tracking-widest rounded-full border border-amber-200">
            Versión de pre-visualización
          </div>
        </div>
      </div>
      
    </div>
  );
}