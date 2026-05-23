"""GitHub API access for coffinit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from typing import Any, Iterable

import requests


BASE_URL = "https://api.github.com"


class GitHubAPIError(RuntimeError):
    """Base error for GitHub API failures."""


class GitHubNotConfiguredError(GitHubAPIError):
    """Raised when a GitHub token is required but missing."""


class GitHubRepositoryNotFoundError(GitHubAPIError):
    """Raised when the requested repository does not exist."""


class GitHubPrivateRepositoryError(GitHubAPIError):
    """Raised when the requested repository is private or inaccessible."""


class GitHubRateLimitError(GitHubAPIError):
    """Raised when the API rate limit is exhausted."""


class GitHubNetworkError(GitHubAPIError):
    """Raised when the network request cannot be completed."""


@dataclass(frozen=True, slots=True)
class RepositoryMetadata:
    """Basic repository information used by coffinit."""

    owner: str
    name: str
    full_name: str
    private: bool
    default_branch: str | None
    html_url: str


@dataclass(frozen=True, slots=True)
class RepositorySnapshot:
    """Collected data used by the scorer and display layers."""

    repository: RepositoryMetadata
    last_commit_at: datetime | None
    latest_open_pr_created_at: datetime | None
    bug_issue_open_count: int
    bug_issue_closed_count: int
    contributor_last_commit_dates: tuple[datetime, ...]
    fetched_at: datetime


def parse_repository_slug(repository: str) -> tuple[str, str]:
    """Split an owner/repo string into its parts."""

    parts = repository.strip().split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("repository must be in owner/repo format")
    return parts[0], parts[1]


def parse_github_datetime(value: str | None) -> datetime | None:
    """Convert a GitHub timestamp into an aware datetime."""

    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class GitHubClient:
    """Small HTTP client for the GitHub REST API."""

    def __init__(self, token: str | None = None, session: requests.Session | None = None) -> None:
        self._token = token or os.getenv("GITHUB_TOKEN")
        self._session = session or requests.Session()

    @classmethod
    def from_env(cls) -> "GitHubClient":
        """Create a client using the current process environment."""

        return cls()

    def fetch_repository_snapshot(self, repository: str) -> RepositorySnapshot:
        """Fetch the API data required for a coffinit diagnosis."""

        owner, name = parse_repository_slug(repository)
        repository_data = self._get_json(f"/repos/{owner}/{name}")

        metadata = RepositoryMetadata(
            owner=owner,
            name=name,
            full_name=repository_data["full_name"],
            private=bool(repository_data.get("private", False)),
            default_branch=repository_data.get("default_branch"),
            html_url=repository_data.get("html_url", f"https://github.com/{owner}/{name}"),
        )

        commits = self._get_json(f"/repos/{owner}/{name}/commits", params={"per_page": 1})
        last_commit_at = self._first_datetime_from_items(commits, ("commit", "committer", "date"))

        pulls = self._get_json(
            f"/repos/{owner}/{name}/pulls",
            params={"state": "open", "sort": "created", "direction": "desc", "per_page": 1},
        )
        latest_open_pr_created_at = self._first_datetime_from_items(pulls, ("created_at",))

        issues = self._get_json(
            f"/repos/{owner}/{name}/issues",
            params={"labels": "bug", "state": "all", "per_page": 100},
        )
        bug_issue_open_count = 0
        bug_issue_closed_count = 0
        for issue in issues:
            if "pull_request" in issue:
                continue
            if issue.get("state") == "open":
                bug_issue_open_count += 1
            else:
                bug_issue_closed_count += 1

        contributors = self._get_json(f"/repos/{owner}/{name}/contributors", params={"per_page": 3})
        contributor_last_commit_dates = tuple(
            date
            for date in (
                self._get_contributor_last_commit_date(owner, name, contributor.get("login"))
                for contributor in contributors
                if contributor.get("login")
            )
            if date is not None
        )

        return RepositorySnapshot(
            repository=metadata,
            last_commit_at=last_commit_at,
            latest_open_pr_created_at=latest_open_pr_created_at,
            bug_issue_open_count=bug_issue_open_count,
            bug_issue_closed_count=bug_issue_closed_count,
            contributor_last_commit_dates=contributor_last_commit_dates,
            fetched_at=datetime.now(timezone.utc),
        )

    def _get_contributor_last_commit_date(self, owner: str, name: str, login: str) -> datetime | None:
        commits = self._get_json(
            f"/repos/{owner}/{name}/commits",
            params={"author": login, "per_page": 1},
        )
        return self._first_datetime_from_items(commits, ("commit", "committer", "date"))

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if not self._token:
            raise GitHubNotConfiguredError("神父の名前も知らねぇのか？（GITHUB_TOKENを.envに設定しろ）")

        url = f"{BASE_URL}{path}"
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/vnd.github+json"}

        try:
            response = self._session.get(url, headers=headers, params=params, timeout=20)
        except requests.RequestException as exc:  # pragma: no cover - network failures are environment dependent
            raise GitHubNetworkError("霊柩車がパンクしちまった。") from exc

        if response.status_code == 404:
            raise GitHubRepositoryNotFoundError("この棺桶は空だ。死に損ないのジジババが終活のために買ったものなようだ。")
        if response.status_code == 403:
            if response.headers.get("X-RateLimit-Remaining") == "0" or "rate limit" in response.text.lower():
                raise GitHubRateLimitError("神父は今日はお休みだってよ。")
            raise GitHubPrivateRepositoryError("おいおい、家族以外葬儀の立ち合いはできねぇぜ？")
        if response.status_code == 429:
            raise GitHubRateLimitError("神父は今日はお休みだってよ。")
        if response.status_code >= 400:
            raise GitHubAPIError("なんか葬儀場で事故が起きたみたいだ。")

        payload = response.json()
        if isinstance(payload, dict) and payload.get("message", "").lower().startswith("api rate limit"):
            raise GitHubRateLimitError("神父は今日はお休みだってよ。")
        return payload

    def _first_datetime_from_items(self, items: Iterable[dict[str, Any]], path: tuple[str, ...]) -> datetime | None:
        for item in items:
            value: Any = item
            for key in path:
                if not isinstance(value, dict):
                    value = None
                    break
                value = value.get(key)
            parsed = parse_github_datetime(value if isinstance(value, str) else None)
            if parsed is not None:
                return parsed
        return None