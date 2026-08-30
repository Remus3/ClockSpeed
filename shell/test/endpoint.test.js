"use strict";

// Where the dashboard is, proven against the module that decides it.
//
// The Python side owns every constant this seam restates - the loopback
// address, the two environment variable names, the certificate pair's file
// names and the default certificate directory. CLAUDE.md section 4 names a
// restated fact as one that drifts, and this file is the guard that turns the
// drift red instead of leaving the companion window pointed at a dashboard
// that is not there. Every such assertion EXTRACTS the Python value at run
// time rather than spelling it here a third time.
//
// THE EXTRACTION IS ITSELF ASSERTED BEFORE ANYTHING IS COMPARED. A regex that
// stops matching - because the Python module reformats, or renames, or moves -
// yields no captures, and a loop over no captures makes no assertions and
// passes. That is the shape CS-605 closed and CS-613 is open on: a test whose
// silence is indistinguishable from its success. `pythonConstants` therefore
// returns only the names it actually captured non-empty, and every caller
// asserts the COUNT before it asserts a value.
//
// NO ARM SKIPS. Not on a missing file, not on a missing export, not on a
// platform. A skip conditioned on the code under test is a mute button.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const endpoint = require("../lib/endpoint.js");

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

// Planted in every temporary directory name so a refusal that quotes the path
// it refused can be caught by searching for a string nothing else would emit.
// `tests/surface/test_server.py:96` plants `zqxjcanary601s2` for the identical
// reason; this is that idiom, namespaced to this slice.
const CANARY = "zqxjcanary602s1";

// Ports used by the fixtures. DELIBERATELY OUTSIDE THE ALLOCATED BAND that
// `config/ports.json` owns - CS-604 is open against exactly the fault of a
// second copy of an in-band number appearing in a tracked file, and a test
// fixture is a tracked file like any other.
const RECORD_PORT = 4321;
const ENV_PORT = 5150;

const SURFACE_CONFIG_PARTS = ["clockspeed", "surface", "config.py"];

function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), `${CANARY}-`));
}

function writeRecord(dir, body) {
  const target = path.join(dir, "ports.json");
  fs.writeFileSync(target, body);
  return target;
}

// Every `NAME: Final = "value"` this file asks for, and NOTHING it could not
// capture non-empty. The caller compares the returned size against what it
// asked for, which is what stops a stale regex from passing silently.
function pythonConstants(source, names) {
  const found = new Map();
  for (const name of names) {
    const pattern = new RegExp(`^${name}:\\s*Final\\s*=\\s*"([^"]*)"`, "m");
    const match = pattern.exec(source);
    if (match !== null && match[1].length > 0) {
      found.set(name, match[1]);
    }
  }
  return found;
}

function surfaceConfigSource() {
  return fs.readFileSync(
    path.join(endpoint.repoRoot(), ...SURFACE_CONFIG_PARTS),
    "utf8"
  );
}

// ---------------------------------------------------------------------------
// The root, derived and never spelled
// ---------------------------------------------------------------------------

test("the repository root is the directory carrying the tracked port record", () => {
  const root = endpoint.repoRoot();
  assert.equal(path.isAbsolute(root), true);
  assert.equal(fs.existsSync(path.join(root, "config", "ports.json")), true);
  assert.equal(fs.existsSync(path.join(root, ...SURFACE_CONFIG_PARTS)), true);
});

test("the module source spells no absolute path and reaches for no home", () => {
  const source = moduleSource();
  // A drive-letter root, a POSIX home root, or a call that resolves one. The
  // WORD is not the fault and is not searched for - the prose above `certDir`
  // has to be free to say why the override is dangerous. The drive-letter
  // pattern demands the letter be ALONE: `https://` ends in `s:/` and would
  // otherwise be reported as a drive root on every url this module builds.
  assert.equal(/(^|[^A-Za-z])[A-Za-z]:[\\/]/.test(source), false);
  assert.equal(/[\\/](?:Users|home)[\\/]/.test(source), false);
  assert.equal(source.includes("homedir"), false);
  assert.equal(source.includes("USERPROFILE"), false);
});

