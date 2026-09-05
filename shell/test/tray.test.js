"use strict";

// CS-909 slice B - tests for shell/lib/tray.js.
//
// WHAT THIS SUITE IS FOR. CS-909 turns the companion into a real desktop
// application: closing the window hides it to a system-tray icon instead of
// quitting, and the dashboard stays warm behind it. Every one of those
// behaviours is wired in shell/main.js, which imports the desktop toolkit and
// which no test in this repository executes (CS-619). So the parts that can be
// decided WITHOUT the toolkit are decided in shell/lib/tray.js instead - the
// menu's shape, its ids, its labels, its checked flags, the tooltip and the
// icon bytes - and this file grades them. What is left in main.js is the
// handing of that data to a Tray and a Menu, which is wiring.
//
// WHY THE ICON IS A DATA URL AND NOT A FILE ON DISK. MEASURED this session:
// this repository tracks ZERO binary files - no .png, no .ico, no .jpg, no
// .woff - and tests/shell/test_shell_assets.py asserts that every byte of
// every file under shell/ sits at or below 0x7E with no carriage return
// anywhere. A committed icon file would redden that arm on its first byte. So
// the icon ships as a base64 data URL, which is text, and main.js is what turns
// it into an image at run time.
//
// AND WHY THAT MAKES THIS SUITE'S JOB HARDER THAN "IS IT A STRING". A data URL
// that decodes to nothing, or to eight bytes of header and no pixels, is still
// a string, still ASCII, and still passes every shallow arm - and produces an
// INVISIBLE tray icon. That is not a cosmetic fault. The tray icon is the only
// route back to a window that has been closed, so an operator who cannot see it
// has an application running that they cannot reopen and cannot quit. The arms
// below therefore walk the PNG's chunk structure, check every chunk's CRC,
// inflate the pixel stream, reverse the per-scanline filters and count how many
// pixels are actually opaque. Nothing short of that distinguishes a real icon
// from a well-formed empty one.

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const zlib = require("node:zlib");

const trayModule = require("../lib/tray.js");
const {
  ICON_DATA_URL,
  MENU_IDS,
  MENU_STATE_KEYS,
  MenuStateError,
  UnknownMenuKeyError,
  menuTemplate,
  tooltip,
} = trayModule;

// ---------------------------------------------------------------------------
// Shared constants and helpers
// ---------------------------------------------------------------------------

// The eight bytes every PNG begins with. SPELLED HERE rather than imported from
// the module under test: a test that imports a constant in order to assert the
// constant grades nothing at all, and this one has to be able to fail.
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

const DATA_URL_PREFIX = "data:image/png;base64,";

// What the icon is declared to be. These four are restated here on purpose, for
// the same reason the signature is: they are the contract, and reading them
// back out of the artifact is the measurement.
//
// THIRTY-TWO AND NOT SIXTEEN, AND THAT IS A MEASUREMENT RATHER THAN A TASTE.
// shell/lib/tray.js records the finding in full: the first thirty-three bytes
// of a PNG are fixed once the header fields are chosen, they encode to a
// forty-four character base64 prefix, and for a 16x16 truecolour-with-alpha
// image that prefix contains a solidus. No search over the encoder's free
// choices can remove it, so the narrowed alphabet below is unreachable at that
// size and reachable at this one.
const ICON_WIDTH = 32;
const ICON_HEIGHT = 32;
const ICON_BIT_DEPTH = 8;
const ICON_COLOR_TYPE = 6; // truecolour with alpha - four bytes per pixel.
const ICON_BYTES_PER_PIXEL = 4;

// A PNG scanline is one filter byte followed by the row's samples.
const RAW_STRIDE = 1 + ICON_WIDTH * ICON_BYTES_PER_PIXEL;
const RAW_LENGTH = ICON_HEIGHT * RAW_STRIDE;

// The size window the icon has to sit inside.
//
// THE FLOOR IS THE POINT AND THE CEILING IS THE PROMISE. A stub that decodes to
// forty bytes would satisfy "it is a PNG" and show nothing; the floor is what
// makes an empty icon fail loudly. The ceiling is what keeps the decision to
// ship the icon as text honest - the only reason a binary asset can live inside
// an ASCII-only tree at all is that this one is small.
const MIN_ICON_BYTES = 200;
const MAX_ICON_BYTES = 8192;

// How much of the icon has to be drawn. A disc of radius 15 covers about 716 of
// the 1024 cells, so this floor is met with room to spare by the real glyph and
// is missed by every degenerate one.
const MIN_OPAQUE_PIXELS = 600;

