"use client";

import { createContext, useContext, useState, useCallback, ReactNode, useRef, useEffect } from "react";

export type ToastType = "success" | "error" | "warning" | "info";

interface ToastData {
  id: number;
  title: string;
  message: string;
  type: ToastType;
  duration?: number; // en milisegundos
}

interface ToastContextType {
  showToast: (title: string, message: string, type?: ToastType, duration?: number) => void;
  hideToast: () => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
};

// Componente Toast interno
const ToastComponent = ({
  title,
  message,
  type,
  onClose,
  duration = 4000,
}: {
  title: string;
  message: string;
  type: ToastType;
  onClose: () => void;
  duration?: number;
}) => {
  const [swipeX, setSwipeX] = useState(0);
  const touchStartX = useRef<number | null>(null);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onClose, 300);
    }, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (touchStartX.current === null) return;
    const diff = e.touches[0].clientX - touchStartX.current;
    setSwipeX(diff);
  };

  const handleTouchEnd = () => {
    if (Math.abs(swipeX) > 75) {
      setIsVisible(false);
      setTimeout(onClose, 300);
    } else {
      setSwipeX(0);
    }
    touchStartX.current = null;
  };

  const getIconByType = () => {
    switch (type) {
      case "success":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        );
      case "error":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      case "warning":
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        );
      default: // info
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const getIconBgClass = () => {
    switch (type) {
      case "success": return "bg-green-500/20 text-green-400";
      case "error": return "bg-red-500/20 text-red-400";
      case "warning": return "bg-amber-500/20 text-amber-400";
      default: return "bg-lgc-primary/20 text-blue-400";
    }
  };

  return (
    <div
      className={`fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-50 transition-all duration-300 ease-out ${
        isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10 pointer-events-none"
      }`}
    >
      <div
        className={`bg-slate-800 text-white px-5 py-4 rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.3)] flex items-center gap-4 w-[calc(100vw-2rem)] sm:w-auto max-w-sm ${
          swipeX === 0 ? "transition-transform duration-300" : ""
        }`}
        style={{ transform: swipeX !== 0 ? `translateX(${swipeX}px)` : "translateX(0)" }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <div className={`p-2 rounded-full shrink-0 ${getIconBgClass()}`}>
          {getIconByType()}
        </div>

        <div className="pr-2">
          <p className="text-sm font-bold text-white">{title}</p>
          <p className="text-xs text-slate-300 mt-0.5">{message}</p>
        </div>

        <button
          onClick={() => {
            setIsVisible(false);
            setTimeout(onClose, 300);
          }}
          className="ml-auto text-slate-400 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-lg shrink-0"
          title="Cerrar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export const ToastProvider = ({ children }: { children: ReactNode }) => {
  const [currentToast, setCurrentToast] = useState<ToastData | null>(null);

  const showToast = useCallback(
    (title: string, message: string, type: ToastType = "info", duration: number = 3000) => {
      setCurrentToast({ id: Date.now(), title, message, type, duration });
    },
    []
  );

  const hideToast = useCallback(() => {
    setCurrentToast(null);
  }, []);

  return (
    <ToastContext.Provider value={{ showToast, hideToast }}>
      {children}
      {currentToast && (
        <ToastComponent
          key={currentToast.id}
          title={currentToast.title}
          message={currentToast.message}
          type={currentToast.type}
          duration={currentToast.duration}
          onClose={hideToast}
        />
      )}
    </ToastContext.Provider>
  );
};