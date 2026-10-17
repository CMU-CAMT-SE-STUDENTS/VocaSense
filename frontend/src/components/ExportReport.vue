<template>
  <div class="export-root" aria-hidden="true">
    <!-- Off-screen print layout captured by exportReport() for PNG. Fixed
         794px width (A4 at 96dpi) so it looks the same at any viewport. Kept
         inside the root div: a comment above it makes this a multi-root
         component and `$el` stops being the element (breaks the History ref).
         It renders the same report model exportPdf.js draws (utils/exportModel.js). -->

    <template v-if="report">
      <section v-for="(page, i) in pages" :key="i" class="report-page" data-report-page>
        <template v-for="r in [page.report]" :key="0">
        <header class="rp-header">
          <div class="rp-head-left">
            <img :src="logoUrl" alt="VocaSense" class="rp-logo" />
            <h1 class="rp-title">Voice Analysis Report</h1>
            <p class="rp-meta">{{ r.meta }}</p>
          </div>
          <p class="rp-date"><span class="rp-date-label">{{ r.headerDate.label }}</span><br />{{ r.headerDate.lines[0] }}<br />{{ r.headerDate.lines[1] }}</p>
        </header>

        <!-- ───────── single session ───────── -->
        <template v-if="page.kind === 'single'">
          <div class="rp-status">
            <h2 class="rp-status-title">Voice Health Status</h2>
            <p v-if="r.score !== null" class="rp-score" :class="'risk-text-' + r.scoreLevel">
              {{ r.scoreText }} <span class="rp-score-of">/ 100</span>
            </p>
            <span class="rp-badge" :class="'risk-bg-' + r.risk">{{ r.resultLabel }}</span>
            <p v-if="r.subtitle" class="rp-status-sub">{{ r.subtitle }}</p>
          </div>

          <div class="rp-metrics">
            <div v-for="m in r.metrics" :key="m.kind" class="rp-metric" :class="'metric-bg-' + m.level">
              <span class="rp-metric-name">{{ m.label }}<template v-if="m.scoreText">: {{ m.scoreText }}</template></span>
              <strong class="rp-metric-value" :class="'risk-text-' + m.level">{{ m.value }}</strong>
            </div>
          </div>

          <h3 v-if="r.recommendations.length" class="rp-section">Personalized Recommendations</h3>
          <div v-if="r.recommendations.length" class="rp-recs">
            <div v-for="r in r.recommendations" :key="r.text" class="rp-rec" :class="'priority-bg-' + r.priority">
              <span class="rp-rec-dot" :class="'priority-dot-' + r.priority"></span>
              <span class="rp-rec-text">{{ r.text }}</span>
              <span class="rp-rec-prio" :class="'priority-text-' + r.priority">{{ r.priority === 'high' ? 'High' : 'Moderate' }} Priority</span>
            </div>
          </div>

          <template v-if="r.acoustic.length || r.context.length || r.baselineFactors.length">
            <h3 class="rp-section rp-section-center">{{ r.acoustic.length ? 'Acoustic Measurement & Assessment Context' : 'Assessment Context' }}</h3>
            <div class="rp-context">
              <table v-if="r.acoustic.length" class="rp-table">
                <thead>
                  <tr><th>Feature</th><th>Reference</th><th>Value</th></tr>
                </thead>
                <tbody>
                  <tr v-for="row in r.acoustic" :key="row.name">
                    <td>{{ row.name }}</td>
                    <td>{{ row.reference }}</td>
                    <td :class="row.abnormal ? ['rp-abnormal', 'risk-text-' + row.level] : ''">{{ row.value }}</td>
                  </tr>
                </tbody>
              </table>

              <div v-if="r.context.length || r.baselineFactors.length" class="rp-facts">
                <template v-if="r.context.length">
                  <h4 class="rp-facts-title">Recording Context</h4>
                  <p v-for="f in r.context" :key="f.label" class="rp-fact"><strong>{{ f.label }}:</strong> {{ f.value }}</p>
                </template>
                <template v-if="r.baselineFactors.length">
                  <h4 class="rp-facts-title rp-facts-title-gap">Relevant Baseline Factors</h4>
                  <p v-for="f in r.baselineFactors" :key="f.label" class="rp-fact"><strong>{{ f.label }}:</strong> {{ f.value }}</p>
                </template>
              </div>
            </div>
          </template>
        </template>

        <!-- ───────── multi-session summary ───────── -->
        <template v-else-if="page.kind === 'summary'">
          <h2 class="rp-big-title">Analysis Summary</h2>

          <p class="rp-chart-title">Overall voice quality score</p>
          <div class="rp-legend">
            <span v-for="b in r.chart.bands" :key="b.level" class="rp-legend-item">
              <i :class="'band-swatch-' + b.level"></i>{{ b.label }}
            </span>
          </div>
          <svg class="rp-chart" :viewBox="`0 0 ${CW} ${CH}`" xmlns="http://www.w3.org/2000/svg">
            <rect v-for="b in r.chart.bands" :key="b.level" :x="PL" :width="CW - PL - PR" :y="yPos(b.to / 100)" :height="yPos(b.from / 100) - yPos(b.to / 100)" :class="'band-fill-' + b.level" />
            <g v-for="t in r.chart.yTicks" :key="t">
              <line :x1="PL" :x2="CW - PR" :y1="yPos(t / 100)" :y2="yPos(t / 100)" stroke="#e6eaf2" stroke-width="1" />
              <text :x="PL - 8" :y="yPos(t / 100) + 4" text-anchor="end" class="rp-axis">{{ t }}</text>
            </g>
            <text v-for="t in r.chart.xTicks" :key="t.label + t.x" :x="xPos(t.x)" :y="CH - 8" text-anchor="middle" class="rp-axis">{{ t.label }}</text>
            <polyline v-if="r.chart.points.length > 1" :points="r.chart.points.map((p) => `${xPos(p.x)},${yPos(p.y)}`).join(' ')" fill="none" :stroke="r.chart.color" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round" />
            <circle v-for="(p, k) in r.chart.points" :key="k" :cx="xPos(p.x)" :cy="yPos(p.y)" r="4" :class="'dot-' + p.level" stroke="#fff" stroke-width="1.2" />
          </svg>

          <h3 class="rp-section">Summary</h3>
          <div class="rp-stats">
            <div class="rp-stat">
              <span class="rp-stat-label">Average score</span>
              <strong class="rp-stat-value" :class="r.summary.average.level ? 'risk-text-' + r.summary.average.level : ''">{{ r.summary.average.score }}</strong>
              <span class="rp-stat-sub">across {{ r.sessionCount }} sessions</span>
            </div>
            <div class="rp-stat">
              <span class="rp-stat-label">Highest score</span>
              <strong class="rp-stat-value" :class="r.summary.highest.level ? 'risk-text-' + r.summary.highest.level : ''">{{ r.summary.highest.score }}</strong>
              <span class="rp-stat-sub">{{ r.summary.highest.date }}</span>
            </div>
            <div class="rp-stat">
              <span class="rp-stat-label">Lowest score</span>
              <strong class="rp-stat-value" :class="r.summary.lowest.level ? 'risk-text-' + r.summary.lowest.level : ''">{{ r.summary.lowest.score }}</strong>
              <span class="rp-stat-sub">{{ r.summary.lowest.date }}</span>
            </div>
          </div>
          <div class="rp-risk">
            <span class="risk-bg-high">High risk: {{ r.riskCounts.high }}</span>
            <span class="risk-bg-moderate">Moderate risk: {{ r.riskCounts.moderate }}</span>
            <span class="risk-bg-low">Low risk: {{ r.riskCounts.low }}</span>
          </div>

          <template v-if="r.baseline.rows.length">
            <h3 class="rp-section">Baseline Context</h3>
            <p class="rp-note">Profile as retrieved on {{ r.baseline.retrievedAt }} — may differ from when older sessions were recorded.</p>
            <div class="rp-baseline">
              <p v-for="f in r.baseline.rows" :key="f.label" class="rp-fact"><strong>{{ f.label }}:</strong> {{ f.value }}</p>
            </div>
          </template>
        </template>

        <!-- ───────── session comparison (paginated) ───────── -->
        <template v-else>
          <h2 class="rp-big-title">Session Comparison</h2>
          <table class="rp-table rp-compare">
            <thead>
              <tr><th>Session</th><th>Voice quality</th><th>Clarity</th><th>Stability</th><th>Hoarseness</th><th>VQ change</th></tr>
            </thead>
            <tbody>
              <tr v-for="row in page.rows" :key="row.session">
                <td>{{ row.session }}</td>
                <td :class="'risk-text-' + row.quality.level"><strong>{{ row.quality.text }}</strong></td>
                <td :class="row.clarity.level ? 'risk-text-' + row.clarity.level : ''">{{ row.clarity.text }}</td>
                <td :class="row.stability.level ? 'risk-text-' + row.stability.level : ''">{{ row.stability.text }}</td>
                <td :class="row.hoarseness.level ? 'risk-text-' + row.hoarseness.level : ''">{{ row.hoarseness.text }}</td>
                <td :class="row.change.level ? 'risk-bg-' + row.change.level : ''">{{ row.change.text }}</td>
              </tr>
            </tbody>
          </table>
          <p class="rp-note">Voice quality, clarity and stability: higher is better. Hoarseness is a risk score: lower is better. VQ change compares each session with the one before it.</p>
        </template>

        <p class="rp-foot-disclaimer"><strong>Medical disclaimer:</strong> {{ DISCLAIMER }}</p>
        <footer class="rp-footer">
          <span>Generated by VocaSense · Report exported on {{ longDate(r.generatedAt) }}, {{ clockTime(r.generatedAt) }}<template v-if="versionFor(r)"> · {{ versionFor(r) }}</template></span>
          <span v-if="pages.length > 1">{{ i + 1 }} / {{ pages.length }}</span>
        </footer>
        </template>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import logoUrl from '@/assets/icons/logo.png'
