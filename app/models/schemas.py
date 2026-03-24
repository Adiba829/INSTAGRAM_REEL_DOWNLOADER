"""
Pydantic models for request validation and response serialization.
"""
from pydantic import BaseModel, field_validator
import re


INSTAGRAM_REEL_PATTERN = re.compile(
    r"(https?://)?(www\.)?instagram\.com/(reel|reels|p)/[\w-]+/?",
    re.IGNORECASE,
)


class DownloadRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_instagram_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("URL must not be empty.")
        if not INSTAGRAM_REEL_PATTERN.search(v):
            raise ValueError(
                f"'{v}' does not appear to be a valid Instagram Reel URL."
            )
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://www.instagram.com/reel/C_example123/"
            }
        }
    }


class ErrorResponse(BaseModel):
    error: str
    message: str
    hint: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    service: str
