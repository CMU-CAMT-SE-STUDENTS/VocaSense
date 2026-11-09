<template>
  <div class="analysis-page">
    <div class="page-inner">
      <div class="content-card">
        <div class="brain-icon">
          <img src="@/assets/icons/Brain.png" alt="" class="brain-img" />
        </div>

        <h1 class="analysis-title">Updating Your Result</h1>
        <p class="analysis-subtitle">
          Combining your answers with your voice analysis to generate updated recommendations
        </p>

        <div class="steps-list">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="step-card"
            :class="{ active: step.status === 'active', done: step.status === 'done', error: step.status === 'error' }"
          >
            <div class="step-icon-wrap">
              <img :src="step.icon" alt="" class="step-icon" />
            </div>
            <span class="step-label">{{ step.label }}</span>
            <div class="step-bar-track">
              <div class="step-bar-fill" :style="{ width: step.progress + '%' }"></div>
            </div>
          </div>
        </div>

        <div v-if="updateError" class="analysis-result analysis-error">
          <span class="result-status">Couldn't Generate Recommendations</span>
          <span class="result-detail">{{ updateError }}</span>
          <div class="error-actions">
            <button class="retry-btn" type="button" @click="retry">Try Again</button>
            <button class="home-btn" type="button" @click="goHome">
              <svg viewBox="0 0 24 24" fill="none"><path d="M3 11l9-8 9 8M5 10v10a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              Back To Home
            </button>
          </div>
        </div>
      </div>
    </div>

    <p class="disclaimer">
      This platform provides preliminary voice health insights and does not replace professional medical diagnosis.
    </p>
  </div>
</template>

<script setup>
// UC-17: View Updated Recommendations (SRS-162 to SRS-173).
//
// The "Analyzing" step between "See my updated result" and the Result
// Dashboard. Answers were already saved by ImproveResultView; this page asks
// the backend to regenerate the recommendation for the current analysis
// (POST /api/analyses/{id}/recommendations/generate?regenerate=true), keeps
// the result for ResultView, and offers Try Again on failure without
// repeating the assessment.
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/utils/supabase'

import saveIcon from '@/assets/icons/check_mark.png'
import brainIcon from '@/assets/icons/Brain.png'
import searchIcon from '@/assets/icons/Search.png'

const router = useRouter()

const updateError = ref('')

const steps = ref([
  { label: 'Saving your answers',                    icon: saveIcon,  progress: 0, status: 'pending' },
  { label: 'Reviewing your voice analysis',           icon: brainIcon, progress: 0, status: 'pending' },
  { label: 'Generating updated recommendations',      icon: searchIcon, progress: 0, status: 'pending' },
])

const STEP_DURATIONS = [400, 500]
const UPDATED_REC_KEY = 'vocasense:updatedRecommendation'

function animateStep(step, duration) {
  return new Promise((resolve) => {
    step.status = 'active'
    step.progress = 0
    const start = performance.now()

    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration)
      step.progress = 100 * (1 - (1 - t) ** 3)
      if (t >= 1) {
        step.progress = 100
        step.status = 'done'
        resolve()
        return
      }
      requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  })
}

function activeGuestToken() {
  try {
    const guest = JSON.parse(sessionStorage.getItem('vocasense:guestAnalysisSession') || 'null')
    return guest?.token && Date.parse(guest.expiresAt) > Date.now() ? guest.token : null
  } catch {
    return null
  }
}

async function requestUpdatedRecommendations() {
  const analysisId = sessionStorage.getItem('vocasense:lastAnalysisId')
  if (!analysisId) throw new Error('No saved analysis was found. Please record a new voice sample.')

  const { data } = await supabase.auth.getSession()
  const headers = {}
  if (data.session?.access_token) headers.Authorization = `Bearer ${data.session.access_token}`
  else {
    const guestToken = activeGuestToken()
    if (!guestToken) throw new Error('Your guest session has expired. Please record a new voice sample.')
    headers['X-Guest-Token'] = guestToken
  }

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  let response
  try {
    response = await fetch(
      `${apiBaseUrl}/api/analyses/${analysisId}/recommendations/generate?regenerate=true&use_current_baseline=true`,
      { method: 'POST', headers }
    )
  } catch {
    throw new Error('Could not reach the recommendation service. Please try again.')
  }
  const payload = await response.json().catch(() => null)
  if (!response.ok || !Array.isArray(payload?.recommendations)) {
    throw new Error(payload?.detail || 'Could not update recommendations. Please try again.')
  }
  // TEMP DEBUG: remove once the recommendation output is verified.
  console.log('[recommendation:generate] response', JSON.parse(JSON.stringify(payload)))
  console.table((payload.recommendations || []).map((r) => ({ rule_id: r.rule_id, category: r.category, priority: r.priority, action: r.action })))
  try {
    sessionStorage.setItem(UPDATED_REC_KEY, JSON.stringify({ analysisId: String(analysisId), recommendations: payload.recommendations }))
  } catch { /* storage unavailable: ResultView falls back to local tips */ }
  return payload
}

async function run() {
  updateError.value = ''
  steps.value.forEach((s) => { s.status = 'pending'; s.progress = 0 })

  try {
    // Step 1: assessment/baseline answers are already persisted by
    // submitAssessment()/baselineNext() in ImproveResultView.vue before the
    // user ever reaches this page — this step just reflects that back
    // honestly rather than re-saving, so it resolves quickly by design.
    await animateStep(steps.value[0], STEP_DURATIONS[0])

    // Step 2: brief review of the stored analysis before generating.
    await animateStep(steps.value[1], STEP_DURATIONS[1])

    // Step 3: the real recommendation-generation call.
    steps.value[2].status = 'active'
    steps.value[2].progress = 10
    await requestUpdatedRecommendations()
    steps.value[2].progress = 100
    steps.value[2].status = 'done'

    setTimeout(() => router.push('/result'), 300)
  } catch (err) {
    const failedStep = steps.value.find((s) => s.status === 'active')
    if (failedStep) failedStep.status = 'error'
    updateError.value = err?.message || 'Something went wrong. Please try again.'
  }
}

