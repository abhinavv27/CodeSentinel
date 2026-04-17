import json
import httpx
from dataclasses import dataclass
from typing import Optional
from app.core.config import get_settings
from app.services.prompt_builder import SYSTEM_PROMPT, build_user_prompt, build_critique_prompt
from app.services.cache_service import CacheService
from langfuse import Langfuse
import structlog

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class FindingResult:
    """A single code issue identified by the LLM."""

    file_path: str
    line_number: int
    category: str
    severity: str
    confidence: float
    summary: str
    explanation: str
    suggested_fix: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "category": self.category,
            "severity": self.severity,
            "confidence": self.confidence,
            "summary": self.summary,
            "explanation": self.explanation,
            "suggested_fix": self.suggested_fix,
        }


VALID_CATEGORIES = {
    "sql_injection", "hardcoded_secret", "missing_null_check", "race_condition",
    "exception_swallowing", "n_plus_1", "insecure_deserialization", "ssrf",
    "missing_input_validation", "dead_code", "style_violation", "unbounded_loop",
}
VALID_SEVERITIES = {"critical", "warning", "info"}


def _validate_finding(raw: dict) -> FindingResult | None:
    """Validate and parse a raw dict into a FindingResult, returning None if invalid."""
    try:
        category = raw.get("category", "").lower()
        severity = raw.get("severity", "").lower()
        if category not in VALID_CATEGORIES or severity not in VALID_SEVERITIES:
            return None
        return FindingResult(
            file_path=str(raw.get("file_path", "unknown")),
            line_number=int(raw.get("line_number", 1)),
            category=category,
            severity=severity,
            confidence=float(raw.get("confidence", 0.5)),
            summary=str(raw.get("summary", ""))[:256],
            explanation=str(raw.get("explanation", "")),
            suggested_fix=raw.get("suggested_fix"),
        )
    except (TypeError, ValueError) as e:
        logger.warning("finding_validation_error", error=str(e), raw=raw)
        return None


class InferenceService:
    """Calls the LLM (vLLM/Ollama OpenAI-compat endpoint) to analyze diff chunks."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.model_endpoint, timeout=90.0
        )
        self.cache = CacheService()
        self.langfuse = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host
        )

    async def get_cached_findings(self, diff_chunk: str) -> Optional[list[FindingResult]]:
        """Retrieve previously generated and critiqued findings for a chunk."""
        cached_raw = await self.cache.get_finding(diff_chunk)
        if cached_raw:
            return [f for f in (_validate_finding(r) for r in cached_raw) if f is not None]
        return None

    async def cache_findings(self, diff_chunk: str, findings: list[FindingResult]) -> None:
        """Store critiqued findings in the cache."""
        await self.cache.set_finding(diff_chunk, [f.to_dict() for f in findings])

    async def analyze_chunk(
        self, diff_chunk: str, context: list[str], feedback_memory: list[dict] = None, security_context: str = "", trace_id: str = None
    ) -> list[FindingResult]:
        """Send a diff chunk to the model and return validated FindingResult objects."""
        user_msg = build_user_prompt(diff_chunk, context, feedback_memory, security_context)
        
        # Langfuse Tracing
        trace = self.langfuse.trace(id=trace_id, name="analyze_chunk") if trace_id else None
        generation = trace.generation(
            name="initial_analysis",
            model=settings.model_name,
            input={"messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_msg}]},
            model_parameters={"temperature": 0.1}
        ) if trace else None

        payload = {
            "model": settings.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            "max_tokens": settings.model_max_tokens,
            "temperature": 0.1,
        }
        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()

            if generation:
                generation.end(output=content)

            if content.startswith("```"):
                content = "\n".join(content.split("\n")[1:])
            if content.endswith("```"):
                content = "\n".join(content.split("\n")[:-1])

            raw_findings = json.loads(content)
            if not isinstance(raw_findings, list):
                return []

            return [f for f in (_validate_finding(r) for r in raw_findings) if f is not None]

        except (json.JSONDecodeError, KeyError, httpx.HTTPError) as e:
            logger.warning("inference_failed", error=str(e))
            if generation:
                generation.end(output=str(e), level="ERROR")
            return []

    async def critique_findings(
        self, diff_chunk: str, initial_findings: list[FindingResult], trace_id: str = None
    ) -> list[FindingResult]:
        """Ask the model to re-evaluate its initial findings to reduce false positives."""
        if not initial_findings:
            return []

        user_msg = build_critique_prompt(
            diff_chunk, [f.to_dict() for f in initial_findings]
        )
        
        # Langfuse Tracing
        trace = self.langfuse.trace(id=trace_id, name="critique_findings") if trace_id else None
        generation = trace.generation(
            name="self_correction_critique",
            model=settings.model_name,
            input={"messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_msg}]},
            model_parameters={"temperature": 0.0}
        ) if trace else None

        payload = {
            "model": settings.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            "max_tokens": settings.model_max_tokens,
            "temperature": 0.0,
        }

        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()

            if generation:
                generation.end(output=content)

            if content.startswith("```"):
                content = "\n".join(content.split("\n")[1:])
            if content.endswith("```"):
                content = "\n".join(content.split("\n")[:-1])

            raw_findings = json.loads(content)
            if not isinstance(raw_findings, list):
                return []

            return [
                f
                for f in (_validate_finding(r) for r in raw_findings)
                if f is not None
            ]

        except (json.JSONDecodeError, KeyError, httpx.HTTPError) as e:
            logger.warning("critique_failed_falling_back", error=str(e))
            if generation:
                generation.end(output=str(e), level="ERROR")
            return initial_findings

    async def review_diff(self, hunks: list, context: list[str]) -> list[FindingResult]:
        """Convenience method to process multiple hunks through the full pipeline."""
        from app.services.diff_service import chunk_hunks
        chunks = chunk_hunks(hunks)
        all_findings = []
        
        for chunk in chunks:
            # Check cache first for evaluation speedup
            cached = await self.get_cached_findings(chunk)
            if cached:
                all_findings.extend(cached)
                continue

            initial = await self.analyze_chunk(chunk, context)
            refined = await self.critique_findings(chunk, initial)
            await self.cache_findings(chunk, refined)
            all_findings.extend(refined)
            
        return all_findings
