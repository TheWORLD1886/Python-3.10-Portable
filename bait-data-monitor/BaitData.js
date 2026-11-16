// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: deep-green; icon-glyph: signal;

/* ============================================================================
 *  BAIT DATA — Monitor de datos móviles BAIT (México) para Scriptable / iOS
 * ----------------------------------------------------------------------------
 *  Cómo obtiene los datos (resumen; ver README.md para el detalle):
 *   1. El inicio de sesión se hace en la página OFICIAL https://mibait.com/login
 *      dentro de un WebView. Tú escribes tus datos en la página de BAIT/Walmart;
 *      este script NUNCA ve ni guarda tu contraseña ni tu código OTP.
 *   2. Al terminar el login, el script lee del almacenamiento del sitio la
 *      sesión que el propio portal guarda (número, token de acceso) y la
 *      guarda cifrada en el Llavero (Keychain) de iOS.
 *   3. Con esa sesión consulta los mismos endpoints que usa el portal web:
 *        GET  /api/core/q/dn/{numero}/get/consumption   (portal actual)
 *        POST /conn/page/api/app/consumoV3               (cuentas "legacy")
 *        POST /conn/page/api/sso/consumoSSO              (cuentas Walmart SSO)
 *   4. Si las llamadas directas fallan y el script corre dentro de la app,
 *      abre el portal en segundo plano y lee el consumo que el portal mismo
 *      descarga (respaldo con WebView).
 *  Las claves de cliente públicas del portal (cabeceras x-ord-service, etc.)
 *  NO están escritas aquí: se leen en tiempo de ejecución del JavaScript
 *  público de mibait.com, así el script sigue funcionando si BAIT las cambia.
 * ==========================================================================*/

// ───────────────────────────── CONFIGURACIÓN ──────────────────────────────
const CFG = {
  BASE: "https://mibait.com",
  CACHE_MINUTES: 20,          // no consultar a BAIT más seguido que esto (el portal permite cada 10)
  WIDGET_REFRESH_MINUTES: 30, // cada cuánto pedimos a iOS refrescar el widget
  KEYS_TTL_HOURS: 24,         // cada cuánto se vuelven a leer las claves públicas del portal
  HISTORY_DAYS: 35,
  TIMEOUT: 20,
  KC_SESSION: "baitdata.session.v1",
  KC_KEYS: "baitdata.clientkeys.v1",
  KC_SETTINGS: "baitdata.settings.v1",
  DIR: "BaitData",
};

const C = {
  bgTop: new Color("#1C1C1E"),
  bgBottom: new Color("#000000"),
  track: new Color("#2C2C2E"),
  text: Color.white(),
  sub: new Color("#8E8E93"),
  green: new Color("#30D158"),
  yellow: new Color("#FFD60A"),
  red: new Color("#FF453A"),
  blue: new Color("#0A84FF"),
};

// ───────────────────────────── UTILIDADES ─────────────────────────────────
const sleep = (ms) => new Promise((r) => Timer.schedule(ms, false, r));
/** Carga una URL/HTML en un WebView ignorando el error -999 (navegación cancelada),
 *  que iOS lanza cuando el portal redirige o una carga reemplaza a otra. */
async function safeLoad(promiseFn) {
  try {
    await promiseFn();
  } catch (e) {
    if (!/-999|cancel/i.test(String(e && (e.message || e)))) throw e;
  }
}
const num = (v) => {
  const n = typeof v === "string" ? parseFloat(v.replace(",", ".")) : Number(v);
  return Number.isFinite(n) ? n : null;
};
const sum = (arr, f) => arr.reduce((a, x) => a + (num(f(x)) || 0), 0);
const pad = (n) => String(n).padStart(2, "0");
const dayKey = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

function fmtData(mb, digits = 2) {
  if (mb == null) return "—";
  if (Math.abs(mb) >= 1024) return `${(mb / 1024).toFixed(digits)} GB`;
  return `${Math.round(mb)} MB`;
}
function fmtGBnum(mb) {
  if (mb == null) return "—";
  return Math.abs(mb) >= 1024 ? (mb / 1024).toFixed(2) : Math.round(mb).toString();
}
function unitOf(mb) {
  return mb != null && Math.abs(mb) >= 1024 ? "GB" : "MB";
}
function fmtDate(d, withYear = false) {
  if (!d) return "—";
  const df = new DateFormatter();
  df.locale = "es_MX";
  df.dateFormat = withYear ? "d MMM yyyy" : "d MMM";
  return df.string(d).replace(".", "");
}
function fmtTime(d) {
  const df = new DateFormatter();
  df.locale = "es_MX";
  df.dateFormat = "HH:mm";
  return df.string(d);
}
function fmtAgo(ts) {
  const m = Math.round((Date.now() - ts) / 60000);
  if (m < 1) return "ahora";
  if (m < 60) return `hace ${m} min`;
  const h = Math.round(m / 60);
  if (h < 24) return `hace ${h} h`;
  return `hace ${Math.round(h / 24)} d`;
}

/** Interpreta las distintas formas de fecha que devuelve BAIT. */
function parseDate(v) {
  if (v == null || v === "") return null;
  if (typeof v === "number") return new Date(v > 1e12 ? v : v * 1000);
  const s = String(v).trim();
  let m;
  if ((m = s.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/))) // dd/MM/yyyy
    return new Date(+m[3], +m[2] - 1, +m[1], 23, 59, 59);
  if ((m = s.match(/^(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})(?:[T ](\d{1,2}):(\d{2})(?::(\d{2}))?)?/))) {
    if (m[4] != null) return new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +(m[6] || 0));
    return new Date(+m[1], +m[2] - 1, +m[3], 23, 59, 59);
  }
  if ((m = s.match(/^(\d{4})(\d{2})(\d{2})(\d{2})?(\d{2})?(\d{2})?$/)))  // yyyyMMdd[HHmmss]
    return new Date(+m[1], +m[2] - 1, +m[3], +(m[4] || 23), +(m[5] || 59), +(m[6] || 59));
  const d = new Date(s);
  return isNaN(d) ? null : d;
}

class BaitError extends Error {
  constructor(kind, message, detail) {
    super(message);
    this.kind = kind; // "auth" | "network" | "format" | "config"
    this.detail = detail;
  }
}

