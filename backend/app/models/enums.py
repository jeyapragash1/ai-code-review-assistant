from enum import StrEnum


class PullRequestStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class WebhookEventStatus(StrEnum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    IGNORED = "ignored"
