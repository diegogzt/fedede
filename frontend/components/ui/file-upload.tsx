"use client";

import React, { useCallback, useState } from "react";
import { Upload, FileSpreadsheet, X, AlertCircle } from "lucide-react";
import { Card, CardContent } from "./card";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  maxSize?: number; // in MB
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  accept = ".xlsx,.xls,.csv",
  maxSize = 10,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string>("");

  const validateFile = useCallback(
    (file: File): boolean => {
      setError("");

      // Validar extensión
      const validExtensions = accept.split(",").map((ext) => ext.trim());
      const fileExtension = "." + file.name.split(".").pop()?.toLowerCase();

      if (!validExtensions.includes(fileExtension)) {
        setError(`Formato no válido. Solo se aceptan: ${accept}`);
        return false;
      }

      // Validar tamaño
      const fileSizeMB = file.size / (1024 * 1024);
      if (fileSizeMB > maxSize) {
        setError(`El archivo es muy grande. Máximo ${maxSize}MB`);
        return false;
      }

      return true;
    },
    [accept, maxSize]
  );

  const handleFile = useCallback(
    (file: File) => {
      if (validateFile(file)) {
        setSelectedFile(file);
        onFileSelect(file);
      }
    },
    [onFileSelect, validateFile]
  );

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFile(e.dataTransfer.files[0]);
      }
    },
    [handleFile]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setError("");
  };

  return (
    <div className="w-full">
      <Card>
        <CardContent className="p-0">
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 transition-all duration-200
              ${
                dragActive
                  ? "border-[var(--primary)] bg-blue-50"
                  : error
                  ? "border-[var(--error)] bg-red-50"
                  : "border-[var(--border)] hover:border-[var(--primary)]"
              }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept={accept}
              onChange={handleChange}
            />

            {!selectedFile ? (
              <label
                htmlFor="file-upload"
                className="flex flex-col items-center justify-center cursor-pointer"
              >
                <div className="w-16 h-16 mb-4 rounded-full bg-blue-100 flex items-center justify-center">
                  <Upload className="w-8 h-8 text-[var(--primary)]" />
                </div>

                <h3 className="text-lg font-semibold text-[var(--foreground)] mb-2">
                  Arrastra tu archivo aquí
                </h3>

                <p className="text-sm text-[var(--muted)] mb-4">
                  o haz clic para seleccionar
                </p>

                <p className="text-xs text-[var(--muted)]">
                  Formatos aceptados: {accept} (Máximo {maxSize}MB)
                </p>
              </label>
            ) : (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center">
                    <FileSpreadsheet className="w-6 h-6 text-green-600" />
                  </div>

                  <div>
                    <p className="font-semibold text-[var(--foreground)]">
                      {selectedFile.name}
                    </p>
                    <p className="text-sm text-[var(--muted)]">
                      {(selectedFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>

                <button
                  onClick={removeFile}
                  className="p-2 rounded-full hover:bg-red-100 transition-colors"
                  type="button"
                >
                  <X className="w-5 h-5 text-[var(--error)]" />
                </button>
              </div>
            )}
          </div>

          {error && (
            <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-[var(--error)] flex-shrink-0 mt-0.5" />
              <p className="text-sm text-[var(--error)]">{error}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