// ──────────────────────── ALMACENAMIENTO (Keychain + archivos) ─────────────
const Store = {
  fm: FileManager.local(),
  dir() {
    const d = this.fm.joinPath(this.fm.documentsDirectory(), CFG.DIR);
    if (!this.fm.fileExists(d)) this.fm.createDirectory(d, true);
    return d;
  },
  readJSON(name, fallback) {
    try {
      const p = this.fm.joinPath(this.dir(), name);
      if (!this.fm.fileExists(p)) return fallback;
      return JSON.parse(this.fm.readString(p));
    } catch (e) {
      return fallback;
    }
  },
  writeJSON(name, obj) {
    this.fm.writeString(this.fm.joinPath(this.dir(), name), JSON.stringify(obj));
  },
  remove(name) {
    const p = this.fm.joinPath(this.dir(), name);
    if (this.fm.fileExists(p)) this.fm.remove(p);
  },
  kcGet(key) {
    try {
      return Keychain.contains(key) ? JSON.parse(Keychain.get(key)) : null;
    } catch (e) {
      return null;
    }
  },
  kcSet(key, obj) {
    Keychain.set(key, JSON.stringify(obj));
  },
  kcRemove(key) {
    if (Keychain.contains(key)) Keychain.remove(key);
  },
};

const Settings = {
  get() {
    return Object.assign({ manualTotalMB: null }, Store.kcGet(CFG.KC_SETTINGS) || {});
  },
  set(s) {
    Store.kcSet(CFG.KC_SETTINGS, s);
  },
};

// ─────────────── CLAVES PÚBLICAS DEL PORTAL (descubiertas en vivo) ────────
const ClientKeys = {
  async get(force = false) {
    const cached = Store.kcGet(CFG.KC_KEYS);
    const fresh = cached && Date.now() - cached.ts < CFG.KEYS_TTL_HOURS * 3600e3;
    if (cached && fresh && !force) return cached;
    try {
      const keys = await this.discover();
      Store.kcSet(CFG.KC_KEYS, keys);
      return keys;
    } catch (e) {
      if (cached) return cached; // usamos las últimas conocidas
      throw new BaitError("network", "No se pudo leer la configuración pública de mibait.com", String(e));
    }
  },
  async discover() {
    const html = await new Request(CFG.BASE + "/").loadString();
    const m = html.match(/src="(main\.[0-9a-f]+\.js)"/);
    if (!m) throw new Error("No se encontró main.js en mibait.com");
    const js = await new Request(`${CFG.BASE}/${m[1]}`).loadString();
    const pick = (name) => {
      const r = js.match(new RegExp(name + ':"([^"]+)"'));
      return r ? r[1] : null;
    };
    const ver = js.match(/exports=\{rE:"([^"]+)"\}/);
    const keys = {
      ts: Date.now(),
      bundle: m[1],
      xOrdService: pick("xOrdService"),
      ordenarisKey: pick("ordenarisKey"),
      xOrdServiceSSO: pick("xOrdServiceSSO"),
      xOrdApiSSO: pick("xOrdApiSSO"),
      xOrdHostSSO: pick("xOrdHostSSO") || CFG.BASE,
      appVersion: ver ? ver[1] : null,
    };
    if (!keys.xOrdService && !keys.ordenarisKey)
      throw new Error("El portal cambió: no se encontraron las cabeceras de servicio");
    return keys;
  },
};

// ─────────────────────────── MÓDULO DE AUTENTICACIÓN ──────────────────────
// Se ejecuta dentro del sitio mibait.com (WebView). Lee lo que el propio portal
// guarda en localStorage tras un login exitoso. No lee contraseñas.
const READ_SITE_STORAGE_JS = `
(function(){
  try {
    if (location.hostname.indexOf('mibait.com') < 0) return JSON.stringify({host: location.hostname});
    var g = function(k){ return localStorage.getItem(k); };
    var dec = function(v){ try { return v ? JSON.parse(atob(v)) : null; } catch(e) { return null; } };
    return JSON.stringify({
      host: location.hostname,
      path: location.pathname,
      member: dec(g('memberbt')),
      accessToken: g('access_token'),
      isSSO: g('isSSO') === 'true',
      legacy: g('SSO-legacy') === 'true',
      consumo: dec(g('mibait-consumo')),
      cookie: document.cookie || ''
    });
  } catch (e) { return JSON.stringify({error: String(e)}); }
})()`;

function sessionFromStorage(raw) {
  let s;
  try {
    s = JSON.parse(raw);
  } catch (e) {
    return null;
  }
  const m = s && s.member;
  if (!m || !m.access || !(m.number || m.serviceNumber)) return null;
  return {
    number: String(m.number || "").replace(/\D/g, ""),
    serviceNumber: m.serviceNumber ? String(m.serviceNumber).replace(/\D/g, "") : null,
    access: m.access,
    accessToken: s.accessToken || (m.isLegacy ? null : m.access),
    isLegacy: m.isLegacy !== false && !s.isSSO,
    isSSO: !!s.isSSO || m.isLegacy === false,
    cookie: s.cookie || "",
    savedAt: Date.now(),
    _siteConsumo: s.consumo || null,
  };
}

