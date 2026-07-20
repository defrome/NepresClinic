import pytest
from fastapi.testclient import TestClient

from app.infrastructure.database import SessionLocal
from app.infrastructure.models import DoctorModel, OrganizationModel, PatientModel
from app.main import app, seed_admin


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        session = SessionLocal()
        try:
            session.query(PatientModel).delete()
            session.query(DoctorModel).delete()
            session.query(OrganizationModel).delete()
            session.commit()
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
    created = client.post("/api/v1/patients", headers=headers, json={"full_name": "Иван Петров", "contact": "+79990000000", "notes": "Первичный прием"})
    assert created.status_code == 201
    patient_id = created.json()["id"]
    assert client.get("/api/v1/patients", headers=headers).json()[0]["full_name"] == "Иван Петров"
    updated = client.patch(f"/api/v1/patients/{patient_id}", headers=headers, json={"notes": "Контроль через неделю"})
    assert updated.status_code == 200
    assert updated.json()["notes"] == "Контроль через неделю"
    assert client.delete(f"/api/v1/patients/{patient_id}", headers=headers).status_code == 204


def test_tenant_isolation_and_admin_organizations(client):
    client.post("/api/v1/auth/register", json={"organization_name": "Клиника Альфа", "username": "alpha.doc", "password": "safe-password", "full_name": "Альфа Доктор"})
    client.post("/api/v1/auth/register", json={"organization_name": "Клиника Бета", "username": "beta.doc", "password": "safe-password", "full_name": "Бета Доктор"})
    alpha = login(client, "alpha.doc", "safe-password")
    beta = login(client, "beta.doc", "safe-password")
    patient_id = client.post("/api/v1/patients", headers=alpha, json={"full_name": "Пациент Альфы"}).json()["id"]
    assert client.get(f"/api/v1/patients/{patient_id}", headers=beta).status_code == 403
    assert client.get("/api/v1/organizations", headers=alpha).status_code == 403
    assert client.get("/api/v1/organizations", headers=login(client, "admin", "admin")).status_code == 200


def test_admin_manages_records_across_organizations(client):
    admin = login(client, "admin", "admin")
    organization = client.post("/api/v1/organizations", headers=admin, json={"name": "Управляемая клиника"}).json()
    doctor = client.post("/api/v1/doctors", headers=admin, json={
        "organization_id": organization["id"], "username": "managed.doctor", "password": "safe-password", "full_name": "Управляемый врач",
    })
    assert doctor.status_code == 201
    doctor = doctor.json()
    patient = client.post("/api/v1/patients", headers=admin, json={
        "organization_id": organization["id"], "doctor_id": doctor["id"], "full_name": "Управляемый пациент",
    })
    assert patient.status_code == 201
    assert any(item["id"] == doctor["id"] for item in client.get("/api/v1/doctors", headers=admin).json())
    assert client.patch(f"/api/v1/doctors/{doctor['id']}", headers=admin, json={"is_active": False}).status_code == 200
    assert client.delete(f"/api/v1/patients/{patient.json()['id']}", headers=admin).status_code == 204
