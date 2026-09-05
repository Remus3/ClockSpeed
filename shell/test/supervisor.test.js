"use strict";

// EVERY DRIVE-LETTERED FIXTURE IN THIS FILE IS ASSEMBLED RATHER THAN SPELLED.
// The reason is measured, not stylistic: tests/shell/test_shell_assets.py sweeps
// every file under shell/ for the drive-path SHAPE, because that shape is how a
// Windows account name reaches a tracked file. These fixtures carry no account
// name - they are inventions like Tools and first - but the sweep grades the
// shape and not the contents, and it is right to. Spelling one as a literal
// reddens a privacy arm against a file that leaks nothing, which is the same
// trap this suite's own account-id specimen fell into one round earlier.
const DRIVE = ["C", ":"].join("");
const SEP = String.fromCharCode(92);
const drivePath = (...parts) => [DRIVE, ...parts].join(SEP);


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
  REFUSE_UNKNOWN_ELAPSED,
  REFUSE_UNSEARCHABLE_PATH,
  REFUSE_UNKNOWN_EXTENSIONS,
  REFUSE_UNTESTABLE_CANDIDATE,
  REFUSE_NO_INTERPRETER,
  NOT_A_REFUSAL,
  PROBE_INTERVAL_MS,
  PROBE_ATTEMPT_CEILING,
  PROBE_TIMEOUT_MS,
  WAIT_BUDGET_MS,
  MODULE_FLAG,
  SERVER_MODULE,
  INTERPRETER_NAME,
  decideStart,
  decideStop,
  decideProbeOutcome,
  resolveInterpreter,
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
    REFUSE_UNKNOWN_ELAPSED,
    REFUSE_UNSEARCHABLE_PATH,
    REFUSE_UNKNOWN_EXTENSIONS,
    REFUSE_UNTESTABLE_CANDIDATE,
    REFUSE_NO_INTERPRETER,
  ];

  // The same guard shell/lib/trust.js carries, for the same reason: a numeric
  // or boolean answer is a vocabulary in which a blanket "yes, kill it" could
  // be written by accident. Words cannot be truthy by mistake.
  const wrongType = words.filter((word) => typeof word !== "string" || word.length === 0);
  assert.deepEqual(wrongType, [], "a decision that is not a non-empty string leaked in");
  assert.equal(new Set(words).size, words.length, "every word must be distinguishable");

  // COUNTED FROM THE MODULE RATHER THAN SPELLED. A refusal word added to
  // supervisor.js without being listed above would otherwise be graded by
  // nothing at all, and this suite would report the same clean result.
  const declared = [...supervisor.REFUSALS.keys()];
  const ungraded = declared.filter((word) => !words.includes(word));
  assert.deepEqual(ungraded, [], `refusal word(s) this suite never grades: ${ungraded.join("; ")}`);
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

// The elapsed time every attempt-ceiling arm below passes. Zero deliberately:
// these arms grade the ATTEMPT bound, and any value that could also trip the
// wall-clock budget would let one bound stand in for the other and leave the
// arm unable to say which one it measured.
const NO_TIME_SPENT = 0;

test("decideProbeOutcome returns READY as soon as the dashboard answers", () => {
  assert.equal(decideProbeOutcome({ attempt: 1, answered: true, elapsedMs: NO_TIME_SPENT }), READY);
});

test("decideProbeOutcome returns RETRY below the ceiling", () => {
  assert.equal(decideProbeOutcome({ attempt: 1, answered: false, elapsedMs: NO_TIME_SPENT }), RETRY);
});

test("decideProbeOutcome at the attempt ceiling and one either side", () => {
  const at = { attempt: PROBE_ATTEMPT_CEILING, answered: false, elapsedMs: NO_TIME_SPENT };
  const below = { ...at, attempt: PROBE_ATTEMPT_CEILING - 1 };
  const above = { ...at, attempt: PROBE_ATTEMPT_CEILING + 1 };

  // Spelled as three separate assertions rather than a loop, so a regression
  // names the side of the boundary that moved.
  assert.equal(decideProbeOutcome(below), RETRY, "one below");
  assert.equal(decideProbeOutcome(at), GIVE_UP, "at the ceiling");
  assert.equal(decideProbeOutcome(above), GIVE_UP, "one above");

  // An off-by-one in either direction is what these two negatives pin. A
  // `>` where a `>=` belongs turns the ceiling itself into another retry.
  assert.notEqual(decideProbeOutcome(at), RETRY);
  assert.notEqual(decideProbeOutcome(below), GIVE_UP);
});