const Auth = {
  get() {
    return Store.kcGet(CFG.KC_SESSION);
  },
  save(session) {
    const { _siteConsumo, ...clean } = session;
    Store.kcSet(CFG.KC_SESSION, clean);
  },
  clear() {
    Store.kcRemove(CFG.KC_SESSION);
  },
  dn(session) {
    // Igual que el portal: si la cuenta tiene número de servicio, se consulta ese.
    return session.serviceNumber && session.serviceNumber.trim() ? session.serviceNumber : session.number;
  },

  /** Login interactivo: abre la página oficial de BAIT y espera a que el usuario inicie sesión. */
  async interactiveLogin() {
    const intro = new Alert();
    intro.title = "Iniciar sesión en BAIT";
    intro.message =
      "Se abrirá la página oficial mibait.com.\n\n" +
      "1. Escribe tu número BAIT.\n" +
      "2. Completa el método que BAIT te pida (cuenta Walmart, contraseña o código SMS).\n" +
      "3. Cuando veas tu consumo en pantalla, el script lo detectará solo.\n\n" +
      "Tus credenciales se escriben en la página de BAIT; este script no las ve ni las guarda.";
    intro.addAction("Continuar");
    intro.addCancelAction("Cancelar");
    if ((await intro.presentAlert()) === -1) return null;

    const wv = new WebView();
    await safeLoad(() => wv.loadURL(CFG.BASE + "/login"));
    let closed = false;
    const shown = wv.present(true).then(() => (closed = true));

    let session = null;
    const deadline = Date.now() + 15 * 60e3;
    while (!closed && !session && Date.now() < deadline) {
      await sleep(1500);
      try {
        session = sessionFromStorage(await wv.evaluateJavaScript(READ_SITE_STORAGE_JS));
      } catch (e) {
        /* la página aún está navegando */
      }
    }
    if (session) {
      this.save(session);
      if (session._siteConsumo) {
        // El portal ya descargó el consumo: lo aprovechamos como primera lectura real.
        try {
          const data = Parse.siteMapped(session._siteConsumo);
          Cache.storeSuccess(data, session);
        } catch (e) {}
      }
      if (!closed) {
        await safeLoad(() => wv.loadHTML(
          `<html><meta name="viewport" content="width=device-width,initial-scale=1">
           <body style="background:#000;color:#fff;font-family:-apple-system;display:flex;
           align-items:center;justify-content:center;height:90vh;text-align:center">
           <div><div style="font-size:64px">✅</div><h2>Línea ${session.number} vinculada</h2>
           <p style="color:#8E8E93">Ya puedes cerrar esta ventana (botón “Cerrar”/“Done”).</p></div></body></html>`
        ));
        await shown;
      }
    }
    return session;
  },

  /** Renueva el token de una cuenta Walmart SSO (mismo endpoint que usa el portal). */
  async refreshSSO(session, keys) {
    if (!session.isSSO || !keys.xOrdServiceSSO) return null;
    const req = new Request(`${CFG.BASE}/api/v1/sso/token/refresh?decrypt=true`);
    req.method = "POST";
    req.timeoutInterval = CFG.TIMEOUT;
    req.headers = {
      ...Api.baseHeaders(keys, session),
      "x-ord-service": keys.xOrdServiceSSO,
      "x-ord-host": keys.xOrdHostSSO,
      "x-ord-api": keys.xOrdApiSSO,
      Authorization: `Bearer ${session.accessToken || session.access}`,
    };
    req.body = "{}";
    try {
      const body = JSON.parse(await req.loadString());
      const d = body && (body.data || body);
      const tok = d && d.token && d.token.access_token;
      if (!tok) return null;
      const updated = { ...session, access: tok, accessToken: tok, savedAt: Date.now() };
      this.save(updated);
      return updated;
    } catch (e) {
      return null;
    }
  },
};

// ──────────────────────────── MÓDULO DE CONSULTA ──────────────────────────
const Api = {
  baseHeaders(keys, session) {
    const h = {
      Accept: "application/json, text/plain, */*",
      "Content-Type": "application/json",
      origen: CFG.BASE,
      Origin: CFG.BASE,
      Referer: CFG.BASE + "/home",
    };
    if (keys.appVersion) h["app-version"] = keys.appVersion;
    if (session && session.cookie) h.Cookie = session.cookie;
    return h;
  },

  async call(url, method, headers, body) {
    const req = new Request(url);
    req.method = method;
    req.headers = headers;
    req.timeoutInterval = CFG.TIMEOUT;
    if (body !== undefined) req.body = JSON.stringify(body);
    let text;
    try {
      text = await req.loadString();
    } catch (e) {
      throw new BaitError("network", "Sin conexión con mibait.com", String(e));
    }
    const status = req.response ? req.response.statusCode : 0;
    let json = null;
    try {
      json = JSON.parse(text);
    } catch (e) {}
    return { status, json, text: (text || "").slice(0, 300) };
  },

  /** Estrategias, en el mismo orden de prioridad que el portal actual. */
  strategies(session, keys) {
    const list = [];
    const bearer = session.accessToken ? { Authorization: `Bearer ${session.accessToken}` } : {};
    if (keys.xOrdService)
      list.push({
        name: "consumption",
        run: () =>
          this.call(
            `${CFG.BASE}/api/core/q/dn/${encodeURIComponent(Auth.dn(session))}/get/consumption`,
            "GET",
            { ...this.baseHeaders(keys, session), "x-ord-service": keys.xOrdService, ...bearer }
          ),
        parse: (j) => Parse.consumptionV4(j),
      });
    if (session.isLegacy && keys.ordenarisKey)
      list.push({
        name: "consumoV3",
        run: () =>
          this.call(
            `${CFG.BASE}/conn/page/api/app/consumoV3`,
            "POST",
            { ...this.baseHeaders(keys, session), ordServicio: keys.ordenarisKey },
            { access: session.access }
          ),
        parse: (j) => Parse.consumoV3(j),
      });
    if (session.isSSO && session.accessToken)
      list.push({
        name: "consumoSSO",
        run: () =>
          this.call(
            `${CFG.BASE}/conn/page/api/sso/consumoSSO`,
            "POST",
            { ...this.baseHeaders(keys, session), ...bearer },
            { numero: session.number }
          ),
        parse: (j) => Parse.consumoV3(j),
      });
    return list;
  },

  async fetchUsage(session, { allowRefresh = true } = {}) {
    const keys = await ClientKeys.get();
    const errors = [];
    let authFailures = 0;
    for (const s of this.strategies(session, keys)) {
      try {
        const r = await s.run();
        if (r.status === 401 || r.status === 403) {
          authFailures++;
          errors.push(`${s.name}: HTTP ${r.status}`);
          continue;
        }
        if (r.status >= 200 && r.status < 300 && r.json) {
          if (r.json.success === false) {
            errors.push(`${s.name}: ${r.json.message || r.json.mensaje || "success=false"}`);
            if (/sesi[oó]n|token|acceso|autoriza/i.test(JSON.stringify(r.json))) authFailures++;
            continue;
          }
          const data = s.parse(r.json);
          data.source = s.name;
          return data;
        }
        errors.push(`${s.name}: HTTP ${r.status}${r.json ? "" : " (respuesta no JSON)"}`);
      } catch (e) {
        if (e.kind === "network") throw e;
        errors.push(`${s.name}: ${e.message}`);
      }
    }
    if (authFailures && allowRefresh && session.isSSO) {
      const refreshed = await Auth.refreshSSO(session, keys);
      if (refreshed) return this.fetchUsage(refreshed, { allowRefresh: false });
    }
    if (authFailures) throw new BaitError("auth", "Tu sesión de BAIT expiró", errors.join("\n"));
    // Las claves pudieron cambiar: forzar redescubrimiento la próxima vez.
    Store.kcSet(CFG.KC_KEYS, { ...keys, ts: 0 });
    throw new BaitError("format", "BAIT respondió de forma inesperada", errors.join("\n"));
  },

  /** Respaldo (solo dentro de la app): abre el portal oculto y lee el consumo que él descarga. */
  async fetchViaPortal() {
    const wv = new WebView();
    await safeLoad(() => wv.loadURL(CFG.BASE + "/"));
    await sleep(1000);
    await wv.evaluateJavaScript("localStorage.removeItem('mibait-consumo'); true");
    await safeLoad(() => wv.loadURL(CFG.BASE + "/home"));
    const deadline = Date.now() + 30e3;
    while (Date.now() < deadline) {
      await sleep(1500);
      let raw;
      try {
        raw = await wv.evaluateJavaScript(READ_SITE_STORAGE_JS);
      } catch (e) {
        continue;
      }
      const st = JSON.parse(raw || "{}");
      if (st.path && /login/.test(st.path) && !st.member)
        throw new BaitError("auth", "La sesión del portal BAIT expiró");
      if (st.consumo && st.consumo.success !== false) {
        const sess = sessionFromStorage(raw);
        if (sess) Auth.save(sess);
        const data = Parse.siteMapped(st.consumo);
        data.source = "portal (WebView)";
        return data;
      }
    }
    throw new BaitError("network", "El portal BAIT no respondió a tiempo");
  },
};

