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
            :class="{ active: step.status === 'active', done: step.status === 'done' }"
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

const router = useRouter()
const goBack = () => router.push('/')

const steps = ref([
  { label: 'Processing audio signal',   icon: micIcon,    progress: 0, status: 'pending' },
  { label: 'Analyzing pitch stability', icon: brainIcon,  progress: 0, status: 'pending' },
  { label: 'Detecting vocal strain',    icon: searchIcon, progress: 0, status: 'pending' },
  { label: 'Generating insights',       icon: chartIcon,  progress: 0, status: 'pending' },
])

const STEP_DURATIONS = [1600, 2000, 2000, 1800]

function runStep(index) {
  if (index >= steps.value.length) {
    setTimeout(() => {
      // TODO: navigate to result-dashboard when ready
      router.push('/')
    }, 700)
    return
  }

  const step = steps.value[index]
  step.status = 'active'
  step.progress = 0

  const duration = STEP_DURATIONS[index]
  const interval = 30
  const increment = (interval / duration) * 100

  const timer = setInterval(() => {
    step.progress = Math.min(100, step.progress + increment)
    if (step.progress >= 100) {
      step.progress = 100
      step.status = 'done'
      clearInterval(timer)
      setTimeout(() => runStep(index + 1), 300)
    }
  }, interval)
}

onMounted(() => {
  setTimeout(() => runStep(0), 500)
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
}

.content-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #fff;
  border-radius: 24px;
  padding: 36px 32px 32px;
  box-shadow: 0 4px 24px rgba(101, 148, 228, 0.12);
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
  white-space: nowrap;
}

.steps-list {
  width: 560px;
  display: flex;
  flex-direction: column;
  gap: 12px;
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
.step-card.done {
  opacity: 1;
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
  width: 160px;
  flex-shrink: 0;
}

.step-bar-track {
  flex: 1;
  height: 13px;
  background: rgba(255,255,255,0.35);
  border-radius: 20px;
  overflow: hidden;
}

.step-bar-fill {
  height: 100%;
  background: #fff;
  border-radius: 20px;
  transition: width 0.03s linear;
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
  white-space: nowrap;
}

@media (max-width: 600px) {
  .page-inner { padding: 20px 24px; }
  .content-card {
    background: #fff;
    border-radius: 24px;
    padding: 28px 20px 24px;
    box-shadow: 0 4px 24px rgba(101, 148, 228, 0.12);
  }
  .analysis-subtitle { white-space: normal; font-size: 12px; }
  .step-label { width: 160px; }
  .disclaimer { white-space: normal; font-size: 11px; }
}
</style>
