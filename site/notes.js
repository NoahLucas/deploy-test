function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderFeaturedAutobio(item) {
  const host = document.getElementById("autobio-featured");
  if (!host) return;
  if (!item) {
    host.innerHTML = '<article class="note"><p class="note-type">LIVE NOTE</p><h3>Autobiography coming soon</h3><p>The nightly autobiographer will publish here once the first live chapter is generated.</p></article>';
    return;
  }

  host.innerHTML = `
    <article class="note">
      <p class="note-type">LIVING AUTOBIOGRAPHY</p>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.summary)}</p>
      <p><a href="/note.html?slug=${encodeURIComponent(item.slug)}">Open living chapter</a></p>
    </article>
  `;
}

function renderNotes(items) {
  const host = document.getElementById("notes-list");
  if (!host) return;
  const filtered = Array.isArray(items)
    ? items.filter((item) => !String(item.slug || "").startsWith("autobiography-"))
    : [];
  if (filtered.length === 0) {
    host.innerHTML = '<article class="note"><p class="note-type">EMPTY</p><h3>No notes yet</h3><p>Run the pipeline to populate drafts.</p></article>';
    return;
  }

  host.innerHTML = filtered.slice(0, 12).map((item, idx) => `
    <article class="note">
      <p class="note-type">DRAFT ${idx + 1}</p>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.summary)}</p>
      <p><a href="/note.html?slug=${encodeURIComponent(item.slug)}">Open draft</a></p>
    </article>
  `).join("");
}

async function loadNotes() {
  try {
    const [liveRes, notesRes] = await Promise.all([
      fetch("/api/v1/public/autobiography/live", { headers: { Accept: "application/json" } }),
      fetch("/api/v1/public/notes-drafts", { headers: { Accept: "application/json" } })
    ]);
    if (liveRes.ok) {
      const live = await liveRes.json();
      renderFeaturedAutobio(live);
    } else {
      renderFeaturedAutobio(null);
    }
    if (!notesRes.ok) throw new Error("notes unavailable");
    const data = await notesRes.json();
    renderNotes(data.items);
  } catch (_) {
    renderFeaturedAutobio(null);
    renderNotes([]);
  }
}

loadNotes();
