'use strict';

// CS-602 slice S2 - tests for the pure certificate-pinning decision module.
//
// The module under test decides whether the Electron shell should trust a
// presented TLS certificate by exact byte identity against a single pinned
// certificate. It returns a SYMBOLIC verdict and never an integer. The integer
// mapping onto Electron's setCertificateVerifyProc callback lives in a
// different module on purpose, so an unconditional-success bypass - a bare
// callback(0), which also disables Certificate Transparency - cannot hide in
// here among the decision logic.
//
// FIXTURES: two REAL self-signed certificates generated with OpenSSL and
// embedded as literals. They are embedded rather than generated at test time
// deliberately. A fixture built only when a tool happens to be on PATH turns
// into a conditional skip, and a skip conditioned on the code under test is a
// mute button the defect gets to press - that is why CS-605 was closed, and
// CS-613 is open on exactly that class. Embedding makes every arm below
// unconditional: there is no branch here that can quietly not run.
//
// The certificates carry no private key material. A certificate is the public
// half by design; the keys that signed these never left a scratch directory.

const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');

const trust = require('../lib/trust.js');

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

// EC P-256, CN=localhost. Stands in for the certificate the local HTTPS
// surface serves and that the shell pins.
const PINNED_CERT_PEM = [
  '-----BEGIN CERTIFICATE-----',
  'MIIBwzCCAWmgAwIBAgIUIcKsv2G8liaS0Oo9ttf8LQN/fXEwCgYIKoZIzj0EAwIw',
  'NjESMBAGA1UEAwwJbG9jYWxob3N0MSAwHgYDVQQKDBdDbG9ja3NwZWVkIFRlc3Qg',
  'Rml4dHVyZTAgFw0yNjA4MzAwNDMxMDBaGA8yMTI2MDgwNjA0MzEwMFowNjESMBAG',
  'A1UEAwwJbG9jYWxob3N0MSAwHgYDVQQKDBdDbG9ja3NwZWVkIFRlc3QgRml4dHVy',
  'ZTBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABBssOp1yXVVlG/RsUUvZF8OK9yTQ',
  'muyFQOHS7NajR219MelXfD+peAK7CGq/Cd5R7ehQ46o+TzToNkrk/eA1S2KjUzBR',
  'MB0GA1UdDgQWBBT8QqgB3EuqZD+XD1lHryyIbW/K+jAfBgNVHSMEGDAWgBT8QqgB',
  '3EuqZD+XD1lHryyIbW/K+jAPBgNVHRMBAf8EBTADAQH/MAoGCCqGSM49BAMCA0gA',
  'MEUCICDzfti+DVigTVXFQ3dwU5iQFywkSfHQ6olR6sGKz0JDAiEA7J5ai21hGTXC',
  'xYvOWq4KZAuAiQyY01LirVMv1j4A7pw=',
  '-----END CERTIFICATE-----',
  '',
].join('\n');