// ---------------------------------------------------------------------------
// The allocated band, read from the record that owns it and never typed here
// ---------------------------------------------------------------------------
//
// `config/ports.json` is the single owner of the numbers (CLAUDE.md section 4)
// and CS-604 is open on the fault of a second copy appearing in a tracked
// file. `tests/surface/test_config.py:223` sweeps the Python module for the
// same fault; this is that sweep over the JavaScript seam. The band is READ
// FROM THE RECORD - typing it here would be the very fault being swept for.

function allocatedBand() {
  const payload = JSON.parse(
    fs.readFileSync(path.join(endpoint.repoRoot(), "config", "ports.json"), "utf8")
  );
  return [payload.band.start, payload.band.end];
}

function integersInBand(source, low, high) {
  const hits = [];
  for (const match of source.matchAll(/\d+/g)) {
    const value = Number(match[0]);
    if (Number.isInteger(value) && value >= low && value <= high) {
      hits.push(match[0]);
    }
  }
  return hits;
}

function moduleSource() {
  return fs.readFileSync(path.join(__dirname, "..", "lib", "endpoint.js"), "utf8");
}

test("the module source spells no port inside the allocated band", () => {
  const [low, high] = allocatedBand();
  const hits = integersInBand(moduleSource(), low, high);
  assert.deepEqual(hits, []);
});

test("this test module spells no port inside the allocated band either", () => {
  const [low, high] = allocatedBand();
  const hits = integersInBand(fs.readFileSync(__filename, "utf8"), low, high);
  assert.deepEqual(hits, []);
});

test("the band detector finds a planted positive, so an empty sweep means something", () => {
  const [low, high] = allocatedBand();
  assert.equal(low <= high, true);
  const planted = `const x = ${low}; const y = ${high};`;
  assert.deepEqual(integersInBand(planted, low, high), [String(low), String(high)]);
});

test("the band detector ignores a number outside the band", () => {
  const [low, high] = allocatedBand();
  const planted = `const x = ${low - 1}; const y = ${high + 1};`;
  assert.deepEqual(integersInBand(planted, low, high), []);
});

// ---------------------------------------------------------------------------
// The port, and where it comes from
// ---------------------------------------------------------------------------

test("the url is built from the base port in a synthetic record", () => {
  const dir = makeTempDir();
  const record = writeRecord(dir, JSON.stringify({ schema: 1, base: RECORD_PORT }));
  const url = endpoint.dashboardUrl({ env: {}, record });
  assert.equal(url, `https://${endpoint.expectedHost()}:${RECORD_PORT}/`);
  fs.rmSync(dir, { recursive: true, force: true });
});

test("the url is built from the declared port environment variable", () => {
  const env = { [endpoint.PORT_ENV]: String(ENV_PORT) };
  const url = endpoint.dashboardUrl({ env, record: path.join(makeTempDir(), "absent") });
  assert.equal(url, `https://${endpoint.expectedHost()}:${ENV_PORT}/`);
});

test("the declared port beats the record rather than the other way round", () => {
  const dir = makeTempDir();
  const record = writeRecord(dir, JSON.stringify({ schema: 1, base: RECORD_PORT }));
  const env = { [endpoint.PORT_ENV]: String(ENV_PORT) };
  assert.notEqual(RECORD_PORT, ENV_PORT);
  assert.equal(endpoint.dashboardPort({ env, record }), ENV_PORT);
  assert.equal(endpoint.dashboardPort({ env: {}, record }), RECORD_PORT);
  fs.rmSync(dir, { recursive: true, force: true });
});

test("the real tracked record resolves to a port without an override", () => {
  const resolved = endpoint.dashboardPort({ env: {} });
  assert.equal(Number.isInteger(resolved), true);
  const payload = JSON.parse(
    fs.readFileSync(path.join(endpoint.repoRoot(), "config", "ports.json"), "utf8")
  );
  assert.equal(resolved, payload.base);
});

// ---------------------------------------------------------------------------
// Every refusal is named, and none is a default
// ---------------------------------------------------------------------------

