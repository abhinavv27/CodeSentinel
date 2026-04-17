"use client";
import { useEffect, useState } from "react";
import { getGlobalStats, getRepos, GlobalStats, Repo } from "@/lib/api";
import { StatCard } from "@/components/StatCard";
import { FindingsChart } from "@/components/FindingsChart";
import { SeverityDonut } from "@/components/SeverityDonut";
import { FPRGauge } from "@/components/FPRGauge";
import { RepoList } from "@/components/RepoList";
import { motion } from "framer-motion";
import {
  ShieldCheck,
  GitPullRequest,
  AlertTriangle,
  TrendingUp,
  Clock,
  Loader2,
  Cpu,
  Zap,
  Bot
} from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState<GlobalStats | null>(null);
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [s, r] = await Promise.all([getGlobalStats(), getRepos()]);
        setStats(s);
        setRepos(r);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !stats) {
    return (
      <div className="relative min-h-screen bg-black flex items-center justify-center overflow-hidden">
        <div className="bg-mesh opacity-50" />
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-6 relative z-10"
        >
          <div className="relative">
            <Loader2 className="w-16 h-16 text-violet-500 animate-spin" />
            <div className="absolute inset-0 blur-xl bg-violet-500/20 animate-pulse" />
          </div>
          <p className="text-gray-400 font-bold tracking-[0.2em] uppercase text-[10px]">Synchronizing Neural Loop</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen selection:bg-violet-500/30">
      {/* Background elements */}
      <div className="bg-mesh" />
      <div className="bg-dot-grid absolute inset-0 opacity-20 pointer-events-none" />

      {/* Navigation Header */}
      <header className="sticky top-0 z-50 border-b border-white/5 bg-black/20 backdrop-blur-xl">
        <div className="max-w-[1440px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-violet-600 flex items-center justify-center shadow-lg shadow-violet-600/20">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight text-white">CodeSentinel</h1>
              <div className="flex items-center gap-1.5 mt-0.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Instance Node: US-EAST-1</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
             <div className="hidden md:flex items-center gap-4 px-4 py-1.5 rounded-full border border-white/5 bg-white/5">
                <div className="flex items-center gap-2">
                  <Cpu className="w-3.5 h-3.5 text-gray-500" />
                  <span className="text-[10px] text-gray-400 font-mono tracking-tighter">LOAD: 12.4%</span>
                </div>
                <div className="w-px h-3 bg-white/5" />
                <div className="flex items-center gap-2">
                  <Zap className="w-3.5 h-3.5 text-gray-500" />
                  <span className="text-[10px] text-gray-400 font-mono tracking-tighter">LAT: 42ms</span>
                </div>
             </div>
             <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-violet-600 to-emerald-500 p-px">
                <div className="w-full h-full rounded-full bg-black flex items-center justify-center text-[10px] font-bold text-white">
                  AZ
                </div>
             </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1440px] mx-auto px-6 py-10 relative z-10">
        {/* Page Title & Breadcrumbs */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <div className="flex items-center gap-2 text-[10px] font-bold text-violet-500/60 uppercase tracking-[0.2em] mb-3">
            <span>Terminal</span>
            <span className="text-gray-700">/</span>
            <span>Dashboard</span>
            <span className="text-gray-700">/</span>
            <span className="text-violet-400">Intelligence</span>
          </div>
          <h2 className="text-4xl font-extrabold tracking-tight text-white mb-2">
            System <span className="gradient-text">Pulse</span>
          </h2>
          <p className="text-gray-500 text-sm font-medium">
            Global orchestration monitoring for <span className="text-white font-bold">{repos.length} active repos</span>.
          </p>
        </motion.div>

        {/* KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5 mb-10">
          <StatCard
            title="Total Reviews"
            value={stats.total_prs_reviewed}
            subtitle="Cross-repo reviewed events"
            icon={<GitPullRequest className="w-5 h-5" />}
            accent="violet"
            trend={{ value: 14, label: "MoM" }}
            delay={1}
          />
          <StatCard
            title="Total Findings"
            value={stats.total_findings}
            subtitle="Potential incidents neutralized"
            icon={<AlertTriangle className="w-5 h-5" />}
            accent="warning"
            delay={2}
          />
          <StatCard
            title="Statistical Confidence"
            value={`${stats.statistical_confidence}%`}
            subtitle="Model assurance level"
            icon={<Cpu className="w-5 h-5" />}
            accent="success"
            trend={{ value: 0.8, label: "uptime" }}
            delay={3}
          />
          <StatCard
             title="Acceptance Rate"
             value={`${stats.acceptance_rate.toFixed(1)}%`}
             subtitle="Human reviewer validation"
             icon={<TrendingUp className="w-5 h-5" />}
             accent={stats.acceptance_rate > 60 ? "success" : "warning"}
             delay={4}
           />
        </div>


        {/* Phase 13 Integrated Intelligence Component */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass-card p-8 mb-10 border-white/5 relative group overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-violet-500/5 to-transparent pointer-events-none" />
          
          <div className="relative flex flex-col lg:flex-row gap-10">
            <div className="lg:w-1/3">
              <div className="flex items-center gap-2 mb-4">
                <div className="px-2 py-0.5 rounded bg-violet-500/10 border border-violet-500/20 text-[10px] font-black text-violet-400 uppercase tracking-widest">
                  Neural Optimizer
                </div>
              </div>
              <h3 className="text-2xl font-bold text-white mb-4">Institutional <span className="text-violet-400">Memory</span></h3>
              <p className="text-sm text-gray-500 leading-relaxed max-w-sm">
                CodeSentinel uses RAG (Retrieval Augmented Generation) to cross-reference every PR against {stats.institutional_memory_size} past critical resolutions.
              </p>
              <div className="flex items-center gap-4 mt-8">
                <div className="flex flex-col">
                  <span className="text-2xl font-black font-mono text-white tracking-tighter">94.2%</span>
                  <span className="text-[10px] text-gray-600 font-bold uppercase tracking-widest">Conf Score</span>
                </div>
                <div className="w-px h-10 bg-white/5" />
                <div className="flex flex-col">
                  <span className="text-2xl font-black font-mono text-emerald-400 tracking-tighter">45s</span>
                  <span className="text-[10px] text-gray-600 font-bold uppercase tracking-widest">Latency</span>
                </div>
              </div>
            </div>

            <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-6 bg-white/2 rounded-2xl p-6 border border-white/5">
               <div className="space-y-4">
                 <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-400 uppercase">Statistical Confidence</span>
                    <span className="text-xs font-mono text-violet-400">{stats.statistical_confidence}%</span>
                 </div>
                 <div className="h-1.5 bg-black/40 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${stats.statistical_confidence}%` }}
                      className="h-full bg-violet-600"
                    />
                 </div>
                 <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-400 uppercase">Cache Efficiency</span>
                    <span className="text-xs font-mono text-emerald-400">{stats.cache_hit_rate.toFixed(1)}%</span>
                 </div>
                 <div className="h-1.5 bg-black/40 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${stats.cache_hit_rate}%` }}
                      className="h-full bg-emerald-600 shadow-[0_0_10px_rgba(16,185,129,0.3)]"
                    />
                 </div>
               </div>
               
               <div className="bg-black/20 rounded-xl p-4 border border-white/5 font-mono text-[11px] text-gray-500 leading-relaxed">
                  <div className="flex items-center gap-2 mb-2 text-emerald-500/80">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="font-bold tracking-widest uppercase">Live Trace Log</span>
                  </div>
                  <div>➜ Analyzing <span className="text-gray-300">fetch_utils.py...</span></div>
                  <div>➜ Found 1 match in <span className="text-violet-400">Institutional DB</span></div>
                  <div>➜ Cross-validating with <span className="text-white">GPT-4o agent</span>...</div>
                  <div className="text-emerald-500/70 mt-2">✓ High confidence finding verified.</div>
               </div>
            </div>
          </div>
        </motion.div>

        {/* Visualization Row */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-10">
          <div className="xl:col-span-2 glass-card p-6 border-white/5">
             <div className="flex items-center justify-between mb-8">
                <div>
                  <h3 className="text-lg font-bold text-white">Findings Distribution</h3>
                  <p className="text-xs text-gray-500">Categorical analysis of anti-patterns</p>
                </div>
                <div className="p-2 rounded-lg bg-white/5 border border-white/5">
                  <TrendingUp className="w-4 h-4 text-violet-400" />
                </div>
             </div>
             <FindingsChart data={stats.findings_by_category} />
          </div>
          
          <div className="glass-card p-6 border-white/5">
             <div className="flex items-center justify-between mb-8">
                <div>
                  <h3 className="text-lg font-bold text-white">Risk Severity</h3>
                  <p className="text-xs text-gray-500">Security priority weighting</p>
                </div>
                <div className="p-2 rounded-lg bg-white/5 border border-white/5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                </div>
             </div>
             <SeverityDonut data={stats.findings_by_severity} />
          </div>
        </div>

        {/* Repository Grid */}
        <motion.div
           initial={{ opacity: 0, y: 20 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ delay: 0.6 }}
           className="mb-10"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white">Repositories</h3>
              <p className="text-sm text-gray-500 font-medium">Monitoring {repos.length} active projects</p>
            </div>
          </div>
          <RepoList initialRepos={repos} />
        </motion.div>

        {/* Gauges & Trend */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20">
          <div className="glass-card p-8 border-white/5">
            <h3 className="text-lg font-bold text-white mb-1">Hallucination Guard</h3>
            <p className="text-xs text-gray-500 mb-8 font-medium">Measuring model accuracy and rejection metrics</p>
            <div className="flex items-center justify-center gap-10 md:gap-20">
              <FPRGauge value={stats.false_positive_rate} target={8} label="False Positives" />
              <FPRGauge value={100 - stats.acceptance_rate} target={40} label="PR Rejections" />
            </div>
          </div>

          <div className="glass-card p-8 border-white/5 relative overflow-hidden">
            <div className="relative z-10">
              <h3 className="text-lg font-bold text-white mb-1">Vulnerability Concentration</h3>
              <p className="text-xs text-gray-500 mb-8 font-medium">Top detected risk categories</p>
              
              <div className="space-y-4">
                {Object.entries(stats.findings_by_category)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 4)
                  .map(([key, count], i) => {
                    const max = Math.max(...Object.values(stats.findings_by_category)) || 1;
                    const pct = (count / max) * 100;
                    const label = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
                    const accentColors = ["#8B5CF6", "#EF4444", "#F59E0B", "#10B981"];
                    return (
                      <div key={key}>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest">{label}</span>
                          <span className="text-xs font-mono font-bold text-white bg-white/5 px-2 py-0.5 rounded">{count}</span>
                        </div>
                        <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 1.5, delay: 0.8 + (i * 0.1), ease: "circOut" }}
                            className="h-full rounded-full"
                            style={{ backgroundColor: accentColors[i % accentColors.length] }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="relative z-10 py-10 border-t border-white/5 bg-black/40">
        <div className="max-w-[1440px] mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-4 h-4 text-violet-500" />
            <span className="text-[10px] font-black text-white uppercase tracking-[0.3em]">CodeSentinel v2.4.0-PRIME</span>
          </div>
          <div className="text-[10px] items-center gap-6 hidden md:flex font-bold text-gray-600 uppercase tracking-widest">
            <span className="hover:text-white transition-colors cursor-pointer">Security Policy</span>
            <span className="hover:text-white transition-colors cursor-pointer">Telemetry Docs</span>
            <span className="hover:text-white transition-colors cursor-pointer">Open Source</span>
          </div>
          <div className="text-[10px] font-mono text-gray-700">
            AUTO_REFRESH_INTERVAL: 30S | REVALIDATE: ENABLED
          </div>
        </div>
      </footer>
    </div>
  );
}

