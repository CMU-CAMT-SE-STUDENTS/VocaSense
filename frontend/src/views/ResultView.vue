<template>
  <div class="result-page">
    <div class="page-inner" v-if="quality">
      <div class="topbar">
        <button class="btn-back" @click="router.push('/')">
          <span class="back-arrow">&larr;</span> Back To Home
        </button>

        <div class="topbar-center">
          <div class="topbar-badge">
            <img src="@/assets/icons/Sparkles_1.png" alt="" class="glyph-img" />
          </div>
          <div>
            <h1 class="topbar-title">Voice Analysis Complete</h1>
            <p class="topbar-date">{{ formattedDate }}</p>
          </div>
        </div>

        <div class="topbar-actions">
          <button class="btn-ghost" type="button" @click="shareResult">
            <svg viewBox="0 0 24 24" fill="none"><path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7M16 6l-4-4-4 4M12 2v14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            Share
          </button>
          <button class="btn-ghost" type="button" @click="exportResult">
            <svg viewBox="0 0 24 24" fill="none"><path d="M12 3v12m0 0 4-4m-4 4-4-4M5 21h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            Export
          </button>
        </div>
      </div>

      <div class="disclaimer-banner">
        <svg viewBox="0 0 24 24" fill="none" class="disclaimer-icon"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/><path d="M12 11v5m0-8h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        <p><strong>Medical Disclaimer:</strong> This platform provides preliminary voice health insights and does not replace professional medical diagnosis. Please consult a healthcare professional for medical concerns.</p>
      </div>

      <section class="status-card">
        <div class="status-icon" :class="overallMeta.level === 'low' ? 'status-icon-healthy' : 'risk-bg-' + overallMeta.level">
          <StatusIcon :level="overallMeta.level" />
        </div>
        <span class="status-badge" :class="'risk-bg-' + overallMeta.level + ' risk-text-' + overallMeta.level">{{ overallMeta.badge }}</span>
        <h2 class="status-title">Your Voice Health Status</h2>
        <p class="status-subtitle">{{ overallMeta.subtitle }}</p>
        <div class="status-actions">
          <button class="btn-outline btn-outline-primary" type="button" @click="router.push('/recording')">
            <svg viewBox="0 0 24 24" fill="none"><path d="M4 4v5h5M20 20v-5h-5M4.6 15a8 8 0 0 0 14.8 1.5M19.4 9A8 8 0 0 0 4.6 7.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            Take Another Test
          </button>
          <button class="btn-outline" type="button" @click="router.push('/')">
            <svg viewBox="0 0 24 24" fill="none"><path d="M3 11l9-8 9 8M5 10v10a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            Back To Home
          </button>
        </div>
      </section>

      <section class="metric-grid">
        <div v-for="metric in metrics" :key="metric.kind" class="metric-card" :class="'metric-bg-' + metric.level">
          <div class="metric-card-top">
            <div class="metric-icon-square" :class="'metric-icon-' + metric.level">
              <MetricIcon :kind="metric.kind" />
            </div>
            <div class="info-wrap" v-click-outside="() => closeInfoIfOpen(metric.kind)">
              <button type="button" class="metric-info" @click="toggleInfo(metric.kind)" :aria-label="'About ' + metric.label">
                <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.6"/><path d="M12 11v5m0-8h.01" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
              </button>

              <div v-if="openInfo === metric.kind" class="info-popover">
                <div class="info-popover-head">
                  <div class="info-popover-icon" :class="'brand-icon-' + metric.kind">
                    <MetricIcon :kind="metric.kind" />
                  </div>
                  <div>
                    <strong>{{ metric.label }}</strong>
                    <span>{{ METRIC_INFO[metric.kind].description }}</span>
                  </div>
                </div>
                <div class="info-popover-levels">
                  <div v-for="lvl in METRIC_INFO[metric.kind].levels" :key="lvl.label" class="info-level-row">
                    <span class="info-level-dot" :class="'risk-dot-' + lvl.level"></span>
                    <span class="info-level-label" :class="'risk-text-' + lvl.level">{{ lvl.label }}</span>
                    <span class="info-level-desc">{{ lvl.desc }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <span class="metric-name">{{ metric.label }}</span>
          <strong class="metric-value" :class="'risk-text-' + metric.level">{{ metric.value }}</strong>
        </div>
      </section>

      <section class="bottom-grid">
        <div class="card rec-card">
          <div class="rec-card-head">
            <div class="rec-card-icon">
              <img src="@/assets/icons/check_mark.png" alt="" class="glyph-img" />
            </div>
            <div>
              <h3 class="card-title">Personalized Recommendations</h3>
              <p class="card-subtitle">Follow these tips to improve your vocal health</p>
            </div>
          </div>
          <div class="rec-list">
            <div v-for="rec in recommendations" :key="rec.text" class="rec-item" :class="'priority-bg-' + rec.priority">
              <span class="rec-icon" :class="'priority-icon-' + rec.priority">
                <RecommendationIcon :kind="rec.kind" />
              </span>
              <span class="rec-text-col">
                <span class="rec-text">{{ rec.text }}</span>
                <span class="rec-priority" :class="'priority-text-' + rec.priority">
                  <span class="priority-dot" :class="'priority-dot-' + rec.priority"></span>
                  {{ rec.priority === 'high' ? 'High' : 'Moderate' }} Priority
                </span>
              </span>
            </div>
          </div>
        </div>

        <div class="side-cards">
          <button class="card improve-card" type="button" @click="router.push('/improve-result')">
            <div class="improve-icon">
              <img src="@/assets/icons/test_passed.png" alt="" class="glyph-img" />
            </div>
            <span class="improve-text">
              <strong>Improve this result</strong>
              <span>{{ improveLabel }}</span>
            </span>
            <svg viewBox="0 0 24 24" fill="none" class="improve-chevron"><path d="m9 6 6 6-6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </button>

          <div class="card progress-card">
            <div class="progress-icon">
              <img src="@/assets/icons/research.png" alt="" class="glyph-img" />
            </div>
            <strong class="progress-title">Track Your Progress</strong>
            <p class="progress-desc">Create a free account to save your test results, view history, and monitor your voice health over time.</p>
            <button class="btn-primary" type="button" @click="router.push('/signup')">Create Account</button>
            <button class="link-underline" type="button" @click="router.push('/login')">Already have an account? Log in</button>
          </div>
        </div>
      </section>
    </div>

    <div class="page-inner empty-state" v-else>
      <p>No recent voice analysis was found.</p>
      <button class="btn-primary" type="button" @click="router.push('/recording')">Take a Voice Test</button>
    </div>

    <transition name="toast">
      <div v-if="toastMessage" class="toast">{{ toastMessage }}</div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/utils/supabase'
import AudioWaveIcon from '@/assets/icons/audio_wave.png'
import AudioIcon from '@/assets/icons/audio.png'
import WaterIcon from '@/assets/icons/water.png'
import MicrophoneIcon from '@/assets/icons/Microphone.png'
import SleepingBedIcon from '@/assets/icons/sleeping_bed.png'
import CheckMarkIcon from '@/assets/icons/check_mark.png'
import SparklesIcon from '@/assets/icons/Sparkles_1.png'
import MuteIcon from '@/assets/icons/mute.png'

const router = useRouter()
const result = ref(null)
const toastMessage = ref('')
const isMember = ref(false)

onMounted(async () => {
  const stateResult = window.history.state?.voiceAnalysis
  const storedResult = sessionStorage.getItem('vocasense:lastVoiceAnalysis')
  try {
    result.value = stateResult || (storedResult ? JSON.parse(storedResult) : null)
  } catch {
    result.value = stateResult || null
  }

  const { data } = await supabase.auth.getSession()
  isMember.value = !!data.session?.user
})

const quality = computed(() => result.value?.quality || null)

const formattedDate = computed(() => {
  const iso = sessionStorage.getItem('vocasense:lastVoiceAnalysisAt')
  const date = iso ? new Date(iso) : new Date()
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) +
    ' · ' + date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
})

