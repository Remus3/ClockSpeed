"use strict";

// CS-602 repair slice R1 - tests for the verdict-to-integer mapping.
//
// WHY THIS FILE EXISTS, STATED AS THE DEFECT IT CLOSES. Until this slice the
// mapping lived inside shell/main.js, and main.js requires electron, so nothing
// could load it. The consequence was measured rather than supposed: with the
// mapping unreachable, EVERY one of these edits to main.js left the whole gate
// green - the shell suite at 63 passed, node --test at 174 passing, the drift
// guard clean and the commit gate passing:
//
//   callback(codeFor(verdict))    ->  callback(0)     blanket accept, every host
//   [trust.DEFER, -3]             ->  [trust.DEFER, 0]
//   [trust.REFUSE_MISMATCH, -2]   ->  [trust.REFUSE_MISMATCH, 0]
//   [trust.REFUSE_NO_PIN, -2]     ->  [trust.REFUSE_NO_PIN, 0]
//
// The root cause was PLACEMENT and never impossibility. The mapping is a total
// function from five strings to three integers: no electron, no display, no
// binary, nothing that cannot run on the tier-2 lane in a millisecond. Moving
// it to shell/lib/verdict.js is the whole repair, and this file is what makes
// the move worth anything.
//
// THE INTEGERS ARE SPELLED HERE AS LITERALS AND ARE NEVER IMPORTED. A test that
// reads the expected value out of the module under test asserts that a number
// equals itself. CS-605 closed on the neighbouring failure - a table imported
// from the source let a deletion in the source delete the test case and stay
// green - so the five verdict strings are spelled here too, and agreement with
// trust.js is asserted as its own arm rather than assumed by importing.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const trust = require("../lib/trust.js");
const verdicts = require("../lib/verdict.js");

// ---------------------------------------------------------------------------
// The table, spelled in this file
// ---------------------------------------------------------------------------

// The accepting code. Named rather than repeated, because it is the one value
// every arm below is really about: it is the code that accepts the certificate
// AND switches Certificate Transparency verification off for the session, so it
// is the code exactly one verdict may reach.
const ACCEPT = 0;

// Chromium net error codes. Both are negative, which is the property the
// "no verdict but TRUST accepts" arms lean on: in that space 0 is the only
// success value and every negative is an error, so a mapping that drifted to
// some other negative would still refuse rather than trust.
const USE_CHROMIUM_RESULT = -3;
const REFUSE = -2;

// Verdict string, expected integer. Every pair is a literal on both sides.
const EXPECTED = [
  ["TRUST", ACCEPT],
  ["DEFER", USE_CHROMIUM_RESULT],
  ["REFUSE_NO_PIN", REFUSE],
  ["REFUSE_NO_CERT", REFUSE],
  ["REFUSE_MISMATCH", REFUSE],
];

const ALL_VERDICTS = EXPECTED.map(([verdict]) => verdict);

// ---------------------------------------------------------------------------
// a. The five mappings, one arm each, by value
// ---------------------------------------------------------------------------

// One test per pair rather than one loop over the table. A single looping arm
// dies once when any pair breaks and reports the first failure only; five arms
// name which mapping moved, which is the difference between "the map changed"
// and "DEFER now accepts".

test("TRUST maps to the accepting code 0", () => {
  assert.equal(verdicts.codeFor("TRUST"), 0);
});

test("DEFER maps to -3, and never to the accepting code", () => {
  assert.equal(verdicts.codeFor("DEFER"), -3);
  assert.notEqual(verdicts.codeFor("DEFER"), 0);
});

test("REFUSE_NO_PIN maps to -2", () => {
  assert.equal(verdicts.codeFor("REFUSE_NO_PIN"), -2);
});

test("REFUSE_NO_CERT maps to -2", () => {
  assert.equal(verdicts.codeFor("REFUSE_NO_CERT"), -2);
});

test("REFUSE_MISMATCH maps to -2", () => {
  assert.equal(verdicts.codeFor("REFUSE_MISMATCH"), -2);
});

// ---------------------------------------------------------------------------
// b. The population property - exactly one verdict may accept
// ---------------------------------------------------------------------------

test("TRUST is the ONLY verdict that maps to the accepting code", () => {
  const accepting = ALL_VERDICTS.filter((verdict) => verdicts.codeFor(verdict) === ACCEPT);
  assert.deepEqual(accepting, ["TRUST"]);
});

