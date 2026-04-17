import asyncio
import time
import os
import fnmatch
from datetime import datetime
from typing import Optional

import httpx
from sqlalchemy import select
import structlog

from app.tasks.celery_app import celery_app
from app.services.diff_service import parse_diff, chunk_hunks
from app.services.rag_service import RagService
from app.services.inference_service import InferenceService
from app.services.github_poster import GitHubPoster
from app.services.github_service import GitHubService
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.repository import Repository
from app.models.pull_request import PullRequest
from app.models.finding import Finding, Category, Severity

logger = structlog.get_logger()
settings = get_settings()


def enqueue_pr_review(payload: dict) -> None:
    """Called from FastAPI BackgroundTask to dispatch a Celery review task."""
    pr_data = payload.get("pull_request", {})
    run_pr_review.delay(
        repo_full_name=payload["repository"]["full_name"],
        pr_number=pr_data["number"],
        diff_url=pr_data["diff_url"],
        commit_sha=pr_data["head"]["sha"],
        title=pr_data.get("title", "Untitled PR"),
        author=pr_data.get("user", {}).get("login", "unknown"),
        installation_id=payload.get("installation", {}).get("id"),
    )


def _get_installation_token(installation_id: Optional[int]) -> str:
    """Exchange a GitHub App installation ID for a short-lived token."""
    if not installation_id:
        raise ValueError("No installation_id provided")
    from github import GithubIntegration
    gi = GithubIntegration(settings.github_app_id, settings.github_app_private_key)
    return gi.get_access_token(installation_id).token


@celery_app.task(name="run_pr_review", bind=True, max_retries=2, soft_time_limit=180)
def run_pr_review(
    self,
    repo_full_name: str,
    pr_number: int,
    diff_url: str,
    commit_sha: str,
    title: str = "Untitled PR",
    author: str = "unknown",
    installation_id: Optional[int] = None,
) -> dict:
    """
    Synchronous Celery task wrapper that runs the async review logic.
    """
    return asyncio.run(
        _async_run_pr_review(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            diff_url=diff_url,
            commit_sha=commit_sha,
            title=title,
            author=author,
            installation_id=installation_id,
        )
    )


