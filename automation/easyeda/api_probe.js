/* ============================================================================
 * PCB Flow — EasyEDA Pro API DISCOVERY PROBE
 * ----------------------------------------------------------------------------
 * WHY: the EasyEDA Pro script API is flagged "early/unstable" and its exact
 *   method names + object shapes vary by build. Before running the schematic
 *   generator, confirm three things on YOUR build: the LIBRARY SEARCH method,
 *   the shape of the object create() returns, and the shape of a PIN object.
 *   This is the "probe before assume" discipline — it prevents the wrong-signature
 *   calls that can hard-hang the renderer. It changes nothing except (optionally)
 *   placing ONE test part you can delete.
 *
 * HOW TO RUN:
 *   1. Open a schematic page in EasyEDA Pro.
 *   2. Press F12 to open the browser Console (to read the output).
 *   3. Settings > Extensions > Standalone Script > paste this > Run Script.
 *   4. Read the lines starting with [PROBE] — they tell you the real method
 *      names + field names to use in dump_schematic.js and the generator.
 * ========================================================================== */
(async function () {
  var out = [];
  function L(m) { out.push("" + m); try { console.log("[PROBE] " + m); } catch (e) {} }
  function J(o) { try { return JSON.stringify(o); } catch (e) { return "<unstringifiable>"; } }
  function keys(o) { try { return Object.keys(o).join(", "); } catch (e) { return "?"; } }
  function methodsOf(o) {
    var s = new Set();
    try { Object.keys(o).forEach(function (k) { s.add(k); }); } catch (e) {}
    try {
      var p = Object.getPrototypeOf(o);
      while (p && p !== Object.prototype) {
        Object.getOwnPropertyNames(p).forEach(function (k) { if (k !== "constructor") s.add(k); });
        p = Object.getPrototypeOf(p);
      }
    } catch (e) {}
    return Array.from(s).join(", ");
  }

  L("===== EasyEDA Pro API probe =====");

  // 1) Which eda.* namespaces exist?
  try {
    var ns = Object.keys(eda).filter(function (k) { return /^(lib|sch|pcb|dmt|sys|prj|wks)_/.test(k); });
    L("eda namespaces: " + ns.join(", "));
  } catch (e) { L("enumerate eda failed: " + e); }

  // 2) Inspect every library-ish object for a search-like method
  try {
    Object.keys(eda).forEach(function (k) {
      if (/lib/i.test(k)) L("methods of eda." + k + " : " + methodsOf(eda[k]));
    });
  } catch (e) { L("lib inspect failed: " + e); }

  // 3) Try likely library-search calls and report the result shape
  var QUERY = "NE555";   // any common part the offline/online lib will return
  var device = null;
  var candidates = [
    ["lib_Device.search", function () { return eda.lib_Device.search(QUERY); }],
    ["lib_Device.searchDevice", function () { return eda.lib_Device.searchDevice(QUERY); }],
    ["lib_LibrariesList.search", function () { return eda.lib_LibrariesList.search(QUERY); }],
    ["lib_Library.search", function () { return eda.lib_Library.search(QUERY); }],
    ["lib_Symbol.search", function () { return eda.lib_Symbol.search(QUERY); }],
    ["sys_Library.search", function () { return eda.sys_Library.search(QUERY); }]
  ];
  for (var i = 0; i < candidates.length; i++) {
    var name = candidates[i][0], fn = candidates[i][1];
    try {
      var r = await fn();
      L("OK  " + name + " -> " + (Array.isArray(r) ? "Array(" + r.length + ")" : keys(r)));
      var arr = Array.isArray(r) ? r : (r && (r.deviceList || r.list || r.items || r.result || r.data));
      if (arr && arr.length) {
        L("    first item keys: " + keys(arr[0]));
        L("    first item: " + J(arr[0]).slice(0, 400));
        if (!device && (arr[0].uuid || arr[0].libraryUuid)) device = arr[0];
      } else if (r && (r.uuid || r.libraryUuid)) {
        if (!device) device = r;
      }
    } catch (e) {
      L("--  " + name + " : not available (" + (e && e.message ? e.message : e) + ")");
    }
  }

  // 4) If a device was found, place it and report create() + pin shapes
  if (device) {
    try {
      var comp = await eda.sch_PrimitiveComponent.create(device, 100, 100);
      L("create() returned keys: " + keys(comp));
      var pid = comp && (comp.primitiveId || comp.id || comp.pid ||
                (comp.getState && comp.getState().primitiveId));
      L("guessed primitiveId = " + pid);
      if (pid != null && eda.sch_PrimitiveComponent.getAllPinsByPrimitiveId) {
        var pins = await eda.sch_PrimitiveComponent.getAllPinsByPrimitiveId(pid);
        L("pin count = " + (pins && pins.length));
        if (pins && pins.length) {
          L("first pin keys: " + keys(pins[0]));
          L("first pin: " + J(pins[0]).slice(0, 400));  // note the num/name/x/y field names
        }
      }
    } catch (e) { L("place/pin probe failed: " + e); }
  } else {
    L("NO library-search candidate worked — read the 'methods of eda.lib*' lines for the real name.");
  }

  L("===== probe done — note the method + field names above =====");
  try { eda.sys_MessageBox.showInformationMessage(out.join("\n")); } catch (e) {}
})();