// ─────────────────────── MÓDULO DE PROCESAMIENTO DE DATOS ─────────────────
// Todas las cantidades de datos que maneja BAIT están en MB.
const Parse = {
  finalize(d) {
    const s = Settings.get();
    if ((!d.totalMB || d.totalMB <= 0) && s.manualTotalMB && d.usedMB != null) {
      d.totalMB = s.manualTotalMB;
      d.totalIsManual = true;
    }
    if (d.availMB == null && d.totalMB != null && d.usedMB != null) d.availMB = Math.max(0, d.totalMB - d.usedMB);
    if (d.usedMB == null && d.totalMB != null && d.availMB != null) d.usedMB = Math.max(0, d.totalMB - d.availMB);
    d.pct = d.totalMB > 0 ? Math.min(1, Math.max(0, d.usedMB / d.totalMB)) : null;
    if (d.expire) {
      d.daysLeft = Math.max(0, Math.ceil((d.expire.getTime() - Date.now()) / 86400e3));
      d.expire = d.expire.toISOString();
    } else d.daysLeft = null;
    d.status = d.unlimited
      ? "Ilimitado"
      : !d.totalMB
      ? "Sin paquete de datos activo"
      : d.daysLeft === 0
      ? "Vence hoy"
      : d.availMB <= 0
      ? "Datos agotados"
      : "Activo";
    d.fetchedAt = Date.now();
    return d;
  },

  /** GET /api/core/q/dn/{dn}/get/consumption → { success, data: [ {category, type, resume:{total,unused,expire_date}, unlimited, ...} ] } */
  consumptionV4(j) {
    const items = j && Array.isArray(j.data) ? j.data : null;
    if (!items) throw new Error("Formato 'consumption' sin arreglo data");
    const dataItems = items.filter((x) => x.type === "BestEffort" || x.type === "Throttling");
    const totalMB = sum(dataItems, (x) => x.resume && x.resume.total);
    const usedMB = sum(dataItems, (x) => x.resume && x.resume.total - x.resume.unused);
    const expDates = items
      .filter((x) => ["Data", "Minutes", "Message"].includes(x.category) && x.resume)
      .map((x) => parseDate(x.resume.expire_date))
      .filter(Boolean);
    const now = new Date();
    const social = items
      .filter((x) => x.type === "SocialMedia" && x.resume && (parseDate(x.resume.expire_date) || now) >= now)
      .reduce(
        (a, x) => ({
          totalMB: a.totalMB + (num(x.resume.total) || 0),
          usedMB: a.usedMB + (num(x.resume.total) - num(x.resume.unused) || 0),
          unlimited: a.unlimited || !!x.unlimited,
        }),
        { totalMB: 0, usedMB: 0, unlimited: false }
      );
    return this.finalize({
      totalMB,
      usedMB,
      availMB: totalMB - usedMB,
      unlimited: items.some(
        (x) => x.category === "Data" && x.type !== "Unkown" && x.type !== "SocialMedia" && x.unlimited
      ),
      expire: expDates.length ? new Date(Math.max(...expDates)) : null,
      social: social.totalMB || social.unlimited ? social : null,
      minutes: sum(items.filter((x) => x.category === "Minutes"), (x) => x.resume && x.resume.unused),
      sms: sum(items.filter((x) => x.category === "Message"), (x) => x.resume && x.resume.unused),
    });
  },

  /** consumoV3 / consumoSSO → { success, consumo:[{nombre, mb_usados, mb_totales, mb_disponibles,...}], proxima_recarga, offeringsIds:[{expireDate}], esIlimitado } */
  consumoV3(j) {
    if (!j || !Array.isArray(j.consumo)) throw new Error("Formato 'consumo' inesperado");
    const by = (n) => j.consumo.find((c) => c.nombre === n);
    const normal = by("datosVelocidadNormal");
    if (!normal) throw new Error("La respuesta no incluye datosVelocidadNormal");
    const socialItem = by("datosRedesSociales");
    const minutes = by("minutos");
    const sms = by("sms");
    const offerDates = (j.offeringsIds || []).map((o) => parseDate(o.expireDate)).filter(Boolean);
    const expire = offerDates.length ? new Date(Math.max(...offerDates)) : parseDate(j.proxima_recarga);
    return this.finalize({
      totalMB: num(normal.mb_totales),
      usedMB: num(normal.mb_usados),
      availMB: num(normal.mb_disponibles),
      unlimited: !!j.esIlimitado,
      expire,
      social: socialItem
        ? { totalMB: num(socialItem.mb_totales) || 0, usedMB: num(socialItem.mb_usados) || 0, unlimited: false }
        : null,
      minutes: minutes ? num(minutes.min_disponibles) : null,
      sms: sms ? num(sms.sms_disponibles) : null,
    });
  },

  /** Objeto que el portal guarda en localStorage 'mibait-consumo' (ya procesado por el portal). */
  siteMapped(o) {
    if (!o || o.total == null) throw new Error("Consumo del portal vacío");
    const totalMB = num(o.total);
    const usedMB = num(o.used);
    return this.finalize({
      totalMB,
      usedMB,
      availMB: totalMB != null && usedMB != null ? totalMB - usedMB : null,
      unlimited: !!o.isUnlimited,
      expire: o.nextRecharge && o.nextRecharge !== "Hoy mismo" ? parseDate(o.nextRecharge) : null,
      // El portal guarda socialMedia.total como texto ("1,5 GB" / "500 MB") y used en GB.
      social: o.socialMedia
        ? {
            totalMB:
              (num(String(o.socialMedia.total).replace(/[^\d.,]/g, "")) || 0) *
              (/GB/i.test(String(o.socialMedia.total)) ? 1024 : 1),
            usedMB: (num(o.socialMedia.used) || 0) * 1024,
            unlimited: !!o.socialMedia.unlimited,
          }
        : null,
      minutes: num(o.minutes),
      sms: num(o.messages),
    });
  },
};

