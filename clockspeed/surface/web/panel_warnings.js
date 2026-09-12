"use strict";

/*
  CS-962 - the Warnings panel. It renders the flagged-and-skipped stream that
  non-negotiable 7 requires be visible, from both sides of the wire that carry
  it: data.world.warnings and data.registry.warnings.

  WHY THIS PANEL EXISTS. The page already showed counts.warnings. A count tells
  a reader that something is wrong and nothing whatever about what, which is
  half of non-negotiable 7 left undone - "flagged" means a person can act on
  it, and nobody can act on the number 3.

  THE TWO SHAPES ARE NOT MERGED. A world warning carries source, code, detail,
  subject and count (world.py:142). A registry warning carries code, subject,
  detail and count and has NO source (registry.py:174). Merging them would mean
  inventing a source for one side or dropping it from the other, so they render
  as two labelled groups instead.

  unknown_classes IS NOT RENDERED HERE. app.js:408-424 already lists it in the
  World section, and world.py:213-221 records that a type_path is the ONE place
  a class path crosses this wire. One place on the wire, one place on the page;
  this panel points at that section rather than copying it.

  ------------------------------------------------------------------------
  THE PERSONAL-DATA FINDING, AND THE DEFENCE BUILT ON IT
  ------------------------------------------------------------------------

  Every string this panel renders came, transitively, out of the operator's
  own save file or their own game install. Non-negotiables 11 and 12 hold that
  a save is a personal-data-bearing artifact - its header carries platform,
  account and player-display-name strings in plaintext - and that ANY path
  echoing raw bytes is a leak. Non-negotiable 3 forbids an absolute path under
  a home directory, because on this machine such a path carries the Windows
  account name. tools/dashboard_probe.py SCREENSHOTS this page, so a leak here
  is a leak into an image.

  WHAT WAS MEASURED BEFORE THIS PANEL WAS WRITTEN. The producers were read, not
  assumed:

    - world.py:230-262 builds the body; the world token is MASKED at
      world.py:250 rather than carried.
    - world.py:192-210 copies exactly source, code, detail, subject and count
      off save/world.py's WorldWarning. Nothing else is promoted.
    - save/world.py:1760-1787 normalises four layers into that stream, and
      save/world.py:1102 fills detail from the fixed _WARNING_DETAIL table at
      save/world.py:484-505.
    - chunks.py:1082 and objects.py:1782 likewise take detail from a fixed
      table (chunks.py:219, objects.py:744). Neither layer declares a subject
      at all.
    - header.py:915-953 is the only header producer. Its subjects are a
      version PAIR and the LENGTH of the world token - header.py:947 takes
      len(world_token) precisely so the token itself cannot become an echo
      path - and its details interpolate only integers.
    - usmap.py raises every warning through _WarningLog.add at usmap.py:662;
      all twelve call sites (usmap.py:709 through usmap.py:1160) pass a
      structural token - "name-12", "schema-4-super", "type-19" - and a detail
      interpolating integers only.
    - registry.py:408-426 declares RegistryWarning; its subject is a class
      name, a group short name or an index, and registry.py:1338 passes a
      reason drawn from the closed REASON_* set at docs_extract.py:313-325.

  THE VERDICT: no producer reachable today can put a filesystem path, an
  account id, a world name or a display name into any field this panel
  renders. Fifty-two detail strings were harvested from those six modules and
  every one of them is inside the character set this file accepts.

  WHY A GUARD IS SHIPPED ANYWAY. That verdict is a statement about today's
  producers. The DOM is where a future producer's mistake would become a
  screenshot, and a sink that trusts an audit is a sink that has no defence the
  day the audit goes stale. So every rendered value must be INSIDE a stated
  shape, and anything else renders as WITHHELD.

  ------------------------------------------------------------------------
  THE REFUTATION THIS GUARD WAS REBUILT AROUND
  ------------------------------------------------------------------------

  THE FIRST VERSION OF THIS GUARD WAS A PATH CHECK WEARING ALLOWLIST CLOTHING,
  and it said so in prose that was false. It accepted any value built from
  letters, digits and a little punctuation, and claimed that as a defence
  against a defect that "wears a different field each time". What it actually
  excluded was a path separator and a non-ASCII byte. Three of the four
  personal-data classes CLAUDE.md section 2 names need neither:

    - a platform account id is ENTIRELY alphanumeric and far under the length
      limit, so a subject carrying one was returned verbatim;
    - a world name is alphanumeric plus spaces;
    - a player display name is alphanumeric plus spaces.

  All three were measured passing the old sets into span.warning-subject and
  span.warning-detail, which is into the dashboard_probe screenshot. A
  character set is the wrong instrument for this: naming the bad characters is
  a denylist however it is spelled, and none of those three shapes needs one.

  WHAT REPLACED IT: A SHAPE RULE PER FIELD, over the whole value rather than
  over its characters one at a time. The character sets are kept as a FLOOR -
  they are what refuses a path and a non-ASCII byte, and they do that well -
  and a positive shape claim is layered on top of each:

    - A CODE OR A SOURCE is a lowercase hyphenated token that LEADS WITH A
      LETTER. Every WARN_* spelling in clockspeed/save and clockspeed/data and
      every stage name in save/world.py matches that and nothing else does; a
      code that is a bare run of digits is now refused where the old set
      returned it.

    - A SUBJECT is a structural token that carries NO OPAQUE IDENTIFIER RUN.
      The two run shapes are not invented here: they are the ones
      tests/surface/test_web_assets.py's personal_data_findings already calls
      personal data - a run of decimal digits, and a longer run of hex
      characters. OPAQUE_DIGIT_RUN and OPAQUE_HEX_RUN below carry those
      thresholds, and a test derives them from that function rather than
      trusting this comment, so the two cannot drift. The version-pair
      exception header.py needs survives, because a version is a short run.

    - A DETAIL MUST READ AS AUTHORED PROSE, which is the one claim strong
      enough to refuse a name. A name is a label: a few title-cased words, or
      one word, and no grammar. An authored consequence line is a sentence. So
      a detail must carry at least MIN_DETAIL_WORDS words AND at least one word
      from PROSE_WORDS - a closed vocabulary of lowercase English function
      words. "Grand Northern Forest Outpost" and "Somebody Nameson" carry
      none; every line the producers author carries several.

      THE VOCABULARY IS MATCHED IN LOWERCASE ONLY, and that is the mechanism
      rather than an oversight: lowerWord keeps only lowercase letters, so
      "The" reduces to "he" and never matches "the". A title-cased name
      therefore cannot borrow a function word to get through, while a sentence
      - which carries lowercase function words wherever it begins - always
      can. Two of the shortest authored lines in the project lead with a
      capitalised identifier ("NativeClass carries no trailing class name",
      "Classes is missing or is not a JSON list") and both pass on their
      lowercase "no" and "is".

  OVERCORRECTION IS THE OTHER FAILURE MODE, and it is a measured one in this
  repository rather than a worry - a repair once started killing healthy work.
  So the floor is pinned by a test that harvests EVERY detail the shipping
  producers can author - the three _WARNING_DETAIL tables plus docs_extract's
  REASON_* constants - pushes all of them through this sink in one mount, and
  fails if any comes back withheld. MIN_DETAIL_WORDS sits one word below the
  shortest of them. A producer that authors a line this sink would hide reddens
  in that producer's own change rather than shipping a page that hides it.

  WHAT THIS GUARD STILL CANNOT DO, stated because a defence that oversells
  itself is worse than one that does not: a world name that IS an ordinary
  lowercase English phrase, interpolated into an otherwise authored sentence,
  is not distinguishable from prose by any lexical rule and would pass. The
  defence against that one is upstream - the producers do not interpolate
  content, and the audit above is what checks that. This sink narrows the
  window; it does not close it.

  NON-ASCII IS REFUSED DELIBERATELY, and it is the sharpest of the floor arms.
  Rule 4 requires every authored line in this project to be 7-bit ASCII. So a
  detail arriving with a character outside that set was not authored - it was
  built from content, and the content most likely to carry one is a player
  display name. Non-ASCII is treated as proof of provenance.

  WITHHELD IS RENDERED, NOT DROPPED. A refused value leaves a visible marker
  and its warning's code still shows. Silently dropping it would make a
  refusal indistinguishable from an absence, which is the same collapse the
  save layer refuses one floor down.

  IT MUST NOT FETCH. app.js owns every request this page makes. The second
  argument is what those requests already returned.

  Everything below lives inside one closure. Panel modules share a global
  scope, so a helper declared at the top level of this file would collide with
  a sibling panel being written at the same moment.
*/

