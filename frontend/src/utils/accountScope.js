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
export function syncAccountScope(userId) {
  try {
    const current = userId || 'guest'
    if (localStorage.getItem(LAST_ACCOUNT_KEY) !== current) {
      clearAccountScopedData()
      localStorage.setItem(LAST_ACCOUNT_KEY, current)
    }
  } catch {
    // Storage unavailable — nothing to sync.
  }
}
