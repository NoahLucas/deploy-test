function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function parseSlug() {
  const url = new URL(window.location.href);
  return (url.searchParams.get("slug") || "").trim();
}

function renderMarkdown(markdown) {
  const safe = String(markdown || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
  return safe
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n\n/g, "</p><p>");
}

async function loadNote() {
  const slug = parseSlug();
  if (!slug) {
    setText("note-title", "Missing note slug");
    setText("note-summary", "Use /note.html?slug=<your-slug>");
    return;
  }

  try {
    const res = await fetch(`/api/v1/public/notes-drafts/${encodeURIComponent(slug)}`, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error("note not found");
    const data = await res.json();
    setText("note-type", slug.startsWith("autobiography-") ? "LIVING AUTOBIOGRAPHY" : "DRAFT NOTE");
    setText("note-title", data.title);
    setText("note-summary", data.summary);
    const body = document.getElementById("note-body");
    if (body) body.innerHTML = `<p>${renderMarkdown(data.body_markdown)}</p>`;
  } catch (_) {
    setText("note-title", "Note unavailable");
    setText("note-summary", "Draft not found or backend unavailable.");
  }
}

loadNote();
