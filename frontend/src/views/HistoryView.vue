<template>
  <div class="history-page">
    <Navbar @scroll-to="goHome" />

    <div class="history-container" :class="{ 'history-container-empty': isLoading || loadError || !records.length }">
      <div v-if="isLoading" class="history-loading">
        <span class="loading-spinner" aria-hidden="true"></span>
        <p class="loading-text">Loading your history&hellip;</p>
      </div>

      <div v-else-if="loadError" class="history-loading">
        <p class="loading-text">Couldn&rsquo;t load your history right now. Please try again shortly.</p>
      </div>

      <template v-else-if="records.length">
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
          <div class="title-with-info">
            <h2 class="card-title">Voice Health Score</h2>
            <div class="info-wrap" v-click-outside="() => (showScoreInfo = false)">
              <button type="button" class="score-info-btn" @click="showScoreInfo = !showScoreInfo" aria-label="About Voice Health Score">
                <svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.6"/><path d="M12 11v5m0-8h.01" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
              </button>
              <div v-if="showScoreInfo" class="score-info-popover">
                <strong>Voice Health Score</strong>
                <span>A composite score from 0–100 reflecting your overall vocal health for that session, based on your voice clarity, stability, and hoarseness. Higher is better.</span>
              </div>
            </div>
          </div>
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
            <div class="chart-row">
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
                  <rect
                    v-for="band in riskBands"
                    :key="band.level"
                    x="0"
                    :y="band.y"
                    :width="CHART_W"
                    :height="band.height"
                    :fill="band.color"
                  />
                  <line v-for="line in gridLines" :key="line.label" x1="0" :y1="line.y" :x2="CHART_W" :y2="line.y" class="chart-grid" />
                  <path :d="chartAreaPath" class="chart-area" />
                  <path :d="chartLinePath" class="chart-line" />
                </svg>
                <!-- Markers are plain HTML elements positioned by %, not SVG <circle> elements:
                     the SVG box can now be much wider than its 600:170 viewBox (see max-height
                     cap above), and preserveAspectRatio="none" would squash SVG circles into
                     flattened ellipses under that non-uniform scaling. Each marker carries its
                     own tooltip showing the score and its color band, instead of a permanently-
                     visible value pill — shown on hover or on click, the latter
                     persisting until an outside click, via v-click-outside below. -->
                <div
                  v-for="(pt, i) in chartPointsFull"
                  :key="i"
                  class="chart-point-wrap"
                  :class="{ 'is-active': activeTooltipIndex === i }"
                  :style="{ left: pt.left + '%', top: pt.top + '%' }"
                  v-click-outside="() => { if (activeTooltipIndex === i) activeTooltipIndex = null }"
                  @click.stop="toggleTooltip(i)"
                >
                  <span v-if="pt.isLast" class="chart-dot-halo"></span>
                  <span class="chart-point-marker" :class="{ 'chart-dot': pt.isLast }"></span>
                  <div class="chart-tooltip">
                    <span class="tooltip-date">{{ formatDate(pt.date) }} &middot; {{ pt.time }}</span>
                    <span class="tooltip-score">{{ pt.score }}</span>
                    <span class="tooltip-risk" :class="'risk-text-' + pt.band">
                      <span class="tooltip-risk-dot" :class="'risk-dot-' + pt.band"></span>
                      {{ riskLabel(pt.band) }}
                    </span>
                  </div>
                </div>
                <p v-if="!scoreFiltered.length" class="chart-empty">No sessions in this range yet.</p>
              </div>
            </div>
            <div class="x-axis-row">
              <div class="x-axis-spacer"></div>
              <div class="x-axis-labels">
                <span v-for="(tick, i) in xAxisTicks" :key="i" class="x-axis-label" :style="{ left: tick.left + '%' }">{{ tick.label }}</span>
              </div>
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

      <section class="card record-card" :class="{ 'detail-overlay-open': mobileDetailOpen }">
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

            <button type="button" class="btn-export" disabled title="Available in a future update">
              <svg viewBox="0 0 24 24" fill="none" class="export-icon"><path d="M12 3v12m0 0-4-4m4 4 4-4M5 21h14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
              Export
            </button>
          </div>
        </div>

        <div class="record-body">
          <div class="record-list">
            <template v-for="group in groupedRecords" :key="group.month">
              <div class="record-group-header">
                <p class="record-group-label">{{ group.month }}</p>
                <span class="record-group-count">{{ group.items.length }} record{{ group.items.length === 1 ? '' : 's' }}</span>
              </div>
              <button
                v-for="rec in visibleGroupItems(group)"
                :key="rec.id"
                class="record-item"
                :class="{ selected: rec.id === selectedId }"
                @click="openRecordDetail(rec.id)"
              >
                <span class="record-dot" :class="'risk-dot-' + rec.risk"></span>
                <span class="record-date-col">
                  <span class="record-date">{{ formatDate(rec.date) }}</span>
                  <span class="record-time">{{ rec.time }}</span>
                </span>
                <span class="record-risk-label" :class="'risk-text-' + rec.risk">{{ riskLabel(rec.risk) }}</span>
              </button>
              <button
                v-if="groupHasMore(group)"
                type="button"
                class="record-view-all"
                @click="toggleMonthExpanded(group.month)"
              >
                {{ isMonthExpanded(group.month) ? 'Show less' : 'View more' }}
                <svg class="chevron" :class="{ open: isMonthExpanded(group.month) }" viewBox="0 0 24 24" fill="none">
                  <path d="m6 9 6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </template>
            <p v-if="!filteredRecords.length" class="record-empty">No records match these filters.</p>
          </div>

          <Transition name="detail-swap" mode="out-in">
            <div class="record-detail" v-if="selectedRecord" :key="selectedRecord.id">
              <!-- UC-15/SRS-131: on tablet & mobile the detail replaces the list as a
                   full-block overlay (see .detail-overlay-open below) instead of a
                   permanently-visible side panel, so this button is what returns to it.
                   Hidden by CSS on desktop, where the list stays visible alongside. -->
              <button type="button" class="detail-back-btn" @click="closeRecordDetail">
                <svg viewBox="0 0 24 24" fill="none"><path d="M15 6l-6 6 6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                Back to Record List
              </button>
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

      </template>

      <div v-else class="history-empty">
        <div class="history-empty-icon">
          <svg viewBox="0 0 24 24" fill="none"><path d="M3 12a9 9 0 1 0 3.5-7.1M3 4v5h5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 7v5l3.5 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <h2 class="history-empty-title">No voice analysis history is available yet</h2>
        <p class="history-empty-desc">Take your first voice test and this page will start tracking your progress over time.</p>

        <ul class="history-empty-benefits">
          <li>
            <span class="history-empty-benefit-icon"><svg viewBox="0 0 24 24" fill="none"><path d="M3 17l6-6 4 4 8-8M15 7h6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
            Track your Voice Health Score over time
          </li>
          <li>
            <span class="history-empty-benefit-icon"><svg viewBox="0 0 24 24" fill="none"><path d="M3 12h4l2-6 4 12 2-6h6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
            See patterns across your recordings
          </li>
          <li>
            <span class="history-empty-benefit-icon"><svg viewBox="0 0 24 24" fill="none"><path d="M4 20V10m8 10V4m8 16v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
            Compare sessions side by side
          </li>
        </ul>

        <button class="btn-primary" type="button" @click="router.push('/recording')">Take a Voice Test</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, h } from 'vue'
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

