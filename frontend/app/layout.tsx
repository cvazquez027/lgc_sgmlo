// Archivo: frontend/app/layout.tsx
import type { Metadata } from "next";
import "./globals.css";
import { ToastProvider } from "./providers/ToastProvider";
import { ConfirmProvider } from "./providers/ConfirmProvider";

export const metadata: Metadata = {
  title: "Sistema de Gestión de Matrices Legales Online - Lamas Global Consulting",
  description: "Sistema de Gestión de Matrices Legales Online",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      {/* El body aplica nuestro color de fondo corporativo y el color de texto por defecto */}
      <body className="bg-slate-50 text-slate-800 antialiased font-sans">
        <ConfirmProvider><ToastProvider>{children}</ToastProvider></ConfirmProvider>
      </body>
    </html>
  );
}