// Turns raw analysis / assessment / baseline data into the "report model" that
// both renderers use (ExportReport.vue for PNG, exportPdf.js for PDF), so the
// two outputs can never drift apart. Pure functions only — no DOM, no jsPDF.
//
// Two report shapes (Feature #7):
//   • single  – one session: status, metrics, recommendations, acoustic table,
//               recording context, relevant baseline factors
//   • summary – 2+ sessions: trend chart, key observations, baseline context,
//               a session-comparison table (paginated), then one single-session
//               detail page per selected record

export const DISCLAIMER =
  'This platform provides preliminary voice health insights and does not replace professional medical diagnosis. Please consult a healthcare professional for medical concerns.'

export const DEFAULT_EXPORT_OPTIONS = Object.freeze({
  includeSubScores: false, // summary chart: also plot Clarity / Stability / Hoarseness
  includeLifestyle: false // baseline: also show smoking & alcohol history
})

export const COMPARISON_ROWS_PER_PAGE = 22

// ── small helpers ────────────────────────────────────────────────────

const pad2 = (n) => String(n).padStart(2, '0')

export function shortDate(date) {
  return `${pad2(date.getDate())}/${pad2(date.getMonth() + 1)}/${pad2(date.getFullYear() % 100)}`
}
export function longDate(date) {
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
}
export function clockTime(date) {
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

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
  { key: 'f0_mean_hz', name: 'F0 (mean)', unit: 'Hz', scale: 1, digits: 1 },
  { key: 'spectral_entropy', name: 'Spectral Entropy', unit: '', scale: 1, digits: 2, good: 5.0, moderate: 10.21, reverse: true }
]

