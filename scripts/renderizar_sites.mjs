// Abre no navegador (Chromium) os sites que a leitura simples não conseguiu ler — lojas montadas por JavaScript
// ou que bloqueiam requisições sem navegador — e salva o HTML renderizado da home e das páginas de contato.
// Uso: node scripts/renderizar_sites.mjs <leads.json> <saida.json>   (precisa do pacote "playwright")
import fs from 'fs'
import { chromium } from 'playwright'

const [entrada, saida] = process.argv.slice(2)
const leads = JSON.parse(fs.readFileSync(entrada, 'utf8'))
const exe = fs.readdirSync('/opt/pw-browsers').filter((d) => d.startsWith('chromium-'))
  .map((d) => `/opt/pw-browsers/${d}/chrome-linux/chrome`).find((p) => fs.existsSync(p))
const CONTATO = /contato|contate|fale[-_ ]?conosco|atendimento|contact|sac\b|quem[-_ ]somos|sobre|about|revend|atacado|parceri/i

const browser = await chromium.launch({ executablePath: exe })
const resultado = []

async function abrir(ctx, url) {
  const page = await ctx.newPage()
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 25000 })
    await page.waitForTimeout(2500) // tempo para o JavaScript da loja montar rodapé e botões de WhatsApp
    return { url: page.url(), html: await page.content(), page }
  } catch {
    await page.close()
    return null
  }
}

async function processar(lead) {
  const ctx = await browser.newContext({ locale: 'pt-BR', userAgent:
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36' })
  const paginas = []
  try {
    const site = lead.site.startsWith('http') ? lead.site : `https://${lead.site}`
    const home = await abrir(ctx, site)
    if (home) {
      paginas.push({ url: home.url, html: home.html })
      const host = new URL(home.url).host
      const links = await home.page.$$eval('a[href]', (as) => as.map((a) => [a.href, (a.textContent || '').trim()]))
      await home.page.close()
      const contato = [...new Set(links.filter(([h, t]) => CONTATO.test(`${t} ${h}`)).map(([h]) => h.split('#')[0]))]
        .filter((h) => { try { return new URL(h).host === host } catch { return false } })
        .sort((a, b) => Number(!/contato|contact|fale/i.test(a)) - Number(!/contato|contact|fale/i.test(b)) || a.length - b.length)
        .slice(0, 3)
      for (const url of contato) {
        const p = await abrir(ctx, url)
        if (p) { paginas.push({ url: p.url, html: p.html }); await p.page.close() }
      }
    }
  } finally {
    await ctx.close()
  }
  return { id: lead.id, paginas }
}

// 6 sites por vez
for (let i = 0; i < leads.length; i += 6) {
  const lote = await Promise.all(leads.slice(i, i + 6).map((l) => processar(l).catch(() => ({ id: l.id, paginas: [] }))))
  resultado.push(...lote)
  console.log(`${Math.min(i + 6, leads.length)}/${leads.length}`)
}
await browser.close()
fs.writeFileSync(saida, JSON.stringify(resultado))
