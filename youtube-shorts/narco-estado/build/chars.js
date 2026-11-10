// Detailed "evolved stickman" characters: white porcelain sphere head with an expressive face,
// sculpted torso with connected shoulders, articulated hands, and layered 3D clothing.
import * as THREE from 'three';

const std = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: .6, metalness: 0, ...o });
const skinMat = () => new THREE.MeshPhysicalMaterial({ color: 0xf4f1ea, roughness: .42, clearcoat: .35, clearcoatRoughness: .4 });
function add(parent, geo, mat, x = 0, y = 0, z = 0) { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; parent.add(m); return m; }
const cap = (r, l, rs = 20) => new THREE.CapsuleGeometry(r, l, 8, rs);
const tex = (w, h, draw, rep = 1) => { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep, rep); return t; };

function camoTex(cols, seed = 3) {
  let s = seed; const r = () => (s = (s * 16807) % 2147483647) / 2147483647;
  return tex(256, 256, (g, w, h) => { g.fillStyle = cols[0]; g.fillRect(0, 0, w, h);
    for (let k = 1; k < cols.length; k++) for (let i = 0; i < 26; i++) { g.fillStyle = cols[k]; g.beginPath();
      const x = r() * w, y = r() * h; for (let a = 0; a < 6.3; a += .7) { const rr = 10 + r() * 22; g.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr * .7); } g.fill(); } }, 3);
}
const fabric = (base, lines = 'rgba(255,255,255,.05)', step = 6) => tex(128, 128, (g, w, h) => { g.fillStyle = base; g.fillRect(0, 0, w, h); g.strokeStyle = lines;
  for (let x = 0; x < w; x += step) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); } }, 4);

// fabric normal map: fine weave + soft irregular rumples (computed from a heightfield)
const _nCache = {};
function fabricNormal(kind = 'wool') {
  if (_nCache[kind]) return _nCache[kind];
  const N = 256, hgt = new Float32Array(N * N); let sd = 11; const r = () => (sd = (sd * 16807) % 2147483647) / 2147483647;
  const blobs = Array.from({ length: 40 }, () => [r() * N, r() * N, 8 + r() * 30, r() - .5]);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    let h = kind === 'wool' ? Math.sin(x * 1.6) * Math.sin(y * 1.6) * .25 + Math.sin((x + y) * .9) * .15 : Math.sin(x * 2.2) * .3 * (Math.sin(y * 2.2) > 0 ? 1 : -1);
    for (const [bx, by, br, bs] of blobs) { const dx = Math.min(Math.abs(x - bx), N - Math.abs(x - bx)), dy = Math.min(Math.abs(y - by), N - Math.abs(y - by)); h += bs * 2.2 * Math.exp(-(dx * dx + dy * dy) / (br * br)); }
    hgt[y * N + x] = h + (r() - .5) * .25;
  }
  const c = document.createElement('canvas'); c.width = c.height = N; const g = c.getContext('2d'), im = g.createImageData(N, N);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const hx = hgt[y * N + (x + 1) % N] - hgt[y * N + (x + N - 1) % N], hy = hgt[((y + 1) % N) * N + x] - hgt[((y + N - 1) % N) * N + x];
    const v = new THREE.Vector3(-hx, -hy, 2).normalize(), i = (y * N + x) * 4;
    im.data[i] = (v.x * .5 + .5) * 255; im.data[i + 1] = (v.y * .5 + .5) * 255; im.data[i + 2] = (v.z * .5 + .5) * 255; im.data[i + 3] = 255; }
  g.putImageData(im, 0, 0); const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(3, 3); return _nCache[kind] = t;
}
const cloth = (o, kind = 'wool') => new THREE.MeshPhysicalMaterial({ roughness: .78, sheen: .5, sheenRoughness: .7, sheenColor: new THREE.Color(0x777777),
  normalMap: fabricNormal(kind), normalScale: new THREE.Vector2(.55, .55), ...o });

const lerpN = (a, b, k) => a + (b - a) * k;
const clamp01 = x => Math.min(1, Math.max(0, x));
// tapered garment tube from a [radius, y] profile, with fabric folds pushed into the surface
function garment(profile, folds = [], seed = 1, segs = 40) {
  const curve = new THREE.SplineCurve(profile.map(([r, y]) => new THREE.Vector2(r, y)));
  const pts = curve.getSpacedPoints(Math.max(24, Math.round(curve.getLength() / .006))); pts[0].x = profile[0][0]; pts[pts.length - 1].x = profile[profile.length - 1][0];
  const geo = new THREE.LatheGeometry(pts, segs), p = geo.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i), rad = Math.hypot(x, z); if (rad < .004) continue;
    const th = Math.atan2(z, x); let d = (Math.sin(th * 5 + y * 40 + seed) + Math.sin(th * 9 - y * 70 + seed * 2)) * .0012;
    for (const [yc, w, amp, k] of folds) { const f = Math.exp(-Math.pow((y - yc) / w, 2)); d += amp * f * (Math.sin(th * k + Math.sin(y * 60 + seed) * 1.5) * .7 + Math.sin(y * 90 + th * 2) * .3); }
    const fade = clamp01(rad / .03); const sc = (rad + d * fade) / rad; p.setX(i, x * sc); p.setZ(i, z * sc);
  }
  geo.computeVertexNormals(); return geo;
}