function retry() {
  run()
}

const goHome = () => router.push('/')

onMounted(run)
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

.analysis-page {
  height: 100vh;
  background: linear-gradient(180deg, #eef2ff 0%, #e8eeff 50%, #eff3ff 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-family: 'Poppins', sans-serif;
  overflow-x: hidden;
}

.page-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  width: 100%;
  box-sizing: border-box;
}

.content-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #fff;
  border-radius: 24px;
  padding: 36px 32px 32px;
  box-shadow: 0 4px 24px rgba(101, 148, 228, 0.12);
  width: 100%;
  max-width: 640px;
  box-sizing: border-box;
}

.brain-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(137deg, #6594e4 6.18%, #95b9f7 94.01%);
  box-shadow: 0 4px 16px rgba(101, 148, 228, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.brain-img {
  width: 38px;
  height: 38px;
  object-fit: contain;
  filter: brightness(0) invert(1);
}

.analysis-title {
  font-size: 26px;
  font-weight: 700;
  background: var(--header-1, linear-gradient(90deg, #75A5F7 0%, #6594E4 100%));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 0 10px;
  text-align: center;
}

.analysis-subtitle {
  font-size: 13px;
  font-weight: 500;
  color: #666;
  text-align: center;
  margin: 0 0 28px;
}

.steps-list {
  width: 100%;
  max-width: 560px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.analysis-result {
  width: 100%;
  max-width: 560px;
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #f4f7ff;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
}

.result-status {
  font-size: 14px;
  font-weight: 700;
  color: #2d7c52;
}

.result-detail {
  font-size: 12px;
  font-weight: 500;
  color: #5b6680;
}

.analysis-error { background: #fff3f3; }
.analysis-error .result-status { color: #c83d3d; }

.error-actions {
  display: flex;
  gap: 10px;
  margin-top: 2px;
  flex-wrap: wrap;
  justify-content: center;
}

.retry-btn {
  border: none;
  background: linear-gradient(102deg, #95b9f7 8.63%, #6594e4 92.33%);
  color: #fff;
  border-radius: 14px;
  padding: 9px 22px;
  font-family: 'Poppins', sans-serif;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.2s ease, opacity 0.2s ease;
}
.retry-btn:hover {
  opacity: 0.95;
  box-shadow: 0 8px 20px rgba(101, 148, 228, 0.45);
  transform: translateY(-1px);
}

.home-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: 1px solid rgba(101, 148, 228, 0.35);
  background: #fff;
  color: #6594e4;
  border-radius: 14px;
  padding: 9px 20px;
  font-family: 'Poppins', sans-serif;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.2s ease, background 0.2s ease;
}
.home-btn svg { width: 15px; height: 15px; }
.home-btn:hover {
  background: #f4f7ff;
  box-shadow: 0 6px 16px rgba(101, 148, 228, 0.22);
  transform: translateY(-1px);
}

.step-card {
  background: #6D96DE;
  border-radius: 50px;
  padding: 11px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  opacity: 0;
  transition: opacity 0.5s ease;
}

.step-card.active,
.step-card.done,
.step-card.error {
  opacity: 1;
}

.step-card.error { background: #d65b5b; }

.step-icon-wrap {
  width: 34px;
  height: 34px;
  background: rgba(255,255,255,0.25);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-icon {
  width: 19px;
  height: 19px;
  object-fit: contain;
  filter: brightness(0) invert(1);
}

.step-label {
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  font-family: 'Poppins', sans-serif;
  white-space: nowrap;
  flex-shrink: 0;
}

/* Fixed, shorter width instead of flex:1 filling the rest of the row, with
   margin-left: auto pushing it flush to the card's right edge — so the gap
   between the label and the bar scales with how much room the label
   actually needs (long labels like "Generating updated recommendations"
   still keep clear space before the bar) instead of the bar's width
   fighting the label for space in a fixed-width slot. */
.step-bar-track {
  width: 190px;
  flex-shrink: 0;
  margin-left: auto;
  height: 9px;
  background: rgba(255,255,255,0.35);
  border-radius: 20px;
  overflow: hidden;
}

.step-bar-fill {
  height: 100%;
  background: #fff;
  border-radius: 20px;
  transition: width 0.12s ease-out;
}

.disclaimer {
  position: fixed;
  bottom: 14px;
  left: 0;
  right: 0;
  font-size: 13px;
  font-weight: 500;
  color: #aaa;
  text-align: center;
  padding: 0 16px;
}

@media (max-width: 600px) {
  .page-inner { padding: 16px; }
  .content-card { padding: 24px 16px 20px; }
  .analysis-title { font-size: 22px; }
  .analysis-subtitle { font-size: 12px; }
  .step-card { padding: 10px 14px; gap: 10px; }
  .step-label { font-size: 12px; }
  .step-bar-track { width: 110px; }
  .disclaimer { font-size: 11px; }
}

@media (max-width: 380px) {
  /* Even the shortest label plus a 70px bar can get tight on very narrow
     phones — let the label wrap to a second line here rather than
     shrinking the bar further or letting it overflow the pill. */
  .step-label { white-space: normal; }
}
</style>
