"use client";

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import Image from 'next/image';

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/Login.php`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.mensaje || 'Error al iniciar sesión');
      }

      localStorage.removeItem('sgml_token');
      localStorage.removeItem('sgml_usuario');
      localStorage.removeItem('sgml_permisos');
      localStorage.removeItem('sgml_cliente_id');

      localStorage.setItem('sgml_token', data.token);
      
      if (data.usuario) {
          localStorage.setItem('sgml_usuario', JSON.stringify(data.usuario));
          localStorage.setItem('sgml_cliente_id', data.usuario.id_cliente ?? 'null');
      }
      
      if (data.permisos) {
          localStorage.setItem('sgml_permisos', JSON.stringify(data.permisos));
      }

      router.push('/dashboard');
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Función para resaltar las iniciales "S G M L O" con color primary
  const highlightInitials = (text: string) => {
    // Busca la frase "Sistema de Gestión de Matrices Legales Online"
    // y reemplaza las iniciales S G M L O con spans de color
    return text.replace(/\b([S]istema)\s+([G]estión)\s+([M]atrices)\s+([L]egales)\s+([O]nline)\b/i, 
      (match, p1, p2, p3, p4, p5) => {
        return `<span class="text-lgc-primary">S</span>istema de <span class="text-lgc-primary">G</span>estión de <span class="text-lgc-primary">M</span>atrices <span class="text-lgc-primary">L</span>egales <span class="text-lgc-primary">O</span>nline`;
      });
  };

  const tituloHTML = highlightInitials("Sistema de Gestión de Matrices Legales Online");

  return (
    <main 
      className="min-h-screen flex items-center justify-center p-4 lg:p-10 relative overflow-hidden"
      style={{ backgroundImage: "url('/bg_trama.png')", backgroundSize: "cover", backgroundPosition: "center" }}
    >
      <div className="absolute inset-0 bg-slate-900/30 z-0 backdrop-blur-[2px]"></div>

      {/* TARJETA MODAL: ancho reducido al 75% (max-w-5xl → max-w-3xl) */}
      <div className="relative z-10 bg-lgc-tostado/40 backdrop-blur-md rounded-4xl shadow-2xl max-w-3xl w-full border border-white/30 flex flex-col md:flex-row overflow-hidden animate-fade-in">
        
        {/* LADO IZQUIERDO: LOGO (centrado) */}
        <div className="w-full md:w-5/12 p-8 md:p-10 flex items-center justify-center bg-white/5 border-b md:border-b-0 md:border-r border-white/20">
          <Image 
            src="/logo_lgc.png" 
            alt="Lamas Global Consulting Logo" 
            width={220} 
            height={94} 
            className="object-contain drop-shadow-2xl transition-transform hover:scale-105 duration-500"
            priority
          />
        </div>

        {/* LADO DERECHO: FORMULARIO */}
        <div className="w-full md:w-7/12 p-8 md:p-12 flex flex-col justify-center bg-lgc-primary/9">
          
          {/* Encabezados con iniciales coloreadas */}
          <div className="text-center md:text-left mb-8">
            <h1 
              className="text-2xl lg:text-3xl font-heading text-white drop-shadow-md leading-tight"
              dangerouslySetInnerHTML={{ __html: tituloHTML }}
            />
            <p className="text-white/80 mt-3 text-sm lg:text-base uppercase tracking-widest font-bold flex items-center justify-center md:justify-start gap-2">
              <span className="w-8 h-px bg-white/50 inline-block"></span>
              Acceso a Usuarios
            </p>
          </div>

          {/* Formulario */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div aria-live="polite" className="bg-red-500/20 backdrop-blur-sm text-white p-4 rounded-xl text-sm border border-red-500/50 text-center font-bold tracking-widest shadow-inner animate-fade-in">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-xs font-bold uppercase tracking-widest text-white/90 mb-2 drop-shadow-sm ml-1">
                Correo Electrónico
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-5 py-3 bg-white/95 border-2 border-transparent rounded-xl focus:ring-4 focus:ring-white/30 focus:border-white outline-none transition-all text-slate-900 shadow-inner placeholder-slate-400 font-medium"
                placeholder="usuario@lamasglobal.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-bold uppercase tracking-widest text-white/90 mb-2 drop-shadow-sm ml-1">
                Contraseña
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-5 py-3 bg-white/95 border-2 border-transparent rounded-xl focus:ring-4 focus:ring-white/30 focus:border-white outline-none transition-all text-slate-900 shadow-inner placeholder-slate-400 font-medium"
                placeholder="••••••••"
              />
            </div>

            <div className="pt-3">
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-lgc-primary hover:bg-slate-900 text-white font-bold py-3.5 rounded-xl uppercase tracking-[0.2em] text-sm transition-all duration-300 disabled:opacity-70 disabled:cursor-not-allowed shadow-xl hover:shadow-2xl border border-white/10 flex justify-center items-center gap-3"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Validando...
                  </>
                ) : (
                  'Ingresar al Sistema'
                )}
              </button>
            </div>
          </form>
        </div>

      </div>
    </main>
  );
}