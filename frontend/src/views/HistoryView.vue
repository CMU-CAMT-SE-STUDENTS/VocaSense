<template>
  <div class="history-page">
    <Navbar @scroll-to="goHome" />

    <div class="history-container">
      <header class="welcome-header">
        <h1 class="welcome-title">Welcome back, {{ displayName }}!</h1>
        <p class="welcome-date">{{ formatDate(latestRecord.date) }}</p>
      </header>

      <section class="today-card">
        <div class="today-icon" :class="riskIconBgClass(latestRecord.risk)">
          <RiskIcon :risk="latestRecord.risk" />
        </div>
        <div class="today-info">
          <span class="today-label">Today's Result</span>
          <span class="today-result" :class="'risk-text-' + latestRecord.risk">{{ latestRecord.resultLabel }}</span>
          <span class="today-meta">{{ formatDate(latestRecord.date) }} &middot; {{ latestRecord.time }}</span>
        </div>
      </section>

      <section class="card score-card">
        <div class="card-header">
          <h2 class="card-title">Voice Health Score</h2>
          <div class="pill-group">
            <span
              class="pill-indicator"
              :style="{ transform: `translateX(${scoreRanges.indexOf(selectedScoreRange) * 100}%)` }"
            ></span>
            <button
              v-for="range in scoreRanges"
              :key="range"
              class="pill-btn"
              :class="{ active: selectedScoreRange === range }"
              @click="selectedScoreRange = range"
            >{{ range }}</button>
          </div>
        </div>

        <div class="score-body">
          <div class="score-chart">
            <div class="axis-labels">
              <span v-for="line in gridLines" :key="line.label" class="axis-label" :style="{ top: line.pct + '%' }">{{ line.label }}</span>
            </div>
            <div class="chart-plot">
              <svg :viewBox="`0 0 ${CHART_W} ${CHART_H}`" preserveAspectRatio="none" class="chart-svg">
                <defs>
                  <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#6594E4" stop-opacity="0.32" />
                    <stop offset="100%" stop-color="#6594E4" stop-opacity="0" />
                  </linearGradient>
                </defs>
                <line v-for="line in gridLines" :key="line.label" x1="0" :y1="line.y" :x2="CHART_W" :y2="line.y" class="chart-grid" />
                <path :d="chartAreaPath" class="chart-area" />
                <path :d="chartLinePath" class="chart-line" />
                <circle v-if="chartLastPoint" :cx="chartLastPoint.x" :cy="chartLastPoint.y" r="6" class="chart-dot-halo" />
                <circle v-if="chartLastPoint" :cx="chartLastPoint.x" :cy="chartLastPoint.y" r="3.5" class="chart-dot" />
              </svg>
              <div v-if="chartLastPoint" class="chart-value-pill" :style="{ left: chartLastPointPct.left + '%', top: chartLastPointPct.top + '%' }">
                {{ chartLastPoint.score }}
              </div>
              <p v-if="!scoreFiltered.length" class="chart-empty">No sessions in this range yet.</p>
            </div>
          </div>

          <div class="stat-tiles">
            <div class="stat-tile stat-total">
              <span class="stat-number">{{ scoreFiltered.length }}</span>
              <span class="stat-label">Total sessions</span>
            </div>
            <div class="stat-tile stat-high">
              <span class="stat-number">{{ riskCount('high') }}</span>
              <span class="stat-label">High risk</span>
            </div>
            <div class="stat-tile stat-moderate">
              <span class="stat-number">{{ riskCount('moderate') }}</span>
              <span class="stat-label">Moderate risk</span>
            </div>
            <div class="stat-tile stat-low">
              <span class="stat-number">{{ riskCount('low') }}</span>
              <span class="stat-label">Low risk</span>
            </div>
          </div>
        </div>
      </section>

      <section class="card record-card">
        <div class="card-header">
          <h2 class="card-title">Record List</h2>
          <div class="record-filters">
            <div class="dropdown" v-click-outside="() => closeDropdownIfOpen('date')">
              <button type="button" class="dropdown-trigger" @click="toggleDropdown('date')">
                {{ dateFilter }}
                <svg class="chevron" :class="{ open: openDropdown === 'date' }" viewBox="0 0 24 24" fill="none">
                  <path d="m6 9 6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <div v-if="openDropdown === 'date'" class="dropdown-menu">
                <button
                  v-for="range in scoreRanges"
                  :key="range"
                  type="button"
                  class="dropdown-option"
                  :class="{ selected: dateFilter === range }"
                  @click="selectDateFilter(range)"
                >
                  {{ range }}
                  <svg v-if="dateFilter === range" class="option-check" viewBox="0 0 24 24" fill="none">
                    <path d="m5 13 4 4L19 7" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>

            <div class="dropdown" v-click-outside="() => closeDropdownIfOpen('risk')">
              <button type="button" class="dropdown-trigger" @click="toggleDropdown('risk')">
                {{ riskFilterLabel }}
                <svg class="chevron" :class="{ open: openDropdown === 'risk' }" viewBox="0 0 24 24" fill="none">
                  <path d="m6 9 6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <div v-if="openDropdown === 'risk'" class="dropdown-menu">
                <button
                  v-for="opt in riskFilterOptions"
                  :key="opt.value"
                  type="button"
                  class="dropdown-option"
                  :class="{ selected: riskFilter === opt.value }"
                  @click="selectRiskFilter(opt.value)"
                >
                  {{ opt.label }}
                  <svg v-if="riskFilter === opt.value" class="option-check" viewBox="0 0 24 24" fill="none">
                    <path d="m5 13 4 4L19 7" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>

            <button class="btn-export" type="button" @click="exportRecords">
              <svg viewBox="0 0 24 24" fill="none" class="export-icon"><path d="M12 3v12m0 0 4-4m-4 4-4-4M5 21h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              Export
            </button>
          </div>
        </div>

        <div class="record-body">
          <div class="record-list">
            <template v-for="group in groupedRecords" :key="group.month">
              <p class="record-group-label">{{ group.month }}</p>
              <button
                v-for="rec in group.items"
                :key="rec.id"
                class="record-item"
                :class="{ selected: rec.id === selectedId }"
                @click="selectedId = rec.id"
              >
                <span class="record-dot" :class="'risk-dot-' + rec.risk"></span>
                <span class="record-date-col">
                  <span class="record-date">{{ formatDate(rec.date) }}</span>
                  <span class="record-time">{{ rec.time }}</span>
                </span>
              </button>
            </template>
            <p v-if="!filteredRecords.length" class="record-empty">No records match these filters.</p>
          </div>

          <Transition name="detail-swap" mode="out-in">
            <div class="record-detail" v-if="selectedRecord" :key="selectedRecord.id">
              <div class="detail-icon" :class="riskIconBgClass(selectedRecord.risk)">
                <RiskIcon :risk="selectedRecord.risk" />
              </div>
              <h3 class="detail-result" :class="'risk-text-' + selectedRecord.risk">{{ selectedRecord.resultLabel }}</h3>
              <p class="detail-meta">{{ formatDate(selectedRecord.date) }} &middot; {{ selectedRecord.time }}</p>

              <div class="metric-row">
                <div v-for="metric in selectedRecord.metrics" :key="metric.label" class="metric-chip" :class="'metric-bg-' + metric.level">
                  <div class="metric-chip-icon" :class="'metric-icon-' + metric.level">
                    <MetricIcon :kind="metric.kind" />
                  </div>
                  <strong class="metric-value" :class="'risk-text-' + metric.level">{{ metric.value }}</strong>
                  <span class="metric-label">{{ metric.label }}</span>
                </div>
              </div>

              <h4 class="rec-title">Recommendations</h4>
              <div class="rec-list">
                <div v-for="rec in selectedRecord.recommendations" :key="rec.text" class="rec-item" :class="'priority-bg-' + rec.priority">
                  <span class="rec-icon" :class="'priority-icon-' + rec.priority">
                    <RecommendationIcon :kind="rec.kind" />
                  </span>
                  <span class="rec-text-col">
                    <span class="rec-text">{{ rec.text }}</span>
                    <span class="rec-priority" :class="'priority-text-' + rec.priority">
                      <span class="priority-dot" :class="'priority-dot-' + rec.priority"></span>
                      {{ priorityLabel(rec.priority) }} Priority
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </section>

      <p class="history-disclaimer">
        Sample data shown for preview &mdash; connect your account history to see real results here.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '@/components/NavBar.vue'
