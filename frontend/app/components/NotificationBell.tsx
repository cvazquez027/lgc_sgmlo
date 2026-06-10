"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

export default function NotificationBell() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const fetchCount = async () => {
      const token = localStorage.getItem("sgml_token");
      if (!token) return;

      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/alertas/contador.php`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        
        if (!res.ok) {
          // No hacemos logout, solo registramos el error
          console.error("Error en contador.php (status:", res.status, ")");
          setCount(0);
          return;
        }
        
        const contentType = res.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
          console.error("Respuesta no es JSON en contador.php");
          setCount(0);
          return;
        }
        
        const data = await res.json();
        setCount(data.count || 0);
      } catch (error) {
        console.error("Error fetching alerts count:", error);
        setCount(0);
      }
    };

    fetchCount();
    const interval = setInterval(fetchCount, 300000);
    return () => clearInterval(interval);
  }, []);

  if (count === 0) return null;

  return (
    <Link href="/dashboard/reportes" className="relative inline-flex items-center">
      <svg className="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
      {count > 0 && (
        <span className="absolute -top-1 -right-2 bg-red-500 text-white text-[10px] font-bold rounded-full px-1.5 py-0.5 min-w-4.5 text-center">
          {count > 9 ? "9+" : count}
        </span>
      )}
    </Link>
  );
}