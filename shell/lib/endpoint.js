"use strict";

/**
 * Where the dashboard is, and what it is listening with.
 *
 * Owns, for the Electron side only: the resolution of the repository root, the
 * dashboard url, the certificate the companion window pins, and the address it
 * expects to find on the other end of the handshake.
 *
 * THE PORT NUMBER IS NOT IN THIS FILE AND MUST NEVER BE. `config/ports.json` is
 * the single owner of the allocation (CLAUDE.md section 4), and this module
 * reads PORTS_RECORD_BASE_KEY out of it - the same key, by the same name, that
 * `clockspeed/surface/config.py` reads. The allocation has MOVED once already;
 * a number spelled here would have become a second, silently stale copy, and
 * the failure it produces is not a crash but a companion window politely
 * connecting to nothing. CS-604 is open against exactly this class, and
 * `test/endpoint.test.js` sweeps this file for an integer anywhere in the
 * allocated band - reading the band FROM the record rather than from a literal.
 *
 * THE ROOT IS DERIVED, NEVER SPELLED. It comes from this file's own location,
 * mirroring `repo_root()` in `clockspeed/surface/config.py`. An absolute path
 * literal would carry the account name of whoever authored it, which is
 * non-negotiable 3.
 *
 * PRECEDENCE IS STATED RATHER THAN LEFT TO WHICHEVER THE READER ASSUMES: an
 * explicit request beats PORT_ENV, which beats the record. NOTHING FALLS BACK
 * PAST THE RECORD. A missing or malformed record is a thrown, named refusal and
 * never a default, because a dashboard on an unexpected port is one the
 * companion cannot find - the same reason `clockspeed/surface/server.py`
 * refuses to negotiate the port after a failed bind rather than trying another.
 *
 * WHY EVERY REFUSAL IS A FIXED LINE. The record path is derived, but
 * CERT_DIR_ENV can point anywhere a user can write, and such a path is personal
 * data under non-negotiable 3. So no message built here quotes a path, a file
 * name, or any fragment of one - and that is enforced by the CONSTRUCTOR rather
 * than by prose. `EndpointError` takes an `EndpointFault` - a member of the
 * frozen set declared below - and never a string, so `endpointRefusal` is the
 * only thing that can decide what an operator reads. A sentence in a docstring
 * is a control that holds exactly as long as every future throw site has read
 * it; `new EndpointError(String(somePath))` would have satisfied a string
 * signature, and would have written a user's directory to a log. It throws at
 * construction now. This is the same shape `clockspeed/surface/config.py`
 * applies over its four-member vocabulary, and the same one `server.py` applies
 * to `BindError`.
 *
 * THIS MODULE READS ONE FILE AND WRITES NONE. The one file is this repository's
 * own tracked configuration record - not a save, not the game install, and
 * nothing derived from either.
 *
 * COMMONJS DELIBERATELY. Sibling modules in `shell/` require this one, and the
 * manifest carries no `"type": "module"`.
 */

const fs = require("node:fs");
const path = require("node:path");

// ---------------------------------------------------------------------------
// The address
// ---------------------------------------------------------------------------

/**
 * The ONLY address the dashboard ever binds, and so the only one the companion
 * ever expects. Not a default and not a preference: the dashboard reads a local
 * save and answers questions about it, so a listener reachable from another
 * machine is a disclosure channel. Pinned byte-for-byte against `LOOPBACK` in
 * `clockspeed/surface/config.py` by `test/endpoint.test.js`.
 */
const LOOPBACK = "127.0.0.1";

/** The dashboard speaks TLS and nothing else. There is no cleartext fallback. */
const SCHEME = "https";

/** Overrides the record's allocation. Matches `PORT_ENV` on the Python side. */
const PORT_ENV = "CLOCKSPEED_DASHBOARD_PORT";

/**
 * The allocation record, relative to the repository root, held as PARTS so this
 * file spells no separator and works unchanged on either platform.
 */
const PORTS_RECORD_PARTS = Object.freeze(["config", "ports.json"]);

/** The key inside that record holding the dashboard's allocated port. */
const PORTS_RECORD_BASE_KEY = "base";

/**
 * What the transport admits. NOT an allocation - the record owns that, and
 * these two are the range any port at all has to sit inside. Zero is admitted
 * deliberately: it is what asks the kernel for an ephemeral port.
 */
const LOWEST_PORT = 0;
const HIGHEST_PORT = 65535;

/** The highest byte the record may contain. Anything above it is not ascii. */
const MAX_ASCII = 0x7e;