// --- illustrated faces: drawn on an equirectangular texture (front of head = u .25) ---
const FACES = {
  president: { iris: '#3b2414', lid: .36, tilt: .05, brow: 'smug', browC: '#17110c', bw: 15, mouth: 'smirk', mustache: true, stubble: .55, nasal: true },
  executive: { iris: '#4f7396', lid: .22, tilt: 0, brow: 'smug', browC: '#9c9c9c', bw: 13, mouth: 'grin', wrinkles: true, blush: .12, mx: -10 },
  soldier:   { iris: '#3a2a1a', lid: .32, tilt: .18, brow: 'stern', browC: '#2a1f16', bw: 15, mouth: 'frown', stubble: .8, paint: 'rgba(40,55,25,.75)' },
  tactical:  { iris: '#6a4a22', lid: .34, tilt: .38, brow: 'angry', browC: '#120d0a', bw: 16, mouth: null, paint: 'rgba(10,10,10,.85)' },
  narrator:  { iris: '#4a3020', lid: .16, tilt: .04, brow: 'pro', browC: '#2e1d12', bw: 14, mouth: 'smile', nasalSoft: true, mx: 0 },
};
function faceTex(kind, closed) {
  const F = FACES[kind], U = 326, CX = 512, CY = 512, ink = '#22140e';
  return tex(2048, 1024, (g) => {
    g.fillStyle = '#f4f1ea'; g.fillRect(0, 0, 2048, 1024); g.translate(CX, CY); g.scale(1.55, 1.55); g.translate(-CX, -CY);
    let q = kind.length * 97; const rnd = () => (q = (q * 16807) % 2147483647) / 2147483647;
    const ey = CY - 34, mx = CX + (F.mx ?? 6), my = CY + 122;
    // soft facial shading: cheeks, under-brow, chin
    const soft = (x, y, r, col) => { const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, col); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); };
    for (const sx of [-1, 1]) soft(CX + sx * 110, ey - 10, 60, 'rgba(150,130,115,.16)');
    soft(CX, my + 70, 60, 'rgba(150,130,115,.12)');
    if (F.blush) for (const sx of [-1, 1]) soft(CX + sx * 118, CY + 62, 50, `rgba(235,120,110,${F.blush})`);
    if (F.paint) for (const sx of [-1, 1]) { g.save(); g.filter = 'blur(6px)'; g.fillStyle = F.paint; g.beginPath(); g.ellipse(CX + sx * 108, ey + 38, 46, 14, sx * .12, 0, 7); g.fill(); g.restore(); }
    if (F.stubble) { for (let i = 0; i < 2600; i++) { const a = rnd() * 6.28, rr = Math.sqrt(rnd()), x = CX + Math.cos(a) * rr * 150, y = my + 30 + Math.sin(a) * rr * 95;
        if (y < my - 20) continue; g.fillStyle = `rgba(55,45,40,${F.stubble * (.15 + rnd() * .3)})`; g.fillRect(x, y, 1.6, 1.6); } }
    if (F.freckles) for (let i = 0; i < 40; i++) { const sx = rnd() < .5 ? -1 : 1; g.fillStyle = 'rgba(170,110,80,.4)'; g.beginPath(); g.arc(CX + sx * (55 + rnd() * 80), CY + 20 + rnd() * 50, 1.5 + rnd() * 1.6, 0, 7); g.fill(); }
    // eyes
    for (const sx of [-1, 1]) {
      const ex = CX + sx * 106, rx = 31, ry = 25;
      if (closed) { g.strokeStyle = ink; g.lineWidth = 6; g.lineCap = 'round'; g.beginPath(); g.moveTo(ex - rx, ey + 2); g.quadraticCurveTo(ex, ey + 14, ex + rx, ey + 2); g.stroke();
        g.lineWidth = 3; g.beginPath(); g.moveTo(ex + sx * rx, ey + 2); g.lineTo(ex + sx * (rx + 9), ey - 5); g.stroke(); continue; }
      const yl = x => ey - ry + F.lid * 2 * ry + F.tilt * ry * ((x - ex) / rx) * -sx;
      g.save(); g.beginPath(); g.ellipse(ex, ey, rx, ry, 0, 0, 7); g.clip();
      const sg = g.createLinearGradient(0, ey - ry, 0, ey + ry); sg.addColorStop(0, '#cfc9c0'); sg.addColorStop(.45, '#ffffff'); sg.addColorStop(1, '#ece8e2');
      g.fillStyle = sg; g.fillRect(ex - rx, ey - ry, 2 * rx, 2 * ry);
      const iy = ey + 3, ig = g.createRadialGradient(ex, iy, 2, ex, iy, 17); ig.addColorStop(0, '#000'); ig.addColorStop(.35, F.iris); ig.addColorStop(.8, F.iris); ig.addColorStop(1, '#120a06');
      g.fillStyle = ig; g.beginPath(); g.arc(ex, iy, 17, 0, 7); g.fill();
      g.fillStyle = '#060606'; g.beginPath(); g.arc(ex, iy, 7.5, 0, 7); g.fill();
      g.fillStyle = '#fff'; g.beginPath(); g.arc(ex - 6, iy - 7, 5.5, 0, 7); g.fill(); g.beginPath(); g.arc(ex + 6, iy + 6, 2.4, 0, 7); g.fill();
      // upper lid (skin) with soft shadow line
      g.fillStyle = '#f0ece4'; g.beginPath(); g.moveTo(ex - rx - 2, yl(ex - rx)); g.lineTo(ex + rx + 2, yl(ex + rx)); g.lineTo(ex + rx + 2, ey - ry - 4); g.lineTo(ex - rx - 2, ey - ry - 4); g.fill();
      g.strokeStyle = 'rgba(60,40,30,.25)'; g.lineWidth = 9; g.beginPath(); g.moveTo(ex - rx, yl(ex - rx) + 4); g.lineTo(ex + rx, yl(ex + rx) + 4); g.stroke();
      g.restore();
      // outlines: thick upper lash line, thin lower lid, outer lash flick
      g.strokeStyle = ink; g.lineCap = 'round'; g.lineWidth = 2.5; g.globalAlpha = .55; g.beginPath(); g.ellipse(ex, ey, rx, ry, 0, .15, Math.PI - .15); g.stroke(); g.globalAlpha = 1;
      g.lineWidth = 6; g.beginPath();
      if (F.lid > .06) { const hw = rx * Math.sqrt(Math.max(0, 1 - Math.pow((yl(ex) - ey) / ry, 2))); g.moveTo(ex - hw - 2, yl(ex - hw)); g.lineTo(ex + hw + 2, yl(ex + hw)); }
      else g.ellipse(ex, ey, rx, ry, 0, Math.PI + .1, -.1);
      g.stroke();
      const ox = ex + sx * rx;
      if (F.wrinkles) { g.lineWidth = 2; g.strokeStyle = 'rgba(80,60,50,.4)'; for (let k = -1; k <= 1; k++) { g.beginPath(); g.moveTo(ox + sx * 10, ey + k * 9); g.lineTo(ox + sx * 26, ey + k * 14); g.stroke(); }
        g.beginPath(); g.ellipse(ex, ey + 30, 22, 6, 0, .2, Math.PI - .2); g.stroke(); }
      // eyebrow: tapered, slightly hairy
      const shapes = { smug: sx < 0 ? [-16, -30, -8] : [2, -4, 4], angry: [16, -2, -14], stern: [8, -2, -4], raised: [-14, -22, -6], pro: [-2, -12, -2] }[F.brow];
      const by = ey - 50, ix = ex - sx * 26, ox2 = ex + sx * 40, pts = [];
      for (let t = 0; t <= 1; t += .05) { const x = ix + (ox2 - ix) * t, y = by + (1 - t) * (1 - t) * shapes[0] + 2 * (1 - t) * t * shapes[1] + t * t * shapes[2]; pts.push([x, y, F.bw * (1 - t * .65)]); }
      g.fillStyle = F.browC; g.beginPath(); pts.forEach(([x, y, w]) => g.lineTo(x, y - w / 2)); [...pts].reverse().forEach(([x, y, w]) => g.lineTo(x, y + w / 2)); g.closePath(); g.fill();
      g.strokeStyle = F.browC; g.lineWidth = 1.5; for (let i = 0; i < 40; i++) { const [x, y, w] = pts[Math.floor(rnd() * (pts.length - 1))]; g.beginPath(); g.moveTo(x, y + w / 2); g.lineTo(x + sx * 7, y - w / 2 - 2); g.stroke(); }
    }
    if (F.wrinkles) { g.strokeStyle = 'rgba(80,60,50,.3)'; g.lineWidth = 2.5; for (let k = 0; k < 3; k++) { g.beginPath(); g.moveTo(CX - 90, CY - 150 + k * 18); g.bezierCurveTo(CX - 30, CY - 158 + k * 18, CX + 30, CY - 142 + k * 18, CX + 90, CY - 150 + k * 18); g.stroke(); } }
    // nose
    if (F.mouth !== null) { g.strokeStyle = 'rgba(110,85,70,.5)'; g.lineWidth = 4; g.lineCap = 'round';
      g.beginPath(); g.moveTo(CX - 4, CY - 20); g.quadraticCurveTo(CX - 18, CY + 30, CX - 6, CY + 44); g.stroke();
      g.beginPath(); g.moveTo(CX - 18, CY + 44); g.quadraticCurveTo(CX, CY + 54, CX + 18, CY + 44); g.stroke();
      soft(CX + 4, CY + 30, 26, 'rgba(255,255,255,.5)'); }
    if (F.nasalSoft) { g.strokeStyle = 'rgba(110,85,70,.18)'; g.lineWidth = 2.5; for (const sx of [-1, 1]) { g.beginPath(); g.moveTo(CX + sx * 36, CY + 54); g.quadraticCurveTo(CX + sx * 54, CY + 90, CX + sx * 50, my + 8); g.stroke(); } }
    if (F.nasal) { g.strokeStyle = 'rgba(110,85,70,.3)'; g.lineWidth = 3; for (const sx of [-1, 1]) { g.beginPath(); g.moveTo(CX + sx * 36, CY + 52); g.quadraticCurveTo(CX + sx * 58, CY + 95, CX + sx * 52, my + 18); g.stroke(); } }
    // mouth
    g.lineCap = 'round';
    if (F.mouth === 'smirk') { g.strokeStyle = '#3a1a14'; g.lineWidth = 7; g.beginPath(); g.moveTo(mx - 42, my + 4); g.quadraticCurveTo(mx + 2, my + 18, mx + 44, my - 14); g.stroke();
      g.lineWidth = 3; g.beginPath(); g.moveTo(mx + 46, my - 22); g.quadraticCurveTo(mx + 54, my - 12, mx + 48, my - 4); g.stroke();
      g.strokeStyle = 'rgba(120,80,70,.35)'; g.lineWidth = 5; g.beginPath(); g.moveTo(mx - 16, my + 30); g.quadraticCurveTo(mx + 4, my + 36, mx + 22, my + 26); g.stroke(); }
    if (F.mouth === 'smile') { g.strokeStyle = '#3a1a14'; g.lineWidth = 6.5; g.beginPath(); g.moveTo(mx - 40, my - 6); g.quadraticCurveTo(mx, my + 14, mx + 40, my - 6); g.stroke();
      g.lineWidth = 2.5; for (const sx of [-1, 1]) { g.beginPath(); g.moveTo(mx + sx * 42, my - 12); g.quadraticCurveTo(mx + sx * 48, my - 5, mx + sx * 43, my + 1); g.stroke(); }
      g.strokeStyle = 'rgba(120,80,70,.3)'; g.lineWidth = 5; g.beginPath(); g.moveTo(mx - 14, my + 26); g.quadraticCurveTo(mx, my + 31, mx + 14, my + 26); g.stroke(); }
    if (F.mouth === 'frown') { g.strokeStyle = '#3a1a14'; g.lineWidth = 7; g.beginPath(); g.moveTo(mx - 36, my + 12); g.quadraticCurveTo(mx, my - 8, mx + 36, my + 12); g.stroke();
      g.strokeStyle = 'rgba(120,80,70,.35)'; g.lineWidth = 4; g.beginPath(); g.moveTo(mx - 14, my + 30); g.quadraticCurveTo(mx, my + 25, mx + 14, my + 30); g.stroke(); }
    if (F.mouth === 'grin') { const w = 48;
      g.beginPath(); g.moveTo(mx - w, my - 10); g.quadraticCurveTo(mx, my + 2, mx + w, my - 10); g.quadraticCurveTo(mx, my + 56, mx - w, my - 10); g.closePath();
      g.save(); g.clip(); g.fillStyle = '#5a1418'; g.fillRect(mx - w, my - 20, 2 * w, 80);
      g.fillStyle = '#fbfaf6'; g.beginPath(); g.moveTo(mx - w, my - 14); g.quadraticCurveTo(mx, my - 2, mx + w, my - 14); g.lineTo(mx + w, my + 6); g.quadraticCurveTo(mx, my + 20, mx - w, my + 6); g.fill();
      g.strokeStyle = 'rgba(0,0,0,.15)'; g.lineWidth = 1.5; for (let k = -3; k <= 3; k++) { g.beginPath(); g.moveTo(mx + k * 12, my - 6); g.lineTo(mx + k * 12, my + 12); g.stroke(); }
      g.fillStyle = '#d0606a'; g.beginPath(); g.ellipse(mx, my + 38, 24, 12, 0, 0, 7); g.fill(); g.restore();
      g.strokeStyle = '#3a1a14'; g.lineWidth = 4.5; g.beginPath(); g.moveTo(mx - w, my - 10); g.quadraticCurveTo(mx, my + 2, mx + w, my - 10); g.quadraticCurveTo(mx, my + 56, mx - w, my - 10); g.stroke();
      g.lineWidth = 3; for (const sx of [-1, 1]) { g.beginPath(); g.moveTo(mx + sx * (w + 2), my - 18); g.quadraticCurveTo(mx + sx * (w + 9), my - 9, mx + sx * (w + 3), my - 1); g.stroke(); } }
    if (F.mustache) { const y = my - 18; g.fillStyle = '#17110c'; g.beginPath(); g.moveTo(CX - 66, y + 14);
      g.quadraticCurveTo(CX - 40, y - 26, CX, y - 18); g.quadraticCurveTo(CX + 40, y - 26, CX + 66, y + 14); g.quadraticCurveTo(CX + 36, y - 2, CX, y + 2); g.quadraticCurveTo(CX - 36, y - 2, CX - 66, y + 14); g.fill();
      g.strokeStyle = 'rgba(255,255,255,.12)'; g.lineWidth = 1.5; for (let i = 0; i < 70; i++) { const x = CX + (rnd() - .5) * 110; g.beginPath(); g.moveTo(x, y - 12 + rnd() * 6); g.lineTo(x + (x - CX) * .15, y + 4); g.stroke(); } }
  });
}