import { supabase } from '@/utils/supabase'
import CheckMarkIcon from '@/assets/icons/check_mark.png'
import SparklesIcon from '@/assets/icons/Sparkles_1.png'
import AudioWaveIcon from '@/assets/icons/audio_wave.png'
import MuteIcon from '@/assets/icons/mute.png'
import WaterIcon from '@/assets/icons/water.png'
import AudioIcon from '@/assets/icons/audio.png'
import MicrophoneIcon from '@/assets/icons/Microphone.png'

const router = useRouter()
const goHome = () => router.push('/')

const displayName = ref('there')

onMounted(async () => {
  const { data } = await supabase.auth.getSession()
  const user = data.session?.user
  displayName.value = user?.user_metadata?.username || user?.email || 'there'
})

// ── Icons — same treatment as the Result Dashboard: real image assets
// where the glyph doesn't need to recolor per state, inline SVG (currentColor)
// where it does (moderate/high risk, and the priority-coded recommendations).
const RiskIcon = (props) => {
  if (props.risk === 'high') {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none' }, [
      h('path', { d: 'M12 9v4m0 4h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
    ])
  }
  if (props.risk === 'moderate') {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none' }, [
      h('circle', { cx: '12', cy: '12', r: '9', stroke: 'currentColor', 'stroke-width': '2' }),
      h('path', { d: 'M12 8v5m0 3h.01', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round' })
    ])
  }
  return h('img', { src: CheckMarkIcon, alt: '', class: 'glyph-img' })
}

