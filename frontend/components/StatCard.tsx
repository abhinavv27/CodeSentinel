"use client";
import { motion, useSpring, useTransform } from "framer-motion";
import { useEffect } from "react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  accent: "violet" | "critical" | "warning" | "success" | "info";
  trend?: { value: number; label: string };
  delay?: number;
}

const ACCENT_STYLES = {
  violet: {
    border: "border-violet-500/20",
    icon: "bg-violet-500/10 text-violet-400",
    value: "text-violet-100",
    glow: "shadow-[0_0_30px_-10px_rgba(139,92,246,0.3)]",
  },
  critical: {
    border: "border-red-500/20",
    icon: "bg-red-500/10 text-red-400",
    value: "text-red-100",
    glow: "shadow-[0_0_30px_-10px_rgba(239,68,68,0.2)]",
  },
  warning: {
    border: "border-amber-500/20",
    icon: "bg-amber-500/10 text-amber-400",
    value: "text-amber-100",
    glow: "shadow-[0_0_30px_-10px_rgba(245,158,11,0.2)]",
  },
  success: {
    border: "border-emerald-500/20",
    icon: "bg-emerald-500/10 text-emerald-400",
    value: "text-emerald-100",
    glow: "shadow-[0_0_30px_-10px_rgba(16,185,129,0.2)]",
  },
  info: {
    border: "border-blue-500/20",
    icon: "bg-blue-500/10 text-blue-400",
    value: "text-blue-100",
    glow: "shadow-[0_0_30px_-10px_rgba(59,130,246,0.2)]",
  },
};

export function StatCard({ title, value, subtitle, icon, accent, trend, delay = 0 }: StatCardProps) {
  const styles = ACCENT_STYLES[accent];
  const isNumeric = typeof value === "number";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: delay * 0.1, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -5, scale: 1.01 }}
      className={`
        glass-card p-6 overflow-hidden relative group
        ${styles.border} ${styles.glow}
      `}
    >
      <div className="shimmer-mask" />
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <motion.div 
            className={`w-10 h-10 rounded-lg flex items-center justify-center ${styles.icon}`}
            whileHover={{ scale: 1.1, rotate: 5 }}
          >
            {icon}
          </motion.div>
          {trend && (
            <div className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
              trend.value >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
            }`}>
              {trend.value >= 0 ? "+" : ""}{trend.value}%
            </div>
          )}
        </div>

        <div className="space-y-1">
          <div className={`text-3xl font-black font-mono tracking-tighter ${styles.value}`}>
            {isNumeric ? <AnimatedNumber value={value as number} /> : value}
          </div>
          <div className="text-xs font-bold text-gray-500 uppercase tracking-widest">{title}</div>
          {subtitle && (
            <div className="text-[10px] text-gray-600 font-medium">{subtitle}</div>
          )}
        </div>
      </div>

      {/* Subtle decorative element */}
      <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-white/2 rounded-full blur-2xl group-hover:bg-white/5 transition-colors" />
    </motion.div>
  );
}

function AnimatedNumber({ value }: { value: number }) {
  const spring = useSpring(0, { stiffness: 45, damping: 15 });
  const display = useTransform(spring, (v) => Math.floor(v).toLocaleString());

  useEffect(() => {
    spring.set(value);
  }, [value, spring]);

  return <motion.span>{display}</motion.span>;
}

