"""Integration-oriented tests with an in-memory Supabase repository."""
from __future__ import annotations

import copy
import os
import unittest
from unittest.mock import patch

from recommendation_service import (
    Actor,
    AuthorizationError,
    InvalidContextError,
    RecordNotFoundError,
    RecommendationService,
    SupabaseRestRepository,
)


def analysis(analysis_id: int, *, user_id: str | None = "user-1", guest_id: str | None = None) -> dict:
    return {
        "id": analysis_id,
        "created_at": "2026-09-10T12:00:00+00:00",
        "user_id": user_id,
        "guest_session_id": guest_id,
        "voice_quality_score": 62,
        "voice_condition": "moderate",
        "hoarseness_score": 38,
        "hoarseness_condition": "low",
        "stability_score": 55,
        "stability_condition": "slightly_unstable",
        "clarity_score": 67,
        "clarity_condition": "slightly_unclear",
        "features": {"jitter_local": 0.004},
    }


def baseline(*, user_id: str = "user-1", revision: int = 1, updated_at: str = "2026-09-09T12:00:00+00:00") -> dict:
    return {
        "id": 1, "user_id": user_id, "answers": {"glassesWaterPerDay": 7},
        "questionnaire_version": "1.0", "revision": revision,
        "created_at": "2026-09-09T10:00:00+00:00", "updated_at": updated_at,
    }


def assessment(analysis_id: int) -> dict:
    return {
        "id": analysis_id, "analysis_id": analysis_id,
        "answers": {"regularVoiceUse": ["Shout or yell"], "continuousMinutes": 10},
        "questionnaire_version": "1.0", "completed_at": "2026-09-10T12:05:00+00:00",
        "updated_at": "2026-09-10T12:05:00+00:00",
    }


class FakeRepository:
    def __init__(self) -> None:
        self.analyses: dict[int, dict] = {}
        self.baselines: dict[str, dict] = {}
        self.assessments: dict[int, dict] = {}
        self.recommendations: dict[int, dict] = {}
        self.baseline_queries = 0
        self.recommendation_upserts: list[int] = []

    def authenticate_user(self, access_token):
        return access_token

    def create_guest_session(self):
        return {"id": "guest-1", "guest_token": "token-1", "expires_at": "2099-01-01T00:00:00+00:00"}

    def get_guest_session_by_token(self, guest_token):
        return self.create_guest_session() if guest_token == "token-1" else None

    def insert_analysis(self, payload):
        row = {**analysis(len(self.analyses) + 1, user_id=payload.get("user_id"), guest_id=payload.get("guest_session_id")), **dict(payload)}
        self.analyses[row["id"]] = row
        return copy.deepcopy(row)

    def get_analysis(self, analysis_id):
        return copy.deepcopy(self.analyses.get(analysis_id))

    def get_member_baseline(self, user_id):
        self.baseline_queries += 1
        return copy.deepcopy(self.baselines.get(user_id))

    def upsert_member_baseline(self, user_id, answers, questionnaire_version):
        current = self.baselines.get(user_id)
        row = baseline(user_id=user_id, revision=(current["revision"] + 1 if current else 1), updated_at="2026-09-11T00:00:00+00:00")
        if current:
            row["created_at"] = current["created_at"]
        row["answers"] = dict(answers)
        row["questionnaire_version"] = questionnaire_version
        self.baselines[user_id] = row
        return copy.deepcopy(row)

    def get_recording_assessment(self, analysis_id):
        return copy.deepcopy(self.assessments.get(analysis_id))

    def upsert_recording_assessment(self, analysis_id, answers, questionnaire_version):
        row = assessment(analysis_id)
        row["answers"] = dict(answers)
        row["questionnaire_version"] = questionnaire_version
        self.assessments[analysis_id] = row
        return copy.deepcopy(row)

    def get_recommendation(self, analysis_id):
        return copy.deepcopy(self.recommendations.get(analysis_id))

    def upsert_recommendation(self, payload):
        row = {"id": self.recommendations.get(payload["analysis_id"], {}).get("id", len(self.recommendations) + 1), **copy.deepcopy(dict(payload))}
        self.recommendations[payload["analysis_id"]] = row
        self.recommendation_upserts.append(payload["analysis_id"])
        return copy.deepcopy(row)


class RecommendationServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = FakeRepository()
        self.repo.analyses[1] = analysis(1)
        self.service = RecommendationService(self.repo)
        self.member = Actor(user_id="user-1")

    def test_analysis_only_context(self):
        self.assertEqual(self.service.generate(1, self.member)["context_type"], "analysis_only")

    def test_analysis_baseline_context(self):
        self.repo.baselines["user-1"] = baseline()
        self.assertEqual(self.service.generate(1, self.member)["context_type"], "analysis_baseline")

    def test_analysis_assessment_context(self):
        self.repo.assessments[1] = assessment(1)
        self.assertEqual(self.service.generate(1, self.member)["context_type"], "analysis_assessment")

    def test_analysis_baseline_assessment_context(self):
        self.repo.baselines["user-1"] = baseline()
        self.repo.assessments[1] = assessment(1)
        self.assertEqual(self.service.generate(1, self.member)["context_type"], "analysis_baseline_assessment")

    def test_guest_assessment_never_queries_baseline(self):
        self.repo.analyses[2] = analysis(2, user_id=None, guest_id="guest-1")
        self.repo.assessments[2] = assessment(2)
        result = self.service.generate(2, Actor(guest_session_id="guest-1"))
        self.assertEqual(result["context_type"], "analysis_assessment")
        self.assertEqual(self.repo.baseline_queries, 0)

    def test_baseline_created_after_analysis_is_excluded(self):
        late = baseline(updated_at="2026-09-11T00:00:00+00:00")
        late["created_at"] = "2026-09-11T00:00:00+00:00"
        self.repo.baselines["user-1"] = late
        self.assertEqual(self.service.generate(1, self.member)["context_type"], "analysis_only")

    def test_saved_historical_recommendation_is_not_regenerated(self):
        first = self.service.generate(1, self.member)
        self.repo.baselines["user-1"] = baseline(revision=9, updated_at="2026-09-11T00:00:00+00:00")
        second = self.service.generate(1, self.member)
        self.assertEqual(first, second)
        self.assertEqual(self.repo.recommendation_upserts, [1])
        self.assertEqual(self.repo.baseline_queries, 1)

    def test_assessment_submission_updates_same_recommendation_row(self):
        self.service.generate(1, self.member)
        original_id = self.repo.recommendations[1]["id"]
        result = self.service.save_recording_assessment(1, self.member, assessment(1)["answers"])
        self.assertEqual(result["context_type"], "analysis_assessment")
        self.assertEqual(self.repo.recommendations[1]["id"], original_id)
        self.assertEqual(len(self.repo.recommendations), 1)

    def test_current_baseline_then_assessment_keeps_member_v2_context(self):
        self.service.save_member_baseline(
            self.member, {"glassesWaterPerDay": 4}, analysis_id=1
        )
        result = self.service.save_recording_assessment(
            1, self.member, assessment(1)["answers"]
        )
        saved = self.repo.recommendations[1]
        self.assertEqual(result["context_type"], "analysis_baseline_assessment")
        self.assertEqual(saved["baseline_snapshot"]["revision"], 1)
        self.assertEqual(saved["assessment_snapshot"]["answers"], assessment(1)["answers"])

    def test_baseline_edit_regenerates_only_target_analysis(self):
        self.repo.analyses[2] = analysis(2)
        self.service.generate(1, self.member)
        self.service.generate(2, self.member)
        before_two = copy.deepcopy(self.repo.recommendations[2])
        result = self.service.save_member_baseline(self.member, {"glassesWaterPerDay": 4}, analysis_id=1)
        self.assertEqual(result["recommendation"]["context_type"], "analysis_baseline")
        self.assertEqual(self.repo.recommendations[2], before_two)
        self.assertEqual(self.repo.recommendation_upserts.count(1), 2)
        self.assertEqual(self.repo.recommendation_upserts.count(2), 1)

    def test_duplicate_generation_is_idempotent(self):
        self.service.generate(1, self.member)
        self.service.generate(1, self.member)
        self.assertEqual(self.repo.recommendation_upserts, [1])

    def test_ai_failure_persists_fallback(self):
        def broken_ai(_contract):
            raise ConnectionError("offline")

        service = RecommendationService(self.repo, broken_ai)
        self.repo.assessments[1] = assessment(1)
        result = service.generate(1, self.member)
        self.assertTrue(result["recommendations"])
        self.assertEqual(self.repo.recommendations[1]["recommendations"]["clinical_claim"], None)

    def test_ai_wording_waits_for_the_recording_assessment(self):
        calls = 0

        def unavailable_ai(_contract):
            nonlocal calls
            calls += 1
            raise ConnectionError("offline")

        service = RecommendationService(self.repo, unavailable_ai)
        service.generate(1, self.member)
        self.assertEqual(calls, 0)

        service.save_recording_assessment(1, self.member, assessment(1)["answers"])
        self.assertEqual(calls, 1)

    def test_unauthorized_member_is_rejected(self):
        with self.assertRaises(AuthorizationError):
            self.service.generate(1, Actor(user_id="user-2"))

    def test_nonexistent_analysis_is_rejected(self):
        with self.assertRaises(RecordNotFoundError):
            self.service.generate(999, self.member)

    def test_invalid_analysis_owner_state_is_rejected(self):
        self.repo.analyses[3] = analysis(3, user_id="user-1", guest_id="guest-1")
        with self.assertRaises(InvalidContextError):
            self.service.generate(3, self.member)

    def test_persistence_has_versions_and_versioned_snapshots(self):
        self.repo.baselines["user-1"] = baseline(revision=2)
        self.repo.assessments[1] = assessment(1)
        self.service.generate(1, self.member)
        saved = self.repo.recommendations[1]
        self.assertTrue(saved["behavior_scoring_version"])
        self.assertTrue(saved["recommendation_rule_version"])
        self.assertEqual(saved["recommendation_version"], "1.0")
        self.assertEqual(saved["baseline_snapshot"]["revision"], 2)
        self.assertEqual(saved["assessment_snapshot"]["questionnaire_version"], "1.0")
        self.assertNotIn("evidence", saved["behavior_scores"]["hydration"])

    def test_repository_accepts_the_configured_secret_key_name(self):
        with patch.dict(
            os.environ,
            {"SUPABASE_URL": "https://project.supabase.co", "SUPABASE_SECRET_KEY": "server-secret"},
            clear=True,
        ), patch("recommendation_service._load_local_environment"):
            repository = SupabaseRestRepository.from_environment()
        self.assertEqual(repository.url, "https://project.supabase.co")
        self.assertEqual(repository.key, "server-secret")


if __name__ == "__main__":
    unittest.main()