// --- outfits & personalities ---
const LOOKS = {
  president: { suit: 0x101014, tex: fabric('#16161b', 'rgba(255,255,255,.04)'), shirt: 0xf4f4f4, tie: 0x0c0c0c, shoes: 0x060606,
    hair: 'slick', hairColor: 0x15110e, brows: 'smug', mouth: 'smirk', mustache: true, sash: true, watch: true, ring: true, pocket: 0xc9962e },
  executive: { suit: 0x2c3038, tex: fabric('#2c3038', 'rgba(255,255,255,.09)', 8), shirt: 0xeef2f8, tie: 0x7a1010, shoes: 0x1a0e06,
    hair: 'side', hairColor: 0x8a8a8a, brows: 'smug', mouth: 'grin', glasses: true, cigar: true, watch: true, pocket: 0xffffff },
  soldier: { camo: ['#4b5532', '#2f3520', '#6b6a45', '#1f2416'], shoes: 0x2a2015, vest: 0x3d4229, helmet: true, brows: 'stern', mouth: 'frown', strap: true, patch: true },
  tactical: { solid: 0x171717, shoes: 0x0a0a0a, vest: 0x1e1e1e, balaclava: true, brows: 'angry', gloves: true, pads: true, radio: true },
  narrator: { suit: 0x16233f, tex: fabric('#16233f', 'rgba(255,255,255,.05)'), shirt: 0xf6f6f6, tie: 0x8a1a1a, shoes: 0x0b0b0b,
    hair: 'side', hairColor: 0x3a2414, brows: 'raised', mouth: 'grin', loose: true, watch: true },
};

