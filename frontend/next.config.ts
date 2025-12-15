import type { NextConfig } from "next";

const backendUrl =
  process.env.BACKEND_URL ||
  `http://127.0.0.1:${process.env.BACKEND_PORT || "8000"}`;

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: {
    compilationMode: "annotation", // Solo compila componentes con "use memo"
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
