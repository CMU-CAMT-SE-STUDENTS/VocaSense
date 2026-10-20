// Builds the report PDF with real (selectable) text using jsPDF. It draws the
// same report model ExportReport.vue renders for PNG (see utils/exportModel.js).
// Poppins is embedded so the PDF looks the same on every device. All
// measurements are in millimetres (A4).
import RegularUrl from '@/assets/fonts/Poppins-Regular.ttf?url'
import SemiBoldUrl from '@/assets/fonts/Poppins-SemiBold.ttf?url'
import BoldUrl from '@/assets/fonts/Poppins-Bold.ttf?url'
import LogoUrl from '@/assets/icons/logo.png?url'
import { DISCLAIMER, longDate, clockTime } from './exportModel'

const PAGE_W = 210
const PAGE_H = 297
const MARGIN = 15
const CONTENT_W = PAGE_W - MARGIN * 2
const FOOTER_Y = PAGE_H - 12
const BOTTOM_LIMIT = FOOTER_Y - 26 // keeps content clear of the footer disclaimer
const CONTENT_TOP = 46 // first y below the header

const BLUE = '#6594e4'
const RULE = '#a9bfe3'
const INK = '#1a1a2e'
const MUTED = '#6b7690'

const RISK = {
  low: { badgeBg: '#e3f7ec', text: '#1f9d5b', cardBg: '#f1ffee' },
  moderate: { badgeBg: '#ffe9d2', text: '#b7791f', cardBg: '#fffdf4' },
  high: { badgeBg: '#fdd9d3', text: '#c83d3d', cardBg: '#fff4f4' }
}
const BAND_FILL = { low: '#eefaf3', moderate: '#fff6e9', high: '#fdeeec' }
const PRIORITY = {
  high: { bg: '#ffe5e0', text: '#c83d3d', dot: '#f43333', label: 'High Priority' },
  moderate: { bg: '#fff5e0', text: '#c68e3f', dot: '#f47033', label: 'Moderate Priority' }
}

async function toBase64(url) {
  const bytes = new Uint8Array(await (await fetch(url)).arrayBuffer())
  let binary = ''
  for (let i = 0; i < bytes.length; i += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000))
  }
  return btoa(binary)
}

async function registerFonts(pdf) {
  const fonts = [
    ['Poppins-Regular.ttf', RegularUrl, 'normal'],
    ['Poppins-SemiBold.ttf', SemiBoldUrl, 'semibold'],
    ['Poppins-Bold.ttf', BoldUrl, 'bold']
  ]
  const data = await Promise.all(fonts.map(([, url]) => toBase64(url)))
  fonts.forEach(([file, , style], i) => {
    pdf.addFileToVFS(file, data[i])
    pdf.addFont(file, 'Poppins', style)
  })
}

// The logo is decoration: if it fails to load the report still builds, with
// the "VocaSense" wordmark drawn as text instead.
async function loadLogo(pdf) {
  try {
    const dataUrl = `data:image/png;base64,${await toBase64(LogoUrl)}`
    const { width, height } = pdf.getImageProperties(dataUrl)
    return { dataUrl, ratio: width / height }
  } catch {
    return null
  }
}

function makeDrawer(pdf) {
  const font = (style, size, color) => {
    pdf.setFont('Poppins', style)
    pdf.setFontSize(size)
    pdf.setTextColor(color)
  }
  const box = (x, y, w, h, fill, radius = 3, stroke) => {
    pdf.setFillColor(fill)
    if (stroke) {
      pdf.setDrawColor(stroke)
      pdf.setLineWidth(0.2)
    }
    pdf.roundedRect(x, y, w, h, radius, radius, stroke ? 'FD' : 'F')
  }
  const rect = (x, y, w, h, fill, stroke) => {
    if (fill) pdf.setFillColor(fill)
    pdf.setDrawColor(stroke || '#1a1a2e')
    pdf.setLineWidth(0.25)
    pdf.rect(x, y, w, h, fill ? (stroke === null ? 'F' : 'FD') : 'S')
  }
  return { font, box, rect }
}

