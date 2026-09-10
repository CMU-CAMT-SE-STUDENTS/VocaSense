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
          <button class="retry-btn" type="button" @click="retry">Try Again</button>
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
// This page is the "Analyzing page" SRS-162 requires between clicking "See
// my updated result" and landing back on the Result Dashboard — it exists
// so the wait for a real recommendation-generation backend call has the
// same honest step-by-step feedback as the voice-analysis Analyzing page
// (AnalysisView.vue), instead of the generic "Loading your result..."
// spinner on ResultView.vue (which is only meant for the quick session
// check on a plain page visit, not a multi-step backend pipeline).
//
// The backend side of SRS-162/165/166/170 (send assessment + baseline +
// acoustic-analysis data to a recommendation generation service, get new
// recommendations back) does not exist yet — see the TODO in
// requestUpdatedRecommendations() below. Until it does, this simulates the
// pipeline with timed steps so the page (including its error/retry path,
// SRS-172/173) is testable end to end right now; swapping in the real call
// later should not require touching the step/error UI at all.
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import saveIcon from '@/assets/icons/check_mark.png'
import brainIcon from '@/assets/icons/Brain.png'
import searchIcon from '@/assets/icons/Search.png'

const router = useRouter()
const route = useRoute()

const updateError = ref('')

const steps = ref([
  { label: 'Saving your answers',                    icon: saveIcon,  progress: 0, status: 'pending' },
  { label: 'Reviewing your voice analysis',           icon: brainIcon, progress: 0, status: 'pending' },
  { label: 'Generating updated recommendations',      icon: searchIcon, progress: 0, status: 'pending' },
])

const STEP_DURATIONS = [500, 700, 900]

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

// TODO(backend): replace this stub with the real recommendation-generation
// call once the service exists. Expected shape per SRS-162/165/166:
//   POST /api/recommendations/update
//   body: { assessmentAnswers, baseline (if Member has one), voiceAnalysis }
//   -> { recommendations: [...], riskLevel: '...' }
// SRS-167 requires validating the response before storing/displaying it,
// and SRS-168/169 requires saving it to only the current voice analysis
// record — do that validation + save here, in place of the fake delay.
//
// `?simulateError=1` in the URL forces the rejection path below, so the
// error state and "Try Again" retry button (SRS-172/173) can be tested
// without a real backend being wired up yet.
function requestUpdatedRecommendations() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (route.query.simulateError === '1') {
        reject(new Error('Could not reach the recommendation service. Please try again.'))
      } else {
        resolve({ ok: true })
      }
    }, STEP_DURATIONS[2])
  })
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

    // Step 2: combine assessment + baseline + this recording's acoustic
    // analysis (SRS-164/165) — currently computed client-side in
    // ResultView.vue's `recommendations`, so there's nothing to await yet;
    // once that logic moves server-side this step should await the real
    // "gather inputs" call instead of animating on a timer.
    await animateStep(steps.value[1], STEP_DURATIONS[1])

    // Step 3: the actual recommendation-generation call (stubbed above).
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

.retry-btn {
  margin-top: 2px;
  border: none;
  background: linear-gradient(102deg, #95b9f7 8.63%, #6594e4 92.33%);
  color: #fff;
  border-radius: 14px;
  padding: 9px 22px;
  font-family: 'Poppins', sans-serif;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
}
.retry-btn:hover { opacity: 0.9; }

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