test("every REFUSE_ verdict maps to a negative number", () => {
  const refusals = ALL_VERDICTS.filter((verdict) => verdict.startsWith("REFUSE_"));
  assert.equal(refusals.length, 3, "the refusal population changed; update this file");

  const wrong = refusals.filter((verdict) => !(verdicts.codeFor(verdict) < 0));
  assert.deepEqual(wrong, [], "a refusal verdict does not map to a negative code");
});

test("DEFER maps to a negative number, so an unhonoured -3 fails closed", () => {
  // The -3 meaning "use Chromium's own result" rests on Electron's prose
  // documentation and is absent from the shipped typings - ADR 0014 records
  // that as documented but not type-checked. This arm pins the fallback
  // argument rather than the claim: the parameter is a Chromium net error code,
  // where 0 alone is success, so a -3 an Electron build did not interpret as
  // documented refuses the connection instead of trusting it.
  assert.ok(verdicts.codeFor("DEFER") < 0);
});

test("no verdict maps to anything but the three known codes", () => {
  const codes = [...new Set(ALL_VERDICTS.map((verdict) => verdicts.codeFor(verdict)))].sort(
    (left, right) => left - right,
  );
  assert.deepEqual(codes, [-3, -2, 0]);
});

// ---------------------------------------------------------------------------
// c. An unknown verdict is loud, never a default
// ---------------------------------------------------------------------------

test("an unknown verdict throws UnknownVerdictError rather than defaulting", () => {
  assert.throws(() => verdicts.codeFor("TRUST_ME"), verdicts.UnknownVerdictError);
  assert.throws(() => verdicts.codeFor(""), verdicts.UnknownVerdictError);
  assert.throws(() => verdicts.codeFor(undefined), verdicts.UnknownVerdictError);
  assert.throws(() => verdicts.codeFor(null), verdicts.UnknownVerdictError);
  assert.throws(() => verdicts.codeFor(0), verdicts.UnknownVerdictError);
});

test("the thrown error names itself and does not carry a code", () => {
  // A default written as a number in the throw path would be a second, quieter
  // place an integer reaches the callback - which is the one property the
  // split into this module exists to keep.
  let caught = null;
  try {
    verdicts.codeFor("NOT_A_VERDICT");
  } catch (err) {
    caught = err;
  }
  assert.ok(caught instanceof Error);
  assert.equal(caught.name, "UnknownVerdictError");
  assert.equal(typeof caught.code, "undefined");
});

// ---------------------------------------------------------------------------
// d. The callback-safe wrapper - a throw here would HANG the load
// ---------------------------------------------------------------------------

// WHY THERE ARE TWO FUNCTIONS AND NOT ONE. codeFor throws, which is right for a
// pure module: a sixth verdict must be loud rather than silently mapped. But
// this mapping is consumed inside Electron's verify callback, and a callback
// that throws never calls back at all - the page HANGS instead of being
// refused. shell/lib/trust.js records that hazard in its own header and ADR
// 0014 records it again. So the strict function is what the tree is graded on,
// and codeForOrRefuse is the one the callback consumes: the SAME map, with an
// unknown verdict ending at a refusal read back out of that map rather than
// written as a literal.

test("codeForOrRefuse agrees with codeFor on every known verdict", () => {
  const disagreements = ALL_VERDICTS.filter(
    (verdict) => verdicts.codeForOrRefuse(verdict) !== verdicts.codeFor(verdict),
  );
  assert.deepEqual(disagreements, []);
});

test("codeForOrRefuse turns an unknown verdict into a refusal, never an accept", () => {
  for (const unknown of ["TRUST_ME", "", undefined, null, 0, {}]) {
    const code = verdicts.codeForOrRefuse(unknown);
    assert.notEqual(code, ACCEPT, `an unknown verdict reached the accepting code: ${unknown}`);
    assert.ok(code < 0, `an unknown verdict did not refuse: ${unknown}`);
  }
});

test("codeForOrRefuse answers the refusal code exactly, not merely something negative", () => {
  assert.equal(verdicts.codeForOrRefuse("NOT_A_VERDICT"), verdicts.codeFor("REFUSE_MISMATCH"));
});

test("codeForOrRefuse never throws, for any input at all", () => {
  const hostile = [
    undefined,
    null,
    0,
    -1,
    "",
    "TRUST ",
    " TRUST",
    "trust",
    {},
    [],
    Symbol("TRUST"),
    () => "TRUST",
  ];
  for (const input of hostile) {
    assert.doesNotThrow(() => verdicts.codeForOrRefuse(input), `threw on ${String(input)}`);
  }
});