function drawHeader(pdf, d, report, logo) {
  if (logo) {
    const h = 9
    pdf.addImage(logo.dataUrl, 'PNG', MARGIN, 12, h * logo.ratio, h)
  } else {
    d.font('bold', 11, BLUE)
    pdf.text('VocaSense', MARGIN, 18)
  }
  d.font('bold', 20, INK)
  pdf.text('Voice Analysis Report', MARGIN, 29)
  d.font('semibold', 7.5, '#7b869c')
  pdf.text(pdf.splitTextToSize(report.meta, CONTENT_W - 45), MARGIN, 34.5)

  // Top-right: the recording date (or the period a summary covers).
  const hd = report.headerDate
  if (hd) {
    d.font('semibold', 7, '#8b96ad')
    pdf.text(hd.label.toUpperCase(), PAGE_W - MARGIN, 14, { align: 'right' })
    d.font('semibold', 8.5, MUTED)
    pdf.text(hd.lines[0], PAGE_W - MARGIN, 19.5, { align: 'right' })
    pdf.text(hd.lines[1], PAGE_W - MARGIN, 25, { align: 'right' })
  }

  pdf.setDrawColor(RULE)
  pdf.setLineWidth(0.9)
  pdf.line(MARGIN, 39, PAGE_W - MARGIN, 39)
}

// ── single session ───────────────────────────────────────────────────

