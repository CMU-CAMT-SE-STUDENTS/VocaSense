<template>
  <div class="analysis-page">
    <div class="page-topbar">
      <button class="btn-back" @click="goBack">
        <span class="back-arrow">←</span> Back To Home
      </button>
    </div>

    <div class="page-inner">
      <div class="content-card">
        <div class="brain-icon">
          <img src="@/assets/icons/Brain.png" alt="" class="brain-img" />
        </div>

        <h1 class="analysis-title">Analyzing Your Voice</h1>
        <p class="analysis-subtitle">
          Analyzing your voice sample using acoustic analysis to detect vocal patterns and health indicators
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
        <div v-if="analysisError" class="analysis-result analysis-error">
          <span class="result-status">Analysis Failed</span>
          <span class="result-detail">{{ analysisError }}</span>
        </div>
      </div>
    </div>

    <p class="disclaimer">
      This platform provides preliminary voice health insights and does not replace professional medical diagnosis.
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import micIcon from '@/assets/icons/Microphone.png'
import brainIcon from '@/assets/icons/Brain.png'
import searchIcon from '@/assets/icons/Search.png'
import chartIcon from '@/assets/icons/Bar Chart.png'
import { takePendingVoiceAnalysisInput } from '@/utils/voiceAnalysisStore'

const router = useRouter()
const goBack = () => router.push('/')
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const analysisDone = ref(false)
const analysisError = ref('')
const analysisResult = ref(null)

const steps = ref([
  { key: 'feature_extraction',label: 'Processing audio signal',   icon: micIcon,    progress: 0, status: 'pending' },
  { key: 'analyze_quality',label: 'Analyzing voice quality', icon: brainIcon,  progress: 0, status: 'pending' },
  { label: 'Choosing recommendations',    icon: searchIcon, progress: 0, status: 'pending' },
  { label: 'Generating insights',       icon: chartIcon,  progress: 0, status: 'pending' },
])

const STEP_DURATIONS = [1000, 1000, 1000, 1000]

function runStep(index) {
  if (index >= steps.value.length) {
    router.push('/result')
    return
  }

  const step = steps.value[index]
  step.status = 'active'
  step.progress = 0

  const duration = STEP_DURATIONS[index]
  const startedAt = performance.now()

  const animate = (now) => {
    const elapsed = now - startedAt
    const ratio = Math.min(1, elapsed / duration)
    step.progress = 100 * (1 - (1 - ratio) ** 3)

    if (ratio >= 1) {
      step.progress = 100
      step.status = 'done'
      setTimeout(() => runStep(index + 1), 300)
      return
    }

    requestAnimationFrame(animate)
  }

  requestAnimationFrame(animate)
}

const rafMap = new Map()
function runProcessingStep(step, requestPromise) {
  if (!step) return

  step.status = 'active'
  step.progress = 5

  let finished = false
  let rafId = null
  const startedAt = performance.now()

  const animate = (now) => {
    if (finished) return
    if (step.status !== 'active') return

    const elapsed = now - startedAt

    const target = Math.min(
      94,
      8 + Math.log1p(elapsed / 220) * 20
    )

    step.progress += (target - step.progress) * 0.12

    rafId = requestAnimationFrame(animate)
    rafMap.set(step, rafId)
  }

  rafId = requestAnimationFrame(animate)
  rafMap.set(step, rafId)

  return requestPromise
    .then((result) => {
      finished = true

      const id = rafMap.get(step)
      if (id) cancelAnimationFrame(id)

      step.progress = 100
      step.status = 'done'

      return result
    })
    .catch((err) => {
      finished = true

      const id = rafMap.get(step)
      if (id) cancelAnimationFrame(id)

      step.status = 'error'
      analysisError.value = err?.message || 'Voice analysis API failed.'

      throw err
    })
}

function runStepOnce(step) {
  if (!step) return Promise.resolve()

  return new Promise((resolve) => {
    step.status = 'active'
    step.progress = 0

    const duration = STEP_DURATIONS[step.key] || 1500
    const start = performance.now()

    let rafId = null

    const animate = (now) => {
      if (step.status !== 'active') return

      const t = Math.min(1, (now - start) / duration)

      step.progress = 100 * (1 - (1 - t) ** 3)

      if (t >= 1) {
        step.progress = 100
        step.status = 'done'
        resolve()
        return
      }

      rafId = requestAnimationFrame(animate)
      rafMap.set(step, rafId)
    }

    rafId = requestAnimationFrame(animate)
    rafMap.set(step, rafId)
  })
}

