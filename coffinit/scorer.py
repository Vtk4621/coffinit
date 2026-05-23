"""Scoring logic for coffinit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .github import RepositorySnapshot


@dataclass(frozen=True, slots=True)
class ScoreSection:
    """One axis of the coffinit score."""

    name: str
    score: int
    raw_value: str


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    """Detailed score breakdown."""

    maintenance: ScoreSection
    pull_request_response: ScoreSection
    bug_backlog: ScoreSection
    author_activity: ScoreSection


@dataclass(frozen=True, slots=True)
class RepositoryAssessment:
    """Total diagnosis for a repository."""

    total_score: int
    label: str
    coffin_state: str
    breakdown: ScoreBreakdown


def assess_repository(snapshot: RepositorySnapshot) -> RepositoryAssessment:
    """Calculate the coffinit score from GitHub snapshot data."""

    maintenance = _score_maintenance(snapshot.last_commit_at, snapshot.fetched_at)
    pull_request_response = _score_pull_request_response(snapshot.latest_open_pr_created_at, snapshot.fetched_at)
    bug_backlog = _score_bug_backlog(snapshot.bug_issue_open_count, snapshot.bug_issue_closed_count)
    author_activity = _score_author_activity(snapshot.contributor_last_commit_dates, snapshot.fetched_at)

    breakdown = ScoreBreakdown(
        maintenance=maintenance,
        pull_request_response=pull_request_response,
        bug_backlog=bug_backlog,
        author_activity=author_activity,
    )
    total_score = maintenance.score + pull_request_response.score + bug_backlog.score + author_activity.score
    label, coffin_state = _label_for_score(total_score)
    return RepositoryAssessment(
        total_score=total_score,
        label=label,
        coffin_state=coffin_state,
        breakdown=breakdown,
    )


def _score_maintenance(last_commit_at: datetime | None, now: datetime) -> ScoreSection:
    if last_commit_at is None:
        return ScoreSection("メンテナンス状況", 0, "最終コミットなし")

    days = _days_since(last_commit_at, now)
    score = _bucket_score(days, [(30, 25), (90, 18), (180, 10), (365, 5)], 0)
    return ScoreSection("メンテナンス状況", score, f"最終コミットから{days}日")


def _score_pull_request_response(latest_open_pr_created_at: datetime | None, now: datetime) -> ScoreSection:
    if latest_open_pr_created_at is None:
        return ScoreSection("PRへの反応", 25, "オープンPRなし")

    days = _days_since(latest_open_pr_created_at, now)
    score = _bucket_score(days, [(14, 25), (30, 18), (90, 10), (180, 5)], 0)
    return ScoreSection("PRへの反応", score, f"最新PRから{days}日")


def _score_bug_backlog(open_count: int, closed_count: int) -> ScoreSection:
    total = open_count + closed_count
    if total <= 0:
        return ScoreSection("バグIssueの放置率", 25, "bugラベルIssueなし")

    ratio = open_count / total
    percent = round(ratio * 100)
    if percent <= 10:
        score = 25
    elif percent <= 30:
        score = 18
    elif percent <= 50:
        score = 10
    elif percent <= 70:
        score = 5
    else:
        score = 0
    return ScoreSection("バグIssueの放置率", score, f"オープン率{percent}%")


def _score_author_activity(contributor_last_commit_dates: tuple[datetime, ...], now: datetime) -> ScoreSection:
    if not contributor_last_commit_dates:
        return ScoreSection("制作者のアクティビティ", 0, "コントリビューター情報なし")

    latest_activity = max(contributor_last_commit_dates)
    days = _days_since(latest_activity, now)
    score = _bucket_score(days, [(30, 25), (90, 18), (180, 10), (365, 5)], 0)
    return ScoreSection("制作者のアクティビティ", score, f"最近の活動から{days}日")


def _days_since(earlier: datetime, later: datetime) -> int:
    delta = later.astimezone(timezone.utc) - earlier.astimezone(timezone.utc)
    return max(0, delta.days)


def _bucket_score(value: int, thresholds: list[tuple[int, int]], default_score: int) -> int:
    for maximum, score in thresholds:
        if value <= maximum:
            return score
    return default_score


def _label_for_score(total_score: int) -> tuple[str, str]:
    if total_score >= 80:
        return "✅ Alive", "全開"
    if total_score >= 50:
        return "⚠️ Struggling", "半開き"
    if total_score >= 20:
        return "🪦 On The Bucket List", "ちょっと開いてる"
    return "⚰️ Dead", "閉じてる"