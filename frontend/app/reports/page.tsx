'use client';

import React, { useEffect, useState } from 'react';
import { 
  FileSpreadsheet, 
  Download, 
  Trash2, 
  Search,
  Filter,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ChevronDown,
  Eye
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useFiles, useActiveFile, documentToFileData } from '@/lib/store';
import { 
  getHistory, 
  downloadReport, 
  deleteDocument, 
  formatDate,
  ProcessedDocument 
} from '@/lib/api';

type StatusFilter = 'all' | 'success' | 'error' | 'processing';

export default function ReportsPage() {
  const { files, setFiles, removeFile } = useFiles();
  const { setActiveFile } = useActiveFile();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [showFilters, setShowFilters] = useState(false);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const documents = await getHistory();
      const fileDataList = documents.map((doc: ProcessedDocument) => documentToFileData(doc));
      setFiles(fileDataList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar el historial');
    } finally {
      setLoading(false);
    }
  };

  // Cargar historial al montar
  useEffect(() => {
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleDownload = (filename: string) => {
    downloadReport(filename);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de que quieres eliminar este reporte?')) return;
    
    try {
      const success = await deleteDocument(id);
      if (success) {
        removeFile(id);
      }
    } catch (err) {
      console.error('Error al eliminar:', err);
    }
  };

  const handleSelect = (file: typeof files[0]) => {
    setActiveFile(file);
    // Navegar al dashboard
    window.location.href = '/';
  };

  // Filtrar archivos
  const filteredFiles = files.filter(file => {
    const originalFilename = file.original_filename || '';
    const filename = file.filename || '';
    const matchesSearch = originalFilename.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         filename.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || file.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-500 animate-spin" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-zinc-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge variant="success">Completado</Badge>;
      case 'error':
        return <Badge variant="error">Error</Badge>;
      case 'processing':
        return <Badge variant="warning">Procesando</Badge>;
      default:
        return <Badge>Desconocido</Badge>;
    }
  };

  const getPriorityStats = (file: typeof files[0]) => {
    const high = file.high_priority_count || 0;
    const medium = file.medium_priority_count || 0;
    const low = file.low_priority_count || 0;
    const total = high + medium + low;
    
    if (total === 0) return null;
    
    return (
      <div className="flex items-center gap-2 text-xs">
        {high > 0 && (
          <span className="px-2 py-0.5 bg-red-500/10 text-red-400 rounded">
            {high} Alta
          </span>
        )}
        {medium > 0 && (
          <span className="px-2 py-0.5 bg-yellow-500/10 text-yellow-400 rounded">
            {medium} Media
          </span>
        )}
        {low > 0 && (
          <span className="px-2 py-0.5 bg-green-500/10 text-green-400 rounded">
            {low} Baja
          </span>
        )}
      </div>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Reportes</h1>
          <p className="text-zinc-400 mt-1">
            Gestiona y descarga los análisis Q&A generados
          </p>
        </div>
        <Button
          onClick={loadHistory}
          disabled={loading}
          className="bg-zinc-800 text-white hover:bg-zinc-700"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>

      {/* Search and Filters */}
      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <input
                type="text"
                placeholder="Buscar por nombre de archivo..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-zinc-700 bg-zinc-800 text-white placeholder-zinc-500 focus:border-yellow-500 focus:outline-none"
              />
            </div>
            
            {/* Filter Toggle */}
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className={`border-zinc-700 ${showFilters ? 'text-yellow-500' : 'text-zinc-400'}`}
            >
              <Filter className="w-4 h-4 mr-2" />
              Filtros
              <ChevronDown className={`w-4 h-4 ml-2 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
            </Button>
          </div>

          {/* Filter Options */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t border-zinc-800">
              <div className="flex items-center gap-2">
                <span className="text-sm text-zinc-400">Estado:</span>
                {(['all', 'success', 'error', 'processing'] as StatusFilter[]).map(status => (
                  <button
                    key={status}
                    onClick={() => setStatusFilter(status)}
                    className={`px-3 py-1 rounded-lg text-sm transition-colors
                      ${statusFilter === status 
                        ? 'bg-yellow-500 text-black' 
                        : 'bg-zinc-800 text-zinc-400 hover:text-white'
                      }`}
                  >
                    {status === 'all' ? 'Todos' : 
                     status === 'success' ? 'Completados' :
                     status === 'error' ? 'Con errores' : 'Procesando'}
                  </button>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
        <Card className="border-red-500/30 bg-red-500/5">
          <CardContent className="p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <p className="text-red-400">{error}</p>
            <Button
              onClick={loadHistory}
              size="sm"
              className="ml-auto bg-red-500/20 text-red-400 hover:bg-red-500/30"
            >
              Reintentar
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Reports List */}
      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardHeader className="pb-0">
          <CardTitle className="text-lg flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-yellow-500" />
            Documentos Procesados
            <span className="text-sm font-normal text-zinc-500">
              ({filteredFiles.length} de {files.length})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading && files.length === 0 ? (
            <div className="p-8 text-center">
              <RefreshCw className="w-8 h-8 text-yellow-500 animate-spin mx-auto mb-4" />
              <p className="text-zinc-400">Cargando reportes...</p>
            </div>
          ) : filteredFiles.length === 0 ? (
            <div className="p-8 text-center">
              <FileSpreadsheet className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
              <p className="text-zinc-400">
                {files.length === 0 
                  ? 'No hay reportes generados aún' 
                  : 'No se encontraron reportes con los filtros aplicados'}
              </p>
              {files.length === 0 && (
                <Button
                  onClick={() => window.location.href = '/data'}
                  className="mt-4 bg-yellow-500 text-black hover:bg-yellow-400"
                >
                  Subir primer archivo
                </Button>
              )}
            </div>
          ) : (
            <div className="divide-y divide-zinc-800">
              {filteredFiles.map(file => (
                <div
                  key={file.id}
                  className="p-4 hover:bg-zinc-800/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    {/* File Info */}
                    <div className="flex items-start gap-4 flex-1">
                      <div className="p-3 rounded-lg bg-zinc-800">
                        <FileSpreadsheet className="w-6 h-6 text-yellow-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-white font-medium truncate">
                            {file.original_filename}
                          </h3>
                          {getStatusBadge(file.status)}
                        </div>
                        <div className="flex items-center gap-4 text-sm text-zinc-500">
                          <span className="flex items-center gap-1">
                            {getStatusIcon(file.status)}
                            {formatDate(file.processed_at)}
                          </span>
                          {file.questions_generated !== undefined && (
                            <span>{file.questions_generated} preguntas</span>
                          )}
                        </div>
                        {file.status === 'success' && getPriorityStats(file)}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      {file.status === 'success' && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleSelect(file)}
                            className="border-zinc-700 text-zinc-400 hover:text-white"
                            title="Ver en dashboard"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownload(file.filename)}
                            className="border-zinc-700 text-zinc-400 hover:text-white"
                            title="Descargar"
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                        </>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(file.id)}
                        className="border-zinc-700 text-red-400 hover:text-red-300 hover:border-red-500/50"
                        title="Eliminar"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