// ───────────────────────────── CACHÉ + HISTORIAL ──────────────────────────
const Cache = {
  get() {
    return Store.readJSON("cache.json", null);
  },
  storeSuccess(data, session) {
    const prev = this.get() || {};
    const entry = { ...prev, data, lastOk: Date.now(), lastAttempt: Date.now(), error: null, number: session && session.number };
    Store.writeJSON("cache.json", entry);
    History.add(data);
    return entry;
  },
  storeError(err) {
    const prev = this.get() || {};
    const entry = { ...prev, lastAttempt: Date.now(), error: { kind: err.kind || "unknown", message: err.message } };
    Store.writeJSON("cache.json", entry);
    return entry;
  },
  isFresh(entry) {
    return entry && entry.lastOk && Date.now() - entry.lastOk < CFG.CACHE_MINUTES * 60e3;
  },
  recentlyFailed(entry) {
    return entry && entry.error && entry.lastAttempt && Date.now() - entry.lastAttempt < 5 * 60e3;
  },
};

const History = {
  get() {
    return Store.readJSON("history.json", { days: {} });
  },
  add(d) {
    if (d.usedMB == null) return;
    const h = this.get();
    h.days[dayKey(new Date())] = { usedMB: d.usedMB, totalMB: d.totalMB, ts: Date.now() };
    const keys = Object.keys(h.days).sort();
    while (keys.length > CFG.HISTORY_DAYS) delete h.days[keys.shift()];
    Store.writeJSON("history.json", h);
  },
  /** Consumo por día (MB). Si el acumulado baja, hubo renovación y se toma el valor del día. */
  daily(n = 10) {
    const h = this.get();
    const out = [];
    const today = new Date();
    for (let i = n - 1; i >= 0; i--) {
      const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() - i);
      const prev = new Date(d.getFullYear(), d.getMonth(), d.getDate() - 1);
      const cur = h.days[dayKey(d)];
      const p = h.days[dayKey(prev)];
      let v = null;
      if (cur && p) v = cur.usedMB >= p.usedMB ? cur.usedMB - p.usedMB : cur.usedMB;
      out.push({ date: d, mb: v });
    }
    return out;
  },
};

// ───────────────────────────── SISTEMA DE ACTUALIZACIÓN ───────────────────
async function getUsage({ force = false } = {}) {
  const session = Auth.get();
  if (!session) return { state: "nosession", cache: Cache.get() };

  let cache = Cache.get();
  if (!force && Cache.isFresh(cache)) return { state: "ok", cache, session };
  if (!force && Cache.recentlyFailed(cache)) return { state: cache.error.kind, cache, session };

  try {
    const data = await Api.fetchUsage(session);
    return { state: "ok", cache: Cache.storeSuccess(data, session), session };
  } catch (e) {
    if (config.runsInApp && e.kind !== "network") {
      try {
        const data = await Api.fetchViaPortal();
        return { state: "ok", cache: Cache.storeSuccess(data, Auth.get()), session };
      } catch (e2) {
        e = e2.kind === "auth" ? e2 : e;
      }
    }
    cache = Cache.storeError(e);
    return { state: e.kind || "error", cache, session, error: e };
  }
}

// ───────────────────────────── DIBUJO (DrawContext) ───────────────────────
function levelColor(d) {
  if (!d || d.unlimited) return C.green;
  if (d.pct == null) return C.sub;
  const lowData = d.availMB != null && d.availMB < 512;
  if (d.pct >= 0.85 || lowData) return C.red;
  if (d.pct >= 0.6) return C.yellow;
  return C.green;
}

function drawArc(dc, cx, cy, r, a0, a1, color, lw) {
  dc.setFillColor(color);
  const steps = Math.max(2, Math.ceil(Math.abs(a1 - a0) / 1.2));
  for (let i = 0; i <= steps; i++) {
    const a = ((a0 + ((a1 - a0) * i) / steps) * Math.PI) / 180;
    const x = cx + r * Math.cos(a);
    const y = cy + r * Math.sin(a);
    dc.fillEllipse(new Rect(x - lw / 2, y - lw / 2, lw, lw));
  }
}

function ringImage(d, size, lw) {
  const dc = new DrawContext();
  dc.size = new Size(size, size);
  dc.opaque = false;
  dc.respectScreenScale = true;
  const c = size / 2;
  const r = c - lw / 2 - 1;
  drawArc(dc, c, c, r, 0, 360, C.track, lw);
  const pct = d ? (d.unlimited ? 1 : d.pct || 0) : 0;
  if (pct > 0) drawArc(dc, c, c, r, -90, -90 + 360 * pct, levelColor(d), lw);

  const big = d ? (d.unlimited ? "∞" : fmtGBnum(d.availMB)) : "—";
  const small = d ? (d.unlimited ? "ilimitado" : `${unitOf(d.availMB)} libres`) : "";
  dc.setTextAlignedCenter();
  dc.setFont(Font.boldSystemFont(size * 0.2));
  dc.setTextColor(C.text);
  dc.drawTextInRect(big, new Rect(lw, c - size * 0.17, size - lw * 2, size * 0.26));
  dc.setFont(Font.mediumSystemFont(size * 0.095));
  dc.setTextColor(C.sub);
  dc.drawTextInRect(small, new Rect(lw, c + size * 0.08, size - lw * 2, size * 0.14));
  return dc.getImage();
}

function barImage(d, w, h) {
  const dc = new DrawContext();
  dc.size = new Size(w, h);
  dc.opaque = false;
  dc.respectScreenScale = true;
  const track = new Path();
  track.addRoundedRect(new Rect(0, 0, w, h), h / 2, h / 2);
  dc.addPath(track);
  dc.setFillColor(C.track);
  dc.fillPath();
  const pct = d ? (d.unlimited ? 1 : d.pct || 0) : 0;
  if (pct > 0) {
    const fw = Math.max(h, w * pct);
    const p = new Path();
    p.addRoundedRect(new Rect(0, 0, fw, h), h / 2, h / 2);
    dc.addPath(p);
    dc.setFillColor(levelColor(d));
    dc.fillPath();
  }
  return dc.getImage();
}

