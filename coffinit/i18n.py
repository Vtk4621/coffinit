"""Simple i18n helper for coffinit.

This module provides a minimal message catalog and runtime locale
selection. It supports English (`en`) and Japanese (`ja`) and a
`t(key)` helper to fetch messages by dotted keys.
"""

from __future__ import annotations

from typing import Any

_LOCALE = "ja"

MESSAGES: dict[str, dict[str, Any]] = {
    "ja": {
        "banner": """
    _________________________
   |                         |
   |     🪣 coffinit       |
   |  Things OSS projects    |
   |  do before they die.    |
   |_________________________|

  Usage: coffinit check <owner>/<repo>
        """,
        "errors": {
            "token_missing": "神父の名前も知らねぇのか？（GITHUB_TOKENを.envに設定しろ）",
            "repo_not_found": "この棺桶は空だ。死に損ないのジジババが終活のために買ったものなようだ。",
            "private_repo": "おいおい、家族以外葬儀の立ち合いはできねぇぜ？",
            "rate_limit": "神父は今日はお休みだってよ。",
            "network": "霊柩車がパンクしちまった。",
            "generic": "なんか葬儀場で事故が起きたみたいだ。",
        },
        "labels": {
            "alive": "✅ Alive",
            "struggling": "⚠️ Struggling",
            "bucket": "🪦 On The Bucket List",
            "dead": "⚰️ Dead",
        },
        "detail": {
            "score_title": "詳細スコア",
            "raw_title": "生データ",
            "column_item": "項目",
            "column_score": "点数",
            "column_value": "値",
            "last_commit": "最終コミット",
            "latest_pr": "最新PR",
            "bug_issues": "bugラベルIssue",
            "recent_contributor": "最近のコントリビューター",
        },
        "sections": {
            "maintenance": "メンテナンス状況",
            "pull_request_response": "PRへの反応",
            "bug_backlog": "バグIssueの放置率",
            "author_activity": "制作者のアクティビティ",
        },
        "raw": {
            "last_commit_days": "最終コミットから{days}日",
            "no_last_commit": "最終コミットなし",
            "no_open_pr": "オープンPRなし",
            "latest_pr_days": "最新PRから{days}日",
            "no_bug_issues": "bugラベルIssueなし",
            "open_rate": "オープン率{percent}%",
            "no_contributor_info": "コントリビューター情報なし",
            "recent_activity_days": "最近の活動から{days}日",
        },
    },
    "en": {
        "banner": """
    _________________________
   |                         |
   |       coffinit          |
   |  Things OSS projects    |
   |  do before they die.    |
   |_________________________|

  Usage: coffinit check <owner>/<repo>
        """,
        "errors": {
            "token_missing": "GITHUB_TOKEN is not set. Put it into .env or set the environment variable.",
            "repo_not_found": "Repository not found.",
            "private_repo": "Repository is private or inaccessible.",
            "rate_limit": "API rate limit exceeded.",
            "network": "Network request failed.",
            "generic": "An unexpected error occurred.",
        },
        "labels": {
            "alive": "✅ Alive",
            "struggling": "⚠️ Struggling",
            "bucket": "🪦 On The Bucket List",
            "dead": "⚰️ Dead",
        },
        "detail": {
            "score_title": "Detail Score",
            "raw_title": "Raw Data",
            "column_item": "Item",
            "column_score": "Score",
            "column_value": "Value",
            "last_commit": "Last commit",
            "latest_pr": "Latest PR",
            "bug_issues": "bug-labelled issues",
            "recent_contributor": "Recent contributor",
        },
        "sections": {
            "maintenance": "Maintenance",
            "pull_request_response": "PR response",
            "bug_backlog": "Bug backlog",
            "author_activity": "Author activity",
        },
        "raw": {
            "last_commit_days": "Last commit {days} days ago",
            "no_last_commit": "No commits",
            "no_open_pr": "No open PRs",
            "latest_pr_days": "Latest PR {days} days ago",
            "no_bug_issues": "No bug-labelled issues",
            "open_rate": "Open rate {percent}%",
            "no_contributor_info": "No contributor information",
            "recent_activity_days": "Last activity {days} days ago",
        },
    },
}


def set_locale(locale: str) -> None:
    global _LOCALE
    if locale and locale in MESSAGES:
        _LOCALE = locale


def get_locale() -> str:
    return _LOCALE


def t(key: str) -> str:
    """Return the localized message for `key`.

    Key is a dotted path, e.g. "errors.token_missing" or "labels.alive".
    If a message is not found, the key is returned as a fallback.
    """

    parts = key.split(".")

    def _lookup(locale: str) -> Any:
        node: Any = MESSAGES.get(locale, {})
        for part in parts:
            if not isinstance(node, dict):
                return None
            node = node.get(part)
            if node is None:
                return None
        return node

    # Special behavior: keep Japanese original for error messages and
    # append English translation in parentheses when locale is 'en'.
    if _LOCALE == "en" and parts and parts[0] == "errors":
        ja_msg = _lookup("ja")
        en_msg = _lookup("en")
        if ja_msg and en_msg and str(ja_msg) != str(en_msg):
            return f"{ja_msg} ({en_msg})"
        return str(en_msg or ja_msg or key)

    node = _lookup(_LOCALE)
    if node is None:
        return key
    return str(node)
