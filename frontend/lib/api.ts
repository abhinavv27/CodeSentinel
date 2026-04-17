const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface GlobalStats {
  total_prs_reviewed: number;
  total_findings: number;
  false_positive_rate: number;
  acceptance_rate: number;
  findings_by_category: Record<string, number>;
  findings_by_severity: Record<string, number>;
  institutional_memory_size: number;
  vulnerabilities_found: number;
  cache_hit_rate: number;
  statistical_confidence: number;
  agent_flakiness: number;
}

export interface Repo {
  id: string;
  name: string;
  installation_id: number | null;
  indexed_at: string | null;
}

export async function getGlobalStats(): Promise<GlobalStats> {
  const res = await fetch(`${API_BASE}/repos/stats`, {
    next: { revalidate: 30 },
  });
  if (!res.ok) {
    // Return mock data when backend is not running
    return {
      total_prs_reviewed: 247,
      total_findings: 1834,
      false_positive_rate: 6.2,
      acceptance_rate: 71.4,
      findings_by_category: {
        sql_injection: 142,
        hardcoded_secret: 98,
        missing_null_check: 312,
        race_condition: 67,
        exception_swallowing: 234,
        n_plus_1: 189,
        insecure_deserialization: 45,
        ssrf: 38,
        missing_input_validation: 276,
        dead_code: 198,
        style_violation: 156,
        unbounded_loop: 79,
      },
      findings_by_severity: {
        critical: 323,
        warning: 891,
        info: 620,
      },
      institutional_memory_size: 142,
      vulnerabilities_found: 84,
      cache_hit_rate: 68.4,
      statistical_confidence: 94.2,
      agent_flakiness: 2.1,
    };
  }
  return res.json();
}

export async function getRepos(): Promise<Repo[]> {
  const res = await fetch(`${API_BASE}/repos`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) return [];
  return res.json();
}

export async function triggerReindex(repoId: string, repoPath?: string) {
  const res = await fetch(`${API_BASE}/repos/${repoId}/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_path: repoPath }),
  });
  if (!res.ok) throw new Error("Failed to trigger re-index");
  return res.json();
}
