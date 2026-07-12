/*
 * section_generator.template.js — AXON schematic section generator (EasyEDA Pro).
 *
 * PATTERN: Engine + CONFIG (P1). Everything above the CONFIG line is board-agnostic
 * and never changes. Everything in CONFIG is data you fill from build_sheet.md.
 *
 * RUN: EasyEDA Pro ▸ Settings ▸ Extensions ▸ Standalone Script ▸ paste ▸ Run.
 * THEN: Design ▸ Annotate (project-wide) — the API cannot reliably set designators.
 *
 * HARD RULES (see docs/06_EASYEDA_INTEGRATION.md):
 *   - Connect BY NET NAME (arg 2 of sch_PrimitiveWire.create). Use SHORT stubs
 *     (long collinear stubs from adjacent parts auto-merge → shorts).
 *   - Never search()[0] for an IC — token-match, reject array parts.
 *   - Verify a picked part by its manufacturerId, not the search string.
 *   - One schematic, multiple PAGES — never separate schematic files.
 */

/* ============================ ENGINE (do not edit) ============================ */
const OUT = 40;                              // short stub length (units) — see hard rules
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function hay(it) {
  return ((it.name||"")+" "+(it.symbolName||"")+" "+(it.manufacturer||"")+" "
    +(it.manufacturerId||"")+" "+(it.description||"")).toLowerCase();
}
function isArrayPart(name) {
  return /^4d\d|cay16|cay10|exb[-_]|isolated|array|network|\brn\b/.test((name||"").toLowerCase());
}
function isWrongType(name, kind) {                 // kind: "R" | "C"
  const s = (name||"").toLowerCase();
  if (kind === "R" && /(cap|µf|uf|nf|pf|inductor|µh|uh)/.test(s)) return true;
  if (kind === "C" && /(ohm|kω|resistor|inductor|µh|uh)/.test(s)) return true;
  return false;
}
async function searchRetry(query, tries = 4) {
  for (let i = 0; i < tries; i++) {
    try { const r = await eda.lib_Device.search(query); if (r) return r; }
    catch (e) {}
    await sleep(800 * (i + 1));                     // backoff
  }
  return null;
}
function unwrap(r) {
  return Array.isArray(r) ? r : (r && (r.deviceList||r.list||r.items||r.result||r.data)) || [];
}
async function pick(query, token) {                 // token = "a|b|c" disambiguation
  const arr = unwrap(await searchRetry(query));
  const tks = token.toLowerCase().split("|");
  for (const it of arr) { const h = hay(it);
    for (const t of tks) if (t && h.indexOf(t) >= 0) return it; }
  return null;                                       // NEVER arr[0] for an IC
}
function eiaCode(kind, val) {                         // secondary value discriminator
  // e.g. "100n"->"104", "47"->"470"(+letter tol). Fill per your value scheme.
  return String(val).replace(/[^0-9]/g, "");
}
async function pickPassive(kind, val) {
  const q = `${val} 0603 ${kind === "R" ? "resistor" : "capacitor"}`;
  const arr = unwrap(await searchRetry(q)).filter(
    (it) => !isArrayPart(it.name) && !isWrongType(it.name, kind));
  const code = eiaCode(kind, val);
  for (const it of arr) if ((it.name||"").indexOf(code) >= 0) return it;   // EIA match wins
  return arr[0] || null;
}
function pinDir(pin, mx, my) {                        // stub direction from rotation + centroid
  const r = ((+pin.rotation || 0) % 360 + 360) % 360;
  if (r === 0 || r === 180) return [Math.sign(pin.x - mx) || 1, 0];
  return [0, Math.sign(pin.y - my) || 1];
}
async function wirePins(comp, pinMap) {
  const pins = await eda.sch_PrimitiveComponent.getAllPinsByPrimitiveId(comp.primitiveId);
  let mx = 0, my = 0; for (const p of pins) { mx += p.x; my += p.y; }
  mx /= pins.length; my /= pins.length;
  for (const p of pins) {
    const net = pinMap[p.name];
    if (net == null) continue;                        // null = intentionally NC
    const [dx, dy] = pinDir(p, mx, my);
    await eda.sch_PrimitiveWire.create([p.x, p.y, p.x + dx*OUT, p.y + dy*OUT], net);
  }
}
async function placeIC(part, x, y, rot) {
  const c = await eda.sch_PrimitiveComponent.create(part.uuid || part.id, x, y, rot || 0);
  await sleep(150);                                   // ~150ms between parts (quota)
  return c;
}

/* ============================ CONFIG (fill this) ============================= */
const SECTION = "<BLOCK NAME>";
const BASE = [200, 200];                              // tile origin for this section

// PARTS: one entry per IC/discrete. pinMap keys = EXACT library pin names.
const PARTS = [
  { ref: "U1", query: "<search term>", token: "<a|b|c>", col: 0, row: 0, rot: 0,
    pinMap: { "<PIN>": "<NET>", "<PIN2>": "<NET2>", "<NC_PIN>": null } },
];

// PASSIVES: [ref, kind("R"|"C"), value, netA, netB]
const PASSIVES = [
  ["R1", "R", "5.1k", "<netA>", "<netB>"],
  ["C1", "C", "10u",  "<netA>", "<netB>"],
];

/* ============================ DRIVER ======================================== */
(async () => {
  const log = [];
  for (const p of PARTS) {
    const part = await pick(p.query, p.token);
    if (!part) { log.push(`SKIP ${p.ref}: no token match for "${p.query}"`); continue; }
    const x = BASE[0] + p.col * 1700, y = BASE[1] + p.row * 1300;
    const comp = await placeIC(part, x, y, p.rot);
    await wirePins(comp, p.pinMap);
    log.push(`OK ${p.ref} <- ${part.name} (${part.manufacturerId||"?"})`);  // verify this ID!
  }
  for (const [ref, kind, val, a, b] of PASSIVES) {
    const part = await pickPassive(kind, val);
    if (!part) { log.push(`SKIP ${ref}: no ${val} ${kind}`); continue; }
    log.push(`OK ${ref} ${val} ${a}-${b} <- ${part.name}`);
    // place + wire the 2-pin passive between nets a,b (positions per your tiling)
  }
  eda.sys_MessageBox.showInformationMessage(
    `${SECTION}\n` + log.join("\n") + `\n\nNEXT: Design ▸ Annotate (project-wide).`);
})();