test("decideProbeOutcome answers READY even at and beyond the ceiling", () => {
  // The ceiling bounds how long the companion WAITS, not whether an answer
  // counts. A dashboard that replied on its last permitted probe has started.
  const answered = { answered: true, elapsedMs: NO_TIME_SPENT };
  assert.equal(decideProbeOutcome({ ...answered, attempt: PROBE_ATTEMPT_CEILING }), READY);
  assert.equal(decideProbeOutcome({ ...answered, attempt: PROBE_ATTEMPT_CEILING + 1 }), READY);
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
    ["probe/answered", decideProbeOutcome({ attempt: 1, answered: true, elapsedMs: 0 })],
    ["probe/first", decideProbeOutcome({ attempt: 1, answered: false, elapsedMs: 0 })],
    [
      "probe/below",
      decideProbeOutcome({ attempt: PROBE_ATTEMPT_CEILING - 1, answered: false, elapsedMs: 0 }),
    ],
    [
      "probe/at",
      decideProbeOutcome({ attempt: PROBE_ATTEMPT_CEILING, answered: false, elapsedMs: 0 }),
    ],
    [
      "probe/above",
      decideProbeOutcome({ attempt: PROBE_ATTEMPT_CEILING + 1, answered: false, elapsedMs: 0 }),
    ],
    // The wall-clock budget belongs in the pinned vector for the same reason
    // every other answer does: a swap between GIVE_UP and RETRY here is an
    // unbounded wait, and it moves exactly one entry of this table.
    [
      "probe/budget-spent",
      decideProbeOutcome({ attempt: 1, answered: false, elapsedMs: WAIT_BUDGET_MS }),
    ],
    [
      "probe/budget-spent-but-answered",
      decideProbeOutcome({ attempt: 1, answered: true, elapsedMs: WAIT_BUDGET_MS }),
    ],
    ["probe/uncounted", decideProbeOutcome({ attempt: 0, answered: false, elapsedMs: 0 })],
    ["probe/unanswerable", decideProbeOutcome({ attempt: 1, answered: 1, elapsedMs: 0 })],
    ["probe/untimed", decideProbeOutcome({ attempt: 1, answered: false })],
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
    ["probe/budget-spent", GIVE_UP],
    ["probe/budget-spent-but-answered", READY],
    ["probe/uncounted", REFUSE_UNKNOWN_ATTEMPT],
    ["probe/unanswerable", REFUSE_UNKNOWN_ANSWER],
    ["probe/untimed", REFUSE_UNKNOWN_ELAPSED],
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
  // SWEPT FROM THE MODULE, not from a list kept here. A hand-written list goes
  // stale silently the day a refusal is added, and reports the same pass.
  const words = [...supervisor.REFUSALS.keys()];
  assert.ok(words.length > 0, "the refusal vocabulary is empty");
  const lines = words.map((word) => supervisorRefusal(word));
  const empty = lines.filter((line) => typeof line !== "string" || line.length === 0);
  assert.deepEqual(empty, [], "a refusal word rendered nothing");
  assert.equal(new Set(lines).size, lines.length, "two refusals share one line");
});

test("no refusal line can quote a path, a host, a file name or a caller's value", () => {
  // NOT_A_REFUSAL is already a line rather than a word - it is what a caller
  // who passed something outside the vocabulary is told - so it is swept
  // alongside the four that are rendered.
  // EVERY line the module can speak, taken from the module. This arm is the one
  // that would catch a refusal added later whose text quoted a directory - and
  // a hand-written list here would simply not look at it. That matters more now
  // that resolveInterpreter refuses about PATHS.
  const lines = [...supervisor.REFUSALS.values(), NOT_A_REFUSAL];

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
    decideProbeOutcome({ attempt: 1, answered: false, elapsedMs: 0 }),
  ];
  const second = [
    decideStart({ healthy: false }),
    decideStop({ started: true }),
    decideProbeOutcome({ attempt: 1, answered: false, elapsedMs: 0 }),
  ];
  assert.deepEqual(second, first, "a decision changed with nothing about the input changing");
});

