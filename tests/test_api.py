import pytest
from fastapi.testclient import TestClient

from app.infrastructure.database import Base, SessionLocal, engine
from app.infrastructure.models import DoctorModel, OrganizationModel, PatientModel
from app.main import app, seed_admin


def patient_payload(**overrides):
    payload = {
        "first_name": "Иван", "last_name": "Петров", "birth_date": "1990-01-15", "sex": "male",
        "phone": "+79990000000", "emergency_contact": "Мария Петрова, +79990000001",
        "consent_to_data_processing": True, "diagnosis": "Восстановление после травмы",
        "treatment_start_date": "2026-07-21", "doctor_notes": "Начать с щадящей нагрузки.",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        session = SessionLocal()
        try:
            seed_admin()
        finally:
            session.close()
        yield test_client


def login(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_health_and_seeded_admin(client):
    assert client.get("/health").json() == {"status": "ok"}
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200


def test_register_auth_and_patient_crud(client):
    registration = client.post("/api/v1/auth/register", json={
        "organization_name": "Клиника Тест", "username": "doctor.test", "password": "safe-password", "full_name": "Тестовый врач", "email": "doctor@example.com",
    })
    assert registration.status_code == 201
    headers = login(client, "doctor.test", "safe-password")
    created = client.post("/api/v1/patients", headers=headers, json=patient_payload())
    assert created.status_code == 201
    patient_id = created.json()["id"]
    assert created.json()["doctor_id"] == registration.json()["id"]
    assert created.json()["data_processing_consent_at"]
    assert client.get("/api/v1/patients", headers=headers).json()[0]["full_name"] == "Иван Петров"
    updated = client.patch(f"/api/v1/patients/{patient_id}", headers=headers, json={"doctor_notes": "Контроль через неделю"})
    assert updated.status_code == 200
    assert updated.json()["doctor_notes"] == "Контроль через неделю"
    assert client.delete(f"/api/v1/patients/{patient_id}", headers=headers).status_code == 204


def test_tenant_isolation_and_admin_organizations(client):
    client.post("/api/v1/auth/register", json={"organization_name": "Клиника Альфа", "username": "alpha.doc", "password": "safe-password", "full_name": "Альфа Доктор"})
    client.post("/api/v1/auth/register", json={"organization_name": "Клиника Бета", "username": "beta.doc", "password": "safe-password", "full_name": "Бета Доктор"})
    alpha = login(client, "alpha.doc", "safe-password")
    beta = login(client, "beta.doc", "safe-password")
    patient_id = client.post("/api/v1/patients", headers=alpha, json=patient_payload()).json()["id"]
    assert client.get(f"/api/v1/patients/{patient_id}", headers=beta).status_code == 403
    assert client.get("/api/v1/organizations", headers=alpha).status_code == 403
    assert client.get("/api/v1/organizations", headers=login(client, "admin", "admin")).status_code == 200


def test_admin_manages_organizations_and_doctors_but_not_patient_creation(client):
    admin = login(client, "admin", "admin")
    organization = client.post("/api/v1/organizations", headers=admin, json={"name": "Управляемая клиника"}).json()
    doctor = client.post("/api/v1/doctors", headers=admin, json={
        "organization_id": organization["id"], "username": "managed.doctor", "password": "safe-password", "full_name": "Управляемый врач",
    })
    assert doctor.status_code == 201
    doctor = doctor.json()
    assert any(item["id"] == doctor["id"] for item in client.get("/api/v1/doctors", headers=admin).json())
    assert client.patch(f"/api/v1/doctors/{doctor['id']}", headers=admin, json={"is_active": False}).status_code == 200
    assert client.post("/api/v1/patients", headers=admin, json=patient_payload()).status_code == 403


def test_patient_requires_contact_and_consent(client):
    client.post("/api/v1/auth/register", json={"organization_name": "Клиника В", "username": "doctor.v", "password": "safe-password", "full_name": "Врач В"})
    headers = login(client, "doctor.v", "safe-password")
    assert client.post("/api/v1/patients", headers=headers, json=patient_payload(phone=None, email=None)).status_code == 422
    assert client.post("/api/v1/patients", headers=headers, json=patient_payload(consent_to_data_processing=False)).status_code == 409


def test_template_assignment_and_patient_magic_link(client):
    client.post("/api/v1/auth/register", json={"organization_name": "Реабилитация", "username": "rehab.doctor", "password": "safe-password", "full_name": "Врач реабилитации"})
    headers = login(client, "rehab.doctor", "safe-password")
    patient = client.post("/api/v1/patients", headers=headers, json=patient_payload()).json()
    template = client.post("/api/v1/treatment-templates", headers=headers, json={
        "title": "Восстановление осанки", "default_duration_days": 2,
        "days": [{"day_number": 1, "blocks": [{"block_type": "exercise", "title": "Комплекс упражнений", "question": "Как вы себя чувствуете?"}]}],
    })
    assert template.status_code == 201
    plan = client.post("/api/v1/treatment-plans", headers=headers, json={
        "patient_id": patient["id"], "template_id": template.json()["id"], "starts_on": "2026-07-21",
    })
    assert plan.status_code == 201
    assert len(plan.json()["days"]) == 2
    today = client.get(f"/api/v1/patient-access/{patient['magic_link_token']}/today")
    assert today.status_code == 200
    block_id = today.json()["blocks"][0]["id"]
    assert client.post(f"/api/v1/patient-access/{patient['magic_link_token']}/block/{block_id}/complete", json={"answer": "Хорошо"}).status_code == 204