(function () {
  /* Letters and digits, shared by every set below. */
  var ALNUM =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

  /* Lowercase letters alone, which is what makes the prose rule work. */
  var LOWER = "abcdefghijklmnopqrstuvwxyz";

  /* A code or a source: lowercase, hyphenated, and leading with a letter. */
  var SET_CODE = LOWER + "0123456789-";

  /* A structural token: a class name, a group name, an index, a stage name. */
  var SET_TOKEN = ALNUM + "_.-";

  /* Authored prose. No backslash, no slash, no colon - no path can pass. */
  var SET_DETAIL = ALNUM + " ,.;'()_-";

  /* The two alphabets an opaque identifier is built out of. */
  var DIGITS = "0123456789";
  var HEX = "0123456789abcdefABCDEF";

  /*
    The run lengths that make a value an identifier rather than a token. Both
    are the thresholds tests/surface/test_web_assets.py's
    personal_data_findings already sweeps for, and
    test_panel_warnings.py's threshold arm derives them from that function
    rather than reading them here - a restated number is a number that drifts.
  */
  var OPAQUE_DIGIT_RUN = 12;
  var OPAQUE_HEX_RUN = 32;

  /*
    A closed vocabulary of lowercase English function words. A detail must
    carry one. A label - a world name, a display name - carries none, and every
    line this project's producers author carries several.
  */
  var PROSE_WORDS =
    " a an and are as at be because been before but by can cannot could did do"
    + " does for from had has have how if in into is it its may no nor not of"
    + " on once only or rather same should since so than that the their them"
    + " then there these they this those to too until up upon was were what"
    + " when where which while who whose why will with within without would ";

  /* One word is a label. A consequence line is a sentence. */
  var MIN_DETAIL_WORDS = 4;

  /* A fixed line is short. A dumped buffer or a deep path is not. */
  var DETAIL_LIMIT = 400;
  var TOKEN_LIMIT = 120;

  /* What stands in for a value whose shape this panel does not accept. */
  var WITHHELD = "[withheld - unexpected shape]";

  function withinSet(value, allowed, limit) {
    /*
      True when every character of value is in allowed and the length is
      inside limit. The scan is an allowlist: a character is accepted only by
      being present in the set, never by failing to match something bad.
    */
    if (typeof value !== "string") {
      return false;
    }
    if (value.length === 0 || value.length > limit) {
      return false;
    }
    for (var i = 0; i < value.length; i += 1) {
      if (allowed.indexOf(value.charAt(i)) === -1) {
        return false;
      }
    }
    return true;
  }

  function isVersionPair(value) {
    /*
      The one shape carrying a slash that this panel accepts: header.py:936
      spells an unmeasured version pair as "<header>/<save>". Both sides must
      be digits, so no path component can wear this shape.
    */
    if (typeof value !== "string" || value.length > TOKEN_LIMIT) {
      return false;
    }
    var parts = value.split("/");
    if (parts.length !== 2) {
      return false;
    }
    for (var i = 0; i < 2; i += 1) {
      if (!withinSet(parts[i], "0123456789", TOKEN_LIMIT)) {
        return false;
      }
    }
    return true;
  }

  function hasOpaqueRun(value, alphabet, limit) {
    /*
      True when value carries an unbroken run of limit characters out of
      alphabet. The run is what matters and not the whole value: an account id
      interpolated into a sentence is the shape a future producer's mistake
      actually wears, and a whole-value test would miss it.
    */
    var run = 0;
    for (var i = 0; i < value.length; i += 1) {
      if (alphabet.indexOf(value.charAt(i)) === -1) {
        run = 0;
        continue;
      }
      run += 1;
      if (run >= limit) {
        return true;
      }
    }
    return false;
  }

  function carriesAnOpaqueIdentifier(value) {
    /* Either of the two identifier shapes this repository already sweeps for. */
    return (
      hasOpaqueRun(value, DIGITS, OPAQUE_DIGIT_RUN)
      || hasOpaqueRun(value, HEX, OPAQUE_HEX_RUN)
    );
  }

  function lowerWord(word) {
    /*
      The word reduced to its lowercase letters. THIS IS THE MECHANISM OF THE
      PROSE RULE, not a tidying step: dropping every character that is not a
      lowercase letter means a capitalised word cannot reduce to a function
      word - "The" becomes "he" - so a title-cased name cannot borrow one.
    */
    var out = "";
    for (var i = 0; i < word.length; i += 1) {
      var ch = word.charAt(i);
      if (LOWER.indexOf(ch) !== -1) {
        out += ch;
      }
    }
    return out;
  }

  function readsAsAuthoredProse(value) {
    /*
      True when value is a sentence rather than a label: enough words, and at
      least one of them a lowercase function word.
    */
    var words = value.split(" ");
    var counted = 0;
    var spoken = false;
    for (var i = 0; i < words.length; i += 1) {
      if (words[i].length === 0) {
        continue;
      }
      counted += 1;
      var word = lowerWord(words[i]);
      if (word.length > 0 && PROSE_WORDS.indexOf(" " + word + " ") !== -1) {
        spoken = true;
      }
    }
    return counted >= MIN_DETAIL_WORDS && spoken;
  }

  function safeCode(value) {
    /*
      A warning code or a source stage name: lowercase, hyphenated, leading
      with a letter. The leading-letter clause is what refuses a code that is a
      bare run of digits, which the character set alone admitted.
    */
    if (!withinSet(value, SET_CODE, TOKEN_LIMIT)) {
      return WITHHELD;
    }
    if (LOWER.indexOf(value.charAt(0)) === -1) {
      return WITHHELD;
    }
    return value;
  }

  function safeToken(value) {
    /* A subject or an unknown-group name, carrying no opaque identifier. */
    if (typeof value !== "string" || carriesAnOpaqueIdentifier(value)) {
      return WITHHELD;
    }
    if (withinSet(value, SET_TOKEN, TOKEN_LIMIT) || isVersionPair(value)) {
      return value;
    }
    return WITHHELD;
  }

  function safeDetail(value) {
    /* An authored consequence line: inside the set, no identifier, prose. */
    if (!withinSet(value, SET_DETAIL, DETAIL_LIMIT)) {
      return WITHHELD;
    }
    if (carriesAnOpaqueIdentifier(value) || !readsAsAuthoredProse(value)) {
      return WITHHELD;
    }
    return value;
  }

  function safeCount(value) {
    /*
      A count is a whole number on both wires. Anything else is not rendered
      as one - a string count could carry any text at all, and a float would
      be a float on a page whose arithmetic is exact.
    */
    if (typeof value !== "number") {
      return WITHHELD;
    }
    if (!isFinite(value) || Math.floor(value) !== value || value < 0) {
      return WITHHELD;
    }
    return String(value);
  }

  function el(tag, className, text) {
    /*
      One element, built the only way the stand-in DOM supports: createElement,
      a className assignment, textContent. Never innerHTML - every string that
      reaches here is untrusted text and parsing it as markup would make the
      shape guard above theatre.
    */
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== null && text !== undefined) {
      node.textContent = text;
    }
    return node;
  }

  function isArray(value) {
    /* Array.isArray, spelled out so a non-array payload is a branch. */
    return Object.prototype.toString.call(value) === "[object Array]";
  }

  function warningRow(entry, withSource) {
    /*
      One warning as a list item. Every field goes through its own guard, and
      the code is emitted first so that a row whose other fields were all
      withheld still tells a reader WHICH warning fired.
    */
    var row = el("li", "warning", null);
    row.appendChild(el("span", "warning-code", safeCode(entry.code)));
    if (withSource) {
      row.appendChild(el("span", "warning-source", safeCode(entry.source)));
    }
    if (entry.subject !== null && entry.subject !== undefined) {
      row.appendChild(el("span", "warning-subject", safeToken(entry.subject)));
    }
    row.appendChild(el("span", "warning-count", safeCount(entry.count)));
    row.appendChild(el("span", "warning-detail", safeDetail(entry.detail)));
    return row;
  }

  function warningList(entries, withSource) {
    /*
      The rows, or null when there is nothing well formed to list. A row that
      is not an object is skipped rather than fatal, which is non-negotiable 7
      applied to this layer's own input.
    */
    var list = el("ul", "warning-list", null);
    var shown = 0;
    for (var i = 0; i < entries.length; i += 1) {
      var entry = entries[i];
      if (entry === null || typeof entry !== "object") {
        continue;
      }
      list.appendChild(warningRow(entry, withSource));
      shown += 1;
    }
    return shown > 0 ? list : null;
  }

  function group(root, label, data, key, withSource) {
    /*
      One labelled group, in exactly one of three states that a reader has to
      be able to tell apart:

        - the route did not answer at all, so nothing is known;
        - it answered and reported nothing, which is a real, good result;
        - it answered and reported these.

      Collapsing the first two into "no warnings" would let an endpoint that
      never replied read as a clean bill of health. That is the worst
      available failure for a panel whose whole job is to surface trouble.
    */
    var section = el("section", "warning-group", null);
    section.appendChild(el("h3", "warning-group-label", label));
    if (data === null || data === undefined || typeof data !== "object") {
      section.appendChild(
        el("p", "note", "did not answer, so nothing is known about what it flagged")
      );
      root.appendChild(section);
      return;
    }
    var entries = isArray(data[key]) ? data[key] : [];
    var list = warningList(entries, withSource);
    if (list === null) {
      section.appendChild(el("p", "note", "answered and reported no warnings"));
    } else {
      section.appendChild(list);
    }
    root.appendChild(section);
  }

  function unmodelled(root, world) {
    /*
      contains_unmodeled_content (world.py:119) is its own fact, not a
      function of the warning list: the flag can be true while the array is
      empty. A panel deriving the line from the list length would say nothing
      in exactly the case that matters.
    */
    if (world === null || world === undefined || typeof world !== "object") {
      return;
    }
    if (!world["contains_unmodeled_content"]) {
      return;
    }
    root.appendChild(
      el(
        "p",
        "note",
        "this world carries unmodelled content; the classes involved are listed"
          + " in the World section of this page"
      )
    );
  }

  function unknownGroups(root, registry) {
    /*
      registry.unknown_groups (registry.py:142) names a docs group this build
      does not model. Each one goes through the token guard - it is a short
      name in every measured case, and a name is the only thing it may be.
    */
    if (registry === null || registry === undefined || typeof registry !== "object") {
      return;
    }
    var groups = isArray(registry["unknown_groups"]) ? registry["unknown_groups"] : [];
    if (groups.length === 0) {
      return;
    }
    var section = el("section", "warning-group", null);
    section.appendChild(el("h3", "warning-group-label", "Unmodelled registry groups"));
    var list = el("ul", "warning-list", null);
    for (var i = 0; i < groups.length; i += 1) {
      list.appendChild(el("li", "warning", safeToken(groups[i])));
    }
    section.appendChild(list);
    root.appendChild(section);
  }

  registerPanel("warnings", function mountWarnings(root, data) {
    /*
      data is the resolved payloads - data.world and data.registry here, each
      null where that route did not answer with one.
    */
    var heading = document.createElement("h2");
    heading.id = "h-panel-warnings";
    heading.textContent = "Warnings";
    root.setAttribute("aria-labelledby", heading.id);
    root.appendChild(heading);

    var world = data ? data["world"] : null;
    var registry = data ? data["registry"] : null;

    group(root, "World warnings", world, "warnings", true);
    unmodelled(root, world);
    group(root, "Registry warnings", registry, "warnings", false);
    unknownGroups(root, registry);
  });
})();
