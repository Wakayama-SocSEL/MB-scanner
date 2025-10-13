"""GitHub API クライアントパッケージ

このパッケージは、PyGithubをラップしたGitHub APIクライアント機能を提供します。
"""

from mb_scanner.lib.github.client import GitHubClient
from mb_scanner.lib.github.schema import GitHubRepository
from mb_scanner.lib.github.search import SearchCriteria, build_default_search_criteria

__all__ = [
    "GitHubClient",
    "GitHubRepository",
    "SearchCriteria",
    "build_default_search_criteria",
]
