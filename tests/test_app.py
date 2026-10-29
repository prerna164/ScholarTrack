import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app, Base, Project, Activity, ProgressUpdate, get_db

@pytest.fixture
def client():
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory=sessionmaker(engine,expire_on_commit=False)
    def override():
        with factory() as db: yield db
    app.dependency_overrides[get_db]=override
    with TestClient(app) as c:
        yield c,factory
    app.dependency_overrides.clear()
    engine.dispose()

def create(c, **overrides):
    data=dict(title='Water quality sensors',summary='Monitor river water quality using sensors and pollution measurements.',owner='Research Team',keywords='water, sensors',status='ongoing',actor='Prerna')
    data.update(overrides)
    return c.post('/projects/new',data=data)

def test_creation_and_validation(client):
    c,f=client
    assert create(c,title='x').status_code==422
    assert create(c).status_code==200
    with f() as db:
        p=db.scalar(select(Project))
        assert p.title=='Water quality sensors'
        assert db.scalar(select(Activity)).actor=='Prerna'
    assert c.get('/projects/999').status_code==404

def test_edit_and_activity_history(client):
    c,f=client; create(c)
    response=c.post('/projects/1/edit',data=dict(title='Updated river study',summary='Monitor river water quality using sensors and pollution measurements.',owner='Research Team',keywords='water, sensors',status='completed',actor='Reviewer'))
    assert response.status_code==200
    with f() as db:
        assert db.get(Project,1).status=='completed'
        logs=db.scalars(select(Activity).order_by(Activity.id)).all()
        assert len(logs)==2 and logs[-1].actor=='Reviewer'
        assert 'before' in logs[-1].changes and 'Updated river study' in logs[-1].changes

def test_relevant_search(client):
    c,_=client; create(c)
    create(c,title='Library catalogue',summary='Recommend fiction books to library readers based on borrowing history.',keywords='books, reading')
    page=c.get('/projects',params={'q':'water quality'}).text
    assert 'Water quality sensors' in page and 'Library catalogue' not in page
    assert 'No matching projects' in c.get('/projects?q=zzzznonexistent').text

def test_empty_search(client):
    c,_=client; create(c)
    assert 'Water quality sensors' in c.get('/projects?q=+').text
    assert 'Water quality sensors' in c.get('/projects').text

def test_duplicate_ranking(client):
    c,_=client; create(c)
    create(c,title='Water consumption',summary='Study household water consumption and compare annual usage records.',keywords='water')
    create(c,title='Library catalogue',summary='Recommend fiction books based on historical borrowing records.',keywords='books')
    page=c.post('/proposal',data={'title':'Water quality sensors','summary':'Monitor river water quality using sensors and pollution measurements.'}).text
    assert page.index('/projects/1')<page.index('/projects/2')
    assert '/projects/3' not in page and 'Human review required' in page
    assert c.post('/proposal',data={'title':'x','summary':''}).status_code==422

def test_progress_timestamps(client):
    c,f=client; create(c)
    with f() as db: before=db.get(Project,1).updated_at
    assert c.post('/projects/1/progress',data={'note':'Sensor testing complete','percentage':'55','actor':'Prerna'}).status_code==200
    with f() as db:
        p=db.get(Project,1)
        assert p.updated_at>before and p.completion==55
        assert db.scalar(select(ProgressUpdate)).note=='Sensor testing complete'
        assert '55' in db.scalars(select(Activity).order_by(Activity.id.desc())).first().changes
    assert c.post('/projects/1/progress',data={'note':'Invalid','percentage':'101','actor':'Prerna'}).status_code==422
