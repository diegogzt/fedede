import React from "react";
import { FileText, Download, Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface Document {
  id: number;
  filename: string;
  processed_at: string;
  status: string;
  output_path: string;
}

interface HistoryTableProps {
  documents: Document[];
}

export const HistoryTable: React.FC<HistoryTableProps> = ({ documents }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("es-ES", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center bg-gray-50/50 rounded-lg border border-dashed border-gray-200">
        <Clock className="w-10 h-10 text-gray-300 mb-3" />
        <p className="text-gray-500 font-medium">No hay actividad reciente</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-white shadow-sm">
      <table className="w-full text-sm text-left">
        <thead className="bg-gray-50 text-[10px] uppercase text-gray-500 font-semibold border-b border-[var(--border)]">
          <tr>
            <th className="px-4 py-3">Documento</th>
            <th className="px-4 py-3">Fecha</th>
            <th className="px-4 py-3">Estado</th>
            <th className="px-4 py-3 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {documents.map((doc) => (
            <tr
              key={doc.id}
              className="hover:bg-blue-50/30 transition-colors group"
            >
              <td className="px-4 py-3 font-medium text-[var(--foreground)] flex items-center gap-3">
                <div className="p-1.5 bg-blue-50 rounded text-[var(--primary)] group-hover:bg-[var(--primary)] group-hover:text-white transition-colors">
                  <FileText size={14} />
                </div>
                {doc.filename}
              </td>
              <td className="px-4 py-3 text-[var(--muted)]">
                {formatDate(doc.processed_at)}
              </td>
              <td className="px-4 py-3">
                <Badge variant={doc.status === "success" ? "success" : "error"}>
                  {doc.status}
                </Badge>
              </td>
              <td className="px-4 py-3 text-right">
                <button className="text-[var(--primary)] hover:text-[var(--secondary)] font-medium text-xs flex items-center justify-end gap-1 ml-auto transition-colors">
                  <Download size={14} />
                  Descargar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
