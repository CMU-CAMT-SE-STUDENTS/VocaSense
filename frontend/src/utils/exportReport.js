// Exports the report as PDF (real text, built by exportPdf.js) or PNG (a
// capture of the off-screen <ExportReport> pages). Libraries are imported on
// demand so they stay out of the main bundle.

const SCALE = 2

function download(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

async function capturePages(root) {
  const { default: html2canvas } = await import('html2canvas-pro')
  // Poppins is loaded from Google Fonts; capture before it resolves and the
  // report would fall back to a default font.
  if (document.fonts?.ready) await document.fonts.ready
  // The logo is an <img> that only starts decoding once the pages render.
  await Promise.all([...root.querySelectorAll('img')].map((img) => img.decode?.().catch(() => {})))
  const pages = [...root.querySelectorAll('[data-report-page]')]
  const canvases = []
  for (const page of pages) {
    canvases.push(await html2canvas(page, { scale: SCALE, backgroundColor: '#ffffff', useCORS: true }))
  }
  return canvases
}

const toBlob = (canvas, type) => new Promise((resolve) => canvas.toBlob(resolve, type))

// Browsers cap canvas height (~32,000px in Chrome, far less on some phones), so
// only a few pages are stacked into one tall PNG; longer reports (a summary plus
// many detail pages) are downloaded as one PNG per page instead.
const MAX_STACKED_PAGES = 4

async function savePng(root, filename) {
  const canvases = await capturePages(root)
  if (canvases.length === 1) {
    download(await toBlob(canvases[0], 'image/png'), `${filename}.png`)
    return
  }
  if (canvases.length > MAX_STACKED_PAGES) {
    const digits = String(canvases.length).length
    for (let i = 0; i < canvases.length; i++) {
      download(await toBlob(canvases[i], 'image/png'), `${filename}-page${String(i + 1).padStart(digits, '0')}.png`)
      await new Promise((r) => setTimeout(r, 250)) // let the browser accept each download
    }
    return
  }
  const target = document.createElement('canvas')
  target.width = Math.max(...canvases.map((c) => c.width))
  target.height = canvases.reduce((sum, c) => sum + c.height, 0)
  const ctx = target.getContext('2d')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, target.width, target.height)
  let y = 0
  for (const c of canvases) {
    ctx.drawImage(c, 0, y)
    y += c.height
  }
  download(await toBlob(target, 'image/png'), `${filename}.png`)
}

// `report` is the model given to <ExportReport> (see buildReport in
// exportModel.js); `root` is that component's element.
export async function exportReport(root, { format, filename, report }) {
  if (!report) throw new Error('Nothing to export')
  if (format === 'png') {
    await savePng(root, filename)
  } else {
    const { buildReportPdf } = await import('./exportPdf')
    await buildReportPdf(report, filename)
  }
}
