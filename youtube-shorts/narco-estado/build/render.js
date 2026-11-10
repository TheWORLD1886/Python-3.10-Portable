// usage: node render.js <out> [fps] [from] [to] | node render.js --stills t1,t2,...
const { chromium } = require('playwright'); const { spawn } = require('child_process'); const fs = require('fs');
(async () => {
  const tl = JSON.parse(fs.readFileSync('timeline.json'));
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => console.log('page:', m.text())); page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto('http://127.0.0.1:8765/scene.html'); await page.waitForFunction(() => window.ready, null, { timeout: 120000 });
  await page.evaluate(tl => setup(tl), tl);
  if (process.argv[2] === '--stills') {
    for (const t of process.argv[3].split(',').map(Number)) { await page.evaluate(t => renderAt(t), t); await page.screenshot({ path: `still_${t}.jpg`, quality: 85, type: 'jpeg' }); }
    return browser.close();
  }
  const [out, fps = 30, from = 0, to = tl.total] = [process.argv[2], ...process.argv.slice(3).map(Number)];
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n0 = Math.round(from * fps), n1 = Math.round(to * fps), t0 = Date.now();
  for (let n = n0; n < n1; n++) {
    await page.evaluate(t => renderAt(t), n / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((n - n0) % 60 === 0) console.log(out, n, ((Date.now() - t0) / (n - n0 + 1)).toFixed(0) + 'ms/frame');
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await browser.close();
})();
