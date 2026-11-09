import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

export const supabase = createClient(supabaseUrl, supabaseKey);

// Guest assessment requests are authorised by a short-lived bearer token
// checked by the recording_assessment RLS policy. Do not place this token in
// query strings or request bodies.
export function createGuestAssessmentClient(guestToken: string) {
  return createClient(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false,
    },
    global: { headers: { 'X-Guest-Token': guestToken } },
  });
}
