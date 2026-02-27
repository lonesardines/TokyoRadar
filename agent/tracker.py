"""Token usage tracking and cost calculation for LLM API calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

# DashScope international pricing per 1M tokens (USD)
MODEL_COSTS: dict[str, tuple[float, float]] = {
    # (input_cost_per_1m, output_cost_per_1m)
    "qwen-max": (1.20, 6.00),
    "qwen-plus": (0.40, 1.20),
    "qwen-plus-latest": (0.40, 1.20),
    "qwen-turbo": (0.05, 0.20),
    "qwen-flash": (0.05, 0.40),
    "qwen3.5-plus": (0.40, 2.40),
}


@dataclass
class APICallRecord:
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def cost_usd(self) -> float:
        input_rate, output_rate = MODEL_COSTS.get(self.model, (0.0, 0.0))
        return (
            self.input_tokens * input_rate / 1_000_000
            + self.output_tokens * output_rate / 1_000_000
        )


class TokenTracker:
    """Accumulates API call metrics across an agent session."""

    def __init__(self) -> None:
        self.calls: list[APICallRecord] = []

    def record(self, response, latency_ms: float, model: str) -> APICallRecord:
        """Record usage from an OpenAI-compatible chat completion response."""
        usage = response.usage
        rec = APICallRecord(
            model=model,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            latency_ms=latency_ms,
        )
        self.calls.append(rec)
        return rec

    @property
    def total_input_tokens(self) -> int:
        return sum(c.input_tokens for c in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(c.output_tokens for c in self.calls)

    @property
    def total_cost(self) -> float:
        return sum(c.cost_usd for c in self.calls)

    @property
    def avg_latency_ms(self) -> float:
        if not self.calls:
            return 0.0
        return sum(c.latency_ms for c in self.calls) / len(self.calls)

    @property
    def p95_latency_ms(self) -> float:
        if not self.calls:
            return 0.0
        sorted_lats = sorted(c.latency_ms for c in self.calls)
        idx = int(len(sorted_lats) * 0.95)
        return sorted_lats[min(idx, len(sorted_lats) - 1)]

    def summary(self) -> dict:
        by_model: dict[str, dict] = {}
        for c in self.calls:
            m = by_model.setdefault(c.model, {
                "calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
            })
            m["calls"] += 1
            m["input_tokens"] += c.input_tokens
            m["output_tokens"] += c.output_tokens
            m["cost_usd"] += c.cost_usd

        return {
            "total_calls": len(self.calls),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": self.total_cost,
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "p95_latency_ms": round(self.p95_latency_ms, 1),
            "by_model": by_model,
        }

    def print_report(self) -> None:
        """Print a rich-formatted session report to the terminal."""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(
            title="TokyoRadar Agent Session Report",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Model", style="bold")
        table.add_column("Calls", justify="right")
        table.add_column("In Tok", justify="right")
        table.add_column("Out Tok", justify="right")
        table.add_column("Cost", justify="right", style="green")

        s = self.summary()
        for model, data in s["by_model"].items():
            table.add_row(
                model,
                f"{data['calls']:,}",
                f"{data['input_tokens']:,}",
                f"{data['output_tokens']:,}",
                f"${data['cost_usd']:.4f}",
            )

        table.add_section()
        table.add_row(
            "[bold]TOTAL[/bold]",
            f"{s['total_calls']:,}",
            f"{s['total_input_tokens']:,}",
            f"{s['total_output_tokens']:,}",
            f"[bold]${s['total_cost_usd']:.4f}[/bold]",
        )

        console.print(table)
        console.print(
            f"  Latency: avg {s['avg_latency_ms']:.0f}ms  "
            f"p95 {s['p95_latency_ms']:.0f}ms",
            style="dim",
        )