import { DISCLAIMER, longDate, clockTime } from '@/utils/exportModel'

const props = defineProps({
  // Report model from buildReport() in utils/exportModel.js, or null.
  report: { type: Object, default: null }
})

// Pages are derived from the model so the PNG matches the PDF page for page.
// `report` supplies each page's header (detail pages carry their own).
const pages = computed(() => {
  const r = props.report
  if (!r) return []
  if (r.type === 'single') return [{ kind: 'single', report: r }]
  return [
    { kind: 'summary', report: r },
    ...r.comparisonPages.map((rows) => ({ kind: 'comparison', report: r, rows })),
    ...r.details.map((detail) => ({ kind: 'single', report: detail }))
  ]
})

function versionFor(r) {
  const v = r.type === 'single' ? (r.scoringVersion ? [r.scoringVersion] : []) : r.scoringVersions
  return v.length ? `scoring v${v.join(', v')}` : ''
}

// Chart: 0..1 model coordinates → SVG pixels.
const CW = 690
const CH = 250
const PL = 38
const PR = 14
const PT = 10
const PB = 28
const xPos = (x) => PL + x * (CW - PL - PR)
const yPos = (y) => PT + (1 - y) * (CH - PT - PB)
</script>

<style scoped>
.export-root {
  position: fixed;
  left: -10000px;
  top: 0;
  pointer-events: none;
  font-family: 'Poppins', sans-serif;
}

