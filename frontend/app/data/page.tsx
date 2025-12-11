'use client';

import React, { useState, useCallback } from 'react';
import { 
  Upload, 
  FileSpreadsheet, 
  X, 
  AlertCircle, 
  Settings, 
  Sparkles,
  Languages,
  Calendar,
  TrendingUp,
  DollarSign,
  Loader2,
  CheckCircle2,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useApp, useConfig, configToProcessConfig, documentToFileData } from '@/lib/store';
import { processDocument, Language } from '@/lib/api';

export default function DataPage() {
  const { addFile, setLoading, setError } = useApp();
  const { config, updateConfig } = useConfig();
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [fileError, setFileError] = useState<string>('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [success, setSuccess] = useState(false);
  const [resultMessage, setResultMessage] = useState('');

  const accept = '.xlsx,.xls,.xlsm,.csv,.txt';
  const maxSize = 100; // MB

  const validateFile = (file: File): boolean => {
    setFileError('');
    
    const validExtensions = accept.split(',').map(ext => ext.trim());
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!validExtensions.includes(fileExtension)) {
      setFileError(`Formato no válido. Solo se aceptan: ${accept}`);
      return false;
    }
    
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxSize) {
      setFileError(`El archivo es muy grande. Máximo ${maxSize}MB`);
      return false;
    }
    
    return true;
  };

  const handleFile = useCallback((file: File) => {
    if (validateFile(file)) {
      setSelectedFile(file);
      setSuccess(false);
      setResultMessage('');
    }
  }, []);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, [handleFile]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setFileError('');
    setSuccess(false);
    setResultMessage('');
  };

  const handleProcess = async () => {
    if (!selectedFile) return;
    
    setProcessing(true);
    setLoading(true);
    setError(null);
    setSuccess(false);
    
    try {
      const result = await processDocument(selectedFile, configToProcessConfig(config));
      
      if (result.success) {
        setSuccess(true);
        setResultMessage(result.message);
        
        // Agregar al store si hay documento
        if (result.document) {
          addFile(documentToFileData(result.document));
        }
      } else {
        setError(result.error || 'Error al procesar el documento');
        setFileError(result.error || 'Error al procesar el documento');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error de conexión con el servidor';
      setError(errorMessage);
      setFileError(errorMessage);
    } finally {
      setProcessing(false);
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const languageOptions: { value: Language; label: string; description: string }[] = [
    { value: 'es', label: 'Español', description: 'Genera reporte en español' },
    { value: 'en', label: 'English', description: 'Generate report in English' },
    { value: 'both', label: 'Bilingüe', description: 'Genera ambos idiomas' },
  ];

  return (
    <div className="p-6 space-y-6 w-full">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Cargar Datos</h1>
        <p className="text-zinc-400 mt-1">
          Sube un archivo financiero Excel o CSV para generar el análisis Q&A
        </p>
      </div>

      {/* File Upload Zone */}
      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardContent className="p-0">
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 transition-all duration-200 cursor-pointer
              ${dragActive 
                ? 'border-yellow-500 bg-yellow-500/5' 
                : fileError 
                  ? 'border-red-500 bg-red-500/5' 
                  : success
                    ? 'border-green-500 bg-green-500/5'
                    : 'border-zinc-700 hover:border-yellow-500/50 hover:bg-zinc-800/50'
              }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <input
              id="file-input"
              type="file"
              accept={accept}
              onChange={handleChange}
              className="hidden"
              aria-label="Seleccionar archivo"
            />

            {!selectedFile ? (
              <div className="flex flex-col items-center gap-4">
                <div className={`p-4 rounded-full ${dragActive ? 'bg-yellow-500/20' : 'bg-zinc-800'}`}>
                  <Upload className={`w-8 h-8 ${dragActive ? 'text-yellow-500' : 'text-zinc-400'}`} />
                </div>
                <div className="text-center">
                  <p className="text-white font-medium">
                    Arrastra un archivo aquí o haz clic para seleccionar
                  </p>
                  <p className="text-zinc-500 text-sm mt-1">
                    Soporta Excel (.xlsx, .xls, .xlsm) y CSV (.csv, .txt) hasta {maxSize}MB
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between" onClick={e => e.stopPropagation()}>
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg ${success ? 'bg-green-500/20' : 'bg-yellow-500/20'}`}>
                    {success ? (
                      <CheckCircle2 className="w-6 h-6 text-green-500" />
                    ) : (
                      <FileSpreadsheet className="w-6 h-6 text-yellow-500" />
                    )}
                  </div>
                  <div>
                    <p className="text-white font-medium">{selectedFile.name}</p>
                    <p className="text-zinc-500 text-sm">{formatFileSize(selectedFile.size)}</p>
                    {success && resultMessage && (
                      <p className="text-green-400 text-sm mt-1">{resultMessage}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={removeFile}
                  className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
                  aria-label="Eliminar archivo"
                >
                  <X className="w-5 h-5 text-zinc-400 hover:text-white" />
                </button>
              </div>
            )}
          </div>

          {fileError && (
            <div className="flex items-center gap-2 text-red-400 text-sm p-4 border-t border-zinc-800">
              <AlertCircle className="w-4 h-4" />
              {fileError}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Configuration Section */}
      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Settings className="w-5 h-5 text-yellow-500" />
              Configuración del Análisis
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-zinc-400 hover:text-white"
            >
              {showAdvanced ? 'Ocultar avanzado' : 'Mostrar avanzado'}
              {showAdvanced ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Idioma */}
          <div className="space-y-3">
            <label className="flex items-center gap-2 text-sm font-medium text-zinc-300">
              <Languages className="w-4 h-4 text-yellow-500" />
              Idioma del Reporte
            </label>
            <div className="grid grid-cols-3 gap-3">
              {languageOptions.map(option => (
                <button
                  key={option.value}
                  onClick={() => updateConfig({ language: option.value })}
                  className={`p-3 rounded-lg border transition-all text-left
                    ${config.language === option.value
                      ? 'border-yellow-500 bg-yellow-500/10 text-white'
                      : 'border-zinc-700 bg-zinc-800/50 text-zinc-400 hover:border-zinc-600'
                    }`}
                >
                  <p className="font-medium">{option.label}</p>
                  <p className="text-xs text-zinc-500 mt-1">{option.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Opciones Avanzadas */}
          {showAdvanced && (
            <div className="space-y-4 pt-4 border-t border-zinc-800">
              {/* Años Fiscales */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-medium text-zinc-300">
                    <Calendar className="w-4 h-4 text-yellow-500" />
                    Año Fiscal Inicio
                  </label>
                  <input
                    type="number"
                    value={config.fiscal_year_start}
                    onChange={e => updateConfig({ fiscal_year_start: parseInt(e.target.value) || 2023 })}
                    className="w-full px-3 py-2 rounded-lg border border-zinc-700 bg-zinc-800 text-white focus:border-yellow-500 focus:outline-none"
                    min={2000}
                    max={2030}
                    placeholder="2023"
                    aria-label="Año fiscal de inicio"
                  />
                </div>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-medium text-zinc-300">
                    <Calendar className="w-4 h-4 text-yellow-500" />
                    Año Fiscal Fin
                  </label>
                  <input
                    type="number"
                    value={config.fiscal_year_end}
                    onChange={e => updateConfig({ fiscal_year_end: parseInt(e.target.value) || 2024 })}
                    className="w-full px-3 py-2 rounded-lg border border-zinc-700 bg-zinc-800 text-white focus:border-yellow-500 focus:outline-none"
                    min={2000}
                    max={2030}
                    placeholder="2024"
                    aria-label="Año fiscal de fin"
                  />
                </div>
              </div>

              {/* Umbrales */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-medium text-zinc-300">
                    <TrendingUp className="w-4 h-4 text-yellow-500" />
                    Umbral de Variación (%)
                  </label>
                  <input
                    type="number"
                    value={config.variation_threshold}
                    onChange={e => updateConfig({ variation_threshold: parseFloat(e.target.value) || 20 })}
                    className="w-full px-3 py-2 rounded-lg border border-zinc-700 bg-zinc-800 text-white focus:border-yellow-500 focus:outline-none"
                    min={0}
                    max={100}
                    step={5}
                    placeholder="20"
                    aria-label="Umbral de variación porcentual"
                  />
                  <p className="text-xs text-zinc-500">
                    Variaciones por encima de este % generarán preguntas
                  </p>
                </div>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm font-medium text-zinc-300">
                    <DollarSign className="w-4 h-4 text-yellow-500" />
                    Umbral de Materialidad (€)
                  </label>
                  <input
                    type="number"
                    value={config.materiality_threshold}
                    onChange={e => updateConfig({ materiality_threshold: parseInt(e.target.value) || 100000 })}
                    className="w-full px-3 py-2 rounded-lg border border-zinc-700 bg-zinc-800 text-white focus:border-yellow-500 focus:outline-none"
                    min={0}
                    step={10000}
                    placeholder="100000"
                    aria-label="Umbral de materialidad en euros"
                  />
                  <p className="text-xs text-zinc-500">
                    Variaciones absolutas por encima de este valor
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Process Button */}
      <div className="flex justify-end gap-3">
        {selectedFile && !success && (
          <Button
            variant="outline"
            onClick={removeFile}
            disabled={processing}
            className="border-zinc-700 text-zinc-400 hover:text-white"
          >
            Cancelar
          </Button>
        )}
        <Button
          onClick={handleProcess}
          disabled={!selectedFile || processing || success}
          className="bg-yellow-500 text-black hover:bg-yellow-400 disabled:opacity-50 disabled:cursor-not-allowed px-8"
        >
          {processing ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Procesando...
            </>
          ) : success ? (
            <>
              <CheckCircle2 className="w-4 h-4 mr-2" />
              Procesado
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-2" />
              Generar Análisis Q&A
            </>
          )}
        </Button>
      </div>

      {/* Success Actions */}
      {success && (
        <Card className="border-green-500/30 bg-green-500/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-6 h-6 text-green-500" />
                <div>
                  <p className="text-white font-medium">¡Análisis completado!</p>
                  <p className="text-zinc-400 text-sm">El reporte Q&A ha sido generado correctamente</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={removeFile}
                  className="border-zinc-700 text-zinc-400 hover:text-white"
                >
                  Subir otro archivo
                </Button>
                <Button
                  onClick={() => window.location.href = '/reports'}
                  className="bg-yellow-500 text-black hover:bg-yellow-400"
                >
                  Ver Reportes
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