const MetricIcon = (props) => {
  const images = { clarity: SparklesIcon, stability: AudioWaveIcon, hoarseness: MuteIcon }
  return h('img', { src: images[props.kind], alt: '', class: 'glyph-img' })
}

const RecommendationIcon = (props) => {
  if (props.kind === 'rest') {
    return h('svg', { viewBox: '0 0 24 24', fill: 'none' }, [
      h('path', { d: 'M12 7v5l3 3M12 3a9 9 0 1 0 9 9', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
    ])
  }
  const images = { water: WaterIcon, voice: AudioIcon, warmup: MicrophoneIcon }
  return h('img', { src: images[props.kind], alt: '', class: 'glyph-img' })
}

// ── Sample data (UI preview only — not wired to a backend yet) ─────
const mockRecords = [
  {
    id: 1,
    date: new Date(2026, 6, 21),
    time: '09:14 AM',
    risk: 'low',
    score: 92,
    resultLabel: 'No Vocal Strain Detected',
    metrics: [
      { kind: 'clarity', label: 'Voice clarity', value: 'Clear', level: 'low' },
      { kind: 'stability', label: 'Voice stability', value: 'Stable', level: 'low' },
      { kind: 'hoarseness', label: 'Voice hoarseness', value: 'Low', level: 'low' }
    ],
    recommendations: [
      { kind: 'rest', text: 'Give your voice a rest for 2-3 hours', priority: 'high' },
      { kind: 'water', text: 'Drink at least 8 glasses of water daily', priority: 'high' },
      { kind: 'voice', text: 'Avoid shouting or speaking loudly', priority: 'moderate' },
      { kind: 'warmup', text: 'Practice vocal warm-up exercises', priority: 'moderate' }
    ]
  },
  {
    id: 2,
    date: new Date(2026, 6, 19),
    time: '10:14 AM',
    risk: 'moderate',
    score: 64,
    resultLabel: 'Mild Vocal Fatigue Detected',
    metrics: [
      { kind: 'clarity', label: 'Voice clarity', value: 'Fair', level: 'moderate' },
      { kind: 'stability', label: 'Voice stability', value: 'Slightly Uneven', level: 'moderate' },
      { kind: 'hoarseness', label: 'Voice hoarseness', value: 'Mild', level: 'moderate' }
    ],
    recommendations: [
      { kind: 'rest', text: 'Rest your voice for at least 4 hours', priority: 'high' },
      { kind: 'water', text: 'Increase water intake throughout the day', priority: 'high' },
      { kind: 'voice', text: 'Avoid whispering, which can strain your voice', priority: 'moderate' },
      { kind: 'warmup', text: 'Do gentle humming exercises before speaking', priority: 'moderate' }
    ]
  },
  {
    id: 3,
    date: new Date(2026, 5, 28),
    time: '09:14 AM',
    risk: 'low',
    score: 88,
    resultLabel: 'No Vocal Strain Detected',
    metrics: [
      { kind: 'clarity', label: 'Voice clarity', value: 'Clear', level: 'low' },
      { kind: 'stability', label: 'Voice stability', value: 'Stable', level: 'low' },
      { kind: 'hoarseness', label: 'Voice hoarseness', value: 'Low', level: 'low' }
    ],
    recommendations: [
      { kind: 'water', text: 'Keep water nearby during long calls', priority: 'moderate' },
      { kind: 'warmup', text: 'Practice vocal warm-up exercises', priority: 'moderate' }
    ]
  },
  {
    id: 4,
    date: new Date(2026, 5, 20),
    time: '10:14 AM',
    risk: 'high',
    score: 38,
    resultLabel: 'Vocal Strain Detected',
    metrics: [
      { kind: 'clarity', label: 'Voice clarity', value: 'Rough', level: 'high' },
      { kind: 'stability', label: 'Voice stability', value: 'Unstable', level: 'high' },
      { kind: 'hoarseness', label: 'Voice hoarseness', value: 'High', level: 'high' }
    ],
    recommendations: [
      { kind: 'rest', text: 'Rest your voice completely for the rest of the day', priority: 'high' },
      { kind: 'water', text: 'Drink warm water with honey to soothe your throat', priority: 'high' },
      { kind: 'voice', text: 'Avoid speaking loudly or for long periods', priority: 'high' },
      { kind: 'warmup', text: 'See a specialist if strain continues past 3 days', priority: 'moderate' }
    ]
  }
]

const latestRecord = mockRecords.reduce((a, b) => (b.date > a.date ? b : a))

// ── Voice Health Score card ─────────────────────────────────────────
const scoreRanges = ['7 Days', '30 Days', 'All Time']
const selectedScoreRange = ref('7 Days')

function withinRange(record, range, referenceDate) {
  if (range === 'All Time') return true
  const days = range === '7 Days' ? 7 : 30
  const diff = (referenceDate - record.date) / (1000 * 60 * 60 * 24)
  return diff >= 0 && diff <= days
}

const scoreFiltered = computed(() =>
  mockRecords
    .filter((r) => withinRange(r, selectedScoreRange.value, latestRecord.date))
    .sort((a, b) => a.date - b.date)
)

function riskCount(risk) {
  return scoreFiltered.value.filter((r) => r.risk === risk).length
}

// Kept relatively wide/flat (vs. a square-ish ratio) so the line still reads
// well once the card stretches on a wide screen — see CSS aspect-ratio below,
// which is what actually keeps the endpoint dot circular at any width.
const CHART_W = 600
const CHART_H = 170
const CHART_PAD = 16

function chartPoints() {
  const items = scoreFiltered.value
  if (items.length < 2) return null
  const usableW = CHART_W - CHART_PAD * 2
  const usableH = CHART_H - CHART_PAD * 2
  return items.map((rec, i) => {
    const x = CHART_PAD + (usableW * i) / (items.length - 1)
    const y = CHART_PAD + usableH * (1 - rec.score / 100)
    return { x, y, score: rec.score }
  })
}

// Catmull-Rom → cubic Bezier, so the trend reads as a curve instead of sharp segments
function smoothLinePath(pts) {
  if (!pts || pts.length < 2) return ''
  if (pts.length === 2) return `M${pts[0].x},${pts[0].y} L${pts[1].x},${pts[1].y}`
  let d = `M${pts[0].x},${pts[0].y}`
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i]
    const p1 = pts[i]
    const p2 = pts[i + 1]
    const p3 = pts[i + 2] || p2
    const cp1x = p1.x + (p2.x - p0.x) / 6
    const cp1y = p1.y + (p2.y - p0.y) / 6
    const cp2x = p2.x - (p3.x - p1.x) / 6
    const cp2y = p2.y - (p3.y - p1.y) / 6
    d += ` C${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`
  }
  return d
}

