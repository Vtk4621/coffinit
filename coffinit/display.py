"""Rich output for coffinit."""

from __future__ import annotations

from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group

from .github import RepositorySnapshot
from .scorer import RepositoryAssessment


COFFIN_ART = {
    "全開": """
        ______
       /      \\
      /  ALIVE  \\
     /____________\\
     |            |
     |            |
     |            |
     |____________|
    """,
    "半開き": """
     ____/????????\\
    /____________\\
    |            |
    |   u ok..?  |
    |            |
    |____________|
    """,
    "ちょっと開いてる": """
     ____________
    /--__________\\
    |            |
    |  R.I.P...? |
    |            |
    |____________|
    """,
    "閉じてる": """
     ____________
    /????????????\\
    |            |
    |   R.I.P    |
    |            |
    |____________|
    """,
}


STATUS_STYLE = {
    "全開": "green",
    "半開き": "yellow",
    "ちょっと開いてる": "magenta",
    "閉じてる": "red",
}


def render_coffin_art(coffin_state: str) -> Panel:
    """Render the coffin art panel for the current diagnosis."""

    art = COFFIN_ART.get(coffin_state, COFFIN_ART["閉じてる"])
    style = STATUS_STYLE.get(coffin_state, "red")
    return Panel.fit(
        Align.center(Text(art.strip("\n"), style=style)),
        border_style=style,
        padding=(1, 2),
    )


def build_repository_report(snapshot: RepositorySnapshot, assessment: RepositoryAssessment) -> Group:
    """Build the full Rich renderable for a repository diagnosis."""

    header = Text(f"🪣 coffinit — {snapshot.repository.full_name}", style="bold")
    score = Text(f"Score: {assessment.total_score} / 100  {assessment.label}", justify="center")

    detail_table = Table(title="詳細スコア", box=box.SQUARE, show_header=True, header_style="bold")
    detail_table.add_column("項目", style="cyan")
    detail_table.add_column("点数", justify="right", style="white")
    for section in (
        assessment.breakdown.maintenance,
        assessment.breakdown.pull_request_response,
        assessment.breakdown.bug_backlog,
        assessment.breakdown.author_activity,
    ):
        detail_table.add_row(section.name, f"{section.score}/25")

    raw_table = Table(title="生データ", box=box.SQUARE, show_header=True, header_style="bold")
    raw_table.add_column("項目", style="cyan")
    raw_table.add_column("値", style="white")
    raw_table.add_row("最終コミット", assessment.breakdown.maintenance.raw_value)
    raw_table.add_row("最新PR", assessment.breakdown.pull_request_response.raw_value)
    raw_table.add_row("bugラベルIssue", assessment.breakdown.bug_backlog.raw_value)
    raw_table.add_row("最近のコントリビューター", assessment.breakdown.author_activity.raw_value)

    return Group(
        header,
        render_coffin_art(assessment.coffin_state),
        Panel.fit(Align.center(score), border_style=STATUS_STYLE.get(assessment.coffin_state, "red")),
        detail_table,
        raw_table,
    )