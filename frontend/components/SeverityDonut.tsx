"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

interface SeverityDonutProps {
  data: Record<string, number>;
}

const SEVERITY_CONFIG = {
  critical: { color: "#EF4444", label: "Critical" },
  warning: { color: "#F59E0B", label: "Warning" },
  info: { color: "#3B82F6", label: "Info" },
};

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: { name: string; value: number; payload: { color: string } }[] }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-black/90 border border-white/10 rounded-xl px-4 py-3 shadow-2xl backdrop-blur-xl">
        <p className="text-[10px] font-black uppercase tracking-widest mb-1" style={{ color: payload[0].payload.color }}>
          {payload[0].name}
        </p>
        <p className="text-xl font-black text-white tracking-tighter">{payload[0].value}</p>
      </div>
    );
  }
  return null;
};

export function SeverityDonut({ data }: SeverityDonutProps) {
  const chartData = Object.entries(SEVERITY_CONFIG).map(([key, cfg]) => ({
    name: cfg.label,
    value: data[key] ?? 0,
    color: cfg.color,
  }));

  const total = chartData.reduce((s, d) => s + d.value, 0);

  return (
    <div className="w-full h-full">
      <div className="flex flex-col h-full">
        <div className="flex-1 relative min-h-[180px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <defs>
                {chartData.map((item, i) => (
                  <linearGradient key={`pie-grad-${i}`} id={`pieGrad-${i}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={item.color} stopOpacity={1} />
                    <stop offset="100%" stopColor={item.color} stopOpacity={0.6} />
                  </linearGradient>
                ))}
              </defs>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={75}
                paddingAngle={4}
                dataKey="value"
                strokeWidth={0}
                animationDuration={800}
                animationBegin={200}
              >
                {chartData.map((entry, i) => (
                  <Cell key={entry.name} fill={`url(#pieGrad-${i})`} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-2xl font-black text-white leading-none">{total}</span>
            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mt-1">Total</span>
          </div>
        </div>

        {/* Legend */}
        <div className="grid grid-cols-1 gap-1.5 mt-2 bg-black/20 p-4 rounded-xl border border-white/5">
          {chartData.map((item) => (
            <div key={item.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div
                  className="w-2.5 h-2.5 rounded-sm"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">{item.name}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[11px] font-black text-gray-200">{item.value}</span>
                <span className="text-[10px] font-bold text-gray-600 w-10 text-right">
                  {total > 0 ? Math.round((item.value / total) * 100) : 0}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