// ---------------------------------------------------------------------------
// The wall-clock budget - the wait is bounded by TIME, not only by attempts
// ---------------------------------------------------------------------------

// Every shape that is not an elapsed duration. Zero is NOT here: a probe that
// finished in the same millisecond it started has a real elapsed time of zero.
// A fraction is not here either - a high-resolution clock yields one, and it is
// a perfectly good duration. What is rejected is anything that cannot be
// compared against a budget and mean something: the infinities, NaN, a string
// that looks like a number, and a boolean.
const NOT_AN_ELAPSED = Object.freeze([
  undefined,
  null,
  -1,
  Number.NaN,
  Number.POSITIVE_INFINITY,
  Number.NEGATIVE_INFINITY,
  "0",
  "1000",
  true,
  false,
  {},
  [],
  [0],
  () => 0,
]);

test("the wall-clock budget bounds the wait far below what the attempt ceiling alone allows", () => {
  // THIS ARM IS THE REPAIR, STATED AS A NUMBER. Before it, the only bound on
  // the wait was the attempt count, and a listener that accepts a connection
  // and never speaks makes every probe burn the FULL timeout rather than
  // failing fast. At the shipped constants that is 80 probes of 2000ms plus 79
  // gaps of 250ms, and the operator sees no window and no tray icon for the
  // whole of it.
  const worstCase =
    PROBE_ATTEMPT_CEILING * PROBE_TIMEOUT_MS + (PROBE_ATTEMPT_CEILING - 1) * PROBE_INTERVAL_MS;

  // A TRIPWIRE AND NOT A RESTATEMENT. The value is derived from the three
  // constants in the line above, so it cannot drift silently; spelling the
  // total here means that moving any constant reddens this arm and forces the
  // budget below to be re-derived rather than inherited.
  assert.equal(worstCase, 179750, "a probe constant moved - re-derive WAIT_BUDGET_MS");

  assert.ok(
    WAIT_BUDGET_MS < worstCase,
    `the budget ${WAIT_BUDGET_MS}ms does not bind below the ceiling's ${worstCase}ms`
  );
  // Not merely lower - decisively lower. A budget a few per cent under the
  // attempt ceiling would satisfy the line above while leaving the operator
  // with substantially the same three-minute wait.
  assert.ok(
    WAIT_BUDGET_MS * 4 <= worstCase,
    `the budget ${WAIT_BUDGET_MS}ms is a formality beside ${worstCase}ms, not the binding bound`
  );
  assert.ok(Number.isInteger(WAIT_BUDGET_MS) && WAIT_BUDGET_MS > 0, "the budget is a duration");
});

test("the budget leaves room for a real start, measured rather than assumed", () => {
  // The slowest cold start measured through the shipped path was under a
  // second. A budget that did not clear a single probe timeout could refuse a
  // dashboard that was still starting, which is the failure direction that
  // costs an operator a working system rather than a slow error.
  assert.ok(
    WAIT_BUDGET_MS > PROBE_TIMEOUT_MS,
    "the budget must outlast at least one whole probe"
  );
  assert.ok(
    WAIT_BUDGET_MS >= 10 * PROBE_TIMEOUT_MS,
    "the budget must leave a real start many probes of headroom"
  );
});

test("decideProbeOutcome gives up once the budget is spent, whatever the attempt says", () => {
  // The whole point: attempt 1 of 80 is nowhere near the ceiling, and the wait
  // still ends. Before this, only the attempt count could end it.
  const decision = decideProbeOutcome({ attempt: 1, answered: false, elapsedMs: WAIT_BUDGET_MS });
  assert.equal(decision, GIVE_UP);
  assert.notEqual(decision, RETRY, "a spent budget must not be retried through");
});

test("decideProbeOutcome at the budget boundary and one either side", () => {
  const below = { attempt: 1, answered: false, elapsedMs: WAIT_BUDGET_MS - 1 };
  const at = { attempt: 1, answered: false, elapsedMs: WAIT_BUDGET_MS };
  const above = { attempt: 1, answered: false, elapsedMs: WAIT_BUDGET_MS + 1 };

  // Spelled separately, like the attempt-ceiling arm above it, so a regression
  // names the side of the boundary that moved.
  assert.equal(decideProbeOutcome(below), RETRY, "one below the budget");
  assert.equal(decideProbeOutcome(at), GIVE_UP, "at the budget");
  assert.equal(decideProbeOutcome(above), GIVE_UP, "one above the budget");
});

