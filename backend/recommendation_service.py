"""Database orchestration for analysis-scoped recommendations.

The service owns authorization, temporal context resolution, snapshots and
idempotent persistence.  The recommendation engine remains database-agnostic.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from recommendation_engine import build_recommendation


RECOMMENDATION_PAYLOAD_VERSION = "1.0"
CONTEXT_TYPES = {
    "analysis_only",
    "analysis_baseline",
    "analysis_assessment",
    "analysis_baseline_assessment",
}


def _load_local_environment() -> None:
    """Load backend/.env for local runs without overriding deployment secrets."""
    env_path = Path(__file__).with_name(".env")
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        name = name.strip()
        if not name or name in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ[name] = value


class RecommendationServiceError(RuntimeError):
    """Base class for controlled API errors."""


class RecordNotFoundError(RecommendationServiceError):
    pass


class AuthorizationError(RecommendationServiceError):
    pass


class InvalidContextError(RecommendationServiceError):
    pass


class RepositoryConfigurationError(RecommendationServiceError):
    pass


@dataclass(frozen=True)
class Actor:
    user_id: str | None = None
    guest_session_id: str | None = None

    def __post_init__(self) -> None:
        if bool(self.user_id) == bool(self.guest_session_id):
            raise InvalidContextError("Actor must identify exactly one member or guest session.")


class RecommendationRepository(Protocol):
    def authenticate_user(self, access_token: str) -> str: ...
    def create_guest_session(self) -> Mapping[str, Any]: ...
    def get_guest_session_by_token(self, guest_token: str) -> Mapping[str, Any] | None: ...
    def insert_analysis(self, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def get_analysis(self, analysis_id: int) -> Mapping[str, Any] | None: ...
    def get_member_baseline(self, user_id: str) -> Mapping[str, Any] | None: ...
    def upsert_member_baseline(self, user_id: str, answers: Mapping[str, Any], questionnaire_version: str) -> Mapping[str, Any]: ...
    def get_recording_assessment(self, analysis_id: int) -> Mapping[str, Any] | None: ...
    def upsert_recording_assessment(self, analysis_id: int, answers: Mapping[str, Any], questionnaire_version: str) -> Mapping[str, Any]: ...
    def get_recommendation(self, analysis_id: int) -> Mapping[str, Any] | None: ...
    def upsert_recommendation(self, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def is_baseline_applicable(
    analysis: Mapping[str, Any],
    baseline: Mapping[str, Any] | None,
    *,
    allow_explicit_current_revision: bool = False,
) -> bool:
    """Whether the current baseline can truthfully represent this analysis."""
    if not baseline or not analysis.get("user_id"):
        return False
    if str(baseline.get("user_id")) != str(analysis.get("user_id")):
        return False
    if allow_explicit_current_revision:
        return True
    analysis_time = _parse_time(analysis.get("created_at"))
    created = _parse_time(baseline.get("created_at"))
    updated = _parse_time(baseline.get("updated_at"))
    if not analysis_time or not created or not updated:
        return False
    # A single-row baseline edited after an old analysis cannot reconstruct
    # the old answers. Excluding it is safer than inventing historical context.
    return created <= analysis_time and updated <= analysis_time


def resolve_recommendation_context(
    analysis: Mapping[str, Any],
    recording_assessment: Mapping[str, Any] | None = None,
    member_baseline: Mapping[str, Any] | None = None,
    *,
    allow_explicit_current_revision: bool = False,
) -> str:
    baseline = is_baseline_applicable(
        analysis, member_baseline,
        allow_explicit_current_revision=allow_explicit_current_revision,
    )
    assessment = recording_assessment is not None
    if baseline and assessment:
        return "analysis_baseline_assessment"
    if baseline:
        return "analysis_baseline"
    if assessment:
        return "analysis_assessment"
    return "analysis_only"


def _authorize_analysis(analysis: Mapping[str, Any], actor: Actor) -> None:
    user_id = analysis.get("user_id")
    guest_session_id = analysis.get("guest_session_id")
    if bool(user_id) == bool(guest_session_id):
        raise InvalidContextError("Analysis must belong to exactly one member or guest session.")
    if user_id and str(user_id) != actor.user_id:
        raise AuthorizationError("Analysis does not belong to the authenticated member.")
    if guest_session_id and str(guest_session_id) != actor.guest_session_id:
        raise AuthorizationError("Analysis does not belong to this guest session.")


def _acoustic_input(analysis: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "quality": {
            "voice_quality": {
                "voice_quality_score": analysis["voice_quality_score"],
                "voice_condition": analysis["voice_condition"],
            },
            "hoarseness_risk": {
                "hoarseness_risk_score": analysis["hoarseness_score"],
                "hoarseness_condition": analysis["hoarseness_condition"],
            },
            "stability": {
                "stability_score": analysis["stability_score"],
                "stability_condition": analysis["stability_condition"],
            },
            "clarity": {
                "clarity_score": analysis["clarity_score"],
                "clarity_condition": analysis["clarity_condition"],
            },
        },
        "features": analysis.get("features", {}),
    }


def _snapshot(row: Mapping[str, Any] | None, *, baseline: bool = False) -> dict[str, Any] | None:
    if row is None:
        return None
    result = {
        "questionnaire_version": row.get("questionnaire_version", "1.0"),
        "answers": dict(row.get("answers") or {}),
    }
    if baseline:
        result["revision"] = row["revision"]
    return result


def _baseline_from_saved_snapshot(
    analysis: Mapping[str, Any], saved_recommendation: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Restore only the baseline already chosen for this target analysis.

    This supports the current-analysis flow where a member sets a baseline
    after recording, then completes the recording assessment. It deliberately
    uses the saved snapshot rather than the latest mutable baseline row.
    """
    snapshot = (saved_recommendation or {}).get("baseline_snapshot")
    if not isinstance(snapshot, Mapping) or not isinstance(snapshot.get("answers"), Mapping):
        return None
    revision = snapshot.get("revision")
    if not isinstance(revision, int) or revision < 1:
        return None
    return {
        "user_id": analysis.get("user_id"),
        "answers": dict(snapshot["answers"]),
        "questionnaire_version": snapshot.get("questionnaire_version", "1.0"),
        "revision": revision,
    }


