from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app
from app.agent_graph import langgraph_available


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.seed import seed_demo_data
    with SessionLocal() as db:
        seed_demo_data(db)


def login(client: TestClient, email: str) -> dict:
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': 'Demo@123'})
    assert response.status_code == 200, response.text
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


def test_proposal_feature_coverage_smoke():
    reset_db()
    with TestClient(app) as client:
        student = login(client, 'student@stuskilllink.demo')
        company = login(client, 'industry@stuskilllink.demo')
        academician = login(client, 'academician@stuskilllink.demo')
        institution = login(client, 'institution@stuskilllink.demo')

        # Multi-provider LLM boundary and integration metadata.
        provider = client.get('/api/v1/sih/system/provider', headers=student).json()
        assert provider['provider'] == 'Multi-provider LLM gateway'
        assert provider['mode'] == 'DETERMINISTIC_FALLBACK'
        assert {item['id'] for item in provider['providers']} == {'nvidia', 'openrouter', 'groq', 'gemini'}
        integrations = client.get('/api/v1/sih/system/integrations', headers=student).json()
        assert {x['name'] for x in integrations['learning']} >= {'NPTEL', 'SWAYAM', 'Coursera'}

        # Secure resume ingestion + skill extraction.
        resume = b'Python FastAPI Docker PostgreSQL machine learning REST APIs project internship communication'
        upload = client.post('/api/v1/sih/student/resume/upload', headers=student, files={'file': ('resume.txt', resume, 'text/plain')})
        assert upload.status_code == 200, upload.text
        assert 'Python' in upload.json()['extracted_skills']

        # Skill gap, LSRW, learning, portfolio/badge verification.
        lsrw = client.post('/api/v1/sih/student/lsrw/assess', headers=student, json={
            'listening_correct': 4, 'listening_total': 5,
            'reading_correct': 4, 'reading_total': 5,
            'speaking_text': 'I built an industry aligned machine learning service and explained the project decisions to my team clearly.',
            'writing_text': 'I am suitable for this internship because I can apply Python, APIs and machine learning to practical problems. I document decisions, collaborate with teammates, and improve missing skills through focused learning.',
        })
        assert lsrw.status_code == 200 and lsrw.json()['overall'] > 0
        gaps = client.get('/api/v1/sih/student/skill-gap', headers=student)
        assert gaps.status_code == 200 and 'priority_gaps' in gaps.json()
        learning = client.get('/api/v1/sih/student/learning', headers=student)
        assert learning.status_code == 200
        pending_skill = None
        if learning.json():
            complete = client.post(f"/api/v1/sih/student/learning/{learning.json()[0]['id']}/complete", headers=student)
            assert complete.status_code == 200
            pending_skill = complete.json()['skill']
        portfolio = client.get('/api/v1/sih/student/portfolio', headers=student).json()
        assert portfolio['badges']
        verified_badge = next(x for x in portfolio['badges'] if x['verified'])
        verify = client.get(f"/api/v1/sih/badges/{verified_badge['id']}/verify")
        assert verify.status_code == 200 and verify.json()['verified'] is True
        if pending_skill:
            pending_badge = next(x for x in portfolio['badges'] if x['title'].lower() == f"{pending_skill} readiness".lower())
            assert pending_badge['verified'] is False
            assert pending_badge['verification_status'] == 'PENDING_VERIFICATION'

        # Industry-led learning creates verifiable portfolio evidence.
        programs = client.get('/api/v1/sih/student/industry-learning', headers=student).json()
        assert programs
        completed_program = client.post(f"/api/v1/sih/student/industry-learning/{programs[-1]['id']}/complete", headers=student)
        assert completed_program.status_code == 200

        # Explainable company rank lists include proposal tiering and deterministic allocation.
        company_dashboard = client.get('/api/v1/sih/company/dashboard', headers=company).json()
        opportunity = next(x for x in company_dashboard['opportunities'] if x['title'] == 'AI Engineer Intern')
        rankings = client.get(f"/api/v1/sih/company/opportunities/{opportunity['id']}/rankings", headers=company)
        assert rankings.status_code == 200 and rankings.json()
        top = rankings.json()[0]
        assert top['match']['explanation']['tier'].startswith('TIER_') or top['match']['explanation']['tier'] == 'NOT_ELIGIBLE'
        assert top['match']['explanation']['tie_break_order']
        allocated = client.post(f"/api/v1/sih/company/opportunities/{opportunity['id']}/allocate", headers=company)
        assert allocated.status_code == 200 and allocated.json()

        # Automated offer letter + controlled engagement lifecycle + company feedback loop.
        allocations = client.get('/api/v1/sih/company/allocations', headers=company).json()
        arjun = next(x for x in allocations if x['student_name'] == 'Arjun Kumar')
        letter = client.get(f"/api/v1/sih/student/offers/{arjun['id']}/letter", headers=student)
        assert letter.status_code == 200 and 'Offer Letter' in letter.json()['letter_text']
        accepted = client.post(f"/api/v1/sih/student/offers/{arjun['id']}/respond", headers=student, json={'response': 'ACCEPTED'})
        assert accepted.status_code == 200
        started = client.patch(f"/api/v1/sih/company/allocations/{arjun['id']}/lifecycle", headers=company, json={'status': 'IN_PROGRESS'})
        assert started.status_code == 200
        completed = client.patch(f"/api/v1/sih/company/allocations/{arjun['id']}/lifecycle", headers=company, json={'status': 'COMPLETED'})
        assert completed.status_code == 200
        feedback = client.post(f"/api/v1/sih/company/allocations/{arjun['id']}/feedback", headers=company, json={
            'rating': 5,
            'strengths': ['Python', 'Communication'],
            'improvement_skills': ['Cloud deployment'],
            'comments': 'Strong performance with clear placement potential.',
            'recommend_for_placement': True,
        })
        assert feedback.status_code == 200

        # Seven-agent orchestration. The isolated review runtime may not have LangGraph installed;
        # production requirements do include it and the dedicated graph tests run when available.
        if langgraph_available():
            agents = client.post('/api/v1/sih/student/agents/run', headers=student)
            assert agents.status_code == 200 and len(agents.json()) == 7
            assert {item['status'] for item in agents.json()} == {'DEGRADED'}
            assert all(item['output_data']['llm']['mode'] == 'FALLBACK' for item in agents.json())
            assert all(item['output_data']['orchestration'] == 'langgraph' for item in agents.json())
            assert all(item['output_data']['graph_node'].startswith('agent_') for item in agents.json())

        # Academician opportunities and curriculum signals.
        acad = client.get('/api/v1/sih/academician/dashboard', headers=academician)
        assert acad.status_code == 200 and acad.json()['opportunities']
        apply = client.post(f"/api/v1/sih/academician/opportunities/{acad.json()['opportunities'][0]['id']}/apply", headers=academician)
        assert apply.status_code == 200

        # Institution analytics and refresh complete the academia-industry loop.
        inst = client.get('/api/v1/sih/institution/dashboard', headers=institution)
        assert inst.status_code == 200 and inst.json()['curriculum_insights']
        refresh = client.post('/api/v1/sih/institution/curriculum/refresh', headers=institution)
        assert refresh.status_code == 200
        readiness = client.get('/api/v1/sih/institution/students', headers=institution)
        assert readiness.status_code == 200 and len(readiness.json()) >= 4

        # Public self-registration stays limited to the four stakeholder roles; ADMIN is provisioned securely.
        blocked = client.post('/api/v1/auth/register/GOVERNMENT', json={'email': 'gov@example.com', 'password': 'Password1234'})
        assert blocked.status_code == 400


def test_role_boundaries_are_enforced():
    reset_db()
    with TestClient(app) as client:
        student = login(client, 'student@stuskilllink.demo')
        company = login(client, 'industry@stuskilllink.demo')
        assert client.get('/api/v1/sih/company/dashboard', headers=student).status_code == 403
        assert client.get('/api/v1/sih/student/dashboard', headers=company).status_code == 403