const records = ref([])
const isLoading = ref(true)
const loadError = ref('')

// Reads this member's saved sessions from Supabase (written by ResultView
// after each analysis) and shapes them the way the rest of this page
// expects — same fields the old mockRecords array used.
async function fetchHistoryRecords(userId) {
  const { data, error } = await supabase
    .from('voice_sessions')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: true })

  if (error) {
    loadError.value = error.message
    return []
  }

  return (data || []).map((row) => {
    const date = new Date(row.created_at)
    return {
      id: row.id,
      date,
      time: date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      risk: row.risk,
      score: row.score,
      resultLabel: row.result_label,
      metrics: row.metrics || [],
      recommendations: row.recommendations || []
    }
  })
}

onMounted(async () => {
  const { data } = await supabase.auth.getSession()
  const user = data.session?.user
  displayName.value = user?.user_metadata?.username || user?.email || 'there'

  if (user) {
    records.value = await fetchHistoryRecords(user.id)
  }
  isLoading.value = false
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
      h('circle', { cx: '12', cy: '12', r: '9', stroke: 'currentColor', 'stroke-width': '2' }),
      h('path', { d: 'M12 7v5l3 3', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
    ])
  }
  const images = { water: WaterIcon, voice: AudioIcon, warmup: MicrophoneIcon }
  return h('img', { src: images[props.kind], alt: '', class: 'glyph-img' })
}