function drawSingle(pdf, d, report, newPage) {
  let y = CONTENT_TOP

  y += 4

  // Status + score
  const risk = RISK[report.risk] || RISK.moderate
  d.font('bold', 15, INK)
  pdf.text('Voice Health Status', PAGE_W / 2, y, { align: 'center' })
  y += 4
  if (report.score !== null) {
    const sc = RISK[report.scoreLevel] || RISK.moderate
    d.font('bold', 30, sc.text)
    const main = report.scoreText
    d.font('bold', 30, sc.text)
    const mainW = pdf.getTextWidth(main + ' ')
    d.font('bold', 18, sc.text)
    const ofW = pdf.getTextWidth('/ 100')
    const startX = (PAGE_W - (mainW + ofW)) / 2
    d.font('bold', 30, sc.text)
    pdf.text(main, startX, y + 11)
    d.font('bold', 18, sc.text)
    pdf.text('/ 100', startX + mainW, y + 11)
    y += 16
  }
  d.font('semibold', 9, risk.text)
  const badgeW = pdf.getTextWidth(report.resultLabel) + 14
  d.box((PAGE_W - badgeW) / 2, y, badgeW, 8, risk.badgeBg, 4)
  pdf.text(report.resultLabel, PAGE_W / 2, y + 5.4, { align: 'center' })
  y += 12
  if (report.subtitle) {
    d.font('normal', 8.5, MUTED)
    const subLines = pdf.splitTextToSize(report.subtitle, CONTENT_W - 20)
    pdf.text(subLines, PAGE_W / 2, y, { align: 'center' })
    y += subLines.length * 4
  }
  y += 5

  // Metric cards
  const gap = 4
  const cardW = (CONTENT_W - gap * 2) / 3
  report.metrics.forEach((m, i) => {
    const c = RISK[m.level] || RISK.moderate
    const x = MARGIN + i * (cardW + gap)
    d.box(x, y, cardW, 22, c.cardBg, 4, '#e5e7eb')
    d.font('normal', 8, '#5b6680')
    pdf.text(m.scoreText ? `${m.label}: ${m.scoreText}` : m.label, x + 5, y + 8)
    d.font('bold', 12.5, c.text)
    pdf.text(m.value, x + 5, y + 16.5)
  })
  y += 22 + 9

  // Recommendations
  if (report.recommendations.length) {
    d.font('bold', 12, INK)
    pdf.text('Personalized Recommendations', MARGIN, y)
    y += 5
  }
  const textW = CONTENT_W - 12 - 36
  for (const r of report.recommendations) {
    const p = PRIORITY[r.priority] || PRIORITY.moderate
    d.font('semibold', 9.5, INK)
    const lines = pdf.splitTextToSize(r.text, textW)
    const h = Math.max(11, lines.length * 4.6 + 6)
    if (y + h > BOTTOM_LIMIT) y = newPage()
    d.box(MARGIN, y, CONTENT_W, h, p.bg, 3)
    pdf.setFillColor(p.dot)
    pdf.circle(MARGIN + 6, y + h / 2, 1.4, 'F')
    d.font('semibold', 9.5, INK)
    pdf.text(lines, MARGIN + 11, y + h / 2 - ((lines.length - 1) * 4.6) / 2 + 1.2)
    d.font('semibold', 8, p.text)
    pdf.text(p.label, PAGE_W - MARGIN - 5, y + h / 2 + 1, { align: 'right' })
    y += h + 2.5
  }
  y += 3

  // Acoustic table (left) + recording context / baseline factors (right)
  const hasTable = report.acoustic.length > 0
  const facts = []
  if (report.context.length) facts.push({ title: 'Recording Context', rows: report.context })
  if (report.baselineFactors.length) facts.push({ title: 'Relevant Baseline Factors', rows: report.baselineFactors })
  if (!hasTable && !facts.length) return

  const tableW = hasTable ? (facts.length ? 106 : CONTENT_W) : 0
  const factsX = hasTable ? MARGIN + tableW + 8 : MARGIN
  const factsW = hasTable ? CONTENT_W - tableW - 8 : CONTENT_W

  // Pre-measure the facts column so the whole block can move to a new page together.
  d.font('normal', 8, INK)
  const factBlocks = facts.map((g) => ({
    title: g.title,
    rows: g.rows.map((r) => pdf.splitTextToSize(`${r.label}: ${r.value}`, factsW - 4))
  }))
  const factsH = factBlocks.reduce((s, g) => s + 7 + g.rows.reduce((t, l) => t + l.length * 3.9 + 0.8, 0) + 4, 0)
  const rowH = 7
  const tableH = hasTable ? rowH * (report.acoustic.length + 1) : 0
  const blockH = 12 + Math.max(tableH, factsH)
  if (y + blockH > BOTTOM_LIMIT) y = newPage()

  pdf.setDrawColor('#c9d6ee')
  pdf.setLineWidth(0.3)
  pdf.line(MARGIN, y, PAGE_W - MARGIN, y)
  y += 7
  d.font('bold', 11.5, INK)
  pdf.text(hasTable ? 'Acoustic Measurement & Assessment Context' : 'Assessment Context', PAGE_W / 2, y, { align: 'center' })
  y += 5

  if (hasTable) {
    const cols = [32, 36, tableW - 68]
    const heads = ['Feature', 'Normal range', 'Value']
    let x = MARGIN
    heads.forEach((h, i) => {
      d.rect(x, y, cols[i], rowH, '#f4f7ff', '#1a1a2e')
      d.font('bold', 7.5, INK)
      pdf.text(h, x + 2, y + 4.7)
      x += cols[i]
    })
    let ry = y + rowH
    report.acoustic.forEach((row) => {
      const cells = [row.name, row.reference, row.value]
      x = MARGIN
      cells.forEach((c, i) => {
        // The Normal range column is tinted, like the "Normal range" row of the comparison table.
        d.rect(x, ry, cols[i], rowH, i === 1 ? '#f4f7ff' : null, '#1a1a2e')
        // Out-of-range values are bold red, like an abnormal result on a lab report.
        const flagged = i === 2 && row.abnormal
        const color = flagged ? (RISK[row.level] || RISK.moderate).text : i === 1 ? '#5b6680' : INK
        d.font(flagged ? 'bold' : i === 1 ? 'semibold' : 'normal', 7.5, color)
        pdf.text(c, x + 2, ry + 4.7)
        x += cols[i]
      })
      ry += rowH
    })
  }

  if (facts.length) {
    if (hasTable) {
      pdf.setDrawColor('#c9d6ee')
      pdf.line(factsX - 4, y, factsX - 4, y + Math.max(tableH, factsH) - 2)
    }
    let fy = y + 3
    factBlocks.forEach((g) => {
      d.font('bold', 9.5, INK)
      pdf.text(g.title, factsX, fy)
      fy += 5.5
      g.rows.forEach((lines) => {
        lines.forEach((line, li) => {
          // Bold the label part ("Label:") on the first line, normal for the rest.
          if (li === 0) {
            const idx = line.indexOf(':')
            const label = line.slice(0, idx + 1)
            const rest = line.slice(idx + 1)
            d.font('bold', 8, INK)
            pdf.text(label, factsX, fy)
            const lw = pdf.getTextWidth(label)
            d.font('normal', 8, INK)
            pdf.text(rest, factsX + lw, fy)
          } else {
            d.font('normal', 8, INK)
            pdf.text(line, factsX, fy)
          }
          fy += 3.9
        })
        fy += 0.8
      })
      fy += 4
    })
  }
}

// ── multi-session summary ────────────────────────────────────────────

