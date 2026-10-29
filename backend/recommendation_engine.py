"""Deterministic behavior scoring and recommendation orchestration.

The LLM is an optional wording layer. It never calculates scores, selects
rules, changes priority, or changes the acoustic analysis result.
"""
from __future__ import annotations

import copy
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any


BEHAVIOR_SCORING_VERSION = "behavior-scoring-v0.1"
RECOMMENDATION_RULE_VERSION = "recommendation-rules-v0.2"
MAX_RECOMMENDATIONS = 3
MAX_SUMMARY_CHARACTERS = 120
MAX_TITLE_CHARACTERS = 50
MAX_REASON_CHARACTERS = 180
MAX_ACTION_CHARACTERS = 160

BANDS = (
    (85, "supportive"),
    (70, "mostly_supportive"),
    (50, "mixed"),
    (0, "needs_attention"),
)

# Product-policy weights. They are deliberately explicit and are not learned
# clinical thresholds. See ml/behavior_scoring_design.md for their evidence.
CATEGORY_WEIGHTS = {
    "voice_use": 36,
    "exposure_avoidance": 34,
    "hydration": 20,
    "recovery": 20,
    "food_pattern": 12,
}
SEVERITY_WEIGHT = 0.35
MAX_SEVERITY_POINTS = 35
MAX_SUPPORT_POINTS = 12
RECORDING_RELEVANCE_POINTS = 12
BASELINE_RELEVANCE_POINTS = 5
BASELINE_CORROBORATION_POINTS = 3
ACOUSTIC_CONTEXT_POINTS = 5


FALLBACK_TEMPLATES = {
    "reduce_vocal_load": {
        "th": ("ลดภาระการใช้เสียง", "พักเสียงเป็นช่วง ลดการตะโกนและการใช้เสียงต่อเนื่องเมื่อทำได้"),
        "en": ("Reduce vocal load", "Take short voice-rest periods and reduce prolonged or forceful voice use when possible."),
    },
    "reduce_shouting": {
        "th": ("ลดการตะโกน", "ลดการตะโกนหรือใช้เสียงดังเมื่อทำได้ และพักเสียงหลังช่วงที่ต้องใช้เสียงมาก"),
        "en": ("Reduce shouting", "Reduce shouting or loud voice use when possible and rest after demanding voice use."),
    },
    "manage_voice_tension": {
        "th": ("ลดความเกร็งขณะใช้เสียง", "ผ่อนคลายคอและไหล่ และหลีกเลี่ยงการฝืนเสียงเมื่อรู้สึกเกร็ง"),
        "en": ("Reduce tension during voice use", "Relax the neck and shoulders and avoid forcing the voice when tension is present."),
    },
    "take_voice_breaks": {
        "th": ("พักเสียงเป็นช่วง", "แทรกช่วงพักสั้น ๆ ระหว่างการใช้เสียงต่อเนื่องเมื่อทำได้"),
        "en": ("Take voice breaks", "Add short rest periods during prolonged voice use when possible."),
    },
    "support_hydration": {
        "th": ("ดูแลการดื่มน้ำ", "รักษาการดื่มน้ำอย่างเพียงพอและสม่ำเสมอตามบริบทของคุณ"),
        "en": ("Support hydration", "Maintain adequate, regular hydration for your circumstances."),
    },
    "improve_recovery": {
        "th": ("เพิ่มเวลาพักฟื้น", "จัดเวลานอนและพักให้เพียงพอ โดยเฉพาะก่อนวันที่ต้องใช้เสียงมาก"),
        "en": ("Improve recovery", "Allow adequate sleep and recovery, especially before demanding voice use."),
    },
    "reduce_smoke_exposure": {
        "th": ("ลดการสัมผัสควัน", "หลีกเลี่ยงการสูบบุหรี่และการสัมผัสควันเมื่อทำได้"),
        "en": ("Reduce smoke exposure", "Avoid smoking and smoke exposure when possible."),
    },
    "reduce_alcohol_exposure": {
        "th": ("ทบทวนการดื่มแอลกอฮอล์", "ลดหรือหลีกเลี่ยงแอลกอฮอล์ใกล้ช่วงที่ต้องใช้เสียงเมื่อทำได้"),
        "en": ("Review alcohol use", "Reduce or avoid alcohol near demanding voice use when possible."),
    },
    "reduce_polluted_air_exposure": {
        "th": ("ลดการสัมผัสอากาศระคายเคือง", "ลดการสัมผัสฝุ่น ควัน หรืออากาศปนเปื้อนเมื่อทำได้"),
        "en": ("Reduce irritating air exposure", "Reduce exposure to dust, smoke, or polluted air when possible."),
    },
    "adjust_food_pattern": {
        "th": ("ทบทวนรูปแบบการรับประทาน", "สังเกตอาหารและเวลารับประทานที่สัมพันธ์กับอาการของคุณ และปรับสิ่งกระตุ้นเฉพาะบุคคลเมื่อพบความสัมพันธ์"),
        "en": ("Review eating patterns", "Notice foods and meal timing associated with your symptoms and adjust personal triggers when a pattern is present."),
    },
}

ACTION_TEXT = {
    "take_voice_breaks": "take short voice-rest periods",
    "reduce_shouting": "reduce shouting when possible",
    "avoid_prolonged_voice_use": "avoid prolonged continuous voice use when possible",
    "relax_neck": "relax the neck and shoulders during voice use",
    "maintain_hydration": "maintain adequate, regular hydration for the user's circumstances",
    "allow_recovery": "allow adequate sleep and recovery before demanding voice use",
    "avoid_smoking": "avoid smoking when possible",
    "avoid_smoke": "avoid second-hand smoke when reported",
    "reduce_alcohol_near_voice_use": "reduce or avoid alcohol near demanding voice use when possible",
    "reduce_polluted_air": "reduce exposure to dust, smoke, or polluted air when possible",
    "review_personal_food_triggers": "review foods and meal timing associated with reported symptoms",
}


