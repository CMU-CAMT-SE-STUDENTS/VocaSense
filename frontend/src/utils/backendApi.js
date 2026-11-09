import { supabase } from './supabase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function backendApi(path) {
  const { data } = await supabase.auth.getSession()
  const accessToken = data.session?.access_token
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
  })
  const value = await response.json().catch(() => null)
  if (!response.ok) throw new Error(value?.detail || 'The request could not be completed.')
  return value
}
