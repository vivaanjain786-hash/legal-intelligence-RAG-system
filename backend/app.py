import re

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from .analytics import (
    get_overview,
    get_cases_by_year,
    get_parser_distribution,
    get_entity_distribution,
    get_top_judges,
    get_cases,
    get_case_detail,
    get_case_types,
    get_top_entities,
    get_cases_for_entity,
    get_case_type_distribution,
    get_reportable_distribution,
    get_metadata_completeness,
)
from .auth import (
    create_token,
    create_user,
    get_current_user,
    get_user_by_email,
    init_users_table,
    verify_password,
)

from retrieval.search import search
from retrieval.citations import add_citations
from rag.rag import generate_answer_from_results


app = FastAPI(
    title="Legal Intelligence System API",
    description="API for Indian Supreme Court judgment analytics and retrieval",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():

    init_users_table()


@app.get("/")
def root():

    return {
        "name": "Legal Intelligence System",
        "status": "running",
    }


@app.get("/api/health")
def health():

    return {"status": "ok"}


# ============================================================
# AUTH
# ============================================================

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    name: str | None = Field(default=None, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


def _auth_response(user):

    token = create_token(user["id"], user["email"])

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name"),
        },
    }


@app.post("/api/auth/signup")
def signup(body: SignupRequest):

    if get_user_by_email(body.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    if not re.search(r"[A-Za-z]", body.password) or not re.search(r"[0-9]", body.password):
        raise HTTPException(
            status_code=422,
            detail="Password must contain at least one letter and one number",
        )

    user = create_user(body.email, body.password, body.name)

    return _auth_response(user)


@app.post("/api/auth/login")
def login(body: LoginRequest):

    user = get_user_by_email(body.email)

    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    return _auth_response(user)


@app.get("/api/auth/me")
def me(current_user: dict = Depends(get_current_user)):

    user = get_user_by_email(current_user["email"])

    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "id": user["id"],
        "email": user["email"],
        "name": user.get("name"),
    }


# ============================================================
# ANALYTICS OVERVIEW
# ============================================================

@app.get("/api/stats")
def stats(current_user: dict = Depends(get_current_user)):

    return get_overview()


@app.get("/api/year-distribution")
def year_distribution(current_user: dict = Depends(get_current_user)):

    return get_cases_by_year()


@app.get("/api/parser-distribution")
def parser_distribution(current_user: dict = Depends(get_current_user)):

    return get_parser_distribution()


@app.get("/api/entity-distribution")
def entity_distribution(current_user: dict = Depends(get_current_user)):

    return get_entity_distribution()


@app.get("/api/judges")
def judges(
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    current_user: dict = Depends(get_current_user),
):

    return get_top_judges(limit)


@app.get("/api/search")
def search_cases(
    q: str = Query(
        ...,
        min_length=3
    ),
    current_user: dict = Depends(get_current_user),
):

    results = add_citations(search(q))

    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


class AskRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)


@app.post("/api/ask")
def ask(
    body: AskRequest,
    current_user: dict = Depends(get_current_user),
):

    results = add_citations(search(body.query))

    if not results:
        return {
            "query": body.query,
            "answer": "No relevant legal authorities were retrieved.",
            "sources": [],
        }

    answer = generate_answer_from_results(body.query, results)

    return {
        "query": body.query,
        "answer": answer,
        "sources": results,
    }


# ============================================================
# JUDGMENTS
# ============================================================

@app.get("/api/cases")
def cases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    year_from: int | None = None,
    year_to: int | None = None,
    case_type: str | None = None,
    q: str | None = Query(default=None, min_length=2),
    current_user: dict = Depends(get_current_user),
):

    return get_cases(
        page=page,
        page_size=page_size,
        year_from=year_from,
        year_to=year_to,
        case_type=case_type,
        q=q,
    )


@app.get("/api/cases/{case_id}")
def case_detail(case_id: int, current_user: dict = Depends(get_current_user)):

    case = get_case_detail(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return case


@app.get("/api/case-types")
def case_types(current_user: dict = Depends(get_current_user)):

    return get_case_types()


# ============================================================
# ENTITIES
# ============================================================

@app.get("/api/entities/top")
def entities_top(
    entity_type: str = Query(...),
    limit: int = Query(default=25, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):

    return get_top_entities(entity_type.upper(), limit)


@app.get("/api/entities/cases")
def entities_cases(
    entity_type: str = Query(...),
    value: str = Query(...),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):

    return get_cases_for_entity(entity_type.upper(), value, limit)


# ============================================================
# ANALYTICS
# ============================================================

@app.get("/api/case-type-distribution")
def case_type_distribution(
    limit: int = Query(default=10, ge=1, le=30),
    current_user: dict = Depends(get_current_user),
):

    return get_case_type_distribution(limit)


@app.get("/api/reportable-distribution")
def reportable_distribution(current_user: dict = Depends(get_current_user)):

    return get_reportable_distribution()


@app.get("/api/metadata-completeness")
def metadata_completeness(current_user: dict = Depends(get_current_user)):

    return get_metadata_completeness()