function drawSummary(pdf, d, report) {
  let y = CONTENT_TOP + 6
  d.font('bold', 21, INK)
  pdf.text('Analysis Summary', PAGE_W / 2, y, { align: 'center' })
  y += 6
  d.font('semibold', 9, '#8b96ad')
  pdf.text(report.periodText, PAGE_W / 2, y, { align: 'center' })
  y += 8

  // Chart title + legend of the guide bands (centered)
  d.font('semibold', 9, '#4a5470')
  pdf.text('Overall voice quality score', PAGE_W / 2, y, { align: 'center' })
  y += 5.5
  d.font('normal', 7.5, '#4a5470')
  const items = report.chart.bands.map((bd) => ({ ...bd, w: pdf.getTextWidth(bd.label) + 8 }))
  const totalW = items.reduce((s, i) => s + i.w + 6, -6)
  let lx = (PAGE_W - totalW) / 2
  items.forEach((bd) => {
    pdf.setFillColor(BAND_FILL[bd.level])
    pdf.setDrawColor(RISK[bd.level].text)
    pdf.setLineWidth(0.2)
    pdf.roundedRect(lx, y - 2.6, 4.2, 3, 0.6, 0.6, 'FD')
    d.font('normal', 7.5, '#4a5470')
    pdf.text(bd.label, lx + 6, y)
    lx += bd.w + 6
  })
  y += 5

  // Chart
  const plotX = MARGIN + 9
  const plotW = CONTENT_W - 9 - 6 // right margin leaves room for the x-axis arrow
  const plotY = y + 8 // room above for the y-axis arrow + title
  const plotH = 56
  const yAt = (v) => plotY + (1 - v / 100) * plotH
  // Guide bands: where a score counts as low / moderate / high risk.
  report.chart.bands.forEach((bd) => {
    pdf.setFillColor(BAND_FILL[bd.level])
    pdf.rect(plotX, yAt(bd.to), plotW, yAt(bd.from) - yAt(bd.to), 'F')
  })
  d.font('normal', 7, '#6b7690')
  report.chart.yTicks.forEach((t) => {
    const ty = yAt(t)
    pdf.setDrawColor('#e6eaf2')
    pdf.setLineWidth(0.2)
    pdf.line(plotX, ty, plotX + plotW, ty)
    pdf.text(String(t), plotX - 2.5, ty + 1.1, { align: 'right' })
  })
  // Dashed threshold lines at the band edges (70 and 50).
  pdf.setLineDashPattern([1.2, 1.2], 0)
  pdf.setLineWidth(0.25)
  report.chart.bands.filter((bd) => bd.from > 0).forEach((bd) => {
    pdf.setDrawColor(RISK[bd.level].text)
    pdf.line(plotX, yAt(bd.from), plotX + plotW, yAt(bd.from))
  })
  pdf.setLineDashPattern([], 0)
  // Axes: solid lines with arrowheads, small tick marks and axis titles.
  const AX = '#6b7690'
  const x0 = plotX
  const y0 = plotY + plotH
  pdf.setDrawColor(AX)
  pdf.setFillColor(AX)
  pdf.setLineWidth(0.35)
  pdf.setLineCap('butt')
  pdf.line(x0, y0, x0, plotY - 3) // y axis
  pdf.line(x0, y0, x0 + plotW + 3, y0) // x axis
  pdf.triangle(x0 - 1.1, plotY - 3, x0 + 1.1, plotY - 3, x0, plotY - 5.6, 'F')
  pdf.triangle(x0 + plotW + 3, y0 - 1.1, x0 + plotW + 3, y0 + 1.1, x0 + plotW + 5.6, y0, 'F')
  pdf.setLineWidth(0.25)
  report.chart.yTicks.forEach((t) => pdf.line(x0 - 1.2, yAt(t), x0, yAt(t)))
  report.chart.xTicks.forEach((t) => pdf.line(x0 + t.x * plotW, y0, x0 + t.x * plotW, y0 + 1.2))
  d.font('semibold', 7, '#4a5470')
  pdf.text('Score (0–100)', x0 + 3, plotY - 3.4)
  pdf.text('Date (dd/mm)', x0 + plotW / 2, y0 + 9.6, { align: 'center' })
  d.font('normal', 7, '#6b7690')
  report.chart.xTicks.forEach((t) => {
    pdf.text(t.label, plotX + t.x * plotW, plotY + plotH + 5, { align: 'center' })
  })
  pdf.setLineJoin('round')
  pdf.setLineCap('round')
  const pts = report.chart.points.map((p) => ({ x: plotX + p.x * plotW, y: plotY + (1 - p.y) * plotH, level: p.level }))
  pdf.setDrawColor(report.chart.color)
  pdf.setLineWidth(0.6)
  for (let i = 1; i < pts.length; i++) pdf.line(pts[i - 1].x, pts[i - 1].y, pts[i].x, pts[i].y)
  pdf.setDrawColor('#ffffff')
  pdf.setLineWidth(0.3)
  pts.forEach((p) => {
    pdf.setFillColor(RISK[p.level].text)
    pdf.circle(p.x, p.y, 1.3, 'FD')
  })
  y = plotY + plotH + 14

  // Summary: average / highest / lowest overall score, and the change since the first session
  const colX = [MARGIN + 4, MARGIN + CONTENT_W / 2 + 4]
  const sgap = 4
  const sw = (CONTENT_W - sgap * 3) / 4
  ;[
    ['Average score', report.summary.average.score, report.summary.average.level, `across ${report.sessionCount} sessions`],
    ['Highest score', report.summary.highest.score, report.summary.highest.level, report.summary.highest.date],
    ['Lowest score', report.summary.lowest.score, report.summary.lowest.level, report.summary.lowest.date],
    ['Change since first', report.summary.trend.text, report.summary.trend.abnormal ? 'high' : null, report.summary.trend.sub]
  ].forEach(([label, value, level, sub], i) => {
    const x = MARGIN + i * (sw + sgap)
    d.box(x, y, sw, 24, '#ffffff', 3.5, '#dde4f2')
    d.font('normal', 8, '#5b6680')
    pdf.text(label, x + 5, y + 6.5)
    d.font('bold', 18, level ? RISK[level].text : INK)
    pdf.text(String(value), x + 5, y + 15.5)
    d.font('normal', 7.5, '#8b96ad')
    pdf.text(sub || '', x + 5, y + 20.5)
  })
  y += 24 + 6

  // Risk counts as chips, with a caption saying what is being counted
  d.font('semibold', 8, '#6b7690')
  pdf.text('Sessions by risk level', MARGIN, y)
  y += 3.5
  let cx = MARGIN
  ;[
    ['high', `High risk: ${report.riskCounts.high}`],
    ['moderate', `Moderate risk: ${report.riskCounts.moderate}`],
    ['low', `Low risk: ${report.riskCounts.low}`]
  ].forEach(([lvl, text]) => {
    d.font('semibold', 8, RISK[lvl].text)
    const w = pdf.getTextWidth(text) + 8
    d.box(cx, y, w, 6.5, RISK[lvl].badgeBg, 3.2)
    pdf.text(text, cx + 4, y + 4.4)
    cx += w + 3
  })
  y += 14

  // Baseline context
  if (report.baseline.rows.length) {
    d.font('bold', 13, INK)
    pdf.text('Baseline Context', MARGIN, y)
    y += 5
    d.font('normal', 7.5, '#8b96ad')
    pdf.text(`Profile as retrieved on ${report.baseline.retrievedAt} — may differ from when older sessions were recorded.`, MARGIN, y)
    y += 6
    report.baseline.rows.forEach((r, i) => {
      const x = colX[i % 2]
      const ry = y + Math.floor(i / 2) * 5.4
      const label = `${r.label}: `
      d.font('bold', 8.5, INK)
      pdf.text(label, x, ry)
      const lw = pdf.getTextWidth(label)
      d.font('normal', 8.5, INK)
      const val = pdf.splitTextToSize(r.value, CONTENT_W / 2 - lw - 8)
      pdf.text(val[0], x + lw, ry)
    })
  }
}

