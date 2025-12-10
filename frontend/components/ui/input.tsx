import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  className = "",
  ...props
}) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-semibold text-[var(--foreground)] mb-2">
          {label}
        </label>
      )}
      <input
        className={`w-full px-4 py-2.5 rounded-lg border-2 transition-all duration-200 
          ${
            error
              ? "border-[var(--error)] focus:border-[var(--error)] focus:ring-2 focus:ring-red-200"
              : "border-[var(--border)] focus:border-[var(--primary)] focus:ring-2 focus:ring-blue-200"
          } 
          bg-[var(--surface)] text-[var(--foreground)] 
          placeholder:text-[var(--muted)]
          outline-none
          ${className}`}
        {...props}
      />
      {error && <p className="mt-1 text-sm text-[var(--error)]">{error}</p>}
      {helperText && !error && (
        <p className="mt-1 text-sm text-[var(--muted)]">{helperText}</p>
      )}
    </div>
  );
};
