// Five cinematic sets. Every update(t, dur) is a pure function of time (deterministic frames).
import * as THREE from 'three';
import { stickman } from './chars.js';
import { std, add, rng, canvasTex, normalFrom, lathe, MAT, helicopter, baluster, column, moneyStack } from './props.js';

const W = 1080, H = 1920;
const lerp = (a, b, k) => a + (b - a) * k, clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const easeOut = k => 1 - Math.pow(1 - clamp(k), 3), easeInOut = k => { k = clamp(k); return k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; };
export const util = { lerp, clamp, easeOut, easeInOut };

function softTex(inner = 'rgba(255,255,255,1)', outer = 'rgba(255,255,255,0)') {
  const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d'); const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, inner); gr.addColorStop(1, outer); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c);
}
function smokeTex(seed) { // irregular billowy puff
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d'), R = rng(seed);
  for (let i = 0; i < 40; i++) { const x = 128 + (R() - .5) * 120, y = 128 + (R() - .5) * 120, r = 30 + R() * 60, gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, `rgba(255,255,255,${.08 + R() * .1})`); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); }
  const m = g.createRadialGradient(128, 128, 60, 128, 128, 128); m.addColorStop(0, 'rgba(0,0,0,0)'); m.addColorStop(1, 'rgba(0,0,0,1)');
  g.globalCompositeOperation = 'destination-out'; g.fillStyle = m; g.fillRect(0, 0, 256, 256); return new THREE.CanvasTexture(c);
}
function textTex(lines, { w = 1024, h = 256, color = '#ffd23a', glow = '#ff9a00', size = 120, border = null } = {}) {
  return canvasTex(w, h, (g) => { if (border) { g.strokeStyle = border; g.lineWidth = 8; g.shadowColor = glow; g.shadowBlur = 25; g.strokeRect(10, 10, w - 20, h - 20); }
    g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = `900 ${size}px "Liberation Sans", Arial`; g.shadowColor = glow; g.shadowBlur = 30; g.fillStyle = color;
    lines.forEach((l, i) => g.fillText(l, w / 2, h / 2 + (i - (lines.length - 1) / 2) * size * 1.1)); });
}
const holo = (tex, w, h, opacity = .95) => new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
function base(bg, near, far) { const s = new THREE.Scene(); s.background = new THREE.Color(bg); s.fog = new THREE.FogExp2(bg, near); s.userData.rigs = []; const cam = new THREE.PerspectiveCamera(34, W / H, .05, 400); return { s, cam }; }
function dirLight(s, color, int, pos, target = [0, 0, 0], size = 6, map = 2048) {
  const l = new THREE.DirectionalLight(color, int); l.position.set(...pos); l.target.position.set(...target); s.add(l, l.target);
  l.castShadow = true; l.shadow.mapSize.set(map, map); const c = l.shadow.camera; c.left = c.bottom = -size; c.right = c.top = size; c.near = .5; c.far = 80; l.shadow.bias = -.0004; l.shadow.normalBias = .02; return l;
}
function beam(color, r, len, opacity = .08) { // volumetric light cone (apex at origin, pointing -y)
  const m = new THREE.Mesh(new THREE.ConeGeometry(r, len, 32, 1, true).translate(0, -len / 2, 0), new THREE.MeshBasicMaterial({ color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide, fog: false }));
  return m;
}
function particles(n, seed, color, size, spread, opacity = .9) {
  const R = rng(seed), geo = new THREE.BufferGeometry(), b = new Float32Array(n * 4);
  for (let i = 0; i < n; i++) b.set([(R() - .5) * spread[0], R() * spread[1], (R() - .5) * spread[2], R()], i * 4);
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  const p = new THREE.Points(geo, new THREE.PointsMaterial({ color, size, map: softTex(), transparent: true, opacity, depthWrite: false, blending: THREE.AdditiveBlending }));
  p.userData = { b, spread }; return p;
}
function moveParticles(p, t, vy, wob = .2) { const { b, spread: sp } = p.userData, a = p.geometry.attributes.position;
  for (let i = 0; i < a.count; i++) { const ph = b[i * 4 + 3] * 6.28; a.setXYZ(i, b[i * 4] + Math.sin(t * .7 + ph) * wob, ((b[i * 4 + 1] + t * vy) % sp[1] + sp[1]) % sp[1], b[i * 4 + 2] + Math.cos(t * .5 + ph) * wob); }
  a.needsUpdate = true; }
function flagTex() {
  return canvasTex(600, 350, (g, w, h) => { ['#006847', '#f4f4f4', '#ce1126'].forEach((c, i) => { g.fillStyle = c; g.fillRect(i * w / 3, 0, w / 3, h); });
    const cx = w / 2, cy = h / 2; g.fillStyle = '#5d8a3a'; g.beginPath(); g.ellipse(cx, cy + 32, 52, 18, 0, 0, Math.PI); g.fill();       // wreath
    g.fillStyle = '#6b4220'; g.beginPath(); g.ellipse(cx, cy, 26, 34, -.2, 0, 7); g.fill();                                          // eagle body
    g.beginPath(); g.moveTo(cx - 10, cy - 20); g.quadraticCurveTo(cx - 52, cy - 50, cx - 40, cy + 5); g.fill(); g.beginPath(); g.moveTo(cx + 10, cy - 20); g.quadraticCurveTo(cx + 50, cy - 46, cx + 36, cy + 8); g.fill();
    g.fillStyle = '#3f7d2c'; g.fillRect(cx - 20, cy + 26, 40, 8); g.strokeStyle = '#3a7a3a'; g.lineWidth = 3; g.beginPath(); g.moveTo(cx - 16, cy - 32); g.quadraticCurveTo(cx, cy - 46, cx + 18, cy - 30); g.stroke(); });
}
function cloth(geo, t, amp, speed, fixedAxis = 'x', fixedAt = 0, base = null) { // waving cloth, fixed along one edge
  const p = geo.attributes.position, b = base || (geo.userData.base ??= p.array.slice());
  for (let i = 0; i < p.count; i++) { const x = b[i * 3], y = b[i * 3 + 1], u = Math.abs((fixedAxis === 'x' ? x : y) - fixedAt);
    p.setZ(i, b[i * 3 + 2] + Math.sin(x * 2.6 - t * speed + y * .8) * amp * u + Math.sin(x * 5.3 - t * speed * 1.7) * amp * .3 * u); p.setY(i, y - u * u * .04); }
  p.needsUpdate = true; geo.computeVertexNormals(); }

