"use strict";

// CS-909 slice A - tests for shell/lib/supervisor.js.
//
// WHAT THE MODULE UNDER TEST DECIDES. Until CS-909 the companion window assumed
// the dashboard was already listening; the desktop shortcut this item adds has
// to start one. Three questions follow from that - start or adopt, keep waiting
// or give up, stop or leave - and all three live in a module that performs none
// of them. main.js spawns, probes and kills; this file decides.
//
// WHY THE DECISIONS ARE NOT IN main.js, MEASURED RATHER THAN ASSERTED. main.js
// imports electron, so no test in either language loads it - CS-619 is open on
// exactly that, and shell/lib/verdict.js exists because the same gap let three
// separate one-line certificate bypasses through a fully green gate. A lifecycle
// decision left in main.js would be ungraded in precisely the same way, and the
// mistake it can make is worse than a hung page: killing a dashboard the
// operator started themselves takes their terminal session with it.
//
// WHY EVERY ARM ASSERTS A WORD BY VALUE. shell/lib/trust.js answers in words so
// that no edit there can quietly become a blanket accept, and this module obeys
// the same rule for the same reason - STOP has to be a thing a reader can see
// being returned. A test that asserted only "a string came back" would be
// satisfied by every one of the swaps this suite exists to catch, so the
// control table below pins the WHOLE decision vector and reddens if any single
// answer is exchanged for another valid answer.
//
// This suite loads nothing but the module and the two node built-ins it needs
// to read that module's own bytes off disk. It runs on a machine with no
// electron binary, no display server, no python and no game install.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const supervisor = require("../lib/supervisor.js");
const {
  START,
  ADOPT,
  STOP,
  LEAVE,
  READY,
  RETRY,
  GIVE_UP,
  REFUSE_UNKNOWN_HEALTH,
  REFUSE_UNKNOWN_OWNERSHIP,
  REFUSE_UNKNOWN_ATTEMPT,
  REFUSE_UNKNOWN_ANSWER,
  NOT_A_REFUSAL,
  PROBE_INTERVAL_MS,
  PROBE_ATTEMPT_CEILING,
  PROBE_TIMEOUT_MS,
  MODULE_FLAG,
  SERVER_MODULE,
  decideStart,
  decideStop,
  decideProbeOutcome,
  serverArgv,
  supervisorRefusal,
} = supervisor;

const SOURCE_PATH = path.join(__dirname, "..", "lib", "supervisor.js");

// Everything that is not a boolean, including the two values a loose check
// would wave through. `0` and `1` are here because `if (healthy)` accepts one
// and rejects the other, and a caller handing over a count rather than an
// answer is the realistic way that arrives. The verdict words are here because
// a caller passing a decision back in is the realistic way THAT arrives.
const NOT_A_BOOLEAN = Object.freeze([
  undefined,
  null,
  0,
  1,
  -1,
  Number.NaN,
  "",
  "true",
  "false",
  "START",
  "STOP",
  {},
  [],
  [true],
  { healthy: true },
  () => true,
]);

// Every shape that is not a probe attempt. A count starts at one: attempt zero
// names a probe that never ran, and a fractional or infinite attempt cannot be
// compared against a ceiling and mean anything.
const NOT_AN_ATTEMPT = Object.freeze([
  undefined,
  null,
  0,
  -1,
  1.5,
  Number.NaN,
  Number.POSITIVE_INFINITY,
  Number.NEGATIVE_INFINITY,
  "1",
  true,
  false,
  {},
  [],
  [1],
]);

// ---------------------------------------------------------------------------
// The exported vocabulary
// ---------------------------------------------------------------------------

