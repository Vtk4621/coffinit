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
from .i18n import t


COFFIN_ART = {
    "full": """
        ______
       /      \\
      /  {label}  \\
     /____________\\
     |            |
     |            |
     |            |
     |____________|
    """,
    "half": """
     ____/????????\\
    /____________\\
    |            |
    |   u ok..?  |
    |            |
    |____________|
    """,
    "small": """
     ____________
    /--__________\\
    |            |
    |  R.I.P...? |
    |            |
    |____________|
    """,
    "closed": """
     ____________
    /????????????\\
    |            |
    |   R.I.P    |
    |            |
    |____________|
    """,
}


STATUS_STYLE = {
    "full": "green",
    "half": "yellow",
    "small": "magenta",
    "closed": "red",
}


def render_coffin_art(coffin_state: str, label_text: str | None = None) -> Panel:
    """Render the coffin art panel for the current diagnosis."""
    art = COFFIN_ART.get(coffin_state, COFFIN_ART["closed"])
    style = STATUS_STYLE.get(coffin_state, "red")
    label_text = label_text or ""
    art_formatted = art.format(label=label_text)
    return Panel.fit(
        Align.center(Text(art_formatted.strip("\n"), style=style)),
        border_style=style,
        padding=(1, 2),
    )


def build_repository_report(snapshot: RepositorySnapshot, assessment: RepositoryAssessment) -> Group:
    """Build the full Rich renderable for a repository diagnosis."""

    header = Text(f"🪣 coffinit — {snapshot.repository.full_name}", style="bold")
    label_text = t(f"labels.{assessment.label_key}")
    score = Text(f"Score: {assessment.total_score} / 100  {label_text}", justify="center")

    detail_table = Table(title=t("detail.score_title") if t("detail.score_title") != "detail.score_title" else "詳細スコア", box=box.SQUARE, show_header=True, header_style="bold")
    detail_table.add_column(t("detail.column_item") if t("detail.column_item") != "detail.column_item" else "項目", style="cyan")
    detail_table.add_column(t("detail.column_score") if t("detail.column_score") != "detail.column_score" else "点数", justify="right", style="white")
    for section in (
        assessment.breakdown.maintenance,
        assessment.breakdown.pull_request_response,
        assessment.breakdown.bug_backlog,
        assessment.breakdown.author_activity,
    ):
        detail_table.add_row(t(section.name) if t(section.name) != section.name else section.name, f"{section.score}/25")

    raw_table = Table(title=t("detail.raw_title") if t("detail.raw_title") != "detail.raw_title" else "生データ", box=box.SQUARE, show_header=True, header_style="bold")
    raw_table.add_column(t("detail.column_item") if t("detail.column_item") != "detail.column_item" else "項目", style="cyan")
    raw_table.add_column(t("detail.column_value") if t("detail.column_value") != "detail.column_value" else "値", style="white")
    raw_table.add_row(t("detail.last_commit") if t("detail.last_commit") != "detail.last_commit" else "最終コミット", assessment.breakdown.maintenance.raw_value)
    raw_table.add_row(t("detail.latest_pr") if t("detail.latest_pr") != "detail.latest_pr" else "最新PR", assessment.breakdown.pull_request_response.raw_value)
    raw_table.add_row(t("detail.bug_issues") if t("detail.bug_issues") != "detail.bug_issues" else "bugラベルIssue", assessment.breakdown.bug_backlog.raw_value)
    raw_table.add_row(t("detail.recent_contributor") if t("detail.recent_contributor") != "detail.recent_contributor" else "最近のコントリビューター", assessment.breakdown.author_activity.raw_value)

    return Group(
        header,
        render_coffin_art(assessment.coffin_state, label_text=label_text),
        Panel.fit(Align.center(score), border_style=STATUS_STYLE.get(assessment.coffin_state, "red")),
        detail_table,
        raw_table,
    )