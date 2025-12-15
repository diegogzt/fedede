"use client";

import React from "react";
import {
  LayoutDashboard,
  FileText,
  Settings,
  LogOut,
  BarChart3,
  Zap,
  Upload,
  ClipboardCheck,
  FileSpreadsheet,
  ChevronDown,
  Check,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useFiles, useActiveFile } from "@/lib/store";

const menuItems = [
  {
    icon: LayoutDashboard,
    label: "Dashboard",
    href: "/",
    description: "Vista general",
  },
  {
    icon: FileText,
    label: "Reportes",
    href: "/reports",
    description: "Documentos generados",
  },
  {
    icon: Upload,
    label: "Cargar datos",
    href: "/data",
    description: "Subir archivos Excel",
  },
  {
    icon: BarChart3,
    label: "Analíticas",
    href: "/analytics",
    description: "Gráficos y métricas",
  },
  {
    icon: ClipboardCheck,
    label: "Auditoría",
    href: "/audit",
    description: "Historial de cambios",
  },
];

export const Sidebar = () => {
  const pathname = usePathname();
  const { files } = useFiles();
  const { activeFile, setActiveFile } = useActiveFile();
  const [isFileMenuOpen, setIsFileMenuOpen] = React.useState(false);

  return (
    <aside className="w-56 h-screen bg-zinc-950 border-r border-zinc-800 flex flex-col">
      {/* Logo - Clickable to Dashboard */}
      <Link
        href="/"
        className="h-14 flex items-center px-4 border-b border-zinc-800 hover:bg-zinc-900/50 transition-colors group"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-yellow-500 rounded-lg flex items-center justify-center shadow-lg shadow-yellow-500/20 group-hover:shadow-yellow-500/40 transition-shadow">
            <Zap className="text-black fill-black" size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight group-hover:text-yellow-500 transition-colors">
              NEXUS
            </h1>
            <p className="text-[9px] font-medium text-zinc-500 tracking-widest uppercase">
              Finance AI
            </p>
          </div>
        </div>
      </Link>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-3 overflow-y-auto">
        {/* Main Menu Section */}
        <div className="mb-4">
          <div className="flex items-center gap-2 px-2 mb-2">
            <div className="w-1 h-1 rounded-full bg-yellow-500"></div>
            <span className="text-[10px] font-semibold text-zinc-600 uppercase tracking-wider">
              Navegación
            </span>
          </div>

          <div className="space-y-0.5">
            {menuItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className={`
                    flex items-center gap-2.5 px-2.5 py-2 rounded-lg transition-all duration-200 group relative
                    ${
                      isActive
                        ? "bg-yellow-500 text-black"
                        : "text-zinc-400 hover:bg-zinc-800/70 hover:text-white"
                    }
                  `}
                >
                  <item.icon
                    size={16}
                    className={`shrink-0 ${
                      isActive ? "text-black" : "group-hover:text-yellow-500"
                    } transition-colors`}
                  />
                  <span className="text-[13px] font-medium">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Divider */}
        <div className="h-px bg-zinc-800 mx-2 my-3"></div>

        {/* File Selector Section */}
        {files.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-2 px-2 mb-2">
              <div className="w-1 h-1 rounded-full bg-emerald-500"></div>
              <span className="text-[10px] font-semibold text-zinc-600 uppercase tracking-wider">
                Archivo activo
              </span>
            </div>

            <div className="relative">
              <button
                onClick={() => setIsFileMenuOpen(!isFileMenuOpen)}
                className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition-colors text-left"
              >
                <FileSpreadsheet
                  size={14}
                  className="text-emerald-500 shrink-0"
                />
                <span className="flex-1 text-xs text-white truncate">
                  {activeFile?.original_filename ||
                    activeFile?.filename ||
                    "Seleccionar archivo"}
                </span>
                <ChevronDown
                  size={14}
                  className={`text-zinc-500 transition-transform ${
                    isFileMenuOpen ? "rotate-180" : ""
                  }`}
                />
              </button>

              {isFileMenuOpen && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl z-50 overflow-hidden">
                  <div className="max-h-40 overflow-y-auto">
                    {files.map((file) => (
                      <button
                        key={file.id}
                        onClick={() => {
                          setActiveFile(file);
                          setIsFileMenuOpen(false);
                        }}
                        className={`w-full flex items-center gap-2 px-2.5 py-2 text-left hover:bg-zinc-800 transition-colors ${
                          activeFile?.id === file.id ? "bg-zinc-800" : ""
                        }`}
                      >
                        <FileSpreadsheet
                          size={12}
                          className="text-zinc-500 shrink-0"
                        />
                        <span className="flex-1 text-xs text-zinc-300 truncate">
                          {file.original_filename || file.filename}
                        </span>
                        {activeFile?.id === file.id && (
                          <Check
                            size={12}
                            className="text-emerald-500 shrink-0"
                          />
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Divider */}
        <div className="h-px bg-zinc-800 mx-2 my-3"></div>

        {/* System Section */}
        <div>
          <div className="flex items-center gap-2 px-2 mb-2">
            <div className="w-1 h-1 rounded-full bg-zinc-600"></div>
            <span className="text-[10px] font-semibold text-zinc-600 uppercase tracking-wider">
              Sistema
            </span>
          </div>

          <Link
            href="/settings"
            className={`
              flex items-center gap-2.5 px-2.5 py-2 rounded-lg transition-all duration-200 group
              ${
                pathname === "/settings"
                  ? "bg-zinc-800 text-white"
                  : "text-zinc-400 hover:bg-zinc-800/70 hover:text-white"
              }
            `}
          >
            <Settings
              size={16}
              className="group-hover:rotate-90 transition-transform duration-300"
            />
            <span className="text-[13px] font-medium">Configuración</span>
          </Link>
        </div>
      </nav>

      {/* User Profile - Fixed at bottom */}
      <div className="p-3 border-t border-zinc-800 bg-zinc-950">
        <div className="flex items-center gap-2 p-2 rounded-lg bg-zinc-900/80 border border-zinc-800">
          <div className="w-7 h-7 rounded-full bg-yellow-500 flex items-center justify-center text-black font-bold text-[10px]">
            JD
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-white truncate">John Doe</p>
          </div>
          <button
            className="p-1.5 text-zinc-500 hover:text-red-400 hover:bg-red-400/10 rounded transition-all"
            title="Cerrar sesión"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </aside>
  );
};