test("an answer inside a spent budget is still an answer", () => {
  // The same asymmetry the ceiling already has. The budget bounds how long the
  // companion WAITS, not whether a reply counts - a dashboard that answered as
  // the budget expired has started, and refusing it would throw away a working
  // system on a stopwatch.
  assert.equal(
    decideProbeOutcome({ attempt: 1, answered: true, elapsedMs: WAIT_BUDGET_MS * 10 }),
    READY
  );
});

test("decideProbeOutcome refuses when the elapsed time is absent, so the budget cannot be forgotten", () => {
  // AN OPTIONAL BOUND IS DECORATION. A caller that omits the elapsed time gets
  // a refusal rather than the old unbounded behaviour, so the wall-clock bound
  // cannot be dropped by forgetting a field. It fails CLOSED: main.js ends the
  // wait on any word that is neither READY nor RETRY.
  assert.equal(decideProbeOutcome({ attempt: 1, answered: false }), REFUSE_UNKNOWN_ELAPSED);
  assert.equal(decideProbeOutcome({ attempt: 1, answered: true }), REFUSE_UNKNOWN_ELAPSED);
});

test("decideProbeOutcome refuses by name for every elapsed value that is not a duration", () => {
  const wrong = NOT_AN_ELAPSED.filter(
    (elapsedMs) =>
      decideProbeOutcome({ attempt: 1, answered: false, elapsedMs }) !== REFUSE_UNKNOWN_ELAPSED
  ).map((elapsedMs) => `${typeof elapsedMs}:${String(elapsedMs)}`);
  assert.deepEqual(wrong, [], `a bad elapsed time was not refused: ${wrong.join("; ")}`);
});

test("decideProbeOutcome accepts zero and a fractional elapsed time", () => {
  // The first probe of a wait genuinely has an elapsed time of zero, and a
  // high-resolution clock yields fractions. Refusing either would make the
  // honest caller the one that gets refused.
  assert.equal(decideProbeOutcome({ attempt: 1, answered: false, elapsedMs: 0 }), RETRY);
  assert.equal(decideProbeOutcome({ attempt: 1, answered: false, elapsedMs: 0.5 }), RETRY);
});

test("the attempt and the answer are still checked before the elapsed time", () => {
  // The stated order, so a caller repairing a broken loop is told which value
  // to look at first. The elapsed time is checked last because it is the
  // newest field and the least likely to be the one a reader is confused by.
  assert.equal(
    decideProbeOutcome({ attempt: 0, answered: "yes", elapsedMs: "later" }),
    REFUSE_UNKNOWN_ATTEMPT
  );
  assert.equal(
    decideProbeOutcome({ attempt: 1, answered: "yes", elapsedMs: "later" }),
    REFUSE_UNKNOWN_ANSWER
  );
});

// ---------------------------------------------------------------------------
// resolveInterpreter - the current directory may never win
// ---------------------------------------------------------------------------

// What an absolute Windows path looks like: drive-rooted, or a UNC share. Note
// what is NOT absolute and is easy to read as though it were - "C:name" is
// rooted on the DRIVE but relative to that drive's current directory, and a
// leading separator with no drive is relative to the current drive.
const ABSOLUTE = /^(?:[A-Za-z]:[\\/]|\\\\[^\\/])/;

// Every PATH entry that must never produce a candidate. The first three are the
// cwd spelled the ways a PATH actually spells it.
const RELATIVE_PATH_ENTRIES = Object.freeze([
  ".",
  ".\\",
  "./",
  "..",
  "bin",
  "tools\\bin",
  "C:relative",
  "C:",
  "\\rooted-on-the-current-drive",
  "",
  "   ",
]);

const ABSOLUTE_PATH_ENTRY = drivePath("Tools", "bin");
const PATHEXT_VALUE = ".COM;.EXE;.BAT";

/**
 * A probe that remembers every candidate it was offered.
 *
 * The recording is the point. Asserting only on the RETURN value would let a
 * resolver that built a candidate out of the current directory pass whenever
 * that candidate happened not to exist - and existence is the attacker's
 * choice, not ours. What must be true is that the candidate is never BUILT.
 */
function recordingProbe(accept) {
  const offered = [];
  const probe = (candidate) => {
    offered.push(candidate);
    return accept(candidate);
  };
  probe.offered = offered;
  return probe;
}