test("a missing record is a named refusal and never a fallback port", () => {
  const record = path.join(makeTempDir(), "absent", "ports.json");
  assert.throws(
    () => endpoint.dashboardUrl({ env: {}, record }),
    (caught) => {
      assert.equal(caught.name, "EndpointError");
      assert.equal(caught.fault, endpoint.EndpointFault.RECORD_UNREADABLE);
      assert.equal(caught.reason, endpoint.RECORD_UNREADABLE);
      return true;
    }
  );
});

test("a record that does not parse is a named refusal", () => {
  const dir = makeTempDir();
  const record = writeRecord(dir, "{not json at all");
  assert.throws(
    () => endpoint.dashboardUrl({ env: {}, record }),
    (caught) => {
      assert.equal(caught.name, "EndpointError");
      assert.equal(caught.fault, endpoint.EndpointFault.RECORD_MALFORMED);
      return true;
    }
  );
  fs.rmSync(dir, { recursive: true, force: true });
});

test("a record carrying no base key is a named refusal", () => {
  const dir = makeTempDir();
  const record = writeRecord(dir, JSON.stringify({ schema: 1, band: { start: 1, end: 2 } }));
  assert.throws(
    () => endpoint.dashboardUrl({ env: {}, record }),
    (caught) => {
      assert.equal(caught.name, "EndpointError");
      assert.equal(caught.fault, endpoint.EndpointFault.RECORD_MALFORMED);
      return true;
    }
  );
  fs.rmSync(dir, { recursive: true, force: true });
});

test("a base that is not a whole number is a named refusal", () => {
  const dir = makeTempDir();
  for (const base of [true, "4321", 43.21, null, [], {}]) {
    const record = writeRecord(dir, JSON.stringify({ schema: 1, base }));
    assert.throws(
      () => endpoint.dashboardPort({ env: {}, record }),
      (caught) => {
        assert.equal(caught.name, "EndpointError");
        assert.equal(caught.fault, endpoint.EndpointFault.RECORD_MALFORMED);
        return true;
      }
    );
  }
  fs.rmSync(dir, { recursive: true, force: true });
});

test("a record carrying a byte outside seven-bit ascii is a named refusal", () => {
  const dir = makeTempDir();
  const target = path.join(dir, "ports.json");
  fs.writeFileSync(target, Buffer.from([0x7b, 0x22, 0xc3, 0xa9, 0x22, 0x7d]));
  assert.throws(
    () => endpoint.dashboardPort({ env: {}, record: target }),
    (caught) => {
      assert.equal(caught.fault, endpoint.EndpointFault.RECORD_MALFORMED);
      return true;
    }
  );
  fs.rmSync(dir, { recursive: true, force: true });
});

test("a blank declared port means unset and falls through to the record", () => {
  // NOT a refusal, and the distinction is deliberate: `config.py:463` strips
  // the declared value and treats the empty result as absent. An arm asserting
  // a refusal here would have pinned behaviour the Python side does not have.
  const dir = makeTempDir();
  const record = writeRecord(dir, JSON.stringify({ schema: 1, base: RECORD_PORT }));
  for (const declared of ["", " ", "\t"]) {
    const env = { [endpoint.PORT_ENV]: declared };
    assert.equal(endpoint.dashboardPort({ env, record }), RECORD_PORT);
  }
  fs.rmSync(dir, { recursive: true, force: true });
});

test("a declared port that is not a base-ten integer is a named refusal", () => {
  for (const declared of ["eight thousand", "0x1f90", "12.5", "1e4", "-", "8_0", "+"]) {
    assert.throws(
      () => endpoint.dashboardPort({ env: { [endpoint.PORT_ENV]: declared } }),
      (caught) => {
        assert.equal(caught.name, "EndpointError");
        assert.equal(caught.fault, endpoint.EndpointFault.PORT_NOT_AN_INTEGER);
        return true;
      }
    );
  }
});

test("a declared port outside the transport range is a named refusal", () => {
  for (const declared of ["65536", "-1", "999999"]) {
    assert.throws(
      () => endpoint.dashboardPort({ env: { [endpoint.PORT_ENV]: declared } }),
      (caught) => {
        assert.equal(caught.fault, endpoint.EndpointFault.PORT_OUT_OF_RANGE);
        return true;
      }
    );
  }
});

