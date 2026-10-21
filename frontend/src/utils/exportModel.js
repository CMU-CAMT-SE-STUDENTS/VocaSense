// Turns raw analysis / assessment / baseline data into the "report model" that
// both renderers use (ExportReport.vue for PNG, exportPdf.js for PDF), so the
// two outputs can never drift apart. Pure functions only — no DOM, no jsPDF.
//
// Two report shapes (Feature #7):
//   • single  – one session: status, metrics, recommendations, acoustic table,
//               recording context, relevant baseline factors
//   • summary – 2+ sessions: trend chart, summary, baseline context,
//               a session-comparison table (paginated), then one single-session
//               detail page per selected record

export const DISCLAIMER =
  'This platform provides preliminary voice health insights and does not replace professional medical diagnosis. Please consult a healthcare professional for medical concerns.'

export const COMPARISON_ROWS_PER_PAGE = 22

// ── small helpers ────────────────────────────────────────────────────

const pad2 = (n) => String(n).padStart(2, '0')

export function shortDate(date) {
  return `${pad2(date.getDate())}/${pad2(date.getMonth() + 1)}/${pad2(date.getFullYear() % 100)}`
}
// "1 – 7 October 2026", "29 August – 7 October 2026", or with both years when they differ.
export function periodText(first, last) {
  if (first.getFullYear() !== last.getFullYear()) return `${longDate(first)} – ${longDate(last)}`
  const day = (d) => d.getDate()
  const month = (d) => d.toLocaleDateString('en-GB', { month: 'long' })
  if (first.getMonth() === last.getMonth()) {
    return day(first) === day(last) ? longDate(last) : `${day(first)} – ${day(last)} ${month(last)} ${last.getFullYear()}`
  }
  return `${day(first)} ${month(first)} – ${day(last)} ${month(last)} ${last.getFullYear()}`
}
export function longDate(date) {
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
}
export function clockTime(date) {
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

// Account ids are long UUIDs; the first 8 characters are enough to tell reports apart.
export const shortUserId = (id) => String(id).slice(0, 8)

const num = (v) => {
  if (v === '' || v === null || v === undefined) return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}
const fixed = (v, d = 1) => (v === null || v === undefined || !Number.isFinite(v) ? '–' : v.toFixed(d))
const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`
const NONE_OPTION = 'None of the above'
const listOrNone = (arr) => {
  const items = (Array.isArray(arr) ? arr : []).filter((x) => x && x !== NONE_OPTION && x !== 'No special voice use')
  return items.length ? items.join(', ') : 'None'
}

// SRS-124 score colours, expressed with the app's existing risk levels:
// ≥ 70 green (low risk), 50–69 orange (moderate), < 50 red (high).
export function scoreLevel(score) {
  if (!Number.isFinite(score)) return 'moderate'
  if (score >= 70) return 'low'
  if (score >= 50) return 'moderate'
  return 'high'
}

// Hoarseness is stored as a RISK score (100 − hoarseness), so higher is worse —
// the opposite of every other score. Only used for the sub-score chart line.
export function hoarsenessLevel(score) {
  if (!Number.isFinite(score)) return 'moderate'
  if (score <= 50) return 'low'
  if (score < 70) return 'moderate'
  return 'high'
}

// ── acoustic table ───────────────────────────────────────────────────
// Reference values mirror VOICE_QUALITY_CONFIG in backend/voice_quality_analyzer.py
// (the "good" / "moderate" cut-offs the scoring model itself uses). If those
// change, update them here too. `scale` converts the stored fraction to %.
const ACOUSTIC_FEATURES = [
  { key: 'jitter_local', name: 'Jitter', unit: '%', scale: 100, digits: 2, good: 0.0032, moderate: 0.0083, reverse: true },
  { key: 'shimmer_local', name: 'Shimmer', unit: '%', scale: 100, digits: 2, good: 0.02, moderate: 0.07, reverse: true },
  { key: 'hnr_db', name: 'HNR', unit: 'dB', scale: 1, digits: 1, good: 24.02, moderate: 16.01, reverse: false },
  { key: 'cpps_db', name: 'CPPS', unit: 'dB', scale: 1, digits: 1, good: 10.2, moderate: 6.35, reverse: false },
  // F0 depends on the speaker (sex, age) so there is no single fair reference.
  { key: 'f0_mean_hz', name: 'F0', unit: 'Hz', scale: 1, digits: 1 },
  { key: 'spectral_entropy', name: 'Spectral Entropy', unit: '', scale: 1, digits: 2, good: 5.0, moderate: 10.21, reverse: true }
]

// Every feature always gets a row (a missing measurement shows "–"), so the table
// reads the same on every report. With no acoustic data at all there is no table.
export function acousticRows(features) {
  if (!features || typeof features !== 'object') return []
  if (!ACOUSTIC_FEATURES.some((f) => num(features[f.key]) !== null)) return []
  const rows = []
  for (const f of ACOUSTIC_FEATURES) {
    const raw = num(features[f.key])
    const withUnit = (v) => `${fixed(v, f.digits)}${f.unit ? ' ' + f.unit : ''}`
    if (raw === null) {
      rows.push({
        name: f.name,
        reference: f.good !== undefined ? `${f.reverse ? '≤' : '≥'} ${withUnit(f.good * f.scale)}` : '–',
        value: '–',
        abnormal: false,
        level: null
      })
      continue
    }
    const value = raw * f.scale
    // Like a lab result sheet: the normal range sits before the value, and a value
    // outside it is shown in bold red. In-range values stay plain.
    let reference = '–'
    let abnormal = false
    let level = null
    if (f.good !== undefined) {
      const good = f.good * f.scale
      reference = `${f.reverse ? '≤' : '≥'} ${withUnit(good)}`
      const ok = f.reverse ? value <= good : value >= good
      if (!ok) {
        abnormal = true
        level = 'high' // anything outside the reference is shown in red, like a lab sheet
      }
    }
    rows.push({ name: f.name, reference, value: withUnit(value), abnormal, level })
  }
  return rows
}

// ── recording context (the per-recording "About This Recording" form) ──

const yesNo = (v) => (v === 'yes' ? 'Yes' : v === 'no' ? 'No' : null)

export function recordingContext(a) {
  if (!a || typeof a !== 'object') return []
  const rows = []
  const push = (label, value) => { if (value !== null && value !== undefined && value !== '') rows.push({ label, value }) }

  if (Array.isArray(a.environment)) push('Environment', listOrNone(a.environment))
  const glasses = num(a.glassesToday)
  if (glasses !== null) push('Water intake today', plural(glasses, 'glass', 'glasses'))
  const slept = num(a.hoursSlept)
  if (slept !== null) push('Sleep', plural(slept, 'hour'))
  if (Array.isArray(a.regularVoiceUse)) push('Voice use before recording', listOrNone(a.regularVoiceUse))

  if (a.symptoms && typeof a.symptoms === 'object') {
    const reported = Object.entries(a.symptoms)
      .filter(([, v]) => typeof v === 'number' && v > 0)
      .sort((x, y) => y[1] - x[1])
    if (!reported.length) push('Throat symptoms', 'None reported')
    else {
      const top = reported.slice(0, 3).map(([name]) => name).join(', ')
      push('Throat symptoms', `${top}${reported.length > 3 ? ` +${reported.length - 3} more` : ''} (max ${reported[0][1]}/5)`)
    }
  }

  push('Caffeine (last 2 h)', yesNo(a.caffeine))
  push('Spicy food (last 2 h)', yesNo(a.spicyFood))
  push('Smoked (last 2 h)', yesNo(a.smoked))
  push('Alcohol (last 6 h)', yesNo(a.alcohol))
  return rows
}

// ── baseline profile (member only) ───────────────────────────────────

const SEX_LABEL = { male: 'Male', female: 'Female', prefer_not_say: 'Not specified' }

function statusLine(status, current, quit, perWhat) {
  if (status === 'never' || status === 'no') return 'No'
  if (status === 'current' || status === 'yes') return current(perWhat)
  if (status === 'quit') return quit()
  return null
}

// `general` (age / sex change how acoustic values are read) and `lifestyle`
// (smoking, alcohol) are both included in every exported report.
export function baselineRows(b) {
  if (!b || typeof b !== 'object') return { general: [], lifestyle: [] }
  const general = []
  const lifestyle = []

  if (SEX_LABEL[b.sex]) general.push({ label: 'Birth sex', value: SEX_LABEL[b.sex] })
  const age = num(b.age)
  if (age !== null) general.push({ label: 'Age', value: `${age}` })
  const water = num(b.glassesWaterPerDay)
  if (water !== null) general.push({ label: 'Water intake', value: `${plural(water, 'glass', 'glasses')} / day` })
  if (Array.isArray(b.regularVoiceUse)) general.push({ label: 'Typical voice use', value: listOrNone(b.regularVoiceUse) })

  const smoke = statusLine(
    b.smokingStatus,
    () => {
      const perDay = num(b.cigarettesPerDay)
      const years = num(b.yearsSmoking)
      return `Yes${perDay !== null ? `, ${plural(perDay, 'cigarette')}/day` : ''}${years !== null ? `, ${plural(years, 'year')}` : ''}`
    },
    () => {
      const ago = num(b.yearsSinceQuitSmoking)
      return `Quit${ago !== null ? `, ${plural(ago, 'year')} ago` : ''}`
    }
  )
  if (smoke) lifestyle.push({ label: 'Smoking', value: smoke })

  const drink = statusLine(
    b.alcoholStatus,
    () => {
      const perWeek = num(b.drinksPerWeek)
      const perDay = num(b.drinksPerDay)
      const amount = perWeek !== null ? `${plural(perWeek, 'drink')}/week` : perDay !== null ? `${plural(perDay, 'drink')}/day` : ''
      const years = num(b.yearsDrinking)
      return `Yes${amount ? ', ' + amount : ''}${years !== null ? `, ${plural(years, 'year')}` : ''}`
    },
    () => {
      const ago = num(b.yearsSinceQuitDrinking)
      return `Quit${ago !== null ? `, ${plural(ago, 'year')} ago` : ''}`
    }
  )
  if (drink) lifestyle.push({ label: 'Alcohol', value: drink })

  return { general, lifestyle }
}

// ── single-session model ─────────────────────────────────────────────

// input: { dateObj, risk, resultLabel, subtitle?, score?, scores?, metrics, recommendations,
//          features?, assessment?, baseline?, scoringVersion? }
// ctx:   { userId (null = guest), generatedAt, baseline? }
export function buildSingleReport(input, ctx) {
  const date = input.dateObj
  const { lifestyle } = baselineRows(input.baseline ?? ctx.baseline)
  const score = num(input.score)
  return {
    type: 'single',
    generatedAt: ctx.generatedAt,
    meta: [
      ctx.userId ? `User ID: ${shortUserId(ctx.userId)}` : 'Guest session'
    ].join('  |  '),
    // Top-right of the page: when this recording was made.
    headerDate: { label: 'Recorded', lines: [longDate(date), clockTime(date)] },
    risk: input.risk,
    resultLabel: input.resultLabel,
    subtitle: input.subtitle || '',
    score,
    scoreText: fixed(score),
    // Colour the score with the same level as the status badge so the two always agree.
    scoreLevel: input.risk || scoreLevel(score),
    metrics: (input.metrics || []).map((m) => {
      const s = num(input.scores?.[m.kind])
      return { ...m, scoreText: s === null ? '' : fixed(s) }
    }),
    recommendations: input.recommendations || [],
    acoustic: acousticRows(input.features),
    context: recordingContext(input.assessment),
    baselineFactors: lifestyle,
    scoringVersion: input.scoringVersion || null
  }
}

// ── multi-session model ──────────────────────────────────────────────

// The trend chart plots the overall voice quality score only.
const LINE_COLOR = '#4f7df3'

// Guide bands behind the chart, matching scoreLevel(): 70+ low risk, 50–69
// moderate, below 50 high. Dots are coloured by the band they fall in.
const BANDS = [
  { from: 70, to: 100, level: 'low', label: 'Low risk (70+)' },
  { from: 50, to: 70, level: 'moderate', label: 'Moderate (50–69)' },
  { from: 0, to: 50, level: 'high', label: 'High risk (below 50)' }
]

function pickTicks(n, max = 5) {
  if (n <= max) return Array.from({ length: n }, (_, i) => i)
  const idx = new Set()
  for (let i = 0; i < max; i++) idx.add(Math.round((i * (n - 1)) / (max - 1)))
  return [...idx]
}

// VQ Change: a drop is shown in red, a rise or no change stays plain. The first
// session has nothing to compare against.
function changeCell(delta) {
  if (delta === null) return { text: '–', abnormal: false }
  const rounded = Math.round(delta * 10) / 10
  return { text: `${rounded > 0 ? '+' : ''}${rounded.toFixed(1)}`, abnormal: rounded < 0 }
}

// Normal ranges shown in the comparison table's "Normal range" row. A value outside
// its range is printed in bold red.
export const COMPARISON_REFERENCE = {
  quality: { text: '≥ 70', ok: (v) => v >= 70 },
  clarity: { text: '≥ 70', ok: (v) => v >= 70 },
  stability: { text: '≥ 70', ok: (v) => v >= 70 },
  hoarseness: { text: '≤ 50', ok: (v) => v <= 50 } // risk score: lower is better
}

// records: [{ id, dateObj, risk, resultLabel, score, scores:{clarity,stability,hoarseness},
//             metrics, scoringVersion? }]  (any order)
// ctx: { userId, generatedAt, baseline?, filterLabel? }
export function buildSummaryReport(records, ctx) {
  const rows = [...records].sort((a, b) => a.dateObj - b.dateObj)
  const first = rows[0].dateObj
  const last = rows[rows.length - 1].dateObj
  const period = `${shortDate(first)} – ${shortDate(last)}`

  const get = {
    overall: (r) => Number(r.score),
    clarity: (r) => Number(r.scores?.clarity),
    stability: (r) => Number(r.scores?.stability),
    hoarseness: (r) => Number(r.scores?.hoarseness)
  }

  // Chart geometry in 0..1 space (y: 0 = score 0, 1 = score 100; x spread evenly
  // over sessions) so the SVG and PDF renderers just scale it.
  const n = rows.length
  const xAt = (i) => (n === 1 ? 0.5 : i / (n - 1))
  const points = rows
    .map((r, i) => {
      const v = get.overall(r)
      return { x: xAt(i), y: Math.max(0, Math.min(100, v)) / 100, level: r.risk || scoreLevel(v), valid: Number.isFinite(v) }
    })
    .filter((p) => p.valid)
  // When every selected session falls on one day (or several ticks would read the
  // same date), the axis switches to clock times so each tick stays distinguishable.
  const tickIdx = pickTicks(n)
  const sameDay = new Set(rows.map((r) => shortDate(r.dateObj))).size === 1
  const tickDates = tickIdx.map((i) => shortDate(rows[i].dateObj).slice(0, 5))
  const dupDates = !sameDay && new Set(tickDates).size < tickDates.length
  const xTicks = tickIdx.map((i, k) => ({
    x: xAt(i),
    // Date on the first line; when dates repeat, the clock time goes on a second line.
    label: sameDay ? clockTime(rows[i].dateObj) : tickDates[k],
    sub: !sameDay && dupDates ? clockTime(rows[i].dateObj) : ''
  }))
  const xTitle = sameDay ? 'Time of day' : dupDates ? 'Date and time (dd/mm)' : 'Date (dd/mm)'
  // Dates on the cards: only the time when the day is already in the period line.
  const when = (d) => (sameDay ? clockTime(d) : shortDate(d))

  const scored = rows.filter((r) => Number.isFinite(get.overall(r)))
  const best = scored.length ? scored.reduce((a, b) => (get.overall(b) > get.overall(a) ? b : a)) : null
  const worst = scored.length ? scored.reduce((a, b) => (get.overall(b) < get.overall(a) ? b : a)) : null
  const avg = scored.length ? scored.reduce((s, r) => s + get.overall(r), 0) / scored.length : null
  const stat = (r) => (r
    ? { score: fixed(get.overall(r)), date: when(r.dateObj), level: r.risk || scoreLevel(get.overall(r)) }
    : { score: '–', date: '', level: null })

  // Direction of travel: latest scored session minus the first scored one. A drop is
  // shown in red, like any other value that is moving the wrong way.
  const trend = (() => {
    if (scored.length < 2) return { text: '–', abnormal: false, sub: 'needs 2+ sessions' }
    const first = scored[0]
    const last = scored[scored.length - 1]
    const d = Math.round((get.overall(last) - get.overall(first)) * 10) / 10
    return {
      text: `${d > 0 ? '+' : d < 0 ? '-' : ''}${Math.abs(d).toFixed(1)}`,
      abnormal: d < 0,
      sub: `${when(first.dateObj)} – ${when(last.dateObj)}`
    }
  })()

  const risk = { high: 0, moderate: 0, low: 0 }
  rows.forEach((r) => { if (risk[r.risk] !== undefined) risk[r.risk]++ })

  const comparison = rows.map((r, i) => {
    const score = get.overall(r)
    const prev = i > 0 ? get.overall(rows[i - 1]) : null
    const delta = i > 0 && Number.isFinite(score) && Number.isFinite(prev) ? score - prev : null
    const metric = (kind) => (r.metrics || []).find((m) => m.kind === kind)
    const cell = (kind, scoreVal) => {
      const m = metric(kind)
      if (!m) return { text: '–', abnormal: false }
      const ref = COMPARISON_REFERENCE[kind]
      const abnormal = Number.isFinite(scoreVal) && !ref.ok(scoreVal)
      return { text: `${m.value}${Number.isFinite(scoreVal) ? ` (${Math.round(scoreVal)})` : ''}`, abnormal }
    }
    const qualityAbnormal = Number.isFinite(score) && !COMPARISON_REFERENCE.quality.ok(score)
    return {
      session: `${i + 1}. ${shortDate(r.dateObj)} ${clockTime(r.dateObj)}`,
      quality: { text: fixed(score), abnormal: qualityAbnormal },
      clarity: cell('clarity', get.clarity(r)),
      stability: cell('stability', get.stability(r)),
      hoarseness: cell('hoarseness', get.hoarseness(r)),
      change: changeCell(delta)
    }
  })
  const comparisonPages = []
  for (let i = 0; i < comparison.length; i += COMPARISON_ROWS_PER_PAGE) {
    comparisonPages.push(comparison.slice(i, i + COMPARISON_ROWS_PER_PAGE))
  }

  const { general, lifestyle } = baselineRows(ctx.baseline)
  const versions = [...new Set(rows.map((r) => r.scoringVersion).filter(Boolean))]

  // The summary is followed by a full single-session page for every selected
  // record, in the same (oldest → newest) order as the comparison table.
  const details = rows.map((r) => buildSingleReport(r, ctx))

  return {
    type: 'summary',
    generatedAt: ctx.generatedAt,
    meta: [
      ctx.userId ? `User ID: ${shortUserId(ctx.userId)}` : 'Member',
      `Sessions: ${n}`,
      ctx.filterLabel ? `Filter: ${ctx.filterLabel}` : null
    ].filter(Boolean).join('  |  '),
    period,
    headerDate: null, // the period sits under the "Analysis Summary" title instead
    periodText: periodText(first, last),
    sessionCount: n,
    chart: {
      color: LINE_COLOR,
      points,
      bands: BANDS,
      xTicks,
      xTitle,
      yTicks: [0, 20, 40, 60, 80, 100]
    },
    // Plain-language summary of the overall score across the selected sessions.
    summary: {
      average: { score: fixed(avg), level: avg === null ? null : scoreLevel(avg) },
      highest: stat(best),
      lowest: stat(worst),
      trend
    },
    riskCounts: risk,
    baseline: {
      retrievedAt: shortDate(ctx.generatedAt),
      rows: [...general, ...lifestyle]
    },
    comparisonPages,
    comparisonReference: ['quality', 'clarity', 'stability', 'hoarseness'].map((k) => COMPARISON_REFERENCE[k].text).concat('–'),
    details,
    scoringVersions: versions
  }
}

// One entry point for both views. Each record carries everything either layout
// needs; one session gives its detail page, several give the summary pages
// followed by every record's detail page.
export function buildReport(records, ctx) {
  if (!records.length) throw new Error('Nothing to export')
  return records.length === 1 ? buildSingleReport(records[0], ctx) : buildSummaryReport(records, ctx)
}
