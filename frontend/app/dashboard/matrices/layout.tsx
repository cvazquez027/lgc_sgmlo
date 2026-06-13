"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { usePathname } from "next/navigation";

// Definición de tipos
interface FiltrosListado {
  filtroCliente: string;
  filtroEstablecimiento: string;
  filtroEspecialidad: string;
  filtroTipo: string;
  filtroVigente: boolean;
  clientesExpandidos: Set<number>;
}

interface FiltrosWorkspace {
  isFilterOpen: boolean;
  filtros: any; // mismo tipo que el estado `filtros` del workspace
}

interface MatrizFiltersContextType {
  listado: FiltrosListado;
  setListado: (filtros: Partial<FiltrosListado>) => void;
  workspace: FiltrosWorkspace;
  setWorkspace: (filtros: Partial<FiltrosWorkspace>) => void;
  resetAll: () => void;
}

const defaultListado: FiltrosListado = {
  filtroCliente: "",
  filtroEstablecimiento: "",
  filtroEspecialidad: "",
  filtroTipo: "",
  filtroVigente: true,
  clientesExpandidos: new Set(),
};

const defaultWorkspace: FiltrosWorkspace = {
  isFilterOpen: false,
  filtros: {
    norma: { tipo: '', nro: '', anio: '', sintesis: '', emisor: '', nivel: '', jurisdiccion: '', categorias: [] },
    evidencia: '',
    dinamicos: {},
  },
};

const MatrizFiltersContext = createContext<MatrizFiltersContextType | undefined>(undefined);

export function useMatrizFilters() {
  const context = useContext(MatrizFiltersContext);
  if (!context) throw new Error("useMatrizFilters must be used within MatrizFiltersProvider");
  return context;
}

export default function MatricesLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [listado, setListadoState] = useState<FiltrosListado>(defaultListado);
  const [workspace, setWorkspaceState] = useState<FiltrosWorkspace>(defaultWorkspace);

  // Función para actualizar solo las propiedades que cambian
  const setListado = useCallback((partial: Partial<FiltrosListado>) => {
    setListadoState(prev => ({
      ...prev,
      ...partial,
      // clientesExpandidos requiere un tratamiento especial (Set)
      clientesExpandidos: partial.clientesExpandidos !== undefined
        ? new Set(partial.clientesExpandidos)
        : prev.clientesExpandidos,
    }));
  }, []);

  const setWorkspace = useCallback((partial: Partial<FiltrosWorkspace>) => {
    setWorkspaceState(prev => ({
      ...prev,
      ...partial,
    }));
  }, []);

  const resetAll = useCallback(() => {
    setListadoState(defaultListado);
    setWorkspaceState(defaultWorkspace);
  }, []);

  // Limpiar filtros al salir del módulo /dashboard/matrices/*
  useEffect(() => {
    if (!pathname.startsWith("/dashboard/matrices")) {
      resetAll();
    }
  }, [pathname, resetAll]);

  return (
    <MatrizFiltersContext.Provider value={{ listado, setListado, workspace, setWorkspace, resetAll }}>
      {children}
    </MatrizFiltersContext.Provider>
  );
}