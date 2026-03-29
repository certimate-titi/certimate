"""Resource Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel


class UploadResourceRequest(BaseModel):
    filename: Optional[str] = None
    subject_id: Optional[str] = None
    file_size_mb: Optional[float] = None
    type: Optional[str] = None


class SubmitYoutubeRequest(BaseModel):
    youtube_url: str
    subject_id: Optional[str] = None
