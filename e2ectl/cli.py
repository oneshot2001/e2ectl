"""e2ectl CLI — Click-based command interface."""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from e2ectl import __version__

console = Console()


def _run(coro: Any) -> Any:
    """Run an async coroutine from sync Click context."""
    return asyncio.run(coro)


@click.group()
@click.version_option(__version__, prog_name="e2ectl")
@click.option("--user", "-u", default="root", help="Default username for device auth.")
@click.option("--password", "-p", default="", help="Default password for device auth.")
@click.option("--timeout", "-t", default=10, type=int, help="Timeout per API call (seconds).")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json", "yaml", "csv"]),
    default="table",
    help="Output format.",
)
@click.option("--verbose", "-v", is_flag=True, help="Show verbose/debug output.")
@click.option("--dry-run", is_flag=True, help="Show what would happen without executing.")
@click.pass_context
def cli(
    ctx: click.Context,
    user: str,
    password: str,
    timeout: int,
    output: str,
    verbose: bool,
    dry_run: bool,
) -> None:
    """e2ectl — kubectl-style CLI for Axis edge-to-edge device pairing."""
    ctx.ensure_object(dict)
    ctx.obj["user"] = user
    ctx.obj["password"] = password
    ctx.obj["timeout"] = timeout
    ctx.obj["output"] = output
    ctx.obj["verbose"] = verbose
    ctx.obj["dry_run"] = dry_run

    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")


@cli.command()
@click.option(
    "--range", "-r", "cidr", required=True,
    help="CIDR range to scan (e.g. 10.1.1.0/24).",
)
@click.pass_context
def discover(ctx: click.Context, cidr: str) -> None:
    """Scan a subnet for Axis devices."""
    from e2ectl.discovery.scanner import scan_subnet
    from e2ectl.reporting.table import render_devices

    user: str = ctx.obj["user"]
    password: str = ctx.obj["password"]
    timeout: int = ctx.obj["timeout"]
    output: str = ctx.obj["output"]
    verbose: bool = ctx.obj["verbose"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(f"Scanning {cidr}...", total=None)
        devices = _run(scan_subnet(cidr, user, password, timeout, verbose))

    if not devices:
        console.print("[yellow]No Axis devices found.[/yellow]")
        return

    render_devices(devices, output)


@cli.command()
@click.option("--file", "-f", "manifest_path", required=True, help="Path to manifest YAML.")
@click.pass_context
def plan(ctx: click.Context, manifest_path: str) -> None:
    """Validate a manifest and show what would be applied."""
    from e2ectl.manifest.parser import ManifestError, load_manifest
    from e2ectl.reporting.table import render_manifest_summary

    try:
        manifest = load_manifest(manifest_path, strict_env=False)
    except ManifestError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(3)

    render_manifest_summary(manifest)

    console.print("\n[bold]Planned pairings:[/bold]")
    for p in manifest.pairings:
        primary_dev = next(d for d in manifest.devices if d.name == p.primary)
        secondary_dev = next(d for d in manifest.devices if d.name == p.secondary)
        labels = ", ".join(f"{k}={v}" for k, v in p.labels.items()) if p.labels else ""
        console.print(
            f"  [cyan]{p.name}[/cyan]: {primary_dev.ip} → {secondary_dev.ip} "
            f"({p.type}{', ' + p.subtype if p.subtype else ''})"
            + (f" [{labels}]" if labels else "")
        )

    console.print(
        f"\n[green]Manifest is valid.[/green] "
        f"Run [bold]e2ectl apply -f {manifest_path}[/bold] to execute."
    )


@cli.command()
@click.option("--file", "-f", "manifest_path", required=True, help="Path to manifest YAML.")
@click.pass_context
def apply(ctx: click.Context, manifest_path: str) -> None:
    """Execute pairings from a manifest."""
    from e2ectl.manifest.parser import ManifestError, load_manifest
    from e2ectl.pairing.engine import PairingEngine
    from e2ectl.reporting.table import render_apply_result

    verbose: bool = ctx.obj["verbose"]
    dry_run: bool = ctx.obj["dry_run"]

    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(3)

    if dry_run:
        console.print("[yellow]Dry run — no changes will be made.[/yellow]")
        ctx.invoke(plan, manifest_path=manifest_path)
        return

    engine = PairingEngine(manifest, verbose=verbose)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Applying pairings...", total=None)
        result = _run(engine.apply())

    render_apply_result(result)
    sys.exit(result.exit_code)


@cli.command()
@click.option("--file", "-f", "manifest_path", required=True, help="Path to manifest YAML.")
@click.pass_context
def verify(ctx: click.Context, manifest_path: str) -> None:
    """Check the live state of pairings declared in a manifest."""
    from e2ectl.manifest.parser import ManifestError, load_manifest
    from e2ectl.models.pairing import PairingType
    from e2ectl.pairing import radar_ptz
    from e2ectl.pairing.engine import ApplyResult, PairingResult
    from e2ectl.reporting.table import render_apply_result as _render
    from e2ectl.vapix.client import VapixClient

    verbose: bool = ctx.obj["verbose"]

    try:
        manifest = load_manifest(manifest_path, strict_env=False)
    except ManifestError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(3)

    devices = {d.name: d for d in manifest.devices}
    result = ApplyResult()

    async def _verify() -> None:
        for p in manifest.pairings:
            primary = devices[p.primary]
            secondary = devices[p.secondary]
            creds = manifest.defaults.credentials

            pr = PairingResult(
                name=p.name,
                pairing_type=p.type,
                primary=primary.ip,
                secondary=secondary.ip,
            )

            if p.type == PairingType.RADAR_PTZ:
                async with VapixClient(
                    ip=primary.ip,
                    username=creds.username,
                    password=creds.password,
                    timeout=manifest.defaults.timeout,
                    verbose=verbose,
                ) as client:
                    pr.state = await radar_ptz.get_camera_connection(client)
                    pr.success = pr.state == "connected"
            else:
                pr.error = f"Verify not implemented for type: {p.type}"

            result.results.append(pr)

    _run(_verify())
    _render(result)


@cli.command()
@click.option("--file", "-f", "manifest_path", required=True, help="Path to manifest YAML.")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def teardown(ctx: click.Context, manifest_path: str, yes: bool) -> None:
    """Remove all pairings declared in a manifest."""
    from e2ectl.manifest.parser import ManifestError, load_manifest
    from e2ectl.pairing.engine import PairingEngine
    from e2ectl.reporting.table import render_apply_result

    verbose: bool = ctx.obj["verbose"]

    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(3)

    if not yes:
        console.print(
            f"[yellow]This will remove {len(manifest.pairings)} pairing(s).[/yellow]"
        )
        if not click.confirm("Continue?"):
            console.print("Aborted.")
            return

    engine = PairingEngine(manifest, verbose=verbose)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Tearing down pairings...", total=None)
        result = _run(engine.teardown())

    render_apply_result(result)
    sys.exit(result.exit_code)