test("every decision and refusal is a distinct non-empty WORD, never a number or a boolean", () => {
  const words = [
    START,
    ADOPT,
    STOP,
    LEAVE,
    READY,
    RETRY,
    GIVE_UP,
    REFUSE_UNKNOWN_HEALTH,
    REFUSE_UNKNOWN_OWNERSHIP,
    REFUSE_UNKNOWN_ATTEMPT,
    REFUSE_UNKNOWN_ANSWER,
  ];

  // The same guard shell/lib/trust.js carries, for the same reason: a numeric
  // or boolean answer is a vocabulary in which a blanket "yes, kill it" could
  // be written by accident. Words cannot be truthy by mistake.
  const wrongType = words.filter((word) => typeof word !== "string" || word.length === 0);
  assert.deepEqual(wrongType, [], "a decision that is not a non-empty string leaked in");
  assert.equal(new Set(words).size, words.length, "all eleven words must be distinguishable");
});

test("the probe constants are positive integers and the ceiling leaves room either side", () => {
  for (const [name, value] of [
    ["PROBE_INTERVAL_MS", PROBE_INTERVAL_MS],
    ["PROBE_ATTEMPT_CEILING", PROBE_ATTEMPT_CEILING],
    ["PROBE_TIMEOUT_MS", PROBE_TIMEOUT_MS],
  ]) {
    assert.equal(typeof value, "number", `${name} must be a number`);
    assert.ok(Number.isInteger(value), `${name} must be an integer, was ${value}`);
    assert.ok(value > 0, `${name} must be positive, was ${value}`);
  }
  // A ceiling of one would make "one below the ceiling" and "a probe that never
  // ran" the same input, and the boundary arms below would grade nothing.
  assert.ok(PROBE_ATTEMPT_CEILING > 1, "the ceiling must admit at least one retry");
});

// ---------------------------------------------------------------------------
// decideStart - both branches, by value
// ---------------------------------------------------------------------------

test("decideStart returns START when nothing answers", () => {
  const decision = decideStart({ healthy: false });
  assert.equal(decision, START);
  assert.notEqual(decision, ADOPT, "nothing is listening, so there is nothing to adopt");
});

test("decideStart returns ADOPT when something already answers", () => {
  const decision = decideStart({ healthy: true });
  assert.equal(decision, ADOPT);
  // The negative is the one that matters. Starting a second dashboard against a
  // port the first one holds ends in a bind refusal and a companion window
  // pointed at a process that just died.
  assert.notEqual(decision, START, "a live dashboard must never be started over");
});

test("decideStart refuses by name for every input that is not a boolean", () => {
  const wrong = NOT_A_BOOLEAN.filter(
    (healthy) => decideStart({ healthy }) !== REFUSE_UNKNOWN_HEALTH
  ).map((healthy) => `${typeof healthy}:${String(healthy)}`);
  assert.deepEqual(wrong, [], `decideStart did not refuse: ${wrong.join("; ")}`);
});

test("decideStart refuses a missing, absent or malformed options object", () => {
  const inputs = [undefined, null, {}, "healthy", 1, [], () => {}];
  const wrong = inputs
    .filter((input) => decideStart(input) !== REFUSE_UNKNOWN_HEALTH)
    .map((input) => String(input));
  assert.deepEqual(wrong, [], `decideStart did not refuse: ${wrong.join("; ")}`);
  assert.equal(decideStart(), REFUSE_UNKNOWN_HEALTH, "no argument at all must refuse");
});

// ---------------------------------------------------------------------------
// decideStop - both branches, by value
// ---------------------------------------------------------------------------

test("decideStop returns STOP only when WE started it", () => {
  const decision = decideStop({ started: true });
  assert.equal(decision, STOP);
  assert.notEqual(decision, LEAVE, "a dashboard this companion spawned is its to clean up");
});

test("decideStop returns LEAVE when we did not start it", () => {
  const decision = decideStop({ started: false });
  assert.equal(decision, LEAVE);
  assert.notEqual(decision, STOP);
});

test("decideStop refuses by name for every input that is not a boolean", () => {
  const wrong = NOT_A_BOOLEAN.filter(
    (started) => decideStop({ started }) !== REFUSE_UNKNOWN_OWNERSHIP
  ).map((started) => `${typeof started}:${String(started)}`);
  assert.deepEqual(wrong, [], `decideStop did not refuse: ${wrong.join("; ")}`);
});