class AIResponseValidationError(ValueError):
    """Raised when wording output changes deterministic decisions or facts."""


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _yes(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().casefold()
    if normalized in {"yes", "true", "1", "current"}:
        return True
    if normalized in {"no", "false", "0", "never", "none", ""}:
        return False
    return None


def _items(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        raw = value.split(",")
    elif isinstance(value, Sequence):
        raw = value
    else:
        return set()
    return {str(item).strip().casefold() for item in raw if str(item).strip()}


def _contains(items: set[str], *labels: str) -> bool:
    return any(label.casefold() in items for label in labels)


def _band(score: int | None) -> str:
    if score is None:
        return "insufficient_data"
    return next(label for lower, label in BANDS if score >= lower)


def _score_record(
    recording_score: float | None,
    baseline_score: float | None,
    evidence: list[dict[str, Any]],
    assumptions: list[str],
) -> dict[str, Any]:
    primary = recording_score if recording_score is not None else baseline_score
    rounded = None if primary is None else round(max(0, min(100, primary)))
    return {
        "care_score": rounded,
        "band": _band(rounded),
        "primary_source": "recording_assessment" if recording_score is not None else (
            "member_baseline" if baseline_score is not None else None
        ),
        "recording_score": None if recording_score is None else round(max(0, min(100, recording_score))),
        "baseline_score": None if baseline_score is None else round(max(0, min(100, baseline_score))),
        "recording_minus_baseline": (
            None if recording_score is None or baseline_score is None
            else round(max(0, min(100, recording_score)) - max(0, min(100, baseline_score)))
        ),
        "evidence": evidence,
        "assumptions": assumptions,
    }


def _water_points(value: Any) -> int | None:
    glasses = _number(value)
    if glasses is None or glasses < 0:
        return None
    if glasses == 0:
        return 0
    if glasses <= 2:
        return 25
    if glasses <= 4:
        return 50
    if glasses <= 6:
        return 75
    return 100


def _symptom(recording: Mapping[str, Any], label: str) -> float | None:
    symptoms = recording.get("symptoms")
    if not isinstance(symptoms, Mapping):
        return None
    aliases = {
        "burning": ("Burning throat or chest", "burning"),
        "sour": ("Sour or bitter taste", "sour"),
    }
    for key in aliases[label]:
        if key in symptoms:
            return _number(symptoms[key])
    return None


def score_behaviors(
    member_baseline: Mapping[str, Any] | None,
    recording_assessment: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return deterministic category scores without modifying either input."""
    baseline = member_baseline or {}
    recording = recording_assessment or {}
    evidence: dict[str, list[dict[str, Any]]] = {name: [] for name in CATEGORY_WEIGHTS}

    recording_water = _water_points(recording.get("glassesToday"))
    baseline_water = _water_points(baseline.get("glassesWaterPerDay"))
    if "glassesToday" in recording:
        evidence["hydration"].append({"source": "recording_assessment", "field": "glassesToday", "value": recording.get("glassesToday"), "included_in_score": recording_water is not None})
    if "recentWater" in recording:
        evidence["hydration"].append({"source": "recording_assessment", "field": "recentWater", "value": recording.get("recentWater"), "included_in_score": False})
    if "glassesWaterPerDay" in baseline:
        evidence["hydration"].append({"source": "member_baseline", "field": "glassesWaterPerDay", "value": baseline.get("glassesWaterPerDay"), "included_in_score": baseline_water is not None})

    reflux_context = max(_symptom(recording, "burning") or 0, _symptom(recording, "sour") or 0) >= 2
    recent_food_rules = (
        ("friedFood", 25), ("irregularMeal", 20), ("spicyFood", 15 if reflux_context else 5),
        ("soda", 10 if reflux_context else 0), ("caffeine", 5 if reflux_context else 0),
    )
    recording_food_answered = any(field in recording for field, _ in recent_food_rules)
    recording_food_penalty = 0
    for field, penalty in recent_food_rules:
        present = _yes(recording.get(field))
        if field in recording:
            evidence["food_pattern"].append({"source": "recording_assessment", "field": field, "value": recording.get(field), "penalty": penalty if present else 0})
        if present:
            recording_food_penalty += penalty
    if recording_food_answered:
        evidence["food_pattern"].append({"source": "recording_assessment", "field": "reflux_symptom_context", "value": reflux_context, "included_in_score": False})
    recording_food = 100 - min(100, recording_food_penalty) if recording_food_answered else None

    baseline_food_items = _items(baseline.get("eatingHabits"))
    baseline_food = None
    if "eatingHabits" in baseline:
        baseline_penalty = 0
        baseline_rules = (
            ("Eat fried or fatty food regularly", 25),
            ("Eat at irregular times", 20),
            ("Eat then lie down within 3-4 hours regularly", 30),
            ("Eat spicy food regularly", 5),
        )
        for label, penalty in baseline_rules:
            present = label.casefold() in baseline_food_items
            if present:
                baseline_penalty += penalty
                evidence["food_pattern"].append({"source": "member_baseline", "field": "eatingHabits", "value": label, "penalty": penalty})
        for label in ("Drink soda regularly", "Drink coffee or caffeinated beverages regularly"):
            if label.casefold() in baseline_food_items:
                evidence["food_pattern"].append({"source": "member_baseline", "field": "eatingHabits", "value": label, "penalty": 0})
        baseline_food = 100 - min(100, baseline_penalty)

    recording_voice_items = _items(recording.get("regularVoiceUse"))
    baseline_voice_items = _items(baseline.get("regularVoiceUse"))
    voice_aliases = {
        "loud": ("speak loudly", "talk_loud"),
        "noisy": ("speak in noisy environments", "talk_in_loud_env"),
        "shout": ("shout or yell", "shout"),
        "continuous": ("speak continuously for long periods", "continuous"),
        "talk_much": ("talk a lot", "talk_much"),
        "mimic": ("mimic voices", "mimic"),
        "altered": ("cut off speech abruptly", "altered"),
        "whisper": ("whisper",),
        "tension": ("strain or tense neck while speaking", "tense", "tense_neck"),
        "cough": ("cough often", "cought_much"),
        "clear_throat": ("clear throat often", "clear_troat_much"),
    }

    def voice_score(items: set[str], minutes_value: Any | None, source: str) -> int | None:
        if not items and minutes_value is None:
            return None
        intensity = max(
            30 if _contains(items, *voice_aliases["shout"]) else 0,
            20 if _contains(items, *voice_aliases["loud"], *voice_aliases["noisy"]) else 0,
        )
        minutes = _number(minutes_value)
        duration = 0 if minutes is None or minutes <= 30 else 10 if minutes <= 60 else 20 if minutes <= 120 else 30
        sustained = min(35, duration + (15 if _contains(items, *voice_aliases["continuous"]) else 0) + (10 if _contains(items, *voice_aliases["talk_much"]) else 0))
        technique = min(20, (5 if _contains(items, *voice_aliases["mimic"]) else 0) + (10 if _contains(items, *voice_aliases["altered"]) else 0) + (10 if _contains(items, *voice_aliases["whisper"]) else 0) + (20 if _contains(items, *voice_aliases["tension"]) else 0))
        irritation = 15 if _contains(items, *voice_aliases["cough"], *voice_aliases["clear_throat"]) else 0
        evidence["voice_use"].extend([
            {"source": source, "field": "regularVoiceUse", "value": sorted(items)},
            {"source": source, "field": "continuousMinutes", "value": minutes, "included_in_score": minutes is not None},
            {"source": source, "field": "voice_load_components", "value": {"intensity": intensity, "sustained": sustained, "technique_or_tension": technique, "irritation": irritation}},
        ])
        return 100 - min(100, intensity + sustained + technique + irritation)

    recording_voice = voice_score(recording_voice_items, recording.get("continuousMinutes"), "recording_assessment") if ("regularVoiceUse" in recording or "continuousMinutes" in recording) else None
    baseline_daily_hours = None
    if "hoursVoiceHome" in baseline or "hoursVoiceWork" in baseline:
        home = _number(baseline.get("hoursVoiceHome")) or 0
        work = _number(baseline.get("hoursVoiceWork")) or 0
        baseline_daily_hours = home + work
    baseline_voice = voice_score(baseline_voice_items, None, "member_baseline") if "regularVoiceUse" in baseline else None
    if baseline_daily_hours is not None:
        daily_penalty = 0 if baseline_daily_hours <= 2 else 10 if baseline_daily_hours <= 4 else 20 if baseline_daily_hours <= 8 else 30
        baseline_voice = (100 if baseline_voice is None else baseline_voice) - daily_penalty
        evidence["voice_use"].append({
            "source": "member_baseline", "field": "hoursVoiceHome+hoursVoiceWork",
            "value": baseline_daily_hours, "penalty": daily_penalty,
        })

    slept = _number(recording.get("hoursSlept"))
    recording_recovery = None
    if "hoursSlept" in recording and slept is not None:
        recording_recovery = 100 if slept >= 7 else 75 if slept >= 6 else 50 if slept >= 5 else 25 if slept >= 4 else 0
        evidence["recovery"].append({"source": "recording_assessment", "field": "hoursSlept", "value": slept})

    recording_environment = _items(recording.get("environment"))
    recording_exposure_answered = any(field in recording for field in ("smoked", "alcohol", "environment"))
    recording_exposure_penalty = 0
    if _yes(recording.get("smoked")):
        recording_exposure_penalty += 70
    if _yes(recording.get("alcohol")):
        recording_exposure_penalty += 15
    if _contains(recording_environment, "dusty or polluted air", "poluted_env", "polluted_env"):
        recording_exposure_penalty += 25
    if recording_exposure_answered:
        evidence["exposure_avoidance"].extend([
            {"source": "recording_assessment", "field": "smoked", "value": recording.get("smoked"), "penalty": 70 if _yes(recording.get("smoked")) else 0},
            {"source": "recording_assessment", "field": "alcohol", "value": recording.get("alcohol"), "penalty": 15 if _yes(recording.get("alcohol")) else 0},
            {"source": "recording_assessment", "field": "environment", "value": sorted(recording_environment), "penalty": 25 if _contains(recording_environment, "dusty or polluted air", "poluted_env", "polluted_env") else 0},
        ])
    recording_exposure = 100 - min(100, recording_exposure_penalty) if recording_exposure_answered else None

    baseline_exposure_answered = any(field in baseline for field in ("smokingStatus", "alcoholStatus", "homeEnvironment", "workEnvironment"))
    baseline_exposure_penalty = 0
    smoking_status = str(baseline.get("smokingStatus", "")).casefold()
    alcohol_status = str(baseline.get("alcoholStatus", "")).casefold()
    baseline_environments = _items(baseline.get("homeEnvironment")) | _items(baseline.get("workEnvironment"))
    if smoking_status == "current":
        baseline_exposure_penalty += 70
    if alcohol_status == "yes":
        baseline_exposure_penalty += 15
    if _contains(baseline_environments, "dusty or polluted air", "poluted_env", "polluted_env"):
        baseline_exposure_penalty += 25
    if baseline_exposure_answered:
        evidence["exposure_avoidance"].extend([
            {"source": "member_baseline", "field": "smokingStatus", "value": baseline.get("smokingStatus"), "penalty": 70 if smoking_status == "current" else 0},
            {"source": "member_baseline", "field": "alcoholStatus", "value": baseline.get("alcoholStatus"), "penalty": 15 if alcohol_status == "yes" else 0},
            {"source": "member_baseline", "field": "home/workEnvironment", "value": sorted(baseline_environments), "penalty": 25 if _contains(baseline_environments, "dusty or polluted air", "poluted_env", "polluted_env") else 0},
        ])
    baseline_exposure = 100 - min(100, baseline_exposure_penalty) if baseline_exposure_answered else None

    return {
        "behavior_scoring_version": BEHAVIOR_SCORING_VERSION,
        "score_direction": "100 = more supportive reported behavior; 0 = more items needing attention",
        "clinical_interpretation": None,
        "categories": {
            "hydration": _score_record(recording_water, baseline_water, evidence["hydration"], ["Glass-count bands are product-policy heuristics.", "recentWater is context only."]),
            "food_pattern": _score_record(recording_food, baseline_food, evidence["food_pattern"], ["Food penalties rank review topics and do not estimate reflux risk.", "Caffeine alone has no penalty."]),
            "voice_use": _score_record(recording_voice, baseline_voice, evidence["voice_use"], ["Voice-load penalties are product-policy heuristics; no universal safe dose is claimed."]),
            "recovery": _score_record(recording_recovery, None, evidence["recovery"], ["The adult 7-hour reference is a general recovery heuristic, not an acoustic cause."]),
            "exposure_avoidance": _score_record(recording_exposure, baseline_exposure, evidence["exposure_avoidance"], ["Exposure penalties prioritize advice and are not disease probabilities."]),
        },
        "overall_behavior_score": None,
    }


def _fact(fact_id: str, source: str, field: str, value: Any, text_en: str, text_th: str, strength: int = 1) -> dict[str, Any]:
    return {"fact_id": fact_id, "source": source, "field": field, "value": value, "text": {"en": text_en, "th": text_th}, "strength": strength}


def _acoustic_quality(acoustic_analysis: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not acoustic_analysis:
        return {}
    quality = acoustic_analysis.get("quality")
    return quality if isinstance(quality, Mapping) else acoustic_analysis


def _acoustic_voice_context(acoustic_analysis: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    quality = _acoustic_quality(acoustic_analysis)
    facts = []
    stability = quality.get("stability")
    if isinstance(stability, Mapping):
        score = _number(stability.get("stability_score"))
        if score is not None and score < 50:
            facts.append(_fact("acoustic_stability_context", "acoustic_analysis", "stability.stability_score", score, f"acoustic stability score was {score:g}; this is context, not a cause", f"คะแนนเสถียรภาพจากเสียงเท่ากับ {score:g} ใช้เป็นบริบทและไม่สรุปสาเหตุ", 1))
    hoarseness = quality.get("hoarseness_risk")
    if isinstance(hoarseness, Mapping):
        score = _number(hoarseness.get("hoarseness_risk_score"))
        if score is not None and score >= 70:
            facts.append(_fact("acoustic_hoarseness_context", "acoustic_analysis", "hoarseness_risk.hoarseness_risk_score", score, f"acoustic hoarseness-risk score was {score:g}; this is context, not a cause", f"คะแนน acoustic hoarseness risk เท่ากับ {score:g} ใช้เป็นบริบทและไม่สรุปสาเหตุ", 1))
    return facts


def _priority(category: str, care_score: int | None, facts: list[dict[str, Any]], acoustic_bonus: bool = False) -> tuple[int, str, dict[str, int]]:
    severity = 0 if care_score is None else min(MAX_SEVERITY_POINTS, round((100 - care_score) * SEVERITY_WEIGHT))
    support = min(MAX_SUPPORT_POINTS, sum(int(fact.get("strength", 1)) for fact in facts if fact["source"] != "acoustic_analysis") * 2)
    sources = {fact["source"] for fact in facts}
    relevance = RECORDING_RELEVANCE_POINTS if "recording_assessment" in sources else (BASELINE_RELEVANCE_POINTS if "member_baseline" in sources else 0)
    corroboration = BASELINE_CORROBORATION_POINTS if {"recording_assessment", "member_baseline"} <= sources else 0
    acoustic = ACOUSTIC_CONTEXT_POINTS if acoustic_bonus else 0
    parts = {"category": CATEGORY_WEIGHTS[category], "severity": severity, "support": support, "source_relevance": relevance, "baseline_corroboration": corroboration, "acoustic_context": acoustic}
    score = min(100, sum(parts.values()))
    label = "high" if score >= 70 else "mid" if score >= 45 else "low"
    return score, label, parts


def _candidate(rule_id: str, category: str, care_score: int | None, facts: list[dict[str, Any]], action_ids: list[str], triggered_rule_ids: list[str] | None = None, acoustic_bonus: bool = False) -> dict[str, Any]:
    priority_score, priority, breakdown = _priority(category, care_score, facts, acoustic_bonus)
    return {
        "rule_id": rule_id,
        "triggered_rule_ids": triggered_rule_ids or [rule_id],
        "category": category,
        "care_score": care_score,
        "priority_score": priority_score,
        "priority": priority,
        "priority_breakdown": breakdown,
        "evidence": [{k: v for k, v in fact.items() if k not in {"text", "strength"}} for fact in facts],
        "reason_facts": [{"fact_id": fact["fact_id"], "text": fact["text"]} for fact in facts],
        "allowed_actions": [{"action_id": action_id, "text": ACTION_TEXT[action_id]} for action_id in action_ids],
    }


def generate_candidates(
    behavior_scores: Mapping[str, Any],
    member_baseline: Mapping[str, Any] | None,
    recording_assessment: Mapping[str, Any] | None,
    acoustic_analysis: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Generate deterministic, ranked, deduplicated recommendation candidates."""
    baseline = member_baseline or {}
    recording = recording_assessment or {}
    categories = behavior_scores["categories"]
    candidates: list[dict[str, Any]] = []

    recording_voice = _items(recording.get("regularVoiceUse"))
    baseline_voice = _items(baseline.get("regularVoiceUse"))
    recording_voice_available = "regularVoiceUse" in recording or "continuousMinutes" in recording
    source_voice = recording_voice if recording_voice_available else baseline_voice
    source_name = "recording_assessment" if recording_voice_available else "member_baseline"
    voice_facts: list[dict[str, Any]] = []
    triggers = []
    action_ids = []
    if _contains(source_voice, "Speak loudly", "talk_loud", "Speak in noisy environments", "talk_in_loud_env"):
        voice_facts.append(_fact("voice_loud", source_name, "regularVoiceUse", "loud_or_noisy", "spoke loudly or in a noisy environment", "พูดดังหรือพูดในสภาพแวดล้อมที่มีเสียงดัง", 2))
        triggers.append("reduce_vocal_load")
    if _contains(source_voice, "Shout or yell", "shout"):
        voice_facts.append(_fact("voice_shouting", source_name, "regularVoiceUse", "shouting", "shouted or yelled", "ตะโกนหรือใช้เสียงตะโกน", 3))
        triggers.append("reduce_shouting")
        action_ids.append("reduce_shouting")
    minutes = _number(recording.get("continuousMinutes"))
    baseline_daily_hours = None
    if source_name == "member_baseline":
        home = _number(baseline.get("hoursVoiceHome")) or 0
        work = _number(baseline.get("hoursVoiceWork")) or 0
        baseline_daily_hours = home + work if home or work else None
    prolonged_recording = source_name == "recording_assessment" and (
        _contains(source_voice, "Speak continuously for long periods", "continuous")
        or (minutes is not None and minutes > 30)
    )
    prolonged_baseline = source_name == "member_baseline" and (
        _contains(source_voice, "Speak continuously for long periods", "continuous")
        or (baseline_daily_hours is not None and baseline_daily_hours > 4)
    )
    if prolonged_recording or prolonged_baseline:
        if source_name == "recording_assessment":
            text_en = "reported prolonged continuous voice use" if minutes is None else f"reported approximately {minutes:g} minutes of continuous voice use"
            text_th = "รายงานการใช้เสียงต่อเนื่องเป็นเวลานาน" if minutes is None else f"รายงานการใช้เสียงต่อเนื่องประมาณ {minutes:g} นาที"
            field, value = "continuousMinutes", minutes
        else:
            text_en = "reported prolonged voice use as a usual behavior" if baseline_daily_hours is None else f"reported approximately {baseline_daily_hours:g} total hours of voice use per day"
            text_th = "รายงานการใช้เสียงต่อเนื่องเป็นพฤติกรรมประจำ" if baseline_daily_hours is None else f"รายงานการใช้เสียงรวมประมาณ {baseline_daily_hours:g} ชั่วโมงต่อวัน"
            field, value = "hoursVoiceHome+hoursVoiceWork", baseline_daily_hours
        voice_facts.append(_fact("voice_continuous", source_name, field, value, text_en, text_th, 3))
        triggers.append("take_voice_breaks")
        action_ids.extend(["take_voice_breaks", "avoid_prolonged_voice_use"])
    if _contains(source_voice, "Strain or tense neck while speaking", "tense", "tense_neck"):
        voice_facts.append(_fact("voice_tension", source_name, "regularVoiceUse", "neck_tension", "reported neck or throat tension during voice use", "รายงานความเกร็งบริเวณคอขณะใช้เสียง", 3))
        triggers.append("manage_voice_tension")
        action_ids.append("relax_neck")
    if voice_facts:
        acoustic_facts = _acoustic_voice_context(acoustic_analysis)
        all_facts = voice_facts + acoustic_facts
        distinct_triggers = list(dict.fromkeys(triggers))
        if len(distinct_triggers) > 1:
            rule_id = "reduce_vocal_load"
        elif distinct_triggers[0] in {"reduce_shouting", "manage_voice_tension", "take_voice_breaks"}:
            rule_id = distinct_triggers[0]
        else:
            rule_id = "reduce_vocal_load"
        if "take_voice_breaks" not in action_ids:
            action_ids.insert(0, "take_voice_breaks")
        candidates.append(_candidate(rule_id, "voice_use", categories["voice_use"]["care_score"], all_facts, list(dict.fromkeys(action_ids)), distinct_triggers, bool(acoustic_facts)))

    hydration = categories["hydration"]
    if hydration["care_score"] is not None and hydration["care_score"] < 70:
        primary = hydration["primary_source"]
        field = "glassesToday" if primary == "recording_assessment" else "glassesWaterPerDay"
        source_obj = recording if primary == "recording_assessment" else baseline
        value = source_obj.get(field)
        facts = [_fact("hydration_amount", primary, field, value, f"reported water amount was {value} glasses", f"รายงานปริมาณน้ำ {value} แก้ว", 2)]
        if "recentWater" in recording:
            facts.append(_fact("hydration_recent_context", "recording_assessment", "recentWater", recording.get("recentWater"), "recent water intake was recorded as context only", "บันทึกการดื่มน้ำก่อนอัดไว้เป็นบริบทเท่านั้น", 1))
        candidates.append(_candidate("support_hydration", "hydration", hydration["care_score"], facts, ["maintain_hydration"]))

    recovery = categories["recovery"]
    if recovery["care_score"] is not None and recovery["care_score"] < 70:
        value = recording.get("hoursSlept")
        facts = [_fact("recovery_sleep", "recording_assessment", "hoursSlept", value, f"reported {value} hours of sleep", f"รายงานการนอน {value} ชั่วโมง", 2)]
        candidates.append(_candidate("improve_recovery", "recovery", recovery["care_score"], facts, ["allow_recovery"]))

    recording_smoke = _yes(recording.get("smoked")) is True
    baseline_smoke = str(baseline.get("smokingStatus", "")).casefold() == "current"
    if recording_smoke or baseline_smoke:
        facts = []
        if recording_smoke:
            facts.append(_fact("smoked_recently", "recording_assessment", "smoked", True, "reported smoking within two hours before recording", "รายงานการสูบบุหรี่ภายในสองชั่วโมงก่อนอัด", 3))
        if baseline_smoke:
            facts.append(_fact("current_smoker", "member_baseline", "smokingStatus", "current", "reported current smoking as a usual behavior", "รายงานว่าสูบบุหรี่เป็นพฤติกรรมประจำ", 3))
        candidates.append(_candidate("reduce_smoke_exposure", "exposure_avoidance", categories["exposure_avoidance"]["care_score"], facts, ["avoid_smoking"]))

    recording_alcohol = _yes(recording.get("alcohol")) is True
    baseline_alcohol = str(baseline.get("alcoholStatus", "")).casefold() == "yes"
    if recording_alcohol or (not recording and baseline_alcohol):
        facts = []
        if recording_alcohol:
            facts.append(_fact("alcohol_recent", "recording_assessment", "alcohol", True, "reported alcohol within six hours before recording", "รายงานการดื่มแอลกอฮอล์ภายในหกชั่วโมงก่อนอัด", 2))
        if baseline_alcohol:
            facts.append(_fact("alcohol_usual", "member_baseline", "alcoholStatus", "yes", "reported alcohol use as a usual behavior", "รายงานการดื่มแอลกอฮอล์เป็นพฤติกรรมปกติ", 1))
        candidates.append(_candidate("reduce_alcohol_exposure", "exposure_avoidance", categories["exposure_avoidance"]["care_score"], facts, ["reduce_alcohol_near_voice_use"]))

    recording_env = _items(recording.get("environment"))
    baseline_env = _items(baseline.get("homeEnvironment")) | _items(baseline.get("workEnvironment"))
    recording_polluted = _contains(recording_env, "Dusty or polluted air", "poluted_env", "polluted_env")
    baseline_polluted = _contains(baseline_env, "Dusty or polluted air", "poluted_env", "polluted_env")
    if recording_polluted or (not recording and baseline_polluted):
        facts = []
        if recording_polluted:
            facts.append(_fact("polluted_air_recent", "recording_assessment", "environment", "polluted_air", "reported dusty or polluted air around the recording", "รายงานฝุ่นหรืออากาศปนเปื้อนในช่วงก่อนอัด", 2))
        if baseline_polluted:
            facts.append(_fact("polluted_air_usual", "member_baseline", "home/workEnvironment", "polluted_air", "reported dusty or polluted air in a usual environment", "รายงานฝุ่นหรืออากาศปนเปื้อนในสภาพแวดล้อมประจำ", 1))
        candidates.append(_candidate("reduce_polluted_air_exposure", "exposure_avoidance", categories["exposure_avoidance"]["care_score"], facts, ["reduce_polluted_air"]))

    food = categories["food_pattern"]
    if food["care_score"] is not None and food["care_score"] < 70:
        facts = []
        food_fields = {
            "friedFood": ("fried/fatty food was reported", "รายงานอาหารทอดหรืออาหารมัน"),
            "irregularMeal": ("irregular meal timing was reported", "รายงานเวลารับประทานไม่สม่ำเสมอ"),
            "spicyFood": ("spicy food was reported", "รายงานอาหารเผ็ด"),
            "soda": ("soda was reported", "รายงานการดื่มน้ำอัดลม"),
        }
        for field, (en, th) in food_fields.items():
            if _yes(recording.get(field)):
                facts.append(_fact(f"food_{field}", "recording_assessment", field, True, en, th, 1))
        if not facts:
            for item in _items(baseline.get("eatingHabits")):
                if item != "drink coffee or caffeinated beverages regularly":
                    facts.append(_fact(f"food_baseline_{len(facts)}", "member_baseline", "eatingHabits", item, f"usual eating pattern included {item}", f"รูปแบบการรับประทานประจำมีรายการ {item}", 1))
        reflux = max(_symptom(recording, "burning") or 0, _symptom(recording, "sour") or 0) >= 2
        if reflux:
            facts.append(_fact("food_reflux_context", "recording_assessment", "symptoms.burning_or_sour", True, "burning or sour-taste symptoms were also reported; this is context, not a diagnosis", "มีรายงานอาการแสบร้อนหรือรสเปรี้ยวร่วมด้วย ใช้เป็นบริบทและไม่ใช่การวินิจฉัย", 2))
        candidates.append(_candidate("adjust_food_pattern", "food_pattern", food["care_score"], facts, ["review_personal_food_triggers"], acoustic_bonus=reflux))

    return _deduplicate_and_rank(candidates)


def _deduplicate_and_rank(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_rule: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        rule_id = candidate["rule_id"]
        existing = by_rule.get(rule_id)
        if existing is None or candidate["priority_score"] > existing["priority_score"]:
            by_rule[rule_id] = candidate
    ranked = sorted(by_rule.values(), key=lambda item: (-item["priority_score"], item["rule_id"]))
    return ranked


def select_candidates(candidates: Sequence[Mapping[str, Any]], maximum: int = MAX_RECOMMENDATIONS) -> list[dict[str, Any]]:
    if maximum < 0:
        raise ValueError("maximum must be non-negative")
    selected = []
    seen_categories = set()
    for candidate in candidates:
        # Keep the first exposure rule even if several exposures coexist, so a
        # small top-N does not become three cards from one category.
        category = candidate["category"]
        if category in seen_categories:
            continue
        selected.append(copy.deepcopy(dict(candidate)))
        seen_categories.add(category)
        if len(selected) >= maximum:
            break
    return selected


def build_ai_wording_contract(selected_candidates: Sequence[Mapping[str, Any]], language: str = "th", maximum: int = MAX_RECOMMENDATIONS) -> dict[str, Any]:
    return {
        "contract_version": "recommendation-wording-contract-v0.1",
        "language": language,
        "maximum_recommendations": maximum,
        "instructions": [
            "Rewrite only the supplied candidates.",
            "Do not add, remove, reorder, or reprioritize candidates.",
            "Use only supplied reason_facts and allowed_actions.",
            "Do not diagnose, claim causation, or change any score.",
            "Return clinical_claim as null.",
        ],
        "immutable_fields": ["rule_id", "category", "priority"],
        "generated_fields": ["summary", "title", "reason", "action"],
        "required_grounding_fields": ["used_fact_ids", "action_ids"],
        "candidates": copy.deepcopy(list(selected_candidates)),
        "response_schema": {
            "summary": "string",
            "recommendations": [{
                "rule_id": "string", "category": "string", "priority": "high|mid|low",
                "title": "string", "reason": "string", "action": "string",
                "used_fact_ids": ["string"], "action_ids": ["string"],
            }],
            "clinical_claim": None,
        },
    }


_FORBIDDEN_CLAIMS = (
    "diagnosed", "diagnosis", "you have ", "caused your", "cause of your",
    "วินิจฉัย", "คุณเป็นโรค", "เป็นสาเหตุของ", "ทำให้เกิดโรค",
)

# Conservative claim markers catch common cross-candidate fabrication. They do
# not attempt medical NLP; an unrecognized or ambiguous response still falls
# back safely when other structural/value checks fail.
_FACT_CLAIM_MARKERS = {
    "voice_": ("shout", "yell", "loud", "tension", "continuous voice", "ตะโกน", "พูดดัง", "เกร็ง", "ใช้เสียงต่อเนื่อง"),
    "hydration_": ("water", "hydration", "น้ำ", "ดื่มน้ำ"),
    "recovery_": ("sleep", "recovery", "นอน", "พักฟื้น"),
    "smoke": ("smok", "cigarette", "บุหรี่", "ควัน"),
    "alcohol_": ("alcohol", "แอลกอฮอล์"),
    "polluted_": ("pollut", "dust", "ฝุ่น", "อากาศปนเปื้อน"),
    "food_": ("food", "meal", "fried", "spicy", "sour", "อาหาร", "มื้อ", "ทอด", "เผ็ด", "รสเปรี้ยว"),
}


def _text(value: Any, field: str, maximum_characters: int | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AIResponseValidationError(f"{field} must be a non-empty string")
    result = value.strip()
    if maximum_characters is not None and len(result) > maximum_characters:
        raise AIResponseValidationError(f"{field} exceeds {maximum_characters} characters")
    return result


def validate_ai_response(response: Any, selected_candidates: Sequence[Mapping[str, Any]], maximum: int = MAX_RECOMMENDATIONS) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise AIResponseValidationError("response must be an object")
    if set(response) != {"summary", "recommendations", "clinical_claim"}:
        raise AIResponseValidationError("response has missing or unknown top-level fields")
    if response["clinical_claim"] is not None:
        raise AIResponseValidationError("clinical_claim must be null")
    summary = _text(response["summary"], "summary", MAX_SUMMARY_CHARACTERS)
    recommendations = response["recommendations"]
    if not isinstance(recommendations, list):
        raise AIResponseValidationError("recommendations must be an array")
    expected = list(selected_candidates)
    if len(recommendations) > maximum or len(recommendations) != len(expected):
        raise AIResponseValidationError("recommendation count must exactly match deterministic selection")
    validated = []
    expected_keys = {"rule_id", "category", "priority", "title", "reason", "action", "used_fact_ids", "action_ids"}
    for index, (item, candidate) in enumerate(zip(recommendations, expected)):
        if not isinstance(item, Mapping) or set(item) != expected_keys:
            raise AIResponseValidationError(f"recommendation {index} has missing or unknown fields")
        for immutable in ("rule_id", "category", "priority"):
            if item[immutable] != candidate[immutable]:
                raise AIResponseValidationError(f"recommendation {index} changed {immutable}")
        title = _text(item["title"], f"recommendations[{index}].title", MAX_TITLE_CHARACTERS)
        reason = _text(item["reason"], f"recommendations[{index}].reason", MAX_REASON_CHARACTERS)
        action = _text(item["action"], f"recommendations[{index}].action", MAX_ACTION_CHARACTERS)
        combined = f"{summary} {title} {reason} {action}".casefold()
        if any(term in combined for term in _FORBIDDEN_CLAIMS):
            raise AIResponseValidationError("diagnostic or causal wording is not allowed")
        allowed_facts = {fact["fact_id"]: fact for fact in candidate["reason_facts"]}
        used_fact_ids = item["used_fact_ids"]
        if not isinstance(used_fact_ids, list) or not used_fact_ids or not set(used_fact_ids) <= set(allowed_facts):
            raise AIResponseValidationError("used_fact_ids must reference only supplied facts")
        reason_folded = reason.casefold()
        for fact_prefix, markers in _FACT_CLAIM_MARKERS.items():
            if any(marker in reason_folded for marker in markers):
                if not any(fact_prefix in fact_id for fact_id in used_fact_ids):
                    raise AIResponseValidationError("reason contains a fact type absent from used_fact_ids")
        allowed_actions = {entry["action_id"] for entry in candidate["allowed_actions"]}
        action_ids = item["action_ids"]
        if not isinstance(action_ids, list) or not action_ids or not set(action_ids) <= allowed_actions:
            raise AIResponseValidationError("action_ids must reference only supplied actions")
        allowed_numbers = set()
        for fact_id in used_fact_ids:
            fact_text = " ".join(allowed_facts[fact_id]["text"].values())
            allowed_numbers.update(re.findall(r"\d+(?:\.\d+)?", fact_text))
        stated_numbers = set(re.findall(r"\d+(?:\.\d+)?", reason))
        if not stated_numbers <= allowed_numbers:
            raise AIResponseValidationError("reason introduced a number absent from supplied facts")
        validated.append({
            "rule_id": item["rule_id"], "category": item["category"], "priority": item["priority"],
            "title": title, "reason": reason, "action": action,
            "used_fact_ids": list(used_fact_ids), "action_ids": list(action_ids),
        })
    return {"summary": summary, "recommendations": validated, "clinical_claim": None}


def deterministic_fallback(selected_candidates: Sequence[Mapping[str, Any]], language: str = "th") -> dict[str, Any]:
    locale = language if language in {"th", "en"} else "en"
    if not selected_candidates:
        summary = "จากข้อมูลที่มี ยังไม่มีหัวข้อพฤติกรรมที่ต้องจัดลำดับเป็นคำเตือน" if locale == "th" else "The available answers did not produce a prioritized behavior warning."
        return {"summary": _short_text(summary, MAX_SUMMARY_CHARACTERS), "recommendations": [], "clinical_claim": None}
    first_category = selected_candidates[0]["category"]
    summary = (f"หมวด {first_category} เป็นหัวข้อที่ควรใส่ใจก่อนจากข้อมูลที่รายงาน" if locale == "th" else f"The {first_category} category is the first behavior topic to review based on the reported information.")
    recommendations = []
    for candidate in selected_candidates:
        title, action = FALLBACK_TEMPLATES[candidate["rule_id"]][locale]
        facts = candidate["reason_facts"]
        fact_texts = [fact["text"][locale] for fact in facts if not fact["fact_id"].startswith("acoustic_")]
        if not fact_texts:
            fact_texts = [fact["text"][locale] for fact in facts]
        reason = ("; ".join(fact_texts) if locale == "en" else " และ ".join(fact_texts))
        recommendations.append({
            "rule_id": candidate["rule_id"], "category": candidate["category"], "priority": candidate["priority"],
            "title": _short_text(title, MAX_TITLE_CHARACTERS),
            "reason": _short_text(reason, MAX_REASON_CHARACTERS),
            "action": _short_text(action, MAX_ACTION_CHARACTERS),
            "used_fact_ids": [fact["fact_id"] for fact in facts if not fact["fact_id"].startswith("acoustic_")] or [fact["fact_id"] for fact in facts],
            "action_ids": [entry["action_id"] for entry in candidate["allowed_actions"]],
        })
    return {"summary": _short_text(summary, MAX_SUMMARY_CHARACTERS), "recommendations": recommendations, "clinical_claim": None}


def _short_text(value: str, maximum_characters: int) -> str:
    """Keep fallback wording within the same concise display contract as AI text."""
    if len(value) <= maximum_characters:
        return value
    return value[: maximum_characters - 1].rstrip() + "…"


def build_recommendation(
    acoustic_analysis: Mapping[str, Any] | None,
    member_baseline: Mapping[str, Any] | None,
    recording_assessment: Mapping[str, Any] | None,
    ai_worder: Callable[[dict[str, Any]], Any] | None = None,
    *,
    language: str = "th",
    maximum: int = MAX_RECOMMENDATIONS,
) -> dict[str, Any]:
    """Run scoring, candidate selection, optional wording, validation, fallback."""
    acoustic_before = copy.deepcopy(acoustic_analysis)
    scores = score_behaviors(member_baseline, recording_assessment)
    candidates = generate_candidates(scores, member_baseline, recording_assessment, acoustic_analysis)
    selected = select_candidates(candidates, maximum)
    contract = build_ai_wording_contract(selected, language, maximum)
    validation_error = None
    # Do not spend an AI request when deterministic scoring found nothing to
    # phrase. This is common for v1 analysis-only results and supportive forms.
    if not selected:
        final = deterministic_fallback(selected, language)
        wording_source = "deterministic_fallback"
    elif ai_worder is None:
        final = deterministic_fallback(selected, language)
        wording_source = "deterministic_fallback"
    else:
        try:
            final = validate_ai_response(ai_worder(copy.deepcopy(contract)), selected, maximum)
            wording_source = "ai_validated"
        except Exception as error:  # provider failure and invalid output use the same safe fallback
            validation_error = f"{type(error).__name__}: {error}"
            final = deterministic_fallback(selected, language)
            wording_source = "deterministic_fallback"
    if acoustic_analysis != acoustic_before:
        raise RuntimeError("recommendation pipeline modified acoustic analysis")
    return {
        "behavior_scoring_version": BEHAVIOR_SCORING_VERSION,
        "recommendation_rule_version": RECOMMENDATION_RULE_VERSION,
        "behavior_scores": scores,
        "candidate_recommendations": candidates,
        "selected_candidates": selected,
        "llm_contract": contract,
        "final_recommendation": final,
        "wording_source": wording_source,
        "wording_validation_error": validation_error,
        "acoustic_result_modified": False,
    }
