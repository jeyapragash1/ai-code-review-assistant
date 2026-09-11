from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    FindingCategory,
    FindingDiffSide,
    FindingSeverity,
    FindingSource,
    FindingStatus,
    ReviewRisk,
    ReviewStatus,
    ReviewTriggerType,
)
from app.schemas.pull_request import PullRequestDetail


class ReviewCreate(BaseModel):
    pull_request_id: UUID
    commit_sha: str = Field(min_length=7, max_length=40)
    attempt_number: int = Field(default=1, ge=1)
    status: ReviewStatus = ReviewStatus.QUEUED
    overall_risk: ReviewRisk | None = None
    trigger_type: ReviewTriggerType
    model_name: str | None = Field(default=None, max_length=100)
    model_version: str | None = Field(default=None, max_length=100)
    prompt_version: str | None = Field(default=None, max_length=100)
    duration_ms: int | None = Field(default=None, ge=0)
    static_analysis_duration_ms: int | None = Field(default=None, ge=0)
    ai_analysis_duration_ms: int | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: Decimal | None = Field(default=None, ge=0)
    error_code: str | None = Field(default=None, max_length=100)
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ReviewStatusUpdate(BaseModel):
    status: ReviewStatus
    overall_risk: ReviewRisk | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    static_analysis_duration_ms: int | None = Field(default=None, ge=0)
    ai_analysis_duration_ms: int | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: Decimal | None = Field(default=None, ge=0)
    error_code: str | None = Field(default=None, max_length=100)
    error_message: str | None = None
    completed_at: datetime | None = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    pull_request_id: UUID
    commit_sha: str
    attempt_number: int
    status: ReviewStatus
    overall_risk: ReviewRisk | None
    trigger_type: ReviewTriggerType
    model_name: str | None
    model_version: str | None
    prompt_version: str | None
    duration_ms: int | None
    static_analysis_duration_ms: int | None
    ai_analysis_duration_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    estimated_cost_usd: Decimal | None
    error_code: str | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    findings_count: int = 0
    high_severity_findings_count: int = 0
    created_at: datetime
    updated_at: datetime


class ReviewDetail(ReviewResponse):
    pull_request: PullRequestDetail


class ReviewFindingCreate(BaseModel):
    review_id: UUID
    file_path: str = Field(min_length=1, max_length=1024)
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    diff_side: FindingDiffSide | None = None
    severity: FindingSeverity
    category: FindingCategory
    title: str = Field(min_length=1, max_length=255)
    problem: str = Field(min_length=1)
    explanation: str | None = None
    suggestion: str | None = None
    confidence: Decimal = Field(ge=0, le=1)
    source: FindingSource
    fingerprint: str = Field(min_length=64, max_length=64)
    code_snippet: str | None = None
    status: FindingStatus = FindingStatus.OPEN
    github_comment_id: int | None = Field(default=None, ge=1)
    published_to_github: bool = False

    @model_validator(mode="after")
    def validate_line_range(self) -> "ReviewFindingCreate":
        if self.start_line is not None and self.end_line is not None and self.end_line < self.start_line:
            raise ValueError("end_line cannot be less than start_line")
        return self


class ReviewFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    review_id: UUID
    file_path: str
    start_line: int | None
    end_line: int | None
    diff_side: FindingDiffSide | None
    severity: FindingSeverity
    category: FindingCategory
    title: str
    problem: str
    explanation: str | None
    suggestion: str | None
    confidence: Decimal
    source: FindingSource
    fingerprint: str
    code_snippet: str | None
    status: FindingStatus
    github_comment_id: int | None
    published_to_github: bool
    created_at: datetime
    updated_at: datetime
