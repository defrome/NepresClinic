from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.application.security import hash_password
from app.domain.exceptions import ConflictError, DomainError, ForbiddenError, NotFoundError
from app.infrastructure.database import Base, SessionLocal, engine
from app.modules.doctors_model import DoctorModel
from app.modules.organizations_model import OrganizationModel  # register ORM mappings
from app.modules.patients_model import PatientModel  # register patient mapping
from app.modules.treatments.infrastructure.model import MedicationDoseModel, PlanBlockModel, PlanDayModel, TreatmentPlanModel  # register treatment mappings
from app.settings import settings


class NoCacheStaticFiles(StaticFiles):
    """Development UI assets must refresh immediately after a local edit."""

    async def get_response(self, path: str, scope: dict):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, max-age=0"
        return response


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


def seed_demo_data() -> None:
    """Create a safe, repeatable local demo account and patient."""
    session = SessionLocal()
    try:
        doctor = session.query(DoctorModel).filter_by(username="doctor.clinic").first()
        if not doctor:
            organization = session.query(OrganizationModel).filter_by(name="Clinic").first()
            if not organization:
                organization = OrganizationModel(name="Clinic")
                session.add(organization)
                session.flush()
            doctor = DoctorModel(
                organization_id=organization.id,
                username="doctor.clinic",
                password_hash=hash_password("clinic-doctor"),
                full_name="Анна Смирнова",
                email="doctor@clinic.local",
            )
            session.add(doctor)
            session.flush()
        patient = session.query(PatientModel).filter_by(doctor_id=doctor.id, first_name="Алексей", last_name="Волков").first()
        demo_token = "clinic-alexey-scoliosis-2026"
        if not patient:
            patient = PatientModel(
                organization_id=doctor.organization_id,
                doctor_id=doctor.id,
                first_name="Алексей",
                last_name="Волков",
                birth_date=date(1992, 4, 18),
                sex="male",
                phone="+7 900 123-45-67",
                email="alexey.volkov@example.com",
                height_cm=178,
                weight_kg=72.5,
                emergency_contact="Мария Волкова, +7 900 123-45-68",
                data_processing_consent_at=datetime.now(timezone.utc),
                diagnosis="Сколиоз II степени грудопоясничного отдела",
                diagnosis_date=date(2026, 6, 10),
                treatment_start_date=date(2026, 7, 1),
                doctor_notes="Контроль осанки и регулярное выполнение назначенного комплекса упражнений.",
                contraindications="Избегать осевой нагрузки с весом и резких скручивающих движений.",
                comorbidities="Не указаны",
                allergies="Не указаны",
                magic_link_token=demo_token,
            )
            session.add(patient)
            session.flush()
        elif patient.magic_link_token != demo_token:
            patient.magic_link_token = demo_token
        plan = session.query(TreatmentPlanModel).filter_by(patient_id=patient.id, status="active").first()
        if not plan:
            plan = TreatmentPlanModel(organization_id=doctor.organization_id, doctor_id=doctor.id, patient_id=patient.id, title="Коррекция осанки при сколиозе II степени", duration_days=14, starts_on=date.today(), status="active")
            session.add(plan); session.flush()
        day_titles = ["Адаптация", "Мягкая мобилизация", "Контроль корпуса", "Стабилизация", "Работа с осанкой", "Дыхание и баланс", "Контрольная неделя", "Плавное усиление", "Мышцы-стабилизаторы", "Осознанная осанка", "Ритм и регулярность", "Закрепление техники", "Оценка самочувствия", "Итоги курса"]
        for day_number, day_title in enumerate(day_titles, 1):
            day = session.query(PlanDayModel).filter_by(plan_id=plan.id, day_number=day_number).first()
            if not day:
                day = PlanDayModel(plan_id=plan.id, day_number=day_number, title=day_title)
                session.add(day); session.flush()
            if not session.query(PlanBlockModel).filter_by(plan_day_id=day.id).first():
                session.add_all([
                    PlanBlockModel(plan_day_id=day.id, position=1, block_type="exercise", title="Назначенный комплекс упражнений", content="Выполните комплекс, согласованный с врачом, в комфортном темпе без усиления боли.", question="Как вы оцениваете самочувствие после комплекса?", is_required=True),
                    PlanBlockModel(plan_day_id=day.id, position=2, block_type="checklist", title="Контроль осанки в течение дня", content="Обратите внимание на положение плеч и спины в повседневных делах.", question="Удалось ли заметить и скорректировать осанку?", is_required=True),
                    PlanBlockModel(plan_day_id=day.id, position=3, block_type="question", title="Самооценка состояния", content="Кратко отметьте изменения самочувствия за день.", question="Есть ли дискомфорт, усталость или боль?", is_required=True),
                ])
        session.commit()
    finally:
        session.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_admin()
    if settings.seed_demo_data:
        seed_demo_data()
    yield


app = FastAPI(
    title="Nepres Clinic — API клиники",
    version="0.1.0",
    description="API клиники для управления врачами, пациентами и назначенным лечением.",
    lifespan=lifespan,
)
app.include_router(router)
admin_page_directory = Path(__file__).parent / "admin_page"
doctor_page_directory = Path(__file__).parent / "doctor_page"
patient_page_directory = Path(__file__).parent / "patient_page"
app.mount("/admin-assets", NoCacheStaticFiles(directory=admin_page_directory), name="admin-assets")
app.mount("/doctor-assets", NoCacheStaticFiles(directory=doctor_page_directory), name="doctor-assets")
app.mount("/patient-assets", NoCacheStaticFiles(directory=patient_page_directory), name="patient-assets")


@app.get("/get_admin_page", include_in_schema=False)
@app.get("/admin", include_in_schema=False)
def get_admin_page() -> FileResponse:
    """Serve the native HTML/CSS/JS administration interface."""
    return FileResponse(admin_page_directory / "index.html", headers={"Cache-Control": "no-store, max-age=0"})


@app.get("/get_doctor_page", include_in_schema=False)
@app.get("/doctor", include_in_schema=False)
def get_doctor_page() -> FileResponse:
    """Serve the native doctor workspace."""
    return FileResponse(doctor_page_directory / "index.html", headers={"Cache-Control": "no-store, max-age=0"})


@app.get("/p/{magic_token}", include_in_schema=False)
def get_patient_page(magic_token: str) -> FileResponse:
    """Patient workspace; the token is validated by its public API calls."""
    return FileResponse(patient_page_directory / "index.html", headers={"Cache-Control": "no-store, max-age=0"})


@app.get("/health", tags=["Система"], summary="Проверка доступности API")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    code = 404 if isinstance(exc, NotFoundError) else 403 if isinstance(exc, ForbiddenError) else 409 if isinstance(exc, ConflictError) else 400
    return JSONResponse(status_code=code, content={"detail": str(exc)})
