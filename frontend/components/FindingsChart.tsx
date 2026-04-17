"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface FindingsChartProps {
  data: Record<string, number>;
}

const CATEGORY_LABELS: Record<string, string> = {
  sql_injection: "SQL Injection",
  hardcoded_secret: "Hardcoded Secret",
  missing_null_check: "Null Check",
  race_condition: "Race Condition",
  exception_swallowing: "Exc. Swallowing",
  n_plus_1: "N+1 Query",
  insecure_deserialization: "Insec. Deser.",
  ssrf: "SSRF",
  missing_input_validation: "Input Validation",
  dead_code: "Dead Code",
  style_violation: "Style",
  unbounded_loop: "Unbounded Loop",
};

const BAR_COLORS = [
  "#8B5CF6", "#EF4444", "#F59E0B", "#10B981",
  "#3B82F6", "#EC4899", "#6366F1", "#A855F7",
];

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) => {
  if (active && payload && payload.length && label !== undefined) {
    return (
      <div className="bg-black/90 border border-white/10 rounded-xl px-4 py-3 shadow-2xl backdrop-blur-xl">
        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">
          {CATEGORY_LABELS[label] ?? label}
        </p>
        <p className="text-xl font-black text-white tracking-tighter">
          {payload[0].value} <span className="text-sm font-medium text-gray-500">Events</span>
        </p>
      </div>
    );
  }
  return null;
};

export function FindingsChart({ data }: FindingsChartProps) {
  const chartData = Object.entries(data)
    .map(([key, value]) => ({ key, label: key, value }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="w-full h-full min-h-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          barSize={20}
        >
          <defs>
            {BAR_COLORS.map((color, i) => (
              <linearGradient key={`grad-${i}`} id={`barGrad-${i}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={1} />
                <stop offset="100%" stopColor={color} stopOpacity={0.6} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="4 4" stroke="rgba(255,255,255,0.03)" vertical={false} />
          <XAxis
            dataKey="key"
            tick={{ fill: "#4B5563", fontSize: 9, fontWeight: 700 }}
            tickFormatter={(v) => CATEGORY_LABELS[v]?.split(" ")[0] ?? v}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#4B5563", fontSize: 10, fontWeight: 700 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip 
            content={<CustomTooltip />} 
            cursor={{ fill: "rgba(255,255,255,0.02)" }} 
            animationDuration={200}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell 
                key={entry.key} 
                fill={`url(#barGrad-${index % BAR_COLORS.length})`} 
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

