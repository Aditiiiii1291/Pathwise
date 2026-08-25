from fastapi import APIRouter

try:
    from app.api.endpoints.auth import router as auth_router
    from app.api.endpoints.students import router as students_router
    from app.api.endpoints.assessment import router as assessment_router
    from app.api.endpoints.dashboard import router as dashboard_router
    from app.api.endpoints.rules import router as rules_router
    from app.api.endpoints.uploads import router as uploads_router
    from app.api.endpoints.notifications import router as notifications_router
    from app.api.endpoints.interventions import router as interventions_router
except ImportError:
    from backend.app.api.endpoints.auth import router as auth_router
    from backend.app.api.endpoints.students import router as students_router
    from backend.app.api.endpoints.assessment import router as assessment_router
    from backend.app.api.endpoints.dashboard import router as dashboard_router
    from backend.app.api.endpoints.rules import router as rules_router
    from backend.app.api.endpoints.uploads import router as uploads_router
    from backend.app.api.endpoints.notifications import router as notifications_router
    from backend.app.api.endpoints.interventions import router as interventions_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(assessment_router)
api_router.include_router(dashboard_router)
api_router.include_router(rules_router)
api_router.include_router(uploads_router)
api_router.include_router(notifications_router)
api_router.include_router(interventions_router)