// ── Latest record — drives the welcome header / "Today's Result" card.
// Reactive (unlike the old mockRecords-era constant) since `records` now
// loads asynchronously from Supabase after mount.
const latestRecord = computed(() =>
  records.value.length
    ? records.value.reduce((a, b) => (b.date > a.date ? b : a))
    : null
)

// ── Voice Health Score card ─────────────────────────────────────────
const scoreRanges = ['7 Days', '30 Days', 'All Time']
const selectedScoreRange = ref('7 Days')

// "N Days" means exactly N calendar days ending today — today plus the
// N-1 days before it — matching the fixed-window chart axis (chartDomain).
function withinRange(record, range, referenceDate) {
  if (range === 'All Time') return true
  const days = range === '7 Days' ? 6 : 29
  const diff = (referenceDate - record.date) / (1000 * 60 * 60 * 24)
  return diff >= 0 && diff <= days
}

const scoreFiltered = computed(() =>
  records.value
    .filter((r) => withinRange(r, selectedScoreRange.value, latestRecord.value?.date))
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
// No vertical padding: the risk bands and 0/50/100 labels must reach the
// exact top/bottom edges of the chart box, or they read as floating/detached
// from the axis numbers. Nothing clips the SVG, so a near-100 last point's
// halo (r=6) can harmlessly extend a few px past the edge on rare high scores.
const CHART_PAD_Y = 0

// The date range each point/tick is positioned against — always the actual
// first-to-last session in the filtered set, for every tab (not a fixed
// calendar window). A fixed window can leave blank space before the first
// real session while the risk-color bands still span the full width, which
// reads as a broken/incomplete chart; spanning actual data keeps the line
// and area filling the chart edge-to-edge no matter which range is picked.
// Multiple recordings on the same calendar day used to each plot as their
// own point — e.g. two sessions both on "10 Sept" produced two dots and two
// overlapping "10 Sept" x-axis labels. The line/axis now always show exactly
// one point per calendar day, averaging that day's scores together;
// `scoreFiltered` (and the stat tiles above) still count every individual
// session, so "Total sessions" etc. stay accurate.
function groupIntoDailyPoints(items) {
  const dayMap = new Map()
  for (const rec of items) {
    const key = rec.date.toDateString()
    if (!dayMap.has(key)) dayMap.set(key, [])
    dayMap.get(key).push(rec)
  }
  return [...dayMap.values()]
    .map((group) => {
      const day = new Date(group[0].date)
      day.setHours(0, 0, 0, 0)
      const avgScore = Math.round(group.reduce((sum, r) => sum + r.score, 0) / group.length)
      return {
        date: day,
        score: avgScore,
        time: group.length > 1 ? `${group.length} sessions` : group[0].time
      }
    })
    .sort((a, b) => a.date - b.date)
}

const dailyPoints = computed(() => groupIntoDailyPoints(scoreFiltered.value))

function chartDomain() {
  const items = dailyPoints.value
  if (items.length < 2) return null
  return [items[0].date, items[items.length - 1].date]
}

// Points are positioned by actual date (not by index) so they land exactly
// under their matching x-axis tick — see chartDomain/xAxisTicks below, which
// share this same domain.
function chartPoints() {
  const items = dailyPoints.value
  const usableW = CHART_W - CHART_PAD * 2
  const usableH = CHART_H - CHART_PAD_Y * 2
  // A single session has no real span to plot against (chartDomain needs two
  // dates to define a range), so without this the whole chart used to render
  // with zero points — no dot at all — even though the stat boxes above it
  // (which read scoreFiltered directly, not chartPoints) correctly counted
  // it. Center the lone point instead of dropping it.
  if (items.length === 1) {
    const rec = items[0]
    const x = CHART_PAD + usableW / 2
    const y = CHART_PAD_Y + usableH * (1 - rec.score / 100)
    return [{ x, y, score: rec.score, date: rec.date, time: rec.time }]
  }
  const domain = chartDomain()
  if (!domain) return null
  const [start, end] = domain
  const span = end - start || 1
  return items.map((rec) => {
    const x = CHART_PAD + usableW * ((rec.date - start) / span)
    const y = CHART_PAD_Y + usableH * (1 - rec.score / 100)
    return { x, y, score: rec.score, date: rec.date, time: rec.time }
  })
}

// Score-based color band: red < 50, yellow 50–69, green >= 70.
// This is independent of a record's overall `risk` field (which can factor
// in more than the score alone) — the chart color must track the score value.
function scoreBand(score) {
  if (score >= 70) return 'low'
  if (score >= 50) return 'moderate'
  return 'high'
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
  const baseline = CHART_H - CHART_PAD_Y
  return `${smoothLinePath(pts)} L${pts[pts.length - 1].x},${baseline} L${pts[0].x},${baseline} Z`
})

