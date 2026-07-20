"""Compatibility facade for the former monolithic router."""
from fastapi import APIRouter

from app.api.routers.auth import router as auth_router
from app.api.routers.doctors import router as doctors_router
from app.api.routers.organizations import router as organizations_router
from app.api.routers.patients import router as patients_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(organizations_router)
router.include_router(doctors_router)
router.include_router(patients_router)
