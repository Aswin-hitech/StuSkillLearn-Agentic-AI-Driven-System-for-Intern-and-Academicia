from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import Base, SessionLocal, engine
from app.main import app
from app.models import Allocation, Opportunity, StudentProfile, User


def login(client: TestClient, email: str) -> dict:
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': 'Demo@123'})
    assert response.status_code == 200, response.text
    return response.json()


def headers(auth: dict) -> dict:
    return {'Authorization': f"Bearer {auth['access_token']}"}


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.seed import seed_demo_data
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()


def test_full_four_portal_flow_and_reallocation():
    reset_db()
    with TestClient(app) as client:
        assert client.get('/health').json()['status'] == 'ok'

        student_auth = login(client, 'student@stuskilllink.demo')
        student_headers = headers(student_auth)
        provider = client.get('/api/v1/sih/system/provider', headers=student_headers).json()
        assert provider['provider'] == 'Multi-provider LLM gateway'
        assert {item['id'] for item in provider['providers']} == {'nvidia', 'openrouter', 'groq', 'gemini'}
        student_dash = client.get('/api/v1/sih/student/dashboard', headers=student_headers)
        assert student_dash.status_code == 200
        assert student_dash.json()['profile']['name'] == 'Arjun Kumar'
        assert student_dash.json()['top_matches']

        skill_gap = client.get('/api/v1/sih/student/skill-gap', headers=student_headers).json()
        assert 'priority_gaps' in skill_gap

        lsrw = client.post('/api/v1/sih/student/lsrw/assess', headers=student_headers, json={
            'listening_correct': 4, 'listening_total': 5,
            'reading_correct': 5, 'reading_total': 5,
            'speaking_text': 'I built a machine learning project that maps student skills to role requirements and explains the gaps clearly.',
            'writing_text': 'I am suitable for this internship because I have applied Python and machine learning in projects. I can build APIs, work with data, communicate progress, and learn missing tools quickly. My recent project focused on skill mapping and explainable recommendations for students.',
        })
        assert lsrw.status_code == 200
        assert lsrw.json()['overall'] > 0

        company_auth = login(client, 'industry@stuskilllink.demo')
        company_headers = headers(company_auth)
        company_dash = client.get('/api/v1/sih/company/dashboard', headers=company_headers)
        assert company_dash.status_code == 200
        ai_opp = next(x for x in company_dash.json()['opportunities'] if x['title'] == 'AI Engineer Intern')
        rankings = client.get(f"/api/v1/sih/company/opportunities/{ai_opp['id']}/rankings", headers=company_headers)
        assert rankings.status_code == 200
        assert len(rankings.json()) >= 3

        allocations = client.get('/api/v1/sih/company/allocations', headers=company_headers).json()
        student_offer = next((x for x in allocations if x['student_name'] == 'Arjun Kumar' and x['status'] == 'OFFERED'), None)
        assert student_offer is not None
        rejected = client.post(f"/api/v1/sih/student/offers/{student_offer['id']}/respond", headers=student_headers, json={'response': 'REJECTED'})
        assert rejected.status_code == 200
        allocations_after = client.get('/api/v1/sih/company/allocations', headers=company_headers).json()
        assert any(x['round'] >= 2 and x['status'] == 'OFFERED' for x in allocations_after)

        academician_auth = login(client, 'academician@stuskilllink.demo')
        academician_dash = client.get('/api/v1/sih/academician/dashboard', headers=headers(academician_auth))
        assert academician_dash.status_code == 200
        assert academician_dash.json()['opportunities']

        institution_auth = login(client, 'institution@stuskilllink.demo')
        institution_dash = client.get('/api/v1/sih/institution/dashboard', headers=headers(institution_auth))
        assert institution_dash.status_code == 200
        assert institution_dash.json()['curriculum_insights']
        students = client.get('/api/v1/sih/institution/students', headers=headers(institution_auth))
        assert students.status_code == 200 and len(students.json()) >= 4
        faculty_ops = client.get('/api/v1/sih/institution/academician-opportunities', headers=headers(institution_auth))
        assert faculty_ops.status_code == 200 and faculty_ops.json()


def test_only_four_product_roles_can_register():
    reset_db()
    with TestClient(app) as client:
        response = client.post('/api/v1/auth/register/ADMIN', json={'email': 'gov@example.com', 'password': 'Password1234'})
        assert response.status_code == 400
        for role in ['STUDENT', 'COMPANY', 'ACADEMICIAN', 'INSTITUTION']:
            response = client.post(f'/api/v1/auth/register/{role}', json={'email': f'{role.lower()}2@example.com', 'password': 'Password1234'})
            assert response.status_code == 201
