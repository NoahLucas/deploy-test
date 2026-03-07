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
loadFeed();
loadNotes();
