# Presence Lab Integration Notes

`/presence-lab.html` is an experimental full-screen presence surface designed to be controlled by external runtime signals.

## Runtime control interfaces

1. Global API (`window.presenceLab`)

```js
window.presenceLab.getState();
window.presenceLab.setState("listening"); // idle | listening | synthesizing | advising | acting
window.presenceLab.setAnimal("wolf"); // none | wolf | owl | octopus | raven
window.presenceLab.setSurface("Voice Relay"); // or numeric index
window.presenceLab.setAuto(true);
window.presenceLab.dispatch({ state: "acting", animal: "wolf", auto: false });
```

2. `postMessage` bridge

```js
iframeEl.contentWindow.postMessage(
  { type: "presence", state: "synthesizing", animal: "octopus", surface: "Web Focus", auto: true },
  "*"
);
```

3. DOM event bridge

```js
window.dispatchEvent(
  new CustomEvent("eos:presence", {
    detail: { state: "advising", animal: "raven", surface: "iPhone Context" }
  })
);
```

## URL boot params

- `?state=listening`
- `?form=wolf` (or `?animal=wolf`)
- `?auto=true`

Example:

`/presence-lab.html?state=synthesizing&form=octopus&auto=true`

## Design intent

- Main page (`/`) remains minimal and stable.
- Presence Lab is the high-variance experimental surface.
- Reduced motion users get lower particle count and no auto mode by default.