// All points as % positions (not raw SVG coords, since these render as HTML
// elements overlaid on the chart, not <circle>s inside the SVG), each keeping
// its score, color band, and session date/time so the tooltip can show all
// three. The last point is flagged so it can still stand out with its own
// halo + bigger dot.
const chartPointsFull = computed(() => {
  const pts = chartPoints()
  if (!pts) return []
  return pts.map((pt, i) => ({
    left: (pt.x / CHART_W) * 100,
    top: (pt.y / CHART_H) * 100,
    score: pt.score,
    band: scoreBand(pt.score),
    date: pt.date,
    time: pt.time,
    isLast: i === pts.length - 1
  }))
})

function riskLabel(risk) {
  return { low: 'Low Risk', moderate: 'Moderate Risk', high: 'High Risk' }[risk] || ''
}

// The score shows on hover (dismissed on mouse leave, handled by
// CSS :hover below) AND on click (persists until the member clicks outside).
// Both can be true independently — hover works regardless of click state.
const activeTooltipIndex = ref(null)
function toggleTooltip(i) {
  activeTooltipIndex.value = activeTooltipIndex.value === i ? null : i
}
// Point indices get reused across ranges (v-for :key="i"), so a pinned
// tooltip from one range's point list could otherwise appear to "jump" onto
// an unrelated point when the member switches ranges.
watch(selectedScoreRange, () => { activeTooltipIndex.value = null })

