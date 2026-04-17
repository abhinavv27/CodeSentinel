import asyncio
import json
import os
import sys
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.diff_service import parse_diff
from app.services.inference_service import InferenceService
from app.models.finding import Category, Severity

# ANSI Color codes for premium CLI experience
C_VIOLET = "\033[95m"
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

class Evaluator:
    def __init__(self, ground_truth_path: str, runs_per_case: int = 3):
        self.ground_truth_path = ground_truth_path
        self.runs_per_case = runs_per_case
        self.inference_service = InferenceService()
        self.results = []

    async def run(self):
        print(f"\n{C_BOLD}{C_VIOLET}--- CodeSentinel Statistical Evaluation Engine ---{C_RESET}")
        print(f"Runs per case: {self.runs_per_case}\n")
        
        if not os.path.exists(self.ground_truth_path):
            print(f"{C_RED}Error: Ground truth file not found at {self.ground_truth_path}{C_RESET}")
            return

        with open(self.ground_truth_path, "r") as f:
            cases = [json.loads(line) for line in f]

        for case in cases:
            print(f"{C_BOLD}{C_CYAN}[CASE {case['id']}]{C_RESET} {case['description']}")
            
            case_runs = []
            for run_idx in range(self.runs_per_case):
                # Parse diff
                hunks = parse_diff(case['diff'])
                
                # Trace evaluation in Langfuse using Case ID as trace identifier
                trace_id = f"eval_{case['id']}_run_{run_idx}"
                
                # Get model findings
                predictions = await self.inference_service.review_diff(hunks, context=[])
                
                # Compare
                matched = self._compare(case['expected_findings'], predictions)
                case_runs.append(matched)
                
            # Aggregate stats for this case
            avg_hits = sum(r['hits'] for r in case_runs) / self.runs_per_case
            avg_fps = sum(r['fps'] for r in case_runs) / self.runs_per_case
            avg_misses = sum(r['misses'] for r in case_runs) / self.runs_per_case
            
            # Variance detection (flakiness)
            hit_counts = [r['hits'] for r in case_runs]
            is_flaky = len(set(hit_counts)) > 1
            flaky_tag = f" {C_YELLOW}[FLAKY]{C_RESET}" if is_flaky else ""

            self.results.append({
                "case": case['id'],
                "expected": len(case['expected_findings']),
                "avg_hits": avg_hits,
                "avg_fps": avg_fps,
                "avg_misses": avg_misses,
                "is_flaky": is_flaky
            })
            
            status_icon = "PASS" if avg_fps == 0 and avg_misses == 0 else "WARN"
            print(f"  [{status_icon}]{flaky_tag} Avg Hits: {C_GREEN}{avg_hits:.1f}{C_RESET} | Avg FPs: {C_RED}{avg_fps:.1f}{C_RESET}\n")

        self._print_summary()

    def _compare(self, expected: List[Dict], predicted: List[Any]) -> Dict:
        hits = 0
        pred_items = [{"category": p.category, "line": p.line_number} for p in predicted]
        exp_items = [{"category": e['category'], "line": e['line_number']} for e in expected]
        
        for exp in exp_items:
            match = next((p for p in pred_items if p['category'] == exp['category']), None)
            if match:
                hits += 1
                pred_items.remove(match)
        
        return {"hits": hits, "fps": len(pred_items), "misses": len(exp_items) - hits}

    def _print_summary(self):
        total_exp = sum(r['expected'] for r in self.results)
        total_hits = sum(r['avg_hits'] for r in self.results)
        total_fps = sum(r['avg_fps'] for r in self.results)
        total_misses = sum(r['avg_misses'] for r in self.results)
        flaky_cases = sum(1 for r in self.results if r['is_flaky'])
        
        recall = (total_hits / total_exp) * 100 if total_exp > 0 else 100
        fpr = (total_fps / (total_hits + total_fps + total_misses)) * 100 if (total_hits + total_fps + total_misses) > 0 else 0

        # Performance gates
        recall_pass = recall >= 80  # Target increased via parallelization & Graph RAG
        fpr_pass = fpr < 5        # Target decreased via critique pass

        print(f"\n{C_BOLD}STATISTICAL SUMMARY{C_RESET}")
        print("-" * 40)
        print(f"Total Test Cases:        {len(self.results)}")
        print(f"Flaky Cases Detected:    {C_YELLOW}{flaky_cases}{C_RESET}")
        print(f"Avg Recall:              {C_GREEN if recall_pass else C_RED}{recall:.2f}%{C_RESET} (Target: >=80%)")
        print(f"Avg FPR:                 {C_GREEN if fpr_pass else C_RED}{fpr:.2f}%{C_RESET} (Target: <5%)")
        print("-" * 40)
        
        if recall_pass and fpr_pass:
            print(f"\n{C_GREEN}{C_BOLD}STATUS: READY FOR PRODUCTION DEPLOYMENT{C_RESET}\n")
        else:
            print(f"\n{C_YELLOW}{C_BOLD}STATUS: TUNING REQUIRED{C_RESET}\n")

if __name__ == "__main__":
    evaluator = Evaluator("backend/eval/ground_truth.jsonl", runs_per_case=2)
    asyncio.run(evaluator.run())