test("the mapping is case sensitive and does not trim", () => {
  // A near-miss must be an unknown verdict rather than a quiet TRUST.
  for (const near of ["trust", "Trust", "TRUST ", " TRUST", "TRUST\n"]) {
    assert.throws(() => verdicts.codeFor(near), verdicts.UnknownVerdictError);
    assert.notEqual(verdicts.codeForOrRefuse(near), ACCEPT);
  }
});

// ---------------------------------------------------------------------------
// e. The seam - this file's five strings are trust.js's five strings
// ---------------------------------------------------------------------------

test("the five verdict strings spelled here are exactly what trust.js exports", () => {
  const exported = [
    trust.TRUST,
    trust.DEFER,
    trust.REFUSE_NO_PIN,
    trust.REFUSE_NO_CERT,
    trust.REFUSE_MISMATCH,
  ];
  assert.deepEqual(exported, ALL_VERDICTS);
});

test("every verdict trust.decide can return is in the map", () => {
  // Driven through the real decision function rather than over the exported
  // constants, so a verdict trust.js can PRODUCE but forgot to EXPORT would
  // still be caught here.
  const produced = new Set([
    trust.decide({}),
    trust.decide({ pinnedDer: Buffer.from("ab"), hostname: "a", expectedHost: "b" }),
    trust.decide({ pinnedDer: Buffer.from("ab"), hostname: "a", expectedHost: "a" }),
    trust.decide({
      pinnedDer: Buffer.from("ab"),
      hostname: "a",
      expectedHost: "a",
      presentedDer: Buffer.from("abc"),
    }),
    trust.decide({
      pinnedDer: Buffer.from("ab"),
      hostname: "a",
      expectedHost: "a",
      presentedDer: Buffer.from("ab"),
    }),
  ]);
  assert.equal(produced.size, 5, `trust.decide produced ${produced.size} distinct verdicts`);

  const unmapped = [...produced].filter((verdict) => !ALL_VERDICTS.includes(verdict));
  assert.deepEqual(unmapped, [], "trust.decide can return a verdict this map does not hold");
});

// ---------------------------------------------------------------------------
// f. The exported map cannot drift from the function
// ---------------------------------------------------------------------------

test("the exported mapping holds exactly the five verdicts and agrees with codeFor", () => {
  assert.ok(verdicts.VERDICT_CODES instanceof Map);
  assert.deepEqual([...verdicts.VERDICT_CODES.keys()].sort(), [...ALL_VERDICTS].sort());

  const disagreements = ALL_VERDICTS.filter(
    (verdict) => verdicts.VERDICT_CODES.get(verdict) !== verdicts.codeFor(verdict),
  );
  assert.deepEqual(disagreements, []);
});

test("the exported mapping matches this file's table pair for pair", () => {
  const actual = EXPECTED.map(([verdict]) => [verdict, verdicts.VERDICT_CODES.get(verdict)]);
  assert.deepEqual(actual, EXPECTED);
});

// ---------------------------------------------------------------------------
// g. Purity and character set - the properties that let this run on tier 2
// ---------------------------------------------------------------------------

const VERDICT_PATH = path.join(__dirname, "..", "lib", "verdict.js");

test("verdict.js requires electron nowhere, and touches no filesystem", () => {
  // THE PROPERTY THAT MADE THE DEFECT POSSIBLE, ASSERTED SO IT STAYS FIXED. The
  // mapping was ungradeable only because it sat in a file that imports
  // electron. If this module ever acquires such an import it becomes
  // unloadable on the every-push lane and this suite goes quiet - which is the
  // original defect returning under a new name.
  const source = fs.readFileSync(VERDICT_PATH, "utf8");
  assert.ok(!/require\(\s*["'](electron|node:fs|fs|node:path|path)["']\s*\)/.test(source));
});

test("verdict.js is 7-bit ASCII with no carriage returns", () => {
  const bytes = fs.readFileSync(VERDICT_PATH);
  assert.equal(bytes.includes(0x0d), false, "verdict.js must be LF, never CRLF");
  for (const byte of bytes) {
    assert.ok(byte <= 0x7e, `non-ASCII byte 0x${byte.toString(16)} in verdict.js`);
  }
});
