// High-detail procedural props and sets for the Short.
import * as THREE from 'three';

export const std = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: .6, metalness: 0, ...o });
export function add(parent, geo, mat, x = 0, y = 0, z = 0) { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; parent.add(m); return m; }
export function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
export function canvasTex(w, h, draw, { rep = [1, 1], srgb = true } = {}) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); t.anisotropy = 8; return t;
}
// height canvas -> normal map
export function normalFrom(w, h, draw, strength = 2, rep = [1, 1]) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); draw(g, w, h);
  const src = g.getImageData(0, 0, w, h).data, out = g.createImageData(w, h), H = (x, y) => src[(((y + h) % h) * w + ((x + w) % w)) * 4] / 255;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const dx = (H(x + 1, y) - H(x - 1, y)) * strength, dy = (H(x, y + 1) - H(x, y - 1)) * strength, l = Math.hypot(dx, dy, 1), i = (y * w + x) * 4;
    out.data[i] = (-dx / l * .5 + .5) * 255; out.data[i + 1] = (dy / l * .5 + .5) * 255; out.data[i + 2] = (1 / l * .5 + .5) * 255; out.data[i + 3] = 255; }
  g.putImageData(out, 0, 0); const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); return t;
}
const noiseFill = (g, w, h, n, col, a, r, seed = 1) => { const R = rng(seed); for (let i = 0; i < n; i++) { g.fillStyle = col.replace('A', (a * R()).toFixed(3)); const s = r * (.3 + R()); g.fillRect(R() * w, R() * h, s, s); } };
export const lathe = (pts, segs = 32, p0 = 0, pl = Math.PI * 2) => new THREE.LatheGeometry(pts.map(([r, y]) => new THREE.Vector2(r, y)), segs, p0, pl);

// ---------- materials ----------
export const MAT = {};
export function initMaterials() {
  // tezontle-red volcanic stone blocks (colonial facade)
  const stoneDraw = (g, w, h, hgt) => { g.fillStyle = hgt ? '#808080' : '#6e2f22'; g.fillRect(0, 0, w, h); const R = rng(4);
    for (let y = 0; y < h; y += 32) for (let x = (y / 32) % 2 * 32; x < w + 64; x += 64) { const v = R();
      g.fillStyle = hgt ? `rgb(${150 + v * 60},${150 + v * 60},${150 + v * 60})` : `rgb(${100 + v * 40},${42 + v * 22},${32 + v * 16})`; g.fillRect(x + 2, y + 2, 60, 28); }
    noiseFill(g, w, h, 5000, hgt ? 'rgba(0,0,0,A)' : 'rgba(20,8,4,A)', .5, 3, 9); };
  MAT.tezontle = std(0xffffff, { map: canvasTex(512, 512, (g, w, h) => stoneDraw(g, w, h, 0), { rep: [6, 6] }), normalMap: normalFrom(512, 512, (g, w, h) => stoneDraw(g, w, h, 1), 3, [6, 6]), roughness: .9 });
  MAT.cantera = std(0xffffff, { map: canvasTex(256, 256, (g, w, h) => { g.fillStyle = '#b9a88a'; g.fillRect(0, 0, w, h); noiseFill(g, w, h, 4000, 'rgba(70,55,35,A)', .25, 3, 2); }, { rep: [2, 2] }), roughness: .85 });
  MAT.iron = std(0x161412, { metalness: .8, roughness: .45 });
  MAT.gold = std(0xd4a537, { metalness: 1, roughness: .22 });
  MAT.brass = std(0xb58a3a, { metalness: 1, roughness: .3 });
  MAT.bronze = std(0xa0703a, { metalness: 1, roughness: .32 });
  const woodDraw = (g, w, h, hgt) => { g.fillStyle = hgt ? '#808080' : '#4a1f0e'; g.fillRect(0, 0, w, h); const R = rng(8);
    for (let i = 0; i < 260; i++) { const y = R() * h; g.strokeStyle = hgt ? `rgba(0,0,0,${R() * .4})` : `rgba(${R() < .5 ? '20,6,2' : '120,60,30'},${.1 + R() * .3})`; g.lineWidth = 1 + R() * 3;
      g.beginPath(); g.moveTo(0, y); for (let x = 0; x <= w; x += 32) g.lineTo(x, y + Math.sin(x * .02 + i) * 6 + Math.sin(x * .007 + i * 3) * 10); g.stroke(); } };
  MAT.mahogany = new THREE.MeshPhysicalMaterial({ map: canvasTex(512, 512, (g, w, h) => woodDraw(g, w, h, 0)), normalMap: normalFrom(512, 512, (g, w, h) => woodDraw(g, w, h, 1), 1.5), roughness: .32, clearcoat: .8, clearcoatRoughness: .15 });
  MAT.panelWood = new THREE.MeshPhysicalMaterial({ map: canvasTex(512, 512, (g, w, h) => woodDraw(g, w, h, 0), { rep: [3, 3] }), roughness: .45, clearcoat: .4, color: 0xb08870 });
  MAT.leather = new THREE.MeshPhysicalMaterial({ color: 0x3a120c, roughness: .55, sheen: .4, normalMap: normalFrom(256, 256, (g, w, h) => { g.fillStyle = '#888'; g.fillRect(0, 0, w, h); noiseFill(g, w, h, 9000, 'rgba(0,0,0,A)', .6, 2, 5); }, 1.5, [4, 4]) });
  MAT.greenLeather = new THREE.MeshPhysicalMaterial({ color: 0x0f3a24, roughness: .5, normalMap: MAT.leather.normalMap });
  MAT.marble = new THREE.MeshPhysicalMaterial({ map: canvasTex(1024, 1024, (g, w, h) => { g.fillStyle = '#e4ddd2'; g.fillRect(0, 0, w, h); const R = rng(12);
      for (let i = 0; i < 60; i++) { g.strokeStyle = `rgba(110,100,95,${.05 + R() * .25})`; g.lineWidth = .5 + R() * 2.5; g.beginPath(); let x = R() * w, y = R() * h; g.moveTo(x, y);
        for (let k = 0; k < 30; k++) { x += (R() - .3) * 40; y += (R() - .5) * 40; g.lineTo(x, y); } g.stroke(); } }, { rep: [3, 3] }), roughness: .12, clearcoat: 1, clearcoatRoughness: .08 });
  MAT.glassDark = new THREE.MeshPhysicalMaterial({ color: 0x0c1418, metalness: .6, roughness: .05, clearcoat: 1 });
}

