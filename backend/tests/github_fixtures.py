from copy import deepcopy


def repository_payload() -> dict:
    return {"id": 101, "owner": {"login": "octocat"}, "name": "example", "full_name": "octocat/example",
            "default_branch": "main", "html_url": "https://github.com/octocat/example",
            "description": "Example repository", "language": "Python", "private": False,
            "updated_at": "2026-09-01T12:00:00Z"}


def pr_payload(number: int = 1, **changes: object) -> dict:
    data = {"number": number, "title": "Improve pagination", "user": {"login": "octocat"},
            "base": {"ref": "main"}, "head": {"ref": "feature", "sha": "a" * 40},
            "html_url": f"https://github.com/octocat/example/pull/{number}", "state": "open",
            "merged_at": None, "draft": False, "additions": 10, "deletions": 2, "changed_files": 3,
            "created_at": "2026-09-01T10:00:00Z", "updated_at": "2026-09-01T12:00:00Z"}
    return deepcopy(data | changes)