// =====================================================================
// 1) Palacio Nacional–style colonial facade at night
// =====================================================================
function scene1() {
  const { s, cam } = base(0x070a14, .012);
  // sky dome with gradient + stars + moon glow
  const sky = new THREE.Mesh(new THREE.SphereGeometry(150, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false,
    vertexShader: 'varying vec3 v; void main(){ v = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
    fragmentShader: 'varying vec3 v; void main(){ float h = clamp(v.y,0.,1.); vec3 c = mix(vec3(.10,.08,.12), vec3(.01,.02,.06), pow(h,.5)); gl_FragColor = vec4(c,1.); }' }));
  s.add(sky);
  const stars = particles(900, 2, 0xffffff, .5, [260, 60, 60], .8); stars.position.set(0, 25, -110); s.add(stars);
  const moon = new THREE.Sprite(new THREE.SpriteMaterial({ map: softTex('rgba(255,240,220,1)', 'rgba(255,200,150,0)'), blending: THREE.AdditiveBlending, fog: false })); moon.position.set(-18, 34, -100); moon.scale.set(14, 14, 1); s.add(moon);
  s.add(new THREE.HemisphereLight(0x2a3550, 0x100806, .35));
  const F = new THREE.Group(); F.position.z = -3; s.add(F);
  // facade wall with cornices
  add(F, new THREE.BoxGeometry(44, 18, 1.2), MAT.tezontle, 0, 7, -.6);
  for (const [y, h, d] of [[-.1, .3, .5], [4.6, .25, .35], [4.85, .12, .45], [13.5, .3, .5], [13.85, .18, .7], [14.05, .5, .3]]) add(F, new THREE.BoxGeometry(44, h, d), MAT.cantera, 0, y, d / 2 - .1);
  // windows: cantera frame, pediment, iron balconette, warm interior
  const winGlow = new THREE.MeshStandardMaterial({ color: 0x120800, emissive: 0xffa040, emissiveIntensity: 1.2, emissiveMap: canvasTex(64, 128, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#ffcf80'); gr.addColorStop(1, '#a04a10'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.fillStyle = '#2a1408'; g.fillRect(w / 2 - 2, 0, 4, h); g.fillRect(0, h * .55, w, 4); g.fillStyle = 'rgba(80,30,10,.6)'; g.fillRect(0, 0, w * .2, h); g.fillRect(w * .8, 0, w * .2, h); }) });
  for (let i = -5; i <= 5; i++) for (let j = 0; j < 2; j++) { if (i === 0) continue;
    const x = i * 3.6, y = j ? 8.7 : 2.4, wg = new THREE.Group(); wg.position.set(x, y, 0); F.add(wg);
    add(wg, new THREE.PlaneGeometry(1.2, 2.3), winGlow, 0, 0, .02);
    for (const [px, py, sw, sh] of [[-.68, 0, .16, 2.6], [.68, 0, .16, 2.6], [0, 1.25, 1.52, .16], [0, -1.25, 1.6, .18]]) add(wg, new THREE.BoxGeometry(sw, sh, .22), MAT.cantera, px, py, .08);
    const ped = new THREE.Shape([new THREE.Vector2(-.95, 0), new THREE.Vector2(.95, 0), new THREE.Vector2(0, .5)]); const pm = add(wg, new THREE.ExtrudeGeometry(ped, { depth: .2, bevelEnabled: true, bevelSize: .03, bevelThickness: .03 }), MAT.cantera, 0, 1.38, -.02);
    if (j) { add(wg, new THREE.BoxGeometry(1.7, .1, .55), MAT.cantera, 0, -1.4, .3); for (let k = -6; k <= 6; k++) add(wg, new THREE.CylinderGeometry(.012, .012, .7), MAT.iron, k * .13, -1.0, .55); add(wg, new THREE.BoxGeometry(1.65, .03, .03), MAT.iron, 0, -.65, .55); }
  }
  // central portal: arched doorway, columns, bell niche
  const arch = new THREE.Shape(); arch.moveTo(-1.6, 0); arch.lineTo(-1.6, 3.2); arch.absarc(0, 3.2, 1.6, Math.PI, 0, true); arch.lineTo(1.6, 0); arch.lineTo(2.1, 0); arch.lineTo(2.1, 5.4); arch.lineTo(-2.1, 5.4); arch.lineTo(-2.1, 0);
  add(F, new THREE.ExtrudeGeometry(arch, { depth: .35, bevelEnabled: true, bevelSize: .04, bevelThickness: .04 }), MAT.cantera, 0, 5.1, -.05);
  const doorIn = new THREE.Shape(); doorIn.moveTo(-1.6, 0); doorIn.lineTo(-1.6, 3.2); doorIn.absarc(0, 3.2, 1.6, Math.PI, 0, true); doorIn.lineTo(1.6, 0);
  add(F, new THREE.ShapeGeometry(doorIn), new THREE.MeshStandardMaterial({ color: 0x1a0c02, emissive: 0xffb050, emissiveIntensity: .35 }), 0, 5.1, .0);
  for (const sx of [-1, 1]) { const c = column(4.6, .22); c.position.set(sx * 2.5, 4.9, .35); F.add(c); }
  add(F, new THREE.BoxGeometry(6.2, .35, .6), MAT.cantera, 0, 10.6, .25);
  const bell = add(F, lathe([[.001, .9], [.12, .88], [.3, .7], [.38, .3], [.5, .05], [.55, 0], [.001, 0]], 32), MAT.bronze, 0, 15.2, .1);
  add(F, new THREE.BoxGeometry(2.2, 2.4, .5), MAT.cantera, 0, 15.2, -.3); add(F, new THREE.BoxGeometry(1.6, 1.9, .2), std(0x0a0503), 0, 15.3, -.05);
  for (let i = -10; i <= 10; i++) add(F, lathe([[.001, 0], [.14, 0], [.12, .3], [.06, .45], [.1, .55], [.001, .8]], 12), MAT.cantera, i * 2.1, 14.3, .1);
  // balcony slab + baluster railing
  const B = new THREE.Group(); B.position.set(0, 4.9, -.2); s.add(B);
  add(B, new THREE.BoxGeometry(7, .3, 3.4), MAT.cantera, 0, -.15, .4);
  add(B, new THREE.BoxGeometry(7.2, .12, 3.5), MAT.cantera, 0, -.33, .45);
  for (let i = 0; i < 9; i++) add(B, new THREE.BoxGeometry(.3, .5, .3), MAT.cantera, -3.3 + i * .82, -.6, 1.9);   // corbels
  const bal = baluster(.85); const balInst = new THREE.InstancedMesh(bal, MAT.cantera, 60); let n = 0; const m4 = new THREE.Matrix4();
  for (let i = 0; i < 30; i++) { m4.makeTranslation(-3.2 + i * .22, 0, 2.0); balInst.setMatrixAt(n++, m4); }
  for (let i = 0; i < 12; i++) for (const sx of [-1, 1]) { m4.makeTranslation(sx * 3.3, 0, -.3 + i * .2); balInst.setMatrixAt(n++, m4); }
  balInst.count = n; balInst.castShadow = true; B.add(balInst);
  add(B, new THREE.BoxGeometry(6.9, .12, .26), MAT.cantera, 0, .92, 2.0);
  for (const sx of [-1, 1]) add(B, new THREE.BoxGeometry(.26, .12, 2.5), MAT.cantera, sx * 3.3, .92, .9);
  // lanterns
  const lamps = [];
  for (const sx of [-1, 1]) { const L = new THREE.Group(); L.position.set(sx * 3.0, 7.6, -2.7); s.add(L);
    add(L, new THREE.BoxGeometry(.05, .05, .6), MAT.iron, 0, 0, .3);
    add(L, lathe([[.001, -.55], [.14, -.5], [.2, -.2], [.18, .1], [.24, .15], [.001, .35]], 6), MAT.iron, 0, -.3, .6);
    add(L, new THREE.CylinderGeometry(.13, .15, .38, 6), new THREE.MeshStandardMaterial({ color: 0x331a00, emissive: 0xffc070, emissiveIntensity: 2.5, transparent: true, opacity: .9 }), 0, -.5, .6);
    const pl = new THREE.PointLight(0xffb050, 6, 7, 1.6); pl.position.set(0, -.5, .75); L.add(pl); lamps.push(pl); }
  // giant waving flag on the roof pole
  add(s, new THREE.CylinderGeometry(.06, .08, 9, 12), MAT.gold, 7, 18.5, -3.2);
  add(s, new THREE.SphereGeometry(.15, 16, 12), MAT.gold, 7, 23.1, -3.2);
  const flagGeo = new THREE.PlaneGeometry(5.5, 3.2, 40, 20); flagGeo.translate(2.75, 0, 0);
  const flag = add(s, flagGeo, std(0xffffff, { map: flagTex(), side: THREE.DoubleSide, roughness: .85 }), 7.05, 21.2, -3.2);
  // facade uplights + beams
  for (const x of [-12, -6, 6, 12]) { const sp = new THREE.SpotLight(0xffb066, 120, 25, .45, .6, 1.4); sp.position.set(x, .2, 2); sp.target.position.set(x * .9, 12, -3); s.add(sp, sp.target);
    const bm = beam(0xffb066, 2.2, 14, .035); bm.position.set(x, .2, 2); bm.lookAt(x * .9, 12, -3); bm.rotateX(-Math.PI / 2); s.add(bm); }
  add(s, new THREE.PlaneGeometry(200, 200).rotateX(-Math.PI / 2), std(0x1a1715, { roughness: .4, metalness: .2 }), 0, 0, 0);
  // president
  const man = stickman('president'); man.root.position.set(0, 4.9, .2); s.add(man.root); s.userData.rigs.push(man);
  const key = dirLight(s, 0xffd6a0, 1.6, [4, 11, 9], [0, 5.8, 0], 4);
  const rim = new THREE.SpotLight(0xffd27a, 12, 12, .5, .6); rim.position.set(0, 9, -2.3); rim.target = man.head; s.add(rim);
  const face = new THREE.SpotLight(0xfff0dd, 3, 9, .25, .7); face.position.set(1.2, 6.8, 4.5); face.target = man.head; s.add(face);
  const dust = particles(300, 7, 0xffc860, .06, [10, 6, 6], .8); dust.position.set(0, 4.5, 1); s.add(dust);
  return { s, cam, update(t, dur) {
    const k = easeOut(t / 2.0);
    cam.position.set(lerp(-1.5, .35, k) + Math.sin(t * .4) * .04, lerp(9, 6.55, k), lerp(34, 3.4, k) - Math.max(0, t - 2) * .05);
    cam.lookAt(0, lerp(9, 6.35, k), 0);
    cloth(flagGeo, t, .22, 4.5, 'x', 0);
    const wave = clamp((t - 3.2) / .6) * (1 - clamp((t - 7.6) / .6));                 // waves to the crowd
    man.rArm.a.rotation.set(lerp(-.03, -.4, wave), 0, lerp(.12, 2.5, wave)); man.rArm.b.rotation.x = lerp(-.2, -.6, wave) + Math.sin(t * 7) * .25 * wave;
    man.rArm.end.rotation.z = Math.sin(t * 7) * .3 * wave;
    man.head.rotation.y = Math.sin(t * .6) * .1 - .05; man.root.rotation.y = Math.sin(t * .3) * .04;
    lamps.forEach((l, i) => l.intensity = 6 + Math.sin(t * 9 + i * 2) * .6 + Math.sin(t * 23 + i) * .3);
    moveParticles(dust, t, .12);
  } };
}

// =====================================================================
// 2) Presidential office: mahogany desk, money, glowing hologram documents
// =====================================================================
function scene2() {
  const { s, cam } = base(0x0b0907, .03);
  s.add(new THREE.HemisphereLight(0x8a7a66, 0x1a120a, .35));
  // parquet floor + rug
  const parquet = canvasTex(512, 512, (g, w, h) => { const R = rng(3); for (let y = 0; y < h; y += 32) for (let x = 0; x < w; x += 128) { const o = (y / 32) % 2 * 64, v = R();
    g.fillStyle = `rgb(${70 + v * 30},${38 + v * 16},${20 + v * 8})`; g.fillRect(x + o, y, 126, 30); g.fillRect(x + o - 128, y, 126, 30); } }, { rep: [6, 6] });
  add(s, new THREE.PlaneGeometry(30, 30).rotateX(-Math.PI / 2), new THREE.MeshPhysicalMaterial({ map: parquet, roughness: .35, clearcoat: .6 }), 0, 0, 0);
  const rug = canvasTex(512, 384, (g, w, h) => { g.fillStyle = '#5a0f12'; g.fillRect(0, 0, w, h); g.strokeStyle = '#c9a040'; g.lineWidth = 10; g.strokeRect(20, 20, w - 40, h - 40); g.lineWidth = 3; g.strokeRect(40, 40, w - 80, h - 80);
    g.fillStyle = 'rgba(201,160,64,.5)'; for (let i = 0; i < 6; i++) { g.beginPath(); g.arc(w / 2, h / 2, 30 + i * 22, 0, 7); g.lineWidth = 2; g.stroke(); } noiseFill2(g, w, h); });
  add(s, new THREE.PlaneGeometry(5, 3.6).rotateX(-Math.PI / 2), std(0xffffff, { map: rug, roughness: 1 }), 0, .005, .4);
  // wood-paneled back wall with moldings
  const wall = new THREE.Group(); wall.position.z = -2.6; s.add(wall);
  add(wall, new THREE.BoxGeometry(14, 6, .2), MAT.panelWood, 0, 3, 0);
  for (let i = -4; i <= 4; i++) { if (Math.abs(i) <= 1) continue; for (const [y, h] of [[1.0, 1.4], [3.2, 2.4]]) { const px = i * 1.4;
    for (const [dx, dy, w, hh] of [[0, h / 2, 1.1, .06], [0, -h / 2, 1.1, .06], [-.55, 0, .06, h], [.55, 0, .06, h]]) add(wall, new THREE.BoxGeometry(w, hh, .06), MAT.panelWood, px + dx, y + dy, .12); } }
  add(wall, new THREE.BoxGeometry(14, .25, .25), MAT.panelWood, 0, 5.6, .15); add(wall, new THREE.BoxGeometry(14, .2, .1), MAT.panelWood, 0, .1, .12);
  // window with night city + velvet curtains
  const city = canvasTex(512, 512, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#05070f'); gr.addColorStop(1, '#1a1020'); g.fillStyle = gr; g.fillRect(0, 0, w, h); const R = rng(9);
    for (let i = 0; i < 400; i++) { const x = R() * w, y = h * .45 + R() * h * .55, r = 1 + R() * 5; const c = R() < .7 ? '255,190,110' : '140,190,255'; const q = g.createRadialGradient(x, y, 0, x, y, r * 3); q.addColorStop(0, `rgba(${c},.9)`); q.addColorStop(1, `rgba(${c},0)`); g.fillStyle = q; g.fillRect(x - r * 3, y - r * 3, r * 6, r * 6); } });
  add(wall, new THREE.PlaneGeometry(2.4, 3.3), new THREE.MeshBasicMaterial({ map: city }), 0, 3.05, .11);
  for (const [dx, dy, w, h] of [[0, 1.7, 2.6, .12], [0, -1.7, 2.7, .16], [-1.25, 0, .1, 3.5], [1.25, 0, .1, 3.5], [0, 0, .05, 3.3], [0, .4, 2.4, .05]]) add(wall, new THREE.BoxGeometry(w, h, .1), std(0xe8e0d0, { roughness: .5 }), dx, 3.05 + dy, .15);
  const velvet = new THREE.MeshPhysicalMaterial({ color: 0x6a0c14, roughness: .7, sheen: 1, sheenColor: new THREE.Color(0xff6070), sheenRoughness: .4, side: THREE.DoubleSide });
  for (const sx of [-1, 1]) { const cg = new THREE.PlaneGeometry(1.1, 4.6, 40, 10), p = cg.attributes.position;
    for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i); p.setZ(i, Math.sin(x * 26) * .06 * (1 - y / 6) + .05); p.setX(i, x * (1 - (2.3 - y) / 4.6 * .25 * (sx * x > 0 ? 1 : .3))); } cg.computeVertexNormals();
    add(wall, cg, velvet, sx * 1.6, 3.2, .25); }
  add(wall, new THREE.CylinderGeometry(.03, .03, 4.2), MAT.brass, 0, 5.4, .3).rotation.z = Math.PI / 2;
  // gilded painting
  const paint = canvasTex(256, 192, (g, w, h) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#d8a060'); gr.addColorStop(1, '#3a2a18'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.fillStyle = '#2a3a20'; g.beginPath(); g.moveTo(0, h * .7); for (let x = 0; x <= w; x += 16) g.lineTo(x, h * .6 + Math.sin(x * .05) * 14); g.lineTo(w, h); g.lineTo(0, h); g.fill(); g.fillStyle = '#e8d8a0'; g.beginPath(); g.arc(w * .7, h * .3, 14, 0, 7); g.fill(); });
  for (const sx of [-1, 1]) { add(wall, new THREE.PlaneGeometry(1.3, 1.0), std(0xffffff, { map: paint, roughness: .8 }), sx * 3.6, 3.4, .14); add(wall, new THREE.BoxGeometry(1.5, 1.2, .06), MAT.gold, sx * 3.6, 3.4, .1); }
  // flags with folds + gold eagle finials
  for (const x of [-1.95, 1.95]) { add(s, new THREE.CylinderGeometry(.025, .025, 3.2, 10), MAT.gold, x, 1.6, -2.1); add(s, new THREE.ConeGeometry(.06, .2, 8), MAT.gold, x, 3.3, -2.1);
    add(s, lathe([[.001, 0], [.25, 0], [.25, .05], [.06, .12], [.04, .3], [.001, .3]], 24), MAT.gold, x, 0, -2.1);
    const fg = new THREE.PlaneGeometry(.95, 1.6, 20, 20); fg.translate(.48, 0, 0); const fp = fg.attributes.position;
    for (let i = 0; i < fp.count; i++) { const u = fp.getX(i), v = fp.getY(i); fp.setZ(i, Math.sin(u * 14) * .05 * u); fp.setX(i, u * .6 * (1 - (v + .8) * .1)); } fg.computeVertexNormals();
    const f = add(s, fg, std(0xffffff, { map: flagTex(), side: THREE.DoubleSide, roughness: .8 }), x + .02, 2.3, -2.1); f.rotation.y = x < 0 ? .3 : Math.PI - .3; }
  // presidential desk
  const D = new THREE.Group(); D.position.set(0, 0, .3); s.add(D);
  add(D, new THREE.BoxGeometry(3.0, .08, 1.4), MAT.mahogany, 0, .84, 0);
  add(D, new THREE.BoxGeometry(3.08, .04, 1.48), MAT.mahogany, 0, .79, 0);
  add(D, new THREE.BoxGeometry(2.2, .01, .9), MAT.greenLeather, 0, .885, 0);
  for (const sx of [-1, 1]) { add(D, new THREE.BoxGeometry(.9, .76, 1.3), MAT.mahogany, sx * 1.0, .39, 0);
    for (let k = 0; k < 3; k++) { add(D, new THREE.BoxGeometry(.8, .2, .02), MAT.mahogany, sx * 1.0, .17 + k * .23, .66); add(D, new THREE.BoxGeometry(.14, .025, .04), MAT.brass, sx * 1.0, .17 + k * .23, .685); } }
  add(D, new THREE.BoxGeometry(1.1, .5, .04), MAT.mahogany, 0, .5, .6); add(D, new THREE.BoxGeometry(.9, .3, .02), MAT.panelWood, 0, .5, .625);
  // desk items: banker's lamp, money, phone, pen set, files, nameplate, holo projector
  const lamp = new THREE.Group(); lamp.position.set(-1.05, .88, -.35); D.add(lamp);
  add(lamp, new THREE.CylinderGeometry(.11, .13, .03, 24), MAT.brass); add(lamp, new THREE.CylinderGeometry(.012, .012, .36), MAT.brass, 0, .18, 0);
  add(lamp, new THREE.CylinderGeometry(.04, .2, .14, 24, 1, true, 0, Math.PI), new THREE.MeshPhysicalMaterial({ color: 0x0a5a2a, emissive: 0x0a5a2a, emissiveIntensity: .4, roughness: .1, side: THREE.DoubleSide }), 0, .38, 0).rotation.set(Math.PI / 2, 0, Math.PI / 2);
  const lampL = new THREE.PointLight(0xffd8a0, 4, 3, 1.5); lampL.position.set(0, .3, .1); lamp.add(lampL);
  const money = moneyStack(12, 4); money.position.set(.6, .885, -.25); money.rotation.y = .3; D.add(money);
  const money2 = moneyStack(6, 7); money2.position.set(.9, .885, .25); money2.rotation.y = -.5; D.add(money2);
  add(D, new THREE.BoxGeometry(.28, .06, .2), std(0x0c0c0c, { roughness: .3 }), -.7, .915, .2); add(D, new THREE.CapsuleGeometry(.025, .18, 6, 10), std(0x0c0c0c, { roughness: .3 }), -.7, .97, .2).rotation.z = Math.PI / 2;
  add(D, new THREE.BoxGeometry(.2, .04, .1), MAT.gold, -.25, .9, .45); for (const dx of [-.04, .04]) add(D, new THREE.CylinderGeometry(.006, .006, .2), std(0x101010), -.25 + dx, 1.0, .43).rotation.x = -.4;
  for (let i = 0; i < 6; i++) add(D, new THREE.BoxGeometry(.32, .012, .42), std(i % 2 ? 0xf2efe6 : 0xd9c48a, { roughness: .8 }), -1.05, .9 + i * .013, .25).rotation.y = i * .06;
  const npTex = canvasTex(256, 64, (g, w, h) => { g.fillStyle = '#c9a040'; g.fillRect(0, 0, w, h); g.fillStyle = '#2a1a08'; g.font = 'bold 26px Liberation Serif'; g.textAlign = 'center'; g.fillText('EL PRESIDENTE', w / 2, 42); });
  add(D, new THREE.BoxGeometry(.4, .09, .05), [MAT.gold, MAT.gold, MAT.gold, MAT.gold, std(0xffffff, { map: npTex, metalness: .8, roughness: .3 }), MAT.gold], 0, .93, .55).rotation.x = -.3;
  const proj = add(D, new THREE.CylinderGeometry(.12, .14, .03, 32), std(0x111111, { metalness: .8, roughness: .2 }), .35, .9, .3);
  add(D, new THREE.RingGeometry(.08, .11, 32).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0x55e0ff }), .35, .917, .3);
  // tufted leather chair
  const C = new THREE.Group(); C.position.set(0, 0, -.85); s.add(C);
  const tuft = normalFrom(256, 256, (g, w, h) => { g.fillStyle = '#888'; g.fillRect(0, 0, w, h); for (let y = 16; y < h; y += 32) for (let x = (y / 32 | 0) % 2 * 16 + 16; x < w; x += 32) { const q = g.createRadialGradient(x, y, 0, x, y, 16); q.addColorStop(0, '#000'); q.addColorStop(1, '#888'); g.fillStyle = q; g.fillRect(x - 16, y - 16, 32, 32); } }, 4, [3, 4]);
  const chairM = MAT.leather.clone(); chairM.normalMap = tuft;
  add(C, new THREE.BoxGeometry(.95, 1.5, .2), chairM, 0, 1.3, -.1); add(C, new THREE.CapsuleGeometry(.12, .8, 6, 16), chairM, 0, 2.05, -.1).rotation.z = Math.PI / 2;
  add(C, new THREE.BoxGeometry(.9, .18, .75), chairM, 0, .55, .3); for (const sx of [-1, 1]) add(C, new THREE.BoxGeometry(.12, .35, .7), chairM, sx * .5, .75, .3);
  for (let i = 0; i < 5; i++) add(C, new THREE.BoxGeometry(.04, .04, .4), std(0x111111, { metalness: .8, roughness: .3 }), 0, .08, .3).rotation.y = i * 1.256;
  // seated executive
  const man = stickman('executive'); man.root.position.set(0, -.36, -.45); s.add(man.root); s.userData.rigs.push(man);
  for (const L of [man.lLeg, man.rLeg]) { L.a.rotation.set(-Math.PI / 2, 0, 0); L.b.rotation.x = Math.PI / 2; } man.rLeg.a.position.y = .9;
  const stamp = new THREE.Group(); man.rArm.end.add(stamp); stamp.position.y = -.09;
  add(stamp, lathe([[.001, .1], [.025, .1], [.03, .06], [.018, .02], [.03, 0], [.001, 0]], 16), std(0x3a1a08, { roughness: .3, metalness: .2 }));
  add(stamp, new THREE.BoxGeometry(.12, .035, .08), MAT.brass, 0, -.02, 0);
  // hologram documents
  const docTex = (label, col) => canvasTex(512, 680, (g) => { g.strokeStyle = '#7fe8ff'; g.lineWidth = 6; g.shadowColor = '#3cf'; g.shadowBlur = 18; g.strokeRect(12, 12, 488, 656);
    g.fillStyle = 'rgba(120,230,255,.9)'; g.font = 'bold 34px Liberation Sans'; g.fillText('GOBIERNO · DECRETO', 40, 70); g.fillStyle = 'rgba(80,220,255,.55)';
    for (let i = 0; i < 9; i++) g.fillRect(40, 110 + i * 34, 300 + (i * 53 % 130), 10);
    if (label) { g.save(); g.translate(256, 520); g.rotate(-.18); g.strokeStyle = col; g.fillStyle = col; g.shadowColor = col; g.lineWidth = 10; g.strokeRect(-215, -62, 430, 124); g.font = '900 68px "Liberation Sans"'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(label, 0, 4); g.restore(); } });
  const docs = [['LEGALIZADO', '#ffcc33'], ['IMPUESTO', '#ff4d3a'], ['LEGALIZADO', '#ffcc33'], ['IMPUESTO', '#ff4d3a']].map(([l, c]) => { const m = holo(docTex('', c), .5, .66, .9); m.userData = { blank: m.material.map, full: docTex(l, c) }; s.add(m); return m; });
  const big = holo(textTex(['LEGALIZADO', '/ IMPUESTO'], { w: 1024, h: 360, size: 130 }), 2.2, .78); big.position.set(0, 2.75, .2); s.add(big);
  const projBeam = beam(0x55e0ff, .5, 1.2, .07); projBeam.rotation.x = Math.PI; projBeam.position.set(.35, .92, .6); s.add(projBeam);
  dirLight(s, 0xffe2b8, 1.8, [2.5, 5, 4], [0, 1, 0], 4);
  const win = new THREE.SpotLight(0x8aa8ff, 25, 10, .5, .8); win.position.set(0, 3.2, -2.3); win.target.position.set(0, 1, 1); s.add(win, win.target);
  const glow = new THREE.PointLight(0xffaa33, 0, 3); glow.position.set(.35, 1.1, .7); s.add(glow);
  const face = new THREE.SpotLight(0xffe8d0, 2, 6, .3, .7); face.position.set(.5, 2.4, 2.2); face.target = man.head; s.add(face);
  return { s, cam, update(t, dur) {
    const a = lerp(-.7, .7, easeInOut(t / dur));
    cam.position.set(Math.sin(a) * 2.6, 1.95 + Math.sin(t * .5) * .04, Math.cos(a) * 2.6 + .3); cam.lookAt(0, 1.35, .1);
    const period = 1.6, ph = (t % period) / period, down = ph < .35 ? Math.sin(ph / .35 * Math.PI / 2) : ph < .45 ? 1 : 1 - (ph - .45) / .55;
    man.rArm.a.rotation.set(-.55 - (1 - down) * .5, 0, .1); man.rArm.b.rotation.x = -1.05 + down * .1; man.setHand('r', 'fist');
    man.lArm.a.rotation.set(-.6, 0, -.1); man.lArm.b.rotation.x = -.9; man.root.rotation.x = .05 + down * .04; man.head.rotation.set(.1, Math.sin(t * .7) * .15, 0);
    glow.intensity = ph > .33 && ph < .6 ? 6 * (1 - (ph - .33) / .27) : 0;
    docs.forEach((d, i) => { const k = ((t - i * .5) % 4 + 4) % 4 / 4;
      d.position.set(lerp(.35, (i % 2 ? 1 : -1) * (.95 + i * .1), easeOut(k * 3)), .95 + easeOut(k * 2) * 1.2, .6 - k * .4);
      d.rotation.set(-.3 + k * .3, (i % 2 ? -1 : 1) * k * .6, 0); d.material.map = k > .08 ? d.userData.full : d.userData.blank; d.material.opacity = .95 * (1 - Math.pow(k, 3)); });
    big.material.opacity = clamp((t - 2.5) / .6) * (.85 + Math.sin(t * 6) * .1); big.lookAt(cam.position);
    projBeam.material.opacity = .05 + Math.sin(t * 13) * .01;
  } };
}
function noiseFill2(g, w, h) { const R = rng(21); for (let i = 0; i < 3000; i++) { g.fillStyle = `rgba(0,0,0,${R() * .15})`; g.fillRect(R() * w, R() * h, 2, 2); } }

