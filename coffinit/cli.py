"""Command line interface for coffinit."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as package_version

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .display import build_repository_report
from .github import (
    GitHubAPIError,
    GitHubClient,
    GitHubNetworkError,
    GitHubNotConfiguredError,
    GitHubPrivateRepositoryError,
    GitHubRateLimitError,
    GitHubRepositoryNotFoundError,
)
from .scorer import assess_repository


try:
    __version__ = package_version("coffinit")
except PackageNotFoundError:  # pragma: no cover - package metadata is unavailable in source checkouts
    __version__ = "0.0.0"


console = Console()
app = typer.Typer(add_completion=False, help="GitHub OSSの生死を診断するCLIです。")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Entry point for the coffinit CLI."""

    load_dotenv()
    if ctx.invoked_subcommand is None:
        _print_banner()


@app.command()
def check(repository: str) -> None:
    """Diagnose a GitHub repository."""

    load_dotenv()
    client = GitHubClient.from_env()
    try:
        snapshot = client.fetch_repository_snapshot(repository)
        assessment = assess_repository(snapshot)
        console.print(build_repository_report(snapshot, assessment))
    except GitHubRepositoryNotFoundError as error:
        _print_error(str(error))
    except GitHubPrivateRepositoryError as error:
        _print_error(str(error))
    except GitHubRateLimitError as error:
        _print_error(str(error))
    except GitHubNotConfiguredError as error:
        _print_error(str(error))
    except GitHubNetworkError as error:
        _print_error(str(error))
    except GitHubAPIError as error:
        _print_error(str(error))
    except ValueError as error:
        _print_error(str(error))
    except Exception:  # pragma: no cover - last resort safety net for the CLI boundary
        _print_error("なんか葬儀場で事故が起きたみたいだ。")


def _print_banner() -> None:
    banner = Text(
        """
    _________________________
   |                         |
   |     🪣 coffinit       |
   |  Things OSS projects    |
   |  do before they die.    |
   |_________________________|

  Usage: coffinit check <owner>/<repo>
        """.strip("\n"),
        justify="left",
    )
    console.print(Panel.fit(banner, border_style="cyan"))


def _print_error(message: str) -> None:
    console.print(f"[red]{message}[/red]")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()