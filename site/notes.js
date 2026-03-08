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
    host.innerHTML = '<article class="note"><p class="note-type">EMPTY</p><h3>No notes yet</h3><p>Run the pipeline to populate drafts.</p></article>';
    return;
  }

  host.innerHTML = items.slice(0, 12).map((item, idx) => `
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
    const res = await fetch("/api/v1/public/notes-drafts", { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error("notes unavailable");
    const data = await res.json();
    renderNotes(data.items);
  } catch (_) {
    renderNotes([]);
  }
}

loadNotes();