// ---------------------------------------------------------------------------
// The certificate pair
// ---------------------------------------------------------------------------
//
// RESTATED FROM PYTHON, AND THE RESTATEMENT IS GUARDED. `clockspeed/surface/
// config.py` owns these four names and `scripts/make_cert.py` writes the pair.
// This is a third spelling, which is exactly the drift CLAUDE.md section 4
// warns about - and neither of those files is on this slice's write-list. So
// `test/endpoint.test.js` parses the four values back out of the Python module
// at run time and asserts they agree, which makes the drift a red test rather
// than a companion window pinning a certificate that is not there.

/** The certificate the companion pins. Public material. */
const CERT_NAME = "dashboard.cert.pem";

/**
 * Its private key, named so the pair has ONE spelling on this side.
 *
 * THERE IS DELIBERATELY NO `keyPath()` HELPER, and its absence is asserted by
 * `test/endpoint.test.js`. The companion window is a TLS CLIENT: it needs the
 * certificate to pin and never the key to present. A function here handing out
 * a private key path is a footgun aimed at a sibling slice, so the name is
 * published - to keep the pair's spelling in one place and let the test pin it
 * against Python - and the path is not.
 */
const KEY_NAME = "dashboard.key.pem";

/**
 * Overrides the default destination. MAY POINT ANYWHERE A USER CAN WRITE,
 * including inside a profile directory, which is why nothing built in this
 * module ever renders the resolved value.
 */
const CERT_DIR_ENV = "CLOCKSPEED_CERT_DIR";

/** The default destination, relative to the repository root. */
const DEFAULT_CERT_DIRNAME = "certs";

// ---------------------------------------------------------------------------
// Refusals. Each is a FIXED line and none is ever built from content.
// ---------------------------------------------------------------------------
//
// Three below are byte-identical to their `clockspeed/surface/config.py`
// counterparts. RECORD_UNREADABLE deliberately is NOT: the Python line ends
// "it belongs at config/ports.json", and a separator in a refusal is the exact
// shape the privacy arm of `test/endpoint.test.js` refuses categorically. The
// guidance survives without the separator.

const RECORD_UNREADABLE =
  "the port allocation record could not be read; it belongs in the project config directory";
const RECORD_MALFORMED =
  "the port allocation record does not carry an integer base port under the key 'base'";
const PORT_NOT_AN_INTEGER = "a declared dashboard port must be a base-ten integer";
const PORT_OUT_OF_RANGE = "a dashboard port must sit between 0 and 65535 inclusive";

/**
 * What a caller who passed something other than an `EndpointFault` is refused
 * with. A PROGRAMMING error rather than a configuration one, so it is a
 * `TypeError` - but it is a fixed line for the identical reason every line
 * above is one. Letting the lookup refuse instead would render the key, and the
 * one call this vocabulary exists to stop is `new EndpointError(String(path))`.
 * It quotes nothing it was handed.
 */
const FAULT_NOT_A_MEMBER = "an endpoint refusal must name an EndpointFault member";

/**
 * WHICH refusal happened, as a value no caller can author.
 *
 * A CLOSED VOCABULARY RATHER THAN A STRING PARAMETER, and the difference is the
 * whole control. The values are keys, deliberately not sentences: a member
 * whose value WAS the refusal would put the line in two places.
 */
const EndpointFault = Object.freeze({
  RECORD_UNREADABLE: "record_unreadable",
  RECORD_MALFORMED: "record_malformed",
  PORT_NOT_AN_INTEGER: "port_not_an_integer",
  PORT_OUT_OF_RANGE: "port_out_of_range",
});

/** Fault to the one line it is spoken as. Maps onto the constants above. */
const REFUSALS = Object.freeze(
  new Map([
    [EndpointFault.RECORD_UNREADABLE, RECORD_UNREADABLE],
    [EndpointFault.RECORD_MALFORMED, RECORD_MALFORMED],
    [EndpointFault.PORT_NOT_AN_INTEGER, PORT_NOT_AN_INTEGER],
    [EndpointFault.PORT_OUT_OF_RANGE, PORT_OUT_OF_RANGE],
  ])
);

const FAULT_MEMBERS = Object.freeze(new Set(Object.values(EndpointFault)));

