from pydantic import BaseModel


class UploadResponse(BaseModel):
    tool_type: str
    parsed_count: int
    new_count: int
    duplicate_count: int
    message: str


class AutoUploadResponse(UploadResponse):
    breakdown: dict = {}