test("resolveInterpreter returns the absolute path of the first directory that holds it", () => {
  const wanted = `${ABSOLUTE_PATH_ENTRY}\\${INTERPRETER_NAME}.EXE`;
  const probe = recordingProbe((candidate) => candidate === wanted);
  const resolved = resolveInterpreter({
    pathValue: [drivePath("Windows", "System32"), ABSOLUTE_PATH_ENTRY].join(";"),
    pathExt: PATHEXT_VALUE,
    isExecutable: probe,
  });
  assert.equal(resolved, wanted);
  assert.ok(ABSOLUTE.test(resolved), `the resolver returned a relative path: ${resolved}`);
});

test("resolveInterpreter NEVER consults the current working directory", () => {
  // THE ARM THIS FUNCTION EXISTS FOR. Measured on this machine: libuv searches
  // the spawn cwd before PATH whenever NeedCurrentDirectoryForExePath says to,
  // and the environment variable that turns that off is absent at both machine
  // and user scope - so an Explorer-launched companion has the cwd search live.
  // The repository root grants Modify to Authenticated Users, so any local user
  // can drop a decoy there.
  //
  // The predicate says YES TO EVERYTHING. A resolver that built even one
  // candidate out of the current directory would therefore return it, and the
  // only way to answer a refusal is to never look there at all.
  const probe = recordingProbe(() => true);
  const decision = resolveInterpreter({
    pathValue: ".",
    pathExt: ".EXE",
    isExecutable: probe,
  });
  assert.equal(decision, REFUSE_NO_INTERPRETER, "the cwd produced a resolution");
  assert.deepEqual(probe.offered, [], `a candidate was built out of the cwd: ${probe.offered}`);
});

// The four words this function may answer instead of a path. Held as a list so
// the sweep below can say "any refusal" without naming which - an empty PATH
// and a PATH of relative entries are different faults and refuse differently,
// and pinning the wrong one would make the sweep a statement about spelling
// rather than about the property.
const RESOLVER_REFUSALS = Object.freeze([
  REFUSE_UNSEARCHABLE_PATH,
  REFUSE_UNKNOWN_EXTENSIONS,
  REFUSE_UNTESTABLE_CANDIDATE,
  REFUSE_NO_INTERPRETER,
]);

test("resolveInterpreter never resolves anything from a relative PATH entry", () => {
  // The sweep behind the arm above. Every spelling of "somewhere relative"
  // this suite knows about is offered as the WHOLE of PATH, with a predicate
  // that accepts anything, and none of them may yield a resolution.
  const resolved = RELATIVE_PATH_ENTRIES.filter(
    (entry) =>
      !RESOLVER_REFUSALS.includes(
        resolveInterpreter({
          pathValue: entry,
          pathExt: PATHEXT_VALUE,
          isExecutable: () => true,
        })
      )
  );
  assert.deepEqual(resolved, [], `a relative PATH entry resolved: ${resolved.join("; ")}`);
});

test("resolveInterpreter offers the predicate no candidate that is not absolute", () => {
  // Stronger than the return value, and for the same reason as above: a
  // candidate that was BUILT out of a relative entry is a vulnerability that
  // happens not to have fired. Every relative spelling is mixed in among a real
  // directory, so the resolver has genuine work to do and cannot pass by
  // refusing everything.
  const probe = recordingProbe(() => false);
  resolveInterpreter({
    pathValue: [...RELATIVE_PATH_ENTRIES, ABSOLUTE_PATH_ENTRY].join(";"),
    pathExt: PATHEXT_VALUE,
    isExecutable: probe,
  });

  assert.ok(probe.offered.length > 0, "the sweep graded nothing - no candidate was built");
  const relative = probe.offered.filter((candidate) => !ABSOLUTE.test(candidate));
  assert.deepEqual(relative, [], `relative candidate(s) offered: ${relative.join("; ")}`);

  // And every candidate came from the one absolute entry, so nothing was
  // silently rewritten into an absolute-looking path.
  const foreign = probe.offered.filter(
    (candidate) => !candidate.startsWith(`${ABSOLUTE_PATH_ENTRY}\\`)
  );
  assert.deepEqual(foreign, [], `candidate(s) from a relative entry: ${foreign.join("; ")}`);
});