function chartImage(daily, w, h) {
  const dc = new DrawContext();
  dc.size = new Size(w, h);
  dc.opaque = false;
  dc.respectScreenScale = true;
  const labelH = 14;
  const valueH = 12;
  const chartH = h - labelH - valueH;
  const max = Math.max(1, ...daily.map((x) => x.mb || 0));
  const slot = w / daily.length;
  const bw = Math.min(18, slot * 0.55);
  const df = new DateFormatter();
  df.locale = "es_MX";
  df.dateFormat = "d";
  daily.forEach((x, i) => {
    const cx = slot * i + slot / 2;
    const bh = x.mb ? Math.max(3, (x.mb / max) * (chartH - 2)) : 3;
    const p = new Path();
    p.addRoundedRect(new Rect(cx - bw / 2, valueH + chartH - bh, bw, bh), 3, 3);
    dc.addPath(p);
    dc.setFillColor(x.mb == null ? C.track : i === daily.length - 1 ? C.green : new Color("#30D158", 0.55));
    dc.fillPath();
    dc.setTextAlignedCenter();
    if (x.mb) {
      dc.setFont(Font.mediumSystemFont(8));
      dc.setTextColor(C.sub);
      const t = x.mb >= 1024 ? (x.mb / 1024).toFixed(1) + "G" : Math.round(x.mb) + "M";
      dc.drawTextInRect(t, new Rect(cx - slot / 2, valueH + chartH - bh - valueH, slot, valueH));
    }
    dc.setFont(Font.mediumSystemFont(9));
    dc.setTextColor(i === daily.length - 1 ? C.text : C.sub);
    dc.drawTextInRect(df.string(x.date), new Rect(cx - slot / 2, h - labelH + 2, slot, labelH));
  });
  return dc.getImage();
}

// ───────────────────────────── WIDGET ─────────────────────────────────────
function txt(stack, s, font, color = C.text, opts = {}) {
  const t = stack.addText(s);
  t.font = font;
  t.textColor = color;
  t.lineLimit = opts.lines || 1;
  t.minimumScaleFactor = opts.scale || 0.6;
  return t;
}

function header(w, res, compact = false) {
  const row = w.addStack();
  row.centerAlignContent();
  txt(row, "BAIT DATA", Font.heavySystemFont(compact ? 11 : 12), C.text);
  row.addSpacer();
  const { label, color } = connState(res);
  if (!compact) {
    txt(row, label, Font.mediumSystemFont(10), color);
    row.addSpacer(4);
  }
  const dot = row.addText("●");
  dot.font = Font.systemFont(8);
  dot.textColor = color;
  return row;
}

function connState(res) {
  switch (res.state) {
    case "ok":
      return { label: "Conectado con BAIT", color: C.green };
    case "auth":
      return { label: "Sesión expirada · toca", color: C.yellow };
    case "network":
      return { label: "Sin conexión", color: C.yellow };
    case "nosession":
      return { label: "Sin configurar", color: C.sub };
    default:
      return { label: "Error de BAIT", color: C.red };
  }
}

function footerText(res) {
  const c = res.cache;
  if (!c || !c.lastOk) return res.state === "nosession" ? "Toca para configurar" : "Sin datos todavía";
  let s = `Act. ${fmtTime(new Date(c.lastOk))}`;
  if (res.state !== "ok") s += ` (${fmtAgo(c.lastOk)})`;
  return s;
}

function newWidget() {
  const w = new ListWidget();
  const g = new LinearGradient();
  g.colors = [C.bgTop, C.bgBottom];
  g.locations = [0, 1];
  w.backgroundGradient = g;
  w.backgroundColor = C.bgBottom;
  w.refreshAfterDate = new Date(Date.now() + CFG.WIDGET_REFRESH_MINUTES * 60e3);
  w.url = `scriptable:///run/${encodeURIComponent(Script.name())}?action=refresh`;
  return w;
}

function emptyState(w, res, family) {
  w.addSpacer();
  const msg =
    res.state === "nosession"
      ? "Toca para vincular tu línea BAIT"
      : res.state === "auth"
      ? "Tu sesión expiró.\nToca para iniciar sesión de nuevo."
      : `No se pudo consultar BAIT.\n${(res.cache && res.cache.error && res.cache.error.message) || ""}`;
  txt(w, msg, Font.semiboldSystemFont(family === "small" ? 13 : 15), C.text, { lines: 4 });
  w.addSpacer();
}

function buildSmall(res) {
  const w = newWidget();
  w.setPadding(12, 12, 12, 12);
  header(w, res, true);
  const d = res.cache && res.cache.data;
  if (!d) return emptyState(w, res, "small"), w;
  w.addSpacer(6);
  const row = w.addStack();
  row.addSpacer();
  const img = row.addImage(ringImage(d, 180, 16));
  img.imageSize = new Size(84, 84);
  row.addSpacer();
  w.addSpacer(6);
  const l1 = w.addStack();
  txt(l1, d.unlimited ? "Ilimitado" : d.pct != null ? `${Math.round(d.pct * 100)}% usado` : d.status, Font.semiboldSystemFont(12), levelColor(d));
  l1.addSpacer();
  const l2 = w.addStack();
  txt(l2, d.expire ? `Vence ${fmtDate(new Date(d.expire))}` : "Sin vigencia", Font.mediumSystemFont(11), C.sub);
  l2.addSpacer();
  if (res.state !== "ok") txt(l2, "⚠︎", Font.mediumSystemFont(11), C.yellow);
  return w;
}

function statCol(stack, label, value, color = C.text) {
  const s = stack.addStack();
  s.layoutVertically();
  txt(s, label.toUpperCase(), Font.semiboldSystemFont(9), C.sub);
  s.addSpacer(2);
  txt(s, value, Font.semiboldSystemFont(14), color);
  return s;
}