// ── X-axis date ticks ────────────────────────────────────────────────
// Ticks are always picked from actual session dates, evenly by index (so the
// first and last sessions — the chart's own edges — are always labeled)
// rather than a fixed calendar grid — a tick's date always comes from a real
// point, so it lands exactly under it. 7 Days keeps up to 5 labels (it's rarely
// more than a handful of sessions); 30 Days and All Time cap at 2
// (start/end only) since hovering or tapping any point already surfaces its
// exact date, so a busier axis there would just be clutter.
function maxTicksFor(range) {
  return range === '7 Days' ? 5 : 2
}
function formatTick(date) {
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

const xAxisTicks = computed(() => {
  const items = dailyPoints.value
  // Same single-point case as chartPoints above: there's no real domain to
  // position against, so just center the one tick under the one dot.
  if (items.length === 1) {
    return [{ left: 50, label: formatTick(items[0].date) }]
  }
  const domain = chartDomain()
  if (!domain) return []
  const [start, end] = domain
  const span = end - start || 1

  const tickCount = Math.min(items.length, maxTicksFor(selectedScoreRange.value))
  const indices = new Set()
  for (let k = 0; k < tickCount; k++) {
    indices.add(tickCount === 1 ? 0 : Math.round((k * (items.length - 1)) / (tickCount - 1)))
  }
  return [...indices].map((idx) => ({
    left: ((items[idx].date - start) / span) * 100,
    label: formatTick(items[idx].date)
  }))
})

// Score-to-y uses the same mapping as gridLines below, so the bands line up
// exactly with the 0/50/100 axis labels regardless of chart height.
function scoreToY(score) {
  const usableH = CHART_H - CHART_PAD_Y * 2
  return CHART_PAD_Y + usableH * (1 - score / 100)
}

// Thresholds: green >= 70, yellow 50–69, red < 50.
const riskBands = computed(() => {
  const yTop = scoreToY(100)
  const yLowBoundary = scoreToY(70)
  const yModerateBoundary = scoreToY(50)
  const yBottom = scoreToY(0)
  return [
    { level: 'low', y: yTop, height: yLowBoundary - yTop, color: 'rgba(34, 197, 94, 0.14)' },
    { level: 'moderate', y: yLowBoundary, height: yModerateBoundary - yLowBoundary, color: 'rgba(245, 166, 35, 0.14)' },
    { level: 'high', y: yModerateBoundary, height: yBottom - yModerateBoundary, color: 'rgba(239, 68, 68, 0.14)' }
  ]
})

const gridLines = computed(() => {
  const usableH = CHART_H - CHART_PAD_Y * 2
  return [100, 50, 0].map((v) => {
    const y = CHART_PAD_Y + usableH * (1 - v / 100)
    return { label: String(v), y, pct: (y / CHART_H) * 100 }
  })
})

// ── Record List card ────────────────────────────────────────────────
const dateFilter = ref('All Time')
const riskFilter = ref('all')
const selectedId = ref(null)
// Once records finish loading, default the selection to the latest record
// (mirrors the old static `ref(latestRecord?.id ?? null)` init, which only
// worked because mockRecords was available synchronously at setup time).
watch(records, (list) => {
  if (selectedId.value == null && list.length) selectedId.value = latestRecord.value?.id ?? null
})

// UC-15/SRS-131: on tablet & mobile, tapping a record opens its detail as a
// full-block overlay in place of the list (closed via the Back button) rather
// than a side panel that's always visible — desktop ignores this flag (CSS
// keeps the side-by-side layout there regardless, see .detail-overlay-open).
const mobileDetailOpen = ref(false)
function openRecordDetail(id) {
  selectedId.value = id
  mobileDetailOpen.value = true
}
function closeRecordDetail() {
  mobileDetailOpen.value = false
}
// UC-15 SRS-144: only drop back to the list when the previously selected
// record no longer matches the new filters — if it still matches, the
// detail stays open.
watch([dateFilter, riskFilter], () => {
  const stillMatches = filteredRecords.value.some((r) => r.id === selectedId.value)
  if (!stillMatches) mobileDetailOpen.value = false
})

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
const showScoreInfo = ref(false)
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
  records.value
    .filter((r) => withinRange(r, dateFilter.value, latestRecord.value?.date))
    .filter((r) => riskFilter.value === 'all' || r.risk === riskFilter.value)
    .sort((a, b) => b.date - a.date)
)

const groupedRecords = computed(() => {
  const groups = new Map()
  for (const rec of filteredRecords.value) {
    // Includes the year so e.g. July 2025 and July 2026 don't merge into one group.
    const key = rec.date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(rec)
  }
  return Array.from(groups, ([month, items]) => ({ month, items }))
})

// Each month group shows at most this many records, with a "View all" toggle
// to reveal the rest — keeps a busy month from pushing the record detail
// panel far down the page.
const RECORD_PAGE_SIZE = 3
const expandedMonths = ref(new Set())
function isMonthExpanded(month) {
  return expandedMonths.value.has(month)
}
function toggleMonthExpanded(month) {
  const next = new Set(expandedMonths.value)
  if (next.has(month)) next.delete(month)
  else next.add(month)
  expandedMonths.value = next
}
function visibleGroupItems(group) {
  if (isMonthExpanded(group.month) || group.items.length <= RECORD_PAGE_SIZE) return group.items
  return group.items.slice(0, RECORD_PAGE_SIZE)
}
function groupHasMore(group) {
  return group.items.length > RECORD_PAGE_SIZE
}