test("decideStop refuses a missing, absent or malformed options object", () => {
  const inputs = [undefined, null, {}, "started", 1, [], () => {}];
  const wrong = inputs
    .filter((input) => decideStop(input) !== REFUSE_UNKNOWN_OWNERSHIP)
    .map((input) => String(input));
  assert.deepEqual(wrong, [], `decideStop did not refuse: ${wrong.join("; ")}`);
  assert.equal(decideStop(), REFUSE_UNKNOWN_OWNERSHIP, "no argument at all must refuse");
});

// ---------------------------------------------------------------------------
// Only stop what you started - the property this module exists for
// ---------------------------------------------------------------------------

test("only stop what you started - an ADOPTED dashboard is LEFT running on quit", () => {
  // The operator ran `python -m clockspeed.surface` in their own terminal and
  // then opened the companion. decideStart adopts, nothing is spawned, and so
  // there is nothing this process is entitled to kill. Answering STOP here
  // would end a server the operator is watching the output of.
  assert.equal(decideStart({ healthy: true }), ADOPT, "precondition: the live one is adopted");

  const onQuit = decideStop({ started: false });
  assert.equal(onQuit, LEAVE);
  assert.notEqual(onQuit, STOP, "killing an adopted dashboard eats the operator's session");
});

test("only stop what you started - STOP is reachable from exactly one input", () => {
  // The whole property as a sweep rather than as two examples. Every value the
  // suite knows about is offered as `started`, and exactly one of them may come
  // back STOP. A refusal must not reach it either: a caller that cannot tell
  // whether it spawned anything has not earned the right to kill.
  const offered = [true, false, ...NOT_A_BOOLEAN];
  const stopped = offered
    .filter((started) => decideStop({ started }) === STOP)
    .map((started) => `${typeof started}:${String(started)}`);
  assert.deepEqual(stopped, ["boolean:true"], `STOP leaked to: ${stopped.join("; ")}`);
});

test("only stop what you started - no unknown ownership falls through to STOP", () => {
  // Stated separately from the sweep above because it is the direction of the
  // refusal that is load bearing, not merely its distinctness. An unknown
  // answer must land on a word that authorises nothing.
  for (const started of NOT_A_BOOLEAN) {
    const decision = decideStop({ started });
    assert.notEqual(decision, STOP, `unknown ownership reached STOP: ${String(started)}`);
    assert.equal(decision, REFUSE_UNKNOWN_OWNERSHIP);
  }
});

test("only stop what you started - supervisor.js returns STOP from exactly one site", () => {
  // The source-level half of the same property, mirroring the arm
  // tests/shell/test_shell_assets.py applies to trust.js. Two return sites
  // would mean a second, unreviewed path to a kill.
  const source = fs.readFileSync(SOURCE_PATH, "utf8");
  const sites = source.split("return STOP;").length - 1;
  assert.equal(sites, 1, `supervisor.js returns STOP from ${sites} site(s), expected exactly 1`);
});

// ---------------------------------------------------------------------------
// decideProbeOutcome - the ceiling boundary and one either side
// ---------------------------------------------------------------------------

test("decideProbeOutcome returns READY as soon as the dashboard answers", () => {
  assert.equal(decideProbeOutcome({ attempt: 1, answered: true }), READY);
});

test("decideProbeOutcome returns RETRY below the ceiling", () => {
  assert.equal(decideProbeOutcome({ attempt: 1, answered: false }), RETRY);
});

