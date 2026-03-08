const fallback = {
  headline: "Operating signal: strong creative momentum with moderate context-switching drag.",
  metrics: {
    recovery: "84/100",
    focus: "91/100",
    balance: "76/100",
    action: "Protect two 90-minute deep-work blocks before noon."
  }
};

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function applyFeed(data) {
  setText("fusion-headline", data.headline);
  setText("m-recovery", data.metrics.recovery);
  setText("m-focus", data.metrics.focus);
  setText("m-balance", data.metrics.balance);
  setText("m-action", data.metrics.action);
}

async function loadFeed() {
  try {
    const res = await fetch("/api/v1/public/feed", { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error("feed unavailable");
    const data = await res.json();
    applyFeed({
      headline: data.headline,
      metrics: {
        recovery: data.metrics.recovery,
        focus: data.metrics.focus,
        balance: data.metrics.balance,
        action: data.metrics.action
      }
    });
  } catch (_) {
    applyFeed(fallback);
  }
}

function setupReveal() {
  const nodes = Array.from(document.querySelectorAll(".reveal"));
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) entry.target.classList.add("in");
    });
  }, { threshold: 0.16 });

  nodes.forEach((node, i) => {
    node.style.transitionDelay = `${Math.min(i * 60, 240)}ms`;
    io.observe(node);
  });
}

function renderAsciiFrame(tick) {
  const width = 58;
  const height = 14;
  const lines = [];
  const centerY = Math.floor(height / 2);
  const centerX = Math.floor(width / 2);

  for (let y = 0; y < height; y += 1) {
    let row = "";
    for (let x = 0; x < width; x += 1) {
      const dx = x - centerX;
      const dy = y - centerY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const wave = Math.sin(dist * 0.42 - tick * 0.23);
      const sweep = Math.sin((x * 0.19) + (tick * 0.18));
      if (Math.abs(dy) < 1 && x > 5 && x < width - 6 && sweep > 0.66) {
        row += ">";
      } else if (wave > 0.72) {
        row += "#";
      } else if (wave > 0.42) {
        row += "*";
      } else if (wave > 0.14) {
        row += "+";
      } else if (wave > -0.2) {
        row += ".";
      } else {
        row += " ";
      }
    }
    lines.push(row);
  }

  const label = "NOAH LUCAS // PRODUCT AS PLATFORM // LIVE SIGNAL";
  const labelStart = Math.max(0, Math.floor((width - label.length) / 2));
  const mid = lines[Math.max(1, centerY - 1)].split("");
  for (let i = 0; i < label.length && labelStart + i < mid.length; i += 1) {
    mid[labelStart + i] = label[i];
  }
  lines[Math.max(1, centerY - 1)] = mid.join("");
  return lines.join("\n");
}

function setupAsciiHero() {
  const host = document.getElementById("ascii-hero");
  if (!host) return;
  let tick = 0;
  const draw = () => {
    host.textContent = renderAsciiFrame(tick);
    tick += 1;
  };
  draw();
  setInterval(draw, 220);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderNotes(items) {
  const host = document.getElementById("notes-list");
  if (!host) return;
  if (!Array.isArray(items) || items.length === 0) {
    host.innerHTML = `
      <article class="note">
        <p class="note-type">PIPELINE READY</p>
        <h3>No generated notes yet</h3>
        <p>Run the notes pipeline endpoint to auto-populate this section.</p>
      </article>
    `;
    return;
  }

  host.innerHTML = items.slice(0, 6).map((item, idx) => `
    <article class="note">
      <p class="note-type">DRAFT ${idx + 1}</p>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.summary)}</p>
    </article>
  `).join("");
}

async function loadNotes() {
  try {
    const res = await fetch("/api/v1/public/notes-drafts", { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error("notes unavailable");
    const data = await res.json();
    renderNotes(data.items);
  } catch (_) {
    renderNotes([]);
  }
}

setText("year", new Date().getFullYear().toString());
setupReveal();
setupAsciiHero();
loadFeed();
loadNotes();
