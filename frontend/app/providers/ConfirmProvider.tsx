"use client";

import { createContext, useContext, useState, ReactNode, useCallback, useRef, useEffect } from "react";

interface ConfirmOptions {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm?: () => void | Promise<void>;
  onCancel?: () => void;
}

interface ConfirmContextType {
  confirm: (options: ConfirmOptions | string) => Promise<boolean>;
}

const ConfirmContext = createContext<ConfirmContextType | undefined>(undefined);

export const useConfirm = () => {
  const context = useContext(ConfirmContext);
  if (!context) throw new Error("useConfirm must be used within ConfirmProvider");
  return context.confirm;
};

const ConfirmModal = ({
  isOpen,
  title,
  message,
  confirmText,
  cancelText,
  onConfirm,
  onCancel,
  onClose,
}: {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText: string;
  cancelText: string;
  onConfirm: () => void;
  onCancel: () => void;
  onClose: () => void;
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [swipeX, setSwipeX] = useState(0);
  const touchStartX = useRef<number | null>(null);

  useEffect(() => {
    if (!isOpen) setSwipeX(0);
  }, [isOpen]);

  const handleConfirm = async () => {
    setIsLoading(true);
    await onConfirm();
    setIsLoading(false);
    onClose();
  };

  const handleCancel = () => {
    onCancel();
    onClose();
  };

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
      handleCancel();
    } else {
      setSwipeX(0);
    }
    touchStartX.current = null;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div
        className={`bg-slate-800 rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.3)] w-full max-w-md transition-transform duration-300 ${
          swipeX === 0 ? '' : 'translate-x-0'
        }`}
        style={{ transform: swipeX !== 0 ? `translateX(${swipeX}px)` : 'translateX(0)' }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <div className="p-5 border-b border-slate-700">
          <h3 className="text-lg font-bold text-white">{title}</h3>
        </div>
        <div className="p-5">
          <p className="text-slate-300 text-sm">{message}</p>
        </div>
        <div className="flex justify-end gap-3 p-5 pt-0">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-xs font-bold uppercase text-slate-400 hover:text-white transition-colors"
          >
            {cancelText}
          </button>
          <button
            onClick={handleConfirm}
            disabled={isLoading}
            className="px-5 py-2 bg-lgc-accent hover:bg-[#D97920] text-white font-bold rounded-lg uppercase text-xs shadow-md transition-colors disabled:opacity-50"
          >
            {isLoading ? "..." : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export const ConfirmProvider = ({ children }: { children: ReactNode }) => {
  const [modalState, setModalState] = useState<{
    isOpen: boolean;
    resolve?: (value: boolean) => void;
    options: ConfirmOptions;
  }>({
    isOpen: false,
    options: { title: "Confirmar", message: "", confirmText: "Aceptar", cancelText: "Cancelar" },
  });

  const confirm = useCallback((options: ConfirmOptions | string): Promise<boolean> => {
    return new Promise((resolve) => {
      const opts = typeof options === "string" 
        ? { message: options, title: "Confirmar", confirmText: "Aceptar", cancelText: "Cancelar" }
        : { title: "Confirmar", confirmText: "Aceptar", cancelText: "Cancelar", ...options };
      
      setModalState({
        isOpen: true,
        resolve,
        options: opts,
      });
    });
  }, []);

  const handleConfirm = async () => {
    if (modalState.resolve) {
      if (modalState.options.onConfirm) await modalState.options.onConfirm();
      modalState.resolve(true);
    }
    setModalState(prev => ({ ...prev, isOpen: false }));
  };

  const handleCancel = () => {
    if (modalState.resolve) {
      if (modalState.options.onCancel) modalState.options.onCancel();
      modalState.resolve(false);
    }
    setModalState(prev => ({ ...prev, isOpen: false }));
  };

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      <ConfirmModal
        isOpen={modalState.isOpen}
        title={modalState.options.title || "Confirmar"}
        message={modalState.options.message}
        confirmText={modalState.options.confirmText || "Aceptar"}
        cancelText={modalState.options.cancelText || "Cancelar"}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
        onClose={() => setModalState(prev => ({ ...prev, isOpen: false }))}
      />
    </ConfirmContext.Provider>
  );
};