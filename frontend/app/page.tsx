"use client";

import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import Image from 'next/image';

interface Cliente {
  id_cliente: number;
  nombre_fantasia: string;
  razon_social: string;
}

export default function Login() {
  const router = useRouter();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const [pasoSeleccion, setPasoSeleccion] = useState(false);
  const [clientesDisponibles, setClientesDisponibles] = useState<Cliente[]>([]);
  const [tokenTemporal, setTokenTemporal] = useState('');
  
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Escuchar si venimos de apretar "Cambiar Empresa"
  useEffect(() => {
    const isChanging = localStorage.getItem("sgml_change_env");
    if (isChanging === "true") {
      const storedClients = localStorage.getItem("sgml_mis_clientes");
      const existingToken = localStorage.getItem("sgml_token");
      
      if (storedClients && existingToken) {
        setClientesDisponibles(JSON.parse(storedClients));
        setTokenTemporal(existingToken);
        setPasoSeleccion(true);
        localStorage.removeItem("sgml_change_env");
      }
    }
  }, []);

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

      if (data.requiere_seleccion) {
        setTokenTemporal(data.token_temporal);
        setClientesDisponibles(data.clientes);
        
        // Guardamos las empresas temporalmente por si luego quiere cambiar de entorno
        localStorage.setItem('sgml_mis_clientes', JSON.stringify(data.clientes));
        
        setPasoSeleccion(true);
        setLoading(false);
        return;
      }

      guardarDatosYRedirigir(data);
      
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleSelectCliente = async (idCliente: number) => {
    setError('');
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/seleccionar_cliente.php`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokenTemporal}`
        },
        body: JSON.stringify({ id_cliente: idCliente }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.mensaje || 'Error al seleccionar el entorno');
      }

      guardarDatosYRedirigir(data);

    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  const guardarDatosYRedirigir = (data: any) => {
      localStorage.removeItem('sgml_token');
      localStorage.removeItem('sgml_usuario');
      localStorage.removeItem('sgml_permisos');
      localStorage.removeItem('sgml_cliente_id');

      localStorage.setItem('sgml_token', data.token);
      
      if (data.clientes) {
          localStorage.setItem('sgml_mis_clientes', JSON.stringify(data.clientes));
      }

      if (data.usuario) {
          localStorage.setItem('sgml_usuario', JSON.stringify(data.usuario));
          localStorage.setItem('sgml_cliente_id', data.usuario.id_cliente ?? 'null');
      }
      
      if (data.permisos) {
          localStorage.setItem('sgml_permisos', JSON.stringify(data.permisos));
      }

      router.push('/dashboard');
  };

  const volverAlLogin = () => {
    setPasoSeleccion(false);
    setTokenTemporal('');
    setClientesDisponibles([]);
    setError('');
    localStorage.removeItem('sgml_token');
  };

  const highlightInitials = (text: string) => {
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

      <div className="relative z-10 bg-lgc-tostado/40 backdrop-blur-md rounded-4xl shadow-2xl max-w-3xl w-full border border-white/30 flex flex-col md:flex-row overflow-hidden animate-fade-in">
        
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

        <div className="w-full md:w-7/12 p-8 md:p-12 flex flex-col justify-center bg-lgc-primary/9">
          
          <div className="text-center md:text-left mb-8">
            <h1 
              className="text-2xl lg:text-3xl font-heading text-white drop-shadow-md leading-tight"
              dangerouslySetInnerHTML={{ __html: tituloHTML }}
            />
            <p className="text-white/80 mt-3 text-sm lg:text-base uppercase tracking-widest font-bold flex items-center justify-center md:justify-start gap-2">
              <span className="w-8 h-px bg-white/50 inline-block"></span>
              {pasoSeleccion ? "Seleccione un Entorno" : "Acceso a Usuarios"}
            </p>
          </div>

          {error && (
            <div aria-live="polite" className="bg-red-500/20 backdrop-blur-sm text-white p-4 rounded-xl text-sm border border-red-500/50 text-center font-bold tracking-widest shadow-inner animate-fade-in mb-5">
              {error}
            </div>
          )}

          {!pasoSeleccion ? (
            <form onSubmit={handleSubmit} className="space-y-5">
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
          ) : (
            <div className="space-y-4 animate-fade-in max-h-80 overflow-y-auto pr-2 custom-scrollbar">
               {clientesDisponibles.map((cliente) => (
                 <button
                   key={cliente.id_cliente}
                   onClick={() => handleSelectCliente(cliente.id_cliente)}
                   disabled={loading}
                   className="group relative flex flex-col p-5 bg-[#00455E] rounded-2xl border border-[#005A7A] shadow-[0_4px_10px_rgba(0,34,48,0.45)] hover:shadow-[0_6px_14px_rgba(0,34,48,0.65)] hover:bg-[#00384D] hover:-translate-y-0.5 transition-all duration-300 overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-lgc-primary w-full text-left disabled:opacity-70 disabled:cursor-not-allowed"
                 >
                   <div className="flex items-start gap-4 mb-3 w-full">
                     <div className="w-11 h-11 rounded-xl flex items-center justify-center bg-white/10 text-white/70 group-hover:bg-lgc-accent/20 group-hover:text-lgc-accent transition-all duration-300 shrink-0 border border-white/5 group-hover:border-lgc-accent/30 shadow-inner group-hover:scale-110 font-black text-lg">
                       {(cliente.nombre_fantasia || cliente.razon_social).substring(0,2).toUpperCase()}
                     </div>
                     <div className="flex-1 mt-0.5 min-w-0">
                       <h2 className="text-base font-heading font-black text-white leading-tight uppercase tracking-tight truncate">
                         {cliente.nombre_fantasia || cliente.razon_social}
                       </h2>
                       <p className="text-[10px] text-[#A8D3E0] leading-relaxed font-medium group-hover:text-white transition-colors duration-300 truncate mt-1 uppercase tracking-widest">
                         {cliente.razon_social}
                       </p>
                     </div>
                   </div>
                   
                   <div className="flex justify-end pt-2.5 border-t border-white/10 w-full">
                     <span className="text-white/30 group-hover:text-lgc-accent transition-colors duration-300 transform group-hover:translate-x-1 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest">
                       Acceder al entorno
                       <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                         <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 12h14m-4-4l4 4-4 4" />
                       </svg>
                     </span>
                   </div>
                 </button>
               ))}
               
               <div className="pt-4 text-center">
                 <button onClick={volverAlLogin} disabled={loading} className="text-xs text-white/70 hover:text-white font-bold uppercase tracking-widest transition-colors underline">
                    ← Volver atrás
                 </button>
               </div>
            </div>
          )}
        </div>

      </div>
    </main>
  );
}