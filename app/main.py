from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.application.security import hash_password
from app.domain.exceptions import ConflictError, DomainError, ForbiddenError, NotFoundError
from app.infrastructure.database import Base, SessionLocal, engine
from app.infrastructure.models import DoctorModel, OrganizationModel  # register ORM mappings


def seed_admin() -> None:
    """Create the fixed bootstrap account exactly once."""
    session = SessionLocal()
    try:
        if session.query(DoctorModel).filter_by(username="admin").first():
            return
        organization = OrganizationModel(name="Администрация платформы")
        session.add(organization)
        session.flush()
        session.add(DoctorModel(
            organization_id=organization.id,
            username="admin",
            password_hash=hash_password("admin"),
            full_name="Системный администратор",
            is_admin=True,
        ))
        session.commit()
    finally:
        session.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_admin()
    yield


app = FastAPI(
    title="Nepres Clinic API",
    version="0.1.0",
    description="API для сопровождения назначенного врачом маршрута лечения.",
    lifespan=lifespan,
)
app.include_router(router)
admin_page_directory = Path(__file__).parent / "admin_page"
doctor_page_directory = Path(__file__).parent / "doctor_page"
app.mount("/admin-assets", StaticFiles(directory=admin_page_directory), name="admin-assets")
app.mount("/doctor-assets", StaticFiles(directory=doctor_page_directory), name="doctor-assets")


@app.get("/get_admin_page", include_in_schema=False)
@app.get("/admin", include_in_schema=False)
def get_admin_page() -> FileResponse:
    """Serve the native HTML/CSS/JS administration interface."""
    return FileResponse(admin_page_directory / "index.html")


@app.get("/get_doctor_page", include_in_schema=False)
@app.get("/doctor", include_in_schema=False)
def get_doctor_page() -> FileResponse:
    """Serve the native doctor workspace."""
    return FileResponse(doctor_page_directory / "index.html")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    code = 404 if isinstance(exc, NotFoundError) else 403 if isinstance(exc, ForbiddenError) else 409 if isinstance(exc, ConflictError) else 400
    return JSONResponse(status_code=code, content={"detail": str(exc)})
