"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link"; // Importamos Link para la navegación

export default function MiPerfilPage() {
  const router = useRouter();
  
  const [formData, setFormData] = useState({
    nombre: "",
    apellido: "", 
    email: "",
    password: "",
    confirmPassword: ""
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });

  const [showToast, setShowToast] = useState(false);
  const [swipeX, setSwipeX] = useState(0);
  const touchStartX = useRef<number | null>(null);

  useEffect(() => {
    if (showToast) {
      const timer = setTimeout(() => {
        cerrarToastYRedirigir();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [showToast]);

  const cerrarToastYRedirigir = () => {
    setShowToast(false);
    setTimeout(() => {
      router.push('/dashboard');
    }, 300);
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
      cerrarToastYRedirigir();
    } else {
      setSwipeX(0);
    }
    touchStartX.current = null;
  };

  useEffect(() => {
    cargarPerfil();
  }, []);

  const cargarPerfil = async () => {
    const token = localStorage.getItem("sgml_token");
    if (!token) {
      setMensaje({ tipo: "error", texto: "Sesión expirada. Por favor, reingrese." });
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/usuarios/leer_perfil.php`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      
      const data = await res.json();
      
      if (data.status === "success") {
        setFormData(prev => ({
          ...prev,
          nombre: data.data.nombre || "",
          apellido: data.data.apellido || "",
          email: data.data.email || ""
        }));
      } else {
        setMensaje({ tipo: "error", texto: data.message });
      }
    } catch (error) {
      console.error("Error al cargar perfil:", error);
      setMensaje({ tipo: "error", texto: "No se pudo conectar con el servidor." });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMensaje({ tipo: "", texto: "" });

    if (formData.password && formData.password !== formData.confirmPassword) {
      setMensaje({ tipo: "error", texto: "Las contraseñas no coinciden." });
      return;
    }

    setSaving(true);
    const token = localStorage.getItem("sgml_token");

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/usuarios/actualizar_perfil.php`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}` 
        },
        body: JSON.stringify({
          nombre: formData.nombre,
          apellido: formData.apellido,
          email: formData.email,
          password: formData.password
        })
      });
      
      const data = await res.json();
      
      if (data.status === "success") {
        setShowToast(true);
        setFormData(prev => ({ ...prev, password: "", confirmPassword: "" }));
      } else {
        setMensaje({ tipo: "error", texto: data.message || "Error al actualizar." });
      }
    } catch (error) {
      setMensaje({ tipo: "error", texto: "Error de conexión con el servidor." });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="py-20 text-center text-lgc-accent animate-pulse font-bold">Cargando perfil...</div>;

  return (
    <div className="h-[calc(100vh-80px)] flex items-center justify-center animate-fade-in px-4">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden w-full max-w-3xl">
        
        {/* CABECERA ACCENT */}
        <div className="bg-lgc-accent p-5 text-white flex items-center gap-4">
          <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center text-xl font-bold uppercase shadow-inner shrink-0">
            {formData.nombre ? formData.nombre.charAt(0) : "U"}
          </div>
          <div>
            <h1 className="text-xl font-heading font-bold leading-tight">Mi Perfil</h1>
            <p className="text-white/80 text-xs">Gestioná tus datos personales</p>
          </div>
          <Link 
            href="/dashboard" 
            className="ml-auto flex items-center justify-center w-9 h-9 rounded-full bg-white/10 text-white/70 hover:bg-white/20 hover:text-white transition-all group"
            title="Volver al inicio"
          >
            <svg className="w-5 h-5 transition-transform group-hover:-translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
        </div>

        <form onSubmit={handleSubmit} className="p-5 md:p-6">
          {mensaje.texto && mensaje.tipo === 'error' && (
            <div className="mb-4 p-3 rounded-lg text-sm font-bold border bg-red-50 text-red-700 border-red-200">
              {mensaje.texto}
            </div>
          )}

          {/* DOS COLUMNAS EN DESKTOP, UNA EN MOBILE */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-0">

            {/* COLUMNA IZQUIERDA: Datos personales */}
            <div className="space-y-3">
              <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 pb-2 mb-3">Datos Personales</h2>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Nombre</label>
                <input type="text" name="nombre" value={formData.nombre} onChange={handleChange} required
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg outline-none text-slate-700 text-sm focus:border-lgc-accent transition-colors" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Apellido</label>
                <input type="text" name="apellido" value={formData.apellido} onChange={handleChange} required
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg outline-none text-slate-700 text-sm focus:border-lgc-accent transition-colors" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Email</label>
                <input type="email" name="email" value={formData.email} onChange={handleChange} required
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg outline-none text-slate-700 text-sm focus:border-lgc-accent transition-colors" />
              </div>
            </div>

            {/* COLUMNA DERECHA: Seguridad */}
            <div className="space-y-3 mt-5 md:mt-0">
              <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 pb-2 mb-3">Seguridad</h2>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Nueva Clave</label>
                <input type="password" name="password" value={formData.password} onChange={handleChange} placeholder="Dejar en blanco para no cambiar"
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg outline-none text-slate-700 text-sm focus:border-lgc-accent transition-colors" />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Confirmar Clave</label>
                <input type="password" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} placeholder="Repetir nueva clave"
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg outline-none text-slate-700 text-sm focus:border-lgc-accent transition-colors" />
              </div>
              <p className="text-[10px] text-slate-400 leading-relaxed pt-1">
                Si no querés cambiar tu contraseña, dejá los campos en blanco. La clave actual seguirá siendo válida.
              </p>
            </div>

          </div>

          <div className="pt-5 flex justify-end border-t border-slate-100 mt-5">
            <button type="submit" disabled={saving || showToast}
              className="bg-lgc-accent hover:bg-[#7A8A1E] text-white font-bold py-2.5 px-8 rounded-lg shadow-md transition-all disabled:opacity-50 text-sm uppercase tracking-widest">
              {saving ? 'Guardando...' : 'Guardar Cambios'}
            </button>
          </div>
        </form>
      </div>

      <div
        className={`fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-50 transition-all duration-300 ease-out ${
          showToast ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10 pointer-events-none"
        }`}
      >
        <div 
          className={`bg-slate-800 text-white px-5 py-4 rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.3)] flex items-center gap-4 w-[calc(100vw-2rem)] sm:w-auto max-w-sm ${swipeX === 0 ? 'transition-transform duration-300' : ''}`}
          style={{ transform: swipeX !== 0 ? `translateX(${swipeX}px)` : 'translateX(0)' }}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          <div className="bg-green-500/20 text-green-400 p-2 rounded-full shrink-0">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          
          <div className="pr-2">
            <p className="text-sm font-bold text-white">¡Éxito!</p>
            <p className="text-xs text-slate-300 mt-0.5">Perfil actualizado correctamente.</p>
          </div>
          
          <button
            onClick={cerrarToastYRedirigir}
            className="ml-auto text-slate-400 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-lg shrink-0"
            title="Cerrar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

    </div>
  );
}