const improveLabel = computed(() =>
  isMember.value ? 'Two short forms · about 4 min' : '7 quick questions about this recording · 1 min'
)

// ── Condition → display copy ────────────────────────────────────────
const OVERALL_META = {
  healthy: { level: 'low', badge: 'No Vocal Strain Detected', subtitle: 'Your voice sounds healthy — keep up the good habits!' },
  moderate: { level: 'moderate', badge: 'Moderate Vocal Strain', subtitle: 'Your voice shows some strain. Try the tips below to help it recover.' },
  warning: { level: 'high', badge: 'Vocal Strain Detected', subtitle: "Your voice shows signs of strain. Try the tips below, and see a specialist if it doesn't improve." }
}

const CLARITY_META = {
  clear: { value: 'Clear', level: 'low' },
  slightly_unclear: { value: 'Slightly Unclear', level: 'moderate' },
  unclear: { value: 'Unclear', level: 'high' }
}
const STABILITY_META = {
  stable: { value: 'Stable', level: 'low' },
  slightly_unstable: { value: 'Slightly Unstable', level: 'moderate' },
  unstable: { value: 'Unstable', level: 'high' }
}
const HOARSENESS_META = {
  low: { value: 'Low', level: 'low' },
  moderate: { value: 'Moderate', level: 'moderate' },
  high: { value: 'High', level: 'high' }
}

