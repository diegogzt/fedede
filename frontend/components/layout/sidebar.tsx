import React from "react";
import {
  LayoutDashboard,
  FileText,
  Settings,
  LogOut,
  PieChart,
  Zap,
  Database,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";

const menuItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/" },
  { icon: FileText, label: "Reportes", href: "/reports" },
  { icon: Database, label: "Datos", href: "/data" },
  { icon: PieChart, label: "Analíticas", href: "/analytics" },
  { icon: ShieldCheck, label: "Auditoría", href: "/audit" },
];

export const Sidebar = () => {
  return (
    <aside className="w-80 h-screen bg-black border-r border-zinc-900 flex flex-col sticky top-0">
      {/* Logo Area */}
      <div className="h-24 flex items-center px-10 border-b border-zinc-900">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-[var(--primary)] rounded-xl flex items-center justify-center shadow-[0_0_15px_rgba(250,204,21,0.3)]">
            <Zap className="text-black fill-black" size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-white tracking-tighter leading-none">
              NEXUS
            </h1>
            <p className="text-[10px] font-bold text-[var(--primary)] tracking-[0.2em] uppercase">
              Finance AI
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-10 px-6 space-y-2">
        <div className="px-4 mb-4 text-xs font-bold text-zinc-600 uppercase tracking-widest">
          Menu Principal
        </div>
        {menuItems.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className="flex items-center gap-4 px-4 py-4 text-zinc-400 hover:text-black hover:bg-[var(--primary)] rounded-xl transition-all duration-300 group font-medium"
          >
            <item.icon
              size={20}
              className="group-hover:scale-110 transition-transform"
            />
            <span className="text-sm">{item.label}</span>
          </Link>
        ))}

        <div className="mt-10 px-4 mb-4 text-xs font-bold text-zinc-600 uppercase tracking-widest">
          Sistema
        </div>
        <Link
          href="/settings"
          className="flex items-center gap-4 px-4 py-4 text-zinc-400 hover:text-white hover:bg-zinc-900 rounded-xl transition-all duration-300 group font-medium"
        >
          <Settings size={20} />
          <span className="text-sm">Configuración</span>
        </Link>
      </nav>

      {/* User Profile */}
      <div className="p-6 border-t border-zinc-900">
        <button className="flex items-center gap-4 w-full p-4 rounded-2xl bg-zinc-900/50 hover:bg-zinc-900 border border-zinc-800 transition-all group">
          <div className="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center text-[var(--primary)] font-bold border border-zinc-700">
            JD
          </div>
          <div className="flex-1 text-left">
            <p className="text-sm font-bold text-white group-hover:text-[var(--primary)] transition-colors">
              John Doe
            </p>
            <p className="text-xs text-zinc-500">Admin Access</p>
          </div>
          <LogOut
            size={18}
            className="text-zinc-600 group-hover:text-red-400 transition-colors"
          />
        </button>
      </div>
    </aside>
  );
};
