'use client';

import React from 'react';
import { 
  BarChart3,
  TrendingUp,
  TrendingDown,
  PieChart,
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileSpreadsheet
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useActiveFile, useFiles } from '@/lib/store';
import { formatCurrency } from '@/lib/api';

// Componente para barras de progreso visual (definido fuera del render)
function PriorityBar({ 
  high, 
  medium, 
  low 
}: { 
  high: number; 
  medium: number; 
  low: number 
}) {
  const total = high + medium + low;
  if (total === 0) return null;

  const highPercent = (high / total) * 100;
  const mediumPercent = (medium / total) * 100;
  const lowPercent = (low / total) * 100;

  return (
    <div className="w-full h-3 rounded-full overflow-hidden flex bg-zinc-800">
      <div 
        className={`bg-red-500 h-full`}
        style={{ width: `${highPercent}%` }}
        title={`Alta: ${high} (${highPercent.toFixed(1)}%)`}
      />
      <div 
        className={`bg-yellow-500 h-full`}
        style={{ width: `${mediumPercent}%` }}
        title={`Media: ${medium} (${mediumPercent.toFixed(1)}%)`}
      />
      <div 
        className={`bg-green-500 h-full`}
        style={{ width: `${lowPercent}%` }}
        title={`Baja: ${low} (${lowPercent.toFixed(1)}%)`}
      />
    </div>
  );
}

export default function AnalyticsPage() {
  const { activeFile } = useActiveFile();
  const { files } = useFiles();

  // Calcular estadísticas agregadas de todos los archivos
  const totalStats = files.reduce((acc, file) => {
    if (file.status === 'success') {
      acc.totalQuestions += file.questions_generated || 0;
      acc.highPriority += file.high_priority_count || 0;
      acc.mediumPriority += file.medium_priority_count || 0;
      acc.lowPriority += file.low_priority_count || 0;
      acc.successCount += 1;
    } else if (file.status === 'error') {
      acc.errorCount += 1;
    }
    return acc;
  }, {
    totalQuestions: 0,
    highPriority: 0,
    mediumPriority: 0,
    lowPriority: 0,
    successCount: 0,
    errorCount: 0
  });

  const totalPriorities = totalStats.highPriority + totalStats.mediumPriority + totalStats.lowPriority;

  // Si hay archivo activo, usar sus estadísticas
  const currentStats = activeFile && activeFile.status === 'success' ? {
    questions: activeFile.questions_generated || 0,
    high: activeFile.high_priority_count || 0,
    medium: activeFile.medium_priority_count || 0,
    low: activeFile.low_priority_count || 0,
    revenue: activeFile.total_revenue || {},
    periods: activeFile.periods || []
  } : null;

  // Vista cuando no hay datos
  if (files.length === 0) {
    return (
      <div className="p-6">
        <div className="text-center py-16">
          <BarChart3 className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Sin datos para analizar</h2>
          <p className="text-zinc-400 mb-6">
            Sube un archivo financiero para ver las analíticas
          </p>
          <Button
            onClick={() => window.location.href = '/data'}
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
            : 'Resumen general de todos los reportes procesados'}
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
                <p className="text-2xl font-bold text-white mt-1">{files.length}</p>
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
                  {currentStats ? currentStats.questions : totalStats.totalQuestions}
                </p>
                <p className="text-xs text-zinc-500 mt-2">
                  {currentStats ? 'En archivo seleccionado' : 'En todos los reportes'}
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
                    ? `${((totalStats.highPriority / totalPriorities) * 100).toFixed(1)}% del total`
                    : 'Sin datos'}
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
              {files.slice(0, 5).map(file => (
                <div 
                  key={file.id}
                  className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg hover:bg-zinc-800 transition-colors cursor-pointer"
                  onClick={() => window.location.href = '/reports'}
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
                    {file.status === 'success' ? (
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                    ) : file.status === 'error' ? (
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
          <CardTitle className="flex items-center gap-2 text-lg">
            <TrendingUp className="w-5 h-5 text-yellow-500" />
            Tendencias de Ingresos
          </CardTitle>
        </CardHeader>
        <CardContent>
          {currentStats && currentStats.revenue && Object.keys(currentStats.revenue).length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(currentStats.revenue).map(([period, value]) => (
                <div key={period} className="p-4 bg-zinc-800/50 rounded-lg">
                  <p className="text-sm text-zinc-400">{period}</p>
                  <p className="text-xl font-bold text-white mt-1">
                    {formatCurrency(value)}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <BarChart3 className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
              <p className="text-zinc-400">
                Selecciona un archivo procesado para ver tendencias de ingresos
              </p>
              <Button
                variant="outline"
                onClick={() => window.location.href = '/reports'}
                className="mt-4 border-zinc-700 text-zinc-400"
              >
                Ver reportes
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