async function analyzePendingRecording(input) {
  const formData = new FormData()
  formData.append('file', input.wavBlob, 'voice-sample.wav')

  const request = fetch(`${API_BASE_URL}/api/voice/analyze`, {
    method: 'POST',
    body: formData,
  }).then(r => r.json())
  const featureStep = steps.value.find(s => s.key === 'feature_extraction')
  const result = await runProcessingStep(featureStep,request)
  const apiSteps = result.steps
  if (apiSteps) {
    for (const step of steps.value) {
      const api = apiSteps[step.key]

      if (api?.status === 'done') {
        step.status = 'done'
        step.progress = 100
      }
    }
  }
  analysisResult.value = result
  sessionStorage.setItem('vocasense:lastVoiceAnalysis', JSON.stringify(result))
  sessionStorage.setItem('vocasense:lastVoiceAnalysisAt', new Date().toISOString())
  window.history.replaceState({ ...window.history.state, voiceAnalysis: result }, '')
  const nextStep = steps.value.find(s => s.key === 'analyze_quality')
  if (nextStep) {
    setTimeout(() => {
      runStep(1)
    }, 300)
  }
  console.log('[voice_analysis]', result)
}

function completeStepsFromStoredResult(result) {
  analysisResult.value = result
  steps.value.forEach((step) => {
    step.status = 'done'
    step.progress = 100
  })
  analysisDone.value = true
}

onMounted(async () => {
  const pendingInput = takePendingVoiceAnalysisInput()
  if (pendingInput?.wavBlob) {
    await analyzePendingRecording(pendingInput).catch(() => {})
    return
  }

  const stateResult = window.history.state?.voiceAnalysis
  const storedResult = sessionStorage.getItem('vocasense:lastVoiceAnalysis')
  try {
    analysisResult.value = stateResult || (storedResult ? JSON.parse(storedResult) : null)
  } catch {
    analysisResult.value = stateResult || null
  }

  if (analysisResult.value) {
    completeStepsFromStoredResult(analysisResult.value)
  } else {
    analysisError.value = 'No recording was found. Please record a new voice sample.'
    steps.value[0].status = 'error'
  }
})
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

.page-topbar {
  position: fixed;
  top: 24px;
  left: 24px;
  z-index: 10;
}

.btn-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  border: 1px solid rgba(101, 148, 228, 0.4);
  border-radius: 20px;
  background: white;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: #6594e4;
  cursor: pointer;
  transition: opacity 0.2s;
  white-space: nowrap;
}

.btn-back:hover { opacity: 0.75; }

.back-arrow {
  font-size: 15px;
  line-height: 1;
  transform: translateY(-1px);
  display: inline-block;
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
  gap: 4px;
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

.analysis-metrics {
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  text-align: left;
}

.analysis-metric {
  min-width: 0;
  padding: 8px 10px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid rgba(101, 148, 228, 0.16);
}

.metric-label,
.metric-value {
  display: block;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metric-label {
  margin-bottom: 2px;
  font-size: 10px;
  font-weight: 600;
  color: #8b96ad;
}

.metric-value {
  font-size: 12px;
  font-weight: 700;
  color: #2f4773;
}

.analysis-error {
  background: #fff3f3;
}

.analysis-error .result-status {
  color: #c83d3d;
}

.step-card {
  background: #6D96DE;
  border-radius: 50px;
  padding: 11px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  opacity: 0;
  transition: opacity 0.5s ease;
}

.step-card.active,
.step-card.done,
.step-card.error {
  opacity: 1;
}

.step-card.error {
  background: #d65b5b;
}

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
  width: 170px;
  flex-shrink: 0;
}

.step-bar-track {
  flex: 1;
  height: 9px;
  margin-left: 24px;
  margin-right: 6px;
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
  .content-card {
    padding: 24px 16px 20px;
  }
  .analysis-title { font-size: 22px; }
  .analysis-subtitle { font-size: 12px; }
  .step-card { padding: 10px 12px; gap: 8px; }
  .step-label { font-size: 12px; width: 148px; }
  .analysis-metrics { grid-template-columns: 1fr; }
  .disclaimer { font-size: 11px; }
}
</style>
