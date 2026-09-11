"""Unit tests for the deterministic recommendation pipeline."""
from __future__ import annotations

import copy
import unittest

from recommendation_engine import build_recommendation


NONE = ["None of the above"]


def supportive_recording() -> dict:
    return {
        "symptoms": {"Burning throat or chest": 0, "Sour or bitter taste": 0},
        "caffeine": "no",
        "soda": "no",
        "spicyFood": "no",
        "friedFood": "no",
        "irregularMeal": "no",
        "smoked": "no",
        "alcohol": "no",
        "glassesToday": 7,
        "recentWater": "Small sips",
        "hoursSlept": 7,
        "regularVoiceUse": NONE,
        "continuousMinutes": 0,
        "environment": NONE,
    }


def rule_ids(result: dict, key: str = "selected_candidates") -> list[str]:
    return [item["rule_id"] for item in result[key]]


class RecommendationEngineTests(unittest.TestCase):
    def test_strong_voice_use_is_first_and_consolidated(self):
        recording = supportive_recording()
        recording.update({
            "regularVoiceUse": [
                "Speak loudly", "Shout or yell", "Speak continuously for long periods",
                "Strain or tense neck while speaking",
            ],
            "continuousMinutes": 60,
        })
        result = build_recommendation(None, None, recording)
        self.assertEqual(rule_ids(result)[0], "reduce_vocal_load")
        voice_candidates = [c for c in result["candidate_recommendations"] if c["category"] == "voice_use"]
        self.assertEqual(len(voice_candidates), 1)
        self.assertEqual(
            set(voice_candidates[0]["triggered_rule_ids"]),
            {"reduce_vocal_load", "reduce_shouting", "take_voice_breaks", "manage_voice_tension"},
        )

    def test_supportive_answers_generate_no_warning(self):
        result = build_recommendation(None, None, supportive_recording())
        self.assertEqual(result["candidate_recommendations"], [])
        self.assertEqual(result["final_recommendation"]["recommendations"], [])

    def test_supportive_answers_do_not_call_the_ai_worder(self):
        calls = 0

        def should_not_run(_contract):
            nonlocal calls
            calls += 1
            raise AssertionError("AI must not be called without selected recommendations")

        result = build_recommendation(None, None, supportive_recording(), should_not_run)
        self.assertEqual(calls, 0)
        self.assertEqual(result["wording_source"], "deterministic_fallback")

    def test_low_hydration_only_uses_cautious_action(self):
        recording = supportive_recording()
        recording["glassesToday"] = 2
        result = build_recommendation(None, None, recording, language="en")
        self.assertEqual(rule_ids(result), ["support_hydration"])
        action = result["final_recommendation"]["recommendations"][0]["action"].lower()
        self.assertIn("adequate", action)
        self.assertNotIn("8 glasses", action)

    def test_caffeine_alone_does_not_create_negative_candidate(self):
        recording = supportive_recording()
        recording["caffeine"] = "yes"
        result = build_recommendation(None, None, recording)
        self.assertEqual(result["candidate_recommendations"], [])

    def test_food_without_reflux_is_cautious_and_low_ranked(self):
        recording = supportive_recording()
        recording.update({"friedFood": "yes", "irregularMeal": "yes"})
        result = build_recommendation(None, None, recording, language="en")
        candidate = next(c for c in result["candidate_recommendations"] if c["rule_id"] == "adjust_food_pattern")
        self.assertEqual(candidate["priority"], "low")
        rendered = str(result["final_recommendation"]).lower()
        self.assertNotIn("diagnos", rendered)
        self.assertNotIn("laryngopharyngeal reflux", rendered)

    def test_smoking_creates_exposure_advice_without_diagnosis(self):
        recording = supportive_recording()
        recording["smoked"] = "yes"
        result = build_recommendation(None, None, recording, language="en")
        self.assertIn("reduce_smoke_exposure", rule_ids(result))
        self.assertIsNone(result["final_recommendation"]["clinical_claim"])
        self.assertNotIn("disease", str(result["final_recommendation"]).lower())

    def test_missing_baseline_still_uses_recording(self):
        recording = supportive_recording()
        recording["regularVoiceUse"] = ["Shout or yell"]
        result = build_recommendation(None, None, recording)
        self.assertIn("reduce_shouting", rule_ids(result))

    def test_missing_recording_uses_baseline(self):
        baseline = {
            "glassesWaterPerDay": 7,
            "regularVoiceUse": ["Shout or yell"],
            "hoursVoiceHome": 0,
            "hoursVoiceWork": 0,
            "smokingStatus": "never",
            "alcoholStatus": "no",
            "homeEnvironment": NONE,
            "workEnvironment": NONE,
            "eatingHabits": NONE,
        }
        result = build_recommendation(None, baseline, None)
        self.assertIn("reduce_shouting", rule_ids(result))
        fact_sources = {f["source"] for f in result["selected_candidates"][0]["evidence"]}
        self.assertEqual(fact_sources, {"member_baseline"})

    def test_guest_has_no_baseline_dependency(self):
        recording = supportive_recording()
        recording["hoursSlept"] = 4
        result = build_recommendation(None, None, recording)
        self.assertIn("improve_recovery", rule_ids(result))

    def test_ai_invented_rule_falls_back(self):
        recording = supportive_recording()
        recording["glassesToday"] = 2

        def bad_ai(contract):
            candidate = contract["candidates"][0]
            return {
                "summary": "summary",
                "recommendations": [{
                    "rule_id": "invented_rule", "category": candidate["category"],
                    "priority": candidate["priority"], "title": "title", "reason": "reason",
                    "action": "action", "used_fact_ids": [candidate["reason_facts"][0]["fact_id"]],
                    "action_ids": [candidate["allowed_actions"][0]["action_id"]],
                }],
                "clinical_claim": None,
            }

        result = build_recommendation(None, None, recording, bad_ai)
        self.assertEqual(result["wording_source"], "deterministic_fallback")
        self.assertIn("changed rule_id", result["wording_validation_error"])

    def test_ai_changed_priority_falls_back(self):
        recording = supportive_recording()
        recording["glassesToday"] = 2

        def bad_ai(contract):
            candidate = contract["candidates"][0]
            changed = "low" if candidate["priority"] != "low" else "high"
            return {
                "summary": "summary",
                "recommendations": [{
                    "rule_id": candidate["rule_id"], "category": candidate["category"],
                    "priority": changed, "title": "title", "reason": "reason",
                    "action": "action", "used_fact_ids": [candidate["reason_facts"][0]["fact_id"]],
                    "action_ids": [candidate["allowed_actions"][0]["action_id"]],
                }],
                "clinical_claim": None,
            }

        result = build_recommendation(None, None, recording, bad_ai)
        self.assertEqual(result["wording_source"], "deterministic_fallback")
        self.assertIn("changed priority", result["wording_validation_error"])

    def test_ai_failure_falls_back(self):
        recording = supportive_recording()
        recording["glassesToday"] = 2

        def unavailable(_contract):
            raise ConnectionError("provider unavailable")

        result = build_recommendation(None, None, recording, unavailable)
        self.assertEqual(result["wording_source"], "deterministic_fallback")
        self.assertEqual(rule_ids(result), ["support_hydration"])

    def test_valid_ai_wording_is_accepted(self):
        recording = supportive_recording()
        recording["glassesToday"] = 2

        def valid_ai(contract):
            candidate = contract["candidates"][0]
            return {
                "summary": "Hydration is the first topic to review.",
                "recommendations": [{
                    "rule_id": candidate["rule_id"], "category": candidate["category"],
                    "priority": candidate["priority"], "title": "Support hydration",
                    "reason": "The reported water amount was 2 glasses.",
                    "action": "Maintain adequate, regular hydration.",
                    "used_fact_ids": ["hydration_amount"],
                    "action_ids": ["maintain_hydration"],
                }],
                "clinical_claim": None,
            }

        result = build_recommendation(None, None, recording, valid_ai, language="en")
        self.assertEqual(result["wording_source"], "ai_validated")
        self.assertIsNone(result["wording_validation_error"])

    def test_ai_cross_category_fact_fabrication_falls_back(self):
        recording = supportive_recording()
        recording["glassesToday"] = 2

        def fabricated_ai(contract):
            candidate = contract["candidates"][0]
            return {
                "summary": "summary",
                "recommendations": [{
                    "rule_id": candidate["rule_id"], "category": candidate["category"],
                    "priority": candidate["priority"], "title": "title",
                    "reason": "You reported shouting and 2 glasses of water.",
                    "action": "Maintain adequate hydration.",
                    "used_fact_ids": ["hydration_amount"],
                    "action_ids": ["maintain_hydration"],
                }],
                "clinical_claim": None,
            }

        result = build_recommendation(None, None, recording, fabricated_ai, language="en")
        self.assertEqual(result["wording_source"], "deterministic_fallback")
        self.assertIn("fact type absent", result["wording_validation_error"])

    def test_acoustic_context_is_read_only(self):
        recording = supportive_recording()
        recording["regularVoiceUse"] = ["Shout or yell"]
        acoustic = {"quality": {"stability": {"stability_score": 30, "stability_condition": "Low"}}}
        before = copy.deepcopy(acoustic)
        result = build_recommendation(acoustic, None, recording)
        self.assertEqual(acoustic, before)
        self.assertFalse(result["acoustic_result_modified"])
        self.assertEqual(result["selected_candidates"][0]["priority_breakdown"]["acoustic_context"], 5)


if __name__ == "__main__":
    unittest.main()