// Legend content for each metric's info popover (opened via the ⓘ button).
const METRIC_INFO = {
  clarity: {
    description: 'How clear your voice sounds',
    levels: [
      { label: 'Clear', level: 'low', desc: 'Your voice sounds healthy' },
      { label: 'Slightly Unclear', level: 'moderate', desc: 'Your voice is starting to lose clarity' },
      { label: 'Unclear', level: 'high', desc: 'Your voice is getting worse' }
    ]
  },
  stability: {
    description: 'How consistent your voice is',
    levels: [
      { label: 'Stable', level: 'low', desc: 'Your voice sounds healthy' },
      { label: 'Slightly Unstable', level: 'moderate', desc: 'Your voice is starting to shake' },
      { label: 'Unstable', level: 'high', desc: 'Your voice is getting worse' }
    ]
  },
  hoarseness: {
    description: 'How raspy your voice sounds',
    levels: [
      { label: 'Low', level: 'low', desc: 'Your voice sounds healthy' },
      { label: 'Moderate', level: 'moderate', desc: 'Your voice is starting to sound raspy' },
      { label: 'High', level: 'high', desc: 'Your voice is getting worse' }
    ]
  }
}

const overallMeta = computed(() => OVERALL_META[quality.value?.voice_quality?.voice_condition] || OVERALL_META.moderate)

const metrics = computed(() => {
  if (!quality.value) return []
  const clarity = CLARITY_META[quality.value.clarity.clarity_condition]
  const stability = STABILITY_META[quality.value.stability.stability_condition]
  const hoarseness = HOARSENESS_META[quality.value.hoarseness_risk.hoarseness_condition]
  return [
    { kind: 'clarity', label: 'Voice clarity', ...clarity },
    { kind: 'stability', label: 'Voice stability', ...stability },
    { kind: 'hoarseness', label: 'Voice hoarseness', ...hoarseness }
  ]
})

const openInfo = ref(null) // metric kind currently showing its popover, or null
const toggleInfo = (kind) => { openInfo.value = openInfo.value === kind ? null : kind }
const closeInfoIfOpen = (kind) => { if (openInfo.value === kind) openInfo.value = null }

const vClickOutside = {
  mounted(el, binding) {
    el.clickOutsideEvent = (event) => {
      if (!(el === event.target || el.contains(event.target))) binding.value()
    }
    document.addEventListener('click', el.clickOutsideEvent)
  },
  unmounted(el) {
    document.removeEventListener('click', el.clickOutsideEvent)
  }
}

