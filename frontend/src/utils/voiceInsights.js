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

// Backend recommendation items ({ rule_id, category, priority, title, reason,
// action }) -> the { kind, text, priority } shape the dashboard, history and
// export render. Returns null when there is nothing usable, so callers can say that
// recommendations are not available.
const REC_KIND_BY_CATEGORY = {
  voice_use: 'voice',
  exposure_avoidance: 'substance',
  hydration: 'water',
  recovery: 'rest',
  food_pattern: 'water'
}
export function backendRecommendationItems(list) {
  if (!Array.isArray(list)) return null
  const items = list
    .filter((r) => r && (r.action || r.title))
    .map((r) => ({
      kind: REC_KIND_BY_CATEGORY[r.category] || 'voice',
      text: r.action || r.title,
      priority: r.priority === 'high' ? 'high' : 'moderate'
    }))
  return items.length ? items : null
}
