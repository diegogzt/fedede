"use client";

import React, { useState, useEffect } from "react";
import {
  Bell,
  Search,
  HelpCircle,
  Calendar,
  Home,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export const Topbar = () => {
  const pathname = usePathname();
  const [currentDate, setCurrentDate] = useState<string>("");
  const [dateTime, setDateTime] = useState<string>("");

  // Mover la fecha al cliente para evitar errores de hidratación
  useEffect(() => {
    const now = new Date();
    setDateTime(now.toISOString());
    setCurrentDate(
      now.toLocaleDateString("es-ES", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    );
  }, []);

  // Generate breadcrumb based on pathname
  const getBreadcrumb = () => {
    if (pathname === "/") return [{ label: "Dashboard", href: "/" }];
    const parts = pathname.split("/").filter(Boolean);
    return [
      { label: "Dashboard", href: "/" },
      ...parts.map((part, index) => ({
        label: part.charAt(0).toUpperCase() + part.slice(1),
        href: "/" + parts.slice(0, index + 1).join("/"),
      })),
    ];
  };

  const breadcrumb = getBreadcrumb();

  return (
    <header className="h-12 bg-zinc-950/80 backdrop-blur-md flex items-center justify-between px-4 sticky top-0 z-20 border-b border-zinc-800">
      {/* Left: Breadcrumb & Context */}
      <div className="flex items-center gap-3">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-1.5" aria-label="Breadcrumb">
          <Link
            href="/"
            className="p-1 text-zinc-500 hover:text-yellow-500 hover:bg-zinc-800 rounded transition-colors"
            title="Ir al inicio"
          >
            <Home size={14} />
          </Link>
          {breadcrumb.map((item, index) => (
            <React.Fragment key={item.href}>
              <ChevronRight size={12} className="text-zinc-700" />
              {index === breadcrumb.length - 1 ? (
                <span className="text-xs font-medium text-white">
                  {item.label}
                </span>
              ) : (
                <Link
                  href={item.href}
                  className="text-xs text-zinc-500 hover:text-white transition-colors"
                >
                  {item.label}
                </Link>
              )}
            </React.Fragment>
          ))}
        </nav>

        {/* Separator */}
        <div className="h-4 w-px bg-zinc-800"></div>

        {/* Date Badge */}
        <div className="flex items-center gap-1.5 text-[11px] text-zinc-500 bg-zinc-900 px-2 py-1 rounded border border-zinc-800">
          <Calendar size={12} className="text-zinc-600" />
          {currentDate && <time dateTime={dateTime}>{currentDate}</time>}
        </div>
      </div>

      {/* Right: Search & Actions */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="relative hidden md:block">
          <label htmlFor="search-input" className="sr-only">
            Buscar reportes y documentos
          </label>
          <Search
            className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500 w-3.5 h-3.5"
            aria-hidden="true"
          />
          <input
            id="search-input"
            type="search"
            placeholder="Buscar..."
            className="pl-8 pr-3 py-1.5 text-xs bg-zinc-900 border border-zinc-800 rounded-md focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500/20 w-44 text-white placeholder:text-zinc-600 transition-all hover:border-zinc-700"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-0.5">
          <button
            className="p-1.5 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded transition-all relative"
            title="Ver notificaciones"
            aria-label="Notificaciones (3 sin leer)"
          >
            <Bell size={16} />
            <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-red-500 rounded-full"></span>
          </button>
          <button
            className="p-1.5 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded transition-all"
            title="Ayuda y documentación"
            aria-label="Abrir ayuda"
          >
            <HelpCircle size={16} />
          </button>
        </div>
      </div>
    </header>
  );
};
