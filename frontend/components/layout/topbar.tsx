import React from "react";
import { Bell, Search, HelpCircle, Calendar } from "lucide-react";

export const Topbar = () => {
  return (
    <header className="h-24 bg-transparent flex items-center justify-between px-10 sticky top-0 z-10 backdrop-blur-sm">
      {/* Left: Breadcrumbs / Context */}
      <div className="flex items-center gap-6">
        <h2 className="text-3xl font-black text-white tracking-tight">
          Dashboard General
        </h2>
        <div className="h-8 w-px bg-zinc-800"></div>
        <div className="flex items-center gap-3 text-base font-medium text-[var(--muted)] bg-zinc-900/50 px-4 py-2 rounded-full border border-zinc-800">
          <Calendar size={16} className="text-[var(--primary)]" />
          <span>
            {new Date().toLocaleDateString("es-ES", {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </span>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-6">
        <div className="relative hidden md:block group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 w-5 h-5 group-focus-within:text-[var(--primary)] transition-colors" />
          <input
            type="text"
            placeholder="Buscar reporte..."
            className="pl-12 pr-6 py-3 text-sm bg-zinc-900 border border-zinc-800 rounded-full focus:outline-none focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] w-80 transition-all text-white placeholder:text-zinc-600"
          />
        </div>

        <div className="flex items-center gap-3 border-l border-zinc-800 pl-6">
          <button className="p-3 text-zinc-400 hover:text-black hover:bg-[var(--primary)] rounded-full transition-all duration-300 relative group">
            <Bell size={22} />
            <span className="absolute top-2 right-2 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-zinc-950 group-hover:border-[var(--primary)]"></span>
          </button>
          <button className="p-3 text-zinc-400 hover:text-black hover:bg-[var(--primary)] rounded-full transition-all duration-300">
            <HelpCircle size={22} />
          </button>
        </div>
      </div>
    </header>
  );
};
