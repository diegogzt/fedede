import React from "react";
import {
  ArrowUpRight,
  TrendingUp,
  Users,
  DollarSign,
  Activity,
} from "lucide-react";

const stats = [
  {
    label: "Ingresos Totales",
    value: ",231,890",
    change: "+12.5%",
    trend: "up",
    icon: DollarSign,
  },
  {
    label: "Usuarios Activos",
    value: "2,543",
    change: "+8.2%",
    trend: "up",
    icon: Users,
  },
  {
    label: "Reportes Generados",
    value: "145",
    change: "+23.1%",
    trend: "up",
    icon: Activity,
  },
  {
    label: "Eficiencia",
    value: "94.2%",
    change: "+4.3%",
    trend: "up",
    icon: TrendingUp,
  },
];

export default function Dashboard() {
  return (
    <div className="p-10 space-y-10">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div
            key={index}
            className="bg-zinc-900/50 border border-zinc-800 p-6 rounded-3xl hover:border-[var(--primary)] transition-all duration-300 group relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity">
              <stat.icon size={64} className="text-[var(--primary)]" />
            </div>

            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-black rounded-2xl border border-zinc-800 group-hover:border-[var(--primary)] transition-colors">
                  <stat.icon size={24} className="text-[var(--primary)]" />
                </div>
                <span className="flex items-center gap-1 text-xs font-bold text-[var(--primary)] bg-[var(--primary)]/10 px-2 py-1 rounded-lg">
                  {stat.change}
                  <ArrowUpRight size={12} />
                </span>
              </div>

              <h3 className="text-zinc-500 text-sm font-medium mb-1">
                {stat.label}
              </h3>
              <p className="text-3xl font-black text-white tracking-tight">
                {stat.value}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Chart Section (Placeholder) */}
        <div className="lg:col-span-2 bg-zinc-900/30 border border-zinc-800 rounded-3xl p-8 min-h-[400px] flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-xl font-bold text-white">Resumen Financiero</h3>
            <select className="bg-black border border-zinc-800 text-zinc-400 text-sm rounded-xl px-4 py-2 focus:outline-none focus:border-[var(--primary)]">
              <option>Últimos 30 días</option>
              <option>Este Año</option>
            </select>
          </div>
          <div className="flex-1 flex items-center justify-center border-2 border-dashed border-zinc-800 rounded-2xl bg-black/20">
            <p className="text-zinc-600 font-medium">Gráfico de Actividad</p>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-zinc-900/30 border border-zinc-800 rounded-3xl p-8">
          <h3 className="text-xl font-bold text-white mb-6">
            Actividad Reciente
          </h3>
          <div className="space-y-6">
            {[1, 2, 3, 4].map((_, i) => (
              <div
                key={i}
                className="flex items-start gap-4 pb-6 border-b border-zinc-800/50 last:border-0 last:pb-0"
              >
                <div className="w-2 h-2 mt-2 rounded-full bg-[var(--primary)] shadow-[0_0_8px_var(--primary)]"></div>
                <div>
                  <p className="text-sm font-bold text-white">
                    Nuevo reporte generado
                  </p>
                  <p className="text-xs text-zinc-500 mt-1">
                    Hace 2 horas Sistema
                  </p>
                </div>
              </div>
            ))}
          </div>

          <button className="w-full mt-6 py-4 rounded-xl border border-zinc-800 text-zinc-400 text-sm font-bold hover:bg-[var(--primary)] hover:text-black hover:border-[var(--primary)] transition-all duration-300">
            Ver todo el historial
          </button>
        </div>
      </div>
    </div>
  );
}
