"use client";
import { useState } from "react";
import { Repo, triggerReindex } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { Database, RefreshCw, CheckCircle, Search, ExternalLink, Shield } from "lucide-react";

export function RepoList({ initialRepos }: { initialRepos: Repo[] }) {
  const [repos] = useState<Repo[]>(initialRepos);
  const [searchTerm, setSearchTerm] = useState("");
  const [indexing, setIndexing] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const filteredRepos = repos.filter(r => 
    r.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleReindex = async (repoId: string) => {
    setIndexing(repoId);
    try {
      await triggerReindex(repoId);
      setSuccess(repoId);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setIndexing(null);
    }
  };

  return (
    <div className="glass-card overflow-hidden border-white/5 shadow-2xl">
      <div className="p-8 border-b border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-6 bg-white/[0.01]">
        <div>
          <h2 className="text-xl font-black text-white flex items-center gap-3 tracking-tight">
            <div className="p-2 rounded-lg bg-violet-500/10 border border-violet-500/20">
              <Database className="w-5 h-5 text-violet-400" />
            </div>
            Monitored Repositories
          </h2>
          <p className="text-gray-500 text-[11px] font-bold uppercase tracking-widest mt-1.5 ml-12">RAG Context & Neural Indexing Status</p>
        </div>
        
        <div className="relative group">
          <div className="absolute inset-0 bg-violet-500/20 blur-xl opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none" />
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-violet-400 transition-colors" />
          <input 
            type="text"
            placeholder="Search Intelligence Node..."
            className="bg-black/40 border border-white/10 rounded-xl py-3 pl-12 pr-6 text-sm text-gray-200 focus:outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition-all w-full md:w-80 font-mono tracking-tight"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="divide-y divide-white/5 bg-black/20">
        <AnimatePresence mode="popLayout">
          {filteredRepos.map((repo, i) => (
            <motion.div
              key={repo.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ delay: i * 0.05, ease: [0.16, 1, 0.3, 1] }}
              className="p-6 hover:bg-white/[0.02] transition-all flex items-center justify-between group relative"
            >
              <div className="flex items-center gap-5 relative z-10">
                <div className="w-12 h-12 rounded-xl bg-gray-900 border border-white/5 flex items-center justify-center text-gray-500 group-hover:border-violet-500/30 group-hover:text-violet-400 transition-all duration-500">
                  <Shield className="w-6 h-6" />
                </div>
                <div>
                  <div className="font-bold text-gray-100 group-hover:text-white transition-colors flex items-center gap-2 text-base">
                    {repo.name}
                    <ExternalLink className="w-3.5 h-3.5 text-gray-600 opacity-0 group-hover:opacity-100 transition-all group-hover:translate-x-1" />
                  </div>
                  <div className="text-[10px] items-center gap-3 mt-1 hidden sm:flex">
                    <span className="font-mono text-gray-600">ID: {repo.id.slice(0, 12)}</span>
                    <span className="w-1 h-1 rounded-full bg-gray-800" />
                    <span className={`font-bold uppercase tracking-widest ${repo.indexed_at ? "text-emerald-500" : "text-amber-500/80"}`}>
                      {repo.indexed_at 
                        ? `Synched: ${new Date(repo.indexed_at).toLocaleDateString()}` 
                        : "NOT INDEXED"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 relative z-10">
                {success === repo.id ? (
                  <motion.div 
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="flex items-center gap-2 text-emerald-400 text-xs font-black uppercase tracking-widest pr-4"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Enqueued
                  </motion.div>
                ) : (
                  <button
                    onClick={() => handleReindex(repo.id)}
                    disabled={indexing === repo.id}
                    className="group/btn relative flex items-center gap-2 px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-[0.1em] bg-white/5 text-gray-400 border border-white/10 hover:border-violet-500/50 hover:text-white hover:bg-violet-600 transition-all disabled:opacity-50 overflow-hidden"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-violet-600 to-indigo-600 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300" />
                    <div className="relative z-10 flex items-center gap-2">
                       {indexing === repo.id ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <RefreshCw className="w-3.5 h-3.5 group-hover/btn:rotate-180 transition-transform duration-500" />
                      )}
                      <span>{indexing === repo.id ? "Processing" : "Trigger Sync"}</span>
                    </div>
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {filteredRepos.length === 0 && (
          <div className="p-20 text-center">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="inline-flex p-6 rounded-3xl bg-white/[0.02] border border-white/5 text-gray-700 mb-6"
            >
              <Database className="w-12 h-12" />
            </motion.div>
            <p className="text-gray-500 font-bold uppercase tracking-widest text-xs">No synchronization nodes matching &quot;{searchTerm}&quot;</p>
          </div>
        )}
      </div>
    </div>
  );
}

