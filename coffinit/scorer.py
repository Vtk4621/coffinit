"""Scoring logic for coffinit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .github import RepositorySnapshot
from .i18n import t


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
    label_key: str
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
    label_key, coffin_state = _label_for_score(total_score)
    return RepositoryAssessment(
        total_score=total_score,
        label_key=label_key,
        coffin_state=coffin_state,
        breakdown=breakdown,
    )


def _score_maintenance(last_commit_at: datetime | None, now: datetime) -> ScoreSection:
    if last_commit_at is None:
        return ScoreSection("section.maintenance", 0, t("raw.no_last_commit"))

    days = _days_since(last_commit_at, now)
    score = _bucket_score(days, [(30, 25), (90, 18), (180, 10), (365, 5)], 0)
    return ScoreSection("section.maintenance", score, t("raw.last_commit_days").format(days=days))


def _score_pull_request_response(latest_open_pr_created_at: datetime | None, now: datetime) -> ScoreSection:
    if latest_open_pr_created_at is None:
        return ScoreSection("section.pull_request_response", 25, t("raw.no_open_pr"))

    days = _days_since(latest_open_pr_created_at, now)
    score = _bucket_score(days, [(14, 25), (30, 18), (90, 10), (180, 5)], 0)
    return ScoreSection("section.pull_request_response", score, t("raw.latest_pr_days").format(days=days))


def _score_bug_backlog(open_count: int, closed_count: int) -> ScoreSection:
    total = open_count + closed_count
    if total <= 0:
        return ScoreSection("section.bug_backlog", 25, t("raw.no_bug_issues"))

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
    return ScoreSection("section.bug_backlog", score, t("raw.open_rate").format(percent=percent))


def _score_author_activity(contributor_last_commit_dates: tuple[datetime, ...], now: datetime) -> ScoreSection:
    if not contributor_last_commit_dates:
        return ScoreSection("section.author_activity", 0, t("raw.no_contributor_info"))

    latest_activity = max(contributor_last_commit_dates)
    days = _days_since(latest_activity, now)
    score = _bucket_score(days, [(30, 25), (90, 18), (180, 10), (365, 5)], 0)
    return ScoreSection("section.author_activity", score, t("raw.recent_activity_days").format(days=days))


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
        return "labels.alive", "full"
    if total_score >= 50:
        return "labels.struggling", "half"
    if total_score >= 20:
        return "labels.bucket", "small"
    return "labels.dead", "closed"