// ── session comparison table ─────────────────────────────────────────

function drawComparison(pdf, d, rows, reference) {
  let y = CONTENT_TOP + 6
  d.font('bold', 21, INK)
  pdf.text('Session Comparison', PAGE_W / 2, y, { align: 'center' })
  y += 8

  const cols = [36, 22, 34, 37, 29, 22]
  const heads = ['Session', 'Voice quality', 'Clarity', 'Stability', 'Hoarseness', 'VQ change']
  const rowH = 8.5
  let x = MARGIN
  heads.forEach((h, i) => {
    d.rect(x, y, cols[i], rowH, '#f4f7ff', '#1a1a2e')
    d.font('bold', 8, INK)
    pdf.text(h, i === 0 ? x + 2.5 : x + cols[i] / 2, y + 5.5, { align: i === 0 ? 'left' : 'center' })
    x += cols[i]
  })
  y += rowH

  // "Normal range" row: tells the reader what a good value looks like.
  x = MARGIN
  ;['Normal range', ...reference].forEach((text, i) => {
    d.rect(x, y, cols[i], rowH, '#f4f7ff', '#1a1a2e')
    d.font('semibold', 7.5, '#5b6680')
    pdf.text(text, i === 0 ? x + 2.5 : x + cols[i] / 2, y + 5.5, { align: i === 0 ? 'left' : 'center' })
    x += cols[i]
  })
  y += rowH

  rows.forEach((row) => {
    const cells = [
      { text: row.session, abnormal: false },
      ...['quality', 'clarity', 'stability', 'hoarseness', 'change'].map((k) => row[k])
    ]
    x = MARGIN
    cells.forEach((c, i) => {
      d.rect(x, y, cols[i], rowH, null, '#1a1a2e')
      // Outside the normal range: bold red text.
      d.font(c.abnormal ? 'bold' : 'normal', 7.5, c.abnormal ? RISK.high.text : INK)
      pdf.text(c.text, i === 0 ? x + 2.5 : x + cols[i] / 2, y + 5.5, { align: i === 0 ? 'left' : 'center' })
      x += cols[i]
    })
    y += rowH
  })
}

