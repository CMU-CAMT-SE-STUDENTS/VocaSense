// Local caches (baseline/assessment answers, the last voice analysis result)
// are only trustworthy for whichever account left them behind. A different
// account signing in on the same browser — or signing back out to guest —
// must never see what the previous account cached. This tracks who last
// left data behind and wipes it the moment that changes, so nothing lingers
// longer than the session it belongs to.
const LAST_ACCOUNT_KEY = 'vocasense:lastLocalAccount'

export function clearAccountScopedData() {
  try {
    localStorage.removeItem('vocasense:baselineAnswers')
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i)
      if (key && key.startsWith('vocasense:assessmentAnswers:')) localStorage.removeItem(key)
    }
    sessionStorage.removeItem('vocasense:lastVoiceAnalysis')
    sessionStorage.removeItem('vocasense:lastVoiceAnalysisAt')
  } catch {
    // Storage unavailable (e.g. private mode) — nothing to clear.
  }
}

// Call once per page load, right after resolving the current session's
// user id (pass null/undefined for guest). If the account differs from
// whoever last left data behind on this browser, wipes it before anything
// on the page gets a chance to read it.
//
// The very first call ever on a browser (nothing recorded yet, `last` is
// null) must NOT wipe — there's no previous account to protect against yet,
// and a guest's own recording/result from moments earlier in this same
// session would otherwise get deleted the instant this runs, before the
// user ever gets to see it (e.g. straight after finishing a voice test,
// wiped on the very next page that happens to call this). Only an actual
// change between two *recorded* values counts as a real account switch.
export function syncAccountScope(userId) {
  try {
    const current = userId || 'guest'
    const last = localStorage.getItem(LAST_ACCOUNT_KEY)
    if (last !== null && last !== current) {
      clearAccountScopedData()
    }
    localStorage.setItem(LAST_ACCOUNT_KEY, current)
  } catch {
    // Storage unavailable — nothing to sync.
  }
}
