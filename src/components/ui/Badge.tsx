"use client";

import type { ReactNode } from "react";

interface BadgeProps {
  children: ReactNode;
  variant?: "green" | "red" | "yellow" | "blue" | "gray" | "orange";
  size?: "sm" | "md";
}

const variantClasses: Record<string, string> = {
  green: "bg-emerald-900/60 text-emerald-300 border border-emerald-700/50",
  red: "bg-red-900/60 text-red-300 border border-red-700/50",
  yellow: "bg-yellow-900/60 text-yellow-300 border border-yellow-700/50",
  blue: "bg-blue-900/60 text-blue-300 border border-blue-700/50",
  gray: "bg-neutral-800 text-neutral-400 border border-neutral-700",
  orange: "bg-orange-900/60 text-orange-300 border border-orange-700/50",
};

export function Badge({ children, variant = "gray", size = "sm" }: BadgeProps) {
  const sizeClass = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";
  return (
    <span className={`inline-flex items-center font-semibold rounded-full ${sizeClass} ${variantClasses[variant]}`}>
      {children}
    </span>
  );
}
