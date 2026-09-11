<template>
  <div class="result-page">
    <div class="page-inner" v-if="isLoading">
      <div class="loading-card">
        <div class="result-spinner"></div>
        <p class="loading-text">Loading your result&hellip;</p>
      </div>
    </div>

    <div class="page-inner" v-else-if="quality">
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
          <button class="btn-ghost" type="button" disabled title="Available in a future update">
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
        <div class="status-icon" :class="statusIconClass">
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

          <div class="card progress-card" v-if="!isMember">
            <div class="progress-icon">
              <svg viewBox="0 0 24 24" fill="none"><path d="M3 17l6-6 4 4 8-8M15 7h6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <strong class="progress-title">Track Your Progress</strong>
            <p class="progress-desc">Create a free account to save your test results, view history, and monitor your voice health over time.</p>
            <button class="btn-primary" type="button" @click="router.push('/signup')">Create Account</button>
            <button class="link-underline" type="button" @click="router.push('/login')">Already have an account? Log in</button>
          </div>
        </div>
      </section>
    </div>

    <div class="page-inner" v-else>
      <div class="empty-state">
        <div class="empty-state-icon">
          <svg viewBox="0 0 24 24" fill="none"><path d="M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M19 11a7 7 0 0 1-14 0M12 19v3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <h2 class="empty-state-title">No recent voice analysis was found</h2>
        <p class="empty-state-desc">Take a quick voice test and your results will show up here, with personalized recommendations for your vocal health.</p>
        <button class="btn-primary" type="button" @click="router.push('/recording')">Take a Voice Test</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/utils/supabase'
import { syncAccountScope } from '@/utils/accountScope'
import { OVERALL_META, CLARITY_META, STABILITY_META, HOARSENESS_META, buildRecommendations } from '@/utils/voiceInsights'
import AudioWaveIcon from '@/assets/icons/audio_wave.png'
import AudioIcon from '@/assets/icons/audio.png'
import WaterIcon from '@/assets/icons/water.png'
import MicrophoneIcon from '@/assets/icons/Microphone.png'
import SleepingBedIcon from '@/assets/icons/sleeping_bed.png'
import SparklesIcon from '@/assets/icons/Sparkles_1.png'
import MuteIcon from '@/assets/icons/mute.png'
import CheckMarkIcon from '@/assets/icons/check_mark.png'

const router = useRouter()
const result = ref(null)
const isMember = ref(false)
const isLoading = ref(true)

