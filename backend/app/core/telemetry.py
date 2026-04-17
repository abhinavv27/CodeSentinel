from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from app.core.config import get_settings

from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor

settings = get_settings()

def setup_telemetry(service_name: str):
    """Initializes OpenTelemetry TracerProvider and auto-instrumentations."""
    resource = Resource.create({
        "service.name": service_name,
        "service.instance.id": f"{service_name}-prod",
        "deployment.environment": "production"
    })
    provider = TracerProvider(resource=resource)
    
    # Only enable OTLP if an endpoint is provided
    otlp_endpoint = getattr(settings, "otlp_endpoint", None)
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    
    trace.set_tracer_provider(provider)
    
    # ── Step 2: Auto-instrument libraries ────────────────────────────────
    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    CeleryInstrumentor().instrument()
    
    return trace.get_tracer(service_name)