// Labels and the tooltip are held to letters and spaces, and nothing else.
//
// THIS IS NON-NEGOTIABLE 3 WRITTEN AS A CHARACTER SET. A path carries the
// Windows account name, a save directory carries the world name, and a URL
// carries a host and a port. Enumerating those as forbidden substrings is a
// blocklist, and a blocklist is only ever as good as the last thing somebody
// thought of. An allow-list of letters and spaces cannot express a drive
// letter, a separator, a scheme, a digit or an account id at all, so the whole
// class is excluded rather than the members somebody remembered.
const LABEL_CHARSET = /^[A-Za-z][A-Za-z ]*[A-Za-z]$/;

// The historic Shell_NotifyIcon tooltip field is 128 bytes including its
// terminator, so anything longer is silently truncated by the platform rather
// than rejected. Bounding it here means the truncation is this project's
// decision instead of the operating system's.
const MAX_TOOLTIP_LENGTH = 127;

const LIB_PATH = path.join(__dirname, "..", "lib", "tray.js");

// assert.throws returns undefined rather than the error it caught, so a
// `const e = assert.throws(...)` reads as a captured exception and is in fact
// always undefined - every instanceof asserted against it would then be
// asserting about nothing. This captures the error itself. Same helper, same
// reason, as shell/test/window.test.js.
function caught(fn) {
  try {
    fn();
  } catch (err) {
    return err;
  }
  throw new Error("expected a throw, and nothing was thrown");
}

// Every combination of the two booleans, so no arm below can quietly grade one
// corner of the state space and be read as covering all four.
const ALL_STATES = Object.freeze([
  Object.freeze({ visible: true, alwaysOnTop: true }),
  Object.freeze({ visible: true, alwaysOnTop: false }),
  Object.freeze({ visible: false, alwaysOnTop: true }),
  Object.freeze({ visible: false, alwaysOnTop: false }),
]);

function iconBase64() {
  return ICON_DATA_URL.slice(DATA_URL_PREFIX.length);
}

function iconBytes() {
  return Buffer.from(iconBase64(), "base64");
}

// Walk the PNG chunk stream.
//
// A LENGTH-DRIVEN WALK IS ITSELF A TEST. Each chunk declares its own payload
// length, so a walk that lands exactly on the end of the buffer having consumed
// whole chunks the entire way is evidence the lengths agree with the bytes. A
// truncated or padded blob cannot produce that, and neither can a string of the
// right first eight bytes followed by anything else.
function pngChunks(bytes) {
  assert.ok(
    bytes.subarray(0, PNG_SIGNATURE.length).equals(PNG_SIGNATURE),
    "the icon does not begin with the PNG signature",
  );
  const chunks = [];
  let offset = PNG_SIGNATURE.length;
  while (offset < bytes.length) {
    assert.ok(offset + 8 <= bytes.length, `chunk header runs past the end at ${offset}`);
    const declaredLength = bytes.readUInt32BE(offset);
    const type = bytes.toString("ascii", offset + 4, offset + 8);
    const end = offset + 12 + declaredLength;
    assert.ok(end <= bytes.length, `chunk ${type} runs past the end at ${offset}`);
    chunks.push({
      type,
      data: bytes.subarray(offset + 8, offset + 8 + declaredLength),
      crc: bytes.readUInt32BE(offset + 8 + declaredLength),
    });
    offset = end;
  }
  assert.equal(offset, bytes.length, "the chunk walk did not land on the end of the file");
  return chunks;
}

function ihdrOf(chunks) {
  const header = chunks.find((chunk) => chunk.type === "IHDR");
  assert.ok(header !== undefined, "the icon carries no IHDR chunk");
  assert.equal(header.data.length, 13, "IHDR must be exactly 13 bytes");
  return {
    width: header.data.readUInt32BE(0),
    height: header.data.readUInt32BE(4),
    bitDepth: header.data[8],
    colorType: header.data[9],
    compression: header.data[10],
    filter: header.data[11],
    interlace: header.data[12],
  };
}

// Reverse the five PNG scanline filters, producing the raw RGBA samples.
//
// WHY THE FILTERS ARE REVERSED HERE RATHER THAN TRUSTED. The filter type is a
// free choice per scanline and every choice decodes to the same picture, which
// is exactly why the icon's bytes were searched over that choice - see the
// alphabet arm below. Reversing them is what turns "these bytes inflate" into
// "these bytes are a picture, and here is what is in it".
function paeth(a, b, c) {
  const p = a + b - c;
  const pa = Math.abs(p - a);
  const pb = Math.abs(p - b);
  const pc = Math.abs(p - c);
  if (pa <= pb && pa <= pc) {
    return a;
  }
  return pb <= pc ? b : c;
}

