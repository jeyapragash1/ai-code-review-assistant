from typing import Literal

from pydantic import BaseModel, ConfigDict


class WebhookPingResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["pong"]
    delivery_id: str
    event: Literal["ping"]


class WebhookAcceptedResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["accepted"]
    delivery_id: str
    event: Literal["pull_request"]
    action: str


class WebhookIgnoredResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["ignored"]
    delivery_id: str
    event: str
    action: str | None = None


class WebhookDuplicateResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["duplicate"]
    delivery_id: str
    event: str
