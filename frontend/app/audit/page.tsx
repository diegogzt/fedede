"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useActiveFile } from "@/lib/store";
import {
  getReport,
  updateReportItem,
  downloadReportWithChanges,
  QAReport,
  QAItem,
  Status,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type DraftEdits = Record<
  string,
  {
    status?: Status;
    response?: string;
    follow_up?: string;
    saving?: boolean;
    error?: string | null;
  }
>;

export default function AuditPage() {
  const { activeFile } = useActiveFile();

  const [report, setReport] = useState<QAReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<DraftEdits>({});

  useEffect(() => {
    const load = async () => {
      if (!activeFile) {
        setReport(null);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const data = await getReport(activeFile.id);
        setReport(data);
      } catch (e) {
        setReport(null);
        setError(e instanceof Error ? e.message : "Error al cargar el reporte");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [activeFile]);

  const itemsWithQuestion = useMemo(() => {
    const items = report?.items || [];
    const withQ = items.filter((i) => (i.question || "").trim().length > 0);

    // Deduplicar por account_code + question (se queda con el primero)
    const seen = new Set<string>();
    return withQ.filter((it) => {
      const key = `${it.account_code}|${(it.question || "").trim()}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [report]);

  const stats = useMemo(() => {
    const items = itemsWithQuestion;
    const byPriority = { Alta: 0, Media: 0, Baja: 0 };
    const byStatus = { Abierto: 0, "En proceso": 0, Cerrado: 0 };

    for (const item of items) {
      if (item.priority in byPriority) byPriority[item.priority] += 1;
      if (item.status in byStatus) byStatus[item.status] += 1;
    }

    return { total: items.length, byPriority, byStatus };
  }, [itemsWithQuestion]);

  const setDraft = (
    accountCode: string,
    patch: Partial<DraftEdits[string]>
  ) => {
    setDrafts((prev) => ({
      ...prev,
      [accountCode]: { ...prev[accountCode], ...patch },
    }));
  };

  const saveItem = async (item: QAItem, itemKey: string) => {
    if (!activeFile) return;

    const accountCode = item.account_code;
    const draft = drafts[itemKey] || {};

    setDraft(itemKey, { saving: true, error: null });
    try {
      const updated = await updateReportItem(activeFile.id, accountCode, {
        status: draft.status ?? item.status,
        response: draft.response ?? item.response,
        follow_up: draft.follow_up ?? item.follow_up,
      });

      setReport((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          items: prev.items.map((it) =>
            it.account_code === accountCode ? { ...it, ...updated } : it
          ),
        };
      });

      setDraft(itemKey, { saving: false, error: null });
    } catch (e) {
      setDraft(itemKey, {
        saving: false,
        error: e instanceof Error ? e.message : "Error al guardar",
      });
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Auditoría</h1>
          <p className="text-zinc-400 mt-1">
            Revisa preguntas, razones y respuestas del archivo activo.
          </p>
        </div>
        {activeFile && report && itemsWithQuestion.length > 0 && (
          <Button
            variant="outline"
            onClick={() => downloadReportWithChanges(activeFile.id)}
            className="flex items-center gap-2"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" x2="12" y1="15" y2="3" />
            </svg>
            Descargar Excel con cambios
          </Button>
        )}
      </div>

      {!activeFile && (
        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardHeader>
            <CardTitle className="text-white">Sin archivo activo</CardTitle>
          </CardHeader>
          <CardContent className="text-zinc-400 text-sm">
            Selecciona un archivo en la barra lateral para ver su auditoría.
          </CardContent>
        </Card>
      )}

      {activeFile && (
        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardHeader>
            <CardTitle className="text-white">
              {activeFile.original_filename || activeFile.name}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-zinc-400">
            {loading
              ? "Cargando reporte…"
              : error
              ? error
              : `Preguntas: ${stats.total} | Alta: ${stats.byPriority.Alta} | Media: ${stats.byPriority.Media} | Baja: ${stats.byPriority.Baja}`}
          </CardContent>
        </Card>
      )}

      {activeFile && !loading && !error && report && (
        <div className="space-y-4">
          {itemsWithQuestion.length === 0 ? (
            <Card className="border-zinc-800 bg-zinc-900/50">
              <CardHeader>
                <CardTitle className="text-white">Sin preguntas</CardTitle>
              </CardHeader>
              <CardContent className="text-zinc-400 text-sm">
                Este reporte no contiene preguntas generadas con los umbrales
                actuales.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {itemsWithQuestion.map((item, idx) => {
                // Usamos índice + account_code para evitar keys duplicadas
                const itemKey = `${idx}_${item.account_code}`;
                const draft = drafts[itemKey] || {};

                const statusValue =
                  (draft.status ?? item.status) || ("Abierto" as Status);
                const responseValue = draft.response ?? item.response ?? "";
                const followUpValue = draft.follow_up ?? item.follow_up ?? "";

                return (
                  <Card
                    key={itemKey}
                    className="border-zinc-800 bg-zinc-900/50"
                  >
                    <CardHeader>
                      <CardTitle className="text-white text-base">
                        {item.account_code} — {item.description}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
                        <div className="lg:col-span-2">
                          <p className="text-xs text-zinc-500 mb-1">Pregunta</p>
                          <pre className="whitespace-pre-wrap text-sm text-white bg-zinc-950/60 border border-zinc-800 rounded-lg p-3">
                            {item.question}
                          </pre>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500 mb-1">Razón</p>
                          <div className="text-xs text-zinc-300 bg-zinc-950/60 border border-zinc-800 rounded-lg p-3 whitespace-pre-wrap">
                            {item.reason || "(sin razón)"}
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
                        <div>
                          <p className="text-xs text-zinc-500 mb-1">
                            Prioridad
                          </p>
                          <div className="text-sm text-white">
                            {item.priority}
                          </div>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500 mb-1">Estado</p>
                          <select
                            value={statusValue}
                            onChange={(e) =>
                              setDraft(itemKey, {
                                status: e.target.value as Status,
                              })
                            }
                            className="w-full bg-zinc-900 border border-zinc-700 text-zinc-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-yellow-500"
                            aria-label="Estado"
                          >
                            <option value="Abierto">Abierto</option>
                            <option value="En proceso">En proceso</option>
                            <option value="Cerrado">Cerrado</option>
                          </select>
                        </div>
                        <div className="flex items-end justify-end">
                          <Button
                            onClick={() => saveItem(item, itemKey)}
                            disabled={!!draft.saving}
                            className="bg-yellow-500 text-black hover:bg-yellow-400"
                          >
                            {draft.saving ? "Guardando…" : "Guardar"}
                          </Button>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                        <div>
                          <p className="text-xs text-zinc-500 mb-1">
                            Respuesta
                          </p>
                          <textarea
                            value={responseValue}
                            onChange={(e) =>
                              setDraft(itemKey, {
                                response: e.target.value,
                              })
                            }
                            rows={3}
                            aria-label="Respuesta"
                            className="w-full bg-zinc-900 border border-zinc-700 text-zinc-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-yellow-500"
                          />
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500 mb-1">
                            Seguimiento
                          </p>
                          <textarea
                            value={followUpValue}
                            onChange={(e) =>
                              setDraft(itemKey, {
                                response: followUpValue,
                                follow_up: e.target.value,
                              })
                            }
                            rows={3}
                            aria-label="Seguimiento"
                            className="w-full bg-zinc-900 border border-zinc-700 text-zinc-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-yellow-500"
                          />
                        </div>
                      </div>

                      {draft.error && (
                        <div className="text-sm text-red-400">
                          {draft.error}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