test("a refusal cannot be built from anything but a member of the vocabulary", () => {
  // THE CALL THIS VOCABULARY EXISTS TO STOP IS THE FIRST ENTRY. A fault held as
  // a string means the member and its value are the same thing, so - unlike a
  // Python Enum - passing `"record_unreadable"` IS passing a member and is
  // correctly accepted. What must never be accepted is arbitrary text, and a
  // path is the arbitrary text that carries personal data.
  const notMembers = [
    "C" + ":" + path.sep + "Users" + path.sep + "someone",
    "/tmp/anything",
    "record unreadable",
    "RECORD_UNREADABLE",
    "",
    0,
    1,
    null,
    undefined,
    {},
    [],
    Symbol("record_unreadable"),
  ];
  for (const notAMember of notMembers) {
    assert.throws(
      () => new endpoint.EndpointError(notAMember),
      (caught) => {
        assert.equal(caught instanceof TypeError, true);
        assert.equal(caught.message, endpoint.FAULT_NOT_A_MEMBER);
        return true;
      }
    );
  }
});

test("every declared member of the vocabulary is spoken as a fixed line", () => {
  const members = Object.values(endpoint.EndpointFault);
  assert.equal(members.length > 0, true);
  const spoken = members.map((fault) => endpoint.endpointRefusal(fault));
  // Every member maps to a non-empty line, and no two members share one.
  assert.equal(spoken.filter((line) => typeof line === "string" && line.length > 0).length, members.length);
  assert.equal(new Set(spoken).size, members.length);
  // And no fixed line quotes a separator - the property the privacy arm relies
  // on, asserted here over the WHOLE vocabulary rather than over the subset a
  // caller happened to trip.
  const withSeparator = spoken.filter((line) => line.includes("/") || line.includes("\\")).length;
  assert.equal(withSeparator, 0);
});

// ---------------------------------------------------------------------------
// PRIVACY - non-negotiable 3. Nothing refused is ever quoted back.
// ---------------------------------------------------------------------------

test("no refusal quotes a path, a separator or any fragment of one", () => {
  const dir = makeTempDir();
  const messages = [];

  const collect = (thunk) => {
    try {
      thunk();
    } catch (caught) {
      messages.push(String(caught.message));
      messages.push(String(caught.reason === undefined ? "" : caught.reason));
      messages.push(String(caught));
      return;
    }
    assert.fail("the call under test did not refuse");
  };

  collect(() => endpoint.dashboardPort({ env: {}, record: path.join(dir, "absent.json") }));
  collect(() => endpoint.dashboardPort({ env: {}, record: writeRecord(dir, "{nope") }));
  collect(() =>
    endpoint.dashboardPort({ env: {}, record: writeRecord(dir, JSON.stringify({ a: 1 })) })
  );
  collect(() => endpoint.dashboardPort({ env: { [endpoint.PORT_ENV]: `${CANARY}` } }));
  collect(() => endpoint.dashboardPort({ env: { [endpoint.PORT_ENV]: "70000" } }));
  collect(() => new endpoint.EndpointError(`${dir}`));

  // Bound to a scalar BEFORE the assertion: pytest-style rewriting is not the
  // hazard here, but an assertion over a freshly computed aggregate hides which
  // member failed, and a count is what makes the failure readable.
  const leakedCanary = messages.filter((line) => line.includes(CANARY)).length;
  assert.equal(leakedCanary, 0);

  const leakedTemp = messages.filter((line) => line.includes(dir)).length;
  assert.equal(leakedTemp, 0);

  const leakedSeparator = messages.filter(
    (line) => line.includes("/") || line.includes("\\")
  ).length;
  assert.equal(leakedSeparator, 0);

  const leakedTempParent = messages.filter((line) => line.includes(os.tmpdir())).length;
  assert.equal(leakedTempParent, 0);

  assert.equal(messages.length > 0, true);
  fs.rmSync(dir, { recursive: true, force: true });
});

