from typing import Any

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from controller import analyze_uploaded_voice
from gemini_recommendation import worder_from_environment
from input_validator_v2 import validate_content as analyze_voice_sample
from recommendation_service import (
    Actor,
    AuthorizationError,
    InvalidContextError,
    RecommendationService,
    RecommendationServiceError,
    RecordNotFoundError,
    RepositoryConfigurationError,
    SupabaseRestRepository,
)

app = FastAPI(title="VocaSense API")

# Define the origins (URLs) allowed to access your API
origins = [
    "http://localhost:5173",  # Web link from Vite
    "http://127.0.0.1:5173",  # Vite via loopback IP
    "http://127.0.0.1:5500",  # Common for VS Code Live Server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


class AssessmentRequest(BaseModel):
    answers: dict[str, Any]
    questionnaire_version: str = Field(default="1.0", min_length=1, max_length=50)


_recommendation_service: RecommendationService | None = None


def get_recommendation_service() -> RecommendationService:
    global _recommendation_service
    if _recommendation_service is None:
        repository = SupabaseRestRepository.from_environment()
        _recommendation_service = RecommendationService(
            repository,
            ai_worder=worder_from_environment(),
        )
    return _recommendation_service


def resolve_actor(
    service: RecommendationService,
    authorization: str | None,
    guest_token: str | None,
) -> Actor:
    if authorization and guest_token:
        raise AuthorizationError("Send either member authorization or a guest token, not both.")
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.casefold() != "bearer" or not token:
            raise AuthorizationError("Authorization must use a Bearer token.")
        return service.actor_from_access_token(token)
    if guest_token:
        return service.actor_from_guest_token(guest_token)
    raise AuthorizationError("Member authorization or X-Guest-Token is required.")


def raise_api_error(error: Exception) -> None:
    if isinstance(error, RecordNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, AuthorizationError):
        raise HTTPException(status_code=403, detail=str(error)) from error
    if isinstance(error, InvalidContextError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, RepositoryConfigurationError):
        raise HTTPException(status_code=503, detail=str(error)) from error
    if isinstance(error, RecommendationServiceError):
        raise HTTPException(status_code=502, detail=str(error)) from error
    raise error


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/guest-sessions")
def create_guest_session():
    try:
        session = get_recommendation_service().create_guest_session()
        return {
            "guest_token": session["guest_token"],
            "expires_at": session["expires_at"],
        }
    except Exception as error:
        raise_api_error(error)


@app.get("/api/analyses/{analysis_id}/recording-assessment")
def get_recording_assessment(
    analysis_id: int,
    authorization: str | None = Header(default=None),
    x_guest_token: str | None = Header(default=None, alias="X-Guest-Token"),
):
    try:
        service = get_recommendation_service()
        actor = resolve_actor(service, authorization, x_guest_token)
        assessment = service.get_recording_assessment(analysis_id, actor)
        if assessment is None:
            return None
        return {
            "analysis_id": analysis_id,
            "answers": assessment.get("answers", {}),
            "questionnaire_version": assessment.get("questionnaire_version"),
            "completed_at": assessment.get("completed_at"),
            "updated_at": assessment.get("updated_at"),
        }
    except Exception as error:
        raise_api_error(error)


@app.put("/api/analyses/{analysis_id}/recording-assessment")
def put_recording_assessment(
    analysis_id: int,
    request: AssessmentRequest,
    authorization: str | None = Header(default=None),
    x_guest_token: str | None = Header(default=None, alias="X-Guest-Token"),
):
    try:
        service = get_recommendation_service()
        actor = resolve_actor(service, authorization, x_guest_token)
        return service.save_recording_assessment(
            analysis_id, actor, request.answers, request.questionnaire_version
        )
    except Exception as error:
        raise_api_error(error)


@app.post("/api/analyses/{analysis_id}/recommendations/generate")
def generate_recommendation(
    analysis_id: int,
    authorization: str | None = Header(default=None),
    x_guest_token: str | None = Header(default=None, alias="X-Guest-Token"),
):
    """Return the saved row when present; otherwise generate it once."""
    try:
        service = get_recommendation_service()
        actor = resolve_actor(service, authorization, x_guest_token)
        return service.generate(analysis_id, actor)
    except Exception as error:
        raise_api_error(error)


@app.post("/api/voice/validate")
async def validate_voice_sample(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="No audio file was uploaded.")

    content_type = (file.content_type or "").lower()
    filename = (file.filename or "").lower()
    if "wav" not in content_type and not filename.endswith(".wav"):
        raise HTTPException(
            status_code=415,
            detail="Please upload WAV audio. The frontend converts recordings to WAV before calling this API.",
        )

    try:
        return analyze_voice_sample(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/voice/analyze")
async def analyze_voice(
    file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
    x_guest_token: str | None = Header(default=None, alias="X-Guest-Token"),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="No audio file was uploaded.")

    content_type = (file.content_type or "").lower()
    filename = (file.filename or "").lower()
    if "wav" not in content_type and not filename.endswith(".wav"):
        raise HTTPException(
            status_code=415,
            detail="Please upload WAV audio. The frontend converts recordings to WAV before calling this API.",
        )

    try:
        service = get_recommendation_service()
        actor = resolve_actor(service, authorization, x_guest_token)
        result = analyze_uploaded_voice(content, file.filename)
        persisted = service.create_analysis(actor, result)
        result["analysis_id"] = persisted["analysis"]["id"]
        result["created_at"] = persisted["analysis"].get("created_at")
        result["recommendation"] = persisted["recommendation"]
        result["steps"]["supabase_persistence"] = {"status": "done"}
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        if isinstance(exc, RecommendationServiceError):
            raise_api_error(exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