const chartLinePath = computed(() => smoothLinePath(chartPoints()))

const chartAreaPath = computed(() => {
  const pts = chartPoints()
  if (!pts) return ''
  const baseline = CHART_H - CHART_PAD
  return `${smoothLinePath(pts)} L${pts[pts.length - 1].x},${baseline} L${pts[0].x},${baseline} Z`
})

const chartLastPoint = computed(() => {
  const pts = chartPoints()
  return pts ? pts[pts.length - 1] : null
})

const chartLastPointPct = computed(() => {
  const p = chartLastPoint.value
  return p ? { left: (p.x / CHART_W) * 100, top: (p.y / CHART_H) * 100 } : { left: 0, top: 0 }
})

const gridLines = computed(() => {
  const usableH = CHART_H - CHART_PAD * 2
  return [100, 50, 0].map((v) => {
    const y = CHART_PAD + usableH * (1 - v / 100)
    return { label: String(v), y, pct: (y / CHART_H) * 100 }
  })
})

// ── Record List card ────────────────────────────────────────────────
const dateFilter = ref('All Time')
const riskFilter = ref('all')
const selectedId = ref(latestRecord.id)

const riskFilterOptions = [
  { value: 'all', label: 'All Risk' },
  { value: 'high', label: 'High Risk' },
  { value: 'moderate', label: 'Moderate Risk' },
  { value: 'low', label: 'Low Risk' }
]
const riskFilterLabel = computed(
  () => riskFilterOptions.find((o) => o.value === riskFilter.value)?.label
)

