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
  const ink = std(0x111111, { roughness: .15 }), browM = std(L.hairColor ?? 0x1a1a1a, { roughness: .8 });
  rig.eyes = [];
  for (const s of [-1, 1]) {
    const eye = new THREE.Group();
    const ball = add(eye, new THREE.SphereGeometry(R * .15, 24, 16), ink); ball.scale.set(1, 1.3, .45);
    add(eye, new THREE.SphereGeometry(R * .045, 10, 8), new THREE.MeshBasicMaterial({ color: 0xffffff }), R * .05, R * .07, R * .06);
    onHead(head, R, eye, s * .32, .1, -.004); rig.eyes.push(eye);
    if (!L.balaclava || true) {
      const moods = { smug: s < 0 ? [.42, -.2] : [.3, .05], angry: [.25, s * .42], stern: [.27, s * .18], raised: [.4, -s * .12] };
      const [bv, rz] = moods[L.brows];
      const brow = new THREE.Group(); const b = add(brow, cap(R * .05, R * .26, 8), browM); b.rotation.z = Math.PI / 2; b.scale.set(1, 1, .6);
      onHead(head, R, brow, s * .33, bv, .004, rz); (rig.brows ??= []).push(brow);
    }
  }
  // nose
  if (!L.balaclava) add(head, new THREE.SphereGeometry(R * .08, 16, 12), head.material, 0, -R * .08, R * .97).scale.set(1, 1.2, .8);
  // mouth
  const mouth = new THREE.Group(), lip = std(0x2a1414, { roughness: .4 });
  if (L.mouth === 'smirk') { const a = add(mouth, new THREE.TorusGeometry(R * .2, R * .03, 8, 24, 1.6), lip); a.rotation.z = -Math.PI / 2 - .5; onHead(head, R, mouth, .08, -.38, 0, .12); }
  if (L.mouth === 'frown') { const a = add(mouth, new THREE.TorusGeometry(R * .2, R * .03, 8, 24, 1.5), lip); a.rotation.z = Math.PI / 2 - .75; onHead(head, R, mouth, 0, -.5); }
  if (L.mouth === 'grin') {
    add(mouth, new THREE.CircleGeometry(R * .22, 24, Math.PI, Math.PI), std(0x3a0d0d, { side: THREE.DoubleSide }));
    add(mouth, new THREE.PlaneGeometry(R * .38, R * .07), std(0xffffff, { roughness: .3 }), 0, -R * .035, .001);
    onHead(head, R, mouth, .03, -.33, .002, .05);
  }
  if (L.mustache) for (const s of [-1, 1]) { const m = new THREE.Group(); const c = add(m, cap(R * .06, R * .2, 8), std(0x15110e, { roughness: .9 })); c.rotation.z = Math.PI / 2 + s * .35; c.scale.z = .6; onHead(head, R, m, s * .12, -.24, .01); }
  if (L.cigar) { const g = new THREE.Group(); const c = add(g, new THREE.CylinderGeometry(R * .05, R * .055, R * .9, 12), std(0x5a3418, { roughness: .9 })); c.rotation.x = Math.PI / 2; c.position.z = R * .4;
    add(g, new THREE.CylinderGeometry(R * .052, R * .052, R * .06, 12), new THREE.MeshBasicMaterial({ color: 0xff5a10 }), 0, 0, R * .86).rotation.x = Math.PI / 2;
    onHead(head, R, g, .2, -.36, -.01, 0); g.rotateY(.5); rig.cigar = g; }
  if (L.glasses) { const gold = std(0xd4a537, { metalness: 1, roughness: .25 }), gl = new THREE.Group();
    for (const s of [-1, 1]) { add(gl, new THREE.TorusGeometry(R * .2, R * .022, 8, 28), gold, s * R * .33, 0, 0);
      add(gl, new THREE.CircleGeometry(R * .19, 24), new THREE.MeshPhysicalMaterial({ color: 0x88aacc, transparent: true, opacity: .25, roughness: 0, metalness: .2 }), s * R * .33, 0, 0); }
    add(gl, new THREE.BoxGeometry(R * .2, R * .03, R * .03), gold);
    onHead(head, R, gl, 0, .08, R * .12); }
  if (L.hair) { const hm = std(L.hairColor, { roughness: .55 });
    const h = add(head, new THREE.SphereGeometry(R * 1.06, 40, 20, 0, Math.PI * 2, 0, Math.PI * .4), hm); h.rotation.x = -.5; h.scale.set(1, 1, 1.04);
    if (L.hair === 'side') { const q = add(head, new THREE.SphereGeometry(R * .5, 20, 12), hm, -R * .35, R * .78, R * .3); q.scale.set(1.3, .45, 1); q.rotation.z = .3; }
    if (L.hair === 'slick') for (let i = -2; i <= 2; i++) { const st = add(head, new THREE.TorusGeometry(R * 1.04, R * .012, 4, 30, 1.6), std(0x2a221c)); st.rotation.set(0, Math.PI / 2, 0); st.position.x = i * R * .15; st.rotation.z = 1.0; } }
  if (L.helmet) { const hm = new THREE.MeshStandardMaterial({ map: camoTex(['#4b5532', '#2f3520', '#6b6a45']), roughness: .9 });
    const h = add(head, new THREE.SphereGeometry(R * 1.14, 36, 18, 0, Math.PI * 2, 0, Math.PI * .5), hm, 0, R * .08, 0);
    add(head, new THREE.TorusGeometry(R * 1.12, R * .07, 8, 40), std(0x2f3520, { roughness: .9 }), 0, R * .08, 0).rotation.x = Math.PI / 2;
    if (L.strap) for (const s of [-1, 1]) { const st = add(head, cap(R * .03, R * .9, 6), std(0x1d1d14)); st.position.set(s * R * .9, -R * .35, R * .2); st.rotation.z = s * .25; } }
  if (L.balaclava) { const bm = std(0x0f0f0f, { roughness: 1, map: fabric('#111111', 'rgba(255,255,255,.04)', 4) });
    add(head, new THREE.SphereGeometry(R * 1.04, 36, 18, 0, Math.PI * 2, 0, Math.PI * .4), bm).rotation.x = -.05;          // top
    const low = add(head, new THREE.SphereGeometry(R * 1.04, 36, 18, 0, Math.PI * 2, Math.PI * .55, Math.PI * .45), bm); low.rotation.x = .12; // lower face
    for (const s of [-1, 1]) add(head, new THREE.SphereGeometry(R * 1.035, 20, 6, Math.PI / 2 + s * 1.15 - .35, .7, Math.PI * .38, Math.PI * .2), bm); // side band
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
    const vee = new THREE.Shape([new THREE.Vector2(-.065, 0), new THREE.Vector2(.065, 0), new THREE.Vector2(0, -.26)]);
    add(root, new THREE.ShapeGeometry(vee), shirt, 0, 1.47, .124).rotation.x = -.12;
    add(root, new THREE.BoxGeometry(.035, .03, .02), std(L.tie, { roughness: .35 }), 0, 1.445, .13);
    const tie = add(root, new THREE.CylinderGeometry(.02, .006, .3, 4), std(L.tie, { roughness: .35 }), 0, L.loose ? 1.29 : 1.28, .128); tie.scale.z = .25; if (L.loose) tie.rotation.z = .06;
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
  if (L.sash) { const cols = [0x0b6b3a, 0xf2f2f2, 0xb3121b];
    cols.forEach((c, i) => { const b = add(root, new THREE.BoxGeometry(.05, .66, .02), std(c, { roughness: .45 }), -.015 + (i - 1) * .046, 1.2, .132); b.rotation.z = .62; });
    const med = add(root, new THREE.CylinderGeometry(.035, .035, .01, 24), std(0xd4a537, { metalness: 1, roughness: .2 }), .12, .98, .13); med.rotation.x = Math.PI / 2; }
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
    rig.eyes.forEach(e => e.scale.y = k); torso.scale.x = 1 + Math.sin(t * 2.2) * .008; };
  rig.setHand = (side, pose) => rig[side === 'r' ? 'rArm' : 'lArm'].end.userData.setPose(pose);
  root.traverse(o => { if (o.isMesh) o.castShadow = true; });
  return rig;
}