export function acousticRows(features) {
  if (!features || typeof features !== 'object') return []
  const rows = []
  for (const f of ACOUSTIC_FEATURES) {
    const raw = num(features[f.key])
    if (raw === null) continue
    const value = raw * f.scale
    const withUnit = (v) => `${fixed(v, f.digits)}${f.unit ? ' ' + f.unit : ''}`
    let reference = '–'
    let interpretation = '–'
    let level = null
    if (f.good !== undefined) {
      const good = f.good * f.scale
      reference = `${f.reverse ? '≤' : '≥'} ${withUnit(good)}`
      const moderate = f.moderate * f.scale
      const ok = f.reverse ? value <= good : value >= good
      const mild = f.reverse ? value <= moderate : value >= moderate
      if (ok) { interpretation = 'Within expected range'; level = 'low' }
      else if (mild) { interpretation = f.reverse ? 'Slightly elevated' : 'Slightly reduced'; level = 'moderate' }
      else { interpretation = f.reverse ? 'Elevated' : 'Reduced'; level = 'high' }
    }
    rows.push({ name: f.name, value: withUnit(value), reference, interpretation, level })
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

// `general` is always safe to show (age / sex change how acoustic values are
// read); `lifestyle` (smoking, alcohol) is only shown when the user opts in.
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
//          features?, assessment?, baseline?, analysisId?, scoringVersion? }
// ctx:   { username (null = guest), generatedAt, options, baseline? }
export function buildSingleReport(input, ctx) {
  const options = { ...DEFAULT_EXPORT_OPTIONS, ...(ctx.options || {}) }
  const date = input.dateObj
  const { lifestyle } = baselineRows(input.baseline ?? ctx.baseline)
  const score = num(input.score)
  return {
    type: 'single',
    generatedAt: ctx.generatedAt,
    meta: [
      ctx.username ? `Username: ${ctx.username}` : 'Guest session',
      input.analysisId ? `Analysis ID: ${input.analysisId}` : null,
      `Recorded: ${shortDate(date)}, ${clockTime(date)}`
    ].filter(Boolean).join('  |  '),
    risk: input.risk,
    resultLabel: input.resultLabel,
    subtitle: input.subtitle || '',
    score,
    scoreText: fixed(score),
    scoreLevel: scoreLevel(score),
    metrics: (input.metrics || []).map((m) => {
      const s = num(input.scores?.[m.kind])
      return { ...m, scoreText: s === null ? '' : fixed(s) }
    }),
    recommendations: input.recommendations || [],
    acoustic: acousticRows(input.features),
    context: recordingContext(input.assessment),
    baselineFactors: options.includeLifestyle ? lifestyle : [],
    scoringVersion: input.scoringVersion || null
  }
}

// ── multi-session model ──────────────────────────────────────────────

// Colours match the app's palette; Hoarseness is red because it is the one
// line where lower is better (see hoarsenessNote).
const SERIES = [
  { key: 'overall', label: 'Overall', color: '#4f7df3' },
  { key: 'clarity', label: 'Clarity', color: '#a47df3' },
  { key: 'stability', label: 'Stability', color: '#f0b45a' },
  { key: 'hoarseness', label: 'Hoarseness (lower is better)', color: '#f0523d' }
]

const stats = (values) => {
  const v = values.filter((x) => Number.isFinite(x))
  if (!v.length) return { avg: null, min: null, max: null }
  return { avg: v.reduce((s, x) => s + x, 0) / v.length, min: Math.min(...v), max: Math.max(...v) }
}

function pickTicks(n, max = 5) {
  if (n <= max) return Array.from({ length: n }, (_, i) => i)
  const idx = new Set()
  for (let i = 0; i < max; i++) idx.add(Math.round((i * (n - 1)) / (max - 1)))
  return [...idx]
}

// VQ Change colouring: any rise is green, a small drop orange, a drop of 10
// points or more red. The first session has nothing to compare against.
function changeCell(delta) {
  if (delta === null) return { text: '–', level: null }
  const rounded = Math.round(delta * 10) / 10
  const text = `${rounded > 0 ? '+' : ''}${rounded.toFixed(1)}`
  if (rounded > 0) return { text, level: 'low' }
  if (rounded === 0) return { text, level: null }
  return { text, level: rounded <= -10 ? 'high' : 'moderate' }
}

// records: [{ id, dateObj, risk, resultLabel, score, scores:{clarity,stability,hoarseness},
//             metrics, scoringVersion? }]  (any order)
// ctx: { username, generatedAt, options, baseline?, filterLabel? }
export function buildSummaryReport(records, ctx) {
  const options = { ...DEFAULT_EXPORT_OPTIONS, ...(ctx.options || {}) }
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
  const keys = options.includeSubScores ? SERIES.map((s) => s.key) : ['overall']
  const n = rows.length
  const xAt = (i) => (n === 1 ? 0.5 : i / (n - 1))
  const series = SERIES.filter((s) => keys.includes(s.key)).map((s) => ({
    key: s.key,
    label: s.label,
    color: s.color,
    points: rows
      .map((r, i) => ({ x: xAt(i), y: Math.max(0, Math.min(100, get[s.key](r))) / 100, valid: Number.isFinite(get[s.key](r)) }))
      .filter((p) => p.valid)
  }))
  const xTicks = pickTicks(n).map((i) => ({ x: xAt(i), label: shortDate(rows[i].dateObj).slice(0, 5) }))

  const observation = (key, label) => {
    const s = stats(rows.map(get[key]))
    return { label, avg: fixed(s.avg), min: fixed(s.min), max: fixed(s.max) }
  }

  const scored = rows.filter((r) => Number.isFinite(get.overall(r)))
  const best = scored.length ? scored.reduce((a, b) => (get.overall(b) > get.overall(a) ? b : a)) : null
  const worst = scored.length ? scored.reduce((a, b) => (get.overall(b) < get.overall(a) ? b : a)) : null
  const bestLine = (r) => (r ? `Score ${fixed(get.overall(r))} · ${shortDate(r.dateObj)}` : '–')

  const risk = { high: 0, moderate: 0, low: 0 }
  rows.forEach((r) => { if (risk[r.risk] !== undefined) risk[r.risk]++ })

  const comparison = rows.map((r, i) => {
    const score = get.overall(r)
    const prev = i > 0 ? get.overall(rows[i - 1]) : null
    const delta = i > 0 && Number.isFinite(score) && Number.isFinite(prev) ? score - prev : null
    const metric = (kind) => (r.metrics || []).find((m) => m.kind === kind)
    const cell = (kind, scoreVal) => {
      const m = metric(kind)
      return m ? { text: `${m.value}${Number.isFinite(scoreVal) ? ` (${Math.round(scoreVal)})` : ''}`, level: m.level } : { text: '–', level: null }
    }
    return {
      session: `${i + 1}. ${shortDate(r.dateObj)} ${clockTime(r.dateObj)}`,
      quality: { text: fixed(score), level: scoreLevel(score) },
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
  const detailCtx = { ...ctx, username: ctx.username || 'Member' }
  const details = rows.map((r) => buildSingleReport({ ...r, analysisId: r.analysisId ?? r.id }, detailCtx))

  return {
    type: 'summary',
    generatedAt: ctx.generatedAt,
    meta: [
      `Username: ${ctx.username || 'Member'}`,
      `Sessions: ${n}`,
      `Period: ${period}`,
      ctx.filterLabel ? `Filter: ${ctx.filterLabel}` : null
    ].filter(Boolean).join('  |  '),
    period,
    chart: {
      series,
      xTicks,
      yTicks: [0, 20, 40, 60, 80, 100],
      showHoarsenessNote: options.includeSubScores
    },
    observations: [
      observation('overall', 'Voice Quality'),
      observation('stability', 'Stability'),
      observation('clarity', 'Clarity'),
      observation('hoarseness', 'Hoarseness')
    ],
    best: bestLine(best),
    worst: bestLine(worst),
    riskCounts: risk,
    baseline: {
      retrievedAt: shortDate(ctx.generatedAt),
      rows: [...general, ...(options.includeLifestyle ? lifestyle : [])]
    },
    comparisonPages,
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

// Name printed in the report header. Falls back to null (shown as "Member" /
// "Guest session"); an email is shortened to the part before the "@".
export function exportUsername(name) {
  if (!name || name === 'there') return null
  const s = String(name)
  return s.includes('@') ? s.split('@')[0] : s
}
