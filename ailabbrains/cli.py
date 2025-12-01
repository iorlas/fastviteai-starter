"""AI Lab Brains CLI - Simplified pipeline orchestration."""

import typer
from rich.console import Console
from rich.panel import Panel

from ailabbrains.orchestrator import process_urls

app = typer.Typer(
    name="ailabbrains",
    help="AI Lab Brains - Content extraction and summarization pipeline",
    add_completion=False,
)
console = Console()


@app.command()
def process() -> None:
    """Process URLs from manual_links.txt through the extraction and summarization pipeline."""
    console.print(Panel.fit("[bold blue]AI Lab Brains Pipeline[/bold blue]"))

    try:
        process_urls()
        console.print("\n[bold green]✓ Pipeline completed successfully![/bold green]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"\n[bold red]✗ Pipeline failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def stats() -> None:
    """Show processing statistics from artifacts."""

    from ailabbrains.config import settings
    from ailabbrains.storage import BronzeTable, SilverTable

    artifacts_path = settings.artifacts_path

    # Count bronze artifacts
    html_count = len(list((artifacts_path / BronzeTable.HTML).glob("*.json"))) if (artifacts_path / BronzeTable.HTML).exists() else 0
    youtube_count = (
        len(list((artifacts_path / BronzeTable.YOUTUBE_DOWNLOADS).glob("*/metadata.json")))
        if (artifacts_path / BronzeTable.YOUTUBE_DOWNLOADS).exists()
        else 0
    )
    discussion_count = (
        len(list((artifacts_path / BronzeTable.DISCUSSIONS).glob("*/metadata.json")))
        if (artifacts_path / BronzeTable.DISCUSSIONS).exists()
        else 0
    )

    # Count silver artifacts
    article_summary_count = (
        len(list((artifacts_path / SilverTable.ARTICLE_SUMMARIES).glob("*.json")))
        if (artifacts_path / SilverTable.ARTICLE_SUMMARIES).exists()
        else 0
    )
    final_summary_count = (
        len(list((artifacts_path / SilverTable.SUMMARIES).glob("*.json"))) if (artifacts_path / SilverTable.SUMMARIES).exists() else 0
    )

    console.print(Panel.fit("[bold]Artifacts Statistics[/bold]"))
    console.print("\n[cyan]Bronze Layer:[/cyan]")
    console.print(f"  HTML extractions:     {html_count}")
    console.print(f"  YouTube downloads:    {youtube_count}")
    console.print(f"  Discussions:          {discussion_count}")
    console.print("\n[cyan]Silver Layer:[/cyan]")
    console.print(f"  Article summaries:    {article_summary_count}")
    console.print(f"  Final summaries:      {final_summary_count}")


@app.command()
def clean_cache(
    layer: str = typer.Option(
        "http",
        "--layer",
        "-l",
        help="Cache layer to clean: 'http', 'bronze', 'silver', or 'all'",
    ),
) -> None:
    """Clean cache files."""
    import shutil

    from ailabbrains.config import settings
    from ailabbrains.storage import BronzeTable, SilverTable

    artifacts_path = settings.artifacts_path

    if layer == "http" or layer == "all":
        cache_path = artifacts_path / "cache" / "http_responses"
        if cache_path.exists():
            shutil.rmtree(cache_path)
            console.print(f"[green]✓ Cleaned HTTP cache: {cache_path}[/green]")

    if layer == "bronze" or layer == "all":
        for table in BronzeTable:
            bronze_path = artifacts_path / table
            if bronze_path.exists():
                shutil.rmtree(bronze_path)
                console.print(f"[green]✓ Cleaned bronze layer: {bronze_path}[/green]")

    if layer == "silver" or layer == "all":
        for table in SilverTable:
            silver_path = artifacts_path / table
            if silver_path.exists():
                shutil.rmtree(silver_path)
                console.print(f"[green]✓ Cleaned silver layer: {silver_path}[/green]")

    console.print("[bold green]✓ Cache cleaning complete[/bold green]")


if __name__ == "__main__":
    app()