test("the canary planter actually plants, so the leak arm could have failed", () => {
  const dir = makeTempDir();
  assert.equal(dir.includes(CANARY), true);
  assert.equal(dir.includes(path.sep), true);
  fs.rmSync(dir, { recursive: true, force: true });
});

// ---------------------------------------------------------------------------
// The certificate pair, and the four constants Python owns
// ---------------------------------------------------------------------------

test("the four certificate and environment constants match the Python module", () => {
  const names = ["CERT_NAME", "KEY_NAME", "CERT_DIR_ENV", "DEFAULT_CERT_DIRNAME"];
  const found = pythonConstants(surfaceConfigSource(), names);

  // ASSERTED BEFORE ANYTHING IS COMPARED. A failed extraction compares nothing
  // and would otherwise pass.
  assert.equal(found.size, names.length);

  assert.equal(endpoint.CERT_NAME, found.get("CERT_NAME"));
  assert.equal(endpoint.KEY_NAME, found.get("KEY_NAME"));
  assert.equal(endpoint.CERT_DIR_ENV, found.get("CERT_DIR_ENV"));
  assert.equal(endpoint.DEFAULT_CERT_DIRNAME, found.get("DEFAULT_CERT_DIRNAME"));
});

test("the address and port constants match the Python module", () => {
  const names = ["LOOPBACK", "PORT_ENV", "PORTS_RECORD_BASE_KEY"];
  const found = pythonConstants(surfaceConfigSource(), names);
  assert.equal(found.size, names.length);

  assert.equal(endpoint.expectedHost(), found.get("LOOPBACK"));
  assert.equal(endpoint.PORT_ENV, found.get("PORT_ENV"));
  assert.equal(endpoint.PORTS_RECORD_BASE_KEY, found.get("PORTS_RECORD_BASE_KEY"));
});

test("the constant extractor reports a name it could not capture", () => {
  const found = pythonConstants(surfaceConfigSource(), ["CERT_NAME", "NO_SUCH_CONSTANT"]);
  assert.equal(found.size, 1);
  assert.equal(found.has("NO_SUCH_CONSTANT"), false);
});

test("the certificate defaults beside the repository and never inside a home", () => {
  const dir = endpoint.certDir({});
  assert.equal(dir, path.join(endpoint.repoRoot(), endpoint.DEFAULT_CERT_DIRNAME));
  assert.equal(
    endpoint.certPath({}),
    path.join(endpoint.repoRoot(), endpoint.DEFAULT_CERT_DIRNAME, endpoint.CERT_NAME)
  );
});

test("the declared certificate directory overrides the default", () => {
  const dir = makeTempDir();
  const env = { [endpoint.CERT_DIR_ENV]: dir };
  assert.equal(endpoint.certDir(env), dir);
  assert.equal(endpoint.certPath(env), path.join(dir, endpoint.CERT_NAME));
  fs.rmSync(dir, { recursive: true, force: true });
});

test("a blank declared certificate directory falls back to the default", () => {
  for (const declared of ["", "   "]) {
    const env = { [endpoint.CERT_DIR_ENV]: declared };
    assert.equal(endpoint.certDir(env), path.join(endpoint.repoRoot(), endpoint.DEFAULT_CERT_DIRNAME));
  }
});

test("the certificate pair is named but no helper hands out the private key", () => {
  assert.equal(typeof endpoint.CERT_NAME, "string");
  assert.equal(typeof endpoint.KEY_NAME, "string");
  assert.notEqual(endpoint.CERT_NAME, endpoint.KEY_NAME);
  assert.equal(endpoint.keyPath, undefined);
});

// ---------------------------------------------------------------------------
// The host
// ---------------------------------------------------------------------------

test("the host is the loopback address and the url never names another", () => {
  const host = endpoint.expectedHost();
  const dir = makeTempDir();
  const record = writeRecord(dir, JSON.stringify({ schema: 1, base: RECORD_PORT }));
  const url = new URL(endpoint.dashboardUrl({ env: {}, record }));
  assert.equal(url.hostname, host);
  assert.equal(url.protocol, "https:");
  assert.equal(url.port, String(RECORD_PORT));
  fs.rmSync(dir, { recursive: true, force: true });
});