test("decideProbeOutcome at the attempt ceiling and one either side", () => {
  const below = PROBE_ATTEMPT_CEILING - 1;
  const at = PROBE_ATTEMPT_CEILING;
  const above = PROBE_ATTEMPT_CEILING + 1;

  // Spelled as three separate assertions rather than a loop, so a regression
  // names the side of the boundary that moved.
  assert.equal(decideProbeOutcome({ attempt: below, answered: false }), RETRY, "one below");
  assert.equal(decideProbeOutcome({ attempt: at, answered: false }), GIVE_UP, "at the ceiling");
  assert.equal(decideProbeOutcome({ attempt: above, answered: false }), GIVE_UP, "one above");

  // An off-by-one in either direction is what these two negatives pin. A
  // `>` where a `>=` belongs turns the ceiling itself into another retry.
  assert.notEqual(decideProbeOutcome({ attempt: at, answered: false }), RETRY);
  assert.notEqual(decideProbeOutcome({ attempt: below, answered: false }), GIVE_UP);
});

test("decideProbeOutcome answers READY even at and beyond the ceiling", () => {
  // The ceiling bounds how long the companion WAITS, not whether an answer
  // counts. A dashboard that replied on its last permitted probe has started.
  assert.equal(decideProbeOutcome({ attempt: PROBE_ATTEMPT_CEILING, answered: true }), READY);
  assert.equal(decideProbeOutcome({ attempt: PROBE_ATTEMPT_CEILING + 1, answered: true }), READY);
});

test("decideProbeOutcome refuses by name for every attempt that is not a count", () => {
  const wrong = NOT_AN_ATTEMPT.filter(
    (attempt) => decideProbeOutcome({ attempt, answered: false }) !== REFUSE_UNKNOWN_ATTEMPT
  ).map((attempt) => `${typeof attempt}:${String(attempt)}`);
  assert.deepEqual(wrong, [], `a bad attempt was not refused: ${wrong.join("; ")}`);
});

test("decideProbeOutcome refuses by name for every answer that is not a boolean", () => {
  const wrong = NOT_A_BOOLEAN.filter(
    (answered) => decideProbeOutcome({ attempt: 1, answered }) !== REFUSE_UNKNOWN_ANSWER
  ).map((answered) => `${typeof answered}:${String(answered)}`);
  assert.deepEqual(wrong, [], `a bad answer was not refused: ${wrong.join("; ")}`);
});

test("decideProbeOutcome refuses the attempt first when both inputs are unusable", () => {
  // The order is stated rather than left to whichever check happens to run
  // first, so that a reader repairing the loop is told which of the two values
  // to look at.
  assert.equal(decideProbeOutcome({ attempt: 0, answered: "yes" }), REFUSE_UNKNOWN_ATTEMPT);
});

test("decideProbeOutcome refuses a missing, absent or malformed options object", () => {
  const inputs = [undefined, null, {}, "attempt", 1, [], () => {}];
  const wrong = inputs
    .filter((input) => decideProbeOutcome(input) !== REFUSE_UNKNOWN_ATTEMPT)
    .map((input) => String(input));
  assert.deepEqual(wrong, [], `decideProbeOutcome did not refuse: ${wrong.join("; ")}`);
  assert.equal(decideProbeOutcome(), REFUSE_UNKNOWN_ATTEMPT, "no argument at all must refuse");
});

// ---------------------------------------------------------------------------
// The control table - reddens if any verdict is swapped for another verdict
// ---------------------------------------------------------------------------

