import React from "react";
import { BarChart3 } from "lucide-react";

export const Logo = () => {
  return (
    <div className="flex items-center gap-3">
      <div className="bg-[var(--primary)] p-2 rounded-lg shadow-lg">
        <BarChart3 className="w-6 h-6 text-white" />
      </div>
      <div className="flex flex-col">
        <span className="text-xl font-bold text-[var(--primary)] leading-none tracking-tight">
          FEDEDE
        </span>
        <span className="text-[10px] font-medium text-[var(--secondary)] uppercase tracking-widest">
          Financial Due Diligence
        </span>
      </div>
    </div>
  );
};