// Backend returns scores/conditions but no coaching copy, so recommendations
// are derived client-side from the same conditions shown in the metric cards.
const recommendations = computed(() => {
  if (!quality.value) return []
  const overall = quality.value.voice_quality.voice_condition
  const hoarse = quality.value.hoarseness_risk.hoarseness_condition
  const stability = quality.value.stability.stability_condition
  const clarity = quality.value.clarity.clarity_condition
  const items = []

  if (overall === 'healthy') {
    items.push({ kind: 'water', text: 'Keep drinking plenty of water throughout the day', priority: 'moderate' })
    items.push({ kind: 'warmup', text: 'Continue regular vocal warm-ups to stay in good shape', priority: 'moderate' })
    return items
  }

  if (hoarse === 'high' || overall === 'warning') {
    items.push({ kind: 'rest', text: 'Give your voice a rest for 2-3 hours', priority: 'high' })
    items.push({ kind: 'water', text: 'Drink at least 8 glasses of water daily', priority: 'high' })
    items.push({ kind: 'sleep', text: 'Get a full night of sleep to help your voice recover', priority: 'high' })
  } else {
    items.push({ kind: 'water', text: 'Drink at least 8 glasses of water daily', priority: 'moderate' })
  }

  if (stability !== 'stable') {
    items.push({ kind: 'voice', text: 'Avoid shouting or speaking loudly', priority: 'moderate' })
  }

  if (clarity !== 'clear') {
    items.push({ kind: 'warmup', text: 'Practice vocal warm-up exercises', priority: 'moderate' })
  }

  return items.slice(0, 4)
})

// ── Share / Export ──────────────────────────────────────────────────
function summaryText() {
  const lines = [
    'VocaSense — Voice Analysis Result',
    formattedDate.value,
    '',
    overallMeta.value.badge,
    ...metrics.value.map((m) => `${m.label}: ${m.value}`),
    '',
    'Recommendations:',
    ...recommendations.value.map((r) => `- ${r.text} (${r.priority === 'high' ? 'High' : 'Moderate'} Priority)`)
  ]
  return lines.join('\n')
}

function showToast(message) {
  toastMessage.value = message
  setTimeout(() => { toastMessage.value = '' }, 2200)
}

async function shareResult() {
  const text = summaryText()
  if (navigator.share) {
    try {
      await navigator.share({ title: 'VocaSense Voice Analysis', text })
      return
    } catch {
      // user cancelled or share failed — fall through to clipboard
    }
  }
  try {
    await navigator.clipboard.writeText(text)
    showToast('Result copied to clipboard')
  } catch {
    showToast('Could not copy result')
  }
}

function exportResult() {
  const blob = new Blob([summaryText()], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'vocasense-voice-analysis.txt'
  link.click()
  URL.revokeObjectURL(url)
}

// ── Icons ────────────────────────────────────────────────────────────
const StatusIcon = (props) => {
  if (props.level === 'high') {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none' }, [
      h('circle', { cx: '12', cy: '12', r: '9', stroke: 'currentColor', 'stroke-width': '2' }),
      h('path', { d: 'M12 8v5m0 3h.01', stroke: 'currentColor', 'stroke-width': '2.5', 'stroke-linecap': 'round' })
    ])
  }
  if (props.level === 'moderate') {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none' }, [
      h('path', { d: 'M12 9v4m0 4h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
    ])
  }
  return h('img', { src: CheckMarkIcon, alt: '', class: 'glyph-img' })
}

// Image glyphs on a gradient square: sparkle for clarity, waveform for
// stability, mute-mic for hoarseness.
const MetricIcon = (props) => {
  if (props.kind === 'clarity') {
    return h('img', { src: SparklesIcon, alt: '', class: 'glyph-img' })
  }
  if (props.kind === 'stability') {
    return h('img', { src: AudioWaveIcon, alt: '', class: 'glyph-img' })
  }
  return h('img', { src: MuteIcon, alt: '', class: 'glyph-img' })
}