async def _async_run_pr_review(
    repo_full_name: str,
    pr_number: int,
    diff_url: str,
    commit_sha: str,
    title: str,
    author: str,
    installation_id: Optional[int],
) -> dict:
    """Full PR review pipeline with DB persistence."""
    start_time = time.time()
    logger.info("review_started", repo=repo_full_name, pr=pr_number)

    async with AsyncSessionLocal() as db:
        try:
            # ── Step 0: Ensure Repository & PullRequest exist in DB ─────────────
            repo = await db.scalar(
                select(Repository).where(Repository.github_full_name == repo_full_name)
            )
            if not repo:
                repo = Repository(
                    github_full_name=repo_full_name, installation_id=installation_id
                )
                db.add(repo)
                await db.flush()

            pr = await db.scalar(
                select(PullRequest).where(
                    PullRequest.repository_id == repo.id,
                    PullRequest.github_pr_number == pr_number,
                )
            )
            if not pr:
                pr = PullRequest(
                    repository_id=repo.id,
                    github_pr_number=pr_number,
                    title=title,
                    author=author,
                    status="processing",
                )
                db.add(pr)
            else:
                pr.status = "processing"
                pr.completed_at = None
            
            await db.commit()
            await db.refresh(pr)

            # ── Step 0: Fetch Repo Config ─────────────────────────────────────────
            token = _get_installation_token(installation_id)
            async with GitHubService(token) as gh:
                repo_config = await gh.get_repo_config(repo_full_name)
            
            threshold = repo_config.get("threshold", settings.confidence_threshold)
            disabled_categories = [c.lower() for c in repo_config.get("disabled_categories", [])]
            exclude_paths = repo_config.get("exclude_paths", [])
            
            logger.info("governance_config_applied", 
                        threshold=threshold, 
                        disabled=disabled_categories, 
                        excludes=exclude_paths)

            # ── Step 1: Fetch diff ────────────────────────────────────────────────
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(
                    diff_url, headers={"Accept": "application/vnd.github.v3.diff"}
                )
                response.raise_for_status()
                diff_text = response.text
            
            logger.info("diff_fetched", size=len(diff_text))
            
            # ── Step 1.1: Security Audit (Phase 14 Intelligence) ────────────────
            security_context = ""
            try:
                from app.services.security_service import SecurityService
                async with GitHubService(token) as gh:
                    reqs_content = await gh.get_file_content(repo_full_name, "requirements.txt", ref=commit_sha)
                    if reqs_content:
                        temp_reqs = f"temp_reqs_{pr_number}_{commit_sha[:7]}.txt"
                        with open(temp_reqs, "w") as f:
                            f.write(reqs_content)
                        vulnerabilities = await SecurityService.run_pip_audit(".", requirements_file=temp_reqs)
                        security_context = SecurityService.format_vulnerabilities_as_context(vulnerabilities)
                        if os.path.exists(temp_reqs):
                            os.remove(temp_reqs)
            except Exception as e:
                logger.warning("security_audit_skipped", error=str(e))

            # ── Step 2: Parse & chunk ─────────────────────────────────────────────
            hunks = [
                h for h in parse_diff(diff_text)
                if not any(fnmatch.fnmatch(h.file_path, pat) for pat in exclude_paths)
            ]
            chunks = chunk_hunks(hunks, max_tokens=3800)
            logger.info("diff_chunked", hunks=len(hunks), chunks=len(chunks))

            if not chunks:
                pr.status = "completed"
                pr.completed_at = datetime.utcnow()
                await db.commit()
                return {"pr": pr_number, "findings": 0, "latency_ms": 0}

            # ── Step 2.1: Architectural Context (Phase 14 Graph RAG) ────────────
            arch_context = ""
            try:
                from app.services.dependency_service import DependencyService
                # Use current dir or a temp clone path
                dep_service = DependencyService(".")
                dep_service.build_graph()
                
                impacted_files = set()
                for hunk in hunks:
                    impacted_files.update(dep_service.get_impacted_files(hunk.file_path))
                
                if impacted_files:
                    arch_context = f"\nArchitectural Context: Changes in these files may impact: {', '.join(list(impacted_files)[:5])}"
            except Exception as e:
                logger.warning("dependency_analysis_skipped", error=str(e))

            # ── Step 3: RAG + Inference per chunk (Parallel Execution) ────────────
            rag = RagService()
            inference = InferenceService()
            task_id = str(self.request.id) if hasattr(self, 'request') else None
            
            async def _process_single_chunk(i, chunk):
                logger.info("processing_chunk", chunk=i + 1, total=len(chunks))
                
                # Step 3.0: Check Cache
                cached_findings = await inference.get_cached_findings(chunk)
                if cached_findings is not None:
                    logger.info("chunk_cache_hit", chunk=i + 1)
                    return cached_findings

                # Combine RAG context with Architectural context
                retrieved = await rag.retrieve_context(chunk[:500], top_k=4)
                context = retrieved + [arch_context] if arch_context else retrieved
                
                feedback_mem = await rag.retrieve_feedback_memory(chunk[:500], top_k=3)
                
                # Step 3a: Initial Analysis
                initial_findings = await inference.analyze_chunk(
                    chunk, context, feedback_mem, security_context, trace_id=task_id
                )
                
                # Step 3b: Self-Correction Critique
                refined_findings = await inference.critique_findings(
                    chunk, initial_findings, trace_id=task_id
                )
                
                # Step 3c: Cache Result
                await inference.cache_findings(chunk, refined_findings)
                
                return refined_findings

            # Process all chunks in parallel
            chunk_results = await asyncio.gather(*[
                _process_single_chunk(i, chunk) for i, chunk in enumerate(chunks)
            ])
            
            all_findings = []
            for results in chunk_results:
                all_findings.extend(results)

            # 4b. Multimodal Visual Review (Phase 14: Vision)
            image_files = [f for f in pr_diff.get("files", []) if f.get("filename", "").endswith(('.png', '.jpg', '.jpeg'))]
            if image_files:
                from app.services.visual_service import VisualReviewService
                visual_svc = VisualReviewService(inference_service)
                for img in image_files:
                    try:
                        v_finding = await visual_svc.review_screenshot(img['filename'], "PR UI Change")
                        all_findings.append(v_finding)
                    except Exception as e:
                        logger.error("visual_review_failed", error=str(e))

            # 4c. Reliability Guard: Detect Agent "Blindness"
            filtered = [
                f for f in all_findings
                if f.confidence >= threshold 
                and f.category.lower() not in disabled_categories
            ]
            
            if len(filtered) == 0 and len(all_findings) > 5:
                logger.warning("review_hallucination_empty_report", repo=repo_full_name)
                # Statistical logic: If critique killed everything, mark for reassessment
                pr.reliability_score = 40 
            else:
                pr.reliability_score = 95
            
            # Post to GitHub first to get comment IDs
            poster = GitHubPoster(repo_full_name, pr_number, token)
            comment_ids = poster.post_review(filtered, commit_sha)

            counts = {"critical": 0, "warning": 0, "info": 0}
            for i, res in enumerate(filtered):
                counts[res.severity] = counts.get(res.severity, 0) + 1
                db_finding = Finding(
                    pull_request_id=pr.id,
                    file_path=res.file_path,
                    line_number=res.line_number,
                    category=Category(res.category),
                    severity=Severity(res.severity),
                    confidence=res.confidence,
                    summary=res.summary,
                    explanation=res.explanation,
                    suggested_fix=res.suggested_fix,
                    github_comment_id=comment_ids[i] if i < len(comment_ids) else None,
                )
                db.add(db_finding)

            # Finalize PR stats
            latency_ms = int((time.time() - start_time) * 1000)
            pr.status = "completed"
            pr.review_latency_ms = latency_ms
            pr.findings_count = counts
            pr.completed_at = datetime.utcnow()
            
            await db.commit()

            # ── Step 6: Apply Governance Policies (Phase 15 Governance) ────────
            try:
                from app.services.policy_service import PolicyService
                policy_engine = PolicyService(repo_path)
                enriched_findings = policy_engine.evaluate_findings([f.to_dict() for f in filtered])
                logger.info("policies_applied", count=len(enriched_findings))
            except Exception as e:
                logger.error("policy_engine_failed", error=str(e))
                enriched_findings = [f.to_dict() for f in filtered]

            # ── Step 7: Dispatch Notifications (Phase 15 DX) ─────────────────────
            try:
                from app.services.notification_service import NotificationService
                notifier = NotificationService()
                await notifier.send_slack_alert(
                    repo_full_name, pr_number, enriched_findings
                )
            except Exception as e:
                logger.warning("notification_failed", error=str(e))

            logger.info(
                "review_completed",
                repo=repo_full_name,
                pr=pr_number,
                findings=len(filtered),
                latency_ms=latency_ms,
            )
            return {"pr": pr_number, "findings": len(filtered), "latency_ms": latency_ms}

        except Exception as exc:
            logger.error("review_failed", repo=repo_full_name, pr=pr_number, error=str(exc))
            async with AsyncSessionLocal() as fail_db:
                fail_pr = await fail_db.scalar(
                    select(PullRequest).where(
                        PullRequest.github_pr_number == pr_number,
                    )
                )
                if fail_pr:
                    fail_pr.status = "failed"
                    await fail_db.commit()
            raise exc