/**
 * The one line an operator reads when the endpoint would not resolve.
 *
 * A MODULE-LEVEL FUNCTION RATHER THAN A METHOD: the text has ONE author, and
 * neither the throw site nor the process's handler has to render an exception
 * OBJECT to reach it. `String(caught)` is what its runtime type decides, and
 * today's runtime type is not a promise about tomorrow's - a widened catch and
 * the same spelling appends the path the call failed on.
 *
 * @param {string} fault A member of `EndpointFault`, never text.
 * @returns {string} The refusal, with no trailing newline.
 * @throws {TypeError} `fault` is not a member. CHECKED EXPLICITLY rather than
 *   left to the lookup, because a lookup failure that renders its key would
 *   leak the path through the guard rail's own failure path.
 */
function endpointRefusal(fault) {
  if (typeof fault !== "string" || !FAULT_MEMBERS.has(fault)) {
    throw new TypeError(FAULT_NOT_A_MEMBER);
  }
  return REFUSALS.get(fault);
}

/**
 * The dashboard endpoint could not be resolved.
 *
 * Carries one of the fixed lines above and never a path, a file name or a
 * fragment of whatever it refused - BY CONSTRUCTION rather than by the
 * discipline of each throw site.
 */
class EndpointError extends Error {
  /**
   * Build the refusal from the fault, and from nothing the caller wrote.
   *
   * @param {string} fault Which refusal happened.
   */
  constructor(fault) {
    const reason = endpointRefusal(fault);
    super(reason);
    this.name = "EndpointError";
    this.fault = fault;
    this.reason = reason;
  }
}

// ---------------------------------------------------------------------------
// Locations, all derived from this file rather than from a working directory
// ---------------------------------------------------------------------------

/**
 * The repository root, derived from this file's own location.
 *
 * Mirrors `repo_root()` in `clockspeed/surface/config.py`. Derived rather than
 * configured because a working directory is whatever the shell happened to be
 * in, and an absolute literal would carry an account name.
 *
 * @returns {string} The directory two levels above `shell/lib/`.
 */
function repoRoot() {
  return path.resolve(__dirname, "..", "..");
}

/**
 * Where the port allocation is recorded.
 *
 * @returns {string} The record under the repository root. Not required to
 *   exist; `dashboardPort` is what refuses a missing one.
 */
function portsRecordPath() {
  return path.join(repoRoot(), ...PORTS_RECORD_PARTS);
}

/**
 * Resolve where the certificate pair lives.
 *
 * @param {Object<string,string>} [env] The environment to read, or omitted for
 *   the real one. Passing an object is how a test overrides without mutating
 *   the process - the same seam `cert_dir(env)` offers on the Python side.
 * @returns {string} The declared directory, or `certs` beside the repository.
 *   Not created and not required to exist.
 */
function certDir(env) {
  const environment = env === undefined ? process.env : env;
  const declared = (environment[CERT_DIR_ENV] || "").trim();
  if (declared !== "") {
    return declared;
  }
  return path.join(repoRoot(), DEFAULT_CERT_DIRNAME);
}

/**
 * The certificate the companion window pins.
 *
 * @param {Object<string,string>} [env] The environment to read.
 * @returns {string} The certificate's path. Not required to exist - a missing
 *   certificate is the trust layer's refusal to make, not this module's.
 */
function certPath(env) {
  return path.join(certDir(env), CERT_NAME);
}

// ---------------------------------------------------------------------------
// The port
// ---------------------------------------------------------------------------

/**
 * Return the port, or refuse one the transport cannot carry.
 *
 * @param {number} value The candidate.
 * @returns {number} The port, unchanged.
 * @throws {EndpointError} It sits outside the transport's range. The message
 *   states the range and does NOT quote the value - a rejected value is
 *   caller-chosen text, and this module quotes none of it.
 */
function checkedPort(value) {
  if (!(value >= LOWEST_PORT && value <= HIGHEST_PORT)) {
    throw new EndpointError(EndpointFault.PORT_OUT_OF_RANGE);
  }
  return value;
}

/**
 * Read the allocated port out of the record that owns it.
 *
 * @param {string} [record] The record to read, or omitted for the real one.
 * @returns {number} The integer under `PORTS_RECORD_BASE_KEY`.
 * @throws {EndpointError} The record could not be read, did not parse, or
 *   carries no integer base. Two distinct fixed lines, so "the file is not
 *   there" and "the file is not what it should be" stay tellable apart -
 *   different faults with different remedies. Neither quotes the path or the
 *   content.
 */
