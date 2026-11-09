// Exports the report as PDF (real text, built by exportPdf.js) or PNG (a
// capture of the off-screen <ExportReport> pages, one image per page). Libraries are imported on
// demand so they stay out of the main bundle.

const SCALE = 2

// yyyy-mm-dd in the user's local time zone (toISOString would use UTC and give
// the previous day just after local midnight). Used in export file names.
export function dayStamp(date = new Date()) {
  const p = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${p(date.getMonth() + 1)}-${p(date.getDate())}`
}

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

// Each report page is downloaded as its own PNG file (never one tall stacked
// image): <filename>.png for one page, <filename>-page01.png, -page02.png ...
// for several. The browser may ask once to allow multiple downloads.
async function savePng(root, filename) {
  const canvases = await capturePages(root)
  if (canvases.length === 1) {
    download(await toBlob(canvases[0], 'image/png'), `${filename}.png`)
    return
  }
  const digits = Math.max(2, String(canvases.length).length)
  for (let i = 0; i < canvases.length; i++) {
    download(await toBlob(canvases[i], 'image/png'), `${filename}-page${String(i + 1).padStart(digits, '0')}.png`)
    await new Promise((r) => setTimeout(r, 400)) // let the browser accept each download
  }
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