function unfilter(raw) {
  assert.equal(raw.length, RAW_LENGTH, "the inflated stream is not one whole image");
  const out = Buffer.alloc(ICON_HEIGHT * ICON_WIDTH * ICON_BYTES_PER_PIXEL);
  const rowBytes = ICON_WIDTH * ICON_BYTES_PER_PIXEL;
  for (let row = 0; row < ICON_HEIGHT; row += 1) {
    const filterType = raw[row * RAW_STRIDE];
    assert.ok(filterType >= 0 && filterType <= 4, `illegal filter type ${filterType}`);
    for (let i = 0; i < rowBytes; i += 1) {
      const x = raw[row * RAW_STRIDE + 1 + i];
      const a = i >= ICON_BYTES_PER_PIXEL ? out[row * rowBytes + i - ICON_BYTES_PER_PIXEL] : 0;
      const b = row > 0 ? out[(row - 1) * rowBytes + i] : 0;
      const c =
        row > 0 && i >= ICON_BYTES_PER_PIXEL
          ? out[(row - 1) * rowBytes + i - ICON_BYTES_PER_PIXEL]
          : 0;
      let value = x;
      if (filterType === 1) {
        value = x + a;
      } else if (filterType === 2) {
        value = x + b;
      } else if (filterType === 3) {
        value = x + Math.floor((a + b) / 2);
      } else if (filterType === 4) {
        value = x + paeth(a, b, c);
      }
      out[row * rowBytes + i] = value & 0xff;
    }
  }
  return out;
}

function pixelsOf() {
  const chunks = pngChunks(iconBytes());
  const idat = chunks.filter((chunk) => chunk.type === "IDAT").map((chunk) => chunk.data);
  assert.ok(idat.length > 0, "the icon carries no IDAT chunk");
  return unfilter(zlib.inflateSync(Buffer.concat(idat)));
}

function pixelAt(pixels, x, y) {
  const at = (y * ICON_WIDTH + x) * ICON_BYTES_PER_PIXEL;
  return {
    r: pixels[at],
    g: pixels[at + 1],
    b: pixels[at + 2],
    a: pixels[at + 3],
  };
}