function buildMedium(res) {
  const w = newWidget();
  w.setPadding(14, 16, 14, 16);
  header(w, res);
  const d = res.cache && res.cache.data;
  if (!d) return emptyState(w, res, "medium"), w;
  w.addSpacer(8);
  const big = w.addStack();
  big.bottomAlignContent();
  txt(big, d.unlimited ? "Ilimitado" : fmtGBnum(d.availMB), Font.boldSystemFont(30), C.text);
  if (!d.unlimited) {
    big.addSpacer(4);
    txt(big, `${unitOf(d.availMB)} de ${fmtData(d.totalMB, d.totalMB % 1024 ? 2 : 0)}${d.totalIsManual ? "*" : ""}`, Font.mediumSystemFont(13), C.sub);
  }
  big.addSpacer();
  if (d.pct != null && !d.unlimited) txt(big, `${Math.round(d.pct * 100)}%`, Font.boldSystemFont(16), levelColor(d));
  w.addSpacer(6);
  w.addImage(barImage(d, 600, 14)).imageSize = new Size(300, 7);
  w.addSpacer(10);
  const row = w.addStack();
  statCol(row, "Consumidos", fmtData(d.usedMB));
  row.addSpacer();
  statCol(row, "Días restantes", d.daysLeft != null ? `${d.daysLeft}` : "—", d.daysLeft != null && d.daysLeft <= 2 ? C.red : C.text);
  row.addSpacer();
  statCol(row, "Sincronizado", footerText(res).replace("Act. ", ""), res.state === "ok" ? C.text : C.yellow);
  return w;
}

function buildLarge(res) {
  const w = newWidget();
  w.setPadding(16, 16, 14, 16);
  header(w, res);
  const d = res.cache && res.cache.data;
  if (!d) return emptyState(w, res, "large"), w;

  w.addSpacer(10);
  const top = w.addStack();
  top.centerAlignContent();
  const ring = top.addImage(ringImage(d, 220, 18));
  ring.imageSize = new Size(96, 96);
  top.addSpacer(14);
  const col = top.addStack();
  col.layoutVertically();
  txt(col, "DISPONIBLES", Font.semiboldSystemFont(10), C.sub);
  txt(col, d.unlimited ? "Ilimitado" : fmtData(d.availMB), Font.boldSystemFont(28), C.text);
  txt(col, d.unlimited ? "" : `de ${fmtData(d.totalMB)}${d.totalIsManual ? " (manual)" : ""}`, Font.mediumSystemFont(12), C.sub);
  col.addSpacer(4);
  txt(col, d.status, Font.semiboldSystemFont(12), levelColor(d));

  w.addSpacer(10);
  w.addImage(barImage(d, 640, 16)).imageSize = new Size(320, 8);
  w.addSpacer(10);

  const g1 = w.addStack();
  statCol(g1, "Consumidos", fmtData(d.usedMB));
  g1.addSpacer();
  statCol(g1, "% usado", d.pct != null ? `${Math.round(d.pct * 100)}%` : "—", levelColor(d));
  g1.addSpacer();
  statCol(g1, "Días rest.", d.daysLeft != null ? `${d.daysLeft}` : "—");
  g1.addSpacer();
  statCol(g1, "Renovación", d.expire ? fmtDate(new Date(d.expire)) : "—");

  if (d.social || d.minutes != null) {
    w.addSpacer(6);
    const g2 = w.addStack();
    if (d.social)
      txt(g2, `Redes sociales: ${d.social.unlimited ? "ilimitadas" : `${fmtData(d.social.totalMB - d.social.usedMB)} libres`}`, Font.mediumSystemFont(11), C.sub);
    g2.addSpacer();
    if (d.minutes != null) txt(g2, `${Math.round(d.minutes)} min · ${Math.round(d.sms || 0)} SMS`, Font.mediumSystemFont(11), C.sub);
  }

  w.addSpacer(10);
  const daily = History.daily(10);
  const known = daily.filter((x) => x.mb != null);
  const hrow = w.addStack();
  txt(hrow, "CONSUMO DIARIO", Font.semiboldSystemFont(10), C.sub);
  hrow.addSpacer();
  if (known.length) {
    const avg = known.reduce((a, x) => a + x.mb, 0) / known.length;
    txt(hrow, `prom. ${fmtData(avg, 1)}/día`, Font.mediumSystemFont(10), C.sub);
  }
  w.addSpacer(4);
  if (known.length >= 1) {
    w.addImage(chartImage(daily, 640, 150)).imageSize = new Size(320, 75);
  } else {
    txt(w, "El historial se llena con cada actualización diaria (necesita al menos 2 días de lecturas).", Font.mediumSystemFont(11), C.sub, { lines: 2 });
  }
  w.addSpacer();
  const f = w.addStack();
  txt(f, footerText(res), Font.mediumSystemFont(10), res.state === "ok" ? C.sub : C.yellow);
  f.addSpacer();
  txt(f, `Línea •••${String((res.session && res.session.number) || "").slice(-4)}`, Font.mediumSystemFont(10), C.sub);
  return w;
}

function buildWidget(res, family) {
  if (family === "small") return buildSmall(res);
  if (family === "large" || family === "extraLarge") return buildLarge(res);
  if (family === "accessoryCircular") {
    const w = new ListWidget();
    const d = res.cache && res.cache.data;
    w.addImage(ringImage(d, 120, 12));
    return w;
  }
  if (family === "accessoryRectangular" || family === "accessoryInline") {
    const w = new ListWidget();
    const d = res.cache && res.cache.data;
    txt(w, d ? `BAIT ${d.unlimited ? "∞" : fmtData(d.availMB)} libres` : "BAIT —", Font.semiboldSystemFont(13));
    return w;
  }
  return buildMedium(res);
}

// ───────────────────────────── DIAGNÓSTICO ────────────────────────────────
async function diagnostics() {
  const lines = [];
  const session = Auth.get();
  lines.push(`Sesión: ${session ? `sí (••${session.number.slice(-4)}, ${session.isSSO ? "Walmart SSO" : "legacy"}, ${fmtAgo(session.savedAt)})` : "no"}`);
  let keys;
  try {
    keys = await ClientKeys.get(true);
    lines.push(`Config. portal: OK (${keys.bundle}, app ${keys.appVersion || "?"})`);
    lines.push(`Cabeceras: consumo ${keys.xOrdService ? "✓" : "✗"} · legacy ${keys.ordenarisKey ? "✓" : "✗"} · SSO ${keys.xOrdServiceSSO ? "✓" : "✗"}`);
  } catch (e) {
    lines.push(`Config. portal: ERROR ${e.message}`);
  }
  if (session && keys) {
    for (const s of Api.strategies(session, keys)) {
      try {
        const r = await s.run();
        let ok = "";
        if (r.json && r.json.success !== false) {
          try {
            const d = s.parse(r.json);
            ok = ` → ${fmtData(d.availMB)} de ${fmtData(d.totalMB)}`;
          } catch (e) {
            ok = ` → formato: ${e.message}`;
          }
        } else if (r.json) ok = ` → ${r.json.message || r.json.mensaje || "success=false"}`;
        lines.push(`${s.name}: HTTP ${r.status}${ok}`);
      } catch (e) {
        lines.push(`${s.name}: ${e.message}`);
      }
    }
  }
  const c = Cache.get();
  if (c) {
    lines.push(`Última lectura OK: ${c.lastOk ? fmtAgo(c.lastOk) + " vía " + (c.data && c.data.source) : "nunca"}`);
    if (c.error) lines.push(`Último error: ${c.error.kind} – ${c.error.message}`);
  }
  lines.push(`Días en historial: ${Object.keys(History.get().days).length}`);
  const a = new Alert();
  a.title = "Diagnóstico BAIT DATA";
  a.message = lines.join("\n");
  a.addAction("Copiar");
  a.addCancelAction("Cerrar");
  if ((await a.presentAlert()) === 0) Pasteboard.copy(lines.join("\n"));
}

