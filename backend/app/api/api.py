from fastapi import APIRouter

try:
    from app.api.endpoints.students import router as students_router
    from app.api.endpoints.assessment import router as assessment_router
    from app.api.endpoints.dashboard import router as dashboard_router
    from app.api.endpoints.rules import router as rules_router
    from app.api.endpoints.uploads import router as uploads_router
except ImportError:
    from backend.app.api.endpoints.students import router as students_router
    from backend.app.api.endpoints.assessment import router as assessment_router
    from backend.app.api.endpoints.dashboard import router as dashboard_router
    from backend.app.api.endpoints.rules import router as rules_router
    from backend.app.api.endpoints.uploads import router as uploads_router

api_router = APIRouter(prefix="/api")

api_router.include_router(students_router)
api_router.include_router(assessment_router)
api_router.include_router(dashboard_router)
api_router.include_router(rules_router)
api_router.include_router(uploads_router)
