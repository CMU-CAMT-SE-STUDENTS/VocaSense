import { supabase } from './supabase'
import { getOrCreateGuestSessionId } from './guestSession'

// Bump these when feature extraction or the scoring formulas change, so old
// rows in `analysis` stay interpretable against the version that produced them.
const FEATURE_VERSION = '1.0'
const SCORING_VERSION = '1.0'

// Persists one completed voice analysis (the backend's /api/voice/analyze
// response) as a row in Supabase's `analysis` table, under whichever account
// is signed in — or under an anonymous guest_session otherwise. Returns the
// new row's id (used to link the "About This Recording" assessment to it),
// or null if the save failed. Saving is best-effort: a failure here must
// never block the member from seeing their result, which is already shown
// straight from the backend response.
export async function saveAnalysisResult(result) {
  const quality = result?.quality
  if (!quality) return null

  try {
    const { data: sessionData } = await supabase.auth.getSession()
    const userId = sessionData.session?.user?.id ?? null

    const row = {
      voice_quality_score: quality.voice_quality.voice_quality_score,
      voice_condition: quality.voice_quality.voice_condition,
      hoarseness_score: quality.hoarseness_risk.hoarseness_risk_score,
      hoarseness_condition: quality.hoarseness_risk.hoarseness_condition,
      stability_score: quality.stability.stability_score,
      stability_condition: quality.stability.stability_condition,
      clarity_score: quality.clarity.clarity_score,
      clarity_condition: quality.clarity.clarity_condition,
      features: result.features ?? {},
      feature_version: FEATURE_VERSION,
      scoring_version: SCORING_VERSION,
    }

    if (userId) {
      row.user_id = userId
    } else {
      const guestSessionId = await getOrCreateGuestSessionId()
      if (guestSessionId) row.guest_session_id = guestSessionId
    }

    const { data, error } = await supabase.from('analysis').insert(row).select('id').single()
    if (error) throw error

    return data.id
  } catch (err) {
    console.error('Failed to save analysis result to Supabase', err)
    return null
  }
}
