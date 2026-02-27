"""CLI entry point for the agent orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from agent.core import AgentLoop
from agent.prompts import ORCHESTRATOR_PROMPT
from agent.recorder import SessionRecorder, SessionReplayer
from agent.tools import get_all_tools
from agent.tracker import TokenTracker

SESSIONS_DIR = Path("sessions")
console = Console()


@click.group()
def cli():
    """TokyoRadar Agent CLI — LLM-driven multi-source product intelligence."""
    pass


@cli.command()
@click.argument("message")
@click.option("--model", default="qwen-plus", help="Model to use (qwen3.5-plus, qwen-max, qwen-plus, qwen-turbo)")
@click.option("--dry-run", is_flag=True, help="Call LLM but mock all tool executions")
@click.option("--no-record", is_flag=True, help="Don't record the session")
def run(message: str, model: str, dry_run: bool, no_record: bool):
    """Run the agent with a user message.

    Example: python -m agent.cli run "research nanamica across all channels"
    """
    tracker = TokenTracker()
    recorder = None if no_record else SessionRecorder(SESSIONS_DIR)

    tools = get_all_tools()

    loop = AgentLoop(
        tools=tools,
        system_prompt=ORCHESTRATOR_PROMPT,
        model=model,
        tracker=tracker,
        recorder=recorder,
        dry_run=dry_run,
    )

    mode_label = "[dry-run]" if dry_run else "[live]"
    console.print(f"\n[bold cyan]TokyoRadar Agent[/bold cyan] {mode_label}")
    console.print(f"  Model: {model}")
    console.print(f"  Tools: {len(tools)}")
    if recorder:
        console.print(f"  Session: {recorder.file}")
    console.print(f"  Message: {message}\n")

    with console.status("[bold green]Agent thinking..."):
        result = loop.run(message)

    # Display tool calls
    if result.tool_calls:
        console.print(f"\n[bold]Tool calls ({len(result.tool_calls)}):[/bold]")
        for tc in result.tool_calls:
            status = "[dim](dry-run)[/dim]" if dry_run else f"[dim]{tc.duration_ms:.0f}ms[/dim]"
            if "error" in (tc.output if isinstance(tc.output, dict) else {}):
                console.print(f"  [red]x[/red] {tc.name} {status}")
            else:
                console.print(f"  [green]v[/green] {tc.name} {status}")

    # Display final response
    console.print("\n[bold]Agent response:[/bold]")
    console.print(Panel(result.final_text or "(no text response)", border_style="cyan"))

    # Display cost report
    console.print()
    tracker.print_report()

    if recorder:
        console.print(f"\n[dim]Session saved: {recorder.file}[/dim]")


@cli.command()
@click.argument("session_file", type=click.Path(exists=True, path_type=Path))
def replay(session_file: Path):
    """Replay a recorded session without making API calls.

    Example: python -m agent.cli replay sessions/20260224_143022.jsonl
    """
    replayer = SessionReplayer(session_file)
    tools = get_all_tools()

    loop = AgentLoop(
        tools=tools,
        system_prompt=ORCHESTRATOR_PROMPT,
        replayer=replayer,
    )

    console.print(f"\n[bold yellow]Replaying session:[/bold yellow] {session_file}")
    summary = replayer.summary()
    console.print(f"  API calls: {summary['api_calls']}")
    console.print(f"  Tool executions: {summary['tool_executions']}\n")

    with console.status("[bold yellow]Replaying..."):
        result = loop.run("(replayed)")

    if result.tool_calls:
        console.print(f"\n[bold]Tool calls ({len(result.tool_calls)}):[/bold]")
        for tc in result.tool_calls:
            console.print(f"  [yellow]>[/yellow] {tc.name}")

    console.print("\n[bold]Agent response:[/bold]")
    console.print(Panel(result.final_text or "(no text response)", border_style="yellow"))


@cli.command()
def sessions():
    """List recorded sessions.

    Example: python -m agent.cli sessions
    """
    if not SESSIONS_DIR.exists():
        console.print("[dim]No sessions directory found.[/dim]")
        return

    files = sorted(SESSIONS_DIR.glob("*.jsonl"), reverse=True)
    if not files:
        console.print("[dim]No recorded sessions found.[/dim]")
        return

    console.print(f"\n[bold]Recorded sessions ({len(files)}):[/bold]")
    for f in files:
        replayer = SessionReplayer(f)
        s = replayer.summary()
        size_kb = f.stat().st_size / 1024
        console.print(
            f"  {f.name}  "
            f"[dim]API:{s['api_calls']}  Tools:{s['tool_executions']}  "
            f"{size_kb:.1f}KB[/dim]"
        )


@cli.command()
@click.argument("session_file", type=click.Path(exists=True, path_type=Path))
def cost(session_file: Path):
    """Show cost report for a recorded session.

    Example: python -m agent.cli cost sessions/20260224_143022.jsonl
    """
    replayer = SessionReplayer(session_file)
    tracker = TokenTracker()

    from agent.tracker import APICallRecord

    for entry in replayer.api_calls:
        usage = entry.get("usage", {})
        rec = APICallRecord(
            model=entry.get("model", "unknown"),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            latency_ms=entry.get("latency_ms", 0),
        )
        tracker.calls.append(rec)

    console.print(f"\n[bold]Cost report for:[/bold] {session_file}\n")
    tracker.print_report()


def main():
    cli()


if __name__ == "__main__":
    main()
