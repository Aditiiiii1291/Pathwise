from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.core.database import get_db
    from app.schemas.upload import UploadSummary
    from app.services.ingestion import IngestionService
except ImportError:
    from backend.app.core.database import get_db
    from backend.app.schemas.upload import UploadSummary
    from backend.app.services.ingestion import IngestionService

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

ALLOWED_DATA_TYPES = {"students", "attendance", "marks", "fees", "attempts"}

@router.post("/{data_type}", response_model=UploadSummary, status_code=status.HTTP_200_OK)
async def upload_dataset(
    data_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Ingests and validates institutional datasets (CSV/XLSX).
    Supported data types: students, attendance, marks, fees, attempts.
    """
    if data_type not in ALLOWED_DATA_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data_type '{data_type}'. Allowed types are: {', '.join(sorted(ALLOWED_DATA_TYPES))}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    service = IngestionService(db)
    summary = service.ingest(data_type, file.filename or "uploaded_file", content)
    return summary