function allocatedPort(record) {
  const target = record === undefined ? portsRecordPath() : record;
  let raw;
  try {
    raw = fs.readFileSync(target);
  } catch (cause) {
    throw new EndpointError(EndpointFault.RECORD_UNREADABLE);
  }

  let payload;
  try {
    // CHECKED RATHER THAN DECODED LOOSELY. `Buffer.toString("ascii")` masks the
    // high bit instead of refusing, so a record with a stray high byte would
    // parse as something subtly different from what is on disk. The Python side
    // gets this from `decode("ascii")` raising; here it has to be explicit.
    for (const byte of raw) {
      if (byte > MAX_ASCII) {
        throw new EndpointError(EndpointFault.RECORD_MALFORMED);
      }
    }
    payload = JSON.parse(raw.toString("ascii"));
  } catch (cause) {
    if (cause instanceof EndpointError) {
      throw cause;
    }
    throw new EndpointError(EndpointFault.RECORD_MALFORMED);
  }

  if (payload === null || typeof payload !== "object" || Array.isArray(payload)) {
    throw new EndpointError(EndpointFault.RECORD_MALFORMED);
  }
  const base = payload[PORTS_RECORD_BASE_KEY];
  // `typeof true === "boolean"`, so the Python side's explicit bool rejection
  // is not needed - but a float that happens to be whole is still not an
  // integer allocation, and `Number.isInteger` is what says so.
  if (!Number.isInteger(base)) {
    throw new EndpointError(EndpointFault.RECORD_MALFORMED);
  }
  return checkedPort(base);
}

/**
 * Resolve the port the dashboard listens on, in the stated order.
 *
 * An explicit request beats `PORT_ENV`, which beats the record. A declared
 * value that does not parse is REFUSED rather than skipped: silently ignoring
 * an override leaves the operator looking at a dashboard on a port they did not
 * ask for and cannot see was overridden.
 *
 * @param {Object} [options]
 * @param {number} [options.requested] An explicit port. Omitted means none.
 * @param {Object<string,string>} [options.env] The environment to read.
 * @param {string} [options.record] The allocation record.
 * @returns {number} The resolved port.
 * @throws {EndpointError} A declared value is not a base-ten integer, or sits
 *   outside the transport's range, or the record could not be resolved.
 */
function dashboardPort(options) {
  const { requested, env, record } = options === undefined ? {} : options;
  if (requested !== undefined) {
    if (!Number.isInteger(requested)) {
      throw new EndpointError(EndpointFault.PORT_NOT_AN_INTEGER);
    }
    return checkedPort(requested);
  }

  const environment = env === undefined ? process.env : env;
  const declared = (environment[PORT_ENV] || "").trim();
  if (declared !== "") {
    // ANCHORED, BASE TEN, AND DIGITS ONLY. `Number("0x1f90")` is 8080 and
    // `parseInt("12.5")` is 12; both would resolve an override the operator
    // did not write. An optional sign plus digits is the whole grammar, and
    // anything else is refused rather than coerced.
    if (!/^-?[0-9]+$/.test(declared)) {
      throw new EndpointError(EndpointFault.PORT_NOT_AN_INTEGER);
    }
    return checkedPort(Number.parseInt(declared, 10));
  }

  return allocatedPort(record);
}

// ---------------------------------------------------------------------------
// The whole endpoint
// ---------------------------------------------------------------------------

/**
 * The address the companion expects on the other end of the handshake.
 *
 * @returns {string} `LOOPBACK`, always.
 */
function expectedHost() {
  return LOOPBACK;
}

/**
 * Where the companion window points.
 *
 * @param {Object} [options] Same shape as `dashboardPort`.
 * @returns {string} The dashboard's origin, with a trailing slash.
 * @throws {EndpointError} The port could not be resolved.
 */
function dashboardUrl(options) {
  return `${SCHEME}://${expectedHost()}:${dashboardPort(options)}/`;
}

module.exports = {
  CERT_DIR_ENV,
  CERT_NAME,
  DEFAULT_CERT_DIRNAME,
  EndpointError,
  EndpointFault,
  FAULT_NOT_A_MEMBER,
  HIGHEST_PORT,
  KEY_NAME,
  LOWEST_PORT,
  PORTS_RECORD_BASE_KEY,
  PORTS_RECORD_PARTS,
  PORT_ENV,
  PORT_NOT_AN_INTEGER,
  PORT_OUT_OF_RANGE,
  RECORD_MALFORMED,
  RECORD_UNREADABLE,
  SCHEME,
  certDir,
  certPath,
  dashboardPort,
  dashboardUrl,
  endpointRefusal,
  expectedHost,
  portsRecordPath,
  repoRoot,
};