// ── entry points ─────────────────────────────────────────────────────

async function render(report) {
  const { jsPDF } = await import('jspdf')
  const pdf = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'portrait', compress: true })
  await registerFonts(pdf)
  const logo = await loadLogo(pdf)
  const d = makeDrawer(pdf)

  // One entry per physical page: which layout it is and which report supplies
  // its header / version text (detail pages carry their own "Recorded:" line).
  const pages = []
  const startPage = (rep, kind) => {
    if (pages.length) pdf.addPage()
    pages.push({ kind, rep })
    drawHeader(pdf, d, rep, logo)
  }
  const drawDetail = (detail) => {
    startPage(detail, 'single')
    // Overflow of one detail page continues on a new page with the same header.
    drawSingle(pdf, d, detail, () => {
      startPage(detail, 'single')
      return CONTENT_TOP
    })
  }

  if (report.type === 'single') {
    drawDetail(report)
  } else {
    startPage(report, 'summary')
    drawSummary(pdf, d, report)
    report.comparisonPages.forEach((rows) => {
      startPage(report, 'comparison')
      drawComparison(pdf, d, rows, report.comparisonReference)
    })
    report.details.forEach(drawDetail)
  }

  // Footer on every page, drawn last so page numbers are final.
  const versionsOf = (rep) => (rep.type === 'single' ? (rep.scoringVersion ? [rep.scoringVersion] : []) : rep.scoringVersions)
  const total = pdf.getNumberOfPages()
  for (let p = 1; p <= total; p++) {
    pdf.setPage(p)
    const { rep } = pages[p - 1]
    const versions = versionsOf(rep)
    const versionText = versions.length ? ` · scoring v${versions.join(', v')}` : ''
    // Above the rule: document notes (disclaimer, then export date). Below: running footer.
    d.font('normal', 6.5, '#a3acbf')
    pdf.text(pdf.splitTextToSize(`Medical disclaimer: ${DISCLAIMER}`, CONTENT_W), MARGIN, FOOTER_Y - 16.5)
    d.font('normal', 7.5, '#a3acbf')
    pdf.text(`Report exported on ${longDate(rep.generatedAt)}, ${clockTime(rep.generatedAt)}`, MARGIN, FOOTER_Y - 6.5)
    pdf.setDrawColor('#c9d6ee')
    pdf.setLineWidth(0.3)
    pdf.line(MARGIN, FOOTER_Y - 4, PAGE_W - MARGIN, FOOTER_Y - 4)
    d.font('normal', 7.5, '#a3acbf')
    pdf.text(`Generated by VocaSense${versionText}`, MARGIN, FOOTER_Y)
    if (total > 1) {
      d.font('semibold', 7.5, '#5b6680')
      pdf.text(`Page ${p} of ${total}`, PAGE_W - MARGIN, FOOTER_Y, { align: 'right' })
    }
  }

  pdf.setProperties({ title: 'VocaSense Voice Analysis Report', creator: 'VocaSense' })
  return pdf
}

export async function buildReportPdfBlob(report) {
  return (await render(report)).output('blob')
}

export async function buildReportPdf(report, filename) {
  const pdf = await render(report)
  pdf.save(`${filename}.pdf`)
}