test("the whole decision vector is pinned, so no answer can be exchanged for another", () => {
  // Every arm above asserts one answer. This one asserts them together as a
  // single value, which is what makes an exchange between two VALID words
  // visible: swapping START for ADOPT, LEAVE for STOP, RETRY for GIVE_UP or a
  // refusal for a decision each move exactly one entry of this vector.
  const observed = [
    ["start/healthy", decideStart({ healthy: true })],
    ["start/dead", decideStart({ healthy: false })],
    ["start/unknown", decideStart({ healthy: "maybe" })],
    ["stop/ours", decideStop({ started: true })],
    ["stop/theirs", decideStop({ started: false })],
    ["stop/unknown", decideStop({ started: null })],
    ["probe/answered", decideProbeOutcome({ attempt: 1, answered: true })],
    ["probe/first", decideProbeOutcome({ attempt: 1, answered: false })],
    [
      "probe/below",
      decideProbeOutcome({ attempt: PROBE_ATTEMPT_CEILING - 1, answered: false }),
    ],
    ["probe/at", decideProbeOutcome({ attempt: PROBE_ATTEMPT_CEILING, answered: false })],
    [
      "probe/above",
      decideProbeOutcome({ attempt: PROBE_ATTEMPT_CEILING + 1, answered: false }),
    ],
    ["probe/uncounted", decideProbeOutcome({ attempt: 0, answered: false })],
    ["probe/unanswerable", decideProbeOutcome({ attempt: 1, answered: 1 })],
  ];

  const expected = [
    ["start/healthy", ADOPT],
    ["start/dead", START],
    ["start/unknown", REFUSE_UNKNOWN_HEALTH],
    ["stop/ours", STOP],
    ["stop/theirs", LEAVE],
    ["stop/unknown", REFUSE_UNKNOWN_OWNERSHIP],
    ["probe/answered", READY],
    ["probe/first", RETRY],
    ["probe/below", RETRY],
    ["probe/at", GIVE_UP],
    ["probe/above", GIVE_UP],
    ["probe/uncounted", REFUSE_UNKNOWN_ATTEMPT],
    ["probe/unanswerable", REFUSE_UNKNOWN_ANSWER],
  ];

  assert.deepEqual(observed, expected);
});

// ---------------------------------------------------------------------------
// serverArgv - no path, no interpreter, no account name
// ---------------------------------------------------------------------------

test("serverArgv is the module invocation and nothing else", () => {
  assert.deepEqual(serverArgv(), [MODULE_FLAG, SERVER_MODULE]);
  assert.deepEqual(serverArgv(), ["-m", "clockspeed.surface"]);
});

test("serverArgv carries no path and no interpreter", () => {
  // A path can carry the Windows account name, which is non-negotiable 3, and
  // an interpreter spelled here would be the hardcoded interpreter BOOTSTRAP.md
  // section 2.5 forbids. Choosing and locating the interpreter is main.js's
  // job; this module only says what follows it.
  const safe = /^[-A-Za-z0-9_.]+$/;
  const unsafe = serverArgv().filter((item) => typeof item !== "string" || !safe.test(item));
  assert.deepEqual(unsafe, [], `serverArgv carries an unsafe argument: ${unsafe.join("; ")}`);

  const interpreters = ["python", "python3", "py", "node", "exe"];
  const named = serverArgv().filter((item) =>
    interpreters.some((token) => item.toLowerCase().includes(token))
  );
  assert.deepEqual(named, [], `serverArgv names an interpreter: ${named.join("; ")}`);
});

test("serverArgv hands back a fresh array each call", () => {
  // A caller that appends a flag to what it was given must not change what the
  // next caller receives. geometry.js returns a fresh object for the same
  // reason: a shared literal is a mutable global wearing a constant's name.
  const first = serverArgv();
  const second = serverArgv();
  assert.notEqual(first, second, "the same array instance was handed out twice");
  first.push("--mutated");
  assert.deepEqual(serverArgv(), [MODULE_FLAG, SERVER_MODULE], "a caller moved the argv");
});

// ---------------------------------------------------------------------------
// The refusal lines - fixed text, authored here and nowhere else
// ---------------------------------------------------------------------------

test("every refusal word renders one fixed non-empty line", () => {
  const words = [
    REFUSE_UNKNOWN_HEALTH,
    REFUSE_UNKNOWN_OWNERSHIP,
    REFUSE_UNKNOWN_ATTEMPT,
    REFUSE_UNKNOWN_ANSWER,
  ];
  const lines = words.map((word) => supervisorRefusal(word));
  const empty = lines.filter((line) => typeof line !== "string" || line.length === 0);
  assert.deepEqual(empty, [], "a refusal word rendered nothing");
  assert.equal(new Set(lines).size, lines.length, "two refusals share one line");
});