const openDropdown = ref(null) // 'date' | 'risk' | null
const toggleDropdown = (name) => {
  openDropdown.value = openDropdown.value === name ? null : name
}
// Each dropdown has its own click-outside listener; only close if THIS one is
// the open one, otherwise opening dropdown B nulls it right back out via A's listener.
const closeDropdownIfOpen = (name) => {
  if (openDropdown.value === name) openDropdown.value = null
}
const selectDateFilter = (range) => { dateFilter.value = range; openDropdown.value = null }
const selectRiskFilter = (value) => { riskFilter.value = value; openDropdown.value = null }

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

const filteredRecords = computed(() =>
  mockRecords
    .filter((r) => withinRange(r, dateFilter.value, latestRecord.date))
    .filter((r) => riskFilter.value === 'all' || r.risk === riskFilter.value)
    .sort((a, b) => b.date - a.date)
)

const groupedRecords = computed(() => {
  const groups = new Map()
  for (const rec of filteredRecords.value) {
    const key = rec.date.toLocaleDateString('en-US', { month: 'long' })
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(rec)
  }
  return Array.from(groups, ([month, items]) => ({ month, items }))
})

const selectedRecord = computed(
  () => filteredRecords.value.find((r) => r.id === selectedId.value) || filteredRecords.value[0] || null
)

function riskIconBgClass(risk) {
  return risk === 'low' ? 'status-icon-healthy' : 'risk-bg-' + risk
}

function priorityLabel(priority) {
  return priority === 'high' ? 'High' : 'Moderate'
}

function exportRecords() {
  const rows = filteredRecords.value.map((r) => `${formatDate(r.date)},${r.time},${r.risk},${r.resultLabel}`)
  const csv = ['Date,Time,Risk,Result', ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'vocasense-voice-history.csv'
  link.click()
  URL.revokeObjectURL(url)
}

function formatDate(date) {
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

* { box-sizing: border-box; }

.history-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #eef2ff 0%, #eff3ff 40%, #fafbff 100%);
  font-family: 'Poppins', sans-serif;
}

.history-container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 24px 64px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── Welcome ── */
.welcome-header {
  text-align: center;
  margin-bottom: 4px;
}

.welcome-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 4px;
}

.welcome-date {
  font-size: 12.5px;
  font-weight: 500;
  color: #8b96ad;
  margin: 0;
}

/* ── Shared card ── */
.card,
.today-card {
  background: #fff;
  border-radius: 18px;
  border: 1px solid rgba(101, 148, 228, 0.14);
  box-shadow: 0 2px 14px rgba(101, 148, 228, 0.08);
  padding: 22px 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 18px;
}