def _persisted_scores(engine_scores: Mapping[str, Any]) -> dict[str, Any]:
    """Remove raw evidence values; snapshots already preserve raw answers."""
    fields = (
        "care_score", "band", "primary_source", "recording_score",
        "baseline_score", "recording_minus_baseline", "assumptions",
    )
    return {
        category: {field: values.get(field) for field in fields}
        for category, values in engine_scores["categories"].items()
    }


def _public_wording(wording: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "summary": wording["summary"],
        "recommendations": [
            {key: item[key] for key in ("rule_id", "category", "priority", "title", "reason", "action")}
            for item in wording["recommendations"]
        ],
        "clinical_claim": None,
    }


def _validate_persistence_payload(payload: Mapping[str, Any]) -> None:
    context = payload.get("context_type")
    if context not in CONTEXT_TYPES:
        raise InvalidContextError("Unknown recommendation context_type.")
    has_baseline = payload.get("baseline_snapshot") is not None
    has_assessment = payload.get("assessment_snapshot") is not None
    expected = {
        (False, False): "analysis_only",
        (True, False): "analysis_baseline",
        (False, True): "analysis_assessment",
        (True, True): "analysis_baseline_assessment",
    }[(has_baseline, has_assessment)]
    if context != expected:
        raise InvalidContextError("context_type does not match stored snapshots.")
    if has_baseline != (payload.get("baseline_revision") is not None):
        raise InvalidContextError("baseline_revision and baseline_snapshot must be present together.")


