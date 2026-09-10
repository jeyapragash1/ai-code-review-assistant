class GitHubError(Exception):
    """Safe error without upstream bodies or credentials."""


class GitHubRateLimitError(GitHubError):
    pass