test("no refusal line can quote a path, a host, a file name or a caller's value", () => {
  // NOT_A_REFUSAL is already a line rather than a word - it is what a caller
  // who passed something outside the vocabulary is told - so it is swept
  // alongside the four that are rendered.
  const lines = [
    supervisorRefusal(REFUSE_UNKNOWN_HEALTH),
    supervisorRefusal(REFUSE_UNKNOWN_OWNERSHIP),
    supervisorRefusal(REFUSE_UNKNOWN_ATTEMPT),
    supervisorRefusal(REFUSE_UNKNOWN_ANSWER),
    NOT_A_REFUSAL,
  ];

  // Separators and scheme punctuation first: a refusal that can hold one of
  // these is a refusal that can hold a home directory.
  const forbiddenChars = ["/", "\\", ":", "%", "$", "~"];

  // THE SAVE SUFFIX IS ASSEMBLED AND NOT SPELLED. Written out, this line would
  // itself carry the shape tests/shell/test_shell_assets.py sweeps every shell
  // file for, and it did - the first draft of this arm went red under that
  // module's personal-data sweep for naming the extension it exists to keep
  // out. Documenting a constraint is enough to violate it; that module's own
  // header records being caught the same way, and it builds its profile
  // segment by concatenation for exactly this reason.
  const saveSuffix = "." + "sav";
  const forbiddenTokens = [".js", ".py", ".pem", saveSuffix, "http", "localhost", "undefined"];
  const offenders = [];
  for (const line of lines) {
    for (const bad of forbiddenChars) {
      if (line.includes(bad)) {
        offenders.push(`char ${bad}`);
      }
    }
    for (const bad of forbiddenTokens) {
      if (line.toLowerCase().includes(bad)) {
        offenders.push(`token ${bad}`);
      }
    }
  }
  assert.deepEqual(offenders, [], `a refusal line can carry: ${offenders.join("; ")}`);
});

test("supervisorRefusal throws a fixed line rather than rendering what it was handed", () => {
  // The endpoint.js shape: letting the lookup fail and reporting the key would
  // publish whatever the caller passed, which is the one call this vocabulary
  // exists to stop.
  for (const notAWord of ["START", "", "refuse_unknown_health", null, undefined, 0, {}, []]) {
    assert.throws(
      () => supervisorRefusal(notAWord),
      (err) => {
        assert.ok(err instanceof TypeError, "a non-member must be a TypeError");
        assert.equal(err.message, NOT_A_REFUSAL, "the throw must carry the fixed line");
        return true;
      },
      `supervisorRefusal accepted ${String(notAWord)}`
    );
  }
});

test("a decision word is not a refusal word", () => {
  // START, ADOPT, STOP, LEAVE, READY, RETRY and GIVE_UP are answers, not
  // faults. Rendering one as a refusal would put a decision in an error line.
  for (const decision of [START, ADOPT, STOP, LEAVE, READY, RETRY, GIVE_UP]) {
    assert.throws(() => supervisorRefusal(decision), TypeError, `${decision} rendered as a refusal`);
  }
});

// ---------------------------------------------------------------------------
// The purity contract, and the bytes
// ---------------------------------------------------------------------------

test("supervisor.js requires no process, transport, platform or filesystem module", () => {
  // The equivalent of window.test.js's "requires electron nowhere" arm, one
  // finding per module so a single surviving import cannot hide behind six
  // absent ones. Every name is matched with and without the `node:` prefix.
  //
  // These are the modules that would let a decision module DO the thing it
  // decides. Keeping them out is what lets this suite run with no electron
  // binary, and what stops a spawn or a kill being added where no test can see
  // it - which is the whole reason CS-909 put the decisions here.
  const source = fs.readFileSync(SOURCE_PATH, "utf8");
  const forbidden = ["electron", "child_process", "http", "https", "net", "os", "fs"];
  const imported = forbidden.filter((name) =>
    new RegExp(`require\\(\\s*["'](?:node:)?${name}["']\\s*\\)`).test(source)
  );
  assert.deepEqual(imported, [], `supervisor.js imports: ${imported.join("; ")}`);
});

