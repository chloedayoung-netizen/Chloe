// 사용: node build_pdf.js <docs 폴더> <PDF 저장 폴더>   (playwright 필요: npm i playwright && npx playwright install chromium)
// 또는 Chrome에서 HTML 열기 → 인쇄 → 대상 'PDF로 저장', 여백 '기본', '배경 그래픽' 체크.
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const dir = process.argv[2], out = process.argv[3];
  const b = await chromium.launch();
  const p = await b.newPage();
  for (const n of ['이력서_최다영','자기소개서_최다영','포트폴리오_최다영']) {
    await p.goto('file://' + path.join(dir, n + '.html'), { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    await p.emulateMedia({ media: 'print' });
    await p.pdf({ path: path.join(out, n + '.pdf'), format: 'A4', printBackground: true, preferCSSPageSize: true });
    const fonts = await p.evaluate(() => [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + f.weight));
    console.log(n, 'fonts loaded:', [...new Set(fonts)].join(','));
  }
  await b.close();
})();
