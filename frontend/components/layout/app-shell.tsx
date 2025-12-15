"use client";

import { AppProvider, documentToFileData, useApp, useFiles } from "@/lib/store";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import React, { useEffect } from "react";
import { getHistory, ProcessedDocument } from "@/lib/api";

interface AppShellProps {
  children: React.ReactNode;
}

function AppBootstrap() {
  const { files, setFiles } = useFiles();
  const { setLoading, setError } = useApp();

  useEffect(() => {
    const load = async () => {
      if (files.length > 0) return;
      setLoading(true);
      try {
        const documents = await getHistory();
        const fileDataList = documents.map((doc: ProcessedDocument) =>
          documentToFileData(doc)
        );
        setFiles(fileDataList);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al cargar datos");
      } finally {
        setLoading(false);
      }
    };
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <AppProvider>
      <AppBootstrap />
      <div className="flex h-screen w-full">
        <Sidebar />
        <div className="flex-1 flex flex-col h-screen overflow-hidden">
          <Topbar />
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
    </AppProvider>
  );
}