.card-title {
  font-size: 16px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

/* ── Today's Result ── */
.today-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.today-icon,
.detail-icon {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.today-icon :deep(svg),
.detail-icon :deep(svg),
.today-icon :deep(.glyph-img),
.detail-icon :deep(.glyph-img) {
  width: 22px;
  height: 22px;
  object-fit: contain;
}

.status-icon-healthy { background: linear-gradient(135deg, #3fc987, #73d8a5, #a8e8c4); }

.today-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.today-label {
  font-size: 12px;
  font-weight: 500;
  color: #8b96ad;
}

.today-result {
  font-size: 16px;
  font-weight: 700;
}

.today-meta {
  font-size: 12px;
  font-weight: 500;
  color: #8b96ad;
}

/* ── Risk color tokens ── */
.risk-bg-low { background: #e3f7ec; color: #1f9d5b; }
.risk-bg-moderate { background: #fff3dc; color: #b7791f; }
.risk-bg-high { background: #fdeaea; color: #c83d3d; }
.risk-text-low { color: #1f9d5b; }
.risk-text-moderate { color: #b7791f; }
.risk-text-high { color: #c83d3d; }
.risk-dot-low { background: #22c55e; }
.risk-dot-moderate { background: #f5a623; }
.risk-dot-high { background: #ef4444; }

/* ── Pills / filters ── */
.pill-group {
  position: relative;
  display: flex;
  background: #f4f7ff;
  padding: 4px;
  border-radius: 20px;
}

.pill-indicator {
  position: absolute;
  top: 4px;
  left: 4px;
  width: calc((100% - 8px) / 3);
  height: calc(100% - 8px);
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 6px rgba(101, 148, 228, 0.25);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.pill-btn {
  position: relative;
  z-index: 1;
  flex: 1;
  white-space: nowrap;
  border: none;
  background: transparent;
  padding: 7px 10px;
  border-radius: 16px;
  font-family: 'Poppins', sans-serif;
  font-size: 11.5px;
  font-weight: 600;
  color: #6b7690;
  cursor: pointer;
  transition: color 0.2s;
}

.pill-btn.active { color: #6594e4; }

/* ── Voice Health Score ── */
.score-body {
  display: grid;
  grid-template-columns: 1fr 128px;
  gap: 20px;
  align-items: stretch;
}

.score-chart {
  display: flex;
  align-items: stretch;
  gap: 6px;
  background: #f8faff;
  border: 1px solid rgba(101, 148, 228, 0.12);
  border-radius: 14px;
  padding: 14px 16px 14px 6px;
  min-height: 90px;
}

.axis-labels {
  position: relative;
  width: 22px;
  flex-shrink: 0;
}

.axis-label {
  position: absolute;
  left: 0;
  transform: translateY(-50%);
  font-size: 9.5px;
  font-weight: 600;
  color: #b0b8cc;
  font-variant-numeric: tabular-nums;
}

/* Positioned so the value-pill's % coordinates line up 1:1 with the SVG's
   own box — no offset to account for, unlike the old padding-based gutter. */
.chart-plot {
  position: relative;
  flex: 1;
  min-width: 0;
}

.chart-svg {
  width: 100%;
  height: auto;
  aspect-ratio: 600 / 170;
  display: block;
}

.chart-grid {
  stroke: rgba(101, 148, 228, 0.14);
  stroke-width: 1;
  stroke-dasharray: 3 4;
}

.chart-area {
  fill: url(#scoreFill);
  stroke: none;
}

.chart-line {
  fill: none;
  stroke: #6594e4;
  stroke-width: 2.5;
  stroke-linejoin: round;
  stroke-linecap: round;
  filter: drop-shadow(0 3px 5px rgba(101, 148, 228, 0.35));
}

.chart-dot-halo {
  fill: rgba(101, 148, 228, 0.22);
}

.chart-dot {
  fill: #6594e4;
  stroke: #fff;
  stroke-width: 1.5;
}

.chart-value-pill {
  position: absolute;
  transform: translate(-50%, calc(-100% - 12px));
  background: #4a7fdb;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  padding: 3px 9px;
  border-radius: 10px;
  box-shadow: 0 4px 10px rgba(101, 148, 228, 0.4);
  white-space: nowrap;
  pointer-events: none;
}

.chart-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  font-size: 12.5px;
  font-weight: 500;
  color: #9aa4bd;
}

.stat-tiles {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-tile {
  flex: 1;
  border-radius: 14px;
  padding: 11px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 4px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
}

.stat-number {
  font-size: 19px;
  font-weight: 800;
  line-height: 1.1;
}

.stat-label {
  font-size: 10.5px;
  font-weight: 600;
}

.stat-total { background: linear-gradient(135deg, #ffffff 3%, #f4f8ff 66%, #e5eeff 100%); }
.stat-total .stat-number { color: #3d6fd1; }
.stat-total .stat-label { color: #5778b2; }

.stat-high { background: linear-gradient(135deg, #ffffff 3%, #fff4f4 66%, #ffe0e0 100%); }
.stat-high .stat-number { color: #c83d3d; }
.stat-high .stat-label { color: #c2694f; }

.stat-moderate { background: linear-gradient(135deg, #ffffff 3%, #fffdf4 66%, #fff5e0 100%); }
.stat-moderate .stat-number { color: #b7791f; }
.stat-moderate .stat-label { color: #b3823f; }

.stat-low { background: linear-gradient(135deg, #ffffff 3%, #f1ffee 66%, #e0ffe0 100%); }
.stat-low .stat-number { color: #1f9d5b; }
.stat-low .stat-label { color: #3e9270; }

/* ── Record List ── */
.record-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.dropdown {
  position: relative;
}

.dropdown-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: 'Poppins', sans-serif;
  font-size: 12.5px;
  font-weight: 600;
  color: #444;
  background: #fff;
  border: 1px solid rgba(101, 148, 228, 0.25);
  border-radius: 16px;
  padding: 8px 14px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.dropdown-trigger:hover {
  border-color: rgba(101, 148, 228, 0.5);
  background: #f8faff;
}

.chevron {
  width: 13px;
  height: 13px;
  color: #8b96ad;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.chevron.open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  min-width: 100%;
  background: #fff;
  border-radius: 12px;
  border: 1px solid rgba(101, 148, 228, 0.15);
  box-shadow: 0 10px 28px rgba(38, 60, 110, 0.16);
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  z-index: 20;
  animation: dropdownIn 0.16s ease;
}

.dropdown-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  white-space: nowrap;
  border: none;
  background: transparent;
  border-radius: 8px;
  padding: 8px 10px;
  font-family: 'Poppins', sans-serif;
  font-size: 12.5px;
  font-weight: 500;
  color: #444;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s, color 0.15s;
}

.dropdown-option:hover {
  background: #f4f7ff;
  color: #6594e4;
}

.dropdown-option.selected {
  background: #eaf1ff;
  color: #3d6fd1;
  font-weight: 700;
}

.option-check {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

@keyframes dropdownIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.btn-export {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(101, 148, 228, 0.25);
  background: #fff;
  border-radius: 16px;
  padding: 8px 16px;
  font-family: 'Poppins', sans-serif;
  font-size: 12.5px;
  font-weight: 600;
  color: #6594e4;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-export:hover { background: #f4f7ff; }

.export-icon { width: 14px; height: 14px; }

.record-body {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 20px;
  border-top: 1px solid #eef1f8;
  padding-top: 18px;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  border-right: 1px solid #eef1f8;
  padding-right: 16px;
}

.record-group-label {
  font-size: 12.5px;
  font-weight: 600;
  color: #9aa4bd;
  margin: 16px 0 6px;
  padding-top: 14px;
  border-top: 1px solid #eef1f8;
}

.record-group-label:first-child {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.record-item {
  display: flex;
  align-items: center;
  gap: 10px;
  border: none;
  background: transparent;
  border-radius: 10px;
  padding: 8px 8px;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
  font-family: 'Poppins', sans-serif;
}

.record-item:hover { background: #f4f7ff; }

.record-item.selected {
  background: #eaf1ff;
}

.record-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.record-date-col {
  display: flex;
  flex-direction: column;
}

.record-date {
  font-size: 12.5px;
  font-weight: 600;
  color: #1a1a2e;
}

.record-time {
  font-size: 11px;
  font-weight: 500;
  color: #9aa4bd;
}

.record-empty {
  font-size: 12.5px;
  color: #9aa4bd;
  padding: 12px 4px;
}

/* ── Record detail ── */
.record-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 8px 8px 0;
}

.detail-result {
  font-size: 17px;
  font-weight: 700;
  margin: 12px 0 2px;
}

.detail-meta {
  font-size: 12px;
  font-weight: 500;
  color: #9aa4bd;
  margin: 0 0 18px;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  width: 100%;
  max-width: 480px;
  margin-bottom: 22px;
}

.metric-chip {
  border-radius: 14px;
  padding: 14px 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

/* Same pale-gradient / dark-icon-square pairing as the Result Dashboard's
   metric cards, just sized down to fit this compact chip layout. */
.metric-bg-low { background: linear-gradient(135deg, #ffffff 3%, #f1ffee 66%, #e0ffe0 100%); }
.metric-bg-moderate { background: linear-gradient(135deg, #ffffff 3%, #fffdf4 66%, #fff5e0 100%); }
.metric-bg-high { background: linear-gradient(135deg, #ffffff 3%, #fff4f4 66%, #ffe0e0 100%); }

.metric-chip-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.metric-chip-icon :deep(.glyph-img) { width: 18px; height: 18px; object-fit: contain; }

.metric-icon-low { background: linear-gradient(135deg, #3fc987, #73d8a5, #a8e8c4); }
.metric-icon-moderate { background: linear-gradient(135deg, #f5942f, #faad4f, #ffc670); }
.metric-icon-high { background: linear-gradient(135deg, #f04b34, #f77b68, #ffab9c); }

.metric-value { font-size: 13px; font-weight: 700; }

.metric-label {
  font-size: 10.5px;
  font-weight: 500;
  color: #6b7690;
}

.rec-title {
  align-self: flex-start;
  font-size: 13px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 10px;
}

.rec-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
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

.rec-icon svg, .rec-icon :deep(.glyph-img) { width: 20px; height: 20px; object-fit: contain; }

.priority-icon-high { background: linear-gradient(135deg, #f04b34, #f77b68, #ffab9c); color: #fff; }
.priority-icon-moderate { background: linear-gradient(135deg, #f5942f, #faad4f, #ffc670); color: #fff; }

.priority-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.priority-dot-high { background: linear-gradient(135deg, #ff8686, #f43333); }
.priority-dot-moderate { background: linear-gradient(135deg, #ffb886, #f47033); border: 1px solid rgba(0, 0, 0, 0.06); }

.rec-text-col {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rec-text {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
}

.rec-priority { display: inline-flex; align-items: center; gap: 5px; font-size: 10.5px; font-weight: 600; }
.priority-text-high { color: #c83d3d; }
.priority-text-moderate { color: #c68e3f; }

.history-disclaimer {
  text-align: center;
  font-size: 11.5px;
  font-weight: 500;
  color: #aaa;
  margin: 4px 0 0;
}

/* ── Responsive ── */
@media (max-width: 860px) {
  .score-body {
    grid-template-columns: 1fr;
  }
  .stat-tiles {
    flex-direction: row;
    flex-wrap: wrap;
  }
  .stat-tile { min-width: 130px; }
  .record-body {
    grid-template-columns: 1fr;
  }
  .record-list {
    border-right: none;
    border-bottom: 1px solid #eef1f8;
    padding-right: 0;
    padding-bottom: 12px;
    flex-direction: row;
    flex-wrap: wrap;
  }
  .record-group-label { width: 100%; }
}

@media (max-width: 520px) {
  .history-container { padding: 24px 16px 48px; }
  .metric-row { grid-template-columns: 1fr; }
  .card { padding: 18px; }
}

/* ── Record detail swap transition ── */
.detail-swap-enter-active, .detail-swap-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.detail-swap-enter-from { opacity: 0; transform: translateY(6px); }
.detail-swap-leave-to { opacity: 0; transform: translateY(-6px); }

@media (prefers-reduced-motion: reduce) {
  .detail-swap-enter-active, .detail-swap-leave-active { transition: opacity 0.12s ease; }
  .detail-swap-enter-from, .detail-swap-leave-to { transform: none; }
}
</style>
