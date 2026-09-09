import { supabase } from './supabase'

// Anonymous (not-logged-in) visitors still get their voice analyses saved,
// grouped under a guest_session row instead of an account. This is the
// browser's local half of that: a random token that identifies "this
// browser" across visits, and the Supabase-assigned guest_session.id that
// analysis.guest_session_id actually points at.
const GUEST_TOKEN_KEY = 'vocasense:guestToken'
const GUEST_SESSION_ID_KEY = 'vocasense:guestSessionId'
const GUEST_SESSION_TTL_MS = 30 * 24 * 60 * 60 * 1000 // 30 days

function randomToken() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID()
  // Fallback for browsers without crypto.randomUUID (very old Safari, non-HTTPS)
  return 'guest-' + Math.random().toString(36).slice(2) + Date.now().toString(36)
}

// Returns the guest_session.id (uuid) for this browser, creating the row in
// Supabase the first time and reusing it (from localStorage) after that.
// Returns null if it couldn't be created/read — callers must treat guest
// persistence as best-effort, same as every other Supabase write in this app.
export async function getOrCreateGuestSessionId() {
  try {
    const cachedId = localStorage.getItem(GUEST_SESSION_ID_KEY)
    if (cachedId) return cachedId

    let token = localStorage.getItem(GUEST_TOKEN_KEY)
    if (!token) {
      token = randomToken()
      localStorage.setItem(GUEST_TOKEN_KEY, token)
    }

    const startedAt = new Date()
    const expiresAt = new Date(startedAt.getTime() + GUEST_SESSION_TTL_MS)

    const { data, error } = await supabase
      .from('guest_session')
      .insert({
        guest_token: token,
        started_at: startedAt.toISOString(),
        expires_at: expiresAt.toISOString(),
      })
      .select('id')
      .single()

    if (error) throw error

    localStorage.setItem(GUEST_SESSION_ID_KEY, data.id)
    return data.id
  } catch (err) {
    console.error('Failed to create guest session', err)
    return null
  }
}
