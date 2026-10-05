// Builds the report PDF with real (selectable) text using jsPDF, laid out to
// match ExportReport.vue / the Result page. Poppins is embedded so the PDF
// looks the same on every device. All measurements are in millimetres (A4).
import RegularUrl from '@/assets/fonts/Poppins-Regular.ttf?url'
import SemiBoldUrl from '@/assets/fonts/Poppins-SemiBold.ttf?url'
import BoldUrl from '@/assets/fonts/Poppins-Bold.ttf?url'

const PAGE_W = 210
const PAGE_H = 297
const MARGIN = 15
const CONTENT_W = PAGE_W - MARGIN * 2
const FOOTER_Y = PAGE_H - 12
const BOTTOM_LIMIT = FOOTER_Y - 8

const BLUE = '#6594e4'
const INK = '#1a1a2e'
const MUTED = '#6b7690'

const RISK = {
  low: { badgeBg: '#e3f7ec', text: '#1f9d5b', cardBg: '#f1ffee' },
  moderate: { badgeBg: '#fff3dc', text: '#b7791f', cardBg: '#fffdf4' },
  high: { badgeBg: '#fdeaea', text: '#c83d3d', cardBg: '#fff4f4' }
}
const PRIORITY = {
  high: { bg: '#ffe5e0', text: '#c83d3d', dot: '#f43333', label: 'High Priority' },
  moderate: { bg: '#fff5e0', text: '#c68e3f', dot: '#f47033', label: 'Moderate Priority' }
}

const DISCLAIMER = 'This platform provides preliminary voice health insights and does not replace professional medical diagnosis. Please consult a healthcare professional for medical concerns.'

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

function drawRecord(pdf, rec) {
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

  // Header
  font('bold', 9, BLUE)
  pdf.text('VocaSense', MARGIN, 20)
  font('bold', 20, INK)
  pdf.text('Voice Analysis Report', MARGIN, 29)
  font('normal', 9, MUTED)
  pdf.text(rec.dateLabel, PAGE_W - MARGIN, 20, { align: 'right' })
  pdf.text(rec.time, PAGE_W - MARGIN, 25, { align: 'right' })
  pdf.setDrawColor(BLUE)
  pdf.setLineWidth(0.6)
  pdf.line(MARGIN, 34, PAGE_W - MARGIN, 34)

  // Disclaimer
  let y = 41
  font('normal', 8, '#3d5a99')
  const discLines = pdf.splitTextToSize(DISCLAIMER, CONTENT_W - 10)
  const discH = 6 + 4 + discLines.length * 3.7
  box(MARGIN, y, CONTENT_W, discH, '#d9e6fc', 3, '#b4cdf5')
  font('bold', 8, '#3d5a99')
  pdf.text('Medical Disclaimer', MARGIN + 5, y + 6)
  font('normal', 8, '#3d5a99')
  pdf.text(discLines, MARGIN + 5, y + 10.5)
  y += discH + 12

  // Status
  const risk = RISK[rec.risk] || RISK.moderate
  font('semibold', 9, risk.text)
  const badgeW = pdf.getTextWidth(rec.resultLabel) + 12
  box((PAGE_W - badgeW) / 2, y, badgeW, 8, risk.badgeBg, 4)
  pdf.text(rec.resultLabel, PAGE_W / 2, y + 5.4, { align: 'center' })
  y += 17
  font('bold', 15, INK)
  pdf.text('Your Voice Health Status', PAGE_W / 2, y, { align: 'center' })
  y += 6
  if (rec.subtitle) {
    font('semibold', 9, MUTED)
    const subLines = pdf.splitTextToSize(rec.subtitle, CONTENT_W - 20)
    pdf.text(subLines, PAGE_W / 2, y, { align: 'center' })
    y += subLines.length * 4.2
  }
  y += 8

  // Metrics
  const gap = 4
  const cardW = (CONTENT_W - gap * 2) / 3
  rec.metrics.forEach((m, i) => {
    const c = RISK[m.level] || RISK.moderate
    const x = MARGIN + i * (cardW + gap)
    box(x, y, cardW, 24, c.cardBg, 4, '#e5e7eb')
    font('normal', 8.5, '#5b6680')
    pdf.text(m.label, x + 5, y + 8)
    font('bold', 12.5, c.text)
    pdf.text(m.value, x + 5, y + 17)
  })
  y += 24 + 12

  // Recommendations
  font('bold', 12, INK)
  pdf.text('Personalized Recommendations', MARGIN, y)
  y += 5
  const textW = CONTENT_W - 12 - 36
  for (const r of rec.recommendations) {
    const p = PRIORITY[r.priority] || PRIORITY.moderate
    font('semibold', 9.5, INK)
    const lines = pdf.splitTextToSize(r.text, textW)
    const h = Math.max(11, lines.length * 4.6 + 6)
    if (y + h > BOTTOM_LIMIT) {
      pdf.addPage()
      y = MARGIN + 5
    }
    box(MARGIN, y, CONTENT_W, h, p.bg, 3)
    pdf.setFillColor(p.dot)
    pdf.circle(MARGIN + 6, y + h / 2, 1.4, 'F')
    font('semibold', 9.5, INK)
    pdf.text(lines, MARGIN + 11, y + h / 2 - ((lines.length - 1) * 4.6) / 2 + 1.2)
    font('semibold', 8, p.text)
    pdf.text(p.label, PAGE_W - MARGIN - 5, y + h / 2 + 1, { align: 'right' })
    y += h + 2.5
  }
}

export async function buildReportPdf(records, filename) {
  const { jsPDF } = await import('jspdf')
  const pdf = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'portrait', compress: true })
  await registerFonts(pdf)

  records.forEach((rec, i) => {
    if (i > 0) pdf.addPage()
    drawRecord(pdf, rec)
  })

  // Footer on every page, drawn last so page numbers are final.
  const total = pdf.getNumberOfPages()
  for (let p = 1; p <= total; p++) {
    pdf.setPage(p)
    pdf.setDrawColor('#eef1f8')
    pdf.setLineWidth(0.3)
    pdf.line(MARGIN, FOOTER_Y - 4, PAGE_W - MARGIN, FOOTER_Y - 4)
    pdf.setFont('Poppins', 'normal')
    pdf.setFontSize(8)
    pdf.setTextColor('#8b96ad')
    pdf.text('Generated by VocaSense', MARGIN, FOOTER_Y)
    if (total > 1) pdf.text(`${p} / ${total}`, PAGE_W - MARGIN, FOOTER_Y, { align: 'right' })
  }

  pdf.setProperties({ title: 'VocaSense Voice Analysis Report', creator: 'VocaSense' })
  pdf.save(`${filename}.pdf`)
}