// place an object on the head sphere, facing outward; u/v are in head-radius units
function onHead(head, R, obj, u, v, push = 0, rz = 0) {
  const d = new THREE.Vector3(u, v, Math.sqrt(Math.max(0, 1 - u * u - v * v))).normalize();
  obj.position.copy(d).multiplyScalar(R + push);
  obj.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), d).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), rz));
  head.add(obj); return obj;
}

function face(head, R, L, rig) {
  // painted, illustrated face (open + blink textures) on the porcelain head
  const open = faceTex(rig.kind, false), shut = faceTex(rig.kind, true);
  head.material = new THREE.MeshPhysicalMaterial({ map: open, roughness: .45, clearcoat: .3, clearcoatRoughness: .45 });
  rig.faceTex = { open, shut };
  if (L.cigar) { const g = new THREE.Group(); const c = add(g, new THREE.CylinderGeometry(R * .05, R * .055, R * .9, 12), std(0x5a3418, { roughness: .9 })); c.rotation.x = Math.PI / 2; c.position.z = R * .4;
    add(g, new THREE.CylinderGeometry(R * .052, R * .052, R * .06, 12), new THREE.MeshBasicMaterial({ color: 0xff5a10 }), 0, 0, R * .86).rotation.x = Math.PI / 2;
    onHead(head, R, g, .2, -.5, -.01, 0); g.rotateY(.5); rig.cigar = g; }
  if (L.glasses) { const gold = std(0xd4a537, { metalness: 1, roughness: .25 }), gl = new THREE.Group();
    for (const s of [-1, 1]) { add(gl, new THREE.TorusGeometry(R * .27, R * .025, 8, 32), gold, s * R * .47, 0, 0);
      add(gl, new THREE.CircleGeometry(R * .26, 24), new THREE.MeshPhysicalMaterial({ color: 0x88aacc, transparent: true, opacity: .25, roughness: 0, metalness: .2 }), s * R * .47, 0, 0); }
    add(gl, new THREE.BoxGeometry(R * .2, R * .03, R * .03), gold);
    onHead(head, R, gl, 0, .16, R * .2); }
  if (L.hair) { const base = '#' + new THREE.Color(L.hairColor).getHexString();
    const hm = std(0xffffff, { roughness: .45, map: tex(512, 256, (g, w, h) => { g.fillStyle = base; g.fillRect(0, 0, w, h); let q = 7; const r = () => (q = (q * 16807) % 2147483647) / 2147483647;
      for (let i = 0; i < 900; i++) { const x = r() * w, l = 40 + r() * 140; g.strokeStyle = r() < .5 ? 'rgba(255,255,255,' + (.04 + r() * .1) + ')' : 'rgba(0,0,0,' + (.1 + r() * .2) + ')'; g.lineWidth = 1 + r() * 2;
        g.beginPath(); g.moveTo(x, r() * h * .3); g.quadraticCurveTo(x + (r() - .5) * 20, h * .5, x + (r() - .5) * 30, l + h * .3); g.stroke(); } }) });
    const h = add(head, new THREE.SphereGeometry(R * 1.06, 40, 20, 0, Math.PI * 2, 0, Math.PI * .4), hm); h.rotation.x = -.5; h.scale.set(1, 1, 1.04);
    if (L.hair === 'side') { h.rotation.z = .12; h.scale.set(1.02, 1.03, 1.05); }
    if (L.hair === 'slick') { h.scale.set(1.01, 1.02, 1.05); for (const sx of [-1, 1]) { const sb = add(head, cap(R * .07, R * .25, 8), hm, sx * R * .96, R * .05, -R * .08); sb.scale.z = .5; sb.rotation.z = sx * .1; } } }
  if (L.helmet) { const hm = new THREE.MeshStandardMaterial({ map: camoTex(['#4b5532', '#2f3520', '#6b6a45']), roughness: .9 });
    const h = add(head, new THREE.SphereGeometry(R * 1.14, 36, 18, 0, Math.PI * 2, 0, Math.PI * .5), hm, 0, R * .36, 0);
    add(head, new THREE.TorusGeometry(R * 1.12, R * .07, 8, 40), std(0x2f3520, { roughness: .9 }), 0, R * .36, 0).rotation.x = Math.PI / 2;
    if (L.strap) for (const s of [-1, 1]) { const st = add(head, cap(R * .03, R * .9, 6), std(0x1d1d14)); st.position.set(s * R * .9, -R * .35, R * .2); st.rotation.z = s * .25; } }
  if (L.balaclava) { const bm = std(0x0f0f0f, { roughness: 1, map: fabric('#111111', 'rgba(255,255,255,.04)', 4) });
    add(head, new THREE.SphereGeometry(R * 1.04, 36, 18, 0, Math.PI * 2, 0, Math.PI * .33), bm).rotation.x = -.05;          // top
    const low = add(head, new THREE.SphereGeometry(R * 1.04, 36, 18, 0, Math.PI * 2, Math.PI * .56, Math.PI * .44), bm); low.rotation.x = .1; // lower face
    for (const s of [-1, 1]) add(head, new THREE.SphereGeometry(R * 1.035, 20, 6, Math.PI / 2 + s * 1.3 - .3, .6, Math.PI * .3, Math.PI * .3), bm); // side band
  }
}

