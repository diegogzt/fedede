"use client";

import Link from "next/link";
import React from "react";
import { useActiveFile, useFiles, useConfig } from "@/lib/store";
import { checkHealth, formatDate } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  const { activeFile } = useActiveFile();
  const { files } = useFiles();
  const { config, updateConfig } = useConfig();
  const [health, setHealth] = React.useState<{
    status: string;
    version?: string;
  } | null>(null);
  const [healthError, setHealthError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        const h = await checkHealth();
        if (!cancelled) {
          setHealth(h);
          setHealthError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setHealth(null);
          setHealthError(
            e instanceof Error ? e.message : "No se pudo conectar al backend"
          );
        }
      }
    };
    run();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-white">Configuración</h1>
        <p className="text-sm text-zinc-400 mt-1">
          Ajustes del sistema y enlaces rápidos.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardHeader>
            <CardTitle className="text-white">Interfaz y Navegación</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg border border-zinc-800 bg-zinc-900/40">
              <div>
                <p className="text-sm font-medium text-white">
                  Mostrar opciones avanzadas
                </p>
                <p className="text-xs text-zinc-500">
                  Habilita las secciones de Auditoría y Analíticas en la barra
                  lateral.
                </p>
              </div>
              <input
                type="checkbox"
                checked={config.show_advanced_sections}
                onChange={(e) =>
                  updateConfig({ show_advanced_sections: e.target.checked })
                }
                className="h-5 w-5 accent-yellow-500 cursor-pointer"
              />
            </div>
          </CardContent>
        </Card>

        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardHeader>
            <CardTitle className="text-white">Estado del sistema</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-zinc-300 space-y-3">
            {health ? (
              <div className="space-y-1">
                <p>
                  Backend: <span className="text-green-400">OK</span>
                </p>
                {health.version && (
                  <p className="text-zinc-400">Versión: {health.version}</p>
                )}
              </div>
            ) : (
              <div className="space-y-1">
                <p>
                  Backend: <span className="text-red-400">No disponible</span>
                </p>
                {healthError && <p className="text-zinc-400">{healthError}</p>}
              </div>
            )}

            <div className="pt-2">
              <Link href="/data">
                <Button className="bg-yellow-500 text-black hover:bg-yellow-400">
                  Ir a Cargar datos
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardHeader>
            <CardTitle className="text-white">Archivo activo</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-zinc-300 space-y-3">
            {activeFile ? (
              <div className="space-y-1">
                <p className="text-white font-medium">
                  {activeFile.original_filename || activeFile.name}
                </p>
                <p className="text-zinc-400">
                  Procesado: {formatDate(activeFile.processed_at || "")}
                </p>
                <p className="text-zinc-500">
                  Historial: {files.length} archivo(s)
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                <p className="text-zinc-400">
                  No hay archivo activo seleccionado.
                </p>
                <p className="text-zinc-500">
                  Historial: {files.length} archivo(s)
                </p>
              </div>
            )}

            <div className="flex gap-2">
              <Link href="/reports">
                <Button
                  variant="outline"
                  className="border-zinc-700 text-zinc-300"
                >
                  Ver reportes
                </Button>
              </Link>
              <Link href="/analytics">
                <Button
                  variant="outline"
                  className="border-zinc-700 text-zinc-300"
                >
                  Ver analíticas
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardHeader>
          <CardTitle className="text-white">Umbrales de análisis</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-zinc-300 space-y-3">
          <p>
            Los umbrales se configuran al procesar un archivo en{" "}
            <Link href="/data" className="text-yellow-500 hover:underline">
              Cargar datos
            </Link>
            .
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
