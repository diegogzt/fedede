"use client";

import React, { useEffect } from "react";
import {
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  FileText,
  Upload,
  AlertCircle,
  CheckCircle,
  BarChart3,
  FileSpreadsheet,
  Clock,
  AlertTriangle,
  Sparkles,
} from "lucide-react";
import {
  useApp,
  useActiveFile,
  useFiles,
  documentToFileData,
} from "@/lib/store";
import { getHistory, formatDate, ProcessedDocument } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function Dashboard() {
  const { isLoading, setLoading, setError } = useApp();
  const { activeFile, setActiveFile } = useActiveFile();
  const { files, setFiles } = useFiles();

  // Cargar historial al montar
  useEffect(() => {
    const loadData = async () => {
      if (files.length === 0) {
        setLoading(true);
        try {
          const documents = await getHistory();
          const fileDataList = documents.map((doc: ProcessedDocument) =>
            documentToFileData(doc)
          );
          setFiles(fileDataList);
        } catch (err) {
          setError(
            err instanceof Error ? err.message : "Error al cargar datos"
          );
        } finally {
          setLoading(false);
        }
      }
    };
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Calcular estadísticas
  const totalStats = files.reduce(
    (acc, file) => {
      if (file.status === "success") {
        acc.totalQuestions += file.questions_generated || 0;
        acc.highPriority += file.high_priority_count || 0;
        acc.mediumPriority += file.medium_priority_count || 0;
        acc.lowPriority += file.low_priority_count || 0;
        acc.successCount += 1;
      }
      return acc;
    },
    {
      totalQuestions: 0,
      highPriority: 0,
      mediumPriority: 0,
      lowPriority: 0,
      successCount: 0,
    }
  );

  // Stats para el archivo activo o totales
  const currentStats =
    activeFile && activeFile.status === "success"
      ? {
          questions: activeFile.questions_generated || 0,
          high: activeFile.high_priority_count || 0,
          medium: activeFile.medium_priority_count || 0,
          low: activeFile.low_priority_count || 0,
        }
      : null;

  const questionsCount = currentStats
    ? currentStats.questions
    : totalStats.totalQuestions;
  const highCount = currentStats ? currentStats.high : totalStats.highPriority;
  const mediumCount = currentStats
    ? currentStats.medium
    : totalStats.mediumPriority;
  const lowCount = currentStats ? currentStats.low : totalStats.lowPriority;

  const stats = [
    {
      label: "Reportes procesados",
      value: files.length.toString(),
      change:
        totalStats.successCount > 0
          ? `${totalStats.successCount} exitosos`
          : "0 exitosos",
      trend: "up",
      icon: FileText,
    },
    {
      label: "Preguntas Q&A",
      value: questionsCount.toString(),
      change: activeFile ? "archivo actual" : "total",
      trend: questionsCount > 0 ? "up" : "neutral",
      icon: Sparkles,
    },
    {
      label: "Prioridad Alta",
      value: highCount.toString(),
      change: "requieren atención",
      trend: highCount > 0 ? "down" : "up",
      icon: AlertTriangle,
      color: "red",
    },
    {
      label: "Media + Baja",
      value: (mediumCount + lowCount).toString(),
      change: "de seguimiento",
      trend: "up",
      icon: TrendingUp,
      color: "green",
    },
  ];

  // Vista sin datos
  if (files.length === 0 && !isLoading) {
    return (
      <div className="p-6">
        <div className="text-center py-20">
          <div className="w-20 h-20 bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-6">
            <Upload className="w-10 h-10 text-zinc-600" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">
            Bienvenido a NEXUS Finance DD
          </h2>
          <p className="text-zinc-400 mb-8 max-w-md mx-auto">
            Sube tu primer archivo financiero (Excel o CSV) para generar
            análisis Q&A automatizados con IA
          </p>
          <Button
            onClick={() => (window.location.href = "/data")}
            className="bg-yellow-500 text-black hover:bg-yellow-400 px-8 py-3"
          >
            <Upload className="w-4 h-4 mr-2" />
            Subir archivo
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Header con selector de archivo */}
      {activeFile && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-500/10 rounded-lg">
              <FileSpreadsheet className="w-5 h-5 text-yellow-500" />
            </div>
            <div>
              <h2 className="text-white font-semibold">
                {activeFile.original_filename}
              </h2>
              <p className="text-xs text-zinc-500">
                Procesado: {formatDate(activeFile.processed_at || "")}
              </p>
            </div>
          </div>

          {files.length > 1 && (
            <select
              value={activeFile.id}
              onChange={(e) => {
                const file = files.find((f) => f.id === e.target.value);
                if (file) setActiveFile(file);
              }}
              className="bg-zinc-800 border border-zinc-700 text-zinc-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-yellow-500"
              aria-label="Seleccionar archivo"
            >
              {files.map((file) => (
                <option key={file.id} value={file.id}>
                  {file.original_filename}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      {/* Stats Grid */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          {stats.map((stat, index) => (
            <article
              key={index}
              className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 hover:border-yellow-500/30 transition-all duration-300 group"
            >
              <div className="flex items-start justify-between mb-3">
                <div
                  className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors
                  ${
                    stat.color === "red"
                      ? "bg-red-500/10"
                      : stat.color === "green"
                      ? "bg-green-500/10"
                      : "bg-zinc-800 group-hover:bg-yellow-500/10"
                  }`}
                >
                  <stat.icon
                    size={18}
                    className={
                      stat.color === "red"
                        ? "text-red-500"
                        : stat.color === "green"
                        ? "text-green-500"
                        : "text-yellow-500"
                    }
                  />
                </div>
                <div
                  className={`flex items-center gap-0.5 text-[11px] font-medium px-2 py-0.5 rounded-full
                  ${
                    stat.trend === "up"
                      ? "text-emerald-400 bg-emerald-400/10"
                      : stat.trend === "down"
                      ? "text-red-400 bg-red-400/10"
                      : "text-zinc-400 bg-zinc-700"
                  }`}
                >
                  {stat.trend === "up" ? (
                    <ArrowUpRight size={10} />
                  ) : stat.trend === "down" ? (
                    <ArrowDownRight size={10} />
                  ) : null}
                  {stat.change}
                </div>
              </div>

              <div>
                <p className="text-zinc-500 text-xs font-medium mb-0.5">
                  {stat.label}
                </p>
                <p className="text-xl font-bold text-white">{stat.value}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Main Content */}
      <section className="grid grid-cols-1 gap-4">
        {/* Actividad Reciente */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between p-3 border-b border-zinc-800">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-zinc-800 rounded flex items-center justify-center">
                <Clock size={14} className="text-yellow-500" />
              </div>
              <h3 className="text-sm font-semibold text-white">
                Actividad reciente
              </h3>
            </div>
          </div>

          <div className="divide-y divide-zinc-800">
            {files.slice(0, 10).map((file) => (
              <button
                key={file.id}
                onClick={() => setActiveFile(file)}
                className={`w-full flex items-center gap-3 p-3 hover:bg-zinc-800/50 transition-colors text-left
                  ${
                    activeFile?.id === file.id
                      ? "bg-yellow-500/5 border-l-2 border-yellow-500"
                      : ""
                  }`}
              >
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center
                  ${
                    file.status === "success"
                      ? "bg-green-500/10"
                      : file.status === "error"
                      ? "bg-red-500/10"
                      : "bg-yellow-500/10"
                  }`}
                >
                  {file.status === "success" ? (
                    <CheckCircle size={16} className="text-green-500" />
                  ) : file.status === "error" ? (
                    <AlertCircle size={16} className="text-red-500" />
                  ) : (
                    <Clock size={16} className="text-yellow-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-white truncate">
                    {file.original_filename || file.name}
                  </p>
                  <p className="text-[10px] text-zinc-500">
                    {formatDate(
                      file.processed_at || file.uploadDate?.toISOString() || ""
                    )}
                  </p>
                </div>
                {file.status === "success" && (
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                      {file.questions_generated} Q&A
                    </span>
                    <ArrowUpRight size={12} className="text-zinc-600" />
                  </div>
                )}
              </button>
            ))}

            {files.length === 0 && (
              <div className="p-4 text-center text-zinc-500 text-sm">
                No hay actividad reciente
              </div>
            )}
          </div>

          {files.length > 10 && (
            <div className="p-2 border-t border-zinc-800">
              <Button
                variant="outline"
                size="sm"
                onClick={() => (window.location.href = "/reports")}
                className="w-full border-zinc-700 text-zinc-400 hover:text-white text-xs"
              >
                Ver todos los reportes
              </Button>
            </div>
          )}
        </div>
      </section>

      {/* Quick Actions */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <button
          onClick={() => (window.location.href = "/data")}
          className="flex items-center gap-3 p-4 bg-zinc-900 border border-zinc-800 rounded-xl hover:border-yellow-500/30 transition-all group"
        >
          <div className="w-10 h-10 bg-yellow-500/10 rounded-lg flex items-center justify-center group-hover:bg-yellow-500/20 transition-colors">
            <Upload size={20} className="text-yellow-500" />
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-white">Subir archivo</p>
            <p className="text-xs text-zinc-500">Procesar nuevo Excel/CSV</p>
          </div>
        </button>

        <button
          onClick={() => (window.location.href = "/reports")}
          className="flex items-center gap-3 p-4 bg-zinc-900 border border-zinc-800 rounded-xl hover:border-yellow-500/30 transition-all group"
        >
          <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center group-hover:bg-blue-500/20 transition-colors">
            <FileText size={20} className="text-blue-500" />
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-white">Ver reportes</p>
            <p className="text-xs text-zinc-500">Descargar y gestionar</p>
          </div>
        </button>

        <button
          onClick={() => (window.location.href = "/analytics")}
          className="flex items-center gap-3 p-4 bg-zinc-900 border border-zinc-800 rounded-xl hover:border-yellow-500/30 transition-all group"
        >
          <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center group-hover:bg-purple-500/20 transition-colors">
            <BarChart3 size={20} className="text-purple-500" />
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-white">Analíticas</p>
            <p className="text-xs text-zinc-500">Visualizar tendencias</p>
          </div>
        </button>
      </section>
    </div>
  );
}