// RSA-2048, CN=evil.example. A different key type on purpose: it guarantees a
// DER length far from the pin's, which is what the different-length arm needs.
const FOREIGN_CERT_PEM = [
  '-----BEGIN CERTIFICATE-----',
  'MIIDVTCCAj2gAwIBAgIUXX+Dn5ineWpwxuCX00LUoQBhucgwDQYJKoZIhvcNAQEL',
  'BQAwOTEVMBMGA1UEAwwMZXZpbC5leGFtcGxlMSAwHgYDVQQKDBdDbG9ja3NwZWVk',
  'IFRlc3QgRml4dHVyZTAgFw0yNjA4MzAwNDMxMDBaGA8yMTI2MDgwNjA0MzEwMFow',
  'OTEVMBMGA1UEAwwMZXZpbC5leGFtcGxlMSAwHgYDVQQKDBdDbG9ja3NwZWVkIFRl',
  'c3QgRml4dHVyZTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAK6XPa9H',
  'v6zTU4n8hMHnubAErH1c3z4Rfofu5fHAG83h2+29CTJUqEDYE70+QlhPGv4NP/MX',
  'twID0MapaudPmxSIz/bXEiqhzuyZzFmBVlRQlgt2x21vPcUT50NikNtQ1COG6q9v',
  'xzBmO+rpLv8mepUZ5O8U/hjWlEIAS+p+j1xDUdSj1pQgn7G/EMB5JH6TZNL9gs7T',
  'DDXBpcH64uW0sDiyYcGYrVDvxurdYraxqdUDem0hSl3KY1GN9KKd590qhb2+xCMy',
  'HOSwVrB1E6m8R8QXaU7iEwnHb3l7ifUPCoiMWzg+Eh7xwyKiPvH3lxEkxgIT/wXy',
  'KicVkDe60gfygsUCAwEAAaNTMFEwHQYDVR0OBBYEFDYIZ8lTbdm0OKpj66UIGACy',
  'w/FMMB8GA1UdIwQYMBaAFDYIZ8lTbdm0OKpj66UIGACyw/FMMA8GA1UdEwEB/wQF',
  'MAMBAf8wDQYJKoZIhvcNAQELBQADggEBAFBPOI4gyAjVhyxC2doqlMeWtHKMCsT5',
  '1QyTNkM1B7Ek/X/P/bUNnaET8G43Ba4WwA7RZq/fktTpSyykzOwM4Qw+gfzAcmtv',
  'HZYYSWfiP47/sE2/9KXD7Dkz0hHzI6VBAqoqgrtrABhMJsQyymlyLAWaKMj2S88K',
  'cRTllZtwZd1sfwim9jjwaQ8+xulCdsMzec3pLDq9+5VMkWBaLMZmShynWY3N6W5t',
  'hTXdcZ0g4w4WIApvukTPWbVRla4o4om4UxNaQouyiBJdYbggHoZ2XGzEhm2/Lr+x',
  'nZi4sLA5pfQ8jr9k5/Z3A1sw4kgsmNjawWXQbUAN7qeTW89G19seAF0=',
  '-----END CERTIFICATE-----',
  '',
].join('\n');

// Derived with the platform primitive directly, NOT with the module's own
// pemToDer. Building the fixtures with the code under test would let a broken
// converter agree with itself and make every byte-identity arm vacuous.
function derOf(pem) {
  return new crypto.X509Certificate(pem).raw;
}

const PINNED_DER = derOf(PINNED_CERT_PEM);
const FOREIGN_DER = derOf(FOREIGN_CERT_PEM);

// Same length as the pin, one byte different - the adversarial case a
// length-only check would wave straight through.
const IMPOSTOR_LAST_BYTE_DER = Buffer.from(PINNED_DER);
IMPOSTOR_LAST_BYTE_DER[IMPOSTOR_LAST_BYTE_DER.length - 1] ^= 0xff;

// Same length again, but differing at the front rather than the tail, so a
// compare that stops early is caught too.
const IMPOSTOR_FIRST_BYTE_DER = Buffer.from(PINNED_DER);
IMPOSTOR_FIRST_BYTE_DER[0] ^= 0xff;

// The pin with its final byte removed - a near miss on length.
const TRUNCATED_DER = PINNED_DER.subarray(0, PINNED_DER.length - 1);

const HOST = 'localhost';

// ---------------------------------------------------------------------------
// Fixture integrity - guards against the suite decaying into tautology
// ---------------------------------------------------------------------------

test('fixtures are distinct real certificates with differing DER lengths', () => {
  assert.ok(PINNED_DER.length > 0, 'pinned DER must be non-empty');
  assert.ok(FOREIGN_DER.length > 0, 'foreign DER must be non-empty');
  assert.notEqual(
    PINNED_DER.length,
    FOREIGN_DER.length,
    'the different-length arm is meaningless unless these differ',
  );
  assert.equal(
    IMPOSTOR_LAST_BYTE_DER.length,
    PINNED_DER.length,
    'the same-length arm is meaningless unless these match',
  );
  assert.ok(
    !IMPOSTOR_LAST_BYTE_DER.equals(PINNED_DER),
    'the same-length impostor must actually differ in content',
  );
});

