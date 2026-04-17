"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { 
  ShieldCheck, 
  Zap, 
  Search, 
  Code, 
  ArrowRight, 
  Github, 
  Database, 
  Cpu, 
  Bot
} from "lucide-react";

export default function LandingPage() {
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.3,
      },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <div className="relative min-h-screen">
      {/* Background elements */}
      <div className="bg-mesh" />
      <div className="bg-dot-grid absolute inset-0 opacity-20" />

      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 border-b border-white/5 bg-black/20 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">CodeSentinel</span>
          </div>
          <div className="flex items-center gap-6">
            <Link href="/docs" className="text-sm text-gray-400 hover:text-white transition-colors">Documentation</Link>
            <Link href="/dashboard" className="btn-primary py-2 px-4 text-sm">
              Launch Dashboard <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-20 px-6">
        {/* Hero Section */}
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-violet-500/20 bg-violet-500/10 text-violet-400 text-xs font-medium mb-8"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-500"></span>
            </span>
            Phase 13: Evaluation Loop Active
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6"
          >
            The Next Generation of <br />
            <span className="gradient-text">Automated Code Review</span>
          </motion.h1>

          <motion.p 
             initial={{ opacity: 0, y: 20 }}
             animate={{ opacity: 1, y: 0 }}
             transition={{ duration: 0.8, delay: 0.1 }}
             className="text-lg text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            An LLM-powered review assistant that sits between your code and human reviewers. 
            Catch 73%+ of anti-patterns with RAG-enhanced intelligence before anyone looks at a PR.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20"
          >
            <Link href="/dashboard" className="btn-primary text-lg w-full sm:w-auto">
              Get Started for Free <ArrowRight className="w-5 h-5" />
            </Link>
            <Link href="https://github.com/abhinavv27/CodeSentinel" className="btn-secondary text-lg w-full sm:w-auto">
              <Github className="w-5 h-5" /> View on GitHub
            </Link>
          </motion.div>

          {/* Interactive Preview Mockup */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.3 }}
            className="relative mx-auto max-w-5xl rounded-2xl overflow-hidden glass-card border-white/10 shadow-2xl p-2"
          >
            <div className="bg-black/40 rounded-xl overflow-hidden min-h-[400px] flex flex-col">
              <div className="border-b border-white/5 px-4 py-2 flex items-center justify-between bg-white/5">
                <div className="flex gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-500/50" />
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/50" />
                </div>
                <div className="text-[10px] text-gray-500 font-mono tracking-widest uppercase">Sentinel-Analysis-Loop</div>
              </div>
              <div className="flex-1 p-6 font-mono text-sm text-gray-400 text-left space-y-4">
                <div className="flex gap-4">
                  <span className="text-violet-500">➜</span>
                  <span className="text-gray-300">Fetching PR #42 diff...</span>
                </div>
                <div className="flex gap-4">
                  <span className="text-emerald-500">✓</span>
                  <span className="text-gray-300">Retrieved context from Vector DB (3 similar anti-patterns found)</span>
                </div>
                <div className="flex gap-4">
                  <span className="text-amber-500">⚙</span>
                  <span className="text-gray-300">Model: codellama-7b | Temperature: 0.0</span>
                </div>
                <div className="bg-white/5 p-4 rounded-lg border border-white/5">
                  <span className="text-emerald-400 font-bold">SENTINEL-COMMENT:</span><br />
                  <span className="text-gray-300">Potential SSRF vulnerability detected in `services/fetcher.py:L127`. </span>
                  <span className="text-gray-500">The user-controlled `url` is not validated against a whitelist. </span>
                  <Link href="/dashboard" className="text-violet-400 underline decoration-violet-400/30 hover:decoration-violet-400">View resolution stack</Link>
                </div>
              </div>
            </div>
            
            {/* Floating elements */}
            <div className="absolute -top-10 -right-10 w-40 h-40 bg-violet-600/20 blur-[80px]" />
            <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-emerald-600/20 blur-[80px]" />
          </motion.div>
        </div>

        {/* Features Section */}
        <div className="max-w-7xl mx-auto mt-40">
          <motion.div 
            variants={container}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            <motion.div variants={item} className="p-8 rounded-2xl border border-white/5 bg-white/5 hover:border-violet-500/30 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-violet-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Database className="w-6 h-6 text-violet-500" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Institutional Memory</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Using Qdrant RAG, Sentinel learns from every past review and architectural rule in your codebase to provide context-aware feedback.
              </p>
            </motion.div>

            <motion.div variants={item} className="p-8 rounded-2xl border border-white/5 bg-white/5 hover:border-emerald-500/30 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Bot className="w-6 h-6 text-emerald-500" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Multi-Agent Loop</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Triple-pass validation reduces hallucinations. Every critical finding is verified by secondary agents to ensure &lt;8% False Positive Rate.
              </p>
            </motion.div>

            <motion.div variants={item} className="p-8 rounded-2xl border border-white/5 bg-white/5 hover:border-blue-500/30 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Zap className="w-6 h-6 text-blue-500" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Sub-45s Latency</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Optimized inference with Redis caching and Celery concurrency means reviews land on your PR before you can walk to the kitchen.
              </p>
            </motion.div>
          </motion.div>
        </div>
      </main>

      <footer className="border-t border-white/5 py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-8 opacity-60">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-violet-500" />
            <span className="text-sm font-bold text-white">CodeSentinel</span>
          </div>
          <div className="text-xs text-gray-400 font-mono">
            &copy; 2026 CodeSentinel • BUILT FOR AGENTIC WORKFLOWS
          </div>
          <div className="flex items-center gap-6">
            <Link href="#" className="hover:text-white transition-colors">Twitter</Link>
            <Link href="#" className="hover:text-white transition-colors">Discord</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