const selectedRecord = computed(
  () => filteredRecords.value.find((r) => r.id === selectedId.value) || filteredRecords.value[0] || null
)

function riskIconBgClass(risk) {
  return risk === 'low' ? 'status-icon-healthy' : 'risk-bg-' + risk
}

function priorityLabel(priority) {
  return priority === 'high' ? 'High' : 'Moderate'
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

.title-with-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-wrap { position: relative; }

.score-info-btn {
  border: none;
  background: transparent;
  padding: 2px;
  color: #00000055;
  display: inline-flex;
  cursor: pointer;
}

.score-info-btn:hover { color: #00000088; }
.score-info-btn svg { width: 16px; height: 16px; }

.score-info-popover {
  position: absolute;
  top: calc(100% + 20px);
  left: 0;
  z-index: 10;
  width: 240px;
  background: #fff;
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 8px 24px rgba(30, 41, 59, 0.14);
  border: 1px solid rgba(101, 148, 228, 0.14);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.score-info-popover strong { font-size: 12.5px; color: #1a1a2e; }
.score-info-popover span { font-size: 11.5px; color: #6b7690; line-height: 1.5; }

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
  /* card-header's space-between only keeps this in the top-right corner
     while it shares a row with the title; once .card-header wraps it onto
     its own line at narrow widths, space-between has nothing left to push
     against and it falls to the left instead — pin it right explicitly. */
  margin-left: auto;
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
  /* Stretch so the chart box matches the stat-tiles column height. The SVG
     itself now fills that height directly (height: 100%, see .chart-svg)
     instead of deriving it from aspect-ratio, so there's no dead gap. */
  align-items: stretch;
}

.score-chart {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: #f8faff;
  border: 1px solid rgba(101, 148, 228, 0.12);
  border-radius: 14px;
  padding: 14px 16px 10px 6px;
  min-height: 90px;
  /* A tooltip on a high-scoring point pops up far enough to overlap the
     range pills above (see .card-header) — those pills have their own
     z-index (see .pill-btn), so without this the tooltip would paint
     underneath them instead of on top. */
  position: relative;
  z-index: 2;
}

.chart-row {
  display: flex;
  align-items: stretch;
  gap: 6px;
  flex: 1;
  min-height: 0;
}

/* Mirrors .chart-row's gutter so the date ticks below line up under the
   chart plot rather than under the (wider) row that includes the y-axis. */
.x-axis-row {
  display: flex;
  gap: 6px;
}

.x-axis-spacer {
  width: 22px;
  flex-shrink: 0;
}

.x-axis-labels {
  position: relative;
  flex: 1;
  min-width: 0;
  height: 14px;
}

.x-axis-label {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  font-size: 9.5px;
  font-weight: 700;
  color: #7c879e;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.x-axis-label:first-child { transform: translateX(0); }
.x-axis-label:last-child { transform: translateX(-100%); }

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
  font-weight: 700;
  color: #7c879e;
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
  /* Fills the height .chart-plot is stretched to (matching the stat-tiles
     column, see .score-body) rather than deriving height from the 600:170
     viewBox via aspect-ratio — that made the SVG's own box shorter than its
     stretched container, leaving a dead gap with "0" floating below the
     actual bands. Point markers are plain HTML circles (see chart-point-marker
     etc.), not SVG <circle>s, so this non-uniform scaling can't squash them. */
  height: 100%;
  min-height: 150px;
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

/* Each point is a hit-target wrapper (bigger than the visible dot, for an
   easier hover/click target) positioned by % over .chart-plot — plain HTML,
   not SVG <circle>s, so it stays perfectly round even though the SVG box
   beneath it can be stretched to a non-600:170 aspect ratio (see max-height
   cap on .chart-svg above). */
.chart-point-wrap {
  position: absolute;
  width: 22px;
  height: 22px;
  transform: translate(-50%, -50%);
  cursor: pointer;
}

.chart-point-marker,
.chart-dot-halo,
.chart-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  pointer-events: none;
}

.chart-point-marker {
  width: 11px;
  height: 11px;
  background: #fff;
  border: 2.5px solid #4a7fdb;
}

.chart-dot-halo {
  width: 16px;
  height: 16px;
  background: rgba(101, 148, 228, 0.22);
}

.chart-dot {
  width: 11px;
  height: 11px;
  background: #6594e4;
  border: 2px solid #fff;
}

/* Tooltip: hidden by default, shown on hover (reverts on mouse
   leave via plain CSS) or while its point is the click-activated one
   (.is-active — persists until an outside click clears it). */
.chart-tooltip {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%) translateY(4px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  background: #fff;
  padding: 5px 10px;
  border-radius: 10px;
  border: 1px solid rgba(101, 148, 228, 0.25);
  box-shadow: 0 4px 10px rgba(101, 148, 228, 0.18);
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.12s ease, transform 0.12s ease;
  z-index: 5;
}

.chart-point-wrap:hover .chart-tooltip,
.chart-point-wrap.is-active .chart-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(0);
}

/* Clamp the first/last point's tooltip to the chart's own edge instead of
   centering on the point — centered would overflow past the card and get
   clipped/overlap the y-axis labels for points that sit right at x=0/100%. */
.chart-point-wrap:first-child .chart-tooltip {
  left: 0;
  transform: translateY(4px);
}
.chart-point-wrap:first-child:hover .chart-tooltip,
.chart-point-wrap:first-child.is-active .chart-tooltip {
  transform: translateY(0);
}

.chart-point-wrap:last-child .chart-tooltip {
  left: auto;
  right: 0;
  transform: translateY(4px);
}
.chart-point-wrap:last-child:hover .chart-tooltip,
.chart-point-wrap:last-child.is-active .chart-tooltip {
  transform: translateY(0);
}

.tooltip-date {
  font-size: 10px;
  font-weight: 600;
  color: #9aa4bd;
  font-variant-numeric: tabular-nums;
}

.tooltip-score {
  font-size: 12px;
  font-weight: 700;
  color: #1a1a2e;
  font-variant-numeric: tabular-nums;
}

.tooltip-risk {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
}

.tooltip-risk-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
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
  /* Keeps the whole group flush right when .card-header wraps it onto its
     own line (narrow screens) — without this it just piles up on the left,
     since it's the sole item on that flex line at that point. On wide
     screens this is a no-op: .card-header's space-between already pushes
     it right, and an auto margin on the last/only item lands in the same
     place free space would already put it. */
  margin-left: auto;
}

/* Matches .dropdown-trigger's shape/border exactly so it reads as one of the
   same set of controls; always disabled, so no separate :disabled override
   or "Coming soon" badge — the dimmed look plus the hover tooltip says enough. */
.btn-export {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(101, 148, 228, 0.25);
  background: #fff;
  border-radius: 16px;
  padding: 8px 14px;
  font-family: 'Poppins', sans-serif;
  font-size: 12.5px;
  font-weight: 600;
  color: #8a94a8;
  opacity: 0.6;
  cursor: not-allowed;
}

.export-icon {
  width: 14px;
  height: 14px;
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

.record-group-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin: 16px 0 6px;
  padding-top: 14px;
  border-top: 1px solid #eef1f8;
}

.record-group-header:first-child {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.record-group-label {
  font-size: 12.5px;
  font-weight: 600;
  color: #9aa4bd;
  margin: 0;
}

.record-group-count {
  font-size: 11px;
  font-weight: 600;
  color: #9aa4bd;
  white-space: nowrap;
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

.record-risk-label {
  font-size: 11.5px;
  font-weight: 600;
  white-space: nowrap;
  margin-left: auto;
  /* No room for this in the narrow desktop sidebar list; shown once the
     list is full-width (860px breakpoint below). */
  display: none;
}

.record-view-all {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  align-self: flex-start;
  border: none;
  background: transparent;
  padding: 6px 4px;
  margin-top: 2px;
  font-family: 'Poppins', sans-serif;
  font-size: 11.5px;
  font-weight: 600;
  color: #6594e4;
  cursor: pointer;
}

.record-view-all:hover { text-decoration: underline; }

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

/* Only meaningful once the detail becomes a full-block overlay on tablet/
   mobile (see .detail-overlay-open below) — desktop keeps the list visible
   alongside the detail, so there's nothing to "go back" to. */
.detail-back-btn {
  display: none;
  align-self: flex-start;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  padding: 6px 4px;
  margin-bottom: 14px;
  font-family: 'Poppins', sans-serif;
  font-size: 12.5px;
  font-weight: 600;
  color: #6594e4;
  cursor: pointer;
}

.detail-back-btn svg {
  width: 16px;
  height: 16px;
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

/* ── Empty state (UC-12 [2E]: no voice analysis records yet) ── */
.history-container-empty {
  flex: 1;
  justify-content: center;
  min-height: calc(100vh - 64px);
}

/* ── Loading state — real history is being fetched from Supabase. A bare
   "Loading…" line used to sit alone on the page background; this gives it
   the same card treatment as the empty state below plus a spinning ring,
   so the page never looks blank/broken while data is in flight. */
.history-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  background: #fff;
  border-radius: 20px;
  border: 1px solid rgba(101, 148, 228, 0.14);
  box-shadow: 0 4px 24px rgba(101, 148, 228, 0.1);
  padding: 64px 32px;
  max-width: 520px;
  margin: 0 auto;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 4px solid rgba(101, 148, 228, 0.16);
  border-top-color: #6594e4;
  animation: history-spin 0.8s linear infinite;
}

.loading-text {
  font-size: 13.5px;
  font-weight: 600;
  color: #6b7690;
  margin: 0;
  animation: history-loading-pulse 1.6s ease-in-out infinite;
}

@keyframes history-spin {
  to { transform: rotate(360deg); }
}

@keyframes history-loading-pulse {
  0%, 100% { opacity: 0.55; }
  50% { opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
  .loading-spinner { animation-duration: 1.6s; }
  .loading-text { animation: none; }
}

.history-empty {
  background: #fff;
  border-radius: 20px;
  border: 1px solid rgba(101, 148, 228, 0.14);
  box-shadow: 0 4px 24px rgba(101, 148, 228, 0.1);
  padding: 56px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 6px;
  max-width: 520px;
  margin: 0 auto;
}

.history-empty-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a5c4f7 0%, #6594e4 100%);
  color: #fff;
  box-shadow: 0 6px 18px rgba(101, 148, 228, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
}

.history-empty-icon svg {
  width: 32px;
  height: 32px;
}

.history-empty-title {
  font-size: 19px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.history-empty-desc {
  font-size: 13.5px;
  font-weight: 500;
  color: #8b96ad;
  line-height: 1.6;
  margin: 8px 0 22px;
  max-width: 340px;
}

.history-empty-benefits {
  list-style: none;
  margin: 0 0 28px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-self: stretch;
  text-align: left;
}

.history-empty-benefits li {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  font-weight: 500;
  color: #444;
}

.history-empty-benefit-icon {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: #eaf1ff;
  color: #6594e4;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.history-empty-benefit-icon svg {
  width: 16px;
  height: 16px;
}

.history-empty .btn-primary {
  border: none;
  background: linear-gradient(102deg, #95b9f7 8.63%, #6594e4 92.33%);
  color: #fff;
  border-radius: 14px;
  padding: 13px 32px;
  font-family: 'Poppins', sans-serif;
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
}

.history-empty .btn-primary:hover { opacity: 0.9; }

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
  }
  /* Full-width rows now have room to show each record's risk label too
     (hidden by default for the narrow desktop sidebar; the group count is
     shown at every width). */
  .record-risk-label {
    display: inline;
  }

  /* UC-15/SRS-131: the detail is hidden until a record is tapped, then
     replaces the list and its filter header in place (Back button returns to
     them) instead of sitting permanently beside the list as on desktop. List
     and detail are never shown at once here, so this is a plain display
     toggle, not a true overlay — no absolute positioning needed. The filter
     header hides too, since a date/risk filter has nothing to act on while
     viewing a single record's detail. */
  .record-detail {
    display: none;
  }
  .detail-overlay-open .card-header,
  .detail-overlay-open .record-list {
    display: none;
  }
  .detail-overlay-open .record-detail {
    display: flex;
  }
  .detail-back-btn {
    display: inline-flex;
  }
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
