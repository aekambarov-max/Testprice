// Собирает кликабельное демо в одну HTML-страницу (JS и CSS встроены): npm run build:demo
import fs from 'node:fs'
import path from 'node:path'

const dist = path.resolve('dist-demo')
const html = fs.readFileSync(path.join(dist, 'index.html'), 'utf8')
const js = html.match(/src="\.\/(assets\/[^"]+\.js)"/)[1]
const css = html.match(/href="\.\/(assets\/[^"]+\.css)"/)[1]
const script = fs.readFileSync(path.join(dist, js), 'utf8').replace(/<\/script/gi, '<\\/script')
const style = fs.readFileSync(path.join(dist, css), 'utf8').replace(/<\/style/gi, '<\\/style')

const page = `<title>Маркетинговый анализ Price</title>
<style>:root{color-scheme:light}${style}</style>
<div id="app"></div>
<script type="module">${script}</script>
`
const out = path.resolve(process.argv[2] || path.join(dist, 'price-demo.html'))
fs.writeFileSync(out, page)
console.log(`${out}: ${(page.length / 1024).toFixed(0)} KB`)
