import React, { useState } from "react";
import {
  Upload,
  FileText,
  AlertCircle,
  CheckCircle,
  Download,
} from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<
    "idle" | "uploading" | "processing" | "success" | "error"
  >("idle");
  const [message, setMessage] = useState("");
  const [downloadUrl, setDownloadUrl] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus("idle");
      setMessage("");
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setStatus("uploading");
    const formData = new FormData();
    formData.append("file", file);

    try {
      // 1. Upload and Process
      setStatus("processing");
      const response = await fetch("http://localhost:8000/process-document", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Error processing document");
      }

      const data = await response.json();

      if (data.status === "success") {
        setStatus("success");
        setDownloadUrl(`http://localhost:8000${data.download_url}`);
        setMessage("Document processed successfully!");
      } else {
        throw new Error(data.detail || "Unknown error");
      }
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "An error occurred");
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-50">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">
          Finance Due Diligence
        </h1>
      </div>

      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <div className="flex flex-col items-center gap-6">
          {/* Upload Area */}
          <div className="w-full">
            <label
              htmlFor="file-upload"
              className="flex flex-col items-center justify-center w-full h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <Upload className="w-12 h-12 mb-4 text-gray-500" />
                <p className="mb-2 text-sm text-gray-500">
                  <span className="font-semibold">Click to upload</span> or drag
                  and drop
                </p>
                <p className="text-xs text-gray-500">
                  Excel files (.xlsx, .xls)
                </p>
              </div>
              <input
                id="file-upload"
                type="file"
                className="hidden"
                onChange={handleFileChange}
                accept=".xlsx,.xls"
              />
            </label>
          </div>

          {/* File Info */}
          {file && (
            <div className="flex items-center gap-2 text-sm text-gray-700 bg-blue-50 px-4 py-2 rounded-full">
              <FileText className="w-4 h-4" />
              {file.name}
            </div>
          )}

          {/* Action Button */}
          <button
            onClick={handleUpload}
            disabled={
              !file || status === "uploading" || status === "processing"
            }
            className={`w-full py-3 px-4 rounded-lg text-white font-medium transition-colors ${
              !file || status === "uploading" || status === "processing"
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700"
            }`}
          >
            {status === "uploading"
              ? "Uploading..."
              : status === "processing"
              ? "Processing..."
              : "Process Document"}
          </button>

          {/* Status Messages */}
          {status === "success" && (
            <Alert className="bg-green-50 border-green-200">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertTitle className="text-green-800">Success</AlertTitle>
              <AlertDescription className="text-green-700">
                {message}
                <div className="mt-2">
                  <a
                    href={downloadUrl}
                    className="inline-flex items-center gap-2 text-sm font-medium text-green-800 hover:underline"
                    download
                  >
                    <Download className="w-4 h-4" />
                    Download Report
                  </a>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {status === "error" && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          )}
        </div>
      </div>
    </main>
  );
}
