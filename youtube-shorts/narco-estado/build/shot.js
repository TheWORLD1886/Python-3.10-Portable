const { chromium } = require('playwright');
(async () => { const [url, out, w = 1600, h = 1000] = process.argv.slice(2); const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: +w, height: +h } }); p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => m.type() === 'error' && console.log(m.text()));
  await p.goto('http://127.0.0.1:8765/' + url); await p.waitForFunction(() => window.ready, null, { timeout: 120000 }); await p.screenshot({ path: out, type: 'jpeg', quality: 88 }); await b.close(); })();