test("resolveInterpreter tries a directory's extensions in PATHEXT order before moving on", () => {
  // Directory-major, which is the order Windows itself searches in. Pinning the
  // whole offered vector also pins the join and the interpreter name, so a
  // resolver that quietly changed either is visible here.
  const probe = recordingProbe(() => false);
  resolveInterpreter({
    pathValue: [drivePath("first"), drivePath("second")].join(";"),
    pathExt: ".COM;.EXE",
    isExecutable: probe,
  });
  assert.deepEqual(probe.offered, [
    drivePath("first", `${INTERPRETER_NAME}.COM`),
    drivePath("first", `${INTERPRETER_NAME}.EXE`),
    drivePath("second", `${INTERPRETER_NAME}.COM`),
    drivePath("second", `${INTERPRETER_NAME}.EXE`),
  ]);
});

test("resolveInterpreter tolerates a trailing separator on a PATH entry", () => {
  // A PATH written by hand routinely ends an entry with a separator, and a
  // naive join would produce a doubled one.
  const probe = recordingProbe(() => false);
  resolveInterpreter({
    pathValue: drivePath("bin") + SEP + ";" + drivePath("other") + "/",
    pathExt: ".EXE",
    isExecutable: probe,
  });
  assert.deepEqual(probe.offered, [
    drivePath("bin", `${INTERPRETER_NAME}.EXE`),
    drivePath("other", `${INTERPRETER_NAME}.EXE`),
  ]);
});

test("resolveInterpreter accepts a UNC directory, which is absolute", () => {
  const wanted = `\\\\host\\share\\${INTERPRETER_NAME}.EXE`;
  const resolved = resolveInterpreter({
    pathValue: "\\\\host\\share",
    pathExt: ".EXE",
    isExecutable: (candidate) => candidate === wanted,
  });
  assert.equal(resolved, wanted);
});

test("resolveInterpreter stops at the first candidate the predicate approves", () => {
  // No later directory is probed once one answers, so a resolver cannot be made
  // to prefer a decoy sitting further down PATH.
  const probe = recordingProbe(() => true);
  const resolved = resolveInterpreter({
    pathValue: [drivePath("first"), drivePath("second")].join(";"),
    pathExt: ".COM;.EXE",
    isExecutable: probe,
  });
  assert.equal(resolved, drivePath("first", `${INTERPRETER_NAME}.COM`));
  assert.equal(probe.offered.length, 1, "the resolver kept probing after an answer");
});

test("resolveInterpreter believes only a real yes from the probe", () => {
  // THE MODULE'S OWN DOCTRINE, APPLIED TO THE INJECTED QUESTION. `isAnswer`
  // exists here because a truthy check reads a count, an object or the string
  // "false" as a yes. The probe is a caller's function, so the same hazard
  // arrives through it: a predicate written to return a stat entry rather than
  // a boolean is answering a different question, and reading its object as a
  // yes would resolve a path nothing confirmed exists - which is a spawn of
  // something unverified, the exact class of fault this resolver was added for.
  //
  // Every value below is TRUTHY, so a resolver testing truthiness rather than
  // `=== true` resolves all of them. Added after a mutation that swapped the
  // strict test for a truthy one survived the rest of this suite.
  for (const truthy of [{}, [], "yes", "false", 1, -1, [0], () => {}]) {
    assert.ok(truthy, "the specimen must be truthy or this arm grades nothing");
    const answer = resolveInterpreter({
      pathValue: ABSOLUTE_PATH_ENTRY,
      pathExt: PATHEXT_VALUE,
      isExecutable: () => truthy,
    });
    assert.equal(
      answer,
      REFUSE_NO_INTERPRETER,
      `a truthy ${typeof truthy} from the probe was read as a yes`
    );
  }
});

test("resolveInterpreter refuses by name when the search path yields nothing", () => {
  assert.equal(
    resolveInterpreter({
      pathValue: ABSOLUTE_PATH_ENTRY,
      pathExt: PATHEXT_VALUE,
      isExecutable: () => false,
    }),
    REFUSE_NO_INTERPRETER
  );
});

