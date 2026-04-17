"use client";
import { motion } from "framer-motion";

interface FPRGaugeProps {
  value: number; // 0–100
  target: number;
  label: string;
}

export function FPRGauge({ value, target, label }: FPRGaugeProps) {
  const isGood = value <= target;
  const color = isGood ? "#10B981" : "#EF4444";
  const pct = Math.min(value / (target * 2), 1); // normalize to 0-1 within 2x target

  // SVG arc parameters
  const r = 52;
  const cx = 70;
  const cy = 70;
  const startAngle = -210;
  const endAngle = 30;
  const totalAngle = endAngle - startAngle;
  const valueAngle = startAngle + totalAngle * pct;

  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const arcPath = (angle: number) =>
    `${cx + r * Math.cos(toRad(angle))},${cy + r * Math.sin(toRad(angle))}`;

  const largeArc = valueAngle - startAngle > 180 ? 1 : 0;

  return (
    <div className="flex flex-col items-center">
      <div className="relative group">
        <svg width="140" height="100" viewBox="0 0 140 100">
          {/* Track */}
          <path
            d={`M ${arcPath(startAngle)} A ${r} ${r} 0 1 1 ${arcPath(endAngle)}`}
            fill="none"
            stroke="rgba(255,255,255,0.07)"
            strokeWidth="10"
            strokeLinecap="round"
          />
          {/* Value arc */}
          <motion.path
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.5, ease: "easeOut", delay: 0.5 }}
            d={`M ${arcPath(startAngle)} A ${r} ${r} 0 ${largeArc} 1 ${arcPath(valueAngle)}`}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 8px ${color}40)` }}
          />
          {/* Center text */}
          <text x={cx} y={cy - 4} textAnchor="middle" fill="white" fontSize="18" fontWeight="800">
            {value.toFixed(1)}%
          </text>
          <text x={cx} y={cy + 14} textAnchor="middle" fill="#6B7280" fontSize="9" fontWeight="500">
            TRGT &lt;{target}%
          </text>
        </svg>

        {/* Hover indicator */}
        <motion.div 
          className="absolute inset-0 bg-white shadow-[0_0_30px_rgba(255,255,255,0.03)] rounded-full -z-10 opacity-0 group-hover:opacity-100 transition-opacity"
        />
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        className={`text-[10px] uppercase font-bold tracking-widest mt-1 ${isGood ? "text-emerald-500" : "text-red-500"}`}
      >
        {isGood ? "Optimal Performance" : "Attention Required"}
      </motion.div>
      <div className="text-[11px] font-medium text-gray-500 mt-0.5">{label}</div>
    </div>
  );
}
