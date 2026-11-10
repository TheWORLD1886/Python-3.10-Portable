const { chromium } = require('playwright');
(async () => { const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 2400, height: 1500 } }); p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => console.log(m.text()));
  const q = process.argv[2] || ''; await p.goto('http://127.0.0.1:8765/preview.html' + q); await p.waitForFunction(() => window.ready, null, { timeout: 60000 });
  for (const m of ['full', 'faces']) { await p.evaluate(m => shot(m), m); await p.screenshot({ path: `preview_${m}${process.argv[3] || ''}.jpg`, quality: 90, type: 'jpeg' }); }
  await b.close(); })();