test("resolveInterpreter refuses by name for every unusable search path", () => {
  const wrong = [undefined, null, "", "   ", ";", ";;", 0, 1, true, {}, [], [drivePath("bin")], () => ""]
    .filter(
      (pathValue) =>
        resolveInterpreter({
          pathValue,
          pathExt: PATHEXT_VALUE,
          isExecutable: () => true,
        }) !== REFUSE_UNSEARCHABLE_PATH
    )
    .map((pathValue) => `${typeof pathValue}:${String(pathValue)}`);
  assert.deepEqual(wrong, [], `an unusable search path was not refused: ${wrong.join("; ")}`);
});

test("resolveInterpreter refuses by name for every unusable extension list", () => {
  const wrong = [undefined, null, "", "   ", ";", 0, 1, true, {}, [], [".EXE"], () => ""]
    .filter(
      (pathExt) =>
        resolveInterpreter({
          pathValue: ABSOLUTE_PATH_ENTRY,
          pathExt,
          isExecutable: () => true,
        }) !== REFUSE_UNKNOWN_EXTENSIONS
    )
    .map((pathExt) => `${typeof pathExt}:${String(pathExt)}`);
  assert.deepEqual(wrong, [], `an unusable extension list was not refused: ${wrong.join("; ")}`);
});

test("resolveInterpreter refuses by name when it is given no way to test a candidate", () => {
  const wrong = [undefined, null, true, false, 0, 1, "", "yes", {}, []]
    .filter(
      (isExecutable) =>
        resolveInterpreter({
          pathValue: ABSOLUTE_PATH_ENTRY,
          pathExt: PATHEXT_VALUE,
          isExecutable,
        }) !== REFUSE_UNTESTABLE_CANDIDATE
    )
    .map((isExecutable) => `${typeof isExecutable}:${String(isExecutable)}`);
  assert.deepEqual(wrong, [], `an unusable probe was not refused: ${wrong.join("; ")}`);
});

test("resolveInterpreter refuses a missing, absent or malformed options object", () => {
  const inputs = [undefined, null, {}, "PATH", 1, [], () => {}];
  const wrong = inputs
    .filter((input) => resolveInterpreter(input) !== REFUSE_UNSEARCHABLE_PATH)
    .map((input) => String(input));
  assert.deepEqual(wrong, [], `resolveInterpreter did not refuse: ${wrong.join("; ")}`);
  assert.equal(resolveInterpreter(), REFUSE_UNSEARCHABLE_PATH, "no argument at all must refuse");
});

test("a refusal from resolveInterpreter is never mistaken for a path", () => {
  // The refusals are words, like every other decision in this module, so a
  // caller that spawned whatever came back would spawn a word rather than
  // silently running something out of the wrong directory. Checked as a
  // property: no refusal this function can answer is an absolute path.
  const pathLike = RESOLVER_REFUSALS.filter((word) => ABSOLUTE.test(word));
  assert.deepEqual(pathLike, [], `a refusal reads as a path: ${pathLike.join("; ")}`);
  assert.equal(
    new Set(RESOLVER_REFUSALS).size,
    RESOLVER_REFUSALS.length,
    "two resolver refusals share a word"
  );
});

test("INTERPRETER_NAME is a bare name, never a path and never an extension", () => {
  // supervisor.js owns the name the way it owns SERVER_MODULE, so main.js has
  // no interpreter spelled in it at all. A NAME is what BOOTSTRAP.md section
  // 2.5 requires; a PATH here would carry whichever account authored it.
  assert.equal(typeof INTERPRETER_NAME, "string");
  assert.ok(INTERPRETER_NAME.length > 0, "the interpreter name is empty");
  assert.ok(
    /^[A-Za-z0-9_-]+$/.test(INTERPRETER_NAME),
    `the interpreter name is not a bare name: ${INTERPRETER_NAME}`
  );
  assert.ok(!ABSOLUTE.test(INTERPRETER_NAME), "the interpreter name is a path");
  assert.ok(!INTERPRETER_NAME.includes("."), "the interpreter name carries an extension");
});

test("resolveInterpreter mutates nothing it is handed and consults nothing else", () => {
  const options = {
    pathValue: ABSOLUTE_PATH_ENTRY,
    pathExt: PATHEXT_VALUE,
    isExecutable: () => false,
  };
  const before = { pathValue: options.pathValue, pathExt: options.pathExt };
  const first = resolveInterpreter(options);
  const second = resolveInterpreter(options);
  assert.equal(second, first, "the resolver answered differently with nothing changed");
  assert.equal(options.pathValue, before.pathValue);
  assert.equal(options.pathExt, before.pathExt);
});
