"""coffinit package."""

from .github import (
	GitHubAPIError,
	GitHubClient,
	GitHubNetworkError,
	GitHubNotConfiguredError,
	GitHubPrivateRepositoryError,
	GitHubRateLimitError,
	GitHubRepositoryNotFoundError,
	RepositoryMetadata,
	RepositorySnapshot,
)
from .scorer import (
	ScoreBreakdown,
	ScoreSection,
	RepositoryAssessment,
	assess_repository,
)

__all__ = [
	"GitHubAPIError",
	"GitHubClient",
	"GitHubNetworkError",
	"GitHubNotConfiguredError",
	"GitHubPrivateRepositoryError",
	"GitHubRateLimitError",
	"GitHubRepositoryNotFoundError",
	"RepositoryMetadata",
	"RepositorySnapshot",
	"ScoreBreakdown",
	"ScoreSection",
	"RepositoryAssessment",
	"assess_repository",
]
