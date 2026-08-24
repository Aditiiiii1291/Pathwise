from typing import List, Optional
from pydantic import BaseModel, Field

class UploadError(BaseModel):
    row_number: Optional[int] = None
    field: Optional[str] = None
    code: str
    message: str

class UploadSummary(BaseModel):
    data_type: str
    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    inserted_rows: int
    errors: List[UploadError] = Field(default_factory=list)