// ---------------------------------------------------------------------------
// The five verdicts, one named test each
// ---------------------------------------------------------------------------

test('verdicts are distinct symbols and never integers', () => {
  const verdicts = [
    trust.TRUST,
    trust.DEFER,
    trust.REFUSE_NO_PIN,
    trust.REFUSE_NO_CERT,
    trust.REFUSE_MISMATCH,
  ];
  const numeric = verdicts.filter((v) => typeof v === 'number');
  assert.deepEqual(numeric, [], 'a numeric verdict would let callback(0) leak into this module');
  assert.equal(new Set(verdicts).size, 5, 'all five verdicts must be distinguishable');
});

test('REFUSE_NO_PIN when no certificate is pinned', () => {
  for (const absent of [undefined, null, Buffer.alloc(0), new Uint8Array(0)]) {
    const verdict = trust.decide({
      hostname: HOST,
      expectedHost: HOST,
      presentedDer: PINNED_DER,
      pinnedDer: absent,
    });
    assert.equal(verdict, trust.REFUSE_NO_PIN, 'absent pin must refuse, not fall through');
  }
});

test('DEFER for a non-loopback hostname, leaving Chromium validation ON', () => {
  const verdict = trust.decide({
    hostname: 'example.com',
    expectedHost: HOST,
    presentedDer: PINNED_DER,
    pinnedDer: PINNED_DER,
  });
  // Deferring hands the decision back to Chromium. The critical property is
  // the negative one: even though the presented bytes ARE the pinned bytes,
  // an unrelated host must not be granted the pin's trust, because that would
  // bypass validation for the whole internet.
  assert.equal(verdict, trust.DEFER);
  assert.notEqual(verdict, trust.TRUST, 'a foreign host must never inherit the pin');
});

test('REFUSE_NO_CERT when the peer presents nothing', () => {
  for (const absent of [undefined, null, Buffer.alloc(0), new Uint8Array(0)]) {
    const verdict = trust.decide({
      hostname: HOST,
      expectedHost: HOST,
      presentedDer: absent,
      pinnedDer: PINNED_DER,
    });
    assert.equal(verdict, trust.REFUSE_NO_CERT);
  }
});

test('REFUSE_MISMATCH for a foreign certificate of a DIFFERENT length', () => {
  // This is the arm that would have crashed. Establish the hazard is real
  // before asserting the module survives it - otherwise the arm proves
  // nothing about the ordering of the length check.
  assert.throws(
    () => crypto.timingSafeEqual(PINNED_DER, FOREIGN_DER),
    { code: 'ERR_CRYPTO_TIMING_SAFE_EQUAL_LENGTH' },
    'baseline: the primitive must throw on unequal lengths',
  );

  // A verify callback that throws never fires, so the page load hangs rather
  // than being refused. decide() must return a refusal instead of raising.
  let verdict;
  assert.doesNotThrow(() => {
    verdict = trust.decide({
      hostname: HOST,
      expectedHost: HOST,
      presentedDer: FOREIGN_DER,
      pinnedDer: PINNED_DER,
    });
  }, 'the length check must precede timingSafeEqual');
  assert.equal(verdict, trust.REFUSE_MISMATCH);

  // Both directions - a pin longer than the presentation must refuse too.
  let reversed;
  assert.doesNotThrow(() => {
    reversed = trust.decide({
      hostname: HOST,
      expectedHost: HOST,
      presentedDer: PINNED_DER,
      pinnedDer: FOREIGN_DER,
    });
  });
  assert.equal(reversed, trust.REFUSE_MISMATCH);
});