// Recommendation icons recolor per priority (red for high, brown for
// moderate) via `currentColor`, so these stay inline SVG rather than fixed-
// color PNG assets, which would flatten that priority color-coding.
// water/voice/warmup/sleep use white-glyph image assets (per-kind, fixed
// asset regardless of priority) — the priority color-coding still comes
// through via the square's own background color (see .priority-icon-*),
// same pattern as the metric cards. "rest" has no matching asset yet, so it
// stays inline SVG.
const RecommendationIcon = (props) => {
  const images = { water: WaterIcon, voice: AudioIcon, warmup: MicrophoneIcon, sleep: SleepingBedIcon }
  if (images[props.kind]) {
    return h('img', { src: images[props.kind], alt: '', class: 'glyph-img' })
  }
  return h('svg', { viewBox: '0 0 24 24', fill: 'none' }, [
    h('path', { d: 'M12 7v5l3 3M12 3a9 9 0 1 0 9 9', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
  ])
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

* { box-sizing: border-box; }

.result-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #eef2ff 0%, #eff3ff 40%, #fafbff 100%);
  font-family: 'Poppins', sans-serif;
  padding: 28px 20px 64px;
}

.page-inner {
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.empty-state {
  align-items: center;
  text-align: center;
  gap: 16px;
  padding-top: 80px;
  color: #667085;
}

/* ── Top bar ── */
.topbar {
  position: sticky;
  top: 16px;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  background: #fff;
  border-radius: 20px;
  padding: 14px 20px;
  border: 1px solid rgba(101, 148, 228, 0.12);
  box-shadow: 0 2px 16px rgba(101, 148, 228, 0.08);
}

.btn-back {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 10px 20px;
  border: 1px solid rgba(101, 148, 228, 0.35);
  border-radius: 20px;
  background: #fff;
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  font-weight: 500;
  color: #6594e4;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-back:hover { opacity: 0.75; }

.back-arrow { font-size: 16px; }

.topbar-center {
  display: flex;
  align-items: center;
  gap: 10px;
}

.topbar-badge {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a5c4f7 0%, #6594e4 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.topbar-badge svg, .topbar-badge .glyph-img { width: 25px; height: 25px; object-fit: contain; }

.topbar-title {
  font-size: 15px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.topbar-date {
  font-size: 11.5px;
  font-weight: 500;
  color: #8b96ad;
  margin: 2px 0 0;
}

.topbar-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(101, 148, 228, 0.25);
  background: #fff;
  border-radius: 16px;
  padding: 8px 14px;
  font-family: 'Poppins', sans-serif;
  font-size: 12.5px;
  font-weight: 600;
  color: #6594e4;
  cursor: pointer;
}

.btn-ghost svg { width: 14px; height: 14px; }
.btn-ghost:hover { background: #f4f7ff; }

/* ── Disclaimer ── */
.disclaimer-banner {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  background: #d9e6fc;
  border: 1px solid rgba(101, 148, 228, 0.3);
  border-radius: 14px;
  padding: 12px 16px;
  color: #3d5a99;
  font-size: 12.5px;
  font-weight: 500;
  line-height: 1.6;
}

.disclaimer-icon { width: 18px; height: 18px; flex-shrink: 0; margin-top: 1px; }

/* ── Status card ── */
.status-card {
  background: #fff;
  border-radius: 20px;
  border: 1px solid rgba(101, 148, 228, 0.14);
  box-shadow: 0 2px 16px rgba(101, 148, 228, 0.08);
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
}

.status-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-icon svg, .status-icon .glyph-img { width: 26px; height: 26px; object-fit: contain; }

.status-icon-healthy { background: linear-gradient(135deg, #3fc987, #73d8a5, #a8e8c4); }

.status-badge {
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 11.5px;
  font-weight: 600;
}

.status-title {
  font-size: 21px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 4px 0 0;
}

.status-subtitle {
  font-size: 13px;
  font-weight: 600;
  color: #6b7590;
  max-width: 100%;
  white-space: nowrap;
  line-height: 1.6;
  margin: 0;
}

.status-actions {
  display: flex;
  gap: 12px;
  margin-top: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(101, 148, 228, 0.35);
  background: #fff;
  border-radius: 20px;
  padding: 10px 20px;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 600;
  color: #6594e4;
  cursor: pointer;
}

.btn-outline svg { width: 16px; height: 16px; }
.btn-outline:hover { background: #f4f7ff; }

.btn-outline-primary {
  border: none;
  background: linear-gradient(102deg, #95b9f7 8.63%, #6594e4 92.33%);
  color: #fff;
}
.btn-outline-primary:hover { background: linear-gradient(102deg, #95b9f7 8.63%, #6594e4 92.33%); opacity: 0.9; }

/* ── Risk tokens ── */
.risk-bg-low { background: #e3f7ec; color: #1f9d5b; }
.risk-bg-moderate { background: #fff3dc; color: #b7791f; }
.risk-bg-high { background: #fdeaea; color: #c83d3d; }
.risk-text-low { color: #1f9d5b; }
.risk-text-moderate { color: #b7791f; }
.risk-text-high { color: #c83d3d; }
.risk-dot-low { background: #22c55e; }
.risk-dot-moderate { background: #f5a623; }
.risk-dot-high { background: #ef4444; }

/* ── Metric grid ── */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.metric-card {
  border-radius: 18px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.metric-bg-low { background: linear-gradient(135deg, #ffffff 3%, #f1ffee 66%, #e0ffe0 100%); }
.metric-bg-moderate { background: linear-gradient(135deg, #ffffff 3%, #fffdf4 66%, #fff5e0 100%); }
.metric-bg-high { background: linear-gradient(135deg, #ffffff 3%, #fff4f4 66%, #ffe0e0 100%); }

.metric-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.metric-icon-square {
  width: 54px;
  height: 54px;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.metric-icon-square svg, .metric-icon-square .glyph-img { width: 30px; height: 30px; }

.metric-icon-low { background: linear-gradient(135deg, #3fc987, #73d8a5, #a8e8c4); }
.metric-icon-moderate { background: linear-gradient(135deg, #f5942f, #faad4f, #ffc670); }
.metric-icon-high { background: linear-gradient(135deg, #f04b34, #f77b68, #ffab9c); }

/* ── Info popover ── */
.info-wrap { position: relative; }

.metric-info {
  border: none;
  background: transparent;
  padding: 2px;
  color: #00000055;
  display: inline-flex;
  cursor: pointer;
}

.metric-info:hover { color: #00000088; }
.metric-info svg { width: 20px; height: 20px; }

.info-popover {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 250px;
  background: #fff;
  border-radius: 14px;
  border: 1px solid rgba(101, 148, 228, 0.15);
  box-shadow: 0 12px 30px rgba(38, 60, 110, 0.18);
  padding: 14px;
  z-index: 30;
  text-align: left;
  animation: popoverIn 0.16s ease;
}

@keyframes popoverIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.info-popover-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 10px;
  margin-bottom: 10px;
  border-bottom: 1px solid #eef1f8;
}

.info-popover-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.info-popover-icon svg, .info-popover-icon .glyph-img { width: 17px; height: 17px; object-fit: contain; }

.brand-icon-clarity { background: linear-gradient(135deg, #6da5ff, #b8d3ff); }
.brand-icon-stability { background: linear-gradient(135deg, #acb7fc, #e8e7ff); }
.brand-icon-hoarseness { background: linear-gradient(135deg, #f5a97f, #ffe3cc); }

.info-popover-head strong {
  display: block;
  font-size: 12.5px;
  color: #1a1a2e;
}

.info-popover-head span {
  display: block;
  font-size: 11px;
  color: #8b96ad;
  margin-top: 1px;
}

.info-popover-levels {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.info-level-row {
  display: grid;
  grid-template-columns: 8px auto;
  column-gap: 8px;
  row-gap: 1px;
  align-items: baseline;
}

.info-level-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  align-self: center;
}

.info-level-label {
  font-size: 11.5px;
  font-weight: 700;
}

.info-level-desc {
  grid-column: 2;
  font-size: 11px;
  color: #8b96ad;
  line-height: 1.4;
}

.metric-name {
  font-size: 12px;
  font-weight: 500;
  color: #5b6680;
}

.metric-value {
  font-size: 17px;
  font-weight: 700;
}

/* ── Bottom grid ── */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 18px;
  align-items: start;
}

.card {
  background: #fff;
  border-radius: 18px;
  border: 1px solid rgba(101, 148, 228, 0.14);
  box-shadow: 0 2px 14px rgba(101, 148, 228, 0.08);
  padding: 20px 22px;
}

.rec-card-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 18px;
}

.rec-card-icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: linear-gradient(137deg, #b47aef 6.18%, #95b9f7 94.01%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.rec-card-icon .glyph-img { width: 26px; height: 26px; object-fit: contain; }

.card-title {
  font-size: 15px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 2px;
}

.card-subtitle {
  font-size: 12px;
  font-weight: 500;
  color: #8b96ad;
  margin: 0;
}

.rec-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rec-item {
  display: flex;
  align-items: center;
  gap: 12px;
  border-radius: 14px;
  padding: 12px 14px;
  text-align: left;
}

.priority-bg-high { background: #ffe5e0; }
.priority-bg-moderate { background: #fff5e0; }

.rec-icon {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.rec-icon svg, .rec-icon .glyph-img { width: 20px; height: 20px; object-fit: contain; }

.priority-icon-high { background: linear-gradient(135deg, #f04b34, #f77b68, #ffab9c); color: #fff; }
.priority-icon-moderate { background: linear-gradient(135deg, #f5942f, #faad4f, #ffc670); color: #fff; }

.rec-text-col { display: flex; flex-direction: column; gap: 2px; }
.rec-text { font-size: 13px; font-weight: 600; color: #1a1a2e; }
.rec-priority { display: inline-flex; align-items: center; gap: 5px; font-size: 10.5px; font-weight: 600; }
.priority-text-high { color: #c83d3d; }
.priority-text-moderate { color: #c68e3f; }

.priority-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.priority-dot-high { background: linear-gradient(135deg, #ff8686, #f43333); }
.priority-dot-moderate { background: linear-gradient(135deg, #ffb886, #f47033); border: 1px solid rgba(0, 0, 0, 0.06); }

/* ── Side cards ── */
.side-cards {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.improve-card {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  text-align: left;
  font-family: 'Poppins', sans-serif;
  transition: box-shadow 0.2s, transform 0.15s;
}

.improve-card:hover {
  box-shadow: 0 6px 20px rgba(101, 148, 228, 0.18);
  transform: translateY(-1px);
}

.improve-icon {
  width: 46px;
  height: 46px;
  border-radius: 13px;
  background: linear-gradient(135deg, #a5c4f7 0%, #6594e4 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.improve-icon svg, .improve-icon .glyph-img { width: 23px; height: 23px; object-fit: contain; }

.improve-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.improve-text strong { font-size: 13.5px; color: #1a1a2e; }
.improve-text span { font-size: 11.5px; font-weight: 500; color: #8b96ad; }

.improve-chevron {
  width: 16px;
  height: 16px;
  color: #b0b8cc;
  flex-shrink: 0;
}

.progress-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 8px;
}

.progress-icon {
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a5c4f7 0%, #6594e4 100%);
  color: #fff;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-icon svg, .progress-icon .glyph-img { width: 24px; height: 24px; object-fit: contain; }

.progress-title { font-size: 15px; font-weight: 700; color: #1a1a2e; }

.progress-desc {
  font-size: 12px;
  color: #8b96ad;
  line-height: 1.6;
  margin: 0;
}

.btn-primary {
  width: 100%;
  border: none;
  background: linear-gradient(102deg, #95b9f7 8.63%, #6594e4 92.33%);
  color: #fff;
  border-radius: 14px;
  padding: 11px;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 4px;
}

.btn-primary:hover { opacity: 0.9; }

.link-plain {
  border: none;
  background: transparent;
  color: #6594e4;
  font-family: 'Poppins', sans-serif;
  font-size: 11.5px;
  font-weight: 500;
  cursor: pointer;
  align-self: center;
  padding: 2px;
}

.link-underline {
  border: none;
  background: transparent;
  color: #7c879e;
  font-family: 'Poppins', sans-serif;
  font-size: 12px;
  font-weight: 600;
  text-decoration: underline;
  cursor: pointer;
  padding: 2px;
}

/* ── Toast ── */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: #1a1a2e;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  padding: 10px 18px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.toast-enter-active, .toast-leave-active { transition: opacity 0.2s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; }

/* ── Responsive ── */
@media (max-width: 780px) {
  .bottom-grid { grid-template-columns: 1fr; }
  .metric-grid { grid-template-columns: 1fr; }
  .info-popover { left: 0; right: auto; }
}

@media (max-width: 560px) {
  .topbar { flex-direction: column; align-items: flex-start; }
  .topbar-actions { width: 100%; }
  .btn-ghost { flex: 1; justify-content: center; }
  .status-card { padding: 24px 16px; }
  .status-subtitle { white-space: normal; }
}
</style>
