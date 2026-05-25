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
        # Lid not overlapping the coffin (fully open)
"full": """
    ________         _________
   /________\\       /   ___   \\
  //         \\     /    | |    \\
 //  [ALIVE]  \\   / ____| |____ \\
//     C       \\ / |____   ____| \\
\\      O       //\\      | |      //
 \\     F      //  \\     | |     //
  \\    F     //    \\    | |    //
   \\   I    //      \\   | |   //
    \\  N   //        \\  |_|  //
     \\____//          \\     //
      \\__//            \\___//
""",

        # Lid overlaps roughly half of the coffin
"half": """
    ________  _________
   /________\\ /   ___   \\
  //         /    | |    \\
 // [ALIVE?]/ ____| |____ \\
//     C   / |____   ____| \\
\\      O   \\      | |      //
 \\     F    \\     | |     //
  \\    F     \\    | |    //
   \\   I    / \\   | |   //
    \\  N   //  \\  |_|  //
     \\____//    \\     //
      \\__//      \\___//

""",

        # Lid overlaps about three quarters of the coffin
"small": """
    _______________
   /_____/   ___   \\
  //    /    | |    \\
 /[R.I.P?]___| |____ \\
//    / |____   ____| \\
\\     \\      | |      //
 \\     \\     | |     //
  \\     \\    | |    //
   \\   I \\   | |   //
    \\  N  \\  |_|  //
     \\____ \\     //
      \\__// \\___//
""",

        # Lid fully closed, covers the coffin
"closed": """
    _________
   / [R.I.P] \\
  /    | |    \\
 / ____| |____ \\
/ |____   ____| \\
\\      | |      //
 \\     | |     //
  \\    | |    //
   \\   | |   //
    \\  |_|  //
     \\     //
      \\___//
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
    # Localized label for the score line (assessment.label_key already
    # contains the full i18n key, e.g. 'labels.alive')
    label_text = t(assessment.label_key)
    score = Text(f"Score: {assessment.total_score} / 100  {label_text}", justify="center")

    # The text displayed ON the coffin art must be language-independent
    # and use the fixed strings per coffin state as requested.
    art_label_map = {
        "full": "ALIVE",
        "half": "ALIVE?",
        "small": "R.I.P?",
        "closed": "R.I.P",
    }
    art_label = art_label_map.get(assessment.coffin_state, "")

    def lt(key: str, fallback: str) -> str:
        v = t(key)
        return v if v != key else fallback

    detail_table = Table(title=lt("detail.score_title", "詳細スコア"), box=box.SQUARE, show_header=True, header_style="bold")
    detail_table.add_column(lt("detail.column_item", "項目"), style="cyan")
    detail_table.add_column(lt("detail.column_score", "点数"), justify="right", style="white")
    for section in (
        assessment.breakdown.maintenance,
        assessment.breakdown.pull_request_response,
        assessment.breakdown.bug_backlog,
        assessment.breakdown.author_activity,
    ):
        # section.name should be an i18n key like 'sections.maintenance'. If
        # it is a key, translate it; otherwise assume it's a literal label.
        if "." in section.name:
            item_label = lt(section.name, section.name)
        else:
            item_label = section.name
        detail_table.add_row(item_label, f"{section.score}/25")

    raw_table = Table(title=lt("detail.raw_title", "生データ"), box=box.SQUARE, show_header=True, header_style="bold")
    raw_table.add_column(lt("detail.column_item", "項目"), style="cyan")
    raw_table.add_column(lt("detail.column_value", "値"), style="white")
    raw_table.add_row(lt("detail.last_commit", "最終コミット"), assessment.breakdown.maintenance.raw_value)
    raw_table.add_row(lt("detail.latest_pr", "最新PR"), assessment.breakdown.pull_request_response.raw_value)
    raw_table.add_row(lt("detail.bug_issues", "bugラベルIssue"), assessment.breakdown.bug_backlog.raw_value)
    raw_table.add_row(lt("detail.recent_contributor", "最近のコントリビューター"), assessment.breakdown.author_activity.raw_value)

    return Group(
        header,
        render_coffin_art(assessment.coffin_state, label_text=art_label),
        Panel.fit(Align.center(score), border_style=STATUS_STYLE.get(assessment.coffin_state, "red")),
        detail_table,
        raw_table,
    )