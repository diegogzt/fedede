import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: {
    compilationMode: "annotation", // Solo compila componentes con "use memo"
  },
};

export default nextConfig;