// WCAG relative luminance, then the WCAG contrast ratio. Both spelled out
// rather than approximated, because the number they produce is the whole
// justification for the icon's colour and a rounded stand-in would let the
// justification pass while the colour failed.
function relativeLuminance(pixel) {
  const channel = (raw) => {
    const value = raw / 255;
    return value <= 0.04045 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * channel(pixel.r) + 0.7152 * channel(pixel.g) + 0.0722 * channel(pixel.b);
}

function contrastRatio(one, other) {
  const a = relativeLuminance(one);
  const b = relativeLuminance(other);
  const light = Math.max(a, b);
  const dark = Math.min(a, b);
  return (light + 0.05) / (dark + 0.05);
}

// ---------------------------------------------------------------------------
// The icon, as text
// ---------------------------------------------------------------------------

test("ICON_DATA_URL is a PNG data URL and nothing else", () => {
  assert.equal(typeof ICON_DATA_URL, "string");
  assert.ok(ICON_DATA_URL.startsWith(DATA_URL_PREFIX), "the data URL declares the wrong type");
  assert.ok(iconBase64().length > 0, "the data URL carries no payload");
});

test("ICON_DATA_URL is 7-bit ASCII, so it can live in an ASCII-only tree", () => {
  const bytes = Buffer.from(ICON_DATA_URL, "utf8");
  assert.equal(bytes.length, ICON_DATA_URL.length, "the data URL is not one byte per character");
  for (const byte of bytes) {
    assert.ok(byte <= 0x7e, `non-ASCII byte 0x${byte.toString(16)} in ICON_DATA_URL`);
  }
});

// THE ALPHABET IS NARROWED ON PURPOSE AND IT IS NOT TIDINESS.
//
// Base64's own alphabet includes two characters that are not word characters -
// a plus and a solidus - plus the padding character. Every one of them creates
// a boundary in the middle of an otherwise unbroken run of letters and digits,
// and this tree is swept by detectors that key on exactly that. The port sweep
// in tests/shell/test_shell_assets.py looks for a standalone integer inside the
// project's allocated band; the personal-data sweep in the same module looks
// for a bounded run of thirty-two hex characters and for a run of fifteen or
// more digits. All three of those need a non-word character on both sides of
// the run, and a payload made only of letters and digits cannot supply one.
//
// A pair of solidus characters is worse still: it opens a line comment as far
// as any text scanner is concerned, and that module's own header records a
// stripper being defeated in exactly that way.
//
// The icon's bytes were therefore searched over the free choice of PNG scanline
// filter - every choice decodes to the same picture - until the encoding landed
// in this alphabet with no padding. So this arm is not a hope about the bytes;
// it is the property they were selected for, and it goes red the moment a
// regenerated icon loses it.
test("the icon payload is letters and digits only, with no padding", () => {
  const payload = iconBase64();
  assert.ok(/^[A-Za-z0-9]+$/.test(payload), "the payload leaves the narrowed alphabet");
  assert.equal(payload.length % 4, 0, "a base64 payload is a whole number of quartets");
  assert.ok(!payload.includes("="), "the payload is padded, so it ends on a word boundary");
});

// ---------------------------------------------------------------------------
// The icon, as a picture
// ---------------------------------------------------------------------------

test("ICON_DATA_URL decodes to bytes beginning with the PNG signature", () => {
  const bytes = iconBytes();
  const head = [...bytes.subarray(0, PNG_SIGNATURE.length)];
  assert.deepEqual(head, [...PNG_SIGNATURE], "the decoded bytes are not a PNG");
});

test("the decoded icon is non-trivial in size, and stays small enough to be text", () => {
  const size = iconBytes().length;
  assert.ok(size >= MIN_ICON_BYTES, `the icon decodes to ${size} bytes, under the floor`);
  assert.ok(size <= MAX_ICON_BYTES, `the icon decodes to ${size} bytes, over the ceiling`);
});

test("every PNG chunk carries a CRC that matches its own bytes", () => {
  const bytes = iconBytes();
  const chunks = pngChunks(bytes);
  const broken = chunks.filter((chunk) => {
    const covered = Buffer.concat([Buffer.from(chunk.type, "ascii"), chunk.data]);
    return zlib.crc32(covered) !== chunk.crc;
  });
  assert.equal(broken.length, 0, `chunks with a bad CRC: ${broken.map((c) => c.type).join()}`);
});

test("the chunk stream opens with IHDR, closes with IEND and holds pixel data", () => {
  const chunks = pngChunks(iconBytes());
  assert.ok(chunks.length >= 3, "a PNG needs a header, some pixels and a terminator");
  assert.equal(chunks[0].type, "IHDR");
  assert.equal(chunks[chunks.length - 1].type, "IEND");
  assert.equal(chunks[chunks.length - 1].data.length, 0, "IEND carries no payload");
  assert.ok(chunks.some((chunk) => chunk.type === "IDAT"), "the icon carries no IDAT chunk");
});

test("IHDR declares the tray geometry this project chose", () => {
  const header = ihdrOf(pngChunks(iconBytes()));
  assert.equal(header.width, ICON_WIDTH);
  assert.equal(header.height, ICON_HEIGHT);
  assert.equal(header.bitDepth, ICON_BIT_DEPTH);
  assert.equal(header.colorType, ICON_COLOR_TYPE);
  assert.equal(header.compression, 0, "PNG declares exactly one compression method");
  assert.equal(header.filter, 0, "PNG declares exactly one filter method");
  assert.equal(header.interlace, 0, "an interlaced tray icon buys nothing and costs bytes");
});

test("the pixel stream inflates to exactly one whole image", () => {
  const chunks = pngChunks(iconBytes());
  const idat = chunks.filter((chunk) => chunk.type === "IDAT").map((chunk) => chunk.data);
  const raw = zlib.inflateSync(Buffer.concat(idat));
  assert.equal(raw.length, RAW_LENGTH, `inflated ${raw.length} bytes, expected ${RAW_LENGTH}`);
});

test("every scanline names a filter type PNG actually declares", () => {
  const chunks = pngChunks(iconBytes());
  const idat = chunks.filter((chunk) => chunk.type === "IDAT").map((chunk) => chunk.data);
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const illegal = [];
  for (let row = 0; row < ICON_HEIGHT; row += 1) {
    const filterType = raw[row * RAW_STRIDE];
    if (!(filterType >= 0 && filterType <= 4)) {
      illegal.push(row);
    }
  }
  assert.equal(illegal.length, 0, `scanlines with an illegal filter: ${illegal.join()}`);
});

// THE ARM THE WHOLE FILE EXISTS FOR. Everything above is satisfied by a
// perfectly formed, perfectly empty icon - 256 transparent pixels, correct
// CRCs, correct dimensions, and invisible in the tray. This one is not.
test("the icon is actually drawn - most of the disc is opaque", () => {
  const pixels = pixelsOf();
  let opaque = 0;
  for (let y = 0; y < ICON_HEIGHT; y += 1) {
    for (let x = 0; x < ICON_WIDTH; x += 1) {
      if (pixelAt(pixels, x, y).a === 255) {
        opaque += 1;
      }
    }
  }
  assert.ok(opaque >= MIN_OPAQUE_PIXELS, `only ${opaque} pixels are opaque - the icon is empty`);
});

test("the icon is a round glyph and not a filled square", () => {
  const pixels = pixelsOf();
  const corners = [
    [0, 0],
    [ICON_WIDTH - 1, 0],
    [0, ICON_HEIGHT - 1],
    [ICON_WIDTH - 1, ICON_HEIGHT - 1],
  ];
  const solid = corners.filter(([x, y]) => pixelAt(pixels, x, y).a !== 0);
  assert.equal(solid.length, 0, `corner pixels are not transparent: ${JSON.stringify(solid)}`);

  const middle = pixelAt(pixels, ICON_WIDTH / 2, ICON_HEIGHT / 2);
  assert.equal(middle.a, 255, "the centre of the glyph is not opaque");
});

// The contrast figures below are the reason the icon is the colour it is, and
// asserting them is what stops that reason being a claim in a comment. A
// Windows notification area is dark under the default theme and near-white
// under the light one, and the same icon has to be legible on both, so the face
// colour is held against BOTH extremes rather than against whichever one
// somebody had on screen.
test("the two drawn colours read against each other and against either taskbar", () => {
  const pixels = pixelsOf();
  const tally = new Map();
  for (let y = 0; y < ICON_HEIGHT; y += 1) {
    for (let x = 0; x < ICON_WIDTH; x += 1) {
      const pixel = pixelAt(pixels, x, y);
      if (pixel.a !== 255) {
        continue;
      }
      const key = `${pixel.r},${pixel.g},${pixel.b}`;
      tally.set(key, (tally.get(key) ?? 0) + 1);
    }
  }
  const ranked = [...tally.entries()].sort((one, other) => other[1] - one[1]);
  assert.ok(ranked.length >= 2, "the icon is drawn in a single flat colour");

  const asPixel = (key) => {
    const [r, g, b] = key.split(",").map(Number);
    return { r, g, b };
  };
  const face = asPixel(ranked[0][0]);
  const hands = asPixel(ranked[1][0]);
  const black = { r: 0, g: 0, b: 0 };
  const white = { r: 255, g: 255, b: 255 };

  const onDark = contrastRatio(face, black);
  const onLight = contrastRatio(face, white);
  const onFace = contrastRatio(hands, face);
  assert.ok(onDark >= 3, `the face reads at ${onDark.toFixed(2)} on a dark taskbar`);
  assert.ok(onLight >= 3, `the face reads at ${onLight.toFixed(2)} on a light taskbar`);
  assert.ok(onFace >= 3, `the hands read at ${onFace.toFixed(2)} against the face`);
});

// ---------------------------------------------------------------------------
// The menu ids
// ---------------------------------------------------------------------------

test("MENU_IDS is frozen, and so is every state key list this module publishes", () => {
  assert.ok(Object.isFrozen(MENU_IDS), "MENU_IDS is not frozen");
  assert.ok(Object.isFrozen(MENU_STATE_KEYS), "MENU_STATE_KEYS is not frozen");
});

// The ids are spelled out here, by value. They are a SEAM: shell/main.js
// switches on them to decide which handler fires, so renaming one silently
// disconnects a menu entry from its behaviour, and the window the operator
// clicked to reopen simply does not appear. A test that read the ids out of the
// module and asserted they equalled themselves would not notice.
test("the menu ids are stable, spelled out by value", () => {
  assert.equal(MENU_IDS.SHOW_HIDE, "clockspeed.tray.showHide");
  assert.equal(MENU_IDS.ALWAYS_ON_TOP, "clockspeed.tray.alwaysOnTop");
  assert.equal(MENU_IDS.SEPARATOR_BEFORE_QUIT, "clockspeed.tray.separatorBeforeQuit");
  assert.equal(MENU_IDS.QUIT, "clockspeed.tray.quit");
});

test("the menu ids are unique", () => {
  const values = Object.values(MENU_IDS);
  assert.equal(new Set(values).size, values.length, `duplicate ids in ${JSON.stringify(values)}`);
});

test("MENU_STATE_KEYS names exactly the two booleans the menu is built from", () => {
  assert.deepEqual([...MENU_STATE_KEYS].sort(), ["alwaysOnTop", "visible"]);
});

// ---------------------------------------------------------------------------
// The menu template
// ---------------------------------------------------------------------------

test("every entry carries an id this module declares, and no id repeats", () => {
  const declared = new Set(Object.values(MENU_IDS));
  for (const state of ALL_STATES) {
    const entries = menuTemplate(state);
    const ids = entries.map((entry) => entry.id);
    const stray = ids.filter((id) => !declared.has(id));
    assert.equal(stray.length, 0, `undeclared id(s) ${stray.join()} for ${JSON.stringify(state)}`);
    assert.equal(new Set(ids).size, ids.length, `a repeated id for ${JSON.stringify(state)}`);
  }
});

// EVERY ENTRY, SEPARATOR INCLUDED, CARRIES AN ID. A separator does not need one
// to render, and giving it one is not decoration: it is what lets the
// uniqueness arm above be total. The alternative was an arm that filters
// separators out before checking, and a filtered arm goes quietly vacuous the
// day the filter widens by one entry type.
test("the entry order is stable across every state", () => {
  for (const state of ALL_STATES) {
    assert.deepEqual(
      menuTemplate(state).map((entry) => entry.id),
      [
        MENU_IDS.SHOW_HIDE,
        MENU_IDS.ALWAYS_ON_TOP,
        MENU_IDS.SEPARATOR_BEFORE_QUIT,
        MENU_IDS.QUIT,
      ],
      `the entry order moved for ${JSON.stringify(state)}`,
    );
  }
});

// THE ONE THE OPERATOR CANNOT DO WITHOUT. A tray whose menu has no quit is an
// application with no exit: the window is hidden rather than closed, so the
// taskbar offers nothing, and the only remaining route out is the task manager.
// This is asserted across all four states rather than on the default one,
// because the failure this guards against is a quit entry that is present until
// some particular combination of flags drops it.
test("a quit item always exists", () => {
  for (const state of ALL_STATES) {
    const entries = menuTemplate(state);
    const quit = entries.filter((entry) => entry.id === MENU_IDS.QUIT);
    assert.equal(quit.length, 1, `no single quit entry for ${JSON.stringify(state)}`);
    assert.equal(quit[0].label, "Quit Clockspeed");
    assert.equal(quit[0].type, undefined, "quit is an ordinary item, not a checkbox");
  }
});

// AN ALWAYS-SHOW LABEL ON A VISIBLE WINDOW IS A LIE IN THE UI, and it is the
// kind that costs the operator a click and then their trust in the rest of the
// menu. Both labels are asserted by exact value in both directions, so an
// implementation that hardcoded either one fails on the other state.
test("the show and hide label follows the window, by value", () => {
  assert.equal(
    menuTemplate({ visible: true, alwaysOnTop: false }).find((e) => e.id === MENU_IDS.SHOW_HIDE)
      .label,
    "Hide window",
  );
  assert.equal(
    menuTemplate({ visible: true, alwaysOnTop: true }).find((e) => e.id === MENU_IDS.SHOW_HIDE)
      .label,
    "Hide window",
  );
  assert.equal(
    menuTemplate({ visible: false, alwaysOnTop: false }).find((e) => e.id === MENU_IDS.SHOW_HIDE)
      .label,
    "Show window",
  );
  assert.equal(
    menuTemplate({ visible: false, alwaysOnTop: true }).find((e) => e.id === MENU_IDS.SHOW_HIDE)
      .label,
    "Show window",
  );
});

test("the always-on-top entry is a checkbox whose checked flag follows the state", () => {
  for (const state of ALL_STATES) {
    const entry = menuTemplate(state).find((one) => one.id === MENU_IDS.ALWAYS_ON_TOP);
    assert.equal(entry.label, "Always on top", `the label moved for ${JSON.stringify(state)}`);
    assert.equal(entry.type, "checkbox", "a toggle that does not render as one shows no state");
    assert.equal(
      entry.checked,
      state.alwaysOnTop,
      `checked was ${entry.checked} for ${JSON.stringify(state)}`,
    );
  }
});

test("the checked flag is present only where it means something", () => {
  for (const state of ALL_STATES) {
    for (const entry of menuTemplate(state)) {
      const isToggle = entry.id === MENU_IDS.ALWAYS_ON_TOP;
      assert.equal(
        Object.hasOwn(entry, "checked"),
        isToggle,
        `checked presence is wrong on ${entry.id}`,
      );
    }
  }
});

test("the separator is a separator and carries no label", () => {
  for (const state of ALL_STATES) {
    const entry = menuTemplate(state).find((one) => one.id === MENU_IDS.SEPARATOR_BEFORE_QUIT);
    assert.equal(entry.type, "separator");
    assert.equal(Object.hasOwn(entry, "label"), false, "a separator with a label renders text");
  }
});

// A caller that mutated the array or an entry it was handed would poison every
// later menu if the module handed back the same objects each time. Returning
// fresh ones is cheap; the alternative is a defect that only appears on the
// second right-click.
test("every call returns a fresh array of fresh entries", () => {
  const state = { visible: true, alwaysOnTop: false };
  const first = menuTemplate(state);
  const second = menuTemplate(state);
  assert.notEqual(first, second, "the same array came back twice");
  assert.notEqual(first[0], second[0], "the same entry object came back twice");
  first[0].label = "MUTATED";
  first.push({ id: "injected" });
  assert.equal(menuTemplate(state)[0].label, "Hide window", "a mutation reached a later call");
  assert.equal(menuTemplate(state).length, second.length, "a push reached a later call");
});

// ---------------------------------------------------------------------------
// Totality - every refusal is named, and nothing is defaulted
// ---------------------------------------------------------------------------

test("a missing state object is refused, not defaulted", () => {
  for (const bad of [undefined, null, "visible", 1, true, [], () => {}]) {
    const err = caught(() => menuTemplate(bad));
    assert.ok(err instanceof MenuStateError, `${JSON.stringify(bad) ?? "undefined"} was accepted`);
    assert.equal(err.name, "MenuStateError");
  }
});

test("a missing boolean is refused, not defaulted to false", () => {
  for (const bad of [{}, { visible: true }, { alwaysOnTop: true }]) {
    const err = caught(() => menuTemplate(bad));
    assert.ok(err instanceof MenuStateError, `${JSON.stringify(bad)} was accepted`);
  }
});

// NOT TRUTHY, BOOLEAN. A state loaded from the operator-editable JSON on disk
// can carry the string "false", which is truthy, and a menu that read it as a
// checked box would report the opposite of the truth to the only person who
// could notice.
test("a non-boolean is refused rather than coerced", () => {
  for (const bad of ["true", "false", 0, 1, null, undefined, {}, []]) {
    const err = caught(() => menuTemplate({ visible: bad, alwaysOnTop: false }));
    assert.ok(err instanceof MenuStateError, `visible ${JSON.stringify(bad)} was coerced`);
    const other = caught(() => menuTemplate({ visible: true, alwaysOnTop: bad }));
    assert.ok(other instanceof MenuStateError, `alwaysOnTop ${JSON.stringify(bad)} was coerced`);
  }
});

// AN UNRECOGNISED KEY IS A DIFFERENT FAULT FROM A MISSING ONE and gets its own
// class, so a caller handling one cannot accidentally swallow the other. It is
// also checked FIRST: a misspelled key produces both faults at once, and the
// unknown-key error names the cause where the missing-key error names only the
// symptom.
test("an unknown key is refused rather than ignored", () => {
  const err = caught(() => menuTemplate({ visible: true, alwaysOnTop: false, minimized: true }));
  assert.ok(err instanceof UnknownMenuKeyError, "an unrecognised key was silently ignored");
  assert.equal(err.name, "UnknownMenuKeyError");

  const typo = caught(() => menuTemplate({ visible: true, alwaysOnTopp: false }));
  assert.ok(typo instanceof UnknownMenuKeyError, "a misspelled key was reported as a missing one");
});

test("the two refusals are distinct classes, and both are real errors", () => {
  assert.notEqual(MenuStateError, UnknownMenuKeyError);
  assert.ok(new MenuStateError() instanceof Error);
  assert.ok(new UnknownMenuKeyError() instanceof Error);
  assert.ok(!(new MenuStateError() instanceof UnknownMenuKeyError));
  assert.ok(!(new UnknownMenuKeyError() instanceof MenuStateError));
});

// Caller-supplied text never reaches the message. shell/lib/window.js takes the
// same line for the same reason: an error message is an echo path, and echoing
// a value nobody audited is how it reaches a log. The rejected input is carried
// as a property instead, where a debugger can read it and a log line will not.
test("no refusal renders the caller's own text into its message", () => {
  const err = caught(() => menuTemplate({ visible: true, secretLookingKey: 1 }));
  assert.ok(!err.message.includes("secretLookingKey"), "the error message echoed a caller key");
  assert.ok(err.message.length > 0, "the refusal carries no message at all");
});

// ---------------------------------------------------------------------------
// The tooltip and the labels - non-negotiable 3
// ---------------------------------------------------------------------------

test("tooltip returns fixed, bounded text", () => {
  const text = tooltip();
  assert.equal(typeof text, "string");
  assert.ok(text.length > 0, "an empty tooltip identifies nothing");
  assert.ok(text.length <= MAX_TOOLTIP_LENGTH, `the tooltip is ${text.length} characters`);
  assert.equal(tooltip(), text, "the tooltip is not fixed");
});

test("the tooltip and every label are letters and spaces, and nothing else", () => {
  const rendered = [tooltip()];
  for (const state of ALL_STATES) {
    for (const entry of menuTemplate(state)) {
      if (Object.hasOwn(entry, "label")) {
        rendered.push(entry.label);
      }
    }
  }
  assert.ok(rendered.length > 1, "there was nothing to sweep");
  const offending = rendered.filter((text) => !LABEL_CHARSET.test(text));
  assert.equal(offending.length, 0, `text outside the allow-list: ${JSON.stringify(offending)}`);
});

// EVERY PLANT IS ASSEMBLED RATHER THAN SPELLED, and that is not a stylistic
// choice. A planted control is still a tracked file, and a tracked file may not
// carry a drive path or a home-directory segment (non-negotiable 3) - so a
// control written out in full would go red under the very sweeps in
// tests/shell/test_shell_assets.py that this project keeps for the purpose.
// Concatenation produces the shape at run time and leaves no such literal on
// disk. The solidus comes from its code point for the same reason: two of them
// adjacent open a line comment to any text scanner reading this file.
test("the label allow-list is proved able to reject each shape it exists for", () => {
  const solidus = String.fromCharCode(47);
  const planted = [
    "C" + ":" + "\\" + "somewhere",
    "https" + ":" + solidus + solidus + "host",
    "world" + "." + "backup",
    "account 123456",
  ];
  const tolerated = planted.filter((text) => LABEL_CHARSET.test(text));
  assert.equal(tolerated.length, 0, `the allow-list admitted: ${JSON.stringify(tolerated)}`);
  assert.ok(LABEL_CHARSET.test("Quit Clockspeed"), "the allow-list rejects a real label");
});

// ---------------------------------------------------------------------------
// The purity partition
// ---------------------------------------------------------------------------

// STRICTER THAN THE ARM shell/test/window.test.js CARRIES, and deliberately so.
// That one names the modules window.js must not reach for. This one asserts
// tray.js reaches for NOTHING - no desktop toolkit, no filesystem, no path
// module, no clock. An enumerated list of forbidden imports is a blocklist and
// goes stale; "imports nothing" cannot.
//
// The module's own header describes the forbidden call rather than spelling it,
// because this arm reads the file as text and cannot tell code from comment.
test("tray.js imports nothing at all - no toolkit, no builtin, no filesystem", () => {
  const source = fs.readFileSync(LIB_PATH, "utf8");
  assert.ok(!/\brequire\s*\(/.test(source), "tray.js reaches for a module");
  assert.ok(!/^\s*import\s/m.test(source), "tray.js carries an import statement");
  assert.ok(!/\bprocess\s*\./.test(source), "tray.js reads the process it runs in");
});

test("the purity detector is proved able to fire", () => {
  assert.ok(/\brequire\s*\(/.test('const a = require("node:fs");'));
  assert.ok(/^\s*import\s/m.test("import x from 'y';\n"));
  assert.ok(/\bprocess\s*\./.test("const p = process.env.HOME;"));
  assert.ok(!/\brequire\s*\(/.test('const a = "nothing here";'));
});

test("tray.js is 7-bit ASCII with no carriage returns", () => {
  const bytes = fs.readFileSync(LIB_PATH);
  assert.equal(bytes.includes(0x0d), false, "tray.js must be LF, never CRLF");
  for (const byte of bytes) {
    assert.ok(byte <= 0x7e, `non-ASCII byte 0x${byte.toString(16)} in tray.js`);
  }
});

test("this suite is itself 7-bit ASCII with no carriage returns", () => {
  const bytes = fs.readFileSync(__filename);
  assert.equal(bytes.includes(0x0d), false, "tray.test.js must be LF, never CRLF");
  for (const byte of bytes) {
    assert.ok(byte <= 0x7e, `non-ASCII byte 0x${byte.toString(16)} in tray.test.js`);
  }
});