// =====================================================================
// 3) War room: real elevation relief map of Mexico + helicopter formation
// =====================================================================
async function scene3() {
  const { s, cam } = base(0x02060a, .03);
  s.add(new THREE.HemisphereLight(0x2a6a80, 0x100404, .5));
  const meta = await (await fetch('geo/height.json')).json(), hb = new Float32Array(await (await fetch('geo/height.bin')).arrayBuffer()), outline = await (await fetch('geo/mexico_outline.json')).json();
  const relief = await new THREE.TextureLoader().loadAsync('geo/relief.jpg'); relief.colorSpace = THREE.SRGBColorSpace; relief.anisotropy = 8;
  const MW = 9.4, MH = MW * (meta.lat[1] - meta.lat[0]) / (meta.lon[1] - meta.lon[0]), EX = .00009;               // map size + vertical exaggeration
  const toXZ = (lon, lat) => [(lon - meta.lon[0]) / (meta.lon[1] - meta.lon[0]) * MW - MW / 2, (meta.lat[1] - lat) / (meta.lat[1] - meta.lat[0]) * MH - MH / 2];
  const hAt = (lon, lat) => { const x = Math.round((lon - meta.lon[0]) / (meta.lon[1] - meta.lon[0]) * (meta.w - 1)), y = Math.round((meta.lat[1] - lat) / (meta.lat[1] - meta.lat[0]) * (meta.h - 1)); return Math.max(0, hb[clamp(y, 0, meta.h - 1) * meta.w + clamp(x, 0, meta.w - 1)]) * EX; };
  const tg = new THREE.PlaneGeometry(MW, MH, meta.w - 1, meta.h - 1).rotateX(-Math.PI / 2), tp = tg.attributes.position;
  for (let i = 0; i < tp.count; i++) tp.setY(i, hb[i] * EX);
  tg.computeVertexNormals();
  const terrain = add(s, tg, std(0xffffff, { map: relief, roughness: .85 }), 0, 0, 0);
  // table, glowing edge, base
  add(s, new THREE.BoxGeometry(MW + .5, .3, MH + .5), std(0x0b1014, { metalness: .7, roughness: .35 }), 0, -.2, 0);
  for (const [w, d, x, z] of [[MW + .5, .03, 0, MH / 2 + .25], [MW + .5, .03, 0, -MH / 2 - .25], [.03, MH + .5, MW / 2 + .25, 0], [.03, MH + .5, -MW / 2 - .25, 0]])
    add(s, new THREE.BoxGeometry(w, .03, d), new THREE.MeshBasicMaterial({ color: 0x2fd6ff }), x, -.05, z);
  add(s, new THREE.PlaneGeometry(200, 200).rotateX(-Math.PI / 2), std(0x05080a, { roughness: .4, metalness: .5 }), 0, -1.5, 0);
  const grid = new THREE.GridHelper(MW, 47, 0x0d6070, 0x0d6070); grid.material.transparent = true; grid.material.opacity = .25; grid.position.y = .06; s.add(grid);
  // glowing red border (tube along the real outline)
  const borderMat = new THREE.MeshBasicMaterial({ color: 0xff2222 });
  outline.forEach(r => { if (r.length < 60) return; const pts = r.filter((_, i) => i % 3 === 0).map(([lo, la]) => { const [x, z] = toXZ(lo, la); return new THREE.Vector3(x, hAt(lo, la) + .03, z); });
    add(s, new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts, true), pts.length * 2, .012, 5, true), borderMat); });
  // cities & ports with pulsing rings and labels
  const places = [['CDMX', -99.13, 19.43], ['TIJUANA', -117.04, 32.52], ['CD. JUÁREZ', -106.45, 31.69], ['MONTERREY', -100.31, 25.69], ['GUADALAJARA', -103.35, 20.66], ['VERACRUZ', -96.13, 19.17], ['MANZANILLO', -104.32, 19.05], ['CULIACÁN', -107.39, 24.8], ['CANCÚN', -86.85, 21.16], ['MATAMOROS', -97.5, 25.87]];
  const marks = places.map(([n, lo, la], i) => { const [x, z] = toXZ(lo, la), y = hAt(lo, la) + .04, g = new THREE.Group(); g.position.set(x, y, z); s.add(g);
    const ring = new THREE.Mesh(new THREE.RingGeometry(.07, .1, 32).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xff2020, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })); g.add(ring);
    add(g, new THREE.SphereGeometry(.03, 12, 8), new THREE.MeshBasicMaterial({ color: 0xff5050 }));
    const bm = new THREE.Mesh(new THREE.CylinderGeometry(.012, .012, .8, 8, 1, true), new THREE.MeshBasicMaterial({ color: 0xff3030, transparent: true, opacity: .5, blending: THREE.AdditiveBlending, depthWrite: false })); bm.position.y = .4; g.add(bm);
    const lbl = holo(textTex([n], { w: 512, h: 96, size: 56, color: '#ffd0d0', glow: '#ff2020' }), .6, .11); lbl.position.set(0, .88, 0); g.add(lbl);
    return { g, ring, lbl }; });
  // attack/blockade arcs from the north and from the gulf (animated dashes)
  const arcs = [[[-104, 36], [-106.45, 31.69]], [[-98, 36], [-100.31, 25.69]], [[-92, 28], [-96.13, 19.17]], [[-118, 30], [-117.04, 32.52]], [[-86, 26], [-86.85, 21.16]]].map(([[lo0, la0], [lo1, la1]]) => {
    const [x0, z0] = toXZ(lo0, la0), [x1, z1] = toXZ(lo1, la1), curve = new THREE.QuadraticBezierCurve3(new THREE.Vector3(x0, .1, z0), new THREE.Vector3((x0 + x1) / 2, 1.6, (z0 + z1) / 2), new THREE.Vector3(x1, .1, z1));
    const dash = canvasTex(256, 8, (g, w, h) => { const gr = g.createLinearGradient(0, 0, w, 0); gr.addColorStop(0, 'rgba(255,40,40,0)'); gr.addColorStop(.8, 'rgba(255,80,60,1)'); gr.addColorStop(1, 'rgba(255,255,255,1)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); }, { rep: [3, 1] });
    const m = new THREE.Mesh(new THREE.TubeGeometry(curve, 64, .015, 6), new THREE.MeshBasicMaterial({ map: dash, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false })); s.add(m); return dash; });
  // hologram label
  const label = holo(textTex(['BLOQUEO', 'INTERNACIONAL'], { w: 1024, h: 340, size: 125, color: '#ff4040', glow: '#ff0000', border: '#ff4040' }), 1.8, .6); s.add(label);
  // wall screens
  const scr = (draw) => holo(canvasTex(512, 320, draw), 3.2, 2, .8);
  const radar = scr((g, w, h) => { g.strokeStyle = '#1fd6ff'; g.lineWidth = 2; for (let i = 1; i < 6; i++) { g.beginPath(); g.arc(w / 2, h / 2, i * 28, 0, 7); g.stroke(); } g.beginPath(); g.moveTo(w / 2 - 150, h / 2); g.lineTo(w / 2 + 150, h / 2); g.moveTo(w / 2, 10); g.lineTo(w / 2, h - 10); g.stroke();
    g.fillStyle = '#ff3030'; for (let i = 0; i < 9; i++) { g.beginPath(); g.arc(w / 2 + Math.cos(i * 2.1) * (30 + i * 13), h / 2 + Math.sin(i * 2.1) * (30 + i * 13), 4, 0, 7); g.fill(); } g.font = 'bold 22px Liberation Mono'; g.fillStyle = '#1fd6ff'; g.fillText('RADAR · SECTOR NORTE', 14, 28); });
  const alert = scr((g, w, h) => { g.fillStyle = 'rgba(255,30,30,.25)'; g.fillRect(0, 0, w, h); g.strokeStyle = '#ff3030'; g.lineWidth = 6; g.strokeRect(6, 6, w - 12, h - 12); g.fillStyle = '#ff5050'; g.font = '900 64px Liberation Sans'; g.textAlign = 'center'; g.fillText('ALERTA', w / 2, 120);
    g.font = 'bold 28px Liberation Mono'; g.fillText('AMENAZA NIVEL 5', w / 2, 180); g.fillText('SEGURIDAD NACIONAL', w / 2, 220); });
  const graph = scr((g, w, h) => { g.strokeStyle = '#1fd6ff'; g.lineWidth = 3; g.beginPath(); for (let x = 0; x < w; x += 8) g.lineTo(x, h * .8 - Math.pow(x / w, 2) * h * .6 + Math.sin(x * .1) * 8); g.stroke(); g.fillStyle = '#1fd6ff'; g.font = 'bold 22px Liberation Mono'; g.fillText('COMERCIO BILATERAL  -87%', 14, 28);
    for (let i = 0; i < 12; i++) g.fillRect(20 + i * 40, h - 20 - (12 - i) * 9, 24, (12 - i) * 9); });
  [[radar, -4, 2.4, -5], [alert, 0, 3.1, -5.6], [graph, 4, 2.4, -5]].forEach(([m, x, y, z]) => { m.position.set(x, y, z); m.lookAt(0, 1, 4); s.add(m); });
  // helicopters
  const helis = [[0, 0], [-1, -1], [1, -1], [-2, -2], [2, -2]].map(([dx, dz], i) => { const h = helicopter(); h.scale.setScalar(.2); h.userData.off = [dx, dz]; s.add(h); return h; });
  // soldier observing
  const man = stickman('soldier'); man.root.position.set(1.7, -.35, 3.6); man.root.rotation.y = Math.PI + .55; s.add(man.root); s.userData.rigs.push(man);
  man.lArm.a.rotation.set(-.25, 0, -.35); man.lArm.b.rotation.x = -1.7; man.rArm.a.rotation.set(-.25, 0, .35); man.rArm.b.rotation.x = -1.7;
  dirLight(s, 0x9fe0ff, 1.4, [-5, 9, 5], [0, 0, 0], 7);
  const redKey = new THREE.SpotLight(0xff3020, 160, 30, .6, .5); redKey.position.set(4, 8, -3); redKey.target.position.set(0, 0, 0); s.add(redKey, redKey.target);
  const reds = [0, 1].map(i => { const l = new THREE.PointLight(0xff2020, 0, 9); l.position.set(i ? 3 : -2, 1.2, i ? 1 : -1); s.add(l); return l; });
  return { s, cam, update(t, dur) {
    const k = easeInOut(t / dur), cx = lerp(-3.0, 2.6, k);
    cam.position.set(cx, 2.7 - k * .4, 5.4 - k * .6); cam.lookAt(cx * .75, .2, -.4);
    const pulse = .5 + .5 * Math.sin(t * 6);
    marks.forEach((m, i) => { const q = (t * .9 + i * .13) % 1; m.ring.scale.setScalar(1 + q * 2.5); m.ring.material.opacity = 1 - q; m.lbl.lookAt(cam.position); m.lbl.material.opacity = clamp((t - .5 - i * .25) / .4) * .9; });
    reds.forEach(l => l.intensity = 4 + pulse * 10); borderMat.color.setRGB(1, .12 + pulse * .25, .1);
    arcs.forEach((d, i) => d.offset.x = -t * .8 - i * .2);
    helis.forEach((h, i) => { const x = lerp(-7, 7, (t + 1) / (dur + 2)) - h.userData.off[1] * .7; h.position.set(x, 1.5 + Math.sin(t * 1.4 + i) * .04, .2 + h.userData.off[0] * .9);
      h.rotation.set(0, Math.PI / 2, -.12); h.userData.tick(t, i); });
    label.position.set(cx * .75, 1.05, 1.0); label.material.opacity = clamp((t - 4.5) / .5) * (.75 + .25 * Math.sin(t * 9)); label.lookAt(cam.position);
  } };
}

// =====================================================================
// 4) Burning city at night, police lights, helicopter searchlight
// =====================================================================
function scene4() {
  const { s, cam } = base(0x0a0605, .018);
  s.add(new THREE.HemisphereLight(0x3a2a40, 0x120804, .4));
  const R = rng(42);
  const wet = std(0x0b0b0c, { roughness: .18, metalness: .5 });
  add(s, new THREE.PlaneGeometry(300, 300).rotateX(-Math.PI / 2), wet, 0, 0, 0);
  const road = canvasTex(256, 1024, (g, w, h) => { g.fillStyle = '#121214'; g.fillRect(0, 0, w, h); noiseFill2(g, w, h); g.fillStyle = '#c8b040'; for (let y = 0; y < h; y += 120) g.fillRect(w / 2 - 4, y, 8, 60); g.fillStyle = '#ddd'; g.fillRect(10, 0, 6, h); g.fillRect(w - 16, 0, 6, h); }, { rep: [1, 8] });
  add(s, new THREE.PlaneGeometry(8, 120).rotateX(-Math.PI / 2), std(0xffffff, { map: road, roughness: .25, metalness: .3 }), 0, .01, -40);
  // buildings with detailed facades
  const facade = (seed, lit) => canvasTex(256, 512, (g, w, h) => { const Rr = rng(seed); g.fillStyle = '#1a1a1e'; g.fillRect(0, 0, w, h); noiseFill2(g, w, h);
    for (let y = 8; y < h; y += 26) { g.fillStyle = '#26262b'; g.fillRect(0, y - 4, w, 3); for (let x = 8; x < w; x += 22) { const on = Rr() < lit; g.fillStyle = on ? (Rr() < .7 ? '#ffb35a' : '#a8d0ff') : '#0a0c10'; g.fillRect(x, y, 14, 18);
      if (on && Rr() < .3) { g.fillStyle = 'rgba(0,0,0,.4)'; g.fillRect(x, y, 14, 7); } } } }, { rep: [1, 1] });
  const facades = [1, 2, 3, 4].map(i => facade(i, .25 + i * .05));
  const hazards = [];
  for (let i = 0; i < 80; i++) {
    const w = 3 + R() * 5, h = 6 + Math.pow(R(), 1.5) * 34, side = R() < .5 ? -1 : 1, x = side * (6 + R() * 30) + (R() - .5) * 4, z = -10 - R() * 70;
    const t = facades[i % 4].clone(); t.repeat.set(Math.max(1, w / 4), Math.max(1, h / 8)); t.needsUpdate = true;
    const mat = new THREE.MeshStandardMaterial({ color: 0x15151a, roughness: .7, metalness: .2, emissive: 0xffffff, emissiveMap: t, emissiveIntensity: .8, map: t });
    add(s, new THREE.BoxGeometry(w, h, w), mat, x, h / 2, z);
    add(s, new THREE.BoxGeometry(w + .2, .4, w + .2), std(0x101012), x, h + .2, z);                                     // parapet
    if (R() < .5) add(s, new THREE.CylinderGeometry(.6, .6, 1.2, 12), std(0x2a2a2a), x + w * .2, h + 1, z);           // water tank
    if (R() < .4) { add(s, new THREE.CylinderGeometry(.05, .05, 4, 6), std(0x222222), x - w * .3, h + 2, z); const m = add(s, new THREE.SphereGeometry(.18, 8, 6), new THREE.MeshBasicMaterial({ color: 0xff1a1a }), x - w * .3, h + 4.1, z); hazards.push({ m, ph: R() * 6 }); }
  }
  // burning cars and barricade on the street
  const fires = [];
  const car = (x, z, ry) => { const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = ry; s.add(g); const burnt = std(0x1a1512, { roughness: .9 });
    add(g, new THREE.BoxGeometry(1.8, .55, 4.2), burnt, 0, .55, 0); add(g, new THREE.BoxGeometry(1.6, .5, 2.2), burnt, 0, 1.05, -.2);
    for (const sx of [-1, 1]) for (const sz of [-1.3, 1.3]) add(g, new THREE.CylinderGeometry(.33, .33, .25, 16), std(0x0a0a0a), sx * .85, .33, sz).rotation.z = Math.PI / 2;
    const f = new THREE.PointLight(0xff6a1a, 30, 14, 1.6); f.position.set(0, 1.6, 0); g.add(f); fires.push({ l: f, g }); return g; };
  car(-2.2, -9, .4); car(2.5, -18, -.8); car(-1.5, -28, 1.2);
  const sand = std(0x6a5a40, { roughness: 1 });
  for (let i = 0; i < 14; i++) add(s, new THREE.CapsuleGeometry(.18, .5, 6, 10), sand, -3 + (i % 7) * .62, .2 + Math.floor(i / 7) * .3, -4.5).rotation.z = Math.PI / 2;
  // police car with lightbar
  const pc = new THREE.Group(); pc.position.set(3.2, 0, -6); pc.rotation.y = -.5; s.add(pc);
  add(pc, new THREE.BoxGeometry(1.8, .6, 4.4), std(0x0d0d10, { roughness: .3, metalness: .6 }), 0, .6, 0); add(pc, new THREE.BoxGeometry(1.6, .5, 2.2), std(0xe8e8e8, { roughness: .3, metalness: .4 }), 0, 1.15, -.2);
  const redB = add(pc, new THREE.BoxGeometry(.6, .12, .25), new THREE.MeshBasicMaterial({ color: 0xff0000 }), -.35, 1.46, -.2), bluB = add(pc, new THREE.BoxGeometry(.6, .12, .25), new THREE.MeshBasicMaterial({ color: 0x1050ff }), .35, 1.46, -.2);
  const sirR = new THREE.PointLight(0xff0000, 0, 14), sirB = new THREE.PointLight(0x1050ff, 0, 14); sirR.position.set(-.4, 1.8, 0); sirB.position.set(.4, 1.8, 0); pc.add(sirR, sirB);
  // smoke columns + fire sprites
  const smokeTexs = [1, 2, 3].map(smokeTex), smokes = [], flames = [];
  [[-6, -26], [4, -32], [10, -42], [-11, -48], [-2.2, -9], [2.5, -18], [-1.5, -28]].forEach(([x, z], ci) => {
    const big = ci < 4, N = big ? 34 : 14;
    for (let i = 0; i < N; i++) { const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: smokeTexs[i % 3], color: 0x2a2523, transparent: true, depthWrite: false, opacity: .8 })); s.add(sp); smokes.push({ sp, x, z, ph: i / N, seed: R(), big }); }
    for (let i = 0; i < (big ? 6 : 4); i++) { const f = new THREE.Sprite(new THREE.SpriteMaterial({ map: softTex('rgba(255,200,80,1)', 'rgba(255,60,0,0)'), blending: THREE.AdditiveBlending, depthWrite: false })); s.add(f); flames.push({ f, x, z, ph: R() * 6, big }); }
    if (big) { const l = new THREE.PointLight(0xff5a10, 50, 40, 1.6); l.position.set(x, 3, z + 2); s.add(l); fires.push({ l }); }
  });
  const embers = particles(500, 11, 0xff7a20, .08, [18, 9, 12]); embers.position.set(0, 0, -4); s.add(embers);
  // helicopter with searchlight
  const heli = helicopter(0x222428); heli.scale.setScalar(.9); s.add(heli); heli.userData.search.intensity = 400; heli.userData.beam.visible = true;
  // tactical character, close-up
  const man = stickman('tactical'); s.add(man.root); s.userData.rigs.push(man); man.root.rotation.y = -.25;
  man.lArm.a.rotation.set(-.1, 0, -.12); man.lArm.b.rotation.x = -.25; man.rArm.a.rotation.set(-.1, 0, .12); man.rArm.b.rotation.x = -.25;
  dirLight(s, 0xff6a2a, 2.2, [-3, 4, -6], [0, 1, 0], 3, 1024);
  const key = new THREE.SpotLight(0xbfd0ff, 3, 10, .45, .7); key.position.set(2, 3, 3); key.target = man.head; s.add(key);
  return { s, cam, update(t, dur) {
    const k = easeInOut(t / dur);
    cam.position.set(lerp(.55, .25, k), lerp(1.55, 1.62, k), lerp(3.4, 1.9, k)); cam.lookAt(0, lerp(1.6, 1.6, k), 0);
    man.head.rotation.y = .3 + Math.sin(t * .5) * .2; man.root.position.y = Math.sin(t * 1.3) * .005;
    smokes.forEach(o => { const q = (o.ph + t * (o.big ? .06 : .09)) % 1, H = o.big ? 40 : 14; o.sp.position.set(o.x + q * (o.big ? 8 : 3) + Math.sin(q * 6 + o.seed * 9) * 1.2, (o.big ? 2 : 1.4) + q * H, o.z);
      const sc = (o.big ? 4 : 1.5) + q * (o.big ? 18 : 7); o.sp.scale.set(sc, sc, 1); o.sp.material.rotation = o.seed * 6 + t * .1;
      o.sp.material.opacity = Math.min(1, q * 6) * (1 - q) * .8; const hot = q < .12 ? (1 - q / .12) : 0; o.sp.material.color.setRGB(.2 + hot * .6, .17 + hot * .25, .16); });
    flames.forEach(o => { const fl = .7 + .3 * Math.sin(t * 17 + o.ph) * Math.sin(t * 7 + o.ph * 2), sc = (o.big ? 6 : 2.2) * fl; o.f.scale.set(sc * .8, sc, 1); o.f.position.set(o.x + Math.sin(o.ph) * .6, (o.big ? 2.5 : 1.3) + Math.sin(t * 9 + o.ph) * .2, o.z + .5); });
    fires.forEach((f, i) => f.l.intensity = (f.g ? 30 : 50) + Math.sin(t * 13 + i) * 8 + Math.sin(t * 29 + i * 3) * 5);
    hazards.forEach(h => h.m.visible = ((t * 1.2 + h.ph) % 1) < .5);
    const on = ((t * 3) % 1) < .5; redB.material.color.setHex(on ? 0xff0000 : 0x330000); bluB.material.color.setHex(on ? 0x000a33 : 0x1050ff); sirR.intensity = on ? 25 : 0; sirB.intensity = on ? 0 : 25;
    heli.position.set(lerp(-14, 10, t / dur), 16 + Math.sin(t * .8), -22); heli.rotation.set(.05, Math.PI / 2 - .2, -.1); heli.userData.tick(t);
    heli.userData.search.target.position.set(0, -10, 4 + Math.sin(t * .7) * 4); heli.userData.beam.rotation.set(-.45 + Math.sin(t * .7) * .1, 0, Math.sin(t * .5) * .1);
    moveParticles(embers, t, .9, .4);
  } };
}