@celery_app.task(name="reindex_repository")
def reindex_repository(repo_id: str, repo_path: str = None) -> dict:
    """
    Background task to re-index a repository's codebase into Qdrant.
    """
    return asyncio.run(_async_reindex_repository(repo_id, repo_path))


async def _async_reindex_repository(repo_id: str, repo_path: str = None) -> dict:
    """Async logic for repository re-indexing."""
    logger.info("reindexing_started", repo_id=repo_id)

    async with AsyncSessionLocal() as db:
        repo = await db.scalar(select(Repository).where(Repository.id == repo_id))
        if not repo:
            logger.error("reindexing_failed_repo_not_found", repo_id=repo_id)
            return {"status": "failed", "error": "Repo not found"}

        # In a real system, we would clone the repo to a temp dir if repo_path is not provided
        path_to_index = repo_path or f"./clones/{repo.github_full_name}"

        try:
            from app.services.rag_service import RagService
            import os

            rag = RagService()

            if os.path.exists(path_to_index):
                for root, _, files in os.walk(path_to_index):
                    for file in files:
                        if file.endswith((".py", ".js", ".ts", ".tsx", ".go", ".rs")):
                            file_full_path = os.path.join(root, file)
                            with open(file_full_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                                rag.index_file(file_full_path, content)

            repo.indexed_at = datetime.utcnow()
            await db.commit()

            logger.info("reindexing_completed", repo=repo.github_full_name)
            return {"status": "success", "repo": repo.github_full_name}
        except Exception as e:
            logger.error("reindexing_failed", repo_id=repo_id, error=str(e))
            return {"status": "failed", "error": str(e)}


@celery_app.task(name="run_remediation")
def run_remediation(finding_id: str, installation_id: Optional[int] = None) -> dict:
    """
    Background task to apply a suggested fix to the codebase.
    """
    return asyncio.run(_async_run_remediation(finding_id, installation_id))


async def _async_run_remediation(finding_id: str, installation_id: Optional[int] = None) -> dict:
    """Async logic for automated remediation."""
    logger.info("remediation_started", finding_id=finding_id)

    async with AsyncSessionLocal() as db:
        finding = await db.scalar(select(Finding).where(Finding.id == finding_id))
        if not finding or not finding.suggested_fix:
            logger.error("remediation_failed_finding_not_found", finding_id=finding_id)
            return {"status": "failed", "error": "Finding or suggested fix not found"}

        pr = await db.scalar(select(PullRequest).where(PullRequest.id == finding.pull_request_id))
        repo = await db.scalar(select(Repository).where(Repository.id == pr.repository_id))
        
        token = _get_installation_token(installation_id)
        
        # Determine path (in production, we'd clone to a unique temp dir)
        repo_path = f"./clones/{repo.github_full_name}"
        
        try:
            from app.services.remediation_service import RemediationService
            remediator = RemediationService(repo_path)
            
            # 1. Create fix branch
            branch_name = remediator.create_fix_branch("main", f"{finding_id[:8]}")
            
            # 2. Apply fix
            success = await remediator.apply_fix(
                finding.file_path, 
                finding.line_number, 
                "", # Original code not strictly needed for line replacement
                finding.suggested_fix
            )
            
            if success:
                # 3. Commit and push
                remediator.commit_and_push(
                    branch_name, 
                    f"CodeSentinel Fix: {finding.category.value}\n\nResolves finding on line {finding.line_number}"
                )
                
                # 4. Notify GitHub (Optional: could also open a PR)
                logger.info("remediation_completed", branch=branch_name)
                return {"status": "success", "branch": branch_name}
            else:
                return {"status": "failed", "error": "Failed to apply fix"}
                
        except Exception as e:
            logger.error("remediation_failed", finding_id=finding_id, error=str(e))
            return {"status": "failed", "error": str(e)}