test('a view whose element count matches but whose BYTE count does not still refuses', () => {
  // A Uint16Array holds two bytes per element. This one has the same .length
  // as the pin but twice its .byteLength. An implementation that guards on
  // .length passes its own check and then crashes inside timingSafeEqual,
  // which compares by byte. Only a byteLength guard is correct here.
  const wideView = new Uint16Array(PINNED_DER.length);
  assert.equal(wideView.length, PINNED_DER.length, 'precondition: element counts match');
  assert.notEqual(wideView.byteLength, PINNED_DER.byteLength, 'precondition: byte counts differ');

  let verdict;
  assert.doesNotThrow(() => {
    verdict = trust.decide({
      hostname: HOST,
      expectedHost: HOST,
      presentedDer: wideView,
      pinnedDer: PINNED_DER,
    });
  }, 'the length guard must compare byteLength, not element count');
  assert.equal(verdict, trust.REFUSE_MISMATCH);
});

test('REFUSE_MISMATCH for a foreign certificate of the SAME length', () => {
  for (const impostor of [IMPOSTOR_LAST_BYTE_DER, IMPOSTOR_FIRST_BYTE_DER]) {
    assert.equal(impostor.length, PINNED_DER.length, 'precondition: equal lengths');
    const verdict = trust.decide({
      hostname: HOST,
      expectedHost: HOST,
      presentedDer: impostor,
      pinnedDer: PINNED_DER,
    });
    assert.equal(verdict, trust.REFUSE_MISMATCH, 'one differing byte must refuse');
  }
});

test('TRUST only for a byte-identical certificate', () => {
  // A distinct Buffer instance holding the same bytes: this must be byte
  // identity, not object identity.
  const copy = Buffer.from(PINNED_DER);
  assert.notEqual(copy, PINNED_DER, 'precondition: a separate instance');

  const verdict = trust.decide({
    hostname: HOST,
    expectedHost: HOST,
    presentedDer: copy,
    pinnedDer: PINNED_DER,
  });
  assert.equal(verdict, trust.TRUST);
});

// ---------------------------------------------------------------------------
// Control arm
// ---------------------------------------------------------------------------

test('control table - not one non-matching input reaches TRUST', () => {
  const cases = [
    ['no pin at all', { hostname: HOST, expectedHost: HOST, presentedDer: PINNED_DER }],
    ['empty pin', { hostname: HOST, expectedHost: HOST, presentedDer: PINNED_DER, pinnedDer: Buffer.alloc(0) }],
    ['no presented certificate', { hostname: HOST, expectedHost: HOST, pinnedDer: PINNED_DER }],
    ['empty presented certificate', { hostname: HOST, expectedHost: HOST, presentedDer: Buffer.alloc(0), pinnedDer: PINNED_DER }],
    ['foreign host', { hostname: 'example.com', expectedHost: HOST, presentedDer: PINNED_DER, pinnedDer: PINNED_DER }],
    ['lookalike host', { hostname: 'localhost.example.com', expectedHost: HOST, presentedDer: PINNED_DER, pinnedDer: PINNED_DER }],
    ['host differing only in case', { hostname: 'LOCALHOST', expectedHost: HOST, presentedDer: PINNED_DER, pinnedDer: PINNED_DER }],
    ['foreign certificate, different length', { hostname: HOST, expectedHost: HOST, presentedDer: FOREIGN_DER, pinnedDer: PINNED_DER }],
    ['impostor, same length, last byte', { hostname: HOST, expectedHost: HOST, presentedDer: IMPOSTOR_LAST_BYTE_DER, pinnedDer: PINNED_DER }],
    ['impostor, same length, first byte', { hostname: HOST, expectedHost: HOST, presentedDer: IMPOSTOR_FIRST_BYTE_DER, pinnedDer: PINNED_DER }],
    ['truncated by one byte', { hostname: HOST, expectedHost: HOST, presentedDer: TRUNCATED_DER, pinnedDer: PINNED_DER }],
    ['both sides empty', { hostname: HOST, expectedHost: HOST, presentedDer: Buffer.alloc(0), pinnedDer: Buffer.alloc(0) }],
    ['hostname absent on both sides', { presentedDer: PINNED_DER, pinnedDer: PINNED_DER }],
    ['presented as a PEM string rather than bytes', { hostname: HOST, expectedHost: HOST, presentedDer: PINNED_CERT_PEM, pinnedDer: PINNED_DER }],
    ['no arguments at all', {}],
  ];

  assert.ok(cases.length >= 6, 'the control arm needs at least six non-matching inputs');

  // Bind the offenders to a scalar first: asserting on the aggregate keeps the
  // failure message naming exactly which case leaked.
  const trusted = cases
    .filter(([, input]) => trust.decide(input) === trust.TRUST)
    .map(([name]) => name);
  assert.deepEqual(trusted, [], 'these non-matching inputs reached TRUST: ' + trusted.join('; '));
});

