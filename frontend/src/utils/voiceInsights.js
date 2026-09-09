// Shared voice-quality display metadata and recommendation logic. Both the
// Result Dashboard (this session's fresh analysis) and History (past
// analyses loaded from Supabase) render the same score/condition shape, so
// they share this instead of drifting into two separately-maintained copies.

export const OVERALL_META = {
  healthy: { level: 'low', badge: 'No Vocal Strain Detected', subtitle: 'Your voice sounds healthy — keep up the good habits!' },
  moderate: { level: 'moderate', badge: 'Moderate Vocal Strain', subtitle: 'Your voice shows some strain. Try the tips below to help it recover.' },
  warning: { level: 'high', badge: 'Vocal Strain Detected', subtitle: "Your voice shows signs of strain. Try the tips below, and see a specialist if it doesn't improve." },
}

export const CLARITY_META = {
  clear: { value: 'Clear', level: 'low' },
  slightly_unclear: { value: 'Slightly Unclear', level: 'moderate' },
  unclear: { value: 'Unclear', level: 'high' },
}
export const STABILITY_META = {
  stable: { value: 'Stable', level: 'low' },
  slightly_unstable: { value: 'Slightly Unstable', level: 'moderate' },
  unstable: { value: 'Unstable', level: 'high' },
}
export const HOARSENESS_META = {
  low: { value: 'Low', level: 'low' },
  moderate: { value: 'Moderate', level: 'moderate' },
  high: { value: 'High', level: 'high' },
}

// Reconstructs the backend's "quality" response shape from a row of the
// `analysis` table, so the same code that reads a live backend response can
// also read a row fetched back from Supabase.
export function qualityFromAnalysisRow(row) {
  return {
    voice_quality: { voice_quality_score: row.voice_quality_score, voice_condition: row.voice_condition },
    hoarseness_risk: { hoarseness_risk_score: row.hoarseness_score, hoarseness_condition: row.hoarseness_condition },
    stability: { stability_score: row.stability_score, stability_condition: row.stability_condition },
    clarity: { clarity_score: row.clarity_score, clarity_condition: row.clarity_condition },
  }
}

export function buildMetrics(quality) {
  if (!quality) return []
  const clarity = CLARITY_META[quality.clarity.clarity_condition]
  const stability = STABILITY_META[quality.stability.stability_condition]
  const hoarseness = HOARSENESS_META[quality.hoarseness_risk.hoarseness_condition]
  return [
    { kind: 'clarity', label: 'Voice clarity', ...clarity },
    { kind: 'stability', label: 'Voice stability', ...stability },
    { kind: 'hoarseness', label: 'Voice hoarseness', ...hoarseness },
  ]
}

// Backend returns scores/conditions but no coaching copy, so recommendations
// are derived here from the acoustic conditions, plus that recording's own
// self-assessment answers and the member's baseline profile when available
// (either can be null/undefined — each only contributes tips when present).
export function buildRecommendations(quality, assessment, baseline) {
  if (!quality) return []
  const overall = quality.voice_quality.voice_condition
  const hoarse = quality.hoarseness_risk.hoarseness_condition
  const stability = quality.stability.stability_condition
  const clarity = quality.clarity.clarity_condition
  const items = []

  if (overall === 'healthy') {
    items.push({ kind: 'water', text: 'Keep drinking plenty of water throughout the day', priority: 'moderate' })
    items.push({ kind: 'warmup', text: 'Continue regular vocal warm-ups to stay in good shape', priority: 'moderate' })
  } else {
    if (hoarse === 'high' || overall === 'warning') {
      items.push({ kind: 'rest', text: 'Give your voice a rest for 2-3 hours', priority: 'high' })
      items.push({ kind: 'water', text: 'Drink at least 8 glasses of water daily', priority: 'high' })
    } else {
      items.push({ kind: 'water', text: 'Drink at least 8 glasses of water daily', priority: 'moderate' })
    }

    if (stability !== 'stable') {
      items.push({ kind: 'voice', text: 'Avoid shouting or speaking loudly', priority: 'moderate' })
    }

    if (clarity !== 'clear') {
      items.push({ kind: 'warmup', text: 'Practice vocal warm-up exercises', priority: 'moderate' })
    }
  }

  if (assessment) {
    const severityScores = assessment.symptoms ? Object.values(assessment.symptoms).filter((v) => v !== null) : []
    const maxSeverity = severityScores.length ? Math.max(...severityScores) : 0
    if (maxSeverity >= 4) {
      items.push({ kind: 'specialist', text: 'Your reported symptoms are severe — consider seeing a specialist if this continues', priority: 'high' })
    }

    const hoursSlept = Number(assessment.hoursSlept)
    if (assessment.hoursSlept !== '' && !Number.isNaN(hoursSlept) && hoursSlept < 6 && !items.some((i) => i.kind === 'sleep')) {
      items.push({ kind: 'sleep', text: 'You reported less sleep than usual — try to rest more before your next recording', priority: 'moderate' })
    }

    if (assessment.alcohol === 'yes' || assessment.smoked === 'yes') {
      items.push({ kind: 'rest', text: 'Avoid alcohol and smoking before recording — they can affect your voice', priority: 'moderate' })
    }

    const glassesToday = Number(assessment.glassesToday)
    if (assessment.glassesToday !== '' && !Number.isNaN(glassesToday) && glassesToday < 6 && !items.some((i) => i.kind === 'water')) {
      items.push({ kind: 'water', text: 'You reported drinking less water than recommended today — try to increase your intake', priority: 'moderate' })
    }

    const voiceUse = assessment.regularVoiceUse || []
    const environment = assessment.environment || []
    if (
      (voiceUse.includes('Shout or yell') || voiceUse.includes('Speak loudly') || environment.includes('Noisy')) &&
      !items.some((i) => i.kind === 'voice')
    ) {
      items.push({ kind: 'voice', text: 'You reported shouting, speaking loudly, or a noisy environment — try to lower your volume', priority: 'moderate' })
    }
  }

  if (baseline) {
    if (baseline.smokingStatus === 'current' || baseline.alcoholStatus === 'yes') {
      items.push({ kind: 'rest', text: 'Your baseline shows regular smoking or alcohol use — both are long-term risk factors for vocal health', priority: 'moderate' })
    }

    const hoursVoiceHome = Number(baseline.hoursVoiceHome)
    const hoursVoiceWork = Number(baseline.hoursVoiceWork)
    const totalDailyVoiceHours = (Number.isNaN(hoursVoiceHome) ? 0 : hoursVoiceHome) + (Number.isNaN(hoursVoiceWork) ? 0 : hoursVoiceWork)
    if (totalDailyVoiceHours >= 6) {
      items.push({ kind: 'warmup', text: 'Your baseline shows heavy daily voice use — take short vocal breaks throughout the day', priority: 'moderate' })
    }

    const baselineVoiceUse = baseline.regularVoiceUse || []
    const baselineEnvironment = [...(baseline.homeEnvironment || []), ...(baseline.workEnvironment || [])]
    if (
      (baselineVoiceUse.includes('Shout or yell') || baselineVoiceUse.includes('Speak loudly') || baselineEnvironment.includes('Noisy')) &&
      !items.some((i) => i.kind === 'voice')
    ) {
      items.push({ kind: 'voice', text: 'Your baseline shows frequent loud speaking or noisy environments — these add up to long-term vocal strain', priority: 'moderate' })
    }
  }

  return items.slice(0, 6)
}
