"use strict";

/*
  CS-962 - the Scope panel's module. A SEAM STUB: it holds a place in the
  panel registry and builds nothing else yet.

  WHY A STUB IS SHIPPED RATHER THAN NOTHING. The seam is only proved by a
  member using it. An empty directory of future panels would leave
  registerPanel, the mount loop and the per-panel throw guard graded by their
  own author's assertions and by no caller at all - and a seam with no members
  is a seam nobody has tried to build against.

  WHAT REPLACING THIS LOOKS LIKE. Read the fields this panel needs off data,
  build nodes, append them to root. THIS FILE IS THE ONLY FILE THAT CHANGES:
  the module is already served, already loaded and already registered, so a
  panel written here collides with no other panel being written at the same
  time. That is the whole reason the seam exists.

  IT MUST NOT FETCH. app.js owns every request this page makes and issues them
  ONE AT A TIME on a button press. The second argument is what those requests
  already returned. A panel that opened its own would put the page's request
  behaviour outside the file that documents it.
*/

registerPanel("scope", function mountScope(root, data) {
  /*
    data is the resolved payloads - data.health, data.world, data.registry and
    the rest, each null where that route did not answer with one. This stub
    reads none of them, which is exactly what makes it a stub.
  */
  var heading = document.createElement("h2");
  heading.id = "h-panel-scope";
  heading.textContent = "Scope";
  root.setAttribute("aria-labelledby", heading.id);
  root.appendChild(heading);

  var note = document.createElement("p");
  note.className = "note";
  note.textContent = "no scope panel is built yet; this module holds the seam.";
  root.appendChild(note);
});