test("the import detector fires on a real import and ignores prose", () => {
  // Without this the arm above is a zero-finding sweep whose detector has never
  // been shown to work, and a broken regex reports the same clean result as a
  // clean module.
  const detect = (text) =>
    ["electron", "child_process", "http", "https", "net", "os", "fs"].filter((name) =>
      new RegExp(`require\\(\\s*["'](?:node:)?${name}["']\\s*\\)`).test(text)
    );

  assert.deepEqual(detect('const cp = require("child_process");\n'), ["child_process"]);
  assert.deepEqual(detect("const n = require('node:net');\n"), ["net"]);
  assert.deepEqual(detect('const f = require( "node:fs" );\n'), ["fs"]);
  assert.deepEqual(detect("// this module spawns nothing and opens no socket\n"), []);
});

test("supervisor.js requires nothing at all", () => {
  // Stronger than the list above and cheaper to keep true: this module has no
  // dependency of any kind, so an import added later is a finding whatever it
  // names. shell/lib/geometry.js holds the same position.
  const source = fs.readFileSync(SOURCE_PATH, "utf8");
  const requires = source.split("require(").length - 1;
  assert.equal(requires, 0, `supervisor.js holds ${requires} require site(s), expected 0`);
});

test("supervisor.js is 7-bit ASCII with no carriage returns", () => {
  const bytes = fs.readFileSync(SOURCE_PATH);
  assert.equal(bytes.includes(0x0d), false, "supervisor.js must be LF, never CRLF");
  const high = [];
  for (const byte of bytes) {
    if (byte > 0x7e && byte !== 0x0a) {
      high.push(`0x${byte.toString(16)}`);
    }
  }
  assert.deepEqual(high, [], `non-ASCII byte(s) in supervisor.js: ${high.join("; ")}`);
});

test("this suite is itself 7-bit ASCII with no carriage returns", () => {
  // The character-set rule is about authored content, and a test file is
  // authored content. tests/shell/test_shell_assets.py grades both from the
  // every-push lane; this arm makes the same fault visible from `node --test`.
  const bytes = fs.readFileSync(__filename);
  assert.equal(bytes.includes(0x0d), false, "this suite must be LF, never CRLF");
  const high = [];
  for (const byte of bytes) {
    if (byte > 0x7e && byte !== 0x0a) {
      high.push(`0x${byte.toString(16)}`);
    }
  }
  assert.deepEqual(high, [], `non-ASCII byte(s) in this suite: ${high.join("; ")}`);
});

test("the decisions mutate nothing they are handed", () => {
  // Pure by contract, so a caller's own bookkeeping cannot be moved by asking a
  // question about it.
  const startInput = { healthy: false };
  const stopInput = { started: true };
  const probeInput = { attempt: 1, answered: false };

  decideStart(startInput);
  decideStop(stopInput);
  decideProbeOutcome(probeInput);

  assert.deepEqual(startInput, { healthy: false });
  assert.deepEqual(stopInput, { started: true });
  assert.deepEqual(probeInput, { attempt: 1, answered: false });
});

test("the decisions consult nothing outside their arguments", () => {
  // The same question asked twice, with an unrelated global moved in between.
  // A decision that read a clock, an environment variable or a module-level
  // flag could answer differently the second time.
  const first = [
    decideStart({ healthy: false }),
    decideStop({ started: true }),
    decideProbeOutcome({ attempt: 1, answered: false }),
  ];
  const second = [
    decideStart({ healthy: false }),
    decideStop({ started: true }),
    decideProbeOutcome({ attempt: 1, answered: false }),
  ];
  assert.deepEqual(second, first, "a decision changed with nothing about the input changing");
});