// =====================================================================
// 5) Courtroom: broken bronze scale of justice, golden-hour light shafts
// =====================================================================
function scene5() {
  const { s, cam } = base(0x1a0e06, .035);
  s.add(new THREE.HemisphereLight(0xffc68a, 0x140a04, .35));
  add(s, new THREE.PlaneGeometry(60, 60).rotateX(-Math.PI / 2), MAT.marble, 0, 0, 0);
  // marble floor crack
  const crack = canvasTex(512, 512, (g, w, h) => { g.clearRect(0, 0, w, h); g.strokeStyle = 'rgba(20,12,8,.95)'; g.lineCap = 'round'; const R = rng(5);
    const br = (x, y, a, l, wd) => { if (l < 8) return; g.lineWidth = wd; g.beginPath(); g.moveTo(x, y); let cx = x, cy = y; for (let i = 0; i < 6; i++) { a += (R() - .5) * .6; cx += Math.cos(a) * l / 6; cy += Math.sin(a) * l / 6; g.lineTo(cx, cy); } g.stroke();
      br(cx, cy, a - .5, l * .6, wd * .7); if (R() < .6) br(cx, cy, a + .6, l * .5, wd * .6); };
    br(256, 256, 0, 200, 6); br(256, 256, 3.1, 180, 6); br(256, 256, 1.6, 120, 4); });
  const cr = add(s, new THREE.PlaneGeometry(4, 4).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: crack, transparent: true, depthWrite: false }), .6, .004, -1.4);
  // back: fluted columns, tall arched windows with light shafts, wood benches
  for (let i = -3; i <= 3; i++) { const c = column(8, .45); c.position.set(i * 3.4, 0, -8); s.add(c); }
  add(s, new THREE.BoxGeometry(30, 12, .5), std(0x2a1d14, { roughness: .8 }), 0, 6, -9.5);
  add(s, new THREE.BoxGeometry(30, .6, 1.4), MAT.cantera, 0, 8.9, -8.2);
  for (let i = -2; i <= 2; i++) { const wx = i * 3.4 + 1.7, sh = new THREE.Shape(); sh.moveTo(-.8, 0); sh.lineTo(-.8, 4); sh.absarc(0, 4, .8, Math.PI, 0, true); sh.lineTo(.8, 0);
    add(s, new THREE.ShapeGeometry(sh), new THREE.MeshBasicMaterial({ color: 0xffc070 }), wx, 2.5, -9.2);
    const bm = beam(0xffb060, 2.6, 16, .045); bm.position.set(wx, 6, -9); bm.rotation.set(-1.05, 0, -.35); s.add(bm); }
  for (let r = 0; r < 3; r++) for (const sx of [-1, 1]) { const g = new THREE.Group(); g.position.set(sx * 4.2, 0, -3.6 - r * 1.3); s.add(g);
    add(g, new THREE.BoxGeometry(3.5, .08, .5), MAT.mahogany, 0, .5, 0); add(g, new THREE.BoxGeometry(3.5, .7, .07), MAT.mahogany, 0, .85, -.25); for (const lx of [-1.6, 1.6]) add(g, new THREE.BoxGeometry(.08, .9, .5), MAT.mahogany, lx, .45, 0); }
  // monumental scale of justice
  const S = new THREE.Group(); S.position.set(.7, 0, -2.4); s.add(S);
  add(S, new THREE.BoxGeometry(2.6, .25, 2.6), MAT.marble, 0, .125, 0); add(S, new THREE.BoxGeometry(2.1, .25, 2.1), MAT.marble, 0, .375, 0);
  add(S, lathe([[.001, 0], [.75, 0], [.75, .12], [.6, .2], [.55, .35], [.45, .45], [.001, .45]], 48), MAT.bronze, 0, .5, 0);
  const pillar = lathe([[.001, 0], [.2, 0], [.16, .3], [.13, .4], [.17, .45], [.13, .5], [.11, 2.5], [.15, 2.6], [.11, 2.7], [.1, 3.6], [.18, 3.7], [.12, 3.85], [.001, 3.9]], 32);
  add(S, pillar, MAT.bronze, 0, .95, 0);
  add(S, new THREE.SphereGeometry(.2, 32, 20), MAT.gold, 0, 5.0, 0); add(S, new THREE.ConeGeometry(.1, .4, 16), MAT.gold, 0, 5.35, 0);
  // beam: intact left half with scroll, snapped right half dangling
  const beamL = new THREE.Group(); beamL.position.set(0, 4.82, 0); beamL.rotation.z = -.22; S.add(beamL);
  add(beamL, new THREE.BoxGeometry(1.9, .14, .14), MAT.bronze, -.95, 0, 0); add(beamL, new THREE.TorusGeometry(.12, .035, 10, 24, 4.5), MAT.bronze, -1.9, .1, 0);
  const jag = (len) => { const g = new THREE.BoxGeometry(len, .14, .14, 8, 1, 1), p = g.attributes.position; for (let i = 0; i < p.count; i++) if (p.getX(i) > len / 2 - .01) p.setX(i, p.getX(i) + (Math.sin(p.getY(i) * 90 + p.getZ(i) * 70)) * .05); g.computeVertexNormals(); return g; };
  add(beamL, jag(.5), MAT.bronze, .25, 0, 0);
  const beamR = add(S, jag(1.1), MAT.bronze, 1.25, 3.95, 0); beamR.rotation.z = -1.05; beamR.rotation.y = Math.PI;
  // chain links helper
  const chain = (a, b, n = 14) => { const g = new THREE.Group(), d = new THREE.Vector3().subVectors(b, a); for (let i = 0; i < n; i++) { const p = a.clone().addScaledVector(d, (i + .5) / n);
    const l = add(g, new THREE.TorusGeometry(.03, .008, 6, 12), MAT.gold, p.x, p.y, p.z); l.lookAt(b); l.rotateY(Math.PI / 2); l.rotateX(i % 2 ? Math.PI / 2 : 0); } return g; };
  const panGeo = lathe([[.001, -.25], [.4, -.22], [.62, -.08], [.7, 0], [.72, .02], [.001, .02]], 48);
  const panL = new THREE.Group(); panL.position.set(-1.88, 4.4, 0); S.add(panL);
  const hangL = new THREE.Group(); hangL.position.set(0, -2.1, 0); panL.add(hangL);
  add(hangL, panGeo, MAT.gold); add(hangL, new THREE.TorusGeometry(.71, .02, 8, 48).rotateX(Math.PI / 2), MAT.gold, 0, .02, 0);
  for (let i = 0; i < 3; i++) { const a = i * 2.09; panL.add(chain(new THREE.Vector3(0, 0, 0), new THREE.Vector3(Math.cos(a) * .66, -2.08, Math.sin(a) * .66), 22)); }
  const panR = add(S, panGeo, MAT.gold, 2.0, .26, 1.2); panR.rotation.set(2.5, .3, .4);
  add(S, new THREE.TorusGeometry(.71, .02, 8, 48), MAT.gold, 2.0, .3, 1.2).rotation.set(2.5 - Math.PI / 2, .3, .4);
  for (let i = 0; i < 3; i++) S.add(chain(new THREE.Vector3(1.55, 3.2, 0), new THREE.Vector3(2.0 + Math.cos(i * 2) * .7, .05, 1.2 + Math.sin(i * 2) * .5), 18));
  const Rr = rng(5); for (let i = 0; i < 24; i++) { const sh = add(s, new THREE.TetrahedronGeometry(.04 + Rr() * .09), MAT.bronze, .7 + (Rr() - .3) * 3.5, .04, -1 + Rr() * 2.4); sh.rotation.set(Rr() * 6, Rr() * 6, Rr() * 6); }
  for (let i = 0; i < 18; i++) add(s, new THREE.CylinderGeometry(.06, .06, .012, 20), MAT.gold, 1.5 + (Rr() - .5) * 2.5, .006, .2 + Rr() * 1.6);              // scattered coins
  // narrator
  const man = stickman('narrator'); man.root.position.set(-.55, 0, .3); s.add(man.root); s.userData.rigs.push(man); man.setHand('r', 'point');
  dirLight(s, 0xffa24a, 3.6, [-6, 3.2, 4], [0, 1.5, -1], 6);
  const back = new THREE.SpotLight(0xff8a3a, 90, 25, .7, .6); back.position.set(4, 7, -6); back.target.position.set(0, 2, -1); s.add(back, back.target);
  const face = new THREE.SpotLight(0xffe2c0, 2, 7, .3, .7); face.position.set(-1.4, 2.4, 2.6); face.target = man.head; s.add(face);
  const dust = particles(400, 3, 0xffc070, .045, [9, 6, 7], .75); dust.position.set(0, 0, -1); s.add(dust);
  return { s, cam, update(t, dur) {
    const k = easeInOut(t / dur);
    cam.position.set(lerp(.2, -.42, k), lerp(2.1, 1.66, k), lerp(6.6, 2.7, k)); cam.lookAt(lerp(.4, -.45, k), lerp(2.4, 1.52, k), -.6);
    const p = easeOut((t - .5) / .8);
    man.rArm.a.rotation.set(lerp(-.03, -1.62, p), 0, lerp(.12, -.1, p)); man.rArm.b.rotation.x = lerp(-.2, -.05, p);
    man.head.rotation.set(-.04, -.08, Math.sin(t * .8) * .03);
    panL.rotation.z = Math.sin(t * 1.1) * .04; panL.rotation.x = Math.sin(t * .8) * .02;
    moveParticles(dust, t, .07);
  } };
}

export async function buildScenes() { return [scene1(), scene2(), await scene3(), scene4(), scene5()]; }