// ---------- helicopter (generic military utility helicopter) ----------
export function helicopter(color = 0x3a3f33) {
  const g = new THREE.Group();
  const panel = canvasTex(512, 256, (c, w, h) => { c.fillStyle = '#' + new THREE.Color(color).getHexString(); c.fillRect(0, 0, w, h); noiseFill(c, w, h, 3000, 'rgba(0,0,0,A)', .12, 4, 3);
    c.strokeStyle = 'rgba(0,0,0,.45)'; c.lineWidth = 1.5; for (let x = 0; x < w; x += 64) { c.beginPath(); c.moveTo(x, 0); c.lineTo(x, h); c.stroke(); } for (let y = 0; y < h; y += 48) { c.beginPath(); c.moveTo(0, y); c.lineTo(w, y); c.stroke(); }
    c.fillStyle = 'rgba(0,0,0,.35)'; for (let x = 0; x < w; x += 64) for (let y = 4; y < h; y += 8) c.fillRect(x + 3, y, 1.5, 1.5);
    c.fillStyle = 'rgba(255,255,255,.55)'; c.font = 'bold 18px Liberation Sans'; c.fillText('UH-7', 300, 150); });
  const body = new THREE.MeshPhysicalMaterial({ map: panel, roughness: .72, metalness: .25 });
  const dark = std(0x111111, { roughness: .5, metalness: .4 }), metal = std(0x555a5e, { metalness: .8, roughness: .35 });
  // fuselage: lathe along Z, squashed for a flat belly
  const fus = add(g, lathe([[.001, -1.0], [.2, -.98], [.42, -.85], [.55, -.5], [.58, .3], [.56, .8], [.48, 1.15], [.32, 1.4], [.12, 1.55], [.001, 1.57]], 40), body);
  fus.rotation.x = Math.PI / 2; fus.scale.set(.86, 1.25, .98);
  // cockpit glazing (upper front)
  const glass = add(g, lathe([[.5, .95], [.45, 1.18], [.32, 1.4], [.14, 1.54], [.02, 1.575]], 40, Math.PI - 1.25, 2.5), MAT.glassDark); glass.rotation.x = Math.PI / 2; glass.scale.set(.875, 1.26, 1.0); glass.position.y = .01;
  for (const s of [-1, 1]) {
    add(g, new THREE.BoxGeometry(.01, .24, .5), MAT.glassDark, s * .49, .14, .45);                       // cabin windows
    add(g, new THREE.BoxGeometry(.012, .5, .02), dark, s * .51, -.02, .05); add(g, new THREE.BoxGeometry(.012, .5, .02), dark, s * .51, -.02, .65); // door frames
    add(g, new THREE.BoxGeometry(.012, .02, .62), metal, s * .515, .32, .35);                               // door rail
    // stub wing + external tank
    const wing = add(g, new THREE.BoxGeometry(.6, .04, .3), body, s * .78, .02, -.1); wing.rotation.z = s * -.08;
    const tank = add(g, lathe([[.001, -.5], [.08, -.42], [.11, -.2], [.11, .25], [.08, .45], [.001, .52]], 20), std(0x2e322a, { roughness: .5, metalness: .3 }), s * .95, -.1, -.1); tank.rotation.x = Math.PI / 2;
    // main landing gear
    add(g, new THREE.CylinderGeometry(.025, .025, .45), metal, s * .42, -.5, .55).rotation.z = s * .4;
    const wheel = add(g, new THREE.TorusGeometry(.09, .045, 10, 20), std(0x0a0a0a, { roughness: .9 }), s * .55, -.68, .55); wheel.rotation.y = Math.PI / 2;
    add(g, new THREE.CylinderGeometry(.06, .06, .05, 16), metal, s * .55, -.68, .55).rotation.z = Math.PI / 2;
    // exhausts
    const ex = add(g, new THREE.CylinderGeometry(.07, .09, .35, 16, 1, true), std(0x2a2522, { metalness: .7, roughness: .5, side: THREE.DoubleSide }), s * .3, .78, -.55); ex.rotation.set(Math.PI / 2 + .3, 0, s * .4);
  }
  // engine housing + intakes
  const eng = add(g, new THREE.CapsuleGeometry(.3, .9, 8, 20), body, 0, .62, .05); eng.rotation.x = Math.PI / 2; eng.scale.set(1.3, 1, .75);
  for (const s of [-1, 1]) add(g, new THREE.CircleGeometry(.12, 20), dark, s * .27, .66, .62).rotation.y = s * .4;
  // rotor mast & hub
  add(g, new THREE.CylinderGeometry(.06, .08, .35, 16), metal, 0, .95, .15);
  add(g, new THREE.CylinderGeometry(.2, .2, .05, 24), metal, 0, .9, .15);
  const rotor = new THREE.Group(); rotor.position.set(0, 1.12, .15); g.add(rotor);
  add(rotor, new THREE.CylinderGeometry(.14, .1, .12, 20), metal);
  for (let i = 0; i < 4; i++) { const arm = new THREE.Group(); arm.rotation.y = i * Math.PI / 2; rotor.add(arm);
    add(arm, new THREE.BoxGeometry(.3, .06, .1), metal, .22, 0, 0);
    const blade = add(arm, new THREE.BoxGeometry(3.1, .025, .2), std(0x1a1a1a, { roughness: .55 }), 1.85, 0, 0); blade.rotation.x = .08;
    add(arm, new THREE.BoxGeometry(.18, .028, .205), std(0xd8c020), 3.32, 0, 0); }                         // tip markings
  const disc = new THREE.Mesh(new THREE.RingGeometry(.3, 3.4, 64).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0x111111, transparent: true, opacity: .14, depthWrite: false, side: THREE.DoubleSide }));
  disc.position.copy(rotor.position); g.add(disc);
  // tail boom, pylon, stabilizer, tail rotor
  const boom = add(g, lathe([[.25, 0], [.2, .9], [.12, 2.2], [.1, 2.4]], 24), body, 0, .22, -.8); boom.rotation.x = -Math.PI / 2;
  const pylonShape = new THREE.Shape([new THREE.Vector2(0, 0), new THREE.Vector2(.45, 0), new THREE.Vector2(.85, .9), new THREE.Vector2(.55, .95), new THREE.Vector2(.05, .25)]);
  const pylon = add(g, new THREE.ExtrudeGeometry(pylonShape, { depth: .06, bevelEnabled: true, bevelSize: .015, bevelThickness: .015 }), body, -.03, .2, -3.0); pylon.rotation.y = Math.PI / 2; pylon.rotation.z = 0;
  pylon.rotation.set(0, Math.PI / 2, 0); pylon.position.set(.03, .22, -2.55);
  add(g, new THREE.BoxGeometry(1.0, .03, .28), body, 0, .3, -2.75);
  const tr = new THREE.Group(); tr.position.set(-.1, .95, -3.25); tr.scale.setScalar(.7); g.add(tr);
  add(tr, new THREE.CylinderGeometry(.04, .04, .08, 12), metal).rotation.z = Math.PI / 2;
  for (let i = 0; i < 4; i++) { const b = add(tr, new THREE.BoxGeometry(.02, .6, .08), std(0x1a1a1a), -.02, 0, 0); b.rotation.x = i * Math.PI / 4 * 2 / 2 * 2; b.rotation.x = i * Math.PI / 2; b.geometry.translate(0, .3, 0); }
  add(g, new THREE.CylinderGeometry(.04, .04, .1, 12), std(0x0a0a0a), 0, .02, -2.7).rotation.z = Math.PI / 2;  // tail wheel
  // sensors, antennas, lights
  add(g, new THREE.SphereGeometry(.12, 20, 14), std(0x222222, { metalness: .5, roughness: .3 }), 0, -.38, 1.25);   // FLIR ball
  add(g, new THREE.CircleGeometry(.06, 16), new THREE.MeshBasicMaterial({ color: 0x334455 }), 0, -.38, 1.37);
  for (const [x, y, z, r] of [[0, .55, .9, .3], [.15, -.45, 0, .4], [-.15, -.45, -.3, .4]]) { const a = add(g, new THREE.CylinderGeometry(.008, .008, r), dark, x, y, z); a.rotation.x = -.3; }
  const nav = [[-.95, .02, -.1, 0xff2020], [.95, .02, -.1, 0x20ff40]].map(([x, y, z, c]) => add(g, new THREE.SphereGeometry(.035, 8, 6), new THREE.MeshBasicMaterial({ color: c }), x + Math.sign(x) * .3, y, z));
  const beacon = add(g, new THREE.SphereGeometry(.05, 10, 8), new THREE.MeshBasicMaterial({ color: 0xff2a2a }), 0, .38, -1.6);
  const search = new THREE.SpotLight(0xdde8ff, 0, 30, .18, .5); search.position.set(0, -.4, 1.2); search.target.position.set(0, -10, 6); g.add(search, search.target);
  const beam = new THREE.Mesh(new THREE.ConeGeometry(1.2, 9, 24, 1, true), new THREE.MeshBasicMaterial({ color: 0xcfe0ff, transparent: true, opacity: .07, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
  beam.position.set(0, -4.9, 2.2); beam.rotation.x = -.45; beam.visible = false; g.add(beam);
  g.traverse(o => { if (o.isMesh) o.castShadow = true; });
  g.userData = { rotor, tr, beacon, search, beam, tick(t, i = 0) { rotor.rotation.y = t * 11 + i; tr.rotation.x = t * 40 + i; beacon.visible = ((t * 1.3 + i * .21) % 1) < .18; } };
  return g;
}

// ---------- ornate baluster / column helpers ----------
export const baluster = (h = .9) => lathe([[.001, 0], [.075, 0], [.075, .06], [.05, .08], [.045, .15], [.085, .32], [.09, .4], [.06, .52], [.035, .62], [.045, .7], [.06, .74], [.06, .8], [.075, .82], [.075, h], [.001, h]], 20);
export const column = (h = 6, r = .32) => {
  const g = new THREE.Group();
  const shaft = new THREE.CylinderGeometry(r * .92, r, h, 32, 1); const p = shaft.attributes.position;          // fluting
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i), a = Math.atan2(z, x), k = 1 - .04 * Math.pow(Math.abs(Math.sin(a * 10)), .5); p.setX(i, x * k); p.setZ(i, z * k); }
  shaft.computeVertexNormals(); add(g, shaft, MAT.cantera, 0, h / 2 + .3, 0);
  add(g, lathe([[.001, 0], [r * 1.35, 0], [r * 1.35, .12], [r * 1.18, .18], [r * 1.12, .26], [r, .3], [.001, .3]], 32), MAT.cantera);
  add(g, lathe([[.001, 0], [r * .95, 0], [r * 1.1, .08], [r * 1.25, .2], [r * 1.45, .3], [r * 1.45, .4], [.001, .4]], 32), MAT.cantera, 0, h + .3, 0);
  return g;
};

