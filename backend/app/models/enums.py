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


class ReviewStatus(StrEnum):
    QUEUED = "queued"
    FETCHING = "fetching"
    STATIC_ANALYSIS = "static_analysis"
    AI_ANALYSIS = "ai_analysis"
    VALIDATING = "validating"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewRisk(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReviewTriggerType(StrEnum):
    MANUAL = "manual"
    WEBHOOK = "webhook"
    SYNCHRONIZATION = "synchronization"


class FindingDiffSide(StrEnum):
    LEFT = "left"
    RIGHT = "right"


class FindingSeverity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FindingCategory(StrEnum):
    SECURITY = "security"
    BUG = "bug"
    VALIDATION = "validation"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE = "performance"
    DATABASE = "database"
    MAINTAINABILITY = "maintainability"
    CODE_QUALITY = "code_quality"
    BEST_PRACTICE = "best_practice"


class FindingSource(StrEnum):
    STATIC = "static"
    AI = "ai"
    HYBRID = "hybrid"


class FindingStatus(StrEnum):
    OPEN = "open"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"
