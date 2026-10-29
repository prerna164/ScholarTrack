from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, String, Text, Integer, ForeignKey, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE = Path(__file__).resolve().parent

def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')

class Base(DeclarativeBase): pass

class Project(Base):
    __tablename__ = 'projects'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    summary: Mapped[str] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(100))
    keywords: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default='ongoing')
    completion: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(default=now)
    updated_at: Mapped[str] = mapped_column(default=now)

class ProgressUpdate(Base):
    __tablename__ = 'progress_updates'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
    note: Mapped[str] = mapped_column(Text)
    percentage: Mapped[int] = mapped_column(Integer)
    actor: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[str] = mapped_column(default=now)

class Activity(Base):
    __tablename__ = 'activity_log'
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id'))
    actor: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(50))
    changes: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(default=now)

engine = create_engine(os.getenv('DATABASE_URL', 'sqlite:///./research.db'), connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(engine, expire_on_commit=False)

def get_db():
    with SessionLocal() as db:
        yield db

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    yield

app = FastAPI(title='ScholarTrack', lifespan=lifespan)
app.mount('/static', StaticFiles(directory=BASE / 'static'), name='static')
templates = Jinja2Templates(directory=BASE / 'templates')

def render(request, page, **context):
    return templates.TemplateResponse(request=request, name=page, context=context)

def project_or_404(db, pid):
    project = db.get(Project, pid)
    if not project: raise HTTPException(404, 'Project not found')
    return project

def log(db, project, actor, action, changes):
    db.add(Activity(project_id=project.id, actor=actor, action=action, changes=json.dumps(changes, ensure_ascii=False)))

def validate(data):
    errors = []
    for field, low, high in [('title',3,160), ('summary',20,10000), ('owner',2,100), ('keywords',0,300), ('actor',2,100)]:
        if not low <= len(data[field]) <= high: errors.append(f'{field.capitalize()} must contain {low}–{high} characters.')
    if data['status'] not in ('planned','ongoing','completed'): errors.append('Choose a valid status.')
    return errors

def ranked(projects, query, limit=None):
    if not query.strip() or not projects: return []
    documents = [f'{p.title} {p.summary} {p.keywords}' for p in projects]
    try:
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,2), sublinear_tf=True)
        matrix = vectorizer.fit_transform(documents)
        scores = cosine_similarity(vectorizer.transform([query]), matrix).ravel()
    except ValueError:
        return []
    results = sorted([(p, float(s)) for p,s in zip(projects,scores) if s > 0], key=lambda item: (-item[1], item[0].id))
    return results[:limit] if limit else results

@app.get('/')
def dashboard(request: Request, db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Project.status,func.count()).group_by(Project.status)).all())
    return render(request,'dashboard.html',counts=counts,total=sum(counts.values()),recent=db.scalars(select(Project).order_by(Project.updated_at.desc()).limit(5)).all())

@app.get('/projects')
def projects(request: Request, q: str = '', db: Session = Depends(get_db)):
    rows = db.scalars(select(Project).order_by(Project.updated_at.desc())).all()
    results = ranked(rows,q) if q.strip() else [(p,None) for p in rows]
    return render(request,'projects.html',results=results,q=q)

@app.get('/projects/new')
def new(request: Request):
    return render(request,'form.html',data={},errors=[],editing=False)

@app.post('/projects/new')
@app.post('/projects/{pid}/edit')
def save(request: Request, pid: int | None = None, title: str = Form(''), summary: str = Form(''), owner: str = Form(''), keywords: str = Form(''), status: str = Form('ongoing'), actor: str = Form(''), db: Session = Depends(get_db)):
    data = {k:v.strip() for k,v in dict(title=title,summary=summary,owner=owner,keywords=keywords,status=status,actor=actor).items()}
    project = project_or_404(db,pid) if pid else None
    errors = validate(data)
    if errors:
        response = render(request,'form.html',data=data,errors=errors,editing=bool(pid))
        response.status_code=422
        return response
    fields = ('title','summary','owner','keywords','status')
    if project:
        changes = {k:{'before':getattr(project,k),'after':data[k]} for k in fields if getattr(project,k)!=data[k]}
        for k in fields: setattr(project,k,data[k])
        if changes:
            project.updated_at=now()
            log(db,project,data['actor'],'edited',changes)
    else:
        project = Project(**{k:data[k] for k in fields})
        db.add(project); db.flush()
        log(db,project,data['actor'],'created',{k:data[k] for k in fields})
    db.commit()
    return RedirectResponse(f'/projects/{project.id}',status_code=303)

@app.get('/projects/{pid}/edit')
def edit(request: Request, pid: int, db: Session = Depends(get_db)):
    p=project_or_404(db,pid)
    return render(request,'form.html',data={k:getattr(p,k) for k in ('title','summary','owner','keywords','status')},errors=[],editing=True)

@app.get('/projects/{pid}')
def detail(request: Request, pid: int, db: Session = Depends(get_db)):
    return render(request,'detail.html',p=project_or_404(db,pid),updates=db.scalars(select(ProgressUpdate).where(ProgressUpdate.project_id==pid).order_by(ProgressUpdate.id.desc())).all(),activities=db.scalars(select(Activity).where(Activity.project_id==pid).order_by(Activity.id.desc())).all(),error=None)

@app.post('/projects/{pid}/progress')
def progress(request: Request, pid: int, note: str = Form(''), percentage: str = Form(''), actor: str = Form(''), db: Session = Depends(get_db)):
    p=project_or_404(db,pid)
    try: value=int(percentage)
    except ValueError: value=-1
    if not 0<=value<=100 or not 3<=len(note.strip())<=5000 or not 2<=len(actor.strip())<=100:
        raise HTTPException(422,'Enter a note (3–5000 characters), completion from 0 to 100, and actor (2–100 characters). Go back to correct the form.')
    before=p.completion
    db.add(ProgressUpdate(project_id=pid,note=note.strip(),percentage=value,actor=actor.strip()))
    p.completion=value; p.updated_at=now()
    log(db,p,actor.strip(),'progress updated',{'completion':{'before':before,'after':value},'note':note.strip()})
    db.commit()
    return RedirectResponse(f'/projects/{pid}',status_code=303)

@app.get('/proposal')
def proposal_form(request: Request):
    return render(request,'proposal.html',results=None,data={},error=None)

@app.post('/proposal')
def proposal(request: Request, title: str = Form(''), summary: str = Form(''), db: Session = Depends(get_db)):
    data={'title':title.strip(),'summary':summary.strip()}
    error=None
    if not 3<=len(data['title'])<=160 or not 20<=len(data['summary'])<=10000:
        error='Enter a title (3–160 characters) and summary (20–10000 characters).'
    rows=db.scalars(select(Project).order_by(Project.id)).all()
    response=render(request,'proposal.html',results=None if error else ranked(rows,title+' '+summary,5),data=data,error=error)
    if error: response.status_code=422
    return response