onMounted(async () => {
  try {
    // Keep whatever this navigation carried (freshest, and always this
    // account's own recording) before touching anything account-scoped.
    const stateResult = window.history.state?.voiceAnalysis

    const { data } = await supabase.auth.getSession()
    isMember.value = !!data.session?.user

    // Must run before the sessionStorage fallback read below — if the
    // signed-in account differs from whoever last left data on this
    // browser, this wipes the stale cache so it's never mistaken for this
    // account's result.
    syncAccountScope(data.session?.user?.id ?? null)

    if (stateResult) {
      result.value = stateResult
    } else {
      const storedResult = sessionStorage.getItem('vocasense:lastVoiceAnalysis')
      try {
        result.value = storedResult ? JSON.parse(storedResult) : null
      } catch {
        result.value = null
      }
    }
  } finally {
    isLoading.value = false
  }
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
// OVERALL_META / CLARITY_META / STABILITY_META / HOARSENESS_META live in
// @/utils/voiceInsights so History (past recordings) renders identical
// labels/colors for the same conditions instead of a second, driftable copy.

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

// Same icon-background rule History uses for its "Today's Result" icon
// (riskIconBgClass in HistoryView.vue): low gets the green gradient chip,
// moderate/high stay the flat risk-bg-* pastel — so this icon matches that
// page's instead of inventing its own look.
const statusIconClass = computed(() =>
  overallMeta.value.level === 'low' ? 'status-icon-healthy' : 'risk-bg-' + overallMeta.value.level
)

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

// The per-recording self-assessment ("About This Recording") is stored under
// the same sessionStorage timestamp key AnalysisView stamps on the result,
// so this recording's answers (if submitted) can be looked up the same way
// ImproveResultView.vue reads/writes them.
function assessmentStorageKey(key) { return `vocasense:assessmentAnswers:${key}` }
const selfAssessment = computed(() => {
  const key = sessionStorage.getItem('vocasense:lastVoiceAnalysisAt')
  if (!key) return null
  try {
    const raw = localStorage.getItem(assessmentStorageKey(key))
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
})

// The member's one-time baseline profile (smoking/alcohol history, daily
// voice-use hours, home/work environment) — same key ImproveResultView.vue
// reads/writes. Unlike the per-recording assessment, this isn't tied to any
// one recording, so it has no session timestamp key.
const LS_BASELINE_KEY = 'vocasense:baselineAnswers'
const voiceBaseline = computed(() => {
  try {
    const raw = localStorage.getItem(LS_BASELINE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
})

// Backend returns scores/conditions but no coaching copy, so recommendations
// are derived (in @/utils/voiceInsights, shared with History) from the same
// conditions shown in the metric cards, plus this recording's self-assessment
// answers and the member's baseline — those can surface tips the acoustic
// analysis alone wouldn't catch, e.g. a healthy-sounding recording where the
// user reported severe symptoms.
const recommendations = computed(() =>
  buildRecommendations(quality.value, selfAssessment.value, voiceBaseline.value)
)

// ── Icons ────────────────────────────────────────────────────────────
const StatusIcon = (props) => {
  if (props.level === 'high') {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none' }, [
      h('path', { d: 'M12 9v4m0 4h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
    ])
  }
  if (props.level === 'moderate') {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none' }, [
      h('circle', { cx: '12', cy: '12', r: '9', stroke: 'currentColor', 'stroke-width': '2' }),
      h('path', { d: 'M12 8v5m0 3h.01', stroke: 'currentColor', 'stroke-width': '2.5', 'stroke-linecap': 'round' })
    ])
  }
  // Same asset History's RiskIcon uses for low risk, instead of a separately
  // drawn checkmark path, so the two pages show the literal same glyph.
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
// same pattern as the metric cards. "rest"/"specialist" have no matching
// asset yet, so they stay inline SVG.
const RecommendationIcon = (props) => {
  const images = { water: WaterIcon, voice: AudioIcon, warmup: MicrophoneIcon, sleep: SleepingBedIcon }
  if (images[props.kind]) {
    return h('img', { src: images[props.kind], alt: '', class: 'glyph-img' })
  }
  if (props.kind === 'specialist') {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none' }, [
      h('circle', { cx: '12', cy: '12', r: '9', stroke: 'currentColor', 'stroke-width': '2' }),
      h('path', { d: 'M12 8v5m0 3h.01', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round' })
    ])
  }
  return h('svg', { viewBox: '0 0 24 24', fill: 'none' }, [
    h('circle', { cx: '12', cy: '12', r: '9', stroke: 'currentColor', 'stroke-width': '2' }),
    h('path', { d: 'M12 7v5l3 3', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
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

/* ── Empty state ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 6px;
  max-width: 460px;
  margin: 80px auto 0;
  padding: 48px 32px;
  background: #fff;
  border-radius: 20px;
  border: 1px solid rgba(101, 148, 228, 0.14);
  box-shadow: 0 4px 24px rgba(101, 148, 228, 0.1);
}

.empty-state-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
  background: linear-gradient(135deg, #a5c4f7 0%, #6594e4 100%);
  color: #fff;
}

.empty-state-icon svg { width: 28px; height: 28px; }

.empty-state-title {
  font-size: 17px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.empty-state-desc {
  font-size: 13px;
  font-weight: 500;
  color: #8b96ad;
  line-height: 1.6;
  margin: 0 0 10px;
}

.empty-state .btn-primary {
  width: auto;
  padding: 11px 28px;
  margin-top: 0;
}

/* ── Loading state ── */
.loading-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  max-width: 460px;
  margin: 120px auto 0;
  padding: 64px 32px;
  background: #fff;
  border-radius: 20px;
  border: 1px solid rgba(101, 148, 228, 0.14);
  box-shadow: 0 4px 24px rgba(101, 148, 228, 0.1);
}

.loading-text {
  font-size: 13.5px;
  font-weight: 600;
  color: #6b7690;
  margin: 0;
  animation: resultLoadingPulse 1.6s ease-in-out infinite;
}

.result-spinner {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 4px solid rgba(101, 148, 228, 0.16);
  border-top-color: #6594e4;
  animation: resultSpin 0.8s linear infinite;
}

@keyframes resultSpin {
  to { transform: rotate(360deg); }
}

@keyframes resultLoadingPulse {
  0%, 100% { opacity: 0.55; }
  50% { opacity: 1; }
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

.btn-back:hover { background: #f4f7ff; }

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

.btn-ghost:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  color: #8a94a8;
  border-color: rgba(138, 148, 168, 0.25);
}

.btn-ghost:disabled:hover { background: #fff; }

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

/* Same shape/coloring as History's .today-icon (HistoryView.vue) — a plain
   circle, gradient only for the low/healthy case (.status-icon-healthy,
   defined below with the exact same gradient values), flat risk-bg-* pastel
   otherwise — so this reads as the same icon as the History page's, not a
   separately-invented style. */
.status-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-icon svg, .status-icon .glyph-img { width: 26px; height: 26px; object-fit: contain; }

/* Matches HistoryView.vue's .status-icon-healthy exactly. */
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
  transition: transform 0.15s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.btn-outline svg { width: 16px; height: 16px; }
.btn-outline:hover {
  background: #f4f7ff;
  box-shadow: 0 6px 16px rgba(101, 148, 228, 0.22);
  transform: translateY(-1px);
}

.btn-outline-primary {
  border: none;
  background: linear-gradient(102deg, #95b9f7 8.63%, #6594e4 92.33%);
  color: #fff;
}
.btn-outline-primary:hover {
  background: linear-gradient(102deg, #95b9f7 8.63%, #6594e4 92.33%);
  box-shadow: 0 8px 20px rgba(101, 148, 228, 0.45);
  transform: translateY(-1px);
}

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
  /* The info icon sits at the top-right of every card (.metric-card-top is
     space-between), so anchoring here and opening leftward keeps the
     popover inside the card in the common cases: every card on mobile
     (single, near-full-width column) and the middle/last cards in the
     desktop 3-col grid. Only the first card in that 3-col grid needs the
     opposite anchor — see the min-width override below. */
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

/* Only in the 3-col grid (tablet/desktop) does the first card's icon sit
   close enough to the screen's left edge that opening leftward (the
   default) would overflow past it — flip that one card to open rightward. */
@media (min-width: 781px) {
  .metric-card:first-child .info-popover {
    left: 0;
    right: auto;
  }
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
  transition: transform 0.15s ease, box-shadow 0.2s ease, opacity 0.2s ease;
}

.btn-primary:hover {
  opacity: 0.95;
  box-shadow: 0 8px 20px rgba(101, 148, 228, 0.45);
  transform: translateY(-1px);
}

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

/* ── Responsive ── */
@media (max-width: 780px) {
  .bottom-grid { grid-template-columns: 1fr; }
  .metric-grid { grid-template-columns: 1fr; gap: 10px; }
  .metric-card { padding: 12px; gap: 6px; }
  .metric-icon-square { width: 40px; height: 40px; border-radius: 12px; }
  .metric-icon-square svg, .metric-icon-square .glyph-img { width: 22px; height: 22px; }
}

@media (max-width: 560px) {
  .topbar { flex-direction: column; align-items: flex-start; }
  .topbar-actions { width: 100%; }
  .btn-ghost { flex: 1; justify-content: center; }
  .status-card { padding: 24px 16px; }
  .status-subtitle { white-space: normal; }
  .empty-state { margin-top: 40px; padding: 36px 20px; }
  .loading-card { margin-top: 60px; padding: 48px 20px; }
}
</style>