// ───────────────────────────── MENÚ EN LA APP ─────────────────────────────
async function showResult(res) {
  const d = res.cache && res.cache.data;
  const a = new Alert();
  a.title = res.state === "ok" ? "BAIT DATA ✓" : "BAIT DATA ⚠︎";
  if (d) {
    a.message =
      `${d.unlimited ? "Datos ilimitados" : `${fmtData(d.availMB)} disponibles de ${fmtData(d.totalMB)}`}\n` +
      `Consumidos: ${fmtData(d.usedMB)}${d.pct != null ? ` (${Math.round(d.pct * 100)}%)` : ""}\n` +
      `Vence: ${d.expire ? fmtDate(new Date(d.expire), true) : "—"}${d.daysLeft != null ? ` · ${d.daysLeft} días` : ""}\n` +
      `Estado: ${d.status}\n${footerText(res)}`;
  } else a.message = "Aún no hay datos.";
  if (res.state !== "ok" && res.cache && res.cache.error) a.message += `\n\n⚠︎ ${res.cache.error.message}`;
  a.addAction("OK");
  await a.presentAlert();
}

async function settingsMenu() {
  const s = Settings.get();
  const a = new Alert();
  a.title = "Paquete manual (opcional)";
  a.message =
    "Solo se usa si BAIT no informa el total de tu paquete. Escribe los GB totales o deja vacío para detección automática.";
  a.addTextField("GB totales", s.manualTotalMB ? String(s.manualTotalMB / 1024) : "");
  a.addAction("Guardar");
  a.addCancelAction("Cancelar");
  if ((await a.presentAlert()) === -1) return;
  const v = num(a.textFieldValue(0));
  Settings.set({ ...s, manualTotalMB: v && v > 0 ? v * 1024 : null });
}

async function resetAll() {
  const a = new Alert();
  a.title = "¿Borrar todo?";
  a.message = "Se eliminarán la sesión, la caché y el historial de este dispositivo.";
  a.addDestructiveAction("Borrar");
  a.addCancelAction("Cancelar");
  if ((await a.presentAlert()) === -1) return;
  Auth.clear();
  Store.kcRemove(CFG.KC_KEYS);
  Store.kcRemove(CFG.KC_SETTINGS);
  Store.remove("cache.json");
  Store.remove("history.json");
  try {
    const wv = new WebView();
    await safeLoad(() => wv.loadURL(CFG.BASE + "/"));
    await wv.evaluateJavaScript("localStorage.clear(); true");
  } catch (e) {}
}

async function setupFlow() {
  const session = await Auth.interactiveLogin();
  if (!session) {
    const a = new Alert();
    a.title = "No se vinculó la línea";
    a.message = "No se detectó un inicio de sesión completo en mibait.com. Vuelve a intentarlo y espera a ver tu consumo antes de cerrar.";
    a.addAction("OK");
    await a.presentAlert();
    return null;
  }
  return getUsage({ force: !(Cache.get() && Cache.isFresh(Cache.get())) });
}

async function appMenu() {
  if (!Auth.get()) {
    const res = await setupFlow();
    if (res) await showResult(res);
    return;
  }
  const a = new Alert();
  a.title = "BAIT DATA";
  const c = Cache.get();
  a.message = c && c.lastOk ? `Última actualización ${fmtAgo(c.lastOk)}` : "Sin datos todavía";
  const options = [
    ["Actualizar ahora", async () => showResult(await getUsage({ force: true }))],
    ["Vista previa · pequeño", async () => (await buildWidget(await getUsage(), "small")).presentSmall()],
    ["Vista previa · mediano", async () => (await buildWidget(await getUsage(), "medium")).presentMedium()],
    ["Vista previa · grande", async () => (await buildWidget(await getUsage(), "large")).presentLarge()],
    ["Diagnóstico", diagnostics],
    ["Volver a iniciar sesión", async () => { const r = await setupFlow(); if (r) await showResult(r); }],
    ["Paquete manual", settingsMenu],
  ];
  options.forEach(([t]) => a.addAction(t));
  a.addDestructiveAction("Cerrar sesión y borrar datos");
  a.addCancelAction("Salir");
  const i = await a.presentSheet();
  if (i === -1) return;
  if (i === options.length) return resetAll();
  await options[i][1]();
}

// ───────────────────────────── PUNTO DE ENTRADA ───────────────────────────
async function main() {
  if (config.runsInWidget || config.runsInAccessoryWidget) {
    const res = await getUsage();
    Script.setWidget(buildWidget(res, config.widgetFamily));
    return;
  }
  const action = args.queryParameters && args.queryParameters.action;
  if (action === "refresh") {
    // Toque en el widget: actualización manual.
    if (!Auth.get()) {
      const r = await setupFlow();
      if (r) await showResult(r);
      return;
    }
    let res = await getUsage({ force: true });
    if (res.state === "auth") {
      const r = await setupFlow();
      if (r) res = r;
    }
    await showResult(res);
    return;
  }
  await appMenu();
}

try {
  await main();
} catch (e) {
  console.error(e);
  if (config.runsInWidget) {
    const w = newWidget();
    txt(w, "BAIT DATA", Font.heavySystemFont(12));
    w.addSpacer();
    txt(w, `Error: ${e.message}`, Font.mediumSystemFont(11), C.red, { lines: 4 });
    Script.setWidget(w);
  } else {
    const a = new Alert();
    a.title = "Error";
    a.message = String(e.message || e);
    a.addAction("OK");
    await a.presentAlert();
  }
}
Script.complete();