function hand(L, mat, side, pose = 'relaxed') {
  const g = new THREE.Group();
  const palm = add(g, cap(.032, .035, 12), mat); palm.scale.set(.55, 1, 1.05); palm.position.y = -.035;
  const fingers = [];
  for (let i = 0; i < 4; i++) { const f = new THREE.Group(); f.position.set(0, -.07, .024 - i * .016); g.add(f);
    const seg = add(f, cap(.0085, .04 - Math.abs(i - 1.2) * .005, 8), mat); seg.position.y = -.022; fingers.push(f); }
  const th = new THREE.Group(); th.position.set(-side * .012, -.03, .03); g.add(th);
  const ts = add(th, cap(.009, .032, 8), mat); ts.position.y = -.018; th.rotation.set(.6, 0, side * .5);
  const setPose = p => fingers.forEach((f, i) => { const curl = p === 'fist' ? 1.6 : p === 'point' ? (i ? 1.6 : 0) : .35 + i * .08; f.rotation.z = -side * curl; });
  setPose(pose); g.userData.setPose = setPose; return g;
}

export function stickman(kind) {
  const L = LOOKS[kind], rig = { root: new THREE.Group(), kind }, root = rig.root;
  const skin = skinMat();
  const top = L.camo ? cloth({ map: camoTex(L.camo), roughness: .92, sheenColor: new THREE.Color(0x3a4030) }, 'ripstop')
            : L.solid ? cloth({ color: L.solid, roughness: .9, sheenColor: new THREE.Color(0x3a3a3a) }, 'ripstop')
            : cloth({ map: L.tex, roughness: .7, sheenColor: new THREE.Color(L.suit).offsetHSL(0, 0, .25) });
  const legsM = top, shoeM = std(L.shoes, { roughness: L.suit ? .2 : .75, metalness: L.suit ? .1 : 0 });
  // sculpted torso (lathe profile: hips → waist → chest → shoulders), jacket hem flares below the belt
  const prof = (L.suit ? [[.001, .76], [.168, .762], [.165, .8], [.155, .9], [.145, 1.0]] : [[.001, .8], [.15, .82], [.155, .9], [.143, 1.0]])
    .concat([[.16, 1.1], [.182, 1.22], [.192, 1.32], [.188, 1.38], [.155, 1.44], [.07, 1.48], [.001, 1.49]]).map(([r, y]) => [r, y]);
  const rAt = y => { for (let i = 1; i < prof.length; i++) { const [r0, y0] = prof[i - 1], [r1, y1] = prof[i]; if (y <= y1 && y >= y0) return r0 + (r1 - r0) * (y - y0) / (y1 - y0); } return .15; };
  const surfZ = (x, y) => Math.sqrt(Math.max(0, rAt(y) ** 2 - x * x)) * .66;   // front of the torso at (x, y)
  const conform = (geo, off) => { const p = geo.attributes.position; for (let i = 0; i < p.count; i++) p.setZ(i, surfZ(p.getX(i), p.getY(i)) + off + p.getZ(i)); geo.computeVertexNormals(); return geo; };
  const torso = add(root, garment(prof, [[1.0, .05, .004, 7], [1.36, .05, .003, 4]], 3, 48), top); torso.scale.z = .66;
  if (L.suit) for (const sx of [-1, 1]) { const vent = add(root, new THREE.BoxGeometry(.004, .14, .004), std(0x000000), sx * .02, .83, .113); }
  // shoulders: a continuous yoke so arms grow out of the body
  const yoke = add(root, cap(.075, .3, 16), top, 0, 1.385, 0); yoke.rotation.z = Math.PI / 2; yoke.scale.set(1, 1, .82);
  add(root, cap(.05, .03), skin, 0, 1.5, 0);                                     // neck
  const R = .135, head = add(root, new THREE.SphereGeometry(R, 56, 40), skin, 0, 1.63, 0); rig.head = head;
  face(head, R, L, rig);
  if (L.suit) {
    const shirt = std(L.shirt, { roughness: .5 });
    const collar = add(root, new THREE.TorusGeometry(.05, .016, 8, 24), shirt, 0, 1.48, 0); collar.rotation.x = Math.PI / 2 + .25;
    // open-front V: shirt + tie with knot
    const vee = new THREE.PlaneGeometry(1, 1, 12, 30), vp = vee.attributes.position;
    for (let i = 0; i < vp.count; i++) { const t = .5 - vp.getY(i), y = 1.48 - t * .27; vp.setXYZ(i, vp.getX(i) * .14 * (1 - t), y, 0); }
    add(root, conform(vee, .015), shirt);
    // tie: knot + blade that widens and ends in a point, with a woven diagonal stripe
    const tieTex = tex(64, 256, (g, w, h) => { g.fillStyle = '#' + new THREE.Color(L.tie).getHexString(); g.fillRect(0, 0, w, h);
      g.strokeStyle = 'rgba(255,255,255,.10)'; g.lineWidth = 4; for (let i = -h; i < h; i += 18) { g.beginPath(); g.moveTo(0, i); g.lineTo(w, i + w * .7); g.stroke(); } });
    tieTex.repeat.set(1, 1);
    const tg = new THREE.PlaneGeometry(1, 1, 6, 60), tp = tg.attributes.position, drop = L.loose ? .035 : 0;
    const tw = t => t < .1 ? lerpN(.034, .024, t / .1) : t < .92 ? lerpN(.02, .05, (t - .1) / .82) : .05 * (1 - (t - .92) / .08);
    for (let i = 0; i < tp.count; i++) { const u = tp.getX(i), t = .5 - tp.getY(i), w = tw(t), x = u * w + (L.loose ? t * .012 : 0);
      tp.setXYZ(i, x, 1.465 - drop - t * .3, (t < .1 ? .007 : .0025) * (1 - Math.abs(u) * 1.6)); }
    add(root, conform(tg, .018), std(0xffffff, { map: tieTex, roughness: .35, side: THREE.DoubleSide }));
    // lapels (peaked), buttons, breast pocket
    for (const s of [-1, 1]) { const lap = new THREE.Shape([new THREE.Vector2(0, 0), new THREE.Vector2(s * .075, .02), new THREE.Vector2(s * .06, -.09), new THREE.Vector2(s * .01, -.24)]);
      const lm = add(root, new THREE.ExtrudeGeometry(lap, { depth: .012, bevelEnabled: true, bevelSize: .004, bevelThickness: .003, bevelSegments: 2 }), top, s * .055, 1.47, .11); lm.rotation.x = -.1; }
    for (const y of [1.17, 1.08]) add(root, new THREE.CylinderGeometry(.009, .009, .006, 12), std(0x050505, { roughness: .2 }), 0, y, .124).rotation.x = Math.PI / 2;
    add(root, new THREE.BoxGeometry(.07, .006, .01), top, -.1, 1.3, .118);
    if (L.pocket) { const ps = add(root, new THREE.ConeGeometry(.018, .03, 3), std(L.pocket, { metalness: L.pocket === 0xc9962e ? 1 : 0, roughness: .4 }), -.1, 1.315, .12); ps.rotation.z = Math.PI; }
    add(root, new THREE.CylinderGeometry(.152, .152, .03, 36), std(0x0a0a0a, { roughness: .3 }), 0, .965, 0).scale.z = .66; // belt
    add(root, new THREE.BoxGeometry(.04, .03, .01), std(0xc9a040, { metalness: 1, roughness: .2 }), 0, .965, .101);
  } else {
    // plate carrier with MOLLE webbing, pouches with flaps, shoulder straps
    const vm = std(L.vest, { roughness: .95 }), web = std(L.vest - 0x0a0a0a, { roughness: 1 });
    const front = add(root, new THREE.BoxGeometry(.3, .34, .05), vm, 0, 1.2, .1); front.geometry.translate(0, 0, 0);
    const back = add(root, new THREE.BoxGeometry(.3, .36, .05), vm, 0, 1.2, -.1);
    for (let i = 0; i < 4; i++) add(root, new THREE.BoxGeometry(.3, .008, .056), web, 0, 1.08 + i * .04, .1);
    for (let i = -1; i <= 1; i++) { add(root, new THREE.BoxGeometry(.08, .1, .05), vm, i * .093, 1.1, .14); add(root, new THREE.BoxGeometry(.084, .03, .054), web, i * .093, 1.145, .142); }
    for (const s of [-1, 1]) { const st = add(root, new THREE.BoxGeometry(.06, .04, .25), vm, s * .11, 1.41, 0); }
    add(root, new THREE.CylinderGeometry(.158, .158, .05, 32), std(0x15140f, { roughness: .9 }), 0, .965, 0).scale.z = .7;
    if (L.radio) { add(root, new THREE.BoxGeometry(.05, .09, .04), std(0x0a0a0a), .12, 1.3, .14); add(root, new THREE.CylinderGeometry(.004, .004, .3), std(0x050505), .14, 1.48, .13); }
    if (L.patch) { const p = add(root, new THREE.PlaneGeometry(.06, .04), new THREE.MeshStandardMaterial({ map: tex(60, 40, g => { ['#006847', '#eee', '#ce1126'].forEach((c, i) => { g.fillStyle = c; g.fillRect(i * 20, 0, 20, 40); }); g.fillStyle = '#7b4b1f'; g.beginPath(); g.arc(30, 20, 6, 0, 7); g.fill(); }) }), -.1, 1.3, .127); }
  }
  if (L.sash) {
    const st = tex(16, 120, (g, w, h) => { [['#c9a040', 0, 4], ['#0b6b3a', 4, 38], ['#f2f2f2', 42, 36], ['#b3121b', 78, 38], ['#c9a040', 116, 4]].forEach(([c, y, hh]) => { g.fillStyle = c; g.fillRect(0, y, w, hh); }); });
    st.repeat.set(1, 1);
    const geo = new THREE.CylinderGeometry(.2, .2, .1, 96, 1, true).rotateZ(-.95).translate(0, 1.17, 0), pp = geo.attributes.position;
    for (let i = 0; i < pp.count; i++) { const x = pp.getX(i), y = pp.getY(i), z = pp.getZ(i), a = Math.atan2(z, x), r = rAt(y) + .016; pp.setX(i, Math.cos(a) * r); pp.setZ(i, Math.sin(a) * r); }
    geo.computeVertexNormals();
    const band = new THREE.Mesh(geo, std(0xffffff, { map: st, roughness: .5, side: THREE.DoubleSide })); band.castShadow = true; torso.add(band);
    const med = add(root, new THREE.CylinderGeometry(.03, .03, .012, 24), std(0xd4a537, { metalness: 1, roughness: .2 }), .105, 1.02, .118); med.rotation.x = Math.PI / 2;
    add(root, new THREE.TorusGeometry(.03, .005, 6, 24), std(0xb08020, { metalness: 1, roughness: .3 }), .105, 1.02, .125); }
  // arms
  const handMat = L.gloves ? std(0x111111, { roughness: .7 }) : skin;
  for (const s of [-1, 1]) {
    const a = new THREE.Group(); a.position.set(s * .2, 1.39, 0); root.add(a); a.rotation.z = s * .08;
    add(a, garment([[.001, .06], [.04, .055], [.062, .02], [.064, -.06], [.06, -.17], [.057, -.26], [.056, -.3], [.03, -.315], [.001, -.316]], [[-.24, .04, .006, 5], [-.04, .03, .003, 3]], s * 5), top);
    const b = new THREE.Group(); b.position.y = -.27; a.add(b);
    add(b, garment([[.001, .03], [.04, .025], [.053, .0], [.053, -.06], [.049, -.16], [.046, -.23], [.05, -.255], [.042, -.262], [.03, -.258]], [[-.03, .04, .006, 5], [-.2, .05, .003, 6]], s * 7), top);
    if (L.suit) add(b, new THREE.CylinderGeometry(.044, .044, .03, 16), std(L.shirt), 0, -.255, 0);   // shirt cuff
    if (L.pads) { add(b, new THREE.SphereGeometry(.062, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2), std(0x0a0a0a, { roughness: .6 }), 0, 0, -.01).rotation.x = -Math.PI / 2; }
    if (L.watch && s < 0) add(b, new THREE.CylinderGeometry(.047, .047, .02, 16), std(0xd4a537, { metalness: 1, roughness: .2 }), 0, -.24, 0);
    const h = hand(L, handMat, s); h.position.y = -.27; b.add(h);
    if (L.ring && s > 0) add(h, new THREE.TorusGeometry(.011, .004, 6, 12), std(0xd4a537, { metalness: 1, roughness: .15 }), 0, -.085, .008).rotation.y = Math.PI / 2;
    rig[s < 0 ? 'lArm' : 'rArm'] = { a, b, end: h };
  }
  // legs
  for (const s of [-1, 1]) {
    const a = new THREE.Group(); a.position.set(s * .085, .9, 0); root.add(a);
    add(a, garment([[.001, .07], [.07, .06], [.088, .0], [.082, -.12], [.074, -.28], [.07, -.4], [.068, -.47], [.001, -.472]], [[-.04, .05, .005, 4], [-.38, .04, .006, 6]], s * 3), legsM);
    const b = new THREE.Group(); b.position.y = -.42; a.add(b);
    const hem = L.suit ? [[.066, -.39], [.071, -.415], [.068, -.43], [.001, -.432]] : [[.062, -.36], [.001, -.365]];
    add(b, garment([[.001, .03], [.05, .025], [.064, .0], [.063, -.1], [.058, -.25], [.06, -.33]].concat(hem), [[.0, .04, .006, 5], [-.39, .03, .007, 7]], s * 9), legsM);
    if (L.pads) add(b, new THREE.SphereGeometry(.072, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), std(0x0a0a0a, { roughness: .6 }), 0, -.02, .01).rotation.x = Math.PI / 2;
    const shoe = add(b, cap(.05, .14, 12), shoeM, 0, -.43, .045); shoe.rotation.x = Math.PI / 2; shoe.scale.set(1.05, 1, .75);
    add(b, new THREE.BoxGeometry(.105, .015, .25), std(0x050505, { roughness: .9 }), 0, -.468, .045);
    if (!L.suit) add(b, new THREE.CylinderGeometry(.068, .062, .12, 16), shoeM, 0, -.37, 0);  // boot shaft
    rig[s < 0 ? 'lLeg' : 'rLeg'] = { a, b };
  }
  rig.relax = () => {
    rig.lArm.a.rotation.set(.04, 0, -.1); rig.rArm.a.rotation.set(-.03, 0, .12); rig.lArm.b.rotation.x = -.28; rig.rArm.b.rotation.x = -.2;
    rig.lArm.end.rotation.y = .3; rig.rArm.end.rotation.y = -.3;
    rig.lLeg.a.rotation.set(0, 0, -.025); rig.rLeg.a.rotation.set(-.1, 0, .06); rig.rLeg.b.rotation.x = .17; rig.rLeg.a.position.y = .89;
    head.rotation.set(.04, -.08, .05); torso.rotation.y = .04; root.rotation.y = .05;
  };
  rig.relax();
  const blinkPh = kind.length * .73;
  rig.tick = t => { const q = (t + blinkPh) % 3.4; const k = q < .13 ? Math.abs(Math.cos(q / .13 * Math.PI)) * .9 + .1 : 1;
    head.material.map = k < .5 ? rig.faceTex.shut : rig.faceTex.open; torso.scale.x = 1 + Math.sin(t * 2.2) * .008; };
  rig.setHand = (side, pose) => rig[side === 'r' ? 'rArm' : 'lArm'].end.userData.setPose(pose);
  root.traverse(o => { if (o.isMesh) o.castShadow = true; });
  return rig;
}
