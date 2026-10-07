"""Typer CLI for llm-sizer."""

from __future__ import annotations

import json
import sys

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from llm_sizer.catalog import MODELS, parse_context, resolve_model, resolve_quant
from llm_sizer.report import COUNSELNODE_BLURB, build_result
from llm_sizer.sizing import estimate_vram


def _enable_utf8_console() -> None:
    """Make emoji and box-drawing characters work on Windows terminals."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass


_enable_utf8_console()
console = Console(legacy_windows=False, stderr=True)
stdout = Console(legacy_windows=False)


def format_gb(value: float) -> str:
    if value >= 1024:
        return f"{value / 1024:.2f} TB"
    if value < 1:
        return f"{value * 1024:.1f} MB"
    return f"{value:.2f} GB"


def format_usd(value: float) -> str:
    return f"${value:,.0f}/mo" if value >= 100 else f"${value:,.2f}/mo"


def render_models(as_json: bool) -> None:
    rows = [
        {
            "id": key,
            "name": spec.name,
            "params_billions": spec.params / 1e9,
            "num_layers": spec.num_layers,
            "hidden_size": spec.hidden_size,
        }
        for key, spec in MODELS.items()
    ]
    if as_json:
        stdout.print_json(json.dumps(rows))
        return

    table = Table(
        title="Supported models",
        box=box.SIMPLE_HEAVY,
        border_style="bright_cyan",
        header_style="bold",
    )
    table.add_column("id", style="bright_green")
    table.add_column("name")
    table.add_column("params", justify="right")
    table.add_column("layers", justify="right")
    table.add_column("hidden", justify="right")
    for row in rows:
        table.add_row(
            row["id"],
            row["name"],
            f"{row['params_billions']:.2f}B",
            str(row["num_layers"]),
            str(row["hidden_size"]),
        )
    stdout.print(table)


def render_report(result: dict) -> None:
    vram = result["vram_gb"]
    rec = result["recommendation"]
    header = Text()
    header.append("LLM SIZER", style="bold bright_cyan")
    header.append("  |  ", style="dim")
    header.append(result["model_name"], style="bold white")
    header.append(
        f"  |  {result['quant'].upper()}  |  {result['context']}  |  {result['concurrent_users']} users",
        style="bright_white",
    )
    stdout.print()
    stdout.print(Panel(header, border_style="bright_cyan", padding=(0, 2)))

    table = Table(
        title="VRAM & Instance Recommendation",
        title_style="bold bright_yellow",
        box=box.HEAVY_HEAD,
        border_style="bright_magenta",
        header_style="bold bright_white",
        show_lines=True,
        pad_edge=True,
        expand=True,
    )
    table.add_column("Weights VRAM", justify="right", style="bright_green")
    table.add_column("KV Cache VRAM", justify="right", style="bright_blue")
    table.add_column("Total VRAM", justify="right", style="bold bright_white")
    table.add_column("Recommended AWS Instance", justify="center", style="bright_cyan")
    table.add_column("Estimated Monthly Cost", justify="right", style="bold bright_yellow")

    if rec["fits_single_node"]:
        instance_label = f"{rec['instance']} ({rec['gpu']}, {rec['vram_gb']:g} GB)"
        cost = format_usd(rec["usd_per_month"])
    else:
        instance_label = "Multi-node cluster required"
        cost = "Contact sales"

    table.add_row(
        format_gb(vram["weights"]),
        format_gb(vram["kv_cache"]),
        format_gb(vram["total"]),
        instance_label,
        cost,
    )
    stdout.print(table)

    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="dim")
    meta.add_column(style="white")
    meta.add_row("params", f"{result['params_billions']:.2f}B")
    meta.add_row("bytes/param", f"{result['bytes_per_param']:g}")
    meta.add_row("context tokens", f"{result['context_tokens']:,}")
    stdout.print(meta)
    stdout.print()
    stdout.print(
        Panel(
            Text(COUNSELNODE_BLURB, style="bold bright_cyan"),
            border_style="bright_yellow",
            padding=(1, 2),
        )
    )


def main(
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Model id, e.g. deepseek-r1, llama-3-70b, qwen2.5-72b.",
    ),
    quant: str = typer.Option(
        "fp16",
        "--quant",
        "-q",
        help="Precision: fp16, bf16, q8, or q4.",
    ),
    concurrent_users: int = typer.Option(
        1,
        "--concurrent-users",
        "-u",
        min=1,
        help="Number of simultaneous sequences in the KV cache.",
    ),
    context: str = typer.Option(
        "8k",
        "--context",
        "-c",
        help="Context window, e.g. 8k, 32k, 128k, or 131072.",
    ),
    as_json: bool = typer.Option(
        False,
        "--json",
        help="Print machine-readable JSON for agents, scripts, and CI.",
    ),
    list_models: bool = typer.Option(
        False,
        "--list-models",
        help="List supported model ids and architecture specs.",
    ),
) -> None:
    """Estimate LLM VRAM and recommend the cheapest AWS GPU instance."""
    if list_models:
        render_models(as_json)
        return

    if not model:
        console.print("[bold red]Error:[/] --model is required unless you pass --list-models.")
        raise typer.Exit(code=2)

    try:
        spec = resolve_model(model)
        bytes_per_param = resolve_quant(quant)
        context_tokens = parse_context(context)
    except ValueError as exc:
        if as_json:
            stdout.print_json(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(code=1) from exc

    breakdown = estimate_vram(spec, bytes_per_param, context_tokens, concurrent_users)
    result = build_result(
        model_id=model,
        spec=spec,
        quant=quant,
        bytes_per_param=bytes_per_param,
        context_label=context,
        context_tokens=context_tokens,
        concurrent_users=concurrent_users,
        breakdown=breakdown,
    )
    if as_json:
        stdout.print_json(json.dumps(result))
        return
    render_report(result)


def run() -> None:
    typer.run(main)


if __name__ == "__main__":
    run()