.report-page {
  box-sizing: border-box;
  width: 794px;
  min-height: 1123px;
  padding: 44px 52px 32px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: #1a1a2e;
}

.rp-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 12px;
  border-bottom: 3px solid #a9bfe3;
}
.rp-logo { height: 34px; width: auto; display: block; }
.rp-title { margin: 6px 0 0; font-size: 26px; font-weight: 700; }
.rp-date { margin: 0; font-size: 12.5px; font-weight: 600; color: #6b7690; text-align: right; line-height: 1.6; }
.rp-date-label { font-size: 10.5px; font-weight: 600; letter-spacing: 0.4px; text-transform: uppercase; color: #8b96ad; }
.rp-meta { margin: 4px 0 0; font-size: 11.5px; font-weight: 600; color: #7b869c; }

.rp-status { text-align: center; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 6px 0 0; }
.rp-status-title { margin: 0; font-size: 22px; font-weight: 700; }
.rp-score { margin: 0; font-size: 46px; font-weight: 700; line-height: 1.15; }
.rp-score-of { font-size: 30px; }
.rp-badge { padding: 6px 22px; border-radius: 20px; font-size: 13px; font-weight: 600; }
.rp-status-sub { margin: 0; font-size: 12px; font-weight: 500; color: #6b7590; }

.rp-metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.rp-metric {
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.rp-metric-name { font-size: 12px; font-weight: 500; color: #5b6680; }
.rp-metric-value { font-size: 18px; font-weight: 700; }

.rp-section { margin: 6px 0 0; font-size: 16px; font-weight: 700; }
.rp-section-center { text-align: center; font-size: 17px; margin-top: 10px; padding-top: 12px; border-top: 1px solid #c9d6ee; }
.rp-recs { display: flex; flex-direction: column; gap: 7px; }
.rp-rec { display: flex; align-items: center; gap: 12px; border-radius: 12px; padding: 10px 14px; }
.rp-rec-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.rp-rec-text { flex: 1; font-size: 12.5px; font-weight: 600; line-height: 1.5; }
.rp-rec-prio { font-size: 10.5px; font-weight: 600; white-space: nowrap; }

.rp-context { display: grid; grid-template-columns: 1.4fr 1fr; gap: 22px; align-items: start; }
.rp-table { border-collapse: collapse; width: 100%; font-size: 11px; }
.rp-table th, .rp-table td { border: 1px solid #1a1a2e; padding: 6px 8px; text-align: left; }
.rp-table th { font-weight: 700; background: #f4f7ff; }
.rp-table td { white-space: nowrap; }
.rp-abnormal { font-weight: 700; }
.rp-facts { border-left: 1px solid #c9d6ee; padding-left: 18px; }
.rp-facts-title { margin: 0 0 6px; font-size: 13px; font-weight: 700; }
.rp-facts-title-gap { margin-top: 14px; }
.rp-fact { margin: 0 0 3px; font-size: 11.5px; line-height: 1.5; }

.rp-big-title { margin: 6px 0 0; text-align: center; font-size: 28px; font-weight: 700; }
.rp-legend { display: flex; justify-content: center; flex-wrap: wrap; gap: 6px 18px; font-size: 11px; color: #4a5470; }
.rp-legend-item { display: inline-flex; align-items: center; gap: 6px; }
.rp-legend-item i { width: 12px; height: 9px; border-radius: 2px; display: inline-block; }
.rp-chart { width: 100%; height: auto; display: block; }
.rp-axis { font-size: 10.5px; fill: #6b7690; font-family: 'Poppins', sans-serif; }

.rp-chart-title { margin: 0; text-align: center; font-size: 12.5px; font-weight: 600; color: #4a5470; }
.band-swatch-low { background: #dff4e8; border: 1px solid #1f9d5b; }
.band-swatch-moderate { background: #fdebd6; border: 1px solid #b7791f; }
.band-swatch-high { background: #fbdcd7; border: 1px solid #c83d3d; }
.band-fill-low { fill: #eefaf3; }
.band-fill-moderate { fill: #fff6e9; }
.band-fill-high { fill: #fdeeec; }
.dot-low { fill: #1f9d5b; }
.dot-moderate { fill: #b7791f; }
.dot-high { fill: #c83d3d; }

.rp-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.rp-stat { border: 1px solid #dde4f2; border-radius: 14px; padding: 12px 16px; display: flex; flex-direction: column; gap: 2px; }
.rp-stat-label { font-size: 11.5px; font-weight: 500; color: #5b6680; }
.rp-stat-value { font-size: 26px; font-weight: 700; line-height: 1.2; }
.rp-stat-sub { font-size: 10.5px; color: #8b96ad; min-height: 1.2em; }
.rp-risk { display: flex; gap: 10px; flex-wrap: wrap; }
.rp-risk span { padding: 4px 12px; border-radius: 14px; font-size: 11.5px; font-weight: 600; }
.rp-note { margin: 0; font-size: 10.5px; color: #8b96ad; }
.rp-baseline { display: grid; grid-template-columns: 1fr 1fr; gap: 2px 24px; padding-left: 8px; }

.rp-compare th { text-align: center; }
.rp-compare td { text-align: center; }
.rp-compare td:first-child { text-align: left; white-space: nowrap; }

.rp-foot-disclaimer { margin: auto 0 0; font-size: 9px; line-height: 1.5; color: #a3acbf; }
.rp-footer {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  padding-top: 10px;
  border-top: 1px solid #c9d6ee;
  font-size: 10.5px;
  font-weight: 500;
  color: #8b96ad;
}
.rp-foot-disclaimer + .rp-footer { margin-top: 6px; }

.risk-bg-low { background: #e3f7ec; color: #1f9d5b; }
.risk-bg-moderate { background: #ffe9d2; color: #b7691f; }
.risk-bg-high { background: #fdd9d3; color: #c83d3d; }
.risk-text-low { color: #1f9d5b; }
.risk-text-moderate { color: #b7791f; }
.risk-text-high { color: #c83d3d; }
.metric-bg-low { background: linear-gradient(135deg, #ffffff 3%, #f1ffee 66%, #e0ffe0 100%); }
.metric-bg-moderate { background: linear-gradient(135deg, #ffffff 3%, #fffdf4 66%, #fff5e0 100%); }
.metric-bg-high { background: linear-gradient(135deg, #ffffff 3%, #fff4f4 66%, #ffe0e0 100%); }
.priority-bg-high { background: #ffe5e0; }
.priority-bg-moderate { background: #fff5e0; }
.priority-dot-high { background: linear-gradient(135deg, #ff8686, #f43333); }
.priority-dot-moderate { background: linear-gradient(135deg, #ffb886, #f47033); }
.priority-text-high { color: #c83d3d; }
.priority-text-moderate { color: #c68e3f; }
</style>
