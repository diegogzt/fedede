"use client";

import React from "react";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  PieChart,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileSpreadsheet,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useActiveFile, useFiles } from "@/lib/store";
import { formatCurrency, formatDate, type QAReport } from "@/lib/api";
import { useReport } from "@/lib/hooks/useReport";
import {
  getEffectiveTotalExpenses,
  getEffectiveTotalRevenue,
} from "@/lib/revenue";

// Componente para barras de progreso visual (definido fuera del render)
const WIDTH_CLASS_BY_STEP_5: Record<number, string> = {
  0: "w-[0%]",
  5: "w-[5%]",
  10: "w-[10%]",
  15: "w-[15%]",
  20: "w-[20%]",
  25: "w-[25%]",
  30: "w-[30%]",
  35: "w-[35%]",
  40: "w-[40%]",
  45: "w-[45%]",
  50: "w-[50%]",
  55: "w-[55%]",
  60: "w-[60%]",
  65: "w-[65%]",
  70: "w-[70%]",
  75: "w-[75%]",
  80: "w-[80%]",
  85: "w-[85%]",
  90: "w-[90%]",
  95: "w-[95%]",
  100: "w-[100%]",
};

const HEIGHT_CLASS_BY_STEP_5: Record<number, string> = {
  0: "h-[0%]",
  5: "h-[5%]",
  10: "h-[10%]",
  15: "h-[15%]",
  20: "h-[20%]",
  25: "h-[25%]",
  30: "h-[30%]",
  35: "h-[35%]",
  40: "h-[40%]",
  45: "h-[45%]",
  50: "h-[50%]",
  55: "h-[55%]",
  60: "h-[60%]",
  65: "h-[65%]",
  70: "h-[70%]",
  75: "h-[75%]",
  80: "h-[80%]",
  85: "h-[85%]",
  90: "h-[90%]",
  95: "h-[95%]",
  100: "h-[100%]",
};

function percentToWidthClass(percent: number): string {
  if (!Number.isFinite(percent)) return WIDTH_CLASS_BY_STEP_5[0];
  const clamped = Math.max(0, Math.min(100, percent));
  const stepped = Math.round(clamped / 5) * 5;
  return WIDTH_CLASS_BY_STEP_5[stepped] || WIDTH_CLASS_BY_STEP_5[0];
}

function percentToHeightClass(percent: number): string {
  if (!Number.isFinite(percent)) return HEIGHT_CLASS_BY_STEP_5[0];
  const clamped = Math.max(0, Math.min(100, percent));
  const stepped = Math.round(clamped / 5) * 5;
  return HEIGHT_CLASS_BY_STEP_5[stepped] || HEIGHT_CLASS_BY_STEP_5[0];
}

type TrendViewMode = "cards" | "bar" | "line";

