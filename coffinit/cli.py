"""Command line interface for coffinit."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as package_version

import typer
from dotenv import load_dotenv
import os
import sys
from typing import Final
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
from .i18n import set_locale, t, get_locale
from .config import get_saved_lang, save_lang


try:
    __version__ = package_version("coffinit")
except PackageNotFoundError:  # pragma: no cover - package metadata is unavailable in source checkouts
    __version__ = "0.0.0"


console = Console()
app = typer.Typer(add_completion=False, help="GitHub OSSの生死を診断するCLIです。")


def _read_key() -> str:
    """Read a single keypress and return one of: 'left','right','enter','other'."""
    if os.name == "nt":
        import msvcrt

        first = msvcrt.getwch()
        if first == "\x00" or first == "\xe0":
            second = msvcrt.getwch()
            if second == "K":
                return "left"
            if second == "M":
                return "right"
        if first == "\r":
            return "enter"
        return "other"
    else:
        import tty
        import termios

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch1 = sys.stdin.read(1)
            if ch1 == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    if ch3 == "D":
                        return "left"
                    if ch3 == "C":
                        return "right"
            if ch1 == "\r" or ch1 == "\n":
                return "enter"
            return "other"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


@app.command()
def set_lang() -> None:
    """Interactively choose the display language for this session.

    Note: setting the language here cannot modify the parent shell's environment.
    After selection this command prints the shell commands to export the
    variable for your shell so you can copy/paste or `eval` them as appropriate.
    """

    options: Final = ["ja", "en"]
    idx = 0
    sys.stdout.write("Select language: Use ← → to choose, Enter to confirm\n")
    sys.stdout.flush()

    def _render(i: int) -> None:
        parts = []
        for n, opt in enumerate(options):
            if n == i:
                parts.append(f"\x1b[33m[{opt}]\x1b[0m")
            else:
                parts.append(f" {opt} ")
        sys.stdout.write("\r" + " | ".join(parts))
        sys.stdout.flush()

    _render(idx)
    while True:
        key = _read_key()
        if key == "left":
            idx = (idx - 1) % len(options)
            _render(idx)
        elif key == "right":
            idx = (idx + 1) % len(options)
            _render(idx)
        elif key == "enter":
            break

    chosen = options[idx]
    sys.stdout.write("\n")
    # set in-process for immediate effect in this process
    os.environ["COFFINIT_LANG"] = chosen

    config_path = None
    try:
        config_path = save_lang(chosen)
    except Exception:
        config_path = None

    # Print shell commands for the user to apply to their shell session
    sys.stdout.write(f"Language selected: {chosen}\n")
    if config_path is not None:
        sys.stdout.write(f"Saved to config: {config_path}\n")
    sys.stdout.write("To apply this to your shell session, run:\n")
    sys.stdout.write("  Bash / WSL / zsh:\n")
    sys.stdout.write(f"    export COFFINIT_LANG={chosen}\n")
    sys.stdout.write("  PowerShell:\n")
    sys.stdout.write(f"    $env:COFFINIT_LANG = '{chosen}'\n")
    sys.stdout.flush()


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context, lang: str | None = None) -> None:
    """Entry point for the coffinit CLI."""

    load_dotenv()
    # Allow language selection via CLI option or COFFINIT_LANG environment variable
    env_lang = os.getenv("COFFINIT_LANG")

    saved_lang = get_saved_lang()
    selected = lang or env_lang or saved_lang or "ja"
    set_locale(selected)
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
        _print_error(t("errors.generic"))


def _print_banner() -> None:
    banner_text = t("banner")
    banner = Text(banner_text.strip("\n"), justify="left")
    console.print(Panel.fit(banner, border_style="cyan"))


def _print_error(message: str) -> None:
    console.print(f"[red]{message}[/red]")
    raise typer.Exit(code=1)


def main() -> None:
    """Run the Typer application."""

    app()


if __name__ == "__main__":
    main()