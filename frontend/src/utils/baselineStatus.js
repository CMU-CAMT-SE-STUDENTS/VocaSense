import { ref } from 'vue'
import { supabase } from './supabase'

// Shared module state (not per-component) so the navbar's "baseline not set"
// dot updates the instant the wizard saves, regardless of which component
// triggered the save or whether a route change happens right after. A
// component-local copy of this (re-fetched on its own mount/route-change)
// was prone to racing the save itself — this is the single source of truth.
export const hasBaseline = ref(false)

export async function refreshBaselineStatus(userId) {
  if (!userId) {
    hasBaseline.value = false
    return
  }
  try {
    const { data, error } = await supabase
      .from('member_baseline')
      .select('user_id')
      .eq('user_id', userId)
      .maybeSingle()
    if (error) {
      console.error('Failed to check baseline status', error)
      return
    }
    hasBaseline.value = !!data
  } catch (err) {
    console.error('Failed to check baseline status', err)
  }
}