function TrendChart({
  title,
  icon,
  series,
  mode,
}: {
  title: string;
  icon: React.ReactNode;
  series: Array<{ period: string; value: number }>;
  mode: TrendViewMode;
}) {
  if (mode === "cards") return null;

  const maxValue = Math.max(...series.map((s) => s.value), 0);

  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <p className="text-sm font-medium text-white">{title}</p>
      </div>

      {mode === "bar" ? (
        <div className="w-full">
          <div className="h-32 flex items-end gap-2 bg-zinc-800/30 rounded-lg p-3 border border-zinc-800">
            {series.map(({ period, value }) => {
              const pct = maxValue > 0 ? (value / maxValue) * 100 : 0;
              return (
                <div
                  key={period}
                  className="flex-1 flex flex-col items-center gap-2"
                >
                  <div className="w-full h-20 flex items-end">
                    <div
                      className={`w-full ${percentToHeightClass(
                        pct
                      )} bg-yellow-500/60 rounded-md border border-yellow-500/30`}
                      title={`${period}: ${formatCurrency(value)}`}
                    />
                  </div>
                  <div className="text-[10px] text-zinc-500 truncate w-full text-center">
                    {period}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="bg-zinc-800/30 rounded-lg p-3 border border-zinc-800">
          <svg
            className="w-full"
            viewBox="0 0 100 40"
            preserveAspectRatio="xMidYMid meet"
            style={{ aspectRatio: "100 / 40" }}
            aria-label={title}
            role="img"
          >
            {(() => {
              const n = series.length;
              if (n === 0) return null;

              const xStep = n > 1 ? 100 / (n - 1) : 0;
              const points = series
                .map((s, idx) => {
                  const x = idx * xStep;
                  const y = maxValue > 0 ? 38 - (s.value / maxValue) * 34 : 38;
                  return `${x},${Math.max(2, Math.min(38, y))}`;
                })
                .join(" ");

              return (
                <>
                  <polyline
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    points={points}
                    className="text-yellow-500"
                  />
                  {series.map((s, idx) => {
                    const x = idx * xStep;
                    const y =
                      maxValue > 0 ? 38 - (s.value / maxValue) * 34 : 38;
                    const cy = Math.max(2, Math.min(38, y));
                    return (
                      <circle
                        key={s.period}
                        cx={x}
                        cy={cy}
                        r={1.8}
                        className="fill-yellow-500"
                      >
                        <title>{`${s.period}: ${formatCurrency(
                          s.value
                        )}`}</title>
                      </circle>
                    );
                  })}
                </>
              );
            })()}
          </svg>
        </div>
      )}
    </div>
  );
}

function PriorityBar({
  high,
  medium,
  low,
}: {
  high: number;
  medium: number;
  low: number;
}) {
  const total = high + medium + low;
  if (total === 0) return null;

  const highPercent = (high / total) * 100;
  const mediumPercent = (medium / total) * 100;
  const lowPercent = (low / total) * 100;

  return (
    <div className="w-full h-3 rounded-full overflow-hidden flex bg-zinc-800">
      <div
        className={`bg-red-500 h-full ${percentToWidthClass(highPercent)}`}
        title={`Alta: ${high} (${highPercent.toFixed(1)}%)`}
      />
      <div
        className={`bg-yellow-500 h-full ${percentToWidthClass(mediumPercent)}`}
        title={`Media: ${medium} (${mediumPercent.toFixed(1)}%)`}
      />
      <div
        className={`bg-green-500 h-full ${percentToWidthClass(lowPercent)}`}
        title={`Baja: ${low} (${lowPercent.toFixed(1)}%)`}
      />
    </div>
  );
}

export default function AnalyticsPage() {
  const { activeFile } = useActiveFile();
  const { files } = useFiles();

  const activeReport = useReport(activeFile?.id ?? null);

  const [compareAId, setCompareAId] = React.useState<string | null>(null);
  const [compareBId, setCompareBId] = React.useState<string | null>(null);

  const [revenueViewMode, setRevenueViewMode] =
    React.useState<TrendViewMode>("cards");
  const [expenseViewMode, setExpenseViewMode] =
    React.useState<TrendViewMode>("cards");

  React.useEffect(() => {
    if (files.length === 0) return;
    setCompareAId((prev) => prev ?? files[0]?.id ?? null);
    setCompareBId((prev) => prev ?? files[1]?.id ?? null);
  }, [files]);

  const reportA = useReport(compareAId);
  const reportB = useReport(compareBId);

  const computeReportStats = React.useCallback(
    (r: QAReport | null | undefined) => {
      if (!r) {
        return { total: 0, high: 0, medium: 0, low: 0 };
      }
      const withQuestion = r.items.filter(
        (it) => !!(it.question && it.question.trim())
      );
      const high = withQuestion.filter((it) => it.priority === "Alta").length;
      const medium = withQuestion.filter(
        (it) => it.priority === "Media"
      ).length;
      const low = withQuestion.filter((it) => it.priority === "Baja").length;
      return { total: withQuestion.length, high, medium, low };
    },
    []
  );

  const statsA = computeReportStats(reportA.report);
  const statsB = computeReportStats(reportB.report);

  // Calcular estadísticas agregadas de todos los archivos
  const totalStats = files.reduce(
    (acc, file) => {
      if (file.status === "success") {
        acc.totalQuestions += file.questions_generated || 0;
        acc.highPriority += file.high_priority_count || 0;
        acc.mediumPriority += file.medium_priority_count || 0;
        acc.lowPriority += file.low_priority_count || 0;
        acc.successCount += 1;
      } else if (file.status === "error") {
        acc.errorCount += 1;
      }
      return acc;
    },
    {
      totalQuestions: 0,
      highPriority: 0,
      mediumPriority: 0,
      lowPriority: 0,
      successCount: 0,
      errorCount: 0,
    }
  );

  const totalPriorities =
    totalStats.highPriority +
    totalStats.mediumPriority +
    totalStats.lowPriority;

  const activeRevenue = React.useMemo(
    () => getEffectiveTotalRevenue(activeReport.report),
    [activeReport.report]
  );

  const activeExpenses = React.useMemo(
    () => getEffectiveTotalExpenses(activeReport.report),
    [activeReport.report]
  );

  const activeRevenuePeriods = React.useMemo(() => {
    const reportPeriods = activeReport.report?.analysis_periods || [];
    const revenueKeys = new Set(Object.keys(activeRevenue));

    if (reportPeriods.length > 0) {
      return reportPeriods.filter((p) => revenueKeys.has(p));
    }

    return Array.from(revenueKeys).sort();
  }, [activeReport.report?.analysis_periods, activeRevenue]);

  const activeExpensesPeriods = React.useMemo(() => {
    const reportPeriods = activeReport.report?.analysis_periods || [];
    const expenseKeys = new Set(Object.keys(activeExpenses));

    if (reportPeriods.length > 0) {
      return reportPeriods.filter((p) => expenseKeys.has(p));
    }

    return Array.from(expenseKeys).sort();
  }, [activeReport.report?.analysis_periods, activeExpenses]);

  // Si hay archivo activo, usar sus estadísticas
  const currentStats = React.useMemo(() => {
    if (!(activeFile && activeFile.status === "success")) return null;
    return {
      questions: activeFile.questions_generated || 0,
      high: activeFile.high_priority_count || 0,
      medium: activeFile.medium_priority_count || 0,
      low: activeFile.low_priority_count || 0,
      revenue: activeRevenue,
      periods: activeRevenuePeriods,
      expenses: activeExpenses,
      expensePeriods: activeExpensesPeriods,
    };
  }, [
    activeFile,
    activeRevenue,
    activeRevenuePeriods,
    activeExpenses,
    activeExpensesPeriods,
  ]);

  const revenueSeries = React.useMemo(() => {
    if (!currentStats) return [] as Array<{ period: string; value: number }>;
    const periods =
      currentStats.periods.length > 0
        ? currentStats.periods
        : Object.keys(currentStats.revenue);
    return periods
      .map((p) => ({ period: p, value: currentStats.revenue[p] }))
      .filter((x) => Number.isFinite(x.value) && x.value > 0);
  }, [currentStats]);

  const expenseSeries = React.useMemo(() => {
    if (!currentStats) return [] as Array<{ period: string; value: number }>;
    const periods =
      currentStats.expensePeriods.length > 0
        ? currentStats.expensePeriods
        : Object.keys(currentStats.expenses);
    return periods
      .map((p) => ({ period: p, value: currentStats.expenses[p] }))
      .filter((x) => Number.isFinite(x.value) && x.value > 0);
  }, [currentStats]);

  // Vista cuando no hay datos
  if (files.length === 0) {
    return (
      <div className="p-6">
        <div className="text-center py-16">
          <BarChart3 className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">
            Sin datos para analizar
          </h2>
          <p className="text-zinc-400 mb-6">
            Sube un archivo financiero para ver las analíticas
          </p>
          <Button
            onClick={() => (window.location.href = "/data")}
            className="bg-yellow-500 text-black hover:bg-yellow-400"
          >
            Subir archivo
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Analíticas</h1>
        <p className="text-zinc-400 mt-1">
          {activeFile
            ? `Análisis de: ${activeFile.original_filename}`
            : "Resumen general de todos los reportes procesados"}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Reportes */}
        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-zinc-400 text-sm">Reportes Procesados</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {files.length}
                </p>
                <div className="flex items-center gap-2 mt-2 text-xs">
                  <span className="text-green-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    {totalStats.successCount} exitosos
                  </span>
                  {totalStats.errorCount > 0 && (
                    <span className="text-red-400 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      {totalStats.errorCount} errores
                    </span>
                  )}
                </div>
              </div>
              <div className="p-2 bg-yellow-500/10 rounded-lg">
                <FileSpreadsheet className="w-5 h-5 text-yellow-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Total Preguntas */}
        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-zinc-400 text-sm">Total Preguntas Q&A</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {currentStats
                    ? currentStats.questions
                    : totalStats.totalQuestions}
                </p>
                <p className="text-xs text-zinc-500 mt-2">
                  {currentStats
                    ? "En archivo seleccionado"
                    : "En todos los reportes"}
                </p>
              </div>
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <BarChart3 className="w-5 h-5 text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Alta Prioridad */}
        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-zinc-400 text-sm">Prioridad Alta</p>
                <p className="text-2xl font-bold text-red-400 mt-1">
                  {currentStats ? currentStats.high : totalStats.highPriority}
                </p>
                <p className="text-xs text-zinc-500 mt-2">
                  {totalPriorities > 0
                    ? `${(
                        (totalStats.highPriority / totalPriorities) *
                        100
                      ).toFixed(1)}% del total`
                    : "Sin datos"}
                </p>
              </div>
              <div className="p-2 bg-red-500/10 rounded-lg">
                <TrendingUp className="w-5 h-5 text-red-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Media/Baja Prioridad */}
        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-zinc-400 text-sm">Media + Baja</p>
                <p className="text-2xl font-bold text-green-400 mt-1">
                  {currentStats
                    ? currentStats.medium + currentStats.low
                    : totalStats.mediumPriority + totalStats.lowPriority}
                </p>
                <p className="text-xs text-zinc-500 mt-2">
                  Preguntas de seguimiento
                </p>
              </div>
              <div className="p-2 bg-green-500/10 rounded-lg">
                <TrendingDown className="w-5 h-5 text-green-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribución de Prioridades */}
        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <PieChart className="w-5 h-5 text-yellow-500" />
              Distribución de Prioridades
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {totalPriorities > 0 ? (
              <>
                <PriorityBar
                  high={currentStats?.high || totalStats.highPriority}
                  medium={currentStats?.medium || totalStats.mediumPriority}
                  low={currentStats?.low || totalStats.lowPriority}
                />

                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div className="text-center p-3 bg-zinc-800/50 rounded-lg">
                    <div className="w-3 h-3 bg-red-500 rounded-full mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {currentStats?.high || totalStats.highPriority}
                    </p>
                    <p className="text-xs text-zinc-400">Alta</p>
                  </div>
                  <div className="text-center p-3 bg-zinc-800/50 rounded-lg">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {currentStats?.medium || totalStats.mediumPriority}
                    </p>
                    <p className="text-xs text-zinc-400">Media</p>
                  </div>
                  <div className="text-center p-3 bg-zinc-800/50 rounded-lg">
                    <div className="w-3 h-3 bg-green-500 rounded-full mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {currentStats?.low || totalStats.lowPriority}
                    </p>
                    <p className="text-xs text-zinc-400">Baja</p>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-zinc-500">
                Sin datos de prioridades
              </div>
            )}
          </CardContent>
        </Card>

        {/* Actividad Reciente */}
        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Clock className="w-5 h-5 text-yellow-500" />
              Últimos Reportes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {files.slice(0, 5).map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg hover:bg-zinc-800 transition-colors cursor-pointer"
                  onClick={() => (window.location.href = "/reports")}
                >
                  <div className="flex items-center gap-3">
                    <FileSpreadsheet className="w-4 h-4 text-yellow-500" />
                    <div>
                      <p className="text-sm text-white truncate max-w-[200px]">
                        {file.original_filename}
                      </p>
                      <p className="text-xs text-zinc-500">
                        {file.questions_generated || 0} preguntas
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {file.status === "success" ? (
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                    ) : file.status === "error" ? (
                      <AlertTriangle className="w-4 h-4 text-red-500" />
                    ) : (
                      <Clock className="w-4 h-4 text-yellow-500" />
                    )}
                  </div>
                </div>
              ))}

              {files.length === 0 && (
                <div className="text-center py-4 text-zinc-500">
                  No hay reportes recientes
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tendencias (placeholder para datos reales) */}
      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <TrendingUp className="w-5 h-5 text-yellow-500" />
              Tendencias de Ingresos
            </CardTitle>
            <select
              value={revenueViewMode}
              onChange={(e) =>
                setRevenueViewMode(e.target.value as TrendViewMode)
              }
              className="bg-zinc-800 border border-zinc-700 text-zinc-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-yellow-500"
              aria-label="Vista de ingresos"
            >
              <option value="cards">Tarjetas</option>
              <option value="bar">Barras</option>
              <option value="line">Línea</option>
            </select>
          </div>
        </CardHeader>
        <CardContent>
          {currentStats &&
          currentStats.revenue &&
          Object.keys(currentStats.revenue).length > 0 ? (
            <>
              <TrendChart
                title="Ingresos"
                icon={<BarChart3 className="w-4 h-4 text-yellow-500" />}
                series={revenueSeries}
                mode={revenueViewMode}
              />
              {revenueViewMode === "cards" && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {(currentStats.periods.length > 0
                    ? currentStats.periods.map(
                        (p) => [p, currentStats.revenue[p]] as const
                      )
                    : Object.entries(currentStats.revenue)
                  ).map(([period, value]) => (
                    <div key={period} className="p-4 bg-zinc-800/50 rounded-lg">
                      <p className="text-sm text-zinc-400">{period}</p>
                      <p className="text-xl font-bold text-white mt-1">
                        {formatCurrency(value)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-8">
              <BarChart3 className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
              <p className="text-zinc-400">
                {activeFile
                  ? activeReport.isLoading
                    ? "Cargando reporte del archivo activo…"
                    : activeReport.error
                    ? "No se pudo cargar el reporte del archivo activo"
                    : "No se encontraron cuentas de ingresos (7*) para calcular ingresos"
                  : "Selecciona un archivo procesado para ver tendencias de ingresos"}
              </p>
              {activeFile && activeReport.error && (
                <p className="text-xs text-zinc-500 mt-2">
                  {activeReport.error}
                </p>
              )}
              <Button
                variant="outline"
                onClick={() => (window.location.href = "/reports")}
                className="mt-4 border-zinc-700 text-zinc-400"
              >
                Ver reportes
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tendencias de Gastos */}
      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <TrendingDown className="w-5 h-5 text-yellow-500" />
              Tendencias de Gastos
            </CardTitle>
            <select
              value={expenseViewMode}
              onChange={(e) =>
                setExpenseViewMode(e.target.value as TrendViewMode)
              }
              className="bg-zinc-800 border border-zinc-700 text-zinc-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-yellow-500"
              aria-label="Vista de gastos"
            >
              <option value="cards">Tarjetas</option>
              <option value="bar">Barras</option>
              <option value="line">Línea</option>
            </select>
          </div>
        </CardHeader>
        <CardContent>
          {currentStats &&
          currentStats.expenses &&
          Object.keys(currentStats.expenses).length > 0 ? (
            <>
              <TrendChart
                title="Gastos"
                icon={<BarChart3 className="w-4 h-4 text-yellow-500" />}
                series={expenseSeries}
                mode={expenseViewMode}
              />
              {expenseViewMode === "cards" && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {(currentStats.expensePeriods.length > 0
                    ? currentStats.expensePeriods.map(
                        (p) => [p, currentStats.expenses[p]] as const
                      )
                    : Object.entries(currentStats.expenses)
                  ).map(([period, value]) => (
                    <div key={period} className="p-4 bg-zinc-800/50 rounded-lg">
                      <p className="text-sm text-zinc-400">{period}</p>
                      <p className="text-xl font-bold text-white mt-1">
                        {formatCurrency(value)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-8">
              <BarChart3 className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
              <p className="text-zinc-400">
                {activeFile
                  ? activeReport.isLoading
                    ? "Cargando reporte del archivo activo…"
                    : activeReport.error
                    ? "No se pudo cargar el reporte del archivo activo"
                    : "No se encontraron cuentas de gastos (6*) para calcular gastos"
                  : "Selecciona un archivo procesado para ver tendencias de gastos"}
              </p>
              {activeFile && activeReport.error && (
                <p className="text-xs text-zinc-500 mt-2">
                  {activeReport.error}
                </p>
              )}
              <Button
                variant="outline"
                onClick={() => (window.location.href = "/reports")}
                className="mt-4 border-zinc-700 text-zinc-400"
              >
                Ver reportes
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Comparación entre fechas */}
      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <TrendingDown className="w-5 h-5 text-yellow-500" />
            Cambios entre reportes
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-1">
              <p className="text-xs text-zinc-500">Reporte A</p>
              <select
                value={compareAId ?? ""}
                onChange={(e) => setCompareAId(e.target.value || null)}
                className="w-full bg-zinc-800 border border-zinc-700 text-zinc-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-yellow-500"
                aria-label="Seleccionar reporte A"
              >
                <option value="">Seleccionar</option>
                {files.map((f) => (
                  <option key={f.id} value={f.id}>
                    {formatDate(f.processed_at || "")} — {f.original_filename}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <p className="text-xs text-zinc-500">Reporte B</p>
              <select
                value={compareBId ?? ""}
                onChange={(e) => setCompareBId(e.target.value || null)}
                className="w-full bg-zinc-800 border border-zinc-700 text-zinc-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-yellow-500"
                aria-label="Seleccionar reporte B"
              >
                <option value="">Seleccionar</option>
                {files.map((f) => (
                  <option key={f.id} value={f.id}>
                    {formatDate(f.processed_at || "")} — {f.original_filename}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {(reportA.isLoading || reportB.isLoading) && (
            <p className="text-sm text-zinc-400">Cargando comparación…</p>
          )}

          {(reportA.error || reportB.error) && (
            <p className="text-sm text-zinc-400">
              No se pudieron cargar ambos reportes para comparar.
            </p>
          )}

          {reportA.report &&
            reportB.report &&
            !reportA.error &&
            !reportB.error && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                {(
                  [
                    { label: "Preguntas", a: statsA.total, b: statsB.total },
                    { label: "Alta", a: statsA.high, b: statsB.high },
                    { label: "Media", a: statsA.medium, b: statsB.medium },
                    { label: "Baja", a: statsA.low, b: statsB.low },
                  ] as const
                ).map((m) => {
                  const delta = m.b - m.a;
                  const deltaText = `${delta >= 0 ? "+" : ""}${delta}`;
                  const deltaClass =
                    delta === 0
                      ? "text-zinc-400"
                      : delta > 0
                      ? "text-red-400"
                      : "text-green-400";

                  return (
                    <div
                      key={m.label}
                      className="p-4 bg-zinc-800/50 rounded-lg"
                    >
                      <p className="text-xs text-zinc-500">{m.label}</p>
                      <div className="flex items-baseline justify-between mt-1">
                        <p className="text-xl font-bold text-white">{m.b}</p>
                        <p className={`text-sm font-medium ${deltaClass}`}>
                          {deltaText}
                        </p>
                      </div>
                      <p className="text-[11px] text-zinc-500 mt-1">
                        A: {m.a} → B: {m.b}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
        </CardContent>
      </Card>
    </div>
  );
}
