"""Traces and provenance for every run. YOU fill this in (project 3, step 5).

Spans follow the OpenTelemetry GenAI semantic conventions and are written as JSON lines to data/traces/.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

ROOT = Path(__file__).resolve().parent.parent
TRACES = ROOT / "data" / "traces"


class JsonlExporter(SpanExporter):
    def export(self, spans):
        TRACES.mkdir(parents=True, exist_ok=True)
        with (TRACES / "spans.jsonl").open("a", encoding="utf-8") as f:
            for s in spans:
                f.write(json.dumps({"trace_id": format(s.context.trace_id, "032x"),
                                    "span_id": format(s.context.span_id, "016x"),
                                    "parent_id": format(s.parent.span_id, "016x") if s.parent else None,
                                    "name": s.name, "attributes": dict(s.attributes),
                                    "start": s.start_time, "end": s.end_time}, ensure_ascii=False) + "\n")
        return SpanExportResult.SUCCESS


provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(JsonlExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("acme-agent")


def model_span(model: str, result: Dict):
    """Attributes for one model call (an 'inference' span)."""
    # TODO: return {"gen_ai.operation.name": "chat", "gen_ai.request.model": model,
    #               "gen_ai.usage.input_tokens": ..., "gen_ai.usage.output_tokens": ...}
    raise NotImplementedError


def tool_span(name: str, args: Dict):
    """Attributes for one tool call (an 'execute_tool' span)."""
    # TODO: return {"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": name,
    #               "gen_ai.tool.call.arguments": json.dumps(args)}
    raise NotImplementedError


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]


def provenance(model_id: str, prompt: str) -> Dict[str, str]:
    """What every run file must record, so a number can always be traced back to what produced it."""
    # TODO: {"model_id": model_id, "prompt_sha": sha256 of the prompt text (first 12 characters),
    #        "grader_sha": sha(ROOT / "lab" / "evals.py"), "dataset_sha": sha(ROOT / "data" / "acme" / "cases.jsonl")}
    raise NotImplementedError