class RecommendationService:
    def __init__(
        self,
        repository: RecommendationRepository,
        ai_worder: Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        self.repository = repository
        self.ai_worder = ai_worder

    def actor_from_access_token(self, access_token: str) -> Actor:
        return Actor(user_id=self.repository.authenticate_user(access_token))

    def actor_from_guest_token(self, guest_token: str) -> Actor:
        session = self.repository.get_guest_session_by_token(guest_token)
        if not session:
            raise AuthorizationError("Guest session was not found or has expired.")
        expires = _parse_time(session.get("expires_at"))
        if not expires or expires <= datetime.now(timezone.utc):
            raise AuthorizationError("Guest session was not found or has expired.")
        return Actor(guest_session_id=str(session["id"]))

    def create_guest_session(self) -> Mapping[str, Any]:
        return self.repository.create_guest_session()

    def create_analysis(self, actor: Actor, analysis_result: Mapping[str, Any]) -> dict[str, Any]:
        quality = analysis_result["quality"]
        payload = {
            "user_id": actor.user_id,
            "guest_session_id": actor.guest_session_id,
            "voice_quality_score": quality["voice_quality"]["voice_quality_score"],
            "voice_condition": quality["voice_quality"]["voice_condition"],
            "hoarseness_score": quality["hoarseness_risk"]["hoarseness_risk_score"],
            "hoarseness_condition": quality["hoarseness_risk"]["hoarseness_condition"],
            "stability_score": quality["stability"]["stability_score"],
            "stability_condition": quality["stability"]["stability_condition"],
            "clarity_score": quality["clarity"]["clarity_score"],
            "clarity_condition": quality["clarity"]["clarity_condition"],
            "features": dict(analysis_result.get("features") or {}),
            "feature_version": "1.0",
            "scoring_version": "1.0",
        }
        analysis = self.repository.insert_analysis(payload)
        recommendation = self.generate(int(analysis["id"]), actor)
        return {"analysis": dict(analysis), "recommendation": recommendation}

    def generate(
        self,
        analysis_id: int,
        actor: Actor,
        *,
        regenerate: bool = False,
        baseline_override: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        analysis = self.repository.get_analysis(analysis_id)
        if not analysis:
            raise RecordNotFoundError("Analysis was not found.")
        _authorize_analysis(analysis, actor)

        saved = self.repository.get_recommendation(analysis_id)
        if saved and not regenerate:
            return self._response(saved)

        assessment = self.repository.get_recording_assessment(analysis_id)
        baseline = None
        allow_current = baseline_override is not None
        if analysis.get("user_id"):
            baseline = baseline_override or self.repository.get_member_baseline(str(analysis["user_id"]))
            if not is_baseline_applicable(
                analysis, baseline, allow_explicit_current_revision=allow_current
            ):
                baseline = None
        # Guest branch intentionally never calls get_member_baseline.

        context = resolve_recommendation_context(
            analysis, assessment, baseline,
            allow_explicit_current_revision=allow_current,
        )
        baseline_snapshot = _snapshot(baseline, baseline=True)
        assessment_snapshot = _snapshot(assessment)
        pipeline = build_recommendation(
            _acoustic_input(analysis),
            baseline_snapshot["answers"] if baseline_snapshot else None,
            assessment_snapshot["answers"] if assessment_snapshot else None,
            # V1 is deterministic and already short. Wait for the recording
            # assessment before spending one AI request on personalized
            # wording, which keeps a daily recording flow to one request.
            self.ai_worder if assessment_snapshot else None,
            language="en",
        )
        wording = _public_wording(pipeline["final_recommendation"])
        persistence = {
            "analysis_id": analysis_id,
            "context_type": context,
            "baseline_revision": baseline_snapshot["revision"] if baseline_snapshot else None,
            "baseline_snapshot": baseline_snapshot,
            "assessment_snapshot": assessment_snapshot,
            "behavior_scores": _persisted_scores(pipeline["behavior_scores"]),
            "behavior_scoring_version": pipeline["behavior_scoring_version"],
            "recommendation_rule_version": pipeline["recommendation_rule_version"],
            "recommendations": wording,
            "recommendation_version": RECOMMENDATION_PAYLOAD_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        _validate_persistence_payload(persistence)
        saved = self.repository.upsert_recommendation(persistence)
        return self._response(saved)

    def save_recording_assessment(
        self,
        analysis_id: int,
        actor: Actor,
        answers: Mapping[str, Any],
        questionnaire_version: str = "1.0",
    ) -> dict[str, Any]:
        analysis = self.repository.get_analysis(analysis_id)
        if not analysis:
            raise RecordNotFoundError("Analysis was not found.")
        _authorize_analysis(analysis, actor)
        self.repository.upsert_recording_assessment(
            analysis_id, answers, questionnaire_version
        )
        saved = self.repository.get_recommendation(analysis_id)
        # Preserve a baseline intentionally attached to this current analysis
        # by a prior baseline-save action. This is not historical inference.
        baseline_override = _baseline_from_saved_snapshot(analysis, saved)
        return self.generate(
            analysis_id,
            actor,
            regenerate=True,
            baseline_override=baseline_override,
        )

    def save_member_baseline(
        self,
        actor: Actor,
        answers: Mapping[str, Any],
        questionnaire_version: str = "1.0",
        analysis_id: int | None = None,
    ) -> dict[str, Any]:
        if not actor.user_id:
            raise AuthorizationError("Guests cannot create a member baseline.")
        baseline = self.repository.upsert_member_baseline(
            actor.user_id, answers, questionnaire_version
        )
        result: dict[str, Any] = {"baseline": dict(baseline), "recommendation": None}
        if analysis_id is not None:
            analysis = self.repository.get_analysis(analysis_id)
            if not analysis:
                raise RecordNotFoundError("Analysis was not found.")
            _authorize_analysis(analysis, actor)
            result["recommendation"] = self.generate(
                analysis_id, actor, regenerate=True, baseline_override=baseline
            )
        return result

    def get_member_baseline(self, actor: Actor) -> Mapping[str, Any] | None:
        if not actor.user_id:
            raise AuthorizationError("Guests do not have a member baseline.")
        return self.repository.get_member_baseline(actor.user_id)

    def get_recording_assessment(self, analysis_id: int, actor: Actor) -> Mapping[str, Any] | None:
        analysis = self.repository.get_analysis(analysis_id)
        if not analysis:
            raise RecordNotFoundError("Analysis was not found.")
        _authorize_analysis(analysis, actor)
        return self.repository.get_recording_assessment(analysis_id)

    @staticmethod
    def _response(saved: Mapping[str, Any]) -> dict[str, Any]:
        wording = saved.get("recommendations") or {}
        return {
            "analysis_id": saved["analysis_id"],
            "context_type": saved["context_type"],
            "behavior_scores": saved.get("behavior_scores") or {},
            "summary": wording.get("summary", ""),
            "recommendations": wording.get("recommendations", []),
            "clinical_claim": None,
            "versions": {
                "behavior_scoring": saved.get("behavior_scoring_version"),
                "recommendation_rules": saved.get("recommendation_rule_version"),
                "recommendation": saved.get("recommendation_version"),
            },
            "generated_at": saved.get("generated_at"),
        }


class SupabaseRestRepository:
    """Minimal PostgREST adapter. The server-side Supabase key remains private."""

    def __init__(self, url: str, service_role_key: str, timeout: float = 15.0) -> None:
        self.url = url.rstrip("/")
        self.key = service_role_key
        self.timeout = timeout

    @classmethod
    def from_environment(cls) -> "SupabaseRestRepository":
        # Local development uses backend/.env. Hosted deployments should inject
        # these values through their secret manager, which takes precedence.
        _load_local_environment()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SECRET_KEY")
        if not url or not key:
            raise RepositoryConfigurationError(
                "SUPABASE_URL and a server-side Supabase key "
                "(SUPABASE_SECRET_KEY or SUPABASE_SERVICE_ROLE_KEY) must be configured on the backend."
            )
        return cls(url, key)

    def _headers(self, *, bearer: str | None = None, prefer: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {bearer or self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        params = kwargs.pop("params", None)
        url = f"{self.url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        payload = kwargs.pop("json", None)
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            url,
            data=body,
            headers=kwargs.pop("headers", {}),
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content = response.read()
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RecommendationServiceError(
                f"Supabase request failed ({error.code}): {detail[:500]}"
            ) from error
        except URLError as error:
            raise RecommendationServiceError(
                f"Supabase request could not be completed: {error.reason}"
            ) from error
        if not content:
            return None
        return json.loads(content.decode("utf-8"))

    @staticmethod
    def _one(rows: Any) -> Mapping[str, Any] | None:
        return rows[0] if isinstance(rows, list) and rows else None

    def authenticate_user(self, access_token: str) -> str:
        user = self._request(
            "GET", "/auth/v1/user", headers=self._headers(bearer=access_token)
        )
        if not user or not user.get("id"):
            raise AuthorizationError("Authentication token is invalid.")
        return str(user["id"])

    def create_guest_session(self) -> Mapping[str, Any]:
        rows = self._request(
            "POST", "/rest/v1/guest_session", json={},
            headers=self._headers(prefer="return=representation"),
        )
        return dict(self._one(rows) or {})

    def get_guest_session_by_token(self, guest_token: str) -> Mapping[str, Any] | None:
        rows = self._request(
            "GET", "/rest/v1/guest_session",
            params={"guest_token": f"eq.{guest_token}", "select": "id,guest_token,expires_at"},
            headers=self._headers(),
        )
        return self._one(rows)

    def insert_analysis(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        rows = self._request(
            "POST", "/rest/v1/analysis", json=dict(payload),
            headers=self._headers(prefer="return=representation"),
        )
        return dict(self._one(rows) or {})

    def _get_one(self, table: str, params: Mapping[str, str]) -> Mapping[str, Any] | None:
        rows = self._request(
            "GET", f"/rest/v1/{table}", params=dict(params), headers=self._headers()
        )
        return self._one(rows)

    def get_analysis(self, analysis_id: int) -> Mapping[str, Any] | None:
        return self._get_one("analysis", {"id": f"eq.{analysis_id}", "select": "*"})

    def get_member_baseline(self, user_id: str) -> Mapping[str, Any] | None:
        return self._get_one("member_baseline", {"user_id": f"eq.{user_id}", "select": "*"})

    def upsert_member_baseline(self, user_id: str, answers: Mapping[str, Any], questionnaire_version: str) -> Mapping[str, Any]:
        result = self._request(
            "POST", "/rest/v1/rpc/upsert_member_baseline",
            json={"p_user_id": user_id, "p_answers": dict(answers), "p_questionnaire_version": questionnaire_version},
            headers=self._headers(),
        )
        row = self._one(result) if isinstance(result, list) else result
        return dict(row or {})

    def get_recording_assessment(self, analysis_id: int) -> Mapping[str, Any] | None:
        return self._get_one("recording_assessment", {"analysis_id": f"eq.{analysis_id}", "select": "*"})

    def upsert_recording_assessment(self, analysis_id: int, answers: Mapping[str, Any], questionnaire_version: str) -> Mapping[str, Any]:
        rows = self._request(
            "POST", "/rest/v1/recording_assessment", params={"on_conflict": "analysis_id"},
            json={"analysis_id": analysis_id, "answers": dict(answers), "questionnaire_version": questionnaire_version, "updated_at": datetime.now(timezone.utc).isoformat()},
            headers=self._headers(prefer="resolution=merge-duplicates,return=representation"),
        )
        return dict(self._one(rows) or {})

    def get_recommendation(self, analysis_id: int) -> Mapping[str, Any] | None:
        return self._get_one("recommendation", {"analysis_id": f"eq.{analysis_id}", "select": "*"})

    def upsert_recommendation(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        rows = self._request(
            "POST", "/rest/v1/recommendation", params={"on_conflict": "analysis_id"},
            json=dict(payload),
            headers=self._headers(prefer="resolution=merge-duplicates,return=representation"),
        )
        return dict(self._one(rows) or {})
