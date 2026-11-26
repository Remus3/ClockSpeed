# 0027 - Local API hardening: loopback by construction, no token yet, a per-mint subject, a logged cause

## Status

`accepted` - 2026-11-25

Written under CS-1261, whose acceptance is one sentence of four clauses: binding a
non-loopback address without an explicit local flag fails fast; no query-string token is
accepted; refusal reasons are logged server-side and the caller gets a generic refusal; two
generated certs differ in subject. This ADR records the four decisions that closed them and
the fence around each. It records nothing else. In particular it holds no token
protocol and no measurement of one, because none was taken and a figure written here would
be a guess.

## Context

**The dashboard is a local tool, and its listener is the only door.** The surface serves
HTTPS on loopback for the operator's own browser and the companion window. Four properties
of that door were open when CS-1261 was filed, and each had a tempting wrong answer.

**A bind flag is a way to be wrong.** The obvious reading of "binding a non-loopback
address fails fast" adds a flag, `--local` or `--allow-remote`, and tests that its absence
refuses. Every flag is a second way to reach the state the clause forbids. The repository
has no such flag today: `clockspeed/surface/server.py` raises before binding for any host
other than the loopback constant, `clockspeed/surface/__main__.py` declares no host
argument, and `clockspeed/surface/config.py` builds the configuration with the loopback
host. The clause is met by construction, and the arms that pin it already exist
(`tests/surface/test_server.py` `test_the_server_refuses_any_address_that_is_not_loopback`
and the loopback arms of `tests/surface/test_config.py`).

**A token is a credential, and a credential is a thing to leak.** "No query-string token is
accepted" invites building a token and then forbidding one transport of it. Nothing in the
current threat model needs a token. The one real attack on a loopback listener is a
cross-site page in the operator's own browser, and CS-1269's same-origin proof (a custom
request header no cross-site form can set, with no CORS preflight granted) already refuses
it. A second user account on this machine, or a build published for another machine, would
change that; neither exists. A token minted now would also have to be stored, rotated and
kept out of every log line and browser history, for no attacker this design has.

**A refusal wants to explain itself, and the caller is where it leaks.** ADR 0012 fixed
that a refusal's `detail` is looked up by reason code and never built from content. CS-1269
added the 403 with the published reason `cross_origin_refused`. The operator, reading
stderr, still cannot tell which check refused, because the log line was only a method, a
template and a status. Telling the CALLER the cause would hand a cross-site page a probe;
telling nobody makes a refusal undebuggable. The unit record flagged a conflict with ADR
0012 here: a reading of "a generic refusal" as a new generic reason code would rewrite a
published vocabulary.

**One fixed certificate subject is a fingerprint.** `scripts/make_cert.py` minted every
certificate with the same common name. Nothing identifies a person by it, but every
install carried the same one, so two installs were indistinguishable in a keychain and a
leaked certificate said nothing about which install it came from. The alternatives were a
name derived from the machine or account (personal data, forbidden by CLAUDE.md
non-negotiable 3), or a random name with no readable prefix (unrecognisable in a keystore).

## Decision

**1. Loopback only, by construction; the clause is closed by citation.** No local flag is
added and no host argument is added. The existing refusal in `server.py` and the arms above
are the evidence. Adding a flag later is a change to this ADR.

**2. No token is built now.** This is a knowing departure from the most literal reading of
the second clause, taken because there is no credential to accept. The clause still holds,
and it is pinned by `tests/surface/test_server.py`
`test_a_query_string_token_does_not_stand_in_for_the_proof`: every mutating route, asked
unproven with `token`, `access_token` or `auth` in the query, answers the 403 and never
reaches its handler. That arm is green on the unchanged code, so it was proven live by a
mutant in which the proof check also admitted a token parameter, which turned it red. The
trigger for building a token, and the wording of how one would travel, live in exactly one
place: the `BACKLOG.md` row for a per-start token. This ADR points at that row and does
not restate it.

**3. The certificate subject is minted per generation.** The subject is the fixed prefix
`/CN=clockspeed-local-` followed by 32 hexadecimal characters from `secrets.token_hex(16)`.
The common name that results is well under the 64 characters an X.509 common name may
carry. It is drawn from
`secrets` and from nothing else, so it carries no machine, account or user name and
depends on no environment value. The subject alternative name, which is the load-bearing
name a client verifies, is unchanged. Varying the subject is safe because the shell pins
the certificate bytes and checks no subject name (`shell/lib/trust.js` states that it
checks no subject, chain, expiry or revocation). Only the subject suffix is built here: no
openssl resolver, no minting service and no expiry or rotation policy, which belong to
later items.

**4. A refusal logs its cause, and the caller gets one envelope.** Only a 403 refusal
logs a cause. Its line is `<METHOD> <template> 403 refused=<cause>`, with the cause drawn
from a closed set held in `clockspeed/surface/server.py` whose only member today is
`proof`, and with the template, never the request path, in the label. This is the form the
CS-1437 leaf already specifies for its refusals, so that item extends the set rather than
rewriting the line. The caller's body is the same envelope whatever the cause,
`cross_origin_refused` with no request byte, and ADR 0012's published reason is unchanged.
"Generic" is therefore read as one fixed envelope, not as a new reason code. A 400, 404 or
405 is a reasoned error rather than a refusal and keeps the three-value log line.

## Consequences

- The only way to reach the listener from another machine is an edit to a refusal this ADR
  names, which is a change to this ADR and an operator-visible one.
- A future token is a decision of its own with its own record, and may not travel in a query
  string. Until its trigger fires there is no credential, and the pin arm keeps a
  query-string one from being admitted by accident.
- Two installs of the same version now carry different certificate subjects, so a keystore
  can tell them apart, and a test reading two real certificates back sees two subjects.
  Anything that matched the old fixed subject would break; nothing in this repository does.
- A new refusal path adds its cause word to the closed set at its raise site and nowhere
  else, and `_log` writes a cause only from that set, so a cause is always a literal this
  repository authored and never text a request supplied.
- Revisit this ADR if a second account uses the machine, if a build is published for
  another machine, if the shell starts checking a certificate subject, or if a refusal's
  published reason changes.
