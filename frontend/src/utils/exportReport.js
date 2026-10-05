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
  const pages = [...root.querySelectorAll('[data-report-page]')]
  const canvases = []
  for (const page of pages) {
    canvases.push(await html2canvas(page, { scale: SCALE, backgroundColor: '#ffffff', useCORS: true }))
  }
  return canvases
}

const toBlob = (canvas, type) => new Promise((resolve) => canvas.toBlob(resolve, type))

// One record -> one PNG; several records -> stacked into a single tall PNG.
async function savePng(root, filename) {
  const canvases = await capturePages(root)
  let target = canvases[0]
  if (canvases.length > 1) {
    target = document.createElement('canvas')
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
  }
  download(await toBlob(target, 'image/png'), `${filename}.png`)
}

// `records` is the same array given to <ExportReport>; `root` is its element.
export async function exportReport(root, { format, filename, records }) {
  if (!records.length) throw new Error('Nothing to export')
  if (format === 'png') {
    await savePng(root, filename)
  } else {
    const { buildReportPdf } = await import('./exportPdf')
    await buildReportPdf(records, filename)
  }
}