// money bundles (narco office prop)
export function moneyStack(n = 6, seed = 1) {
  const g = new THREE.Group(), R = rng(seed);
  const bill = canvasTex(128, 64, (c, w, h) => { c.fillStyle = '#5c7a52'; c.fillRect(0, 0, w, h); c.strokeStyle = '#2e4229'; c.lineWidth = 3; c.strokeRect(4, 4, w - 8, h - 8);
    c.fillStyle = '#d8e4c8'; c.beginPath(); c.arc(w / 2, h / 2, 16, 0, 7); c.fill(); c.fillStyle = '#2e4229'; c.font = 'bold 16px Liberation Sans'; c.fillText('100', 8, 22); c.fillText('100', w - 38, h - 10); });
  const band = std(0xd8c48a, { roughness: .6 }), side = std(0xc8d4b8, { roughness: .9 });
  for (let i = 0; i < n; i++) { const b = new THREE.Group(); b.position.set((i % 3) * .165 + (R() - .5) * .02, Math.floor(i / 3) * .05, (R() - .5) * .03); b.rotation.y = (R() - .5) * .15; g.add(b);
    add(b, new THREE.BoxGeometry(.156, .045, .066), [side, side, std(0xffffff, { map: bill }), side, side, side]);
    add(b, new THREE.BoxGeometry(.03, .047, .068), band); }
  return g;
}
