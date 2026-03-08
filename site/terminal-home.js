const bootLines = [
  "booting noahlucas terminal...",
  "loading operator profile...",
  "mounting ai-native surfaces: public, lab, integrations...",
  "syncing signal feed...",
  "ready."
];

const output = document.getElementById("terminal-output");
const boot = document.getElementById("boot-log");
const form = document.getElementById("terminal-form");
const input = document.getElementById("terminal-input");
const clock = document.getElementById("terminal-clock");
const ascii = document.getElementById("ascii-hero");

const state = {
  feed: null,
  notes: [],
};

function writeLine(text, cls = "") {
  if (!output) return;
  const line = document.createElement("div");
  if (cls) line.className = cls;
  line.textContent = text;
  output.appendChild(line);
  output.scrollTop = output.scrollHeight;
}

function renderAscii(tick) {
  if (!ascii) return;
  const w = 64;
  const h = 12;
  const rows = [];
  for (let y = 0; y < h; y += 1) {
    let row = "";
    for (let x = 0; x < w; x += 1) {
      const wave = Math.sin((x * 0.21) + (tick * 0.2)) + Math.cos((y * 0.7) - (tick * 0.24));
      row += wave > 1.15 ? "#" : wave > 0.55 ? "*" : wave > 0.08 ? "+" : wave > -0.35 ? "." : " ";
    }
    rows.push(row);
  }
  const tag = "LIVE SIGNAL // NOAH LUCAS";
  const start = Math.floor((w - tag.length) / 2);
  const mid = rows[5].split("");
  for (let i = 0; i < tag.length; i += 1) mid[start + i] = tag[i];
  rows[5] = mid.join("");
  ascii.textContent = rows.join("\n");
}

function renderHelp() {
  writeLine("commands:", "accent");
  writeLine("  help           show commands");
  writeLine("  about          brand positioning");
  writeLine("  feed           latest signal headline");
  writeLine("  notes          list latest notes");
  writeLine("  open [target]  open page (lab|integrations|notes|work|contact)");
  writeLine("  clear          clear console");
}

function renderAbout() {
  writeLine("Noah Lucas: VP Product + Entrepreneur.", "accent");
  writeLine("Building products that turn ambiguity into advantage.");
  writeLine("This terminal is a living interface for brand, strategy, and AI-native execution.");
}

function renderFeed() {
  if (!state.feed) {
    writeLine("signal feed unavailable. try again shortly.", "muted");
    return;
  }
  writeLine(`headline: ${state.feed.headline}`, "accent");
  writeLine(`recovery: ${state.feed.metrics.recovery}`);
  writeLine(`focus:    ${state.feed.metrics.focus}`);
  writeLine(`balance:  ${state.feed.metrics.balance}`);
  writeLine(`action:   ${state.feed.metrics.action}`);
}

function renderNotes() {
  if (!state.notes.length) {
    writeLine("no notes generated yet.", "muted");
    return;
  }
  state.notes.slice(0, 6).forEach((note, i) => {
    writeLine(`${i + 1}. ${note.title}`, "accent");
    writeLine(`   ${note.summary}`);
  });
}

function openTarget(target) {
  const map = {
    lab: "/lab.html",
    integrations: "/integrations.html",
    notes: "/notes.html",
    work: "/work.html",
    contact: "/contact.html",
  };
  const url = map[target];
  if (!url) {
    writeLine("unknown target. use: lab|integrations|notes|work|contact", "muted");
    return;
  }
  window.location.href = url;
}

function runCommand(raw) {
  const value = raw.trim();
  if (!value) return;
  writeLine(`noah@studio:~$ ${value}`);
  const [cmd, arg] = value.split(/\s+/, 2);
  switch (cmd.toLowerCase()) {
    case "help":
      renderHelp();
      break;
    case "about":
      renderAbout();
      break;
    case "feed":
      renderFeed();
      break;
    case "notes":
      renderNotes();
      break;
    case "open":
      openTarget((arg || "").toLowerCase());
      break;
    case "clear":
      if (output) output.innerHTML = "";
      break;
    default:
      writeLine(`command not found: ${cmd}`, "muted");
      writeLine("type 'help' for available commands", "muted");
  }
}

async function loadData() {
  try {
    const feedRes = await fetch("/api/v1/public/feed", { headers: { Accept: "application/json" } });
    if (feedRes.ok) state.feed = await feedRes.json();
  } catch (_) {}
  try {
    const notesRes = await fetch("/api/v1/public/notes-drafts", { headers: { Accept: "application/json" } });
    if (notesRes.ok) {
      const body = await notesRes.json();
      state.notes = Array.isArray(body.items) ? body.items : [];
    }
  } catch (_) {}
}

async function bootTerminal() {
  if (boot) {
    for (const line of bootLines) {
      boot.textContent += `${line}\n`;
      await new Promise((resolve) => setTimeout(resolve, 180));
    }
  }
  writeLine("terminal online.", "accent");
  writeLine("type 'help' to begin.");
}

function startClock() {
  const tick = () => {
    if (clock) clock.textContent = new Date().toLocaleTimeString();
  };
  tick();
  setInterval(tick, 1000);
}

let frame = 0;
setInterval(() => {
  renderAscii(frame);
  frame += 1;
}, 240);
renderAscii(0);
startClock();
loadData().finally(() => {
  bootTerminal();
});

if (form && input) {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    runCommand(input.value);
    input.value = "";
  });
}