test('two empty buffers must not be mistaken for a match', () => {
  // The primitive says empty equals empty. If the emptiness checks were ever
  // reordered after the compare, this is the input that would silently TRUST.
  assert.equal(
    crypto.timingSafeEqual(Buffer.alloc(0), Buffer.alloc(0)),
    true,
    'baseline: the primitive really does call two empty buffers equal',
  );
  const verdict = trust.decide({
    hostname: HOST,
    expectedHost: HOST,
    presentedDer: Buffer.alloc(0),
    pinnedDer: Buffer.alloc(0),
  });
  assert.equal(verdict, trust.REFUSE_NO_PIN);
  assert.notEqual(verdict, trust.TRUST);
});

// ---------------------------------------------------------------------------
// PEM to DER helper
// ---------------------------------------------------------------------------

test('pemToDer converts a real certificate to its DER bytes', () => {
  const der = trust.pemToDer(PINNED_CERT_PEM);
  assert.ok(Buffer.isBuffer(der) || ArrayBuffer.isView(der), 'must return bytes');
  assert.ok(Buffer.from(der).equals(PINNED_DER), 'must match the platform primitive byte for byte');
});

test('pemToDer returns null rather than throwing on unusable input', () => {
  const garbage = [
    'not a certificate at all',
    '',
    '-----BEGIN CERTIFICATE-----\nnot base64 !!!\n-----END CERTIFICATE-----\n',
    '-----BEGIN CERTIFICATE-----\n-----END CERTIFICATE-----\n',
    PINNED_CERT_PEM.replace('MIIBwzCCAWmg', 'MIIBwzCCAWmh'),
    null,
    undefined,
    12345,
    {},
    Buffer.from([0x00, 0x01, 0x02]),
  ];

  // Every one must be handled by returning null. A throw here would crash the
  // verify callback, and a callback that never fires hangs the load.
  const threw = [];
  const nonNull = [];
  for (const input of garbage) {
    let result;
    try {
      result = trust.pemToDer(input);
    } catch (err) {
      threw.push(String(input) + ' -> ' + err.constructor.name);
      continue;
    }
    if (result !== null) {
      nonNull.push(String(input));
    }
  }
  assert.deepEqual(threw, [], 'pemToDer threw on: ' + threw.join('; '));
  assert.deepEqual(nonNull, [], 'pemToDer returned non-null for garbage: ' + nonNull.join('; '));
});

test('decide is pure - it does not mutate the buffers it is handed', () => {
  const pinned = Buffer.from(PINNED_DER);
  const presented = Buffer.from(IMPOSTOR_LAST_BYTE_DER);
  const pinnedBefore = Buffer.from(pinned);
  const presentedBefore = Buffer.from(presented);

  trust.decide({ hostname: HOST, expectedHost: HOST, presentedDer: presented, pinnedDer: pinned });

  assert.ok(pinned.equals(pinnedBefore), 'the pin must be left untouched');
  assert.ok(presented.equals(presentedBefore), 'the presentation must be left untouched');
});
