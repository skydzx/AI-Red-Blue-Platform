"""CLI tool for AI Red Blue Platform."""

import asyncio
import sys
from datetime import datetime, timezone
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ai_red_blue_common import get_settings, setup_logging, get_logger
from ai_red_blue_core import Alert, AlertSeverity, AlertStatus, AlertType, DetectionEngine
from ai_red_blue_security import SecurityUtils


# Initialize
settings = get_settings()
setup_logging()
logger = get_logger("cli")
console = Console()

# Storage for demo
alerts_db = {}


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, verbose: bool):
    """AI Red Blue Platform CLI."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    if verbose:
        setup_logging(log_level="DEBUG")
    click.echo("[+] AI Red Blue Platform CLI v0.1.0")


@cli.command()
def status():
    """Show platform status."""
    engine = DetectionEngine()
    stats = engine.get_statistics()

    table = Table(title="Platform Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    table.add_row("Core Library", "OK")
    table.add_row("Security Library", "OK")
    table.add_row(f"Detection Rules", str(stats["total_rules"]))
    table.add_row(f"Enabled Rules", str(stats["enabled_rules"]))
    table.add_row(f"Alerts", str(len(alerts_db)))

    console.print(table)


@cli.command()
@click.argument("title")
@click.argument("description")
@click.option("--severity", type=click.Choice(["critical", "high", "medium", "low"]), default="medium")
@click.option("--type", "alert_type", type=click.Choice(["threat_detection", "intrusion_detection", "malware_detection", "vulnerability"]), default="threat_detection")
@click.option("--source", default="CLI")
@click.option("--target", default=None)
def create_alert(title: str, description: str, severity: str, alert_type: str, source: str, target: Optional[str]):
    """Create a new alert."""
    alert = Alert(
        title=title,
        description=description,
        severity=AlertSeverity(severity),
        type=AlertType(alert_type),
        source=source,
        target=target,
    )
    alerts_db[alert.id] = alert
    click.echo(f"[+] Alert created: {alert.id}")
    click.echo(f"    Title: {title}")
    click.echo(f"    Severity: {severity.upper()}")


@cli.command()
def list_alerts():
    """List all alerts."""
    if not alerts_db:
        click.echo("[!] No alerts found")
        return

    table = Table(title="Alerts")
    table.add_column("ID", style="dim", width=8)
    table.add_column("Severity", width=10)
    table.add_column("Title", style="cyan")
    table.add_column("Status", width=12)
    table.add_column("Created", style="dim")

    for alert in sorted(alerts_db.values(), key=lambda x: x.created_at, reverse=True):
        severity_style = {
            "critical": "red",
            "high": "orange1",
            "medium": "yellow",
            "low": "green",
        }.get(alert.severity.value, "white")

        table.add_row(
            alert.id[:8],
            f"[{severity_style}]{alert.severity.value}[/]",
            alert.title,
            alert.status.value,
            alert.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


@cli.command()
@click.argument("alert_id")
def show_alert(alert_id: str):
    """Show alert details."""
    alert = alerts_db.get(alert_id)
    if not alert:
        click.echo(f"[!] Alert not found: {alert_id}")
        return

    panel = Panel(
        Text(f"{alert.description}\n\nStatus: {alert.status.value}\nSource: {alert.source}"),
        title=f"[bold cyan]{alert.title}[/]",
        subtitle=f"ID: {alert.id} | Severity: {alert.severity.value.upper()}",
    )
    console.print(panel)


@cli.command()
@click.argument("alert_id")
@click.option("--status", type=click.Choice(["open", "investigating", "resolved", "closed"]))
def update_alert(alert_id: str, status: str):
    """Update alert status."""
    alert = alerts_db.get(alert_id)
    if not alert:
        click.echo(f"[!] Alert not found: {alert_id}")
        return

    alert.status = AlertStatus(status)
    click.echo(f"[+] Alert {alert_id} status updated to {status}")


@cli.command()
@click.argument("content")
@click.option("--algorithm", type=click.Choice(["sha256", "sha512", "md5"]), default="sha256")
def hash(content: str, algorithm: str):
    """Calculate hash of content."""
    data = content.encode("utf-8")
    result = SecurityUtils.generate_fingerprint(data)
    click.echo(f"[+] {algorithm.upper()} Hash: {result.get(algorithm, '')}")


@cli.command()
@click.argument("content")
@click.option("--encoding", type=click.Choice(["base64", "hex", "url"]), default="base64")
def encode(content: str, encoding: str):
    """Encode content."""
    data = content.encode("utf-8")
    encoded = SecurityUtils.encode_payload(data, encoding)
    click.echo(f"[+] Encoded ({encoding}):")
    click.echo(encoded)


@cli.command()
@click.argument("encoded")
@click.option("--encoding", type=click.Choice(["base64", "hex", "url"]), default="base64")
def decode(encoded: str, encoding: str):
    """Decode content."""
    try:
        decoded = SecurityUtils.decode_payload(encoded, encoding)
        click.echo(f"[+] Decoded ({encoding}):")
        click.echo(decoded.decode("utf-8", errors="replace"))
    except Exception as e:
        click.echo(f"[!] Decode failed: {e}")


@cli.command()
def demo():
    """Create demo data."""
    sample_alerts = [
        Alert(
            title="Suspicious PowerShell Execution",
            description="Detected PowerShell execution with encoded commands",
            severity=AlertSeverity.HIGH,
            type=AlertType.THREAT_DETECTION,
            source="EDR",
            target="workstation-01",
        ),
        Alert(
            title="Brute Force Attempt",
            description="Multiple failed login attempts detected",
            severity=AlertSeverity.MEDIUM,
            type=AlertType.INTRUSION_DETECTION,
            source="WAF",
            target="web-server",
        ),
        Alert(
            title="Malware Detected",
            description="Known malware signature found",
            severity=AlertSeverity.CRITICAL,
            type=AlertType.MALWARE_DETECTION,
            source="AV",
            target="file-server",
        ),
    ]

    for alert in sample_alerts:
        alerts_db[alert.id] = alert

    click.echo(f"[+] Created {len(sample_alerts)} demo alerts")


@cli.command()
def version():
    """Show version."""
    click.echo("AI Red Blue Platform CLI v0.1.0")


@cli.command()
@click.argument("message")
@click.option("--provider", type=click.Choice(["openai", "anthropic"]), default="openai")
def chat(message: str, provider: str):
    """Chat with AI provider."""
    import asyncio
    from ai_red_blue_ai import OpenAIProvider, AnthropicProvider, ProviderConfig, ProviderType, ChatMessage, ChatRole

    async def _chat():
        try:
            if provider == "openai":
                config = ProviderConfig(
                    type=ProviderType.OPENAI,
                    name="openai",
                    api_key=settings.openai_api_key or "",
                )
                provider_obj = OpenAIProvider(config)
            else:
                config = ProviderConfig(
                    type=ProviderType.ANTHROPIC,
                    name="anthropic",
                    api_key=settings.anthropic_api_key or "",
                )
                provider_obj = AnthropicProvider(config)

            messages = [ChatMessage(role=ChatRole.USER, content=message)]
            response = await provider_obj.chat(messages)

            click.echo(f"[AI {provider}]")
            click.echo(response.content)
        except Exception as e:
            click.echo(f"[!] Chat error: {e}")

    asyncio.run(_chat())


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
